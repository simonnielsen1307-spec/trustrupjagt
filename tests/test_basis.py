import json, sys, re, asyncio
from playwright.async_api import async_playwright

import os
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..', 'index.html')
LEAF = os.path.join(HERE, 'node_modules', 'leaflet', 'dist') + '/'
DB = {}   # mock Firebase
LOG = []
errors = []

def getp(path):
    cur = DB
    for k in [p for p in path.split('/') if p]:
        if not isinstance(cur, dict) or k not in cur: return None
        cur = cur[k]
    return cur

def setp(path, val):
    ks = [p for p in path.split('/') if p]
    cur = DB
    for k in ks[:-1]:
        if not isinstance(cur.get(k), dict): cur[k] = {}
        cur = cur[k]
    if val is None: cur.pop(ks[-1], None)
    else: cur[ks[-1]] = val

def fbarr(v):
    # som rigtig Firebase: talnøgler -> array
    if isinstance(v, dict):
        v = {k: fbarr(x) for k, x in v.items()}
        if v and all(k.isdigit() for k in v) and len(v) > (max(map(int, v)) + 1) / 2:
            a = [None] * (max(map(int, v)) + 1)
            for k, x in v.items(): a[int(k)] = x
            return a
    return v

async def fb(route, req):
    m = re.search(r'firebasedatabase\.app/(.*?)\.json', req.url)
    from urllib.parse import unquote
    path = unquote(m.group(1))
    if not path.startswith('trustrup'):
        LOG.append('FORKERT STI: ' + path)
    path = path[len('trustrup'):]
    if req.method == 'GET':
        return await route.fulfill(status=200, content_type='application/json', body=json.dumps(fbarr(getp(path))))
    if req.method in ('PUT', 'PATCH', 'POST'):
        v = json.loads(req.post_data or 'null')
        if req.method == 'PATCH':
            cur = getp(path) or {}
            cur.update(v); v = cur
        setp(path, v)
    elif req.method == 'DELETE':
        setp(path, None)
    LOG.append(req.method + ' ' + (path or '/'))
    await route.fulfill(status=200, content_type='application/json', body='null')

async def handler(route):
    req = route.request; u = req.url
    if 'firebasedatabase' in u: return await fb(route, req)
    if u.startswith('https://app.test/'):
        import os
        name=u.split('?')[0].rsplit('/',1)[-1]
        fp=os.path.join(os.path.dirname(APP),name)
        if name and os.path.isfile(fp):
            ct={'js':'application/javascript','json':'application/json','png':'image/png','html':'text/html'}.get(name.rsplit('.',1)[-1],'text/plain')
            return await route.fulfill(path=fp, content_type=ct)
        return await route.fulfill(path=APP, content_type='text/html')
    if 'unpkg.com/leaflet' in u:
        f = u.split('/dist/')[-1].split('?')[0]
        return await route.fulfill(path=LEAF + f)
    if 'open-meteo' in u:
        return await route.fulfill(status=200, content_type='application/json', body=json.dumps({
            'current': {'temperature_2m': 8.5, 'windspeed_10m': 12, 'winddirection_10m': 240, 'weathercode': 3},
            'daily': {'sunrise': ['2026-10-24T08:05'], 'sunset': ['2026-10-24T17:50']},
            'hourly': {}}))
    return await route.abort()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True,
                                  geolocation={'latitude': 56.3466, 'longitude': 10.7802}, permissions=['geolocation'])
        pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errors.append('JS-FEJL: ' + str(e)))
        pg.on('console', lambda m: m.type == 'error' and 'ERR_FAILED' not in m.text and errors.append('CONSOLE: ' + m.text))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await ctx.route('**/*', handler)
        await pg.goto('https://app.test/trustrupjagt/')
        await pg.wait_for_timeout(2500)

        res = {}
        res['titel'] = await pg.title()
        res['login-navne'] = await pg.eval_on_selector_all('#login-user option', 'o=>o.map(x=>x.value).filter(Boolean)')

        # forkert kode
        await pg.select_option('#login-user', 'Jørgen')
        await pg.fill('#login-pass', 'forkert')
        await pg.evaluate('doLogin()'); await pg.wait_for_timeout(400)
        res['forkert-kode-afvist'] = await pg.eval_on_selector('#login-err', 'e=>e.textContent')

        # rigtig kode (testværdi)
        await pg.fill('#login-pass', 'trustrup')
        await pg.evaluate('doLogin()'); await pg.wait_for_timeout(800)
        res['logget-ind-som'] = await pg.evaluate('currentUser')

        # alle visninger
        views = ['hjem','kort','jagt','log','chat','vagt','kvoter','stat','vejr']
        res['visninger'] = {}
        for v in views:
            n = len(errors)
            await pg.evaluate(f"showView('{v}')"); await pg.wait_for_timeout(600)
            vis = await pg.evaluate(f"(()=>{{const e=document.getElementById('v-{v}');return e&&e.classList.contains('active')&&e.innerText.trim().length}})()")
            res['visninger'][v] = ('OK' if vis is not False and len(errors)==n else 'FEJL') + f' ({vis} tegn)'

        # kort
        res['kort-centrum'] = await pg.evaluate('map?map.getCenter():null')
        res['arealer-tegnet'] = await pg.evaluate('ag?ag.getLayers().length:0')
        res['tårne'] = await pg.evaluate('stands.length')

        # nedlagt vildt
        await pg.evaluate('openKillModal()'); await pg.wait_for_timeout(300)
        await pg.evaluate("""(()=>{const s=document.getElementById('k-animal');s.value=s.options[1]?s.options[1].value:'Råbuk';
          document.getElementById('k-weight').value='14';document.getElementById('k-note').value='Testbuk';})()""")
        await pg.evaluate('saveKill()'); await pg.wait_for_timeout(500)
        res['vildt-gemt'] = bool(DB.get('kills'))

        # jagt
        await pg.evaluate("document.getElementById('h-date').value='2026-11-08';document.getElementById('h-note').value='Testjagt'")
        await pg.evaluate('saveHunt()'); await pg.wait_for_timeout(500)
        res['jagt-gemt'] = bool(DB.get('hunts'))
        hid = list((DB.get('hunts') or {}).keys())
        if hid:
            await pg.evaluate(f"toggleSignup({json.dumps(hid[0]) if not hid[0].isdigit() else hid[0]})"); await pg.wait_for_timeout(400)
            res['tilmelding'] = json.dumps((DB['hunts'][hid[0]] or {}).get('signups'), ensure_ascii=False)

        # chat
        await pg.evaluate("showView('chat')"); await pg.wait_for_timeout(300)
        await pg.fill('#chat-input', 'Hej fra test')
        await pg.evaluate('sendChat()'); await pg.wait_for_timeout(500)
        res['chat-gemt'] = bool(DB.get('chat'))

        # vagtplan + kvote
        await pg.evaluate("openVagtModal&&openVagtModal()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.getElementById('vagt-date').value='2026-11-01';document.getElementById('vagt-note').value='Fodring'")
        await pg.evaluate('saveVagt()'); await pg.wait_for_timeout(400)
        res['vagt-gemt'] = bool(DB.get('vagtplan'))

        # tårn checkin
        await pg.evaluate('openCheckin(1)'); await pg.wait_for_timeout(300)
        await pg.evaluate('doCheckin()'); await pg.wait_for_timeout(400)
        res['tårn-booking'] = json.dumps((DB.get('stands') or {}).get('1', {}).get('booking'), ensure_ascii=False)

        # skift adgangskode
        await pg.evaluate("document.getElementById('cp-old').value='trustrup';document.getElementById('cp-new').value='ny1234';document.getElementById('cp-confirm').value='ny1234'")
        await pg.evaluate('doChangePass()'); await pg.wait_for_timeout(500)
        res['kode-skiftet'] = 'Jørgen' in (DB.get('members') or {})

        # admin: opret medlem, nulstil kode
        await pg.evaluate("openMemberModal&&openMemberModal()"); await pg.wait_for_timeout(200)
        await pg.evaluate("document.getElementById('mm-name').value='Testmand';document.getElementById('mm-pass').value='abcd';")
        await pg.evaluate('saveMember()'); await pg.wait_for_timeout(500)
        res['medlem-oprettet'] = list((DB.get('members') or {}).keys())

        # genindlæs: data bliver
        await pg.reload(); await pg.wait_for_timeout(2500)
        res['efter-genindlæs-bruger'] = await pg.evaluate('currentUser')
        res['efter-genindlæs-vildt'] = await pg.evaluate('kills.length')
        res['efter-genindlæs-jagter'] = await pg.evaluate('hunts.length')

        # admin: Simon
        await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(2500)
        res['admin-fane-skjult-for-ikke-logget'] = await pg.evaluate("getComputedStyle(document.getElementById('tab-admin')).display")
        res['medlemmer-i-db'] = list((DB.get('members') or {}).keys())
        await pg.screenshot(path='login.png')
        await b.close()

    print(json.dumps(res, ensure_ascii=False, indent=1))
    print('DB-skrivninger:', len(LOG), sorted(set(l.split('/')[0] + '/' + (l.split('/')[1] if '/' in l else '') for l in LOG))[:20])
    print('FEJL:', errors if errors else 'ingen')

asyncio.run(main())

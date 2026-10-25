import os, json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
SLUG = 'trustrupjagt' if 'trustrup' in os.path.abspath(APP) else 'dystrupjagt'
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['pwReset2026']=True
DB['members']={'Simon':{'hash':h,'admin':True},'Jens':{'hash':h,'admin':False}}
DB['hunts']={'h_1':{'id':'h_1','date':'2026-11-08','type':'Trykjagt','signups':['Simon']},'h_2':{'id':'h_2','date':'2026-11-21','type':'Drivjagt','signups':[]}}
async def login(pg,u):
    await pg.evaluate("localStorage.removeItem('"+('tj' if SLUG.startswith('t') else 'dj')+"_user')"); await pg.reload(); await pg.wait_for_timeout(2300)
    await pg.select_option('#login-user',u); await pg.fill('#login-pass','admin1'); await pg.evaluate('doLogin()'); await pg.wait_for_timeout(900)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e)))
        await ctx.route('**/*',handler)
        await pg.goto('https://app.test/'+SLUG+'/'); await pg.wait_for_timeout(2300)
        await login(pg,'Simon')
        await pg.tap('#tab-jagt'); await pg.wait_for_timeout(500)
        await pg.tap('#jagt-mine-btn'); await pg.wait_for_timeout(400)
        r={'mine-viser-tilmeldt':await pg.evaluate("document.getElementById('hunt-list').innerText.includes('FÆLLESJAGT')")}
        await pg.get_by_text('＋ Tilføj anden jagt').tap(); await pg.wait_for_timeout(300)
        await pg.fill('#pj-name','Svogers jagt Mols'); await pg.fill('#pj-date','2026-11-07'); await pg.fill('#pj-end','2026-11-08')
        await pg.evaluate('pjCheckWarn()')
        r['advarsel-i-formular']=await pg.evaluate("document.getElementById('pj-warn').innerText")
        await pg.locator('#pj-modal .btn-g').tap(); await pg.wait_for_timeout(500)
        r['liste']=await pg.evaluate("document.getElementById('hunt-list').innerText.replace(/\\s+/g,' ')")
        r['ikke-i-database']='Svogers' not in json.dumps(DB,ensure_ascii=False)
        await pg.tap('#jagt-liste-btn'); await pg.wait_for_timeout(300)
        r['fællesjagt-advarsel']=await pg.evaluate("document.getElementById('hunt-list').innerText.includes('Du har også')")
        await pg.tap('#jagt-kal-btn'); await pg.wait_for_timeout(300)
        r['kalender-forklaring']=await pg.evaluate("document.getElementById('hunt-list').innerText.includes('Overlap')")
        await pg.screenshot(path='privat_kalender.png')
        # tilmelding til dag med privat jagt -> bekræft
        await pg.evaluate("toggleSignup('h_1')"); await pg.wait_for_timeout(300)  # frameld (ingen spørgsmål)
        await pg.evaluate("toggleSignup('h_1')"); await pg.wait_for_timeout(300)
        r['spørger-ved-tilmelding']=await pg.evaluate("document.getElementById('confirm-modal').classList.contains('open')&&document.getElementById('confirm-text').textContent")
        await pg.tap('#confirm-ok'); await pg.wait_for_timeout(400)
        r['tilmeldt-efter-ja']='Simon' in (DB['hunts']['h_1'].get('signups') or [])
        await pg.tap('#tab-hjem'); await pg.wait_for_timeout(500)
        r['forside']=await pg.evaluate("(document.getElementById('hjem-content').innerText.match(/Din næste anden jagt[^\\n]*/)||[''])[0]")
        await pg.screenshot(path='privat_hjem.png')
        # anden bruger på samme telefon ser ikke Simons
        await login(pg,'Jens')
        await pg.tap('#tab-jagt'); await pg.wait_for_timeout(400); await pg.tap('#jagt-mine-btn'); await pg.wait_for_timeout(300)
        r['jens-ser-ikke-simons']=not await pg.evaluate("document.getElementById('hunt-list').innerText.includes('Svogers')")
        # ret og slet
        await login(pg,'Simon')
        pid=await pg.evaluate("getPrivate()[0].id")
        await pg.evaluate(f"openPrivate('{pid}')"); await pg.wait_for_timeout(300)
        await pg.locator('#pj-del').tap(); await pg.wait_for_timeout(300); await pg.tap('#confirm-ok'); await pg.wait_for_timeout(300)
        r['slettet']=await pg.evaluate("getPrivate().length")==0
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

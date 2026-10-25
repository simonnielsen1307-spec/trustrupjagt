import os
import json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['members']={'Simon':{'hash':h,'admin':True},'Jørgen':{'hash':h,'admin':False}}
DB['stands']={'1':{'id':1,'name':'Egetårnet','lat':56.3470,'lng':10.7805,'booking':None},'2':{'id':2,'name':'Mosen','lat':56.3500,'lng':10.7900,'booking':None}}
DB['nextStandId']=3
DB['kvoter']={'kv1':{'id':'kv1','animal':'Råbuk','antal':2,'saeson':'2026/2027'}}
DB['kills']={'1':{'id':1,'animal':'Råbuk','hunter':'Jørgen','date':'2026-10-01'},'2':{'id':2,'animal':'Råbuk','hunter':'Jørgen','date':'2025-10-01'}}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,
            geolocation={'latitude':56.3471,'longitude':10.7806},permissions=['geolocation','notifications'])
        pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e)+' | '+(e.stack or '')[:300]))
        pg.on('dialog',lambda d:asyncio.ensure_future(d.accept()))
        await ctx.route('**/*',handler)
        await pg.goto('https://app.test/trustrupjagt/'); await pg.wait_for_timeout(2500)
        await pg.select_option('#login-user','Simon'); await pg.fill('#login-pass','admin1')
        await pg.evaluate('doLogin()'); await pg.wait_for_timeout(1500)
        r={}
        r['tema-bg']=await pg.evaluate("getComputedStyle(document.body).backgroundColor")
        r['font']=await pg.evaluate("getComputedStyle(document.body).fontFamily")
        r['hurtigknapper']=await pg.eval_on_selector_all('.quick-btn','b=>b.map(x=>x.innerText.trim())')
        r['kvote-oversigt']=await pg.evaluate("(document.getElementById('hjem-content').innerText.match(/Råbuk\\s*\\d+ tilbage/)||[''])[0]")
        await pg.screenshot(path='hjem.png')
        await pg.evaluate("showView('kort')"); await pg.wait_for_timeout(1500)
        await pg.evaluate("showView('hjem')"); await pg.wait_for_timeout(500)
        await pg.evaluate('quickCheckin()'); await pg.wait_for_timeout(1500)
        r['quick-åbner']=await pg.evaluate("document.getElementById('checkin-modal').classList.contains('open')&&document.getElementById('ci-title').textContent")
        await pg.evaluate('doCheckin()'); await pg.wait_for_timeout(1500)
        r['booking']=DB['stands']['1'].get('booking') if isinstance(DB['stands'],dict) else None
        r['position-delt']=list((DB.get('positions') or {}).keys())
        # anden jæger i felten
        import time
        DB.setdefault('positions',{})['J%C3%B8rgen']={'user':'Jørgen','lat':56.35,'lng':10.79,'stand':'Mosen','ts':int(time.time()*1000)}
        # ny jagt & vildt fra andre -> besked
        DB['hunts']={'h_9':{'id':'h_9','date':'2026-11-08','type':'Trykjagt','createdBy':'Jørgen','signups':[]}}
        DB['kills']['3']={'id':3,'animal':'Råbuk','hunter':'Jørgen','date':'2026-10-20'}
        await pg.evaluate("notifyOn=()=>true; window.__n=[]; notify=(t,b)=>window.__n.push(t+': '+b+(t?'':' @'+new Error().stack.split(String.fromCharCode(10)).slice(1,4).join(' / ')));")
        await pg.evaluate("""(async()=>{const [hd,kd,pd]=await Promise.all(['hunts','kills','positions'].map(k=>fetch(FB+'/'+k+'.json').then(r=>r.json())));
          checkNews('hunts',hd);DB.hunts=hd;checkNews('kills',kd);DB.kills=kd;populateArrays();otherPos=pd||{};drawPositions();})()""")
        await pg.wait_for_timeout(800)
        r['beskeder']=await pg.evaluate('window.__n')
        r['andres-positioner-på-kort']=await pg.evaluate("Object.keys(posMarkers)")
        await pg.evaluate("showView('kvoter')"); await pg.wait_for_timeout(500)
        r['kvote-side']=await pg.evaluate("document.getElementById('kvote-list').innerText.replace(/\\s+/g,' ')")
        # tjek ud stopper deling
        await pg.evaluate('quickCheckin()'); await pg.wait_for_timeout(600)
        await pg.evaluate('doCheckin()'); await pg.wait_for_timeout(800)
        r['position-efter-tjek-ud']=list((DB.get('positions') or {}).keys())
        r['sw-registreret']=await pg.evaluate("navigator.serviceWorker.getRegistration().then(r=>!!r)")
        r['manifest+ikon']=await pg.evaluate("[!!document.querySelector('link[rel=manifest]'),!!document.querySelector('link[rel=apple-touch-icon]')]")
        await pg.evaluate("localStorage.removeItem('tj_user')"); await pg.reload(); await pg.wait_for_timeout(1300)
        await pg.screenshot(path='splash_login.png')
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

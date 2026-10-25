import os
import json, asyncio, hashlib, re
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])  # genbrug mock + handler
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['members']={'Simon':{'hash':h,'admin':True},'Jørgen':{'hash':h,'admin':False}}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        pg=await ctx.new_page()
        pg.on('pageerror',lambda e:errors.append(str(e)+' | '+(e.stack or '')[:400]))
        await ctx.route('**/*',handler)
        await pg.goto('https://app.test/trustrupjagt/'); await pg.wait_for_timeout(2500)
        r={}
        r['tårne-ved-start']=await pg.evaluate('stands.length')
        await pg.select_option('#login-user','Simon'); await pg.fill('#login-pass','admin1')
        await pg.evaluate('doLogin()'); await pg.wait_for_timeout(800)
        await pg.evaluate("showView('kort')"); await pg.wait_for_timeout(800)
        r['arealer-ved-start']=await pg.evaluate('ag.getLayers().length')
        r['nord/syd-knapper-væk']=await pg.evaluate("!document.body.innerHTML.includes(\"startAreaEdit('nord')\")")
        # nyt tårn
        await pg.evaluate("openAddStand()"); await pg.fill('#as-name','Egetårnet')
        await pg.evaluate('saveNewStand()'); await pg.wait_for_timeout(800)
        box=await pg.eval_on_selector('#map','e=>{const r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]}')
        await pg.mouse.click(box[0],box[1]); await pg.wait_for_timeout(600)
        r['tårn-placeret']=DB.get('stands',{}).get('1')
        # nyt areal via UI
        await pg.evaluate('startDrawNewArea()'); await pg.wait_for_timeout(300)
        await pg.fill('#new-area-inp','Vesterskov')
        btn=await pg.query_selector('#new-area-overlay button:has-text("Tegn")') or await pg.query_selector('#new-area-overlay button:last-child')
        r['knap']=await btn.inner_text(); await btn.click(); await pg.wait_for_timeout(600)
        for dx,dy in [(-80,-80),(80,-80),(80,80),(-80,80)]:
            await pg.mouse.click(box[0]+dx,box[1]+dy); await pg.wait_for_timeout(250)
        r['punkter-under-tegning']=await pg.evaluate('newAreaPoints.length')
        await pg.evaluate('saveAreaEdit()'); await pg.wait_for_timeout(600)
        a=list((DB.get('extraAreas') or {}).values())
        r['areal-gemt']=a and (a[0]['name'],len(a[0]['points']))
        r['arealer-på-kort']=await pg.evaluate('ag.getLayers().length')
        await pg.screenshot(path='kort.png')
        # ikke-admin kan ikke tegne
        await pg.reload(); await pg.wait_for_timeout(2500)
        r['efter-genindlæs-tårne']=await pg.evaluate('stands.filter(s=>s.lat).length')
        r['efter-genindlæs-arealer']=await pg.evaluate('Object.keys(extraAreas).length')
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

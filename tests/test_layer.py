import os
import json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['members']={'Simon':{'hash':h,'admin':True}}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e)))
        await ctx.route('**/*',handler)
        await pg.goto('https://app.test/trustrupjagt/'); await pg.wait_for_timeout(2500)
        await pg.select_option('#login-user','Simon'); await pg.fill('#login-pass','admin1')
        await pg.evaluate('doLogin()'); await pg.wait_for_timeout(800)
        await pg.evaluate("showView('kort')"); await pg.wait_for_timeout(800)
        await pg.evaluate("toggleLP()"); await pg.wait_for_timeout(200)
        r={'valgmuligheder':await pg.eval_on_selector_all('#base-layers label','l=>l.map(x=>x.innerText.trim())')}
        urls={}
        for k in ['sat','hybrid','topo','terraen','lys','moerk','vej']:
            await pg.click('#bl-'+k); await pg.wait_for_timeout(250)
            urls[k]=await pg.evaluate("Object.values(map._layers).filter(l=>l._url).map(l=>l._url.split('/')[2]+(l._url.includes('Reference')?'+ref':'')).join(',')")
        r['lag-pr-valg']=urls
        await pg.click('#bl-sat'); await pg.reload(); await pg.wait_for_timeout(2500)
        await pg.evaluate("showView('kort')"); await pg.wait_for_timeout(800)
        r['husket-efter-genindlæs']=await pg.evaluate('aktivBase')
        r['areal+gps-tilvalg-findes']=await pg.evaluate("!!document.getElementById('c4')&&!!document.getElementById('c5')")
        await pg.evaluate("toggleLP()"); await pg.wait_for_timeout(200)
        await pg.screenshot(path='lag.png'); await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

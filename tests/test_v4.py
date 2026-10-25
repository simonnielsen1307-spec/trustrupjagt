import os, json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
SLUG='trustrupjagt' if 'trustrup' in os.path.abspath(APP) else 'dystrupjagt'
PFX='tj' if SLUG.startswith('t') else 'dj'
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['pwReset2026']=True; DB['cleanedDefaults']=True
DB['members']={'Simon':{'hash':h,'admin':True},'Jón':{'hash':h,'admin':False}}
DB['hunts']={'h_1':{'id':'h_1','date':'2026-12-12','type':'Drivjagt','signups':[]}}
async def page(b,u):
    ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e))); await ctx.route('**/*',handler)
    await pg.goto('https://app.test/'+SLUG+'/'); await pg.wait_for_timeout(2300)
    await pg.select_option('#login-user',u); await pg.fill('#login-pass','admin1'); await pg.evaluate('doLogin()'); await pg.wait_for_timeout(1000)
    await pg.tap('#tab-jagt'); await pg.wait_for_timeout(500)
    return pg
async def main():
    r={}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        A=await page(b,'Simon'); B=await page(b,'Jón')
        await A.locator('#hunt-list').get_by_text('✓ Kommer').first.tap(); await A.wait_for_timeout(500)
        await A.locator('#hunt-list').get_by_text('Gæster & hunde').first.tap(); await A.wait_for_timeout(300)
        await A.fill('#gd-gname','Peter Hansen'); await A.locator('#gd-modal .gd-add button').first.tap()
        await A.fill('#gd-gname','Ole'); await A.locator('#gd-modal .gd-add button').first.tap()
        await A.fill('#gd-dname','Bella'); await A.select_option('#gd-dtype','Apportør'); await A.locator('#gd-modal .gd-add button').nth(1).tap()
        await A.fill('#gd-note','Kommer kl. 8')
        await A.locator('#gd-modal .btn-g').tap(); await A.wait_for_timeout(600)
        r['simon-extra-i-db']=DB['hunts']['h_1'].get('extra',{}).get('Simon')
        # Jón gemmer hund uden først at tilmelde sig (bliver tilmeldt), skriver navn uden at trykke tilføj
        await B.evaluate("openGuestsDogs('h_1')"); await B.wait_for_timeout(300)
        await B.fill('#gd-dname','Rex'); await B.select_option('#gd-dtype','Schweisshund')
        await B.locator('#gd-modal .btn-g').tap(); await B.wait_for_timeout(600)
        r['begge-gemt']=sorted(DB['hunts']['h_1'].get('extra',{}).keys())
        r['jón-tilmeldt']='Jón' in DB['hunts']['h_1']['signups']
        await A.wait_for_timeout(31000)
        r['simon-ser']=await A.evaluate("document.getElementById('hunt-list').textContent.replace(/\\s+/g,' ')")
        await A.screenshot(path='v4_jagt.png')
        r['forside']=await A.evaluate("(showView('hjem'),(document.getElementById('hjem-content').textContent.match(/👥[^<]*?hunde/)||[''])[0])")
        # frameld fjerner også gæster/hunde
        await B.evaluate("toggleSignup('h_1')"); await B.wait_for_timeout(500)
        r['efter-framelding']=sorted(DB['hunts']['h_1'].get('extra',{}).keys())
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

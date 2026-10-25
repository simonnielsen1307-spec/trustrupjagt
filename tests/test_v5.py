import os, json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
SLUG='trustrupjagt' if 'trustrup' in os.path.abspath(APP) else 'dystrupjagt'
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['pwReset2026']=True; DB['cleanedDefaults']=True
DB['members']={'Simon':{'hash':h,'admin':True},'Jón':{'hash':h,'admin':False},'Allan':{'hash':h,'admin':False},'Jørgen':{'hash':h,'admin':False}}
DB['stands']={'1':{'id':1,'name':'Egetårnet','lat':56.40,'lng':10.70,'booking':None}}; DB['nextStandId']=2
DB['hunts']={'h_1':{'id':'h_1','date':'2026-12-12','type':'Drivjagt','signups':[]}}
async def page(b,u):
    ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e))); await ctx.route('**/*',handler)
    await pg.goto('https://app.test/'+SLUG+'/'); await pg.wait_for_timeout(2300)
    await pg.select_option('#login-user',u); await pg.fill('#login-pass','admin1'); await pg.evaluate('doLogin()'); await pg.wait_for_timeout(1000)
    return pg
async def main():
    r={}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        A=await page(b,'Simon'); B=await page(b,'Jón')
        # 1 låste tårne
        for nm,pg in [('admin',A),('jón',B)]:
            await pg.tap('#tab-kort'); await pg.wait_for_timeout(1200)
            r[nm+'-kan-trække']=await pg.evaluate("stands[0].marker.dragging.enabled()")
            await pg.tap('#tab-Tårne'); await pg.wait_for_timeout(300)
            r[nm+'-ser-tilføj']=await pg.evaluate("getComputedStyle(document.querySelector('#v-Tårne .btn-add')).display!=='none'")
            r[nm+'-ser-flyt-knap']=await pg.evaluate("document.getElementById('Tårne-list').innerHTML.includes('placeTorn(')")
        await B.evaluate("placeTorn(1)"); await B.wait_for_timeout(200)
        r['jón-placeTorn-blokeret']=await B.evaluate("placingStand===null")
        # 2 svar
        await B.tap('#tab-jagt'); await B.wait_for_timeout(400)
        await B.locator('#hunt-list').get_by_text('✗ Kan ikke').first.tap(); await B.wait_for_timeout(600)
        await A.tap('#tab-jagt'); await A.wait_for_timeout(400)
        await A.locator('#hunt-list').get_by_text('✓ Kommer').first.tap(); await A.wait_for_timeout(600)
        r['db']={'signups':DB['hunts']['h_1'].get('signups'),'declines':DB['hunts']['h_1'].get('declines')}
        # 3 samlet graf på forsiden
        await A.wait_for_timeout(31000)
        await A.tap('#tab-hjem'); await A.wait_for_timeout(500)
        r['graf']=await A.evaluate("(()=>{const c=document.querySelector('#hjem-content .rsvp-cols');return c?c.textContent.replace(/\\s+/g,' '):null})()")
        r['graf-tekst']=await A.evaluate("document.querySelector('#hjem-content .rsvp-legend').textContent")
        await A.evaluate("document.querySelector('#hjem-content .rsvp').scrollIntoView({block:'start'})"); await A.wait_for_timeout(200); await A.screenshot(path='v5_hjem.png')
        # Jón ombestemmer sig
        await B.tap('#tab-jagt'); await B.wait_for_timeout(300); await B.locator('#hunt-list').get_by_text('✓ Kommer alligevel').first.tap(); await B.wait_for_timeout(600)
        r['efter-ombestemt']={'signups':DB['hunts']['h_1'].get('signups'),'declines':DB['hunts']['h_1'].get('declines')}
        await B.screenshot(path='v5_jagt.png')
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

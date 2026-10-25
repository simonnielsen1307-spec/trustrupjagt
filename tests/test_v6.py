import os, json, asyncio, hashlib, time
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
SLUG='trustrupjagt' if 'trustrup' in os.path.abspath(APP) else 'dystrupjagt'
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['pwReset2026']=True; DB['cleanedDefaults']=True
DB['members']={'Simon':{'hash':h,'admin':True},'Jón':{'hash':h,'admin':False},'Allan':{'hash':h,'admin':False}}
DB['stands']={'1':{'id':1,'name':'Egetårnet','lat':56.40,'lng':10.70,'booking':None}}; DB['nextStandId']=2
y=time.strftime('%Y')
DB['hunts']={'h_1':{'id':'h_1','date':y+'-01-10','type':'Drivjagt','signups':['Simon','Jón'],'extra':{'Jón':{'guests':[{'name':'P. Hansen'}],'dogs':[]}}},
             'h_2':{'id':'h_2','date':'2099-12-12','type':'Trykjagt','signups':['Jón']}}
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
        A=await page(b,'Simon'); B=await page(b,'Jón'); C=await page(b,'Allan')
        # jagttid-kort er kompakt
        r['jagttid-kort-højde']=await A.evaluate("document.querySelector('.jt-mini').getBoundingClientRect().height")
        # tårnmærke-størrelse
        await A.tap('#tab-kort'); await A.wait_for_timeout(1200)
        r['tårnmærke-px']=await A.evaluate("(()=>{const e=document.querySelector('.tm').getBoundingClientRect();return [Math.round(e.width),Math.round(e.height)]})()")
        # Jón skriver resultat for sig selv og sin gæst
        await B.tap('#tab-jagt'); await B.wait_for_timeout(400)
        await B.locator('#hunt-list').get_by_text('Skriv resultat').first.tap(); await B.wait_for_timeout(300)
        r['jón-kan-vælge']=await B.evaluate("[...document.querySelectorAll('#res-who option')].map(o=>o.value)")
        await B.fill('#res-shots','4'); await B.select_option('#res-animal','Råbuk'); await B.locator('#res-modal .gd-add button').tap()
        await B.select_option('#res-animal','Ræv'); await B.locator('#res-modal .gd-add button').tap()
        await B.locator('#res-modal .btn-g').tap(); await B.wait_for_timeout(500)
        await B.locator('#hunt-list').get_by_text('Skriv resultat').first.tap(); await B.wait_for_timeout(300)
        await B.select_option('#res-who','P. Hansen (gæst)'); await B.fill('#res-shots','3'); await B.locator('#res-modal .btn-g').tap(); await B.wait_for_timeout(500)
        # admin skriver for Simon
        await A.tap('#tab-jagt'); await A.wait_for_timeout(400)
        await A.evaluate("openResult('h_1')"); await A.wait_for_timeout(300)
        r['admin-kan-vælge']=await A.evaluate("[...document.querySelectorAll('#res-who option')].map(o=>o.value)")
        await A.fill('#res-shots','2'); await A.select_option('#res-animal','Fasan'); await A.fill('#res-count','2'); await A.locator('#res-modal .gd-add button').tap()
        await A.locator('#res-modal .btn-g').tap(); await A.wait_for_timeout(500)
        r['db']=DB['hunts']['h_1'].get('result')
        r['allan-ikke-tilmeldt-kan-ikke-skrive']=await C.evaluate("(showView('jagt'),!document.getElementById('hunt-list').textContent.includes('Skriv resultat'))")
        r['fremtidig-jagt-ingen-resultatknap']=await B.evaluate("!canReport(hunts.find(x=>x.id==='h_2'))")
        await A.wait_for_timeout(31000)
        await A.evaluate("showView('jagt')"); await A.wait_for_timeout(300)
        r['jagtkort']=await A.evaluate("document.querySelector('#hunt-list .card .res-sum').textContent")
        await A.screenshot(path='v6_jagt.png')
        await A.evaluate("showView('stat');setStatYear(0)"); await A.wait_for_timeout(400)
        r['statistik']=await A.evaluate("document.getElementById('stat-content').textContent.replace(/\\s+/g,' ').slice(0,400)")
        await A.screenshot(path='v6_stat.png')
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

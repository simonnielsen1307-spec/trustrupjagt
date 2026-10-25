import os
import json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['members']={'Simon':{'hash':h,'admin':True}}
DB['stands']={str(i):{'id':i,'name':'Torn %d'%i,'lat':None,'lng':None,'booking':None} for i in range(1,11)}
DB['stands']['11']={'id':11,'name':'Egetårnet','lat':56.347,'lng':10.7805,'booking':None}
DB['nextStandId']=12
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        await ctx.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=':root{--sat:47px!important;--sab:34px!important}';document.head.appendChild(s);});")
        pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e)))
        await ctx.route('**/*',handler)
        await pg.goto('https://app.test/trustrupjagt/'); await pg.wait_for_timeout(500)
        # gammel cache fra tidligere database
        await pg.evaluate("""localStorage.setItem('tj_user','Simon');localStorage.setItem('tj_cache',JSON.stringify({stands:{1:{id:1,name:'Torn 1'}},members:{Simon:{hash:'%s',admin:true}},ts:Date.now()}))"""%h)
        await pg.reload(); await pg.wait_for_timeout(2500)
        r={'tårne-efter-oprydning':await pg.evaluate("stands.map(s=>s.name)"),'tårne-i-db':[v['name'] for v in (DB['stands'].values() if isinstance(DB['stands'],dict) else DB['stands']) if v]}
        await pg.tap('#tab-kort'); await pg.wait_for_timeout(1200)
        await pg.tap('#lp-h'); await pg.wait_for_timeout(300)
        await pg.screenshot(path='a1.png')
        await pg.get_by_text('＋ Nyt areal').tap(); await pg.wait_for_timeout(300)
        await pg.fill('#new-area-inp','Vesterskov')
        await pg.get_by_text('Start tegning').tap(); await pg.wait_for_timeout(800)
        box=await pg.eval_on_selector('#map','e=>{const r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]}')
        for dx,dy in [(-90,-90),(90,-90),(90,90),(-90,90)]:
            await pg.touchscreen.tap(box[0]+dx,box[1]+dy); await pg.wait_for_timeout(350)
        r['punkter']=await pg.evaluate('newAreaPoints.length')
        await pg.screenshot(path='a2.png')
        gem=pg.locator('#area-bar button', has_text='Gem')
        r['gem-knap-synlig']=await gem.is_visible()
        await gem.tap(); await pg.wait_for_timeout(800)
        r['areal-i-db']=[(a['name'],len(a['points'])) for a in (DB.get('extraAreas') or {}).values()]
        # redigér arealet og gem
        aid=list((DB.get('extraAreas') or {}).keys())
        if aid:
            await pg.evaluate(f"startAreaEdit('{aid[0]}')"); await pg.wait_for_timeout(500)
            await pg.locator('#area-bar button', has_text='Punkt').tap(); await pg.wait_for_timeout(300)
            await gem.tap(); await pg.wait_for_timeout(600)
            r['efter-redigering-punkter']=len(DB['extraAreas'][aid[0]]['points'])
        await pg.screenshot(path='a3.png')
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

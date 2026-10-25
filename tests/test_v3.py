import os, json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
SLUG='trustrupjagt' if 'trustrup' in os.path.abspath(APP) else 'dystrupjagt'
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['pwReset2026']=True; DB['cleanedDefaults']=True
DB['members']={'Simon':{'hash':h,'admin':True},'Jens':{'hash':h,'admin':False}}
DB['stands']={'1':{'id':1,'name':'Egetårnet','lat':56.40,'lng':10.70,'booking':None}}; DB['nextStandId']=2
DB['extraAreas']={'a%d'%i:{'name':'Areal %d'%i,'color':'#4a90d9','points':[{'lat':56.39+i*.001,'lng':10.69},{'lat':56.391+i*.001,'lng':10.69},{'lat':56.391+i*.001,'lng':10.691}]} for i in range(3)}
async def main():
    r={}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for w,hh in [(390,844),(320,568)]:
            ctx=await b.new_context(viewport={'width':w,'height':hh},is_mobile=True,has_touch=True)
            await ctx.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=':root{--sat:47px!important;--sab:34px!important}';document.head.appendChild(s);});")
            pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e))); await ctx.route('**/*',handler)
            await pg.goto('https://app.test/'+SLUG+'/'); await pg.wait_for_timeout(2300)
            await pg.select_option('#login-user','Simon'); await pg.fill('#login-pass','admin1'); await pg.evaluate('doLogin()'); await pg.wait_for_timeout(1000)
            await pg.tap('#tab-kort'); await pg.wait_for_timeout(1200); await pg.tap('#lp-h'); await pg.wait_for_timeout(300)
            # rul panelet med fingeren
            box=await pg.eval_on_selector('#lp','e=>{const r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height*0.7]}')
            cdp=await ctx.new_cdp_session(pg)
            x,y=int(box[0]),int(box[1])
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
            for k in range(1,16):
                await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-k*14}]}); await pg.wait_for_timeout(16)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
            for k in range(1,16):
                await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-k*14}]}); await pg.wait_for_timeout(16)
            await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
            await pg.wait_for_timeout(600)
            touch_st=await pg.evaluate("document.getElementById('lp').scrollTop")
            await pg.wait_for_timeout(1200)
            st=await pg.evaluate("(()=>{const l=document.getElementById('lp');return l.scrollHeight>l.clientHeight?'kan rulle':'passer'})()")
            vis=await pg.evaluate("(()=>{const b=document.getElementById('off-btn').getBoundingClientRect();const t=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);return t&&(t.id==='off-btn'||t.closest('#off-btn')!==null)})()")
            r['%dx%d'%(w,hh)]={'rullet-med-finger':touch_st,'panel-rullet':st,'gem-knap-kan-trykkes':vis,'kort-flyttet-ikke':await pg.evaluate("Math.abs(map.getCenter().lat-56.448)<1")}
            await pg.screenshot(path='v3_lp_%d.png'%w)
            # skudretning fra tårnet
            if w==390:
                await pg.evaluate("openCheckin(1)"); await pg.wait_for_timeout(300)
                r['retning-felt-for-admin']=await pg.evaluate("document.getElementById('ci-dir-wrap').style.display!=='none'")
                await pg.select_option('#ci-dir','225'); await pg.wait_for_timeout(500)
                r['retning-gemt']=DB['stands']['1'].get('dir')
            await ctx.close()
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

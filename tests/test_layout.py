import os
import json, asyncio, hashlib
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['members']={'Simon':{'hash':h,'admin':True}}
DB['stands']={'5':{'id':5,'name':'Egetårnet','lat':56.3470,'lng':10.7805,'booking':None}}
CHECK="""(()=>{const bad=[];const vw=innerWidth,vh=innerHeight,top=47,bot=34;
 document.querySelectorAll('button,a,input,select,.nav-tab,[onclick]').forEach(e=>{
  const r=e.getBoundingClientRect(); if(!r.width||!r.height) return;
  const st=getComputedStyle(e); if(st.visibility==='hidden'||st.display==='none') return;
  if(e.closest('.overlay:not(.open)')||e.closest('#more-menu')&&getComputedStyle(document.getElementById('more-menu')).display==='none') return;
  if(e.closest('.view:not(.active)')||e.closest('#login-screen.hidden')||e.closest('#app.hidden')) return;
  const cx=r.left+r.width/2, cy=r.top+r.height/2;
  if(cy<0||cy>vh) return;
  let p=e.parentElement,clipped=false;
  while(p&&p!==document.body){const ps=getComputedStyle(p);if(/(auto|scroll|hidden)/.test(ps.overflowY+ps.overflowX)){const pr=p.getBoundingClientRect();if(cy<pr.top||cy>pr.bottom||cx<pr.left||cx>pr.right){clipped=true;break;}}p=p.parentElement;}
  if(clipped) return; // rullet ud af sin liste = kan rulles frem
  let why='';
  if(cy<top) why='under statuslinje';
  else if(cy>vh-bot) why='under hjem-bjælke';
  else if(r.left<-1||r.right>vw+1) why='uden for skærm vandret';
  else { const t=document.elementFromPoint(cx,cy); if(t&&t!==e&&!e.contains(t)&&!t.contains(e)) why='dækket af '+(t.id||t.className||t.tagName); }
  if(why) bad.push((e.id||e.textContent.trim().slice(0,18)||e.tagName)+': '+why);
 });return bad;})()"""
async def run(b,w,hgt,label):
    ctx=await b.new_context(viewport={'width':w,'height':hgt},is_mobile=True,has_touch=True)
    await ctx.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=':root{--sat:47px!important;--sab:34px!important}';document.head.appendChild(s);});")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e)))
    await ctx.route('**/*',handler)
    await pg.goto('https://app.test/trustrupjagt/'); await pg.wait_for_timeout(2300)
    res={'login':await pg.evaluate(CHECK)}
    await pg.select_option('#login-user','Simon'); await pg.fill('#login-pass','admin1')
    await pg.evaluate('doLogin()'); await pg.wait_for_timeout(1200)
    for v in ['hjem','kort','Tårne','log','jagt','chat']:
        await pg.evaluate(f"showView('{v}')"); await pg.wait_for_timeout(700)
        if v=='kort': await pg.evaluate("toggleLP()"); await pg.wait_for_timeout(200)
        res[v]=await pg.evaluate(CHECK)
        await pg.screenshot(path=f'lay_{label}_{v}.png')
        if v=='kort':
            res['kort-header-synlig']=await pg.evaluate("(()=>{const h=document.querySelector('#app header').getBoundingClientRect();const m=document.getElementById('map').getBoundingClientRect();return h.bottom<=m.top+1})()")
            await pg.evaluate("toggleLP()")
    await pg.evaluate("toggleMore&&toggleMore()"); await pg.wait_for_timeout(400)
    res['mere-menu']=await pg.evaluate(CHECK); await pg.screenshot(path=f'lay_{label}_mere.png')
    await ctx.close(); return res
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); out={}
        for w,hh,l in [(390,844,'iphone14'),(320,568,'lille'),(430,932,'stor')]:
            out[l]=await run(b,w,hh,l)
        await b.close()
    print(json.dumps(out,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

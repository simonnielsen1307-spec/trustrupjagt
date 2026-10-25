import os, json, asyncio, hashlib, time, base64
from playwright.async_api import async_playwright
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'test_basis.py')).read().split('async def main')[0])
SLUG = 'trustrupjagt' if 'trustrup' in os.path.abspath(APP) else 'dystrupjagt'
PFX = 'tj' if SLUG.startswith('t') else 'dj'
h=hashlib.sha256(('admin1'+'dystrup-jagt-salt-2024').encode()).hexdigest()
DB['pwReset2026']=True; DB['cleanedDefaults']=True
DB['members']={'Simon':{'hash':h,'admin':True},'Jens':{'hash':h,'admin':False}}
DB['stands']={'1':{'id':1,'name':'Egetårnet','lat':56.40,'lng':10.70,'dir':0,'booking':None},   # skyder mod nord
              '2':{'id':2,'name':'Mosen','lat':56.401,'lng':10.701,'dir':180,'booking':None}}    # skyder mod syd
DB['nextStandId']=3
DB['extraAreas']={'a1':{'name':'Skov','color':'#4a90d9','points':[{'lat':56.399,'lng':10.699},{'lat':56.402,'lng':10.699},{'lat':56.402,'lng':10.703},{'lat':56.399,'lng':10.703}]}}
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
TILES=[0]
async def handler2(route):
    u=route.request.url
    if 'open-meteo' in u:
        hrs=[time.strftime('%Y-%m-%dT%H:00',time.localtime(time.time()+i*3600)) for i in range(-12,36)]
        return await route.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps({
          'current':{'temperature_2m':8,'windspeed_10m':12,'winddirection_10m':0,'weathercode':3,'wind_direction_10m':0,'wind_speed_10m':4.5},  # vind FRA nord
          'daily':{'sunrise':['2026-10-25T07:05'],'sunset':['2026-10-25T16:50']},
          'hourly':{'time':hrs,'wind_direction_10m':[0]*len(hrs),'wind_speed_10m':[4.5]*len(hrs)}}))
    if 'tile.openstreetmap' in u or 'arcgisonline' in u:
        TILES[0]+=1
        return await route.fulfill(status=200,content_type='image/png',headers={'Access-Control-Allow-Origin':'*'},body=PNG)
    return await handler(route)
async def login(pg,u):
    await pg.evaluate("localStorage.removeItem('"+PFX+"_user')"); await pg.reload(); await pg.wait_for_timeout(2300)
    await pg.select_option('#login-user',u); await pg.fill('#login-pass','admin1'); await pg.evaluate('doLogin()'); await pg.wait_for_timeout(1500)
async def newpage(b):
    ctx=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,geolocation={'latitude':56.4005,'longitude':10.7005},permissions=['geolocation'])
    pg=await ctx.new_page(); pg.on('pageerror',lambda e:errors.append(str(e)))
    await ctx.route('**/*',handler2)
    await pg.goto('https://app.test/'+SLUG+'/'); await pg.wait_for_timeout(1500)
    return ctx,pg
async def main():
    r={}
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctxA,A=await newpage(b); ctxB,B=await newpage(b)
        await login(A,'Simon'); await login(B,'Jens')
        await A.evaluate("refreshWind(true)"); await A.wait_for_timeout(800)
        # 1 vind: fra nord -> duft mod syd. Egetårnet (skyder N) = god, Mosen (skyder S) = dårlig
        r['vind-egetårn']=await A.evaluate("standWind(stands.find(s=>s.id===1)).c")
        r['vind-mosen']=await A.evaluate("standWind(stands.find(s=>s.id===2)).c")
        r['forside-vindkort']=await A.evaluate("document.getElementById('hjem-content').textContent.includes('Vind ved tårnene')")
        await A.tap('#tab-Tårne'); await A.wait_for_timeout(400)
        r['tårnliste-viser-retning']=await A.evaluate("document.getElementById('Tårne-list').innerText.includes('Skyder mod N')")
        # sæt retning via redigering
        await A.evaluate("openTårneEdit(2)"); await A.wait_for_timeout(200)
        await A.select_option('#te-dir','0'); await A.evaluate("saveTårnedit()"); await A.wait_for_timeout(500)
        r['retning-gemt-i-db']=DB['stands']['2'].get('dir')
        await A.evaluate("openCheckin(2)"); await A.evaluate("doCheckin()"); await A.wait_for_timeout(500)
        r['retning-bevaret-efter-tjek-ind']=DB['stands']['2'].get('dir')
        await A.tap('#tab-kort'); await A.wait_for_timeout(1500)
        r['skudsektorer-på-kort']=await A.evaluate("sectorLayer.getLayers().length")
        # 2 jagttider
        r['jagttid-forside']=await A.evaluate("(showView('hjem'),document.getElementById('hjem-content').textContent.includes('Jagttid i dag'))")
        r['råbuk-15-07']=await A.evaluate("jtOpen('Råbuk','2026-07-15')"); r['råbuk-16-07']=await A.evaluate("jtOpen('Råbuk','2026-07-16')")
        r['hare-10-01']=await A.evaluate("jtOpen('Hare','2027-01-10')"); r['hare-20-01']=await A.evaluate("jtOpen('Hare','2027-01-20')")
        r['kronkalv-29-02']=await A.evaluate("jtOpen('Kronkalv','2028-02-29')")
        await A.evaluate("showView('jagttider')"); await A.wait_for_timeout(300)
        r['jagttid-side-arter']=await A.evaluate("document.querySelectorAll('#jagttid-list .card').length")
        # vildt uden for jagttid -> spørger, afvis = ikke gemt
        A.once('dialog',lambda d:asyncio.ensure_future(d.dismiss()))
        await A.evaluate("openKillModal()"); await A.wait_for_timeout(200)
        await A.evaluate("document.getElementById('k-animal').value='Hare';document.getElementById('k-date').value='2026-08-10'")
        n0=len(DB.get('kills') or {}); await A.evaluate("saveKill()"); await A.wait_for_timeout(500)
        r['hare-august-afvist']=len(DB.get('kills') or {})==n0
        await A.evaluate("closeModal('kill-modal')")
        # 3 offline-kort
        await A.evaluate("showView('kort')"); await A.wait_for_timeout(500)
        await A.evaluate("saveOfflineMap()"); await A.wait_for_timeout(6000)
        r['offline-felter-i-cache']=await A.evaluate("caches.open('tiles-v1').then(c=>c.keys()).then(k=>k.length)")
        r['offline-status']=await A.evaluate("document.getElementById('off-status').textContent")
        # 4 SOS: Jens sender, Simon får banner
        await B.evaluate("sosPress()"); await B.wait_for_timeout(300); await B.tap('#confirm-ok'); await B.wait_for_timeout(1500)
        r['alarm-i-db']=[(a['user'],a['active'],bool(a['lat'])) for a in (DB.get('alerts') or {}).values()]
        await A.wait_for_timeout(7000)
        r['simon-ser-banner']=await A.evaluate("document.getElementById('sos-banner').style.display!=='none'&&document.getElementById('sos-banner').innerText.split('\\n')[0]")
        r['alarm-på-kort']=await A.evaluate("Object.keys(alertMarkers).length")
        await B.evaluate("stopSOS(myAlertId)"); await B.wait_for_timeout(600)
        await A.wait_for_timeout(7000)
        r['banner-væk-efter-stop']=await A.evaluate("document.getElementById('sos-banner').style.display==='none'")
        # 7 foder
        await B.evaluate("openFeeder()"); await B.fill('#fd-name','Majsfoder'); await B.fill('#fd-every','3')
        await B.evaluate("saveFeeder()"); await B.wait_for_timeout(1500)
        box=await B.eval_on_selector('#map','e=>{const r=e.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]}')
        await B.touchscreen.tap(box[0]+40,box[1]); await B.wait_for_timeout(700)
        f=list((DB.get('feeders') or {}).values())
        r['foder-placeret']=bool(f and f[0].get('lat'))
        r['foder-skal-tilses']=await B.evaluate("(showView('hjem'),document.getElementById('hjem-content').textContent.includes('Skal tilses'))")
        await B.evaluate(f"feederDone('{f[0]['id']}')"); await B.wait_for_timeout(500)
        r['foder-fodret']=(DB['feeders'][f[0]['id']].get('last'),DB['feeders'][f[0]['id']].get('lastBy'))
        await A.wait_for_timeout(31000)
        r['simon-ser-foder-på-kort']=await A.evaluate("Object.keys(feederMarkers).length")
        await A.evaluate("showView('foder')"); await A.wait_for_timeout(300)
        r['foder-liste']=await A.evaluate("document.getElementById('foder-list').innerText.replace(/\\s+/g,' ')")
        await A.screenshot(path='v2_foder.png'); await A.evaluate("showView('hjem')"); await A.wait_for_timeout(400); await A.screenshot(path='v2_hjem.png',full_page=True)
        await b.close()
    print(json.dumps(r,ensure_ascii=False,indent=1)); print('FEJL:',errors or 'ingen')
asyncio.run(main())

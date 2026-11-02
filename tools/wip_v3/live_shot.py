# usage: serve site/ on :8765 (python3 -m http.server 8765 in site/), three@0.160.0 in /tmp/viewer (npm i), then python3 live_shot.py OUT.png TAB(1 wide band,2 band,3 solitaire); env DSF=2 CLIP=x,y,w,h for a zoom
import asyncio,sys,subprocess,os
from playwright.async_api import async_playwright
OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp/live.png'
TAB=sys.argv[2] if len(sys.argv)>2 else '1'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--use-angle=swiftshader'])
        pg=await b.new_page(viewport={'width':1200,'height':600},device_scale_factor=int(os.environ.get('DSF',1)))
        async def route(r):
            u=r.request.url
            if 'cdn.jsdelivr.net/npm/three@0.160.0/' in u:
                f='/tmp/viewer/node_modules/three/'+u.split('three@0.160.0/')[1].split('?')[0]
                await r.fulfill(path=f,content_type='application/javascript')
            elif u.endswith('/index.html'):   # expose camera/controls for the shot (the page itself no longer defines __ctl/__cam)
                resp=await r.fetch(); body=(await resp.text()).replace('controls.enableDamping = true;','window.__ctl=controls; window.__cam=camera; controls.enableDamping = true;',1)
                await r.fulfill(response=resp,body=body)
            else: await r.continue_()
        await pg.route('**/*',route)
        pg.on('console',lambda m:print('console',m.type,m.text[:200]))
        pg.on('pageerror',lambda e:print('pageerror',str(e)[:200]))
        pg.on('requestfailed',lambda r:print('reqfail',r.url[:120]))
        await pg.goto('http://localhost:8765/index.html',wait_until='domcontentloaded')
        await pg.wait_for_timeout(3000)
        await pg.evaluate("(n)=>document.querySelector('#tabs button:nth-child('+n+')').click()",TAB); await pg.wait_for_timeout(4000)
        await pg.evaluate("()=>document.getElementById('tog').click()"); await pg.wait_for_timeout(1500)
        await pg.evaluate("()=>{__ctl.autoRotate=false;__cam.up.set(0,0,1);__cam.position.set(0,23,0);__ctl.target.set(0,9.9,0);__ctl.update();}")
        await pg.wait_for_timeout(2500)
        CL=os.environ.get('CLIP')  # CLIP=x,y,w,h (css px) for a zoomed crop, use with DSF=2
        await pg.screenshot(path=OUT,timeout=120000,**({'clip':dict(zip(['x','y','width','height'],map(float,CL.split(','))))} if CL else {}))
        await b.close()
asyncio.run(main())

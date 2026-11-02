import asyncio,sys,subprocess,os
from playwright.async_api import async_playwright
OUT=sys.argv[1] if len(sys.argv)>1 else '/tmp/live.png'
TAB=sys.argv[2] if len(sys.argv)>2 else '1'
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--use-angle=swiftshader'])
        pg=await b.new_page(viewport={'width':1200,'height':600})
        async def route(r):
            u=r.request.url
            if 'cdn.jsdelivr.net/npm/three@0.160.0/' in u:
                f='/tmp/viewer/node_modules/three/'+u.split('three@0.160.0/')[1].split('?')[0]
                await r.fulfill(path=f,content_type='application/javascript')
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
        await pg.screenshot(path=OUT,timeout=120000)
        await b.close()
asyncio.run(main())

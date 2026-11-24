import asyncio,sys,json
from playwright.async_api import async_playwright
TAB=sys.argv[1]; OUT=sys.argv[2]
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/tmp/chromium',args=['--no-sandbox','--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--use-angle=swiftshader'])
        pg=await b.new_page(viewport={'width':1200,'height':600})
        async def route(r):
            u=r.request.url
            if 'cdn.jsdelivr.net/npm/three@0.160.0/' in u:
                f='/tmp/viewer/node_modules/three/'+u.split('three@0.160.0/')[1].split('?')[0]
                await r.fulfill(path=f,content_type='application/javascript')
            elif '/index.html' in u.split('?')[0]:
                resp=await r.fetch(); body=(await resp.text())
                a="const group = new THREE.Group(); scene.add(group);"; assert a in body
                await r.fulfill(response=resp,body=body.replace(a,a+" window.__g=group;",1))
            else: await r.continue_()
        await pg.route('**/*',route)
        pg.on('pageerror',lambda e:print('pageerror',str(e)[:200]))
        await pg.goto('http://localhost:8765/index.html',wait_until='domcontentloaded')
        await pg.wait_for_timeout(3000)
        await pg.evaluate("()=>document.querySelector('#tabs button:nth-child(%s)').click()"%TAB); await pg.wait_for_timeout(9000)
        js="""()=>{const g=window.__g; g.updateMatrixWorld(true); const res=[];
          const b64=(a)=>{let s='';const u=new Uint8Array(a.buffer,a.byteOffset,a.byteLength);for(let k=0;k<u.length;k+=32768)s+=String.fromCharCode.apply(null,u.subarray(k,k+32768));return btoa(s)};
          g.traverse(o=>{ if(!o.isMesh) return; const geo=o.geometry,pos=geo.attributes.position,e=o.matrixWorld.elements,arr=new Float32Array(pos.count*3);
            for(let k=0;k<pos.count;k++){const x=pos.getX(k),y=pos.getY(k),z=pos.getZ(k);arr[3*k]=e[0]*x+e[4]*y+e[8]*z+e[12];arr[3*k+1]=e[1]*x+e[5]*y+e[9]*z+e[13];arr[3*k+2]=e[2]*x+e[6]*y+e[10]*z+e[14];}
            let idx; if(geo.index){idx=new Uint32Array(geo.index.array)} else {idx=new Uint32Array(pos.count);for(let k=0;k<idx.length;k++)idx[k]=k}
            res.push({type:geo.type,nv:pos.count,nt:idx.length/3,p:b64(arr),i:b64(idx)}); });
          return {info:document.getElementById('info').textContent,meshes:res}; }"""
        r=await pg.evaluate(js); json.dump(r,open(OUT,'w')); print(r['info']); print([(m['type'],m['nv'],m['nt']) for m in r['meshes']])
        await b.close()
asyncio.run(main())

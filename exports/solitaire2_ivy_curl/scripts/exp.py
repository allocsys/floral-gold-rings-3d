import asyncio,os,base64,json
from playwright.async_api import async_playwright
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
                body=body.replace(a,a+" window.__g=group;",1)
                await r.fulfill(response=resp,body=body)
            else: await r.continue_()
        await pg.route('**/*',route)
        pg.on('pageerror',lambda e:print('pageerror',str(e)[:200]))
        await pg.goto('http://localhost:8765/index.html',wait_until='domcontentloaded')
        await pg.wait_for_timeout(3000)
        await pg.evaluate("()=>document.querySelector('#tabs button:nth-child(4)').click()"); await pg.wait_for_timeout(6000)
        print(await pg.evaluate("()=>document.getElementById('info').textContent"))
        js="""()=>{
          const g=window.__g; g.updateMatrixWorld(true);
          const out={gold:{p:[],i:[],n:0},stone:{p:[],i:[],n:0}}; const info=[];
          const b64=(a)=>{let s='';const u=new Uint8Array(a.buffer,a.byteOffset,a.byteLength);for(let k=0;k<u.length;k+=32768)s+=String.fromCharCode.apply(null,u.subarray(k,k+32768));return btoa(s)};
          g.traverse(o=>{ if(!o.isMesh) return; const m=o.material, mat=Array.isArray(m)?m[0]:m;
            const stone = mat.emissive && mat.emissive.getHex()===0x3c4352;
            const geo=o.geometry, pos=geo.attributes.position, T=out[stone?'stone':'gold'];
            const base=T.n, e=o.matrixWorld.elements, arr=new Float32Array(pos.count*3);
            for(let k=0;k<pos.count;k++){ const x=pos.getX(k),y=pos.getY(k),z=pos.getZ(k); arr[3*k]=e[0]*x+e[4]*y+e[8]*z+e[12]; arr[3*k+1]=e[1]*x+e[5]*y+e[9]*z+e[13]; arr[3*k+2]=e[2]*x+e[6]*y+e[10]*z+e[14]; }
            let idx; if(geo.index){ idx=new Uint32Array(geo.index.array.length); for(let k=0;k<idx.length;k++) idx[k]=geo.index.array[k]+base; } else { idx=new Uint32Array(pos.count); for(let k=0;k<idx.length;k++) idx[k]=base+k; }
            const det=o.matrixWorld.determinant?o.matrixWorld.determinant():0; info.push([o.geometry.type,stone?'stone':'gold',pos.count,idx.length/3,+det.toFixed(4)]);
            T.p.push(arr); T.i.push(idx); T.n+=pos.count; });
          const cat=(L,C)=>{let n=0;for(const a of L)n+=a.length;const r=new C(n);let o=0;for(const a of L){r.set(a,o);o+=a.length}return r};
          const res={info}; for(const k of ['gold','stone']){ res[k]={p:b64(cat(out[k].p,Float32Array)),i:b64(cat(out[k].i,Uint32Array))}; }
          return res; }"""
        r=await pg.evaluate(js)
        json.dump(r,open('/tmp/export.json','w'))
        for x in r['info']: print(x)
        await b.close()
asyncio.run(main())

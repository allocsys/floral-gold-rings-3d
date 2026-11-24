import json,base64,numpy as np
r=json.load(open('/tmp/export.json'))
p=np.frombuffer(base64.b64decode(r['gold']['p']),np.float32).reshape(-1,3).astype(np.float64)
i=np.frombuffer(base64.b64decode(r['gold']['i']),np.uint32).reshape(-1,3)
names=['Meshy body','Sphere hub','Tube1','Tube2','Tube3','Tube4','Lathe rim collar','Cylinder cross bar']
tri=[522894,2160,1280,1280,1280,1280,11520,128]; vt=[278262,1189,697,697,697,697,5983,196]
tb=np.cumsum([0]+tri); assert tb[-1]==len(i),(tb[-1],len(i))
mesh_of_face=np.repeat(np.arange(8),tri)
q=np.round(p,4); _,inv=np.unique(q,axis=0,return_inverse=True); inv=inv.ravel(); f=inv[i]
ok=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,0]!=f[:,2]); print('degenerate faces',int((~ok).sum()))
fid=np.arange(len(i))[ok]; f=f[ok]
e=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]); ef=np.concatenate([fid,fid,fid])
es=np.sort(e,axis=1); u,idx,c=np.unique(es,axis=0,return_inverse=True,return_counts=True); idx=idx.ravel()
# welded vertex coordinates
wp=np.zeros((inv.max()+1,3)); wp[inv]=p
def report(mask,label):
    bad=np.where(mask)[0]; print('\n==',label,len(bad),'edges')
    mid=(wp[u[bad,0]]+wp[u[bad,1]])/2; ln=np.linalg.norm(wp[u[bad,0]]-wp[u[bad,1]],axis=1)
    # faces touching these edges -> source mesh
    m_by_edge={}
    for k,ed in enumerate(bad): pass
    sel=np.isin(idx,bad); fm=mesh_of_face[ef[sel]]; print('source mesh of adjacent faces:',{names[k]:int((fm==k).sum()) for k in range(8) if (fm==k).any()})
    # cluster by 0.25mm grid union
    cl=-np.ones(len(bad),int); n=0
    for a in range(len(bad)):
        if cl[a]>=0: continue
        st=[a]; cl[a]=n
        while st:
            x=st.pop(); d=np.linalg.norm(mid-mid[x],axis=1); 
            for y in np.where((d<0.6)&(cl<0))[0]: cl[y]=n; st.append(y)
        n+=1
    print('clusters',n,'total edge length mm',round(ln.sum(),3),'max edge len',round(ln.max(),3))
    for k in range(n):
        s=cl==k; m=mid[s]; print(' #%d: %d edges, centre (%.2f,%.2f,%.2f) mm, extent %.2f, len %.3f'%(k,s.sum(),*m.mean(0),np.ptp(m,axis=0).max(),ln[s].sum()))
    return bad,mid,cl
b1,m1,c1=report(c==1,'OPEN (used once)')
b3,m3,c3=report(c>2,'NON-MANIFOLD (used >2)')
np.save('/tmp/open_mid.npy',m1); np.save('/tmp/nm_mid.npy',m3)

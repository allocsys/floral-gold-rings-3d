import numpy as np, struct
def write_stl(path, shells):
    tris=[]
    for V,F in shells:
        T=V[F]
        vol=np.einsum('ij,ij->',T[:,0],np.cross(T[:,1],T[:,2]))/6
        if vol<0: T=T[:,::-1]
        tris.append(T)
    T=np.concatenate(tris); n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0])
    n/= (np.linalg.norm(n,axis=1,keepdims=True)+1e-12)
    with open(path,'wb') as f:
        f.write(b'\0'*80); f.write(struct.pack('<I',len(T)))
        d=np.zeros(len(T),dtype=[('n','<f4',3),('v','<f4',(3,3)),('a','<u2')])
        d['n']=n; d['v']=T; f.write(d.tobytes())
    return T

def torus_mesh(P):  # P[i,j,3] closed in both directions
    N,M,_=P.shape; V=P.reshape(-1,3)
    I,J=np.meshgrid(np.arange(N),np.arange(M),indexing='ij')
    a=I*M+J; b=((I+1)%N)*M+J; c=((I+1)%N)*M+(J+1)%M; d=I*M+(J+1)%M
    F=np.concatenate([np.stack([a,b,c],-1).reshape(-1,3),np.stack([a,c,d],-1).reshape(-1,3)])
    return V,F

def band(ID,w,t,period_n,flower_r,vine_amp,groove=0.15,mask=None,NT=900,M=50):
    Ri=ID/2; Ro=Ri+t
    th=np.linspace(0,2*np.pi,NT,endpoint=False)
    z=np.linspace(-w/2,w/2,M)
    TH,Z=np.meshgrid(th,z,indexing='ij')
    s=TH*Ro; P=2*np.pi*Ro/period_n
    disp=np.zeros_like(TH)
    # vine groove
    sc=(s%P)
    vz=vine_amp*np.sin(2*np.pi*sc/P)
    disp-=groove*np.exp(-((Z-vz)/0.22)**2)
    # flowers: engraved petals + raised centre
    ds=((sc-P/2+P/2)%P)-P/2        # offset from flower centre (at s=P/2 shifted)
    ds=((s-P*0.0+P/2)%P)-P/2
    rho=np.hypot(ds,Z); phi=np.arctan2(Z,ds)
    petal=flower_r*(0.55+0.45*np.abs(np.cos(2.5*phi)))
    disp-=groove*((rho<petal)&(rho>flower_r*0.22))*1.0
    disp+=0.06*(rho<flower_r*0.22)
    # edge borders
    disp+=0.07*(np.abs(np.abs(Z)-(w/2-0.3))<0.1)
    if mask is not None: disp*=mask(TH)
    dome=0.12*(1-(2*Z/w)**2)
    Rout=Ro+dome+disp
    outer=np.stack([Rout*np.cos(TH),Rout*np.sin(TH),Z],-1)
    # inner (comfort fit), z reversed
    zi=z[::-1]; THi,Zi=np.meshgrid(th,zi,indexing='ij')
    Rin=Ri-0.08*(1-(2*Zi/w)**2)
    inner=np.stack([Rin*np.cos(THi),Rin*np.sin(THi),Zi],-1)
    return torus_mesh(np.concatenate([outer,inner],1)),Ro+0.12

def revolve(prof,n=48):
    prof=np.array(prof,float); a=np.linspace(0,2*np.pi,n,endpoint=False)
    P=np.stack([prof[None,:,0]*np.cos(a)[:,None],prof[None,:,0]*np.sin(a)[:,None],
                np.broadcast_to(prof[None,:,1],(n,len(prof)))],-1)
    return torus_mesh(P)
def to_up(V,y0,x0=0): # local z-axis -> world +Y
    return np.stack([V[:,0]+x0,V[:,2]+y0,-V[:,1]],1)

# --- bands ---
(b1,_)=band(19.0,4.5,1.5,8,1.1,0.55)
write_stl('models/ring_1_wide_band.stl',[b1])
(b2,_)=band(17.0,4.0,1.4,7,1.0,0.5)
write_stl('models/ring_2_band.stl',[b2])

# --- engagement ring: pattern only on shoulders ---
def shoulder(TH):
    d=np.abs(((TH-np.pi/2+np.pi)%(2*np.pi))-np.pi)   # angle from top
    return np.clip((d-0.45)/0.25,0,1)*np.clip((2.2-d)/0.25,0,1)
(e,Rtop)=band(17.0,2.2,1.3,12,0.7,0.35,groove=0.1,mask=shoulder)
top=Rtop+0.0
sr=2.6  # stone radius (~5.2mm)
gy=top+1.7  # girdle height
stone=revolve([(0,gy+1.0),(1.55,gy+1.0),(sr,gy),(sr,gy-0.15),(0,gy-1.6-0.15)],64)
shells=[e,(to_up(stone[0],0),stone[1])]
# basket cone
bk=revolve([(0,top-0.3),(1.3,top-0.3),(sr-0.3,gy-0.5),(0.9,gy-0.5),(0,top+0.6)],48)
shells.append((to_up(bk[0],0),bk[1]))
# prongs
for k in range(6):
    ang=k*np.pi/3
    pr=revolve([(0,top-0.2),(0.32,top-0.2),(0.28,gy+0.2),(0.3,gy+0.9),(0,gy+1.15)],16)
    V=to_up(pr[0],0)
    cx,cz=(sr+0.05)*np.cos(ang),(sr+0.05)*np.sin(ang)
    V[:,0]+=cx; V[:,2]+=cz
    shells.append((V,pr[1]))
write_stl('models/ring_3_solitaire.stl',shells)
# sanity
import os
for f in sorted(os.listdir('/mnt/user-data/outputs')): print(f,os.path.getsize('models/'+f)//1024,'KB')

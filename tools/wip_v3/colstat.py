import cv2,numpy as np,sys
C=np.array([[69,143,159],[211,132,175],[13,134,135],[147,143,178]],np.float32)
def gold(img):
    lab=cv2.cvtColor(cv2.GaussianBlur(img,(0,0),1.5),cv2.COLOR_BGR2LAB).astype(np.float32)
    m=np.isin(((lab[:,:,None,:]-C[None,None])**2).sum(3).argmin(2),[1,3])
    return lab,m
T2=cv2.imread('/tmp/band_v3_out/T2.png'); ref=T2[14:534,2396:4792]
lab,m=gold(ref); v=lab[m]
print('REF  gold frac %.2f  L mean %.0f p10 %.0f p50 %.0f p90 %.0f | a %.0f b %.0f'%(m.mean(),v[:,0].mean(),*np.percentile(v[:,0],[10,50,90]),v[:,1].mean(),v[:,2].mean()))
for f in sys.argv[1:]:
    im=cv2.imread(f)[170:430,150:1050]   # band face area
    lab,m=gold(im); v=lab[m]
    print(f,'gold frac %.2f L mean %.0f p10 %.0f p50 %.0f p90 %.0f | a %.0f b %.0f'%(m.mean(),v[:,0].mean(),*np.percentile(v[:,0],[10,50,90]),v[:,1].mean(),v[:,2].mean()))

"""Original wear masks and pavement relief, deterministic and runtime-local."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
out=Path(__file__).resolve().parents[1]/'showcase/assets/city'
rng=np.random.default_rng(428)
n=512
alpha=np.where(rng.random((n,n))<.065,0,255).astype('uint8')
for _ in range(230):
    x,y=rng.integers(0,n,2);r=int(rng.integers(1,4));alpha[max(0,y-r):y+r,max(0,x-r):x+r]=0
paint=np.ones((n,n,4),dtype='uint8')*255;paint[:,:,3]=alpha
Image.fromarray(paint).save(out/'paint-wear.png')
h=rng.normal(0,.003,(n,n))
for i in range(0,n,128):
    h[i:i+2,:]-=.09;h[:,i:i+2]-=.09
gy,gx=np.gradient(gaussian_filter(h,.6,mode='wrap'))
normal=np.stack([-gx*12,-gy*12,np.ones_like(h)],axis=-1)
normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
Image.fromarray(((normal*.5+.5)*255).astype('uint8')).save(out/'paving-normal.png')
Image.fromarray(np.clip(225+rng.normal(0,7,(n,n)),0,255).astype('uint8')).save(out/'paving-roughness.jpg',quality=90)
print('Wrote chipped paint and pavement normal/roughness maps.')

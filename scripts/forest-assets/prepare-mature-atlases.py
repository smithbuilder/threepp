import os
from pathlib import Path
from PIL import Image
import numpy as np,json
from scipy.ndimage import distance_transform_edt,gaussian_filter
recipeDir=Path(__file__).resolve().parent; root=Path(os.environ['THREEPP_FOREST_SOURCE_DIR']);bakes=root/'mature-bakes';out=Path(os.environ['THREEPP_FOREST_OUTPUT_DIR'])/'textures';out.mkdir(exist_ok=True)
for variant in ['c','b','c-mirrored']:
    metadata=json.loads((bakes/f'fir_tree_01-{variant}.json').read_text());views=[];atlases={k:Image.new('RGBA',(1024,1024)) for k in ['albedo','normal']}
    for view in range(4):
        alpha=np.asarray(Image.open(bakes/f'fir_tree_01-{variant}-{view}-albedo.png'))[:,:,3];nearest=distance_transform_edt(alpha<=30,return_distances=False,return_indices=True)
        for kind in ['albedo','normal']:
            a=np.array(Image.open(bakes/f'fir_tree_01-{variant}-{view}-{kind}.png'))
            for channel in range(3):a[:,:,channel]=a[nearest[0],nearest[1],channel]
            a[:,:,3]=alpha;atlases[kind].paste(Image.fromarray(a),(view%2*512,view//2*512))
        depth=np.asarray(Image.open(bakes/f'fir_tree_01-{variant}-{view}-depth.png'))[:,:,0].astype(float)/255;depth=gaussian_filter(depth[nearest[0],nearest[1]],4)
        coords=[]
        for row in range(9):
            v=.05/1.1+(row/8)/1.1;y=round((1-v)*511)
            for col in range(5):coords.append(float(np.clip(depth[y,round(col/4*511)]-.5,-.38,.38)*metadata['cardSpanMetres']))
        views.append({'view':view,'alphaCoverageAt0_3':float(np.mean(alpha>=77)),'farGrid':{'columns':4,'rows':8,'depthMetres':coords}})
    for kind,atlas in atlases.items():atlas.save(out/f'fir_tree_01-{variant}-canopy-{kind}-1k.png',optimize=True)
    metadata['views']=views;(bakes/f'fir_tree_01-{variant}-grids.json').write_text(json.dumps(metadata,separators=(',',':')))
print('Packed three adult-fir far atlases and depth grids.')

"""Fetch bounded 1K CC0 PBR maps from Poly Haven's official API; verify MD5.

The generated manifest keeps original URLs, authors, license, dimensions and
SHA256. No API key is required. Run once when preparing assets, never at runtime.
"""
import hashlib,json,urllib.request,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'showcase/assets/city';CACHE=ROOT/'build/city-realism'
OUT.mkdir(exist_ok=True);CACHE.mkdir(exist_ok=True)
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Cinder-city-environment/1.0'}),timeout=30) as response:return response.read()
def cached_json(name,url):
    path=CACHE/name
    if not path.exists():path.write_bytes(fetch(url))
    return json.loads(path.read_text())
catalog=cached_json('texture-catalog.json','https://api.polyhaven.com/assets?t=textures')
manifest={'license':'CC0-1.0','licenseUrl':'https://polyhaven.com/license','maps':[]}
for key,prefix in [('asphalt_01','asphalt'),('asphalt_02','cracked'),('brick_wall_001','red-brick'),('brick_wall_003','buff-brick'),('grey_plaster_02','plaster'),('bark_platanus','bark')]:
    metadata=cached_json(key+'.json','https://api.polyhaven.com/files/'+key)
    for semantic,kind in [('Diffuse','color'),('nor_gl','normal'),('Rough','roughness')]:
        entry=metadata[semantic]['1k']['jpg'];target=OUT/f'ph-{prefix}-{kind}.jpg'
        data=fetch(entry['url'])
        if len(data)>6*1024*1024:raise ValueError('Unexpected texture size')
        assert hashlib.md5(data).hexdigest()==entry['md5'],'Source checksum mismatch'
        target.write_bytes(data)
        with Image.open(target) as image:
            assert max(image.size)<=1024
            dimensions=list(image.size)
        manifest['maps'].append({'asset':key,'file':target.name,'semantic':kind,'url':entry['url'],'authors':catalog[key].get('authors'),'source':'https://polyhaven.com/a/'+key,'sha256':hashlib.sha256(data).hexdigest(),'dimensions':dimensions,'officialMd5Verified':True,'colorSpace':'sRGB' if kind=='color' else 'linear'})
sky=ROOT/'asset-library/environments/kloofendal-partly-cloudy'
shutil.copy2(sky/'sky_1k.hdr',OUT/'sky_1k.hdr')
manifest['sky']=json.loads((sky/'environment.json').read_text())
(OUT/'photo-surfaces.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Verified {len(manifest["maps"])} 1K PBR maps and copied the existing CC0 sky.')

"""Reproduce portable mature fir GLBs from pinned CC0 sources, entirely on CPU.

Requires Blender4.5.9+ and Python with numpy, Pillow and scipy. No installs,
credentials, runtime engine files or ignored build cache are required.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,urllib.request

def digest(path,algorithm='sha256'):
    h=hashlib.new(algorithm)
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def main():
    here=Path(__file__).resolve().parent;support=here/'forest-assets';repo=here.name=='scripts'
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--blender',type=Path,required=True);p.add_argument('--workdir',type=Path,default=(here.parent/'build/fidelity-v1/forest-source' if repo else Path.cwd()/'.mature-fir-source'));p.add_argument('--out',type=Path,default=(here.parent/'asset-library/models/trees' if repo else here.parent));p.add_argument('--offline',action='store_true');a=p.parse_args()
    import numpy,PIL,scipy # Fail clearly before doing any work if unavailable.
    work=a.workdir.resolve();out=a.out.resolve();work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    spec=json.loads((support/'fir-tree-source.json').read_text())
    for entry in spec['files']:
        path=(work/entry['path']).resolve()
        if not path.is_relative_to(work):raise RuntimeError('Source manifest escapes work directory')
        if not path.exists() or digest(path)!=entry['sha256']:
            if a.offline:raise RuntimeError(f'Missing or changed pinned source: {path}')
            if not entry['url'].startswith('https://dl.polyhaven.org/'):raise RuntimeError('Unexpected source host')
            path.parent.mkdir(parents=True,exist_ok=True);urllib.request.urlretrieve(entry['url'],path)
        if digest(path,'md5')!=entry['md5'] or digest(path)!=entry['sha256']:raise RuntimeError(f'Pinned source hash mismatch: {path}')
    (work/'fir_tree_01-files.json').write_text(json.dumps(spec['capturedApiFiles'],indent=2))
    env=os.environ.copy();env['THREEPP_FOREST_SOURCE_DIR']=str(work);env['THREEPP_FOREST_OUTPUT_DIR']=str(out)
    for name,blender in [('prepare-mature-maps.py',False),('bake-mature-far.py',True),('prepare-mature-atlases.py',False),('export-mature-trees.py',True),('audit-mature-trees.py',False)]:
        command=[str(a.blender),'--background','--factory-startup','--disable-autoexec','--threads','2','--python',str(support/name)] if blender else [sys.executable,str(support/name)]
        print(f'Processing {name}',flush=True)
        with (work/(name+'.log')).open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    print(f'Validated portable models: {out}')
if __name__=='__main__':main()

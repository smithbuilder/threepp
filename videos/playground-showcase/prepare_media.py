"""Freeze source-bound native footage and normalize the authored narration."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import csv,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
video=ROOT/'assets/video';video.mkdir(parents=True,exist_ok=True)
audio=ROOT/'assets/audio';logs=ROOT/'proof';logs.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(cmd,log):
    result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    (logs/log).write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('Failed: '+str(cmd[:4])+'; see '+log)
    return result.stdout
sessions=json.loads((ROOT/'native-captures.json').read_text())
sessions+=[{'name':v+'-jumps','session':str(REPO/'build/sessions'/s)} for v,s in [('safari','20261105-062101-565'),('baja','20261105-062134-341'),('buggy','20261105-062314-812')]]
def encode(item):
    p=REPO/Path(item['session']);r=json.loads((p/'result.json').read_text());name=item['name'];dest=video/(name+'.mp4')
    assert r['exitCode']==0 and r['sequence'] and r['captureScale']==1 and r['renderWidth']==960 and r['renderHeight']==600
    assert r['binarySha256'].lower()=='ed6427e687ad00437d1cf34320ef313796530c212a5422a8ce5bbd1062642ed8'
    assert not (p/'stderr.log').read_text().strip()
    paths=sorted((p/'frames').glob('frame_*.png'));assert len(paths)==r['requestedFrames']
    if not dest.exists():
        run(['ffmpeg','-nostdin','-v','error','-y','-framerate','30','-i',str(p/'frames/frame_%05d.png'),'-frames:v',str(len(paths)),'-an','-c:v','libx264','-threads','2','-filter_threads','1','-preset','medium','-crf','16','-vf','scale=iw:ih:out_color_matrix=bt709:out_range=tv,format=yuv420p','-colorspace','bt709','-movflags','+faststart',str(dest)],name+'-encode.log')
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)],name+'-probe.json'))
    v=next(s for s in probe['streams'] if s['codec_type']=='video');assert v['width']==960 and v['height']==600 and int(v['nb_frames'])==len(paths) and v['avg_frame_rate']=='30/1'
    rows=list(csv.DictReader(open(p/'drive.json.csv')))[r['warmupFrames']:]
    assert len(rows)==len(paths)
    (video/(name+'-telemetry.json')).write_text(json.dumps(rows,separators=(',',':')))
    print(name,len(paths),'native frames',flush=True)
    return {'name':name,'session':str(p.relative_to(REPO)),'binarySha256':r['binarySha256'],'assets':r['playgroundAssetSha256'],'sourceResultSha256':sha(p/'result.json'),'sourceFrames':[sha(x) for x in paths],'video':str(dest.relative_to(ROOT)),'sha256':sha(dest),'frames':len(paths),'fps':30,'width':960,'height':600,'sourceWarmupFrames':r['warmupFrames']}
with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(encode,sessions))
(ROOT/'source-manifest.json').write_text(json.dumps({'picture':'Actual native 960x600 30fps frames; no upscale, interpolation or generated gameplay','clips':records},indent=2)+'\n')
voice=json.loads((ROOT/'voice-receipt.json').read_text())
for item in voice['voices']:
    source=ROOT/item['file'];dest=audio/(item['id']+'-narration.wav')
    run(['ffmpeg','-nostdin','-v','error','-y','-i',str(source),'-af','highpass=f=70,loudnorm=I=-17:TP=-3:LRA=7','-ar','48000','-ac','2',str(dest)],item['id']+'-normalize.log')
run(['ffmpeg','-nostdin','-v','error','-y','-ss','16','-i',str(audio/'deliberate-thought.mp3'),'-t','80','-af','loudnorm=I=-23:TP=-5:LRA=7','-ar','48000','-ac','2',str(audio/'music-bed.wav')],'music-normalize.log')
print('Native media and narration prepared',flush=True)

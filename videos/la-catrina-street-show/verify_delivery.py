"""Verify encoded delivery and compare sampled frames to the original native clips."""
from pathlib import Path
import hashlib,json,math,re,shutil,subprocess
from fractions import Fraction
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent;PROOF=ROOT/'proof';OUT=ROOT/'outputs/La-Catrina-Street-Show.mp4'
FRAMES=PROOF/'delivery-frames';FRAMES.mkdir(exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def run(args,timeout=180):return subprocess.run(args,cwd=ROOT,capture_output=True,text=True,check=True,timeout=timeout)
probe=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(OUT)]).stdout)
(PROOF/'delivery-probe.json').write_text(json.dumps(probe,indent=2)+'\n')
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['codec_name'],v['width'],v['height'],Fraction(v['avg_frame_rate']),int(v['nb_frames']))==('h264',960,600,30,1440),v
assert abs(float(v['duration'])-48)<1/30 and abs(float(probe['format']['duration'])-48)<.1
assert a['codec_name']=='aac' and int(a['sample_rate'])==48000 and a['channels']==2
decoded=run(['ffmpeg','-v','error','-threads','2','-i',str(OUT),'-map','0','-f','null','NUL'])
(PROOF/'delivery-decode.log').write_text(decoded.stderr);assert not decoded.stderr.strip(),decoded.stderr
black=run(['ffmpeg','-hide_banner','-nostats','-threads','2','-i',str(OUT),'-an','-vf','blackdetect=d=0.05:pix_th=0.02:pic_th=0.98','-f','null','NUL'])
(PROOF/'delivery-black-scan.log').write_text(black.stderr);assert 'black_start:' not in black.stderr,'Unexpected black interval'
audio=run(['ffmpeg','-hide_banner','-nostats','-threads','2','-i',str(OUT),'-vn','-af','ebur128=peak=true','-f','null','NUL'])
(PROOF/'delivery-audio.log').write_text(audio.stderr);summary=audio.stderr.split('Summary:')[-1]
lufs=float(re.search(r'I:\s*(-?[\d.]+) LUFS',summary)[1]);peak=float(re.search(r'Peak:\s*(-?[\d.]+) dBFS',summary)[1])
assert -23<lufs<-13 and peak<-.5,summary
edit=json.loads((ROOT/'edit-manifest.json').read_text());source=json.loads((ROOT/'source-manifest.json').read_text());native=json.loads((ROOT/'native-captures.json').read_text())
assert source['status']=='PASS' and source['nativeFramesVerified']==1440
indices={0,24,90,179,180,294,330,479,480,555,629,630,750,869,870,990,1109,1110,1275,1350,1425,1439}
# Motion strip across one complete front-hop cycle, without accelerating footage.
indices.update(range(300,361,10));indices=sorted(indices)
select='+'.join(f'eq(n\\,{n})' for n in indices)
run(['ffmpeg','-hide_banner','-loglevel','error','-threads','2','-filter_threads','1','-i',str(OUT),'-vf',f'select={select}','-fps_mode','passthrough','-frames:v',str(len(indices)),'-y',str(FRAMES/'sample-%03d.png')])
matches=[]
for i,n in enumerate(indices,1):
    path=FRAMES/f'sample-{i:03d}.png';final=Image.open(path).convert('RGB')
    assert final.size==(960,600) and np.asarray(final).mean()>15
    scene=next(s for s in edit['scenes'] if s['start']*30<=n<(s['start']+s['duration'])*30);local=n-round(scene['start']*30)
    ref=FRAMES/f'ref-{scene["id"]}-{local:04d}.png'
    run(['ffmpeg','-hide_banner','-loglevel','error','-threads','2','-filter_threads','1','-i',str(ROOT/scene['source']),'-vf',f'select=eq(n\\,{local})','-frames:v','1','-y',str(ref)])
    box=(0,150,960,600) if scene['labelDuration'] else (0,0,960,600)
    f=np.asarray(final.crop(box)).astype(float);r=np.asarray(Image.open(ref).convert('RGB').crop(box)).astype(float);mae=float(np.abs(f-r).mean())
    assert mae<8,(n,scene['id'],mae)
    matches.append({'frame':n,'time':n/30,'scene':scene['id'],'sourceFrame':local,'nativeRegionMeanAbsoluteError':round(mae,4),'decodedPngSha256':sha(path)})
font=ImageFont.truetype(str(ROOT/'assets/fonts/Barlow-Regular.ttf'),14)
def contact(frameSet,name):
    items=[(i,n) for i,n in enumerate(indices,1) if n in frameSet];cols=3;w=360;h=254
    sheet=Image.new('RGB',(cols*w,math.ceil(len(items)/cols)*h),(241,235,228));d=ImageDraw.Draw(sheet)
    for pos,(i,n) in enumerate(items):
        x=(pos%cols)*w;y=(pos//cols)*h;im=Image.open(FRAMES/f'sample-{i:03d}.png').convert('RGB').resize((360,225),Image.Resampling.LANCZOS);sheet.paste(im,(x,y))
        m=next(m for m in matches if m['frame']==n);d.text((x+8,y+231),f'{n/30:05.2f}s {m["scene"]} / f{n}',font=font,fill=(35,25,30))
    sheet.save(PROOF/name,quality=95)
contact({24,90,294,330,555,750,990,1275,1350,1425},'La-Catrina-Review.jpg')
contact({0,179,180,479,480,629,630,869,870,1109,1110,1439},'La-Catrina-Seams.jpg')
contact(set(range(300,361,10)),'La-Catrina-Hop-Motion.jpg')
# Frame310 was selected by inspecting the decoded hop sequence: both front
# tires have clear road separation and the complete body remains in frame.
posterFrame=310;poster=next(i for i,n in enumerate(indices,1) if n==posterFrame)
posterSource=FRAMES/f'sample-{poster:03d}.png';posterPath=ROOT/'outputs/La-Catrina-Street-Show.png'
shutil.copyfile(posterSource,posterPath);assert sha(posterPath)==sha(posterSource)
posterEvidence={'file':posterPath.relative_to(ROOT).as_posix(),'sha256':sha(posterPath),'bytes':posterPath.stat().st_size,
    'width':960,'height':600,'frame':posterFrame,'timeSeconds':posterFrame/30,'scene':'hop','nativeClipFrame':posterFrame-180,
    'decodedSample':posterSource.relative_to(ROOT).as_posix(),'selection':'Visually inspected front-pair airborne hero frame; unchanged decoded video pixels.'}
data=OUT.read_bytes();assert data.find(b'moov')<data.find(b'mdat'),'Fast-start metadata missing'
receipt={'status':'PASS','output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'durationSeconds':float(probe['format']['duration']),'video':{'codec':v['codec_name'],'width':960,'height':600,'fps':30,'frames':1440},'poster':posterEvidence,'audio':{'codec':a['codec_name'],'sampleRate':48000,'channels':2,'integratedLufs':lufs,'truePeakDbfs':peak,'review':'Measured, not human listened. Credited real recordings reconstruct engine/pump sound.'},'fullDecode':'PASS; no decoder errors','blackFrameScan':'PASS; no98%-black interval at least0.05s','fastStart':True,'nativeFramesVerified':1440,'modelSha256':native['modelSha256'],'nativeCaptureManifestSha256':sha(ROOT/'native-captures.json'),'verifiedSourceManifestSha256':sha(ROOT/'source-manifest.json'),'projectHtmlSha256':sha(ROOT/'index.html'),'sourceCorrespondence':matches,'correspondenceLimit':'H.264 re-encoding causes small pixel differences. Title regions are excluded only in the two title scenes.','notes':['Actual native city driving and hydraulic controller; normal-speed clips.','No upscale, crop, interpolation, generated replacement footage or color grade.','Independent model and final editorial reviews are recorded separately.']}
(PROOF/'delivery-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('status','output','sha256','bytes','durationSeconds','video','audio')},indent=2))

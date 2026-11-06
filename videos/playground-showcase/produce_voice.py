"""Narrate authored lines through the user's existing, free fleet Voicebox."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse,hashlib,json,time,urllib.request,wave

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'narration.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--only');parser.add_argument('--revision',default='');args=parser.parse_args()
base='http://100.97.152.42:17493'
folder=ROOT/'assets/audio';folder.mkdir(parents=True,exist_ok=True)
def read(url,body=None):
    request=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=60) as response:return response.read()
def generate(scene):
    path=folder/(scene['id']+'-voice'+('-'+args.revision if args.revision else '')+'.wav')
    if path.exists():raise RuntimeError('Preserve existing narration; do not regenerate silently')
    generation=json.loads(read(base+'/generate',{'profile_id':data['profile_id'],'text':scene['text'],'engine':'kokoro'}))
    identity=generation['id'];deadline=time.monotonic()+300
    while True:
        result=json.loads(read(base+'/history/'+identity));status=result.get('status','').lower()
        if status=='completed':break
        if status in ('failed','error'):raise RuntimeError(result.get('error',status))
        if time.monotonic()>deadline:raise TimeoutError(identity)
        time.sleep(1)
    path.write_bytes(read(base+'/audio/'+identity))
    with wave.open(str(path),'rb') as audio:duration=audio.getnframes()/audio.getframerate()
    receipt={'id':scene['id'],'text':scene['text'],'generation':identity,'file':str(path.relative_to(ROOT)),'duration':duration,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    print(scene['id'],round(duration,3),'seconds',flush=True);return receipt
scenes=[s for s in data['scenes'] if not args.only or s['id']==args.only]
with ThreadPoolExecutor(max_workers=3) as pool:voices=list(pool.map(generate,scenes))
if args.only:
    prior=json.loads((ROOT/'voice-receipt.json').read_text());mapping={s['id']:s for s in prior['voices']};mapping.update({s['id']:s for s in voices});voices=[mapping[s['id']] for s in data['scenes']]
(ROOT/'voice-receipt.json').write_text(json.dumps({'provider':'fleet Voicebox','profile':data['profile_id'],'voice':data['voice'],'voices':voices},indent=2)+'\n')

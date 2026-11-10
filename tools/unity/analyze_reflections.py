"""Compare capture-only GPU reflection readbacks with native HDR directions.

No editor/player launch or rendering occurs here. Reads retained first-frame HDR
samples before tone mapping, using the same source HDR and native inverse yaw.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def hdr_pixels(path):
    info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(path)]))["streams"][0]
    w,h=info["width"],info["height"]
    data=subprocess.check_output(["ffmpeg","-v","error","-nostdin","-threads","1","-i",str(path),"-frames:v","1","-pix_fmt","gbrpf32le","-f","rawvideo","pipe:1"])
    return np.frombuffer(data,dtype="<f4").reshape(3,h,w)[[2,0,1]].transpose(1,2,0)

def sample(image,direction):
    x,y,z=direction/np.linalg.norm(direction)
    u=(.5+math.atan2(z,x)/(2*math.pi)+3.4095478/(2*math.pi))%1
    v=.5+math.asin(max(-1,min(1,y)))/math.pi
    h,w,_=image.shape
    sx=u*w-.5;sy=(1-v)*h-.5
    x0=math.floor(sx);y0=math.floor(sy);fx=sx-x0;fy=sy-y0
    return sum(image[min(h-1,max(0,y0+dy)),(x0+dx)%w]*weight for dx,dy,weight in ((0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--revision",required=True);args=parser.parse_args()
    folder=ROOT/"evidence"/args.revision
    if folder.parent!=ROOT/"evidence" or not folder.is_dir():raise ValueError("Existing revision required")
    controls={}
    for session in sorted(folder.glob("*-Capture")):
        path=session/"render-diagnostics.json"
        if path.exists():
            data=read(path);control=data.get("materialControl")
            if control in ("reflection-direction","coat-normal","cube-lod0","cube-filtered","cube-decode","white-coat"):
                controls[control]=(session,data)
    required={"reflection-direction","coat-normal","cube-lod0","cube-filtered","cube-decode","white-coat"}
    if set(controls)!=required:raise ValueError("Missing GPU controls: "+str(required-set(controls)))
    player=digest(ROOT/"builds"/args.revision/"Cinder.exe")
    for session,_ in controls.values():
        receipt=read(session/"runtime-receipt.json")
        if not receipt["normal"] or receipt["exeSha256"].lower()!=player:raise ValueError("Control player binding mismatch")
    source=ROOT/"Unity/Assets/Resources/Cinder/sky.hdr";image=hdr_pixels(source)
    def values(name):
        data=controls[name][1]
        return np.vstack((np.array(data["linearSamples"],dtype=float).reshape(-1,3),data["centerLinearRgb"]))
    directions=values("reflection-direction")*2-1;normals=values("coat-normal")*2-1
    raw=values("cube-lod0");filtered=values("cube-filtered");white=values("white-coat")
    coords=controls["coat-normal"][1]["sampleCoordinates"]+[480,300]
    decode=values("cube-decode")
    rows=[]
    for i,(direction,normal) in enumerate(zip(directions,normals)):
        # Debug returns occur only on coated material. Reject background/trim
        # samples by the near-constant HDR decode instructions, not their look.
        if abs(decode[i,1]-1)>.002 or abs(decode[i,2])>.002:
            continue
        expected=sample(image,direction)*.65
        nv=max(0,min(1,float(np.dot(normal/np.linalg.norm(normal),direction/np.linalg.norm(direction)))))
        predicted=(.04+.96*(1-nv)**5)/(1+.045**4)
        rows.append(dict(pixel=coords[i*2:i*2+2],reflectionDirection=direction.tolist(),coatNormal=normal.tolist(),normalDotView=nv,nativeSourceRadiance=expected.tolist(),gpuDecodedLod0=raw[i].tolist(),rawRelativeError=float(np.linalg.norm(raw[i]-expected)/max(.01,np.linalg.norm(expected))),gpuFilteredRadiance=filtered[i].tolist(),gpuWhiteCoat=white[i].tolist(),schlickWhiteCoatApprox=predicted))
    report=dict(revision=args.revision,playerSha256=player,sourceSha256=digest(source),scope="Finite same-pixel GPU shader readbacks before tone mapping. Raw source comparison includes .65 environment intensity; filtered kernels/BRDF differ and are not certified equivalent. Pixel coordinates are source texture bottom-left.",decodeInstructionsXYZ=controls["cube-decode"][1]["centerLinearRgb"],rows=rows,controls={name:{"session":str(session.relative_to(ROOT)),"diagnosticSha256":digest(session/"render-diagnostics.json")} for name,(session,_) in controls.items()})
    output=folder/"reflection-analysis.json"
    with output.open("x",encoding="utf-8") as stream:json.dump(report,stream,indent=2)
    print(json.dumps({"output":str(output),"decode":report["decodeInstructionsXYZ"],"rawRelativeErrors":[round(row["rawRelativeError"],4) for row in rows]},indent=2))

if __name__=="__main__":main()

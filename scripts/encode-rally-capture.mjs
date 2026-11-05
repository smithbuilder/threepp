// Build a local gameplay clip and replacement engine audio from native frame telemetry.
// No audio endpoint, network, GPU encoder, or generated gameplay is used.
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const [session, output] = process.argv.slice(2);
if (!session || !output) throw new Error('Usage: node scripts/encode-rally-capture.mjs SESSION OUTPUT.mp4');
const frames = path.join(session, 'frames');
const rows = fs.readFileSync(path.join(frames,'frame-data.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(x=>x.split(',').map(Number));
if(rows.length<1 || rows.length>900) throw new Error('Invalid bounded sequence');
for(let i=0;i<rows.length;i++) if(rows[i][0]!==i || !fs.existsSync(path.join(frames,`frame_${String(i).padStart(5,'0')}.png`))) throw new Error('Incomplete sequence');
function readBand(name){
 const src=fs.readFileSync(`showcase/assets/cinder_exhaust_${name}.wav`);let sourceRate,channels,bits,data;
 for(let i=12;i+8<src.length;){const tag=src.toString('ascii',i,i+4),n=src.readUInt32LE(i+4);if(tag==='fmt '){channels=src.readUInt16LE(i+10);sourceRate=src.readUInt32LE(i+12);bits=src.readUInt16LE(i+22);}if(tag==='data')data=src.subarray(i+8,i+8+n);i+=8+n+(n%2);}
 if(channels!==1||bits!==16||!data)throw new Error('Expected mono PCM16 exhaust band');return {data,rate:sourceRate,phase:0,length:data.length/2};
}
if(rows.some(r=>r.length<9))throw new Error('Sequence must contain the new RPM/load/gear telemetry');
const bands=['idle','mid','high'].map(readBand);
const rate=48000, samples=Math.round(rows.length/30*rate), audio=Buffer.alloc(44+samples*2);
audio.write('RIFF');audio.writeUInt32LE(36+samples*2,4);audio.write('WAVEfmt ',8);audio.writeUInt32LE(16,16);audio.writeUInt16LE(1,20);audio.writeUInt16LE(1,22);audio.writeUInt32LE(rate,24);audio.writeUInt32LE(rate*2,28);audio.writeUInt16LE(2,32);audio.writeUInt16LE(16,34);audio.write('data',36);audio.writeUInt32LE(samples*2,40);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
for(let i=0;i<samples;i++){
 const t=i/rate,frame=Math.min(rows.length-1,Math.floor(t*30)),f=t*30-frame,r=rows[frame],n=rows[Math.min(rows.length-1,frame+1)];
 const rpm=r[4]+(n[4]-r[4])*f,load=r[5]+(n[5]-r[5])*f,shift=r[7];
 const a=clamp((rpm-1600)/1900,0,1),b=clamp((rpm-3400)/2100,0,1),weights=[Math.sqrt(1-a),Math.sqrt(a*(1-b)),Math.sqrt(b)];
 let v=0;
 for(let j=0;j<3;j++){
  const band=bands[j],at=Math.floor(band.phase)%band.length,next=(at+1)%band.length,frac=band.phase-Math.floor(band.phase);
  const pitch=clamp(rpm/[2600,3900,5600][j],j===0?.48:.72,j===0?1.12:1.3);
  const gain=weights[j]*(.22+.3*load)*(shift>.05?.45:1)*.75;
  v+=(band.data.readInt16LE(at*2)*(1-frac)+band.data.readInt16LE(next*2)*frac)*gain;
  band.phase+=band.rate/rate*pitch;
 }
 const edge=Math.min(1,t/.055,(samples-i)/rate/.16);audio.writeInt16LE(clamp(Math.round(v*edge),-32768,32767),44+i*2);
}
fs.mkdirSync(path.dirname(output),{recursive:true});
const wav=output.replace(/\.mp4$/i,'.wav');fs.writeFileSync(wav,audio);
const result=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate','30','-i',path.join(frames,'frame_%05d.png'),'-i',wav,'-frames:v',String(rows.length),'-c:v','libx264','-preset','medium','-crf','17','-threads','2','-g','30','-keyint_min','30','-pix_fmt','yuv420p','-af','loudnorm=I=-19:TP=-2:LRA=7','-ar','48000','-c:a','aac','-b:a','128k','-movflags','+faststart',output],{stdio:'inherit'});
if(result.error)throw result.error;if(result.status!==0)process.exit(result.status??1);
console.log(JSON.stringify({output,frames:rows.length,duration:rows.length/30,source:session,audio:'CC0 real dune-buggy exhaust, three RPM/load layers and shift cuts matching the game; replacement audio, not endpoint capture'}));

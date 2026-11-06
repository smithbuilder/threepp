"""Build an editable HyperFrames film around unchanged native source clips."""
from pathlib import Path
import csv,html,json,shutil,wave
ROOT=Path(__file__).resolve().parent
sources={x['name']:x for x in json.loads((ROOT/'source-manifest.json').read_text())['clips']}
voices={x['id']:x for x in json.loads((ROOT/'voice-receipt.json').read_text())['voices']}
scenes=[
 ('world',10,'One world. Every vehicle.','A selectable vehicle tuning playground',[(0,3,'baja-ruts',1),(3,3,'safari-jumps',0),(6,2,'buggy-whoops',0),(8,2,'safari-ridge',1)]),
 ('suspension',12,'Let the wheels work','Recorded suspension compression',[(0,7,'baja-ruts',0),(7,5,'buggy-whoops',1)]),
 ('terrain',14,'Find the limits','Steep grades remain an open tuning target',[(0,5,'safari-hills',0),(5,4.5,'safari-ridge',1),(9.5,4.5,'safari-side-slope',1)]),
 ('jumps',18,'One jump line, three vehicles','Takeoff, full droop, landing and recovery',[(0,4.5,'baja-jumps',.7),(4.5,4.5,'safari-jumps',5.1),(9,4.5,'buggy-jumps',5.1),(13.5,4.5,'baja-jumps',5.1)]),
 ('wind',14,'Put the air to work','20 m/s steady crosswind',[(0,7,'baja-wind-side',1),(7,7,'baja-wind',1)]),
 ('future',12,"A proving ground for what's next",'Shared vehicle definitions and repeatable tests',[(0,5,'safari-ridge',2),(5,7,'baja-ruts',4)])
]
styles='''
@font-face{font-family:Barlow;src:url("assets/fonts/Barlow-Regular.ttf")}@font-face{font-family:BarlowCondensed;src:url("assets/fonts/BarlowCondensed-Bold.ttf");font-weight:700}
#root{position:absolute;inset:0;overflow:hidden;font-family:Barlow,sans-serif;color:#fff8e8}
#root .footage{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;z-index:0}
#root .footer{position:absolute;left:0;right:0;top:464px;height:136px;background:#24271f;z-index:4}
#root .accent{position:absolute;left:0;top:0;width:10px;height:136px;background:#d6813b}
#root .headline{position:absolute;left:96px;top:14px;font:700 38px/1.05 BarlowCondensed,sans-serif;white-space:nowrap;letter-spacing:.15px}
#root .subline{position:absolute;left:96px;top:59px;font:20px/1.1 Barlow,sans-serif;white-space:nowrap;color:#eddfc5}
#root .shotlabel{position:absolute;right:96px;bottom:150px;background:#24271f;padding:7px 12px;font:18px/1.1 Barlow,sans-serif;color:#fff8e8;z-index:3}
#root .note{position:absolute;left:96px;top:107px;font:16px/1.1 Barlow,sans-serif;color:#eadcc2}
#root .telemetry{position:absolute;right:96px;top:18px;display:flex;gap:17px;align-items:flex-end}
#root .sensor{position:relative;width:24px;height:60px;font:16px/1 Barlow,sans-serif;text-align:center}
#root .sensor-bg{position:absolute;left:4px;top:0;width:16px;height:34px;background:#64705c}
#root .bar{position:absolute;left:4px;top:0;width:16px;height:34px;background:#e4ad61;transform-origin:50% 100%}
#root .corner{position:absolute;left:0;top:43px;width:24px}
#root .metric{position:absolute;left:96px;top:4px;font:700 76px/1 BarlowCondensed,sans-serif;color:#e4ad61}
#root .metric-copy{position:absolute;left:200px;top:20px;font:25px/1.1 Barlow,sans-serif}
#root .metric-small{position:absolute;left:200px;top:55px;font:19px/1.1 Barlow,sans-serif;color:#eddfc5}
'''
out=ROOT/'compositions';out.mkdir(exist_ok=True)
hosts=[];audio=[];story=[];timing=[];start=0
for sid,duration,title,subtitle,shots in scenes:
    videos=[]
    for i,(when,length,source,offset) in enumerate(shots):
        record=sources[source];assert offset+length<=record['frames']/30+.001
        videos.append(f'<video id="{sid}-shot-{i}" class="clip footage" data-start="{when}" data-duration="{length}" data-media-start="{offset}" data-track-index="0" src="{record["video"]}" muted playsinline preload="metadata" data-layout-allow-overlap="true"></video>')
    extra='';scripts=[]
    if sid=='suspension':
        extra='<div id="suspension-sensors" class="telemetry">'+''.join(f'<div class="sensor"><span class="sensor-bg"></span><span id="suspension-bar-{i}" class="bar"></span><span class="corner">{name}</span></div>' for i,name in enumerate(['FL','FR','RL','RR']))+'</div>'
        keys=['flTravel','frTravel','rlTravel','rrTravel']
        for when,length,source,offset in shots:
            rows=json.loads((ROOT/'assets/video'/f'{source}-telemetry.json').read_text());low,high=(.268,.52) if source.startswith('baja') else (.16,.68)
            for frame in range(0,round(length*30),3):
                row=rows[min(len(rows)-1,round(offset*30)+frame)];t=when+frame/30
                for k,key in enumerate(keys):
                    value=max(0,min(1,(float(row[key])-low)/(high-low)))
                    if frame==0:scripts.append(f'tl.set("#suspension-bar-{k}",{{scaleY:{value:.6f}}},{t:.6f});')
                    else:scripts.append(f'tl.to("#suspension-bar-{k}",{{scaleY:{value:.6f},duration:0.1,ease:"none"}},{t-.1:.6f});')
        scripts.insert(0,'tl.set(".bar",{scaleY:0.3});')
    if sid=='terrain':
        labels=[(0,5,'Steep grade: Safari stalls before the crest'),(5,4.5,'Curved ridge: 3.6 m crown'),(9.5,4.5,'Side slope: load moves downhill')]
    elif sid=='jumps':labels=[(0,4.5,'Small ramp · Baja 427'),(4.5,4.5,'Large jump · Safari'),(9,4.5,'Large jump · Original buggy'),(13.5,4.5,'Large jump · Baja 427')]
    elif sid=='world':labels=[(0,3,'Baja 427'),(3,3,'Safari'),(6,2,'Original buggy'),(8,2,'The same testing world')]
    else:labels=[]
    for i,(t,d,text) in enumerate(labels):
        videos.append(f'<div id="{sid}-label-{i}" class="clip shotlabel" data-start="{t}" data-duration="{d}" data-track-index="2" data-layout-allow-overlap="true">{html.escape(text)}</div>')
    if sid=='wind':extra='<div class="note">Uniform simulated airflow · estimated coefficients · no CFD</div>'
    if sid=='future':
        footer=f'''<div id="future-metric-clip" class="clip" data-start="0" data-duration="5.5"><div id="future-metric-content"><div class="metric">79</div><div class="metric-copy">physics checks passed</div><div class="metric-small">plus 6 existing regression tests</div></div></div>
        <div id="future-close-clip" class="clip" data-start="5.5" data-duration="6.5"><div id="future-close"><div class="headline">Vehicle Tuning Playground</div><div class="subline">More vehicles. The same tests. Your feedback next.</div></div></div>
        <div class="note" data-layout-ignore="true">Music: Deliberate Thought · Kevin MacLeod / incompetech · CC BY 4.0</div>'''
        scripts+=['tl.fromTo("#future-metric-content",{opacity:0},{opacity:1,duration:.35,ease:"power2.out"},.2);','tl.fromTo("#future-close",{opacity:0},{opacity:1,duration:.3,ease:"power2.out"},5.5);']
    else:
        title_size=32 if sid=='suspension' else 38
        footer=f'<div id="{sid}-headline" class="headline" style="font-size:{title_size}px" data-var-text="{sid}-title">{html.escape(title)}</div><div id="{sid}-subline" class="subline" style="font-size:{18 if sid=="suspension" else 20}px">{html.escape(subtitle)}</div>'+extra
    if sid in ('world','suspension','jumps'):
        scripts.insert(0,f'tl.fromTo("#{sid}-footer",{{clipPath:"inset(0 100% 0 0)"}},{{clipPath:"inset(0 0% 0 0)",duration:.48,ease:"power4.out"}},.1);')
    else:scripts.insert(0,f'tl.fromTo("#{sid}-footer",{{opacity:0}},{{opacity:1,duration:.24,ease:"power2.out"}},.1);')
    terrain_style='#root .footer{top:0;height:148px}#root .accent{height:148px}#root .headline{top:55px}#root .subline{top:101px}#root .shotlabel{left:96px;right:auto;top:152px;bottom:auto}' if sid=='terrain' else ''
    text=f'''<template><style>{styles}{terrain_style}</style><div id="root" data-composition-id="{sid}" data-width="960" data-height="600">
    {''.join(videos)}<div id="{sid}-overlay" class="clip" data-start="0" data-duration="{duration}" data-track-index="3" data-layout-allow-overlap="true" data-layout-allow-caption-zone="true"><div id="{sid}-footer" class="footer"><span class="accent"></span>{footer}</div></div>
    </div><script>const tl=gsap.timeline({{paused:true}});{''.join(scripts)}window.__timelines["{sid}"]=tl;</script></template>'''
    (out/(sid+'.html')).write_text(text,encoding='utf8')
    hosts.append(f'<div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{start}" data-duration="{duration}" data-track-index="1" data-track-kind="graphics" data-width="960" data-height="600"></div>')
    vf=ROOT/'assets/audio'/f'{sid}-narration.wav'
    with wave.open(str(vf),'rb') as w:voice_duration=w.getnframes()/w.getframerate()
    assert voice_duration+.5<duration
    audio.append(f'<audio id="voice-{sid}" class="clip" src="assets/audio/{sid}-narration.wav" data-start="{start+.5}" data-duration="{voice_duration}" data-track-index="3" data-audio-role="voiceover" data-audio-group="narration" data-volume="1" data-fade-in=".025" data-fade-out=".04"></audio>')
    story.append(f'## Frame {sid}\n\nstatus: built\nsrc: compositions/{sid}.html\nstart: {start}\nduration: {duration}\nTreatment: footage-led editorial cut; adapted lt-clean-bar; wheel chart adapted animated-bar-chart when present.\n\n{title}\n\n{voices[sid]["text"]}\n')
    timing.append({'id':sid,'start':start,'duration':duration,'title':title,'shots':[{'start':a,'duration':b,'source':c,'sourceStart':d} for a,b,c,d in shots]});start+=duration
assert start==80
variables=[{'id':sid+'-title','type':'string','label':sid+' title','default':title} for sid,duration,title,sub,shots in scenes]
variables +=[{'id':'color-ground','type':'color','label':'Soil ink','default':'#24271f'},{'id':'color-accent','type':'color','label':'Vehicle paint accent','default':'#d6813b'}]
root=f'''<!doctype html><html lang="en" data-composition-variables='{html.escape(json.dumps(variables),quote=True)}'><head><meta charset="utf-8"><meta name="viewport" content="width=960,height=600"><script src="assets/vendor/gsap.min.js"></script><style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:960px;height:600px;overflow:hidden;background:#24271f}}#root{{width:100%;height:100%;position:relative}}</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="80" data-width="960" data-height="600" data-fps="30">{''.join(hosts)}{''.join(audio)}<audio id="music-bed" class="clip" src="assets/audio/music-bed.wav" data-start="0" data-duration="80" data-track-index="2" data-audio-role="music" data-audio-group="music" data-volume="0.5" data-fade-in=".7" data-fade-out="1.4"></audio></div><script>window.__timelines["main"]=gsap.timeline({{paused:true}});</script></body></html>'''
(ROOT/'index.html').write_text(root,encoding='utf8')
(ROOT/'STORYBOARD.md').write_text('---\nmode: autonomous\n---\n\n# Playground showcase\n\n'+'\n'.join(story),encoding='utf8')
(ROOT/'edit-manifest.json').write_text(json.dumps({'duration':80,'width':960,'height':600,'fps':30,'scenes':timing},indent=2)+'\n')
(ROOT/'SPEC.md').write_text('''# Showcase specification

GOAL: Show how the shared testing world reveals vehicle behavior and remaining limits.
OUTPUT: HyperFrames, native 960 x 600, 30 fps; 80 seconds / 2400 frames.
LOOK: Unaltered native terrain and vehicle footage; ink #24271f, text #fff8e8, paint accent #d6813b, sensor accent #e4ad61. Barlow Condensed Bold 32–38 px display, Barlow Regular 18–20 px body. No global grade or image filters.
OBJECTS: The actual Safari, buggy and Baja v3; actual trails, jump line and open wind-test gantry. Recorded per-wheel compression drives the four bars.
MOTION: Actual vehicle motion plays at 1x. Editorial hard cuts preserve physics continuity within each shot. Lower-third wipe 0.48 s power4.out; alternate opacity entry 0.24 s power2.out. No camera zoom, invented vehicle movement or interpolation.
SOUND: Fleet Kokoro George narration; Kevin MacLeod's Deliberate Thought underneath, carved around speech. Footage is silent; no claim of endpoint or engine audio.
SHOTS: See edit-manifest.json for every source range. Scene starts are 0, 10, 22, 36, 54 and 68 seconds.
BANNED: Invented UI, fake before/after, racing framing, implying every course is completed, generated gameplay, upscaling, drifting titles, KPI card grids, glow, particles, decorative HUDs, physics obscured by transitions.
QA: Every scene midpoint; title entry at 0.3; terrain limit at 25; takeoffs/landings across 36–54; wind label at 60; closing at 77. Verify source hashes, frame count/dimensions, full decode and mixed audio levels. No subjective listening claim.
''',encoding='utf8')
print('Assembled six scenes, 80 seconds, native 960x600',flush=True)

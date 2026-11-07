"""Editable film around the accepted native driving captures; never fabricates footage."""
from pathlib import Path
import html,json

ROOT=Path(__file__).resolve().parent
SCENES=[('reveal',6,'Rolling reveal'),('hop',10,'Front hopping'),('wheel',5,'Wheel and suspension detail'),('left',8,'Left three-wheel glide'),('right',8,'Right three-wheel glide'),('exit',11,'Cruising exit')]
style='''
@font-face{font-family:Barlow;src:url("assets/fonts/Barlow-Regular.ttf");font-weight:400}
@font-face{font-family:BarlowCondensed;src:url("assets/fonts/BarlowCondensed-Bold.ttf");font-weight:700}
#root{position:absolute;inset:0;overflow:hidden;font-family:Barlow,sans-serif}
#root .footage{position:absolute;inset:0;width:960px;height:600px;object-fit:contain;z-index:0}
#root .caption{position:absolute;inset:0;z-index:2;pointer-events:none}
#root .label{position:absolute;left:96px;top:60px;color:#fff7ed;text-shadow:0 2px 4px #151014,0 0 2px #151014;display:flex;flex-direction:column;gap:4px}
#root .headline{font-family:BarlowCondensed,sans-serif;font-size:46px;font-weight:700;line-height:1;letter-spacing:1px;white-space:nowrap}
#root .subline{font-family:Barlow,sans-serif;font-size:19px;line-height:1.2;letter-spacing:2px;white-space:nowrap}
'''
hosts=[];timing=[];story=[];start=0
for sid,duration,description in SCENES:
    title=sid in ('reveal','exit')
    labelStart=.4 if sid=='reveal' else 7.0
    labelDuration=3.6 if sid=='reveal' else 3.7
    caption=f'''<div id="{sid}-caption" class="clip caption" data-start="{labelStart}" data-duration="{labelDuration}" data-track-index="1" data-layout-allow-overlap="true"><div id="{sid}-label" class="label"><div id="{sid}-headline" class="headline" data-var-text="vehicle">LA CATRINA</div><div id="{sid}-subline" class="subline" data-var-text="subtitle">STREET SHOW</div></div></div>''' if title else ''
    timeline=f'''tl.fromTo("#{sid}-label",{{opacity:0}},{{opacity:1,duration:.30,ease:"power2.out"}},{labelStart});tl.to("#{sid}-label",{{opacity:0,duration:.30,ease:"power2.in"}},{labelStart+labelDuration-.30});''' if title else ''
    content=f'''<template><style>{style}</style><div id="root" data-composition-id="{sid}" data-width="960" data-height="600"><video id="{sid}-video" class="clip footage" data-start="0" data-duration="{duration}" data-media-start="0" data-track-index="0" src="assets/video/{sid}.mp4" muted playsinline preload="metadata" data-layout-allow-overlap="true"></video>{caption}</div><script>const tl=gsap.timeline({{paused:true}});{timeline}window.__timelines["{sid}"]=tl;</script></template>'''
    (ROOT/'compositions'/f'{sid}.html').write_text(content,encoding='utf-8')
    hosts.append(f'<div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{start}" data-duration="{duration}" data-width="960" data-height="600" data-track-index="0" data-track-kind="graphics"></div>')
    timing.append({'id':sid,'start':start,'duration':duration,'frames':duration*30,'description':description,'source':f'assets/video/{sid}.mp4','sourceStart':0,'labelStart':labelStart if title else None,'labelDuration':labelDuration if title else 0})
    story.append(f'## Frames {start*30}–{(start+duration)*30-1} / {start}–{start+duration}s: {description}\n\nPlanned source: assets/video/{sid}.mp4; {duration}s at 1×. Capture the actual shared-physics motion with no HUD. '+(f'Title window: {start+labelStart:.1f}–{start+labelStart+labelDuration:.1f}s in the full film. Keep it in the upper margin and verify that it clears the car.' if title else 'No text; wheels and body motion carry the shot.')+'\n')
    start+=duration
assert start==48
audio='''<audio id="sunset-pulse" class="clip" src="assets/audio/catrina-sunset-pulse.wav" data-start="0" data-duration="48" data-track-index="2" data-audio-role="music" data-volume="1" data-fade-in="0.35" data-fade-out="0.25"></audio>'''
# An optional separate action track is built only from the accepted source telemetry.
if (ROOT/'assets/audio/catrina-action.wav').exists():
    audio+='''<audio id="street-action" class="clip" src="assets/audio/catrina-action.wav" data-start="0" data-duration="48" data-track-index="3" data-audio-role="sfx" data-volume="1" data-fade-in="0.3" data-fade-out="1"></audio>'''
variables=json.dumps([{'id':'vehicle','type':'string','label':'Vehicle title','default':'LA CATRINA'},{'id':'subtitle','type':'string','label':'Subtitle','default':'STREET SHOW'}],separators=(',',':'))
main=f'''<!doctype html><html lang="en" data-composition-variables='{variables}'><head><meta charset="utf-8"><meta name="viewport" content="width=960,height=600"><title>La Catrina / Street Show</title><script src="assets/vendor/gsap.min.js"></script><style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:960px;height:600px;overflow:hidden;background:#202122}}#root{{position:relative;width:960px;height:600px;overflow:hidden}}</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="48" data-width="960" data-height="600" data-fps="30">{''.join(hosts)}{audio}</div><script>window.__timelines=window.__timelines||{{}};window.__timelines["main"]=gsap.timeline({{paused:true}});</script></body></html>'''
(ROOT/'index.html').write_text(main,encoding='utf-8')
(ROOT/'STORYBOARD.md').write_text('# La Catrina / Street Show\n\nPrepared six-shot edit: 48seconds/1440frames. Production capture remains gated on two independent scores of at least8/10 for the exact model. This storyboard does not assert that accepted footage or a final video exists. Planned motion is unretimed, with no opening card delaying the car.\n\n'+'\n'.join(story),encoding='utf-8')
(ROOT/'edit-manifest.json').write_text(json.dumps({'duration':48,'frames':1440,'width':960,'height':600,'fps':30,'scenes':timing,'footageTreatment':'full frame,1x; no crop,upscale,interpolation,grade or fabricated animation','music':'assets/audio/catrina-sunset-pulse.wav','action':'assets/audio/catrina-action.wav' if (ROOT/'assets/audio/catrina-action.wav').exists() else None},indent=2)+'\n')
print('Prepared six editable native scenes,48seconds/1440frames. Footage and gate verification remain required.')

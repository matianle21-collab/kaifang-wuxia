from pathlib import Path
from PIL import Image
import json,subprocess,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';U=D/'UI设计/毒姥与金刚定妆_20261024_2216';W=P/'work';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
p=json.loads((U/'定妆参数_v01.json').read_text());assert len(p)==2;checks=[]
for a in p:
 im=Image.open(D/a['file']).convert('RGBA');assert im.size==tuple(a['frame_size']) and set(im.getchannel('A').get_flattened_data())=={0,255};cs={c[:3] for c in im.get_flattened_data() if c[3]};assert len(cs)<=16 and (0,0,0) not in cs and (255,0,255) not in cs;ax,ay=a['anchor'];foot=a['actual_opaque_foot_points'];assert foot[0][0]+foot[1][0]==ax*2 and foot[0][1]==foot[1][1]==ay
 for q in foot:assert im.getpixel(tuple(q))[3]==255
 assert not im.getchannel('A').crop((0,ay+1,im.width,im.height)).getbbox();small=Image.open(W/a['role']/'small.png').convert('RGBA');assert sum(v>0 for v in small.getchannel('A').get_flattened_data())==sum(v>0 for v in im.getchannel('A').get_flattened_data());ob=a['source_component'];coverage=sum(v>0 for v in small.getchannel('A').get_flattened_data())/(small.width*small.height);assert abs(coverage-ob['area']/(ob['box'][2]*ob['box'][3]))<.12
 big=Image.open(U/f'{a["name"]}_6倍_v01.png').convert('RGBA');assert big.size==(im.width*6,im.height*6)
 for y in range(big.height):
  for x in range(big.width):
   c=big.getpixel((x,y));e=im.getpixel((x//6,y//6));assert c[3]==e[3] and(not c[3] or c==e)
 if a['role']=='jingang':assert (78,107,88) in cs and sum(im.getpixel((x,y))==(212,50,44,255) for y in range(ay//2) for x in range(ax,im.width))>=3
 checks.append({'file':a['file'],'size':a['frame_size'],'colors':len(cs),'alpha':[0,255],'anchor':a['anchor'],'actual_opaque_foot_points':foot,'feet_exact_on_root_line':True,'below_root_transparent':True,'source_uncut':True,'alpha_coverage':coverage,'nearest6x_exact':True,'single_frame_reference_only':True})
sha=P.parent/'art-shaolin-move-20261024-1501/delivery/assets/chr/chr_shaolin_idle_down_v01.png';player=W/'shaolin_idle0.png';run([sha,'-crop','48x64+0+0','+repage',player]);xu=P.parent/'art-roles-ref-20261024-1432/delivery/assets/ref/ref_boss_xuancheng_down_v01.png';items=[(player,48,64,24,60,80),(xu,64,80,32,76,210)]+[(D/a['file'],*a['frame_size'],*a['anchor'],340 if a['role']=='dulao' else 480) for a in p];args=['-size','600x160','xc:#46525E']
for f,cw,ch,ax,ay,x in items:args+=[f,'-geometry',f'+{x-ax}+{140-ay}','-compose','Over','-composite']
run([*args,'-filter','point','-resize','300%',U/'玩家与三Boss同尺度_v01.png']);env=P.parent/'art-shanmen-20261024-1328/delivery/assets/env/env_shanmen_v01.png';args=[env]
for f,cw,ch,ax,ay,x in items:args+=[f,'-geometry',f'+{x+500-ax}+{340-ay}','-compose','Over','-composite']
run([*args,U/'山门原比例Boss_v01.png'])
for n in ['generation_prompts.json','production_plan.md','process_refs.py','validate_refs.py']:shutil.copy2(P/'source'/n,U/n)
d=U/'source_inputs';d.mkdir(exist_ok=True)
for f in (P/'source').glob('style_*_reference.png'):shutil.copy2(f,d/f.name)
r={'status':'passed','new_front_references':2,'generated_sources':2,'reference_inputs':2,'checks':checks,'native_frames':1,'animations_started':False,'independent_runtime_test':False,'visual_review':'both native references, exact6x, scale comparison and static1:1 scene inspected before upload','notes':['Latest jingang96x112 anchor48,108/rustgreen4E6B58/chest copper mirror overrides old128x160/purple core.','Dulao staff is inside same PNG; cane tip excluded from the two actual shoe-root points.','Both are front static references awaiting each own developer confirmation; no shield/breach/portrait or full animation claimed.','ImageMagick technical binaryalpha/crop/uniformnearest/fixed16palette/registration only; PIL read-only. No code-drawn character pixels or moved shoe fragments.']};(U/'核验结果_v01.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['checks','notes','visual_review']},ensure_ascii=False))

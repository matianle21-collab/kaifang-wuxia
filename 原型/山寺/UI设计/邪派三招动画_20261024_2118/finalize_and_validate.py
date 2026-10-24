from pathlib import Path
from PIL import Image
import subprocess,json,hashlib,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';UI=D/'UI设计/邪派三招动画_20261024_2118';W=P/'work';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
p=json.loads((UI/'三招动画参数_v01.json').read_text());base=P.parent/'art-xiepai-head-move-20261024-1935/delivery';combat=P.parent/'art-xiepai-combat-20261024-2038/delivery';old=json.loads((base/'UI设计/邪派移动动画_20261024_1935/动画参数_v01.json').read_text())+json.loads((combat/'UI设计/邪派基础战斗_20261024_2038/基础战斗参数_v01.json').read_text());index=[{k:a[k] for k in ['file','action','direction','frame_size','frame_count','fps','anchor'] if k in a}|{'delivery':'20261024-2118' if a in p else '20261024-1935' if a['action'] in ['idle','walk'] else '20261024-2038','phase':a.get('phase'),'hold_frames':a.get('hold_frames',[])} for a in old+p];assert len(index)==33 and sum(a['frame_count'] for a in index)==132
(UI/'邪派完整132帧索引_v01.json').write_text(json.dumps(index,ensure_ascii=False,indent=2));oldcolors=set();colors=set();rows=[]
for a in old:
 f=(base if a['action'] in ['idle','walk'] else combat)/a['file'];im=Image.open(f).convert('RGBA');oldcolors|={c[:3] for c in im.get_flattened_data() if c[3]};assert im.size==tuple([48*a['frame_count'],64])
for a in p:
 action,dr,n=a['action'],a['direction'],a['frame_count'];file=D/a['file'];im=Image.open(file).convert('RGBA');assert im.size==(48*n,64);assert set(im.getchannel('A').get_flattened_data())=={0,255};cs={c[:3] for c in im.get_flattened_data() if c[3]};colors|=cs;assert (0,0,0) not in cs and (255,0,255) not in cs;assert a['anchor']==[24,60] and a['fps']==12 and not a['loop'];seq=a['gif_playback_frame_order'];args=[];dt=[]
 for j,i in enumerate(seq):
  delay=60 if j==len(seq)-1 else 80 if action=='huagongsan' and i==1 else [8,8,9][j%3];args+=['-delay',str(delay),'(',str(W/dr/action/f'{i:02}.png'),'-background','#46525E','-alpha','remove','-alpha','off','-filter','point','-resize','600%',')'];dt.append(delay*10)
 run([*args,'-loop','0',UI/f'{action}_{dr}_相位预览_v01.gif']);gif=Image.open(UI/f'{action}_{dr}_相位预览_v01.gif');assert gif.n_frames==len(seq);times=[]
 for j in range(gif.n_frames):gif.seek(j);times.append(gif.info['duration'])
 assert times==dt
 hashes=[]
 for i,rec in enumerate(a['frames']):
  f=im.crop((i*48,0,i*48+48,64));wim=Image.open(W/dr/action/f'{i:02}.png').convert('RGBA');assert f.tobytes()==wim.tobytes();hashes.append(hashlib.sha256(f.tobytes()).hexdigest());assert rec['index']==i and rec['anchor']==[24,60] and rec['integer_horizontal_margin_registration']==0;assert abs(rec['projected_root_x_error_px'])<=.5;ox,oy=rec['registered_offset'];sw,sh=rec['scaled_size'];assert ox>=1 and ox+sw<=47 and oy>=1 and oy+sh<=64;small=Image.open(W/dr/action/f'{i:02}_colored.png').convert('RGBA');assert sum(v>0 for v in small.getchannel('A').get_flattened_data())==sum(v>0 for v in f.getchannel('A').get_flattened_data());assert not f.getchannel('A').crop((0,61,48,64)).getbbox()
 assert len(set(hashes))==n,(action,dr,'duplicate frame')
 big=Image.open(UI/f'{action}_{dr}_6倍_v01.png').convert('RGBA');assert big.size==(im.width*6,im.height*6)
 for y in range(big.height):
  for x in range(big.width):
   q=big.getpixel((x,y));e=im.getpixel((x//6,y//6));assert q[3]==e[3] and(not q[3] or q==e)
 if action=='dushazhang':assert a['phase']=={'windup':[0],'palm':[1],'flick':[2],'recover':[3]}
 elif action=='shehunshu':assert a['phase']=={'charge_loop':[0,1,2,3],'release':[4,5]}
 else:assert a['phase']=={'aim':[0,1],'aim_hold_frame':1,'throw_recover':[2,3,4]} and a['hold_frames']==[1]
 rows.append({'file':a['file'],'frames':n,'colors':len(cs),'alpha':[0,255],'fixed_root':[24,60],'projected_root_rounding_error_max':max(abs(r['projected_root_x_error_px']) for r in a['frames']),'source_uncut':True,'no_pose_pixels_lost_in_canvas':True,'forced_margin_shift':False,'distinct_frames':n,'nearest6x':True,'gif_playback_frames':len(seq),'gif_durations_ms':dt,'phase':a['phase']})
assert len(colors|oldcolors)<=16 and len(p)==9 and sum(a['frame_count'] for a in p)==45
# Original scale static scene comparison only; no game execution.
env=P.parent/'art-shanmen-20261024-1328/delivery/assets/env/env_shanmen_v01.png';args=[env]
for row,dr in enumerate(['down','left','up']):
 for col,(ac,i) in enumerate([('old',0),('dushazhang',0),('dushazhang',2),('shehunshu',2),('shehunshu',4),('huagongsan',1),('huagongsan',3)]):
  f=base/'assets/chr'/f'chr_xiepai_idle_{dr}_v01.png' if ac=='old' else W/dr/ac/f'{i:02}.png'
  if ac=='old':out=W/f'old_idle_{dr}.png';run([f,'-crop','48x64+0+0','+repage',out]);f=out
  args += [str(f),'-geometry',f'+{670+col*90-24}+{650+row*90-60}','-compose','Over','-composite']
run([*args,UI/'山门原比例三招_v01.png'])
for name in ['skill_prompts.json','skill_fix_prompts.json','frame_registration.json','process_skills.py','finalize_and_validate.py']:
 shutil.copy2(P/'source'/name,UI/name)
inputs=UI/'source_inputs';inputs.mkdir(exist_ok=True)
for f in (P/'source').glob('*reference.png'):shutil.copy2(f,inputs/f.name)
for f in (P/'source').glob('left_pose_*_original_crop.png'):shutil.copy2(f,inputs/f.name)
r={'status':'passed','new_strips':9,'new_frames':45,'combined_strips':33,'combined_frames':132,'new_colors':len(colors),'combined_colors':len(colors|oldcolors),'source_images':len(list((P/'source').glob('xiepai_skills_*_generated.png'))),'derived_reference_images':3,'native_alpha':[0,255],'frame_size':[48,64],'anchor':[24,60],'fps':12,'no_forced_margin_shifts':True,'independent_runtime_test':False,'visual_review':'all three direction sheets and static1:1 scene are inspected before upload','notes':['Single dao secured to back frees casting hands; independent FX27-29 not claimed.','Five generated sources (3 first drafts and 2 direction corrections), selected frames only.','All scale normalized per direction by41px first charging stance, no per-frame stretch or program drawing.','GIF charge0-3 twice then release4-5; aim frame1 held800ms, last600ms for review. Native12fps/controller.','Old base87PNG untouched; full132 index combines three deliveries.'],'checks':rows};(UI/'核验结果_v01.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['checks','notes','visual_review']},ensure_ascii=False))

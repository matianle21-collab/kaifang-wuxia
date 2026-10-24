from pathlib import Path
from PIL import Image
import subprocess,json,hashlib,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';UI=D/'UI设计/邪派基础战斗_20261024_2038';W=P/'work';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
params=json.loads((UI/'基础战斗参数_v01.json').read_text());base=P.parent/'art-xiepai-head-move-20261024-1935/delivery';old=json.loads((base/'UI设计/邪派移动动画_20261024_1935/动画参数_v01.json').read_text());idx=[]
for a in old+params:idx.append({k:a[k] for k in ['file','action','direction','frame_size','frame_count','fps','anchor','loop','hold_frames'] if k in a}|{'delivery':'20261024-2038' if a in params else '20261024-1935'})
assert len(idx)==24 and sum(a['frame_count'] for a in idx)==87;(UI/'邪派基础87帧索引_v01.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2));colors=set();oldcolors=set();checks=[];margin=[];low=[]
for a in old:
 im=Image.open(base/a['file']).convert('RGBA');assert im.size==(48*a['frame_count'],64);oldcolors|={c[:3] for c in im.get_flattened_data() if c[3]}
for a in params:
 ac,dr,n=a['action'],a['direction'],a['frame_count'];im=Image.open(D/a['file']).convert('RGBA');assert im.size==(48*n,64);assert set(im.getchannel('A').get_flattened_data())=={0,255};cs={v[:3] for v in im.get_flattened_data() if v[3]};colors|=cs;assert len(cs)<=16 and (0,0,0) not in cs and (255,0,255) not in cs;assert a['anchor']==[24,60] and a['fps']==12 and not a['loop'];assert a['frame_order']==list(range(n));assert a['hold_frames']==([3] if ac=='down' else [])
 hashes=[]
 for i,r in enumerate(a['frames']):
  f=im.crop((48*i,0,48*(i+1),64));native=Image.open(W/dr/ac/f'{i:02}.png').convert('RGBA');assert f.tobytes()==native.tobytes();hashes.append(hashlib.sha256(f.tobytes()).hexdigest());assert r['index']==i and r['anchor']==[24,60];ox,oy=r['registered_offset'];sw,sh=r['scaled_size'];assert ox>=0 and ox+sw<=48 and oy>=1 and oy+sh<=64;small=Image.open(W/dr/ac/f'{i:02}_colored.png').convert('RGBA');assert sum(v>0 for v in small.getchannel('A').get_flattened_data())==sum(v>0 for v in f.getchannel('A').get_flattened_data());assert max(abs(v) for v in r['integer_margin_registration'])<=2
  if any(r['integer_margin_registration']):margin.append({'direction':dr,'action':ac,'frame':i,'registration':r['integer_margin_registration']})
  below=[(x,y) for y in range(61,64) for x in range(48) if f.getpixel((x,y))[3]]
  if below:low.append({'direction':dr,'action':ac,'frame':i,'pixels_below60':below})
  assert all(abs(e-reg)<=.5 for e,reg in zip(r['projected_ground_rounding_error'],r['integer_margin_registration']))
 assert len(set(hashes))==n,(ac,dr,'duplicate frame')
 big=Image.open(UI/f'{ac}_{dr}_6倍_v01.png').convert('RGBA');assert big.size==(im.width*6,384)
 for y in range(big.height):
  for x in range(big.width):
   q=big.getpixel((x,y));e=im.getpixel((x//6,y//6));assert q[3]==e[3] and(not q[3] or q==e)
 gif=Image.open(UI/f'{ac}_{dr}_播放预览_v01.gif');assert gif.n_frames==n;dur=[]
 for i in range(n):gif.seek(i);dur.append(gif.info['duration'])
 assert dur==[(600 if i==n-1 else [80,80,90][i%3]) for i in range(n)]
 if ac.startswith('atk'):assert a['phase']=={'windup':[0],'strike':[1],'recover':[2]}
 checks.append({'file':a['file'],'size':list(im.size),'frames':n,'colors':len(cs),'alpha':[0,255],'anchor':[24,60],'source_uncut':True,'canvas_loses_no_opaque_pixels':True,'distinct_frames':n,'nearest6x':True,'gif_frames':n,'gif_durations_ms':dur,'hold_frames':a['hold_frames']})
assert len(params)==18 and sum(a['frame_count'] for a in params)==57 and len(colors|oldcolors)<=16
# 1:1 scene, never a game runtime screenshot.
env=P.parent/'art-shanmen-20261024-1328/delivery/assets/env/env_shanmen_v01.png';args=[env]
for row,dr in enumerate(['down','left','up']):
 for col,(ac,i) in enumerate([('old',0),('atk1',1),('atk2',1),('atk3',1),('hit',0),('roll',1),('down',3)]):
  if ac=='old':src=base/'assets/chr'/f'chr_xiepai_idle_{dr}_v01.png';f=W/f'old_idle_{dr}.png';run([src,'-crop','48x64+0+0','+repage',f])
  else:f=W/dr/ac/f'{i:02}.png'
  args += [str(f),'-geometry',f'+{670+col*90-24}+{650+row*90-60}','-compose','Over','-composite']
run([*args,UI/'山门原比例基础战斗_v01.png'])
inputs=UI/'source_inputs';inputs.mkdir(exist_ok=True)
for p in (P/'source').glob('*edit_target.png'):shutil.copy2(p,inputs/p.name)
for p in (P/'source').glob('*reference.png'):shutil.copy2(p,inputs/p.name)
for dr in ['down','left','up']:shutil.copy2(base/'UI设计/邪派移动动画_20261024_1935'/f'chr_xiepai_idle_{dr}_6倍_v01.png',inputs/f'approved_xiepai_idle_{dr}_6x.png')
for name in ['combat_prompts.json','weapon_fix_prompts.json','four_compact_prompt.json','up_cut_contact_prompt.json','four_compact_reference_sources.json','frame_registration.json','process_combat.py','finalize_and_validate.py']:shutil.copy2(P/'source'/name,UI/name)
r={'status':'passed','new_strips':18,'new_frames':57,'base_strips':24,'base_frames':87,'new_colors':len(colors),'combined_colors':len(colors|oldcolors),'source_images':7,'derived_reference_images':9,'alpha':[0,255],'frame_size':[48,64],'anchor':[24,60],'fps':12,'margin_registration':margin,'pixels_below60':low,'independent_runtime_test':False,'visual_review':'3 complete direction sheets, roll inversion, prone ending and static1:1 scene inspected before upload','notes':['Only base combat completed; dushazhang/huagongsan/shehunshu still pending; row10/11 remain partial.','Four poses from standalone compact correction, one rear slash contact from standalone correction; geometry is AI artwork, no body drawing by code.','Four left poses have1–2px horizontal margin registration; left final prone width47px uses full edge and remains uncut.','GIF ends600ms for review and loops; game12fps with down frame3 held by controller.','Original movement PNGs unchanged; head and dao embedded; no separate head runtime assets.'],'checks':checks};(UI/'核验结果_v01.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['checks','notes','visual_review','pixels_below60']},ensure_ascii=False));print('below60',[(v['direction'],v['action'],v['frame'],len(v['pixels_below60'])) for v in low])

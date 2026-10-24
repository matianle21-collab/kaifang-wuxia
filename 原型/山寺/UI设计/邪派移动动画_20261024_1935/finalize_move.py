from pathlib import Path
from PIL import Image
import subprocess,json,shutil,hashlib
P=Path(__file__).resolve().parents[1];D=P/'delivery';W=P/'work';UI=D/'UI设计/邪派移动动画_20261024_1935';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
r=json.loads((P/'source/frame_registration.json').read_text());params=[]
for e in r:
 dr,a,i=e['direction'],e['action'],e['index'];f=W/dr/a
 # Keep blade pixels outside lower-limb registration region; no full-width crop of weapon.
 run([f/f'{i:02}_reg.png','-region','16x31+16+0','-channel','A','-evaluate','set','0','+channel','+region','-region','27x11+11+53','-channel','A','-evaluate','set','0','+channel','+region',f/f'{i:02}_torso.png'])
 run([f/f'{i:02}_torso.png',f/f'{i:02}_legs.png','-compose','Over','-composite',f/f'{i:02}_body.png']);run([f/f'{i:02}_body.png',f/f'{i:02}_head.png','-compose','Over','-composite',f/f'{i:02}_runtime.png']);e['lower_limb_clear_region']=[11,53,27,11]
for dr in ['down','left','up']:
 panels=[]
 for a,n in [('idle',4),('walk',6)]:
  f=W/dr/a
  for key in ['runtime','head','body','shaolin_body','shaolin_normalized']:
   target=D/'assets/chr'/f'chr_xiepai_{a}_{dr}_v01.png' if key=='runtime' else UI/'layers/head'/f'chr_head_default_{a}_{dr}_v01.png' if key=='head' else UI/'layers'/key/f'{key}_{a}_{dr}_v01.png';run([*[f/f'{i:02}_{key}.png' for i in range(n)],'+append',target])
  target=D/'assets/chr'/f'chr_xiepai_{a}_{dr}_v01.png';six=UI/f'chr_xiepai_{a}_{dr}_6倍_v01.png';run([target,'-filter','point','-resize','600%',six]);args=[]
  for i in range(n):args+=['-delay',str([8,8,9][i%3]),'(',str(f/f'{i:02}_runtime.png'),'-filter','point','-resize','600%',')']
  run([*args,'-loop','0','-dispose','background',UI/f'chr_xiepai_{a}_{dr}_循环_v01.gif'])
  params.append({'file':target.relative_to(D).as_posix(),'action':a,'direction':dr,'frame_size':[48,64],'frame_count':n,'fps':12,'loop':True,'anchor':[24,60],'gap':0,'frame_order':list(range(n)),'hold_frames':[],'head_embedded':True,'weapon_embedded':'dao','source_pose':'chr_shaolin_'+a+'_'+dr+'_v01.png','remaining_actions':['atk1','atk2','atk3','hit','roll','down','dushazhang','huagongsan','shehunshu'],'source_layers_are_editable_only':True})
 for key in ['original','runtime']:
  for a in ['idle','walk']:
   target=P.parent/'art-shaolin-move-20261024-1501/delivery/assets/chr'/f'chr_shaolin_{a}_{dr}_v01.png' if key=='original' else D/'assets/chr'/f'chr_xiepai_{a}_{dr}_v01.png';out=W/f'final_{key}_{a}_{dr}.png';run([target,'-background','none','-gravity','NorthWest','-extent','288x64',out]);panels.append(out)
 run([*panels,'-append','-filter','point','-resize','600%',UI/f'少林与邪派同帧_{dr}_6倍_v01.png'])
 # Retain production head-layer preview as source only, current request embeds head in runtime body.
 p=UI/f'换装逐帧_{dr}_6倍_v01.png'
 if p.exists():shutil.move(str(p),str(W/f'working_head_preview_{dr}.png'))
(P/'source/frame_registration.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));(UI/'动画参数_v01.json').write_text(json.dumps(params,ensure_ascii=False,indent=2))
# Scene 1:1 composite: down/left/up rows, original Shaolin and Xiepai idle and walk phases.
env=P.parent/'art-shanmen-20261024-1328/delivery/assets/env/env_shanmen_v01.png';args=[env]
for row,dr in enumerate(['down','left','up']):
 for col,(who,a,i) in enumerate([('shaolin','idle',0),('xiepai','idle',0),('xiepai','walk',0),('xiepai','walk',3)]):
  src=W/dr/a/f'{i:02}_{"original" if who=="shaolin" else "runtime"}.png';args += [str(src),'-geometry',f'+{790+col*90-24}+{650+row*92-60}','-compose','Over','-composite']
run([*args,UI/'山门原比例对照_v01.png'])
for n in ['move_prompts.json','up_fix_prompt.json','frame_registration.json','process_move.py','register_lower_legs.py','finalize_move.py']:
 shutil.copy2(P/'source'/n,UI/n)
print('Finalized',len(params),'native strips',sum(p['frame_count'] for p in params),'poses')

from pathlib import Path
from PIL import Image
import subprocess,json,re
P=Path(__file__).resolve().parents[1];W=P/'work';D=P/'delivery';UI=D/'UI设计/邪派移动动画_20261024_1935';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
r=json.loads((P/'source/frame_registration.json').read_text())
for e in r:
 dr,a,i=e['direction'],e['action'],e['index'];f=W/dr/a;of=f/f'{i:02}_original.png';low=f/f'{i:02}_lower_full.png';run([of,'-crop','48x11+0+53','+repage',low]);s=run([low,'-alpha','extract','-threshold','50%','-define','connected-components:verbose=true','-connected-components','8','null:']);ids=[]
 for line in s.splitlines():
  m=re.search(r'\s*(\d+): (\d+)x(\d+)\+(\d+)\+(\d+) ([\d.]+),([\d.]+) ([\de+.-]+) srgb\(255,255,255\)',line)
  if m:
   k,w,h,x,y,cx,cy,area=m.groups()
   if float(area)>=15 or 18<=float(cx)<=31:ids.append(int(k))
 mask=f/f'{i:02}_leg_components.png';run([low,'-alpha','extract','-threshold','50%','-define','connected-components:keep='+','.join(map(str,ids)),'-connected-components','8','-auto-level','-threshold','0',mask]);cut=f/f'{i:02}_lower_cut.png';run([low,mask,'-alpha','off','-compose','CopyOpacity','-composite',cut]);run([cut,'-alpha','extract',f/'leg_a.png']);run([cut,'-alpha','off','+dither','-remap',W/'headpalette.png',f/'leg_rgb.png']);col=f/f'{i:02}_lower_color.png';run([f/'leg_rgb.png',f/'leg_a.png','-alpha','off','-compose','CopyOpacity','-composite',col]);leg=f/f'{i:02}_legs.png';run(['-size','48x64','xc:none',col,'-geometry','+0+53','-compose','Over','-composite',leg]);run([f/f'{i:02}_torso.png',leg,'-compose','Over','-composite',f/f'{i:02}_body.png']);run([f/f'{i:02}_body.png',f/f'{i:02}_head.png','-compose','Over','-composite',f/f'{i:02}_runtime.png']);e.update(lower_leg_region=[0,53,48,11],lower_leg_component_ids=ids,lower_leg_registration='keep leg components area>=15 or centroid x18..31, remove only detached source staff tips; original pixel positions unchanged')
(P/'source/frame_registration.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
for dr in ['down','left','up']:
 imgs=[]
 for act,n in [('idle',4),('walk',6)]:
  f=W/dr/act
  for key in ['runtime','head','body','shaolin_body','shaolin_normalized']:
   target=D/'assets/chr'/f'chr_xiepai_{act}_{dr}_v01.png' if key=='runtime' else UI/'layers/head'/f'chr_head_default_{act}_{dr}_v01.png' if key=='head' else UI/'layers'/key/f'{key}_{act}_{dr}_v01.png';run([*[f/f'{i:02}_{key}.png' for i in range(n)],'+append',target])
 for key in ['shaolin_normalized','runtime','head']:
  for act in ['idle','walk']:
   src=UI/'layers/shaolin_normalized'/f'shaolin_normalized_{act}_{dr}_v01.png' if key=='shaolin_normalized' else (D/'assets/chr'/f'chr_xiepai_{act}_{dr}_v01.png' if key=='runtime' else UI/'layers/head'/f'chr_head_default_{act}_{dr}_v01.png');out=W/f'{key}_{act}_{dr}_panel.png';run([src,'-background','none','-gravity','NorthWest','-extent','288x64',out]);imgs.append(out)
 run([*imgs,'-append','-filter','point','-resize','600%',UI/f'换装逐帧_{dr}_6倍_v01.png'])
print('Updated lower legs',len(r))

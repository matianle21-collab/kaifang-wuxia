from pathlib import Path
from PIL import Image
import subprocess,json,hashlib,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';W=P/'work';UI=D/'UI设计/邪派移动动画_20261024_1935'
M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
pal=['2B211E','3B2A20','78523D','DAB082','B9865D','806047','514038','15121A','2B2335','4A2A6B','70508A','7BE38A','466B48','C8C8C8','8C929D','4C5765'];headpal=pal[:7]
for name,colors in [('palette',pal),('headpalette',headpal)]:run([v for c in colors for v in ['-size','1x1','xc:#'+c]]+['+append',W/f'{name}.png'])
(UI/'调色板_v01.json').write_text(json.dumps({'xiepai':pal,'common_head':headpal,'note':'通用头保留原少林逐帧轮廓与坐标，归并为原少林调色板中已有的7色子集；不改旧PNG。'},ensure_ascii=False,indent=2))
objs=json.loads((P/'source/objects.json').read_text());records=[]
def remap(src,pal,out):
 run([src,'-alpha','extract',W/'alpha.png']);run([src,'-alpha','off','+dither','-remap',pal,W/'rgb.png']);run([W/'rgb.png',W/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite',out])
def place(src,size,offset,out):run(['-size',size,'xc:none',src,'-geometry',f'+{offset[0]}+{offset[1]}','-compose','Over','-composite',out])
for dr in ['down','left','up']:
 src=P/'source'/f'imagegen_move_{dr}{"_fix" if dr=="up" else ""}_v01.png'
 for act,n,start in [('idle',4,0),('walk',6,4)]:
  folder=W/dr/act;folder.mkdir(parents=True,exist_ok=True);orig=P.parent/'art-shaolin-move-20261024-1501/delivery/assets/chr'/f'chr_shaolin_{act}_{dr}_v01.png'
  outs={k:[] for k in ['runtime','head','body','shaolin_body','shaolin_normalized']}
  for i in range(n):
   ob=objs[dr][start+i];x,y,w,h=ob['box'];small=folder/f'{i:02}_small.png';mask=folder/f'{i:02}_mask.png';run([src,'-alpha','extract','-threshold','80%','-define',f'connected-components:keep={ob["id"]}','-connected-components','8','-auto-level','-threshold','0',mask]);run([src,mask,'-alpha','off','-compose','CopyOpacity','-composite','-compose','Over','-crop',f'{w}x{h}+{x}+{y}','+repage','-filter','point','-resize',f'{round(w*41/h)}x41!',small]);colored=folder/f'{i:02}_colored.png';remap(small,W/'palette.png',colored)
   of=folder/f'{i:02}_original.png';run([orig,'-crop',f'48x64+{48*i}+0','+repage',of]);oi=Image.open(of).convert('RGBA');ni=Image.open(colored).convert('RGBA');oc=[x for yy in range(20,28) for x in range(16,32) if oi.getpixel((x,yy))[3]];nc=[x for yy in range(0,8) for x in range(ni.width) if ni.getpixel((x,yy))[3] and ni.getpixel((x,yy))[:3] in [tuple(bytes.fromhex(v)) for v in headpal]];dx=round(sum(oc)/len(oc)-sum(nc)/len(nc));reg=folder/f'{i:02}_reg.png';place(colored,'48x64',(dx,20),reg)
   # Exact head region and lower-leg geometry from the approved native pose.
   hc=folder/f'{i:02}_head_crop.png';run([of,'-crop','16x31+16+0','+repage',hc]);hr=folder/f'{i:02}_head_remap.png';remap(hc,W/'headpalette.png',hr);head=folder/f'{i:02}_head.png';place(hr,'48x64',(16,0),head)
   lc=folder/f'{i:02}_leg_crop.png';run([of,'-crop','20x11+14+53','+repage',lc]);lr=folder/f'{i:02}_leg_remap.png';remap(lc,W/'headpalette.png',lr);leg=folder/f'{i:02}_legs.png';place(lr,'48x64',(14,53),leg)
   # New outfit between head line and lower-leg line; head-only bbox clear is technical registration.
   torso=folder/f'{i:02}_torso.png';run([reg,'-region','16x31+16+0','-channel','A','-evaluate','set','0','+channel','+region','-crop','48x53+0+0','+repage','-background','none','-gravity','NorthWest','-extent','48x64',torso]);body=folder/f'{i:02}_body.png';run([torso,leg,'-compose','Over','-composite',body]);runtime=folder/f'{i:02}_runtime.png';run([body,head,'-compose','Over','-composite',runtime])
   # Shaolin original headless layer is retained losslessly outside identical rectangular head mask.
   oldhead=folder/f'{i:02}_oldhead.png';place(hc,'48x64',(16,0),oldhead);sb=folder/f'{i:02}_shaolin_body.png';run([oldhead,'-alpha','extract','-negate',folder/'inverse_head.png']);run([of,oldhead,'-compose','DstOut','-composite',sb]);sn=folder/f'{i:02}_shaolin_normalized.png';run([sb,head,'-compose','Over','-composite',sn])
   for key,val in [('runtime',runtime),('head',head),('body',body),('shaolin_body',sb),('shaolin_normalized',sn)]:outs[key].append(val)
   records.append({'action':act,'direction':dr,'index':i,'source':str(src.relative_to(P)),'component':ob,'scaled_size':list(ni.size),'registered_offset':[dx,20],'root_anchor':[24,60],'head_region':[16,0,16,31],'lower_leg_region':[14,53,20,11],'source_pose':str(orig),'head_and_leg_geometry':'copied from same approved Shaolin native pose; palette normalized to 7 existing colors; original PNG unchanged','frame_files':{k:str(v) for k,v in [('runtime',runtime),('head',head),('body',body),('shaolin_body',sb),('shaolin_normalized',sn)]}})
  for key,frames in outs.items():
   if key=='runtime':target=D/'assets/chr'/f'chr_xiepai_{act}_{dr}_v01.png'
   elif key=='head':target=UI/'layers/head'/f'chr_head_default_{act}_{dr}_v01.png'
   else:target=UI/'layers'/key/f'{key}_{act}_{dr}_v01.png'
   target.parent.mkdir(parents=True,exist_ok=True);run([*frames,'+append',target])
(P/'source/frame_registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
for dr in ['down','left','up']:
 imgs=[]
 for key,pr in [('shaolin_normalized',UI/'layers/shaolin_normalized'),('runtime',D/'assets/chr'),('head',UI/'layers/head')]:
  for act,n in [('idle',4),('walk',6)]:
   name=f'{key}_{act}_{dr}_v01.png' if key=='shaolin_normalized' else f'chr_{"xiepai" if key=="runtime" else "head_default"}_{act}_{dr}_v01.png';p=pr/name;out=W/f'{key}_{act}_{dr}_panel.png';run([p,'-background','none','-gravity','NorthWest','-extent','288x64',out]);imgs.append(out)
 run([*imgs,'-append','-filter','point','-resize','600%',UI/f'换装逐帧_{dr}_6倍_v01.png'])
print('Prepared',len(records),'poses')

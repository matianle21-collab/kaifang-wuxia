from pathlib import Path
from PIL import Image
import subprocess,json,re,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';U=D/'UI设计/开场角色定妆_20261024_2137';W=P/'work';M='/opt/homebrew/bin/magick';roles=json.loads((P/'source/role_specs.json').read_text())
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout

def extract(src,d,h=None):
 s=run([src,'-alpha','extract','-threshold','80%','-define','connected-components:verbose=true','-connected-components','8','null:']);obs=[]
 for line in s.splitlines():
  m=re.search(r'\s*(\d+): (\d+)x(\d+)\+(\d+)\+(\d+) ([\d.]+),([\d.]+) ([\de+.-]+) srgb\(255,255,255\)',line)
  if m:
   k,w,hh,x,y,cx,cy,area=m.groups();obs.append({'id':int(k),'box':list(map(int,[x,y,w,hh])),'area':float(area)})
 ob=max(obs,key=lambda a:a['area']);x,y,w,hh=ob['box'];mask=d/'mask.png';run([src,'-alpha','extract','-threshold','80%',mask]);out=d/'small.png';args=[src,mask,'-alpha','off','-compose','CopyOpacity','-composite','-compose','Over','-crop',f'{w}x{hh}+{x}+{y}','+repage','-filter','point'];args+=['-resize','x'+str(h)] if h else ['-resize','92x92'];run([*args,'PNG32:'+str(out)]);return out,ob

def feet(im):
 yb=im.height-1;pts={(x,y) for y in range(max(0,yb-2),im.height) for x in range(im.width) if im.getpixel((x,y))[3]};cs=[]
 while pts:
  todo=[pts.pop()];co=[]
  while todo:
   x,y=todo.pop();co.append((x,y))
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    q=x+dx,y+dy
    if q in pts:pts.remove(q);todo.append(q)
  if len(co)>=3:cs.append(co)
 cs.sort(key=len,reverse=True);cs=cs[:2];assert len(cs)==2;cs.sort(key=lambda c:min(x for x,y in c));out=[]
 for c in cs:
  yy=max(y for x,y in c);out.append({'y':yy,'xs':sorted(x for x,y in c if y==yy),'box':[min(x for x,y in c),min(y for x,y in c),max(x for x,y in c)+1,max(y for x,y in c)+1]})
 return out

def remap(src,pal,out,d):
 run([src,'-alpha','extract',d/'a.png']);run([src,'-alpha','off','+dither','-remap',pal,d/'rgb.png']);run([d/'rgb.png',d/'a.png','-alpha','off','-compose','CopyOpacity','-composite','PNG32:'+str(out)])
params=[];palettes={}
for r in roles:
 id=r['id'];d=W/id;d.mkdir(exist_ok=True);src=P/'source'/f'{id}_standing{"_fix" if id=="guanshi" else ""}_generated.png';small,ob=extract(src,d,r['height']);im=Image.open(small).convert('RGBA');f=feet(im);print(id,im.size,f,flush=True)
 # A single reference is registered from a pair of actual opaque bottom-row shoe pixels.
 if f[0]['y']!=f[1]['y']:raise RuntimeError('Foot baseline differs: '+id)
 y=f[0]['y'];pairs=[(a,c) for a in f[0]['xs'] for c in f[1]['xs'] if (a+c)%2==0];assert pairs
 a,c=min(pairs,key=lambda ac:abs(ac[0]-sum(f[0]['xs'])/len(f[0]['xs']))+abs(ac[1]-sum(f[1]['xs'])/len(f[1]['xs'])));ox=24-(a+c)//2;oy=60-y;assert ox>=1 and ox+im.width<=47 and oy>=1 and oy+im.height<=61
 por_small=None
 if r['portrait']:
  pd=d/'portrait';pd.mkdir(exist_ok=True);por_small,pob=extract(P/'source'/f'{id}_portrait{"_fix" if id=="aluo" else ""}_generated.png',pd)
 # Use one shared16-color palette per role, sampled from sprite and portrait pixel clusters.
 palette=d/'palette.png';srcs=[small]+([por_small] if por_small else []);run([*srcs,'-background','none','-gravity','NorthWest','+append','-background','#2B211E','-alpha','remove','-alpha','off','+dither','-colors','14' if id=='aluo' else '16','-unique-colors',palette]);
 if id=='aluo':run([palette,'-size','1x1','xc:#312938','-size','1x1','xc:#705067','+append',palette])
 palim=Image.open(palette).convert('RGB');palettes[id]=['%02X%02X%02X'%c for c in palim.get_flattened_data()];assert len(palettes[id])<=16
 colored=d/'colored.png';remap(small,palette,colored,d);fname=f'npc_{id}_idle_down_v01.png' if id in ['zhikeseng','guanshi','aluo'] else f'ref_npc_{id}_down_v01.png';rel=('assets/npc/' if id in ['zhikeseng','guanshi','aluo'] else 'assets/ref/')+fname;dest=D/rel;run(['-size','48x64','xc:none',colored,'-geometry',f'+{ox}+{oy}','-compose','Over','-composite','PNG32:'+str(dest)]);run([dest,'-filter','point','-resize','800%',U/f'{r["name"]}_定妆8倍_v01.png']);run([dest,'-background','#46525E','-alpha','remove','-alpha','off','-filter','point','-resize','800%',U/f'{r["name"]}_定妆灰底_v01.png']);shutil.copy2(src,D/'assets/ref'/f'ref_npc_{id}_standing_source_v01.png')
 if id=='guanshi':shutil.copy2(P/'source/guanshi_standing_generated.png',D/'assets/ref/ref_npc_guanshi_standing_initial_source_v01.png')
 rec={'role':id,'name':r['name'],'row':64 if id=='aluo' else 76,'standing':rel,'source':f'assets/ref/ref_npc_{id}_standing_source_v01.png','source_component':ob,'frame_size':[48,64],'content_size':list(im.size),'uniform_scale_height':r['height'],'registered_offset':[ox,oy],'anchor':[24,60],'actual_opaque_foot_points':[[a+ox,60],[c+ox,60]],'single_frame':True,'stage':'standing_only_requested' if id in ['zhikeseng','guanshi','aluo'] else 'front_reference_only_await_own_approval_before_animation','portrait':None,'design':r['design']}
 if r['portrait']:
  por=D/'assets/por'/f'por_{id}_v01.png';candidate=d/'portrait_canvas.png';run([por_small,'-background','none','-gravity','South','-extent','96x96','+repage',candidate]);remap(candidate,palette,por,d/'portrait');run([por,'-filter','point','-resize','400%',U/f'{r["name"]}_头像4倍_v01.png']);run([por,'-background','#46525E','-alpha','remove','-alpha','off','-filter','point','-resize','400%',U/f'{r["name"]}_头像灰底_v01.png']);shutil.copy2(P/'source'/f'{id}_portrait{"_fix" if id=="aluo" else ""}_generated.png',D/'assets/ref'/f'ref_por_{id}_source_v01.png')
  if id=='aluo':shutil.copy2(P/'source/aluo_portrait_generated.png',D/'assets/ref/ref_por_aluo_initial_source_v01.png')
  rec['portrait']={'file':'assets/por/'+por.name,'frame_size':[96,96],'source':'assets/ref/'+f'ref_por_{id}_source_v01.png','source_component':pob,'resized_size':list(Image.open(por_small).size),'fit':'isotropic max92x92, centered horizontally, bottom-aligned; no source content clipped'}
 params.append(rec)
(U/'定妆参数_v01.json').write_text(json.dumps(params,ensure_ascii=False,indent=2));(U/'调色板_v01.json').write_text(json.dumps(palettes,ensure_ascii=False,indent=2));print('Built8 standing +5 portraits')

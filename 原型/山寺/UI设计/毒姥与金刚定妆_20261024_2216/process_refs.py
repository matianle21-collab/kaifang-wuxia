from pathlib import Path
from PIL import Image
import json,subprocess,re,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';U=D/'UI设计/毒姥与金刚定妆_20261024_2216';W=P/'work';M='/opt/homebrew/bin/magick';specs=json.loads((P/'source/generation_prompts.json').read_text())
palettes={'dulao':['1B171F','2B2335','4A2A6B','70508A','5C744C','7BE38A','2B211E','514038','806047','B18A54','DAB082','B9865D','78523D','8D8A80','BCB7A9','DCD7C3'],'jingang':['1D231F','2B352E','344B40','4E6B58','71856B','3B2A20','66503B','8A4B2B','A37143','C5904E','E6B763','F6D58C','77735C','2B211E','B19B6B','D4322C']}
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout

def components(im):
 pts={(x,y) for y in range(im.height-3,im.height) for x in range(im.width) if im.getpixel((x,y))[3]};cs=[]
 while pts:
  todo=[pts.pop()];co=[]
  while todo:
   x,y=todo.pop();co.append((x,y))
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    q=x+dx,y+dy
    if q in pts:pts.remove(q);todo.append(q)
  if len(co)>2:cs.append(co)
 return sorted(cs,key=lambda c:min(x for x,y in c))
params=[]
for s in specs:
 id=s['id'];d=W/id;d.mkdir(exist_ok=True);src=P/'source'/f'{id}_standing_generated.png';text=run([src,'-alpha','extract','-threshold','80%','-define','connected-components:verbose=true','-connected-components','8','null:']);obs=[]
 for line in text.splitlines():
  m=re.search(r'\s*(\d+): (\d+)x(\d+)\+(\d+)\+(\d+) ([\d.]+),([\d.]+) ([\de+.-]+) srgb\(255,255,255\)',line)
  if m:
   k,w,h,x,y,cx,cy,area=m.groups();obs.append({'id':int(k),'box':list(map(int,[x,y,w,h])),'area':float(area)})
 ob=max(obs,key=lambda x:x['area']);x,y,w,h=ob['box'];small=d/'small.png';run([src,'(','+clone','-alpha','extract','-threshold','80%',')','-alpha','off','-compose','CopyOpacity','-composite','-compose','Over','-crop',f'{w}x{h}+{x}+{y}','+repage','-filter','point','-resize','x'+str(s['content_height']),'PNG32:'+str(small)]);im=Image.open(small).convert('RGBA');cs=components(im);assert len(cs)>=2
 if id=='jingang':cs=sorted(cs,key=len,reverse=True)[:2];cs.sort(key=lambda c:min(x for x,y in c))
 else:cs=cs[:2] # The cane is the third/rightmost contact, not a shoe.
 feet=[]
 for c in cs:
  yy=max(y for x,y in c);feet.append({'y':yy,'xs':sorted({x for x,y in c if y==yy})})
 print(id,im.size,feet,flush=True);assert feet[0]['y']==feet[1]['y'];ax,ay=s['anchor'];pairs=[(a,c) for a in feet[0]['xs'] for c in feet[1]['xs'] if (a+c)%2==0];assert pairs;a,c=min(pairs,key=lambda ac:abs(ac[0]-sum(feet[0]['xs'])/len(feet[0]['xs']))+abs(ac[1]-sum(feet[1]['xs'])/len(feet[1]['xs'])));ox=ax-(a+c)//2;oy=ay-feet[0]['y'];cw,ch=s['frame'];assert 1<=ox and ox+im.width<cw and 1<=oy and oy+im.height<=ch
 palette=d/'palette.png';run([v for color in palettes[id] for v in ['-size','1x1','xc:#'+color]]+['+append',palette]);run([small,'-alpha','extract',d/'a.png']);run([small,'-alpha','off','+dither','-remap',palette,d/'rgb.png']);colored=d/'colored.png';run([d/'rgb.png',d/'a.png','-alpha','off','-compose','CopyOpacity','-composite','PNG32:'+str(colored)]);dest=D/'assets/ref'/f'ref_boss_{id}_down_v01.png';run(['-size',f'{cw}x{ch}','xc:none',colored,'-geometry',f'+{ox}+{oy}','-compose','Over','-composite','PNG32:'+str(dest)]);run([dest,'-filter','point','-resize','600%',U/f'{s["name"]}_6倍_v01.png']);run([dest,'-background','#46525E','-alpha','remove','-alpha','off','-filter','point','-resize','600%',U/f'{s["name"]}_灰底_v01.png']);shutil.copy2(src,D/'assets/ref'/f'ref_boss_{id}_standing_source_v01.png');params.append({'role':id,'name':s['name'],'row':s['row'],'file':'assets/ref/'+dest.name,'frame_size':s['frame'],'anchor':s['anchor'],'source':'assets/ref/'+f'ref_boss_{id}_standing_source_v01.png','source_component':ob,'content_size':list(im.size),'registered_offset':[ox,oy],'actual_opaque_foot_points':[[a+ox,ay],[c+ox,ay]],'single_frame_reference':True,'stage':'front_reference_delivered_await_own_approval_before_animation','source_crop_preserves_whole_figure':True,'scale':'uniform nearest-neighbor height; width not independently stretched','staff_contact_not_counted_as_foot':id=='dulao'})
(U/'定妆参数_v01.json').write_text(json.dumps(params,ensure_ascii=False,indent=2));(U/'调色板_v01.json').write_text(json.dumps(palettes,ensure_ascii=False,indent=2));print('Built two front references')

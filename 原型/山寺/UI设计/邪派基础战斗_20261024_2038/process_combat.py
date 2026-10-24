from pathlib import Path
from PIL import Image
import json,re,subprocess,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';UI=D/'UI设计/邪派基础战斗_20261024_2038';W=P/'work';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
pal=json.loads((P.parent/'art-xiepai-head-move-20261024-1935/delivery/UI设计/邪派移动动画_20261024_1935/调色板_v01.json').read_text())['xiepai'];run([v for c in pal for v in ['-size','1x1','xc:#'+c]]+['+append',W/'palette.png']);(UI/'调色板_v01.json').write_text(json.dumps(pal,indent=2))
def objects(src,single=0):
 im=Image.open(src);s=run([src,'-alpha','extract','-threshold','80%','-define','connected-components:verbose=true','-connected-components','8','null:']);rows=[[]] if single else [[],[],[],[]]
 for line in s.splitlines():
  m=re.search(r'\s*(\d+): (\d+)x(\d+)\+(\d+)\+(\d+) ([\d.]+),([\d.]+) ([\de+.-]+) srgb\(255,255,255\)',line)
  if m and float(m[8])>300:
   k,w,h,x,y,cx,cy,area=m.groups();rows[0 if single else min(int(float(cy)*4/im.height),3)].append({'id':int(k),'box':list(map(int,[x,y,w,h])),'centroid':[float(cx),float(cy)]})
 for row,n in zip(rows,[single] if single else [6,5,4,4]):row.sort(key=lambda o:o['centroid'][0]);assert len(row)==n,(src,len(row),n)
 return rows

def feet(im):
 steel=[tuple(bytes.fromhex(v)) for v in ['C8C8C8','8C929D','4C5765']];pts={(x,y) for y in range(max(0,im.height-6),im.height) for x in range(im.width) if im.getpixel((x,y))[3] and im.getpixel((x,y))[:3] not in steel};cs=[]
 while pts:
  st=[pts.pop()];c=[]
  while st:
   x,y=st.pop();c.append((x,y))
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
    q=x+dx,y+dy
    if q in pts:pts.remove(q);st.append(q)
  if len(c)>=3:cs.append(c)
 cs.sort(key=len,reverse=True);out=[]
 for c in cs[:2]:
  yy=max(y for x,y in c);xx=[x for x,y in c if y==yy];out.append([sum(xx)/len(xx),yy])
 return out
layout=[('atk1',0,0,3),('atk2',0,3,3),('atk3',1,0,3),('hit',1,3,2),('roll',2,0,4),('down',3,0,4)]
def build():
 data={};params=[];registration=[]
 for dr in ['down','left','up']:
  sources={'raw':P/'source'/f'xiepai_combat_{dr}_generated.png'}
  if dr in ['left','up']:sources['fix']=P/'source'/f'xiepai_combat_{dr}_weaponfix_generated.png'
  
  if dr in ['left','up']:sources['compact']=P/'source/xiepai_combat_four_compact_generated.png'
  
  if dr=='up':sources['cutfix']=P/'source/xiepai_combat_up_cutfix_generated.png'
  objs={k:objects(v,4 if k=='compact' else 1 if k=='cutfix' else 0) for k,v in sources.items()};data[dr]=objs;scales={k:(38 if k=='cutfix' else 41)/(objs[k][0][0]['box'][3] if k in ['compact','cutfix'] else objs[k][2][3]['box'][3]) for k in objs}
  for action,row,start,n in layout:
   folder=W/dr/action;folder.mkdir(parents=True,exist_ok=True);frames=[];records=[]
   for i in range(n):
    k='fix' if dr=='up' or (dr=='left' and action=='atk3' and i==1) else 'raw';rr,cc=row,start+i
    if dr=='left' and ((action=='atk1' and i in [1,2]) or(action=='hit' and i==1)):k='compact';rr,cc=0,(i-1 if action=='atk1' else 2)
    if dr=='up' and action=='roll' and i==2:k='compact';rr,cc=0,3
    if dr=='up' and action=='atk2' and i==1:k='cutfix';rr,cc=0,0
    src=sources[k];ob=objs[k][rr][cc];x,y,w,h=ob['box'];scale=scales[k];sw,sh=round(w*scale),round(h*scale);mask=folder/f'{i:02}_mask.png';run([src,'-alpha','extract','-threshold','80%','-define',f'connected-components:keep={ob["id"]}','-connected-components','8','-auto-level','-threshold','0',mask]);small=folder/f'{i:02}_small.png';run([src,mask,'-alpha','off','-compose','CopyOpacity','-composite','-compose','Over','-crop',f'{w}x{h}+{x}+{y}','+repage','-filter','point','-resize',f'{sw}x{sh}!',small]);run([small,'-alpha','extract',folder/'alpha.png']);run([small,'-alpha','off','+dither','-remap',W/'palette.png',folder/'rgb.png']);colored=folder/f'{i:02}_colored.png';run([folder/'rgb.png',folder/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite',colored]);im=Image.open(colored).convert('RGBA');fp=feet(im)
    if (action=='roll' and i==1) or (action=='down' and i>=2) or len(fp)<2:gx=(sw-1)/2;gy=sh-1;reg='rotated/prone projected body ground center'
    else:gx=sum(v[0] for v in fp)/2;gy=max(v[1] for v in fp);reg='projected center between visible shoe components; steel excluded from foot detection'
    ox=24-round(gx);oy=60-round(gy);margin=0 if sw>46 else 1;ax=max(margin-ox,0)+min(48-margin-sw-ox,0);ay=max(1-oy,0)+min(64-sh-oy,0);ox+=ax;oy+=ay
    if sw>48 or sh>63 or max(abs(ax),abs(ay))>2:print('OUTLIER',dr,action,i,sw,sh,'offset',ox,oy,'adjust',ax,ay)
    assert sw<=48 and sh<=63 and 0<=ox and ox+sw<=48 and 1<=oy and oy+sh<=64,(dr,action,i,sw,sh,ox,oy,ax,ay)
    final=folder/f'{i:02}.png';run(['-size','48x64','xc:none',colored,'-geometry',f'+{ox}+{oy}','-compose','Over','-composite','PNG32:'+str(final)]);frames.append(final);rec={'index':i,'source':'assets/ref/ref_chr_'+src.name.replace('_generated','_source_v01'),'source_row_col':[rr,cc],'component':ob,'uniform_scale':scale,'scale_reference':'原稿按同方向roll末帧恢复站姿41px整方向等比；独立4姿态以首帧站姿41px校准，4张同比例；背面横切独立单帧按原相同蹲势38px校准' ,'scaled_size':[sw,sh],'registered_offset':[ox,oy],'anchor':[24,60],'source_native_foot_candidates':fp,'registration_method':reg,'integer_margin_registration':[ax,ay],'projected_ground_rounding_error':[gx+ox-24,gy+oy-60]};records.append(rec);registration.append(dict(direction=dr,action=action,**rec))
   name=f'chr_xiepai_{action}_{dr}_v01.png';run([*frames,'+append','PNG32:'+str(D/'assets/chr'/name)]);run([D/'assets/chr'/name,'-filter','point','-resize','600%',UI/f'{action}_{dr}_6倍_v01.png']);gif=[]
   for i,f in enumerate(frames):gif+=['-delay',str(60 if i==n-1 else [8,8,9][i%3]),'(',str(f),'-background','#46525E','-alpha','remove','-alpha','off','-filter','point','-resize','600%',')']
   run([*gif,'-loop','0',UI/f'{action}_{dr}_播放预览_v01.gif']);params.append({'file':'assets/chr/'+name,'action':action,'direction':dr,'frame_size':[48,64],'frame_count':n,'fps':12,'loop':False,'anchor':[24,60],'gap':0,'frame_order':list(range(n)),'head_embedded':True,'weapon_embedded':'one Chinese dao','hold_frames':[3] if action=='down' else [],'end_behavior':'hold_last_until_state_change' if action=='down' else 'return_to_idle_by_controller','phase':{'windup':[0],'strike':[1],'recover':[2]} if action.startswith('atk') else None,'frames':records})
  panels=[]
  for a,row,start,n in layout:
   src=D/'assets/chr'/f'chr_xiepai_{a}_{dr}_v01.png';pane=W/f'{a}_{dr}_panel.png';run([src,'-background','none','-gravity','NorthWest','-extent','192x64',pane]);panels.append(pane)
  run([*panels,'-append','-filter','point','-resize','600%',UI/f'{dr}_基础战斗逐帧_v01.png'])
 for src in (P/'source').glob('xiepai_combat_*_generated.png'):shutil.copy2(src,D/'assets/ref'/('ref_chr_'+src.name.replace('_generated','_source_v01')))
 (P/'source/components.json').write_text(json.dumps(data,indent=2));(P/'source/frame_registration.json').write_text(json.dumps(registration,ensure_ascii=False,indent=2));(UI/'基础战斗参数_v01.json').write_text(json.dumps(params,ensure_ascii=False,indent=2));print('Built18strips57frames')
if __name__=='__main__':build()

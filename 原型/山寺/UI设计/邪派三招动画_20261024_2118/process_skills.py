from pathlib import Path
from PIL import Image
import json,re,subprocess,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';UI=D/'UI设计/邪派三招动画_20261024_2118';W=P/'work';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
pal=json.loads((P.parent/'art-xiepai-head-move-20261024-1935/delivery/UI设计/邪派移动动画_20261024_1935/调色板_v01.json').read_text())['xiepai'];run([v for c in pal for v in ['-size','1x1','xc:#'+c]]+['+append',W/'palette.png']);(UI/'调色板_v01.json').write_text(json.dumps(pal,indent=2))
def objects(src):
 im=Image.open(src);s=run([src,'-alpha','extract','-threshold','80%','-define','connected-components:verbose=true','-connected-components','8','null:']);rows=[[],[],[]]
 for line in s.splitlines():
  m=re.search(r'\s*(\d+): (\d+)x(\d+)\+(\d+)\+(\d+) ([\d.]+),([\d.]+) ([\de+.-]+) srgb\(255,255,255\)',line)
  if m and float(m[8])>500:
   k,w,h,x,y,cx,cy,area=m.groups();rows[min(int(float(cy)*3/im.height),2)].append({'id':int(k),'box':list(map(int,[x,y,w,h])),'centroid':[float(cx),float(cy)]})
 for row,n in zip(rows,[4,5,6]):row.sort(key=lambda o:o['centroid'][0]);assert len(row)==n,(src,len(row))
 return rows

def comps(im,start):
 pts={(x,y) for y in range(start,im.height) for x in range(im.width) if im.getpixel((x,y))[3]};out=[]
 while pts:
  st=[pts.pop()];co=[]
  while st:
   x,y=st.pop();co.append((x,y))
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
    q=(x+dx,y+dy)
    if q in pts:pts.remove(q);st.append(q)
  if len(co)>2:out.append(co)
 return sorted(out,key=len,reverse=True)
layout=[('dushazhang',0,4),('huagongsan',1,5),('shehunshu',2,6)]
def phase(a,i):return ('windup' if i==0 else 'palm' if i==1 else 'flick' if i==2 else 'recover') if a=='dushazhang' else ('aim' if i<2 else 'throw_recover') if a=='huagongsan' else ('charge' if i<4 else 'release')
def build():
 metadata=[];allobj={};params=[]
 for dr in ['down','left','up']:
  sources={'raw':P/'source'/f'xiepai_skills_{dr}_generated.png'}
  if dr!='left':sources['fix']=P/'source'/f'xiepai_skills_{dr}_fix_generated.png'
  objs={k:objects(v) for k,v in sources.items()};allobj[dr]=objs;sc={k:41/objs[k][2][0]['box'][3] for k in objs}
  for act,row,n in layout:
   folder=W/dr/act;folder.mkdir(parents=True,exist_ok=True);frames=[];records=[]
   for i in range(n):
    k='fix' if dr!='left' and ((act=='dushazhang' and i in [1,2]) or (act=='huagongsan' and i in [2,3]) or (act=='shehunshu' and i==4)) else 'raw'
    ob=objs[k][row][i];x,y,w,h=ob['box'];scale=sc[k];sw,sh=round(w*scale),round(h*scale);src=sources[k];mask=folder/f'{i:02}_mask.png';run([src,'-alpha','extract','-threshold','80%','-define',f'connected-components:keep={ob["id"]}','-connected-components','8','-auto-level','-threshold','0',mask]);small=folder/f'{i:02}_small.png';run([src,mask,'-alpha','off','-compose','CopyOpacity','-composite','-compose','Over','-crop',f'{w}x{h}+{x}+{y}','+repage','-filter','point','-resize',f'{sw}x{sh}!',small]);run([small,'-alpha','extract',folder/'alpha.png']);run([small,'-alpha','off','+dither','-remap',W/'palette.png',folder/'rgb.png']);colored=folder/f'{i:02}_colored.png';run([folder/'rgb.png',folder/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite',colored]);im=Image.open(colored).convert('RGBA');cs=comps(im,max(0,sh-6));assert len(cs)>=2,(dr,act,i,len(cs));foot=[]
    for c in cs[:2]:
     yy=max(y for x,y in c);xs=[x for x,y in c if y==yy];foot.append([sum(xs)/len(xs),yy])
    gx=sum(v[0] for v in foot)/2;gy=max(v[1] for v in foot);ox=24-round(gx);oy=60-gy;adj=max(1-ox,0)+min(47-sw-ox,0);ox+=adj
    assert sw<=46 and 1<=ox and ox+sw<=47 and 1<=oy and oy+sh<=64,(dr,act,i,sw,sh,ox,oy,adj)
    final=folder/f'{i:02}.png';run(['-size','48x64','xc:none',colored,'-geometry',f'+{ox}+{oy}','-compose','Over','-composite','PNG32:'+str(final)]);frames.append(final);rec={'index':i,'source':'assets/ref/ref_chr_'+src.name.replace('_generated','_source_v01'),'source_row_col':[row,i],'component':ob,'uniform_scale':scale,'scale_reference':'同源同方向摄魂术首帧站姿41px，全组统一等比，不逐帧拉高','scaled_size':[sw,sh],'registered_offset':[ox,oy],'anchor':[24,60],'source_native_foot_points':foot,'projected_root_x_error_px':gx+ox-24,'integer_horizontal_margin_registration':adj,'phase':phase(act,i)};records.append(rec);metadata.append(dict(direction=dr,action=act,**rec))
   name=f'chr_xiepai_{act}_{dr}_v01.png';out=D/'assets/chr'/name;run([*frames,'+append','PNG32:'+str(out)]);run([out,'-filter','point','-resize','600%',UI/f'{act}_{dr}_6倍_v01.png']);seq=list(range(4))*2+[4,5] if act=='shehunshu' else list(range(n));params.append({'file':'assets/chr/'+name,'action':act,'direction':dr,'frame_size':[48,64],'frame_count':n,'anchor':[24,60],'fps':12,'loop':False,'frame_order':list(range(n)),'gap':0,'head_embedded':True,'weapon':'one_dao_secured_diagonally_on_back_to_free_hands','phase':{'windup':[0],'palm':[1],'flick':[2],'recover':[3]} if act=='dushazhang' else {'aim':[0,1],'aim_hold_frame':1,'throw_recover':[2,3,4]} if act=='huagongsan' else {'charge_loop':[0,1,2,3],'release':[4,5]},'hold_frames':[1] if act=='huagongsan' else [],'end_behavior':'controller_returns_idle','frames':records,'gif_playback_frame_order':seq})
  panels=[]
  for a,row,n in layout:
   src=D/'assets/chr'/f'chr_xiepai_{a}_{dr}_v01.png';pane=W/f'{a}_{dr}_panel.png';run([src,'-background','none','-gravity','NorthWest','-extent','288x64',pane]);panels.append(pane)
  run([*panels,'-append','-filter','point','-resize','600%',UI/f'{dr}_三招逐帧_v01.png'])
 for src in (P/'source').glob('xiepai_skills_*_generated.png'):shutil.copy2(src,D/'assets/ref'/('ref_chr_'+src.name.replace('_generated','_source_v01')))
 (P/'source/components.json').write_text(json.dumps(allobj,indent=2));(UI/'三招动画参数_v01.json').write_text(json.dumps(params,ensure_ascii=False,indent=2));(P/'source/frame_registration.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2));print('Built9 strips45 frames')
if __name__=='__main__':build()

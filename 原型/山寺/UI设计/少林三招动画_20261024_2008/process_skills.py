from pathlib import Path
from PIL import Image
import json,re,subprocess,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';UI=D/'UI设计/少林三招动画_20261024_2008';W=P/'work';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
pal=json.loads((P.parent/'art-shaolin-move-20261024-1501/delivery/UI设计/少林移动动画_20261024_1501/调色板_v01.json').read_text());run([v for c in pal for v in ['-size','1x1','xc:'+c]]+['+append',W/'palette.png']);(UI/'调色板_v01.json').write_text(json.dumps(pal,indent=2))
def objects(src,single=False):
 im=Image.open(src);s=run([src,'-alpha','extract','-threshold','80%','-define','connected-components:verbose=true','-connected-components','8','null:']);rows=[[]] if single else [[],[],[]]
 for line in s.splitlines():
  m=re.search(r'\s*(\d+): (\d+)x(\d+)\+(\d+)\+(\d+) ([\d.]+),([\d.]+) ([\de+.-]+) srgb\(255,255,255\)',line)
  if m and float(m[8])>500:
   k,w,h,x,y,cx,cy,area=m.groups();rows[0 if single else min(int(float(cy)*3/im.height),2)].append({'id':int(k),'box':list(map(int,[x,y,w,h])),'centroid':[float(cx),float(cy)]})
 for row,n in zip(rows,[3] if single else [4,6,6]):row.sort(key=lambda o:o['centroid'][0]);assert len(row)==n,(src,len(row))
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
layout=[('luohanquan',0,4),('jinzhongzhao',1,6),('dalijingangzhang',2,6)]
def build():
 metadata=[];allobj={};params=[]
 for dr in ['down','left','up']:
  sources={k:P/'source'/f'shaolin_skills_{dr}{"_fix" if k=="fix" else ""}_generated.png' for k in ['raw','fix']};
  if dr=='left':sources['compact']=P/'source/shaolin_skills_left_compact_generated.png'
  objs={k:objects(v,k=='compact') for k,v in sources.items()};allobj[dr]=objs;sc={k:(37/objs[k][0][0]['box'][3] if k=='compact' else 41/objs[k][1][0]['box'][3]) for k in objs}
  for act,row,n in layout:
   folder=W/dr/act;folder.mkdir(parents=True,exist_ok=True);frames=[];records=[]
   for i in range(n):
    k='fix' if (act=='luohanquan' and i==1) or (act=='dalijingangzhang' and i<2) else 'raw';rr,cc=row,i
    if dr=='up' and act=='dalijingangzhang' and i==1:k='raw';rr,cc=1,3
    
    if dr=='left' and ((act=='luohanquan' and i==2) or (act=='dalijingangzhang' and i in [3,4])):k='compact';rr,cc=0,0 if act=='luohanquan' else i-2
    ob=objs[k][rr][cc];x,y,w,h=ob['box'];scale=sc[k];sw,sh=round(w*scale),round(h*scale);src=sources[k];mask=folder/f'{i:02}_mask.png';run([src,'-alpha','extract','-threshold','80%','-define',f'connected-components:keep={ob["id"]}','-connected-components','8','-auto-level','-threshold','0',mask]);small=folder/f'{i:02}_small.png';run([src,mask,'-alpha','off','-compose','CopyOpacity','-composite','-compose','Over','-crop',f'{w}x{h}+{x}+{y}','+repage','-filter','point','-resize',f'{sw}x{sh}!',small]);run([small,'-alpha','extract',folder/'alpha.png']);run([small,'-alpha','off','+dither','-remap',W/'palette.png',folder/'rgb.png']);colored=folder/f'{i:02}_colored.png';run([folder/'rgb.png',folder/'alpha.png','-alpha','off','-compose','CopyOpacity','-composite',colored]);im=Image.open(colored).convert('RGBA');cs=comps(im,max(0,sh-6));assert len(cs)>=2,(dr,act,i,len(cs));foot=[]
    for c in cs[:2]:
     yy=max(y for x,y in c);xs=[x for x,y in c if y==yy];foot.append([sum(xs)/len(xs),yy])
    gx=sum(v[0] for v in foot)/2;gy=max(v[1] for v in foot);ox=24-round(gx);oy=60-gy;adj=max(1-ox,0)+min(47-sw-ox,0);ox+=adj
    assert sw<=46 and 1<=ox and ox+sw<=47 and 1<=oy and oy+sh<=64,(dr,act,i,sw,sh,ox,oy,adj)
    final=folder/f'{i:02}.png';run(['-size','48x64','xc:none',colored,'-geometry',f'+{ox}+{oy}','-compose','Over','-composite','PNG32:'+str(final)]);frames.append(final);rec={'index':i,'source':'assets/ref/ref_chr_'+src.name.replace('_generated','_source_v01'),'source_row_col':[rr,cc],'component':ob,'uniform_scale':scale,'scale_reference':'同源同方向金钟罩首帧站姿41px；独立左向紧凑蹲势按同蹲姿37px校准，整组等比' ,'scaled_size':[sw,sh],'registered_offset':[ox,oy],'anchor':[24,60],'source_native_foot_points':foot,'projected_root_x_error_px':gx+ox-24,'integer_horizontal_margin_registration':adj,'phase':('punch'+str(i+1) if i<3 else 'recover') if act=='luohanquan' else ('charge' if i<4 else 'release') if act=='jinzhongzhao' else ('aim_hold' if i<2 else 'push_recover')};records.append(rec);metadata.append(dict(direction=dr,action=act,**rec))
   name=f'chr_shaolin_{act}_{dr}_v01.png';out=D/'assets/chr'/name;run([*frames,'+append','PNG32:'+str(out)]);run([out,'-filter','point','-resize','600%',UI/f'{act}_{dr}_6倍_v01.png']);gif=[]
   # Charge preview demonstrates two complete loops (8 plays), then two release frames.
   seq=list(range(4))*2+[4,5] if act=='jinzhongzhao' else list(range(n))
   for j,i in enumerate(seq):
    dt=60 if j==len(seq)-1 else 80 if act=='dalijingangzhang' and i==1 else [8,8,9][j%3];gif+=['-delay',str(dt),'(',str(frames[i]),'-filter','point','-resize','600%',')']
   run([*gif,'-dispose','background','-loop','0',UI/f'{act}_{dr}_相位预览_v01.gif']);params.append({'file':'assets/chr/'+name,'action':act,'direction':dr,'frame_size':[48,64],'frame_count':n,'anchor':[24,60],'fps':12,'loop':False,'frame_order':list(range(n)),'gap':0,'head_embedded':True,'staff':'on_back_to_free_both_hands','phase':{'punch':[0,1,2],'recover':[3]} if act=='luohanquan' else {'charge_loop':[0,1,2,3],'release':[4,5]} if act=='jinzhongzhao' else {'aim':[0,1],'aim_hold_frame':1,'push_recover':[2,3,4,5]},'hold_frames':[1] if act=='dalijingangzhang' else [],'end_behavior':'controller_returns_idle','frames':records,'gif_playback_frame_order':seq})
  panels=[]
  for a,row,n in layout:
   src=D/'assets/chr'/f'chr_shaolin_{a}_{dr}_v01.png';pane=W/f'{a}_{dr}_panel.png';run([src,'-background','none','-gravity','NorthWest','-extent','288x64',pane]);panels.append(pane)
  run([*panels,'-append','-filter','point','-resize','600%',UI/f'{dr}_三招逐帧_v01.png'])
 for src in (P/'source').glob('shaolin_skills_*_generated.png'):shutil.copy2(src,D/'assets/ref'/('ref_chr_'+src.name.replace('_generated','_source_v01')))
 (P/'source/components.json').write_text(json.dumps(allobj,indent=2));(UI/'三招动画参数_v01.json').write_text(json.dumps(params,ensure_ascii=False,indent=2));(P/'source/frame_registration.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2));print('Built9 strips48 frames')
if __name__=='__main__':build()

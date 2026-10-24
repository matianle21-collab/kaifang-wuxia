from pathlib import Path
from PIL import Image
import json,hashlib,subprocess,shutil
P=Path(__file__).resolve().parents[1];D=P/'delivery';U=D/'UI设计/开场角色定妆_20261024_2137';W=P/'work';M='/opt/homebrew/bin/magick'
def run(a):return subprocess.run([M,*map(str,a)],capture_output=True,text=True,check=True).stdout
p=json.loads((U/'定妆参数_v01.json').read_text());assert len(p)==8;checks=[];portraits=[];colors={}
for a in p:
 f=D/a['standing'];im=Image.open(f).convert('RGBA');assert im.size==(48,64) and set(im.getchannel('A').get_flattened_data())=={0,255};cs={c[:3] for c in im.get_flattened_data() if c[3]};assert (0,0,0) not in cs and (255,0,255) not in cs;assert a['anchor']==[24,60];foot=a['actual_opaque_foot_points'];assert foot[0][1]==foot[1][1]==60 and foot[0][0]+foot[1][0]==48
 for point in foot:assert im.getpixel(tuple(point))[3]==255
 assert not im.getchannel('A').crop((0,61,48,64)).getbbox();small=Image.open(W/a['role']/'small.png').convert('RGBA');assert sum(v>0 for v in small.getchannel('A').get_flattened_data())==sum(v>0 for v in im.getchannel('A').get_flattened_data());big=Image.open(U/f'{a["name"]}_定妆8倍_v01.png').convert('RGBA');assert big.size==(384,512)
 for y in range(big.height):
  for x in range(big.width):
   c=big.getpixel((x,y));e=im.getpixel((x//8,y//8));assert c[3]==e[3] and (not c[3] or c==e)
 obj=a['source_component'];expected=obj['area']/(obj['box'][2]*obj['box'][3]);actual=sum(v>0 for v in small.getchannel('A').get_flattened_data())/(small.width*small.height);assert abs(actual-expected)<.12,(a['role'],'standing alpha coverage')
 colors[a['role']]=cs
 if a['portrait']:
  po=Image.open(D/a['portrait']['file']).convert('RGBA');assert po.size==(96,96) and set(po.getchannel('A').get_flattened_data())=={0,255};pcs={c[:3] for c in po.get_flattened_data() if c[3]};assert (0,0,0) not in pcs and (255,0,255) not in pcs;colors[a['role']]|=pcs;ps=Image.open(W/a['role']/'portrait/small.png').convert('RGBA');assert sum(v>0 for v in ps.getchannel('A').get_flattened_data())==sum(v>0 for v in po.getchannel('A').get_flattened_data());pb=Image.open(U/f'{a["name"]}_头像4倍_v01.png').convert('RGBA');assert pb.size==(384,384)
  for y in range(pb.height):
   for x in range(pb.width):
    c=pb.getpixel((x,y));e=po.getpixel((x//4,y//4));assert c[3]==e[3] and(not c[3] or c==e)
  obj=a['portrait']['source_component'];expected=obj['area']/(obj['box'][2]*obj['box'][3]);actual=sum(v>0 for v in ps.getchannel('A').get_flattened_data())/(ps.width*ps.height);assert abs(actual-expected)<.08,(a['role'],'portrait alpha coverage')
  portraits.append(D/a['portrait']['file'])
 assert len(colors[a['role']])<=16
 checks.append({'role':a['role'],'name':a['name'],'standing':a['standing'],'standing_size':[48,64],'portrait':a['portrait']['file'] if a['portrait'] else None,'portrait_size':[96,96] if a['portrait'] else None,'colors_shared':len(colors[a['role']]),'alpha':[0,255],'anchor':[24,60],'actual_foot_points':foot,'feet_exact_on60':True,'below60_transparent':True,'native_content_uncut':True,'nearest_preview_exact':True,'scope':a['stage']})
assert len(portraits)==5 and len(list((D/'assets/por').glob('*.png')))==5
rows=[]
for n in [0,4]:
 row=W/f'row{n//4}.png';run([*[D/a['standing'] for a in p[n:n+4]],'+append',row]);rows.append(row)
run([*rows,'-append','-background','#46525E','-alpha','remove','-alpha','off','-filter','point','-resize','600%',U/'八角色同尺度_v01.png']);run([*portraits,'+append','-background','#46525E','-alpha','remove','-alpha','off','-filter','point','-resize','300%',U/'五头像总览_v01.png'])
env=P.parent/'art-shanmen-20261024-1328/delivery/assets/env/env_shanmen_v01.png';args=[env]
# Static 1:1 perspective comparison on the open courtyard, no runtime claim.
for i,a in enumerate(p):args += [D/a['standing'],'-geometry',f'+{600+(i%4)*160-24}+{260+(i//4)*120-60}','-compose','Over','-composite']
run([*args,U/'山门原比例八角色_v01.png'])
for name in ['role_specs.json','portrait_prompts.json','fix_prompts.json','process_refs.py','validate_refs.py','production_plan.md']:shutil.copy2(P/'source'/name,U/name)
ref=U/'source_inputs';ref.mkdir(exist_ok=True)
for f in (P/'source').glob('style_*_reference.png'):shutil.copy2(f,ref/f.name)
r={'status':'passed','new_standing_sprites':8,'new_portraits':5,'generated_sources':15,'reference_inputs':2,'single_frames_only':True,'animation_not_started_for_unapproved_characters':True,'rows':{'64':'站姿+头像所列已交，待开发确认','76':'7角色正面定妆+前4头像已交，5角色动画待各自确认；整体出图中'},'checks':checks,'visual_review':'eight native standing figures, five native portraits, enlarged comparison and static scene inspected before upload','independent_runtime_test':False,'notes':['No program-drawn character pixels. ImageMagick technical crop, binaryalpha, uniform nearest resize, per-role16color palette and registration only; PIL read-only.','Selected guanshi standing shoe-baseline AI correction and aluo portrait black-tongue AI correction; both initials preserved.','Native standing root fixed24,60; each has two actual opaque sole pixels on row60 with exact midpoint24. No foot fragment moved by code.','Only Aluo, Zhikeseng, Guanshi have requested single idle_down runtime files. Five animated NPCs currently only ref images, not 1frame pretending idle4.']};(U/'核验结果_v01.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['checks','notes','visual_review']},ensure_ascii=False))

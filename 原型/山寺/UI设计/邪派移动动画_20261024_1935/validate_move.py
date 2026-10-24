from pathlib import Path
from PIL import Image
import json,hashlib
P=Path(__file__).resolve().parents[1];D=P/'delivery';UI=D/'UI设计/邪派移动动画_20261024_1935';W=P/'work'
params=json.loads((UI/'动画参数_v01.json').read_text());records=json.loads((P/'source/frame_registration.json').read_text());colors=set();headcolors=set();checks=[]
def pix(p):return Image.open(p).convert('RGBA')
def flat(im):return [(r,g,b,a) if a else (0,0,0,0) for r,g,b,a in im.get_flattened_data()]
for p in params:
 im=pix(D/p['file']);n=p['frame_count'];a=p['action'];dr=p['direction'];assert im.size==(48*n,64);assert set(im.getchannel('A').get_flattened_data())=={0,255};assert p['anchor']==[24,60] and p['fps']==12 and p['loop'];cs={v[:3] for v in im.get_flattened_data() if v[3]};colors|=cs;assert len(cs)<=16;assert (255,0,255) not in cs and (0,0,0) not in cs
 frames=[im.crop((48*i,0,48*(i+1),64)) for i in range(n)];assert len({hashlib.sha256(bytes(v for q in flat(f) for v in q)).hexdigest() for f in frames})==n
 preview=pix(UI/f'chr_xiepai_{a}_{dr}_6倍_v01.png');assert preview.size==(im.width*6,384)
 for y in range(preview.height):
  for x in range(preview.width):
   v=preview.getpixel((x,y));e=im.getpixel((x//6,y//6));assert v[3]==e[3] and (not v[3] or v==e)
 gif=Image.open(UI/f'chr_xiepai_{a}_{dr}_循环_v01.gif');assert gif.n_frames==n;dur=[]
 for i in range(n):gif.seek(i);dur.append(gif.info['duration'])
 assert sum(dur)==(330 if n==4 else 500)
 for i,f in enumerate(frames):
  fd=W/dr/a;orig=pix(fd/f'{i:02}_original.png');head=pix(fd/f'{i:02}_head.png');body=pix(fd/f'{i:02}_body.png');shaobody=pix(fd/f'{i:02}_shaolin_body.png');norm=pix(fd/f'{i:02}_shaolin_normalized.png');leg=pix(fd/f'{i:02}_legs.png');sourceleg=pix(fd/f'{i:02}_lower_cut.png');reg=pix(fd/f'{i:02}_reg.png');headcolors|={v[:3] for v in head.get_flattened_data() if v[3]}
  assert flat(f)==[(h if h[3] else b) for h,b in zip(flat(head),flat(body))]
  assert flat(norm)==[(h if h[3] else b) for h,b in zip(flat(head),flat(shaobody))]
  assert head.getchannel('A').crop((16,0,32,31)).tobytes()==orig.getchannel('A').crop((16,0,32,31)).tobytes()
  for y in range(64):
   for x in range(48):
    if y<31 and 16<=x<32:assert f.getpixel((x,y))==head.getpixel((x,y)) or (f.getpixel((x,y))[3]==head.getpixel((x,y))[3]==0)
    elif y>=53 and 11<=x<38:assert f.getpixel((x,y))[3]==leg.getpixel((x,y))[3]
    else:
     q=f.getpixel((x,y));e=reg.getpixel((x,y));assert q[3]==e[3] and (not q[3] or q==e),(dr,a,i,x,y)
  assert leg.getchannel('A').crop((0,53,48,64)).tobytes()==sourceleg.getchannel('A').tobytes();assert not f.getchannel('A').crop((0,61,48,64)).getbbox()
  rec=next(e for e in records if (e['direction'],e['action'],e['index'])==(dr,a,i));assert rec['registered_offset'][0]>=0 and rec['registered_offset'][0]+rec['scaled_size'][0]<=48
 checks.append({'file':p['file'],'size':list(im.size),'frames':n,'colors':len(cs),'alpha':[0,255],'anchor':[24,60],'head_geometry_matches_source':True,'lower_leg_geometry_matches_selected_source_components':True,'layer_reconstruction':True,'kept_blade_pixels_outside_head_and_leg_registration':True,'preview_nearest_neighbor':True,'gif_frames':gif.n_frames,'gif_durations_ms':dur})
assert len(colors)<=16 and len(headcolors)<=7 and len(params)==6 and sum(p['frame_count'] for p in params)==30
result={'status':'passed','native_strips':6,'native_pose_frames':30,'combined_colors':len(colors),'common_head_source_layer_colors':len(headcolors),'head_delivery_rule':'latest request embeds head in bodies; no head overlay delivered to assets/chr','rows10_11_complete':False,'visual_review':'all three direction comparisons and 1:1 scene inspected before upload','independent_runtime_test':False,'checks':checks,'notes':['Head and lower-leg alpha shapes/positions copied from same approved Shaolin native pose; colors normalized to a seven-color subset of old palette. Old Shaolin PNGs untouched.','Only head/feet registration is exact source geometry. Coat and dao are new AI artwork registered to those poses; no claim of pixel-identical torso/arm shapes.','No pixels below row60 in this new movement set. This does not mean two moving shoes both touch y60. World anchor remains24,60.','No standalone head asset is registered or shipped into game assets; editable source layers remain under UI design.']}
(UI/'核验结果_v01.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['checks','notes']},ensure_ascii=False))

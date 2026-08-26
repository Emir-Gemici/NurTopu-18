import json, io, sys
from pathlib import Path
sys.path.insert(0, 'scripts/olcum')
import importlib.util
spec = importlib.util.spec_from_file_location("ryo", "scripts/olcum/rota_yol_olcumu.py"); ryo = importlib.util.module_from_spec(spec); spec.loader.exec_module(ryo)
import cv2
G='results/gece_20260826/'
def kareler(p):
    d=json.load(io.open(p,encoding='utf-8')); v=list(d['modeller'].values())[0]; return v['kareler']
def tavan(p): return {s['kare']:s['rota'] for s in json.load(io.open(p,encoding='utf-8'))['kareler']}
def say(karel, tv, etiket_dizin, kare_dizin):
    tp=fp=fn=0; fpk=[]; seb={}; rota=[]; yanlis=[]
    for s in karel:
        seb[s['olceksiz_sebep']]=seb.get(s['olceksiz_sebep'],0)+1
        mr = s['olceksiz_sebep'] is None
        er = tv.get(s['kare'])
        if mr and er: tp+=1
        elif mr and er is False: fp+=1; fpk.append(s['kare'])
        elif (not mr) and er: fn+=1
        if mr:
            img=cv2.imread(str(Path(kare_dizin)/s['kare'])); h,w=img.shape[:2]
            uc=ryo.uc_durum_maske(Path(etiket_dizin)/(Path(s['kare']).stem+'.txt'),h,w)
            o=ryo.rota_yol_olc(s['olceksiz_wps'],uc); y=ryo.yanlis_guzergah_mi(o)
            rota.append(s['kare'])
            if y: yanlis.append((s['kare'],o['yol_payi'],o['engel_wp']))
    return dict(n=len(karel), sebep=seb, rota=len(rota), TP=tp, FP=fp, FN=fn, fp_kareler=fpk, yanlis=len(yanlis), yanlis_kareler=yanlis, rota_kareler=rota)
D='dataset/dji_kirsal_0038_bolum_v3/'
out={}
out['v7a_test29']=say(kareler(G+'gece_v7a_test29.json'), tavan(G+'test29_etiket_tavani_v3.json'), D+'labels/test', D+'images/test')
out['v35_test29']=say(kareler(G+'v35_ref3_test29.json'), tavan(G+'test29_etiket_tavani_v3.json'), D+'labels/test', D+'images/test')
out['v7a_val82']=say(kareler(G+'gece_v7a_val82_test29.json'), tavan(G+'sizinti/val82_etiket_tavani.json'), D+'labels/val', D+'images/val')
out['v35_val82']=say(kareler(G+'sizinti/val82_v35_test29.json'), tavan(G+'sizinti/val82_etiket_tavani.json'), D+'labels/val', D+'images/val')
# kare kare karsilastirma test29
a={s['kare']:s for s in kareler(G+'gece_v7a_test29.json')}; b={s['kare']:s for s in kareler(G+'v35_ref3_test29.json')}
tv=tavan(G+'test29_etiket_tavani_v3.json')
tablo=[]
for k in sorted(a):
    tablo.append((k[-24:-4], a[k]['olceksiz_sebep'], b[k]['olceksiz_sebep'], tv.get(k)))
out['test29_kare_kare']=tablo
json.dump(out, io.open('results/gece_20260826/v7a_curut/olcum/yeniden_say.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
for k in ['v7a_test29','v35_test29','v7a_val82','v35_val82']:
    o=out[k]; print(k, {kk:o[kk] for kk in ['n','sebep','rota','TP','FP','FN','yanlis']}); print('   fp:',o['fp_kareler']); print('   yanlis:',o['yanlis_kareler'])
print('kare | v7a | v35 | tavan')
for r in tablo: print(r)

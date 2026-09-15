"""Kayitlari yeniden sayar; iki altyapi kusurunu izole ortamda yeniden uretir.
GPU/model/canli simulasyon calistirmaz, uretim dosyalarini degistirmez.
Depo kokunden python ile calistirilir.
"""
import ast, contextlib, hashlib, io, json, subprocess, sys, tempfile, types
from pathlib import Path
from zipfile import ZipFile
ROOT=Path.cwd()
OUT=ROOT/'results/yazilim_rapor_senkron_20260915/ikinci_kontrol'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fun(path,name):
    tree=ast.parse(Path(path).read_text())
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
    return compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec')
r={}
a=json.loads((OUT.parent/'kanit.json').read_text())
r['onceki_dosya_butunlugu']={f['path']:sha(f['path'])==f['sha256'] for f in a['files'] if f.get('sha256') and Path(f['path']).is_file()}
p='results/fdr_sprint_20260910/H1/k3b/v1_15harita_yerlesim_d441.json'
d=json.loads(Path(p).read_text()); h=d['haritalar']
r['d441']={'kaynak':p,'sha256':sha(p),'n':len(h),'rota':sum(x['rota_bulundu'] for x in h),'dogru':sum(x['dogru'] for x in h),'teshis_512_dogru':sum(x['teshis_imgsz']['dogru'] for x in h),'conf':d['conf']}
assert (len(h),r['d441']['dogru'],r['d441']['teshis_512_dogru'])==(15,7,6)
p='results/gece_20260907/karisiklik/piksel_karisiklik_test29.json';d=json.loads(Path(p).read_text());m=d['toplam']['uretim']['matris']
recount=[[sum(x['uretim']['matris'][i][j] for x in d['kareler']) for j in range(3)] for i in range(3)]
assert m==recount
r['piksel']={'kaynak':p,'sha256':sha(p),'matris_karelerden_toplandi':m==recount,'kare_n':len(d['kareler']),'matris':m,'etiketsiz_orani':sum(row[2] for row in m)/sum(map(sum,m)),'dogruluk_etiketli':(m[0][0]+m[1][1])/sum(row[0]+row[1] for row in m),'siniflar':{}}
for i,name in enumerate(['zemin','engel']):
 tp=m[i][i];r['piksel']['siniflar'][name]={'precision_etiketli':tp/(m[i][0]+m[i][1]),'recall':tp/sum(row[i] for row in m),'etiketsiz_tahmin_payi':m[i][2]/sum(m[i])}
# Actual function extracted unchanged; no imports that load the model.
p='scripts/olcum/176_piksel_karisiklik_matrisi.py';g={'Path':Path,'hashlib':hashlib};exec(fun(p,'kume_parmak_izi'),g)
with tempfile.TemporaryDirectory(prefix='navitas-fingerprint-') as td:
 f=Path(td)/'label.txt';f.write_bytes(b'AAAA');before=g['kume_parmak_izi'](Path(td));s1=sha(f)
 f.write_bytes(b'BBBB');after=g['kume_parmak_izi'](Path(td));s2=sha(f)
 r['parmak_izi_mutasyon']={'kaynak':p,'sha256':sha(p),'ayni_boyut_icerik_degisti':s1!=s2,'parmak_izi_degismedi':before==after}
 assert s1!=s2 and before==after
# Real watch function with only clock and YOLO replaced. Missing SCAN_DONE, no real wait.
p='simulation/scripts/iha_haritala.py';clock=types.SimpleNamespace(t=0)
def tick(): clock.t+=1801;return clock.t
clock.time=tick;clock.sleep=lambda _:None
mod=types.ModuleType('ultralytics');mod.YOLO=lambda *a,**k:object()
old=sys.modules.get('ultralytics');sys.modules['ultralytics']=mod
calls=[]
def unexpected(*a,**k): calls.append(True);raise AssertionError('Inference should not run')
g={'Path':Path,'time':clock,'sys':sys,'haritala':unexpected};exec(fun(p,'watch'),g)
stdout,stderr=io.StringIO(),io.StringIO()
try:
 with tempfile.TemporaryDirectory(prefix='navitas-watch-') as td,contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
  ret=g['watch'](td,'kolay orta zor','stub.pt','stub_obb.pt',.15,.25,0,1.0)
finally:
 if old is None:sys.modules.pop('ultralytics',None)
 else:sys.modules['ultralytics']=old
r['watch_timeout']={'kaynak':p,'sha256':sha(p),'donus':ret,'cikarim_cagri_sayisi':len(calls),'stdout':stdout.getvalue(),'stderr':stderr.getvalue(),'kapsam':'Gercek watch fonksiyonu; YOLO ve saat taklit; gercek model/simulasyon degil.'}
assert ret is None and not calls and stderr.getvalue().count('atlanıyor')==3
src=Path('NAVITAS_FDR_BIRLESIK.docx');dst=Path('NAVITAS_FDR_BIRLESIK_DUZELTILMIS_20260915.docx')
with ZipFile(src) as a,ZipFile(dst) as b:
 different=[n for n in a.namelist() if a.read(n)!=b.read(n)]
 r['docx']={'source_sha256':sha(src),'output_sha256':sha(dst),'degisen_zip_parcalari':different,'medya_sayisi':sum(n.startswith('word/media/') for n in a.namelist()),'zip_test':b.testzip()}
 assert different==['word/document.xml']
r['git']={}
for label,args in [('head',['rev-parse','HEAD']),('origin_master',['rev-parse','origin/master']),('fark',['rev-list','--left-right','--count','HEAD...origin/master'])]:
 p=subprocess.run(['git',*args],capture_output=True,text=True);r['git'][label]={'output':p.stdout.strip(),'exit':p.returncode}
rs=[json.loads(p.read_text()) for p in Path('results/fdr_sprint_20260910/H1/kosum_tur3').glob('*_*_*_*.json')]
r['t214a']={}
for source in ['gt','model','uretim']:
 rows=[x for x in rs if x['rota_kaynak']==source]
 r['t214a'][source]={'n':len(rows),'basari':sum(x['basari'] for x in rows),'rota_ack':sum(bool(x['open_route_ack']) for x in rows),'harita_senaryo':len({(x['harita'],x['senaryo']) for x in rows}),'tohumlar':sorted({x['seed'] for x in rows})}
assert [(r['t214a'][k]['n'],r['t214a'][k]['basari']) for k in ['gt','model','uretim']]==[(45,45),(45,9),(15,0)]
(OUT/'dogrulama.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print('D441: 15 kayit; 1024 ana kosu 7 dogru; 512 teshis 6 dogru.')
print('Piksel: 29 karenin matrisi toplamla birebir; oranlar yeniden hesaplandi.')
print('Parmak izi: ayni boyutta icerik degisikligi YAKALANMADI (kusur uretildi).')
print('Watch: 3 zaman asimi; 0 cikarim; normal None donusu (kusur uretildi).')
print('DOCX: yalniz document.xml farkli; 124 medya parcasi korundu.')
print('Onceki dosyalar:',len(r['onceki_dosya_butunlugu']),'kontrol;',sum(not v for v in r['onceki_dosya_butunlugu'].values()),'degisiklik.')
print('SONUC: tum dogrulama beklentileri saglandi; uretim kusurlari ONARILMADI.')

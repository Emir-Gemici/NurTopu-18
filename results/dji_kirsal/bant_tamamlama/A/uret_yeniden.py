"""ops.json -> uc durumlu PNG + rapor.json. YALNIZ mevcut 0 pikselleri degistirir."""
import json, os, sys, time, hashlib
import numpy as np, cv2
sys.path.insert(0, r"O:\navitas\codes")
from rpi_inference import hedef_bant_yuksekligi
from karar_sozlesmesi import bant_temasi_gereken_px

KOK = r"O:\navitas"
SP  = r"C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\bant_A"
CIK = os.path.join(KOK, 'results', 'dji_kirsal', 'bant_tamamlama', 'A')
os.makedirs(CIK, exist_ok=True)
ATAMA = json.load(open(os.path.join(KOK,'results','dji_kirsal','bant_tamamlama_atama.json'), encoding='utf-8'))
A = ATAMA['gruplar']['A']
BH = hedef_bant_yuksekligi(540)          # 43
GEREKEN = bant_temasi_gereken_px(960)    # 20

def mask_yolu(r): return os.path.join(KOK,'results','dji_20260822','f5_olcek',r['maske'].replace('/',os.sep))
def img_yolu(r):  return os.path.join(KOK,r['goruntu'].replace('/',os.sep))

def temas(m, taraf):
    b = m[:BH] if taraf=='ust' else m[540-BH:]
    return int(np.count_nonzero(np.any(b==1, axis=0)))

def sayim(m):
    return {"etiketsiz": int((m==0).sum()), "sinif0": int((m==1).sum()), "sinif1": int((m==2).sum())}

def bolge_maskesi(op, sekil=(540,960)):
    z = np.zeros(sekil, np.uint8)
    t = op['tip']
    if t=='dikdortgen':
        x0,y0,x1,y1 = op['kutu']; z[y0:y1, x0:x1] = 1
    elif t=='poligon':
        cv2.fillPoly(z, [np.array(op['nokta'], np.int32)], 1)
    else:
        raise ValueError(t)
    return z.astype(bool)

def karanlik_oyma(s960, kutu, k=3.0, min_kenar=5, min_alan=30):
    """Olculmus derin golge/bosluk bolgelerini dondur (0 birakilacak yerler).

    Esik bandin KENDI dagilimindan: med - k*1.4826*MAD. Yalniz BAGLI ve
    yeterince BUYUK (>=25 cm) lekeler alinir; doku gurultusu elenir.
    """
    x0,y0,x1,y1 = kutu
    b = s960[y0:y1, x0:x1]
    g = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    med = float(np.median(g)); mad = float(np.median(np.abs(g-med)))
    esik = med - k*1.4826*mad
    ham = (g < esik).astype(np.uint8)
    ham = cv2.morphologyEx(ham, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    n,lab,st,_ = cv2.connectedComponentsWithStats(ham, 8)
    tut = np.zeros_like(ham)
    for j in range(1,n):
        x,y,w,h,a = st[j]
        if min(w,h) >= min_kenar and a >= min_alan:
            tut[lab==j] = 1
    tut = cv2.dilate(tut, np.ones((3,3),np.uint8), 1)
    z = np.zeros((540,960), np.uint8); z[y0:y1, x0:x1] = tut
    return z.astype(bool)

def esik_bolgesi(s960, kutu, yuzde, yon='parlak', min_alan=20, kapat=3):
    """Kutu icinde OLCULMUS parlaklik yuzdeligine gore bolge sec.

    yon='parlak' -> gri >= p(yuzde); yon='koyu' -> gri <= p(yuzde).
    Kucuk lekeler elenir, delikler kapatilir.
    """
    x0,y0,x1,y1 = kutu
    b = s960[y0:y1, x0:x1]
    g = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)
    t = float(np.percentile(g, yuzde))
    ham = (g >= t).astype(np.uint8) if yon=='parlak' else (g <= t).astype(np.uint8)
    if kapat:
        ham = cv2.morphologyEx(ham, cv2.MORPH_CLOSE, np.ones((kapat,kapat),np.uint8))
        ham = cv2.morphologyEx(ham, cv2.MORPH_OPEN, np.ones((kapat,kapat),np.uint8))
    n,lab,st,_ = cv2.connectedComponentsWithStats(ham, 8)
    tut = np.zeros_like(ham)
    for j in range(1,n):
        if st[j][4] >= min_alan:
            tut[lab==j] = 1
    z = np.zeros((540,960), np.uint8); z[y0:y1, x0:x1] = tut
    return z.astype(bool)


def uygula(i, ops_kare):
    r = A[i]
    m0 = np.squeeze(cv2.imread(mask_yolu(r), cv2.IMREAD_UNCHANGED)).astype(np.uint8)
    assert m0.shape==(540,960)
    s960 = cv2.resize(cv2.imread(img_yolu(r)), (960,540), interpolation=cv2.INTER_AREA)
    m = m0.copy()
    for op in ops_kare['ops']:
        if op['tip']=='esik':
            sec = esik_bolgesi(s960, op['kutu'], op['yuzde'], op.get('yon','parlak'),
                               op.get('min_alan',20), op.get('kapat',3)) & (m0==0)
            m[sec] = int(op['deger'])
            continue
        if op['tip']=='karanlik':
            sec = karanlik_oyma(s960, op['kutu'], op.get('k',3.0), op.get('min_kenar',5), op.get('min_alan',30)) & (m0==0)
            m[sec] = 0
            continue
        sec = bolge_maskesi(op) & (m0==0)
        m[sec] = int(op['deger'])
    assert set(np.unique(m).tolist()) <= {0,1,2}
    assert np.all(m[m0!=0] == m0[m0!=0]), "mevcut etiket bozuldu"
    yol = os.path.join(CIK, f"{r['kare']}_uc.png")
    cv2.imwrite(yol, m)
    kayit = {
        "kare": r['kare'],
        "saniye": ops_kare.get('saniye', 0),
        "degisen_piksel": int((m!=m0).sum()),
        "once": sayim(m0), "sonra": sayim(m),
        "bant_temas_once": {"ust": temas(m0,'ust'), "alt": temas(m0,'alt')},
        "bant_temas_sonra": {"ust": temas(m,'ust'), "alt": temas(m,'alt')},
        "bant_gereken_px": GEREKEN,
        "bant_yeterli_sonra": {"ust": temas(m,'ust')>=GEREKEN, "alt": temas(m,'alt')>=GEREKEN},
        "eksik_taraf": r['eksik_taraf'], "neden": r['neden'],
        "hukum_gerekce": ops_kare['hukum_gerekce'],
        "guven": ops_kare['guven'],
        "png": os.path.relpath(yol, KOK).replace(os.sep, '/'),
        "md5": hashlib.md5(open(yol,'rb').read()).hexdigest(),
    }
    return kayit

def main():
    ops = json.load(open(os.path.join(SP,'ops.json'), encoding='utf-8'))
    rapor=[]
    for anahtar in sorted(ops.keys(), key=int):
        rapor.append(uygula(int(anahtar), ops[anahtar]))
    with open(os.path.join(CIK,'rapor.json'),'w',encoding='utf-8') as f:
        json.dump({"amele":"A","bant_yuksekligi_px":BH,"gereken_temas_px":GEREKEN,
                   "kare_sayisi":len(rapor),"kareler":rapor}, f, ensure_ascii=False, indent=1)
    for k in rapor:
        print(f"{k['kare'][-24:]} deg={k['degisen_piksel']:7d} ust {k['bant_temas_once']['ust']:3d}->{k['bant_temas_sonra']['ust']:3d} alt {k['bant_temas_once']['alt']:3d}->{k['bant_temas_sonra']['alt']:3d} guven={k['guven']}")
    print("yazildi:", len(rapor))

if __name__=="__main__":
    main()

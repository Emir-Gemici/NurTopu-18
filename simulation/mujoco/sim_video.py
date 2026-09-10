"""T214-B · ON_KAYIT H1-K7 — MuJoCo görev icra simülasyonu VİDEOSU (üç kamera + HUD, ≥ 90 s, ≥ 24 FPS).

İki adım (GPU işleri TEK süreçte sıralı — ON_KAYIT §5.6):
  --kos        3 koşum (kolay / orta / zor) `gorev_kosumu.kos(..., kare_kaydet=True)` →
               `results/fdr_sprint_20260910/video/kosum/<kaynak>_<h>_<lv>_<tohum>.json` + `kareler_video/`
               (üç kamera JPG'si, 25 Hz sim saati; `durum.jsonl` = kare başına HUD girdisi). Birincil koşum
               ÜRETİM MODELİ'dir (mozaik zinciri, v36); başarısızsa aynı harita/seviye/tohum YER GERÇEĞİ
               ile koşulur ve bu seçim etiketlenir (gizlenmez).
  --birlestir  kareler + durum.jsonl + koşum JSON'u → HUD'lu 1280×720, 25 FPS ana kopya (`cv2.VideoWriter`,
               FFMPEG arka ucu, mp4v) → teslim dosyası H.264 (ffmpeg libx264; cv2'de mp4v bit hızı ayarlanamıyor,
               ölçüldü — `h264_donustur`) + `video_ozeti.json` (sha256, süre, çözünürlük, kare sayısı, bölüm
               tablosu, kosum_tur3 eşliği, değişmezlik) + `OKUBENI.md` (video_ozeti.json'dan ÜRETİLİR).

HUD (kare başına, `durum.jsonl` + koşum JSON'undan; tahmin yok): sim saati (MuJoCo `data.time`; İHA kolu
kinematik profil), faz (FIRLATMA / TARAMA / ROTA / AKTARIM / IKA_GO / SURUS / VARIS), rota kaynağı etiketi
(YER GERCEGI / URETIM MODELI), OPEN_ROUTE ACK [ika, yks] · IHA_LANDED · IKA_GO · IKA_GO ACK, İKA→HB mesafesi,
temas sayısı, oynatma hızı, SENTETİK etiketi. Yazılar ASCII'dir (cv2 Hershey yazı tipi Türkçe harf çizmez).

Oynatma hızı faza göre (`HIZ`; kayıt 25 Hz = video 25 FPS → 1× gerçek zaman): FIRLATMA/TARAMA 2×, AKTARIM 1×,
IKA_GO 0,25× (kare tekrarı; olay 0,1–0,2 s sürer), SURUS 3×. ROTA kartı sim saatini DONDURUR: `iha_haritala`
hesap süresi sim saatine eklenmez (gorev_kosumu SINIR). Her kartta ve HUD'da hız yazılıdır.

SENTETİK: saha kanıtı değildir. Video linki İNSAN (T222); mp4 git dışıdır (`*.mp4`).

Kullanım (depo kökünden):
  venv python -B simulation/mujoco/sim_video.py --kos
  venv python -B simulation/mujoco/sim_video.py --birlestir
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
for _p in (str(BURASI.parent / "scripts"), str(KOK / "codes"), str(KOK / "comms"), str(BURASI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gorev_kosumu as gk                                 # noqa: E402

VIDEO_DIR = KOK / "results" / "fdr_sprint_20260910" / "video"
KOSUM_DIR = VIDEO_DIR / "kosum"
TUR3_DIR = gk.KOSUM_TUR3_KOK
K3_OZET = KOK / "results" / "fdr_sprint_20260910" / "H1" / "k3_uretim_boru" / "ozet_k3_uretim.json"
MP4_ADI = "navitas_sim_gorev_20260910.mp4"
OZET_ADI = "video_ozeti.json"
OKUBENI_ADI = "OKUBENI.md"
FPS = 25
GEN, YUK = 1280, 720
ANA_W, ANA_H = 960, 540
KUC_W, KUC_H = 320, 180
ESIK_SURE_S = 90.0                 # ON_KAYIT H1-K7 (önceden yazılı; gevşetilmez)
ESIK_FPS = 24.0
BOYUT_SINIRI_MB = 60.0             # görev tanımı (T214-B): < 60 MB
KOSUMLAR = (("model", 1, "kolay", 44), ("model", 3, "orta", 42), ("model", 5, "zor", 42))
YEDEK_KAYNAK = "gt"
FAZLAR = ("FIRLATMA", "TARAMA", "ROTA", "AKTARIM", "IKA_GO", "SURUS", "VARIS")
HIZ = {"FIRLATMA": 2.0, "TARAMA": 2.0, "AKTARIM": 1.0, "IKA_GO": 0.25, "SURUS": 3.0}
KART_S = {"giris": 8.0, "kosum": 4.0, "rota": 4.0, "varis": 3.0, "cikis": 8.0}
ANA_KAMERA = {"FIRLATMA": "ucuncu_sahis", "TARAMA": "iha_nadir", "AKTARIM": "ucuncu_sahis",
              "IKA_GO": "ika_takip", "SURUS": "ika_takip", "VARIS": "ika_takip"}
KAMERALAR = tuple(ad for ad, _ in gk._KareKaydedici.KAMERALAR)
KAMERA_ETIKETI = {"iha_nadir": "IHA NADIR KAMERA (tarama, 30 m)", "ucuncu_sahis": "UCUNCU SAHIS (arena genel)",
                  "ika_takip": "IKA TAKIP KAMERASI"}
KAYNAK_ETIKETI_ASCII = {"gt": "YER GERCEGI", "model": "URETIM MODELI", "uretim": "URETIM BORU HATTI"}
KAYNAK_RENGI = {"gt": (214, 120, 42), "model": (0, 140, 255), "uretim": (60, 60, 220)}
ESLIK_ALANLARI = ("basari", "rota_bulundu", "rota_dogru", "model_yol", "model_guven", "cikis_kodu",
                  "temas_sayisi", "hb_icinde", "wp_sayisi", "sure_sim_ika", "varis_mesafesi_m")

_KATLA = str.maketrans({"İ": "I", "ı": "i", "Ğ": "G", "ğ": "g", "Ü": "U", "ü": "u", "Ş": "S", "ş": "s",
                        "Ö": "O", "ö": "o", "Ç": "C", "ç": "c", "→": "->", "·": "|", "—": "-", "–": "-",
                        "×": "x", "≥": ">=", "≤": "<=", "✓": "OK", "✗": "--", "…": "..."})


# ── saf yardımcılar (testli) ────────────────────────────────────────────────

def ascii_katla(metin) -> str:
    """HUD metni → ASCII (cv2 Hershey yazı tipi Türkçe harf çizmez; '?' yerine anlamlı karşılık)."""
    return str(metin).translate(_KATLA).encode("ascii", "replace").decode("ascii")


def faz_belirle(satir: dict) -> str:
    """`durum.jsonl` satırı → HUD fazı. Uçuş: profil fazı (tarama/dönüş = TARAMA, öncesi FIRLATMA).
    Sürüş modeli: hakem/sürüş bayraklarından (VARIS > SURUS > IKA_GO > AKTARIM)."""
    if satir.get("kaynak") == "ucus":
        return "TARAMA" if satir.get("faz_profil") in ("tarama", "donus") else "FIRLATMA"
    if satir.get("surus_bitti"):
        return "VARIS"
    if satir.get("surus"):
        return "SURUS"
    if satir.get("ika_go"):
        return "IKA_GO"
    return "AKTARIM"


def kare_plani(fazlar, hiz=HIZ) -> list:
    """Kayıt karesi dizisi (faz listesi) → video karesi olarak yayınlanan kayıt indeksleri.

    Faz hızı s: her kayıt karesi ortalama 1/s video karesi (s > 1 seyreltme, s < 1 tekrar). Kayıt aralığı
    1/KARE_HZ_VIDEO = 1/FPS olduğundan s = 1 gerçek zamandır. Her fazın İLK karesi daima yayınlanır."""
    plan, acc, onceki = [], 0.0, None
    for i, f in enumerate(fazlar):
        s = float(hiz[f])
        if f != onceki:
            acc = max(0.0, 1.0 - 1.0 / s)
            onceki = f
        acc += 1.0 / s
        while acc >= 1.0 - 1e-9:
            plan.append(i)
            acc -= 1.0
    return plan


def hiz_metni(s) -> str:
    if s is None:
        return "sim saati DONDURULDU (kart)"
    if abs(s - 1.0) < 1e-9:
        return "oynatma 1x (gercek zaman)"
    return f"oynatma {s:g}x ({'hizlandirilmis' if s > 1 else 'yavas'})"


def sha256_dosya(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def sha256_metin(p: Path) -> str:
    """Metin kanıtının sha256'sı, satır sonu NORMALİZE (CRLF → LF). NEDEN: depo `core.autocrlf=true`;
    koşum JSON'ları Windows'ta CRLF, `durum.jsonl` LF yazılır, checkout hepsini CRLF verir → bayt sha'sı
    ağaçtan ağaca değişirdi (D-407 §4 sınıfı kırılgan kapı). İkili dosya (mp4) için `sha256_dosya`."""
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _j(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _ad(k, h, lv, s) -> str:
    return f"{k}_{h}_{lv}_{s}"


# ── 1) koşumlar (GPU) ───────────────────────────────────────────────────────

def kos_hepsi(res: int = 1280) -> list:
    """Birincil koşumlar (ÜRETİM MODELİ); başarısızsa aynı harita/seviye/tohum YER GERÇEĞİ (etiketli)."""
    KOSUM_DIR.mkdir(parents=True, exist_ok=True)
    model, kunye = gk.model_yukle()
    print(f"[video] model {kunye['model_id']} sha eşleşti={kunye['eslesti']}", flush=True)
    secim = []
    for kaynak, h, lv, s in KOSUMLAR:
        t0 = time.perf_counter()
        r = gk.kos(h, lv, s, kaynak, res=res, out=KOSUM_DIR, model=model, model_kunye=kunye,
                   conf=0.15, kare_kaydet=True)
        print(f"[video] {_ad(kaynak, h, lv, s)}: basari={r['basari']} kod={r['cikis_kodu']} "
              f"sure={r['sure_sim_ika']} varis={r['varis_mesafesi_m']} temas={r['temas_sayisi']} "
              f"kare={r['kare_n_video']} (ucus {r['kare_n_video_ucus']}) duvar={time.perf_counter() - t0:.0f} s",
              flush=True)
        kayit = {"birincil": _ad(kaynak, h, lv, s), "secilen": _ad(kaynak, h, lv, s), "yedek_nedeni": None}
        if not r["basari"]:
            ry = gk.kos(h, lv, s, YEDEK_KAYNAK, res=res, out=KOSUM_DIR, kare_kaydet=True)
            print(f"[video] YEDEK {_ad(YEDEK_KAYNAK, h, lv, s)}: basari={ry['basari']}", flush=True)
            kayit.update(secilen=_ad(YEDEK_KAYNAK, h, lv, s),
                         yedek_nedeni=f"birincil başarısız (kod {r['cikis_kodu']}, rota_bulundu {r['rota_bulundu']})")
        secim.append(kayit)
    (KOSUM_DIR / "secim.json").write_text(json.dumps(secim, ensure_ascii=False, indent=1), encoding="utf-8")
    degismezlik_kos(res=res)
    return secim


DEGISMEZLIK = ("gt", 1, "kolay", 42)     # rota deterministik (arena.route_waypoints) → fizik eşliği kesin sınanır
DEGISMEZLIK_ALANLARI = ESLIK_ALANLARI + ("takip_hatasi_maks_m", "takip_hatasi_ort_m", "takip_ornek_n",
                                         "plan_takip_hatasi_maks_m", "son_konum", "t_ika_go", "t_ika_go_ack",
                                         "sure_sim_gorev", "temas_adim")


def degismezlik_kos(res: int = 1280) -> dict:
    """Kaydedici fizik trajektorisini değiştirmez mi? YER GERÇEĞİ koşumunu (rota render'dan bağımsız) kareli
    koşup kosum_tur3'teki kaydısız eşiyle alan alan karşılaştırır → `kosum/degismezlik.json`."""
    k, h, lv, s = DEGISMEZLIK
    out = KOSUM_DIR / "degismezlik"
    out.mkdir(parents=True, exist_ok=True)
    r = gk.kos(h, lv, s, k, res=res, out=out, kare_kaydet=True)
    t3 = _j(TUR3_DIR / f"{_ad(k, h, lv, s)}.json")
    alan = {a: {"video": r.get(a), "kosum_tur3": t3.get(a), "es": r.get(a) == t3.get(a)} for a in DEGISMEZLIK_ALANLARI}
    sonuc = {"kosum": _ad(k, h, lv, s), "kare_n_video": r.get("kare_n_video"), "alanlar": alan,
             "hepsi_es": all(v["es"] for v in alan.values()),
             "kosum_tur3": str((TUR3_DIR / f"{_ad(k, h, lv, s)}.json").relative_to(KOK)).replace("\\", "/")}
    (KOSUM_DIR / "degismezlik.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[video] değişmezlik {sonuc['kosum']}: hepsi_es={sonuc['hepsi_es']} "
          + ", ".join(f"{a}={v['video']}↔{v['kosum_tur3']}" for a, v in alan.items() if not v["es"]), flush=True)
    return sonuc


# ── 2) çizim ────────────────────────────────────────────────────────────────

def _cv2():
    import cv2
    return cv2


def _yaz(img, metin, xy, olcek=0.55, renk=(255, 255, 255), kalin=1):
    """Gölgeli yazı. Gölge AYNI kalınlıkta, 1 px ofsetle çizilir: cv2 5 kalınlıkla harf aralığını da
    büyüttüğünden kalın siyah dış hat metinden geniş çıkıp sonda 'hayalet' harf bırakıyordu (gözle görüldü)."""
    cv2 = _cv2()
    m = ascii_katla(metin)
    x, y = xy
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        cv2.putText(img, m, (x + dx, y + dy), cv2.FONT_HERSHEY_SIMPLEX, olcek, (0, 0, 0), kalin, cv2.LINE_AA)
    cv2.putText(img, m, xy, cv2.FONT_HERSHEY_SIMPLEX, olcek, renk, kalin, cv2.LINE_AA)


def _sigdir(img, w, h):
    """En-boy korunarak (w, h) kutusuna sığdır, kenarlar siyah."""
    cv2 = _cv2()
    out = np.zeros((h, w, 3), np.uint8)
    if img is None:
        return out
    ih, iw = img.shape[:2]
    o = min(w / iw, h / ih)
    nw, nh = max(1, int(round(iw * o))), max(1, int(round(ih * o)))
    k = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if o < 1 else cv2.INTER_LINEAR)
    x, y = (w - nw) // 2, (h - nh) // 2
    out[y:y + nh, x:x + nw] = k
    return out


def _panel(tuval, img, x, y, w, h, etiket, vurgu=False):
    cv2 = _cv2()
    tuval[y:y + h, x:x + w] = _sigdir(img, w, h)
    cv2.rectangle(tuval, (x, y), (x + w - 1, y + h - 1), (0, 200, 255) if vurgu else (90, 90, 90), 2 if vurgu else 1)
    (tw, _), _ = cv2.getTextSize(ascii_katla(etiket), cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.rectangle(tuval, (x + 2, y + 2), (x + 12 + tw, y + 22), (0, 0, 0), -1)
    _yaz(tuval, etiket, (x + 7, y + 17), 0.45)


def _isaret(v) -> str:
    return "[OK]" if v else "[--]"


def hud_ciz(tuval, *, faz, t, hiz, kaynak, kosum_ad, sira, toplam, model_guven, satir=None, not_=None):
    """Alt şerit (0,540)-(1280,720) + sağ alt bilgi kutusu (960,360)-(1280,540)."""
    cv2 = _cv2()
    satir = satir or {}
    y0 = ANA_H
    tuval[y0:, :] = (26, 26, 26)
    w = (GEN - 20) // len(FAZLAR)
    i_cur = FAZLAR.index(faz)
    for i, f in enumerate(FAZLAR):
        x = 10 + i * w
        bg = (0, 170, 255) if i == i_cur else ((70, 95, 70) if i < i_cur else (48, 48, 48))
        cv2.rectangle(tuval, (x + 2, y0 + 8), (x + w - 2, y0 + 40), bg, -1)
        _yaz(tuval, f, (x + 12, y0 + 31), 0.6, (0, 0, 0) if i == i_cur else (225, 225, 225), 2 if i == i_cur else 1)
    _yaz(tuval, f"SIM SAATI  t = {t:7.2f} s", (12, y0 + 74), 0.8, (255, 255, 255), 2)
    _yaz(tuval, hiz_metni(hiz), (430, y0 + 74), 0.6, (200, 200, 200))
    acked = satir.get("acked") or []
    ack = (f"OPEN_ROUTE ACK  ika {_isaret('ika' in acked)}  yks {_isaret('yks' in acked)}    "
           f"IHA_LANDED {_isaret(satir.get('landed'))}    IKA_GO {_isaret(satir.get('ika_go'))}  "
           f"ACK {_isaret(satir.get('ika_go_ack'))}")
    _yaz(tuval, ack, (12, y0 + 110), 0.6, (180, 255, 180))
    if satir.get("kaynak") == "surus":
        ika = f"IKA -> HB {satir.get('hb_m', 0.0):6.2f} m    temas {satir.get('temas', 0)}"
    else:
        ika = "IKA: KB'de bekliyor (rota yok)"
    _yaz(tuval, ika, (12, y0 + 146), 0.6, (230, 230, 230))
    if not_:
        _yaz(tuval, not_, (430, y0 + 146), 0.5, (200, 200, 120))
    cv2.rectangle(tuval, (GEN - 356, y0 + 88), (GEN - 10, y0 + 170), (0, 0, 175), -1)
    _yaz(tuval, "SENTETIK", (GEN - 342, y0 + 122), 0.9, (255, 255, 255), 2)
    _yaz(tuval, "MuJoCo simulasyonu - saha kaniti degil", (GEN - 346, y0 + 154), 0.45, (255, 255, 255))
    # sağ alt bilgi kutusu
    bx, by = ANA_W, 2 * KUC_H
    tuval[by:ANA_H, bx:] = (18, 18, 18)
    _yaz(tuval, f"KOSUM {sira}/{toplam}  {kosum_ad}", (bx + 10, by + 26), 0.5)
    _yaz(tuval, "ROTA KAYNAGI:", (bx + 10, by + 60), 0.55, (200, 200, 200))
    cv2.rectangle(tuval, (bx + 10, by + 72), (GEN - 10, by + 112), KAYNAK_RENGI.get(kaynak, (90, 90, 90)), -1)
    _yaz(tuval, KAYNAK_ETIKETI_ASCII.get(kaynak, kaynak), (bx + 18, by + 102), 0.85, (255, 255, 255), 2)
    alt = ("v36 mozaik zinciri | guven " + (f"{model_guven:.2f}" if model_guven is not None else "-")
           if kaynak == "model" else "arena.route_waypoints (goruntu isleme YOK)")
    _yaz(tuval, alt, (bx + 10, by + 140), 0.42, (220, 220, 220))
    _yaz(tuval, "sure: sim saati | IHA kolu kinematik", (bx + 10, by + 166), 0.42, (170, 170, 170))


def kart_ciz(satirlar_metin, baslik) -> np.ndarray:
    cv2 = _cv2()
    t = np.full((YUK, GEN, 3), 20, np.uint8)
    cv2.rectangle(t, (0, 0), (GEN, 70), (0, 0, 150), -1)
    _yaz(t, baslik, (30, 48), 1.0, (255, 255, 255), 2)
    y = 120
    for s in satirlar_metin:
        olcek, renk = (0.62, (235, 235, 235))
        if isinstance(s, tuple):
            s, olcek, renk = s
        _yaz(t, s, (40, y), olcek, renk, 2 if olcek >= 0.7 else 1)
        y += int(46 * max(olcek, 0.62) / 0.62) if olcek >= 0.7 else 38
    _yaz(t, "SENTETIK - MuJoCo simulasyonu - saha kaniti degildir", (40, YUK - 30), 0.6, (120, 160, 255), 1)
    return t


# ── 3) birleştirme ──────────────────────────────────────────────────────────

class _KareOkuyucu:
    def __init__(self, kdir: Path):
        self.kdir = kdir
        self._son = {}

    def oku(self, n: int, ad: str):
        anahtar = (n, ad)
        if anahtar not in self._son:
            img = _cv2().imread(str(self.kdir / f"{ad}_{n:05d}.jpg"))
            if img is None:
                raise FileNotFoundError(self.kdir / f"{ad}_{n:05d}.jpg")
            self._son = {k: v for k, v in self._son.items() if k[0] >= n - 1}
            self._son[anahtar] = img
        return self._son[anahtar]


def _durum_oku(kdir: Path) -> list:
    return [json.loads(s) for s in (kdir / "kareler_video" / "durum.jsonl").read_text(encoding="utf-8").splitlines()
            if s.strip()]


def kamera_etiketi(kam: str, faz: str) -> str:
    """İHA nadir kamerası tarama bittikten sonra iniş/yer görüntüsü verir → etiket faza bağlı (yanıltmasın)."""
    if kam == "iha_nadir":
        return {"FIRLATMA": "IHA NADIR KAMERA (tirmanis)", "TARAMA": KAMERA_ETIKETI[kam]}.get(
            faz, "IHA NADIR KAMERA (inis / yerde)")
    return KAMERA_ETIKETI[kam]


def _cerceve(okuyucu, satir, faz, ana_override=None, ana_etiket=None):
    tuval = np.zeros((YUK, GEN, 3), np.uint8)
    ana = ANA_KAMERA[faz]
    digerleri = [k for k in KAMERALAR if k != ana]
    img_ana = ana_override if ana_override is not None else okuyucu.oku(satir["n"], ana)
    _panel(tuval, img_ana, 0, 0, ANA_W, ANA_H, ana_etiket or kamera_etiketi(ana, faz), vurgu=True)
    for j, k in enumerate(digerleri):
        _panel(tuval, okuyucu.oku(satir["n"], k), ANA_W, j * KUC_H, KUC_W, KUC_H, kamera_etiketi(k, faz))
    return tuval


def _eslik(r: dict) -> dict:
    p = TUR3_DIR / f"{_ad(r['rota_kaynak'], r['harita'], r['senaryo'], r['seed'])}.json"
    if not p.is_file():
        return {"kaynak": None, "alanlar": {}, "hepsi_es": None}
    t3 = _j(p)
    alan = {k: {"video": r.get(k), "kosum_tur3": t3.get(k), "es": r.get(k) == t3.get(k)} for k in ESLIK_ALANLARI}
    # Rota geometrisi: model koşumlarında rota GPU render'lı mozaikten gelir (kareler ~%50 bayt-eş, T213-A) →
    # rota.json farklıysa sürüş farkı rotadandır, kaydediciden değil (kaydedici: `degismezlik.json`).
    ad = _ad(r["rota_kaynak"], r["harita"], r["senaryo"], r["seed"])
    rv, rt = KOSUM_DIR / ad / "iha_scan" / "rota.json", TUR3_DIR / ad / "iha_scan" / "rota.json"
    rota_es = (_j(rv) == _j(rt)) if (rv.is_file() and rt.is_file()) else None
    return {"kaynak": str(p.relative_to(KOK)).replace("\\", "/"), "alanlar": alan,
            "hepsi_es": all(v["es"] for v in alan.values()), "rota_json_es": rota_es}


def _genel_sayilar() -> dict:
    """Giriş/çıkış kartı sayıları — ÖLÇÜM JSON'larından (elle yazılmaz)."""
    import t214a_rapor
    oz = _j(TUR3_DIR / "ozet_kosum.json")
    rs = [_j(p) for p in sorted(TUR3_DIR.glob("*_*_*_*.json"))]
    k3m = t214a_rapor._k3_mozaik(rs, 42)
    k3u = _j(K3_OZET)["beslemeler"]["kerteriz"]
    kay = {k: {"basari_n": o["basari_n"], "n": o["n"], "harita": o["harita_hepsi_basarili_n"],
               "harita_n": o["harita_n"]} for k, o in oz["kaynaklar"].items()}
    return {"k3_mozaik": {"dogru": k3m["dogru"], "n": k3m["n"]},
            "k3_uretim": {"dogru": k3u["dogru_n"], "n": k3u["harita_n"]}, "k5": kay,
            "kaynak": [str((TUR3_DIR / "ozet_kosum.json").relative_to(KOK)).replace("\\", "/"),
                       str(K3_OZET.relative_to(KOK)).replace("\\", "/")]}


def _hukum(a, b, esik=12) -> str:
    return "GECTI" if a >= esik else "DUSTU"


ILK_KOSUM_DIR = VIDEO_DIR / "ilk_kosum_kare_bekle_sonu"


def _ilk_kosum_kusuru() -> dict | None:
    """T214-B ilk video koşumu (kare `bekle` SONUNDA çiziliyordu) ↔ kosum_tur3 — ölçülen kusurun kaydı."""
    if not ILK_KOSUM_DIR.is_dir():
        return None
    satir = []
    for p in sorted(ILK_KOSUM_DIR.glob("*_*_*_*.json")):
        v, t3 = _j(p), _j(TUR3_DIR / p.name)
        satir.append({"kosum": p.stem, **{k: [v.get(k), t3.get(k)] for k in
                                          ("sure_sim_ika", "varis_mesafesi_m", "takip_hatasi_maks_m", "t_ika_go_ack")}})
    return {"klasor": str(ILK_KOSUM_DIR.relative_to(KOK)).replace("\\", "/"), "alanlar": "[ilk video koşumu, kosum_tur3]",
            "neden": "kare bekle sonunda çiziliyordu → mj_forward xpos'u tazeledi → denetleyici 2 ms taze poz okudu "
                     "(olay zamanları eş); düzeltme: kare yalnız alt-adım öbeğinin başında (gorev_kosumu.surus_adimla)",
            "satirlar": satir}


FFMPEG_ADAYLARI = (Path(r"C:\ffmpeg\bin\ffmpeg.exe"),)
H264_CRF = 23


def _ffmpeg():
    import shutil
    w = shutil.which("ffmpeg")
    return Path(w) if w else next((p for p in FFMPEG_ADAYLARI if p.is_file()), None)


def h264_donustur(ana: Path, cikti: Path) -> dict:
    """cv2 mp4v ana kopyası → H.264 (libx264, CRF) teslim dosyası.

    NEDEN (ölçüldü, T214-B): bu cv2 derlemesinde mp4v bit hızı ayarlanamıyor — `OPENCV_FFMPEG_WRITER_OPTIONS`
    ("b;2000000", "b;3000000") etkisiz, üç ayarda da 5,82 MB / 10 s → 178 s video 123,7 MB > 60 MB sınırı.
    ffmpeg yoksa ana kopya aynen teslim edilir ve boyut hükmü düşer (gizlenmez)."""
    import shutil
    import subprocess
    ff = _ffmpeg()
    if ff is None:
        shutil.copyfile(ana, cikti)
        return {"arac": None, "not": "ffmpeg bulunamadı — cv2 ana kopyası teslim edildi"}
    arg = ["-y", "-hide_banner", "-loglevel", "error", "-i", str(ana), "-c:v", "libx264", "-preset", "medium",
           "-crf", str(H264_CRF), "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", "-an", str(cikti)]
    p = subprocess.run([str(ff)] + arg, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg dönüşümü düştü (çıkış {p.returncode}): {p.stderr[-400:]}")
    surum = subprocess.run([str(ff), "-hide_banner", "-version"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace").stdout.splitlines()[0]
    rel = lambda q: str(Path(q).relative_to(KOK)).replace("\\", "/")      # noqa: E731
    return {"arac": "ffmpeg", "surum": surum, "codec": f"libx264 CRF {H264_CRF} · preset medium · yuv420p · {FPS} FPS",
            "komut": " ".join(["ffmpeg"] + [rel(a) if a in (str(ana), str(cikti)) else a for a in arg])}


def birlestir(cikti: Path | None = None) -> dict:
    cv2 = _cv2()
    cikti = Path(cikti or VIDEO_DIR / MP4_ADI)
    ana = cikti.with_name(cikti.stem + "_cv2_mp4v.mp4")          # cv2.VideoWriter ana kopyası (git dışı)
    secim = _j(KOSUM_DIR / "secim.json")
    g = _genel_sayilar()
    yazici = cv2.VideoWriter(str(ana), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (GEN, YUK))
    if not yazici.isOpened():
        raise RuntimeError("cv2.VideoWriter açılamadı (mp4v / FFMPEG)")
    sayac = {"n": 0}
    bolumler = []

    def yaz(img, adet=1):
        for _ in range(adet):
            yazici.write(img)
            sayac["n"] += 1

    k5 = g["k5"]
    giris = kart_ciz([
        ("NAVITAS - MuJoCo 3B gorev icra simulasyonu (T214-B)", 0.8, (255, 255, 255)),
        "Zincir: mancinik firlatma -> 30 m nadir tarama -> goruntu isleme (uretim modeli v36)",
        "        -> OPEN_ROUTE (UDP, ACK'li) -> sim hakem (otomatik) -> IHA_LANDED -> IKA_GO",
        "        -> IKA otonom surus (ika_nav + MuJoCo fizik, skid-steer) -> HB'ye varis",
        "Kameralar: IHA nadir (tarama) | ucuncu sahis (arena genel) | IKA takip",
        ("Olcum (ON_KAYIT esikleri gevsetilmedi; 15 harita x 3 tohum):", 0.7, (255, 220, 120)),
        f"  H1-K3 mozaik zinciri dogru etiket {g['k3_mozaik']['dogru']}/{g['k3_mozaik']['n']} (esik 12/15) "
        f"-> {_hukum(g['k3_mozaik']['dogru'], g['k3_mozaik']['n'])}",
        f"  H1-K3 uretim kare-bazli boru hatti {g['k3_uretim']['dogru']}/{g['k3_uretim']['n']} "
        f"-> {_hukum(g['k3_uretim']['dogru'], g['k3_uretim']['n'])}",
        f"  H1-K5 YER GERCEGI {k5['gt']['basari_n']}/{k5['gt']['n']} (harita {k5['gt']['harita']}/{k5['gt']['harita_n']}) "
        f"-> {_hukum(k5['gt']['harita'], k5['gt']['harita_n'])} | URETIM MODELI {k5['model']['basari_n']}/{k5['model']['n']} "
        f"(harita {k5['model']['harita']}/{k5['model']['harita_n']}) -> {_hukum(k5['model']['harita'], k5['model']['harita_n'])}",
        "Bu videodaki 3 kosum BASARILI kosumlardir; genel oran yukaridadir (secim etiketli).",
    ], "SENTETIK | NAVITAS gorev simulasyonu")
    yaz(giris, int(KART_S["giris"] * FPS))
    bolumler.append({"bolum": "giris_karti", "video_s": KART_S["giris"], "hiz": None})

    kosum_bilgi = []
    for sira, kay in enumerate(secim, 1):
        r = _j(KOSUM_DIR / f"{kay['secilen']}.json")
        kdir = KOSUM_DIR / kay["secilen"]
        satirlar = _durum_oku(kdir)
        okuyucu = _KareOkuyucu(kdir / "kareler_video")
        kaynak = r["rota_kaynak"]
        ad = f"harita {r['harita']} | {r['senaryo']} | tohum {r['seed']}"
        guven = r.get("model_guven")
        t_bas = sayac["n"] / FPS
        faz_video = {}

        def hud(tuval, faz, t, hiz, satir=None, not_=None):
            hud_ciz(tuval, faz=faz, t=t, hiz=hiz, kaynak=kaynak, kosum_ad=ad, sira=sira, toplam=len(secim),
                    model_guven=guven, satir=satir, not_=not_)
            return tuval

        genel = k5.get(kaynak, {})
        kart = kart_ciz([
            (f"KOSUM {sira}/{len(secim)} - {ad}", 0.8, (255, 255, 255)),
            (f"ROTA KAYNAGI: {KAYNAK_ETIKETI_ASCII.get(kaynak, kaynak)}"
             + (" (iha_haritala mozaik zinciri, v36, imgsz 512)" if kaynak == "model" else " (arena.route_waypoints)"),
             0.7, (120, 200, 255)),
            f"Bu kosum: {'BASARILI' if r['basari'] else 'BASARISIZ'} | surus {r['sure_sim_ika']} s (sim) | "
            f"varis {r['varis_mesafesi_m']} m | temas {r['temas_sayisi']} | cikis kodu {r['cikis_kodu']}",
            (f"Genel oran ({kaynak}, kosum_tur3): {genel.get('basari_n')}/{genel.get('n')} | "
             f"harita {genel.get('harita')}/{genel.get('harita_n')} (esik 12/15)", 0.62, (255, 220, 120)),
            ("Secim: " + (kay["yedek_nedeni"] or "birincil kosum (URETIM MODELI) basarili"), 0.55, (200, 200, 200)),
            "Oynatma: FIRLATMA/TARAMA 2x | AKTARIM 1x | IKA_GO 0.25x | SURUS 3x | ROTA karti sim saatini dondurur",
        ], f"KOSUM {sira}/{len(secim)} | {KAYNAK_ETIKETI_ASCII.get(kaynak, kaynak)}")
        yaz(kart, int(KART_S["kosum"] * FPS))

        ucus = [s for s in satirlar if s["kaynak"] == "ucus"]
        surus = [s for s in satirlar if s["kaynak"] == "surus"]
        # uçuş
        f_ucus = [faz_belirle(s) for s in ucus]
        for i in kare_plani(f_ucus):
            s, f = ucus[i], f_ucus[i]
            yaz(hud(_cerceve(okuyucu, s, f), f, s["t"], HIZ[f], s))
            faz_video[f] = faz_video.get(f, 0) + 1
        # ROTA kartı (sim saati dondurulur)
        son_ucus = ucus[-1]
        scan = kdir / "iha_scan"
        mt = r.get("model_teshis") or {}
        tuval = np.zeros((YUK, GEN, 3), np.uint8)
        algi = cv2.imread(str(scan / "algi.jpg")) if kaynak == "model" else None
        mozaik = cv2.imread(str(scan / "ortomozaik.jpg")) if kaynak == "model" else None
        if kaynak == "model":
            _panel(tuval, algi, 0, 0, ANA_W, ANA_H, "GORUNTU ISLEME (v36)", vurgu=True)
            _panel(tuval, mozaik, ANA_W, 0, KUC_W, KUC_H, "ORTOMOZAIK (tarama kareleri)")
            not_ = (f"rota: yol {r.get('model_yol')} | durum {mt.get('rota_durum')} | guven {guven} | "
                    f"darbogaz {mt.get('darbogaz_m')} m | wp {r.get('wp_sayisi')}")
        else:
            _panel(tuval, okuyucu.oku(son_ucus["n"], "iha_nadir"), 0, 0, ANA_W, ANA_H,
                   "YER GERCEGI rota: arena.route_waypoints (goruntu isleme YOK)", vurgu=True)
            not_ = f"rota: yol {r.get('model_yol')} | wp {r.get('wp_sayisi')}"
        _panel(tuval, okuyucu.oku(son_ucus["n"], "ika_takip"), ANA_W, KUC_H, KUC_W, KUC_H, KAMERA_ETIKETI["ika_takip"])
        yaz(hud(tuval, "ROTA", r["t_rota_yayini"], None, {"kaynak": "ucus"}, not_), int(KART_S["rota"] * FPS))
        faz_video["ROTA"] = int(KART_S["rota"] * FPS)
        # sürüş modeli (AKTARIM → IKA_GO → SURUS)
        f_surus = [faz_belirle(s) for s in surus]
        son = None
        for i in kare_plani(f_surus):
            s, f = surus[i], f_surus[i]
            if f == "VARIS":
                continue
            son = s
            yaz(hud(_cerceve(okuyucu, s, f), f, s["t"], HIZ[f], s))
            faz_video[f] = faz_video.get(f, 0) + 1
        son = surus[-1] if son is None else surus[-1]
        # VARIS (son kare tutulur, sonuç yazılır)
        tuval = _cerceve(okuyucu, son, "VARIS")
        cv2.rectangle(tuval, (20, 400), (ANA_W - 20, 520), (20, 20, 20), -1)
        _yaz(tuval, f"VARIS: HB'ye {r['varis_mesafesi_m']} m ({'HB 2x2 m icinde' if r['hb_icinde'] else 'HB DISINDA'})",
             (36, 440), 0.75, (120, 255, 120) if r["hb_icinde"] else (80, 80, 255), 2)
        _yaz(tuval, f"surus {r['sure_sim_ika']} s (sim) | temas {r['temas_sayisi']} | "
                    f"{'BASARI' if r['basari'] else 'BASARISIZ'} (gorev_kosumu.basari_hesapla)",
             (36, 490), 0.6, (235, 235, 235))
        yaz(hud(tuval, "VARIS", son["t"], None, son), int(KART_S["varis"] * FPS))
        faz_video["VARIS"] = int(KART_S["varis"] * FPS)
        bolumler.append({"bolum": kay["secilen"], "video_bas_s": round(t_bas, 2),
                         "video_son_s": round(sayac["n"] / FPS, 2),
                         "faz_video_kare": faz_video, "hiz": HIZ, "kayit_kare_n": len(satirlar),
                         "kayit_ucus_n": len(ucus), "kayit_surus_n": len(surus)})
        kosum_bilgi.append({"secim": kay, "json": f"kosum/{kay['secilen']}.json",
                            "json_sha256": sha256_metin(KOSUM_DIR / f"{kay['secilen']}.json"),
                            "durum_sha256": sha256_metin(kdir / "kareler_video" / "durum.jsonl"),
                            "rota_kaynak": kaynak, "etiket": r["rota_kaynak_etiketi"],
                            "harita": r["harita"], "senaryo": r["senaryo"], "seed": r["seed"],
                            "basari": r["basari"], "sure_sim_ika": r["sure_sim_ika"],
                            "sure_sim_gorev": r["sure_sim_gorev"], "varis_mesafesi_m": r["varis_mesafesi_m"],
                            "temas_sayisi": r["temas_sayisi"], "model_guven": guven,
                            "kare_hz_video": r.get("kare_hz_video"), "kare_n_video": r.get("kare_n_video"),
                            "eslik_kosum_tur3": _eslik(r)})

    cikis = kart_ciz([
        ("Sinirlar (rapora aynen yazilir):", 0.75, (255, 220, 120)),
        "- IHA ucusu KINEMATIK (mocap; aerodinamik yok); sure = sim saati (MuJoCo data.time)",
        "- Hakem onayi sim'de OTOMATIK (sim_hakem, sim=true) - saha kaniti sayilmaz",
        "- IKA iz genisligi 0,39 m TAHMIN; teker armature TAHMIN; motor tork siniri yok",
        "- Modeller BASITLESTIRILMIS (sabit kanat mesh, DDR olculu IKA kutusu); dokular sentetik yerlesim",
        "- iha_haritala hesap suresi sim saatine eklenmez (ROTA karti)",
        ("Uretec: simulation/mujoco/sim_video.py | kosumlar: results/fdr_sprint_20260910/video/kosum/", 0.55,
         (200, 200, 200)),
        ("Olcum: results/fdr_sprint_20260910/H1/README_T214A.md (105 kosum)", 0.55, (200, 200, 200)),
    ], "SENTETIK | NAVITAS gorev simulasyonu - sinirlar")
    yaz(cikis, int(KART_S["cikis"] * FPS))
    bolumler.append({"bolum": "cikis_karti", "video_s": KART_S["cikis"], "hiz": None})
    yazici.release()
    donusum = h264_donustur(ana, cikti)

    cap = cv2.VideoCapture(str(cikti))
    okunan_n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    okunan_fps = float(cap.get(cv2.CAP_PROP_FPS))
    ok, ilk = cap.read()
    gen_o, yuk_o = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC)).to_bytes(4, "little").decode("ascii", "replace")
    cap.release()
    boyut = cikti.stat().st_size
    ozet = {
        "is": "T214-B · ON_KAYIT H1-K7 video", "etiket": "SENTETİK (MuJoCo simülasyonu; saha kanıtı değildir)",
        "dosya": f"results/fdr_sprint_20260910/video/{cikti.name}", "sha256": sha256_dosya(cikti),
        "boyut_bayt": boyut, "boyut_mb": round(boyut / 1e6, 2),
        "yazilan_kare_n": sayac["n"], "fps_yazilan": FPS,
        "okunan": {"kare_n": okunan_n, "fps": okunan_fps, "genislik": gen_o, "yukseklik": yuk_o,
                   "fourcc": fourcc, "ilk_kare_okundu": bool(ok)},
        "sure_s": round(okunan_n / okunan_fps, 2) if okunan_fps else None,
        "esik": {"sure_s": ESIK_SURE_S, "fps": ESIK_FPS, "boyut_mb_siniri": BOYUT_SINIRI_MB,
                 "kaynak": "ON_KAYIT H1-K7 (≥ 90 s, ≥ 24 FPS, HUD, üç kamera); boyut sınırı görev tanımı"},
        "kameralar": {k: KAMERA_ETIKETI[k] for k in KAMERALAR},
        "hud_alanlari": ["sim saati", "faz " + "/".join(FAZLAR), "rota kaynağı etiketi (YER GERCEGI / URETIM MODELI)",
                         "OPEN_ROUTE ACK [ika,yks] · IHA_LANDED · IKA_GO · IKA_GO ACK", "İKA→HB mesafesi · temas",
                         "oynatma hızı", "SENTETİK"],
        "hiz": HIZ, "kart_s": KART_S,
        "yazici": {"api": "cv2.VideoWriter", "fourcc": "mp4v", "arka_uc": "FFMPEG",
                   "ana_kopya": str(ana.relative_to(KOK)).replace("\\", "/"), "ana_kopya_sha256": sha256_dosya(ana),
                   "ana_kopya_boyut_mb": round(ana.stat().st_size / 1e6, 2)},
        "donusum": donusum,
        "genel_sayilar": g, "kosumlar": kosum_bilgi, "bolumler": bolumler,
        "degismezlik": _j(KOSUM_DIR / "degismezlik.json"),
        "ilk_kosum_kusuru": _ilk_kosum_kusuru(),
        "komutlar": ["O:/navitas-local-train/venv/Scripts/python.exe -B simulation/mujoco/sim_video.py --kos",
                     "O:/navitas-local-train/venv/Scripts/python.exe -B simulation/mujoco/sim_video.py --birlestir"],
        "link": "BEYAN GEREKLİ (insan — YouTube liste dışı / Drive; T222)",
        "tarih": time.strftime("%Y-%m-%d %H:%M"),
    }
    ozet["hukum"] = {
        "sure": bool(ozet["sure_s"] is not None and ozet["sure_s"] >= ESIK_SURE_S),
        "fps": bool(okunan_fps >= ESIK_FPS),
        "cozunurluk": (gen_o, yuk_o) == (GEN, YUK),
        "uc_kamera": len(KAMERALAR) == 3,
        "boyut": boyut / 1e6 < BOYUT_SINIRI_MB,
        "kosumlar_basarili": all(k["basari"] for k in kosum_bilgi),
    }
    (VIDEO_DIR / OZET_ADI).write_text(json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    (VIDEO_DIR / OKUBENI_ADI).write_text(okubeni_uret(ozet), encoding="utf-8")
    return ozet


# ── 4) OKUBENI (video_ozeti.json'dan) ───────────────────────────────────────

def okubeni_uret(oz: dict) -> str:
    L = []
    a = L.append
    hk = oz["hukum"]
    a("# H1-K7 · T214-B — MuJoCo görev icra simülasyonu videosu")
    a("")
    a("> **SENTETİK** — MuJoCo simülasyonu; saha kanıtı değildir. Bu dosya `simulation/mujoco/sim_video.py` ile "
      f"`{OZET_ADI}`'ndan üretilir, elle düzenlenmez (nöbetçi `tests/test_sim_mujoco_video.py`). "
      "mp4 **git dışıdır** (`.gitignore`: `*.mp4`, `results/**/*.mp4`); yerel dosya aşağıdaki sha256 ile tanınır.")
    a("")
    a("| alan | değer | eşik (ON_KAYIT H1-K7) | hüküm |")
    a("|---|---|---|---|")
    a(f"| dosya | `{oz['dosya']}` | mp4 yazıldı | {'VAR' if oz['okunan']['ilk_kare_okundu'] else 'OKUNAMADI'} |")
    a(f"| sha256 | `{oz['sha256']}` | — | — |")
    a(f"| süre | {oz['sure_s']} s ({oz['okunan']['kare_n']} kare) | ≥ {oz['esik']['sure_s']:g} s | "
      f"{'GEÇTİ' if hk['sure'] else 'DÜŞTÜ'} |")
    a(f"| kare hızı | {oz['okunan']['fps']:g} FPS | ≥ {oz['esik']['fps']:g} FPS | {'GEÇTİ' if hk['fps'] else 'DÜŞTÜ'} |")
    a(f"| çözünürlük | {oz['okunan']['genislik']}×{oz['okunan']['yukseklik']} (fourcc `{oz['okunan']['fourcc']}`) | "
      f"— | {'1280×720' if hk['cozunurluk'] else 'BEKLENMEYEN'} |")
    a(f"| boyut | {oz['boyut_mb']} MB | < {oz['esik']['boyut_mb_siniri']:g} MB (görev tanımı) | "
      f"{'GEÇTİ' if hk['boyut'] else 'DÜŞTÜ'} |")
    a(f"| kameralar | {' · '.join(oz['kameralar'].values())} | üç kamera | {'GEÇTİ' if hk['uc_kamera'] else 'DÜŞTÜ'} |")
    a(f"| HUD | {' · '.join(oz['hud_alanlari'])} | HUD'lu | VAR |")
    a(f"| link | {oz['link']} | yönerge `Y-3.3.3-M03` linki ister | **AÇIK** |")
    a("")
    a("## Koşumlar (her biri `gorev_kosumu.kos(..., kare_kaydet=True)`; üç kamera 25 Hz sim saati)")
    a("")
    a("| # | koşum | rota kaynağı | başarı | sürüş sim-s | görev sim-s | varış m | temas | kosum_tur3 eşliği | seçim |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for i, k in enumerate(oz["kosumlar"], 1):
        e = k["eslik_kosum_tur3"]
        es = ("—" if e["hepsi_es"] is None else ("11/11 alan eş" if e["hepsi_es"] else
              "FARK: " + ", ".join(f"{a_}={v['video']}↔{v['kosum_tur3']}" for a_, v in e["alanlar"].items()
                                   if not v["es"])))
        a(f"| {i} | `{k['json']}` | {k['etiket']} | {'✓' if k['basari'] else '✗'} | {k['sure_sim_ika']} | "
          f"{k['sure_sim_gorev']} | {k['varis_mesafesi_m']} | {k['temas_sayisi']} | {es} | "
          f"{k['secim']['yedek_nedeni'] or 'birincil'} |")
    a("")
    a("Eşlik alanları: " + ", ".join(f"`{x}`" for x in ESLIK_ALANLARI) + " — video koşumu aynı harita/seviye/tohumun "
      "`kosum_tur3` JSON'uyla karşılaştırılır. `rota.json` eşliği: "
      + " · ".join(f"{k['secim']['secilen']} {'eş' if k['eslik_kosum_tur3'].get('rota_json_es') else ('FARKLI' if k['eslik_kosum_tur3'].get('rota_json_es') is False else '—')}"
                   for k in oz["kosumlar"])
      + ". Model koşumunda rota GPU render'lı mozaikten gelir (kareler koşumdan koşuma ~%50 bayt-eş, T213-A "
      "ölçümü); rota farklıysa sürüş farkı rotadandır — kaydedicinin kendisi aşağıdaki değişmezlik koşumuyla sınanır.")
    a("")
    dz = oz.get("degismezlik") or {}
    a("## Kaydedici fizik değişmezliği (ölçüm)")
    a("")
    a(f"YER GERÇEĞİ koşumu `{dz.get('kosum')}` (rota render'dan bağımsız) kareli koşuldu ve `{dz.get('kosum_tur3')}` "
      f"ile {len(dz.get('alanlar', {}))} alanda karşılaştırıldı: **{'hepsi eş' if dz.get('hepsi_es') else 'FARK VAR'}** "
      f"(kare {dz.get('kare_n_video')}; `kosum/degismezlik.json`)."
      + ("" if dz.get("hepsi_es") else " Farklar: " + ", ".join(
          f"{a_}={v['video']}↔{v['kosum_tur3']}" for a_, v in dz.get("alanlar", {}).items() if not v["es"])))
    ik = oz.get("ilk_kosum_kusuru")
    if ik:
        a("")
        a(f"**Ölçülen ve düzeltilen kusur (ilk video koşumu, `{ik['klasor']}/`):** {ik['neden']}. "
          f"Alanlar {ik['alanlar']}:")
        a("")
        a("| koşum | sürüş sim-s | varış m | takip maks m | IKA_GO ACK t |")
        a("|---|---|---|---|---|")
        for s in ik["satirlar"]:
            a(f"| {s['kosum']} | {s['sure_sim_ika'][0]} ↔ {s['sure_sim_ika'][1]} | {s['varis_mesafesi_m'][0]} ↔ "
              f"{s['varis_mesafesi_m'][1]} | {s['takip_hatasi_maks_m'][0]} ↔ {s['takip_hatasi_maks_m'][1]} | "
              f"{s['t_ika_go_ack'][0]} ↔ {s['t_ika_go_ack'][1]} |")
    a("")
    g = oz["genel_sayilar"]
    k5 = g["k5"]
    a("## Videodaki genel sayılar (giriş kartı; ölçüm JSON'larından)")
    a("")
    a(f"- H1-K3 mozaik zinciri doğru etiket {g['k3_mozaik']['dogru']}/{g['k3_mozaik']['n']} · üretim kare-bazlı "
      f"{g['k3_uretim']['dogru']}/{g['k3_uretim']['n']} (eşik 12/15, ikisi de DÜŞTÜ)")
    a(f"- H1-K5 YER GERÇEĞİ {k5['gt']['basari_n']}/{k5['gt']['n']} (harita {k5['gt']['harita']}/{k5['gt']['harita_n']}) · "
      f"ÜRETİM MODELİ {k5['model']['basari_n']}/{k5['model']['n']} (harita {k5['model']['harita']}/{k5['model']['harita_n']})"
      + (f" · ÜRETİM BORU HATTI {k5['uretim']['basari_n']}/{k5['uretim']['n']}" if "uretim" in k5 else ""))
    a(f"- Kaynak: {', '.join(f'`{x}`' for x in g['kaynak'])}. Videodaki 3 koşum **başarılı** koşumlardır ve bu "
      "girişte açıkça yazılıdır; genel oranın yerine geçmez.")
    a("")
    a("## Bölümler (video saniyesi)")
    a("")
    a("| bölüm | başlangıç s | bitiş s | faz → video karesi |")
    a("|---|---|---|---|")
    for b in oz["bolumler"]:
        if "video_bas_s" in b:
            a(f"| {b['bolum']} | {b['video_bas_s']} | {b['video_son_s']} | "
              + " · ".join(f"{f} {n}" for f, n in b["faz_video_kare"].items()) + " |")
        else:
            a(f"| {b['bolum']} | — | — | kart {b['video_s']:g} s |")
    a("")
    a("Oynatma hızı (HUD'da her karede yazılı): " + " · ".join(f"{f} {s:g}×" for f, s in oz["hiz"].items())
      + " · ROTA kartı sim saatini dondurur (`iha_haritala` hesap süresi sim saatine eklenmez).")
    a("")
    a("## Üretim komutu")
    a("")
    a("```")
    for c in oz["komutlar"]:
        a(c)
    a("```")
    a("")
    y, dn = oz["yazici"], oz.get("donusum") or {}
    a(f"Ana kopya: `{y['api']}` fourcc `{y['fourcc']}` ({y['arka_uc']}) → `{y['ana_kopya']}` "
      f"({y['ana_kopya_boyut_mb']} MB, sha256 `{y['ana_kopya_sha256']}`; git dışı).")
    if dn.get("arac"):
        a(f"Teslim dosyası H.264'e dönüştürüldü ({dn['codec']}): `{dn['komut']}` — {dn['surum']}. Neden (ölçüldü): bu "
          "cv2 derlemesinde mp4v bit hızı ayarlanamıyor (`OPENCV_FFMPEG_WRITER_OPTIONS` etkisiz, 5,82 MB / 10 s), "
          "ana kopya 60 MB sınırını aşıyor. Kareler ana kopyayla aynıdır; yalnız sıkıştırma değişir.")
    else:
        a(f"Dönüşüm YOK: {dn.get('not', '—')}.")
    a(f"Özet tarihi: {oz['tarih']}.")
    a("")
    a("## Sınırlar")
    a("")
    a("- İHA uçuşu KİNEMATİK (mocap, aerodinamik yok); hakem onayı sim'de OTOMATİK (`sim=true`); İKA iz genişliği "
      "0,39 m TAHMİN; modeller BASİTLEŞTİRİLMİŞ (sabit kanat mesh, DDR ölçülü İKA). GPU render kareleri koşumdan "
      "koşuma ~%50 bayt-eş (T213-A ölçümü) — video yeniden üretildiğinde sha256 değişir, sayılar değişmez.")
    a("- Link yoktur: yükleme İNSAN işidir (T222). Link gelene kadar `Y-3.3.3-M03` KISMEN.")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="T214-B H1-K7 video (MuJoCo; SENTETİK)")
    ap.add_argument("--kos", action="store_true", help="3 koşumu kareleriyle koş (GPU, sıralı)")
    ap.add_argument("--birlestir", action="store_true", help="kareler → HUD'lu mp4 + video_ozeti.json + OKUBENI.md")
    ap.add_argument("--okubeni", action="store_true", help="yalnız OKUBENI.md'yi video_ozeti.json'dan yeniden yaz")
    a = ap.parse_args(argv)
    if not (a.kos or a.birlestir or a.okubeni):
        ap.error("--kos / --birlestir / --okubeni")
    if a.kos:
        print(json.dumps(kos_hepsi(), ensure_ascii=False, indent=1), flush=True)
    if a.birlestir:
        oz = birlestir()
        print(json.dumps({k: oz[k] for k in ("dosya", "sha256", "boyut_mb", "sure_s", "okunan", "hukum")},
                         ensure_ascii=False, indent=1))
    if a.okubeni:
        (VIDEO_DIR / OKUBENI_ADI).write_text(okubeni_uret(_j(VIDEO_DIR / OZET_ADI)), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

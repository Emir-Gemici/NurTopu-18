"""GÖREV KOŞUMU — MuJoCo'da uçtan uca zincir (T213-B · ON_KAYIT H1.4–H1.5 · K4/K5).

Zincir (tek süreç, GPU işleri sıralı — ON_KAYIT §5.6):
  MJCF (arena_mjcf, deterministik) → İHA kinematik uçuş + 1 Hz tarama (iha_ucus.tara)
  → ROTA: `model` = iha_haritala.haritala (ÜRETİM MODELİ v36, OBB kapalı, sim'e özel
           eğitim YOK) · `gt` = arena.route_waypoints (YER GERÇEĞİ; 3,3 m segmentler
           MAX_SEGMENT_M 2,10'a bölünür — D-438 c kusuru burada çözülür, comms
           sözleşmesi aşılmaz)
  → IhaSender OPEN_ROUTE / NO_ROUTE (UDP ephemeral, ACK'lı tekrar)
  → IkaReceiver (İKA ucu, ephemeral) + SimHakem (YKS ucu + İHA zaman çizelgesi,
     `sim: true`, CONTRACTS §6.7.x) → IHA_LANDED @ t_inis → CMD IKA_GO
  → ika_nav.ika_gorevi + MuJoCoSurucu, 10 Hz kontrol SİM SAATİYLE (her tik 50 fizik
     alt adımı, 2 ms) → bitiş: HB'ye ≤ FINAL_WP_RADIUS · sürüş 600 s (§6.2) doldu ·
     temas kaydedilir (koşum durdurulmaz; başarı temas=0 ister).

Sim saati: sürüş MjData'sı t=0'dan başlar, görev saati = t_tarama_son + data.time
(rota tarama biter bitmez yayınlanır; haritala hesap süresi sim'de modellenmez).
"sure_sim_iha_profil" = kinematik profil süresi (fırlatma→iniş; aerodinamik yok).

T214-A eklemeleri (D-441 mimar kararları):
  · `basari_hesapla` — K5 başarı tanımının TEK saf fonksiyonu (çürütücü M9: temas kilidi).
  · takip hatası — sürüş boyunca, İLK TEMASTAN ÖNCE, İKA konumu → arena açık yol merkez
    hattı uzaklığı (`takip_hatasi_maks_m/ort_m`) ve komut edilen rotaya uzaklık (`plan_*`).
  · `uretim` rota kaynağı — ÜRETİM KARE-BAZLI boru hattı (`sim_karar_toplayici`, rpi_inference
    run_camera + KararYayinci); İKA'ya İKA ucuna ulaşan SON OPEN_ROUTE verilir, ref = İKA
    başlangıcı (saf öteleme, CONTRACTS §3.2/§6.5). Yayın zaman çizelgesi sürüşe beslenmez.
  · `tel_tipi` — İHA'nın TEL'e çıkardığı karar tipi (hakem kaydından). `send_open_route` güven
    eşiği altında NO_ROUTE gönderir (CONTRACTS §6.3, K-B); `iha_gonderim.tip` ise ÇAĞRILAN yöntemi
    yazar (T214-A ölçümü: model_2_zor_42 conf 0,141 `tip=OPEN_ROUTE` sayılıyordu, telde NO_ROUTE).
  · varsayılan çıktı `kosum_tur3/` (T213-B `kosum/` sonuçları silinmez, üzerine yazılmaz).

Kullanım:
  venv python simulation/mujoco/gorev_kosumu.py --map 1 --level kolay --seed 42 \
      --rota-kaynak gt --res 1280
  venv python simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak gt --tohumlar 42,43,44
  venv python simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak uretim --haritalar 1_orta,4_kolay
  --kare-kaydet: sürüşte üçüncü şahıs + İKA takip kareleri (T214 videosu), varsayılan KAPALI.
"""
from __future__ import annotations

import argparse
import functools
import json
import math
import statistics
import sys
import threading
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

import arena                                              # noqa: E402
import arena_mjcf                                         # noqa: E402
import araclar                                            # noqa: E402
import iha_ucus                                           # noqa: E402
import ika_nav                                            # noqa: E402
from ika_surucu_mujoco import MuJoCoSurucu, ENGEL_ONEKLERI as ENGEL_ONEKLERI_KOSUM   # noqa: E402
from sim_hakem import SimHakem                            # noqa: E402
from iha_sender import IhaSender, rota_json_oku           # noqa: E402
from link import UDPLink                                  # noqa: E402
from karar_sozlesmesi import (IKA_BEKLEME_SURESI_S,       # noqa: E402
                              IKA_SURUS_SURESI_S,
                              SARTNAME_IKA_GOREV_SURESI_S)

KOSUM_KOK = KOK / "results" / "fdr_sprint_20260910" / "H1" / "kosum"          # T213-B (değiştirilmez)
KOSUM_TUR3_KOK = KOK / "results" / "fdr_sprint_20260910" / "H1" / "kosum_tur3"  # T214-A (CLI varsayılanı)
ROTA_KAYNAKLARI = ("gt", "model", "uretim")
ROTA_KAYNAK_ETIKETI = {"gt": "YER GERÇEĞİ", "model": "ÜRETİM MODELİ",
                       "uretim": "ÜRETİM BORU HATTI (kare-bazlı)"}
TOHUMLAR_VARSAYILAN = (42, 43, 44)
KARE_HZ_VIDEO = 25.0      # T214-B (H1-K7 ≥ 24 FPS): kayıt aralığı sim saatiyle 0,04 s (5 Hz → 25 Hz)
METRIK_ANAHTARLARI = (
    "rota_kaynak", "rota_kaynak_etiketi", "harita", "senaryo", "seed", "acik_yol",
    "rota_bulundu", "rota_dogru", "model_yol", "wp_sayisi", "sure_sim_iha_profil",
    "sure_sim_ika", "sure_sim_gorev", "varis_mesafesi_m", "hb_icinde", "temas_sayisi",
    "link_olaylari", "ack_listesi", "open_route_ack", "cikis_kodu", "basari",
    "rota_engel_aciklik_m", "rota_engel_aciklik_geom", "rota_insaat_geregi_gecilemez",
    "takip_hatasi_maks_m", "takip_hatasi_ort_m", "tel_tipi", "guven_kapisi_reddi",
    "duvar_saati_s", "sinir",
)
SINIR = ("İHA uçuşu KİNEMATİK (mocap, aerodinamik yok); hakem onayı sim'de OTOMATİK "
         "(sim=true, saha kanıtı değil); İKA iz genişliği 0,39 m TAHMİN; teker armature "
         "0,01 TAHMİN; motor tork sınırı yok (DDR'de yok); haritala hesap süresi sim'de yok; "
         "modeller basitleştirilmiş (D-438 ek).")


def rota_bol(wps, maks=ika_nav.MAX_SEGMENT_M):
    """Ardışık segmentleri `maks`'ı aşmayacak şekilde DOĞRUSAL ara noktayla böl
    (geometri EKLENMEZ, mevcut kenar bölünür — iha_sender.piksel_rotayi_yerele_cevir
    ile aynı kural). D-438 c: arena.route_waypoints 3,3 m segment üretir."""
    out = [tuple(map(float, wps[0]))]
    for a, b in zip(wps, wps[1:]):
        L = math.dist(a, b)
        n = max(1, int(math.ceil(L / maks)))
        for k in range(1, n + 1):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


IKA_YARI_GENISLIK_M = (araclar.IKA_IZ_M + araclar.IKA_TEKER_W) / 2.0   # teker dış kenarı


def rota_engel_acikligi(m, wps_dunya, engel_onekleri=ENGEL_ONEKLERI_KOSUM, adim_m: float = 0.05):
    """Rota polyline'ı ile engel geomları arasındaki en küçük XY açıklık (m) ve geom adı.

    Rota `adim_m` aralıkla örneklenir; her engel geomu için örnekler geomun yerel
    çerçevesine (geom_pos/geom_quat, statik geomlar) çevrilir: kutu → eksen hizalı
    dikdörtgene uzaklık hypot(max(|x|−sx,0), max(|y|−sy,0)); silindir/küre → |xy| − r.
    İçerideyse 0. `< IKA_YARI_GENISLIK_M` ise rota İNŞAAT GEREĞİ çarpışmasız izlenemez
    (İKA merkez hatta sıfır hatayla gitse bile). TEŞHİS metriğidir: arena yerleşimi
    (kapalı yol tıkaması açık yol hattına sokulmuş mu) ile sürücü hatasını AYIRIR
    (10 Eyl teşhisi: 1 zor 43 — tikama_2_2_2 açık yol 3 hattına 0,07 m; İKA orada takıldı).
    """
    import mujoco
    pts = [np.asarray(wps_dunya[0], float)]
    for a, b in zip(wps_dunya, wps_dunya[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        L = float(np.hypot(*(b - a)))
        n = max(1, int(math.ceil(L / adim_m)))
        for k in range(1, n + 1):
            pts.append(a + (b - a) * (k / n))
    P = np.asarray(pts, float)
    en_kucuk, geom_ad = None, None
    R9 = np.zeros(9)
    for g in range(m.ngeom):
        ad = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or ""
        if not ad.startswith(engel_onekleri):
            continue
        mujoco.mju_quat2Mat(R9, m.geom_quat[g])
        R = R9.reshape(3, 3)[:2, :2]
        yerel = (P - m.geom_pos[g][:2]) @ R          # dünya→yerel: R^T · v  (satır vektörü: v · R)
        sx, sy = float(m.geom_size[g][0]), float(m.geom_size[g][1])
        if int(m.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_BOX):
            d = np.hypot(np.maximum(np.abs(yerel[:, 0]) - sx, 0.0), np.maximum(np.abs(yerel[:, 1]) - sy, 0.0))
        else:
            d = np.maximum(np.hypot(yerel[:, 0], yerel[:, 1]) - sx, 0.0)
        dm = float(d.min())
        if en_kucuk is None or dm < en_kucuk:
            en_kucuk, geom_ad = dm, ad
    return (None if en_kucuk is None else round(en_kucuk, 3)), geom_ad


def gt_rota(h: int, lv: str):
    H = arena.harita(h, lv)
    wps = rota_bol(arena.route_waypoints(H["open"], lv, h))
    ref = wps[0]
    yerel = [[round(x - ref[0], 2), round(y - ref[1], 2)] for x, y in wps]
    return H["open"], 1.0, [round(ref[0], 2), round(ref[1], 2)], yerel


def model_rota(ldir: Path, model, conf: float):
    """iha_haritala (v36, OBB kapalı) → (road, conf, ref_xy, yerel) ya da (None, det)."""
    import iha_haritala as ih
    meta = ih._meta_oku(ldir)
    cx, cy = ih._htab_merkez(meta, None)
    det = ih.haritala(ldir, model, cx, cy, conf=conf, kb_xy=ih._meta_xy(meta, "KB_XY"),
                      hb_xy=ih._meta_xy(meta, "HB_XY"), arac_model=None)
    rj = ldir / "rota.json"
    if rj.is_file():
        try:
            road, guven, ref_xy, yerel = rota_json_oku(rj)
            return (road, guven, ref_xy, yerel), det
        except ValueError as exc:
            det["rota_sebep"] = f"rota.json sözleşme dışı: {exc}"
            det["rota_durum"] = "ROTA_GEOMETRI"
    return None, det


def model_yukle():
    from ultralytics import YOLO
    from on_olcum_k3 import model_coz
    mk = model_coz()
    return YOLO(mk["path"], task="segment"), mk


def basari_hesapla(kod, rota_bulundu, hb_icinde, temas_sayisi, sure_ika) -> bool:
    """H1-K5 BAŞARI — TEK TANIM (saf fonksiyon; D-441 çürütücü M9: `temas == 0` kilitsizdi).

    başarı ⇔ çıkış kodu 0 ∧ rota bulundu ∧ HB 2×2 m karesi içinde ∧ temas 0 ∧ sürüş süresi
    ölçüldü ve ≤ SARTNAME_IKA_GOREV_SURESI_S (600 s, sim saati). Her koşul tek başına
    düşürülünce False döner (tests/test_sim_mujoco_olcum.py, mutasyonlu)."""
    if sure_ika is None:
        return False
    return bool(int(kod) == 0 and bool(rota_bulundu) and bool(hb_icinde)
                and int(temas_sayisi) == 0 and float(sure_ika) <= SARTNAME_IKA_GOREV_SURESI_S)


def _tel_tipi_hakemden(seq, hakem: dict):
    """Hakem (YKS ucu) kaydından `seq`'in TEL tipi: OPEN_ROUTE · NO_ROUTE · None (kanıt yok)."""
    if seq is None:
        return None
    if hakem.get("rota_seq") == seq:
        return "OPEN_ROUTE"
    if (hakem.get("no_route") or {}).get("seq") == seq:
        return "NO_ROUTE"
    return None


def tel_tipi(r: dict):
    """Koşum JSON'u → İHA'nın TEL'e çıkardığı karar tipi (bkz. modül başı `tel_tipi`).
    Yeni koşumlar `iha_gonderim.tel_tipi` taşır; eskileri (T214-A ilk koşu gt/model) hakem
    alanlarından (`hakem.rota_seq`, `hakem.no_route.seq`) çözülür — ölçüm dosyası değiştirilmez."""
    g = r.get("iha_gonderim") or {}
    if g.get("tel_tipi"):
        return g["tel_tipi"]
    return _tel_tipi_hakemden(g.get("seq"), r.get("hakem") or {})


def nokta_polyline_uzakligi(x: float, y: float, hat) -> float:
    """(x, y) → polyline'a en kısa uzaklık (m); `arena.dist_to_path` ile aynı tanım, vektörel."""
    P = np.asarray(hat, float)
    if len(P) == 1:
        return float(np.hypot(x - P[0, 0], y - P[0, 1]))
    A, AB = P[:-1], P[1:] - P[:-1]
    L2 = np.einsum("ij,ij->i", AB, AB)
    L2[L2 == 0.0] = 1e-12
    t = np.clip(((x - A[:, 0]) * AB[:, 0] + (y - A[:, 1]) * AB[:, 1]) / L2, 0.0, 1.0)
    return float(np.min(np.hypot(x - (A[:, 0] + AB[:, 0] * t), y - (A[:, 1] + AB[:, 1] * t))))


class TakipOlcer:
    """Sürüş takip hatası: İKA konumu → referans hattı uzaklığı, yalnız İLK TEMASTAN ÖNCE.

    Temastan sonra konumu sürücü değil temas kuvvetleri belirler → ölçüm KESİLİR ve bir daha
    açılmaz (`temasla_kesildi`). Örnek yoksa maks/ort None (ÖLÇÜLEMEDİ ≠ 0)."""

    def __init__(self, hat):
        self.hat = np.asarray(hat, float)
        self.maks, self.toplam, self.n = 0.0, 0.0, 0
        self.temasla_kesildi = False

    def ornekle(self, x: float, y: float, temas_sayisi: int) -> None:
        if self.temasla_kesildi:
            return
        if int(temas_sayisi) > 0:
            self.temasla_kesildi = True
            return
        d = nokta_polyline_uzakligi(x, y, self.hat)
        self.maks = max(self.maks, d)
        self.toplam += d
        self.n += 1

    def ozet(self) -> dict:
        return {"maks": (round(self.maks, 3) if self.n else None),
                "ort": (round(self.toplam / self.n, 3) if self.n else None),
                "n": self.n, "temasla_kesildi": self.temasla_kesildi}


def takip_ornekle(kayit: dict, surucu, *olcerler) -> bool:
    """`bekle()` kancası — takip hatasını YALNIZ SÜRÜŞ sırasında örnekler (`t_surus_bas` kurulu,
    `t_surus_son` yok). Rota bekleme / IKA_GO öncesi ve sürüş sonrası adımlar sayılmaz.
    Döner: örnek alındı mı (test ve mutasyon için)."""
    if kayit.get("t_surus_bas") is None or kayit.get("t_surus_son") is not None:
        return False
    kx, ky = surucu.konum_al()[:2]
    for o in olcerler:
        if o is not None:
            o.ornekle(kx, ky, surucu.temas_sayisi)
    return True


def uretim_rota(ldir: Path, kdir: Path, model, h: int, lv: str, seed: int, *, besleme: str = "kerteriz",
                model_kunye=None):
    """ÜRETİM KARE-BAZLI boru hattı (`sim_karar_toplayici`) → ((road, conf, ref_xy, yerel), det)
    ya da (None, det).

    İKA ucuna ulaşan SON OPEN_ROUTE seçilir (İKA alıcısı `latest`'i tutar). ref_xy = İKA
    başlangıcı (KB): üretimde ref daima [0,0] ve İKA SAF ÖTELEME yapar (CONTRACTS §3.2/§6.5) —
    rota İKA'nın bulunduğu noktadan başlar sayılır; rotanın pozdan hesaplanan gerçek ankoru
    `ankor_kb_uzakligi_m` ile ayrıca raporlanır. Yayın zaman çizelgesi (sonraki NO_ROUTE'lar)
    sürüşe BESLENMEZ; `son_yayin` alanında durur. Toplayıcı kaydı `kdir/karar_toplayici.json`."""
    import sim_karar_toplayici as skt
    H = arena.harita(h, lv)
    sonuc = skt.topla(ldir, model, besleme=besleme, out_dir=kdir, harita=h, senaryo=lv, seed=seed,
                      model_kunye=model_kunye)
    sonuc["tarih"] = time.strftime("%Y-%m-%d %H:%M")
    (Path(kdir) / "karar_toplayici.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
    orl = [s for s in sonuc["kareler"] if s.get("karar") == "OPEN_ROUTE"]
    det = {"rota_durum": None, "rota_sebep": None, "besleme": besleme,
           "open_route_n": sonuc["open_route_n"], "open_route_yollari": sonuc["open_route_yollari"],
           "open_route_kareleri": sonuc["open_route_kareleri"], "son_yayin": sonuc["son_yayin"],
           "hukum": sonuc["hukum"], "hizali": sonuc["hizali"],
           "ankor_kb_uzakligi_m": (orl[-1].get("ankor_kb_uzakligi_m") if orl else None),
           "rota_sonu_hb_uzakligi_m": (orl[-1].get("rota_sonu_hb_uzakligi_m") if orl else None),
           "karar_toplayici": "karar_toplayici.json",
           # TEŞHİS (hüküm dışı): son OPEN_ROUTE'un DÜNYA yolu ↔ etiketi; KB–HB aynı karede mi
           "son_or_dunya_yolu": (orl[-1].get("rota_dunya_yolu") if orl else None),
           "son_or_etiket_dunya_esit": (orl[-1].get("etiket_dunya_esit") if orl else None),
           "teshis": sonuc.get("teshis")}
    son = sonuc["son_open_route"]
    if son is None:
        nr = [m for m in sonuc["ika_yayin"] if m["tip"] == "NO_ROUTE"]
        det["rota_durum"] = nr[-1]["sebep"] if nr else "KARAR_YOK"
        det["rota_sebep"] = nr[-1].get("detay") if nr else "üretim boru hattı karar yayımlamadı"
        return None, det
    det["rota_durum"] = "OPEN_ROUTE"
    kb = H["kb"]
    ref = [round(float(kb[0]), 2), round(float(kb[1]), 2)]
    yerel = [[float(x), float(y)] for x, y in son["waypoints"]]
    return (int(son["yol"]), float(son["guven"]), ref, yerel), det


class _KareKaydedici:
    """T214-B VİDEO kaydedicisi (ON_KAYIT H1-K7). Uçuşta (`iha_ucus.tara` kancası) ve sürüşte
    (`bekle`) AYNI sim-saati aralığıyla (`KARE_HZ_VIDEO`) üç kamera — `iha_nadir` (scan_camera),
    `ucuncu_sahis` (arena genel), `ika_takip` — ve her kare için bir `durum.jsonl` satırı (görev
    saati, faz girdileri, ACK durumu, İKA konumu). HUD bu satırlardan kurulur (`sim_video.py`).

    Fizik trajektorisi DEĞİŞMEZ (kanıt: `tests/test_sim_mujoco_video.py` B — poz dizisi ve qpos bit-eş;
    `results/fdr_sprint_20260910/video/kosum/degismezlik.json` — kareli GT koşumu kosum_tur3 eşiyle
    20/20 alan eş): İHA/paraşüt geom'ları çarpışmasız (contype=conaffinity=0, `araclar`);
    `mj_forward` durum değişkenlerine (qpos/qvel/qacc_warmstart) dokunmaz; sürüşte `surus_adimla`
    `surucu.adimla(dt)` ile AYNI alt adım dizisini kare anlarında böler. Sürüş modelinde İHA'nın
    paraşütle inişi aynı profilden (`iha_ucus.mocap_uygula`) çizilir (yalnız görüntü)."""

    KAMERALAR = (("iha_nadir", "scan_camera"), ("ucuncu_sahis", "ucuncu_sahis"), ("ika_takip", "ika_takip"))

    def __init__(self, kok: Path, hz: float = KARE_HZ_VIDEO, res=(960, 540), jpg_kalite: int = 85,
                 bosta_aralik_s=None):
        self.kok = Path(kok)
        self.kok.mkdir(parents=True, exist_ok=True)
        for eski in self.kok.glob("*.jpg"):
            eski.unlink()
        self.hz = float(hz)
        self.aralik = 1.0 / self.hz
        self.res = (int(res[0]), int(res[1]))
        self.jpg_kalite = int(jpg_kalite)
        self.n = 0
        self.n_ucus = 0
        self.bosta_aralik_s = bosta_aralik_s
        self.son_bosta_kare = None
        self.sonraki_surus = 0.0          # sürüş modeli d.time (görev saati − rota yayını anı)
        self.prof = iha_ucus.UcusProfili(0.0, 0.0)
        self._r = {}                      # id(model) → (model, Renderer, (iha_mocap, parasut_mocap))
        self._durum = open(self.kok / "durum.jsonl", "w", encoding="utf-8", newline="\n")

    def _cizici(self, m):
        import mujoco
        k = self._r.get(id(m))
        if k is None:
            ids = tuple(int(m.body_mocapid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, ad)])
                        for ad in ("iha", "parasut"))
            k = self._r[id(m)] = (m, mujoco.Renderer(m, height=self.res[1], width=self.res[0]), ids)
        return k

    def kare(self, m, d, t_gorev: float, durum: dict):
        import cv2
        if self.bosta_aralik_s and durum.get("no_route") and durum.get("landed"):
            if self.son_bosta_kare is not None and t_gorev - self.son_bosta_kare < self.bosta_aralik_s - 1e-8:
                return
            self.son_bosta_kare = t_gorev
        r = self._cizici(m)[1]
        for ad, kam in self.KAMERALAR:
            r.update_scene(d, camera=kam)
            cv2.imwrite(str(self.kok / f"{ad}_{self.n:05d}.jpg"),
                        cv2.cvtColor(r.render(), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, self.jpg_kalite])
        self._durum.write(json.dumps({"n": self.n, "t": round(float(t_gorev), 3), **durum},
                                     ensure_ascii=False) + "\n")
        self.n += 1

    def ucus_karesi(self, m, d, t: float, faz: str):
        """`iha_ucus.tara(kare_kancasi=...)` — uçuş modeli; tarama sonuna dek (sonrası sürüş modelinde)."""
        if t > self.prof.t_tarama_son + 1e-9:
            return
        pos = d.mocap_pos[self._cizici(m)[2][0]]
        self.kare(m, d, t, {"kaynak": "ucus", "faz_profil": faz,
                            "iha_xyz": [round(float(v), 2) for v in pos]})
        self.n_ucus += 1

    def surus_karesi(self, m, d, t_gorev: float, durum: dict):
        import mujoco
        iha, par = self._cizici(m)[2]
        iha_ucus.mocap_uygula(d, self.prof, float(t_gorev), iha, par)    # iniş görüntüsü (çarpışmasız)
        mujoco.mj_forward(m, d)
        self.kare(m, d, t_gorev, {"kaynak": "surus", **durum})

    def surus_adimla(self, surucu, m, d, dt: float, saat, durum):
        """`surucu.adimla(dt)` ile AYNI alt adım sayısı ve sırası; kare anlarında bölünür.

        Kare YALNIZ bir alt-adım öbeğinin BAŞINDA çizilir, `bekle`'nin SONUNDA asla: `mj_forward`
        türetilmiş durumu (xpos/xmat) tazeler; `bekle` sonunda çizilseydi denetleyicinin bir sonraki
        okuduğu poz 1 alt adım (2 ms) taze olur ve sürüş değişirdi. ÖLÇÜLDÜ (T214-B ilk video koşumu,
        kare bekle sonunda çiziliyordu): model_1_kolay_44 olay zamanları ve rota.json kosum_tur3 ile
        eş iken varış 0,286 ↔ 0,273 m, takip maks 1,016 ↔ 1,012 m. Kilit: tests/test_sim_mujoco_video.py B."""
        ts = float(m.opt.timestep)
        n = max(1, int(round(float(dt) / ts))) if dt > 0 else 0
        while n > 0:
            if float(d.time) + 1e-9 >= self.sonraki_surus:
                self.surus_karesi(m, d, saat(), durum())
                self.sonraki_surus += self.aralik
            k = min(n, max(1, int(math.ceil((self.sonraki_surus - float(d.time)) / ts - 1e-6))))
            surucu.adimla(k * ts)
            n -= k

    def kapat(self):
        if not self._durum.closed:
            self._durum.close()
        for _, r, _ in self._r.values():
            r.close()
        self._r.clear()


def kos(h: int, lv: str, seed: int, rota_kaynak: str, *, res: int, out: Path, model=None,
        model_kunye=None, conf: float = 0.15, kare_kaydet: bool = False, fizik_tarama: bool = True,
        bekleme_suresi: float = IKA_BEKLEME_SURESI_S, surus_suresi: float = IKA_SURUS_SURESI_S,
        verbose: bool = False, uretim_besleme: str = "kerteriz", cad_modeller: bool = False,
        video_bosta_aralik_s=None, video_kaydedici=None) -> dict:
    import mujoco
    if rota_kaynak not in ROTA_KAYNAKLARI:
        raise ValueError(f"rota_kaynak {rota_kaynak!r} — {ROTA_KAYNAKLARI}")
    if rota_kaynak in ("model", "uretim") and model is None:
        raise ValueError(f"rota_kaynak={rota_kaynak} için YOLO modeli gerekli")
    t_duvar0 = time.perf_counter()
    H = arena.harita(h, lv)
    kdir = Path(out) / f"{rota_kaynak}_{h}_{lv}_{seed}"
    ldir = kdir / "iha_scan"
    kdir.mkdir(parents=True, exist_ok=True)

    # T214-B video (H1-K7): kaydedici uçuşta `tara` kancasıyla, sürüşte `bekle` üzerinden AYNI aralıkla.
    kaydedici_sinifi = video_kaydedici or _KareKaydedici
    kaydedici = (kaydedici_sinifi(kdir / "kareler_video", bosta_aralik_s=video_bosta_aralik_s)
                 if kare_kaydet else None)

    # 1) İHA uçuş + tarama (render GPU, tek süreç)
    tarama = iha_ucus.tara(h, lv, seed, out=ldir, res=res, fizik=fizik_tarama, onizleme=False,
                           kare_kancasi=(kaydedici.ucus_karesi if kaydedici else None),
                           kanca_aralik_s=(kaydedici.aralik if kaydedici else None), cad_modeller=cad_modeller)
    t_inis, t_tarama_son = float(tarama["t_inis"]), float(tarama["t_tarama_son"])

    # 2) Rota (model: çıkarım GPU, aynı süreçte renderdan SONRA)
    det = None
    if rota_kaynak == "gt":
        rota = gt_rota(h, lv)
    elif rota_kaynak == "model":
        rota, det = model_rota(ldir, model, conf)
    else:   # uretim: kare-bazlı üretim boru hattı (kendi conf'u = üretim CLI varsayılanı)
        rota, det = uretim_rota(ldir, kdir, model, h, lv, seed, besleme=uretim_besleme,
                                model_kunye=model_kunye)
    rota_bulundu = rota is not None
    road = rota[0] if rota_bulundu else None
    wp_sayisi = len(rota[3]) if rota_bulundu else 0
    if rota_bulundu:
        segler = [math.dist(a, b) for a, b in zip(rota[3], rota[3][1:])]
        assert max(segler) <= ika_nav.MAX_SEGMENT_M + 1e-9, "segment sözleşmesi"

    # 3) Sürüş modeli + sim saati
    m = arena_mjcf.yukle(h, lv, seed, kam_res=res, cad_modeller=cad_modeller)
    d = mujoco.MjData(m)
    surucu = MuJoCoSurucu(m, d)
    t_ofset = t_tarama_son
    rota_aciklik, rota_aciklik_geom = (None, None)
    # Takip hatası (T214-A): referans = arena AÇIK YOL merkez hattı (yoğun spline, KB→HB);
    # `plan_takip` = İKA'ya komut edilen rota (sürücü hatasını planlayıcı sapmasından ayırır).
    takip = TakipOlcer(H["paths"][H["open"]])
    plan_takip = None
    if rota_bulundu:
        wps_dunya = [(rota[2][0] + x, rota[2][1] + y) for x, y in rota[3]]
        rota_aciklik, rota_aciklik_geom = rota_engel_acikligi(m, wps_dunya)
        plan_takip = TakipOlcer(wps_dunya)

    def saat():
        return t_ofset + float(d.time)

    # 4) Haberleşme uçları (ephemeral; 5005/5006/5007'ye bağlanılmaz)
    ika_link = UDPLink(bind=("127.0.0.1", 0))
    ika_addr = ("127.0.0.1", ika_link.port)
    hakem = SimHakem(ika_addr, t_inis=t_inis, saat=saat)
    iha_link = UDPLink(bind=("127.0.0.1", 0))
    sender = IhaSender(iha_link, {"ika": ika_addr, "yks": hakem.addr})
    gonderim = {}

    def iha_gonder():
        try:
            if rota_bulundu:
                seq, acked = sender.send_open_route(rota[0], rota[1], rota[3], rota[2])
                gonderim.update({"tip": "OPEN_ROUTE", "seq": seq, "acked": sorted(acked)})
            else:
                sebep = (det or {}).get("rota_durum") or "KARAR_YOK"
                detay = (det or {}).get("rota_sebep")
                seq, acked = sender.send_no_route(sebep, detay)
                gonderim.update({"tip": "NO_ROUTE", "seq": seq, "acked": sorted(acked),
                                 "sebep": sebep, "detay": detay})
        except Exception as exc:          # tanı: gönderim hatası koşumu düşürmesin
            gonderim.update({"tip": "HATA", "hata": f"{type(exc).__name__}: {exc}"})

    kayit = {"link_kayip": 0, "link_geri": 0, "t_surus_bas": None, "t_surus_son": None,
             "surus_sonucu": None}
    def durum_anlik():                            # T214-B video HUD girdisi (yalnız okuma)
        x, y, _, _ = surucu.konum_al()
        return {"acked": gonderim.get("acked"), "rota_alindi": hakem.rota is not None,
                "ika_ack": hakem.rota_ack_kaniti is not None, "yks_ack": hakem.iha_ack_gonderildi is not None,
                "no_route": hakem.no_route is not None, "landed": hakem.t_landed is not None,
                "ika_go": hakem.t_ika_go is not None, "ika_go_ack": hakem.t_ika_go_ack is not None,
                "surus": kayit["t_surus_bas"] is not None, "surus_bitti": kayit["t_surus_son"] is not None,
                "ika_xy": [round(x, 2), round(y, 2)],
                "hb_m": round(math.hypot(x - H["hb"][0], y - H["hb"][1]), 2), "temas": int(surucu.temas_sayisi)}

    def bekle(dt):
        if kaydedici is None:
            surucu.adimla(dt)
        else:
            kaydedici.surus_adimla(surucu, m, d, dt, saat, durum_anlik)
        takip_ornekle(kayit, surucu, takip, plan_takip)          # yalnız sürüşte (T214-A)
        hakem.adimla(saat())

    def rota_bekle(bind, timeout, keep_receiver=True, deadline_monotonic=None, yks_peer=None):
        alindi = ika_nav.wait_open_route_from_comms(
            bind, timeout, keep_receiver=keep_receiver, deadline_monotonic=deadline_monotonic,
            yks_peer=yks_peer, saat=saat, bekle=bekle, link=ika_link)
        if isinstance(alindi, tuple):
            rx = alindi[1]
            rx.on_link_lost = lambda: kayit.__setitem__("link_kayip", kayit["link_kayip"] + 1)
            rx.on_link_back = lambda: kayit.__setitem__("link_geri", kayit["link_geri"] + 1)
        return alindi

    def sur(route, **kw):
        kayit["t_surus_bas"] = saat()
        try:
            sonuc = ika_nav.navigate_route(route, verbose=verbose, bekle=bekle, **kw)
        finally:
            kayit["t_surus_son"] = saat()
        kayit["surus_sonucu"] = bool(sonuc)
        return sonuc

    ika_nav.surucu_ayarla(surucu)
    thr = threading.Thread(target=iha_gonder, name="sim-iha-sender", daemon=True)
    try:
        bekle(0.5)                                   # İKA yerleşsin, heartbeat başlasın
        thr.start()
        kod = ika_nav.ika_gorevi("127.0.0.1:0", bekleme_suresi, surus_suresi, saat=saat,
                                 bekle=bekle, rota_bekle=rota_bekle, sur=sur, yks_peer=hakem.addr)
    finally:
        ika_nav.surucu_ayarla(None)
        thr.join(5.0)
        hakem.adimla(saat())
        if kaydedici is not None:
            kaydedici.kapat()
        hakem.kapat()
        try:
            iha_link.close()
        except OSError:
            pass

    # 5) Ölçümler
    x, y, z, yaw = surucu.konum_al()
    hb = H["hb"]
    varis = math.hypot(x - hb[0], y - hb[1])
    hb_icinde = (abs(x - hb[0]) <= arena_mjcf.HB_KENAR_M / 2 and abs(y - hb[1]) <= arena_mjcf.HB_KENAR_M / 2)
    sure_ika = (None if kayit["t_surus_bas"] is None
                else round(kayit["t_surus_son"] - kayit["t_surus_bas"], 2))
    hz = hakem.ozet()
    if gonderim.get("seq") is not None:          # TEL tipi: güven kapısı OPEN_ROUTE'u NO_ROUTE'a çevirebilir
        gonderim["tel_tipi"] = _tel_tipi_hakemden(gonderim["seq"], hz)
    basari = basari_hesapla(kod, rota_bulundu, hb_icinde, surucu.temas_sayisi, sure_ika)
    to = takip.ozet()
    po = plan_takip.ozet() if plan_takip is not None else None
    metrik = {
        "rota_kaynak": rota_kaynak, "rota_kaynak_etiketi": ROTA_KAYNAK_ETIKETI[rota_kaynak],
        "harita": h, "senaryo": lv, "seed": seed,
        "acik_yol": H["open"], "acik_yol_etiket": arena.ROAD_LABEL[H["open"]],
        "rota_bulundu": bool(rota_bulundu), "rota_dogru": bool(rota_bulundu and road == H["open"]),
        "model_yol": road, "model_guven": (round(float(rota[1]), 4) if rota_bulundu else None),
        "wp_sayisi": wp_sayisi,
        "maks_segment_m": (round(max(segler), 3) if rota_bulundu else None),
        "rota_engel_aciklik_m": rota_aciklik, "rota_engel_aciklik_geom": rota_aciklik_geom,
        "rota_insaat_geregi_gecilemez": (None if rota_aciklik is None
                                         else bool(rota_aciklik < IKA_YARI_GENISLIK_M)),
        "ika_yari_genislik_m": round(IKA_YARI_GENISLIK_M, 3),
        "takip_hatasi_maks_m": to["maks"], "takip_hatasi_ort_m": to["ort"], "takip_ornek_n": to["n"],
        "takip_temasla_kesildi": to["temasla_kesildi"],
        "takip_referansi": "arena açık yol merkez hattı (arena.harita paths[open]); ilk temastan önce",
        "plan_takip_hatasi_maks_m": (po["maks"] if po else None),
        "plan_takip_hatasi_ort_m": (po["ort"] if po else None),
        "sure_sim_iha_profil": round(t_inis, 2),
        "sure_sim_ika": sure_ika,
        "sure_sim_gorev": round(saat(), 2),
        "t_rota_yayini": round(t_ofset, 2), "t_inis": round(t_inis, 2),
        "t_ika_go": hz["t_ika_go"], "t_ika_go_ack": hz["t_ika_go_ack"],
        "varis_mesafesi_m": round(varis, 3), "hb_icinde": bool(hb_icinde),
        "son_konum": [round(x, 3), round(y, 3), round(z, 3)], "hb_xy": [round(hb[0], 3), round(hb[1], 3)],
        "temas_sayisi": int(surucu.temas_sayisi), "temas_adim": int(surucu.temas_adim),
        "temas_geomlari": sorted(surucu.temas_geomlari), "ilk_temas_t": surucu.ozet()["ilk_temas_t"],
        "kararsiz_adim": int(surucu.kararsiz_adim),
        "link_olaylari": {"kayip": kayit["link_kayip"], "geri": kayit["link_geri"]},
        "ack_listesi": hz["ack_listesi"],
        "open_route_ack": gonderim.get("acked"), "iha_gonderim": gonderim,
        "hakem": {k: hz[k] for k in ("rota_seq", "rota_ack_kaniti", "iha_ack_gonderildi", "no_route",
                                      "t_landed", "landed_durum", "ika_go_durum", "ika_go_deneme",
                                      "heartbeat_sayisi")},
        "hakem_olaylari": hz["olaylar"],
        "cikis_kodu": int(kod), "navigate_sonucu": kayit["surus_sonucu"],
        "basari": basari,
        "tel_tipi": gonderim.get("tel_tipi"),
        "guven_kapisi_reddi": bool(rota_bulundu and gonderim.get("tel_tipi") == "NO_ROUTE"),
        "tarama": {"kare_n": tarama["kare_n"], "kabul": tarama["kabul_edilen_kare"],
                   "htab_kapsama_orani": tarama["htab_kapsama_orani"], "res": res, "fizik": fizik_tarama},
        "model_teshis": (None if (det is None or rota_kaynak != "model") else {k: det.get(k) for k in (
            "rota_durum", "rota_sebep", "label", "conf", "wp_n", "darbogaz_m", "kare_n", "imgsz",
            "mozaik_px", "hb_yaricap_m", "birlestirme")}),
        "uretim_teshis": (det if rota_kaynak == "uretim" else None),
        "model": model_kunye,
        "isaretler_carpismasiz": surucu.isaretler_degisti,
        "kare_kaydet": bool(kare_kaydet), "kare_n_video": (kaydedici.n if kaydedici else 0),
        "kare_n_video_ucus": (kaydedici.n_ucus if kaydedici else 0),
        "kare_hz_video": (kaydedici.hz if kaydedici else None),
        "video_bosta_aralik_s": video_bosta_aralik_s,
        "duvar_saati_s": round(time.perf_counter() - t_duvar0, 2),
        "tarih": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sinir": (SINIR if not cad_modeller else
                  "CAD URDF/STL görselleri; İHA kinematik, İKA mevcut basitleştirilmiş çarpışma/atalet modeli. "
                  "CAD kütle/ataleti ve fiziksel araç kabulü değildir. Hakem simülasyonda otomatik."),
        "cad_modeller": bool(cad_modeller),
    }
    (Path(out) / f"{rota_kaynak}_{h}_{lv}_{seed}.json").write_text(
        json.dumps(metrik, ensure_ascii=False, indent=1), encoding="utf-8")
    return metrik


def ozet_hesapla(out: Path) -> dict:
    """kosum/*.json → etiket başına başarı oranı + süre dağılımı. YAZMAZ (nöbetçi: diskteki
    `ozet_kosum.json` ↔ yeniden hesap, `tarih` hariç — elle düzenlenmiş/bayat özet yakalanır)."""
    satirlar = []
    for p in sorted(Path(out).glob("*_*_*_*.json")):
        if p.name == "ozet_kosum.json":
            continue
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if r.get("rota_kaynak") in ROTA_KAYNAKLARI:
            satirlar.append(r)
    ozet = {"tarih": time.strftime("%Y-%m-%d %H:%M"), "kosum_n": len(satirlar),
            "esik": "H1-K5 ≥ 12/15 harita × 3 tohum (ön kayıt; gevşetilmez)", "kaynaklar": {}}

    def dagilim(v, nd=1):
        v = [float(x) for x in v if x is not None]
        if not v:
            return None
        return {"n": len(v), "min": round(min(v), nd), "medyan": round(statistics.median(v), nd),
                "ort": round(statistics.fmean(v), nd), "maks": round(max(v), nd)}

    for kaynak in ROTA_KAYNAKLARI:
        rs = [r for r in satirlar if r["rota_kaynak"] == kaynak]
        if not rs:
            continue
        basarili = [r for r in rs if r["basari"]]
        senaryo = {}
        for lv in arena.SCENARIOS:
            s = [r for r in rs if r["senaryo"] == lv]
            if s:
                senaryo[lv] = {"n": len(s), "basari_n": sum(r["basari"] for r in s),
                               "hb_icinde_n": sum(r["hb_icinde"] for r in s),
                               "temas_var_n": sum(r["temas_sayisi"] > 0 for r in s)}
        harita_basari = {}
        for r in rs:
            harita_basari.setdefault(f"{r['harita']}_{r['senaryo']}", []).append(bool(r["basari"]))
        ozet["kaynaklar"][kaynak] = {
            "etiket": ROTA_KAYNAK_ETIKETI[kaynak], "n": len(rs),
            "rota_bulundu_n": sum(r["rota_bulundu"] for r in rs),
            "rota_dogru_n": sum(r["rota_dogru"] for r in rs),
            # H1-K4 anlamı (T214-B, çürütücü RED-2): yalnız TEL'de OPEN_ROUTE olan ve [ika,yks] ACK'ı
            # alan koşum (= olaylar.open_route_ack_ika_yks). Eski tanım tel tipinden bağımsız her karar
            # mesajını sayıyordu (model 45 / uretim 15 ↔ OPEN_ROUTE 9 / 12) → `karar_ack_ika_yks_n`.
            "open_route_ack_ika_yks_n": sum(tel_tipi(r) == "OPEN_ROUTE"
                                            and (r.get("open_route_ack") or []) == ["ika", "yks"] for r in rs),
            "karar_ack_ika_yks_n": sum((r.get("open_route_ack") or []) == ["ika", "yks"] for r in rs),
            "ika_go_ack_n": sum(r.get("t_ika_go_ack") is not None for r in rs),
            "hb_icinde_n": sum(r["hb_icinde"] for r in rs),
            "temas_var_n": sum(r["temas_sayisi"] > 0 for r in rs),
            "rota_insaat_geregi_gecilemez_n": sum(bool(r.get("rota_insaat_geregi_gecilemez")) for r in rs),
            "temas_var_ve_gecilemez_n": sum(r["temas_sayisi"] > 0 and bool(r.get("rota_insaat_geregi_gecilemez"))
                                            for r in rs),
            "temas_var_ve_gecilebilir_n": sum(r["temas_sayisi"] > 0 and not r.get("rota_insaat_geregi_gecilemez")
                                              for r in rs),
            "sure_asimi_n": sum(r["cikis_kodu"] == 4 for r in rs),
            "basari_n": len(basarili), "basari_orani": round(len(basarili) / len(rs), 3),
            "harita_hepsi_basarili_n": sum(all(v) for v in harita_basari.values()),
            "harita_n": len(harita_basari),
            "sure_sim_ika_basarili": dagilim([r["sure_sim_ika"] for r in basarili]),
            "sure_sim_ika_hepsi": dagilim([r["sure_sim_ika"] for r in rs]),
            "varis_mesafesi_m": dagilim([r["varis_mesafesi_m"] for r in rs]),
            "duvar_saati_s_toplam": round(sum(r["duvar_saati_s"] for r in rs), 1),
            "senaryo": senaryo,
            "cikis_kodlari": {str(k): sum(r["cikis_kodu"] == k for r in rs) for k in range(5)},
            # T214-A (takip hatası, toplam görev süresi, olay sayıları, harita düzeyi)
            "takip_hatasi_maks_m": dagilim([r.get("takip_hatasi_maks_m") for r in rs], 3),
            "takip_hatasi_maks_m_basarili": dagilim([r.get("takip_hatasi_maks_m") for r in basarili], 3),
            "takip_hatasi_ort_m": dagilim([r.get("takip_hatasi_ort_m") for r in rs], 3),
            "plan_takip_hatasi_maks_m": dagilim([r.get("plan_takip_hatasi_maks_m") for r in rs], 3),
            "sure_sim_gorev_basarili": dagilim([r.get("sure_sim_gorev") for r in basarili]),
            # Olay sayıları TEL tipinden (`tel_tipi`; güven kapısı dönüşümü doğru sayılır).
            "olaylar": {
                "open_route_yayini": sum(tel_tipi(r) == "OPEN_ROUTE" for r in rs),
                "open_route_ack_ika_yks": sum(tel_tipi(r) == "OPEN_ROUTE"
                                              and (r.get("open_route_ack") or []) == ["ika", "yks"] for r in rs),
                "no_route_yayini": sum(tel_tipi(r) == "NO_ROUTE" for r in rs),
                "no_route_ack_ika_yks": sum(tel_tipi(r) == "NO_ROUTE"
                                            and (r.get("open_route_ack") or []) == ["ika", "yks"] for r in rs),
                "guven_kapisi_reddi": sum(bool(r.get("rota_bulundu")) and tel_tipi(r) == "NO_ROUTE" for r in rs),
                "ika_go_ack": sum(r.get("t_ika_go_ack") is not None for r in rs),
                "temas_var": sum(r["temas_sayisi"] > 0 for r in rs),
                "sure_asimi_kod4": sum(r["cikis_kodu"] == 4 for r in rs),
                "hb_icinde": sum(bool(r["hb_icinde"]) for r in rs),
                "link_kayip_var": sum((r.get("link_olaylari") or {}).get("kayip", 0) > 0 for r in rs),
            },
            "harita_duzeyi": {k: {"basari_n": sum(v), "n": len(v)} for k, v in sorted(harita_basari.items())},
        }
    return ozet


def ozet_kur(out: Path) -> dict:
    """`ozet_hesapla` + `ozet_kosum.json` yazımı (T213-B imzası korunur)."""
    ozet = ozet_hesapla(out)
    (Path(out) / "ozet_kosum.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    return ozet


def main(argv=None):
    ap = argparse.ArgumentParser(description="NAVITAS MuJoCo görev koşumu (OPEN_ROUTE → hakem → İKA sürüşü)")
    ap.add_argument("--map", type=int, default=1, choices=range(1, arena.HARITA_N + 1))
    ap.add_argument("--level", default="kolay", choices=arena.SCENARIOS)
    ap.add_argument("--seed", type=int, default=arena_mjcf.SEED_VARSAYILAN)
    ap.add_argument("--rota-kaynak", default="gt", choices=ROTA_KAYNAKLARI)
    ap.add_argument("--res", type=int, default=arena_mjcf.KAM_RES_VARSAYILAN)
    ap.add_argument("--out", default=str(KOSUM_TUR3_KOK))
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--kare-kaydet", action="store_true", help="T214 videosu için kareler (varsayılan kapalı)")
    ap.add_argument("--hizli", action="store_true", help="taramada fizik adımı yok (yalnız kinematik + render)")
    ap.add_argument("--hepsi", action="store_true", help="15 harita × --tohumlar")
    ap.add_argument("--tohumlar", default=",".join(str(s) for s in TOHUMLAR_VARSAYILAN))
    ap.add_argument("--haritalar", default=None,
                    help="--hepsi ile yalnız bu haritalar: '1_orta,4_kolay' (uretim kaynağı için K3 seçimi)")
    ap.add_argument("--uretim-besleme", default="kerteriz", choices=("kerteriz", "ham"))
    ap.add_argument("--bekleme-suresi", type=float, default=IKA_BEKLEME_SURESI_S)
    ap.add_argument("--surus-suresi", type=float, default=IKA_SURUS_SURESI_S)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    model = kunye = None
    if a.rota_kaynak == "model":
        model, kunye = model_yukle()
        print(f"[kosum] model {kunye['model_id']} sha eşleşti={kunye['eslesti']}")
    elif a.rota_kaynak == "uretim":
        import sim_karar_toplayici as skt
        model, kunye = skt.model_yukle_uretim()     # rpi_inference.load_model (kayıt FAIL-CLOSED)
        print(f"[kosum] üretim yükleyicisi {kunye['model_id']} sha eşleşti={kunye['eslesti']} "
              f"kayıt={kunye['kayit_dogrulamasi']}")
    ortak = dict(res=a.res, out=out, model=model, model_kunye=kunye, conf=a.conf,
                 kare_kaydet=a.kare_kaydet, fizik_tarama=not a.hizli,
                 bekleme_suresi=a.bekleme_suresi, surus_suresi=a.surus_suresi, verbose=a.verbose,
                 uretim_besleme=a.uretim_besleme)
    if a.hepsi:
        tohumlar = [int(s) for s in a.tohumlar.split(",")]
        secili = None if not a.haritalar else {s.strip() for s in a.haritalar.split(",") if s.strip()}
        t0 = time.perf_counter()
        for h in range(1, arena.HARITA_N + 1):
            for lv in arena.SCENARIOS:
                if secili is not None and f"{h}_{lv}" not in secili:
                    continue
                for seed in tohumlar:
                    r = kos(h, lv, seed, a.rota_kaynak, **ortak)
                    print(f"[kosum] {a.rota_kaynak} {h} {lv} {seed}: rota={r['rota_bulundu']} "
                          f"dogru={r['rota_dogru']} kod={r['cikis_kodu']} hb={r['hb_icinde']} "
                          f"varis={r['varis_mesafesi_m']:.2f} m temas={r['temas_sayisi']} "
                          f"sure={r['sure_sim_ika']} s basari={r['basari']} "
                          f"aciklik={r['rota_engel_aciklik_m']} ({r['rota_engel_aciklik_geom']}) "
                          f"duvar={r['duvar_saati_s']} s")
        oz = ozet_kur(out)
        print(json.dumps(oz["kaynaklar"].get(a.rota_kaynak), ensure_ascii=False, indent=1))
        print(f"[kosum] toplam duvar saati {time.perf_counter() - t0:.1f} s → {out / 'ozet_kosum.json'}")
        return
    r = kos(a.map, a.level, a.seed, a.rota_kaynak, **ortak)
    print(json.dumps({k: r[k] for k in METRIK_ANAHTARLARI if k in r}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

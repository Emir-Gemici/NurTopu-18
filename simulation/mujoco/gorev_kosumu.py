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

Kullanım:
  venv python simulation/mujoco/gorev_kosumu.py --map 1 --level kolay --seed 42 \
      --rota-kaynak gt --res 1280 --out results/fdr_sprint_20260910/H1/kosum
  venv python simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak gt --tohumlar 42,43,44
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

KOSUM_KOK = KOK / "results" / "fdr_sprint_20260910" / "H1" / "kosum"
ROTA_KAYNAKLARI = ("gt", "model")
ROTA_KAYNAK_ETIKETI = {"gt": "YER GERÇEĞİ", "model": "ÜRETİM MODELİ"}
TOHUMLAR_VARSAYILAN = (42, 43, 44)
KARE_HZ_VIDEO = 5.0
METRIK_ANAHTARLARI = (
    "rota_kaynak", "rota_kaynak_etiketi", "harita", "senaryo", "seed", "acik_yol",
    "rota_bulundu", "rota_dogru", "model_yol", "wp_sayisi", "sure_sim_iha_profil",
    "sure_sim_ika", "sure_sim_gorev", "varis_mesafesi_m", "hb_icinde", "temas_sayisi",
    "link_olaylari", "ack_listesi", "open_route_ack", "cikis_kodu", "basari",
    "rota_engel_aciklik_m", "rota_engel_aciklik_geom", "rota_insaat_geregi_gecilemez",
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


class _KareKaydedici:
    """Sürüş sırasında üçüncü şahıs + İKA takip kareleri (T214 videosu için)."""

    def __init__(self, m, d, kok: Path, hz: float = KARE_HZ_VIDEO, res=(1280, 720)):
        import mujoco
        self.d = d
        self.kok = kok
        self.kok.mkdir(parents=True, exist_ok=True)
        self.r = mujoco.Renderer(m, height=res[1], width=res[0])
        self.aralik = 1.0 / hz
        self.sonraki = 0.0
        self.n = 0

    def tik(self):
        import cv2
        if self.d.time + 1e-9 < self.sonraki:
            return
        for kam in ("ucuncu_sahis", "ika_takip"):
            self.r.update_scene(self.d, camera=kam)
            cv2.imwrite(str(self.kok / f"{kam}_{self.n:05d}.jpg"),
                        cv2.cvtColor(self.r.render(), cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 88])
        self.n += 1
        self.sonraki += self.aralik

    def kapat(self):
        self.r.close()


def kos(h: int, lv: str, seed: int, rota_kaynak: str, *, res: int, out: Path, model=None,
        model_kunye=None, conf: float = 0.15, kare_kaydet: bool = False, fizik_tarama: bool = True,
        bekleme_suresi: float = IKA_BEKLEME_SURESI_S, surus_suresi: float = IKA_SURUS_SURESI_S,
        verbose: bool = False) -> dict:
    import mujoco
    if rota_kaynak not in ROTA_KAYNAKLARI:
        raise ValueError(f"rota_kaynak {rota_kaynak!r} — {ROTA_KAYNAKLARI}")
    if rota_kaynak == "model" and model is None:
        raise ValueError("rota_kaynak=model için YOLO modeli gerekli")
    t_duvar0 = time.perf_counter()
    H = arena.harita(h, lv)
    kdir = Path(out) / f"{rota_kaynak}_{h}_{lv}_{seed}"
    ldir = kdir / "iha_scan"
    kdir.mkdir(parents=True, exist_ok=True)

    # 1) İHA uçuş + tarama (render GPU, tek süreç)
    tarama = iha_ucus.tara(h, lv, seed, out=ldir, res=res, fizik=fizik_tarama, onizleme=False)
    t_inis, t_tarama_son = float(tarama["t_inis"]), float(tarama["t_tarama_son"])

    # 2) Rota (model: çıkarım GPU, aynı süreçte renderdan SONRA)
    det = None
    if rota_kaynak == "gt":
        rota = gt_rota(h, lv)
    else:
        rota, det = model_rota(ldir, model, conf)
    rota_bulundu = rota is not None
    road = rota[0] if rota_bulundu else None
    wp_sayisi = len(rota[3]) if rota_bulundu else 0
    if rota_bulundu:
        segler = [math.dist(a, b) for a, b in zip(rota[3], rota[3][1:])]
        assert max(segler) <= ika_nav.MAX_SEGMENT_M + 1e-9, "segment sözleşmesi"

    # 3) Sürüş modeli + sim saati
    m = arena_mjcf.yukle(h, lv, seed, kam_res=res)
    d = mujoco.MjData(m)
    surucu = MuJoCoSurucu(m, d)
    t_ofset = t_tarama_son
    rota_aciklik, rota_aciklik_geom = (None, None)
    if rota_bulundu:
        wps_dunya = [(rota[2][0] + x, rota[2][1] + y) for x, y in rota[3]]
        rota_aciklik, rota_aciklik_geom = rota_engel_acikligi(m, wps_dunya)

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
    kaydedici = _KareKaydedici(m, d, kdir / "kareler_video") if kare_kaydet else None

    def bekle(dt):
        surucu.adimla(dt)
        hakem.adimla(saat())
        if kaydedici is not None:
            kaydedici.tik()

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
    basari = bool(kod == 0 and rota_bulundu and hb_icinde and surucu.temas_sayisi == 0
                  and sure_ika is not None and sure_ika <= SARTNAME_IKA_GOREV_SURESI_S)
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
        "tarama": {"kare_n": tarama["kare_n"], "kabul": tarama["kabul_edilen_kare"],
                   "htab_kapsama_orani": tarama["htab_kapsama_orani"], "res": res, "fizik": fizik_tarama},
        "model_teshis": (None if det is None else {k: det.get(k) for k in (
            "rota_durum", "rota_sebep", "label", "conf", "wp_n", "darbogaz_m", "kare_n")}),
        "model": model_kunye,
        "isaretler_carpismasiz": surucu.isaretler_degisti,
        "kare_kaydet": bool(kare_kaydet), "kare_n_video": (kaydedici.n if kaydedici else 0),
        "duvar_saati_s": round(time.perf_counter() - t_duvar0, 2),
        "tarih": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sinir": SINIR,
    }
    (Path(out) / f"{rota_kaynak}_{h}_{lv}_{seed}.json").write_text(
        json.dumps(metrik, ensure_ascii=False, indent=1), encoding="utf-8")
    return metrik


def ozet_kur(out: Path) -> dict:
    """kosum/*.json → etiket başına başarı oranı + süre dağılımı (ozet_kosum.json)."""
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

    def dagilim(v):
        v = [float(x) for x in v if x is not None]
        if not v:
            return None
        return {"n": len(v), "min": round(min(v), 1), "medyan": round(statistics.median(v), 1),
                "ort": round(statistics.fmean(v), 1), "maks": round(max(v), 1)}

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
            "open_route_ack_ika_yks_n": sum((r.get("open_route_ack") or []) == ["ika", "yks"] for r in rs),
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
        }
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
    ap.add_argument("--out", default=str(KOSUM_KOK))
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--kare-kaydet", action="store_true", help="T214 videosu için kareler (varsayılan kapalı)")
    ap.add_argument("--hizli", action="store_true", help="taramada fizik adımı yok (yalnız kinematik + render)")
    ap.add_argument("--hepsi", action="store_true", help="15 harita × --tohumlar")
    ap.add_argument("--tohumlar", default=",".join(str(s) for s in TOHUMLAR_VARSAYILAN))
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
    ortak = dict(res=a.res, out=out, model=model, model_kunye=kunye, conf=a.conf,
                 kare_kaydet=a.kare_kaydet, fizik_tarama=not a.hizli,
                 bekleme_suresi=a.bekleme_suresi, surus_suresi=a.surus_suresi, verbose=a.verbose)
    if a.hepsi:
        tohumlar = [int(s) for s in a.tohumlar.split(",")]
        t0 = time.perf_counter()
        for h in range(1, arena.HARITA_N + 1):
            for lv in arena.SCENARIOS:
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

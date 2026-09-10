"""SİM KARAR TOPLAYICI — ÜRETİM KARE-BAZLI boru hattının render tarama karelerine DOSYA
KAYNAĞIYLA uygulanması ve yayımlanan kararların toplanması (T214-A · ON_KAYIT H1-K3 ·
REVIEW_LOG D-441 mimar kararı c).

Zincir — üretim kodu DEĞİŞTİRİLMEDEN, üretim fonksiyonları doğrudan çağrılır:

  tarama kareleri (`iha_scan/kareler/scan_%05d.jpg` + `poses.csv`)
    → cv2 görüntü dizisi = `rpi_inference --camera --kaynak <dosya>` kipi
      (`kamera_kaynagi_coz` → dosya; Jetson'da aynı yere `kamera_koprusu` MJPEG URL'si gelir)
    → `rpi_inference.run_camera(..., ekransiz=True)` — kare döngüsü BİREBİR üretimdir:
        _preprocess (letterbox) → v36 predict(imgsz = kayıt defteri INFER_SIZE)
        → get_masks (+ Katman 2 ince bariyer) → kare_olcek_kahini (Katman 1 telemetri:
          `CanliOlcekSaglayici` + `SimIrtifaOkuyucu` ← poses.csv z; FOV = sim scan_camera hfov)
        → analyze_path (Katman A: zemin kapısı, morfoloji, engel çıkarma, K-A uç bantları,
          C-uzayı R_GEREKLI; HB tespiti `hb_konumu` ölçek+şekil; Katman B: bağlı koridor A*
          + yol düzeltme; şerit rota gövdesinden) → _rota_kararini_esikle (K-B)
        → KararYumusatici (D-396) → KararYayinci (latest-wins, ACK'lı; `yayinci_kur` kalıbı)
    → UDP 127.0.0.1 ephemeral → `IkaReceiver` (İKA ucu, GERÇEK alıcı) + YKS dinleyicisi (ACK)

İki besleme (ön kayıt, sonuç görülmeden yazıldı — README_T214A §0):
  kerteriz (BİRİNCİL, K3 kapısı): her kare poz yaw'ından çeyrek tura yuvarlanarak (np.rot90,
      kayıpsız) KB→HB-yukarı (kuzey-yukarı) kadraja döndürülür. NEDEN: üretim `analyze_path`
      rotayı ALT→ÜST (KB→HB) arar ve şeridi içerik genişliğinin üçte birlerinden okur;
      `run_camera` eksen parametresi (`rota_ekseni_derece`, S2) GEÇİRMEZ. Sim kamerasında
      görüntü yukarısı gövde +Y'dir (sol kanat; MuJoCo kamera çerçevesi, `navitas_scan_cam.cc`
      sözleşmesi) → kuzey/güney bacaklarında yollar karede YATAY akar. Döndürme SİM TARAFINDADIR;
      üretim koduna eklenmedi. Artık açı |yaw − k·90°| kare kaydına yazılır.
  ham (TEŞHİS): kareler render edildiği gibi (sim kamera montajı) — üretimin kadraj varsayımı
      dışında kalan yönelimin etkisini gösterir; kapı değildir.

Senkron yayın: `KararYayinci` latest-wins tek yuvadır; sim kareleri Jetson'dan (~1,35 FPS,
D-431) hızlı işlendiği için karar kaybı olmasın diye her `karar()` çağrısından sonra gönderim
tamamlanana dek beklenir (kare döngüsü bloklanır). Karar içeriği değişmez.

Hüküm (ön kayıt): harita başına `dogru` = İKA ucuna ≥ 1 OPEN_ROUTE ulaştı ∧ ulaşan HER
OPEN_ROUTE'un yolu açık yol (yanlış yol yayını 0). Ayrıca ilk/son OPEN_ROUTE ve son yayın
raporlanır (İKA alıcısı son kararı tutar; iniş karelerinin NO_ROUTE'u sürüşü durdurur).

TEŞHİS alanları (hüküm DIŞI; T214-A devam, 10 Eyl öğleden sonra — ilk koşu sonuçları GÖRÜLDÜKTEN
SONRA eklendi, bu yüzden kapı değildir, yalnız ayrım yapar):
  · `rota_dunya_yolu` — OPEN_ROUTE rotasının DÜNYADA izlediği arena yolu (merkez hatlarına ortalama
    uzaklık). Yayınlanan `road` ise karenin genişliğinin üçte birlerinden okunur
    (`karar_sozlesmesi.rota_serit_karari`, KARE-GÖRELİ); kare HTAB'a ortalanmadıkça ikisi ayrışır.
  · `kb_karede` / `hb_karede` — KB ve HB bu karenin görüş alanında mı (üretim rotası kare-içi
    alt banttan başlar; İKA saf öteleme yaptığı için KB karede değilse rota KB'ye ankorlanamaz).
  · `kare_ika_or_tutarli` — kare kaydındaki OPEN_ROUTE sayısı ↔ İKA ucuna ulaşan OPEN_ROUTE sayısı.

Kullanım:
  venv python simulation/mujoco/sim_karar_toplayici.py --hepsi --seed 42 --res 1280
  venv python simulation/mujoco/sim_karar_toplayici.py --map 1 --level kolay --besleme ham
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import io
import json
import math
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

CIKTI_KOK = KOK / "results" / "fdr_sprint_20260910" / "H1" / "k3_uretim_boru"
BESLEMELER = ("kerteriz", "ham")
BESLEME_VARSAYILAN = "kerteriz"
HFOV_DERECE = math.degrees(arena_mjcf.HFOV_RAD)      # sim scan_camera yatay FOV (kare kare)
SENKRON_ZAMAN_ASIMI_S = 10.0
OZET_ADI = "ozet_k3_uretim.json"
ESIK = "H1-K3 açık yol etiketi doğru ≥ 12/15 (ön kayıt; gevşetilmez)"
HUKUM_TANIMI = ("dogru = İKA ucuna ≥ 1 OPEN_ROUTE ulaştı ∧ ulaşan her OPEN_ROUTE'un yolu açık yol "
                "(yanlış yol yayını 0)")
SINIR = ("SENTETİK: MuJoCo render; İHA uçuşu KİNEMATİK; irtifa poses.csv z (gürültüsüz, MAVLink "
         "relative_alt yerine); FOV sim kamerası (74,5°; gerçek IMX477+6 mm ~55°, ÖLÇÜLMEDİ); "
         "kamera köprüsü (MJPEG) atlandı, kare döngüsü üretimdir; yayın senkron beklenir "
         "(latest-wins kaybı yok); kerteriz beslemesinde döndürme sim tarafındadır.")


# ── Tarama girdisi ───────────────────────────────────────────────────────────

def poz_listesi(tarama_dir: Path) -> list[tuple]:
    """poses.csv (n,t,x,y,z,yaw) → [(n, t, x, y, z, yaw)] kare sırasıyla; n ardışık olmalı."""
    satirlar = []
    for satir in (Path(tarama_dir) / "poses.csv").read_text(encoding="utf-8").splitlines():
        p = satir.strip().split(",")
        if len(p) != 6:
            continue
        satirlar.append((int(float(p[0])), *(float(v) for v in p[1:])))
    satirlar.sort(key=lambda r: r[0])
    if [r[0] for r in satirlar] != list(range(len(satirlar))):
        raise ValueError("poses.csv kare numaraları 0..N-1 ardışık değil (görüntü dizisi boşlukta durur)")
    return satirlar


def ceyrek_tur(yaw_rad: float) -> int:
    """Kareyi KB→HB-yukarı (kuzey-yukarı) yapan CCW çeyrek tur sayısı (0..3).

    Sim kamerası: görüntü sağı = burun (yaw), yukarısı = sol kanat (yaw+90°). İçerik CCW θ
    döndürülünce ekran-yukarısı dünya (yaw + 90° − θ) olur → kuzey için θ = yaw
    (`iha_haritala.mozaik_kur` ile aynı kural: `getRotationMatrix2D(..., degrees(yaw))`)."""
    return int(round(math.degrees(yaw_rad) / 90.0)) % 4


def piksel_dunya(px: float, py: float, poz: tuple, genislik: int, yukseklik: int, mpp: float,
                 teta_rad: float) -> tuple[float, float]:
    """Beslenen karenin pikseli → dünya (x, y). `teta_rad` = beslemede uygulanan CCW döndürme.
    Ekran açısı φ ↔ dünya yaw + φ − θ (bkz. `ceyrek_tur`); nadir, yatışsız varsayım."""
    _n, _t, x, y, _z, yaw = poz
    du, dv = float(px) - genislik / 2.0, yukseklik / 2.0 - float(py)
    a = yaw - teta_rad
    return (x + mpp * (du * math.cos(a) - dv * math.sin(a)),
            y + mpp * (du * math.sin(a) + dv * math.cos(a)))


def dunya_piksel(wx: float, wy: float, poz: tuple, genislik: int, yukseklik: int, mpp: float,
                 teta_rad: float) -> tuple[float, float]:
    """`piksel_dunya`nın TERSİ: dünya (x, y) → beslenen karenin pikseli (px, py)."""
    _n, _t, x, y, _z, yaw = poz
    a = yaw - teta_rad
    dx, dy = (float(wx) - x) / mpp, (float(wy) - y) / mpp
    du = dx * math.cos(a) + dy * math.sin(a)
    dv = -dx * math.sin(a) + dy * math.cos(a)
    return genislik / 2.0 + du, yukseklik / 2.0 - dv


def karede_mi(wx: float, wy: float, poz: tuple, genislik: int, yukseklik: int, mpp: float,
              teta_rad: float) -> bool:
    """TEŞHİS: dünya noktası karenin görüş alanında mı (nadir, yatışsız varsayım)."""
    px, py = dunya_piksel(wx, wy, poz, genislik, yukseklik, mpp, teta_rad)
    return bool(0.0 <= px < genislik and 0.0 <= py < yukseklik)


def dunya_yolu(wps_dunya, H) -> dict:
    """TEŞHİS: rotanın DÜNYADA izlediği arena yolu — üç yolun merkez hattına (`arena.dist_to_path`)
    ortalama uzaklık, en küçüğü. Hükmü DEĞİŞTİRMEZ (hüküm yayınlanan etiketle kurulur)."""
    if not wps_dunya:
        return {"yol": None, "ort_uzaklik_m": None, "ayrim_m": None}
    ort = {r: sum(arena.dist_to_path(px, py, H["paths"][r]) for px, py in wps_dunya) / len(wps_dunya)
           for r in (1, 2, 3)}
    sirali = sorted(ort, key=lambda r: (ort[r], r))
    return {"yol": int(sirali[0]), "ort_uzaklik_m": {str(r): round(ort[r], 2) for r in (1, 2, 3)},
            "ayrim_m": round(ort[sirali[1]] - ort[sirali[0]], 2)}


def besleme_hazirla(tarama_dir: Path, pozlar: list[tuple], besleme: str, hedef_dir: Path) -> tuple[str, list]:
    """cv2 görüntü dizisi deseni + kare başına uygulanan θ (rad). `ham` kopya yapmaz."""
    import cv2
    kare_dir = Path(tarama_dir) / "kareler"
    if besleme == "ham":
        for n, *_ in pozlar:
            if not (kare_dir / f"scan_{n:05d}.jpg").is_file():
                raise FileNotFoundError(kare_dir / f"scan_{n:05d}.jpg")
        return str(kare_dir / "scan_%05d.jpg"), [0.0] * len(pozlar)
    if besleme != "kerteriz":
        raise ValueError(f"besleme {besleme!r} — {BESLEMELER}")
    hedef_dir = Path(hedef_dir)
    hedef_dir.mkdir(parents=True, exist_ok=True)
    for eski in hedef_dir.glob("scan_*.png"):
        eski.unlink()
    tetalar = []
    for n, _t, _x, _y, _z, yaw in pozlar:
        img = cv2.imread(str(kare_dir / f"scan_{n:05d}.jpg"))
        if img is None:
            raise FileNotFoundError(kare_dir / f"scan_{n:05d}.jpg")
        k = ceyrek_tur(yaw)
        cv2.imwrite(str(hedef_dir / f"scan_{n:05d}.png"), np.ascontiguousarray(np.rot90(img, k)))
        tetalar.append(k * math.pi / 2.0)
    return str(hedef_dir / "scan_%05d.png"), tetalar


# ── Üretim yoluna takılan sim uçları ─────────────────────────────────────────

class SimIrtifaOkuyucu:
    """`comms/inis_kaniti.BagilIrtifaOkuyucu` yerine sim irtifası (poses.csv z).

    `run_camera` kare başına `kare_olcek_kahini` → `CanliOlcekSaglayici.kare_mpp` TAM BİR KEZ
    çağırır; her `irtifa_m()` bir sonraki kareye karşılık gelir. Hizalama koşum sonunda
    `okunan == cagri_n` ile DENETLENİR (sonuç JSON'unda `hizali`)."""

    def __init__(self, z_listesi):
        self.z = [float(v) for v in z_listesi]
        self.kare = -1

    def irtifa_m(self):
        self.kare += 1
        if self.kare >= len(self.z):
            return None                    # fail-closed: kare yoksa ölçek yok
        return self.z[self.kare]

    @property
    def cagri_n(self) -> int:
        return self.kare + 1

    def durdur(self):
        return True


def _yayinci_sinifi():
    from iha_sender import KararYayinci

    class SenkronYayinci(KararYayinci):
        """Üretim `KararYayinci`; yalnız `karar()` gönderim tamamlanana dek bekler ve kaydeder."""

        def __init__(self, sender, okuyucu, **kw):
            super().__init__(sender, **kw)
            self._okuyucu = okuyucu
            self.kayit = []

        def karar(self, open_path, conf, waypoints_px, mpp, karar_reddi=None):
            n0, h0 = len(self.gonderilen), len(self.hata)
            k = {"kare": self._okuyucu.kare,
                 "open_path": (None if open_path is None else int(open_path)),
                 "conf": round(float(conf), 4),
                 "wp_px": [[round(float(px), 1), round(float(py), 1)] for px, py in (waypoints_px or [])],
                 "mpp": (None if mpp is None else round(float(mpp), 6)),
                 "red": (None if karar_reddi is None else [str(v) for v in karar_reddi])}
            self.kayit.append(k)
            super().karar(open_path, conf, waypoints_px, mpp, karar_reddi)
            bitis = time.monotonic() + SENKRON_ZAMAN_ASIMI_S
            while len(self.gonderilen) == n0 and len(self.hata) == h0 and time.monotonic() < bitis:
                time.sleep(0.0005)
            if len(self.gonderilen) > n0:
                tip, deger, seq, acked = self.gonderilen[n0]
                k["gonderim"] = {"tip": tip, "deger": deger, "seq": seq, "acked": sorted(acked)}
            else:
                k["gonderim"] = {"tip": "HATA", "hata": self.hata[h0:] or ["zaman aşımı"]}

    return SenkronYayinci


class _YksDinleyici:
    """YKS ucu: OPEN_ROUTE/NO_ROUTE'u kaydeder ve ACK döner (ref_tip'li, CONTRACTS §6.6)."""

    def __init__(self):
        from link import UDPLink
        from protocol import FrameReader
        self.link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        self.addr = ("127.0.0.1", self.link.port)
        self.mesajlar, self.heartbeat_n = [], 0
        self._dur = threading.Event()
        self._FrameReader = FrameReader
        self._thr = threading.Thread(target=self._dongu, name="sim-yks", daemon=True)

    def _dongu(self):
        from protocol import (MESAJ_HEARTBEAT, MESAJ_NO_ROUTE, MESAJ_OPEN_ROUTE, ack, encode)
        while not self._dur.is_set():
            d, adr = self.link.recv()
            if not d:
                continue
            for m in self._FrameReader().feed(d):
                tip = m.get("type") if isinstance(m, dict) else None
                if tip == MESAJ_HEARTBEAT:
                    self.heartbeat_n += 1
                elif tip in (MESAJ_OPEN_ROUTE, MESAJ_NO_ROUTE):
                    self.mesajlar.append(m)
                    self.link.send(encode(ack(m["seq"], "yks", ref_tip=tip)), adr)

    def baslat(self):
        self._thr.start()
        return self

    def kapat(self):
        self._dur.set()
        self._thr.join(2.0)
        self.link.close()


# ── Tek harita ──────────────────────────────────────────────────────────────

def _mesaj_ozeti(m: dict) -> dict:
    from protocol import MESAJ_OPEN_ROUTE
    if m.get("type") == MESAJ_OPEN_ROUTE:
        return {"tip": "OPEN_ROUTE", "seq": m.get("seq"), "yol": m.get("road"),
                "guven": m.get("conf"), "wp_n": len(m.get("waypoints") or [])}
    return {"tip": "NO_ROUTE", "seq": m.get("seq"), "sebep": m.get("sebep"), "detay": m.get("detay")}


def harita_hukmu(kayit: dict) -> dict:
    """Ön kayıtlı hüküm — TEK TANIM (test ve özet bunu çağırır). Girdi: `ika_yayin` listesi."""
    acik = int(kayit["acik_yol"])
    orl = [m for m in kayit["ika_yayin"] if m["tip"] == "OPEN_ROUTE"]
    yanlis = [m for m in orl if int(m["yol"]) != acik]
    son = kayit["ika_yayin"][-1] if kayit["ika_yayin"] else None
    return {
        "open_route_var": bool(orl),
        "dogru": bool(orl) and not yanlis,
        "yanlis_yol_yayini_n": len(yanlis),
        "ilk_open_route_dogru": (None if not orl else int(orl[0]["yol"]) == acik),
        "son_open_route_dogru": (None if not orl else int(orl[-1]["yol"]) == acik),
        "son_yayin_tipi": (None if son is None else son["tip"]),
    }


def harita_teshisi(kayit: dict) -> dict:
    """TEŞHİS — ön kayıtlı hükmü DEĞİŞTİRMEZ (bkz. modül başı). Girdi: `topla` sonucu."""
    kare = kayit["kareler"]
    tb = [s for s in kare if s.get("tarama_bacagi")]
    orl = [s for s in kare if s.get("karar") == "OPEN_ROUTE"]
    return {
        "tarama_bacagi_kare_n": len(tb),
        "kb_karede_kare_n": sum(bool(s.get("kb_karede")) for s in tb),
        "hb_karede_kare_n": sum(bool(s.get("hb_karede")) for s in tb),
        "kb_hb_ayni_karede_kare_n": sum(bool(s.get("kb_karede")) and bool(s.get("hb_karede")) for s in tb),
        "or_kare_n": len(orl),
        "or_dunya_yolu_dogru_n": sum(bool(s.get("rota_dunya_yolu_dogru")) for s in orl),
        "or_etiket_dunya_esit_n": sum(bool(s.get("etiket_dunya_esit")) for s in orl),
        "or_dunya_yollari": dict(sorted(collections.Counter(str(s.get("rota_dunya_yolu")) for s in orl).items())),
        "dunya_yolu_dogru_var": any(bool(s.get("rota_dunya_yolu_dogru")) for s in orl),
        "kare_ika_or_tutarli": len(orl) == int(kayit["open_route_n"]),
        "not": "TEŞHİS — hüküm (ön kayıt, yayınlanan etiket) değişmez",
    }


def teshis_topla(rs: list) -> dict:
    """Besleme başına TEŞHİS sayımı (`harita_teshisi` toplamı)."""
    th = [harita_teshisi(r) for r in rs]
    return {
        "harita_n": len(th),
        "dunya_yolu_dogru_or_olan_harita_n": sum(t["dunya_yolu_dogru_var"] for t in th),
        "or_kare_n": sum(t["or_kare_n"] for t in th),
        "or_dunya_yolu_dogru_n": sum(t["or_dunya_yolu_dogru_n"] for t in th),
        "or_etiket_dunya_esit_n": sum(t["or_etiket_dunya_esit_n"] for t in th),
        "tarama_bacagi_kare_n": sum(t["tarama_bacagi_kare_n"] for t in th),
        "kb_karede_kare_n": sum(t["kb_karede_kare_n"] for t in th),
        "hb_karede_kare_n": sum(t["hb_karede_kare_n"] for t in th),
        "kb_hb_ayni_karede_kare_n": sum(t["kb_hb_ayni_karede_kare_n"] for t in th),
        "kb_hb_ayni_karede_harita_n": sum(t["kb_hb_ayni_karede_kare_n"] > 0 for t in th),
        "kare_ika_or_tutarli_n": sum(t["kare_ika_or_tutarli"] for t in th),
    }


def topla(tarama_dir: Path, model, *, besleme: str = BESLEME_VARSAYILAN, out_dir: Path,
          harita: int, senaryo: str, seed: int, conf: float | None = None,
          model_kunye: dict | None = None) -> dict:
    """Bir haritanın tarama karelerini üretim kare döngüsünden geçir → sonuç sözlüğü."""
    import rpi_inference as ri
    from iha_sender import IhaSender
    from ika_receiver import IkaReceiver
    from karar_sozlesmesi import KARAR_HISTEREZIS_KARE, mpp_irtifadan
    from link import UDPLink
    import iha_ucus

    t0 = time.perf_counter()
    tarama_dir, out_dir = Path(tarama_dir), Path(out_dir)
    H = arena.harita(harita, senaryo)
    pozlar = poz_listesi(tarama_dir)
    desen, tetalar = besleme_hazirla(tarama_dir, pozlar, besleme, out_dir / f"besleme_{besleme}")
    if conf is None:
        conf = float(ri._arguman_ayristirici().get_default("conf"))   # üretim CLI varsayılanı (0,30)

    okuyucu = SimIrtifaOkuyucu([p[4] for p in pozlar])
    canli = ri.CanliOlcekSaglayici(okuyucu, yatay_fov_derece=HFOV_DERECE)
    yks = _YksDinleyici().baslat()
    ika_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
    ika_addr = ("127.0.0.1", ika_link.port)
    ika_rx = IkaReceiver(ika_link)
    ika_mesajlar = []
    ika_rx.on_route = ika_mesajlar.append
    ika_rx.on_no_route = ika_mesajlar.append
    ika_rx.start()
    iha_link = UDPLink(bind=("127.0.0.1", 0))
    yayinci = _yayinci_sinifi()(IhaSender(iha_link, {"ika": ika_addr, "yks": yks.addr}), okuyucu)
    yayinci.start()
    log = io.StringIO()
    import cv2
    _eski_seviye = cv2.utils.logging.getLogLevel()
    try:
        ri.durdurma_bayragini_sifirla()
        # Dizi sonunda üretim `kamera_kareleri` 30 kez yeniden dener (KAMERA_DUSEN_KARE_UST_SINIRI);
        # cv2 her denemede "imread_ can't open" UYARISI basar — yalnız log seli, davranış aynı.
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        with contextlib.redirect_stdout(log):
            kamera_ozet = ri.run_camera(model, conf, canli_olcek=canli, kaynak=desen,
                                        yayinci=yayinci, ekransiz=True)
    finally:
        cv2.utils.logging.setLogLevel(_eski_seviye)
        durdu = yayinci.stop()
        time.sleep(0.2)                       # son ACK/datagramlar alıcılarda işlensin
        ika_rx.stop()
        ika_link.close()
        yks.kapat()
        iha_link.close()
    son_ika = ika_rx.decision_snapshot()

    kayit_kare = {k["kare"]: k for k in yayinci.kayit}
    import cv2
    _ilk_kare = cv2.imread(desen % pozlar[0][0]) if pozlar else None
    hh, ww = (_ilk_kare.shape[:2] if _ilk_kare is not None else (0, 0))   # tarama kareleri aynı boy
    kareler = []
    for i, poz in enumerate(pozlar):
        n, t, x, y, z, yaw = poz
        k = kayit_kare.get(i)
        satir = {"n": n, "t": round(t, 3), "x": round(x, 2), "y": round(y, 2), "z": round(z, 2),
                 "yaw_derece": round(math.degrees(yaw), 1),
                 "teta_derece": round(math.degrees(tetalar[i]), 1),
                 "artik_aci_derece": round(abs(math.degrees(math.atan2(math.sin(yaw - tetalar[i]),
                                                                        math.cos(yaw - tetalar[i])))) if besleme == "kerteriz" else math.degrees(yaw) % 360, 1),
                 "tarama_bacagi": bool(iha_ucus.kare_kabul(x, y, z, yaw))}
        # TEŞHİS (hüküm dışı): KB / HB bu karenin görüş alanında mı — ölçek üretim formülüyle
        # (`mpp_irtifadan`, aynı irtifa ve FOV; `CanliOlcekSaglayici` ile aynı sayı).
        mpp_g = mpp_irtifadan(z, ww, yatay_fov_derece=HFOV_DERECE) if (ww and z > 0) else None
        satir["kb_karede"] = (None if not mpp_g else karede_mi(*H["kb"], poz, ww, hh, mpp_g, tetalar[i]))
        satir["hb_karede"] = (None if not mpp_g else karede_mi(*H["hb"], poz, ww, hh, mpp_g, tetalar[i]))
        if k is None:
            satir["karar"] = "BASTIRILDI (KararYumusatici D-396)"
        else:
            g = k.get("gonderim") or {}
            satir.update({"karar": g.get("tip"), "yol": k["open_path"], "guven": k["conf"], "mpp": k["mpp"],
                          "sebep": (k["red"][0] if k["red"] else None),
                          "detay": (k["red"][1] if k["red"] and len(k["red"]) > 1 else None),
                          "wp_n": len(k["wp_px"]), "acked": g.get("acked")})
            if g.get("tip") == "OPEN_ROUTE" and k["wp_px"] and k["mpp"]:
                dunya = [piksel_dunya(px, py, poz, ww, hh, k["mpp"], tetalar[i]) for px, py in k["wp_px"]]
                ilk, son = dunya[0], dunya[-1]
                dy = dunya_yolu(dunya, H)
                satir.update({"rota_ilk_dunya": [round(ilk[0], 2), round(ilk[1], 2)],
                              "rota_son_dunya": [round(son[0], 2), round(son[1], 2)],
                              "ankor_kb_uzakligi_m": round(math.dist(ilk, H["kb"]), 2),
                              "rota_sonu_hb_uzakligi_m": round(math.dist(son, H["hb"]), 2),
                              # TEŞHİS (hüküm dışı): rotanın DÜNYADA izlediği arena yolu
                              "rota_dunya": [[round(a, 2), round(b, 2)] for a, b in dunya],
                              "rota_dunya_yolu": dy["yol"], "rota_dunya_ort_uzaklik_m": dy["ort_uzaklik_m"],
                              "rota_dunya_ayrim_m": dy["ayrim_m"],
                              "rota_dunya_yolu_dogru": dy["yol"] == int(H["open"]),
                              "etiket_dunya_esit": (k["open_path"] is not None
                                                    and int(k["open_path"]) == dy["yol"])})
        kareler.append(satir)

    ika_yayin = [_mesaj_ozeti(m) for m in ika_mesajlar]
    yks_yayin = [_mesaj_ozeti(m) for m in yks.mesajlar]
    orl_ham = [m for m in ika_mesajlar if m.get("type") == "OPEN_ROUTE"]
    sonuc = {
        "harita": harita, "senaryo": senaryo, "seed": seed, "besleme": besleme,
        "acik_yol": H["open"], "acik_yol_etiket": arena.ROAD_LABEL[H["open"]],
        "kb_xy": [round(v, 2) for v in H["kb"]], "hb_xy": [round(v, 2) for v in H["hb"]],
        "tarama_dir": (str(tarama_dir.relative_to(KOK)) if tarama_dir.is_relative_to(KOK) else str(tarama_dir)),
        "kaynak_deseni": ("<tarama>/kareler/scan_%05d.jpg" if besleme == "ham" else f"<out>/besleme_{besleme}/scan_%05d.png"),
        "kare_n": len(pozlar), "okunan": int(kamera_ozet.get("okunan", 0)),
        "irtifa_cagri_n": okuyucu.cagri_n, "hizali": okuyucu.cagri_n == int(kamera_ozet.get("okunan", -1)),
        "kamera_bitis": kamera_ozet.get("bitis"), "yayinci_durdu": bool(durdu),
        "yayinci_hata": list(yayinci.hata), "karar_cagri_n": len(yayinci.kayit),
        "bastirilan_n": sum(1 for s in kareler if s["karar"].startswith("BASTIRILDI")),
        "uretim": {"imgsz": int(ri.INFER_SIZE), "conf": conf, "fov_derece": round(HFOV_DERECE, 3),
                   "histerezis_kare": int(KARAR_HISTEREZIS_KARE), "kaynak_kipi": "run_camera + dosya kaynağı"},
        "model": model_kunye,
        "kareler": kareler,
        "ika_yayin": ika_yayin, "yks_yayin": yks_yayin, "yks_heartbeat_n": yks.heartbeat_n,
        "open_route_n": len(orl_ham),
        "open_route_yollari": dict(sorted(collections.Counter(str(m.get("road")) for m in orl_ham).items())),
        "no_route_sebepleri": dict(sorted(collections.Counter(
            m["sebep"] for m in ika_yayin if m["tip"] == "NO_ROUTE").items())),
        "ack_ika_yks_n": sum(1 for s in kareler if s.get("acked") == ["ika", "yks"]),
        "ack_eksik_n": sum(1 for s in kareler if s.get("acked") not in (None, ["ika", "yks"])),
        "ilk_open_route": (None if not orl_ham else {"yol": orl_ham[0].get("road"), "guven": orl_ham[0].get("conf"),
                                                     "waypoints": orl_ham[0].get("waypoints"),
                                                     "ref_xy": orl_ham[0].get("ref_xy")}),
        "son_open_route": (None if not orl_ham else {"yol": orl_ham[-1].get("road"), "guven": orl_ham[-1].get("conf"),
                                                     "waypoints": orl_ham[-1].get("waypoints"),
                                                     "ref_xy": orl_ham[-1].get("ref_xy")}),
        "son_yayin": (ika_yayin[-1] if ika_yayin else None),
        "ika_son_durum": {"latest_yol": (None if son_ika[0] is None else son_ika[0].get("road")),
                          "last_no_route": (None if son_ika[1] is None else son_ika[1].get("sebep")),
                          "nesil": son_ika[2]},
        "log_son": log.getvalue().strip().splitlines()[-3:],
        "duvar_saati_s": round(time.perf_counter() - t0, 2),
        "hukum_tanimi": HUKUM_TANIMI, "sinir": SINIR,
    }
    orl_kare = [s for s in kareler if s.get("karar") == "OPEN_ROUTE"]
    sonuc["open_route_kareleri"] = [s["n"] for s in orl_kare]
    sonuc["open_route_tarama_bacaginda_n"] = sum(1 for s in orl_kare if s["tarama_bacagi"])
    sonuc["hukum"] = harita_hukmu(sonuc)
    sonuc["teshis"] = harita_teshisi(sonuc)
    return sonuc


# ── Özet ────────────────────────────────────────────────────────────────────

def ozet_kur(out: Path) -> dict:
    """<out>/<besleme>/harita_<h>_<lv>.json → ozet_k3_uretim.json (yazar ve döndürür)."""
    oz = ozet_hesapla(out)
    (Path(out) / OZET_ADI).write_text(json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
    return oz


def ozet_hesapla(out: Path) -> dict:
    """Besleme başına sayım — YAZMAZ, deterministik (tarih harita JSON'larından). Nöbetçi test
    diskteki özeti bununla karşılaştırır (elle düzenlenmiş/bayat özet yakalanır)."""
    out = Path(out)
    oz = {"esik": ESIK, "hukum_tanimi": HUKUM_TANIMI, "sinir": SINIR, "beslemeler": {}}
    tarih = None
    for bes in BESLEMELER:
        rs = []
        for p in sorted((out / bes).glob("harita_*_*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            r["_dosya"] = (p.relative_to(KOK) if p.is_relative_to(KOK) else p).as_posix()
            rs.append(r)
        if not rs:
            continue
        tarih = max([tarih] + [r.get("tarih") for r in rs if r.get("tarih")], key=lambda v: v or "")
        hk = [harita_hukmu(r) for r in rs]
        sebep = collections.Counter()
        for r in rs:
            sebep.update(r["no_route_sebepleri"])
        oz["beslemeler"][bes] = {
            "harita_n": len(rs),
            "open_route_var_n": sum(h["open_route_var"] for h in hk),
            "dogru_n": sum(h["dogru"] for h in hk),
            "yanlis_yol_yayini_olan_n": sum(h["yanlis_yol_yayini_n"] > 0 for h in hk),
            "ilk_open_route_dogru_n": sum(bool(h["ilk_open_route_dogru"]) for h in hk),
            "son_open_route_dogru_n": sum(bool(h["son_open_route_dogru"]) for h in hk),
            "son_yayin_no_route_n": sum(h["son_yayin_tipi"] == "NO_ROUTE" for h in hk),
            "kare_n": sum(r["kare_n"] for r in rs),
            "open_route_kare_n": sum(r["open_route_n"] for r in rs),
            "open_route_tarama_bacaginda_n": sum(r["open_route_tarama_bacaginda_n"] for r in rs),
            "hizali_n": sum(bool(r["hizali"]) for r in rs),
            "ack_eksik_n": sum(r["ack_eksik_n"] for r in rs),
            "no_route_sebepleri": dict(sorted(sebep.items(), key=lambda kv: (-kv[1], kv[0]))),
            "haritalar": [{"harita": r["harita"], "senaryo": r["senaryo"], "acik_yol": r["acik_yol"],
                           "open_route_n": r["open_route_n"], "open_route_yollari": r["open_route_yollari"],
                           "open_route_kareleri": r["open_route_kareleri"],
                           "son_yayin": r["son_yayin"], **harita_hukmu(r),
                           "teshis": {k: v for k, v in harita_teshisi(r).items() if k != "not"},
                           "dosya": r["_dosya"]} for r in rs],
            "teshis": teshis_topla(rs),
        }
    oz["tarih"] = tarih
    return oz


def model_yukle_uretim():
    """Üretim yükleyicisi (`rpi_inference.load_model`, kayıt defteri FAIL-CLOSED) + künye."""
    import rpi_inference as ri
    from on_olcum_k3 import model_coz
    mk = model_coz()
    model, yol, detay = ri.load_model(mk["path"], ayrinti=True)
    mk["kayit_dogrulamasi"] = detay.get("durum")
    mk["yukleyici"] = "rpi_inference.load_model"
    return model, mk


def main(argv=None):
    import iha_ucus
    ap = argparse.ArgumentParser(description="Üretim kare-bazlı boru hattı → sim karar toplayıcı (T214-A)")
    ap.add_argument("--map", type=int, default=1, choices=range(1, arena.HARITA_N + 1))
    ap.add_argument("--level", default="kolay", choices=arena.SCENARIOS)
    ap.add_argument("--seed", type=int, default=arena_mjcf.SEED_VARSAYILAN)
    ap.add_argument("--res", type=int, default=arena_mjcf.KAM_RES_VARSAYILAN)
    ap.add_argument("--besleme", default="hepsi", choices=BESLEMELER + ("hepsi",))
    ap.add_argument("--out", default=str(CIKTI_KOK))
    ap.add_argument("--hepsi", action="store_true", help="15 harita")
    ap.add_argument("--yeniden-tara", action="store_true", help="tarama klasörü varsa da yeniden render et")
    a = ap.parse_args(argv)
    out = Path(a.out)
    model, kunye = model_yukle_uretim()
    print(f"[toplayici] model {kunye['model_id']} sha eşleşti={kunye['eslesti']} kayıt={kunye['kayit_dogrulamasi']}")
    beslemeler = BESLEMELER if a.besleme == "hepsi" else (a.besleme,)
    isler = ([(h, lv) for h in range(1, arena.HARITA_N + 1) for lv in arena.SCENARIOS]
             if a.hepsi else [(a.map, a.level)])
    for h, lv in isler:
        tdir = out / "tarama" / f"harita_{h}_{lv}_{a.seed}" / "iha_scan"
        if a.yeniden_tara or not (tdir / "poses.csv").is_file() or not (tdir / "kareler").is_dir():
            oz = iha_ucus.tara(h, lv, a.seed, out=tdir, res=a.res, onizleme=False)
            (tdir / "tarama_ozeti.json").write_text(json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
        for bes in beslemeler:
            r = topla(tdir, model, besleme=bes, out_dir=out / bes / f"harita_{h}_{lv}", harita=h,
                      senaryo=lv, seed=a.seed, model_kunye=kunye)
            r["tarih"] = time.strftime("%Y-%m-%d %H:%M")
            (out / bes).mkdir(parents=True, exist_ok=True)
            (out / bes / f"harita_{h}_{lv}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
            hk = r["hukum"]
            print(f"[toplayici] {bes} {h} {lv}: acik={r['acik_yol']} OPEN_ROUTE={r['open_route_n']} "
                  f"yollar={r['open_route_yollari']} kareler={r['open_route_kareleri']} dogru={hk['dogru']} "
                  f"son={r['son_yayin']} hizali={r['hizali']} NO_ROUTE={r['no_route_sebepleri']} "
                  f"duvar={r['duvar_saati_s']} s")
    oz = ozet_kur(out)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "haritalar"}
                      for k, v in oz["beslemeler"].items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

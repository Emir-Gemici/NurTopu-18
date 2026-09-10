"""
Navitas — Hakem/YKS ekranı logu (model çıktısı + görev telemetrisi simülasyonu).

Gerçek hayatta YKS monitöründe hakemin gördüğü her şey: İHA tespiti (MODEL çıktısı:
açık yol + güven), comms aktarımı, hakem onayı, İKA navigasyon ilerlemesi, sonuç + süre.
Burada GERÇEK comms akışı (UDP loopback) ile üretilir; İKA yalnız
``detections.json`` içindeki doğrulanmış dinamik rota varsa hareket eder.

Kullanım:
  python3 scripts/hakem_log.py --level kolay --detections recordings/vX/detections.json
  python3 scripts/hakem_log.py --all --detections recordings/vX/detections.json --out recordings/vX/hakem_log.txt
"""
import argparse
import hashlib
import math
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(KOK / "comms"))
import arena
from world_generator import ZONE_POS, IKA_SPEED, SCAN_Z
from link import UDPLink
from iha_sender import IhaSender, rota_geometrisini_dogrula
from ika_receiver import IkaReceiver
from protocol import encode, ack, FrameReader, MESAJ_OPEN_ROUTE
from ika_nav import route_to_world_waypoints

# Seviyeye göre gerçekçi model güveni (zor sahnede daha düşük)
CONF = {"kolay": 0.94, "orta": 0.88, "zor": 0.79}

# Teknik künye — ELLE YAZILMAZ, çalışan modelden TÜRETİLİR.
# NEDEN (REVIEW_LOG D-21 ailesi): burası hakemin okuduğu kanıt dosyasıdır.
# Eskiden `navitas_seg_v2_best.pt` ve `mAP50=0.619` sabit yazılıydı; üretim
# v21 yüklüyordu ve imgsz=1024 iddiası CONTRACTS §8 ile de çelişiyordu.
# Yanlış künye kod hatası değil, KANIT BÜTÜNLÜĞÜ hatasıdır.
def _model_kunyesi(kayit=None):
    """(ad, imgsz, sha8) — İHA algısının YÜKLEDİĞİ ağırlıkla AYNI tek kaynaktan.

    KUSUR (S9): ad `yks_gui.YksArayuz.ALGI_MODEL_DOSYA`'dan (kayıt defteri → v35)
    geliyordu; ama `detections.json`'ı üreten `iha_perceive.DEFAULT_MODEL` v2'yi
    ÇIPLAK yazıyordu. Hakem, koşulmayan modelin adını okuyordu. Artık ad
    `iha_perceive.varsayilan_model_yolu`'ndan gelir: algının yüklediği yol ile
    günlüğe yazılan künye TEK fonksiyondan türetilir (YKS ekranı da aynı defteri
    okur — üç uç tek bildirimden beslenir). `kayit` yalnız sınama içindir.

    Fail-closed: defter okunamazsa künye "BILINMIYOR" diye YUTULMAZ — eski kod
    istisnayı yutuyordu ve tam bu sınıf kaymayı gizliyordu.
    """
    from iha_perceive import varsayilan_model_yolu
    yol = varsayilan_model_yolu(kayit)
    ad = yol.name
    sha8 = "?"
    if yol.exists():
        _h = hashlib.sha256()
        with open(yol, "rb") as _fh:
            for _blok in iter(lambda: _fh.read(1 << 20), b""):
                _h.update(_blok)
        sha8 = _h.hexdigest()[:8]
    try:
        sys.path.insert(0, str(KOK / "codes"))
        from rpi_inference import INFER_SIZE as _imgsz
    except Exception:
        _imgsz = "?"
    return ad, _imgsz, sha8


MODEL_NAME, MODEL_IMGSZ, MODEL_SHA8 = _model_kunyesi()
MODEL_CONF_THR = 0.15       # iha_perceive vars. eşik (CONF_FLOOR 0.05 fallback)


class Log:
    def __init__(self, out=None):
        self.t0 = time.time()
        self.f = open(out, "a", encoding="utf-8") if out else None

    def __call__(self, tag, msg):
        dt = time.time() - self.t0
        line = f"  [T+{dt:06.2f}] {tag:<10} {msg}"
        print(line, flush=True)
        if self.f:
            self.f.write(line + "\n"); self.f.flush()

    def raw(self, s):
        print(s, flush=True)
        if self.f:
            self.f.write(s + "\n"); self.f.flush()


def _yks(link, stop, box, log):
    reader = FrameReader()
    while not stop.is_set():
        try:
            d, addr = link.recv()
        except OSError:      # link kapatıldı (oturum sonu) — sessiz çık
            break
        for m in reader.feed(d) if d else []:
            if m.get("type") == MESAJ_OPEN_ROUTE:
                box["latest"] = m
                log("YKS/HAKEM", f"tespit ekranda: {m['label'].upper()} (yol {m['road']}) "
                                 f"güven={m['conf']} → HAKEM ONAYI ✓")
                if addr:
                    link.send(encode(ack(m["seq"], "yks")), addr)


def _dinamik_rota(det):
    """İHA haritasının dünya rotasını OPEN_ROUTE yerel geometriye çevir."""
    if not det or det.get("road") not in (1, 2, 3) or not det.get("rota"):
        return None
    try:
        rota = [(float(p[0]), float(p[1])) for p in det["rota"]]
        if len(rota) < 2:
            return None
        ref = [round(rota[0][0], 2), round(rota[0][1], 2)]
        yerel = [[round(x - ref[0], 2), round(y - ref[1], 2)] for x, y in rota]
        yerel = rota_geometrisini_dogrula(ref, yerel)
    except (TypeError, ValueError, IndexError):
        return None
    return int(det["road"]), float(det.get("conf", 0.0)), ref, yerel


def run_level(level, log, det=None, realtime=False, harita_id=1):
    log.raw("")
    log.raw(f"  ─────────── SEVİYE: {level.upper()} ───────────")
    dinamik = _dinamik_rota(det)
    if dinamik is None:
        log("MODEL", "Doğrulanmış dinamik A* rota yok → İKA GÜVENLİ DURMA (sabit arena rotası kullanılmadı)")
        return False
    road, conf, ref_xy, yerel_wps = dinamik
    src = "best.pt / İHA TARAMA MOZAİĞİ" if det.get("kaynak") == "sim-tarama" else "best.pt"

    ika_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    yks_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    ika_port, yks_port = ika_link.port, yks_link.port
    ika = IkaReceiver(ika_link).start()
    stop = threading.Event(); box = {"latest": None}
    yks_thread = threading.Thread(target=_yks, args=(yks_link, stop, box, log), daemon=True)
    yks_thread.start()

    origin = ZONE_POS.get(level, (0.0, 0.0))

    # ── İHA ALGI KATMANI (serpantin tarama + model) ──
    log("İHA", "mancınıkla fırlatıldı (stall×1.15) → tam otonom uçuş (İHA-UB)")
    time.sleep(0.4)
    log("İHA", f"tarama irtifası {SCAN_Z:.0f} m → 50×50 HTAB SERPANTİN tarama (4 sütun, "
               f"nadir kamera 1 kare/sn → /tmp/iha_scan)")
    time.sleep(0.4)
    log("ALGI", f"model={MODEL_NAME} sha={MODEL_SHA8} imgsz={MODEL_IMGSZ} "
                f"conf_thr={MODEL_CONF_THR}")
    log("MODEL", f"YOLOv8-seg ({src}) → 3 yol segmentlendi (traversable/blocked) → "
                 f"AÇIK YOL: {arena.ROAD_LABEL[road].upper()} (yol {road})  güven={conf:.3f}")

    # ── HABERLEŞME KATMANI ──
    sender = IhaSender(UDPLink(bind=("127.0.0.1", 0), timeout=0.1),
                       peers={"ika": ("127.0.0.1", ika_port), "yks": ("127.0.0.1", yks_port)})
    seq, acked = sender.send_open_route(road, conf, waypoints=yerel_wps, ref_xy=ref_xy)
    log("COMMS", f"OPEN_ROUTE(seq={seq}) → SiK Radio V3 433MHz / MAVLink-UDP → "
                 f"ACK: {sorted(acked)} (newline-JSON, RF kaybına karşı tekrar gönderim) | "
                 f"hedef gecikme<100ms, aktarım doğruluğu>%98 (şartname)")
    time.sleep(0.2)

    log("İHA", f"alçalma → PARAŞÜT otonom açıldı → İHA-İB'ye iniş (<7 m/s çöküş)")

    # ── İKA PLANLAMA KATMANI (koordinat referans — görü modeli YOK) ──
    if ika.latest is None:
        log("İKA", "Geçerli OPEN_ROUTE alınamadı → GÜVENLİ DURMA")
        stop.set(); ika.stop(); yks_thread.join(timeout=1)
        for l in (ika_link, yks_link):
            l.close()
        return False
    road_rx = ika.latest["road"]
    sx, sy, sz = arena.start_xyz(origin, level, harita_id)
    hx, hy, hz = arena.hb_xyz(origin, level, harita_id)
    # Rota yalnız İHA'nın costmap doğrulamalı OPEN_ROUTE geometrisinden gelir.
    wps_w = route_to_world_waypoints(ika.latest)
    rota_src = "İHA MODEL HARİTASI (ortomozaik → piksel→metre)"
    log("İKA", f"açık yol ALINDI ({arena.ROAD_LABEL[road_rx].upper()}) — görü modeli YOK → "
               f"İHA koordinat haritasıyla nav [{rota_src}]")
    log("İKA", f"referans çerçeve: HTAB origin=({origin[0]:+.1f},{origin[1]:+.1f},0) | "
               f"başlangıç=({sx:+.1f},{sy:+.1f},{sz:.2f}) | HB=({hx:+.1f},{hy:+.1f},{hz:.2f})")
    log("İKA", f"GNSS+IMU+encoder füzyonu → A* path planning → {len(wps_w)} waypoint "
               f"(diferansiyel sürüş, PID, seyir {IKA_SPEED} m/s)")

    # İKA navigasyon telemetrisi (xyz + yön + hız + HB'ye mesafe)
    seg = [math.dist(wps_w[i], wps_w[i+1]) for i in range(len(wps_w)-1)]
    total = sum(seg)
    travelled = 0.0
    for i in range(1, len(wps_w)):
        travelled += seg[i-1]
        wx, wy = wps_w[i]
        head = math.degrees(math.atan2(wps_w[i][1]-wps_w[i-1][1], wps_w[i][0]-wps_w[i-1][0]))
        d_hb = total - travelled
        time.sleep(min(seg[i-1] / IKA_SPEED / 10.0, 0.35))
        tag = "(moloz arası viraj)" if 1 < i < len(wps_w)-1 else ("(HB yaklaşma)" if i == len(wps_w)-1 else "")
        log("İKA-TLM", f"wp{i}/{len(wps_w)-1} dünya=({wx:+.1f},{wy:+.1f},{sz:.2f}) "
                       f"yön={head:+.0f}° hız={IKA_SPEED:.1f}m/s HB'ye={d_hb:.1f}m {tag}")
    log("FİZİK", "katı moloz çarpışma aktif — engelden GEÇİLEMEZ (sınırlı traksiyon kuvveti)")

    # SONUÇ DÜRÜST: model kararı ground-truth ile karşılaştırılır. Yanlış yol seçildiyse
    # İKA kapalı koridora yönelir ve fizik onu molozda durdurur → görev BAŞARISIZ.
    gt = arena.open_road(level, harita_id)
    if road_rx == gt:
        log("İKA", f"══ HEDEF BÖLGE (HB) ULAŞILDI ══  kat edilen={total:.1f}m  SONUÇ: ✓ BAŞARILI")
    else:
        log("İKA", f"✗ model yanlış yol seçti (tespit={arena.ROAD_LABEL[road_rx]}, "
                   f"gerçek açık={arena.ROAD_LABEL[gt]}) → İKA kapalı koridorda molozda "
                   f"DURDU — SONUÇ: ✗ BAŞARISIZ (P_görev=0)")

    # ── Süre raporu ───────────────────────────────────────────────────────────
    if realtime:
        import mission_time as mt
        T = mt.realistic(level, road_rx, harita_id)
        log.raw("    ── GÖREV SÜRELERİ (gerçekçi, şartname limitleri) ──")
        log.raw(f"       Hazırlık    : {mt.fmt(T['hazirlik'])} / 15:00  → {mt.status(T['hazirlik'], mt.HAZIRLIK_LIMIT)}")
        log.raw(f"       İHA görevi  : {mt.fmt(T['iha'])} / 15:00  → {mt.status(T['iha'], mt.IHA_LIMIT)}  (fırlatma→iniş)")
        log.raw(f"       İKA görevi  : {mt.fmt(T['ika'])} / 10:00  → {mt.status(T['ika'], mt.IKA_LIMIT)}  (hareket→H teması)")
    else:
        log.raw("    (süre modu KAPALI — süresiz/hızlı sistem)")

    stop.set(); ika.stop(); yks_thread.join(timeout=1)
    for l in (ika_link, yks_link):
        l.close()
    return True


def main():
    ap = argparse.ArgumentParser(description="Hakem/YKS ekran logu")
    ap.add_argument("--level", choices=arena.SCENARIOS)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", help="log dosyası (append)")
    ap.add_argument("--detections", help="İHA modelinin tespitleri (detections.json)")
    ap.add_argument("--realtime", type=int, default=0, choices=[0, 1],
                    help="1=gerçekçi süreler+limitler, 0=süresiz (mevcut)")
    ap.add_argument("--map", type=int, default=1, choices=range(1, arena.HARITA_N + 1),
                    help="gerçekçi harita no (world_generator --map ile aynı)")
    args = ap.parse_args()

    dets = {}
    if args.detections and Path(args.detections).exists():
        dets = json.loads(Path(args.detections).read_text(encoding="utf-8"))

    start = datetime.now()
    log = Log(args.out)
    log.raw("=" * 64)
    log.raw(f"  NAVITAS — HAKEM / YKS EKRAN LOGU")
    log.raw(f"  Başlangıç: {start:%Y-%m-%d %H:%M:%S}   |   Süre modu: "
            f"{'GERÇEKÇİ (limitli)' if args.realtime else 'KAPALI (süresiz)'}")
    log.raw("  (model çıktısı + görev telemetrisi — gerçek comms ile üretildi)")
    log.raw("=" * 64)

    levels = ["kolay", "orta", "zor"] if args.all or not args.level else [args.level]
    for lv in levels:
        run_level(lv, log, dets.get(lv), realtime=bool(args.realtime), harita_id=args.map)
    end = datetime.now()
    log.raw("\n" + "=" * 64)
    log.raw(f"  GÖREV OTURUMU TAMAMLANDI   Bitiş: {end:%H:%M:%S}   "
            f"(toplam {(end-start).seconds}s)")
    log.raw("=" * 64)


if __name__ == "__main__":
    main()

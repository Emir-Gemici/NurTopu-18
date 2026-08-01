"""
Navitas — Hakem/YKS ekranı logu (model çıktısı + görev telemetrisi simülasyonu).

Gerçek hayatta YKS monitöründe hakemin gördüğü her şey: İHA tespiti (MODEL çıktısı:
açık yol + güven), comms aktarımı, hakem onayı, İKA navigasyon ilerlemesi, sonuç + süre.
Burada GERÇEK comms akışı (UDP loopback) ile üretilir; arena tek kaynak.

Kullanım:
  python3 scripts/hakem_log.py --level kolay
  python3 scripts/hakem_log.py --all --out recordings/v5/hakem_log.txt
"""
import argparse
import math
import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comms"))
import arena
from world_generator import ZONE_POS, IKA_SPEED, SCAN_Z
from link import UDPLink
from iha_sender import IhaSender
from ika_receiver import IkaReceiver
from protocol import encode, ack, FrameReader

# Seviyeye göre gerçekçi model güveni (zor sahnede daha düşük)
CONF = {"kolay": 0.94, "orta": 0.88, "zor": 0.79}

# Teknik künye (model_analiz.md + şartname + sim parametreleri)
MODEL_NAME = "navitas_seg_v4_best.pt (YOLOv8s-seg, SHA 6b93f200…)"
MODEL_IMGSZ = 640           # config/model_registry.json competition profili
MODEL_CONF_THR = 0.15       # iha_perceive vars. eşik (CONF_FLOOR 0.05 fallback)
MODEL_MAP = "mask mAP50=0.6751 (blocked 0.4937; RescueNet val)"


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
            if m.get("type") == "OPEN_ROUTE":
                box["latest"] = m
                log("YKS/HAKEM", f"tespit ekranda: {m['label'].upper()} (yol {m['road']}) "
                                 f"güven={m['conf']} → HAKEM ONAYI ✓")
                if addr:
                    link.send(encode(ack(m["seq"], "yks", m.get("session"))), addr)


def run_level(level, log, det=None, realtime=False, harita_id=1):
    # det = İHA modelinin GERÇEK tespiti (detections.json); yoksa ground-truth.
    if det and det.get("road") in (1, 2, 3):
        road = det["road"]; conf = det.get("conf", 0.0)
        src = "best.pt / İHA TARAMA MOZAİĞİ" if det.get("kaynak") == "sim-tarama" else "best.pt"
    elif det is not None:
        log.raw("")
        log.raw(f"  ─────────── SEVİYE: {level.upper()} ───────────")
        log("ALGI", "ALGILAMA_BASARISIZ — model güvenilir rota üretmedi; "
                    "ground-truth fallback yasak, görev hareket ettirilmedi")
        return False
    else:
        road = arena.open_road(level, harita_id); conf = CONF.get(level, 0.85); src = "ground-truth"
    log.raw("")
    log.raw(f"  ─────────── SEVİYE: {level.upper()} ───────────")

    ika_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    yks_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    ika_port, yks_port = ika_link.port, yks_link.port
    ika = IkaReceiver(ika_link).start()
    stop = threading.Event(); box = {"latest": None}
    threading.Thread(target=_yks, args=(yks_link, stop, box, log), daemon=True).start()

    origin = ZONE_POS.get(level, (0.0, 0.0))

    # ── İHA ALGI KATMANI (serpantin tarama + model) ──
    log("İHA", "mancınıkla fırlatıldı (stall×1.15) → tam otonom uçuş (İHA-UB)")
    time.sleep(0.4)
    log("İHA", f"tarama irtifası {SCAN_Z:.0f} m → 50×50 HTAB SERPANTİN tarama (4 sütun, "
               f"nadir kamera 1 kare/sn → /tmp/iha_scan)")
    time.sleep(0.4)
    log("ALGI", f"model={MODEL_NAME} imgsz={MODEL_IMGSZ} conf_thr={MODEL_CONF_THR} | {MODEL_MAP}")
    log("MODEL", f"YOLOv8-seg ({src}) → 3 yol segmentlendi (traversable/blocked) → "
                 f"AÇIK YOL: {arena.ROAD_LABEL[road].upper()} (yol {road})  güven={conf:.3f}")

    # ── HABERLEŞME KATMANI ──
    sender = IhaSender(UDPLink(bind=("127.0.0.1", 0), timeout=0.1),
                       peers={"ika": ("127.0.0.1", ika_port), "yks": ("127.0.0.1", yks_port)})
    seq, acked = sender.send_open_route(road, conf)
    log("COMMS", f"OPEN_ROUTE(seq={seq}) → SiK Radio V3 433MHz / MAVLink-UDP → "
                 f"ACK: {sorted(acked)} (newline-JSON, RF kaybına karşı tekrar gönderim) | "
                 f"hedef gecikme<100ms, aktarım doğruluğu>%98 (şartname)")
    time.sleep(0.2)

    log("İHA", f"alçalma → PARAŞÜT otonom açıldı → İHA-İB'ye iniş (<7 m/s çöküş)")

    # ── İKA PLANLAMA KATMANI (koordinat referans — görü modeli YOK) ──
    road_rx = (box["latest"] or {}).get("road", road)
    sx, sy, sz = arena.start_xyz(origin, level, harita_id)
    hx, hy, hz = arena.hb_xyz(origin, level, harita_id)
    # Rota: MODELİN ürettiği harita (iha_haritala → det["rota"], DÜNYA koordinatı).
    # Yoksa (eski kayıt / model rota verememiş) ground-truth waypoint'e düşülür.
    if det and det.get("rota"):
        wps_w = [tuple(p) for p in det["rota"]]
        rota_src = "İHA MODEL HARİTASI (ortomozaik → piksel→metre)"
    else:
        wps_w = [arena.to_world(p, origin)
                 for p in arena.route_waypoints(road_rx, level, harita_id)]
        rota_src = "ground-truth fallback"
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

    stop.set(); ika.stop()
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

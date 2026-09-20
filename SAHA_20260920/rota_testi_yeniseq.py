"""CANLI HAKEM ONAY TESTI — uretim gibi HER SANIYE YENI SEQ (20 Eyl 2026).

NEDEN: 19 Eyl aksami bulunan hata (D-516) her yeni seq'te hakemin onay adimlarini
sifirliyordu; hakem 1. adima bassa bile ~1 s sonra siliniyordu. Duzeltme a2e69b9b +
db692109 ile geldi ama CANLI denenmedi. Elde mevcut `rota_testi.py` hep AYNI seq'i
yolladigi icin hatayi zaten gorememisti — bu bir TEST TASARIMI acigidir.

Bu betik uretimi taklit eder: ayni serit, her saniye YENI seq, arada NO_ROUTE.
Hakem iki adima BIRER KEZ basar; onay kalici degilse ACK akisi durur ve test DUSER.

GECME OLCUTU (on kayit — kosudan once yazildi, sonradan degistirilmez):
  1. Ilk ACK'ten sonra her 10 s'lik pencerede EN AZ BIR yeni-seq ACK'i gelmeli.
  2. Her NO_ROUTE'tan sonra 10 s icinde yeniden OPEN_ROUTE ACK'i gelmeli.
  3. Hicbir ACK, GONDERILMEMIS bir seq'e ait olmamali.
Uc olcut de gecerse GECTI; biri bile duserse DUSTU.

KULLANIM (Jetson'da, uretim rpi_inference DURAKLATILMIS iken):
  python3 rota_testi_yeniseq.py --sure 90 --serit 2 --seq-basla 9000
"""
import argparse, json, os, socket, sys, time

for _y in (os.environ.get("NAVITAS_COMMS"),
           os.path.expanduser("~/navitas/comms"),
           os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comms")):
    if _y and os.path.isdir(_y):
        sys.path.insert(0, _y)
        break
from protocol import open_route, rota_yok, heartbeat, encode, decode  # noqa: E402

PENCERE_S = 10.0   # olcut 1 ve 2'nin penceresi


def waypointler():
    """Ilk nokta ANKOR [0,0] (iha_sender kurali); 24 nokta ~18 m — rota_testi.py ile ayni."""
    return [[0.0, 0.0]] + [[round(0.3 * ((i % 4) - 1.5), 2), round(0.8 * i, 2)]
                           for i in range(1, 24)]


def kosu(sure, serit, seq_basla, no_route_her, hub, dinle_port, ref_xy, saat=time.time,
         dinle_adres="127.0.0.1"):
    """1 Hz uretim taklidi. Dondurur: (gonderimler, ackler, bitis).
    gonderimler: [{"seq":int,"tip":"OPEN_ROUTE"|"NO_ROUTE","t":float}]
    ackler:      [{"ref":int,"t":float}]"""
    wp = waypointler()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # NEDEN dinle_adres: 127.0.0.1'e bagli soket loopback DISINA yazamaz (OSError 22).
    # Saha kullaniminda hub Jetson icinde (127.0.0.1) dogrudur; makineler arasi kosuda 0.0.0.0 gerekir.
    s.bind((dinle_adres, dinle_port))
    s.settimeout(0.05)
    hub_adr = (hub.rsplit(":", 1)[0], int(hub.rsplit(":", 1)[1]))

    gonderimler, ackler = [], []
    seq = seq_basla
    hb_seq = seq_basla + 100000
    bas = saat()
    son_gonderim = son_hb = 0.0
    tik = 0
    try:
        while saat() - bas < sure:
            t = saat()
            if t - son_hb >= 1.0:
                s.sendto(encode(heartbeat("iha", seq=hb_seq, karar_yas=0.3)), hub_adr)
                hb_seq += 1
                son_hb = t
            if t - son_gonderim >= 1.0:
                tik += 1
                nr = no_route_her > 0 and tik % no_route_her == 0
                if nr:
                    m = rota_yok("test: periyodik NO_ROUTE (uretim taklidi)", seq=seq)
                else:
                    m = open_route(serit, 0.91, wp, list(ref_xy), seq=seq)
                s.sendto(encode(m), hub_adr)
                gonderimler.append({"seq": seq, "tip": m["type"], "t": t})
                seq += 1
                son_gonderim = t
            try:
                veri, _ = s.recvfrom(4096)
            except socket.timeout:
                continue
            for satir in veri.split(b"\n"):
                try:
                    m = decode(satir)
                except Exception:
                    continue
                if m.get("type") == "ACK" and m.get("ref") is not None:
                    ackler.append({"ref": int(m["ref"]), "t": saat(), "node": m.get("node")})
    finally:
        s.close()
    return gonderimler, ackler, saat()


def hukum(gonderimler, ackler, bitis, pencere=PENCERE_S):
    """On kayitli uc olcutu uygular. Dondurur: {"sonuc":"GECTI"|"DUSTU","gerekce":[...], ...}"""
    tip = {g["seq"]: g["tip"] for g in gonderimler}
    gerekce, notlar = [], {}

    # Olcut 3 — gonderilmemis seq'e ACK
    hayalet = sorted({a["ref"] for a in ackler} - set(tip))
    notlar["hayalet_ack_seq"] = hayalet
    if hayalet:
        gerekce.append(f"OLCUT 3 DUSTU: gonderilmemis seq'lere ACK geldi: {hayalet[:10]}")

    acik_ackler = [a for a in ackler if tip.get(a["ref"]) == "OPEN_ROUTE"]
    notlar["open_route_gonderim"] = sum(1 for g in gonderimler if g["tip"] == "OPEN_ROUTE")
    notlar["no_route_gonderim"] = sum(1 for g in gonderimler if g["tip"] == "NO_ROUTE")
    notlar["open_route_ack"] = len(acik_ackler)
    notlar["no_route_ack"] = sum(1 for a in ackler if tip.get(a["ref"]) == "NO_ROUTE")

    # Olcut 1 — ilk ACK'ten sonra her 10 s'de en az bir YENI seq ACK'i
    if not acik_ackler:
        gerekce.append("OLCUT 1 DUSTU: hic OPEN_ROUTE ACK'i gelmedi "
                       "(hakem basmadi mi, yoksa onay silindi mi? gunluge bak)")
        notlar["en_uzun_ack_boslugu_s"] = None
    else:
        ilk = acik_ackler[0]["t"]
        # yalniz YENI seq'ler sayilir: ayni seq'e ikinci ACK pencereyi doldurmaz
        gorulen, yeni_t = set(), []
        for a in acik_ackler:
            if a["ref"] not in gorulen:
                gorulen.add(a["ref"])
                yeni_t.append(a["t"])
        son_gonderim = max((g["t"] for g in gonderimler if g["tip"] == "OPEN_ROUTE"), default=ilk)
        sinir = min(bitis, son_gonderim)
        bosluklar = [b - a for a, b in zip(yeni_t, yeni_t[1:])]
        kuyruk = sinir - yeni_t[-1]
        en_uzun = max(bosluklar + [kuyruk]) if (bosluklar or kuyruk > 0) else 0.0
        notlar["en_uzun_ack_boslugu_s"] = round(en_uzun, 1)
        notlar["yeni_seq_ack_sayisi"] = len(yeni_t)
        if en_uzun > pencere:
            gerekce.append(f"OLCUT 1 DUSTU: yeni-seq ACK'leri arasinda {en_uzun:.1f} s "
                           f"bosluk var (sinir {pencere:.0f} s)")

    # Olcut 2 — her NO_ROUTE'tan sonra 10 s icinde yeniden OPEN_ROUTE ACK'i
    toparlanmayan = []
    for g in gonderimler:
        if g["tip"] != "NO_ROUTE":
            continue
        if bitis - g["t"] < pencere:
            continue           # testin sonuna denk geldi, hukum verilmez
        if not any(g["t"] < a["t"] <= g["t"] + pencere for a in acik_ackler):
            toparlanmayan.append(g["seq"])
    notlar["toparlanmayan_no_route_seq"] = toparlanmayan
    if toparlanmayan:
        gerekce.append(f"OLCUT 2 DUSTU: NO_ROUTE sonrasi {pencere:.0f} s icinde "
                       f"OPEN_ROUTE ACK'i donmedi: {toparlanmayan[:10]}")

    return {"sonuc": "DUSTU" if gerekce else "GECTI", "gerekce": gerekce,
            "pencere_s": pencere, **notlar}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sure", type=float, default=90.0, help="kosu suresi (s)")
    ap.add_argument("--serit", type=int, default=2, help="1=sol 2=orta 3=sag (DEGISMEZ)")
    ap.add_argument("--seq-basla", type=int, default=9000)
    ap.add_argument("--no-route-her", type=int, default=20,
                    help="kac tikta bir NO_ROUTE (0 = hic)")
    ap.add_argument("--hub", default="127.0.0.1:5100")
    ap.add_argument("--dinle-port", type=int, default=5193)
    ap.add_argument("--dinle-adres", default="127.0.0.1",
                    help="ACK dinleme adresi; hub baska makinedeyse 0.0.0.0 verilmeli")
    ap.add_argument("--pencere", type=float, default=PENCERE_S,
                    help="OLCUT penceresi (s). ON KAYIT 10; degistirmek olcutu GEVSETIR")
    ap.add_argument("--kayit", default=None, help="ham kaydin yazilacagi JSON")
    a = ap.parse_args(argv)

    try:
        from karar_sozlesmesi import YAYIN_REF_XY
    except Exception:
        YAYIN_REF_XY = (0.0, 0.0)

    print(f"# {a.sure:.0f} s, serit {a.serit}, her saniye YENI seq, "
          f"her {a.no_route_her} tikta NO_ROUTE. Hakem iki adima BIRER KEZ bassin.",
          flush=True)
    g, ack, bitis = kosu(a.sure, a.serit, a.seq_basla, a.no_route_her,
                         a.hub, a.dinle_port, YAYIN_REF_XY, dinle_adres=a.dinle_adres)
    if a.pencere != PENCERE_S:
        print(f"!! OLCUT GEVSETILDI: pencere {a.pencere} s (on kayit {PENCERE_S} s). "
              f"Bu kosu SAHA KANITI DEGILDIR.", flush=True)
    h = hukum(g, ack, bitis, a.pencere)
    kayit = {"olcut": {"pencere_s_on_kayit": PENCERE_S, "pencere_s_kullanilan": a.pencere,
                       "gevsetildi": a.pencere != PENCERE_S,
                       "1": "ilk ACK'ten sonra her pencerede en az bir yeni-seq ACK",
                       "2": "her NO_ROUTE'tan sonra pencere icinde OPEN_ROUTE ACK",
                       "3": "gonderilmemis seq'e ACK yok"},
             "hukum": h, "gonderimler": g, "ackler": ack}
    print(json.dumps(h, ensure_ascii=False, indent=1))
    yol = a.kayit or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  f"onay_testi_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=1)
    print("kayit:", yol)
    return 0 if h["sonuc"] == "GECTI" else 1


if __name__ == "__main__":
    sys.exit(main())

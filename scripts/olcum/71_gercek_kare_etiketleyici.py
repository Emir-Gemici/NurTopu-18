"""T84 · GERCEK KARE ETIKETLEYICI — yari otomatik, GORSEL ONAYLI.

NEDEN. Elimizdeki tek gercek goruntu 67 otopark karesidir ve ETIKETSIZDIR.
Etiketsiz veri egitime giremez; giremeyince model gercek dokuyu ogrenemez ve
cati/asfalt ayrimini yapamaz (D-118 gorseli: cati YESIL boyaniyor).

TASARIM KURALI — SENTETIK URETECIN EN KRITIK KURALI BURADA DA GECERLIDIR:
**GECILEMEZ NESNE ASLA ETIKETSIZ BIRAKILMAZ.** v16 bu kural ihlal edildigi
icin moloza basmada %2,7'den %31,6'ya cokmustu. Bu yuzden sinif atamasi
"geriye kalan zemindir" mantigiyla YAPILMAZ; her sinif KENDI kaniti ile
isaretlenir ve KANITSIZ kalan piksel `blocked` olur (fail-safe).

UC KANIT (hepsi modelden BAGIMSIZ, klasik):
  1. ARAC   — DOTA OBB yonlu kutulari. K-6'da olculdu: ayni fotografta
              COCO 2 arac, DOTA OBB 93 arac. Kahin budur.
  2. BITKI  — LAB kromasi. Kuru ot ve agac renklidir; asfalt AKROMATIKTIR.
  3. YAPI   — parlak + duz (dusuk yerel varyans) + genis bilesen. Cati asfalttan
              PARLAKLIK ve DOKUSUZLUKLA ayrilir.
Geriye kalan AKROMATIK, ORTA PARLAKLIKTA, DOKULU alan asfalttir -> traversable.

⚠ Bu betik ETIKET ONERIR, ETIKET KESINLESTIRMEZ. Cikti gorsellestirilir ve
GOZLE dogrulanir (D-80: gorsel kazanir). Onaylanmayan kare egitime GIRMEZ.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(r"O:\navitas")
sys.path.insert(0, str(REPO / "codes"))
from arac_maskesi import ARAC_SINIFLERI                     # noqa: E402
from karar_sozlesmesi import hb_konumu                      # noqa: E402

# ── Esikler: hepsi bu dosyada TEK YERDE, gorsel denetimle ayarlanir ─────────
BITKI_KROMA = 12          # LAB kroma sapmasi; gri-dunya notrune gore
# ⚠ YAPI kurali OLCUMLE ayarlandi (dorduncu gecis). Ilk hali "parlak + duz +
# genis" diyordu ve GUNES ALAN ACIK ASFALTI bina saniyordu — tam cozunurlukte
# bakildiginda otoparkin ortasinda kocaman kirmizi lekeler cikti. Aday
# bilesenler tek tek olculdu (ayni kare):
#     cati          alan 31794  L 222,3  DIKDORTGENLIK 0,853
#     asfalt lekesi alan 54250  L 180,0  DIKDORTGENLIK 0,324
#     asfalt lekesi alan 15527  L 212,7  DIKDORTGENLIK 0,339
#     asfalt lekesi alan  3881  L 182,3  DIKDORTGENLIK 0,355
# Cati DIKDORTGENDIR (dogal yapi), gunes lekesi PACAVRADIR. Ayrim keskin.
YAPI_PARLAKLIK = 205      # L ortalamasi (175 -> 205; asfalt lekesi 180-213)
YAPI_DOKU_VAR = 90        # yerel varyans TAVANI — cati DUZDUR
YAPI_DIKDORTGENLIK = 0.45  # alan / minAreaRect alani; cati 0,47-0,85 · leke 0,32-0,36
YAPI_ASGARI_ALAN = 4000   # px; kucuk parlak lekeler yapi degildir
YAPI_KAPAMA = 9           # 15 -> 9: buyuk cekirdek catiyi komsu asfalta YAPISTIRIYORDU
ARAC_CONF = 0.25


def yerel_varyans(gri, k=9):
    g = gri.astype(np.float32)
    ort = cv2.blur(g, (k, k))
    return cv2.blur(g * g, (k, k)) - ort * ort


def hedef_pedi(img, hedef_kutu=None):
    """(maske|None, kaynak_metni) — H pedinin piksel bolgesi.

    🔴 T87 KUSURU (mimar gozle gordu): kompozit karelere eklenen `H` HEDEF
    PEDI, BITKI kuralinin kroma esigine takilip **ENGEL** isaretleniyordu.
    H, IKA'nin ULASMASI GEREKEN hedeftir; onu engel ogretmek IKA'yi hedefe
    hicbir zaman ulasamaz hale getirir — K-2 sinifi kusur.

    Iki kaynak, sirasiyla:
      1. MANIFEST `arena.hedef_kutu` — pedin YAPISTIRILDIGI yer; tam ve
         tartisilmaz. Otorite budur.
      2. `karar_sozlesmesi.hb_konumu` — T72/D-105 dedektoru. Manifest yoksa.
    Ikisi de yoksa None doner ve cagirici bunu KAYDA yazar; ped sessizce
    engel BIRAKILMAZ, durum GORUNUR olur.
    """
    h, w = img.shape[:2]
    if hedef_kutu:
        x, y, bw, bh = (int(v) for v in hedef_kutu)
        m = np.zeros((h, w), np.uint8)
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(w, x + bw), min(h, y + bh)
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] = 1
            return m, f"manifest hedef_kutu {[x, y, bw, bh]}"
        return None, f"manifest hedef_kutu KARE DISINDA {[x, y, bw, bh]}"
    kon = hb_konumu(img)
    if kon is None:
        return None, "manifest yok ve HB dedektoru ped BULAMADI"
    x, y, bw, bh = kon["kutu"]
    m = np.zeros((h, w), np.uint8)
    m[max(0, y):min(h, y + bh), max(0, x):min(w, x + bw)] = 1
    return m, f"hb_konumu (T72/D-105) kutu {[x, y, bw, bh]}"


def etiket_onerisi(img, obb_sonuc, hedef_kutu=None):
    """(engel_maskesi, zemin_maskesi, ayrinti) — ikisi ORTUSMEZ, birlesimi TAM."""
    h, w = img.shape[:2]
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    a = lab[:, :, 1].astype(np.int16) - 128
    b = lab[:, :, 2].astype(np.int16) - 128

    # 1) ARAC — OBB poligonlari
    arac = np.zeros((h, w), np.uint8)
    n_arac = 0
    if obb_sonuc.obb is not None and len(obb_sonuc.obb):
        adlar = obb_sonuc.names
        cls = obb_sonuc.obb.cls.cpu().numpy().astype(int)
        poly = obb_sonuc.obb.xyxyxyxy.cpu().numpy()
        for c, p in zip(cls, poly):
            if adlar.get(int(c), str(c)) not in ARAC_SINIFLERI:
                continue
            cv2.fillPoly(arac, [p.reshape(-1, 2).astype(np.int32)], 1)
            n_arac += 1

    # 2) BITKI — kromatik alan.
    # ⚠ MUTLAK kroma KULLANILAMAZ (olculdu, ilk gecis): bu kareler drone
    # kaydidir ve GLOBAL MAVI YATKINLIGI tasir. LAB'de mavi, `b`yi notrden
    # uzaklastirir; mutlak esik asfalti "bitki" sanip ZEMINI ENGEL yapti
    # (zemin orani 0,17 cikti, gorselde asfalt kirmizi bitki yesildi).
    # Cozum GRI-DUNYA: karenin KENDI medyan a/b'si notr kabul edilir. Asfalt
    # baskin yuzey oldugu icin medyan onu temsil eder; bitki ondan SAPAR.
    a0, b0 = float(np.median(a)), float(np.median(b))
    # ⚠ YONSUZ kroma da YETMEZ (olculdu, ikinci gecis): golge de notrden sapar
    # ve arac siralarinin kenarindaki golgeler ENGEL isaretlendi. "Koyu asfalt
    # engeldir" ogretmek golgeli koridorlari kapatir — kabul edilemez.
    # Bitki ile golge FARKLI YONE sapar:
    #     kuru ot / toprak -> SARI  (b - b0 > 0)
    #     agac / cim       -> YESIL (a - a0 < 0)
    #     golge            -> MAVI  (b - b0 < 0)   <- disarida birakilir
    # ⚠ SADECE bitki yonlerini saymak da YETMEZ (olculdu, ucuncu gecis):
    # KIREMIT CATILI bina ne parlak (yapi kurali kacirdi) ne sari/yesil
    # (bitki kurali kacirdi) — ZEMIN isaretlendi. Gecilemez bir yapiyi
    # etiketsiz birakmak uretecin EN KRITIK kural ihlalidir (v16: %2,7 -> %31,6).
    #
    # Kural TERSINE cevrildi: artik "zemin nedir" degil, "NOTR GRI ASFALT
    # DEGILSE ENGELDIR" tanimlanir (fail-safe, madde 15 yonunde).
    #   a ekseninde HER IKI yon  -> yesil (agac) VE kirmizi (kiremit) yakalanir
    #   b ekseninde YALNIZ sari  -> kuru ot yakalanir
    #   b ekseninde MAVI HARIC   -> golge asfalt olarak KALIR (tek istisna)
    bitki = ((np.abs(a - a0) > BITKI_KROMA) |
             ((b - b0) > BITKI_KROMA)).astype(np.uint8)
    bitki = cv2.morphologyEx(bitki, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    # 3) YAPI — parlak VE duz VE genis
    duz = yerel_varyans(L) < YAPI_DOKU_VAR
    aday = ((L > YAPI_PARLAKLIK) & duz).astype(np.uint8)
    aday = cv2.morphologyEx(aday, cv2.MORPH_CLOSE,
                            np.ones((YAPI_KAPAMA, YAPI_KAPAMA), np.uint8))
    n, lbl, st, _ = cv2.connectedComponentsWithStats(aday, 8)
    yapi = np.zeros((h, w), np.uint8)
    n_yapi = 0
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < YAPI_ASGARI_ALAN:
            continue
        m = (lbl == i).astype(np.uint8)
        kon, _h = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not kon:
            continue
        rect = cv2.minAreaRect(max(kon, key=cv2.contourArea))
        ra = rect[1][0] * rect[1][1]
        # DIKDORTGENLIK: yapi dogal olarak dikdortgendir; gunes alan asfalt
        # lekesi degildir. Bu olcut olmadan asfalt "bina" isaretleniyordu.
        if ra <= 0 or st[i, cv2.CC_STAT_AREA] / ra < YAPI_DIKDORTGENLIK:
            continue
        yapi[lbl == i] = 1
        n_yapi += 1

    engel = ((arac | bitki | yapi) > 0).astype(np.uint8)

    # 4) 🔴 HEDEF PEDI (H) ENGEL DEGILDIR — T87.
    # Bu ADIM SON SIRADA olmali: ped, BITKI (kirmizi kroma) ve YAPI (parlak
    # duz dikdortgen) kurallarinin IKISINE de takilabilir; hangisi isaretlemis
    # olursa olsun burada geri alinir.
    ped, ped_kaynak = hedef_pedi(img, hedef_kutu)
    ped_engel_px = 0
    if ped is not None:
        ped_engel_px = int((engel & ped).sum())
        engel[ped > 0] = 0

    zemin = 1 - engel
    return engel, zemin, {"arac": n_arac, "yapi_bileseni": n_yapi,
                          "engel_orani": float(engel.mean()),
                          "zemin_orani": float(zemin.mean()),
                          "hedef_kaynagi": ped_kaynak,
                          "hedef_px": int(ped.sum()) if ped is not None else 0,
                          # Pedin KAC pikseli yanlislikla engel isaretlenmisti:
                          # kusurun BUYUKLUGU kayda gecer, "duzelttim" demek yetmez.
                          "hedef_engelden_kurtarilan_px": ped_engel_px}


def gorsellestir(img, engel, zemin, ped=None):
    g = img.copy()
    g[engel > 0] = (0.45 * g[engel > 0] + 0.55 * np.array([0, 0, 255])).astype(np.uint8)
    g[zemin > 0] = (0.65 * g[zemin > 0] + 0.35 * np.array([0, 255, 0])).astype(np.uint8)
    if ped is not None and ped.any():
        # T87 gorsel kaniti: pedin KIRMIZI (engel) DEGIL, zemin tonunda ve
        # MAVI cerceveli oldugu tek bakista gorulmeli (D-80: gorsel kazanir).
        kon, _ = cv2.findContours(ped, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(g, kon, -1, (255, 200, 0), 2)
        for c in kon:
            x, y, bw, bh = cv2.boundingRect(c)
            cv2.putText(g, "H = HEDEF (engel DEGIL)", (max(0, x - 4), max(12, y - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 200, 0), 1, cv2.LINE_AA)
    return g


def poligonlar(maske, asgari=250):
    """Maskeyi YOLO-seg poligonlarina cevir. Delikler ic konturla YOK EDILMEZ —
    delik varsa parca ayri poligon olur; kucuk parcalar ATILMAZ, ENGEL tarafina
    birakilir (fail-safe)."""
    kon, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cikti = []
    for c in kon:
        if cv2.contourArea(c) < asgari:
            continue
        eps = 0.002 * cv2.arcLength(c, True)
        p = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
        if len(p) >= 3:
            cikti.append(p)
    return cikti


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", type=Path, default=REPO / "data" / "raw_frames")
    ap.add_argument("--cikti", type=Path, required=True)
    ap.add_argument("--obb", type=Path, default=REPO / "yolov8m-obb.pt")
    ap.add_argument("--adim", type=int, default=1, help="her N. kare")
    ap.add_argument("--azami", type=int, default=0, help="0 = sinirsiz")
    ap.add_argument("--yaz-etiket", action="store_true",
                    help="YOLO-seg .txt yaz (varsayilan: yalniz onizleme)")
    # T87: kompozit kareler HEDEF PEDI tasir ve manifest onun yerini BILIR.
    # Manifest verilmezse dedektore dusulur; ikisi de yoksa durum kayda gecer.
    ap.add_argument("--manifest", type=Path, default=None,
                    help="kaynak kumenin manifest.json'u (arena.hedef_kutu)")
    # Bolumu manifestten al: train/val ayrimi UYDURULMAZ, kaynak kumeninkiyle
    # AYNI kalir — aksi halde ayni kare hem egitimde hem dogrulamada olabilir.
    ap.add_argument("--bolum-manifestten", action="store_true")
    args = ap.parse_args()

    from ultralytics import YOLO
    obb = YOLO(str(args.obb), task="obb")

    hedef_kutulari, bolumler = {}, {}
    if args.manifest is not None:
        man = json.loads(args.manifest.read_text(encoding="utf-8"))
        for o in man.get("ornekler", []):
            cikti = o.get("cikti")
            if not cikti:
                continue
            ad = Path(cikti).name
            arena = o.get("arena") or {}
            if arena.get("hedef_kutu"):
                hedef_kutulari[ad] = arena["hedef_kutu"]
            if o.get("bolum"):
                bolumler[ad] = o["bolum"]
        print(f"manifest: {len(hedef_kutulari)} hedef kutusu · "
              f"{len(bolumler)} bolum kaydi")

    kareler = sorted(args.kok.rglob("*.jpg"))[::args.adim]
    if args.azami:
        kareler = kareler[:args.azami]
    (args.cikti / "onizleme").mkdir(parents=True, exist_ok=True)
    if args.yaz_etiket:
        for b in (set(bolumler.values()) or {""}) if args.bolum_manifestten else {""}:
            (args.cikti / "images" / b).mkdir(parents=True, exist_ok=True)
            (args.cikti / "labels" / b).mkdir(parents=True, exist_ok=True)

    ozet = []
    for p in kareler:
        img = cv2.imread(str(p))
        if img is None:
            continue
        r = obb.predict(str(p), conf=ARAC_CONF, verbose=False)[0]
        kutu = hedef_kutulari.get(p.name)
        engel, zemin, d = etiket_onerisi(img, r, hedef_kutu=kutu)
        ped, _ = hedef_pedi(img, kutu)
        ad = f"{p.parent.name[-8:]}_{p.stem}"
        cv2.imwrite(str(args.cikti / "onizleme" / f"{ad}.jpg"),
                    gorsellestir(img, engel, zemin, ped))
        d["kare"] = ad
        d["kaynak"] = str(p)
        bolum = bolumler.get(p.name, "") if args.bolum_manifestten else ""
        d["bolum"] = bolum or None
        ozet.append(d)

        if args.yaz_etiket:
            h, w = img.shape[:2]
            satirlar = []
            for sinif, mask in ((0, zemin), (1, engel)):
                for poly in poligonlar(mask):
                    xy = poly.astype(np.float32)
                    xy[:, 0] /= w
                    xy[:, 1] /= h
                    satirlar.append(str(sinif) + " " +
                                    " ".join(f"{v:.6f}" for v in xy.reshape(-1)))
            # 🔴 HEDEF PEDI AYRI VE SON POLIGON — T87, OLCUMLE gerekcelendirildi.
            # Pedi maskeden cikarmak YETMEDI: `poligonlar()` `RETR_EXTERNAL`
            # kullanir, yani pedin actigi DELIK kaybolur ve ped yeniden engel
            # poligonunun icinde kalir. Egiticinin gordugu maske olculdugunde
            # (Ultralytics `overlap_mask: true`, `polygons2masks_overlap`)
            # pedin 9 karenin 6'sinda HALA engel oldugu goruldu; 2 karede
            # 1681 pikselin 1681'i.
            # Cozum: ped KENDI poligonu olarak EN SONA yazilir. Ultralytics
            # poligonlari ALANA GORE buyukten kucuge basar, kucuk olan KAZANIR;
            # ped (1681 px) her buyuk engel poligonunu EZER. Pedin uzerindeki
            # DAHA KUCUK bir enkaz poligonu pedi ezmeye devam eder — dogrusu da
            # budur, ped uzerindeki gercek engel gorunur kalmalidir.
            if ped is not None and ped.any():
                for poly in poligonlar(ped, asgari=1):
                    xy = poly.astype(np.float32)
                    xy[:, 0] /= w
                    xy[:, 1] /= h
                    satirlar.append("0 " +
                                    " ".join(f"{v:.6f}" for v in xy.reshape(-1)))
            cv2.imwrite(str(args.cikti / "images" / bolum / f"{ad}.jpg"), img)
            (args.cikti / "labels" / bolum / f"{ad}.txt").write_text(
                "\n".join(satirlar), encoding="utf-8")

    zo = np.array([o["zemin_orani"] for o in ozet])
    print(f"\n{'=' * 62}\nETIKET ONERISI · {len(ozet)} kare\n{'=' * 62}")
    print(f"  arac (kare basina)  ort {np.mean([o['arac'] for o in ozet]):.1f}")
    print(f"  yapi bileseni       ort {np.mean([o['yapi_bileseni'] for o in ozet]):.1f}")
    print(f"  ZEMIN orani         medyan {np.median(zo):.3f} · "
          f"min {zo.min():.3f} · maks {zo.max():.3f}")
    print(f"  (v27'nin ayni karelerdeki zemin kaplamasi: ~0,81 — kapi tavani 0,67)")
    # T87: hedef pedi kusurunun BUYUKLUGU ve nereden cozuldugu GORUNUR olsun.
    kurtarilan = [o.get("hedef_engelden_kurtarilan_px", 0) for o in ozet]
    pedli = sum(1 for o in ozet if o.get("hedef_px"))
    print(f"  HEDEF PEDI (H)      {pedli}/{len(ozet)} karede bulundu · "
          f"engelden kurtarilan px: toplam {sum(kurtarilan)} · "
          f"kare basina ort {np.mean(kurtarilan):.0f}")
    kaynaklar = {}
    for o in ozet:
        kaynaklar[str(o.get("hedef_kaynagi")).split(" kutu")[0].split(" hedef_kutu")[0]] = \
            kaynaklar.get(str(o.get("hedef_kaynagi")).split(" kutu")[0]
                          .split(" hedef_kutu")[0], 0) + 1
    for k, c in sorted(kaynaklar.items(), key=lambda x: -x[1]):
        print(f"                      {c:3d}  {k}")
    print("=" * 62)
    print(f"onizleme -> {args.cikti / 'onizleme'}")
    (args.cikti / "ozet.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

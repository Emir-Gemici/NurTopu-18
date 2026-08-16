"""KORIDOR ENVANTERI KARARLI MI? — YALNIZ OLCUM (gorev T79-A).

NEDEN. Uretim modeli v30, gercekci algilayici gurultusu altinda 260 karenin
8'inde KARARI CEVIRIYOR (D-142; hedef <= 4/260). D-126'da "gurultu tabani
altindaki beraberliklerde deterministik secim" denendi ve 9 -> 8'e indi, yani
yalniz 1 kare duzeldi. D-143 nedenini olctu: cevrilen 8 karenin 4'unde SAHNEDE
TEK SERIT DOLUDUR — tek seritli bir kare seritler arasi beraberlikten
cevrilemez, ortada ikinci aday yoktur.

KOD TESPITI (bu olcumun cikis noktasi): uretim yolu `analyze_path` TEK bir
kuresel A* kosturur; serit rotadan SONRADAN olculur. Yani beraberlik bozma,
rotanin hangi koridordan gececegini YAPISAL OLARAK degistiremez. Buna karsilik
`rota_bul` icinde gercek bir koridor ENVANTERI vardir: `koridor_adaylari()`
kapilari ayirir, her birini tek tek gecilebilirlik testinden gecirir ve bir
kazanan secilir. Uretim bunu KULLANMIYOR.

SORULAN TEK SORU: koridor ENVANTERI, uretimin kuresel A*'indan daha mi
kararlidir? Oyleyse care "beraberlik bozma" degil "secimi envantere baglamak"
olabilir; envanter de ceviriyorsa care BASKA yerdedir.

────────────────────────────────────────────────────────────────────────────
ON KAYIT — SONUCU GORMEDEN ONCE BAGLAYICI (D-107 disiplini).
Bu kural bu dosyaya, betik KOSULMADAN once yazilmistir. Sonuca gore kurali
degistirmek YASAKTIR.

  (A) B <= 4/260  VE  D >= 255/260 ACIK
      -> envanter YETERINCE KARARLI. Yon: uretim secimini envantere baglamak.
         🔴 FIX YINE DE YAZILMAZ. Olc, yaz, gorevi [ ] birak. Tasarim mimarindir.
  (B) B > 4/260
      -> envanter DE kararsiz. (E)'de hangi alanin cevirdigini yaz, fix YAZMA.
  (C) A, 8/260'tan ±1'den fazla sapiyorsa
      -> olcum kosumu D-142'den IRAKSAMIS demektir. DUR, nedenini arastir,
         baska hicbir sonucu rapor etme.
  (D) D < 255/260 ise, B ne cikarsa ciksin envantere baglamak KAZANC DEGILDIR
      (8 karelik kararsizlik icin 5+ kare yetenek odenmez). Bunu acikca yaz.
────────────────────────────────────────────────────────────────────────────

🔴 OLCUM SOZLESMESI (D-139 dersi: uretimin yaptigi islemi atlayan bir olcum
uretimi olcmez). Kare basina model YALNIZ BIR KEZ kosar ve CIKAN AYNI `mk`
maskeleri HEM `analyze_path`e HEM `rota_bul`a verilir. Iki ayri cikarim
yapilsaydi envanter ile karar FARKLI gurultu orneklerinden gelirdi ve
karsilastirma anlamsiz olurdu.

Gurultu receteleri 68_karar_kararliligi.py'den AYNEN alinmistir (sigma=2/255,
tekrar=3, tohum=7, kume sentetik_arena_kadraj_t66, CONF=0.30, model kayit
defterinden). Sayilar D-142 ile kiyaslanabilsin diye DEGISTIRILMEZ.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from costmap_path_finder import (koridor_adaylari,  # noqa: E402
                                 rota_bul, serbest_alan)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
# Surum adi CIPLAK SABIT degildir (madde 16) — kayit defteri tek kaynak.
MODEL = uretim_pt()
CONF = 0.30


# ────────────────────────────────────────────────────────────────────────────
# 1) TEK CIKARIM — iki tuketici
# ────────────────────────────────────────────────────────────────────────────
def cikarim(model, img):
    """Modeli BIR KEZ kostur; `mk` hem uretime hem envantere GIDER."""
    sq, small, icerik = _preprocess(img)
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
    return mk, icerik


def uretim_karari(mk, icerik, mpp):
    """68_karar_kararliligi.karar() ile BIREBIR ayni.

    Tek fark cikarimin disaridan verilmesidir; cagri imzasi, bayraklar ve
    donen demet aynen korunmustur — A sayisi D-142 ile kiyaslanabilsin diye.
    """
    yol, guven, wps, _k, red, olcum = analyze_path(
        mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
        return_clean=True, return_reason=True, return_olcum=True)
    olcum = olcum or {}
    return (yol, red[0] if isinstance(red, tuple) else red, guven,
            olcum.get("darbogaz_px"), olcum.get("r_gerekli_px"))


def _aday_ozeti(adaylar):
    """(etiket, gecilebilir, darbogaz) demetleri — kapi merkezine gore sirali
    gelirler, sirayi BOZMA."""
    return [[int(a["etiket"]), bool(a["gecilebilir"]),
             round(float(a["darbogaz_px"]), 2)] for a in adaylar]


def envanter(mk, icerik, mpp):
    """`rota_bul(plan=False)` — A* atlanir, envanter kurulur.

    `rota_bul` `tani`yi DONDURMEZ; n_kapi/belirsiz/bant_y icin `serbest_alan`
    + `koridor_adaylari` ayrica cagrilir. Bu ikinci cagri SAF ve AYNI girdiyle
    yapilir; asagidaki `tutarli` bayragi iki yolun ayni `adaylar`i uretip
    uretmedigini HER KAREDE dogrular (olcumun kendi pozitif kontrolu).
    Kazanan asla elle hesaplanmaz — tek kaynak `rota_bul`un `yol_no`sudur.
    """
    r = rota_bul(mk, mpp=mpp, icerik=icerik, plan=False)

    # `rota_bul` `serbest_alan`i `icerik` ile cagirir; ikinci cagri BIREBIR
    # ayni argumanlarla yapilmalidir, yoksa `tutarli` sahte kirmizi verir.
    s = serbest_alan(mk, mpp=mpp, icerik=icerik)
    ad2, tani = koridor_adaylari(s["dt_px"], s["olcek"]["r_gerekli_px"],
                                 None, None, icerik=s["icerik"])
    tutarli = _aday_ozeti(ad2) == _aday_ozeti(r["adaylar"])

    return {
        "durum": r["durum"],
        "yol_no": r["yol_no"],
        "guven": r["guven"],
        "n_kapi": tani.get("n_kapi"),
        "belirsiz": tani.get("belirsiz"),
        "bant_y": list(tani["bant_y"]) if tani.get("bant_y") else None,
        "adaylar": _aday_ozeti(r["adaylar"]),
        "tutarli": tutarli,
    }


# ────────────────────────────────────────────────────────────────────────────
# 2) KIYAS ANAHTARLARI
# ────────────────────────────────────────────────────────────────────────────
def _karar_anahtari(k):
    """68'in kararliligi (serit, red_sebebi) uzerinden sayar — AYNEN."""
    return (k[0], k[1])


def _gecilebilir_kumesi(env):
    return tuple(sorted((a[0], a[1]) for a in env["adaylar"]))


def _darbogaz_sirasi(env):
    """`_guven_hesapla`nin kullandigi siralama: gecilebilenler, darbogaz
    BUYUKTEN kucuge. Kazanan burada hesaplanmaz — yalniz siranin degisip
    degismedigi raporlanir."""
    gec = [a for a in env["adaylar"] if a[1]]
    return tuple(a[0] for a in sorted(gec, key=lambda a: -a[2]))


def _env_farklari(a, b):
    """Iki envanter arasinda NE degisti (E maddesi)."""
    f = []
    if a["n_kapi"] != b["n_kapi"]:
        f.append(f"n_kapi {a['n_kapi']}->{b['n_kapi']}")
    if a["bant_y"] != b["bant_y"]:
        f.append(f"bant_y {a['bant_y']}->{b['bant_y']}")
    if _gecilebilir_kumesi(a) != _gecilebilir_kumesi(b):
        f.append(f"gecilebilir {_gecilebilir_kumesi(a)}->{_gecilebilir_kumesi(b)}")
    if _darbogaz_sirasi(a) != _darbogaz_sirasi(b):
        f.append(f"darbogaz_sirasi {_darbogaz_sirasi(a)}->{_darbogaz_sirasi(b)}")
    if a["durum"] != b["durum"]:
        f.append(f"durum {a['durum']}->{b['durum']}")
    if a["yol_no"] != b["yol_no"]:
        f.append(f"yol_no {a['yol_no']}->{b['yol_no']}")
    return f


# ────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sigma", type=float, default=2.0,
                    help="Gauss gurultu sigmasi, 0-255 olceginde (68 ile ayni)")
    ap.add_argument("--tekrar", type=int, default=3)
    ap.add_argument("--tohum", type=int, default=7)
    ap.add_argument("--sinir", type=int, default=0,
                    help="yalniz ilk N kare (0 = hepsi) — SADECE deneme kosusu")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    rng = np.random.default_rng(args.tohum)

    n = 0
    kayitlar = []
    tutarsiz_kare = []
    maske_bozuldu = []

    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = args.kume / ornek["cikti"]
        mpp = ornek["arena"].get("mpp")
        if not p.is_file() or not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        if args.sinir and n >= args.sinir:
            break
        n += 1

        kosular = []
        for i in range(args.tekrar + 1):
            if i == 0:
                girdi = img
            else:
                # RNG akisi 68 ile BIREBIR: temiz kosu cekilis YAPMAZ,
                # ardindan kare basina `tekrar` cekilis yapilir.
                g = rng.normal(0.0, args.sigma, img.shape).astype(np.float32)
                girdi = np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8)

            mk, icerik = cikarim(model, girdi)
            imza_once = (int(mk[0].sum()), int(mk[1].sum()))
            kar = uretim_karari(mk, icerik, mpp)
            env = envanter(mk, icerik, mpp)
            imza_sonra = (int(mk[0].sum()), int(mk[1].sum()))
            if imza_once != imza_sonra:
                maske_bozuldu.append(f"{p.name}#{i} {imza_once}->{imza_sonra}")
            if not env["tutarli"]:
                tutarsiz_kare.append(f"{p.name}#{i}")

            kosular.append({
                "serit": kar[0], "red": kar[1], "guven": kar[2],
                "darbogaz_px": kar[3], "r_gerekli_px": kar[4], "env": env})

        kayitlar.append({"kare": p.name, "kosular": kosular})
        if n % 20 == 0:
            print(f"  ... {n} kare", flush=True)

    # ── COZUMLEME ──────────────────────────────────────────────────────────
    A = B = 0
    acik_temiz = 0
    durum_dagilimi = {}
    n_kapi_dagilimi = {}
    a_kareler, b_kareler = [], []
    env_ayni, env_degisti = 0, 0
    e_dokumu = []
    eb_dokumu = []

    for kayit in kayitlar:
        ks = kayit["kosular"]
        temiz, gurultulu = ks[0], ks[1:]

        durum_dagilimi[temiz["env"]["durum"]] = \
            durum_dagilimi.get(temiz["env"]["durum"], 0) + 1
        nk = temiz["env"]["n_kapi"]
        n_kapi_dagilimi[str(nk)] = n_kapi_dagilimi.get(str(nk), 0) + 1
        if temiz["env"]["durum"] == "ACIK":
            acik_temiz += 1

        kararlar = {_karar_anahtari((k["serit"], k["red"])) for k in ks}
        yol_nolari = {k["env"]["yol_no"] for k in ks}
        a_cevrildi = len(kararlar) > 1
        b_cevrildi = len(yol_nolari) > 1
        if a_cevrildi:
            A += 1
            a_kareler.append(kayit["kare"])
        if b_cevrildi:
            B += 1
            b_kareler.append(kayit["kare"])

        kayit["A_cevrildi"] = a_cevrildi
        kayit["B_cevrildi"] = b_cevrildi

        # (E-B) — ON KAYIT (B) dali icin: envanteri CEVIREN karelerde hangi
        # alan cevirdi? Emrin (E) maddesi "ENVANTER_DEGISTI kareler" der; kural
        # (B) atesledigi icin ayni dokum envanterin KENDI cevrilmelerine de
        # cikarilir, yoksa "hangi alan cevirdi" sorusu cevapsiz kalir.
        if b_cevrildi:
            b_farklar = []
            for k in gurultulu:
                if k["env"]["yol_no"] != temiz["env"]["yol_no"]:
                    b_farklar.extend(_env_farklari(temiz["env"], k["env"]))
            eb_dokumu.append({
                "kare": kayit["kare"],
                "env_yol_no": [k["env"]["yol_no"] for k in ks],
                "env_durum": [k["env"]["durum"] for k in ks],
                "uretim": [f"{k['serit']}/{k['red']}" for k in ks],
                "uretim_de_cevrildi": a_cevrildi,
                "degisenler": sorted(set(b_farklar))})

        if not a_cevrildi:
            continue

        # (C) — uretimi CEVIREN kosularda envanter ayni mi?
        ceviren = [k for k in gurultulu
                   if _karar_anahtari((k["serit"], k["red"])) !=
                   _karar_anahtari((temiz["serit"], temiz["red"]))]
        farklar = []
        for k in ceviren:
            farklar.extend(_env_farklari(temiz["env"], k["env"]))
        if farklar:
            env_degisti += 1
            kayit["C"] = "ENVANTER_DEGISTI"
            e_dokumu.append({"kare": kayit["kare"],
                             "uretim": [f"{k['serit']}/{k['red']}" for k in ks],
                             "env_yol_no": [k["env"]["yol_no"] for k in ks],
                             "env_durum": [k["env"]["durum"] for k in ks],
                             "degisenler": sorted(set(farklar))})
        else:
            env_ayni += 1
            kayit["C"] = "ENVANTER_AYNI"
            e_dokumu.append({"kare": kayit["kare"],
                             "uretim": [f"{k['serit']}/{k['red']}" for k in ks],
                             "env_yol_no": [k["env"]["yol_no"] for k in ks],
                             "env_durum": [k["env"]["durum"] for k in ks],
                             "degisenler": []})

    # ── RAPOR ──────────────────────────────────────────────────────────────
    c = "=" * 74
    print(f"\n{c}\nKORIDOR ENVANTERI KARARLILIGI · {args.model.name}")
    print(f"  gurultu Gauss sigma={args.sigma}/255 · kare basina {args.tekrar} "
          f"tekrar · tohum {args.tohum}\n  kume: {args.kume.name} · CONF={CONF}"
          f"\n{c}")
    print(f"  olculen kare : {n}")
    print(f"  (A) URETIM SERIDI cevrilen  : {A}/{n}   (D-142 referansi 8/260)")
    print(f"  (B) ENVANTER yol_no cevrilen: {B}/{n}")
    print(f"  (D) temiz kosuda durum=ACIK : {acik_temiz}/{n}")
    print("      durum dagilimi: " + " · ".join(
        f"{k}={v}" for k, v in sorted(durum_dagilimi.items(),
                                      key=lambda x: -x[1])))
    print(f"  (C) uretimi ceviren karelerde envanter: "
          f"AYNI={env_ayni} · DEGISTI={env_degisti}")
    print(f"  olcum kontrolu: rota_bul<->koridor_adaylari tutarsiz kosu "
          f"{len(tutarsiz_kare)} · maske bozulmasi {len(maske_bozuldu)}")
    if tutarsiz_kare[:5]:
        print("     tutarsiz: " + ", ".join(tutarsiz_kare[:5]))
    if maske_bozuldu[:5]:
        print("     bozulan : " + ", ".join(maske_bozuldu[:5]))

    print(f"\n{c}\n(E) URETIMI CEVIREN KARELER — kare kare\n{c}")
    for d in e_dokumu:
        print(f"  {d['kare']}")
        print(f"     uretim   : {' | '.join(d['uretim'])}")
        print(f"     env yol  : {d['env_yol_no']}")
        print(f"     env durum: {d['env_durum']}")
        if d["degisenler"]:
            for f in d["degisenler"]:
                print(f"     DEGISTI  : {f}")
        else:
            print("     DEGISTI  : (yok — envanter AYNI kaldi)")

    ortak = [k for k in a_kareler if k in b_kareler]
    print(f"\n{c}\n(E-B) ENVANTERI CEVIREN KARELER — kare kare\n{c}")
    for d in eb_dokumu:
        isaret = "  [URETIM DE CEVIRDI]" if d["uretim_de_cevrildi"] else ""
        print(f"  {d['kare']}{isaret}")
        print(f"     env yol  : {d['env_yol_no']}")
        print(f"     env durum: {d['env_durum']}")
        print(f"     uretim   : {' | '.join(d['uretim'])}")
        for f in d["degisenler"]:
            print(f"     DEGISTI  : {f}")

    print(f"\n{c}\nORTUSME\n{c}")
    print(f"  (A) uretim ceviren : {len(a_kareler)}  -> {', '.join(a_kareler)}")
    print(f"  (B) envanter ceviren: {len(b_kareler)} -> {', '.join(b_kareler)}")
    print(f"  ORTAK: {len(ortak)} -> {', '.join(ortak) if ortak else '(yok)'}")
    print(f"  BIRLESIM: {len(set(a_kareler) | set(b_kareler))}")
    # NOT: `⚠` gibi cp1254 disi karakter BASILMAZ (T85'te UnicodeEncodeError
    # yasandi); ekran metni ASCII, yalniz `·` (cp1254'te var) kullanilir.
    print("  [!] (C) tanimi geregi 'ceviren kosu' yalniz URETIMI ceviren kosudur;")
    print("    envanter BASKA bir kosuda cevirmisse kare yine ENVANTER_AYNI")
    print("    siniflanir. Ortak karelerde bu fark GORUNMEZ kalir — yukaridaki")
    print("    (E-B) dokumu bu korlugu kapatmak icin vardir.")
    print(f"\n  temiz kosuda n_kapi dagilimi: " + " · ".join(
        f"{k}={v}" for k, v in sorted(n_kapi_dagilimi.items())))
    print(f"  (envanterin 'ACIK' verebilmesi icin n_kapi==3 SARTTIR)")

    # ── ON KAYIT KURALININ UYGULANMASI ────────────────────────────────────
    print(f"\n{c}\nON KAYIT KURALI (kosmadan once yazildi) — UYGULAMA\n{c}")
    if abs(A - 8) > 1:
        print(f"  (C) IRAKSAMA: A={A}/{n}, D-142'nin 8/260'indan ±1'den fazla "
              f"sapti. Bu kosu D-142 ile KIYASLANAMAZ; diger sonuclar "
              f"RAPOR EDILMEZ.")
    else:
        print(f"  (C) A={A}/{n} — D-142 ile tutarli (8 ± 1). Kiyas gecerli.")
        if B > 4:
            print(f"  (B) B={B}/{n} > 4 -> ENVANTER DE KARARSIZ. Fix YAZILMAZ.")
        elif acik_temiz >= 255:
            print(f"  (A) B={B}/{n} <= 4 VE D={acik_temiz}/{n} >= 255 -> "
                  f"envanter YETERINCE KARARLI. Yon: secimi envantere baglamak. "
                  f"FIX YINE DE YAZILMAZ (tasarim mimarindir).")
        else:
            print(f"  (D) D={acik_temiz}/{n} < 255 -> B={B}/{n} ne olursa olsun "
                  f"envantere baglamak KAZANC DEGILDIR: {n - acik_temiz} karede "
                  f"envanter zaten karar veremiyor, {A} karelik kararsizlik icin "
                  f"bu yetenek odenmez.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "model": str(args.model), "kume": str(args.kume),
            "sigma": args.sigma, "tekrar": args.tekrar, "tohum": args.tohum,
            "conf": CONF, "n": n,
            "A_uretim_cevrilen": A, "B_envanter_cevrilen": B,
            "D_acik_temiz": acik_temiz, "durum_dagilimi": durum_dagilimi,
            "n_kapi_dagilimi": n_kapi_dagilimi,
            "C_envanter_ayni": env_ayni, "C_envanter_degisti": env_degisti,
            "A_kareler": a_kareler, "B_kareler": b_kareler,
            "ortak_kareler": ortak,
            "E_dokumu": e_dokumu, "EB_dokumu": eb_dokumu,
            "kontrol_tutarsiz": tutarsiz_kare,
            "kontrol_maske_bozuldu": maske_bozuldu,
            "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()

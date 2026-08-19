"""T111 · ALAN DISI DOGRULAMA KUMESI VAR MI? — ENVANTER (olcum DEGIL).

NEDEN. Bugune kadarki BUTUN kabul olcumleri egitim dagiliminin ICINDE yapildi.
PC garantiye gidecek; yerel veri gidince bu envanter BIR DAHA CIKARILAMAZ.

NE YAPAR:
  1. `dataset/` ve `data/` altindaki her goruntu kumesini listeler.
  2. `dataset/*.yaml` icindeki her train/val yolunu COZER — goreceli yollar
     yaml'in KENDI konumuna gore cozulur (Ultralytics `path` anahtari varsa
     once o taban alinir), TAHMIN EDILMEZ.
  3. Uyelik matrisi uretir: kume x yaml -> results/t111_bakirlik_envanteri/
     ozet.json + insan okunur ozet (stdout).
  4. Hicbir yaml'a girmemis kume icin: KAC KARE, kaynak, ETIKETI VAR MI.
     ⚠ Etiketsiz kume "bakir dogrulama kumesi" DEGILDIR — olcum yapilamaz.

MIMARIN KISITLARI (uygulanir, tartisilmaz):
  · KAPI YAPILMAZ — bakir kume bulunsa bile esik OLCULMEDEN kapiya cevrilmez.
  · copy_paste_gercek / raw_frames / sentetik_arena / kadraj_t66 BAKIR
    DEGILDIR (karisim_t54_engelli.yaml:25 dogrulandi) — yeniden tartisilmaz.
  · "Bakir kume YOK" da bir BULGUDUR; oyle cikarsa oyle yazilir.
  · v34 terfisi bu gorevle GERI ALINMAZ.

⚠ YAML AYRISTIRMA: pyyaml KULLANILMAZ (yasak listesinde degil ama bagimlilik
eklememek icin) — karisim yaml'lari basit `anahtar:` + `  - yol` bicimindedir;
satir tabanli ayristirici yeterlidir ve NE ANLADIGINI json'a yazar, sessiz
atlama yapmaz (`cozulemeyen` listesi).
"""
import json
import sys
from pathlib import Path

from ayarlar import REPO

SONUC_DIZINI = REPO / "results" / "t111_bakirlik_envanteri"
GORUNTU_UZANTILARI = {".jpg", ".jpeg", ".png", ".bmp"}


def goruntu_koku_mu(d: Path) -> bool:
    return any(p.suffix.lower() in GORUNTU_UZANTILARI
               for p in d.rglob("*") if p.is_file())


def kume_bul():
    """`dataset/` ve `data/` altindaki BIRINCI SEVIYE goruntu kumeleri."""
    kumeler = {}
    for kok in (REPO / "dataset", REPO / "data"):
        for d in sorted(p for p in kok.iterdir() if p.is_dir()):
            gorseller = [p for p in d.rglob("*")
                         if p.is_file() and p.suffix.lower() in GORUNTU_UZANTILARI]
            etiketler = [p for p in d.rglob("*.txt")
                         if p.is_file() and "labels" in p.parts]
            kumeler[f"{kok.name}/{d.name}"] = {
                "yol": str(d),
                "goruntu": len(gorseller),
                "etiket_txt": len(etiketler),
                "etiketli_mi": len(etiketler) > 0,
            }
    return kumeler


def yaml_yollari(yaml_yolu: Path):
    """train/val altindaki yollari coz. -> (cozulen[], cozulemeyen[])."""
    cozulen, cozulemeyen = [], []
    taban = yaml_yolu.parent
    path_taban = None
    aktif = None
    for ham in yaml_yolu.read_text(encoding="utf-8").splitlines():
        satir = ham.split("#", 1)[0].rstrip()
        if not satir.strip():
            continue
        if satir.startswith("path:"):
            aday = satir.split(":", 1)[1].strip()
            path_taban = Path(aday) if aday else None
            continue
        if satir.startswith(("train:", "val:", "test:")):
            anahtar, kalan = satir.split(":", 1)
            aktif = anahtar.strip()
            kalan = kalan.strip()
            if kalan:                                  # tek satirlik deger
                _ekle(kalan, taban, path_taban, aktif, cozulen, cozulemeyen)
                aktif = None
            continue
        if aktif and satir.lstrip().startswith("- "):
            _ekle(satir.lstrip()[2:].strip(), taban, path_taban, aktif,
                  cozulen, cozulemeyen)
            continue
        if aktif and not satir.startswith(" "):
            aktif = None                               # blok bitti
    return cozulen, cozulemeyen


def _ekle(deger, taban, path_taban, bolum, cozulen, cozulemeyen):
    p = Path(deger)
    if not p.is_absolute():
        # Ultralytics kurali: once `path:` tabani, yoksa yaml'in konumu.
        p = (Path(path_taban) / deger) if path_taban else (taban / deger)
    kayit = {"bolum": bolum, "ham": deger, "cozulen": str(p),
             "var": p.exists()}
    (cozulen if p.exists() else cozulemeyen).append(kayit)


def kume_eslestir(kumeler, yol: str):
    """Cozulmus bir yolu kume adina esle (yol, kumenin ALTINDA mi)."""
    eslesen = []
    for ad, k in kumeler.items():
        kok = Path(k["yol"]).resolve()
        try:
            Path(yol).resolve().relative_to(kok)
            eslesen.append(ad)
        except ValueError:
            pass
    return eslesen


def main():
    kumeler = kume_bul()
    yamllar = sorted((REPO / "dataset").glob("*.yaml"))

    matris = {ad: {} for ad in kumeler}
    yaml_dokumu = {}
    tum_cozulemeyen = {}
    for y in yamllar:
        cozulen, cozulemeyen = yaml_yollari(y)
        yaml_dokumu[y.name] = {"cozulen": cozulen, "cozulemeyen": cozulemeyen}
        if cozulemeyen:
            tum_cozulemeyen[y.name] = cozulemeyen
        for kayit in cozulen:
            for kume_adi in kume_eslestir(kumeler, kayit["cozulen"]):
                matris[kume_adi].setdefault(y.name, []).append(kayit["bolum"])

    hic_girmemis = {ad: k for ad, k in kumeler.items() if not matris[ad]}

    c = "=" * 78
    print(f"\n{c}\nT111 · BAKIRLIK ENVANTERI — kume x yaml uyelik matrisi\n{c}")
    print(f"  kume sayisi: {len(kumeler)} · yaml sayisi: {len(yamllar)}")
    print(f"\n  {'kume':34s}{'goruntu':>8s}{'etiket':>8s}  giren yaml'lar")
    for ad, k in kumeler.items():
        uye = sorted(matris[ad])
        print(f"  {ad:34s}{k['goruntu']:>8d}{k['etiket_txt']:>8d}  "
              + (", ".join(uye) if uye else "🔴 HICBIRI"))

    print(f"\n{c}\nHICBIR YAML'A GIRMEMIS KUMELER ({len(hic_girmemis)})\n{c}")
    for ad, k in hic_girmemis.items():
        durum = ("ETIKETLI — olcum ADAYI olabilir" if k["etiketli_mi"]
                 else "ETIKETSIZ — 'bakir dogrulama kumesi' DEGILDIR, "
                      "olcum YAPILAMAZ")
        print(f"  {ad:34s}{k['goruntu']:>6d} kare · {k['etiket_txt']} etiket · {durum}")

    if tum_cozulemeyen:
        print(f"\n{c}\nCOZULEMEYEN YAML YOLLARI (dosya diskte YOK)\n{c}")
        for y, kayitlar in tum_cozulemeyen.items():
            for k in kayitlar:
                print(f"  {y}: [{k['bolum']}] {k['ham']} -> {k['cozulen']}")

    SONUC_DIZINI.mkdir(parents=True, exist_ok=True)
    hedef = SONUC_DIZINI / "ozet.json"
    hedef.write_text(json.dumps({
        "betik": Path(__file__).name,
        "not": ("ENVANTERDIR, OLCUM DEGIL. Kapi YAPILMAZ (mimarin kisiti); "
                "etiketsiz kume bakir dogrulama kumesi DEGILDIR."),
        "kumeler": kumeler,
        "yamllar": {y.name: yaml_dokumu[y.name] for y in yamllar},
        "matris": {ad: sorted(m) for ad, m in matris.items()},
        "hicbir_yamla_girmemis": {
            ad: {**k, "olcum_adayi_mi": k["etiketli_mi"]}
            for ad, k in hic_girmemis.items()},
        "cozulemeyen": tum_cozulemeyen,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\njson -> {hedef}")


if __name__ == "__main__":
    main()

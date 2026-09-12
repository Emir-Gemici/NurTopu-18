# -*- coding: utf-8 -*-
"""T240 (D-460 karar 2 · D-465) — KACAN 31 MUTANTIN yeniden kurulup DUSURULDUGUNUN kaniti.

T240-B (D-460 hukmu, bagimsiz curutucu) 9 mutant EKLEDI: Y4/Y4b (HTML varlik
bicimi), Y7a/b/c (kalin baslik TASIMAYAN celiskili hukum paragrafi, uc AYRI
yerde), Y5 (aile disi es anlamli), Y10 (esik birimi s->ms), Y11 (anahtar
sozcuksuz README celiskisi) ve D461 (ikinci gevsetilmis kabul olcutu).

T240-C (D-465 hukmu, IKINCI bagimsiz curutucu) 3 mutant EKLEDI: X15/X16/X17 —
`&#96;` (backtick'in HTML varlik bicimi) ile kurulan SAHTE KOD ARALIGI. T240-B'nin
duzeltmesi `&#96;`'i cozup kod araligi saniyordu ve icindeki cizigi taramadan
tamamen gizliyordu; oysa CommonMark/GFM'de varlik referansi YAPI URETMEZ (okuyucuda
`&#96;` duz backtick KARAKTERIDIR, kod araligi ACMAZ; icindeki `~~` cizgiyi ACAR).
Bu bir GERILEMEYDI: ayni girdi T240-B ONCESI (64b60ae5) yakalaniyordu.

Bagimsiz mimar denetimi (D-460) uc isi REDDETTI; ortak gerekce belge kilitlerinin
yalniz `~~...~~` ayiklamasiydi ve 19 gercek dosya mutasyonunun 19'u kacmisti:
  T226 (CONTRACTS.md §6.8)        : D1b <del>, D1c tek tilde, D1d <s>, D1e celiskili ikinci hukum
  T228 (GOSTERICI_KURULUM.md)     : A3 tek tilde, A4 <del>, A5 <s>, A6 sayi yaziyla,
                                    A7 "en az", A8 "teyit edildi", A9 "asan"
  T221 (config/pixhawk/README.md) : W1 ~OLCULEMEDI~, W6 ~OLCULEMEDI~+KANITLANDI, W2 KANITLANDI,
                                    W3 _dogrulandi_, W4 __kosuldu__, W7 "sorunsuz tamamlandi",
                                    V1 numarasiz celiskili hukum, V3 ikinci "Sonuc" cumlesi

Bu kosucu her mutasyonu TEK TEK gercek dosyaya yazar, ilgili suiti GERCEKTEN kosar,
sonra dosyayi sha256 ile BAYT-ES geri yukler. Ayrica denetimde ZATEN DUSEN kontrol
mutantlari (D1 cift tilde, D1f tipografik tirnak, W5 duz DOGRULANDI, W8 duz GECTI)
da kosulur: kosucunun kendisi saglam mi, mutasyonsuz taban yesil mi olculur.

Kullanim (depo kokunden):
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 -B \\
      results/fdr_sprint_20260910/T240/mutasyon_t240.py
Cikis 0 = her KACAN mutant DUSTU ve her dosya bayt-es geri yuklendi.
"""

import hashlib
import io
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = Path(__file__).resolve().parent
PY = sys.executable

SOZLESME = "CONTRACTS.md"
KURULUM = "jetson_paket/gosterici/GOSTERICI_KURULUM.md"
README = "config/pixhawk/README.md"
ON_KAYIT_T235 = "results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md"

MK15 = "test_yks_mk15_hakem_ekrani.py"
GOSTERICI = "test_isaretli_gosterici.py"
ARDUPLANE = "test_faz_b_arduplane_sablon.py"
T235 = "test_t235_alan_etiketi.py"

# ── mutasyon capalari (her biri ilgili dosyada TAM 1 kez gecer) ────────────────
C_KAYNAK = ("**`KAMERA_KANIT.kaynak` (T226 · D-443, 10 Eylül):** `kaynak` = kare URL'si "
            "[+ ` [<etiket>]`] — `yks_gui --kamera-etiket` verildiyse "
            "`\"http://127.0.0.1:8080/kare.jpg [MK15 · HDMI · yakalama]\"` biçimi "
            "(`yks_gui.kamera_kanit_kaynagi`), verilmediyse yalnız URL, URL yoksa `null`; "
            "video karar üretmez, hakem onayı telsiz verisine verilir (§6.7).")
C_D1E = ("\n\n**GEÇERSİZ (12 Eylül):** yukarıdaki kaynak biçimi KALDIRILDI; kaynak artık yalnız "
         "null yazılır ve etiket sözleşmesi YOKTUR.")

K_A3 = "**`-v` nabız satırı biçimi Jetson'da ÖLÇÜLEMEDİ — DOĞRULANACAK**"
K_A4 = "- Dönüştürücünün canlı kodeki (H.264/H.265 çelişkili)."
K_A5 = "**hiçbiri Jetson'da koşulmadı**"
K_CAPA = "- **Geri alma:**"      # §5'in son maddesi; yeni "saha kurali" maddeleri bunun ONUNE girer

R_BASLIK = "### 6.6 SITL provası — ÖLÇÜLEMEDİ (bu makine, 10 Eylül)"
R_CAPA = "ön hükümle kaydedilir."   # SS6.6 GOVDESI (on kayitli kabul/on hukum bloklarinin DISI)

# ── T240-B capalari: bagimsiz curutucunun (D-460 hukmu) kacan mutantlari ──────
C_Y4_CAPA = "maliyeti 2 satır/dk'dır."
C_Y4 = "".join(h + "&#822;" for h in "maliyeti") + " 2 satır/dk'dır."
C_Y4B = "m&#x336;aliyeti 2 satır/dk'dır."
C_Y7 = ("Not (12 Eylül): `kaynak` alanı artık zorunlu değildir; etiket biçimi bağlayıcı "
        "sayılmaz ve her durumda `null` yazılabilir.")
SOZLESME_KAYNAK_BASI_C = "**`KAMERA_KANIT.kaynak` (T226 · D-443, 10 Eylül):**"
C_ILKELER = "**Bağlayıcı ilkeler:**"
C_SON_PARAGRAF = "`tests/test_yks_hakem_kaydi.py` `HakemKaydi`nin kendi dayanıklılık kapısıdır"

K_Y5 = ("- **Saha kuralı (12 Eylül):** `-v` nabız satırı biçimi sahada **hatasız yürüdü**; "
        "kip **kusursuz işledi**.\n")
K_Y10_ESKI = "ölen GÖRÜNTÜ YOK borusu ≥ 3 s"
K_Y10_YENI = "ölen GÖRÜNTÜ YOK borusu ≥ 3000 ms"

O_CAPA = "insanca doğrulanır (BEYAN)."
O_D461 = ("\n- **T236 SITL kapısı (gözden geçirilmiş):** ≤ 4,0 m · ±15° · ≥ %70 · ±3,0 m")

# ── T240-C capalari: IKINCI bagimsiz curutucunun (D-465 hukmu) kacan mutantlari ──
# X15/X16/X17: `&#96;` (backtick'in HTML varlik bicimi) ile SAHTE KOD ARALIGI. T240-B'nin
# ilk surumu `&#96;`'i cozup kod araligi saniyor, icindeki cizik taramadan tamamen
# gizleniyordu; okuyucuda ise `&#96;` duz backtick KARAKTERIDIR (CommonMark/GFM'de varlik
# YAPI URETMEZ), kod araligi ACMAZ ve icindeki `~~` cizgiyi ACAR. Yani hukum belgede USTU
# CIZILI gorunurken testte YURURLUKTE sayiliyordu. Ucu de GOSTERICI_KURULUM §9'a (OLCULEMEDI
# / ACIK listesi) kuruldu.
K_X16_CAPA = ("- `gst-launch-1.0 -v` nabız satırı biçimi (DRM gözetmeninin boru ilerlemesi "
              "denetimi) ve `identity`'nin boruya etkisi, `-v` satırlarının zamanında "
              "gelmesi / `stdbuf -oL` (T228-D).")

#: (ad, sinif, dosya, eski, yeni, suit) — sinif: "KACAN" (19) ya da "KONTROL" (denetimde dusenler)
MUTANTLAR = (
    # ── T226 · CONTRACTS §6.8 ────────────────────────────────────────────────
    ("D1  cift tilde", "KONTROL", SOZLESME, C_KAYNAK, "~~" + C_KAYNAK + "~~", MK15),
    ("D1b <del>", "KACAN", SOZLESME, C_KAYNAK, "<del>" + C_KAYNAK + "</del>", MK15),
    ("D1c tek tilde", "KACAN", SOZLESME, C_KAYNAK, "~" + C_KAYNAK + "~", MK15),
    ("D1d <s>", "KACAN", SOZLESME, C_KAYNAK, "<s>" + C_KAYNAK + "</s>", MK15),
    ("D1e celiskili ikinci hukum", "KACAN", SOZLESME, C_KAYNAK, C_KAYNAK + C_D1E, MK15),
    ("D1f tipografik tirnak", "KONTROL", SOZLESME,
     "`\"http://127.0.0.1:8080/kare.jpg [MK15 · HDMI · yakalama]\"`",
     "`\u201chttp://127.0.0.1:8080/kare.jpg [MK15 · HDMI · yakalama]\u201d`", MK15),

    # ── T228 · GOSTERICI_KURULUM.md ──────────────────────────────────────────
    ("A3 tek tilde", "KACAN", KURULUM, K_A3, "~" + K_A3 + "~", GOSTERICI),
    ("A4 <del>", "KACAN", KURULUM, K_A4, "<del>" + K_A4 + "</del>", GOSTERICI),
    ("A5 <s>", "KACAN", KURULUM, K_A5, "<s>" + K_A5 + "</s>", GOSTERICI),
    ("A6 sayi yaziyla", "KACAN", KURULUM, K_CAPA,
     "- **Saha kuralı (12 Eylül):** çırpınmayı azaltmak için videoya dönüş **bir** ardışık "
     "taze yoklamayla yapılır.\n" + K_CAPA, GOSTERICI),
    ("A7 'en az' ile esik gevsetme", "KACAN", KURULUM, K_CAPA,
     "- **Saha kuralı (12 Eylül):** boru başlatma aralığı sahada **en az 1 saniye** alınır.\n"
     + K_CAPA, GOSTERICI),
    ("A8 'teyit edildi' / 'basarili'", "KACAN", KURULUM, K_CAPA,
     "- **12 Eylül:** `-v` nabız satırı biçimi Jetson'da **teyit edildi**, saha koşumu "
     "**başarılı**.\n" + K_CAPA, GOSTERICI),
    ("A9 'asan' ile donma esigi", "KACAN", KURULUM, K_CAPA,
     "- **Saha kuralı (12 Eylül):** video borusu **6 saniyeyi aşan** süre tampon geçirmezse "
     "GÖRÜNTÜ YOK'a düşülür.\n" + K_CAPA, GOSTERICI),

    # ── T221 · config/pixhawk/README.md §6.6 ─────────────────────────────────
    ("W1 baslikta ~OLCULEMEDI~", "KACAN", README, R_BASLIK,
     "### 6.6 SITL provası — ~ÖLÇÜLEMEDİ~ (bu makine, 10 Eylül)", ARDUPLANE),
    ("W6 ~OLCULEMEDI~ + KANITLANDI", "KACAN", README, R_BASLIK,
     "### 6.6 SITL provası — ~ÖLÇÜLEMEDİ~ · prova KANITLANDI (bu makine, 10 Eylül)", ARDUPLANE),
    ("W2 KANITLANDI", "KACAN", README, R_CAPA,
     R_CAPA + " SITL prova sonucu: KANITLANDI.", ARDUPLANE),
    ("W3 _dogrulandi_", "KACAN", README, R_CAPA,
     R_CAPA + " SITL prova sonucu: _doğrulandı_.", ARDUPLANE),
    ("W4 __kosuldu__", "KACAN", README, R_CAPA,
     R_CAPA + " SITL prova sonucu: __koşuldu__.", ARDUPLANE),
    ("W7 'sorunsuz tamamlandi'", "KACAN", README, R_CAPA,
     R_CAPA + " SITL provası sorunsuz tamamlandı; ölçütler sağlanmış durumdadır.", ARDUPLANE),
    ("V1 numarasiz celiskili hukum", "KACAN", README, R_CAPA,
     R_CAPA + " Bu koşullardan biri tutmasa da prova kabul edilir; liste sonradan "
     "genişletilebilir.", ARDUPLANE),
    ("V3 ikinci 'Sonuc' cumlesi", "KACAN", README, R_CAPA,
     R_CAPA + " **Sonuç (11 Eylül): SITL zinciri yerinde; prova kapıları sorun çıkarmadı.**",
     ARDUPLANE),
    ("W5 duz DOGRULANDI", "KONTROL", README, R_CAPA,
     R_CAPA + " SITL prova sonucu: DOĞRULANDI.", ARDUPLANE),
    ("W8 duz GECTI", "KONTROL", README, R_CAPA,
     R_CAPA + " SITL provası GEÇTİ.", ARDUPLANE),

    # ── T240-B: BAGIMSIZ CURUTUCUNUN (D-460 hukmu) KACAN MUTANTLARI ──────────
    # Y4  : U+0336'nin HTML VARLIK bicimi. Ciplak hali (Y3) DUSUYORDU, varlik hali KACTI.
    ("Y4  &#822; harf harf", "KACAN", SOZLESME, C_Y4_CAPA, C_Y4, MK15),
    ("Y4b &#x336; onaltilik", "KACAN", SOZLESME, C_Y4_CAPA, C_Y4B, MK15),
    # Y7  : kalin baslik TASIMAYAN, kaynak paragrafinin ardina DEGIL baska yere konan
    #       celiskili hukum paragrafi. Uc AYRI yere ayri ayri sokuldu (curutucunun istegi).
    ("Y7a celiskili paragraf (kaynak onu)", "KACAN", SOZLESME,
     SOZLESME_KAYNAK_BASI_C, C_Y7 + "\n\n" + SOZLESME_KAYNAK_BASI_C, MK15),
    ("Y7b celiskili paragraf (ilkeler onu)", "KACAN", SOZLESME,
     C_ILKELER, C_Y7 + "\n\n" + C_ILKELER, MK15),
    ("Y7c celiskili paragraf (son paragraf onu)", "KACAN", SOZLESME,
     C_SON_PARAGRAF, C_Y7 + "\n\n" + C_SON_PARAGRAF, MK15),
    # Y5  : olumlu hukum ailesinin DISINDA es anlamli ("hatasiz yurudu / kusursuz isledi").
    ("Y5  aile disi es anlamli", "KACAN", KURULUM, K_CAPA, K_Y5 + K_CAPA, GOSTERICI),
    # Y10 : esik BIRIM kaydirmasi; G8'in "≥ N s" kalibi "ms" bicimini HIC gormuyordu.
    ("Y10 esik birimi s -> ms", "KACAN", KURULUM, K_Y10_ESKI, K_Y10_YENI, GOSTERICI),
    # Y11 : anahtar sozcuksuz README celiskisi; kapali kumenin SECICISI dardi.
    ("Y11 anahtarsiz README celiskisi", "KACAN", README, R_CAPA,
     R_CAPA + " Zincir yerinde; kapılar sorun çıkarmadı.", ARDUPLANE),
    # D-461: ON KAYIT TEKLIGI — ikinci ve GEVSETILMIS kabul olcutu (T236-B curutucusu).
    ("D461 ikinci gevsetilmis olcut", "KACAN", ON_KAYIT_T235, O_CAPA, O_CAPA + O_D461, T235),

    # ── T240-C: IKINCI BAGIMSIZ CURUTUCUNUN (D-465 hukmu) KACAN MUTANTLARI ───
    # X15 : `&#96;~~...~~&#96;` — sahte kod araligi, ICI cizili (§9 kodek maddesi).
    ("X15 &#96; sarmali ~~cizik~~", "KACAN", KURULUM, K_A4,
     "- &#96;~~" + K_A4[2:] + "~~&#96;", GOSTERICI),
    # X16 : ayni sinif, §9'un `-v` nabiz maddesinde (baska bir OLCULEMEDI maddesi).
    ("X16 &#96; sarmali nabiz maddesi", "KACAN", KURULUM, K_X16_CAPA,
     "- &#96;~~" + K_X16_CAPA[2:] + "~~&#96;", GOSTERICI),
    # X17 : ayni sinif, cizik HTML etiketiyle: `&#96;<s>...</s>&#96;`.
    ("X17 &#96; sarmali <s>cizik</s>", "KACAN", KURULUM, K_A4,
     "- &#96;<s>" + K_A4[2:] + "</s>&#96;", GOSTERICI),
)


def sha(yol):
    return hashlib.sha256(Path(yol).read_bytes()).hexdigest()


def suit_kos(desen):
    p = subprocess.run([PY, "-X", "utf8", "-B", "-m", "unittest", "discover",
                        "-s", "tests", "-p", desen, "-q"],
                       cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    kayit = io.StringIO()

    def yaz(s=""):
        print(s)
        kayit.write(s + "\n")

    yaz("# T240 mutasyon kaniti — KACAN 31 mutant + 4 kontrol")
    yaz("#   19'u D-460 mimar denetiminin, 9'u (Y4/Y4b/Y7a-c/Y5/Y10/Y11/D461)")
    yaz("#   T240-B'ye, 3'u (X15/X16/X17) T240-B'ye RED veren IKINCI bagimsiz")
    yaz("#   curutucunun (D-465) kacan mutantidir.")
    yaz("# yorumlayici: {}".format(PY))
    yaz("# depo koku : {}".format(KOK))
    yaz()

    suitler = sorted({m[5] for m in MUTANTLAR})
    yaz("## 0. Mutasyonsuz TABAN")
    taban_ok = True
    for s in suitler:
        rc, cikti = suit_kos(s)
        son = [x for x in cikti.strip().splitlines() if x.strip()][-1:]
        yaz("  {:<38} cikis={}  {}".format(s, rc, son[0] if son else ""))
        taban_ok &= (rc == 0)
    yaz("  TABAN: {}".format("YESIL" if taban_ok else "KIRMIZI"))
    yaz()

    yaz("## 1. Mutasyonlar (her biri gercek dosyaya yazildi, suit kosuldu, sha256 ile geri alindi)")
    kacan_toplam = kacan_dusen = 0
    kontrol_toplam = kontrol_dusen = 0
    geri_yukleme_ok = True
    for ad, sinif, goreli, eski, yeni, suit in MUTANTLAR:
        yol = KOK / goreli
        ham = yol.read_bytes()
        once = hashlib.sha256(ham).hexdigest()
        metin = ham.decode("utf-8")
        adet = metin.count(eski)
        if adet != 1:
            yaz("  {:<34} CAPA HATASI: {} kez bulundu".format(ad, adet))
            geri_yukleme_ok = False
            continue
        yol.write_bytes(metin.replace(eski, yeni, 1).encode("utf-8"))
        try:
            rc, _ = suit_kos(suit)
        finally:
            yol.write_bytes(ham)
        sonra = hashlib.sha256(yol.read_bytes()).hexdigest()
        bayt_es = (once == sonra)
        geri_yukleme_ok &= bayt_es
        hukum = "DUSTU" if rc != 0 else "KACTI"
        if sinif == "KACAN":
            kacan_toplam += 1
            kacan_dusen += rc != 0
        else:
            kontrol_toplam += 1
            kontrol_dusen += rc != 0
        yaz("  [{}] {:<34} {:<32} cikis={} -> {:<6} geri_bayt_es={} sha={}"
            .format("KACAN" if sinif == "KACAN" else "kontr", ad, goreli.split("/")[-1],
                    rc, hukum, bayt_es, sonra[:12]))

    yaz()
    yaz("## 2. OZET")
    yaz("  KACAN mutantlar   : {}/{} DUSTU".format(kacan_dusen, kacan_toplam))
    yaz("  KONTROL mutantlar : {}/{} DUSTU".format(kontrol_dusen, kontrol_toplam))
    yaz("  geri yukleme      : {}".format("hepsi bayt-es" if geri_yukleme_ok else "BOZUK"))
    basarili = (taban_ok and geri_yukleme_ok
                and kacan_dusen == kacan_toplam == 31
                and kontrol_dusen == kontrol_toplam)
    yaz("  HUKUM             : {}".format("GECTI" if basarili else "DUSTU"))

    CIKTI.mkdir(parents=True, exist_ok=True)
    (CIKTI / "mutasyon_ciktisi.txt").write_text(kayit.getvalue(), encoding="utf-8")
    return 0 if basarili else 1


if __name__ == "__main__":
    sys.exit(main())

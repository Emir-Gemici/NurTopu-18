"""AKIS-D mutasyon kontrolu: her yeni kilit GERCEK dosya mutasyonuyla yakalaniyor mu.

Her mutant scripts/akis_satir_tazele.py ya da scripts/akis_diyagram_dogrula.py
icinde TEKIL bir satiri degistirir, tests/test_akis_kapsam_korumasi.py kosulur,
dosya BAYT-ES geri yuklenir (sha256 karsilastirilir). Yakalanmayan mutant = kacan.
AKIS-D2 (curutucu RED): M21-M25 curutucunun KACAN N1/N2/N3/N4 mutasyonlari (+ N2b capa),
M26-M34 taban suphesi (KUSUR-1), M35 goreli --mmd; M36-M41 EK (T226-D bulgusu: alt-grafik
basliklari / tek desen / bicim bayt-es / def basligi). M02/M09/M10 metni yeni koda
uyarlandi (capa, damga, dugum_ayikla).
AKIS-D2 2. RED (curutucu KUSUR-A + kacan Y2/Y3/Y14/Y16/X1/X4/Y10): M42-M44 ikinci tabanin
DUGUM BASINA `git blame` ile alinmasi (dosya duzeyi L, blame satir eslemesi, blame'in
tabandan okunmasi), M45-M52 sinir/durum kilitleri. M28/M29/M33 metni yeni koda uyarlandi
(dosya duzeyi L kaldirildi). Kacmasi BEKLENEN tek mutant yok; curutucunun X8'i (L == sha
iken de ikinci taban) yeni kodda zaten yapiyi geregi olanaksiz — `koken != sha` kosulu.
GPU yok, model yok. Kullanim: python mutasyon_akis_d.py  (cikti stdout)
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEPO = Path(__file__).resolve().parents[3]
PY = sys.executable
TAZELE = DEPO / "scripts" / "akis_satir_tazele.py"
DOGRULA = DEPO / "scripts" / "akis_diyagram_dogrula.py"
TEST = "test_akis_kapsam_korumasi.py"

# M42: dugum basina blame → dosya duzeyi "son commit" (KUSUR-A'nin ta kendisi)
BLAME_ESKI = '''    r = subprocess.run(["git", "-C", str(kok), "blame", "--porcelain", ref, "--", yol],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return {}
    kokenler = {}
    for s in r.stdout.split("\\n"):
        m = RE_BLAME.match(s.rstrip("\\r"))
        if m:
            sha, ilk, adet = m.group(1), int(m.group(3)), int(m.group(4) or 1)
            for k in range(adet):
                kokenler[ilk + k] = sha
    return kokenler'''
BLAME_DOSYA_DUZEYI = '''    r = subprocess.run(["git", "-C", str(kok), "log", "-1", "--format=%H", ref, "--", yol],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    son = r.stdout.strip()
    if r.returncode != 0 or not son:
        return {}
    n = len((taban_icerigi(kok, ref, yol) or "").split("\\n"))
    return {k: son for k in range(1, n + 1)}'''

# (ad, dosya, [(eski, yeni), ...], beklenen dusen testlerden en az biri)
MUTANTLAR = [
    ("M01 tazele: kapsam kisiti kaldirildi (tum dosyada ara)", TAZELE,
     [("    adaylar = adaylari_bul(ds_c, hc.satirlari(kt), parcalar)",
       "    adaylar = adaylari_bul(ds_c, range(1, len(ds_c) + 1), parcalar)")],
     ["test_f1_icine_ekleme", "test_f1_den_metin_silinirse"]),
    ("M02 tazele: ESKI algoritma (tum dosya + eski satira mutlak en yakin)", TAZELE,
     [("    adaylar = adaylari_bul(ds_c, hc.satirlari(kt), parcalar)",
       "    adaylar = adaylari_bul(ds_c, range(1, len(ds_c) + 1), parcalar)"),
      ("    beklenen = hc.capa(kt) + (t_satir - ht.capa(kt))",
       "    beklenen = eski")],
     ["test_f1_ustune_ekleme", "test_f1_icine_ekleme", "test_tazele_baslik_kendi_sinifinin"]),
    ("M03 tazele: kapsam tabandan degil calisma agacindan", TAZELE,
     [("    kt = ht.kapsam(t_satir)", "    kt = hc.kapsam(t_satir) or ht.kapsam(t_satir)")],
     ["test_f1_ustune_ekleme"]),
    ("M04 tazele: esitlik denetimi kaldirildi", TAZELE,
     [("    if len(sirali) > 1 and abs(sirali[0] - beklenen) == abs(sirali[1] - beklenen):",
       "    if False:")],
     ["test_esit_uzak_iki_aday"]),
    ("M05 tazele: tabanda metin denetimi kaldirildi", TAZELE,
     [("    pencere = range(max(1, eski - tolerans), min(len(satirlar), eski + tolerans) + 1)",
       "    return eski, None")],
     ["test_mmd_tabana_gore_bayatsa", "test_kod_commitlendiyse"]),
    ("M06 tazele: ayni adli tanimin sirasi yok sayildi", TAZELE,
     [("    kt = ht.kapsam(t_satir)", "    kt = (ht.kapsam(t_satir)[0], 0)")],
     ["test_kacinci_tanim_korunur"]),
    ("M07 tazele: tanim sayisi degisimi denetimi kaldirildi", TAZELE,
     [("    if hc.sayi(q) != ht.sayi(q):", "    if False:")],
     ["test_tanim_sayisi_degisirse_belirsiz"]),
    ("M08 tazele: --kuru yine de yaziyor", TAZELE,
     [("    if not kuru:", "    if True:")],
     ["test_kuru_dosya_yazmaz"]),
    ("M09 tazele: hata varken baslik guncelleniyor", TAZELE,
     [('        if not hatalar and damga and satirlar and satirlar[0].startswith("%% koddan turetildi"):',
       '        if damga and satirlar and satirlar[0].startswith("%% koddan turetildi"):')],
     ["test_f1_den_metin_silinirse"]),
    ("M10 tazele: alt-grafik basliklari atlaniyor (T226-D bulgusu; master'daki eski desen)", TAZELE,
     [("    if not m:\n        return None\n    _, kimlik, sekil, etiket, kapanis = m.groups()",
       "    if not m or m.group(1):\n        return None\n    _, kimlik, sekil, etiket, kapanis = m.groups()")],
     ["test_f1_ustune_ekleme", "test_tazele_basliklari_kaydirir", "test_bes_diyagramda",
      "test_iki_arac_ayni_dugum_kumesini"]),
    ("M11 tazele: cok parcali etikette yalniz ilk parca", TAZELE,
     [("               for k, p in enumerate(parcalar))",
       "               for k, p in enumerate(parcalar[:1]))")],
     ["test_parcalar_ardisik"]),
    ("M12 harita: ic ice tanim satirlari kapsama dahil", DOGRULA,
     [("        return [n for n in range(bas, son + 1) if self._en_ic[n] == i]",
       "        return list(range(bas, son + 1))")],
     ["test_ic_ice_tanimdaki"]),
    ("M13 dogrula: qualname farki (KAPSAM DEGISTI) kaldirildi", DOGRULA,
     [("        if kt[0] != kc[0]:", "        if False:")],
     ["test_baska_fonksiyona_kayma", "test_dogrula_basligin_baska_metoda",
      "test_dogrula_baslik_ayni_adli"]),
    ("M14 dogrula: ayni adli baska tanim karsilastirmasi kaldirildi", DOGRULA,
     [("        elif kt[1] != kc[1]:", "        elif False:")],
     ["test_dogrula_ayni_adli"]),
    ("M15 dogrula: KAPSAM BELIRSIZ kaldirildi", DOGRULA,
     [("        elif ht.sayi(kt[0]) != hc.sayi(kt[0]):", "        elif False:")],
     ["test_dogrula_tanim_sayisi"]),
    ("M16 dogrula: cikis kodu kapsam hatasini yok sayiyor", DOGRULA,
     [("    return len(hatalar) == 0 and not kapsam_hatalari", "    return len(hatalar) == 0")],
     ["test_baska_fonksiyona_kayma"]),
    ("M17 dogrula: kapsam hatasi varken --tablo yaziliyor", DOGRULA,
     [("    if tablo and not hatalar and not kapsam_hatalari:", "    if tablo and not hatalar:")],
     ["test_baska_fonksiyona_kayma"]),
    ("M18 dogrula: taban .mmd yerine calisma .mmd", DOGRULA,
     [("    taban_mmd = taban_icerigi(kok, taban, goreli)",
       '    taban_mmd = Path(mmd_yolu).read_text(encoding="utf-8")')],
     ["test_baska_fonksiyona_kayma"]),
    ("M19 dogrula: taban kodu yerine calisma kodu", DOGRULA,
     [("            ht, hc = kaynak.harita(t.dosya, taban), kaynak.harita(d.dosya)",
       "            ht, hc = kaynak.harita(t.dosya), kaynak.harita(d.dosya)")],
     ["test_dogrula_tanim_sayisi"]),
    ("M20 tazele: taban yerine calisma agaci okunuyor", TAZELE,
     [("    ds_t = kaynak.satirlar(dosya, taban)", "    ds_t = kaynak.satirlar(dosya)"),
      ("        ht, hc = kaynak.harita(dosya, taban), kaynak.harita(dosya)",
       "        ht, hc = kaynak.harita(dosya), kaynak.harita(dosya)")],
     ["test_f1_ustune_ekleme"]),
    # ── AKIS-D2: curutucunun KACAN mutasyonlari (KUSUR-2) ──
    ("M21 (N1) dogrula: dosya degisimi kilidi kaldirildi", DOGRULA,
     [("        if t.dosya != d.dosya:", "        if False:")],
     ["test_dogrula_baska_dosyadaki"]),
    ("M22 (N2) harita: dekorator satirlari tanima ait degil", DOGRULA,
     [("                bas = min([c.lineno] + [d.lineno for d in c.decorator_list])",
       "                bas = c.lineno")],
     ["test_tazele_dekorator_dugumu", "test_dogrula_baska_fonksiyonun_dekoratorune"]),
    ("M23 (N2b) harita: goreli konum capasi dekoratorlu baslangic (fd65b427)", DOGRULA,
     [("                capa = c.lineno", "                capa = bas")],
     ["test_iki_dekorator_eklenince"]),
    ("M24 (N3) harita: async def kapsam degil", DOGRULA,
     [("_KAPSAM_TIPLERI = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)",
       "_KAPSAM_TIPLERI = (ast.FunctionDef, ast.ClassDef)")],
     ["test_tazele_async", "test_dogrula_async"]),
    ("M25 (N4) tazele: dosya:N-M araliginin sonu kaydirilmiyor", TAZELE,
     [('            yeni_sat2 = f"-{int(sat2) + yeni - eski}" if sat2 else ""',
       '            yeni_sat2 = f"-{sat2}" if sat2 else ""')],
     ["test_aralik_sonu_da_kayar"]),
    # ── AKIS-D2: taban suphesi (KUSUR-1) ──
    ("M26 tazele: varsayilan tabanda suphe engeli kaldirildi (fd65b427 davranisi)", TAZELE,
     [("    if tum and varsayilan:", "    if False:")],
     ["test_varsayilan_taban_supheli", "test_kuru_da_supheli"]),
    ("M27 tazele: iki tabanin sonucu karsilastirilmiyor", TAZELE,
     [("        if diger[0] != secilen[0]:", "        if False:")],
     ["test_varsayilan_taban_supheli", "test_ikinci_kosu_supheli"]),
    ("M28 tazele: ikinci taban (dugum satirinin kokeni) hic alinmiyor", TAZELE,
     [("    kokenler = D.satir_kokenleri(kok, sha, goreli) if mmd_taban is not None else {}",
       "    kokenler = {}")],
     ["test_varsayilan_taban_supheli", "test_dogru_taban_elle_verilince_f1"]),
    ("M29 tazele: tabandaki .mmd'de olmayan dugum icin calisma agaci adayi yok", TAZELE,
     [("        if taban_no is None:\n            aday = W",
       "        if taban_no is None:\n            aday = None")],
     ["test_ikinci_kosu_supheli"]),
    ("M30 tazele: toptan dosya farki supheli (satir kaydirmayan commit yanlis alarm)", TAZELE,
     [("        if diger[0] != secilen[0]:", "        if True:")],
     ["test_dosya_sonuna_ekleme"]),
    ("M31 tazele: elle taban + uyari varken baslik damgalaniyor", TAZELE,
     [("                                      damga=not supheler[p])",
       "                                      damga=True)")],
     ["test_elle_head_uyariyla"]),
    ("M32 dogrula: TABAN SUPHELI kaldirildi", DOGRULA,
     [("            if ko != kt:", "            if False:")],
     ["test_dogrula_taban_head_supheyi"]),
    ("M33 dogrula: dugum koken commit'leri hic kullanilmiyor", DOGRULA,
     [("    oncekiler = mmd_dugum_kokenleri(kok, taban, goreli, taban_mmd)",
       "    oncekiler = {}")],
     ["test_dogrula_taban_head_supheyi"]),
    ("M34 dogrula: toptan dosya farki supheli (yanlis alarm)", DOGRULA,
     [("            if ko != kt:", "            if True:")],
     ["test_dosya_sonuna_ekleme"]),
    ("M35 dogrula: goreli --mmd yolunda eski relative_to (D-440 EK)", DOGRULA,
     [('    print(f"{_yol_goster(mmd_yolu, kok)}: {len(dugumler)} düğüm · "',
       '    print(f"{mmd_yolu.relative_to(kok)}: {len(dugumler)} düğüm · "')],
     ["test_goreli_mmd_yolu"]),
    # ── AKIS-D2 EK (T226-D amelesi bulgusu: alt-grafik basliklari) ──
    ("M36 dogrula+tazele: tek desende `ID [\"` bosluklu bicim yok", DOGRULA,
     [(r'([A-Za-z][A-Za-z0-9_]*)\s*(\["|\{")', r'([A-Za-z][A-Za-z0-9_]*)(\["|\{")')],
     ["test_iki_arac_ayni_dugum_kumesini", "test_tazele_basliklari_kaydirir"]),
    ("M37 dogrula+tazele: tek desen subgraph basligini tanimiyor", DOGRULA,
     [("(?:(subgraph)\\s+)?", "(?:(subgraphX)\\s+)?")],
     ["test_iki_arac_ayni_dugum_kumesini", "test_bes_diyagramda", "test_tazele_basliklari_kaydirir"]),
    ("M38 tazele: dosya:satir ayraci yalniz <br/> (<br> ve <br /> atlaniyor)", TAZELE,
     [(r"RE_ATIF = re.compile(r'(<br\s*/?>)(", r"RE_ATIF = re.compile(r'(<br/>)(")],
     ["test_iki_arac_ayni_dugum_kumesini", "test_tazele_basliklari_kaydirir"]),
    ("M39 tazele: satir yeniden kurulurken ayrac <br/> yaziliyor (bicim bayt-es degil)", TAZELE,
     [("            satirlar[k] = s[:bas] + f\"{yeni}{yeni_sat2}\" + s[son:]",
       "            satirlar[k] = s[:s.index('\"') + 1] + f'{etiket}<br/>{dosya}:{yeni}{yeni_sat2}' + s[son:]")],
     ["test_tazele_basliklari_kaydirir"]),
    ("M40 tazele: `def ad()` etiketi icin tanim satiri eslemesi yok", TAZELE,
     [("    if not adaylar and len(parcalar) == 1 and D.RE_DEF.match(parcalar[0]):", "    if False:")],
     ["test_tazele_basliklari_kaydirir", "test_tazele_baslik_kendi_sinifinin"]),
    ("M41 tazele: acilis/kapanis uyusmayan satir dugum sayiliyor", TAZELE,
     [("    if (sekil == '[\"') != (kapanis == '\"]'):", "    if False:")],
     ["test_acilis_kapanis_uyusmayan"]),
    # ── AKIS-D2 2. RED: ikinci taban DUGUM BASINA (curutucu KUSUR-A) ──
    ("M42 dogrula+tazele: ikinci taban DOSYA duzeyinde (.mmd'ye dokunan son commit) — KUSUR-A",
     DOGRULA, [(BLAME_ESKI, BLAME_DOSYA_DUZEYI)],
     ["test_varsayilan_taban_supheli_dugum_kokenine_gore", "test_dogrula_taban_head_supheyi_raporlar"]),
    ("M43 dogrula+tazele: blame satir eslemesi bir satir kayik", DOGRULA,
     [("                kokenler[ilk + k] = sha", "                kokenler[ilk + k + 1] = sha")],
     ["test_varsayilan_taban_supheli_dugum_kokenine_gore", "test_dogrula_taban_head_supheyi_raporlar"]),
    ("M44 dogrula: dugum kokenleri tabandan degil HEAD'den okunuyor", DOGRULA,
     [('["git", "-C", str(kok), "blame", "--porcelain", ref, "--", yol]',
       '["git", "-C", str(kok), "blame", "--porcelain", "HEAD", "--", yol]')],
     ["test_dogrula_eski_tabanda_koken_tabandan_hesaplanir"]),
    ("M45 tazele: tabanda pencerenin UST siniri bir eksik", TAZELE,
     [("    pencere = range(max(1, eski - tolerans), min(len(satirlar), eski + tolerans) + 1)",
       "    pencere = range(max(1, eski - tolerans), min(len(satirlar), eski + tolerans))")],
     ["test_eski_arti_tolerans_bulunur"]),
    ("M46 tazele: tabanda pencerenin ALT siniri bir fazla", TAZELE,
     [("    pencere = range(max(1, eski - tolerans), min(len(satirlar), eski + tolerans) + 1)",
       "    pencere = range(max(1, eski - tolerans + 1), min(len(satirlar), eski + tolerans) + 1)")],
     ["test_eski_eksi_tolerans_bulunur"]),
    ("M47 tazele: TABANDA ESITLIK denetimi kaldirildi", TAZELE,
     [("    if len(sirali) > 1 and abs(sirali[0] - eski) == abs(sirali[1] - eski):", "    if False:")],
     ["test_tabanda_esit_uzak_iki_aday"]),
    ("M48 tazele: def-kipi eslemesi `async def` onekini tanimiyor", TAZELE,
     [('r"\\s*(?:async\\s+)?def\\s+"', 'r"\\s*def\\s+"')],
     ["test_async_def_basligi_kaydirilir"]),
    ("M49 tazele: RE_ATIF'in `$` capasi yok (orta parcadaki ':N' dosya:satir sanilir)", TAZELE,
     [("(?:-(\\d+))?$')", "(?:-(\\d+))?')")],
     ["test_dosya_satir_etiketin_sonundan_okunur"]),
    ("M50 dogrula: TABAN SUPHELI taban satiri yerine calisma satiriyla hesaplaniyor", DOGRULA,
     [("            ko = ho.kapsam(t.satir) if ho is not None else None",
       "            ko = ho.kapsam(d.satir) if ho is not None else None")],
     ["test_dogrula_supheyi_taban_satiriyla_hesaplar"]),
    ("M51 tazele: CRLF korunmuyor (LF yaziliyor)", TAZELE,
     [('    crlf = b"\\r\\n" in ham', "    crlf = False")],
     ["test_crlf_mmd_crlf_kalir"]),
    ("M52 tazele: taban dugumu tam satir yerine yalniz ID ile eslestiriliyor", TAZELE,
     [("            taban_dugum.setdefault((a[0], s.strip()), k + 1)",
       "            taban_dugum.setdefault((a[0], a[0]), k + 1)"),
      ("        taban_no = taban_dugum.get((kimlik, s.strip()))",
       "        taban_no = taban_dugum.get((kimlik, kimlik))")],
     ["test_ikinci_kosu_supheli"]),
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def testi_kos():
    r = subprocess.run([PY, "-m", "unittest", "discover", "-s", "tests", "-p", TEST],
                       cwd=str(DEPO), capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    cikti = r.stdout + r.stderr
    dusen = re.findall(r"^(?:FAIL|ERROR): (\w+) \(", cikti, re.M)
    ozet = [s for s in cikti.splitlines() if s.startswith(("Ran ", "OK", "FAILED"))]
    return r.returncode, dusen, ozet


def main():
    rc, dusen, ozet = testi_kos()
    print(f"TEMIZ (once): cikis={rc} {ozet} dusen={dusen}")
    if rc != 0:
        print("TEMIZ AGAC DUSUYOR — mutasyon anlamsiz, durduruldu")
        return 1
    yakalanan = kacan = uygulanamayan = 0
    for ad, yol, degisimler, beklenen in MUTANTLAR:
        asil = yol.read_bytes()
        s0 = sha(asil)
        metin = asil
        hata = None
        for eski, yeni in degisimler:
            e = eski.encode("utf-8")
            if metin.count(e) != 1:
                hata = f"eslesme {metin.count(e)} (tekil degil): {eski!r}"
                break
            metin = metin.replace(e, yeni.encode("utf-8"))
        if hata:
            uygulanamayan += 1
            print(f"{ad}: UYGULANAMADI — {hata}")
            continue
        try:
            yol.write_bytes(metin)
            rc, dusen, ozet = testi_kos()
        finally:
            yol.write_bytes(asil)
        s1 = sha(yol.read_bytes())
        beklenen_dustu = [b for b in beklenen if any(d.startswith(b) for d in dusen)]
        if rc != 0 and beklenen_dustu:
            yakalanan += 1
            durum = "YAKALANDI"
        else:
            kacan += 1
            durum = "KACTI"
        print(f"{ad}: {durum} · cikis={rc} {ozet} · dusen={dusen} · beklenen dusen="
              f"{beklenen_dustu}/{beklenen} · geri yukleme {yol.name} sha {s1[:12]} == "
              f"{s0[:12]}: {s1 == s0}")
        if s1 != s0:
            print("GERI YUKLEME BAYT-ES DEGIL — DURDURULDU")
            return 2
    rc, dusen, ozet = testi_kos()
    print(f"TEMIZ (sonra): cikis={rc} {ozet} dusen={dusen}")
    print(f"OZET: {yakalanan}/{len(MUTANTLAR)} yakalandi · kacan {kacan} · uygulanamayan "
          f"{uygulanamayan}")
    return 0 if kacan == 0 and uygulanamayan == 0 and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

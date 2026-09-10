"""AKIS-D mutasyon kontrolu: her yeni kilit GERCEK dosya mutasyonuyla yakalaniyor mu.

Her mutant scripts/akis_satir_tazele.py ya da scripts/akis_diyagram_dogrula.py
icinde TEKIL bir satiri degistirir, tests/test_akis_kapsam_korumasi.py kosulur,
dosya BAYT-ES geri yuklenir (sha256 karsilastirilir). Yakalanmayan mutant = kacan.
AKIS-D2 (curutucu RED): M21-M25 curutucunun KACAN N1/N2/N3/N4 mutasyonlari (+ N2b capa),
M26-M34 taban suphesi (KUSUR-1), M35 goreli --mmd; M36-M41 EK (T226-D bulgusu: alt-grafik
basliklari / tek desen / bicim bayt-es / def basligi). M02/M09/M10 metni yeni koda
uyarlandi (capa, damga, dugum_ayikla).
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
    ("M28 tazele: ikinci taban .mmd'nin son commit'i (L) hic alinmiyor", TAZELE,
     [("    L = (son, f\"{son[:7]} (.mmd'nin son commit'i)\") if son is not None and son != sha else None",
       "    L = None")],
     ["test_varsayilan_taban_supheli"]),
    ("M29 tazele: tabandaki .mmd'de olmayan dugum icin calisma agaci adayi yok", TAZELE,
     [("        aday = L if s.strip() in taban_dugum else W", "        aday = L")],
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
    ("M33 dogrula: .mmd'nin son commit'i hic kullanilmiyor", DOGRULA,
     [("            onceki = son", "            pass")],
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

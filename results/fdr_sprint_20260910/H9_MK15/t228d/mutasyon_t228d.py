"""T228-D mutasyon kosucusu — her mutasyonu uygular, `tests/test_isaretli_gosterici.py`'yi kosar,
dosyalari BAYT-ES geri yukler (sha256 ile dogrulanir). Ham cikti: t228d/mutasyon_ciktisi.txt.

Gosterici mutasyonlari `scripts/isaretli_gosterici.py` kanonik kopyasina VE
`jetson_paket/kod/isaretli_gosterici.py` aynasina BIRLIKTE uygulanir (ayna bayt-es testi G9 mutanti
bos yere yakalamasin — HEDEF test dusmeli). Belge mutasyonlari
`jetson_paket/gosterici/GOSTERICI_KURULUM.md`'ye; betik mutasyonlari `jetson_paket/jetson_baslat.sh`'e.
Satir sonu korunur (calisma kopyasi autocrlf ile CRLF olabilir). Bir mutasyon birden cok
(eski, yeni) cifti tasiyabilir; her eski metin dosyada TAM 1 kez bulunmali.

"YAKALANDI" yalniz TUM hedef testler dustuyse yazilir; baska testlerin dusmesi ayrica listelenir.
T228-D mutasyonlari (gorev tanimi): MG x11 dongusu hatayi yok sayar · MH1 histerezis kaldirildi ·
MP boru ilerlemesi esigi kaldirildi — ve ek kilitler. R-* satirlari T228'in (t228/mutasyon_t228.py)
metni DEGISMEYEN mutantlarinin yeniden kosumudur (test dosyasi degisti: regresyon denetimi); T228
M6'nin metni T228-D'de kaldirildi, yerine M6' var.

T228-D2 (T228-D curutucusu RED, REVIEW_LOG D-453): curutucunun KACAN uc mutanti NG (nabiz
izleyicisi borular arasi paylasilir), NK1 (§1 kodek notu cizilir), NK2 (§5 DOGRULANACAK maddesi
cizilip 'doğrulandı' yazilir) + yeni kilitlerin mutantlari: NS (olen videonun sebebi), NK3-NK10
(D-453: belge kilitleri cizili araliklar AYIKLANMIS metinde; §1/§5/§9'da olculmemis GECTI yok;
§4 adim 9 sonuc hucresi tam 'ÖLÇÜLECEK'; §8 satiri; T228 kapsam kilidi). Hepsi MUTASYONLAR_D2'de.
NK11-NK21 (D-454 sinifi — T221-D2 curutucusunun kacan kaliplari): olculmemis hukum 'tutar' / karma
yazim 'dogrulandı' / kalin parcali 'Doğ**rulan**dı' / yumusak tireli 'doğ-rulandı' ile cevrilir; §4
satir sonucu ve basligi ('tamamı ölçüldü'), ust hukum cizilir; §5'e kalin sayili ya da ASCII '>='li
CELISKILI ikinci hukum yazilir; eski (nabizsiz) boru tipografik tirnakla CANLI metne geri gelir.
Hedef: test_G8_D453_D454_olculmemis_hukum_celiski_eski_komut (normallestirilmis metin).

KOSUM (depo kokunden; baska surec bu dosyalari okurken KOSMA):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t228d/mutasyon_t228d.py
"""
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
PY = sys.executable
TEST = "test_isaretli_gosterici.py"
CIKTI = Path(__file__).resolve().parent / "mutasyon_ciktisi.txt"
GOSTERICI = (KOK / "scripts" / "isaretli_gosterici.py",
             KOK / "jetson_paket" / "kod" / "isaretli_gosterici.py")
KURULUM = (KOK / "jetson_paket" / "gosterici" / "GOSTERICI_KURULUM.md",)
BETIK = (KOK / "jetson_paket" / "jetson_baslat.sh",)

G11_S = "test_G11_x11_dongusu_CANLI_iken_503_ya_da_erisilemez_ILK_cizim_GORUNTU_YOK"
G11_G = "test_G11_x11_dongusu_gercek_cekici_gercek_HTTP_CANLI_sonra_503"
HIST = "test_G7_histerezis_tek_taze_yoklama_videoya_DONMEZ_cikis_ANINDA"
TABLO = "test_G7_saf_karar_tablosu"
CIRP = "test_G7_cirpinan_yayin_baslatma_sikligi_sinirli"
OLEN = "test_G7_hemen_biten_boru_uyari_ve_baslatma_sikligi_sinirli"
DONMUS = "test_G7_donmus_boru_kare_taze_olsa_da_GORUNTU_YOK"
SINIR = "test_G7_boru_donmus_mu_sinir_ve_referans"
KOS_DONMUS = "test_G7_drm_kos_donmus_boru_GORUNTU_YOK_borusuna_gecer"
AYRIS = "test_G7_nabiz_ayristir_toleransli_ve_secici"
IZLEYICI = "test_G7_nabiz_izleyici_ayni_ya_da_geri_pts_ilerleme_DEGIL"
SINA = "test_G7_nabiz_sina_cli_eslesti_0_eslesmedi_1"
G4 = "test_G4_drm_borusu_elemanlar_sirali_ve_parametreler"
G6 = "test_G6_kuru_her_kip_exit_0_hicbir_sey_acmaz"
G8D = "test_G8_kurulum_T228D_kodek_celiskisi_nabiz_DOGRULANACAK_eski_komut_cizili"

ESKI_KOMUT = ("gst-launch-1.0 -e 'souphttpsrc location=http://127.0.0.1:8081/video is-live=true "
              "do-timestamp=true ! multipartdemux ! jpegdec ! nvvidconv ! video/x-raw(memory:NVMM),"
              "width=1280,height=720 ! nvdrmvideosink set_mode=1 sync=false'")
YENI_KOMUT = ("gst-launch-1.0 -v -e 'souphttpsrc location=http://127.0.0.1:8081/video is-live=true "
              "do-timestamp=true ! multipartdemux ! jpegdec ! identity name=nabiz silent=false ! "
              "nvvidconv ! video/x-raw(memory:NVMM),width=1280,height=720 ! nvdrmvideosink "
              "set_mode=1 sync=false'")

# (ad, dosyalar, [(eski, yeni), ...], hedef testler)
MUTASYONLAR = [
    ("MG x11 dongusu cekme hatasini yok sayiyor (ekran_durumu(..., None))", GOSTERICI,
     [("            d = ekran_durumu(saat(), son_t, cekme_hatasi)\n",
       "            d = ekran_durumu(saat(), son_t, None)\n")], (G11_S, G11_G)),
    ("MH1 histerezis kaldirildi (tek taze yoklama videoyu acar)", GOSTERICI,
     [("    istenen = BORU_VIDEO if (taze and ardisik >= gerekli_ardisik) else BORU_YOK\n",
       "    istenen = BORU_VIDEO if taze else BORU_YOK\n")], (HIST, TABLO)),
    ("MH2 CANLI'dan cikis baslatma araligina takiliyor (aninda degil)", GOSTERICI,
     [("        return DrmKarar(BORU_YOK, True, True)          # CANLI'dan cikis ANINDA (guvenli taraf)\n",
       "        return DrmKarar(BORU_YOK if serbest else BORU_VIDEO, serbest, True)\n")], (HIST, TABLO)),
    ("MT boru baslatma araligi kaldirildi (serbest hep True)", GOSTERICI,
     [("    serbest = son_baslatma_t is None or (float(simdi) - float(son_baslatma_t)) >= asgari_aralik_s\n",
       "    serbest = True\n")], (CIRP, OLEN, TABLO)),
    ("MO olen video borusundan sonra GORUNTU YOK hemen acilmiyor", GOSTERICI,
     [("    if calisan is None and son_boru == BORU_VIDEO:\n",
       "    if False:\n")], (OLEN, TABLO)),
    ("MP boru ilerlemesi esigi kaldirildi (boru_donmus_mu hep False)", GOSTERICI,
     [("    return float(simdi) - ref > esik_s\n", "    return False\n")], (DONMUS, SINIR, KOS_DONMUS)),
    ("MP2 gozetmen boru nabzini denetlemiyor", GOSTERICI,
     [("            if taze and calisan == BORU_VIDEO and ilerleme_oku is not None:\n",
       "            if False:\n")], (DONMUS, KOS_DONMUS)),
    ("MN drm_kos nabiz izleyicisini gozetmene baglamiyor", GOSTERICI,
     [("                     asgari_omur_s=DRM_ASGARI_OMUR_S, ilerleme_oku=ilerleme_oku,\n",
       "                     asgari_omur_s=DRM_ASGARI_OMUR_S, ilerleme_oku=None,\n")], (KOS_DONMUS,)),
    ("MV video argv'sinde -v yok (nabiz satiri basilmaz)", GOSTERICI,
     [('    return onek + [gst, "-v", "-e", drm_boru(kaynak, conn_id=conn_id)]\n',
       '    return onek + [gst, "-e", drm_boru(kaynak, conn_id=conn_id)]\n')], (G4, G6, G8D)),
    ("MB drm_kos stdbuf onekini koymuyor", GOSTERICI,
     [('    stdbuf = stdbuf_yolu if stdbuf_yolu is not None else shutil.which("stdbuf")\n',
       "    stdbuf = None\n")], ("test_G7_drm_kos_stdbuf_onekli_video_borusu",)),
    ("MZT --nabiz-sina zamanlama denetimi kaldirildi (TOPLU yakalanmaz)", GOSTERICI,
     [("    if varis < NABIZ_SINA_VARIS_ORANI * pts_yay:\n", "    if False:\n")],
     ("test_G7_nabiz_sina_zamanlama_ZAMANINDA_0_TOPLU_1",
      "test_G7_nabiz_sina_gercek_boru_ZAMANINDA_0_TOPLU_1")),
    ("MI identity silent=true (last-message yok)", GOSTERICI,
     [('"identity name={} silent=false ! nvvidconv', '"identity name={} silent=true ! nvvidconv')],
     (G4, G6, G8D)),
    ("MA ayristirici olay satirini nabiz sayiyor ('chain' sarti yok)", GOSTERICI,
     [('    if tur is None or tur.group(1) != "chain":\n', "    if tur is None:\n")],
     (AYRIS, IZLEYICI, SINA)),
    ("MS ayristirici eleman adini denetlemiyor (nabizci sayilir)", GOSTERICI,
     [("    if not s or ad not in s or not _nabiz_eleman_kalibi(ad).search(s):\n",
       "    if not s or ad not in s:\n")], (AYRIS,)),
    ("MZ ayni/geri pts ilerleme sayiliyor", GOSTERICI,
     [("                ilerledi = pts is None or self.son_pts is None or pts > self.son_pts\n",
       "                ilerledi = True\n")], (IZLEYICI,)),
    ("M6' drm gozetmeni BAYAT'ta video borusunu durdurmuyor", GOSTERICI,
     [("            taze = d.durum == DURUM_CANLI\n", "            taze = d.durum != DURUM_YOK\n")],
     ("test_G7_yok_kirmizi_canli_video_bayatta_video_DURUR",)),
    ("MD1 belge: §1 kodlayici satirindan H.264/H.265 celiski notu silindi", KURULUM,
     [("Dönüştürücünün canlı kodeki **H.264/H.265 çelişkili** (TASARIM §5; SIYI dönüştürücü "
       "kılavuzu V1.1) — §4 adım 5'te VLC'de okunur (**DOĞRULANACAK**) ", "")], (G8D,)),
    ("MD2 belge: §5 nabiz bicimi DOGRULANACAK notu silindi", KURULUM,
     [("🔴 **`-v` nabız satırı biçimi Jetson'da ÖLÇÜLEMEDİ — DOĞRULANACAK** (PC'de",
       "🔴 **`-v` nabız satırı biçimi** (PC'de")], (G8D,)),
    ("MD3 belge: eski komut cizilmeden silindi", KURULUM,
     [("~~10 Eylül (T228): `" + ESKI_KOMUT + "`~~ → ", "")], (G8D,)),
    ("MD4 belge: §5 komutu kodla ayni degil (eski komut geri)", KURULUM,
     [("sudo modprobe nvidia-drm modeset=1\n" + YENI_KOMUT + "\n",
       "sudo modprobe nvidia-drm modeset=1\n" + ESKI_KOMUT + "\n")], (G8D,)),
    ("MD5 belge: §4 adim 9 (--nabiz-sina) silindi", KURULUM,
     [("| 9 | DRM nabız biçimi + zamanlaması: §5 `--nabiz-sina` komutu (DRM kipinden ÖNCE) | "
       "çıkış 0, `NABIZ_SINA: ESLESTI — … 20 nabiz …; ZAMANINDA` | ÖLÇÜLECEK |\n", "")], (G8D,)),
    ("MD6 belge: §5 satir tamponu (stdbuf) maddesi silindi", KURULUM,
     [("- **Satır tamponu:** `drm_kos` video borusunu `stdbuf -oL` önekiyle koşar (coreutils `stdbuf`\n"
       "  varsa; yoksa KIRMIZI uyarı, önek konmaz). Stdout boruya bağlıyken blok tampon nabız satırlarını\n"
       "  topluca getirirdi; `gst-launch`'ın kendi `fflush`'ı **ÖLÇÜLEMEDİ**.\n", "")], (G8D,)),
    # ── T228 regresyon (metni degismeyen mutantlar) ──
    ("R-M1 bayat esigi kaldirildi", GOSTERICI,
     [("    if yas > bayat_esigi_s:\n        return EkranDurumu(DURUM_BAYAT,",
       "    if False:\n        return EkranDurumu(DURUM_BAYAT,")], ("test_G1_taze_bayat_yok",)),
    ("R-M2 yasak IP kontrolu kaldirildi", GOSTERICI,
     [("    if s in SIYI_SABIT_IP:\n", "    if False:\n")], ("test_G5_SIYI_sabitleri_REDDEDILIR",)),
    ("R-M3 GORUNTU YOK ekrani eski kareyi ciziyor", GOSTERICI,
     [("    tuval = np.empty((yukseklik, genislik, 3), np.uint8)\n    tuval[:] = KIRMIZI_ZEMIN\n",
       "    tuval = np.empty((yukseklik, genislik, 3), np.uint8)\n    tuval[:] = KIRMIZI_ZEMIN\n"
       "    if kare is not None:\n        tuval = sigdir(kare, genislik, yukseklik)\n")],
     ("test_G2_GORUNTU_YOK_eski_kareyi_ASLA_cizmez",)),
    ("R-M4 ayni sira/govde tazeligi uzatiyor", GOSTERICI,
     [("                onceki_hata, self.hata = self.hata, None\n                self.basari += 1\n"
       "            if onceki_hata is not None:\n                self.log(\"yayin yanit veriyor",
       "                onceki_hata, self.hata = self.hata, None\n                self.basari += 1\n"
       "                self.son_taze_t = self.saat()\n"
       "            if onceki_hata is not None:\n                self.log(\"yayin yanit veriyor")],
     ("test_G3_ayni_sira_tazelik_UZATMAZ_bayat_sonra_yok",)),
    ("R-M5 x11 DISPLAY denetimi yok", GOSTERICI,
     [("    if ortam.get(\"DISPLAY\"):\n        return None\n    ek = \"\"\n",
       "    return None\n    ek = \"\"\n")], ("test_G6_x11_DISPLAY_yoksa_cikis_2_pencere_acilmaz",)),
    ("R-M7 jetson_baslat --isaretli-yayin bayragini vermiyor", BETIK,
     [("if [ \"$GOSTERICI_KIP\" != kapali ]; then RPI_EK_ARGS=\"$RPI_EK_ARGS --isaretli-yayin "
       "$ISARETLI_YAYIN\"; fi\n", ":\n")], ("test_G10_x11_T227siz_paket_YOK_exit_3_bayrak_verilir",)),
    ("R-M8 --kur/--dogrudan T227 denetimi yok", BETIK,
     [("    isaretli_destek_var \"$y\" \\\n      || hata \"GOSTERICI_KIP=",
       "    true \\\n      || hata \"GOSTERICI_KIP=")],
     ("test_G10_kur_T227siz_kurulu_rpi_HATA_hicbir_systemctl_yok",)),
    ("R-M9 ISARETLI_YAYIN loopback denetimi yok", BETIK,
     [("  *) hata \"ISARETLI_YAYIN='$ISARETLI_YAYIN': yalniz 127.0.0.1:<port>",
       "  *) _iy_port=8081; : \"ISARETLI_YAYIN='$ISARETLI_YAYIN': yalniz 127.0.0.1:<port>")],
     ("test_G10_gecersiz_kip_yayin_port_cakismasi_fail_closed",)),
    ("R-M10 kuru gosterici [YOK] satirlarini saymiyor", BETIK,
     [("  yok=$((yok + $(printf '%s\\n' \"$g\" | grep -c '^\\[YOK\\]' || true)))\n", "  :\n")],
     ("test_G10_x11_T227siz_paket_YOK_exit_3_bayrak_verilir",)),
]

# ── T228-D2: curutucunun KACAN mutantlari (NG, NK1, NK2) + yeni kilitlerin mutantlari ──
NG_T = "test_G7_drm_kos_ikinci_video_borusu_YENI_nabiz_izleyicisiyle_surer"
NS_T = "test_G7_olen_video_borusu_GORUNTU_YOK_sebebi_rc_ya_da_yayin_sebebi"
G8K = "test_G8_kurulum_belgesi_kapsami"
D454_T = "test_G8_D453_D454_olculmemis_hukum_celiski_eski_komut"
DOGRULANACAK_KOK = "ÖLÇÜLEMEDİ — DOĞRULANACAK** (PC'de GStreamer yok;"
MUTASYONLAR_D2 = [
    ("NG nabiz izleyicisi borular arasi PAYLASILIYOR (ikinci boru onceki izleyiciyle)", GOSTERICI,
     [("        iz = NabizIzleyici(saat=saat)\n",
       "        iz = son[\"iz\"] or NabizIzleyici(saat=saat)\n")], (NG_T,)),
    ("NS olen video borusunun GORUNTU YOK sebebi 'yayin dogrulaniyor'a donuyor", GOSTERICI,
     [("                    elif olen_video is not None:\n", "                    elif False:\n")],
     (NS_T,)),
    ("NK1 belge: §1 kodek celiski notu CIZILDI (metin durur)", KURULUM,
     [("**H.264/H.265 çelişkili**", "~~**H.264/H.265 çelişkili**~~")], (G8D,)),
    ("NK2 belge: §5 nabiz bicimi DOGRULANACAK maddesi cizilip 'doğrulandı' yazildi", KURULUM,
     [("🔴 **`-v` nabız satırı biçimi Jetson'da ÖLÇÜLEMEDİ — DOĞRULANACAK**",
       "~~🔴 **`-v` nabız satırı biçimi Jetson'da ÖLÇÜLEMEDİ — DOĞRULANACAK**~~ "
       "(10 Eylül: doğrulandı)")], (G8D,)),
    ("NK3 belge: §5 satir tamponu (stdbuf) cumlesi CIZILDI", KURULUM,
     [("`drm_kos` video borusunu `stdbuf -oL` önekiyle koşar",
       "~~`drm_kos` video borusunu `stdbuf -oL` önekiyle koşar~~")], (G8D,)),
    ("NK4 belge: §9 nabiz bicimi OLCULEMEDI maddesi CIZILDI", KURULUM,
     [("- `gst-launch-1.0 -v` nabız satırı biçimi (DRM",
       "- ~~`gst-launch-1.0 -v` nabız satırı biçimi~~ (DRM")], (G8D,)),
    ("NK5 belge: §5 DOGRULANACAK maddesi durur ama yanina 'doğrulandı' yazildi", KURULUM,
     [("ÖLÇÜLEMEDİ — DOĞRULANACAK** (PC'de GStreamer yok;",
       "ÖLÇÜLEMEDİ — DOĞRULANACAK** (12 Eylül atölyede doğrulandı; PC'de GStreamer yok;")],
     (G8D,)),
    ("NK6 belge: §5 olen video sebebi notu CIZILDI", KURULUM,
     [("`video borusu kendiliginden bitti (rc N)` (journal",
       "~~`video borusu kendiliginden bitti (rc N)`~~ (journal")], (G8D,)),
    ("NK7 belge: §8 'kendiliginden bitti' sorun giderme satiri CIZILDI", KURULUM,
     [('| drm kipinde kırmızı "video borusu kendiliginden bitti (rc N)" |',
       '| ~~drm kipinde kırmızı "video borusu kendiliginden bitti (rc N)"~~ |')], (G8D,)),
    ("NK8 belge: §0 'Video KARAR ÜRETMEZ' CIZILDI (T228 kapsam kilidi)", KURULUM,
     [("**Video KARAR ÜRETMEZ.**", "~~**Video KARAR ÜRETMEZ.**~~")], (G8K,)),
    ("NK9 belge: §4 adim 9 sonuc hucresi 'GEÇTİ — ÖLÇÜLECEK' (tam ÖLÇÜLECEK degil)", KURULUM,
     [("ZAMANINDA` | ÖLÇÜLECEK |", "ZAMANINDA` | GEÇTİ — ÖLÇÜLECEK |")], (G8D,)),
    ("NK10 belge: §5 yeni video borusu komutu CIZILDI (kod blogunda)", KURULUM,
     [("sudo modprobe nvidia-drm modeset=1\n" + YENI_KOMUT + "\n",
       "sudo modprobe nvidia-drm modeset=1\n~~" + YENI_KOMUT + "~~\n")], (G8D,)),
    # ── D-454 sinifi: tipografik / eszanlamli varyant, celiskili ikinci hukum, eski kuralin donusu ──
    ("NK11 belge: §5 DOGRULANACAK durur, yanina 'biçim tutar' (eski kalip 'tutar'i bilmez)", KURULUM,
     [(DOGRULANACAK_KOK, DOGRULANACAK_KOK.replace("(PC'de", "(12 Eylül: biçim tutar; PC'de"))],
     (G8D, D454_T)),
    ("NK12 belge: §5 DOGRULANACAK yanina karma yazim 'dogrulandı' (g breve'siz, ı noktasiz)", KURULUM,
     [(DOGRULANACAK_KOK, DOGRULANACAK_KOK.replace("(PC'de", "(12 Eylül: dogrulandı; PC'de"))],
     (G8D, D454_T)),
    ("NK13 belge: §5 DOGRULANACAK yanina kalin parcali 'Doğ**rulan**dı'", KURULUM,
     [(DOGRULANACAK_KOK, DOGRULANACAK_KOK.replace("(PC'de", "(12 Eylül: Doğ**rulan**dı; PC'de"))],
     (G8D, D454_T)),
    ("NK14 belge: §5 DOGRULANACAK yanina yumusak tireli 'doğ\\u00adrulandı' (ekranda gorunmez)",
     KURULUM,
     [(DOGRULANACAK_KOK, DOGRULANACAK_KOK.replace("(PC'de", "(12 Eylül: doğ\u00adrulandı; PC'de"))],
     (G8D, D454_T)),
    ("NK15 belge: §4 adim 3 sonucu cizildi, yerine 'GEÇTİ (12 Eylül)'", KURULUM,
     [("| CANLI, bindirme okunur | ÖLÇÜLECEK |",
       "| CANLI, bindirme okunur | ~~ÖLÇÜLECEK~~ GEÇTİ (12 Eylül) |")], (D454_T,)),
    ("NK16 belge: §4 basligi 'hepsi şu an ÖLÇÜLEMEDİ' cizildi, yerine 'tamamı ölçüldü'", KURULUM,
     [("hepsi şu an ÖLÇÜLEMEDİ)", "~~hepsi şu an ÖLÇÜLEMEDİ~~ tamamı ölçüldü)")], (D454_T,)),
    ("NK17 belge: ust hukum 'hiçbiri Jetson'da koşulmadı' cizildi (tipografik kesmeyle 'koşuldu')",
     KURULUM,
     [("**hiçbiri Jetson'da koşulmadı**",
       "~~**hiçbiri Jetson'da koşulmadı**~~ tamamı 12 Eylül’de koşuldu")], (D454_T,)),
    ("NK18 belge: §5'e CELISKILI ikinci hukum, kalin sayi: 'Sahada **1** ardışık taze yoklama yeterli'",
     KURULUM,
     [("Açılışta kırmızı ekran ~3 s görünür (bu kurala göre beklenen).",
       "Açılışta kırmızı ekran ~3 s görünür (bu kurala göre beklenen). Sahada **1** ardışık taze "
       "yoklama yeterli.")], (D454_T,)),
    ("NK19 belge: §5'e CELISKILI donma esigi: 'Sahada donma eşiği **> 6 s** alınır'", KURULUM,
     [('açılır (sebep "video borusu ilerlemiyor").',
       'açılır (sebep "video borusu ilerlemiyor"). Sahada donma eşiği **> 6 s** alınır.')], (D454_T,)),
    ("NK20 belge: eski (nabizsiz) boru tipografik tirnakla §5 kod blogunda CANLI", KURULUM,
     [("sudo modprobe nvidia-drm modeset=1\n" + YENI_KOMUT + "\n",
       "sudo modprobe nvidia-drm modeset=1\n" + YENI_KOMUT + "\n"
       + ESKI_KOMUT.replace("'", "’") + "\n")], (D454_T,)),
    ("NK21 belge: §5 ikinci baslatma araligi ASCII '>= 1 s' (tipografik varyantla gevsetme)", KURULUM,
     [("ölen GÖRÜNTÜ YOK borusu ≥ 3 s", "ölen GÖRÜNTÜ YOK borusu >= 1 s")], (D454_T,)),
]
MUTASYONLAR += MUTASYONLAR_D2

SATIRLAR = []


def yaz(metin):
    print(metin, flush=True)
    SATIRLAR.append(metin)


def kos():
    p = subprocess.run([PY, "-B", "-X", "utf8", "-m", "unittest", "discover", "-s", "tests",
                        "-p", TEST], cwd=KOK, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800)
    cikti = p.stdout + p.stderr
    ran = re.search(r"Ran (\d+) tests?", cikti)
    satirlar = [s for s in cikti.strip().splitlines() if s.strip()]
    son = satirlar[-1] if satirlar else "?"
    dusen = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", cikti, re.M)))
    return p.returncode, (ran.group(1) if ran else "?"), son, dusen


def uygula(dosyalar, ciftler, orijinal):
    for yol in dosyalar:
        metin = orijinal[yol].decode("utf-8")
        crlf = "\r\n" in metin
        n = metin.replace("\r\n", "\n")
        for eski, yeni in ciftler:
            sayi = n.count(eski)
            if sayi != 1:
                raise RuntimeError("{}: mutasyon metni {} kez bulundu (1 olmali): {!r}".format(
                    yol.name, sayi, eski[:60]))
            n = n.replace(eski, yeni, 1)
        yol.write_bytes((n.replace("\n", "\r\n") if crlf else n).encode("utf-8"))


def main():
    tum = sorted({y for _a, ds, _c, _h in MUTASYONLAR for y in ds})
    orijinal = {y: y.read_bytes() for y in tum}
    sha0 = {y: hashlib.sha256(b).hexdigest() for y, b in orijinal.items()}
    yaz("# T228-D + T228-D2 mutasyon ciktisi · {} · {}".format(time.strftime("%Y-%m-%d %H:%M:%S"),
                                                    Path(PY).name))
    yakalanan = 0
    uygulanamayan = 0
    try:
        for ad, dosyalar, ciftler, hedefler in MUTASYONLAR:
            try:
                uygula(dosyalar, ciftler, orijinal)
            except RuntimeError as exc:
                uygulanamayan += 1
                yaz("{}: UYGULANAMADI — {}".format(ad, exc))
                for y in dosyalar:
                    y.write_bytes(orijinal[y])
                continue
            try:
                kod, ran, son, dusen = kos()
            finally:
                for y in dosyalar:
                    y.write_bytes(orijinal[y])
            durum = {h: ("DUSTU" if h in dusen else "GECTI") for h in hedefler}
            tuttu = all(v == "DUSTU" for v in durum.values())
            yakalanan += 1 if tuttu else 0
            yaz("{}: cikis={} ran={} son={!r} -> {}; hedef={}; dusen={}".format(
                ad, kod, ran, son, "YAKALANDI" if tuttu else "KACTI", durum, dusen))
    finally:
        for y, b in orijinal.items():
            y.write_bytes(b)
    esit = all(hashlib.sha256(y.read_bytes()).hexdigest() == sha0[y] for y in tum)
    yaz("geri yukleme sha esit: {} ({})".format(
        esit, ", ".join("{}={}".format(y.relative_to(KOK).as_posix(), sha0[y][:12]) for y in tum)))
    yaz("OZET: {}/{} mutasyon TUM hedef testleriyle yakalandi; uygulanamayan {}".format(
        yakalanan, len(MUTASYONLAR), uygulanamayan))
    kod, ran, son, dusen = kos()
    yaz("TEMIZ KOSUM (mutasyonsuz): cikis={} ran={} son={!r} dusen={}".format(kod, ran, son, dusen))
    CIKTI.write_text("\n".join(SATIRLAR) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

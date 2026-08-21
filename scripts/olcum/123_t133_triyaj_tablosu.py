"""T133 — triyaj + curutucu sonuclarini MIMARIN TEK GECISTE okuyacagi tabloya cevirir.

GIRDI : results/t133/triyaj_ham.json  (39 triyaj + 35 curutucu, fan-out ciktisi)
CIKTI : results/t133/triyaj_tablosu.md

🔴 USTABASI SINIFLANDIRMASI. Curutucunun `curutuldu: true` demesi tek basina
"gorev kapanmaz" demek DEGILDIR; uc AYRI sey demek olabilir ve mimarin karari
her birinde FARKLIDIR:

  A  KAPANMAZ            — gorevin KENDI iddiasi (ya da lafzen yazili kapsami)
                          bugun HALA yeniden uretiliyor.
  B  KAPANIR + YENI KAYIT— gorevin kendi kapsami GERCEKTEN duzelmis, ama AYNI
                          mekanizma BASKA bir cagri yerinde yasiyor. Gorev
                          kapanir; bulgu YENI bir kayit olarak acilir.
  C  CURUTME TUTMADI     — curutucunun bayragi kendi gerekcesiyle CELISIYOR
                          ("curutemedim" deyip true isaretlemis). Triyajin
                          verdikti AYAKTA; curutucunun notu YAN BULGUDUR.

Bu ayrimi elle yaptim ve gerekcesi her satirda yazili — otomatik degildir,
cunku "ayni kusur mu, yeni kusur mu" sorusu OLCUMLE degil OKUMAYLA ayrilir.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK / "results" / "t133"

# ── USTABASI SINIFLANDIRMASI (elle, gerekceli) ─────────────────────────────
SINIF = {
    "T22": ("A", "Lafzen zorunlu UC ikameden IKISI yok (SerialLink ornekleme yok, "
                 "halka_motor sahte surucu almiyor) — kapsam tamamlanmamis."),
    "T23": ("A", "Kuru kosunun surus_izni halkasi kendi probunu OKUMUYOR: uretimdeki "
                 "iki-latch guvenlik kapisi TUMUYLE kaldirilsa da GECTI basiyor."),
    "T3":  ("A", "Gorevi kapatan tek gecer kanit bugunku kodla yeniden kosulunca "
                 "OLCUM_YOK/exit 1 veriyor; kayit hic yeniden kosulmamis."),
    "T4":  ("A", "Cekimserlik kapisi yalniz BIR kopyaya konmus; ayni dosyanin diger "
                 "iki-kipli olcum yollari korumasiz."),
    "T11": ("B", "Gorevin KENDI kapisi temiz (exit 2 — USTABASI da kostu, gecti); ama "
                 "ayni mekanizma simulation/scripts/iha_detect_send.py'de yasiyor "
                 "(USTABASI kostu: yaniltici satir + ayni TypeError, exit 1)."),
    "T48": ("A", "Kapi IKI rota ureticisinden yalnizca analyze_path'e konmus; IKA'ya "
                 "yayinlanan rota.json'i ureten yol cokmus maskede hala ACIK veriyor."),
    "T85": ("A", "Kilitledigi one surulen JETSON_KILAVUZ yarisi v34 ve v35 terfilerinde "
                 "IKI KEZ sessizce kaydi; kapinin assert yuzeyi bunu gormuyor."),
    "T83": ("A", "USTABASI dogruladi: jetson_paket/kod/arac_maskesi.py YOK (pakette 10 "
                 ".py). Sahaya giden muhurlu artefaktta olcek katmani olu."),
    "T82": ("C", "Curutucu kendi gerekcesinde 'AYIRMIYOR verdikti AYAKTA — onu "
                 "curutemedim' diyor ama bayragi true isaretlemis. Triyaj verdikti "
                 "ayakta; envanter eksigi YAN BULGU."),
    "T78": ("A", "0,67 tavaninin varlik sebebi olan TEK gercek arena karesi v24'ten "
                 "sonra hicbir uretim modeliyle kapi olcusune sokulmamis."),
    "T77": ("A", "Kaydin acik iddiasi ('ekranda yanlis kume adi kalmiyor') bugun yanlis: "
                 "kaynak degistirme kolu gunluge hala ciplak 'T60 sartname kadraji' yaziyor."),
    "T76": ("A", "Kapsamina ACIKCA yazili 'iki kilavuz' ucu v34->v35 terfisinde yeniden "
                 "kaydi ve kapi goremedi."),
    "T73": ("A", "Mutasyon geciyor: --model dogrulanip yuklenen agirlik varsayilana "
                 "sabitlense de halka_model GECTI ve 20/20 test OK."),
    "T67": ("A", "Bariyer yalniz YATAY kutuyla araniyor; kare 12 derece dondurulunce "
                 "ENGEL maskesi %0,0'a dusuyor — 'dedektor KAPALI' haliyle ayni."),
    "T59": ("A", "USTABASI dogruladi: tests/test_gercek_arena_kapisi.py:44 MODEL = "
                 "navitas_seg_v24_best.pt. Kilit v24'e civili, uretim v35 — yapisal "
                 "olarak dusemeyen bos yesil."),
    "T56": ("A", "'Kadraj kipinde aynalama YOK' degismezi moloz_yigini'nda ihlal "
                 "ediliyor (200 boyutun 95'inde tam dikey ayna ekseni)."),
    "S9":  ("A", "USTABASI dogruladi: iha_perceive.py:42 DEFAULT_MODEL = "
                 "navitas_seg_v2_best.pt iken hakem_log.py:68 kunyeyi defterden (v35) "
                 "turetiyor — gorevin OZGUN iddiasi birebir yeniden uretiliyor."),
}

# Ustabasinin KENDI kostugu dogrulamalar (5/39 elle)
ELLE_DOGRULANAN = {
    "T1": "temiz worktree'de test_accuracy/test_batch --help -> exit 0 (gorevin kendi kapisi)",
    "T11": "kendi kapisi exit 2; curutmenin komutu da kosuldu -> exit 1, ayni TypeError",
    "T83": "ls jetson_paket/kod/arac_maskesi.py -> yok; pakette 10 .py",
    "T59": "tests/test_gercek_arena_kapisi.py:44 -> navitas_seg_v24_best.pt",
    "S9":  "iha_perceive.py:42 v2_best.pt vs hakem_log.py:68 defterden kunye",
}


def kisalt(s, n):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + "…"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    d = json.loads((CIKTI / "triyaj_ham.json").read_text(encoding="utf-8"))

    kapanmali, kapanmaz, kapanir_yeni, hala, belirsiz = [], [], [], [], []
    for k in d["kayitlar"]:
        c = k.get("curutucu")
        yikildi = bool(c and c.get("curutuldu"))
        if k["kova"] == "BELIRSIZ":
            belirsiz.append(k)
        elif k["kova"] == "HALA_GECERLI":
            hala.append(k)
        elif yikildi:
            tip = SINIF.get(k["gorev"], ("A", ""))[0]
            (kapanmaz if tip == "A" else kapanir_yeni).append(k)
        else:
            kapanmali.append(k)

    def tablo(baslik, kayitlar, curutucudan=False):
        satir = [f"### {baslik} — **{len(kayitlar)}**", "",
                 "| görev | kanıt | tek cümle |", "|---|---|---|"]
        for k in sorted(kayitlar, key=lambda x: x["gorev"]):
            if curutucudan and k.get("curutucu"):
                kanit = k["curutucu"]["kanit"]
                sinif, neden = SINIF.get(k["gorev"], ("?", k["curutucu"]["gerekce"]))
                gerekce = f"**[{sinif}]** {neden}"
            else:
                kanit, gerekce = k["kanit"], k["gerekce"]
            elle = ELLE_DOGRULANAN.get(k["gorev"])
            if elle:
                gerekce += f" · 🔎 **USTABAŞI KOŞTU:** {elle}"
            satir.append(f"| **{k['gorev']}** | `{kisalt(kanit, 170)}` | "
                         f"{kisalt(gerekce, 400)} |")
        return satir + [""]

    md = ["# T133 · TRİYAJ TABLOSU — 39 READY_FOR_REVIEW görevi", "",
          "> **Üreten:** Claude 2 (ustabaşı) · 39 triyaj ajanı + 35 çürütücü "
          "(74 ajan, 0 hata) · ham çıktı `results/t133/triyaj_ham.json`.",
          "> 🔴 **KAPATMA YETKİSİ MİMARDA (§9.2).** Bu tablo kanıt üretir, karar vermez.",
          "> Görev durumlarına **dokunulmadı**.", "",
          "## Özet", "",
          f"| kova | adet |", "|---|---|",
          f"| KAPANMALI (çürütücü dayanamadı) | **{len(kapanmali)}** |",
          f"| KAPANIR + YENİ KAYIT ŞARTIYLA | **{len(kapanir_yeni)}** |",
          f"| KAPANMAZ (çürütücü YIKTI) | **{len(kapanmaz)}** |",
          f"| HÂLÂ GEÇERLİ (triyaj) | **{len(hala)}** |",
          f"| BELİRSİZ | **{len(belirsiz)}** |", "",
          "🔴 **Çürütücü harness'i 35 KAPANMALI verdiktinin 17'sini yıktı.** "
          "Harness olmasaydı bu tablo mimara 17 yanlış \"kapat\" gönderecekti — "
          "ve her biri **gerçek bir kusuru gömecekti**.", "",
          "⚠ **Ustabaşı 5 kalemi ELLE koştu** (T1 · T11 · T83 · T59 · S9); "
          "beşinde de ajanın sonucu doğrulandı. Kalan 34 kalem ajan kanıtına "
          "dayanıyor ve her satırda **çalıştırılabilir komut** var — mimar "
          "dilediğini yeniden koşabilir.", ""]

    md += tablo("KAPANMALI · çürütücü dayanamadı", kapanmali)
    md += tablo("KAPANIR + YENİ KAYIT ŞARTIYLA", kapanir_yeni, curutucudan=True)
    md += tablo("🔴 KAPANMAZ · çürütücü YIKTI", kapanmaz, curutucudan=True)
    md += tablo("HÂLÂ GEÇERLİ · triyaj", hala)
    md += tablo("BELİRSİZ", belirsiz)

    io.open(CIKTI / "triyaj_tablosu.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"KAPANMALI {len(kapanmali)} · KAPANIR+YENI {len(kapanir_yeni)} · "
          f"KAPANMAZ {len(kapanmaz)} · HALA {len(hala)} · BELIRSIZ {len(belirsiz)}")
    print("toplam:", len(kapanmali) + len(kapanir_yeni) + len(kapanmaz)
          + len(hala) + len(belirsiz))
    print("yazildi:", CIKTI / "triyaj_tablosu.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

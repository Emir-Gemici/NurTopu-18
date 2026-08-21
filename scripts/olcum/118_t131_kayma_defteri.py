"""T131 — SURUM-OTESI KAYMA DEFTERI: taban tasiyan alanlarin terfi gecmisi.

NEDEN (D-257 §4, mimar olcumu): terfi, kendisini uyaran kapiyi SUSTURDU.
    terfi ONCESI (v34 taban) : figur %9,03 · taban %0,49 · oran 18,43  🔴 DIKKAT
    terfi SONRASI (v35 taban): figur %9,03 · taban %9,03 · oran  1,00  (uyari YOK)
Davranis TASARIM GEREGI dogrudur (oran aday<->uretim kiyasidir); sorun
KUMULATIF hareketin hicbir yerde GORUNMEMESIDIR. Bu, projenin en sik kusur
sinifinin (bayat/kaymis taban, 8 ornek) mekanizma halidir: taban yanlis
kopyalanmiyor, HER TERFIDE MESRU OLARAK kaiyor.

🔴 BU BETIK KAPI DEGILDIR, ESIK KOYMAZ (T131'in acik kisiti). Yalnizca
`config/model_registry.json`'un GIT GECMISINI tarar ve taban tasiyan alanlarin
surumden surume nasil hareket ettigini TEK TABLODA gorunur kilar.

YONTEM: her commit icin `git show <commit>:config/model_registry.json` okunur
ve etkin profil (`profiles[default_profile]`) ayristirilir. Eski surumlerde
alan adlari FARKLI olabilir; bulunamayan alan `None` yazilir ve "sema farkli"
diye isaretlenir — UYDURULMAZ.

CIKTI: results/t131/kayma_defteri.json + kayma_defteri.md
"""
from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
DOSYA = "config/model_registry.json"
CIKTI = KOK / "results" / "t131"

# Taban tasiyan / karar besleyen alanlar: (etiket, erisim yolu)
ALANLAR = [
    ("model_id", ("model_id",)),
    ("imgsz", ("imgsz",)),
    ("sha256", ("sha256",)),
    ("kabul_kumesi", ("kabul_kumesi",)),   # 🔴 her sayinin PAYDASI (D-214)
    # T132: kumenin PARMAK IZI de surumler arasi izlenir. Yol ayni kalip
    # icerigin degismesi, sessizce kiyaslanamaz sayilar uretir (D-263 §4.3).
    ("kume parmak izi", ("kabul_kumesi_parmak_izi", "ozet")),
    ("kume dosya sayisi", ("kabul_kumesi_parmak_izi", "n")),
    ("K0 figur_zemin_orani", ("metrics", "k0_korluk", "figur_zemin_orani")),
    ("K0 figur (METINDEN)", ("metrics", "k0_korluk", "olculen")),
    ("K1 rota", ("metrics", "k1_rota_uretimi", "olculen")),
    ("K2 basma %", ("metrics", "k2_moloza_basma_yuzde", "olculen")),
    ("K3 agir %", ("metrics", "k3_agir_basma_yuzde", "olculen")),
    ("K4 arena disi %", ("metrics", "k4_arena_disi_yuzde", "olculen")),
    ("K5 bariyer px", ("metrics", "k5_bariyer_kesisimi_px", "olculen")),
    ("karar cevrilmesi", ("metrics", "karar_cevrilmesi", "olculen")),
    ("gercek kare kaplama", ("metrics", "gercek_kare_zemin_kaplamasi", "olculen")),
    # 🔴 v30'da AYNI SEY BASKA ADLA duruyordu; ad degisikligini "alan dogdu"
    # diye okumak, kayma defterinin KENDI kusuru olurdu.
    ("gercek kare (ESKI ad)", ("metrics", "gercek_kare_gecen", "olculen")),
    ("cati kacagi", ("metrics", "cati_kacagi", "olculen")),
]


def kos(*arg: str) -> str:
    p = subprocess.run(arg, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(KOK))
    return p.stdout


def gez(veri, yol):
    """Ic ice alan erisimi; yoksa None (UYDURMA YOK)."""
    su = veri
    for anahtar in yol:
        if not isinstance(su, dict) or anahtar not in su:
            return None
        su = su[anahtar]
    return su


def main() -> int:
    ham = kos("git", "log", "--follow", "--format=%H|%ad|%s", "--date=short",
              "--reverse", "--", DOSYA).splitlines()
    satirlar = []
    for kayit in ham:
        if "|" not in kayit:
            continue
        sha, tarih, konu = kayit.split("|", 2)
        icerik = kos("git", "show", f"{sha}:{DOSYA}")
        if not icerik.strip():
            continue
        try:
            veri = json.loads(icerik)
        except json.JSONDecodeError:
            satirlar.append({"commit": sha[:8], "tarih": tarih,
                             "konu": konu[:60], "hata": "JSON ayristirilamadi"})
            continue
        profil_adi = veri.get("default_profile")
        profil = (veri.get("profiles") or {}).get(profil_adi) if profil_adi else None
        if profil is None:
            satirlar.append({"commit": sha[:8], "tarih": tarih,
                             "konu": konu[:60], "sema": "FARKLI (profiles yok)"})
            continue
        satir = {"commit": sha[:8], "tarih": tarih, "konu": konu[:60],
                 "profil": profil_adi, "sema": "tanidik",
                 "_metrik_anahtarlari": sorted((profil.get("metrics") or {}).keys())}
        for etiket, yol in ALANLAR:
            deger = gez(profil, yol)
            satir[etiket] = deger
        satirlar.append(satir)

    # Kayma: ardisik surumlerde DEGISEN alanlar
    kaymalar = []
    onceki = None
    for s in satirlar:
        if s.get("sema") != "tanidik":
            continue
        if onceki is not None and s.get("model_id") != onceki.get("model_id"):
            fark = {}
            for etiket, _ in ALANLAR:
                if etiket in ("model_id", "sha256"):
                    continue
                a, b = onceki.get(etiket), s.get(etiket)
                if a != b:
                    fark[etiket] = {"onceki": a, "yeni": b}
            # Sema hareketi: alan DOGDU mu, YOK OLDU mu? (ad degisikligi burada
            # gorunur — yoksa yeniden adlandirma "yeni olcum" gibi okunur.)
            eski_a = set(onceki.get("_metrik_anahtarlari") or [])
            yeni_a = set(s.get("_metrik_anahtarlari") or [])
            kaymalar.append({
                "gecis": f"{onceki.get('model_id')} -> {s.get('model_id')}",
                "tarih": s["tarih"], "commit": s["commit"], "degisen": fark,
                "alan_dogdu": sorted(yeni_a - eski_a),
                "alan_yok_oldu": sorted(eski_a - yeni_a),
            })
        if s.get("model_id"):
            onceki = s

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "kayma_defteri.json", "w", encoding="utf-8").write(
        json.dumps({
            "_ne": "T131 · surum-otesi kayma defteri. KAPI DEGIL, ESIK KOYMAZ.",
            "_kaynak": f"git gecmisi · {DOSYA} · {len(satirlar)} surum",
            "_uyari": ("Bulunamayan alan None yazilir ve sema FARKLI diye "
                        "isaretlenir; deger UYDURULMAZ."),
            "surumler": satirlar, "kaymalar": kaymalar,
        }, ensure_ascii=False, indent=1))

    # Insan okumasi: tek tablo
    tanidik = [s for s in satirlar if s.get("sema") == "tanidik"]
    basliklar = ["tarih", "model_id"] + [e for e, _ in ALANLAR
                                          if e not in ("model_id", "sha256")]
    md = ["# T131 · SÜRÜM-ÖTESİ KAYMA DEFTERİ", "",
          "> Bu tablo bir **kapı değildir** ve eşik koymaz (T131 kısıtı).",
          "> Amaç: taban taşıyan alanların terfiden terfiye nasıl hareket",
          "> ettiğini **tek yerde görünür** kılmak (D-257 §4).", "",
          "| " + " | ".join(basliklar) + " |",
          "|" + "---|" * len(basliklar)]
    for s in tanidik:
        md.append("| " + " | ".join(
            str(s.get(b, "")) if s.get(b) is not None else "—"
            for b in basliklar) + " |")
    # 119'un BUGUNKU yeniden olcumu varsa deftere katilir: K0 tabaninin gercek
    # gecmisi defterde SAYI olarak durmuyor (v30'da yalniz duz metinde vardi).
    yol119 = CIKTI / "k0_taban_gecmisi.json"
    if yol119.exists():
        y = json.loads(yol119.read_text(encoding="utf-8"))
        md += ["", "## K0 figür tabanı — TEK ALETLE bugün yeniden ölçüldü (119)", "",
               f"> Alet: `{y['_alet']['fonksiyon']}` · CONF {y['_alet']['CONF']} · "
               f"imgsz {y['_alet']['INFER_SIZE']} · figür `{y['_alet']['figur']}`",
               "> Defterdeki değerler düz metne gömülüydü; bunlar **ölçümdür**.", "",
               "| sürüm | figür zemin | not |", "|---|---|---|"]
        for o in y["olcumler"]:
            md.append(f"| {o['surum']} | {100*o['figur']:.2f}% | "
                      + ("" if o["donem_512"] else "⚠ dönem-tutarlı değil (640 dönemi)")
                      + " |")
        md += ["", "| terfi | taban | figür | oran | denetçinin bandı |",
               "|---|---|---|---|---|"]
        for z in y["terfi_zinciri"]:
            md.append(f"| {z['terfi']} | {100*z['taban']:.2f}% | "
                      f"{100*z['figur']:.2f}% | {z['oran']:.2f}× | "
                      + (z["yon"] if z["band_disi"] else "band içi — uyarı yok") + " |")

    md += ["", "## Terfi geçişlerinde DEĞİŞEN alanlar", ""]
    for k in kaymalar:
        md.append(f"### {k['gecis']} · {k['tarih']} · `{k['commit']}`")
        if not k["degisen"]:
            md.append("- (taban taşıyan alanlarda değişiklik yok)")
        for etiket, d in k["degisen"].items():
            md.append(f"- **{etiket}**: `{d['onceki']}` → `{d['yeni']}`")
        if k["alan_dogdu"]:
            md.append(f"- 🆕 **metrik alanı DOĞDU:** `{'`, `'.join(k['alan_dogdu'])}`")
        if k["alan_yok_oldu"]:
            md.append(f"- ❌ **metrik alanı YOK OLDU:** `{'`, `'.join(k['alan_yok_oldu'])}`")
        md.append("")
    io.open(CIKTI / "kayma_defteri.md", "w", encoding="utf-8").write(
        "\n".join(md) + "\n")

    print(f"surum kaydi: {len(satirlar)} · tanidik sema: {len(tanidik)} · "
          f"terfi gecisi: {len(kaymalar)}")
    for k in kaymalar:
        print(f"  {k['gecis']:26s} {k['tarih']}  degisen alan: {len(k['degisen'])}")
    # T132 · D-263 §4.4: bir olcum ekseninin defterden CIKMASI hicbir yerde
    # uyari uretmiyordu — `mask_map50` v34 terfisinde SESSIZCE dustu ve bunu
    # ancak bu arac gosterdi. Artik stdout'ta da BAGIRIR.
    kayiplar = [(k["gecis"], k["alan_yok_oldu"]) for k in kaymalar
                if k["alan_yok_oldu"]]
    if kayiplar:
        # ⚠ stdout'ta EMOJI YOK: konsol cp1254 ve yonlendirilmis cikti
        # `UnicodeEncodeError` ile PATLIYOR. Isaret ASCII tutulur.
        print("\n[!] METRIK ALANI YOK OLMUS (olcum ekseni defterden CIKTI):")
        for gecis, alanlar in kayiplar:
            print(f"   {gecis}: {', '.join(alanlar)}")
        print("   Bu bir KAPI DEGILDIR - kaybin MESRU olup olmadigi insan"
              " kararidir; arac yalniz GORUNUR kilar.")
    print(f"yazildi: {CIKTI / 'kayma_defteri.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

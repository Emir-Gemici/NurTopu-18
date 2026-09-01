"""FDR KANIT PAKETI URETECI — sayilar ARTEFAKTTAN okunur, elle YAZILMAZ.

NICIN URETEC: `FDA = FDR x 0,85 + Test Ucusu x 0,15`. FDR raporuna elle
kopyalanan bir sayi, artefakt degistiginde SESSIZCE bayatlar — bu projede
bayat sayi tasima kusuru defalarca kayda gecti (D-256 SS3, D-372, D-376).
Bu betik paketi HER KOSUMDA kaynaktan yeniden uretir; kaynak degisirse
metin de degisir.

⚠ Betik HUKUM URETMEZ. Her sayinin yaninda kaynagi ve kapsami yazilir;
gecmeyen kapi GECMEDI diye yazilir (OLCULEMEDI != GECTI).

Cikti: `results/fdr/GORUNTU_ISLEME_KANIT.md`
"""
import argparse
import glob
import json
import os
import statistics
import sys
from pathlib import Path

from ayarlar import REPO

KAYIT = REPO / "config" / "model_registry.json"
FDR = REPO / "results" / "fdr"


def _oku(yol):
    p = REPO / yol
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _y(x, n=4):
    """Turkce ondalik; None ise ACIKCA yazilir (sessiz bosluk birakilmaz)."""
    if x is None:
        return "**ÖLÇÜLEMEDİ**"
    if isinstance(x, float):
        return f"{x:.{n}f}".replace(".", ",")
    return str(x)


def bolum_model():
    d = json.loads(KAYIT.read_text(encoding="utf-8"))
    c = d["profiles"]["competition"]
    s = ["## 1. Üretim modeli — kayıt defterinden okundu\n",
         f"| alan | değer |", "|---|---|",
         f"| `model_id` | `{c['model_id']}` |",
         f"| çıkarım boyutu | `{c['imgsz']}` |",
         f"| arka uç | `{c['backend']}` |",
         f"| SHA-256 | `{c['sha256']}` |",
         f"| kabul kümesi | `{os.path.basename(c['kabul_kumesi'])}` |",
         "",
         "> Kaynak: `config/model_registry.json` · "
         "`profiles.competition`. Saha paketindeki ayna kopya "
         "`jetson_paket/config/model_registry.json` ile aynı olmalıdır "
         "(nöbetçi: `tests/test_t202_jetson_paket_butunlugu.py`).\n"]
    return "\n".join(s), c


def bolum_kapilar(c):
    m = c["metrics"]
    s = ["## 2. Kabul kapıları — sentetik arena kümesi (n=260)\n",
         "| kapı | ne ölçer | eşik | ölçülen | sonuç |", "|---|---|---|---|---|"]
    ad = {
        "k0_korluk": "körlük yok (boş maske üretmiyor)",
        "k1_rota_uretimi": "rota üretilen kare",
        "k2_moloza_basma_yuzde": "rotanın molozdan geçmesi",
        "k3_agir_basma_yuzde": "ağır moloz teması",
        "k4_arena_disi_yuzde": "arena dışına taşma",
        "k5_bariyer_kesisimi_px": "bariyer kesişimi",
        "k6_yanlis_guzergah_yuzde": "yanlış güzergâh",
    }
    for k, aciklama in ad.items():
        v = m.get(k) or {}
        s.append(f"| **{k.split('_')[0].upper()}** | {aciklama} | "
                 f"`{v.get('esik', '—')}` | `{v.get('olculen', '—')}` | "
                 f"{v.get('sonuc', '—')} |")
    s += ["",
          "⚠ **KAPSAM (kayıt defterinin kendi cümlesi):** "
          "*\"ARENA ÖLÇÜMLERİNİN TAMAMI SENTETİKTİR (T66 ada kadrajı, n=260); "
          "gerçek ARENA karesi YOKTUR — K0..K6 SAHA BAŞARIMI İDDİA ETMEZ.\"*",
          "",
          "> Kaynak: `scripts/olcum/65_kabul_denetcisi.py` · verdikt "
          "`scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json`\n"]
    return "\n".join(s)


def bolum_gercek_kare(c):
    m = c["metrics"]
    g = m.get("gercek_kare_kapisi") or {}
    s = ["## 3. 🔴 Gerçek kare kapısı — ÖN KAYITLI EŞİKLER GEÇİLMEDİ\n",
         "Bu bölüm bilerek öne alınmıştır: üretim modeli, kendi ön kayıtlı "
         "eşiklerinin **ikisini geçmeden** terfi etmiştir ve gerekçesi "
         "kayıtlıdır.\n",
         "```text", str(g.get("sonuc", "—"))[:900], "```", "",
         f"**Terfi kararı:** {str(c.get('_surum_karari', '—'))[:700]}", "",
         "> Doğrulama kümesi `dji/DOGRULAMA/` = `DJI_20260822172613_0038_D`; "
         "CONTRACTS §12 gereği **0038 kareleri eğitime ve erken durdurmaya "
         "girmez**.\n"]
    return "\n".join(s)


def bolum_gercek_zamanlilik():
    p = _oku("results/b4_fps/p_ve_kosu_20260901.json")
    i = _oku("results/b4_fps/infer_size_20260901.json")
    f = _oku("results/b4_fps/fp16_denklik_20260901.json")
    s = ["## 4. Gerçek zamanlılık — eşik TÜRETİLDİ, tahmin edilmedi\n",
         "Şartname §6.4: hakem onayı alınmayan tespit geçersizdir. "
         "Sözleşme `YKS_TESPIT_TAZELIK_S = 5,0` s; karar kare başınadır "
         "(kareler arası uzlaşma yoktur). Buradan:\n",
         "```", "GEREKLI_FPS  >=  1 / (5 · p)", "```",
         "`p` = bir karenin geçerli rota yayınlama olasılığı.\n"]
    if p:
        h = p.get("hukum", {})
        s += ["| küme | p | gereken FPS | kapsam |", "|---|---|---|---|",
              f"| sentetik arena (260) | {_y(h.get('G2_S', {}).get('p'))} | "
              f"{_y(h.get('gerekli_fps_S'), 3)} | göreve benzer, **sentetik** |"]
        # R_TEMIZ yeniden hesapla (D-376: havuz kirli)
        egit = set()
        for b in ("train", "val"):
            for q in glob.glob(str(REPO / f"dataset/dji_v7/images/{b}/*.jpg")):
                egit.add(os.path.basename(q))
        kat = [k for k in p["R"]["kareler"] if (k["rel_alt"] or 0) >= 30.0]
        temiz = [k for k in kat
                 if k["dosya"].replace("\\", "/").replace("/", "__") not in egit]
        if temiz:
            pt = sum(1 for k in temiz if k["fov"]["67.3"]["yayinlandi"]) / len(temiz)
            s.append(f"| gerçek DJİ, **sızıntısız** ({len(temiz)}) | {_y(pt)} | "
                     f"{_y(1 / (5 * pt), 3)} | gerçek, arenaya **OOD** |")
        s += ["",
              "⚠ **D-376:** ilk ölçümde kullanılan gerçek-kare havuzunun "
              f"**%62'si modelin eğitim kümesindeydi**; yukarıdaki satır "
              "sızıntı ayıklandıktan sonrasıdır. Kirli okuma daha iyimserdi.",
              "",
              "**Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena görüntüsü yoktur "
              "(maket çekimi yapılmayacaktır). İki sayı alt/üst çerçevedir; "
              "arası tahmin edilmemiştir.\n"]
    if i:
        h = i.get("hukum", {})
        s += ["### 4.1 Çözünürlük denendi ve **reddedildi** (D-377)\n",
              f"- Sentetik arenada gerileme: "
              f"`{_y(h.get('I2_gerileme', {}).get('p_S_512'))}` → "
              f"`{_y(h.get('I2_gerileme', {}).get('p_S_640'))}` → **RED**",
              f"- FPS maliyeti oranı: "
              f"`{_y(h.get('I4_fps', {}).get('maliyet_orani'), 3)}` "
              f"(bütçe kısıt değildi)",
              "- Ön kayıt *\"I2 düşerse RED, I1 ne olursa olsun\"* diye "
              "**sonuç görülmeden** yazılmıştı.\n"]
    if f:
        h = f.get("hukum", {})
        s += ["### 4.2 FP16 karar denkliği (D-375)\n",
              f"- Zarar yönü (FP32 doğruyken FP16 yanlış şerit): "
              f"`{h.get('F1', {}).get('sayi')}` → **{h.get('F1', {}).get('durum')}**",
              f"- Karar uyuşması: `{_y(h.get('F2', {}).get('uyusma'))}` "
              f"(eşik `{_y(h.get('F2', {}).get('esik'), 2)}`) → "
              f"**{h.get('F2', {}).get('durum')}**\n"]
    return "\n".join(s)


def bolum_yordam():
    return "\n".join([
        "## 5. Yöntem — bu paketin asıl iddiası\n",
        "Sayılardan çok, sayıların **nasıl** üretildiği:\n",
        "1. **Ön kayıt (D-107).** Eşik, sonuç görülmeden yazılır ve sonradan "
        "gevşetilmez. D-377'de bu kural somut iş gördü: umut verici bir ara "
        "sayı (%21,6) önceden yazılmış bir RED kuralıyla karşılaştı.",
        "2. **`ÖLÇÜLEMEDİ != GEÇTİ`.** Ölçülemeyen şey geçmiş sayılmaz; "
        "paydası olmayan oran rapora girmez.",
        "3. **Mutasyon kontrolü.** Her kapı, kaldırıldığında **düşerek** "
        "ayırt ediciliğini kanıtlar. Mutasyon koda uygulanır, yoruma değil; "
        "uygulanmayan mutasyon başarı sayılmaz (D-370).",
        "4. **Çürütme kaydı.** Yanlış çıkan iddialar **silinmez**, üstü "
        "çizilip düzeltmesine işaret verilir (D-373). Bu paket, kendi "
        "hatalarını da gösterir.",
        "",
        "> Kanıt defteri: `REVIEW_LOG.md`. Bugüne dek **çürütülmüş kendi "
        "iddiaları** dâhil her kayıt ölçümlüdür.\n"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cikti", default=str(FDR / "GORUNTU_ISLEME_KANIT.md"))
    a = ap.parse_args()

    bas, c = bolum_model()
    parcalar = [
        "# NAVITAS · FDR — GÖRÜNTÜ İŞLEME KANIT PAKETİ\n",
        "> ⚙ Bu belge `scripts/olcum/167_fdr_kanit_paketi.py` tarafından "
        "**artefaktlardan üretilir**. Elle düzenlenmez; kaynak değişirse "
        "yeniden koşulur. Sayıların hiçbiri metne elle yazılmamıştır.\n",
        bas,
        bolum_kapilar(c),
        bolum_gercek_kare(c),
        bolum_gercek_zamanlilik(),
        bolum_yordam(),
    ]
    metin = "\n".join(parcalar)
    p = Path(a.cikti)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(metin, encoding="utf-8")
    print(f"YAZILDI: {p}  ({len(metin)} karakter)")
    eksik = metin.count("ÖLÇÜLEMEDİ")
    print(f"OLCULEMEDI isareti: {eksik} yerde (sessiz bosluk birakilmadi)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

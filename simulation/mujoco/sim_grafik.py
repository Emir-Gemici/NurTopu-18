"""SİM GRAFİKLERİ — ON_KAYIT H1-K6 (T214-A): başarı oranı (kaynak × seviye), görev süresi
dağılımı, takip hatası / varış mesafesi, sistem tepkileri. ÖLÇÜMDEN üretilir, elle düzenlenmez.

Girdi : results/fdr_sprint_20260910/H1/kosum_tur3/ozet_kosum.json + <kaynak>_<h>_<lv>_<tohum>.json
        results/fdr_sprint_20260910/H1/k3_uretim_boru/ozet_k3_uretim.json (K3 alt başlığı)
Çıktı : FDR/sekiller/sim_basari_orani · sim_gorev_suresi · sim_takip_hatasi · sim_sistem_tepkileri
        (.svg + .png). Her grafiğin veri kaynağı JSON yolu ALT YAZIDA ve SVG `dc:description`
        metaverisinde durur.
Deterministik: `svg.hashsalt` sabit, tarih metaverisi yok, titreşim tohumlu → aynı JSON aynı
bayt (nöbetçi: tests/test_sim_mujoco_olcum.py E).
Renk: dataviz referans paletinin ilk üç kategorik yuvası sabit sırada (mavi / turuncu / aqua;
`validate_palette.js --pairs all` light: GEÇTİ; aqua #1baf7a yüzeye 2,74:1 → kontrast WARN, rahatlatma:
doğrudan çubuk/değer etiketleri + README_T214A tablo görünümü); metin seri rengi taşımaz, kimlik göstergede
ve çubuk etiketinde de yazılıdır (renk tek başına taşıyıcı değil). SENTETİK etiketi başlıkta.

Kullanım:  venv python simulation/mujoco/sim_grafik.py [--out FDR/sekiller]
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.ticker import PercentFormatter               # noqa: E402

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from costmap_path_finder import TAKIP_HATA_M               # noqa: E402  CONTRACTS §4 tek kaynak
from karar_sozlesmesi import HB_KENAR_M, SARTNAME_IKA_GOREV_SURESI_S   # noqa: E402

KOSUM_DIR = KOK / "results" / "fdr_sprint_20260910" / "H1" / "kosum_tur3"
K3_DIR = KOK / "results" / "fdr_sprint_20260910" / "H1" / "k3_uretim_boru"
SEKIL_DIR = KOK / "FDR" / "sekiller"
GRAFIKLER = ("sim_basari_orani", "sim_gorev_suresi", "sim_takip_hatasi", "sim_sistem_tepkileri")
KAYNAKLAR = ("gt", "model", "uretim")
ETIKET = {"gt": "YER GERÇEĞİ (gt)", "model": "ÜRETİM MODELİ · mozaik (model)",
          "uretim": "ÜRETİM BORU HATTI · kare-bazlı (uretim)"}
KISA = {"gt": "gt", "model": "model", "uretim": "uretim"}
RENK = {"gt": "#2a78d6", "model": "#eb6834", "uretim": "#1baf7a"}   # dataviz yuva 1–3 (light)
MUREKKEP, IKINCIL, SOLUK, IZGARA, ZEMIN = "#0b0b0b", "#52514e", "#8a8983", "#e4e3de", "#ffffff"
SENARYOLAR = ("kolay", "orta", "zor")
SVG_TUZ = "navitas-t214a-sim-grafik"
ALT_BASLIK_SUTUN = 125     # 7,6 in genişlik, 7,6 pt: kesilmesin diye sarılır (ölçüldü: ~135 karakter sığıyor)
ALT_YAZI_SUTUN = 150       # 6,3 pt alt yazı


def _goreli(p: Path) -> str:
    p = Path(p)
    return (str(p.relative_to(KOK)) if p.is_relative_to(KOK) else str(p)).replace("\\", "/")


def veri_yukle(kosum_dir: Path = KOSUM_DIR, k3_dir: Path = K3_DIR) -> dict:
    """Grafiklerin tüm girdisi (JSON'lardan). Koşum satırları dosya adına göre sıralı."""
    kosum_dir, k3_dir = Path(kosum_dir), Path(k3_dir)
    oz = json.loads((kosum_dir / "ozet_kosum.json").read_text(encoding="utf-8"))
    kosumlar = []
    for p in sorted(kosum_dir.glob("*_*_*_*.json")):
        if p.name == "ozet_kosum.json":
            continue
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("rota_kaynak") in KAYNAKLAR:
            kosumlar.append({k: r.get(k) for k in (
                "rota_kaynak", "harita", "senaryo", "seed", "basari", "rota_bulundu", "rota_dogru",
                "cikis_kodu", "sure_sim_ika", "sure_sim_gorev", "takip_hatasi_maks_m",
                "varis_mesafesi_m", "temas_sayisi")})
    k3p = k3_dir / "ozet_k3_uretim.json"
    k3 = json.loads(k3p.read_text(encoding="utf-8")) if k3p.is_file() else None
    return {"ozet": oz, "kosumlar": kosumlar, "k3": k3,
            "yol": {"ozet": _goreli(kosum_dir / "ozet_kosum.json"),
                    "kosum": _goreli(kosum_dir) + "/<kaynak>_<h>_<lv>_<tohum>.json",
                    "k3": _goreli(k3p)}}


def _stil():
    plt.rcParams.update({
        "svg.hashsalt": SVG_TUZ, "svg.fonttype": "path",
        "font.family": "DejaVu Sans", "font.size": 8.5,
        "axes.edgecolor": SOLUK, "axes.labelcolor": MUREKKEP, "axes.titlecolor": MUREKKEP,
        "xtick.color": IKINCIL, "ytick.color": IKINCIL, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": IZGARA, "grid.linewidth": 0.6,
        "axes.axisbelow": True, "figure.facecolor": ZEMIN, "axes.facecolor": ZEMIN,
        "savefig.facecolor": ZEMIN, "legend.frameon": False, "lines.linewidth": 2.0,
    })


def _kaydet(fig, ad: str, out_dir: Path, alt_yazi: str):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.text(0.012, 0.012, textwrap.fill(alt_yazi, width=ALT_YAZI_SUTUN), fontsize=6.3, color=IKINCIL,
             ha="left", va="bottom", linespacing=1.25)
    fig.savefig(out_dir / f"{ad}.svg", format="svg",
                metadata={"Date": None, "Creator": None, "Description": alt_yazi})
    fig.savefig(out_dir / f"{ad}.png", format="png", dpi=150, metadata={"Software": None})
    plt.close(fig)


def _baslik(fig, ust: str, alt: str):
    fig.text(0.012, 0.975, ust, fontsize=10.5, color=MUREKKEP, weight="bold", ha="left", va="top")
    alt = "\n".join(textwrap.fill(s, width=ALT_BASLIK_SUTUN) for s in alt.split("\n"))
    fig.text(0.012, 0.93, alt, fontsize=7.6, color=IKINCIL, ha="left", va="top", linespacing=1.25)


def _olan(veri) -> list[str]:
    return [k for k in KAYNAKLAR if k in veri["ozet"]["kaynaklar"]]


def _k3_satiri(veri) -> str:
    k3 = veri.get("k3") or {}
    b = (k3.get("beslemeler") or {}).get("kerteriz")
    m42 = [r for r in veri["kosumlar"] if r["rota_kaynak"] == "model" and r["seed"] == 42]
    moz = (f"mozaik zinciri (imgsz 512, tohum 42) {sum(bool(r['rota_dogru']) for r in m42)}/{len(m42)}"
           if m42 else "mozaik zinciri ÖLÇÜLMEDİ")
    ure = (f"üretim boru hattı (kerteriz) {b['dogru_n']}/{b['harita_n']}" if b else "üretim boru hattı ÖLÇÜLMEDİ")
    return f"H1-K3 açık yol etiketi doğru (eşik ≥ 12/15): {moz} · {ure}"


def basari_orani(veri, out_dir: Path) -> str:
    oz = veri["ozet"]["kaynaklar"]
    olan = _olan(veri)
    kat = SENARYOLAR + ("toplam",)
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.78, bottom=0.25)
    w = 0.8 / max(1, len(olan))
    for i, k in enumerate(olan):
        o = oz[k]
        oran, etik = [], []
        for c in kat:
            if c == "toplam":
                b, n = o["basari_n"], o["n"]
            else:
                sv = (o.get("senaryo") or {}).get(c)
                b, n = (sv["basari_n"], sv["n"]) if sv else (0, 0)
            oran.append(b / n if n else 0.0)
            etik.append(f"{b}/{n}" if n else "—")
        xs = [j + (i - (len(olan) - 1) / 2) * w for j in range(len(kat))]
        ax.bar(xs, oran, width=w * 0.9, color=RENK[k], edgecolor=ZEMIN, linewidth=1.0,
               label=(f"{ETIKET[k]} — harita 3/3 tohum: {o['harita_hepsi_basarili_n']}/15"
                      + (f" ({o['harita_n']} harita koşuldu)" if o["harita_n"] < 15 else "")))
        for x, y, t in zip(xs, oran, etik):
            ax.text(x, y + 0.018, t, ha="center", va="bottom", fontsize=6.8, color=MUREKKEP)
    ax.set_xticks(range(len(kat)), ["kolay", "orta", "zor", "TOPLAM"])
    ax.set_ylim(0, 1.15)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylabel("koşum başarı oranı")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.08), ncol=1, fontsize=7.0, handlelength=1.2)
    _baslik(fig, "H1-K5 · İKA otonom sürüş başarısı — rota kaynağı × seviye (SENTETİK, MuJoCo)",
            "başarı = çıkış 0 ∧ rota ∧ HB 2×2 m içinde ∧ temas 0 ∧ sürüş ≤ 600 s sim · 15 harita × 3 tohum; "
            "uretim yalnız K3'te OPEN_ROUTE üreten haritalar\n" + _k3_satiri(veri))
    alt = (f"Veri: {veri['yol']['ozet']} (+ {veri['yol']['kosum']}) · K3: {veri['yol']['k3']} · "
           "eşik H1-K5 ≥ 12/15 harita (3/3 tohum), gevşetilmez · üreteç simulation/mujoco/sim_grafik.py")
    _kaydet(fig, "sim_basari_orani", out_dir, alt)
    return alt


def _kutu_nokta(ax, degerler: dict, olan, birim_fmt="{:.1f}"):
    """Kaynak başına kutu (medyan/çeyrekler) + titreşimli noktalar; boş kaynak metinle."""
    rng = np.random.RandomState(0)
    for i, k in enumerate(olan):
        v = [float(x) for x in degerler.get(k, []) if x is not None]
        if not v:
            ax.text(i, 0.5, "başarılı koşum yok", transform=ax.get_xaxis_transform(), ha="center",
                    va="center", fontsize=7, color=IKINCIL)
            continue
        ax.boxplot([v], positions=[i], widths=0.5, showfliers=False, patch_artist=True,
                   boxprops=dict(facecolor=ZEMIN, edgecolor=RENK[k], linewidth=1.4),
                   medianprops=dict(color=RENK[k], linewidth=2.0),
                   whiskerprops=dict(color=RENK[k], linewidth=1.0), capprops=dict(color=RENK[k], linewidth=1.0))
        xs = i + rng.uniform(-0.17, 0.17, size=len(v))
        ax.scatter(xs, v, s=11, color=RENK[k], alpha=0.75, edgecolors=ZEMIN, linewidths=0.4, zorder=3)
        ax.text(i + 0.30, float(np.median(v)), ("med " + birim_fmt).format(float(np.median(v))) + f"\nn={len(v)}",
                fontsize=6.6, color=MUREKKEP, va="center", ha="left")
    ax.set_xticks(range(len(olan)), [KISA[k] for k in olan])
    ax.set_xlim(-0.6, len(olan) - 0.2)


def gorev_suresi(veri, out_dir: Path) -> str:
    olan = _olan(veri)
    bas = [r for r in veri["kosumlar"] if r["basari"]]
    surus = {k: [r["sure_sim_ika"] for r in bas if r["rota_kaynak"] == k] for k in olan}
    gorev = {k: [r["sure_sim_gorev"] for r in bas if r["rota_kaynak"] == k] for k in olan}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 4.0))
    fig.subplots_adjust(left=0.085, right=0.975, top=0.80, bottom=0.19, wspace=0.42)
    _kutu_nokta(a1, surus, olan)
    a1.set_ylabel("İKA sürüş süresi (sim s)")
    a1.set_title("İKA sürüşü: IKA_GO → HB varışı", fontsize=8, color=IKINCIL, loc="left")
    _kutu_nokta(a2, gorev, olan)
    a2.set_ylabel("toplam görev süresi (sim s)")
    a2.set_title("görev: fırlatma → HB varışı (sim saati)", fontsize=8, color=IKINCIL, loc="left")
    _baslik(fig, "H1-K6 · Sanal görev süresi — yalnız BAŞARILI koşumlar (SENTETİK, MuJoCo sim saati)",
            f"sürüş sınırı {SARTNAME_IKA_GOREV_SURESI_S:.0f} s (şartname §6.2); İHA kolu kinematik profil "
            "süresi (aerodinamik yok); haritala/çıkarım hesap süresi sim saatine eklenmez")
    alt = (f"Veri: {veri['yol']['kosum']} (sure_sim_ika, sure_sim_gorev; basari=True) · özet "
           f"{veri['yol']['ozet']} · üreteç simulation/mujoco/sim_grafik.py")
    _kaydet(fig, "sim_gorev_suresi", out_dir, alt)
    return alt


def takip_hatasi(veri, out_dir: Path) -> str:
    olan = _olan(veri)
    tk = {k: [r["takip_hatasi_maks_m"] for r in veri["kosumlar"] if r["rota_kaynak"] == k] for k in olan}
    vm = {k: [r["varis_mesafesi_m"] for r in veri["kosumlar"] if r["rota_kaynak"] == k] for k in olan}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 4.0))
    fig.subplots_adjust(left=0.085, right=0.975, top=0.78, bottom=0.19, wspace=0.42)
    _kutu_nokta(a1, tk, olan, "{:.2f}")
    a1.axhline(TAKIP_HATA_M, color=SOLUK, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
    a1.text(len(olan) - 0.25, TAKIP_HATA_M, f"TAKIP_HATA_M {TAKIP_HATA_M:.2f} m ", fontsize=6.4,
            color=IKINCIL, va="bottom", ha="right")        # sağ uç: gt medyan etiketiyle çakışmasın
    a1.set_ylabel("maks. takip hatası (m)")
    a1.set_title("İKA → açık yol merkez hattı, ilk temastan önce", fontsize=8, color=IKINCIL, loc="left")
    _kutu_nokta(a2, vm, olan, "{:.2f}")
    a2.set_yscale("log")
    a2.axhline(HB_KENAR_M / 2.0, color=SOLUK, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
    a2.text(-0.55, HB_KENAR_M / 2.0, f" HB yarı kenarı {HB_KENAR_M / 2.0:.1f} m", fontsize=6.4,
            color=IKINCIL, va="bottom", ha="left")
    a2.set_ylabel("son konum → HB merkezi (m, log)")
    a2.set_title("varış mesafesi (tüm koşumlar)", fontsize=8, color=IKINCIL, loc="left")
    _baslik(fig, "H1-K6 · Takip hatası ve varış mesafesi — tüm koşumlar (SENTETİK, MuJoCo)",
            "takip: sürüş sırasında her kontrol adımında konum → arena açık yol merkez hattı uzaklığı; "
            "temastan sonra ölçülmez · NO_ROUTE koşumlarında İKA hareket etmez (varış ≈ KB→HB) · kesikli çizgiler: "
            "TAKIP_HATA_M (CONTRACTS §4 takip payı) ve HB yarı kenarı")
    alt = (f"Veri: {veri['yol']['kosum']} (takip_hatasi_maks_m, varis_mesafesi_m) · özet "
           f"{veri['yol']['ozet']} · üreteç simulation/mujoco/sim_grafik.py")
    _kaydet(fig, "sim_takip_hatasi", out_dir, alt)
    return alt


OLAYLAR = (("open_route_yayini", "OPEN_ROUTE yayını"),
           ("open_route_ack_ika_yks", "OPEN_ROUTE ACK [ika, yks]"),
           ("no_route_yayini", "NO_ROUTE yayını"),
           ("guven_kapisi_reddi", "güven kapısı reddi (K-B)"),
           ("ika_go_ack", "IKA_GO ACK (sim hakem)"),
           ("hb_icinde", "HB içinde bitiş"),
           ("temas_var", "temaslı koşum"),
           ("sure_asimi_kod4", "süre aşımı / varamadı (kod 4)"))


def sistem_tepkileri(veri, out_dir: Path) -> str:
    oz = veri["ozet"]["kaynaklar"]
    olan = _olan(veri)
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    fig.subplots_adjust(left=0.28, right=0.975, top=0.80, bottom=0.16)
    h = 0.8 / max(1, len(olan))
    ys = np.arange(len(OLAYLAR))[::-1]
    for i, k in enumerate(olan):
        ol = oz[k].get("olaylar") or {}
        v = [int(ol.get(a, 0)) for a, _ in OLAYLAR]
        yk = ys + ((len(olan) - 1) / 2 - i) * h
        ax.barh(yk, v, height=h * 0.9, color=RENK[k], edgecolor=ZEMIN, linewidth=1.0,
                label=f"{ETIKET[k]} (n={oz[k]['n']})")
        for y, x in zip(yk, v):
            ax.text(x + 0.4, y, str(x), va="center", ha="left", fontsize=6.6, color=MUREKKEP)
    ax.set_yticks(ys, [e for _, e in OLAYLAR])
    ax.grid(axis="x"); ax.grid(axis="y", visible=False)
    ax.set_xlabel("koşum sayısı")
    ax.legend(loc="lower right", ncol=1, fontsize=7.0, handlelength=1.2, frameon=True, facecolor=ZEMIN,
              edgecolor=ZEMIN, framealpha=1.0)      # alt satırlarda çubuklar kısa → sağ alt boş
    _baslik(fig, "H1-K4/K6 · Sistem tepkileri — mesaj ve olay sayıları (SENTETİK, MuJoCo)",
            "İHA→İKA/YKS UDP (ephemeral), ACK'lı tekrar; hakem onayı sim'de OTOMATİK (sim=true, saha kanıtı "
            "sayılmaz); koşum başına bir karar mesajı · güven kapısı reddi (K-B): rota bulundu ama conf < 0,20 → "
            "telde NO_ROUTE (CONTRACTS §6.3)")
    alt = (f"Veri: {veri['yol']['ozet']} (kaynaklar.<k>.olaylar) · üreteç simulation/mujoco/sim_grafik.py")
    _kaydet(fig, "sim_sistem_tepkileri", out_dir, alt)
    return alt


def hepsini_ciz(veri, out_dir: Path = SEKIL_DIR) -> dict:
    _stil()
    return {"sim_basari_orani": basari_orani(veri, out_dir), "sim_gorev_suresi": gorev_suresi(veri, out_dir),
            "sim_takip_hatasi": takip_hatasi(veri, out_dir), "sim_sistem_tepkileri": sistem_tepkileri(veri, out_dir)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="H1-K6 sim grafikleri (ölçümden)")
    ap.add_argument("--out", default=str(SEKIL_DIR))
    ap.add_argument("--kosum", default=str(KOSUM_DIR))
    ap.add_argument("--k3", default=str(K3_DIR))
    a = ap.parse_args(argv)
    alt = hepsini_ciz(veri_yukle(Path(a.kosum), Path(a.k3)), Path(a.out))
    for ad, metin in alt.items():
        for uz in ("svg", "png"):
            p = Path(a.out) / f"{ad}.{uz}"
            print(f"[sim_grafik] {p} ({p.stat().st_size} B)")
        print(f"             alt yazı: {metin}")


if __name__ == "__main__":
    main()

"""T214-A RAPORU — `results/fdr_sprint_20260910/H1/README_T214A.md` ÖLÇÜMDEN üretilir.

Elle düzenlenmez; nöbetçi `tests/test_sim_mujoco_olcum.py::G_Readme` üreteç çıktısıyla eşliği
denetler. Girdi YALNIZ JSON (ve grafik dosyalarının varlığı):
  kosum_tur3/ozet_kosum.json + <kaynak>_<h>_<lv>_<tohum>.json  (+ kesilen_kosu/*.json)
  k3_uretim_boru/ozet_k3_uretim.json + <besleme>/harita_*.json + iki_kosu_karsilastirma.json
  k3b/v1_15harita_yerlesim_d441.json   (önceki K3 ölçümü, imgsz 1024 — yalnız karşılaştırma)
  kosum/ozet_kosum.json                (T213-B, eski yerleşim — yalnız karşılaştırma)
Tarih/saat YAZILMAZ (JSON'lardaki `tarih` alanları dışında) → aynı JSON aynı metin.

Kullanım:  venv python simulation/mujoco/t214a_rapor.py
"""
from __future__ import annotations

import collections
import json
import math
import statistics
import sys
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
for _p in (str(BURASI.parent / "scripts"), str(KOK / "codes"), str(KOK / "comms"), str(BURASI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arena                                              # noqa: E402
import gorev_kosumu as gk                                 # noqa: E402
import sim_karar_toplayici as skt                         # noqa: E402

H1 = KOK / "results" / "fdr_sprint_20260910" / "H1"
KOSUM = H1 / "kosum_tur3"
K3 = H1 / "k3_uretim_boru"
README_YOL = H1 / "README_T214A.md"
SEKIL_DIR = KOK / "FDR" / "sekiller"
_KT = "results/fdr_sprint_20260910/H1/kosum_tur3"
GRAFIKLER = (("sim_basari_orani", "başarı oranı — rota kaynağı × seviye (çubuk)",
              f"`{_KT}/ozet_kosum.json` (kaynaklar.<k>.senaryo, harita düzeyi); alt başlıkta K3: model koşum "
              "JSON'ları (tohum 42) ve `results/fdr_sprint_20260910/H1/k3_uretim_boru/ozet_k3_uretim.json`"),
             ("sim_gorev_suresi", "görev süresi dağılımı — sürüş ve toplam görev, sim s (kutu + nokta)",
              f"`{_KT}/<kaynak>_<h>_<lv>_<tohum>.json` (sure_sim_ika, sure_sim_gorev; basari=True)"),
             ("sim_takip_hatasi", "takip hatası (ilk temastan önce) ve varış mesafesi (kutu + nokta)",
              f"`{_KT}/<kaynak>_<h>_<lv>_<tohum>.json` (takip_hatasi_maks_m, varis_mesafesi_m)"),
             ("sim_sistem_tepkileri", "sistem tepkileri — OPEN_ROUTE/NO_ROUTE/ACK/IKA_GO/temas olay sayıları",
              f"`{_KT}/ozet_kosum.json` (kaynaklar.<k>.olaylar; tel tipinden)"))
ESIK = 12
KAYNAKLAR = gk.ROTA_KAYNAKLARI
ETIKET = {"gt": "YER GERÇEĞİ (gt)", "model": "ÜRETİM MODELİ · mozaik zinciri (model)",
          "uretim": "ÜRETİM BORU HATTI · kare-bazlı (uretim)"}


def _j(p: Path):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rel(p: Path) -> str:
    p = Path(p)
    return (p.relative_to(KOK) if p.is_relative_to(KOK) else p).as_posix()


def _hk(gecti: bool) -> str:
    return "**GEÇTİ**" if gecti else "**DÜŞTÜ**"


def _s(v, nd: int = 2) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "✓" if v else "✗"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def _dag(d) -> str:
    if not d:
        return "—"
    return f"n={d['n']} · min {d['min']} · medyan {d['medyan']} · ort {d['ort']} · maks {d['maks']}"


def _dagilim(v, nd: int = 2):
    v = [float(x) for x in v if x is not None]
    if not v:
        return None
    return {"n": len(v), "min": round(min(v), nd), "medyan": round(statistics.median(v), nd),
            "ort": round(statistics.fmean(v), nd), "maks": round(max(v), nd)}


def veri() -> dict:
    rs = [_j(p) for p in sorted(KOSUM.glob("*_*_*_*.json"))]
    k3h = {bes: [_j(p) for p in sorted((K3 / bes).glob("harita_*_*.json"))] for bes in skt.BESLEMELER}
    opsiyon = {"iki": K3 / "iki_kosu_karsilastirma.json", "k3_eski": H1 / "k3b" / "v1_15harita_yerlesim_d441.json",
               "t213b": H1 / "kosum" / "ozet_kosum.json", "k3_kosu1": K3 / "kosu1_ozet_k3_uretim.json"}
    return {"oz": _j(KOSUM / "ozet_kosum.json"), "rs": rs,
            "kesilen": [_j(p) for p in sorted((KOSUM / "kesilen_kosu").glob("*_*_*_*.json"))],
            "k3": _j(K3 / skt.OZET_ADI), "k3h": k3h,
            **{k: (_j(p) if p.is_file() else None) for k, p in opsiyon.items()}}


def _model_kunyeleri(rs, k3h) -> list:
    """Model künyesi taşıyan tüm ölçümler (model/uretim koşumları + K3 üretim harita JSON'ları)."""
    return ([r["model"] for r in rs if r.get("model")]
            + [r["model"] for bes in sorted(k3h) for r in k3h[bes] if r.get("model")])


def _model_sha(rs, k3h) -> str:
    shas = sorted({(m.get("sha256_dosya") or "?")[:12] for m in _model_kunyeleri(rs, k3h)})
    return "/".join(shas) if shas else "?"


def _model_eslesti(rs, k3h) -> str:
    ks = _model_kunyeleri(rs, k3h)
    return f"{sum(bool(m.get('eslesti')) for m in ks)}/{len(ks)} ölçüm"


def _k3_mozaik(rs, seed):
    m = [r for r in rs if r["rota_kaynak"] == "model" and r["seed"] == seed]
    return {"n": len(m), "rota": sum(r["rota_bulundu"] for r in m), "dogru": sum(r["rota_dogru"] for r in m),
            "yanlis": sum(r["rota_bulundu"] and not r["rota_dogru"] for r in m),
            "or_dogru": sum(gk.tel_tipi(r) == "OPEN_ROUTE" and r["rota_dogru"] for r in m),
            "guven_reddi": sum(r["rota_bulundu"] and gk.tel_tipi(r) == "NO_ROUTE" for r in m),
            "basari": sum(r["basari"] for r in m), "satirlar": m}


def _kb_hb_mesafe():
    d = [math.dist(arena.harita(h, lv)["kb"], arena.harita(h, lv)["hb"])
         for h in range(1, arena.HARITA_N + 1) for lv in arena.SCENARIOS]
    return round(min(d), 1), round(max(d), 1)


def _or_metni(r) -> str:
    parca = [f"k{s['n']}: {s['yol']}→{s.get('rota_dunya_yolu', '?')}"
             for s in r["kareler"] if s.get("karar") == "OPEN_ROUTE"]
    return " · ".join(parca) if parca else "—"


def _sebepler(d: dict, n: int = 3) -> str:
    if not d:
        return "—"
    return ", ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:n])


def uret() -> str:
    V = veri()
    oz, rs, k3 = V["oz"], V["rs"], V["k3"]
    ok = oz["kaynaklar"]
    kb_ = k3["beslemeler"].get("kerteriz", {})
    ham = k3["beslemeler"].get("ham", {})
    m42 = _k3_mozaik(rs, 42)
    L: list[str] = []
    a = L.append

    a("# H1 · T214-A — Ölçüm zinciri: K3 (mozaik 512 / üretim boru hattı), K5 (gt / model / uretim), K6 süreler ve grafikler")
    a("")
    a("> **SENTETİK** (D-441 d): MuJoCo simülasyonu; saha kanıtı değildir. **ÖLÇÜLEMEDİ ≠ GEÇTİ**; eşikler ön kayıttan "
      "(`results/fdr_sprint_20260910/ON_KAYIT.md` H1-K3/K4/K5/K6) ve **gevşetilmedi**. Üretim modeli v36 "
      f"(`sha {_model_sha(rs, V['k3h'])}…`, kayıt defteriyle eş: {_model_eslesti(rs, V['k3h'])}) **değişmedi**; "
      "sim'e özel eğitim YOK. Bu belge `simulation/mujoco/t214a_rapor.py` ile JSON'lardan üretilir, elle düzenlenmez "
      "(nöbetçi: `tests/test_sim_mujoco_olcum.py::G_Readme`).")
    a(f"> Özet tarihleri: koşum `{oz['tarih']}` · K3 üretim boru hattı `{k3.get('tarih')}`.")
    a("")

    # ── 0 ──
    a("## 0. Sonuç tablosu")
    a("")
    a("| kapı | ölçüm | eşik (ön kayıt) | hüküm |")
    a("|---|---|---|---|")
    a(f"| H1-K3 · mozaik zinciri (`iha_haritala`, çıkarım imgsz **{m42['satirlar'][0]['model_teshis']['imgsz'] if m42['satirlar'] else '?'}** "
      f"kayıt defterinden, tohum 42) | rota bulundu {m42['rota']}/{m42['n']} · **doğru etiket {m42['dogru']}/{m42['n']}** · "
      f"yanlış {m42['yanlis']} · güven kapısı sonrası yayımlanan doğru OPEN_ROUTE {m42['or_dogru']}/{m42['n']} | "
      f"≥ {ESIK}/15 | {_hk(m42['dogru'] >= ESIK)} |")
    a(f"| H1-K3 · üretim kare-bazlı boru hattı (`rpi_inference.run_camera` dosya kaynağı, kerteriz beslemesi, tohum 42) | "
      f"**doğru (ön kayıt) {kb_.get('dogru_n', 0)}/{kb_.get('harita_n', 0)}** · OPEN_ROUTE yayını olan harita "
      f"{kb_.get('open_route_var_n', 0)} · yanlış yol yayını olan {kb_.get('yanlis_yol_yayini_olan_n', 0)} | "
      f"≥ {ESIK}/15 | {_hk(kb_.get('dogru_n', 0) >= ESIK)} |")
    g = ok.get("gt", {})
    go = g.get("olaylar", {})
    a(f"| H1-K4 · aktarım (gt kolu) | OPEN_ROUTE ACK [ika,yks] {go.get('open_route_ack_ika_yks', 0)}/{go.get('open_route_yayini', 0)} · "
      f"IKA_GO ACK {go.get('ika_go_ack', 0)}/{g.get('n', 0)} · harita {g.get('harita_n', 0)} | 15/15 | "
      f"{_hk(bool(g) and go.get('open_route_ack_ika_yks') == g.get('n') and go.get('ika_go_ack') == g.get('n') and g.get('harita_n') == 15)} |")
    for k in KAYNAKLAR:
        o = ok.get(k)
        if not o:
            a(f"| H1-K5 · {ETIKET[k]} | ÖLÇÜLMEDİ | ≥ {ESIK}/15 harita × 3 tohum | **ÖLÇÜLEMEDİ** |")
            continue
        not_ = (f" (yalnız K3'te OPEN_ROUTE üreten {o['harita_n']} harita koşuldu; kalan {15 - o['harita_n']} harita "
                "NO_ROUTE → başarısız sayılır)" if o["harita_n"] < 15 else "")
        a(f"| H1-K5 · {ETIKET[k]} | başarı **{o['basari_n']}/{o['n']}** · harita (3/3 tohum) "
          f"**{o['harita_hepsi_basarili_n']}/15**{not_} | ≥ {ESIK}/15 harita × 3 tohum | {_hk(o['harita_hepsi_basarili_n'] >= ESIK)} |")
    var = [g[0] for g in GRAFIKLER if all((SEKIL_DIR / f"{g[0]}.{u}").is_file() for u in ("svg", "png"))]
    a(f"| H1-K6 · sanal görev süresi + grafikler | koşum tablosu §9 ({len(rs)} koşum) · grafik {len(var)}/4 (SVG + PNG) | "
      f"45 koşum tablo + 4 grafik | {'**ÜRETİLDİ**' if len(var) == 4 else '**EKSİK**'} |")
    a("")
    a("Başarı tanımı (K5, TEK tanım `gorev_kosumu.basari_hesapla`): çıkış 0 ∧ rota bulundu ∧ HB 2×2 m karesi içinde ∧ "
      "temas 0 ∧ sürüş ≤ 600 s (sim saati).")
    a("")

    # ── 1 ──
    a("## 1. H1-K3 — mozaik zinciri (`iha_haritala`, imgsz kayıt defterinden)")
    a("")
    a("D-441 (a): çıkarım boyu `config/model_registry.json` etkin profilinden okunur (`iha_haritala.INFER_SIZE`, "
      "`cikarim_boyu()`; eskiden `_infer(..., MOZ_PX=1024)` çıplaktı). Mozaik tuvali 1024 px'te kalır, maskeler "
      "en-yakın-komşu ile tuvale büyütülür (costmap/MPP/tohum geometrisi değişmez). HB tohumu 0 (üretim; D-441 b). "
      "Her koşum kendi taramasını render eder (GPU render kareleri ~%50 bayt-eş — tohum 42 taraması K3 üretim "
      "hattının taramasıyla aynı dosya değildir).")
    a("")
    a("| harita | senaryo | açık yol | zincir durumu | rota yolu | doğru | güven | darboğaz m | tel tipi | başarı |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for r in m42["satirlar"]:
        mt = r.get("model_teshis") or {}
        a(f"| {r['harita']} | {r['senaryo']} | {r['acik_yol']} | {mt.get('rota_durum')} | {_s(r['model_yol'])} | "
          f"{_s(r['rota_dogru'])} | {_s(r.get('model_guven'), 3)} | {_s(mt.get('darbogaz_m'), 3)} | {gk.tel_tipi(r)} | "
          f"{_s(r['basari'])} |")
    a("")
    a("| tohum | rota bulundu | doğru etiket | yanlış etiket | güven kapısı reddi (conf < 0,20 → NO_ROUTE) | yayımlanan doğru OPEN_ROUTE | sürüş başarısı |")
    a("|---|---|---|---|---|---|---|")
    for sd in sorted({r["seed"] for r in rs if r["rota_kaynak"] == "model"}):
        m = _k3_mozaik(rs, sd)
        a(f"| {sd} | {m['rota']}/{m['n']} | {m['dogru']}/{m['n']} | {m['yanlis']} | {m['guven_reddi']} | "
          f"{m['or_dogru']}/{m['n']} | {m['basari']}/{m['n']} |")
    if V["k3_eski"]:
        e = V["k3_eski"]["ozet"]
        a("")
        a(f"Karşılaştırma (aynı zincir, **imgsz 1024**, ayrı render; `results/fdr_sprint_20260910/H1/k3b/v1_15harita_yerlesim_d441.json`, "
          f"D-441 ek): rota {e['rota_bulunan']}/{e['harita_n']}, doğru {e['dogru_etiket']}/{e['harita_n']}. İki ölçüm aynı "
          "tarama kareleri üzerinde değildir; fark çıkarım boyu ile render değişkenliğini birlikte içerir.")
    a("")

    # ── 2 ──
    a("## 2. H1-K3 — üretim kare-bazlı boru hattı (D-441 c)")
    a("")
    a("Zincir (üretim kodu DEĞİŞTİRİLMEDEN, `simulation/mujoco/sim_karar_toplayici.py`): tarama kareleri "
      "(`scan_%05d` + `poses.csv`) → `rpi_inference.run_camera(kaynak=<dosya dizisi>, ekransiz=True)` = `--camera --kaynak` "
      "kipi (`kamera_kaynagi_coz` → dosya) → letterbox → v36 (imgsz 512) → `get_masks` → `kare_olcek_kahini` "
      "(Katman 1: `CanliOlcekSaglayici` ← sim irtifası `poses.csv` z, FOV sim kamerası) → `analyze_path` (Katman A/B, "
      "HB tespiti) → `_rota_kararini_esikle` → `KararYumusatici` (D-396) → `KararYayinci` → UDP (ephemeral) → "
      "`IkaReceiver` (İKA ucu, gerçek alıcı) + YKS dinleyicisi (ACK). Kamera köprüsü (MJPEG) atlanır; kare döngüsü üretimdir. "
      "**Kerteriz beslemesi (BİRİNCİL):** kare poz yaw'ına göre çeyrek tur döndürülerek (np.rot90, kayıpsız) kuzey-yukarı "
      "(KB→HB yukarı) verilir — üretim `analyze_path` rotayı ALT→ÜST arar, `run_camera` eksen parametresi geçirmez; "
      "döndürme SİM TARAFINDADIR. **Ham** besleme TEŞHİS'tir (kapı değil).")
    a("")
    a(f"Hüküm tanımı (ön kayıt, toplayıcı modül başı): {k3.get('hukum_tanimi')}.")
    a("")
    a("| harita | senaryo | açık yol | OPEN_ROUTE kareleri (kare: yayınlanan etiket → dünyada izlenen yol) | yanlış etiket yayını | dünya yolu doğru OR var | son yayın | NO_ROUTE sebepleri (ilk 3) | hüküm (ön kayıt) |")
    a("|---|---|---|---|---|---|---|---|---|")
    for r in V["k3h"].get("kerteriz", []):
        hk = skt.harita_hukmu(r)
        th = skt.harita_teshisi(r)
        son = r.get("son_yayin") or {}
        a(f"| {r['harita']} | {r['senaryo']} | {r['acik_yol']} | {_or_metni(r)} | {hk['yanlis_yol_yayini_n']} | "
          f"{_s(th['dunya_yolu_dogru_var'])} | {son.get('tip')} {son.get('sebep') or ''} | "
          f"{_sebepler(r.get('no_route_sebepleri'))} | {'✓' if hk['dogru'] else '✗'} |")
    a("")
    for bes, b in (("kerteriz", kb_), ("ham", ham)):
        if not b:
            continue
        t = b.get("teshis", {})
        a(f"- **{bes}**: doğru (ön kayıt) **{b['dogru_n']}/{b['harita_n']}** · OPEN_ROUTE yayını olan harita "
          f"{b['open_route_var_n']} · yanlış yol yayını olan {b['yanlis_yol_yayini_olan_n']} · ilk OPEN_ROUTE doğru "
          f"{b['ilk_open_route_dogru_n']} · son OPEN_ROUTE doğru {b['son_open_route_dogru_n']} · son yayın NO_ROUTE "
          f"{b['son_yayin_no_route_n']}/{b['harita_n']} · OPEN_ROUTE kare {b['open_route_kare_n']}/{b['kare_n']} · "
          f"hizalı {b['hizali_n']}/{b['harita_n']} · ACK eksik {b['ack_eksik_n']}.")
        a(f"  TEŞHİS (hüküm dışı): OPEN_ROUTE karelerinin **{t.get('or_dunya_yolu_dogru_n', 0)}/{t.get('or_kare_n', 0)}**'i "
          f"dünyada açık yolu izliyor, yayınlanan etiket = dünya yolu {t.get('or_etiket_dunya_esit_n', 0)}/{t.get('or_kare_n', 0)}; "
          f"dünya yolu doğru OPEN_ROUTE'u olan harita {t.get('dunya_yolu_dogru_or_olan_harita_n', 0)}/{t.get('harita_n', 0)}; "
          f"KB ile HB **aynı karede: {t.get('kb_hb_ayni_karede_kare_n', 0)}/{t.get('tarama_bacagi_kare_n', 0)}** tarama-bacağı karesi "
          f"(KB karede {t.get('kb_karede_kare_n', 0)}, HB karede {t.get('hb_karede_kare_n', 0)}); kare kaydı ↔ İKA ucu "
          f"OPEN_ROUTE sayısı tutarlı {t.get('kare_ika_or_tutarli_n', 0)}/{t.get('harita_n', 0)}.")
    a("")
    sebep = sorted(set(kb_.get("no_route_sebepleri", {})) | set(ham.get("no_route_sebepleri", {})))
    if sebep:
        a("| NO_ROUTE sebebi (kare) | kerteriz | ham |")
        a("|---|---|---|")
        for s in sorted(sebep, key=lambda x: (-kb_.get("no_route_sebepleri", {}).get(x, 0), x)):
            a(f"| {s} | {kb_.get('no_route_sebepleri', {}).get(s, 0)} | {ham.get('no_route_sebepleri', {}).get(s, 0)} |")
        a("")
    if V["iki"]:
        i = V["iki"]
        a(f"**İki koşu (aynı tarama kareleri):** ilk koşu (`kosum_tur3.sh`, 12:39–12:43) ↔ devam koşusu — "
          f"{i['harita_besleme_n']} harita·besleme, {i['kare_n']} kare, kare kararı farkı **{i['fark_n']}** "
          f"(`k3_uretim_boru/iki_kosu_karsilastirma.json`; karar izi `kosu1_karar_izi.json`, ilk özet `kosu1_ozet_k3_uretim.json`).")
        a("")

    # ── 3 ──
    a("## 3. H1-K4 — aktarım (tel tipinden sayım, `gorev_kosumu.tel_tipi`)")
    a("")
    a("| kaynak | n | OPEN_ROUTE yayını (tel) | ACK [ika,yks] | NO_ROUTE yayını (tel) | ACK [ika,yks] | güven kapısı reddi | IKA_GO ACK | link kaybı olan |")
    a("|---|---|---|---|---|---|---|---|---|")
    for k in KAYNAKLAR:
        o = ok.get(k)
        if not o:
            continue
        e = o.get("olaylar", {})
        a(f"| {k} | {o['n']} | {e.get('open_route_yayini')} | {e.get('open_route_ack_ika_yks')} | {e.get('no_route_yayini')} | "
          f"{e.get('no_route_ack_ika_yks')} | {e.get('guven_kapisi_reddi')} | {e.get('ika_go_ack')} | {e.get('link_kayip_var')} |")
    a("")
    a("Not: `send_open_route` güven eşiği (0,20) altındaki rotayı NO_ROUTE(DUSUK_GUVEN) olarak gönderir (CONTRACTS §6.3, K-B). "
      "İlk koşunun ham `iha_gonderim.tip` alanı ÇAĞRILAN yöntemi yazıyordu; sayım hakem kaydından (TEL) yapılır (§6.3).")
    a("")

    # ── 4 ──
    a("## 4. H1-K5 — İKA otonom sürüş (MuJoCo fizik, `ika_nav` + `MuJoCoSurucu`, sim saati)")
    a("")
    a("| kaynak | n | rota bulundu | rota doğru | OPEN_ROUTE (tel) | IKA_GO ACK | HB içinde | temas var | süre aşımı (kod 4) | **BAŞARI** | harita (3/3 tohum) | eşik |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in KAYNAKLAR:
        o = ok.get(k)
        if not o:
            a(f"| {k} | 0 | — | — | — | — | — | — | — | **ÖLÇÜLMEDİ** | — | ≥ {ESIK}/15 |")
            continue
        e = o.get("olaylar", {})
        a(f"| {k} | {o['n']} | {o['rota_bulundu_n']} | {o['rota_dogru_n']} | {e.get('open_route_yayini')} | {o['ika_go_ack_n']} | "
          f"{o['hb_icinde_n']} | {o['temas_var_n']} | {o['sure_asimi_n']} | **{o['basari_n']}/{o['n']} ({o['basari_orani']})** | "
          f"{o['harita_hepsi_basarili_n']}/{o['harita_n']} | ≥ {ESIK}/15 |")
    a("")
    a("| kaynak | senaryo | n | başarı | HB içinde | temas var |")
    a("|---|---|---|---|---|---|")
    for k in KAYNAKLAR:
        for lv, sv in (ok.get(k, {}).get("senaryo") or {}).items():
            a(f"| {k} | {lv} | {sv['n']} | {sv['basari_n']} | {sv['hb_icinde_n']} | {sv['temas_var_n']} |")
    a("")
    a("Harita düzeyi (başarılı tohum / koşulan tohum):")
    a("")
    a("| harita_senaryo | " + " | ".join(KAYNAKLAR) + " |")
    a("|---|" + "---|" * len(KAYNAKLAR))
    anahtarlar = sorted({hk for k in KAYNAKLAR for hk in (ok.get(k, {}).get("harita_duzeyi") or {})},
                        key=lambda s: (int(s.split("_")[0]), arena.SCENARIOS.index(s.split("_")[1])))
    for hs in anahtarlar:
        hucre = []
        for k in KAYNAKLAR:
            d = (ok.get(k, {}).get("harita_duzeyi") or {}).get(hs)
            hucre.append("—" if d is None else f"{d['basari_n']}/{d['n']}")
        a(f"| {hs} | " + " | ".join(hucre) + " |")
    a("")
    if V["t213b"]:
        tg = V["t213b"]["kaynaklar"].get("gt", {})
        a(f"Karşılaştırma: T213-B (`results/fdr_sprint_20260910/H1/kosum/ozet_kosum.json`, **eski yerleşim**, "
          f"D-441 öncesi) YER GERÇEĞİ {tg.get('basari_n')}/{tg.get('n')}, harita {tg.get('harita_hepsi_basarili_n')}/15 — "
          f"yeni yerleşim (açık yol koridoru ≥ 1,45 m engelsiz) ile {g.get('basari_n')}/{g.get('n')}, harita "
          f"{g.get('harita_hepsi_basarili_n')}/15. Sürücü ve kontrol kodu değişmedi.")
        a("")
    ur = [r for r in rs if r["rota_kaynak"] == "uretim"]
    if ur:
        a("**Üretim boru hattıyla sürüş (uretim):** İKA'ya İKA ucuna ulaşan SON OPEN_ROUTE verilir; üretimde `ref_xy` "
          "daima [0,0] ve İKA SAF ÖTELEME yapar (CONTRACTS §3.2/§6.5) → rotanın ilk noktası İKA'nın bulunduğu KB sayılır. "
          "`ankor KB` = rotanın pozdan hesaplanan gerçek başlangıcının KB'ye uzaklığı (TEŞHİS).")
        a("")
        a("| harita | senaryo | tohum | OPEN_ROUTE (son etiket) | doğru | son OR dünya yolu | ankor KB m | rota sonu → HB m | KB–HB aynı kare | kod | temas | varış m | takip maks m | başarı |")
        a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in ur:
            u = r.get("uretim_teshis") or {}
            t = u.get("teshis") or {}
            a(f"| {r['harita']} | {r['senaryo']} | {r['seed']} | {_s(r['model_yol'])} | {_s(r['rota_dogru'])} | "
              f"{_s(u.get('son_or_dunya_yolu'))} | {_s(u.get('ankor_kb_uzakligi_m'))} | {_s(u.get('rota_sonu_hb_uzakligi_m'))} | "
              f"{t.get('kb_hb_ayni_karede_kare_n', '—')} | {r['cikis_kodu']} | {r['temas_sayisi']} | {_s(r['varis_mesafesi_m'])} | "
              f"{_s(r['takip_hatasi_maks_m'])} | {_s(r['basari'])} |")
        ank = _dagilim([(r.get("uretim_teshis") or {}).get("ankor_kb_uzakligi_m") for r in ur])
        a("")
        a(f"Ankor KB uzaklığı (uretim, OPEN_ROUTE alan koşumlar): {_dag(ank)} m.")
        a("")
    if V["kesilen"]:
        kz = V["kesilen"]
        a(f"Kesilen ilk koşu (`kosum_tur3/kesilen_kosu/`, {len(kz)} koşum, 12:57–12:59, kullanım kredisi bitince yarıda kaldı): "
          f"başarı {sum(r['basari'] for r in kz)}/{len(kz)}, ankor KB "
          f"{_dag(_dagilim([(r.get('uretim_teshis') or {}).get('ankor_kb_uzakligi_m') for r in kz]))} m. "
          "Devam koşusu 15 koşumun hepsini tek kod sürümüyle yeniden koştu (üstteki tablo); ilk koşu silinmedi.")
        a("")

    # ── 5 ──
    a("## 5. H1-K6 — sanal görev süresi, takip hatası, varış")
    a("")
    a("Süreler SİM SAATİ (`MjData.time`, ON_KAYIT §5.3); İHA kolu kinematik profil süresidir (aerodinamik yok); "
      "haritala/çıkarım hesap süresi sim saatine eklenmez. Takip hatası: sürüş boyunca her `bekle()` adımında İKA "
      "konumu → arena AÇIK YOL merkez hattı uzaklığı, **ilk temastan önce** (`takip_hatasi_*`); `plan_takip_*` = "
      "komut edilen rotaya uzaklık (sürücü hatasını planlayıcı sapmasından ayırır).")
    a("")
    a("| kaynak | İKA sürüş sim-s (başarılı) | toplam görev sim-s (başarılı) | takip maks m (sürülen) | takip maks m (başarılı) | plan takip maks m | varış m (hepsi) |")
    a("|---|---|---|---|---|---|---|")
    for k in KAYNAKLAR:
        o = ok.get(k)
        if o:
            a(f"| {k} | {_dag(o.get('sure_sim_ika_basarili'))} | {_dag(o.get('sure_sim_gorev_basarili'))} | "
              f"{_dag(o.get('takip_hatasi_maks_m'))} | {_dag(o.get('takip_hatasi_maks_m_basarili'))} | "
              f"{_dag(o.get('plan_takip_hatasi_maks_m'))} | {_dag(o.get('varis_mesafesi_m'))} |")
    a("")
    a("Grafikler (`simulation/mujoco/sim_grafik.py`, JSON'dan; nöbetçi `tests/test_sim_mujoco_olcum.py::F`):")
    a("")
    for ad, ne, kaynak in GRAFIKLER:
        a(f"- `FDR/sekiller/{ad}.svg` · `.png` — {ne}. Veri: {kaynak}.")
    a("")

    # ── 6 ──
    kmin, kmaks = _kb_hb_mesafe()
    t = kb_.get("teshis", {})
    a("## 6. Bulgular (kanıtlı; üretim kodu DEĞİŞTİRİLMEDİ — karar mimarın)")
    a("")
    a(f"1. **Üretim yol etiketi KARE-GÖRELİ.** `analyze_path` → `_rota_serit_olcumu` → `karar_sozlesmesi.rota_serit_karari`: "
      "`road` rotanın gövdesinin karenin genişliğinin hangi üçte birinde olduğundan okunur. Tarama kareleri HTAB'a ortalanmadığında "
      f"(bacaklar x = −18/−6/+6/+18 m) etiket dünyadaki yoldan ayrışır: kerteriz OPEN_ROUTE karelerinde yayınlanan etiket = dünya yolu "
      f"**{t.get('or_etiket_dunya_esit_n', 0)}/{t.get('or_kare_n', 0)}**, rota dünyada açık yolu izliyor "
      f"**{t.get('or_dunya_yolu_dogru_n', 0)}/{t.get('or_kare_n', 0)}**. Ön kayıtlı hüküm yayınlanan etiketle kurulur "
      "(İKA'nın aldığı değer) ve DEĞİŞMEDİ; teşhis, K3 düşüşünün bir kısmının algıdan değil etiket semantiğinden geldiğini gösterir. "
      "Sahada kare HTAB'a ortalanmazsa aynı sapma beklenir (ÖLÇÜLMEDİ).")
    a(f"2. **Tek kare KB ile HB'yi birlikte görmüyor → üretim rotası KB'ye ankorlanamıyor.** Sim arenasında KB–HB {kmin}–{kmaks} m; "
      "sim kamerası 30 m'de 45,6 m kare (hfov 74,5°). Kerteriz tarama-bacağı karelerinde KB ile HB aynı karede "
      f"**{t.get('kb_hb_ayni_karede_kare_n', 0)}/{t.get('tarama_bacagi_kare_n', 0)}**. Üretim rotası karenin alt bandından başlar; İKA saf öteleme "
      "yaptığı için rota KB'den `ankor KB` kadar kaymış sürülür (§4 tablosu) → temas/varamama. Gerçek kamera (IMX477 + 6 mm, "
      "hfov ~55°, ÖLÇÜLMEDİ) 30 m'de ~31 m iz verir (TAHMİN) — daha dar. Gerçek arenada KB/HB konumu **BEYAN GEREKLİ**.")
    a("3. **Ölçüm zinciri kusuru — güven kapısı dönüşümü OPEN_ROUTE sayılıyordu (düzeltildi).** `gorev_kosumu` ilk koşuda "
      "`iha_gonderim.tip` = çağrılan yöntem; `send_open_route` conf < 0,20'de NO_ROUTE(DUSUK_GUVEN) gönderir. model_2_zor_42: rota doğru "
      "(conf 0,141), telde NO_ROUTE, kod 2. Düzeltme: `tel_tipi` (hakem kaydından), `iha_gonderim.tel_tipi`, `guven_kapisi_reddi`; "
      "özet olay sayıları tel tipinden. Ölçüm dosyaları değiştirilmedi (eski JSON'lar hakem alanlarından çözülür).")
    a("4. **WIP kusuru — `sim_karar_toplayici.ozet_hesapla` \"YAZMAZ\" diyip yazıyordu (düzeltildi).** Diskteki özeti "
      "yeniden hesapla karşılaştıran nöbetçi, karşılaştırmadan önce dosyayı ezdiği için BOŞ kapı olurdu (D-370 sınıfı). "
      "Artık yazmaz; test `Path.write_text` yamasıyla denetler (mutasyon M10).")
    a("")

    # ── 7 ──
    a("## 7. Sınırlar (FDR'ye aynen taşınır)")
    a("")
    for s in (
        "**SENTETİK** ölçüm: MuJoCo render, dokular gerçek kare kırpması (yol şeridi zeminden AYRI doku; şartname arenasında zemin ile güzergâh aynı sıkıştırılmış topraktır — T213-A §6).",
        "İHA uçuşu **KİNEMATİK** (mocap, aerodinamik yok); tarama bacağında yatış 0 (T213-A düzeltmesi).",
        "Hakem onayı sim'de **OTOMATİK** (`sim_hakem`, `sim=true`, CONTRACTS §6.7.1 istisnası; saha kanıtı sayılmaz).",
        "İKA iz genişliği 0,39 m **TAHMİN**; teker armature 0,01 TAHMİN; motor tork sınırı yok (DDR'de yok).",
        "Kamera: sim hfov 74,5° (gerçek ~55°, ÖLÇÜLMEDİ); irtifa `poses.csv` z (gürültüsüz, MAVLink `relative_alt` yerine); kamera köprüsü (MJPEG) atlandı.",
        "Kerteriz beslemesinde kare döndürme SİM tarafındadır (üretim `run_camera` eksen parametresi geçirmez); ham besleme teşhis olarak ayrıca ölçüldü.",
        "Senkron yayın: toplayıcı her karardan sonra gönderimi bekler (latest-wins kaybı yok); Jetson ~1,35 FPS (D-431) ile kare hızı farkı modellenmez.",
        "OBB araç maskesi sim'de kapalı (sim'de araç yok).",
    ):
        a(f"- {s}")
    a("")

    # ── 8 ──
    a("## 8. Yeniden üretim ve kanıt")
    a("")
    a("- İlk koşu: `kosum_tur3/kosum_tur3.sh` → ham çıktı `kosum_tur3/kosum_tur3_log.txt` (git `42ca7b8f` + çalışma ağacı; "
      "K3 üretim 15 harita × 2 besleme, gt 45, model 45, uretim 6/15'te kesildi).")
    a("- Devam: `kosum_tur3/kosum_tur3_devam.sh` → `kosum_tur3/kosum_tur3_devam_log.txt` (git `3132c503` + çalışma ağacı, "
      "10 Eyl 15:27–15:37; K3 üretim aynı taramalarla yeniden + "
      "teşhis alanları, karar izi karşılaştırması, uretim 15 koşum). gt/model kolları yeniden koşulmadı: sürüş/rota kod yolları "
      "değişmedi (yalnız özet, tel-tipi ve takip örnekleme kancası `takip_ornekle` — davranış eş).")
    a("- Tarama kareleri / mozaik / besleme PNG'leri git dışıdır (`.gitignore`; `--hepsi` içerik-eş yeniden üretir); "
      "`detection.json`, `rota.json`, `poses.csv`, `karar_toplayici.json` ve tüm ölçüm JSON'ları depodadır.")
    a("- Özetler: `gorev_kosumu.ozet_kur` (`ozet_kosum.json`), `sim_karar_toplayici.ozet_kur` (`ozet_k3_uretim.json`); "
      "grafikler `sim_grafik.py`; bu belge `t214a_rapor.py`. Nöbetçiler ve mutasyonlar: `tests/test_sim_mujoco_olcum.py`, "
      "`results/fdr_sprint_20260910/H1/t214a/mutasyon_t214a.py` → `mutasyon_ciktisi.txt`.")
    a("")

    # ── 9 ──
    a("## 9. Koşum tablosu (her satır bir JSON, `kosum_tur3/<kaynak>_<harita>_<senaryo>_<tohum>.json`)")
    a("")
    a("| kaynak | harita | senaryo | tohum | rota | doğru | tel | wp | açıklık m | kod | HB | varış m | temas | sürüş sim-s | görev sim-s | takip maks m | başarı |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    sira = {k: i for i, k in enumerate(KAYNAKLAR)}
    for r in sorted(rs, key=lambda r: (sira.get(r["rota_kaynak"], 9), r["harita"],
                                       arena.SCENARIOS.index(r["senaryo"]), r["seed"])):
        a(f"| {r['rota_kaynak']} | {r['harita']} | {r['senaryo']} | {r['seed']} | {_s(r['rota_bulundu'])} | "
          f"{_s(r['rota_dogru'])} | {gk.tel_tipi(r)} | {r['wp_sayisi']} | {_s(r.get('rota_engel_aciklik_m'), 3)} | "
          f"{r['cikis_kodu']} | {_s(r['hb_icinde'])} | {_s(r['varis_mesafesi_m'])} | {r['temas_sayisi']} | "
          f"{_s(r['sure_sim_ika'], 1)} | {_s(r.get('sure_sim_gorev'), 1)} | {_s(r.get('takip_hatasi_maks_m'), 3)} | "
          f"{'**✓**' if r['basari'] else '✗'} |")
    a("")
    return "\n".join(L)


def main() -> int:
    metin = uret()
    README_YOL.write_text(metin, encoding="utf-8")
    print(f"[t214a_rapor] {README_YOL} ({len(metin)} karakter)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

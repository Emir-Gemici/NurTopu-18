"""README_T213B.md üreteci — H1 koşum kanıtları ÖLÇÜMDEN yazılır, elle düzenlenmez (T213-B).

Girdi: `results/fdr_sprint_20260910/H1/kosum/<kaynak>_<h>_<lv>_<seed>.json` + `ozet_kosum.json`
(gorev_kosumu.kos / ozet_kur). Çıktı: aynı klasörde `README_T213B.md`.
Deterministiktir: tarih `ozet_kosum.json`'dan alınır → aynı JSON'lar aynı README'yi verir
(kilit: tests/test_sim_mujoco_zincir.py — diskteki README üreteç çıktısıyla BAYT-EŞ olmalı).

Kullanım:  venv python simulation/mujoco/kosum_readme.py [--out <kosum klasörü>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
for _p in (str(BURASI.parent / "scripts"), str(KOK / "codes"), str(BURASI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gorev_kosumu                                       # noqa: E402
from karar_sozlesmesi import IKA_IZ_GENISLIGI_M           # noqa: E402

README_ADI = "README_T213B.md"
TAKIP_HATA_M = 0.50            # CONTRACTS §4 — üretim planlayıcısının takip payı varsayımı
ESIK = "≥ 12/15 harita (× 3 tohum) — ON_KAYIT H1-K5; gevşetilmez"


def _kosumlar(out: Path):
    rs = []
    for p in sorted(out.glob("*_*_*_*.json")):
        if p.name == "ozet_kosum.json":
            continue
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if r.get("rota_kaynak") in gorev_kosumu.ROTA_KAYNAKLARI:
            rs.append(r)
    sira = {k: i for i, k in enumerate(gorev_kosumu.ROTA_KAYNAKLARI)}
    lvs = {lv: i for i, lv in enumerate(("kolay", "orta", "zor"))}
    rs.sort(key=lambda r: (sira[r["rota_kaynak"]], r["harita"], lvs.get(r["senaryo"], 9), r["seed"]))
    return rs


def _f(v, nd=2):
    return "—" if v is None else f"{v:.{nd}f}"


def _dag(d):
    if not d:
        return "—"
    return f"n={d['n']} · min {d['min']} · medyan {d['medyan']} · ort {d['ort']} · maks {d['maks']}"


def _neden(r) -> str:
    """Koşumun tek satırlık sonucu/nedeni (ölçülen alanlardan)."""
    if r["basari"]:
        return "BAŞARI"
    if r["cikis_kodu"] == 2:
        return "NO_ROUTE (model karar vermedi)"
    if r["cikis_kodu"] == 1:
        return "rota gelmedi"
    if r["cikis_kodu"] == 3:
        return "sürüş izni gelmedi (hakem)"
    a = r.get("rota_engel_aciklik_m")
    if r["temas_sayisi"] > 0:
        if a is not None and a < r["ika_yari_genislik_m"]:
            return f"temas · rota inşaat gereği geçilemez (açıklık {a:.3f} < {r['ika_yari_genislik_m']:.2f})"
        if a is not None and a < TAKIP_HATA_M:
            return f"temas · açıklık takip bandında ({a:.3f} < {TAKIP_HATA_M:.2f})"
        return f"temas · açıklık {_f(a, 3)} ≥ {TAKIP_HATA_M:.2f} (sürücü kusuru adayı)"
    if r["cikis_kodu"] == 4:
        return "süre doldu / HB'ye ulaşılamadı (temassız)"
    return f"çıkış {r['cikis_kodu']}"


def uret(out: Path) -> str:
    out = Path(out)
    oz = json.loads((out / "ozet_kosum.json").read_text(encoding="utf-8"))
    rs = _kosumlar(out)
    yari = (IKA_IZ_GENISLIGI_M + gorev_kosumu.araclar.IKA_TEKER_W) / 2.0
    L = []
    L.append("# H1 · T213-B — OPEN_ROUTE → sim hakem → İKA MuJoCo fizik sürüşü (15 harita × 3 tohum)")
    L.append("")
    L.append(f"Üreteç: `simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak {{gt,model}} --res 1280 "
             f"--tohumlar 42,43,44` → bu klasördeki `<kaynak>_<harita>_<senaryo>_<tohum>.json` + `ozet_kosum.json`; "
             f"bu README `simulation/mujoco/kosum_readme.py` ile **ölçümden** yazılır, elle düzenlenmez "
             f"(kilit: bayt-eş). Özet tarihi: {oz['tarih']}.")
    L.append("")
    L.append("Etiketler (ON_KAYIT §5.2): **YER GERÇEĞİ** = `arena.route_waypoints` (açık yolun merkez hattı, "
             "engel kaçınması YOK; 3,3 m segmentler `MAX_SEGMENT_M` 2,10'a bölünür — D-438 c) · "
             "**ÜRETİM MODELİ** = `iha_haritala` (v36, OBB kapalı, sim'e özel eğitim YOK). "
             "Sürüş her ikisinde AYNI: `ika_nav.navigate` + `MuJoCoSurucu`, 10 Hz kontrol, 2 ms fizik, SİM SAATİ.")
    L.append("")
    L.append("## 1. Özet (`ozet_kosum.json`)")
    L.append("")
    L.append("| kaynak | n | rota bulundu | rota doğru | OPEN_ROUTE ACK [ika,yks] | IKA_GO ACK | HB içinde | temas var | süre aşımı | **BAŞARI** | harita (3/3) | eşik |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in gorev_kosumu.ROTA_KAYNAKLARI:
        o = oz["kaynaklar"].get(k)
        if not o:
            L.append(f"| {k} | 0 | — | — | — | — | — | — | — | **ÖLÇÜLMEDİ** | — | {ESIK} |")
            continue
        L.append(f"| {k} ({o['etiket']}) | {o['n']} | {o['rota_bulundu_n']} | {o['rota_dogru_n']} | "
                 f"{o['open_route_ack_ika_yks_n']} | {o['ika_go_ack_n']} | {o['hb_icinde_n']} | {o['temas_var_n']} | "
                 f"{o['sure_asimi_n']} | **{o['basari_n']}/{o['n']} ({o['basari_orani']:.3f})** | "
                 f"{o['harita_hepsi_basarili_n']}/{o['harita_n']} | {ESIK} |")
    L.append("")
    L.append("Başarı tanımı (K5): çıkış 0 ∧ rota bulundu ∧ HB 2×2 m karesi içinde ∧ temas 0 ∧ sürüş ≤ 600 s sim.")
    L.append("")
    L.append("## 2. Sürüş süresi (sim saniye — SANAL, `data.time`; İHA kolu kinematik profil süresi)")
    L.append("")
    L.append("| kaynak | başarılı koşumlar | tüm koşumlar | varış mesafesi (m) | duvar saati toplam (s) |")
    L.append("|---|---|---|---|---|")
    for k in gorev_kosumu.ROTA_KAYNAKLARI:
        o = oz["kaynaklar"].get(k)
        if o:
            L.append(f"| {k} | {_dag(o['sure_sim_ika_basarili'])} | {_dag(o['sure_sim_ika_hepsi'])} | "
                     f"{_dag(o['varis_mesafesi_m'])} | {o['duvar_saati_s_toplam']} |")
    L.append("")
    L.append("Senaryo kırılımı:")
    L.append("")
    L.append("| kaynak | senaryo | n | başarı | HB içinde | temas var |")
    L.append("|---|---|---|---|---|---|")
    for k in gorev_kosumu.ROTA_KAYNAKLARI:
        o = oz["kaynaklar"].get(k)
        if o:
            for lv, sv in o["senaryo"].items():
                L.append(f"| {k} | {lv} | {sv['n']} | {sv['basari_n']} | {sv['hb_icinde_n']} | {sv['temas_var_n']} |")
    L.append("")
    L.append("## 3. Teşhis — başarısızlık nedenleri (ölçülen alanlardan sayılır)")
    L.append("")
    L.append(f"`rota_engel_aciklik_m`: rota polyline'ı ile en yakın engel geomunun (moloz/tıkama/chicane/bariyer) "
             f"XY OBB açıklığı. İKA yarı genişliği {yari:.2f} m (iz {IKA_IZ_GENISLIGI_M} TAHMİN + teker). "
             f"Açıklık < {yari:.2f} → rota **inşaat gereği** çarpışmasız izlenemez (sürücü sıfır hatayla gitse bile). "
             f"{yari:.2f}–{TAKIP_HATA_M:.2f} → üretim planlayıcısının `TAKIP_HATA_M` payının altında (CONTRACTS §4 "
             f"`R_GEREKLI_M` 1,10 açıklık garantisi GT merkez hattında YOKTUR).")
    L.append("")
    L.append("| kaynak | temas ∧ geçilemez (< yarı gen.) | temas ∧ takip bandı | temas ∧ açıklık ≥ 0,50 (sürücü adayı) | kod 3 (izin yok) | kod 2 (NO_ROUTE) | kod 4 temassız |")
    L.append("|---|---|---|---|---|---|---|")
    for k in gorev_kosumu.ROTA_KAYNAKLARI:
        ks_ = [r for r in rs if r["rota_kaynak"] == k]
        if not ks_:
            continue
        gec = sum(1 for r in ks_ if r["temas_sayisi"] > 0 and r.get("rota_engel_aciklik_m") is not None
                  and r["rota_engel_aciklik_m"] < r["ika_yari_genislik_m"])
        band = sum(1 for r in ks_ if r["temas_sayisi"] > 0 and r.get("rota_engel_aciklik_m") is not None
                   and r["ika_yari_genislik_m"] <= r["rota_engel_aciklik_m"] < TAKIP_HATA_M)
        sur = sum(1 for r in ks_ if r["temas_sayisi"] > 0 and (r.get("rota_engel_aciklik_m") is None
                  or r["rota_engel_aciklik_m"] >= TAKIP_HATA_M))
        k3 = sum(1 for r in ks_ if r["cikis_kodu"] == 3)
        k2 = sum(1 for r in ks_ if r["cikis_kodu"] == 2)
        k4t = sum(1 for r in ks_ if r["cikis_kodu"] == 4 and r["temas_sayisi"] == 0)
        L.append(f"| {k} | {gec} | {band} | {sur} | {k3} | {k2} | {k4t} |")
    L.append("")
    L.append("## 4. Koşum tablosu (her satır bir JSON)")
    L.append("")
    L.append("| kaynak | harita | senaryo | tohum | rota | doğru | wp | açıklık m (geom) | çıkış | HB | varış m | temas | sürüş sim-s | başarı | sonuç/neden |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rs:
        a = r.get("rota_engel_aciklik_m")
        ag = f"{a:.3f} ({r.get('rota_engel_aciklik_geom')})" if a is not None else "—"
        L.append(f"| {r['rota_kaynak']} | {r['harita']} | {r['senaryo']} | {r['seed']} | "
                 f"{'✓' if r['rota_bulundu'] else '✗'} | {'✓' if r['rota_dogru'] else '✗'} | {r['wp_sayisi']} | {ag} | "
                 f"{r['cikis_kodu']} | {'✓' if r['hb_icinde'] else '✗'} | {_f(r['varis_mesafesi_m'])} | "
                 f"{r['temas_sayisi']} | {_f(r['sure_sim_ika'], 1)} | {'**✓**' if r['basari'] else '✗'} | {_neden(r)} |")
    L.append("")
    L.append("## 5. Sınırlar (rapora yazılır)")
    L.append("")
    L.append("- İHA uçuşu **kinematik** (mocap; aerodinamik yok); `sure_sim_iha_profil` = fırlatma→iniş profil süresi.")
    L.append("- Hakem onayı sim'de **otomatik** (`sim_hakem`, mesajlar `sim: true`, CONTRACTS §6.7.1) — **saha kanıtı sayılmaz**.")
    L.append(f"- İKA iz genişliği {IKA_IZ_GENISLIGI_M} m **TAHMİN** (DDR'de yok, CONTRACTS §4.1); teker armature 0,01 kg·m² TAHMİN "
             "(fizik kararlılığı için, araclar.py); motor tork sınırı yok; modeller basitleştirilmiş (D-438 ek).")
    L.append("- `haritala` hesap süresi sim'de modellenmez (rota tarama biter bitmez yayınlanır); OBB araç maskesi kapalı.")
    L.append("- Yer işaretleri (İHA-İB, HB pedi/H, KB karesi) arena MJCF'inde 1–7 cm kalın **çarpışan** kutulardır; sürücü "
             "bunları yüklenen modelde çarpışmasız yapar (`isaretleri_carpismasiz_yap`) — MJCF/sha256 değişmez.")
    L.append("- `ika_nav.steer()` geri gitmez (teker hızı ≥ 0; pivot dönüş yok) — dokunulmadı, kayıt (CONTRACTS §4.1).")
    L.append("- `TURN_GAIN` 1,8: 1,3 m/s tabanda GT koşumlarında takip hatası ≤ 0,15 m ölçüldü (teşhis yörüngesi, 1 zor 43); değiştirilmedi.")
    L.append("- Temas koşumu **durdurmaz** (kayıt); başarı temas = 0 ister. Portlar yalnız ephemeral (127.0.0.1:0).")
    L.append("")
    L.append("## 6. Kusur kayıtları (kanıtlı; REVIEW_LOG'a mimar taşır)")
    L.append("")
    L.append("1. **Arena yerleşimi — GT merkez hattı engelle kesişiyor (T212 `arena_mjcf.yerlesim`).** Kapalı yol tıkamaları "
             "(`tikama_<yol>_<k>_<j>`, t = 0,30–0,80, u ∈ ±(lane_w/2+0,5), v ∈ ±1,8) yollar HB'ye yaklaşırken açık yolun "
             "hattına taşıyor; chicane'lar (`off ≥ clear+0,4`, ama 1,4× büyütülmüş 1,8–3,6 m yarı-boy plakalar, kıvrımlı hat) "
             "merkez hattı kesebiliyor. Ölçüm: yukarıdaki §3 tablosu ('temas ∧ geçilemez') ve §4 açıklık sütunu. "
             "Örnek (10 Eyl teşhis yörüngesi): `gt 1 zor 43` — `tikama_2_2_2` (yol 2 kapalı) açık yol 3 hattına 0,003 m; "
             "İKA 88,9 s'de takıldı, 600 s'e dek 6,6 m kala. Üretim planlayıcısı böyle rota ÜRETMEZ (R_GEREKLI 1,10 m); "
             "GT merkez hattı bu garantiyi taşımaz → **GT etiketli oran sürücü kusuru değil, rota inşaatının ölçümüdür**.")
    L.append("2. **`sim_hakem` sıra kusuru (düzeltildi, yeniden koşuldu).** İKA'nın OPEN_ROUTE ACK kopyası hakeme "
             "OPEN_ROUTE'tan ÖNCE gelince kanıt atılıyordu; İHA 'ika' ACK'ını gördüğü için İKA'ya tekrar göndermez → kopya bir "
             "daha gelmez → 2/2 asla, çıkış 3 (`gt 1 orta 44` ilk koşum: ack_listesi t=32,68 ACK, sonra ROTA_ALINDI). "
             "Erken kanıt seq ile saklanıp rota gelince eşleniyor (test E, mutasyonlu). İlk toplu koşumda 3/45 GT koşumu "
             "bu yüzden kod 3 verdi (`ilk_toplu_kosum_cikti.txt`: gt 1 orta 44, gt 2 zor 44, gt 5 orta 43); düzeltme sonrası "
             "yalnız bu üçü yeniden koşuldu (→ kod 4 temas/geçilemez, başarı, başarı), JSON'lar yenisidir. "
             "⚠ **Üretim YKS'de aynı sıra:** `comms/yks_gui.py:2081` `if (self.rota and ref == self.rota['seq'] …)` — "
             "kopya rota'dan önce gelirse `ika_rota_ack`'a yazılmaz; İHA→YKS ilk datagramı kayıpsa tek yayınlı OPEN_ROUTE'ta "
             "2/2 kilitlenir (sürekli yeniden yayında geçicidir). Mimar kararı: T216 alanı, burada DOKUNULMADI.")
    L.append("3. **Yer işaretleri çarpışan kutu** (arena MJCF, T213-A ile eş zamanlı düzenleniyor → MJCF'e dokunulmadı; "
             "sürücü modelde kapatıyor, `isaretler_carpismasiz` alanı JSON'da).")
    L.append("")
    L.append("## 7. Komutlar")
    L.append("")
    L.append("```")
    L.append("venv python simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak gt    --res 1280 --tohumlar 42,43,44")
    L.append("venv python simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak model --res 1280 --tohumlar 42,43,44")
    L.append("venv python simulation/mujoco/gorev_kosumu.py --map 1 --level zor --seed 43 --rota-kaynak gt   # tek koşum")
    L.append("venv python simulation/mujoco/kosum_readme.py                                                  # bu README")
    L.append("venv python -B -m unittest discover -s tests -p test_sim_mujoco_zincir.py")
    L.append("```")
    L.append("")
    L.append("Klasör: `<kaynak>_<h>_<lv>_<seed>.json` (metrik, git'te) · `<kaynak>_<h>_<lv>_<seed>/iha_scan/` "
             "(tarama kareleri/mozaik — **git dışı**, `--hepsi` ile bayt-eş yeniden üretilir; model koşumlarında "
             "`detection.json`/`rota.json` git'te).")
    L.append("")
    return "\n".join(L)


def yaz(out: Path) -> Path:
    out = Path(out)
    p = out / README_ADI
    p.write_text(uret(out), encoding="utf-8")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="README_T213B.md üreteci (ölçümden)")
    ap.add_argument("--out", default=str(gorev_kosumu.KOSUM_KOK))
    a = ap.parse_args(argv)
    p = yaz(Path(a.out))
    print(f"[kosum_readme] {p} ({p.stat().st_size} B)")


if __name__ == "__main__":
    main()

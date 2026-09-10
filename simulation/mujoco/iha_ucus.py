"""İHA KİNEMATİK uçuş profili + 1 Hz nadir tarama (MuJoCo render).

SINIR (rapora yazılır): İHA uçuşu KİNEMATİKTİR — mocap gövde, aerodinamik/itki modeli
YOK; poz zamanın fonksiyonudur (`world_generator._timed_flight` faz hızları). Yalnız
İKA fizik gövdedir (bu görevde KB'de durur). Sim saati = MuJoCo `data.time`
(`mj_step`, 2 ms); kare zamanları tam saniyelerdir.

Profil (world_generator.iha_flight ile aynı şekil; farkı: çıkış/iniş İHA-İB 30×30
merkezine, x=+42 — D-438: 8×8 iniş alanı yanlıştı):
  mancınık (İHA-FB, x=−26) → doğuya tırmanış → sola 180° raketrak → kuzey kenar →
  30 m'de 4 sütunlu SERPANTİN (x=−18,−6,6,18; uçlarda yarım daire U dönüşleri) →
  sağa çıkış dönüşü → İHA-İB üstünde güneye sokulma → PARAŞÜT (~20 m) → pede iniş.

TARAMA SÖZLEŞMESİ (`plugins/navitas_scan_cam.cc` ↔ `scripts/iha_haritala.py`):
  <out>/kareler/scan_%05d.jpg  ve  <out>/poses.csv (başlıksız: n,t,x,y,z,yaw)
  n. kare ↔ n. satır BİREBİR (aynı sim anında yazılır). yaw = gövde +X'in dünya
  azimutu (rad, +X doğu, CCW). Kamera: görüntü SAĞI = burun, YUKARISI = sol kanat
  (Gazebo sdf pozuyla aynı) → `iha_haritala --rot-isaret +1` kuzey-yukarı verir.
  hfov = 1.3 rad (model.sdf), kare kare (fovy = hfov). `kareler/` alt dizini
  `record_in_container.sh`'ın host düzenidir; `meta.txt` de aynı anahtarları taşır.

Kullanım:
  venv python simulation/mujoco/iha_ucus.py --map 1 --level kolay --seed 42 \
      --out results/fdr_sprint_20260910/H1/harita_1_kolay
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
SCRIPTS = BURASI.parent / "scripts"
for _p in (str(SCRIPTS), str(KOK / "codes"), str(BURASI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arena                                              # noqa: E402
import arena_mjcf                                         # noqa: E402
import araclar                                            # noqa: E402
from world_generator import _arc, _timed_flight, SCAN_Z   # noqa: E402
from iha_haritala import (HFOV, HTAB_HALF_MARJ, YAW_TOL, Z_TOL,   # noqa: E402
                          MOZ_M, MOZ_PX)

assert abs(HFOV - arena_mjcf.HFOV_RAD) < 1e-12, "hfov sözleşmesi: iha_haritala ≠ arena_mjcf"

KARE_HZ = 1.0
ROLL_DERECE = 35.0
PARASUT_YUKSEKLIK = 3.2          # harness → kanopi rim (araclar.parasut_meshleri ip_boyu)


# ── Uçuş profili ───────────────────────────────────────────────────────────

def ucus_noktalari(cx: float = 0.0, cy: float = 0.0):
    """(x, y, z, faz) yoğun yol — world_generator.iha_flight şekli, İHA-İB 30×30'a iniş."""
    C = math.pi
    ibx = arena_mjcf.IHA_IB_MERKEZ_X + cx
    pts = [
        (cx - 26.0, cy, 0.5, "rampa"),
        (cx - 23.0, cy, 1.4, "kalkis"),
        (cx - 6.0, cy, 6.5, "kalkis"),
        (cx + 20.0, cy, 14.0, "tirmanis"),
    ]
    pts += _arc(cx + 20.0, cy + 12.0, 12.0, -C / 2, C / 2, 14.0, 22.0, "tirmanis")
    pts += [(cx - 10.0, cy + 27.0, 27.0, "tirmanis")]
    pts += _arc(cx - 10.0, cy + 19.0, 8.0, C / 2, C, 27.0, SCAN_Z, "tirmanis")
    cols = [-18.0, -6.0, 6.0, 18.0]
    ys = 20.0
    for i, lx in enumerate(cols):
        south = (i % 2 == 0)
        y_end = -ys if south else ys
        pts.append((cx + lx, cy + y_end, SCAN_Z, "tarama"))
        if i < len(cols) - 1:
            mid = lx + 6.0
            if south:
                pts += _arc(cx + mid, cy - ys, 6.0, C, 2 * C, SCAN_Z, SCAN_Z, "donus")
            else:
                pts += _arc(cx + mid, cy + ys, 6.0, C, 0.0, SCAN_Z, SCAN_Z, "donus")
    # çıkış: son sütun kuzey ucu (x=+18) → SAĞ U-dönüş R=12 → İHA-İB hattı (x=+42), güneye
    pts += _arc(cx + 30.0, cy + ys, 12.0, C, 0.0, SCAN_Z, SCAN_Z, "donus")
    pts += [
        (ibx, cy + 13.0, 26.0, "sokulma"),
        (ibx, cy + 6.0, 21.0, "sokulma"),
        (ibx, cy + 4.5, 19.5, "parasut"),
        (ibx, cy + 2.0, 12.0, "parasut"),
        (ibx, cy + 0.5, 4.5, "parasut"),
        (ibx, cy, 0.35, "parasut"),
    ]
    return pts


def _sar(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class UcusProfili:
    """Zaman → (pos, yaw, pitch, roll, faz). Segment yaw'ı = segment yönü (tarama
    bacaklarında tam ±π/2 → iha_haritala YAW_TOL süzgecinden geçer)."""

    def __init__(self, cx=0.0, cy=0.0):
        self.fp = ucus_noktalari(cx, cy)
        tl = _timed_flight(self.fp)
        self.t = np.array([p[0] for p in tl])
        self.xyz = np.array([[p[1], p[2], p[3]] for p in tl])
        n = len(tl)
        yaw = np.zeros(n); pitch = np.zeros(n); roll = np.zeros(n)
        for i in range(n - 1):
            d = self.xyz[i + 1] - self.xyz[i]
            yaw[i] = math.atan2(d[1], d[0])
            pitch[i] = max(-0.45, min(0.45, math.atan2(d[2], math.hypot(d[0], d[1]))))
        yaw[-1], pitch[-1] = yaw[-2], 0.0
        for i in range(1, n - 1):
            faz = self.fp[i + 1][3]
            if faz in ("donus", "tirmanis"):
                dy = _sar(yaw[i + 1] - yaw[i]) if i + 1 < n - 1 else 0.0
                if abs(dy) > math.radians(2):
                    roll[i] = -math.copysign(math.radians(ROLL_DERECE), dy)   # sola dönüş = sol kanat aşağı
        for _ in range(2):
            roll = np.concatenate([[roll[0]], (roll[:-1] + roll[1:]) / 2.0])
        # T213-A KUSUR DÜZELTMESİ (10 Eyl, ölçüldü): yumuşatma bir önceki dönüş yayının yatışını
        # sonraki DÜZ tarama bacağına sızdırıyordu (bacak tek segment → tüm bacak boyunca roll
        # ±26,2°). 30 m'de 26,2° yatış nadir noktasını 14,8 m yana kaydırır; kare süzgeci yalnız
        # z ve yaw'a baktığından bu kareler mozaiğe KABUL ediliyor ve içerik ±15 m kaymış
        # yerleşiyordu (T212 K2/K3 mozaikleri bu hatayla kuruldu). Düz tarama segmentinde roll = 0.
        for i in range(n):
            if self.fp[min(i + 1, n - 1)][3] == "tarama":
                roll[i] = 0.0
        self.yaw, self.pitch, self.roll = yaw, pitch, roll
        self.faz = [p[3] for p in self.fp]
        self.t_parasut = float(self.t[next(i for i, p in enumerate(self.fp) if p[3] == "parasut")])
        self.t_inis = float(self.t[-1])
        self.t_tarama0 = float(self.t[next(i for i, p in enumerate(self.fp) if p[3] == "tarama")])
        self.t_tarama_son = float(max(self.t[i] for i, p in enumerate(self.fp) if p[3] in ("tarama", "donus")))

    def durum(self, t: float):
        if t <= self.t[0]:
            i, s = 0, 0.0
        elif t >= self.t[-1]:
            return self.xyz[-1].copy(), float(self.yaw[-1]), 0.0, 0.0, self.faz[-1]
        else:
            i = int(np.searchsorted(self.t, t, side="right") - 1)
            s = (t - self.t[i]) / max(self.t[i + 1] - self.t[i], 1e-9)
        pos = self.xyz[i] + (self.xyz[min(i + 1, len(self.t) - 1)] - self.xyz[i]) * s
        return pos, float(self.yaw[i]), float(self.pitch[i]), float(self.roll[i]), self.faz[min(i + 1, len(self.faz) - 1)]


def quat_ypr(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """Gövde X burun, Y sol, Z yukarı; pitch + = burun yukarı; roll + = sol kanat yukarı."""
    import mujoco
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, -sp], [0, 1, 0], [sp, 0, cp]])       # Ry(−pitch)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    R = Rz @ Ry @ Rx
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, R.reshape(9))
    return q


# ── Kapsama (H1-K2 ön-ölçümü, iha_haritala süzgeçleriyle) ──────────────────

def kare_kabul(x, y, z, yaw, cx=0.0, cy=0.0) -> bool:
    """iha_haritala.mozaik_kur'un kare süzgeci (aynı sabitler)."""
    if abs(z - SCAN_Z) > Z_TOL or abs(abs(yaw) - math.pi / 2) > YAW_TOL:
        return False
    return abs(x - cx) <= HTAB_HALF_MARJ and abs(y - cy) <= HTAB_HALF_MARJ


def htab_kapsama(pozlar: dict, cx=0.0, cy=0.0, hucre_m=0.25) -> float:
    """Kabul edilen karelerin (yaw ±90° → eksen hizalı) yer ayak izlerinin HTAB'ı örtme oranı."""
    n = int(round(arena.HTAB / hucre_m))
    ortu = np.zeros((n, n), bool)
    for (x, y, z, yaw) in pozlar.values():
        if not kare_kabul(x, y, z, yaw, cx, cy):
            continue
        yarim = z * math.tan(HFOV / 2.0)
        x0 = int(math.floor((x - yarim - cx + arena.HTAB_HALF) / hucre_m))
        x1 = int(math.ceil((x + yarim - cx + arena.HTAB_HALF) / hucre_m))
        y0 = int(math.floor((y - yarim - cy + arena.HTAB_HALF) / hucre_m))
        y1 = int(math.ceil((y + yarim - cy + arena.HTAB_HALF) / hucre_m))
        ortu[max(0, y0):min(n, y1), max(0, x0):min(n, x1)] = True
    return float(ortu.mean())


# ── Tarama koşumu ───────────────────────────────────────────────────────────

def tara(harita_id: int, lv: str, seed: int = arena_mjcf.SEED_VARSAYILAN, *,
         out: Path, res: int = arena_mjcf.KAM_RES_VARSAYILAN, fizik: bool = True,
         onizleme: bool = True, max_kare: int | None = None, jpg_kalite: int = 92,
         onizleme_res: int = 640, yol_dokusu: str = arena_mjcf.YOL_DOKUSU_VARSAYILAN,
         varyant: str = arena_mjcf.VARYANT_VARSAYILAN,
         zemin_dokusu: str = arena_mjcf.ZEMIN_DOKUSU_VARSAYILAN) -> dict:
    """Uçuşu koş, 1 Hz tarama karelerini + poses.csv + meta.txt yaz. Döner: özet dict.
    `varyant`/`zemin_dokusu` (T213-A) arena_mjcf render varyantı; meta.txt'ye yazılır."""
    import cv2
    import mujoco

    arena_mjcf.varyant_dogrula(varyant, zemin_dokusu)
    out = Path(out)
    kare_dir = out / "kareler"
    kare_dir.mkdir(parents=True, exist_ok=True)
    for eski in kare_dir.glob("scan_*.jpg"):
        eski.unlink()
    H = arena.harita(harita_id, lv)
    t0 = time.perf_counter()
    m = arena_mjcf.yukle(harita_id, lv, seed, kam_res=res, yol_dokusu=yol_dokusu,
                         varyant=varyant, zemin_dokusu=zemin_dokusu)
    d = mujoco.MjData(m)
    t_yukle = time.perf_counter() - t0
    iha = m.body_mocapid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "iha")]
    par = m.body_mocapid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "parasut")]
    prof = UcusProfili(0.0, 0.0)
    t_son = prof.t_inis + 2.0

    def mocap_guncelle(t):
        pos, yaw, pitch, roll, faz = prof.durum(t)
        d.mocap_pos[iha] = pos
        d.mocap_quat[iha] = quat_ypr(yaw, pitch, roll)
        if t >= prof.t_inis:
            d.mocap_pos[par] = [pos[0], pos[1] - 1.2, 0.05]
            d.mocap_quat[par] = [1, 0, 0, 0]
        elif faz == "parasut":
            d.mocap_pos[par] = [pos[0], pos[1], pos[2] + PARASUT_YUKSEKLIK]
            d.mocap_quat[par] = [1, 0, 0, 0]
        else:
            d.mocap_pos[par] = [pos[0], pos[1], -60.0]
        return pos, yaw, faz

    r = mujoco.Renderer(m, height=res, width=res)
    ro = mujoco.Renderer(m, height=onizleme_res, width=onizleme_res) if onizleme else None
    poz_satirlari, pozlar = [], {}
    n = 0
    render_ms = []
    onizlemeler = {}

    def onizle(ad, kam):
        if ro is None:
            return
        ro.update_scene(d, camera=kam)
        img = cv2.cvtColor(ro.render(), cv2.COLOR_RGB2BGR)
        p = out.parent / f"onizleme_{ad}.jpg"
        cv2.imwrite(str(p), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        onizlemeler[ad] = p.name

    mocap_guncelle(0.0)
    mujoco.mj_forward(m, d)
    onizle("baslangic_ucuncu_sahis", "ucuncu_sahis")
    sonraki_kare_t = 0.0
    tarama_onizlendi = False
    t_bas = time.perf_counter()
    while d.time <= t_son + 1e-9:
        if d.time + 1e-9 >= sonraki_kare_t:
            pos, yaw, faz = mocap_guncelle(d.time)
            mujoco.mj_forward(m, d)
            tk = time.perf_counter()
            r.update_scene(d, camera="scan_camera")
            img = cv2.cvtColor(r.render(), cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(kare_dir / f"scan_{n:05d}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, jpg_kalite])
            render_ms.append((time.perf_counter() - tk) * 1000)
            x, y, z = (float(v) for v in pos)
            # navitas_scan_cam.cc: n,t,x,y,z,yaw — AYNI olayda, aynı anın pozu
            poz_satirlari.append(f"{n},{d.time:.3f},{x:.4f},{y:.4f},{z:.4f},{yaw:.6f}")
            pozlar[n] = (x, y, z, yaw)
            if onizleme and not tarama_onizlendi and faz == "tarama" and z >= SCAN_Z - Z_TOL:
                onizle("tarama_ucuncu_sahis", "ucuncu_sahis")
                onizle("tarama_nadir", "nadir_genel")
                tarama_onizlendi = True
            n += 1
            sonraki_kare_t += 1.0 / KARE_HZ
            if max_kare is not None and n >= max_kare:
                break
        if fizik:
            mocap_guncelle(d.time)
            mujoco.mj_step(m, d)
        else:
            d.time = sonraki_kare_t
    sure = time.perf_counter() - t_bas
    if onizleme:
        mocap_guncelle(min(prof.t_inis, d.time)); mujoco.mj_forward(m, d)
        onizle("inis_ucuncu_sahis", "ucuncu_sahis")
    r.close()
    if ro is not None:
        ro.close()

    (out / "poses.csv").write_text("\n".join(poz_satirlari) + "\n", encoding="utf-8")
    kb, hb = H["kb"], H["hb"]
    meta = {
        "LEVEL": lv, "MAP": harita_id, "SEED": seed,
        "HTAB_CENTER": "0,0", "KB_XY": f"{kb[0]:.2f},{kb[1]:.2f}", "HB_XY": f"{hb[0]:.2f},{hb[1]:.2f}",
        "SCAN_Z": SCAN_Z, "HFOV": HFOV, "RES": res, "SIM": "mujoco-kinematik",
        "YOL_DOKUSU": yol_dokusu, "VARYANT": varyant, "ZEMIN_DOKUSU": zemin_dokusu,
        "SCAN_END_T": f"{prof.t_tarama_son:.0f}", "LAND_T": f"{prof.t_inis:.0f}",
    }
    (out / "meta.txt").write_text("".join(f"{k}={v}\n" for k, v in meta.items()), encoding="utf-8")
    kabul = sum(kare_kabul(*p) for p in pozlar.values())
    ozet = {
        "harita": harita_id, "senaryo": lv, "seed": seed, "res": res, "fizik": fizik,
        "yol_dokusu": yol_dokusu, "varyant": varyant, "zemin_dokusu": zemin_dokusu,
        "kare_n": n, "kabul_edilen_kare": int(kabul),
        "htab_kapsama_orani": round(htab_kapsama(pozlar), 4),
        "sim_sure_s": round(float(d.time), 2), "t_tarama0": round(prof.t_tarama0, 2),
        "t_tarama_son": round(prof.t_tarama_son, 2), "t_parasut": round(prof.t_parasut, 2),
        "t_inis": round(prof.t_inis, 2),
        "render_ms_kare_ort": round(float(np.mean(render_ms)), 1) if render_ms else None,
        "render_ms_kare_maks": round(float(np.max(render_ms)), 1) if render_ms else None,
        "duvar_saati_s": round(sure, 2), "mjcf_yukleme_ms": round(t_yukle * 1000, 1),
        "poses_sha256": hashlib.sha256((out / "poses.csv").read_bytes()).hexdigest(),
        "onizleme": onizlemeler,
        "sinir": "İHA uçuşu KİNEMATİK (mocap); aerodinamik yok. Kamera renderi gerçek (MuJoCo).",
    }
    (out / "tarama_ozeti.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    return ozet


def main():
    ap = argparse.ArgumentParser(description="NAVITAS İHA kinematik uçuş + 1 Hz tarama (MuJoCo)")
    ap.add_argument("--map", type=int, default=1, choices=range(1, arena.HARITA_N + 1))
    ap.add_argument("--level", default="kolay", choices=arena.SCENARIOS)
    ap.add_argument("--seed", type=int, default=arena_mjcf.SEED_VARSAYILAN)
    ap.add_argument("--out", default=None, help="harita dizini (iha_scan/ altına yazar)")
    ap.add_argument("--res", type=int, default=arena_mjcf.KAM_RES_VARSAYILAN)
    ap.add_argument("--hizli", action="store_true", help="fizik adımı yok (yalnız kinematik + render)")
    ap.add_argument("--max-kare", type=int, default=None)
    ap.add_argument("--hepsi", action="store_true", help="15 haritayı tara (kok = --out)")
    ap.add_argument("--yol-dokusu", default=arena_mjcf.YOL_DOKUSU_VARSAYILAN, choices=arena_mjcf.YOL_DOKULARI)
    ap.add_argument("--varyant", default=arena_mjcf.VARYANT_VARSAYILAN, choices=arena_mjcf.VARYANTLAR,
                    help="T213-A render varyantı (taban | v1 | v2 | v3)")
    ap.add_argument("--zemin-dokusu", default=arena_mjcf.ZEMIN_DOKUSU_VARSAYILAN,
                    choices=arena_mjcf.ZEMIN_DOKULARI, help="v1+ zemin kaynağı")
    a = ap.parse_args()
    kok = Path(a.out) if a.out else KOK / "results" / "fdr_sprint_20260910" / "H1"
    ek = {"yol_dokusu": a.yol_dokusu, "varyant": a.varyant, "zemin_dokusu": a.zemin_dokusu}
    if a.hepsi:
        rows = []
        for h in range(1, arena.HARITA_N + 1):
            for lv in arena.SCENARIOS:
                oz = tara(h, lv, a.seed, out=kok / f"harita_{h}_{lv}" / "iha_scan", res=a.res,
                          fizik=not a.hizli, max_kare=a.max_kare, **ek)
                print(f"[iha_ucus] harita {h} {lv}: {oz['kare_n']} kare, kabul {oz['kabul_edilen_kare']}, "
                      f"kapsama {oz['htab_kapsama_orani']:.3f}, {oz['render_ms_kare_ort']} ms/kare")
                rows.append(oz)
        (kok / "tarama_ozeti_15.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        return
    out = (kok / f"harita_{a.map}_{a.level}" if not a.out else Path(a.out)) / "iha_scan"
    oz = tara(a.map, a.level, a.seed, out=out, res=a.res, fizik=not a.hizli, max_kare=a.max_kare, **ek)
    print(json.dumps(oz, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

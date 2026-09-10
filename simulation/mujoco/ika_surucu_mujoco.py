"""MuJoCoSurucu — `IkaSurucu` (CONTRACTS §7.2) arayüzünün MuJoCo fizik arka ucu (T213).

NEDEN: `ika_nav` motor komutunu `ika_surucu` soyutlamasından geçirir; Gazebo arka
ucu bu makinede koşamaz (D-438: gz yok). H1-K5 "İKA otonom sürüş fizikte" kapısı,
aynı `navigate` döngüsünün DDR ölçülü fizik gövdeyi (araclar.ika_govdesi) sürmesini
ister — teker hızı komutu, gövde pozu, moloz/bariyer temas sayacı, SİM SAATİ.

Sözleşme (IkaSurucu):
  hiz_ver(sag, sol) -> bool   m/s → teker eklem hız hedefi (rad/s = v / r_teker),
                              ctrlrange'e kırpılır; başarıysa True. İstisna sızmaz.
  konum_al()        -> (x, y, z, yaw)  gövde dünya pozu; yaw = gövde +X azimutu (rad)
  durdur(), saglikli()          IkaSurucu ortak sözleşmesi (ardışık hata sayacı)
Ek (sim'e özgü):
  adimla(dt)  -> data.time    fizik alt adımları (dt / timestep adet mj_step);
                              her alt adımda İKA–engel teması sayılır
  saat()      -> data.time    SİM SAATİ (ON_KAYIT §5.3) — ika_nav'a `saat=` olarak
                              enjekte edilir; sürüş süresi sanal saniyeyle ölçülür

Temas sayacı: İKA geomları (gövde + tekerler) ile `ENGEL_ONEKLERI` adlı geomlar
(moloz_, tikama_, chicane_, bariyer_, ub_duvar_) arasındaki her mujoco temas
kayıt edilir; zemin/işaret boyası sayılmaz. `temas_sayisi` = temas OLAYI sayısı
(yükselen kenar), `temas_adim` = temasta geçen alt adım sayısı.

İşaret boyaları (İHA-İB, HB pedi/H harfi, KB karesi) arena MJCF'inde 1–7 cm
kalınlığında ÇARPIŞAN kutulardır (arena_mjcf.py, T212). Ø125 mm tekerli İKA
için 4–6 cm'lik basamak demektir — boya değil. `isaretleri_carpismasiz_yap`
bunları yüklenen MODELDE (contype/conaffinity = 0) çarpışmasız yapar; MJCF
metni ve kanonik sha256 DEĞİŞMEZ (arena_mjcf T213-A ile eş zamanlı düzenleniyor;
kusur README_T213B'de kayıtlı).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

BURASI = Path(__file__).resolve().parent
_SCRIPTS = BURASI.parent / "scripts"
for _p in (str(_SCRIPTS), str(BURASI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import araclar                                   # noqa: E402
from ika_surucu import IkaSurucu                 # noqa: E402

ENGEL_ONEKLERI = ("moloz_", "tikama_", "chicane_", "bariyer_", "ub_duvar_")
ISARET_GEOMLARI = ("iha_ib", "hb_ped", "hb_H_sol", "hb_H_sag", "hb_H_orta",
                   "kb_N", "kb_S", "kb_W", "kb_E", "kb_kose")


def _geom_adlari(m) -> list[str]:
    import mujoco
    return [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or "" for i in range(m.ngeom)]


def isaretleri_carpismasiz_yap(m) -> list[str]:
    """Yer işaretlerini (boya) modelde çarpışmasız yap; değişen geom adlarını döndür."""
    import mujoco
    degisen = []
    for ad in ISARET_GEOMLARI:
        g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, ad)
        if g < 0:
            continue
        if m.geom_contype[g] != 0 or m.geom_conaffinity[g] != 0:
            m.geom_contype[g] = 0
            m.geom_conaffinity[g] = 0
            degisen.append(ad)
    return degisen


class MuJoCoSurucu(IkaSurucu):
    """DDR ölçülü fizik İKA'yı MuJoCo'da sürer (skid-steer, 4 hız aktüatörü)."""

    def __init__(self, model, data, *, teker_r: float = araclar.IKA_TEKER_R,
                 engel_onekleri=ENGEL_ONEKLERI, isaretler_carpismasiz: bool = True):
        import mujoco
        super().__init__()
        self.m, self.d = model, data
        self.teker_r = float(teker_r)
        self.ika = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ika")
        if self.ika < 0:
            raise ValueError("modelde 'ika' gövdesi yok")
        akt = {mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, i): i
               for i in range(model.nu)}
        eksik = [a for a in araclar.IKA_AKTUATORLER if a not in akt]
        if eksik:
            raise ValueError(f"İKA aktüatörleri eksik: {eksik}")
        self.sol_akt = [akt[a] for a in araclar.IKA_AKTUATORLER if a.endswith("_sol")]
        self.sag_akt = [akt[a] for a in araclar.IKA_AKTUATORLER if a.endswith("_sag")]
        self.w_maks = float(model.actuator_ctrlrange[self.sag_akt[0]][1])
        self.isaretler_degisti = isaretleri_carpismasiz_yap(model) if isaretler_carpismasiz else []
        adlar = _geom_adlari(model)
        self._ika_geom = np.array([model.body_rootid[model.geom_bodyid[g]] == self.ika
                                   for g in range(model.ngeom)], bool)
        self._engel_geom = np.array([any(a.startswith(o) for o in engel_onekleri)
                                     for a in adlar], bool)
        self._adlar = adlar
        self.temas_sayisi = 0        # temas olayı (yükselen kenar)
        self.temas_adim = 0          # temasta geçen alt adım
        self.temasta = False
        self.temas_geomlari = set()
        self.ilk_temas_t = None
        self.kararsiz_adim = 0       # mjWARN_BADQACC sayısı (fizik kararsızlığı)
        self.komut_sayisi = 0
        self.son_komut = (0.0, 0.0)
        self._mujoco = mujoco

    # ── IkaSurucu sözleşmesi ────────────────────────────────────────────────
    def _hiz_ver(self, sag, sol) -> bool:
        ws = max(-self.w_maks, min(self.w_maks, float(sag) / self.teker_r))
        wl = max(-self.w_maks, min(self.w_maks, float(sol) / self.teker_r))
        if not (math.isfinite(ws) and math.isfinite(wl)):
            return False
        for i in self.sag_akt:
            self.d.ctrl[i] = ws
        for i in self.sol_akt:
            self.d.ctrl[i] = wl
        self.komut_sayisi += 1
        self.son_komut = (float(sag), float(sol))
        return True

    def konum_al(self):
        p = self.d.xpos[self.ika]
        R = self.d.xmat[self.ika].reshape(3, 3)
        yaw = math.atan2(R[1, 0], R[0, 0])
        return float(p[0]), float(p[1]), float(p[2]), float(yaw)

    # ── sim'e özgü ─────────────────────────────────────────────────────────
    def teker_hedefleri(self):
        """(sağ rad/s, sol rad/s) — test/teşhis."""
        return float(self.d.ctrl[self.sag_akt[0]]), float(self.d.ctrl[self.sol_akt[0]])

    def saat(self) -> float:
        return float(self.d.time)

    def _temas_guncelle(self):
        n = int(self.d.ncon)
        if n == 0:
            self.temasta = False
            return
        g1 = self.d.contact.geom1[:n]
        g2 = self.d.contact.geom2[:n]
        vur = (self._ika_geom[g1] & self._engel_geom[g2]) | (self._engel_geom[g1] & self._ika_geom[g2])
        if vur.any():
            if not self.temasta:
                self.temas_sayisi += 1
                self.temasta = True
                if self.ilk_temas_t is None:
                    self.ilk_temas_t = float(self.d.time)
            self.temas_adim += 1
            for a, b in zip(g1[vur], g2[vur]):
                self.temas_geomlari.add(self._adlar[int(b if self._ika_geom[a] else a)])
        else:
            self.temasta = False

    def adimla(self, dt: float) -> float:
        """dt saniyelik fizik: round(dt/timestep) alt adım; her alt adımda temas sayımı."""
        mujoco = self._mujoco
        n = max(1, int(round(float(dt) / self.m.opt.timestep))) if dt > 0 else 0
        for _ in range(n):
            mujoco.mj_step(self.m, self.d)
            self._temas_guncelle()
        w = self.d.warning[mujoco.mjtWarning.mjWARN_BADQACC].number
        if w:
            self.kararsiz_adim = int(w)
        return float(self.d.time)

    def ozet(self) -> dict:
        x, y, z, yaw = self.konum_al()
        return {
            "konum": [round(x, 3), round(y, 3), round(z, 3)], "yaw_rad": round(yaw, 4),
            "temas_sayisi": int(self.temas_sayisi), "temas_adim": int(self.temas_adim),
            "temas_geomlari": sorted(self.temas_geomlari),
            "ilk_temas_t": None if self.ilk_temas_t is None else round(self.ilk_temas_t, 3),
            "kararsiz_adim": int(self.kararsiz_adim), "komut_sayisi": int(self.komut_sayisi),
            "isaretler_carpismasiz": list(self.isaretler_degisti),
            "teker_r_m": self.teker_r, "w_maks_rad_s": round(self.w_maks, 3),
        }

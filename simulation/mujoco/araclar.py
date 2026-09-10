"""Araç modelleri — İHA (sabit kanat, görsel mesh), İKA (DDR ölçülü fizik), paraşüt.

KULLANICI KARARI (10 Eyl 01:3x, D-438 ek): birebir CAD GEREKMİYOR; basitleştirilmiş
modeller serbest. Burada:
  · İHA  : procedural sabit kanat (gövde silindiri + burun + kanat + kuyruk + pervane),
           trimesh ile STL'e yazılır. Açıklık 1,8 m (DDR'de kanat açıklığı YOK —
           FDR §3.1.2 "BEYAN GEREKLİ"; görev tanımındaki ~1,8 m kullanıldı).
           Görsel; çarpışma yok (contype=0). Uçuş KİNEMATİKTİR (mocap).
  · İKA  : DDR ölçüleri — 488×440×310 mm, 9,40 kg, 4 teker Ø125 mm, iz genişliği
           0,39 m (TAHMİN, ON_KAYIT §3.3), dingil 0,36 m (varsayılan), skid-steer,
           azami 1,3 m/s. Fizik gövde: kutu + 4 menteşe tekerlek + hız aktüatörü.
  · Paraşüt: kubbe mesh (yarım küre) + askı ipleri; görsel, mocap.

Mesh dosyaları `simulation/mujoco/mesh/` altına yazılır (`mesh_uret()`); depoda dururlar,
yoksa ilk çağrıda üretilir.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

BURASI = Path(__file__).resolve().parent
MESH_DIR = BURASI / "mesh"
_CODES = BURASI.parents[1] / "codes"
if str(_CODES) not in sys.path:
    sys.path.insert(0, str(_CODES))
# T213 (CONTRACTS §4): İKA kinematik sabitleri TEK KAYNAK — burada yeniden yazılmaz.
from karar_sozlesmesi import (IKA_AZAMI_HIZ_MS, IKA_IZ_GENISLIGI_M,   # noqa: E402
                              IKA_TEKER_YARICAP_M)

# ── İHA ölçüleri (m) — basitleştirilmiş ────────────────────────────────────
IHA_ACIKLIK = 1.80        # kanat açıklığı (görev tanımı; DDR'de yok)
IHA_GOVDE_L = 1.25
IHA_GOVDE_R = 0.09
IHA_VETER = 0.30

# ── İKA ölçüleri (DDR) ──────────────────────────────────────────────────────
IKA_KUTLE_KG = 9.40
IKA_TEKER_R = IKA_TEKER_YARICAP_M      # Ø125 mm (karar_sozlesmesi, CONTRACTS §4)
IKA_TEKER_W = 0.05        # teker genişliği (yarım: 0.025)
IKA_IZ_M = IKA_IZ_GENISLIGI_M          # iz genişliği (TAHMİN — insan teyidine kadar)
IKA_DINGIL_M = 0.36       # dingil mesafesi (varsayılan)
IKA_GOVDE = (0.40, 0.32, 0.16)     # gövde kutusu L×W×H (toplam 488×440×310 içinde)
IKA_TEKER_KUTLE = 0.25
IKA_VMAX_MS = IKA_AZAMI_HIZ_MS         # DDR 1,3 m/s (karar_sozlesmesi)
IKA_TEKER_WMAX = IKA_VMAX_MS / IKA_TEKER_R     # ≈ 20,8 rad/s
# T213 ÖLÇÜM (10 Eyl): armature'suz teker eklemi + kv=0,6 hız servosu Euler 2 ms'de
# KARARSIZ — mjWARN_BADQACC 1377/1500 adım, İKA hiç ilerlemedi (kv·dt/I = 2,45 > 2).
# armature = redüktörlü motorun (KGX38, 200 rpm) tekere yansıyan rotor ataleti;
# 0,01 kg·m² ile kararlı (0/1500 uyarı), 1,0 m/s komutta 3 s'de 2,68 m. Değer
# TAHMİNDİR (DDR'de motor ataleti yok); fiziksel gerekçe: yüksek redüksiyonlu
# motorda yansıyan atalet teker ataletinin (4,9e-4) onlarca katıdır.
IKA_TEKER_ARMATURE = 0.01
IKA_BASLANGIC_Z = IKA_TEKER_R                   # gövde orijini = aks yüksekliği
IKA_KAM_YUKSEKLIK = 0.25
IKA_KAM_EGIM_DERECE = 15.0
IKA_EKLEMLER = ("j_on_sol", "j_arka_sol", "j_on_sag", "j_arka_sag")
IKA_AKTUATORLER = ("ika_on_sol", "ika_arka_sol", "ika_on_sag", "ika_arka_sag")

MESH_ADLARI = ("iha_govde", "iha_kanat", "iha_pervane", "parasut_kubbe", "parasut_ip")


# ── Mesh üretimi (trimesh) ──────────────────────────────────────────────────

def _tm():
    import trimesh
    return trimesh


def _kutu(tm, boyut, merkez):
    b = tm.creation.box(extents=boyut)
    b.apply_translation(merkez)
    return b


def _silindir_x(tm, r, L, merkez, sections=24):
    c = tm.creation.cylinder(radius=r, height=L, sections=sections)
    c.apply_transform(tm.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    c.apply_translation(merkez)
    return c


def iha_meshleri(tm):
    """(govde, kanat, pervane) trimesh nesneleri — X burun, Y sol kanat, Z yukarı."""
    govde = _silindir_x(tm, IHA_GOVDE_R, IHA_GOVDE_L, (0.0, 0.0, 0.0))
    burun = tm.creation.icosphere(subdivisions=2, radius=IHA_GOVDE_R * 1.05)
    burun.apply_translation((IHA_GOVDE_L / 2, 0, 0))
    kuyruk_koni = tm.creation.cone(radius=IHA_GOVDE_R, height=0.25, sections=24)
    kuyruk_koni.apply_transform(tm.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))
    kuyruk_koni.apply_translation((-IHA_GOVDE_L / 2, 0, 0))
    kanopi = tm.creation.icosphere(subdivisions=2, radius=0.08)
    kanopi.apply_scale((1.6, 1.0, 0.8))
    kanopi.apply_translation((0.22, 0, 0.08))
    govde_m = tm.util.concatenate([govde, burun, kuyruk_koni, kanopi])

    kanat = _kutu(tm, (IHA_VETER, IHA_ACIKLIK, 0.03), (-0.02, 0, 0.05))
    # kanat uçları (winglet)
    wl = _kutu(tm, (0.22, 0.02, 0.10), (-0.05, IHA_ACIKLIK / 2, 0.10))
    wr = _kutu(tm, (0.22, 0.02, 0.10), (-0.05, -IHA_ACIKLIK / 2, 0.10))
    htail = _kutu(tm, (0.20, 0.70, 0.02), (-0.62, 0, 0.03))
    vtail = _kutu(tm, (0.20, 0.02, 0.28), (-0.62, 0, 0.16))
    kanat_m = tm.util.concatenate([kanat, wl, wr, htail, vtail])

    gobek = _silindir_x(tm, 0.03, 0.05, (IHA_GOVDE_L / 2 + 0.10, 0, 0), sections=12)
    pal_v = _kutu(tm, (0.015, 0.04, 0.60), (IHA_GOVDE_L / 2 + 0.12, 0, 0))
    pal_h = _kutu(tm, (0.015, 0.60, 0.04), (IHA_GOVDE_L / 2 + 0.12, 0, 0))
    pervane_m = tm.util.concatenate([gobek, pal_v, pal_h])
    return govde_m, kanat_m, pervane_m


def parasut_meshleri(tm, yaricap=2.2, yukseklik=1.3, ip_boyu=3.2):
    """(kubbe, ipler) — kubbe tepe noktası z=+yukseklik, harness z=−ip_boyu."""
    # scipy YOK (venv'de kurulu değil): slice_plane yerine üst yarı yüzleri süz
    kure = tm.creation.icosphere(subdivisions=3, radius=1.0)
    ust = (kure.vertices[kure.faces][:, :, 2] >= -1e-9).all(axis=1)
    kure.update_faces(ust)
    kure.remove_unreferenced_vertices()
    kubbe = kure
    kubbe.apply_scale((yaricap, yaricap, yukseklik))
    ipler = []
    for k in range(8):
        a = 2 * math.pi * k / 8
        p0 = np.array([yaricap * math.cos(a), yaricap * math.sin(a), 0.0])
        p1 = np.array([0.0, 0.0, -ip_boyu])
        seg = tm.creation.cylinder(radius=0.015, height=1.0, sections=6,
                                   segment=[p0, p1])
        ipler.append(seg)
    harness = _kutu(tm, (0.25, 0.25, 0.15), (0, 0, -ip_boyu))
    ip_m = tm.util.concatenate(ipler + [harness])
    return kubbe, ip_m


def mesh_uret(zorla: bool = False) -> dict[str, Path]:
    """Mesh STL'lerini `mesh/` altına yaz (varsa ve zorla=False ise dokunma)."""
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    yollar = {ad: MESH_DIR / f"{ad}.stl" for ad in MESH_ADLARI}
    if not zorla and all(p.is_file() for p in yollar.values()):
        return yollar
    tm = _tm()
    g, k, p = iha_meshleri(tm)
    kubbe, ip = parasut_meshleri(tm)
    for ad, m in (("iha_govde", g), ("iha_kanat", k), ("iha_pervane", p),
                  ("parasut_kubbe", kubbe), ("parasut_ip", ip)):
        m.export(str(yollar[ad]), file_type="stl")
    return yollar


# ── MJCF parçaları ──────────────────────────────────────────────────────────

def mesh_assetleri() -> str:
    return "\n".join(f'    <mesh name="{ad}" file="{ad}.stl"/>' for ad in MESH_ADLARI)


def iha_govdesi(x: float, y: float, z: float, hfov_rad: float, kam_res: int) -> str:
    """İHA mocap gövdesi + nadir tarama kamerası.

    Kamera sözleşmesi (`models/iha/model.sdf` scan_camera ↔ `navitas_scan_cam.cc`):
    görüntü SAĞI = burun (+X), görüntü YUKARISI = sol kanat (+Y), bakış −Z (nadir).
    MuJoCo kamerası varsayılan olarak −z'ye bakar, +y yukarı → gövdeye BİRİM
    yönelimle bağlanınca bu sözleşme aynen sağlanır (`iha_haritala --rot-isaret +1`).
    Kare kare olduğundan yatay = dikey FOV: fovy = hfov."""
    fovy = math.degrees(hfov_rad)
    return f"""    <body name="iha" mocap="true" pos="{x:.3f} {y:.3f} {z:.3f}">
      <geom type="mesh" mesh="iha_govde" rgba="0.13 0.22 0.60 1" contype="0" conaffinity="0" group="1"/>
      <geom type="mesh" mesh="iha_kanat" rgba="0.92 0.92 0.95 1" contype="0" conaffinity="0" group="1"/>
      <geom type="mesh" mesh="iha_pervane" rgba="0.05 0.05 0.05 1" contype="0" conaffinity="0" group="1"/>
      <camera name="scan_camera" pos="0 0 -0.12" fovy="{fovy:.3f}" resolution="{kam_res} {kam_res}"/>
    </body>"""


def parasut_govdesi() -> str:
    """Paraşüt mocap gövdesi — açılana dek yer altında (z=−60) gizli."""
    return """    <body name="parasut" mocap="true" pos="0 0 -60">
      <geom type="mesh" mesh="parasut_kubbe" rgba="0.95 0.45 0.05 1" contype="0" conaffinity="0" group="1"/>
      <geom type="mesh" mesh="parasut_ip" rgba="0.12 0.12 0.12 1" contype="0" conaffinity="0" group="1"/>
    </body>"""


def ika_govdesi(x: float, y: float, yaw_rad: float) -> str:
    """İKA fizik gövdesi (DDR ölçülü). Orijin = aks yüksekliği (z = teker yarıçapı)."""
    L, W, H = IKA_GOVDE
    hx, hy = IKA_DINGIL_M / 2, IKA_IZ_M / 2
    r, hw = IKA_TEKER_R, IKA_TEKER_W / 2
    govde_kutle = IKA_KUTLE_KG - 4 * IKA_TEKER_KUTLE - 0.8 - 0.2
    e = math.radians(IKA_KAM_EGIM_DERECE)
    kam_xy = f"0 -1 0 {math.sin(e):.4f} 0 {math.cos(e):.4f}"
    tekerler = []
    for ad, sx, sy in (("on_sol", hx, hy), ("arka_sol", -hx, hy),
                       ("on_sag", hx, -hy), ("arka_sag", -hx, -hy)):
        tekerler.append(
            f'      <body name="teker_{ad}" pos="{sx:.3f} {sy:.3f} 0">\n'
            f'        <joint name="j_{ad}" type="hinge" axis="0 1 0" damping="0.05" '
            f'armature="{IKA_TEKER_ARMATURE:.4f}"/>\n'
            f'        <geom name="g_teker_{ad}" type="cylinder" size="{r:.4f} {hw:.3f}" '
            f'euler="90 0 0" rgba="0.06 0.06 0.06 1" mass="{IKA_TEKER_KUTLE:.2f}" '
            f'friction="1.2 0.005 0.0001" condim="3"/>\n'
            f'      </body>')
    return f"""    <body name="ika" pos="{x:.3f} {y:.3f} {IKA_BASLANGIC_Z:.4f}" euler="0 0 {math.degrees(yaw_rad):.2f}">
      <freejoint name="ika_serbest"/>
      <geom name="ika_govde" type="box" size="{L/2:.3f} {W/2:.3f} {H/2:.3f}" pos="0 0 {H/2:.3f}" rgba="0.26 0.33 0.20 1" mass="{govde_kutle:.2f}"/>
      <geom name="ika_ekutu" type="box" size="0.10 0.10 0.045" pos="-0.03 0 {H + 0.045:.3f}" rgba="0.10 0.10 0.12 1" mass="0.80"/>
      <geom name="ika_yuk" type="box" size="0.06 0.06 0.03" pos="0.10 0 {H + 0.03:.3f}" rgba="0.95 0.50 0.05 1" mass="0.20"/>
      <camera name="ika_kam" pos="{L/2 - 0.02:.3f} 0 {IKA_KAM_YUKSEKLIK - IKA_BASLANGIC_Z:.3f}" xyaxes="{kam_xy}" fovy="60"/>
      <camera name="ika_takip" pos="-1.6 0 1.0" xyaxes="0 -1 0 0.55 0 0.835" fovy="60"/>
{chr(10).join(tekerler)}
    </body>"""


def ika_aktuatorleri() -> str:
    kv = 0.6
    rng = f"-{IKA_TEKER_WMAX:.2f} {IKA_TEKER_WMAX:.2f}"
    satirlar = [f'    <velocity name="{a}" joint="{j}" kv="{kv}" ctrllimited="true" ctrlrange="{rng}"/>'
                for a, j in zip(IKA_AKTUATORLER, IKA_EKLEMLER)]
    return "  <actuator>\n" + "\n".join(satirlar) + "\n  </actuator>"

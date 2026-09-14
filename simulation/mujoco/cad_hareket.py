"""NEDEN: STL montajı eklem eksenlerinde hareket eder; kayıtlı fizik durumu değiştirilmez."""

import copy
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

import cad_modeller


KOK = cad_modeller.KOK
CIKTI = KOK / "results/fdr_33_20260914/cad_eklem_mesh"
TEKER_ESLEME = {"sol_on_teker": "j_on_sol", "sol_arka_teker": "j_arka_sol",
                "sag_on_teker": "j_on_sag", "sag_arka_teker": "j_arka_sag"}
PERVANE_GOSTERIM_HZ = 3.7
YUZ_GOSTERIM_DERECE = 22.0


def hazirla():
    sys.path.insert(0, str(KOK / "scripts"))
    from fdr_33_cad_teshis import bilesenler

    veri = copy.deepcopy(cad_modeller.hazirla())
    CIKTI.mkdir(parents=True, exist_ok=True)
    for ad in ("iha", "ika"):
        kaynaklar, pozlar, urdf = cad_modeller.urdf_oku(ad)
        donus = np.array(veri[ad]["rotasyon"])
        merkez = np.array(veri[ad]["orijin_cikarilan_m"])
        eklemler = {eklem.find("child").get("link"): eklem
                    for eklem in ET.parse(urdf).getroot().findall("joint")}
        kayitlar = []
        for kaynak, eski in zip(kaynaklar, veri[ad]["parcalar"]):
            link = kaynak["ad"].removeprefix(ad + "_").removesuffix("_0")
            mesh = kaynak["mesh"]
            eklem = eklemler.get(link)
            parcalar = [("", mesh, "govde")]
            if ad == "ika" and link != "base_link":
                secilen = []
                pivot = pozlar[link][:3, 3]
                for yuzler in bilesenler(mesh):
                    noktalar = mesh.vertices[mesh.faces[yuzler]].reshape(-1, 3)
                    fark = (noktalar.min(axis=0) + noktalar.max(axis=0)) / 2 - pivot
                    uygun = (np.linalg.norm(fark[:2]) < .001 and abs(fark[2]) < .08
                             if "teker" in link else np.linalg.norm(noktalar - pivot, axis=1).max() < .04)
                    if uygun:
                        parca = mesh.copy()
                        parca.update_faces(yuzler)
                        parca.remove_unreferenced_vertices()
                        secilen.append(parca)
                beklenen = 2 if "teker" in link else 4
                if len(secilen) != beklenen:
                    raise ValueError(f"CAD bileşen seçimi belirsiz: {link}, {len(secilen)}")
                if "teker" in link:
                    parcalar = [("", secilen[0], "lastik"), ("_jant", secilen[1], "jant")]
                else:
                    import trimesh
                    parcalar = [("", trimesh.util.concatenate(secilen), "kamera")]
            for ek, parca, malzeme in parcalar:
                parca.apply_transform(donus)
                parca.apply_translation(-merkez)
                kayit = {**eski, "ad": eski["ad"] + ek, "malzeme": malzeme,
                         "ucgen": len(parca.faces), "zarf_m": parca.bounds.tolist(),
                         "kaynak_ucgen": len(mesh.faces)}
                if eklem is not None and eklem.get("type") == "continuous":
                    eksen = np.fromstring(eklem.find("axis").get("xyz"), sep=" ")
                    eksen = (donus @ pozlar[link])[:3, :3] @ eksen
                    eksen /= np.linalg.norm(eksen)
                    kayit["eklem"] = {"ad": link, "pivot": ((donus @ pozlar[link])[:3, 3] - merkez).tolist(),
                                      "eksen": eksen.tolist(), "fizik_eklemi": TEKER_ESLEME.get(link)}
                if ad == "iha" and "pervane" in link:
                    kayit["malzeme"] = "pervane"
                elif ad == "iha" and kayit.get("eklem"):
                    kayit["malzeme"] = "kumanda_yuzeyi"
                hedef = CIKTI / (kayit["ad"] + ".stl")
                icerik = parca.export(file_type="stl")
                if hedef.exists() and hedef.read_bytes() != icerik:
                    raise ValueError(f"Mevcut CAD çıktısı korunur: {hedef}")
                if not hedef.exists():
                    hedef.write_bytes(icerik)
                kayit["hedef"] = hedef.relative_to(KOK).as_posix()
                kayit["hedef_sha256"] = hashlib.sha256(icerik).hexdigest()
                kayitlar.append(kayit)
        veri[ad]["parcalar"] = kayitlar
    (CIKTI / "manifest.json").write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
    return veri


def uygula(xml, manifest):
    kok = ET.fromstring(xml)
    asset = kok.find("asset")
    for ad in ("iha", "ika"):
        govde = kok.find(f"worldbody/body[@name='{ad}']")
        for geom in list(govde.findall("geom")):
            if geom.get("name", "").startswith("cad_g_"):
                govde.remove(geom)
        for mesh in list(asset.findall("mesh")):
            if mesh.get("name", "").startswith("cad_" + ad + "_"):
                asset.remove(mesh)
        for parca in manifest[ad]["parcalar"]:
            ET.SubElement(asset, "mesh", name="cad_" + parca["ad"], file=(KOK / parca["hedef"]).as_posix())
            ET.SubElement(govde, "geom", name="cad_g_" + parca["ad"], type="mesh", mesh="cad_" + parca["ad"],
                          rgba=cad_modeller.RENKLER[ad], mass="0", contype="0", conaffinity="0", group="1")
    return ET.tostring(kok, encoding="unicode")


def rotasyon(eksen, aci):
    quaternion = np.empty(4)
    mujoco.mju_axisAngle2Quat(quaternion, np.asarray(eksen), float(aci))
    matris = np.empty(9)
    mujoco.mju_quat2Mat(matris, quaternion)
    return matris.reshape(3, 3), quaternion


def iha_acilari(zaman, profil=None):
    if profil is None:
        sapma = math.radians(YUZ_GOSTERIM_DERECE) * math.sin(2 * math.pi * zaman / 3.5)
        elevator, rudder, aileron = sapma, sapma, sapma
        pervane_zaman = zaman
    else:
        konum, yaw, pitch, roll, faz = profil.durum(zaman)
        aileron = float(np.clip(-roll * .55, -.38, .38))
        elevator = float(np.clip(-pitch * .7, -.38, .38))
        rudder = float(np.clip(roll * .25, -.2, .2))
        pervane_zaman = min(zaman, profil.t_parasut)
    return {"sag_aileron": aileron, "sol_aileron": aileron, "elevator": elevator, "rudder": rudder,
            "pervane1": 2 * math.pi * PERVANE_GOSTERIM_HZ * pervane_zaman,
            "pervane2": -2 * math.pi * PERVANE_GOSTERIM_HZ * pervane_zaman}


class Hareket:
    def __init__(self, model, manifest):
        self.model = model
        self.baglar = []
        for ad in ("iha", "ika"):
            for parca in manifest[ad]["parcalar"]:
                eklem = parca.get("eklem")
                geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "cad_g_" + parca["ad"])
                if eklem is None or geom < 0:
                    continue
                model.geom_sameframe[geom] = mujoco.mjtSameFrame.mjSAMEFRAME_NONE
                fizik = eklem["fizik_eklemi"]
                joint = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, fizik) if fizik else -1
                qpos = int(model.jnt_qposadr[joint]) if joint >= 0 else None
                self.baglar.append({**eklem, "arac": ad, "geom": geom, "qpos": qpos,
                                    "poz0": model.geom_pos[geom].copy(), "quat0": model.geom_quat[geom].copy()})

    def uygula(self, durum, zaman, profil=None, studyo=False):
        acilar = iha_acilari(zaman, profil)
        sonuc = {}
        for bag in self.baglar:
            if bag["arac"] == "ika":
                if studyo:
                    aci = zaman * 2 * math.pi * .45
                elif bag["qpos"] is None:
                    raise ValueError("İKA teker açısı için fizik kaydı eksik")
                else:
                    aci = float(durum.qpos[bag["qpos"]])
                aci *= np.sign(bag["eksen"][1])
            else:
                aci = acilar[bag["ad"]]
            donus, quaternion = rotasyon(bag["eksen"], aci)
            pivot = np.asarray(bag["pivot"])
            self.model.geom_pos[bag["geom"]] = pivot + donus @ (bag["poz0"] - pivot)
            mujoco.mju_mulQuat(self.model.geom_quat[bag["geom"]], quaternion, bag["quat0"])
            sonuc[bag["ad"]] = aci
        mujoco.mj_forward(self.model, durum)
        return sonuc

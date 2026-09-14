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
TEKER_GOVDESI = {"sol_on_teker": "teker_on_sol", "sol_arka_teker": "teker_arka_sol",
                 "sag_on_teker": "teker_on_sag", "sag_arka_teker": "teker_arka_sag"}
# TEMSİLİ tahrik zinciri: IKA_GAZEBO_MODEL CAD paketinde motor / mil / braket parçası YOK.
# Ölçüler İKA gövde çerçevesinde (orijin = aks yüksekliği, +x ileri, +y sol). CAD STL'den
# ışınla ölçüldü (14 Eyl): yan ray alt yüzü z = 0,067 (x = ±0,18; y = 0,13 ve 0,145),
# jant göbek diski teker merkezine göre eksen boyunca +0,026…+0,036 m (r ≤ 12 mm).
MONTAJ = {"govde_alt_z": 0.067, "sac_m": 0.006, "braket_yari_x": 0.020, "flans_ic_y": 0.120,
          "bacak_alt_z": -0.030, "motor_r": 0.017, "motor_ic_y": 0.100, "reduktor_r": 0.019,
          "reduktor_boy": 0.035, "mil_r": 0.004, "mil_gomme": 0.005, "gobek_yuz": 0.026,
          "gobek_orta": 0.031, "kavrama_r": 0.010, "kavrama_boy": 0.014}
MONTAJ_GRUBU = "2"
MONTAJ_MALZEME = {"montaj_braket": "0.21 0.22 0.24 1", "montaj_motor": "0.055 0.06 0.065 1",
                  "montaj_mil": "0.33 0.34 0.36 1", "montaj_lastik": "0.075 0.08 0.09 1",
                  "montaj_jant": cad_modeller.RENKLER["ika"]}


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


def _teker_merkezi(manifest, teker):
    lastik = next(parca for parca in manifest["ika"]["parcalar"]
                  if parca["ad"] == f"ika_{teker}_0" and parca.get("malzeme") == "lastik")
    return np.mean(np.asarray(lastik["zarf_m"]), axis=0)


def montaj_parcalari(manifest, iz_m):
    """İKA gövde çerçevesinde temsili braket / motor / redüktör; teker gövdesinde mil / kavrama."""
    base = next(parca for parca in manifest["ika"]["parcalar"] if parca["ad"] == "ika_base_link_0")
    duvar = float(base["zarf_m"][1][1])
    olcu = MONTAJ
    sac, alt_z, yari_y = olcu["sac_m"], olcu["govde_alt_z"], iz_m / 2
    parcalar = []
    for teker, govde in TEKER_GOVDESI.items():
        isaret = 1.0 if teker.startswith("sol") else -1.0
        teker_x = None
        for ad, x_isaret in (("on", 1.0), ("arka", -1.0)):
            if f"_{ad}_" in teker:
                teker_x = x_isaret
        parcalar.append({"teker": teker, "govde": govde, "isaret": isaret, "x_isaret": teker_x})
    sonuc = []
    for kayit in parcalar:
        s = kayit["isaret"]
        teker, govde = kayit["teker"], kayit["govde"]

        def aralik(ic, dis):
            return s * (ic + dis) / 2, (dis - ic) / 2

        flans_y, flans_yari = aralik(olcu["flans_ic_y"], duvar + sac)
        bacak_y, bacak_yari = aralik(duvar, duvar + sac)
        motor_y, motor_yari = aralik(olcu["motor_ic_y"], duvar)
        red_y, red_yari = aralik(duvar + sac, duvar + sac + olcu["reduktor_boy"])
        mil_ic = duvar + sac + olcu["reduktor_boy"] - olcu["mil_gomme"] - yari_y
        mil_y, mil_yari = aralik(mil_ic, olcu["gobek_orta"])
        kav_y, kav_yari = aralik(olcu["gobek_yuz"] - olcu["kavrama_boy"], olcu["gobek_yuz"])
        bx = olcu["braket_yari_x"]
        sonuc += [
            {"ad": f"montaj_flans_{teker}", "govde": "ika", "teker": teker, "tip": "box", "malzeme": "montaj_braket",
             "pos": ("X", flans_y, alt_z - sac / 2), "size": (bx, flans_yari, sac / 2)},
            {"ad": f"montaj_bacak_{teker}", "govde": "ika", "teker": teker, "tip": "box", "malzeme": "montaj_braket",
             "pos": ("X", bacak_y, (alt_z + olcu["bacak_alt_z"]) / 2),
             "size": (bx, bacak_yari, (alt_z - olcu["bacak_alt_z"]) / 2)},
            {"ad": f"montaj_motor_{teker}", "govde": "ika", "teker": teker, "tip": "cylinder", "malzeme": "montaj_motor",
             "pos": ("X", motor_y, 0.0), "size": (olcu["motor_r"], motor_yari)},
            {"ad": f"montaj_reduktor_{teker}", "govde": "ika", "teker": teker, "tip": "cylinder", "malzeme": "montaj_braket",
             "pos": ("X", red_y, 0.0), "size": (olcu["reduktor_r"], red_yari)},
            {"ad": f"montaj_mil_{teker}", "govde": govde, "teker": teker, "tip": "cylinder", "malzeme": "montaj_mil",
             "pos": (0.0, mil_y, 0.0), "size": (olcu["mil_r"], mil_yari)},
            {"ad": f"montaj_kavrama_{teker}", "govde": govde, "teker": teker, "tip": "cylinder", "malzeme": "montaj_motor",
             "pos": (0.0, kav_y, 0.0), "size": (olcu["kavrama_r"], kav_yari)},
        ]
    return sonuc


def montaj_uygula(xml, manifest):
    """İKA CAD montajını fizik gövde ağacına bağlar (yalnız GÖRSEL; kütle 0, çarpışma yok).

    Lastik + jant STL'leri fizik teker gövdelerine taşınır: teker merkezi = fizik eklemi,
    dönüş = kayıtlı eklem açısı (MuJoCo kinematiği; elle geom döndürme yok). Gövde çerçevesine
    temsili L-braket, motor, redüktör; teker gövdesine mil ve göbek kavraması eklenir."""
    kok = ET.fromstring(xml)
    asset = kok.find("asset")
    dunya = kok.find("worldbody")
    ika = dunya.find("body[@name='ika']")
    govdeler = {govde.get("name"): govde for govde in ika.iter("body")}
    for govde in govdeler.values():
        for geom in list(govde.findall("geom")):
            if geom.get("name", "").startswith(("cad_g_ika_", "montaj_")):
                govde.remove(geom)
            else:
                geom.set("rgba", "0 0 0 0")
                geom.set("group", "5")
    mevcut = {oge.get("name") for oge in asset}
    for ad, renk in MONTAJ_MALZEME.items():
        if ad not in mevcut:
            ET.SubElement(asset, "material", name=ad, rgba=renk, specular="0.28", shininess="0.45")
    for parca in manifest["ika"]["parcalar"]:
        mesh_ad = "cad_" + parca["ad"]
        if mesh_ad not in mevcut:
            ET.SubElement(asset, "mesh", name=mesh_ad, file=(KOK / parca["hedef"]).as_posix())
            mevcut.add(mesh_ad)
        eklem = parca.get("eklem")
        if eklem is None:
            ET.SubElement(ika, "geom", name="cad_g_" + parca["ad"], type="mesh", mesh=mesh_ad,
                          rgba=cad_modeller.RENKLER["ika"], mass="0", contype="0", conaffinity="0", group="1")
            continue
        merkez = _teker_merkezi(manifest, eklem["ad"])
        ET.SubElement(govdeler[TEKER_GOVDESI[eklem["ad"]]], "geom", name="montaj_g_" + parca["ad"], type="mesh",
                      mesh=mesh_ad, pos=" ".join(f"{-v:.6f}" for v in merkez),
                      material="montaj_lastik" if parca["malzeme"] == "lastik" else "montaj_jant",
                      mass="0", contype="0", conaffinity="0", group="1")
    for parca in montaj_parcalari(manifest, float(_iz_m(ika))):
        govde = govdeler["ika" if parca["govde"] == "ika" else parca["govde"]]
        x = parca["pos"][0]
        if x == "X":
            x = float(govdeler[TEKER_GOVDESI[parca["teker"]]].get("pos").split()[0])
        oznitelik = {"name": parca["ad"], "type": parca["tip"], "material": parca["malzeme"],
                     "pos": f"{x:.6f} {parca['pos'][1]:.6f} {parca['pos'][2]:.6f}",
                     "size": " ".join(f"{v:.6f}" for v in parca["size"]),
                     "mass": "0", "contype": "0", "conaffinity": "0", "group": MONTAJ_GRUBU}
        if parca["tip"] == "cylinder":
            oznitelik["euler"] = "90 0 0"
        ET.SubElement(govde, "geom", **oznitelik)
    return ET.tostring(kok, encoding="unicode")


def _iz_m(ika):
    ylar = [abs(float(govde.get("pos").split()[1])) for govde in ika.findall("body")
            if govde.get("name", "").startswith("teker_")]
    if len(ylar) != 4 or max(ylar) - min(ylar) > 1e-9:
        raise ValueError("Fizik teker gövdeleri simetrik değil")
    return 2 * ylar[0]


def montaj_olcumu(model, durum, manifest):
    """Derlenmiş modelde montaj kanıtı: teker merkezi ↔ fizik eklemi ve zincir boşlukları (m)."""
    mujoco.mj_forward(model, durum)
    ika = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ika")
    govde_R, govde_p = durum.xmat[ika].reshape(3, 3), durum.xpos[ika]

    def yerel(nokta):
        return govde_R.T @ (np.asarray(nokta) - govde_p)

    def dunya(nokta):
        return govde_p + govde_R @ np.asarray(nokta)

    def geom(ad):
        kimlik = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, ad)
        if kimlik < 0:
            raise ValueError(f"Montaj geom'u yok: {ad}")
        return kimlik

    def kutu(ad):
        kimlik = geom(ad)
        merkez = yerel(durum.geom_xpos[kimlik])
        R = govde_R.T @ durum.geom_xmat[kimlik].reshape(3, 3)
        boyut = model.geom_size[kimlik]
        yari = np.abs(R) @ (boyut if model.geom_type[kimlik] == mujoco.mjtGeom.mjGEOM_BOX
                            else np.array([boyut[0], boyut[0], boyut[1]]))
        return merkez - yari, merkez + yari

    def ayrilik(a, b):
        (a0, a1), (b0, b1) = kutu(a), kutu(b)
        return float(np.max(np.maximum(b0 - a1, a0 - b1)))

    grup = np.zeros(6, dtype=np.uint8)
    grup[1] = 1
    kayitlar = {}
    for teker, govde_ad in TEKER_GOVDESI.items():
        s = 1.0 if teker.startswith("sol") else -1.0
        govde = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, govde_ad)
        eklem = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, TEKER_ESLEME[teker])
        lastik = geom("montaj_g_ika_" + teker + "_0")
        adres, sayi = model.mesh_vertadr[model.geom_dataid[lastik]], model.mesh_vertnum[model.geom_dataid[lastik]]
        koseler = durum.geom_xpos[lastik] + model.mesh_vert[adres:adres + sayi] @ durum.geom_xmat[lastik].reshape(3, 3).T
        merkez = yerel((koseler.min(axis=0) + koseler.max(axis=0)) / 2)
        anchor = yerel(durum.xanchor[eklem])
        flans0, flans1 = kutu(f"montaj_flans_{teker}")
        alt_bosluk = []
        base = geom("cad_g_ika_base_link_0")
        for x in np.linspace(flans0[0] + 1e-3, flans1[0] - 1e-3, 5):
            for y in np.linspace(min(abs(flans0[1]), abs(flans1[1])) + 1e-3,
                                 max(abs(flans0[1]), abs(flans1[1])) - 1e-3, 9):
                geomid = np.array([-1], dtype=np.int32)
                mesafe = mujoco.mj_ray(model, durum, dunya([x, s * y, -0.3]), govde_R[:, 2], grup, 0, govde, geomid)
                if mesafe >= 0 and geomid[0] == base:
                    alt_bosluk.append(float(-0.3 + mesafe - flans1[2]))
        red0, red1 = kutu(f"montaj_reduktor_{teker}")
        mil0, mil1 = kutu(f"montaj_mil_{teker}")
        kav0, kav1 = kutu(f"montaj_kavrama_{teker}")
        eksen_bas = [anchor[0], s * (abs(red1[1]) if s > 0 else abs(red0[1])), anchor[2]]
        geomid = np.array([-1], dtype=np.int32)
        mesafe = mujoco.mj_ray(model, durum, dunya(eksen_bas), govde_R[:, 1] * s, grup, 0, ika, geomid)
        jant = geom("montaj_g_ika_" + teker + "_0_jant")
        gobek_y = abs(eksen_bas[1]) + mesafe if mesafe >= 0 and geomid[0] == jant else None
        mil_uc = max(abs(mil0[1]), abs(mil1[1]))
        kav_uc = max(abs(kav0[1]), abs(kav1[1]))
        baglar = {
            "govde_alti__flans": min(alt_bosluk) if alt_bosluk else None,
            "flans__bacak": ayrilik(f"montaj_flans_{teker}", f"montaj_bacak_{teker}"),
            "bacak__motor": ayrilik(f"montaj_bacak_{teker}", f"montaj_motor_{teker}"),
            "bacak__reduktor": ayrilik(f"montaj_bacak_{teker}", f"montaj_reduktor_{teker}"),
            "reduktor__mil": ayrilik(f"montaj_reduktor_{teker}", f"montaj_mil_{teker}"),
            "mil__jant_gobegi": None if gobek_y is None else float(gobek_y - mil_uc),
            "kavrama__jant_gobegi": None if gobek_y is None else float(gobek_y - kav_uc),
        }
        kayitlar[teker] = {
            "teker_merkezi_govde_m": merkez.round(5).tolist(), "fizik_eklemi_govde_m": anchor.round(5).tolist(),
            "merkez_eklem_farki_mm": float(np.linalg.norm(merkez - anchor) * 1000),
            "baglar_bosluk_m": baglar,
            "govde_alti_isin_n": len(alt_bosluk),
            "govde_alti_bosluk_maks_m": max(alt_bosluk) if alt_bosluk else None,
            "zincir_maks_bosluk_mm": (None if any(v is None for v in baglar.values())
                                     else float(max(0.0, *baglar.values()) * 1000)),
        }
    return kayitlar


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

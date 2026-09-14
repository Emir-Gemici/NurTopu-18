"""NEDEN: Gerçek CAD ayrıntıları yakın kameralarla, simülasyon durumları değiştirilmeden gösterilir."""

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time
import xml.etree.ElementTree as ET

import cv2
import mujoco
import numpy as np


KOK = Path(__file__).resolve().parents[1]
for dizin in (KOK / "simulation/mujoco", KOK / "simulation/scripts", KOK / "codes", KOK / "comms"):
    sys.path.insert(0, str(dizin))

import arena_mjcf
import cad_modeller
import gorev_kosumu
import iha_ucus
import sim_video


CIKTI = KOK / "results/fdr_33_20260914/cad_video_sinematik"
BOYUT = (1920, 1080)
FPS = 25
VIDEO_ADI = "navitas_cad_sinematik_1080p.mp4"
EKLEMLI = False
KAYIT_KOK = None
MAGENTA = (225, 30, 240)
MAVI = (226, 181, 0)
ACIK = (238, 238, 241)


def sha(yol):
    ozet = hashlib.sha256()
    with Path(yol).open("rb") as dosya:
        for parca in iter(lambda: dosya.read(1024 * 1024), b""):
            ozet.update(parca)
    return ozet.hexdigest()


def yaz(ad, veri):
    (CIKTI / ad).write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")


class DurumKaydedici(gorev_kosumu._KareKaydedici):
    def _cizici(self, model):
        kimlikler = tuple(int(model.body_mocapid[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, ad)])
                         for ad in ("iha", "parasut"))
        return model, None, kimlikler

    def kare(self, model, durum, t_gorev, olay):
        if olay.get("no_route") and olay.get("landed"):
            if self.son_bosta_kare is not None and t_gorev - self.son_bosta_kare < 2 - 1e-8:
                return
            self.son_bosta_kare = t_gorev
        satir = {"n": self.n, "t": float(t_gorev), **olay,
                 "qpos": durum.qpos.tolist(), "qvel": durum.qvel.tolist(),
                 "mocap_pos": durum.mocap_pos.tolist(), "mocap_quat": durum.mocap_quat.tolist()}
        self._durum.write(json.dumps(satir, ensure_ascii=False) + "\n")
        self.n += 1

    def kapat(self):
        self._durum.close()


def kayit_al():
    kosum_koku = CIKTI / "kosum"
    if kosum_koku.exists():
        raise FileExistsError("Mevcut koşu korunur; --out ile yeni çıktı klasörü seçin")
    model, kunye = gorev_kosumu.model_yukle()
    ozet = []
    for kaynak in ("model", "gt"):
        print("DURUM_KAYDI_BASLADI", kaynak, flush=True)
        sonuc = gorev_kosumu.kos(5, "zor", 42, kaynak, res=1280, out=kosum_koku,
                                 model=model if kaynak == "model" else None,
                                 model_kunye=kunye if kaynak == "model" else None,
                                 kare_kaydet=True, cad_modeller=True, video_bosta_aralik_s=2.0,
                                 video_kaydedici=DurumKaydedici)
        ozet.append({"ad": kaynak + "_5_zor_42", "basari": sonuc["basari"], "cikis_kodu": sonuc["cikis_kodu"]})
        yaz("kosum_ozeti.json", ozet)
        print("DURUM_KAYDI_BITTI", json.dumps(ozet[-1]), flush=True)


def gorsel_xml(xml, eklemli=False):
    kok = ET.fromstring(xml)
    kok.find("compiler").set("meshdir", arena_mjcf.MESH_DIR.as_posix())
    kok.find("compiler").set("texturedir", arena_mjcf.DOKU_DIR.as_posix())
    visual = kok.find("visual")
    visual.find("global").set("offwidth", "1920")
    visual.find("global").set("offheight", "1080")
    visual.find("quality").set("shadowsize", "4096")
    visual.find("quality").set("offsamples", "4")
    visual.find("headlight").set("ambient", "0.32 0.32 0.34")
    visual.find("headlight").set("diffuse", "0.45 0.45 0.45")
    visual.find("headlight").set("specular", "0.1 0.1 0.1")
    for light in kok.findall("worldbody/light"):
        light.set("dir", "-0.4 -0.5 -1")
        light.set("diffuse", "0.65 0.62 0.60")
        light.set("specular", "0.18 0.18 0.18")
    asset = kok.find("asset")
    for ad, renk in cad_modeller.RENKLER.items():
        ET.SubElement(asset, "material", name="sunum_" + ad, rgba=renk,
                      specular="0.28", shininess="0.45", reflectance="0")
    ET.SubElement(asset, "material", name="sunum_lastik", rgba="0.075 0.08 0.09 1", specular="0.1", shininess="0.1")
    if eklemli:
        ET.SubElement(asset, "material", name="sunum_yuzey", rgba="1 0.18 0.72 1", specular="0.28")
    for geom in kok.iter("geom"):
        ad = geom.get("name", "")
        if ad.startswith("cad_g_"):
            arac = ad.removeprefix("cad_g_").split("_")[0]
            geom.set("material", "sunum_" + arac)
            if ad.startswith("cad_g_iha_") and "pervane" in ad.lower():
                geom.set("material", "sunum_lastik")
                geom.set("rgba", "0.075 0.08 0.09 1")
            if eklemli and ad.startswith("cad_g_ika_") and "teker" in ad and not ad.endswith("_jant"):
                geom.set("material", "sunum_lastik")
                geom.set("rgba", "0.075 0.08 0.09 1")
            if eklemli and ad.startswith("cad_g_iha_") and any(kisim in ad for kisim in ("aileron", "elevator", "rudder")):
                geom.set("material", "sunum_yuzey")
                geom.set("rgba", "1 0.18 0.72 1")
    return ET.tostring(kok, encoding="unicode")


def kamera_kur(hedef, azimut, mesafe, yukselis=-18):
    kamera = mujoco.MjvCamera()
    kamera.type = mujoco.mjtCamera.mjCAMERA_FREE
    kamera.lookat[:] = hedef
    kamera.azimuth = azimut
    kamera.elevation = yukselis
    kamera.distance = mesafe
    return kamera


def durum_uygula(model, durum, satir):
    if len(satir["qpos"]) != model.nq:
        raise ValueError("Kaydedilmiş fizik durumu model boyutuyla eşleşmiyor")
    durum.qpos[:] = satir["qpos"]
    durum.qvel[:] = satir["qvel"]
    durum.mocap_pos[:] = satir["mocap_pos"]
    durum.mocap_quat[:] = satir["mocap_quat"]
    durum.time = satir["t"]
    mujoco.mj_forward(model, durum)


def yazi(goruntu, metin, konum, boy=0.8, renk=ACIK, kalin=1):
    sim_video._yaz(goruntu, metin, konum, boy, renk, kalin)


def kaplama(goruntu, dikdortgen, alpha=0.84):
    bas_x, bas_y, son_x, son_y = dikdortgen
    alan = goruntu[bas_y:son_y, bas_x:son_x]
    alan[:] = cv2.addWeighted(alan, 1 - alpha, np.full_like(alan, (19, 22, 29)), alpha, 0)


def hud(goruntu, baslik, alt, *, kaynak="CAD INCELEME", satir=None, hiz=1.0, detaylar=None, renk=MAGENTA):
    kaplama(goruntu, (0, 0, 1920, 118))
    cv2.rectangle(goruntu, (32, 26), (40, 92), renk, -1)
    yazi(goruntu, "NAVITAS / " + baslik, (62, 56), 1.0, ACIK, 2)
    yazi(goruntu, alt, (64, 94), 0.63, (201, 205, 215))
    kaplama(goruntu, (0, 915, 1920, 1080))
    yazi(goruntu, "SIMULASYON | CAD GORSELLESTIRME", (40, 954), 0.75, (135, 194, 244), 2)
    yazi(goruntu, "KAYNAK: " + kaynak, (40, 995), 0.70, renk, 2)
    if satir:
        yazi(goruntu, f"SIM t={satir['t']:.2f} s  /  GOSTERIM {hiz:.2f}x", (1110, 954), 0.78)
        durumlar = [("ROTA", satir.get("rota_alindi")), ("INIS", satir.get("landed")),
                    ("SURUS IZNI", satir.get("ika_go")), ("KOMUT ACK", satir.get("ika_go_ack"))]
        for indis, (ad, gecerli) in enumerate(durumlar):
            yazi(goruntu, ad + (": EVET" if gecerli else ": --"), (1070 + (indis % 2) * 395, 994 + (indis // 2) * 35),
                 0.63, (143, 223, 149) if gecerli else (173, 175, 184))
    yazi(goruntu, "Ucus kinematik; CAD gorunumu / basitlestirilmis IKA fizigi. Gercek saha kaydi degildir.",
          (40, 1041), 0.55, (182, 184, 197))
    if detaylar:
        kaplama(goruntu, (1450, 152, 1882, 152 + len(detaylar) * 40 + 36))
        for indis, metin in enumerate(detaylar):
            yazi(goruntu, metin, (1472, 191 + indis * 40), 0.59, ACIK if indis else renk, 2 if not indis else 1)
    return goruntu


class Sunum:
    def __init__(self):
        self.manifest = cad_modeller.hazirla()
        xml = arena_mjcf.uret(5, "zor", 42, cad_modeller=True)
        self.kayit_kok = KAYIT_KOK or CIKTI
        if EKLEMLI:
            import cad_hareket
            self.manifest = cad_hareket.hazirla()
            xml = cad_hareket.uygula(xml, self.manifest)
        self.model = mujoco.MjModel.from_xml_string(gorsel_xml(xml, EKLEMLI))
        self.hareket = cad_hareket.Hareket(self.model, self.manifest) if EKLEMLI else None
        self.durum = mujoco.MjData(self.model)
        self.renderer = mujoco.Renderer(self.model, height=1080, width=1920)
        self.model.vis.global_.fovy = 38
        self.profil = iha_ucus.UcusProfili()
        self.iha = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "iha")
        self.ika = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "ika")
        self.kayitlar = {}
        self.sonuclar = {}
        for kaynak in ("model", "gt"):
            ad = kaynak + "_5_zor_42"
            yol = self.kayit_kok / "kosum" / ad / "kareler_video/durum.jsonl"
            self.kayitlar[kaynak] = [json.loads(satir) for satir in yol.read_text(encoding="utf-8").splitlines()]
            self.sonuclar[kaynak] = json.loads((self.kayit_kok / "kosum" / (ad + ".json")).read_text(encoding="utf-8"))
        self.zamanlar = {ad: np.array([satir["t"] for satir in satirlar]) for ad, satirlar in self.kayitlar.items()}
        self.kamera_zaman = np.arange(0, self.profil.t_inis + .04, .04)
        ham_yaw = np.unwrap([self.profil.durum(zaman)[1] for zaman in self.kamera_zaman])
        self.kamera_yaw = np.convolve(np.pad(ham_yaw, (8, 8), mode="edge"), np.ones(17) / 17, mode="valid")
        self.rota = gorev_kosumu.gt_rota(5, "zor")
        self.harita = gorev_kosumu.arena.harita(5, "zor")
        scan = self.kayit_kok / "kosum/model_5_zor_42/iha_scan"
        self.scan = scan
        self.pozlar = np.loadtxt(scan / "poses.csv", delimiter=",")
        self.kamera_girdi = {}
        self.studyo_modeller = {}

    def satir(self, kaynak, zaman):
        indis = int(np.searchsorted(self.zamanlar[kaynak], zaman, side="right")) - 1
        return self.kayitlar[kaynak][max(0, min(indis, len(self.kayitlar[kaynak]) - 1))]

    def ciz(self, kamera):
        if self.hareket:
            self.hareket.uygula(self.durum, self.durum.time, self.profil)
        self.renderer.update_scene(self.durum, camera=kamera)
        return cv2.cvtColor(self.renderer.render(), cv2.COLOR_RGB2BGR)

    def ucus(self, zaman):
        satir = self.satir("model", zaman)
        durum_uygula(self.model, self.durum, satir)
        hedef = self.durum.xpos[self.iha].copy()
        azimut = math.degrees(float(np.interp(zaman, self.kamera_zaman, self.kamera_yaw))) + 135
        kamera = kamera_kur(hedef, azimut, 3.9, -22)
        if zaman > self.profil.t_parasut:
            hedef[2] += 1.35
            kamera = kamera_kur(hedef, 125, 8.2, -13)
        goruntu = self.ciz(kamera)
        faz = self.profil.durum(zaman)[-1]
        detaylar = ["SABIT KANAT / MAGENTA", "GitHub URDF + 8 STL parca", "Kanat acikligi: 2.050 m", "Boy: 1.516 m (CAD)",
                   f"Kinematik irtifa: {self.durum.xpos[self.iha][2]:.2f} m", "Faz: " + sim_video.ascii_katla(faz),
                   "Yakindan takip kamerasi"]
        hud(goruntu, "SABIT KANAT / YAKIN TAKIP", "Magenta govde ve kanat CAD ayrintilari | 0.75x yavas gosterim",
                   kaynak="KAYITLI MODEL KOSUSU / GORSEL TEKRAR" if EKLEMLI else "MODEL-MOZAIK / YENI DURUM KAYDI",
                   satir=satir, hiz=0.75, detaylar=detaylar)
        if EKLEMLI:
            kaplama(goruntu, (42, 142, 1350, 210))
            yazi(goruntu, "Pervane + servo hareketi TEMSILI | Olculmus RPM / servo telemetrisi degildir", (62, 184), .66)
        indisler = np.where(self.pozlar[:, 1] <= satir["t"])[0]
        if len(indisler):
            poz = self.pozlar[indisler[-1]]
            kare_no = int(poz[0])
            if kare_no not in self.kamera_girdi:
                self.kamera_girdi[kare_no] = cv2.imread(str(self.scan / "kareler" / f"scan_{kare_no:05d}.jpg"))
            girdi = self.kamera_girdi[kare_no]
            if girdi is not None:
                goruntu[546:884, 1466:1870] = sim_video._sigdir(girdi, 404, 338)
                kaplama(goruntu, (1450, 493, 1882, 548))
                yazi(goruntu, f"HAM NADIR / 1 Hz / t={poz[1]:.1f}s", (1468, 527), .56)
        return goruntu

    def surus(self, zaman):
        satir = self.satir("gt", zaman)
        durum_uygula(self.model, self.durum, satir)
        hedef = self.durum.xpos[self.ika].copy()
        hedef[2] += 0.08
        matris = self.durum.xmat[self.ika].reshape(3, 3)
        yaw = math.degrees(math.atan2(matris[1, 0], matris[0, 0]))
        kamera = kamera_kur(hedef, yaw + 145, 1.72, -20)
        goruntu = self.ciz(kamera)
        detaylar = ["IKA / TURAN MAVISI", "Ozgun CAD / ayristirilmis STL" if EKLEMLI else "GitHub URDF + 6 STL parca", f"X: {satir['ika_xy'][0]:.2f} m (yerel)",
                   f"Y: {satir['ika_xy'][1]:.2f} m (yerel)", f"HB uzakligi: {satir['hb_m']:.2f} m",
                   f"Temas sayisi: {satir['temas']}", "GT = goruntu isleme YOK"]
        hud(goruntu, "IKA / CAD YAKIN TAKIP", "Ayni kaydedilmis qpos / qvel | kamera ve isik sunum icin yenilendi",
                   kaynak="YER GERCEGI (GT) / TANISAL SURUS", satir=satir, detaylar=detaylar, renk=MAVI)
        self.rota_paneli(goruntu, satir)
        if EKLEMLI:
            kaplama(goruntu, (42, 142, 1370, 210))
            yazi(goruntu, "4 teker + jant: kayitli MuJoCo eklem acilari | GT surusu, model basarisi DEGIL", (62, 184), .64)
        return goruntu

    def rota_paneli(self, goruntu, satir):
        kaplama(goruntu, (1450, 493, 1882, 901))
        yazi(goruntu, "GT ROTA / YEREL METRE", (1470, 522), .62, MAVI, 2)
        merkez = np.array([1666, 710])

        def piksel(nokta):
            return tuple(np.rint(merkez + np.array(nokta) * [6.1, -6.1]).astype(int))

        for yol, noktalar in self.harita["paths"].items():
            dizi = np.array([piksel(nokta) for nokta in noktalar], dtype=np.int32)
            cv2.polylines(goruntu, [dizi], False, (78, 86, 101), 3, cv2.LINE_AA)
        referans = np.array(self.rota[2])
        noktalar = np.array(self.rota[3]) + referans
        dizi = np.array([piksel(nokta) for nokta in noktalar], dtype=np.int32)
        cv2.polylines(goruntu, [dizi], False, (151, 203, 127), 2, cv2.LINE_AA)
        for nokta in dizi:
            cv2.circle(goruntu, tuple(nokta), 2, (151, 203, 127), -1)
        cv2.circle(goruntu, piksel(satir["ika_xy"]), 7, MAVI, -1, cv2.LINE_AA)
        cv2.circle(goruntu, piksel(self.harita["hb"]), 6, (65, 65, 237), 2)
        yazi(goruntu, "KB", piksel(self.harita["kb"]), .43)
        yazi(goruntu, "HB", piksel(self.harita["hb"]), .43)
        yazi(goruntu, "Yesil: GT girdi / mavi: kayitli konum", (1468, 878), .47)

    def studyo_hazirla(self, ad):
        kok = ET.Element("mujoco", model="cad_detay_" + ad)
        ET.SubElement(kok, "compiler", angle="degree")
        visual = ET.SubElement(kok, "visual")
        ET.SubElement(visual, "global", offwidth="1920", offheight="1080", fovy="38")
        ET.SubElement(visual, "quality", shadowsize="4096", offsamples="4")
        ET.SubElement(visual, "headlight", ambient="0.30 0.30 0.32", diffuse="0.4 0.4 0.4", specular="0.2 0.2 0.2")
        asset = ET.SubElement(kok, "asset")
        ET.SubElement(asset, "texture", name="studyo_zemin", type="2d", builtin="checker", rgb1="0.17 0.19 0.23", rgb2="0.18 0.20 0.24", width="512", height="512")
        ET.SubElement(asset, "material", name="studyo_zemin", texture="studyo_zemin", texrepeat="16 16", reflectance="0.08")
        ET.SubElement(asset, "material", name="boya", rgba=cad_modeller.RENKLER[ad], specular="0.32", shininess="0.5")
        ET.SubElement(asset, "material", name="lastik", rgba="0.075 0.08 0.09 1", specular="0.08")
        ET.SubElement(asset, "material", name="yuzey", rgba="1 0.18 0.72 1", specular="0.25")
        dunya = ET.SubElement(kok, "worldbody")
        veri = self.manifest[ad]
        alt = min(parca["zarf_m"][0][2] for parca in veri["parcalar"])
        ET.SubElement(dunya, "geom", type="plane", size="200 200 .1", pos=f"0 0 {alt - .003}", material="studyo_zemin")
        ET.SubElement(dunya, "light", pos="-3 -4 6", dir="0.3 0.4 -1", diffuse="0.7 0.65 0.63", specular="0.3 0.3 0.3")
        ET.SubElement(dunya, "light", pos="3 4 3", dir="-0.4 -0.5 -1", diffuse="0.25 0.3 0.4", castshadow="false")
        for parca in veri["parcalar"]:
            ET.SubElement(asset, "mesh", name=parca["ad"], file=(KOK / parca["hedef"]).as_posix())
            malzeme = "lastik" if ad == "iha" and "pervane" in parca["ad"].lower() else "boya"
            if EKLEMLI and parca.get("malzeme") == "lastik":
                malzeme = "lastik"
            if EKLEMLI and parca.get("malzeme") == "kumanda_yuzeyi":
                malzeme = "yuzey"
            ET.SubElement(dunya, "geom", name="cad_g_" + parca["ad"], type="mesh", mesh=parca["ad"], material=malzeme, contype="0", conaffinity="0")
        model = mujoco.MjModel.from_xml_string(ET.tostring(kok, encoding="unicode"))
        durum = mujoco.MjData(model)
        mujoco.mj_forward(model, durum)
        renderer = mujoco.Renderer(model, height=1080, width=1920)
        self.studyo_modeller[ad] = model, durum, renderer, alt
        if EKLEMLI:
            import cad_hareket
            if not hasattr(self, "studyo_hareket"):
                self.studyo_hareket = {}
            self.studyo_hareket[ad] = cad_hareket.Hareket(model, self.manifest)

    def studyo(self, ad, oran):
        if ad not in self.studyo_modeller:
            self.studyo_hazirla(ad)
        model, durum, renderer, alt = self.studyo_modeller[ad]
        veri = self.manifest[ad]
        hedef = [0.35 if ad == "mancinik" else 0, 0, alt + veri["boyut_m"][2] / 2]
        mesafe = {"iha": 3.65, "ika": 1.1, "mancinik": 4.5}[ad]
        kamera = kamera_kur(hedef, 105 + oran * 150, mesafe, -22 - 8 * math.sin(oran * math.pi))
        acilar = {}
        yakin_detay = "MONTAJ"
        if EKLEMLI:
            acilar = self.studyo_hareket[ad].uygula(durum, oran * (14 if ad == "iha" else 10), studyo=True)
            if ad == "iha" and oran > .44:
                if oran < .64:
                    parca_ad, yakin_detay, mesafe = "pervane1", "PERVANE / URDF DONUS EKSENI", .85
                elif oran < .83:
                    parca_ad, yakin_detay, mesafe = "sol_aileron", "AILERON / MENTESE HAREKETI", .95
                else:
                    parca_ad, yakin_detay, mesafe = "elevator", "ELEVATOR + RUDDER", 1.05
                bag = next(bag for bag in self.studyo_hareket[ad].baglar if bag["ad"] == parca_ad)
                hedef = np.asarray(bag["pivot"]).copy()
                if parca_ad == "sol_aileron":
                    hedef[1] += .18
                kamera = kamera_kur(hedef, 30 if parca_ad == "pervane1" else 225, mesafe, -30)
            elif ad == "ika" and oran > .50:
                bag = next(bag for bag in self.studyo_hareket[ad].baglar if bag["ad"] == "sag_on_teker")
                kamera = kamera_kur(bag["pivot"], 275, .57, -12)
                yakin_detay = "LASTIK + JANT / EKLEM YAKIN PLAN"
        renderer.update_scene(durum, camera=kamera)
        goruntu = cv2.cvtColor(renderer.render(), cv2.COLOR_RGB2BGR)
        etiket = {"iha": "MAGENTA SABIT KANAT", "ika": "TURAN MAVISI IKA", "mancinik": "BEYAZ MANCINIK"}[ad]
        boyut = veri["boyut_m"]
        detaylar = ["OZGUN TAKIM CAD MONTAJI", f"STL parca sayisi: {len(veri['parcalar'])}",
                   f"X / boy: {boyut[0]:.4f} m", f"Y / genislik: {boyut[1]:.4f} m", f"Z / yukseklik: {boyut[2]:.4f} m",
                   "1:1 metre olcegi", "Boyutlar CAD hesabidir"]
        sonuc = hud(goruntu, etiket + " / 3D DETAY", cad_modeller.PAKETLER[ad] + " | " + yakin_detay,
                   detaylar=detaylar, renk=MAVI if ad == "ika" else MAGENTA if ad == "iha" else ACIK)
        if EKLEMLI and acilar:
            kaplama(sonuc, (42, 740, 1400, 903))
            yazi(sonuc, "TEZGAH GOSTERIMI / TEMSILI AKTUATOR HAREKETI / TELEMETRI DEGIL", (62, 780), .66)
            if ad == "iha":
                yazi(sonuc, "Pervane: 3.7 tur/s gorsel yavas donus; gercek motor RPM'si degil", (62, 822), .65)
                yazi(sonuc, f"Yuzey taramasi: +/-22 derece | Elevator: {math.degrees(acilar['elevator']):+.1f} derece", (62, 866), .67)
            else:
                yazi(sonuc, "Bu bolum: serbest teker gosterimi | Suruste: orijinal fizik qpos kaydi", (62, 826), .65)
                yazi(sonuc, "STL icindeki mukerrer govdeler ayrildi; lastik ve jant birlikte doner", (62, 869), .65)
        return sonuc

    def teshis(self):
        sonuc = self.sonuclar["model"]
        goruntu = np.full((1080, 1920, 3), (24, 27, 34), dtype=np.uint8)
        scan = self.kayit_kok / "kosum/model_5_zor_42/iha_scan"
        for ad, konum_x in (("ortomozaik.jpg", 35), ("algi.jpg", 775)):
            kaynak = cv2.imread(str(scan / ad))
            assert kaynak is not None
            goruntu[180:890, konum_x:konum_x + 710] = sim_video._sigdir(kaynak, 710, 710)
        yazi(goruntu, "KAYDEDILMIS ORTOMOZAIK", (60, 160), 0.65)
        yazi(goruntu, "MODEL CIKTISI / A* DENETIMI", (800, 160), 0.65)
        detaylar = ["MODEL SONUCU", str(sonuc.get("iha_gonderim", {}).get("tel_tipi")), f"Rota noktasi: {sonuc['wp_sayisi']}",
                   f"Basari: {sonuc['basari']}", f"Cikis: {sonuc['cikis_kodu']}", "Ret kaydi saklandi", "GT sonucu ayri gosterilir"]
        sonuc_goruntu = hud(goruntu, "GORUNTU ISLEME / DOGRULANAN SONUC", "Sunum isiklandirmasi model girdisine uygulanmadi; burada ozgun tarama/algilama kaydi gosterilir",
                   kaynak="MODEL-MOZAIK / BASARISIZLIK GIZLENMEZ", detaylar=detaylar)
        if EKLEMLI:
            kaplama(sonuc_goruntu, (42, 740, 1430, 903))
            ret = sonuc.get("iha_gonderim", {}).get("sebep", "BILINMIYOR")
            yazi(sonuc_goruntu, "YESIL: MODEL ZEMIN MASKESI | KIRMIZI: MODEL ENGEL MASKESI", (62, 782), .67)
            yazi(sonuc_goruntu, "Maske var; gecerli KB-HB rotasi YOK. Ret: " + ret, (62, 825), .67)
            yazi(sonuc_goruntu, "CAD hareket duzeltmesi algilama modelini egitmez; GT, model ciktisi yerine konmadi.", (62, 870), .61)
        return sonuc_goruntu

    def sonuc(self):
        goruntu = np.full((1080, 1920, 3), (24, 27, 34), dtype=np.uint8)
        for indis, kaynak in enumerate(("model", "gt")):
            sonuc = self.sonuclar[kaynak]
            konum_x = 85 + indis * 920
            renk = MAGENTA if kaynak == "model" else MAVI
            yazi(goruntu, "MODEL-MOZAIK" if kaynak == "model" else "YER GERCEGI / GT", (konum_x, 215), 1.15, renk, 2)
            metinler = ["Sonuc: " + ("BASARILI" if sonuc["basari"] else "BASARISIZ"),
                        f"Tel karari: {sonuc.get('iha_gonderim', {}).get('tel_tipi')}", f"Görev sim suresi: {sonuc['sure_sim_gorev']} s",
                        f"Temas sayisi: {sonuc['temas_sayisi']}", f"HB mesafesi: {sonuc['varis_mesafesi_m']} m",
                        f"Rota noktasi: {sonuc['wp_sayisi']}", "Goruntu basarisi degil; tanisal surus" if kaynak == "gt" else "Gecerli rota yoksa IKA surulmez"]
            for satir_no, metin in enumerate(metinler):
                yazi(goruntu, metin, (konum_x, 305 + satir_no * 70), 0.82)
        return hud(goruntu, "YENI CAD SUNUMU / GERCEK KOSUM SONUCLARI", "Kamera yakinlasti; test esikleri, mesajlar, fizik durumu ve basari tanimi degismedi",
                   kaynak="MUJOCO / MODEL VE GT AYRI")

    def kapat(self):
        self.renderer.close()
        for model, durum, renderer, alt in self.studyo_modeller.values():
            renderer.close()


def magenta_olc(goruntu):
    alan = goruntu[120:910, :1440]
    mavi, yesil, kirmizi = cv2.split(alan)
    maske = (kirmizi > 100) & (mavi > 80) & (yesil.astype(float) < kirmizi * 0.60) & (yesil.astype(float) < mavi * 0.65)
    satir, kolon = np.where(maske)
    return {"piksel": int(maske.sum()), "genislik_px": int(kolon.max() - kolon.min() + 1) if len(kolon) else 0,
            "boy_px": int(satir.max() - satir.min() + 1) if len(satir) else 0}


def onizleme():
    sunum = Sunum()
    try:
        olcumler = {}
        for ad, goruntu in (("iha_cad", sunum.studyo("iha", 0.2)), ("ika_cad", sunum.studyo("ika", 0.2)),
                            ("mancinik_cad", sunum.studyo("mancinik", 0.2)), ("iha_ucus", sunum.ucus(12)),
                            ("ika_surus", sunum.surus(65)), ("model_teshis", sunum.teshis())):
            cv2.imwrite(str(CIKTI / (ad + ".png")), goruntu)
            if ad.startswith("iha"):
                olcumler[ad] = magenta_olc(goruntu)
                assert olcumler[ad]["piksel"] > 15000, (ad, olcumler[ad])
                assert olcumler[ad]["genislik_px"] > 500, (ad, olcumler[ad])
        yaz("magenta_gorunurluk.json", olcumler)
        ornekler = [{"sim_s": zaman, **magenta_olc(sunum.ucus(zaman))} for zaman in range(37)]
        gecen = sum(ornek["piksel"] > 15000 and ornek["genislik_px"] > 500 for ornek in ornekler)
        yaz("magenta_ucus_ornekleri.json", {"ornekler": ornekler, "gecen": gecen, "n": len(ornekler)})
        assert gecen / len(ornekler) >= .8, (gecen, len(ornekler))
        if EKLEMLI:
            eklem_kaniti(sunum)
        print("ONIZLEME_OK", json.dumps(olcumler), flush=True)
    finally:
        sunum.kapat()


def eklem_kaniti(sunum):
    kayitlar = []
    for ad in ("iha", "ika"):
        sunum.studyo(ad, .2)
        model, durum, renderer, alt = sunum.studyo_modeller[ad]
        hareket = sunum.studyo_hareket[ad]
        hareket.uygula(durum, 0, studyo=True)
        once = durum.geom_xmat.copy()
        hareket.uygula(durum, .65, studyo=True)
        for bag in hareket.baglar:
            degisim = float(np.linalg.norm(durum.geom_xmat[bag["geom"]] - once[bag["geom"]]))
            assert degisim > .1, bag["ad"]
            kayitlar.append({"arac": ad, "eklem": bag["ad"], "geom": int(bag["geom"]),
                             "matris_farki": degisim, "pivot": bag["pivot"], "eksen": bag["eksen"]})
    for ad, oran in (("iha", .55), ("iha", .74), ("iha", .94), ("ika", .71)):
        cv2.imwrite(str(CIKTI / f"eklem_yakin_{ad}_{oran:.2f}.png"), sunum.studyo(ad, oran))
    yaz("eklem_kaniti.json", {"hareketli_mesh": len(kayitlar), "bagimsiz_eklem": len({kayit["eklem"] for kayit in kayitlar}),
                             "kayitlar": kayitlar, "gosterim_zamanlari_s": [0, .65],
                             "koken": "İHA/stüdyo açıları temsili; İKA sürüşünde fizik eklemi qpos kullanılır."})


def render():
    hedef = CIKTI / VIDEO_ADI
    ana = CIKTI / "sinematik_ana.mp4"
    if hedef.exists() or ana.exists():
        raise FileExistsError("Önceki video korunur; yeni çıktı klasörü seçin")
    sunum = Sunum()
    yazici = cv2.VideoWriter(str(ana), cv2.VideoWriter_fourcc(*"mp4v"), FPS, BOYUT)
    assert yazici.isOpened()
    bolumler, gorunurluk = [], []
    kare_n = 0
    baslangic = time.perf_counter()

    def bolum(ad, sure, fonksiyon, kaynak, sim_bas=None, hiz=None):
        nonlocal kare_n
        ilk = kare_n
        toplam = int(round(sure * FPS))
        print("RENDER_BOLUM", ad, toplam, flush=True)
        for indis in range(toplam):
            goruntu = fonksiyon(indis / FPS, indis / max(1, toplam - 1))
            if ad == "iha_yakin_ucus" and indis % FPS == 0:
                gorunurluk.append({"video_s": kare_n / FPS, **magenta_olc(goruntu)})
            yazici.write(goruntu)
            kare_n += 1
        bolumler.append({"ad": ad, "bas_s": ilk / FPS, "son_s": kare_n / FPS,
                        "kaynak": kaynak, "sim_bas": sim_bas, "hiz": hiz})
        yaz("render_ilerleme.json", {"kare": kare_n, "bolumler": bolumler})

    try:
        for ad, sure in (("iha", 14), ("mancinik", 10), ("ika", 10)):
            bolum(ad + "_cad_inceleme", sure, lambda zaman, oran, arac=ad: sunum.studyo(arac, oran),
                  "TEMSILI EKLEM GOSTERIMI" if EKLEMLI and ad != "mancinik" else "STATIK CAD / DONEN KAMERA")
        bolum("iha_yakin_ucus", sunum.profil.t_inis / .75, lambda zaman, oran: sunum.ucus(zaman * .75),
              "MODEL KOSUSU TAM UCUS PROFILI", 0, .75)
        bolum("model_algilama", 10, lambda zaman, oran: sunum.teshis(), "OZGUN MODEL ALGILAMA CIKTISI")
        gt_satirlar = [satir for satir in sunum.kayitlar["gt"] if satir.get("kaynak") == "surus"]
        sim_bas = gt_satirlar[0]["t"]
        sim_son = gt_satirlar[-1]["t"]
        bolum("gt_izin_ve_surusu", sim_son - sim_bas, lambda zaman, oran: sunum.surus(sim_bas + zaman),
              "GT TANISAL KOSUSU / HAM FIZIK DURUMU", sim_bas, 1)
        bolum("sonuc", 10, lambda zaman, oran: sunum.sonuc(), "MODEL VE GT SONUCLARI AYRI")
    finally:
        yazici.release()
        sunum.kapat()
    donusum = sim_video.h264_donustur(ana, hedef)
    video = cv2.VideoCapture(str(hedef))
    fps = video.get(cv2.CAP_PROP_FPS)
    okunan = 0
    while True:
        okundu, kare = video.read()
        if not okundu:
            break
        assert kare.shape[:2] == (1080, 1920)
        okunan += 1
    video.release()
    assert okunan == kare_n and fps == FPS
    gecerli = [kayit for kayit in gorunurluk if kayit["piksel"] > 15000 and kayit["genislik_px"] > 500]
    assert len(gecerli) / len(gorunurluk) >= .8, "İHA yakın takip görünürlüğü yetersiz"
    sonuc = {"tarih": datetime.now().astimezone().isoformat(), "dosya": hedef.relative_to(KOK).as_posix(),
             "sha256": sha(hedef), "fps": fps, "kare_n": kare_n, "sure_s": kare_n / FPS,
             "cozunurluk": list(BOYUT), "bayt": hedef.stat().st_size, "tum_kareler_okundu": True,
             "bolumler": bolumler, "magenta_gorunurluk": gorunurluk,
             "gorunurluk_esigi": "Örneklerin en az %80'inde 15000 magenta piksel ve 500 px genişlik; HUD hariç",
             "gorunurluk_gecen": len(gecerli), "gorunurluk_ornek": len(gorunurluk),
             "kosum_sonuclari": sunum.sonuclar, "donusum": donusum,
             "kaynak_ozetleri": {str(yol.relative_to(KOK)): sha(yol) for yol in (sunum.kayit_kok / "kosum").rglob("*.jsonl")},
             "eklemli": EKLEMLI,
             "eklem_siniri": "İKA sürüş açıları kaydedilmiş qpos; stüdyo ve İHA servo/pervane açıları temsili, gerçek telemetri/RPM değildir.",
             "sinir": "Yakın kamera/ışık sunum revizyonudur; fizik durumu yeniden oynatılır. Uçuş kinematik, İKA basitleştirilmiş fizik; GT model başarısı değildir.",
             "duvar_s": time.perf_counter() - baslangic, "komut": [sys.executable, *sys.argv]}
    yaz("video_ozeti.json", sonuc)
    teslim = KOK / "FDR/JURI/video" / VIDEO_ADI
    shutil.copy2(hedef, teslim)
    assert sha(teslim) == sonuc["sha256"]
    print("SINEMATIK_VIDEO_OK", kare_n, "KARE", sonuc["sure_s"], "s", sonuc["sha256"], flush=True)


def main():
    global CIKTI, EKLEMLI, KAYIT_KOK, VIDEO_ADI
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kayit", action="store_true")
    parser.add_argument("--onizleme", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--eklemli", action="store_true")
    parser.add_argument("--out", type=Path, default=CIKTI)
    args = parser.parse_args()
    EKLEMLI = args.eklemli
    if EKLEMLI:
        KAYIT_KOK = CIKTI
        if args.out == CIKTI:
            args.out = KOK / "results/fdr_33_20260914/cad_video_eklemli"
        VIDEO_ADI = "navitas_cad_eklemli_1080p.mp4"
        if args.kayit:
            parser.error("Eklemli gösterim mevcut fizik kaydını kullanır; yeni koşu değildir")
    CIKTI = args.out.resolve()
    if not CIKTI.is_relative_to(KOK / "results"):
        parser.error("Çıktı results altında olmalıdır")
    CIKTI.mkdir(parents=True, exist_ok=True)
    if args.kayit:
        kayit_al()
    if args.onizleme:
        onizleme()
    if args.render:
        render()


if __name__ == "__main__":
    main()

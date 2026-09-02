#!/usr/bin/env python3
"""NEDEN: Jetson paketindeki dosyalar elle kopyalanirsa depo uygulamasindan
sessizce ayrisabilir. Bu betik saha paketini kanonik codes/comms/scripts
kaynaklarindan mekanik olarak yeniler ve kopyalanan her dosyayi raporlar.
"""

from __future__ import annotations

import shutil
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
PAKET = KOK / "jetson_paket"
PAKET_KOD = PAKET / "kod"
KOPYALAR = {
    # 🔴 KAYIT DEFTERI — T103 · REVIEW_LOG D-177. Paket bunu TASIMIYORDU ve
    # kilavuza gore kurulan bir Jetson MODEL YUKLEYEMIYORDU:
    #     model_kayit_dogrula -> False | durum "kayit_defteri_yok"
    #     load_model -> RuntimeError: ... fail-closed
    # Tek calistirma yolu `--kayit-dogrulamasiz` idi, o da T73'te BILEREK
    # kurulan yanlis-model korumasini kapatir. Hedef `kod/` DEGIL `config/`:
    # `rpi_inference` defteri `_here.parent / "config" / ...` diye arar.
    KOK / "config" / "model_registry.json": PAKET / "config" / "model_registry.json",
    KOK / "codes" / "karar_sozlesmesi.py": PAKET_KOD / "karar_sozlesmesi.py",
    KOK / "codes" / "rpi_inference.py": PAKET_KOD / "rpi_inference.py",
    KOK / "codes" / "costmap_path_finder.py": PAKET_KOD / "costmap_path_finder.py",
    # 🔴 OLCEK KATMANI — T83 onarimi. `rpi_inference._arac_kisa_kenari` bu
    # modulu GECIKMELI + try/except ile import eder; dosya pakette YOKSA
    # kahin SESSIZCE "arac_maskesi modulu yok" notuyla None doner ve arac
    # govdesinden mpp turetme (CONTRACTS SS5.4, 3. katman) sahada OLU kalir.
    # Cokmeden kotu: hicbir kapi dusmuyordu. Kilit: tests/test_jetson_comms_paketi.
    KOK / "codes" / "arac_maskesi.py": PAKET_KOD / "arac_maskesi.py",
    KOK / "scripts" / "jetson_fps.py": PAKET_KOD / "jetson_fps.py",
    # 🔴 T202 · D-352: asagidaki UCU pakette VARDI ama KOPYALAR'da YOKTU
    # (yani "oksuz"du: paket yenilendiginde tazelenmiyorlardi) ya da HIC yoktu.
    # Kilavuzun kurulum blogu de onlari tasimiyordu; saha gunu su komutlar
    # `No such file` ile cokerdi:
    #   · model_registry.py  -> derlenen .engine KAYDEDILEMEZ, model_kayit_dogrula
    #     fail-closed doner ve model YUKLENMEZ (T103/D-177 ile ayni sinif kusur)
    #   · karisim_arena.yaml -> INT8/Q8 KALIBRASYON dosyasi; 30 Agustos Q8
    #     derlemesi (`int8=True data=...`) bunsuz kosmaz
    #   · kamera_dogrula.py  -> depoda HIC YOKTU, yalniz pakette duruyordu;
    #     kanonik kaynak artik `codes/` altindadir
    KOK / "codes" / "model_registry.py": PAKET_KOD / "model_registry.py",
    KOK / "dataset" / "karisim_arena.yaml": PAKET_KOD / "karisim_arena.yaml",
    KOK / "codes" / "kamera_dogrula.py": PAKET_KOD / "kamera_dogrula.py",
    KOK / "comms" / "protocol.py": PAKET_KOD / "protocol.py",
    KOK / "comms" / "link.py": PAKET_KOD / "link.py",
    KOK / "comms" / "iha_sender.py": PAKET_KOD / "iha_sender.py",
    KOK / "comms" / "inis_kaniti.py": PAKET_KOD / "inis_kaniti.py",
    KOK / "comms" / "iha_inis_yayinci.py": PAKET_KOD / "iha_inis_yayinci.py",
    # Faz B (D-403): YKS'nin PARACHUTE/ARM/DISARM komutlarini Pixhawk'a
    # aktaran Jetson sureci — D-393'un "AVIYONIK-BLOKLU" IHA yarisi. Pakette
    # yoksa sahada parasut yedegi ACK'siz kalir (YKS kirmizi "ACK YOK").
    KOK / "comms" / "iha_komut_alici.py": PAKET_KOD / "iha_komut_alici.py",
    # D-404: SiK hub (CONTRACTS 7.5; navitas-seri-hub.service) ve on-ucus kapisi
    # (jetson_baslat.sh --kapi, ~/navitas/scripts/ altinda arar) pakete alindi.
    KOK / "comms" / "seri_hub.py": PAKET_KOD / "seri_hub.py",
    KOK / "scripts" / "mavlink_dogrula.py": PAKET_KOD / "mavlink_dogrula.py",
    # Gorev K (SAHA_HAZIRLIK_PLANI_20260903 §1.4): kamera koprusu — Nano'da CSI
    # IMX477 yalniz sistem Python 3.6 + GStreamer'li sistem OpenCV ile okunur;
    # navitas-kamera-koprusu.service bunu KAMERA_PYTHON ile kosar ve
    # ~/navitas/scripts/kamera_koprusu.py arar. Kanonik scripts/, kod/ AYNADIR.
    KOK / "scripts" / "kamera_koprusu.py": PAKET_KOD / "kamera_koprusu.py",
}


def paketi_hazirla():
    """Kanonik saha modullerini Jetson paketine birebir kopyala."""
    PAKET_KOD.mkdir(parents=True, exist_ok=True)
    for kaynak, hedef in KOPYALAR.items():
        if not kaynak.is_file():
            raise FileNotFoundError(f"kanonik paket kaynagi yok: {kaynak}")
        # Hedef `kod/` disinda da olabilir (T103: `config/`). Dizin yoksa
        # olusturulur; raporlama ve `copy2` akisi DEGISMEZ.
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(kaynak, hedef)
        print(f"[JETSON_PAKET] {kaynak.relative_to(KOK)} -> "
              f"{hedef.relative_to(KOK)}")


def main():
    paketi_hazirla()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

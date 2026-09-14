"""NEDEN: Hatalı algı sonucu özgün tarama girdisi ve aynı üretim ağırlığı ile yeniden ölçülür."""

import json
from pathlib import Path
import sys

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "scripts"))
import fdr_33_sinematik_video as video
import iha_haritala


def main():
    girdi = video.CIKTI / "kosum/model_5_zor_42/iha_scan"
    cikti = KOK / "results/fdr_33_20260914/cad_video_eklemli/model_teshis"
    if cikti.exists():
        raise FileExistsError("Önceki teşhis korunur")
    cikti.mkdir(parents=True)
    model, kunye = video.gorev_kosumu.model_yukle()
    meta = iha_haritala._meta_oku(girdi)
    merkez = iha_haritala._htab_merkez(meta, None)
    sonuc = iha_haritala.haritala(cikti, model, *merkez, conf=.15, girdi_dir=girdi,
                                 kb_xy=iha_haritala._meta_xy(meta, "KB_XY"),
                                 hb_xy=iha_haritala._meta_xy(meta, "HB_XY"), arac_model=None)
    kaynak = json.loads((girdi / "detection.json").read_text(encoding="utf-8"))
    kontrol = {"model": kunye, "model_siniflari": model.names, "eski_sonuc": kaynak, "tekrar": sonuc,
               "mozaik_sha256": video.sha(cikti / "ortomozaik.jpg"),
               "girdi_mozaik_sha256": video.sha(girdi / "ortomozaik.jpg"),
               "kaynak_poses_sha256": video.sha(girdi / "poses.csv"),
               "esik_degisimi": False, "gt_maske_kullanildi": False,
               "sinir": "CAD eklem onarımı algı ağırlığını değiştirmez; bu tanısal tekrar başarıya dönüştürülmez."}
    (cikti / "teshis.json").write_text(json.dumps(kontrol, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MODEL_TESHIS", json.dumps(sonuc, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

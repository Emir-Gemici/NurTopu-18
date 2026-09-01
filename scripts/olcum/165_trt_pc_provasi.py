"""B4 — TensorRT DONUSUM PROVASI (PC'de, bilgi amacli).

NE KANITLAR: v36 ONNX grafiginin TensorRT'ye DONUSTUGUNU (desteklenmeyen
katman yok). NE KANITLAMAZ: Jetson `.engine`'i — engine tasimaz (surum +
compute capability kilidi). Asil kapi Gun-1 §3'tedir (T16,
`jetson_paket/GUN1_KONTROL_LISTESI.md`).

PC'de `tensorrt` pip paketi YOK (bilerek kurulmadi: uretim venv'ine GB'lik
SDK sokulmaz — roboflow dersi). Prova onnxruntime'in TensorrtExecutionProvider
saglayicisiyla denenir; TRT calisma zamani kutuphaneleri sistemde yoksa sonuc
OLCULEMEDI'dir ve "gecti" URETILMEZ.
"""
import json
import sys
from pathlib import Path

import numpy as np

from ayarlar import REPO

ONNX = REPO / "jetson_paket" / "models" / "navitas_seg_v36_best_512_fp16.onnx"


def main():
    import onnxruntime as ort
    rapor = {"onnx": str(ONNX), "ort": ort.__version__,
             "saglayicilar_mevcut": ort.get_available_providers()}
    if "TensorrtExecutionProvider" not in rapor["saglayicilar_mevcut"]:
        rapor["sonuc"] = "OLCULEMEDI: ORT derlemesinde TRT saglayicisi yok"
        print(json.dumps(rapor, ensure_ascii=False, indent=1))
        return 0
    try:
        ses = ort.InferenceSession(
            str(ONNX), providers=["TensorrtExecutionProvider"])
        aktif = ses.get_providers()
        rapor["saglayicilar_aktif"] = aktif
        if aktif and aktif[0] == "TensorrtExecutionProvider":
            g = ses.get_inputs()[0]
            x = np.zeros([d if isinstance(d, int) else 1 for d in g.shape],
                         dtype=np.float16 if "16" in g.type else np.float32)
            ses.run(None, {g.name: x})
            rapor["sonuc"] = "DONUSTU: graf TRT ile kosuldu (PC)"
        else:
            # Oturum kuruldu ama TRT bas saglayici DEGIL -> geri dusme var;
            # bunu "donustu" SAYMAYIZ.
            rapor["sonuc"] = ("OLCULEMEDI: TRT bas saglayici olamadi "
                              "(geri dusme) — donusum kaniti YOK")
    except Exception as e:
        rapor["sonuc"] = f"OLCULEMEDI: {type(e).__name__}"
        rapor["hata"] = str(e)[:400]
    print(json.dumps(rapor, ensure_ascii=False, indent=1))
    cikti = REPO / "results" / "b4_fps" / "trt_pc_provasi.json"
    cikti.write_text(json.dumps(rapor, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

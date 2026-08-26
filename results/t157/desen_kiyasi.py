import re

satir = "  --engine models/navitas_seg_v30_best_512_fp16 \\"
ESKI = re.compile(r"navitas_seg_(v\d+)[A-Za-z0-9_]*\.(?:pt|onnx|engine)")
YENI = re.compile(r"navitas_seg_(v\d+)[A-Za-z0-9_]*(?:\.(?:pt|onnx|engine))?")
print("satir      :", satir)
print("ESKI desen :", ESKI.findall(satir), "<- KOR (kapi bos liste gorur, satiri hic denetlemez)")
print("YENI desen :", YENI.findall(satir), "<- yakaliyor")

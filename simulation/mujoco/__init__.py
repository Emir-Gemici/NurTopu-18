"""NAVITAS — MuJoCo görev icra simülasyonu (FDR sprinti H1, D-438).

Modüller:
  arena_mjcf : `simulation/scripts/arena.py` haritasından DETERMİNİSTİK MJCF üretir
  araclar    : İHA (sabit kanat, procedural mesh), İKA (DDR ölçülü fizik), paraşüt
  iha_ucus   : kinematik uçuş profili + 1 Hz nadir tarama (scan_N.jpg + poses.csv)
  on_olcum_k3: mozaik → üretim modeli v36 → rota; K3 ön-ölçümü

Bu paket SİMÜLASYON aracıdır: mujoco / trimesh / cv2 / numpy kullanır.
`codes/` ve `comms/` üretim kuralına (OpenCV + NumPy + heapq) TABİ DEĞİLDİR
(görev tanımı, 10 Eyl 2026).
"""

"""T153 olcum kosumu: ana depodaki olcum betikleri (scripts/olcum, REPO=O:\\navitas)
uretim kodunu `sys.path.insert(0, O:\\navitas\\codes)` ile ice aktarir. Bu
worktree'nin (T153 degisikligi iceren) `codes/` kopyasini KULLANMALARI icin
`rpi_inference` ve `karar_sozlesmesi` burada, yorumlayici acilirken, sys.modules'e
ONCEDEN yuklenir; sonraki `from rpi_inference import ...` ayni modulu bulur.
PYTHONPATH bu dizini gosterdiginde alt sureclere de (65 -> 61 ..., 142 -> 126) gecer.
Her surec stderr'e hangi dosyayi yuklediğini yazar (kanit).
"""
import os
import sys

WT = r"O:\navitas\.claude\worktrees\wf_2d1c9d5e-54f-1\codes"
if WT not in sys.path:
    sys.path.insert(0, WT)
import karar_sozlesmesi  # noqa: E402,F401
import rpi_inference  # noqa: E402,F401

print(f"[T153 sitecustomize] rpi_inference={rpi_inference.__file__} "
      f"NAVITAS_INCE_BETON_SERIT={os.environ.get('NAVITAS_INCE_BETON_SERIT')!r}",
      file=sys.stderr, flush=True)

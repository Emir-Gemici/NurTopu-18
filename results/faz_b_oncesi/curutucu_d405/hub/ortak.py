"""Curutucu ortak kurulum: repo yollari + istege bagli mutant hub yukleme."""
import importlib.util
import sys
from pathlib import Path

KOK = Path("O:/navitas")
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

YEREL = "127.0.0.1"


def hub_modulu_yukle(dosya=None):
    """dosya verilirse o dosyayi 'seri_hub' adiyla yukler (mutant); yoksa repo."""
    if dosya is None:
        import seri_hub
        return seri_hub
    spec = importlib.util.spec_from_file_location("seri_hub", dosya)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["seri_hub"] = mod
    spec.loader.exec_module(mod)
    return mod


class SahteSaat:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

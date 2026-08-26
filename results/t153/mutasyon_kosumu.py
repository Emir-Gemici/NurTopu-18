"""T153 MUTASYON KANITI: genislik UST siniri kaldirilinca (oran 1.0 = tum tuval)
genis acik yol da engel olur ve `test_GENIS_ACIK_YOL_engel_SAYILMAZ` DUSMELIDIR.
Kod DEGISTIRILMEZ; sabit calisma aninda yamalanir (fonksiyon modul globalini
cagri aninda okur). Cikti results/t153/mutasyon.log'a yazilir.
"""
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))
sys.path.insert(0, str(KOK / "tests"))
import karar_sozlesmesi as KS  # noqa: E402

hangi = sys.argv[1] if len(sys.argv) > 1 else "ust"
if hangi == "ust":
    KS.INCE_BETON_GENISLIK_UST_ORANI = 1.0
    print("MUTASYON: INCE_BETON_GENISLIK_UST_ORANI = 1.0 (ust sinir YOK)")
elif hangi == "uzunluk":
    KS.INCE_BETON_ASGARI_UZUNLUK_ORANI = 0.0
    KS.INCE_BETON_EN_BOY_ORANI = 0.0
    print("MUTASYON: uzunluk / en-boy suzgeci YOK")
elif hangi == "yok":
    print("MUTASYON YOK (kontrol)")
import test_t153_ince_beton_serit as T  # noqa: E402

suite = unittest.defaultTestLoader.loadTestsFromModule(T)
r = unittest.TextTestRunner(verbosity=1, stream=sys.stdout).run(suite)
print("DUSEN:", [str(t).split(" ")[0] for t, _ in r.failures + r.errors])

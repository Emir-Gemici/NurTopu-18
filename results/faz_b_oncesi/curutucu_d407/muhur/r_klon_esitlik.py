"""Iki klon (CRLF checkout vs LF checkout) arasinda kunye kapsamindaki HER dosya icin
ham sha256 ve sha256_kanonik esitligini say. Ek: kapsam DISI ama sahada belirleyici
dosyalar (config/pixhawk/*.param|*.waypoints, requirements_nano.txt, manifest)."""
import sys
from pathlib import Path

A, B = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(A / "scripts")); sys.path.insert(0, str(A / "codes"))
import surum_dondur as sd  # noqa: E402

kapsam = [h for _, h in sd.PAKET_ESLEMESI] + [k for k, _ in sd.PAKET_ESLEMESI]
kapsam += list(sd.SAHA_YAPILANDIRMA) + list(sd.YKS_IKA)
kapsam += [sd.DEFTER_GORELI.as_posix(), "models/navitas_seg_v36_best.pt",
           "jetson_paket/models/navitas_seg_v36_best.pt",
           "jetson_paket/models/navitas_seg_v36_best_512_fp16.onnx"]
ek = ["config/pixhawk/arducopter_fda.param", "config/pixhawk/fda_gorev.waypoints",
      "config/pixhawk/README.md", "jetson_paket/kod/requirements_nano.txt",
      "jetson_paket/models/jetson_derleme_manifest.json"]


def olc(liste, baslik):
    ham_es = kan_es = n = 0
    farkli = []
    for y in liste:
        a, b = A / y, B / y
        if not (a.is_file() and b.is_file()):
            print(f"  (atlandi, yok) {y}")
            continue
        n += 1
        h = sd.sha256_hesapla(a) == sd.sha256_hesapla(b)
        k = sd.sha256_kanonik(a) == sd.sha256_kanonik(b)
        ham_es += h
        kan_es += k
        if not k:
            farkli.append(y)
    print(f"{baslik}: n={n}  ham_esit={ham_es}/{n}  kanonik_esit={kan_es}/{n}")
    for y in farkli:
        print(f"    KANONIK FARKLI: {y}  (uzanti {Path(y).suffix!r} metin listesinde: "
              f"{Path(y).suffix.lower() in sd.METIN_UZANTILARI})")


olc(sorted(set(kapsam)), "KUNYE KAPSAMI")
olc(ek, "KAPSAM DISI EK")

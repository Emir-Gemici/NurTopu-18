import os
import requests
import zipfile
from pathlib import Path

API_KEY = os.environ.get("ROBOFLOW_API_KEY", "")
if not API_KEY:
    raise SystemExit("ROBOFLOW_API_KEY ortam değişkeni ayarlanmamış. Örnek: export ROBOFLOW_API_KEY=xxx")

DATASETS = [
    ("yolo11-mldyd", "post-disaster-mitigation"),
    ("hind-althabi", "road-debris-iya6s"),
    ("dsn", "drone-based-road-mapping-test"),
    ("dsn", "drone-based-road-mapping-dojdm"),
    ("drone-journalism", "collapsed-buildings-jjz1g"),
    ("roads-detection-with-drones", "landslide-detection-2dme2"),
    ("raghava-priya", "landslide-htrll"),
    ("syadil", "road-damage-classification-drone"),
    ("roads-8jikc", "landslide-8kxwy"),
    ("harikrishna-71pmm", "drone-obstacle-detection-hvfyt"),
    ("monit-dfskw", "aerial-waste-d2orx"),
    ("rubble-project", "rubble-detection"),
    ("rmit-ayab4", "demolition-waste-ws20c"),
    ("object-detection-of-illegal-dumping-sites", "aerial-dumping-sites"),
    ("plat-mbvpb", "road-blocked-clasification"),
]

FORMAT_MAP = {
    "object-detection": "coco",
    "instance-segmentation": "coco-segmentation",
    "semantic-segmentation": "coco-segmentation",
    "classification": "multiclass",
}

BASE_DIR = Path("~/trs/github/navitas/test_images/roboflow").expanduser()
BASE_DIR.mkdir(parents=True, exist_ok=True)


def download_dataset(workspace, project):
    print(f"\n→ {workspace}/{project}")

    # Proje bilgisi al
    r = requests.get(f"https://api.roboflow.com/{workspace}/{project}?api_key={API_KEY}")
    if r.status_code != 200:
        print(f"  HATA proje: {r.status_code} — {r.text[:100]}")
        return

    proj = r.json().get("project", {})
    version = proj.get("versions", 0)
    ptype = proj.get("type", "object-detection")
    fmt = FORMAT_MAP.get(ptype, "coco")

    if version == 0:
        print(f"  HATA: versiyon bulunamadı")
        return

    print(f"  tip={ptype}  format={fmt}  versiyon={version}")

    # Download URL al
    r2 = requests.get(
        f"https://api.roboflow.com/{workspace}/{project}/{version}/{fmt}",
        params={"api_key": API_KEY}
    )
    if r2.status_code != 200:
        print(f"  HATA link: {r2.status_code} — {r2.text[:200]}")
        return

    link = r2.json().get("export", {}).get("link")
    if not link:
        print(f"  HATA: link yok — {r2.json()}")
        return

    # İndir
    out_dir = BASE_DIR / project
    out_dir.mkdir(exist_ok=True)
    zip_path = out_dir / f"{project}.zip"

    print(f"  İndiriliyor...", end="", flush=True)
    with requests.get(link, stream=True) as resp:
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
    print(" ✓")

    # Görselleri çıkar
    img_count = 0
    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            if name.lower().endswith((".jpg", ".jpeg", ".png")):
                (out_dir / Path(name).name).write_bytes(z.read(name))
                img_count += 1

    zip_path.unlink()
    print(f"  ✓ {img_count} görsel → {out_dir}")


if __name__ == "__main__":
    for workspace, project in DATASETS:
        try:
            download_dataset(workspace, project)
        except Exception as e:
            print(f"  İSTİSNA: {e}")
    print("\nTamamlandı.")

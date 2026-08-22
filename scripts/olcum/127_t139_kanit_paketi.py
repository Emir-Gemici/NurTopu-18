"""T139 ADIM 1 — KANITI KURTAR: rota ureten kareleri repoya KALICI koy.

🔴 NEDEN: oturumun en guvenlik-kritik bulgusunun (gece karesinde
`YOL=2 · guven=1,000`) GIRDISI diskte izlenmiyordu — `find results/t138
results/t136 -name "*.jpg"` -> 0. Mimar iddiayi dogrulamak istedi ve
DOGRULAYAMADI; iki kez YANLIS KARE aldi.

🔴 KOK NEDEN (T139'da bulundu): AD SEMASI YANILTICI.
`extract_key_frames.py:169` -> f"frame_{sira + yazilan:06d}_{kare_no:09d}.jpg"
  · birinci sayi = KACINCI KAYDEDILEN kare (video indeksi DEGIL)
  · ikinci sayi = VIDEO KARE NUMARASI — **MILISANIYE DEGIL**
`frame_000064_000004740.jpg` 9 haneli sifir dolgulu ikinci sayisiyla ms gibi
GORUNUYOR ama video karesi 4740'tir (30 fps -> 158,2 sn).
OLCULDU (ayni dosya, uc okuma):
    kare_no=4740 (DOGRU)          -> L=18,5
    "4740 ms" = video karesi 142  -> L=22,8   <- mimarin 1. okumasi
    "indeks 64"                   -> L=22,5   <- mimarin 2. okumasi
    cikarilmis jpg                -> L=18,4
Yani iddia YANLIS DEGILDI; ADRESLENEMIYORDU. Bu betik adresi KALICI kilar.

CIKTI: results/t139/kanit/ + kanit_manifest.json (sha256 dahil)
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
KARE_KOK = KOK / "data" / "dji_prova_kareler"
CIKTI = KOK / "results" / "t139" / "kanit"
GECE_OLCUM = KOK / "results" / "t138" / "gece_kumesi.json"
GUNDUZ_KOK = KOK / "data" / "raw_frames"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    import cv2

    kare_mf = {k["dosya"]: k for k in
               json.loads((KARE_KOK / "manifest.json").read_text(encoding="utf-8"))["kareler"]}
    olcum = json.loads(GECE_OLCUM.read_text(encoding="utf-8"))["modeller"]

    # 1) ROTA URETEN kareler (hangi model uretti bilgisiyle)
    rota = {}
    for model, v in olcum.items():
        for k in v["kareler"]:
            if k["olceksiz_wp"] > 0 or k["olcekli_wp"] > 0:
                anahtar = (k["klip"], k["kare"])
                rota.setdefault(anahtar, {"modeller": [], "olcum": k})
                rota[anahtar]["modeller"].append(model.replace("navitas_seg_", "").replace("_best.pt", ""))

    # 2) KONTROL kareleri: en karanlik · tipik MASKE_YOK · gunduz referansi
    v35 = olcum["navitas_seg_v35_best.pt"]["kareler"]
    reddedilen = [k for k in v35 if k["olceksiz_wp"] == 0]
    kontrol = []
    if reddedilen:
        kontrol.append(("en_dusuk_zemin", min(reddedilen, key=lambda k: k["zemin_orani"])))
        kontrol.append(("en_yuksek_zemin_ama_RED", max(reddedilen, key=lambda k: k["zemin_orani"])))

    CIKTI.mkdir(parents=True, exist_ok=True)
    kayitlar = []

    def ekle(rol, klip, kare, ekstra):
        aday = list(KARE_KOK.rglob(kare))
        aday = [p for p in aday if p.parent.name.startswith(klip[:20])] or aday
        if not aday:
            print(f"  ATLANDI (kare bulunamadi): {klip}/{kare}")
            return
        p = aday[0]
        bagil = f"{p.parent.name}/{p.name}"
        mf = kare_mf.get(bagil, {})
        hedef = CIKTI / f"{rol}__{p.parent.name[:34]}__{p.name}"
        shutil.copy2(p, hedef)
        img = cv2.imread(str(p))
        L = float(cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].mean())
        kayitlar.append({
            "rol": rol, "dosya": hedef.name,
            "kaynak_video": mf.get("kaynak"),
            "video_kare_no": mf.get("kare_no"),
            "zaman_sn": mf.get("zaman_sn"),
            "yaklasik_ms": round(mf["zaman_sn"] * 1000) if mf.get("zaman_sn") is not None else None,
            "sha256": sha(hedef), "bayt": hedef.stat().st_size,
            "L_ort": round(L, 2), "cozunurluk": [img.shape[1], img.shape[0]],
            **ekstra,
        })
        print(f"  {rol:24s} {hedef.name[:58]:60s} L={L:5.1f} "
              f"kare_no={mf.get('kare_no')}")

    print("ROTA URETEN kareler:")
    for (klip, kare), v in sorted(rota.items()):
        ekle("rota_uretildi", klip, kare,
             {"uretien_modeller": v["modeller"],
              "zemin_orani": v["olcum"]["zemin_orani"],
              "wp_olceksiz": v["olcum"]["olceksiz_wp"],
              "wp_olcekli": v["olcum"]["olcekli_wp"],
              "yol_olceksiz": v["olcum"].get("olceksiz_yol")})
    print("KONTROL kareleri:")
    for rol, k in kontrol:
        ekle(f"kontrol_{rol}", k["klip"], k["kare"],
             {"zemin_orani": k["zemin_orani"], "sebep": k["olceksiz_sebep"]})
    print("GUNDUZ referans karesi:")
    gunduz = sorted(GUNDUZ_KOK.rglob("*.jpg"))
    if gunduz:
        p = gunduz[len(gunduz) // 2]
        hedef = CIKTI / f"kontrol_gunduz__{p.parent.name[:34]}__{p.name}"
        shutil.copy2(p, hedef)
        img = cv2.imread(str(p))
        L = float(cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].mean())
        kayitlar.append({"rol": "kontrol_gunduz", "dosya": hedef.name,
                         "kaynak_video": p.parent.name, "video_kare_no": None,
                         "zaman_sn": None, "yaklasik_ms": None,
                         "sha256": sha(hedef), "bayt": hedef.stat().st_size,
                         "L_ort": round(L, 2),
                         "cozunurluk": [img.shape[1], img.shape[0]]})
        print(f"  kontrol_gunduz           {hedef.name[:58]:60s} L={L:5.1f}")

    io.open(CIKTI.parent / "kanit_manifest.json", "w", encoding="utf-8").write(
        json.dumps({
            "_ne": "T139 · kanit paketi — rota ureten kareler + kontroller",
            "_ad_semasi": (
                "extract_key_frames.py:169 -> frame_{KACINCI_KAYDEDILEN:06d}_"
                "{VIDEO_KARE_NO:09d}.jpg. IKINCI SAYI MILISANIYE DEGIL, VIDEO "
                "KARE NUMARASIDIR. 9 haneli sifir dolgusu ms gibi gosterir; "
                "zaman icin `zaman_sn` alanini kullanin."),
            "_adresleme": (
                "Kareyi videodan cozmek icin: cv2.VideoCapture(kaynak_video) + "
                "CAP_PROP_POS_FRAMES = video_kare_no. `yaklasik_ms` ile SEEK "
                "ETMEYIN — kodlayici anahtar kareye yuvarlar."),
            "_olcum": "results/t138/gece_kumesi.json",
            "toplam": len(kayitlar), "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1))
    toplam_mb = sum(k["bayt"] for k in kayitlar) / 1e6
    print(f"\n{len(kayitlar)} kare · {toplam_mb:.1f} MB -> {CIKTI}")
    print(f"manifest: {CIKTI.parent / 'kanit_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

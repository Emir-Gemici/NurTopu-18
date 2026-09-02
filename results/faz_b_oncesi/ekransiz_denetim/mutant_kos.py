"""D-404 §2 bagimsiz denetim — mutant kosumu (repo dosyalarina DOKUNMAZ).

Her mutant icin codes/rpi_inference.py scratchpad altina kopyalanir, tek bir
metin degisimi uygulanir (tam 1 eslesme sart), test dosyasinin kopyasi
sys.path ile o kopyaya yonlendirilir ve tests/test_faz_b_rpi_ekransiz.py
(7 test) kosulur. Cikti: mutant -> sonuc satiri + dusen/ERROR testler.
"""
import subprocess
import sys
from pathlib import Path

KOK = Path(r"O:\navitas")
SCR = Path(__file__).resolve().parent / "mutants"
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
ORIG = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")
TEST = (KOK / "tests" / "test_faz_b_rpi_ekransiz.py").read_text(encoding="utf-8")

MUTANTLAR = {
    # (a) run_video: ekransiz+kayitsizda gorsel atlama kaldirildi (draw yine cagrilir)
    "a_video_ilk_continue_False": (
        "        if ekransiz and not writer:\n            continue\n        vis = draw_masks(sq, masks)",
        "        if False:\n            continue\n        vis = draw_masks(sq, masks)"),
    # (b) run_video: imshow oncesi ekransiz atlama kaldirildi (imshow yine cagrilir)
    "b_video_ikinci_continue_False": (
        "        if ekransiz:\n            continue\n        cv2.imshow(\"Navitas\", vis)",
        "        if False:\n            continue\n        cv2.imshow(\"Navitas\", vis)"),
    # (c) run_camera: destroyAllWindows kosulsuz
    "c_camera_destroy_kosulsuz": (
        "    cap.release()\n    if not ekransiz:\n        cv2.destroyAllWindows()\n    print(kamera_bitis_raporu(ozet))",
        "    cap.release()\n    cv2.destroyAllWindows()\n    print(kamera_bitis_raporu(ozet))"),
    # (d) run_camera: mimarin denedigi mutant (kontrol)
    "d_camera_continue_False_MIMAR": (
        "        if ekransiz:\n            continue\n        vis = draw_masks(sq, masks)",
        "        if False:\n            continue\n        vis = draw_masks(sq, masks)"),
    # (e) run_video: destroyAllWindows kosulsuz
    "e_video_destroy_kosulsuz": (
        "    if writer:\n        writer.release()\n    if not ekransiz:\n        cv2.destroyAllWindows()",
        "    if writer:\n        writer.release()\n    cv2.destroyAllWindows()"),
    # (g) run_video: ekransizda KAYIT da atlanir (kayitli ekransiz kosum bos video uretir)
    "g_video_kayit_da_atlanir": (
        "        if ekransiz and not writer:\n            continue\n        vis = draw_masks(sq, masks)",
        "        if ekransiz:\n            continue\n        vis = draw_masks(sq, masks)"),
    # (h) run_camera: ekransiz yazisi basilmaz (print dali ters)
    "h_camera_ekransiz_print_yok": (
        "    if ekransiz:\n        print(\"EKRANSIZ kip: pencere yok, karar yayini surer (durdurma: SIGINT/SIGTERM)\")\n    else:\n        print(\"Kamera acik — cikmak icin 'q'\")",
        "    print(\"Kamera acik — cikmak icin 'q'\")"),
}


def kur(ad, eski, yeni):
    d = SCR / ad
    d.mkdir(parents=True, exist_ok=True)
    n = ORIG.count(eski)
    assert n == 1, f"{ad}: kalip {n} kez eslesti (1 olmali)"
    (d / "rpi_inference.py").write_text(ORIG.replace(eski, yeni), encoding="utf-8")
    # test kopyasi: KOK sabit, mutant dizini sys.path basina
    t = TEST.replace("KOK = Path(__file__).resolve().parents[1]",
                     f"KOK = Path(r\"{KOK}\")")
    assert t != TEST
    t2 = t.replace("import rpi_inference as ri  # noqa: E402",
                   f"sys.path.insert(0, r\"{d}\")\nimport rpi_inference as ri  # noqa: E402\n"
                   f"assert ri.__file__.lower().startswith(r\"{d}\".lower()), ri.__file__")
    assert t2 != t
    (d / "test_mut.py").write_text(t2, encoding="utf-8")
    return d


def kos(d):
    s = subprocess.run([PY, "-B", str(d / "test_mut.py"), "-v"], cwd=KOK,
                       capture_output=True, text=True, timeout=600)
    err = s.stderr
    ozet = [l for l in err.splitlines() if l.startswith(("OK", "FAILED", "Ran "))]
    dusen = [l for l in err.splitlines()
             if l.startswith(("ERROR:", "FAIL:"))]
    return s.returncode, ozet, dusen, err


if __name__ == "__main__":
    secim = sys.argv[1:] or list(MUTANTLAR)
    print(f"{'mutant':34} {'sonuc':40} yakalandi?")
    for ad in secim:
        eski, yeni = MUTANTLAR[ad]
        d = kur(ad, eski, yeni)
        rc, ozet, dusen, err = kos(d)
        yak = "EVET" if rc != 0 else "HAYIR (VAKUM)"
        print(f"{ad:34} {' | '.join(ozet):40} {yak}")
        for l in dusen:
            print(f"    {l}")
        if "Traceback" in err and rc != 0 and not dusen:
            print("    [import/asama hatasi]:", err.strip().splitlines()[-1])

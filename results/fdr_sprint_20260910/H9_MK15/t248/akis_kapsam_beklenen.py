r"""T248 — `akis_kapsam_t226d.py`in BEKLENEN EXIT=1 durumunu MAKİNEYE bağlar.

`akis_kapsam_OKUBENI.md` "EXIT=1 beklenendir, çünkü T248 ürüne gerçek bir dal
ekledi ve diyagram onu göstermek zorunda" diyor. Düzyazı bir beyan denetlenmez:
bu betik beklentiyi ÖN KAYIT hâline getirir — `[YENI]` kümesi TAM OLARAK
{d59 -> comms/yks_gui.py:1973, d59b -> comms/yks_gui.py:1981} olmalı, başka
her kapsam hatası türü SIFIR olmalı ve çıkış kodu 1 olmalıdır. Kümeye üçüncü
bir düğüm girerse ya da bu ikisinden biri çıkarsa kapı DÜŞER.

`--mutasyon`: pinin boş olmadığını ölçer — `FDR/sekiller/akis_d.mmd`den d59b
düğüm satırı geçici olarak SİLİNİR (sha256 ile bayt-eş geri yazılır) ve gözlenen
kümenin GERÇEKTEN değiştiği gösterilir.

Kullanım:
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t248/akis_kapsam_beklenen.py [--mutasyon]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
BETIK = KOK / "results" / "fdr_sprint_20260910" / "H9_MK15" / "t226" / "akis_kapsam_t226d.py"
MMD = KOK / "FDR" / "sekiller" / "akis_d.mmd"
TABAN = "776f0254~1"
PY = sys.executable

BEKLENEN_YENI = {
    ("d59", "comms/yks_gui.py:1973"),
    ("d59b", "comms/yks_gui.py:1981"),
}
# Ozet satirindaki her hata turu icin beklenen sayi (YENI disinda hepsi 0).
BEKLENEN_OZET = {
    "ALTGRAFIK": 0, "KAPSAM": 0, "DEYIM": 0, "SIRA": 0, "DOSYA": 0,
    "DEYIM_YOK": 0, "KENAR": 0, "YENI": 2, "SILINEN": 0, "KENAR_KUMESI": 0,
}
SATIR = re.compile(r"^\s*HATA (\S+) \[YENI\]: tabanda yok -> (\S+)$", re.M)


def kos():
    p = subprocess.run([PY, "-X", "utf8", "-B", str(BETIK), "--taban", TABAN],
                       cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    cikti = p.stdout + p.stderr
    gozlenen = set(SATIR.findall(cikti))
    ozet = {}
    m = re.search(r"kapsam HATASI (\d+) \(([^)]*)\)", cikti)
    if m:
        for parca in m.group(2).split(","):
            ad, _, sayi = parca.strip().rpartition(" ")
            ozet[ad] = int(sayi)
    return p.returncode, gozlenen, ozet, cikti


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutasyon", action="store_true")
    a = ap.parse_args()

    kod, gozlenen, ozet, _c = kos()
    print(f"[PIN] exit={kod} (beklenen 1)", flush=True)
    print(f"[PIN] gozlenen YENI kumesi = {sorted(gozlenen)}", flush=True)
    print(f"[PIN] beklenen YENI kumesi = {sorted(BEKLENEN_YENI)}", flush=True)
    print(f"[PIN] ozet = {ozet}", flush=True)
    tamam = (kod == 1 and gozlenen == BEKLENEN_YENI and ozet == BEKLENEN_OZET)
    print(f"[PIN] {'TUTTU' if tamam else 'TUTMADI'}", flush=True)

    if a.mutasyon:
        ham = MMD.read_bytes()
        ozet_sha = hashlib.sha256(ham).hexdigest()
        ss = b"\r\n" if b"\r\n" in ham else b"\n"
        hedef = [s for s in ham.split(ss) if s.strip().startswith(b"d59b[")
                 or s.strip().startswith(b'd59b["')]
        if len(hedef) != 1:
            raise SystemExit(f"MUTASYON HEDEFI TEK DEGIL: {len(hedef)}")
        try:
            MMD.write_bytes(ss.join(s for s in ham.split(ss) if s != hedef[0]))
            m_kod, m_gozlenen, m_ozet, _mc = kos()
        finally:
            MMD.write_bytes(ham)
            if hashlib.sha256(MMD.read_bytes()).hexdigest() != ozet_sha:
                raise SystemExit(f"GERI YAZILAMADI {MMD}")
        print(f"\n[MUTASYON] d59b dugum satiri SILINDI", flush=True)
        print(f"[MUTASYON] exit={m_kod} · YENI kumesi={sorted(m_gozlenen)}",
              flush=True)
        print(f"[MUTASYON] ozet = {m_ozet}", flush=True)
        degisti = (m_gozlenen != BEKLENEN_YENI) or (m_ozet != BEKLENEN_OZET)
        print(f"[MUTASYON] pin {'YAKALADI' if degisti else 'KACIRDI'}",
              flush=True)
        tamam = tamam and degisti

    print(f"AKIS_KAPSAM_BEKLENEN {'GECTI' if tamam else 'DUSTU'}", flush=True)
    return 0 if tamam else 1


if __name__ == "__main__":
    raise SystemExit(main())

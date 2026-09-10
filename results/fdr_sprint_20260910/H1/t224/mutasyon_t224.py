"""T224 mutasyon koşucusu — her mutasyonu `comms/yks_gui.py`'ye uygular,
`tests/test_yks_erken_ika_ack_tamponu.py`'yi koşar, dosyayı BAYT-EŞ geri
yükler (sha256 ile doğrulanır). M0 = T224 öncesi kod (`4c75cf2d`, T224
worktree'sinin taban commit'i): testin özgün kusuru yeniden ürettiğinin kanıtı.

KOSUM (depo kökünden; başka süreç yks_gui.py'yi okurken KOŞMA):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H1/t224/mutasyon_t224.py
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
YOL = KOK / "comms" / "yks_gui.py"
PY = r"O:/navitas-local-train/venv/Scripts/python.exe"
TEST = "test_yks_erken_ika_ack_tamponu.py"
T224_ONCESI = "4c75cf2d"

orijinal = YOL.read_bytes()
sha0 = hashlib.sha256(orijinal).hexdigest()
metin = orijinal.decode("utf-8")
crlf = "\r\n" in metin
metin_n = metin.replace("\r\n", "\n")
oncesi = subprocess.run(["git", "-C", str(KOK), "show",
                         f"{T224_ONCESI}:comms/yks_gui.py"],
                        capture_output=True, check=True).stdout

MUTASYONLAR = [
    (f"M0 T224 oncesi yks_gui.py ({T224_ONCESI})", None, None),
    ("M1 tampona yazma kapali",
     "                self._erken_ika_rota_ack_sakla(ref)\n",
     "                pass\n"),
    ("M2 sure denetimi yok",
     "        if time.monotonic() - gelis > IKA_ROTA_ACK_ERKEN_TAMPON_S:\n",
     "        if False:\n"),
    ("M3 ref_tip'siz kopya da tamponlanir",
     "            elif ref_tip == MESAJ_OPEN_ROUTE:\n",
     "            elif ref_tip in (None, MESAJ_OPEN_ROUTE):\n"),
    ("M4 havada esleme aninda olculur",
     "        self._ika_rota_ack_bagla(seq, damga, havada, erken=True)\n",
     "        self._ika_rota_ack_bagla(seq, damga, self._iha_havada_mi(), erken=True)\n"),
    ("M5 _mesaj_isle esleme cagrisi yok",
     '            self._erken_ika_rota_ack_esle(m["seq"])\n',
     "            pass\n"),
    ("M6 erken alani yazilmaz",
     '            alanlar["erken"] = True\n',
     "            pass\n"),
    ("M7 baska seq'in kaydi eslenir",
     "        kayit = tampon.pop(seq, None)\n",
     "        kayit = tampon.pop(next(iter(tampon)), None)\n"),
    ("M8 fikstur geri donusu (getattr) yok",
     '        tampon = getattr(self, "_erken_ika_rota_ack", None)\n        if not tampon:\n',
     "        tampon = self._erken_ika_rota_ack\n        if not tampon:\n"),
    ("M9 anlik yol satiri da erken=true yazar",
     "        if erken:\n",
     "        if True:\n"),
]


def kos():
    p = subprocess.run([PY, "-B", "-X", "utf8", "-m", "unittest", "discover",
                        "-s", "tests", "-p", TEST],
                       cwd=KOK, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    cikti = p.stdout + p.stderr
    ran = re.search(r"Ran (\d+) tests?", cikti)
    son = [s for s in cikti.strip().splitlines() if s.strip()][-1]
    dusen = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", cikti, re.M)))
    return p.returncode, (ran.group(1) if ran else "?"), son, dusen


sonuc = []
try:
    for ad, eski, yeni in MUTASYONLAR:
        if eski is None:
            YOL.write_bytes(oncesi)
        else:
            n = metin_n.count(eski)
            if n != 1:
                print(f"{ad}: eski dize {n} kez — ATLANDI")
                sonuc.append((ad, None))
                continue
            m = metin_n.replace(eski, yeni)
            YOL.write_bytes((m.replace("\n", "\r\n") if crlf else m).encode("utf-8"))
        kod, ran, son, dusen = kos()
        YOL.write_bytes(orijinal)
        yakalandi = kod != 0
        sonuc.append((ad, yakalandi))
        print(f"{ad}: cikis={kod} ran={ran} son='{son}' -> "
              f"{'YAKALANDI' if yakalandi else 'KACTI'}; dusen={dusen}")
finally:
    YOL.write_bytes(orijinal)
    sha1 = hashlib.sha256(YOL.read_bytes()).hexdigest()
    print(f"geri yukleme sha esit: {sha1 == sha0} ({sha0[:12]})")

yakalanan = sum(1 for _, y in sonuc if y)
print(f"OZET: {yakalanan}/{len(sonuc)} mutasyon yakalandi")
kod, ran, son, dusen = kos()
print(f"TEMIZ KOSUM (mutasyonsuz): cikis={kod} ran={ran} son='{son}'")

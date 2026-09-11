"""T226 mutasyon koşucusu — her mutasyonu `comms/yks_gui.py` ve/veya
`scripts/kamera_koprusu.py`'ye uygular, `tests/test_yks_mk15_hakem_ekrani.py`'yi
koşar, dosyaları BAYT-EŞ geri yükler (sha256 ile doğrulanır). M0 = T226 öncesi
kod (`dcf6edcf`, T226 worktree'sinin taban commit'i): kapının özgün kusuru
(D-443 a/d) yeniden ürettiğinin kanıtı.

KOSUM (depo kökünden; başka süreç bu dosyaları okurken KOŞMA):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/mutasyon_t226.py
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
PY = r"O:/navitas-local-train/venv/Scripts/python.exe"
TEST = "test_yks_mk15_hakem_ekrani.py"
T226_ONCESI = "dcf6edcf"
GUI = KOK / "comms" / "yks_gui.py"
KOPRU = KOK / "scripts" / "kamera_koprusu.py"
DOSYALAR = (GUI, KOPRU)

MUTASYONLAR = [
    (f"M0 T226 oncesi yks_gui.py + kamera_koprusu.py ({T226_ONCESI})", None),
    ("M1 pack_forget geri gelir (kucuk harita kamera gorunumunde gizli)", [
        (GUI, "            self._harita_ciz()          # küçük kopya güncel rotayla\n",
         "            self.mini_harita_cerceve.pack_forget()\n"
         "            self._harita_ciz()          # küçük kopya güncel rotayla\n")]),
    ("M2 kucuk harita durum degisiminde cizilmez (ozyineleme yok)", [
        (GUI, "                self._harita_ciz(mini)\n", "                pass\n")]),
    ("M3 arka uc eslemesi bozuk (dshow<->msmf)", [
        (KOPRU, '    "dshow": cv2.CAP_DSHOW,\n    "msmf": cv2.CAP_MSMF,\n',
         '    "dshow": cv2.CAP_MSMF,\n    "msmf": cv2.CAP_DSHOW,\n')]),
    ("M4 indeks kaynaginda cap.set atlanir", [
        (KOPRU, "            if self.kip_istegi:\n"
                "                rapor = cihaz_kipini_uygula(cap, self.kip_istegi)\n",
         "            if False:\n"
         "                rapor = cihaz_kipini_uygula(cap, self.kip_istegi)\n")]),
    ("M5 etiket KAMERA_KANIT kaynagindan duser", [
        (GUI, '                getattr(self, "kamera_etiket", "")),\n', '                ""),\n')]),
    ("M6 sabit 'karar uretmez' notu basliktan duser", [
        (GUI, '    return f"VİDEO KAYNAĞI: {kaynak}   |   {KAMERA_KARAR_NOTU}"\n',
         '    return f"VİDEO KAYNAĞI: {kaynak}"\n')]),
    ("M7 video yok/kopukken hakem onayi kilitlenir", [
        (GUI, "        if not self.rota or self.rota_yok or self.onaylandi:\n            return\n",
         "        if not self.rota or self.rota_yok or self.onaylandi:\n            return\n"
         '        if getattr(self, "kamera_istemci", None) is None or '
         'self.kamera_istemci.snapshot().get("jpeg") is None:\n            return\n')]),
    ("M8 nvargus'a da cap.set uygulanir", [
        (KOPRU, "                           if self.kaynak_turu in KIP_AYARLI_TURLER else {})\n",
         "                           if True else {})\n"),
        (KOPRU, "        if self.kaynak_turu in KIP_AYARLI_TURLER:\n            if self.kip_istegi:\n",
         "        if True:\n            if self.kip_istegi:\n")]),
    ("M9 /durum'a kamera_ayari yazilmaz", [
        (KOPRU, '"kamera_ayari": (None if self.kamera_ayari is None else',
         '"kamera_ayari": (None if True else')]),
    ("M10 kanit bicimi CONTRACTS orneginden ayrisir", [
        (GUI, '    return f"{url} [{etiket}]" if etiket else str(url)\n',
         '    return f"{url} · {etiket}" if etiket else str(url)\n')]),
    ("M11 kip verilmese de set cagrilir (eski davranis bozulur)", [
        (KOPRU, "        self.kip_istegi = ({ad: ayar[ad] for ad, _o in KIP_OZELLIKLERI if ad in ayar}\n",
         '        self.kip_istegi = ({"genislik": 1280, "yukseklik": 720}\n')]),
    ("M12 kucuk haritanin <Configure> baglantisi yok", [
        (GUI, '        self.mini_harita.bind(\n'
              '            "<Configure>", lambda _e: self._harita_ciz(self.mini_harita))\n', "")]),
    ("M13 kamera cercevesi dugmelerin altina degil en sona paketlenir", [
        (GUI, '                **({"after": anahtar} if anahtar is not None else {}))\n',
         "                **{})\n")]),
    ("M14 kamera_govde.pack_propagate(False) yok (genis kare onay panelini daraltir)", [
        (GUI, "        kamera_govde.pack_propagate(False)\n", "")]),
]


def oku(yol):
    ham = yol.read_bytes()
    metin = ham.decode("utf-8")
    return ham, "\r\n" in metin, metin.replace("\r\n", "\n")


def yaz(yol, metin_n, crlf):
    yol.write_bytes((metin_n.replace("\n", "\r\n") if crlf else metin_n).encode("utf-8"))


def kos():
    p = subprocess.run([PY, "-B", "-X", "utf8", "-m", "unittest", "discover",
                        "-s", "tests", "-p", TEST],
                       cwd=KOK, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    cikti = p.stdout + p.stderr
    ran = re.search(r"Ran (\d+) tests?", cikti)
    son = [s for s in cikti.strip().splitlines() if s.strip()][-1]
    dusen = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", cikti, re.M)))
    return p.returncode, (ran.group(1) if ran else "?"), son, dusen


asil = {y: oku(y) for y in DOSYALAR}
sha0 = {y: hashlib.sha256(asil[y][0]).hexdigest() for y in DOSYALAR}
sonuc = []
try:
    for ad, degisiklikler in MUTASYONLAR:
        if degisiklikler is None:
            for y in DOSYALAR:
                rel = y.relative_to(KOK).as_posix()
                y.write_bytes(subprocess.run(
                    ["git", "-C", str(KOK), "show", f"{T226_ONCESI}:{rel}"],
                    capture_output=True, check=True).stdout)
        else:
            gecici = {y: asil[y][2] for y in DOSYALAR}
            for y, eski, yeni in degisiklikler:
                sayi = gecici[y].count(eski)
                if sayi != 1:
                    raise SystemExit(f"{ad}: hedef metin {sayi} kez bulundu ({y.name})")
                gecici[y] = gecici[y].replace(eski, yeni)
            for y in {d[0] for d in degisiklikler}:
                yaz(y, gecici[y], asil[y][1])
        kod, ran, son, dusen = kos()
        yakalandi = kod != 0
        satir = (f"{ad}: cikis={kod} ran={ran} son={son!r} -> "
                 f"{'YAKALANDI' if yakalandi else 'YAKALANMADI'}; dusen={dusen}")
        print(satir, flush=True)
        sonuc.append((ad, yakalandi))
        for y in DOSYALAR:
            y.write_bytes(asil[y][0])
finally:
    for y in DOSYALAR:
        y.write_bytes(asil[y][0])
esit = all(hashlib.sha256(y.read_bytes()).hexdigest() == sha0[y] for y in DOSYALAR)
print("geri yukleme sha esit:", esit,
      " ".join(f"{y.name}={sha0[y][:12]}" for y in DOSYALAR))
print(f"OZET: {sum(1 for _a, y in sonuc if y)}/{len(sonuc)} mutasyon yakalandi")
kod, ran, son, _d = kos()
print(f"TEMIZ KOSUM (mutasyonsuz): cikis={kod} ran={ran} son={son!r}")

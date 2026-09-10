"""T226-D mutasyon koşucusu (D-448) — her mutasyonu `comms/yks_gui.py` ve/veya
`scripts/kamera_koprusu.py`'ye uygular, `tests/test_yks_mk15_hakem_ekrani.py`'yi
koşar, dosyaları BAYT-EŞ geri yükler (sha256 ile doğrulanır).

  M0      T226-D öncesi kod (77853afb = T226, çürütücü RED): yeni kapıların
          özgün kusuru (etiket çakışması, NO_ROUTE bant/uyarı, dönüş sırası,
          cv2 sabiti) yeniden ürettiğinin kanıtı.
  M1–M14  T226'nın mutasyonları (`mutasyon_t226.py`) YENİ kodda yeniden;
          M3 (getattr biçimi) ve M13 (`**yer`) hedefleri T226-D koduna uyarlandı.
  N1–N10  T226-D kilitleri (her yeni kilit için gerçek dosya mutasyonu).

KOSUM (depo kökünden; başka süreç bu dosyaları okurken KOŞMA):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/mutasyon_t226d.py
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
T226D_ONCESI = "77853afb"
GUI = KOK / "comms" / "yks_gui.py"
KOPRU = KOK / "scripts" / "kamera_koprusu.py"
DOSYALAR = (GUI, KOPRU)

MUTASYONLAR = [
    (f"M0 T226-D oncesi yks_gui.py + kamera_koprusu.py ({T226D_ONCESI})", None),
    # ── T226 mutasyonları, yeni kodda ────────────────────────────────────────
    ("M1 pack_forget geri gelir (kucuk harita kamera gorunumunde gizli)", [
        (GUI, "            self._harita_ciz()          # küçük kopya güncel rotayla\n",
         "            self.mini_harita_cerceve.pack_forget()\n"
         "            self._harita_ciz()          # küçük kopya güncel rotayla\n")]),
    ("M2 kucuk harita durum degisiminde cizilmez (ozyineleme yok)", [
        (GUI, "                self._harita_ciz(mini)\n", "                pass\n")]),
    ("M3 arka uc eslemesi bozuk (dshow<->msmf) [T226-D: getattr hedefi]", [
        (KOPRU, '    "dshow": getattr(cv2, "CAP_DSHOW", 700),\n'
                '    "msmf": getattr(cv2, "CAP_MSMF", 1400),\n',
         '    "dshow": getattr(cv2, "CAP_MSMF", 1400),\n'
         '    "msmf": getattr(cv2, "CAP_DSHOW", 700),\n')]),
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
    ("M13 kamera cercevesi dugmelerin altina degil en sona paketlenir [T226-D: **yer]", [
        (GUI, '            self.kamera_cerceve.pack(fill="both", expand=True, **yer)\n',
         '            self.kamera_cerceve.pack(fill="both", expand=True)\n')]),
    ("M14 kamera_govde.pack_propagate(False) yok (genis kare onay panelini daraltir)", [
        (GUI, "        kamera_govde.pack_propagate(False)\n", "")]),
    # ── T226-D kilitleri ─────────────────────────────────────────────────────
    ("N1 kucuk haritada eski '✕ KAPALI' geri gelir (kisaltma yok)", [
        (GUI, "                kapali_etiketi = KAPALI_SERIT_ETIKETI_KISA\n",
         "                pass\n")]),
    ("N2 NO_ROUTE uyari y duzeltmesi geri alinir (uyari bant ustunde kalir)", [
        (GUI, '            y["uyari_y"] = y["bant_h"] + pay\n', "            pass\n")]),
    ("N3 gorunum donus sirasi duzeltmesi geri alinir (harita sona paketlenir)", [
        (GUI, '            self.harita.pack(padx=10, pady=(4, 6), fill="both", expand=True,\n'
              '                             **yer)\n',
         '            self.harita.pack(padx=10, pady=(4, 6), fill="both", expand=True)\n')]),
    ("N4 kamera_koprusu cv2.CAP_DSHOW dogrudan okunur (getattr yok)", [
        (KOPRU, '    "dshow": getattr(cv2, "CAP_DSHOW", 700),\n',
         '    "dshow": cv2.CAP_DSHOW,\n')]),
    ("N5 kucuk harita IKA-KB ofseti ana haritaya sizar", [
        (GUI, '        c.create_text(kx + 12 + S(4) if kucuk else kx + 16, ky, text="İKA-KB",\n',
         '        c.create_text(kx + 12 + S(4), ky, text="İKA-KB",\n')]),
    ("N6 kucuk harita fontu ana haritaya sizar", [
        (GUI, '        f_etiket = self.f_kucuk if olcu is None else olcu["font"]\n',
         '        f_etiket = getattr(self, "f_mini", self.f_kucuk)\n')]),
    ("N7 ref etiketi carpisinca yer degistirmez", [
        (GUI, "            if len(ref_adaylari) > 1:\n"
              "                self._etiket_yerlestir(c, ref, ref_adaylari)\n",
         "            if False:\n"
         "                self._etiket_yerlestir(c, ref, ref_adaylari)\n")]),
    ("N8 ROTA YOK bant yuksekligi metinden olculmez (eski sabit)", [
        (GUI, "                              0 if bant is None else bant[1] + 2 * pay)\n",
         "                              0)\n")]),
    ("N9 renk aciklamasi kucuk haritada eski sabit y (S(52))", [
        (GUI, '                lx, (olcu["aciklama_y"] if kucuk and olcu["aciklama_y"] is not None\n',
         '                lx, (S(HARITA_RENK_ACIKLAMA_Y_PX) if kucuk and olcu["aciklama_y"] is not None\n')]),
    ("N10 sikisik kucuk haritada serit adlari kisalmaz", [
        (GUI, "                    serit_adi_kisa = True\n", "                    pass\n")]),
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
                    ["git", "-C", str(KOK), "show", f"{T226D_ONCESI}:{rel}"],
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

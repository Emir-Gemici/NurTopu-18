"""T214-A mutasyon koşucusu — her mutasyonu kaynağa uygular, `tests/test_sim_mujoco_olcum.py`'yi
koşar, dosyayı BAYT-EŞ geri yükler (sha256 ile doğrulanır). Beklenen: M0 (mutasyonsuz) OK, her
mutasyonda test DÜŞER (yakalandı). Çıktı: bu klasörde `mutasyon_ciktisi.txt`.

KOŞUM (depo kökünden; başka süreç bu kaynakları okurken / GPU koşumu sürerken KOŞMA):
  O:/navitas-local-train/venv/Scripts/python.exe -B results/fdr_sprint_20260910/H1/t214a/mutasyon_t214a.py
"""
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
PY = r"O:/navitas-local-train/venv/Scripts/python.exe"
TEST = "test_sim_mujoco_olcum.py"
GK = "simulation/mujoco/gorev_kosumu.py"
IH = "simulation/scripts/iha_haritala.py"
OO = "simulation/mujoco/on_olcum_k3.py"
SKT = "simulation/mujoco/sim_karar_toplayici.py"
SG = "simulation/mujoco/sim_grafik.py"
RP = "simulation/mujoco/t214a_rapor.py"

MUTASYONLAR = [
    ("M0 mutasyonsuz temel", None, None, None),
    ("M1 basari: temas kosulu yok", GK,
     "                and int(temas_sayisi) == 0 and float(sure_ika) <= SARTNAME_IKA_GOREV_SURESI_S)",
     "                and float(sure_ika) <= SARTNAME_IKA_GOREV_SURESI_S)"),
    ("M2 basari: sure siniri 1 s gevsek", GK,
     "float(sure_ika) <= SARTNAME_IKA_GOREV_SURESI_S)",
     "float(sure_ika) <= SARTNAME_IKA_GOREV_SURESI_S + 1.0)"),
    ("M3 basari: cikis kodu kosulu yok", GK,
     "    return bool(int(kod) == 0 and bool(rota_bulundu)",
     "    return bool(bool(rota_bulundu)"),
    ("M4 takip: temasta kesilmez", GK,
     "        if int(temas_sayisi) > 0:\n            self.temasla_kesildi = True\n            return\n",
     "        if int(temas_sayisi) > 0:\n            self.temasla_kesildi = True\n"),
    ("M5 takip: surus kosulu yok (bekleme/sonrasi da orneklenir)", GK,
     "    if kayit.get(\"t_surus_bas\") is None or kayit.get(\"t_surus_son\") is not None:\n        return False\n",
     ""),
    ("M6 iha_haritala: cikarim MOZ_PX (1024) ile", IH,
     "        mozaik, model, conf, INFER_SIZE)",
     "        mozaik, model, conf, MOZ_PX)"),
    ("M7 iha_haritala: cikarim_boyu sabit 512 (defter okunmaz)", IH,
     "    return int(veri[\"profiles\"][veri[\"default_profile\"]][\"imgsz\"])",
     "    return 512"),
    ("M8 on_olcum_k3: teshis varsayilani MOZ_PX", OO,
     "    imgsz = int(imgsz or ih.INFER_SIZE)",
     "    imgsz = int(imgsz or ih.MOZ_PX)"),
    ("M9 hukum: yanlis yol yayini sayilmaz", SKT,
     "        \"dogru\": bool(orl) and not yanlis,",
     "        \"dogru\": bool(orl),"),
    ("M10 toplayici ozet_hesapla diske yazar (bos kapi)", SKT,
     "    oz[\"tarih\"] = tarih\n    return oz\n",
     "    oz[\"tarih\"] = tarih\n    (out / OZET_ADI).write_text(json.dumps(oz, ensure_ascii=False, indent=1), encoding=\"utf-8\")\n    return oz\n"),
    ("M11 tel_tipi: cagrilan yontem (ilk kosu kusuru)", GK,
     "    if g.get(\"tel_tipi\"):\n        return g[\"tel_tipi\"]\n    return _tel_tipi_hakemden(g.get(\"seq\"), r.get(\"hakem\") or {})\n",
     "    return g.get(\"tel_tipi\") or g.get(\"tip\")\n"),
    ("M12 kosum ozet_hesapla diske yazar (bos kapi)", GK,
     "    return ozet\n\n\ndef ozet_kur(out: Path) -> dict:\n",
     "    (Path(out) / \"ozet_kosum.json\").write_text(json.dumps(ozet), encoding=\"utf-8\")\n    return ozet\n\n\ndef ozet_kur(out: Path) -> dict:\n"),
    ("M13 grafik: gt rengi degisti", SG,
     "RENK = {\"gt\": \"#2a78d6\"",
     "RENK = {\"gt\": \"#2a78d7\""),
    ("M14 rapor: bolum basligi elle degisti", RP,
     "    a(\"## 0. Sonuç tablosu\")",
     "    a(\"## 0. Sonuc tablosu\")"),
]


def kos():
    p = subprocess.run([PY, "-B", "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-p", TEST],
                       cwd=KOK, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
    cikti = p.stdout + p.stderr
    ran = re.search(r"Ran (\d+) tests?", cikti)
    son = cikti.strip().splitlines()[-1] if cikti.strip() else ""
    dusen = re.findall(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", cikti, flags=re.M)
    return p.returncode, (int(ran.group(1)) if ran else None), son, dusen


def main() -> int:
    satirlar = [f"# T214-A mutasyon çıktısı — {time.strftime('%Y-%m-%d %H:%M')} · test {TEST}", ""]
    kacan = 0
    for ad, yol, eski, yeni in MUTASYONLAR:
        t0 = time.perf_counter()
        if yol is None:
            rc, ran, son, dusen = kos()
            beklenen = rc == 0
            durum = "OK (temel geçer)" if beklenen else "TEMEL DÜŞTÜ — mutasyon ölçümü geçersiz"
        else:
            p = KOK / yol
            orijinal = p.read_bytes()
            sha0 = hashlib.sha256(orijinal).hexdigest()
            metin = orijinal.decode("utf-8")
            crlf = "\r\n" in metin
            metin_n = metin.replace("\r\n", "\n")
            n = metin_n.count(eski)
            if n != 1:
                raise SystemExit(f"{ad}: kaynakta {n} eşleşme ({yol}) — mutasyon tanımı bayat")
            mut = metin_n.replace(eski, yeni)
            try:
                p.write_bytes((mut.replace("\n", "\r\n") if crlf else mut).encode("utf-8"))
                rc, ran, son, dusen = kos()
            finally:
                p.write_bytes(orijinal)
            if hashlib.sha256(p.read_bytes()).hexdigest() != sha0:
                raise SystemExit(f"{ad}: GERİ YÜKLEME BAYT-EŞ DEĞİL ({yol})")
            beklenen = rc != 0
            durum = "YAKALANDI (test düştü)" if beklenen else "KAÇTI (test geçti)"
        if not beklenen:
            kacan += 1
        ilk = ", ".join(f"{a} ({b.split('.')[-1]})" for a, b in dusen[:4])
        satirlar.append(f"{ad:<58} → {durum} · Ran {ran} · {son} · {time.perf_counter() - t0:.1f} s"
                        + (f"\n    düşen: {ilk}" if ilk else ""))
        print(satirlar[-1], flush=True)
    satirlar += ["", f"özet: {len(MUTASYONLAR) - 1} mutasyon, kaçan/temel sorunu {kacan}; kaynaklar sha256 ile bayt-eş geri yüklendi"]
    (Path(__file__).resolve().parent / "mutasyon_ciktisi.txt").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print(satirlar[-1])
    return 1 if kacan else 0


if __name__ == "__main__":
    raise SystemExit(main())

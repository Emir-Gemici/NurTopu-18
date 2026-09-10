"""T214-B mutasyon koşucusu — her mutasyonu kaynağa/kanıta uygular, ilgili test dosyasını koşar, dosyayı
BAYT-EŞ geri yükler (sha256 ile doğrulanır). Beklenen: M0 (mutasyonsuz) üç test dosyası OK; her mutasyonda
ilgili test DÜŞER (yakalandı). Çıktı: bu klasörde `mutasyon_ciktisi.txt`.

KOŞUM (depo kökünden; GPU koşumu sürerken KOŞMA — B testi MuJoCo fiziği koşar, render yok):
  O:/navitas-local-train/venv/Scripts/python.exe -B results/fdr_sprint_20260910/H1/t214b/mutasyon_t214b.py
"""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
PY = r"O:/navitas-local-train/venv/Scripts/python.exe"
VID, OLC, ATIF = "test_sim_mujoco_video.py", "test_sim_mujoco_olcum.py", "test_fdr_sarkan_atif_kapisi.py"
GK = "simulation/mujoco/gorev_kosumu.py"
SV = "simulation/mujoco/sim_video.py"
RP = "simulation/mujoco/t214a_rapor.py"
B3 = "FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"
OZ = "results/fdr_sprint_20260910/video/video_ozeti.json"
OK_ = "results/fdr_sprint_20260910/video/OKUBENI.md"


def _sure_80(metin: str) -> str:
    oz = json.loads(metin)
    oz["sure_s"] = 80.0
    return json.dumps(oz, ensure_ascii=False, indent=1)


MUTASYONLAR = [
    ("M0 mutasyonsuz temel", None, None, None, (VID, OLC, ATIF)),
    ("M1 kaydedici: kare bekle SONUNDA da cizilir (ilk kosum kusuru)", GK,
     "            surucu.adimla(k * ts)\n            n -= k\n",
     "            surucu.adimla(k * ts)\n            n -= k\n"
     "            if n <= 0 and float(d.time) + 1e-9 >= self.sonraki_surus:\n"
     "                self.surus_karesi(m, d, saat(), durum())\n                self.sonraki_surus += self.aralik\n", (VID,)),
    ("M2 kaydedici: alt adim eksik (n -= k + 1)", GK, "            n -= k\n", "            n -= k + 1\n", (VID,)),
    ("M3 faz: donus FIRLATMA sayilir", SV, "in (\"tarama\", \"donus\") else", "in (\"tarama\",) else", (VID,)),
    ("M4 plan: yavas oynatmada kare tekrari yok", SV,
     "        while acc >= 1.0 - 1e-9:\n            plan.append(i)", "        if acc >= 1.0 - 1e-9:\n            plan.append(i)", (VID,)),
    ("M5 RED-2: open_route_ack_ika_yks_n eski tanim (tel tipinden bagimsiz)", GK,
     "            \"open_route_ack_ika_yks_n\": sum(tel_tipi(r) == \"OPEN_ROUTE\"\n"
     "                                            and (r.get(\"open_route_ack\") or []) == [\"ika\", \"yks\"] for r in rs),\n",
     "            \"open_route_ack_ika_yks_n\": sum((r.get(\"open_route_ack\") or []) == [\"ika\", \"yks\"] for r in rs),\n",
     (OLC,)),
    ("M6 RED-1: README poses.csv iddiasi eski haline doner", RP,
     "\"Depoda: tüm ölçüm JSON'ları, `detection.json`, `rota.json`, `karar_toplayici.json`. `poses.csv` yalnız \"",
     "\"Depoda: tüm ölçüm JSON'ları, `detection.json`, `rota.json`, `poses.csv`, `karar_toplayici.json`. `poses.csv` yalnız \"",
     (OLC,)),
    ("M7 FDR atif: ika_gorevi eski satira (437) doner", B3, "`:477 ika_gorevi`", "`:437 ika_gorevi`", (ATIF,)),
    ("M8 video_ozeti.json: sure elle 80 s", OZ, _sure_80, None, (VID,)),
    ("M9 OKUBENI.md elle duzenlendi", OK_, "| süre |", "| sure |", (VID,)),
]


def kos(testler):
    toplam_rc, ran_t, sonlar, dusen_t = 0, 0, [], []
    for test in testler:
        p = subprocess.run([PY, "-B", "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-p", test],
                           cwd=KOK, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
        cikti = p.stdout + p.stderr
        ran = re.search(r"Ran (\d+) tests?", cikti)
        ran_t += int(ran.group(1)) if ran else 0
        sonlar.append(f"{test}: {cikti.strip().splitlines()[-1] if cikti.strip() else ''}")
        dusen_t += re.findall(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", cikti, flags=re.M)
        toplam_rc |= p.returncode
    return toplam_rc, ran_t, " · ".join(sonlar), dusen_t


def main() -> int:
    satirlar = [f"# T214-B mutasyon çıktısı — {time.strftime('%Y-%m-%d %H:%M')}", ""]
    kacan = 0
    for ad, yol, eski, yeni, testler in MUTASYONLAR:
        t0 = time.perf_counter()
        if yol is None:
            rc, ran, son, dusen = kos(testler)
            beklenen = rc == 0
            durum = "OK (temel geçer)" if beklenen else "TEMEL DÜŞTÜ — mutasyon ölçümü geçersiz"
        else:
            p = KOK / yol
            orijinal = p.read_bytes()
            sha0 = hashlib.sha256(orijinal).hexdigest()
            metin = orijinal.decode("utf-8")
            crlf = "\r\n" in metin
            metin_n = metin.replace("\r\n", "\n")
            if callable(eski):
                mut = eski(metin_n)
            else:
                n = metin_n.count(eski)
                if n != 1:
                    raise SystemExit(f"{ad}: kaynakta {n} eşleşme ({yol}) — mutasyon tanımı bayat")
                mut = metin_n.replace(eski, yeni)
            try:
                p.write_bytes((mut.replace("\n", "\r\n") if crlf else mut).encode("utf-8"))
                rc, ran, son, dusen = kos(testler)
            finally:
                p.write_bytes(orijinal)
            if hashlib.sha256(p.read_bytes()).hexdigest() != sha0:
                raise SystemExit(f"{ad}: GERİ YÜKLEME BAYT-EŞ DEĞİL ({yol})")
            beklenen = rc != 0
            durum = "YAKALANDI (test düştü)" if beklenen else "KAÇTI (test geçti)"
        if not beklenen:
            kacan += 1
        ilk = ", ".join(f"{a} ({b.split('.')[-2] if '.' in b else b})" for a, b in dusen[:4])
        satirlar.append(f"{ad:<66} → {durum} · Ran {ran} · {son} · {time.perf_counter() - t0:.1f} s"
                        + (f"\n    düşen: {ilk}" if ilk else ""))
        print(satirlar[-1], flush=True)
    satirlar += ["", f"özet: {len(MUTASYONLAR) - 1} mutasyon, kaçan/temel sorunu {kacan}; "
                     "dosyalar sha256 ile bayt-eş geri yüklendi"]
    (Path(__file__).resolve().parent / "mutasyon_ciktisi.txt").write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print(satirlar[-1])
    return 1 if kacan else 0


if __name__ == "__main__":
    raise SystemExit(main())

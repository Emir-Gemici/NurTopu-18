"""T243 kilit mutasyon kontrolu — GERCEK dosyalar, sha256 ile bayt-es geri yukleme."""
import hashlib
import subprocess
import sys
from pathlib import Path

KOK = Path(r"O:\navitas\.claude\worktrees\wf_88f63745-bff-1")
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
FDR = KOK / "FDR" / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"
ON = KOK / "results" / "fdr_sprint_20260910" / "T243" / "ON_KAYIT.md"
RM = KOK / "results" / "fdr_sprint_20260910" / "T243" / "README.md"
TB = KOK / "results" / "fdr_sprint_20260910" / "T243" / "TABLO.md"
PROTO = KOK / "comms" / "protocol.py"
BETIK = KOK / "scripts" / "paket_boyutu_olc.py"

MUTASYONLAR = [
    ("M1 FDR boyut tablosu hucresi 365 -> 366", FDR,
     "| `OPEN_ROUTE` | 125 | 365 |", "| `OPEN_ROUTE` | 125 | 366 |"),
    ("M2 FDR veri hizi hucresi 1722,3 -> 1720,0", FDR,
     "| 1722,3 | 4,996 |", "| 1720,0 | 4,996 |"),
    ("M3 FDR ECC hukmu olumluya cevrildi (cizili + 'dogrulandi')", FDR,
     "**Telsizin ECC ayarı ÖLÇÜLEMEDİ**",
     "~~**Telsizin ECC ayarı ÖLÇÜLEMEDİ**~~ **ECC ayarı doğrulandı**"),
    ("M4 FDR yayin tavani bulgusu silindi (61 -> 61 ifadesi)", FDR,
     "(`saha` 61 → 61, `udp` 50 → 50)", "(kadanstan bagimsiz)"),
    ("M5 ON_KAYIT: ikinci GEVSETILMIS kabul olcutu eklendi", ON,
     "3. Kötü sayı da rapora girer:",
     "2b. Gözden geçirilmiş ölçüt: doluluk en az %90,0 ise risk satırı açılır.\n"
     "3. Kötü sayı da rapora girer:"),
    ("M6 ON_KAYIT: olcut cizilip ES ANLAMLI yeniden yazildi", ON,
     "2. **RAPOR ÖLÇÜTÜ:** Hat doluluk oranı yüzde 80,0 ya da üzeri çıkarsa kırmızı risk satırı açılır.",
     "2. **RAPOR ÖLÇÜTÜ:** ~~Hat doluluk oranı yüzde 80,0 ya da üzeri çıkarsa kırmızı risk satırı açılır.~~ Hat doluluk oranı en az %80,0 ise kırmızı risk satırı açılır."),
    ("M7 README: olcut TEK TILDE ile cizildi", RM,
     "**RAPOR ÖLÇÜTÜ (ON_KAYIT §4 madde 2):** Hat doluluk oranı yüzde 80,0 ya da üzeri çıkarsa kırmızı risk satırı açılır.",
     "**RAPOR ÖLÇÜTÜ (ON_KAYIT §4 madde 2):** ~Hat doluluk oranı yüzde 80,0 ya da üzeri çıkarsa kırmızı risk satırı açılır.~"),
    ("M8 README: <strike> ile ECC hukmu gizlendi", RM,
     "**ECC durumu: ÖLÇÜLEMEDİ**",
     "<strike>**ECC durumu: ÖLÇÜLEMEDİ**</strike>"),
    ("M9 README: ilk kosumun eksikligi beyani silindi", RM,
     "**kötüleştirdi**", "**iyilestirdi**"),
    ("M10 TABLO.md elle duzenlendi (bir bayt degeri)", TB,
     "| `OPEN_ROUTE` | 125 | 365 |", "| `OPEN_ROUTE` | 125 | 999 |"),
    ("M11 protocol.encode ayirici degisti (bosluklu JSON)", PROTO,
     'return (json.dumps(msg, separators=(",", ":"), ensure_ascii=False,',
     'return (json.dumps(msg, separators=(", ", ": "), ensure_ascii=False,'),
    ("M12 protocol HEARTBEAT sozlesmesine alan eklendi", PROTO,
     '"lat", "lon", "gps_fix", "armed", "mod", "pixhawk_canli",',
     '"lat", "lon", "gps_fix", "armed", "mod", "pixhawk_canli", "rssi",'),
    ("M15 SayanLink recv sayaci oldüruldu", BETIK,
     "                self.alinan_bayt += len(veri)",
     "                self.alinan_bayt += 0"),
    ("M16 tepe kovasi maks yerine son kovayi veriyor", BETIK,
     'd["tepe_gonderilen_bayt_s"] = max(tam_kovalar) if tam_kovalar else None',
     'd["tepe_gonderilen_bayt_s"] = tam_kovalar[-1] if tam_kovalar else None'),
    ("M13 betik: duyarlilik carpimi oldüruldu", BETIK,
     "yeni_bayt_s = hat[\"gonderilen_bayt_s\"] + (fark * cerceve) / sure",
     "yeni_bayt_s = hat[\"gonderilen_bayt_s\"]"),
    ("M14 betik: hat yuku yalniz IHA'yi sayiyor (ilk kosumun kusuru geri geldi)",
     BETIK,
     "    bayt = sum(u.gonderilen_bayt for u in uclar.values())",
     "    bayt = uclar[\"iha\"].gonderilen_bayt"),
]


def kos():
    r = subprocess.run(
        [PY, "-X", "utf8", "-B", "-m", "unittest", "discover",
         "-s", "tests", "-p", "test_t243_paket_boyutu.py"],
        cwd=str(KOK), capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    son = [s for s in (r.stdout + r.stderr).splitlines() if s.strip()]
    ozet = son[-1] if son else "?"
    dusen = [s for s in son if s.startswith(("FAIL:", "ERROR:"))]
    return r.returncode, ozet, dusen


def main():
    rc, ozet, _ = kos()
    print(f"TABAN: rc={rc} · {ozet}")
    if rc != 0:
        print("TABAN YESIL DEGIL — mutasyon kontrolu anlamsiz"); return 2
    yakalanan = 0
    for ad, yol, eski, yeni in MUTASYONLAR:
        ham = yol.read_bytes()
        sha = hashlib.sha256(ham).hexdigest()
        metin = ham.decode("utf-8")
        if eski not in metin:
            print(f"  [ATLANDI] {ad} — capa bulunamadi"); continue
        yol.write_bytes(metin.replace(eski, yeni, 1).encode("utf-8"))
        try:
            rc2, ozet2, dusen = kos()
        finally:
            yol.write_bytes(ham)
            assert hashlib.sha256(yol.read_bytes()).hexdigest() == sha, yol
        durum = "YAKALANDI" if rc2 != 0 else "!! KACTI !!"
        yakalanan += rc2 != 0
        kisa = "; ".join(d.split("(")[0].strip() for d in dusen[:4])
        print(f"  [{durum}] {ad} · {ozet2} · {kisa}")
    print(f"SONUC: {yakalanan}/{len(MUTASYONLAR)} mutasyon yakalandi")
    rc3, ozet3, _ = kos()
    print(f"GERI YUKLEME SONRASI: rc={rc3} · {ozet3}")
    return 0 if yakalanan == len(MUTASYONLAR) and rc3 == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

"""T141 — kilidin MUTASYON olcumu. On kayit: `results/t141_on_kayit.md` §2.

Mutasyonlar ON KAYITTA, kilit yazilmadan ONCE listelendi. Her biri icin HEM
yeni T141 icra kilidi HEM de mevcut `test_ika_surus_no_route` kosulur; boylece
yeni kilidin EKLEDIGI deger (belge<->kod bagi) OLCULUR, iddia edilmez.

⚠ M2 hakkinda DURUST NOT: on kayitta "M2 dusmeli" yazmistim. Olcunce
dusmedi ve nedeni kilit degil KOD cikti: `receiver_rota_gecerli` no_route'u
IKI KEZ denetliyor (satir 225 ve 238). Tek denetimi kaldirmak DAVRANISI
DEGISTIRMIYOR, dolayisiyla yakalanmamasi DOGRU. Mutasyon sertlestirildi
(M2': iki denetim de kaldirilir) ve o YAKALANIYOR. Etkisiz mutasyon
tabloda BIRAKILDI — cikarilirsa olcumun kendisi yaniltici olur.

⚠ CRLF: tum dosyalar BAYT duzeyinde yedeklenir ve `finally` ile bayt-es geri
yazilir; satir sonuna hic dokunulmaz (T123'te `\\n` arayan desen mutasyonu hic
uygulamamis ve "dusmedi" gorunmustu).

KOSUM: venv python ile, depo kokunden.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"

NAV = KOK / "simulation" / "scripts" / "ika_nav.py"
KIL = KOK / "JETSON_KILAVUZ.md"
LISTE = KOK / "results" / "t123" / "saha_gunu_kontrol_listesi.md"

CUMLE = ("> **Rota üretilmiyorsa model değiştirilmez; "
         "İKA sürmez ve sebep kaydedilir.**").encode("utf-8")

MUTASYONLAR = [
    ("M1 navigate rota kapisi DEVRE DISI", [
        (NAV, b"        if rota_gecerli is None or rota_gecerli():",
         b"        if True:  # MUTASYON")]),
    ("M2 receiver ilk NO_ROUTE denetimi yok (ETKISIZ)", [
        (NAV, b"    if route is None or no_route is not None:",
         b"    if route is None:  # MUTASYON")]),
    ("M2' HER IKI NO_ROUTE denetimi de yok", [
        (NAV, b"    if route is None or no_route is not None:",
         b"    if route is None:  # MUTASYON"),
        (NAV, b"        current_no_route is None\n",
         b"        True  # MUTASYON\n")]),
    ("M3 belgede (b) YASAK -> SERBEST", [
        (KIL, b"SENARYO (b) rota uretilmiyor          -> GECIS YASAK",
         b"SENARYO (b) rota uretilmiyor          -> GECIS SERBEST")]),
    ("M3b zorunlu CUMLE listeden silindi", [
        (LISTE, CUMLE, b"> (silindi)")]),
]

KILITLER = [
    ("T141 icra kilidi", "test_t141_rota_yoksa_surme.py"),
    ("mevcut kod kilidi", "test_ika_surus_no_route.py"),
]


def kos(desen: str) -> str:
    """-> 'dusen/kosulan'."""
    r = subprocess.run(
        [PY, "-m", "unittest", "discover", "-s", "tests", "-p", desen],
        cwd=str(KOK), capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    cikti = r.stdout + r.stderr
    kosulan = 0
    for satir in cikti.splitlines():
        if satir.startswith("Ran ") and " test" in satir:
            kosulan = int(satir.split()[1])
    if cikti.rstrip().endswith("OK"):
        return f"0/{kosulan}"
    dusen = 0
    for satir in cikti.splitlines():
        if satir.startswith("FAILED"):
            for parca in satir[satir.find("(") + 1:satir.find(")")].split(","):
                dusen += int(parca.split("=")[1])
    return f"{dusen}/{kosulan}"


def tablo(baslik: str) -> None:
    sonuc = [f"{ad:18s} {kos(desen)}" for ad, desen in KILITLER]
    print(f"  {baslik:48s} " + " · ".join(sonuc), flush=True)


def _satir_sonuna_uyarla(icerik: bytes, desen: bytes) -> bytes:
    """Deseni dosyanin KENDI satir sonuna uyarla (LF <-> CRLF).

    🔴 D-370: M2' mutasyonu satir sonu ICEREN bir desen ariyordu ama
    `ika_nav.py` TAMAMEN CRLF'tir (658 CRLF, 0 ciplak LF). Desen 0 KEZ
    eslesiyor ve mutasyon HIC UYGULANMIYORDU.

    Bu betigin KENDI docstring'i tuzagi zaten uyariyordu ("T123'te LF arayan
    desen mutasyonu hic uygulamamis ve 'dusmedi' gorunmustu") — M2' aynen
    ona dustu. Uyari YETMEDI; kod duzeyinde onlem gerekiyordu.

    Doner: dosyada GERCEKTEN bulunan bicim; hicbiri yoksa `desen`.
    """
    if desen in icerik:
        return desen
    crlf = desen.replace(b"\n", b"\r\n")
    if crlf != desen and crlf in icerik:
        return crlf
    lf = desen.replace(b"\r\n", b"\n")
    if lf != desen and lf in icerik:
        return lf
    return desen


def _es_satir_sonu(yeni: bytes, bulunan_desen: bytes) -> bytes:
    """Yerine yazilan metni, bulunan desenin satir sonuna uydur.

    Aksi halde CRLF dosyaya LF sokariz ve dosya KARISIK satir sonlu olur.
    """
    if bulunan_desen.endswith(b"\r\n"):
        return yeni.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return yeni


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    yedek = {p: p.read_bytes() for p in (NAV, KIL, LISTE)}
    uygulanmayan = []          # D-370: exit kodunu belirler
    try:
        print("=" * 92)
        print("POZITIF KONTROL (mutasyon YOK — hepsi gecmeli)")
        tablo("mutasyonsuz")

        print("\nMUTASYONLAR (on kayitta, kilit yazilmadan ONCE listelendi)")
        for ad, adimlar in MUTASYONLAR:
            ham = {d: d.read_bytes() for d, _, _ in adimlar}
            # D-370: desenleri dosyanin KENDI satir sonuna uyarla.
            uyarli = []
            for dosya, eski, yeni in adimlar:
                bulunan = _satir_sonuna_uyarla(ham[dosya], eski)
                uyarli.append((dosya, bulunan, _es_satir_sonu(yeni, bulunan)))
            eksik = [d.name for d, e, _ in uyarli if e not in ham[d]]
            if eksik:
                # 🔴 D-370: UYGULANMAYAN MUTASYON "GECTI" DEGILDIR.
                # Eskiden yalniz yazdirilip `continue` ediliyordu ve betik yine
                # exit 0 donuyordu; cikis kodunu okuyan bir kapi bunu BASARI
                # sanardi. OLCULEMEDI != GECTI — artik exit 1.
                uygulanmayan.append((ad, eksik))
                print(f"  {ad:48s} !! DESEN YOK {eksik} — UYGULANMADI")
                continue
            for dosya, eski, yeni in uyarli:
                dosya.write_bytes(dosya.read_bytes().replace(eski, yeni, 1))
            try:
                tablo(ad)
            finally:
                for dosya, icerik in ham.items():
                    dosya.write_bytes(icerik)

        print("\nGERI ALINDI")
        tablo("mutasyonsuz (geri alma dogrulamasi)")
    finally:
        for p, b in yedek.items():
            p.write_bytes(b)
        es = all(p.read_bytes() == b for p, b in yedek.items())
        print("bayt-es geri alindi:", es)
    if uygulanmayan:
        print()
        print(">> UYGULANMAYAN MUTASYON VAR — OLCUM EKSIK (D-370):")
        for _ad, _eksik in uygulanmayan:
            print(f"   . {_ad}  (desen bulunamayan dosya: {_eksik})")
        print("   Uygulanmayan mutasyon 'dusmedi' DEMEK DEGILDIR; OLCULMEDI.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

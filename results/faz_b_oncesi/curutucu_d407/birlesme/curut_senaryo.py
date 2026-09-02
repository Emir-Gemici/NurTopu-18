"""CURUTUCU senaryolari — repo testinin shim altyapisini (salt okunur import) kullanir.

S1  KIP=sik + KAMERA=http  --kur  : enable/restart listesi, disable YOK, env dosyasi, --kuru satirlari
S2  KIP=udp + KAMERA=http  --kapi : kopru enable+restart dogrulamadan ONCE mi? sira
S3  KAMERA=0 / KAMERA bos  --kur  : navitas-kamera-koprusu disable --now var mi
S4  JETSON_NANO_KURULUM §5.1 yerlesimi (kamera_koprusu.py codes/ altinda) --kuru / --kur
S5  SERVIS_KULLANICI turetimi: SUDO_USER=yunus (sudo -E), USER=root; NAVITAS_KOK / User= / PATH
S6  KIP=sik + KAMERA=http  --kapi : hub + kopru sirasi
S7  --durdur (root shim): disable sirasi TUM_BIRIMLER
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, r"O:\navitas\tests")
import test_faz_b_jetson_baslat as T  # noqa: E402
from test_faz_b_jetson_baslat import (_AnaMakine, _kos, _bolumler, _msys,  # noqa: E402
                                      BEYAN_TAM, KOPRU_URL)


def shim(m, on=None):
    sat = m.shim_satirlari()
    return [s for s in sat if (on is None or s.startswith(on + " "))]


def ham_sirali(m):
    """zaman damgali ham shim satirlari (systemctl + sudo) — sira kaniti"""
    if not m.shim_log.is_file():
        return []
    return [s for s in m.shim_log.read_text(encoding="utf-8", errors="replace").splitlines()
            if " systemctl " in s or " sudo " in s]


def bas(baslik):
    print("\n" + "=" * 78 + "\n" + baslik + "\n" + "=" * 78)


# ---------------------------------------------------------------- S1
bas("S1  KIP=sik + KAMERA=http --kur  (soru 3)")
m = _AnaMakine(sbin=True, kullanici="saha")
try:
    e = m.env(KIP="sik", FOV="78", KAMERA=KOPRU_URL)
    kod, out, err = _kos(m.betik, e, "--kur")
    print("exit:", kod, "| stderr:", err.strip()[:300])
    for s in shim(m, "systemctl"):
        print("  ", s)
    print("--- env dosyasi:")
    print(m.env_dosya.read_text(encoding="utf-8"))
    kod2, out2, err2 = _kos(m.betik, e)
    b = _bolumler(out2)
    print("--- --kuru exit", kod2, "birimler sirasi:", list(b["birimler"]))
    for ad, k in b["birimler"].items():
        print("  ", ad, "::", k)
    # kurulu rpi birimi After= satiri
    rpi = (m.systemd / "navitas-rpi-inference.service").read_text(encoding="utf-8")
    print("--- kurulu rpi [Unit] After/Wants:")
    for s in rpi.splitlines():
        if s.startswith(("After=", "Wants=", "Requires=", "BindsTo=")):
            print("  ", s)
finally:
    m.temizle()

# ---------------------------------------------------------------- S2
bas("S2  KIP=udp + KAMERA=http --kapi  (soru 1: --kapi'da kopru enable+restart; sira)")
m = _AnaMakine(sbin=True, kullanici="saha")
try:
    e = m.env(KIP="udp", **BEYAN_TAM, KAMERA=KOPRU_URL, FAKE_SURE="1")
    kod, out, err = _kos(m.betik, e, "--kapi", timeout=120)
    print("exit:", kod, "| stderr:", err.strip()[:300])
    for s in ham_sirali(m):
        print("  ", s)
    print("--- kapi ciktisi (ozet):")
    for s in out.splitlines():
        if s.startswith(("[GECTI]", "[DUSTU]", "thazirlik", "[KURULDU]", "[YAZILDI]")):
            print("  ", s)
finally:
    m.temizle()

# ---------------------------------------------------------------- S3
bas("S3  koprusuz kipte kopru disable --now  (soru 1)")
for kam in ("0", None, "/dev/video1", "http://192.168.1.42:4747/video"):
    m = _AnaMakine(sbin=True, kullanici="saha")
    try:
        ek = {"KAMERA": kam} if kam is not None else {}
        e = m.env(KIP="udp", **BEYAN_TAM, **ek)
        kod, out, err = _kos(m.betik, e, "--kur")
        dis = [s for s in shim(m, "systemctl") if s.startswith("systemctl disable")]
        en = [s for s in shim(m, "systemctl") if s.startswith("systemctl enable")]
        print(f"KAMERA={kam!r}: exit {kod} | disable: {dis} | enable: {en}")
    finally:
        m.temizle()

# ---------------------------------------------------------------- S4
bas("S4  JETSON_NANO_KURULUM §5.1 yerlesimi: kamera_koprusu.py codes/ altinda (scripts/ degil)")
m = _AnaMakine(sbin=True, kullanici="saha")
try:
    kaynak = m.kok / "scripts" / "kamera_koprusu.py"
    hedef = m.kok / "codes" / "kamera_koprusu.py"
    shutil.move(str(kaynak), str(hedef))
    print("kok/scripts:", sorted(p.name for p in (m.kok / "scripts").iterdir()))
    print("kok/codes  :", sorted(p.name for p in (m.kok / "codes").iterdir()))
    e = m.env(KIP="udp", **BEYAN_TAM, KAMERA=KOPRU_URL)
    kod, out, err = _kos(m.betik, e)
    b = _bolumler(out)
    print("--kuru exit:", kod, "|", b["sonuc"])
    for s in b["makine"]:
        if "kamera_koprusu" in s or s.startswith("[YOK]"):
            print("  ", s)
    kod, out, err = _kos(m.betik, e, "--kur")
    print("--kur exit:", kod, "| stderr:", err.strip()[:400])
    print("systemctl cagrilari:", shim(m, "systemctl"))
    print("env dosyasi var mi:", m.env_dosya.exists())
finally:
    m.temizle()

# ---------------------------------------------------------------- S5
bas("S5  SERVIS_KULLANICI turetimi (soru 5): sudo -E altinda SUDO_USER=yunus, USER=root")
for ek in ({"SUDO_USER": "yunus", "USER": "root", "SHIM_KULLANICI": "yunus"},
           {"USER": "yunus", "SHIM_KULLANICI": "yunus"},
           {"USER": "root", "SHIM_KULLANICI": "root"},       # `sudo su` / `su -` sonrasi (SUDO_USER yok)
           {}):
    m = _AnaMakine(sbin=True, kullanici="saha")
    try:
        e = m.env(KIP="udp", **BEYAN_TAM)
        e.pop("SERVIS_KULLANICI", None)
        e.pop("NAVITAS_KOK", None)     # varsayilan turetilsin
        e.update(ek)
        kod, out, err = _kos(m.betik, e)
        b = _bolumler(out)
        kul = [s for s in b["makine"] if " kullanici " in s]
        print(f"ek={ek}: exit {kod} | NAVITAS_KOK={b['env'].get('NAVITAS_KOK')} | {kul} | "
              f"{b['sonuc']}")
        print("   cogullayici:", b["birimler"].get("navitas-cogullayici"))
    finally:
        m.temizle()

# ---------------------------------------------------------------- S6
bas("S6  KIP=sik + KAMERA=http --kapi: hub + kopru sirasi")
m = _AnaMakine(sbin=True, kullanici="saha")
try:
    e = m.env(KIP="sik", FOV="78", KAMERA=KOPRU_URL, FAKE_SURE="1")
    kod, out, err = _kos(m.betik, e, "--kapi", timeout=120)
    print("exit:", kod, "| stderr:", err.strip()[:300])
    for s in ham_sirali(m):
        print("  ", s)
finally:
    m.temizle()

# ---------------------------------------------------------------- S7
bas("S7  --durdur (root shim): disable sirasi")
m = _AnaMakine(sbin=True, kullanici="saha")
try:
    e = m.env(KIP="sik", FOV="78", KAMERA=KOPRU_URL)
    kod, out, err = _kos(m.betik, e, "--durdur", timeout=60)
    print("exit:", kod, "| stderr:", err.strip()[:300])
    for s in shim(m, "systemctl"):
        print("  ", s)
    print(out)
finally:
    m.temizle()

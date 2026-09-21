"""c9ee27f0 Jetson kurulumu (telemetri kapisi) — PC'den tek komut.
Kullanim:  NAVITAS_SIFRE=... python uygula.py [host]
Sira: beklenen sha kontrolu -> yedek (.yedek_20260919b, varsa ustune YAZMAZ) -> .yeni yukle -> uzakta sha+ast
-> mv -> navitas-rpi-inference MainPID kill (Restart=always) -> 20 s sonra gunluk.
karar_sozlesmesi = Jetson'daki 3bc18e5d + YALNIZ TELEMETRI eki (IKA_IZ_GENISLIGI_M 0.4595 korunur).
Beklenen sha tutmazsa HICBIR SEY yazilmaz."""
import hashlib, json, os, sys, time, paramiko

HOST = sys.argv[1] if len(sys.argv) > 1 else "10.21.8.7"
BURASI = os.path.dirname(os.path.abspath(__file__))
UZAK = "/home/n4vitas/navitas/codes/"
DOSYALAR = [  # (uzak ad, yerel dosya, Jetson'da BEKLENEN mevcut sha onek)
    ("rpi_inference.py", "rpi_inference.py", "6fe5819b"),
    ("karar_sozlesmesi.py", "karar_sozlesmesi_jetson_yeni2.py", "3bc18e5d"),
]
YEDEK_EKI = ".yedek_20260919b"

def sha(b): return hashlib.sha256(b).hexdigest()

yerel = {u: open(os.path.join(BURASI, y), "rb").read() for u, y, _ in DOSYALAR}
assert b"IKA_IZ_GENISLIGI_M = 0.4595" in yerel["karar_sozlesmesi.py"], "olculu IKA_IZ_GENISLIGI_M kayip"
assert b"TELEMETRI_GPS_ASGARI_FIX" in yerel["karar_sozlesmesi.py"], "TELEMETRI eki yok"
assert all(b"\r" not in v for v in yerel.values()), "CRLF var"

c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=os.environ.get("NAVITAS_KULLANICI", "n4vitas"), password=os.environ["NAVITAS_SIFRE"],
          timeout=8, banner_timeout=10, auth_timeout=10, look_for_keys=False, allow_agent=False)

def kos(komut, t=60):
    _, o, e = c.exec_command(komut, timeout=t)
    return o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")

kayit = {"host": HOST, "baslangic": time.strftime("%Y-%m-%d %H:%M:%S"), "adimlar": []}
def adim(ad, cikti):
    print(f"--- {ad}\n{cikti.rstrip()}"); kayit["adimlar"].append({"adim": ad, "cikti": cikti})

# 1) mevcut durum
simdi = {}
for u, _, bek in DOSYALAR:
    s = kos(f"sha256sum {UZAK}{u}").split()
    simdi[u] = s[0] if s else None
adim("mevcut sha", json.dumps(simdi))
for u, _, bek in DOSYALAR:
    if simdi[u] == sha(yerel[u]):
        print(f"{u}: zaten kurulu"); continue
    if not (simdi[u] or "").startswith(bek):
        print(f"DUR: {u} Jetson'da beklenmeyen sha {simdi[u]} (beklenen {bek}...) — elle incele, hicbir sey yazilmadi")
        sys.exit(2)

# 2) yedek (var olan yedegin ustune yazma)
for u, _, _ in DOSYALAR:
    adim(f"yedek {u}", kos(f"cd {UZAK} && if [ -e {u}{YEDEK_EKI} ]; then echo 'yedek zaten var, dokunulmadi'; "
                          f"else cp -p {u} {u}{YEDEK_EKI} && sha256sum {u}{YEDEK_EKI}; fi"))

# 3) .yeni yukle + uzakta dogrula
sf = c.open_sftp()
for u, _, _ in DOSYALAR:
    with sf.open(UZAK + u + ".yeni", "wb") as f: f.write(yerel[u])
sf.close()
for u, _, _ in DOSYALAR:
    out = kos(f"cd {UZAK} && sha256sum {u}.yeni && python3 -c \"import ast,sys; ast.parse(open('{u}.yeni').read()); print('ast OK')\"")
    adim(f"dogrula {u}.yeni", out)
    if sha(yerel[u]) not in out or "ast OK" not in out:
        print("DUR: uzak dogrulama tutmadi; .yeni birakildi, canli dosyaya dokunulmadi"); sys.exit(3)

# 4) yerine koy
for u, _, _ in DOSYALAR:
    adim(f"mv {u}", kos(f"cd {UZAK} && mv {u}.yeni {u} && sha256sum {u}"))

# 5) servis yeniden baslat (Restart=always -> kill yeter; sudo gerekmez, User=n4vitas)
eski = kos("systemctl show -p MainPID --value navitas-rpi-inference").strip()
adim("kill", f"eski MainPID {eski}\n" + kos(f"kill {eski} && echo kill-ok"))
time.sleep(20)
yeni = kos("systemctl show -p MainPID --value navitas-rpi-inference").strip()
adim("yeni MainPID", f"{yeni} (eski {eski}) · " + kos("systemctl is-active navitas-rpi-inference"))
gunluk = kos("journalctl -u navitas-rpi-inference --since '-40s' --no-pager -o cat | tail -n 60", 30)
adim("gunluk (son 40 s)", gunluk)
kayit["sonuc"] = {"yeni_pid_farkli": yeni not in ("", "0", eski), "traceback": "Traceback" in gunluk,
                  "telemetri_satiri": "[TELEMETRI]" in gunluk}
print("SONUC", json.dumps(kayit["sonuc"]))
c.close()
yol = os.path.join(BURASI, f"kurulum_{time.strftime('%Y%m%d_%H%M%S')}.json")
json.dump(kayit, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("kayit:", yol)

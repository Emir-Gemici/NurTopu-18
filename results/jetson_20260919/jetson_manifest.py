"""Jetson kod manifesti: ~/navitas altindaki kod dosyalarinin sha256'si, hangi git kaynagiyla BIREBIR ayni oldugu.
Kullanim: NAVITAS_SIFRE=... python jetson_manifest.py [host]  -> results/jetson_20260919/manifest_<zaman>.json + .md
Kaynaklar: kamera-dayanikli-20260919, tunel-saha-20260918, origin/master (git show ile LF blob)."""
import hashlib, json, os, subprocess, sys, time, paramiko
HOST = sys.argv[1] if len(sys.argv) > 1 else "10.21.8.7"
REFLER = ["kamera-dayanikli-20260919", "tunel-saha-20260918", "origin/master"]
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username="n4vitas", password=os.environ["NAVITAS_SIFRE"], timeout=8, look_for_keys=False, allow_agent=False)
_, o, _ = c.exec_command("cd ~/navitas && for e in py sh json yaml; do find . -type f -name \"*.$e\" -not -path './results/*' -not -path '*/__pycache__/*' -not -path './models/*' -exec sha256sum {} +; done; "
                         "echo ===ENV; cat /etc/navitas.env; echo ===UNIT; for u in /etc/systemd/system/navitas-*.service; do echo \"## $u\"; grep -E '^(ExecStart|User|Restart)' $u; done", timeout=60)
ham = o.read().decode("utf-8", "replace"); c.close()
govde, _, ek = ham.partition("===ENV")
jet = {}
for s in govde.splitlines():
    if "  " in s:
        h, p = s.split("  ", 1); jet[p[2:] if p.startswith("./") else p] = h
_blob = {}
def blob_sha(ref, yol):
    k = (ref, yol)
    if k not in _blob:
        r = subprocess.run(["git", "show", f"{ref}:{yol}"], capture_output=True)
        _blob[k] = hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None
    return _blob[k]
def adaylar(p):
    b = os.path.basename(p)
    return list(dict.fromkeys([p, f"jetson_paket/kod/{b}", f"scripts/{b}", f"comms/{b}", f"codes/{b}"]))
satirlar = []
for p, h in sorted(jet.items()):
    eslesen = [f"{r}:{a}" for r in REFLER for a in adaylar(p) if blob_sha(r, a) == h]
    satirlar.append({"dosya": p, "sha256": h, "eslesen": eslesen})
zaman = time.strftime("%Y%m%d_%H%M%S")
json.dump({"host": HOST, "zaman": zaman, "dosyalar": satirlar, "env_ve_birimler": ek}, open(f"results/jetson_20260919/manifest_{zaman}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
esz = [s for s in satirlar if not s["eslesen"]]
with open(f"results/jetson_20260919/manifest_{zaman}.md", "w", encoding="utf-8") as f:
    f.write(f"# Jetson kod manifesti {zaman} ({HOST})\n\n{len(satirlar)} dosya · eslesmeyen {len(esz)}\n\n| dosya | sha256 (ilk 12) | birebir ayni oldugu kaynak |\n|---|---|---|\n")
    for s in satirlar: f.write(f"| {s['dosya']} | {s['sha256'][:12]} | {', '.join(x.split(':')[0] for x in s['eslesen']) or '**HICBIRI**'} |\n")
    f.write("\n## /etc/navitas.env ve servis birimleri\n\n```\n" + ek.strip() + "\n```\n")
print(f"{len(satirlar)} dosya, kaynagi bilinmeyen {len(esz)}: " + ", ".join(s['dosya'] for s in esz[:15]))
print(f"yazildi: results/jetson_20260919/manifest_{zaman}.md")

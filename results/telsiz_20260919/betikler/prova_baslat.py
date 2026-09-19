"""Saha provasi: COM7 bosalinca SAHA_YKI_BASLAT.cmd'nin yaptigini baslatir (yonlendirici COM7 -> MP 14550 + tunel 14590; YKI --tunel 14590 --fda), loglar results/telsiz_20260919/prova_*."""
import subprocess, time, serial, sys
PY=r"O:\navitas-local-train\venv\Scripts\python.exe"; T=r"O:\navitas\.claude\worktrees\glistening-inventing-sphinx"; R=r"O:\navitas\results\telsiz_20260919"
bas=time.time()
while time.time()-bas<900:
    try: s=serial.Serial("COM7",57600,timeout=0.1); s.close(); break
    except Exception: time.sleep(2)
else: print("15 dk icinde COM7 bosalmadi", flush=True); sys.exit(1)
print(time.strftime("%H:%M:%S"), "COM7 bos -> yonlendirici", flush=True)
subprocess.Popen([PY,"-u","-B","scripts/yer_yonlendirici.py","--port","COM7","--baud","57600","--tunel","127.0.0.1:14590"], cwd=T, stdout=open(R+r"\prova5_yonlendirici.log","w"), stderr=subprocess.STDOUT)
time.sleep(4)
print(time.strftime("%H:%M:%S"), "YKI aciliyor", flush=True)
subprocess.Popen([PY,"-u","-B","comms/yks_gui.py","--tunel","127.0.0.1:14590","--fda","--hakem-log",R+r"\prova5_hakem_log.jsonl"], cwd=T, stdout=open(R+r"\prova5_yki.log","w"), stderr=subprocess.STDOUT, env={**__import__("os").environ,"PYTHONIOENCODING":"utf-8"})
print("hazir: Mission Planner -> UDP 14550 -> Connect", flush=True)

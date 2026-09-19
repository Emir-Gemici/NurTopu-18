"""Jetson'a SSH ile komut kos (paramiko). Kullanim: jetson_ssh.py <host> <komut>
Kullanici NAVITAS_KULLANICI (vars. n4vitas), parola NAVITAS_SIFRE ortam degiskeninden; dosyada parola TUTULMAZ."""
import sys, os, paramiko
host=sys.argv[1]; komut=" ".join(sys.argv[2:])
kul=os.environ.get("NAVITAS_KULLANICI","n4vitas"); sifre=os.environ["NAVITAS_SIFRE"]
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(host, username=kul, password=sifre, timeout=8, banner_timeout=10, auth_timeout=10, look_for_keys=False, allow_agent=False)
_,out,err=c.exec_command(komut, timeout=90)
sys.stdout.write(out.read().decode("utf-8","replace")); e=err.read().decode("utf-8","replace")
if e.strip(): sys.stdout.write("[stderr] "+e)
c.close()

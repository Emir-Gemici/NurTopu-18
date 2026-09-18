"""NEDEN: Iki gercek surec/UDP ile 10 s telemetri kesintisi ve kill/restart.
Yalniz gorunum widget'lari test fiksturudur; protokol, surec kimligi ve YKS
mesaj isleme/yaslandirma uretim kodudur. Jetson/systemd/RF kaniti degildir.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'comms'), str(ROOT/'tests')]
import protocol
from test_yks_operator_guvenligi import _taban_arayuz
out=Path(__file__).resolve().parent
sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(('127.0.0.1',0))
sock.settimeout(0.05)
g=_taban_arayuz()
g.protokol_kilidi=True
children=[]
seen={'tel':set(),'hb':set()}
events=[]
code='''import socket,sys,time
from protocol import heartbeat,encode
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
kind=sys.argv[2]
while True:
    fields=dict(lat=40.9599798,lon=29.133553,gps_fix=6,armed=True,mod="AUTO") if kind=="tel" else {}
    s.sendto(encode(heartbeat("iha",**fields)),("127.0.0.1",int(sys.argv[1])))
    time.sleep(0.1)
'''
def start(kind):
    p=subprocess.Popen([sys.executable,'-B','-c',code,str(sock.getsockname()[1]),kind],cwd=ROOT/'comms',env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    children.append(p)
    return p

def pump(duration):
    end=time.monotonic()+duration
    while time.monotonic()<end:
        try:
            data,adr=sock.recvfrom(65535)
            msg=protocol.decode(data)
            seen['tel' if 'lat' in msg else 'hb'].add(msg['akis'])
            g._mesaj_isle(msg,adr)
        except socket.timeout:
            pass
        g._telemetriyi_yaslandir(time.monotonic())

def event(label):
    r=dict(event=label,tel=dict(g.tel.get('iha',{})),armed=g.arm_acik,
           heartbeat_age=time.monotonic()-g.son_hb.get('iha',0))
    events.append(r)
    print(json.dumps(r,ensure_ascii=False),flush=True)

ok=False
try:
    hb=start('hb')
    tel=start('tel')
    pump(1)
    assert 'lat' in g.tel['iha'] and g.arm_acik is True
    old=set(seen['tel'])
    event('two_streams_PASS')
    tel.kill()
    tel.wait(timeout=3)
    pump(10)
    assert g.tel['iha']=={} and g.arm_acik is None
    assert time.monotonic()-g.son_hb['iha']<0.5
    event('10s_cut_health_alive_telemetry_stale_PASS')
    tel=start('tel')
    pump(1)
    assert 'lat' in g.tel['iha'] and g.arm_acik is True
    assert len(seen['tel']-old)==1
    assert len(seen['hb'])==1
    assert g.protokol_ret_sayaci==0
    event('new_process_seq_restart_recovers_PASS')
    ok=True
finally:
    for p in children:
        if p.poll() is None:
            p.terminate()
            p.wait(timeout=3)
    sock.close()
    (out/'udp_sonuc.json').write_text(json.dumps(dict(passed=ok,events=events),ensure_ascii=False,indent=2))

"""NEDEN: NEW YKI icin Jetson sagligi ve gunluklerini salt okunur SSH ile aktar."""
import argparse
import base64
import getpass
import json
import os
import shlex
import sys
import time
from pathlib import Path

REMOTE_CODE = r'''
import json,pathlib,subprocess,time
out={'mono':time.monotonic(),'boot':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
try: out['health']=json.loads(pathlib.Path('/run/navitas-saglik/durum.json').read_text())
except (OSError,ValueError) as e: out['health_error']=str(e)
units=['navitas-rpi-inference','navitas-kamera-koprusu','navitas-saglik','nvfancontrol','nvpmodel']
out['services']={}
for unit in units:
 r=subprocess.run(['systemctl','show',unit,'-p','ActiveState','-p','SubState','-p','MainPID','-p','NRestarts','-p','Result'],capture_output=True,text=True,timeout=2)
 out['services'][unit]=r.stdout.strip()
cmd=['journalctl','-b','--no-pager','-n','80','-o','json']
for unit in units: cmd+=['-u',unit]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=4)
out['journal']=[]
for line in r.stdout.splitlines():
 try:
  event=json.loads(line)
  allowed=('MESSAGE','__CURSOR','__REALTIME_TIMESTAMP','__MONOTONIC_TIMESTAMP','_BOOT_ID','_SYSTEMD_UNIT','PRIORITY')
  clean={k:event[k] for k in allowed if k in event}
  clean['MESSAGE']=str(clean.get('MESSAGE',''))[:4000]
  out['journal'].append(clean)
 except (ValueError,TypeError): pass
if r.returncode or r.stderr:out['journal_note']=r.stderr[:2000]
out['mono']=time.monotonic()
print(json.dumps(out,allow_nan=False))
'''


def komut():
    code=base64.b64encode(REMOTE_CODE.encode()).decode()
    return '/usr/bin/python3 -c '+shlex.quote('import base64;exec(base64.b64decode('+repr(code)+'))')


def atomik_yaz(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    os.replace(temporary,path)


def main():
    import paramiko
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host',required=True)
    ap.add_argument('--kullanici',default='n4vitas')
    ap.add_argument('--cikti',type=Path,default=Path(__file__).resolve().parents[1]/'results/canli_tani/jetson.json')
    ap.add_argument('--bir-kez',action='store_true')
    args=ap.parse_args()
    password=getpass.getpass('Jetson parolasi (kaydedilmez): ')
    client=None;previous=None;last_event=0;seen=set()
    args.cikti.parent.mkdir(parents=True,exist_ok=True)
    journal=args.cikti.parent/('jetson_tani_'+time.strftime('%Y%m%d_%H%M%S')+'_'+str(os.getpid())+'.jsonl')
    print('NEW salt okunur tani -> '+str(args.cikti),flush=True)
    try:
        with journal.open('x',encoding='utf-8') as log:
            while True:
                try:
                    if client is None:
                        client=paramiko.SSHClient()
                        client.load_system_host_keys(str(Path.home()/'.ssh/known_hosts'))
                        client.connect(args.host,username=args.kullanici,password=password,
                                       look_for_keys=False,allow_agent=False,timeout=6,
                                       auth_timeout=6,banner_timeout=6)
                    _,out,err=client.exec_command(komut(),timeout=20)
                    data=out.read(1024*1024+1);error=err.read(8192)
                    rc=out.channel.recv_exit_status()
                    if len(data)>1024*1024 or rc:
                        raise RuntimeError('Remote read failed: '+str(rc)+' '+error.decode(errors='replace')[:300])
                    remote=json.loads(data)
                    if not isinstance(remote,dict):raise ValueError('Remote snapshot must be object')
                    snapshot=dict(v=1,ok=True,host=args.host,pc_mono=time.monotonic(),
                                  pc_unix=time.time(),remote=remote)
                except Exception as exc:
                    if client is not None:client.close()
                    client=None
                    snapshot=dict(v=1,ok=False,host=args.host,pc_mono=time.monotonic(),
                                  pc_unix=time.time(),error=type(exc).__name__+': '+str(exc)[:400])
                atomik_yaz(args.cikti,snapshot)
                health=(snapshot.get('remote') or {}).get('health') or {}
                state=(snapshot['ok'],health.get('saglikli'),tuple(health.get('nedenler') or []),
                       health.get('boot'),health.get('pid'),snapshot.get('error'))
                if state!=previous or time.monotonic()-last_event>=30:
                    record={k:v for k,v in snapshot.items() if k!='remote'}
                    record.update(olay='JETSON_TANI',health=health,
                                  services=(snapshot.get('remote') or {}).get('services'))
                    log.write(json.dumps(record,ensure_ascii=False)+'\n');log.flush()
                    print(json.dumps(record,ensure_ascii=False),flush=True)
                    previous=state;last_event=time.monotonic()
                for event in (snapshot.get('remote') or {}).get('journal',[]):
                    key=(event.get('_BOOT_ID'),event.get('__CURSOR'))
                    if key[1] and key not in seen:
                        seen.add(key)
                        log.write(json.dumps(dict(olay='JETSON_JOURNAL',pc_unix=time.time(),
                                                  pc_mono=time.monotonic(),veri=event),ensure_ascii=False)+'\n')
                log.flush()
                if len(seen)>5000:
                    seen={(e.get('_BOOT_ID'),e.get('__CURSOR')) for e in (snapshot.get('remote') or {}).get('journal',[])}
                if args.bir_kez:return 0 if snapshot['ok'] else 1
                time.sleep(2)
    except KeyboardInterrupt:
        return 0
    finally:
        if client is not None:client.close()


if __name__=='__main__':
    sys.exit(main())

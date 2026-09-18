"""NEDEN: Gercek ArduCopter SITL ile yerde acilis ve ucus/inis kapisini olc.
Yalniz bu betigin baslattigi instance 10 ve loopback uclari kullanilir.
Jetson, radyo, motor ve fiziksel arac baglantisi yoktur.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from pymavlink import mavutil
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'comms'))
import protocol

binary = Path('/home/trs/projects/navitas_sitl/arducopter')
def free_udp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', 0))
    return s

router, receiver, reserve = free_udp(), free_udp(), free_udp()
port = reserve.getsockname()[1]
reserve.close()
router.setblocking(False)
receiver.setblocking(False)
children = []
logs = []
master = None
state = dict(landed=None, alt=None, armed=False, mode=None, gps=0)
events = []
landed_packets = []
start = time.monotonic()
last_hb = 0

def event(kind, **kw):
    record = dict(t=round(time.monotonic()-start, 3), event=kind, **kw)
    events.append(record)
    print(json.dumps(record, ensure_ascii=False), flush=True)

def pump(seconds=0.1):
    global last_hb
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if time.monotonic() - last_hb > 1:
            master.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
            last_hb = time.monotonic()
        for _ in range(100):
            msg = master.recv_match(blocking=False)
            if msg is None:
                break
            if msg.get_type() == 'BAD_DATA':
                continue
            router.sendto(msg.get_msgbuf(), ('127.0.0.1', port))
            typ = msg.get_type()
            if typ == 'EXTENDED_SYS_STATE':
                if state['landed'] != msg.landed_state:
                    event('landed_state', value=msg.landed_state)
                state['landed'] = msg.landed_state
            elif typ == 'GLOBAL_POSITION_INT':
                state['alt'] = msg.relative_alt / 1000
            elif typ == 'GPS_RAW_INT':
                state['gps'] = msg.fix_type
            elif typ == 'HEARTBEAT' and msg.get_srcSystem() == 1:
                state['armed'] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                state['mode'] = msg.custom_mode
            elif typ == 'STATUSTEXT':
                event('status', text=msg.text)
            elif typ == 'COMMAND_ACK':
                event('command_ack', command=msg.command, result=msg.result)
        while True:
            try:
                data, _ = router.recvfrom(65535)
                master.write(data)
            except BlockingIOError:
                break
        while True:
            try:
                data, adr = receiver.recvfrom(65535)
            except BlockingIOError:
                break
            msg = protocol.decode(data)
            if msg['type'] == 'IHA_LANDED':
                landed_packets.append(msg)
                event('IHA_LANDED', seq=msg['seq'], state=dict(state))
                receiver.sendto(protocol.encode(protocol.ack(msg['seq'], 'ika', ref_tip='IHA_LANDED')), adr)
        time.sleep(0.005)

def wait_for(predicate, timeout, label):
    limit = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > limit:
            raise AssertionError(f'{label}: timeout; {state}')
        pump()
    event(label, state=dict(state))

def launch(cmd, logfile, cwd):
    f = open(OUT / logfile, 'w')
    logs.append(f)
    p = subprocess.Popen(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT,
                         env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    children.append(p)
    return p

ok = False
try:
    with tempfile.TemporaryDirectory(prefix='navitas-onarim18-sitl-') as temp:
        sitl = launch([str(binary), '-S', '--model', '+', '--speedup', '1',
                       '--defaults', '/home/trs/projects/navitas_sitl/copter.parm',
                       '-I10', '--home', '40.9599799,29.1335529,20,0'], 'sitl_firmware.log', temp)
        deadline = time.monotonic() + 20
        while master is None:
            try:
                master = mavutil.mavlink_connection('tcp:127.0.0.1:5860', source_system=255, retries=1)
            except (OSError, ConnectionError):
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.2)
        event('sitl_connected', pid=sitl.pid)
        publisher = launch([sys.executable, '-B', '-u', str(ROOT / 'comms/iha_inis_yayinci.py'),
                            '--mavlink', f'udpin:127.0.0.1:{port}', '--sysid', '1',
                            '--kanit-timeout', '60', '--heartbeat-sure', '0',
                            '--ika', f'127.0.0.1:{receiver.getsockname()[1]}'],
                           'sitl_yayinci.log', ROOT)
        wait_for(lambda: state['landed'] == 1 and state['gps'] >= 3, 45, 'ground_ready')
        pump(8)
        assert not landed_packets and publisher.poll() is None
        event('ground_no_landing_PASS')
        # Yalniz izole SITL parametresi: fiziksel arac ayari degismez.
        master.mav.param_set_send(1, 1, b'ARMING_CHECK', 0, mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
        master.mav.param_set_send(1, 1, b'FS_GCS_ENABLE', 0, mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
        master.set_mode('GUIDED')
        wait_for(lambda: state['mode'] == 4, 10, 'guided')
        for _ in range(15):
            master.arducopter_arm()
            pump(2)
            if state['armed']:
                break
        wait_for(lambda: state['armed'], 1, 'armed')
        master.mav.command_long_send(1, 1, mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 3)
        wait_for(lambda: state['landed'] == 2 and (state['alt'] or 0) > 2, 30, 'airborne')
        assert not landed_packets
        master.set_mode('LAND')
        wait_for(lambda: bool(landed_packets), 40, 'landing_received')
        wait_for(lambda: publisher.poll() is not None, 8, 'publisher_done')
        assert publisher.returncode == 0, publisher.returncode
        assert state['landed'] == 1 and state['alt'] < 1
        ok = True
        event('SITL_PASS', packets=len(landed_packets))
finally:
    for p in reversed(children):
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=5)
    if master is not None:
        master.close()
    for s in (router, receiver):
        s.close()
    for f in logs:
        f.close()
    (OUT / 'sitl_sonuc.json').write_text(json.dumps(dict(passed=ok, events=events), ensure_ascii=False, indent=2))

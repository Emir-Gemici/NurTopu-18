"""NEDEN: Eski/kopuk veri saglikli sayilmamali, arsiv dosyasi arac baglantisi acmamali."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'comms'))
sys.path.insert(0,str(ROOT/'scripts'))
from sistem_gunlugu import snapshot_oku,jetson_ozeti,pixhawk_ozeti,arsiv_oku,filtrele,satir_metni
from jetson_tani_aktar import atomik_yaz,komut


def fresh():
    return dict(v=1,ok=True,pc_mono=100.,pc_unix=1000.,remote=dict(mono=900.,health=dict(
        kontrol_mono=899.9,model_yasi_s=.2,kamera_yasi_s=.1,boot='abc',pid='42',son_kare=55,
        karar_reddi='MASKE_YOK',nedenler=[])))


class HealthTests(unittest.TestCase):
    def test_live_model_with_no_mask_is_not_reported_as_stopped(self):
        state=jetson_ozeti(fresh(),101,1001)
        self.assertEqual('KARE İŞLİYOR',state['model'])
        self.assertEqual('MASKE_YOK',state['karar'])
        self.assertEqual('KARE GELİYOR',state['kamera'])

    def test_collector_stops_old_good_health_turns_stale(self):
        state=jetson_ozeti(fresh(),106,1006)
        self.assertEqual('VERİ BAYAT',state['jetson'])
        self.assertEqual('BİLİNMİYOR',state['model'])
        self.assertIn('kanıtlanmış değil',state['detay'])

    def test_fresh_download_of_dead_watcher_not_healthy(self):
        value=fresh();value['remote']['health']['kontrol_mono']=800
        self.assertEqual('BİLİNMİYOR',jetson_ozeti(value,100,1000)['model'])

    def test_camera_and_model_independent(self):
        value=fresh();value['remote']['health']['model_yasi_s']=10
        state=jetson_ozeti(value,100,1000)
        self.assertEqual('YOK / BAYAT',state['model'])
        self.assertEqual('KARE GELİYOR',state['kamera'])

    def test_frozen_camera_reason_overrides_recent_timestamp(self):
        value=fresh();value['remote']['health']['nedenler']=['KAMERA_BAYAT_VEYA_YOK']
        self.assertEqual('YOK / BAYAT',jetson_ozeti(value,100,1000)['kamera'])

    def test_reboot_future_or_invalid_timestamps_not_live(self):
        for key,value in (('pc_mono',110),('pc_unix',1010),('pc_mono',True),('pc_unix',float('nan'))):
            snapshot=fresh();snapshot[key]=value
            self.assertNotEqual('KARE İŞLİYOR',jetson_ozeti(snapshot,100,1000)['model'])

    def test_error_snapshot_does_not_keep_old_green_model(self):
        value=fresh();value['ok']=False;value['error']='timeout'
        state=jetson_ozeti(value,100,1000)
        self.assertEqual('BAĞLANTI HATASI',state['jetson'])
        self.assertEqual('BİLİNMİYOR',state['model'])

    def test_pixhawk_requires_fresh_hb_and_own_liveness(self):
        for telemetry,age in (({'pixhawk_canli':True},10),({},0),({'pixhawk_canli':False},0)):
            self.assertFalse(pixhawk_ozeti(telemetry,age,3)['canli'])
        self.assertTrue(pixhawk_ozeti({'pixhawk_canli':True},1,3)['canli'])

    def test_stale_pixhawk_hides_old_battery_and_mode(self):
        state=pixhawk_ozeti({'pixhawk_canli':True,'bat':16,'armed':True},4,3,mode='AUTO')
        self.assertIsNone(state['bat']);self.assertIsNone(state['armed'])
        self.assertEqual('—',state['mod'])

    def test_demo_is_explicit(self):
        state=pixhawk_ozeti({'pixhawk_canli':True},0,3,demo=True)
        self.assertIn('gerçek araç değil',state['kaynak'])


class FileTests(unittest.TestCase):
    def test_atomic_snapshot_roundtrip_and_no_temp_left(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'live.json';atomik_yaz(path,fresh())
            self.assertEqual(fresh(),snapshot_oku(path))
            self.assertEqual([path],list(Path(folder).iterdir()))

    def test_invalid_json_and_large_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.json'
            for content in ('[]','{','x'*(1024*1024+1)):
                path.write_text(content)
                with self.assertRaises(ValueError):snapshot_oku(path)

    def test_malformed_remote_nested_types_rejected_before_ui(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.json'
            for remote in ([],{'health':[]},{'health':{'nedenler':True}},{'journal':42}):
                path.write_text(json.dumps({'v':1,'remote':remote}))
                with self.assertRaises(ValueError):snapshot_oku(path)

    def test_human_readable_archive_keeps_source_and_archive_label(self):
        text=satir_metni({'arsiv':True,'kaynak':'Pixhawk','veri':{'mavpackettype':'ERR','Subsys':5}})
        self.assertIn('ARŞİV',text);self.assertIn('Pixhawk',text);self.assertIn('ERR',text)

    def test_archive_bounded_and_malformed_record_visible(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'old.jsonl'
            path.write_text('\n'.join(json.dumps({'n':i,'ok':True}) for i in range(12))+'\nBAD\n',encoding='utf-8')
            result=arsiv_oku(path,limit=5)
            self.assertEqual(5,len(result['rows']));self.assertEqual(1,result['bad'])
            self.assertTrue(all(row['arsiv'] for row in result['rows']))
            self.assertIn('canlı bağlantı',result['note'])
            self.assertEqual('BAD',result['rows'][-1]['veri']['metin'])

    def test_missing_file_cannot_be_interpreted_as_serial_or_udp(self):
        with patch('pymavlink.mavutil.mavlink_connection') as live:
            with self.assertRaises(ValueError):arsiv_oku('udp:127.0.0.1:14550')
            live.assert_not_called()

    def test_empty_archive_and_cancellation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'empty.txt';path.write_text('')
            stop=threading.Event();stop.set()
            result=arsiv_oku(path,stop)
            self.assertEqual([],result['rows']);self.assertTrue(result['cancelled'])

    def test_query_and_source_filter(self):
        rows=[{'kaynak':'Jetson','mesaj':'MASKE_YOK'},{'kaynak':'Pixhawk','mesaj':'Failsafe'}]
        self.assertEqual([rows[1]],filtrele(rows,'failsafe','Pixhawk'))
        self.assertEqual([],filtrele(rows,'failsafe','Jetson'))

    def test_remote_command_is_fixed_read_only_script(self):
        import base64,shlex
        command=shlex.split(komut())
        self.assertEqual(['/usr/bin/python3','-c'],command[:2])
        from jetson_tani_aktar import REMOTE_CODE
        self.assertIn(base64.b64encode(REMOTE_CODE.encode()).decode(),command[2])
        for forbidden in ('systemctl stop','systemctl restart','mavlink_connection','sudo '):
            self.assertNotIn(forbidden,REMOTE_CODE)


if __name__=='__main__':unittest.main()

"""NEDEN: Gercek Tk paneli bayatlikta yesil kalmamali ve bos arsivi canli satirlarla doldurmamali."""
import json
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'comms'))
from sistem_gunlugu_ui import SistemGunlugu


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=tk.Tk();self.root.withdraw()
        self.path=Path(self.tmp.name)/'snapshot.json'
        app=SimpleNamespace(kok=self.root,son_hb={},tel={},mod={},demo=False,
                            hakem_kaydi=SimpleNamespace(yol=Path(self.tmp.name)/'hakem.jsonl'))
        self.panel=SistemGunlugu(app,self.path,3)
        self.panel.win.withdraw()

    def tearDown(self):
        self.panel.kapat();self.root.destroy();self.tmp.cleanup()

    def write(self,age=0):
        value=dict(v=1,ok=True,pc_mono=time.monotonic()-age,pc_unix=time.time()-age,
                   remote=dict(mono=500,health=dict(kontrol_mono=500,model_yasi_s=.1,
                      kamera_yasi_s=.1,nedenler=[],karar_reddi='MASKE_YOK'),journal=[]))
        self.path.write_text(json.dumps(value),encoding='utf-8')
        self.panel.tick()

    def test_real_panel_moves_fresh_to_stale_and_pixhawk_stays_disconnected(self):
        self.write()
        self.assertIn('KARE İŞLİYOR',self.panel.jetson.get())
        self.assertIn('MASKE_YOK',self.panel.jetson.get())
        self.assertIn('BAĞLI DEĞİL',self.panel.pixhawk.get())
        self.write(age=20)
        self.assertIn('VERİ BAYAT',self.panel.jetson.get())
        self.assertNotIn('KARE İŞLİYOR',self.panel.jetson.get())

    def test_empty_archive_does_not_show_live_rows_and_close_idempotent(self):
        self.panel.archive_mode=True;self.panel.archive=[]
        self.assertEqual([],self.panel.visible())
        self.panel.live();self.assertTrue(self.panel.visible())
        self.panel.kapat();self.panel.kapat()

    def test_invalid_file_is_visible_without_destroying_panel(self):
        self.path.write_text('[]')
        self.panel.tick()
        self.assertIn('VERİ YOK',self.panel.jetson.get())
        self.assertIn('bekleniyor',self.panel.footer.get())


if __name__=='__main__':unittest.main()

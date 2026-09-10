"""T226 (D-443 kusur a) — YKS hakem ekranı: VİDEO + ROTA AYNI ANDA; MK15 video
kaynak etiketi; KAMERA_KANIT kaynak = URL [+ etiket]; kamera_koprusu indeks/
aygıt kaynağında çözünürlük/FPS/arka uç.

ÖLÇÜLEN KUSURLAR (D-443, kod haritası `kod-harita`; T226 öncesi `dcf6edcf`):
  a) `comms/yks_gui.py` `gorunum("kamera")` dalı `self.harita.pack_forget()`
     ile şematik haritayı gizliyordu: MK15 videosu açıkken hakem seçilen
     şeridi haritada GÖREMİYORDU (sağ panel açık kalsa da).
  d) `scripts/kamera_koprusu.py --kaynak <indeks>`: çözünürlük/FPS/arka uç
     seçilemiyordu (--genislik/--yukseklik yalnız nvargus borusuna gidiyordu).
     Ölçüldü (10 Eylül, bu PC): web kamerası indeks 0'da sürücü varsayılanı
     640×480 açılıyor; DSHOW ve MSMF ile `set(1280×720)` tuttu.

Kapılar:
  H1  Kamera görünümünde KÜÇÜK harita yerleşik: pack yöneticisi + ata zinciri
      (geri çekilmiş kök); görünür pencerede `winfo_ismapped`, videonun SAĞINDA,
      gerçek boyutla çizilmiş, onay paneli daralmadı. Tam harita görünümü aynı.
  H2  Küçük harita AYNI `_harita_ciz` yolundan: SEMATIK uyarısı, seçili şerit
      (YEŞİL), ROTA YOK bandı; metin kümesi ana haritayla aynı; yeni çizim kodu
      yok (AST: uyarı ve ROTA YOK metni modülde TEK yerde).
  H3  Video başlığı: etiket + SABİT not; boş etiket; doğrulama; CLI bayrağı
      varsayılanı boş, `main()` kurucuya geçirir; geçersiz etiket ekranı açmaz.
  H4  KAMERA_KANIT `kaynak` = URL [+ etiket] (gerçek HakemKaydi); CONTRACTS
      §6.8 örneği kodla bayt-eş.
  H5  Kamera URL'si YOKKEN ve KOPUKKEN (ölü port) OPEN_ROUTE + İKA ACK + iki
      aşamalı onay GERÇEK Tk düğmesiyle (`btn_onay.invoke`) tamamlanır; ACK
      gerçek UDP ile İHA ucuna ULAŞIR — video onay yolunu kilitlemez.
  K1  Köprü indeks kaynağı: cap.set sırası/değerleri (sahte VideoCapture),
      /durum'da sürücü bildirimi; kip verilmezse set ÇAĞRILMAZ (eski davranış);
      sürücü reddi ve istisnası KIRMIZI log + /durum; /dev/videoN = aygıt.
  K2  Arka uç eşlemesi: 4 seçenek ↔ cv2 sabiti, VideoCapture'a apiPreference
      olarak gider; nvargus borusu ve set'siz açılışı DEĞİŞMEDİ; indeks dışı
      kaynakta "auto" dışı arka uç reddedilir.
  K3  CLI: seçenekler, varsayılanlar (None = verilmedi), ret yolları (çıkış 2).
  K4  /durum HTTP (gerçek sunucu, sahte kaynak): kamera_ayari + boyut +
      cozunurluk_eslesti (eşleşen ve eşleşmeyen iki yön).

Mutasyon (elle koşuldu; betik ve ham çıktı results/fdr_sprint_20260910/
H9_MK15/t226/mutasyon_t226.py · mutasyon_ciktisi.txt).

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_yks_mk15_hakem_ekrani.py"
"""

import ast
import contextlib
import gc
import io
import json
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import kamera_koprusu as kk  # noqa: E402
import yks_gui  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import FrameReader, ack, encode, heartbeat  # noqa: E402
from test_yks_hakem_kanit_olaylari import (ROTA, YOK_ROTA, _SahteKamera,  # noqa: E402
                                           _arayuz, _satirlar, _sozlesme_tablosu)

GUI_YOLU = KOK / "comms" / "yks_gui.py"
SOZLESME = KOK / "CONTRACTS.md"
SEQ = ROTA["seq"]
ETIKET = "MK15 · HDMI · yakalama"


def _olu_port():
    """Bağlanıp hemen bırakılan efemer port: dinleyeni yok (kopuk kamera)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _tk_kok(test):
    import tkinter as tk
    try:
        kok = tk.Tk()
    except Exception as exc:               # başsız oturum / ekran yok
        test.skipTest(f"YAPILAMADI: tkinter ekran açamadı: {exc!r}")
    kok.withdraw()
    return kok


def _metinler(tuval):
    return [tuval.itemcget(i, "text") for i in tuval.find_all()
            if tuval.type(i) == "text" and "inset" not in tuval.gettags(i)]


def _dolgulu(tuval, tur, renk):
    return [i for i in tuval.find_all()
            if tuval.type(i) == tur and tuval.itemcget(i, "fill") == renk]


# ── Gerçek kurucu + gerçek Tk + gerçek UDP (efemer) ─────────────────────────
class _GercekEkran(unittest.TestCase):
    def _kur(self, kamera_url=None, etiket=ETIKET):
        self.app = None
        self.kok = _tk_kok(self)
        self.link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        # Sahte İHA/İKA uçları: kaynak kilidi GERÇEK adreslerle çalışır, ACK
        # gerçek UDP ile İHA ucuna döner (5005/5006/5007'ye bind YOK).
        self.iha = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        self.ika = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        gecici = tempfile.TemporaryDirectory()
        self.addCleanup(gecici.cleanup)         # LIFO: söküm SONRASI silinir
        self.addCleanup(self._kapat)
        self.log_yolu = Path(gecici.name) / "hakem_log.jsonl"
        self.app = yks_gui.YksArayuz(
            self.kok, self.link, demo=False,
            ika_peer=("127.0.0.1", self.ika.port),
            iha_peer=("127.0.0.1", self.iha.port),
            kamera_url=kamera_url, kamera_etiket=etiket,
            hakem_log_yolu=self.log_yolu)
        self.hedef = ("127.0.0.1", self.link.port)
        self.kok.update()
        return self.app

    def _kapat(self):
        """Tk'yi ANA iş parçacığında, deterministik sırayla sök.

        NEDEN (ölçüldü, bu dosyanın ilk koşumu): unittest koşan test örneğini
        bırakır; Tk yorumlayıcısına son referansı `_dinle` iş parçacığı ya da
        başka testin iş parçacığında koşan GC bırakırsa süreç
        "Tcl_AsyncDelete: async handler deleted by the wrong thread" ile ÇÖKER
        ve bekleyen `after` işleri "invalid command name ..._tik" basar.
        """
        app, kok = self.app, self.kok
        if kok is not None:
            try:
                for kimlik in kok.tk.splitlist(kok.tk.call("after", "info")):
                    kok.after_cancel(kimlik)
            except Exception:
                pass
        if app is not None:
            istemci = getattr(app, "kamera_istemci", None)
            if istemci is not None:
                istemci.durdur()
            if app.hakem_kaydi is not None:
                app.hakem_kaydi.kapat()
        for uc in (self.link, self.iha, self.ika):
            uc.close()
        for t in threading.enumerate():
            if t is not threading.current_thread() and t.name.endswith("(_dinle)"):
                t.join(timeout=2.0)
        if kok is not None:
            kok.destroy()
        self.app = self.kok = None
        del app, kok
        gc.collect()

    def _pompala(self, kosul, tavan_s=5.0):
        bitis = time.monotonic() + tavan_s
        while time.monotonic() < bitis:
            self.kok.update()
            if kosul():
                return True
            time.sleep(0.02)
        self.kok.update()
        return bool(kosul())

    def _rota_gonder(self, mesaj=None):
        self.iha.send(encode(dict(ROTA) if mesaj is None else mesaj), self.hedef)

    def _hb_gonder(self):
        """Gerçek İHA gibi `karar_yas` taşıyan heartbeat (A2/D-381): alan hiç
        gelmezse tespit TAZE SAYILMAZ ve onay düğmesi kapalı kalır — bu doğru,
        var olan fail-closed davranıştır; video testinin konusu değildir."""
        self._hb_seq = getattr(self, "_hb_seq", 0) + 1
        self.iha.send(encode(heartbeat("iha", seq=self._hb_seq, karar_yas=0.3)),
                      self.hedef)
        hedef_seq = self._hb_seq
        # `_son_heartbeat_seq[node]` = (seq, monotonik alım anı).
        self.assertTrue(self._pompala(
            lambda: getattr(self.app, "_son_heartbeat_seq", {}).get(
                "iha", (None, None))[0] == hedef_seq
            and self.app.karar_yas_rx is not None))

    @staticmethod
    def _al(uc, tavan_s=2.0):
        okuyucu = FrameReader()
        mesajlar = []
        bitis = time.monotonic() + tavan_s
        while time.monotonic() < bitis:
            veri, _adr = uc.recv()
            if veri is None:
                if mesajlar:
                    break
                continue
            mesajlar.extend(okuyucu.feed(veri))
        return mesajlar


class H1_KucukHaritaYerlesimi(_GercekEkran):
    def test_H1_kamera_gorunumunde_kucuk_harita_yerlesik_tam_harita_degismedi(self):
        app = self._kur()
        # Açılış (DEĞİŞMEDİ): tam harita görünür, kamera çerçevesi yok.
        self.assertEqual("harita", app.gorunum_adi)
        self.assertEqual("pack", app.harita.winfo_manager())
        self.assertEqual("", app.kamera_cerceve.winfo_manager())
        app.gorunum("kamera")
        self.kok.update()
        # Küçük harita ve kamera çerçevesine dek BÜTÜN ataları pack'li:
        # biri `pack_forget` ile gizlenirse zincir kopar (D-443 kusurunun biçimi).
        zincir, w = [], app.mini_harita
        while w is not app.kamera_cerceve.master:
            zincir.append((str(w), w.winfo_manager()))
            w = w.master
        self.assertGreaterEqual(len(zincir), 3, zincir)
        self.assertTrue(all(y == "pack" for _ad, y in zincir),
                        f"küçük harita kamera görünümünde gizli: {zincir}")
        # Video ile küçük harita AYNI gövdede; harita SAĞDA, video solda.
        self.assertIs(app.mini_harita_cerceve.master, app.lbl_kamera_img.master)
        self.assertEqual("right", app.mini_harita_cerceve.pack_info()["side"])
        self.assertEqual("left", app.lbl_kamera_img.pack_info()["side"])
        self.assertEqual("pack", app.lbl_kamera_img.winfo_manager())
        # Tam harita kamera görünümünde gizli (eski davranış korunur).
        self.assertEqual("", app.harita.winfo_manager())
        # Harita görünümüne dönüş: tam harita geri, kamera çerçevesi gizli.
        app.gorunum("harita")
        self.kok.update()
        self.assertEqual("pack", app.harita.winfo_manager())
        self.assertEqual("", app.kamera_cerceve.winfo_manager())
        # Tekrar kamera: küçük harita yine görünür (tek seferlik değil).
        app.gorunum("kamera")
        self.kok.update()
        self.assertEqual("pack", app.kamera_cerceve.winfo_manager())
        self.assertEqual("pack", app.mini_harita_cerceve.winfo_manager())
        # Kamera çerçevesi görünüm düğmelerinin HEMEN altında paketlenir.
        slavlar = app.kamera_cerceve.master.pack_slaves()
        self.assertEqual(slavlar.index(app._gorunum_anahtari) + 1,
                         slavlar.index(app.kamera_cerceve))

    def test_H1b_gorunur_pencerede_harita_video_yaninda_cizili_onay_paneli_daralmadi(self):
        app = self._kur()
        self.kok.deiconify()
        self.kok.update()
        self._pompala(lambda: app.p_karar.winfo_width() > 1, 3.0)
        onay_w = app.p_karar.winfo_width()
        app.gorunum("kamera")
        self.assertTrue(self._pompala(
            lambda: app.mini_harita.winfo_ismapped()
            and app.mini_harita.winfo_width() > 1, 5.0))
        for ad in ("mini_harita", "lbl_kamera_img", "lbl_kamera_baslik", "btn_onay",
                   "lbl_karar"):
            self.assertTrue(getattr(app, ad).winfo_ismapped(), f"{ad} görünmüyor")
        video_sag = app.lbl_kamera_img.winfo_rootx() + app.lbl_kamera_img.winfo_width()
        self.assertGreaterEqual(app.mini_harita.winfo_rootx(), video_sag - 1,
                                "küçük harita videonun SAĞINDA değil")
        self.assertEqual(onay_w, app.p_karar.winfo_width(),
                         "kamera görünümü onay panelini daralttı")
        # `<Configure>` ile GERÇEK boyutta çizildi: arena kutusu dejenere değil.
        c = app.mini_harita
        self._pompala(lambda: False, 0.3)
        arena = [c.coords(i) for i in c.find_all()
                 if c.type(i) == "rectangle" and c.itemcget(i, "outline") == yks_gui.CIZGI]
        self.assertTrue(arena)
        x0, y0, x1, y1 = arena[0]
        self.assertGreater(x1 - x0, yks_gui.S(100), f"küçük harita dejenere: {arena[0]}")
        self.assertLessEqual(x1, c.winfo_width())
        self.assertLessEqual(y1, c.winfo_height())
        # Geniş video karesi (1080p ayna) sol paneli büyütüp onay panelini
        # DARALTMAMALI ve küçük haritayı pencere dışına itmemeli
        # (`kamera_govde.pack_propagate(False)`). `update_idletasks` yalnız
        # yerleşimi koşar; `_tik` (resmi silen kamera tazelemesi) koşmaz.
        import tkinter as tk
        buyuk = tk.PhotoImage(master=self.kok, width=yks_gui.S(1920),
                              height=yks_gui.S(1080))
        app.lbl_kamera_img.config(image=buyuk)
        self.kok.update_idletasks()
        try:
            self.assertEqual(onay_w, app.p_karar.winfo_width(),
                             "geniş video karesi onay panelini daralttı")
            self.assertTrue(app.mini_harita.winfo_ismapped())
            self.assertLessEqual(
                app.mini_harita.winfo_rootx() + app.mini_harita.winfo_width(),
                app.p_karar.winfo_rootx(), "küçük harita onay paneline taştı")
        finally:
            app.lbl_kamera_img.config(image="")
            del buyuk                      # Tcl görüntüsü ANA iş parçacığında silinir


class H2_AyniCizimYolu(_GercekEkran):
    def test_H2_kucuk_harita_secili_serit_rota_yok_ve_uyari(self):
        app = self._kur()
        app.gorunum("kamera")
        self.kok.update()
        mini = app.mini_harita
        self.assertIn(yks_gui.SEMATIK_GOSTERIM_UYARISI, _metinler(mini))
        self._rota_gonder()                       # road=2 · orta, gerçek UDP
        self.assertTrue(self._pompala(lambda: app.rota is not None))
        self.assertEqual(1, len(_dolgulu(mini, "rectangle", yks_gui.YESIL)),
                         "seçili şerit küçük haritada YEŞİL değil")
        secili = f"2·{yks_gui.ROAD_LABEL[2].upper()}"
        yesil_metin = [mini.itemcget(i, "text") for i in _dolgulu(mini, "text", yks_gui.YESIL)]
        self.assertIn(secili, yesil_metin)
        self.assertIn(yks_gui.SEMATIK_GOSTERIM_UYARISI, _metinler(mini))
        # Aynı yol: küçük haritanın metin kümesi ana haritanınkiyle birebir.
        self.assertEqual(sorted(_metinler(app.harita)), sorted(_metinler(mini)))
        # NO_ROUTE → ROTA YOK bandı küçük haritada da; yeşil şerit kalmaz.
        self._rota_gonder(dict(YOK_ROTA, seq=SEQ + 1))
        self.assertTrue(self._pompala(lambda: app.rota_yok is not None))
        bant = [m for m in _metinler(mini) if m.startswith("ROTA YOK — ")]
        self.assertEqual(1, len(bant), _metinler(mini))
        self.assertIn(YOK_ROTA["sebep"], bant[0])
        self.assertTrue(_dolgulu(mini, "rectangle", yks_gui.KIRMIZI))
        self.assertEqual([], _dolgulu(mini, "rectangle", yks_gui.YESIL))
        self.assertIn(yks_gui.SEMATIK_GOSTERIM_UYARISI, _metinler(mini))

    def test_H2b_yeni_cizim_kodu_yok(self):
        kaynak = GUI_YOLU.read_text(encoding="utf-8")
        agac = ast.parse(kaynak, filename=str(GUI_YOLU))
        sinif = next(n for n in agac.body
                     if isinstance(n, ast.ClassDef) and n.name == "YksArayuz")
        uyari_yeri, rota_yok_yeri = [], []
        for f in (n for n in sinif.body if isinstance(n, ast.FunctionDef)):
            for c in ast.walk(f):
                if not (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                        and c.func.attr == "create_text"):
                    continue
                metin = next((k.value for k in c.keywords if k.arg == "text"), None)
                if isinstance(metin, ast.Name) and metin.id == "SEMATIK_GOSTERIM_UYARISI":
                    uyari_yeri.append(f.name)
        for f in (n for n in sinif.body if isinstance(n, ast.FunctionDef)):
            for d in ast.walk(f):
                if isinstance(d, ast.JoinedStr) and d.values \
                        and isinstance(d.values[0], ast.Constant) \
                        and str(d.values[0].value).startswith("ROTA YOK — "):
                    rota_yok_yeri.append(f.name)
        self.assertEqual(["_harita_ciz"], uyari_yeri)
        self.assertEqual(["_harita_ciz"], rota_yok_yeri)
        # Küçük harita bu yola TUVALLE bağlıdır (Configure + ana çağrı).
        self.assertIn("self._harita_ciz(self.mini_harita)", kaynak)
        harita = next(n for n in sinif.body
                      if isinstance(n, ast.FunctionDef) and n.name == "_harita_ciz")
        self.assertIn("tuval", [a.arg for a in harita.args.args])
        self.assertIn('"mini_harita"', ast.get_source_segment(kaynak, harita))


class H3_VideoBasligi(unittest.TestCase):
    def test_H3_baslik_etiket_ve_sabit_not(self):
        self.assertEqual("karar üretmez — onay telsiz verisine verilir",
                         yks_gui.KAMERA_KARAR_NOTU)
        m = yks_gui.kamera_baslik_metni(ETIKET)
        self.assertIn(ETIKET, m)
        self.assertIn(yks_gui.KAMERA_KARAR_NOTU, m)
        bos = yks_gui.kamera_baslik_metni("")
        self.assertIn(yks_gui.KAMERA_KARAR_NOTU, bos, "etiket boşken not silinmemeli")
        self.assertNotIn("None", bos)

    def test_H3b_etiket_dogrulama(self):
        d = yks_gui.kamera_etiketi_dogrula
        self.assertEqual(ETIKET, d(f"  {ETIKET}  "))
        self.assertEqual("", d(None))
        self.assertEqual("", d(""))
        sinir = "x" * yks_gui.KAMERA_ETIKETI_AZAMI_KARAKTER
        self.assertEqual(sinir, d(sinir))
        for kotu in ("a\nb", "a\tb", "\x1b[31mX", "a\u2028b", sinir + "x", 15, b"MK15"):
            with self.subTest(kotu=repr(kotu)), self.assertRaises(ValueError):
                d(kotu)

    def test_H3c_kurucu_gecersiz_etiketi_reddeder(self):
        with mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur") as kur, \
                mock.patch.object(yks_gui.YksArayuz, "_tik"), \
                mock.patch.object(yks_gui.threading, "Thread"), \
                self.assertRaises(ValueError):
            yks_gui.YksArayuz(mock.Mock(), mock.Mock(), demo=True,
                              kamera_etiket="a\nb")
        kur.assert_not_called()

    def _add_argument(self, bayrak):
        ana = next(d for d in ast.walk(ast.parse(GUI_YOLU.read_text(encoding="utf-8")))
                   if isinstance(d, ast.FunctionDef) and d.name == "main")
        return ana, next(
            c for c in ast.walk(ana) if isinstance(c, ast.Call)
            and isinstance(c.func, ast.Attribute) and c.func.attr == "add_argument"
            and c.args and isinstance(c.args[0], ast.Constant) and c.args[0].value == bayrak)

    def test_H3d_cli_bayragi_varsayilan_bos_ve_main_kurucuya_gecirir(self):
        ana, cagri = self._add_argument("--kamera-etiket")
        varsayilan = next((k.value for k in cagri.keywords if k.arg == "default"), None)
        self.assertIsInstance(varsayilan, ast.Constant)
        self.assertEqual("", varsayilan.value)
        kurucu = [c for c in ast.walk(ana) if isinstance(c, ast.Call)
                  and isinstance(c.func, ast.Name) and c.func.id == "YksArayuz"]
        self.assertEqual(1, len(kurucu))
        gecen = {k.arg: k.value for k in kurucu[0].keywords}
        self.assertIn("kamera_etiket", gecen)
        self.assertEqual("args.kamera_etiket", ast.unparse(gecen["kamera_etiket"]))

    def test_H3e_gecersiz_etiket_ekrani_acmaz(self):
        sonuc = subprocess.run(
            [sys.executable, "-B", str(GUI_YOLU), "--kamera-etiket",
             "x" * (yks_gui.KAMERA_ETIKETI_AZAMI_KARAKTER + 1)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120, cwd=str(KOK / "comms"))
        self.assertEqual(2, sonuc.returncode, sonuc.stdout + sonuc.stderr)
        self.assertIn("--kamera-etiket", sonuc.stderr)


class H3f_GercekBaslik(_GercekEkran):
    def test_H3f_gercek_ekranda_baslik(self):
        app = self._kur(etiket=f"  {ETIKET} ")
        self.assertEqual(ETIKET, app.kamera_etiket)
        self.assertEqual(yks_gui.kamera_baslik_metni(ETIKET),
                         app.lbl_kamera_baslik.cget("text"))
        self.assertIs(app.lbl_kamera_baslik.master, app.kamera_cerceve)


class H4_KameraKanitKaynagi(unittest.TestCase):
    URL = "http://127.0.0.1:8080/kare.jpg"

    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        self.yol = Path(self._gecici.name) / "hakem_log.jsonl"

    def tearDown(self):
        self._gecici.cleanup()

    def _kamera_kanitlari(self, g):
        g._kamera_tazele()
        g.hakem_kaydi.kapat()
        return [k for k in _satirlar(self.yol) if k["olay"] == "KAMERA_KANIT"]

    def test_H4_etiketli_kaynak_url_ve_etiket(self):
        g = _arayuz(self.yol, kamera_url="http://127.0.0.1:8080")
        g.kamera_istemci = _SahteKamera("CANLI")
        g.kamera_etiket = ETIKET
        kanit = self._kamera_kanitlari(g)
        self.assertEqual(1, len(kanit))
        self.assertEqual(f"{self.URL} [{ETIKET}]", kanit[0]["kaynak"])
        for alan in _sozlesme_tablosu()["KAMERA_KANIT"]:
            self.assertIn(alan, kanit[0])

    def test_H4b_etiketsiz_yalniz_url(self):
        g = _arayuz(self.yol, kamera_url="http://127.0.0.1:8080")
        g.kamera_istemci = _SahteKamera("KARE_BAYAT", hata="bağlantı hatası")
        self.assertFalse(hasattr(g, "kamera_etiket"))   # kurucusuz fikstür
        kanit = self._kamera_kanitlari(g)
        self.assertEqual(self.URL, kanit[0]["kaynak"])

    def test_H4c_url_yokken_kaynak_null_etiket_olsa_da(self):
        g = _arayuz(self.yol)
        g.kamera_etiket = ETIKET
        kanit = self._kamera_kanitlari(g)
        self.assertEqual("YAPILANDIRILMADI", kanit[0]["durum"])
        self.assertIsNone(kanit[0]["kaynak"])

    def test_H4d_saf_bicim(self):
        f = yks_gui.kamera_kanit_kaynagi
        self.assertIsNone(f(None, ETIKET))
        self.assertIsNone(f("", ETIKET))
        self.assertEqual(self.URL, f(self.URL, ""))
        self.assertEqual(f"{self.URL} [{ETIKET}]", f(self.URL, ETIKET))

    def test_H4e_contracts_ornegi_kodla_ayni(self):
        metin = SOZLESME.read_text(encoding="utf-8")
        bas = metin.index("### 6.8 Hakem kanıt kaydının OLAY KÜMESİ")
        son = metin.index("### 6.2 `road` sözleşmesi", bas)
        blok = metin[bas:son]
        self.assertIn("--kamera-etiket", blok)
        self.assertIn("`KAMERA_KANIT.kaynak`", blok)
        ornek = yks_gui.kamera_kanit_kaynagi(self.URL, ETIKET)
        self.assertIn(f'`"{ornek}"`', blok, "CONTRACTS §6.8 örneği kodla ayrıştı")


class H5_VideoOnayiKilitlemez(_GercekEkran):
    """Video karar üretmez: yokluğu/kopukluğu §2.2.3 onay yolunu KİLİTLEMEZ."""

    def _onay_akisi(self):
        app = self.app
        app.gorunum("kamera")
        self._hb_gonder()                              # veri hattı CANLI
        self._rota_gonder()
        self.assertTrue(self._pompala(
            lambda: app.rota is not None and app.rota.get("seq") == SEQ))
        self.ika.send(encode(ack(SEQ, "ika", "OPEN_ROUTE")), self.hedef)
        self.assertTrue(self._pompala(app.ika_aktarim_kaniti_var))
        self._hb_gonder()
        self.assertEqual("normal", str(app.btn_onay.cget("state")),
                         app.btn_onay.cget("text"))
        app.btn_onay.invoke()                          # 1/2 tespit
        self.kok.update()
        self.assertTrue(app.tespit_onayli)
        self._hb_gonder()
        self.assertEqual("normal", str(app.btn_onay.cget("state")),
                         app.btn_onay.cget("text"))
        app.btn_onay.invoke()                          # 2/2 aktarım → ACK
        self.kok.update()
        self.assertTrue(app.onaylandi)
        acklar = [m for m in self._al(self.iha) if m.get("type") == "ACK"]
        self.assertEqual([(SEQ, "yks", "OPEN_ROUTE")],
                         [(m["ref"], m["node"], m.get("ref_tip")) for m in acklar],
                         "hakem ACK'i İHA ucuna ULAŞMADI")
        app.hakem_kaydi.kapat()
        return _satirlar(self.log_yolu)

    def test_H5_kamera_url_yokken_onay_tamamlanir(self):
        self._kur(kamera_url=None)
        satirlar = self._onay_akisi()
        olaylar = [k["olay"] for k in satirlar]
        self.assertIn("HAKEM_ONAYI_2", olaylar)
        self.assertNotIn("HAKEM_ONAYI_REDDI", olaylar)
        kamera = [k for k in satirlar if k["olay"] == "KAMERA_KANIT"]
        self.assertTrue(kamera)
        self.assertEqual("YAPILANDIRILMADI", kamera[0]["durum"])
        self.assertIsNone(kamera[0]["kaynak"])

    def test_H5b_kamera_kopukken_onay_tamamlanir(self):
        olu = _olu_port()
        self._kur(kamera_url=f"http://127.0.0.1:{olu}")
        satirlar = self._onay_akisi()
        self.assertIsNone(self.app.kamera_istemci.snapshot()["jpeg"])
        olaylar = [k["olay"] for k in satirlar]
        self.assertIn("HAKEM_ONAYI_2", olaylar)
        self.assertNotIn("HAKEM_ONAYI_REDDI", olaylar)
        kamera = [k for k in satirlar if k["olay"] == "KAMERA_KANIT"]
        self.assertTrue(kamera)
        self.assertTrue(all(not k["durum"].startswith("CANLI") for k in kamera), kamera)
        self.assertEqual(f"http://127.0.0.1:{olu}/kare.jpg [{ETIKET}]",
                         kamera[-1]["kaynak"])


# ── kamera_koprusu: indeks/aygıt kip ayarı ve arka uç ───────────────────────
class _KipCap:
    """VideoCapture taklidi: set/get çağrılarını kaydeder, değişen kare üretir.

    ``kabul``: set dönüşü · ``gercek``: üretilen karenin (w, h)'si (None =
    sürücünün bildirdiği değer) · ``set_hatasi``: set'te yükseltilecek istisna.
    """

    def __init__(self, arg, api, kabul=True, gercek=None, set_hatasi=None):
        self.arg, self.api = arg, api
        self.kabul, self.gercek, self.set_hatasi = kabul, gercek, set_hatasi
        self.degerler = {cv2.CAP_PROP_FRAME_WIDTH: 640.0,
                         cv2.CAP_PROP_FRAME_HEIGHT: 480.0, cv2.CAP_PROP_FPS: 30.0}
        self.set_cagrilari = []
        self.sayac = 0

    def isOpened(self):
        return True

    def set(self, ozellik, deger):
        self.set_cagrilari.append((ozellik, deger))
        if self.set_hatasi is not None:
            raise self.set_hatasi
        if self.kabul:
            self.degerler[ozellik] = float(deger)
        return self.kabul

    def get(self, ozellik):
        return self.degerler.get(ozellik, 0.0)

    def getBackendName(self):
        return "SAHTE"

    def read(self):
        self.sayac += 1
        w, h = self.gercek or (int(self.get(cv2.CAP_PROP_FRAME_WIDTH)),
                               int(self.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        kare = np.zeros((h, w, 3), np.uint8)
        kare[:, :, 0] = (self.sayac * 7) % 256
        kare[:, :, 2] = 40
        return True, kare

    def release(self):
        pass


class _KopruTaban(unittest.TestCase):
    def _yamala(self, **cap_kw):
        self.capler = []

        def fabrika(arg, api=cv2.CAP_ANY):
            cap = _KipCap(arg, api, **cap_kw)
            self.capler.append(cap)
            return cap

        asil = kk.cv2.VideoCapture
        kk.cv2.VideoCapture = fabrika
        self.addCleanup(setattr, kk.cv2, "VideoCapture", asil)

    def _uretici(self, kaynak="0", **kw):
        self.loglar = []
        return kk.KareUretici(
            kaynak, fps_tavani=0, log_aralik_s=0,
            log=lambda m, kirmizi=False: self.loglar.append((kirmizi, m)), **kw)

    def _ac(self, u):
        cap = u._ac()
        self.assertIsNotNone(cap)
        self.addCleanup(u._guvenli_birak, cap)
        return cap


class K1_IndeksKipAyari(_KopruTaban):
    def test_K1_indeks_kaynaginda_set_sirasi_degerler_ve_durum(self):
        self._yamala()
        u = self._uretici("0", arka_uc="dshow", genislik=1280, yukseklik=720, fps=30)
        cap = self._ac(u)
        self.assertEqual((0, cv2.CAP_DSHOW), (cap.arg, cap.api))
        self.assertEqual([(cv2.CAP_PROP_FRAME_WIDTH, 1280.0),
                          (cv2.CAP_PROP_FRAME_HEIGHT, 720.0),
                          (cv2.CAP_PROP_FPS, 30.0)], cap.set_cagrilari)
        d = u.durum()
        ayar = d["kamera_ayari"]
        self.assertEqual({"genislik": 1280, "yukseklik": 720, "fps": 30}, ayar["istenen"])
        self.assertEqual({"genislik": True, "yukseklik": True, "fps": True},
                         ayar["set_kabul"])
        self.assertEqual({"genislik": 1280.0, "yukseklik": 720.0, "fps": 30.0},
                         ayar["surucu"])
        self.assertIsNone(ayar["hata"])
        self.assertEqual("dshow", d["arka_uc"])
        self.assertEqual("SAHTE", d["arka_uc_adi"])
        self.assertEqual({"genislik": 1280, "yukseklik": 720, "fps": 30}, d["kip_istegi"])
        self.assertIsNone(d["cozunurluk_eslesti"], "kare yokken eşleşme ÖLÇÜLEMEDİ olmalı")
        self.assertFalse([m for k, m in self.loglar if k], self.loglar)
        self.assertTrue(any("kamera kipi: istenen 1280x720@30" in m for _k, m in self.loglar))
        # /durum anlık görüntüsü iç durumu paylaşmaz (JSON'a giden kopya).
        d["kamera_ayari"]["surucu"]["genislik"] = -1
        self.assertEqual(1280.0, u.durum()["kamera_ayari"]["surucu"]["genislik"])

    def test_K1b_kip_verilmezse_set_cagrilmaz_eski_davranis(self):
        self._yamala()
        u = self._uretici("0")
        cap = self._ac(u)
        self.assertEqual([], cap.set_cagrilari)
        self.assertEqual((0, cv2.CAP_ANY), (cap.arg, cap.api))
        d = u.durum()
        self.assertIsNone(d["kamera_ayari"])
        self.assertIsNone(d["kip_istegi"])
        self.assertEqual("auto", d["arka_uc"])

    def test_K1c_surucu_reddi_kirmizi_log_ve_durumda_gorunur(self):
        self._yamala(kabul=False)
        u = self._uretici("1", arka_uc="msmf", genislik=1920, yukseklik=1080)
        self._ac(u)
        ayar = u.durum()["kamera_ayari"]
        self.assertEqual({"genislik": False, "yukseklik": False}, ayar["set_kabul"])
        self.assertEqual({"genislik": 640.0, "yukseklik": 480.0, "fps": 30.0},
                         ayar["surucu"])
        kirmizi = [m for k, m in self.loglar if k]
        self.assertEqual(1, len(kirmizi), self.loglar)
        self.assertIn("UYGULANMADI", kirmizi[0])
        self.assertIn("set REDDEDILDI", kirmizi[0])
        self.assertIn("genislik surucu 640 != istenen 1920", kirmizi[0])
        self.assertTrue(u.kaynak_acik, "kip reddi kaynağı kapatmamalı (akış sürer)")

    def test_K1d_set_istisnasi_kaynagi_oldurmez(self):
        self._yamala(set_hatasi=cv2.error("surucu set desteklemiyor"))
        u = self._uretici("0", genislik=1280)
        self._ac(u)
        ayar = u.durum()["kamera_ayari"]
        self.assertIn("kip ayari istisnasi", ayar["hata"])
        self.assertTrue(u.kaynak_acik)
        self.assertTrue(any(k and "UYGULANMADI" in m for k, m in self.loglar))

    def test_K1e_v4l2_aygit_yolu_cihaz_turu_ve_yalniz_verilen_alan(self):
        self.assertEqual(("/dev/video0", cv2.CAP_V4L2, kk.KAYNAK_TURU_CIHAZ),
                         kk.kaynagi_coz("/dev/video0", arka_uc="v4l2"))
        self.assertEqual(kk.KAYNAK_TURU_DOSYA, kk.kaynagi_coz("/dev/videoX")[2])
        self._yamala()
        u = self._uretici("/dev/video2", arka_uc="v4l2", genislik=800)
        cap = self._ac(u)
        self.assertEqual(("/dev/video2", cv2.CAP_V4L2), (cap.arg, cap.api))
        self.assertEqual([(cv2.CAP_PROP_FRAME_WIDTH, 800.0)], cap.set_cagrilari)


class K2_ArkaUcEslemesi(_KopruTaban):
    BEKLENEN = {"auto": cv2.CAP_ANY, "dshow": cv2.CAP_DSHOW,
                "msmf": cv2.CAP_MSMF, "v4l2": cv2.CAP_V4L2}

    def test_K2_dort_secenek_cv2_sabitine_ve_videocapturea_gider(self):
        self.assertEqual(self.BEKLENEN, kk.ARKA_UC_API)
        self.assertEqual(tuple(self.BEKLENEN), kk.ARKA_UC_SECENEKLERI)
        self.assertEqual(4, len(set(self.BEKLENEN.values())))
        self._yamala()
        for ad, sabit in self.BEKLENEN.items():
            with self.subTest(arka_uc=ad):
                self.assertEqual((3, sabit, kk.KAYNAK_TURU_INDEKS),
                                 kk.kaynagi_coz("3", arka_uc=ad))
                cap = self._ac(self._uretici("3", arka_uc=ad))
                self.assertEqual((3, sabit), (cap.arg, cap.api))

    def test_K2b_nvargus_borusu_ve_setsiz_acilis_degismedi(self):
        self._yamala()
        self.assertEqual(kk.nvargus_boru(), self._uretici("").kaynak_arg)
        self.assertEqual(kk.nvargus_boru(), self._uretici(
            "", genislik=None, yukseklik=None, fps=None, sensor_id=None).kaynak_arg)
        u = self._uretici("", genislik=640, yukseklik=480, fps=15)
        self.assertEqual(kk.nvargus_boru(640, 480, 15), u.kaynak_arg)
        self.assertEqual({}, u.kip_istegi)
        cap = self._ac(u)
        self.assertEqual(cv2.CAP_GSTREAMER, cap.api)
        self.assertEqual([], cap.set_cagrilari, "nvargus'a cap.set UYGULANMAMALI")
        d = u.durum()
        self.assertIsNone(d["kamera_ayari"])
        self.assertIsNone(d["arka_uc_adi"])
        self.assertIsNone(d["kip_istegi"])

    def test_K2c_indeks_disi_kaynakta_auto_disi_arka_uc_reddedilir(self):
        for kaynak in ("", "nvargus", "videotestsrc ! appsink",
                       "http://127.0.0.1:4747/video", "/tmp/x.avi"):
            for ad in ("dshow", "msmf", "v4l2"):
                with self.subTest(kaynak=kaynak, arka_uc=ad), \
                        self.assertRaises(ValueError):
                    kk.kaynagi_coz(kaynak, arka_uc=ad)
        with self.assertRaises(ValueError):
            kk.kaynagi_coz("0", arka_uc="ffmpeg")


class K3_Cli(unittest.TestCase):
    def test_K3_secenekler_varsayilanlar(self):
        eylem = {a.dest: a for a in kk._parser()._actions}
        self.assertEqual(kk.ARKA_UC_SECENEKLERI, tuple(eylem["arka_uc"].choices))
        self.assertEqual("auto", eylem["arka_uc"].default)
        for ad in ("genislik", "yukseklik", "kamera_fps"):
            self.assertIsNone(eylem[ad].default, f"{ad}: None = verilmedi olmalı")
        a = kk._parser().parse_args(["--kaynak", "0", "--arka-uc", "msmf",
                                     "--genislik", "1920", "--yukseklik", "1080",
                                     "--kamera-fps", "30"])
        self.assertEqual(("msmf", 1920, 1080, 30),
                         (a.arka_uc, a.genislik, a.yukseklik, a.kamera_fps))

    def test_K3b_ret_yollari_cikis_2(self):
        for argv, beklenen in (
                (["--kaynak", "x.avi", "--arka-uc", "dshow"], "--arka-uc"),
                (["--kaynak", "nvargus", "--arka-uc", "v4l2"], "--arka-uc"),
                (["--kaynak", "0", "--genislik", "0"], "pozitif"),
                (["--kaynak", "0", "--kamera-fps", "-5"], "pozitif"),
                (["--kaynak", "0", "--arka-uc", "ffmpeg"], "--arka-uc")):
            with self.subTest(argv=argv):
                hata = io.StringIO()
                with contextlib.redirect_stderr(hata), \
                        self.assertRaises(SystemExit) as cm:
                    kk.main(argv + ["--port", "0"])
                self.assertEqual(2, cm.exception.code)
                self.assertIn(beklenen, hata.getvalue())


class K4_DurumHttp(_KopruTaban):
    def _durum(self, port):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/durum", timeout=3) as r:
            return json.loads(r.read().decode("utf-8"))

    def _kopru(self, **cap_kw):
        self._yamala(**cap_kw)
        sunucu, u = kk.kopru_kur("0", port=0, fps_tavani=20, log_aralik_s=0,
                                 log=lambda *_a, **_k: None, arka_uc="msmf",
                                 genislik=64, yukseklik=48, fps=15)
        iplik = threading.Thread(target=sunucu.serve_forever,
                                 kwargs={"poll_interval": 0.05}, daemon=True)
        iplik.start()
        self.addCleanup(kk.kopru_kapat, sunucu, u)
        port = sunucu.server_address[1]
        bitis = time.monotonic() + 5.0
        while time.monotonic() < bitis and self._durum(port)["kare_sayaci"] < 2:
            time.sleep(0.05)
        return self._durum(port)

    def test_K4_durum_http_eslesen_kip(self):
        d = self._kopru()
        self.assertTrue(d["kaynak_acik"])
        self.assertEqual([64, 48], d["boyut"])
        self.assertEqual({"genislik": 64.0, "yukseklik": 48.0, "fps": 15.0},
                         d["kamera_ayari"]["surucu"])
        self.assertIs(True, d["cozunurluk_eslesti"])
        self.assertEqual(("msmf", "SAHTE"), (d["arka_uc"], d["arka_uc_adi"]))

    def test_K4b_durum_http_surucu_bildirimi_ile_gercek_kare_ayristi(self):
        d = self._kopru(gercek=(32, 24))
        self.assertEqual([32, 24], d["boyut"])
        self.assertEqual(64.0, d["kamera_ayari"]["surucu"]["genislik"])
        self.assertIs(False, d["cozunurluk_eslesti"],
                      "sürücü 64x48 dese de gerçek kare 32x24: eşleşme YOK")


if __name__ == "__main__":
    unittest.main()

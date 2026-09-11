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

T226-D (D-448; çürütücü RED 77853afb — küçük haritada etiketler üst üste):
  H2c  GÖRÜNÜR pencere, gerçek Tk, OLCEK 1,0 ve 1,5 (tk scaling = OLCEK×96/72):
       kamera görünümünde KÜÇÜK haritanın metin kutuları ikişer ikişer
       kesişmez (istisna yalnız H ↔ HB (hedef)) ve tuvalden taşmaz — boşta,
       road 1/2/3 OPEN_ROUTE, NO_ROUTE (kısa + uzun detay); beklenen metinler
       yerinde, kapalı şerit etiketi kendi şeridinde; ROTA YOK'ta bant metni
       bandın İÇİNDE, SEMATİK uyarısı bandın ALTINDA; ana haritada (inset
       dahil) aynı kesişmezlik.
  H2d  ANA harita OPEN_ROUTE (road 1/2/3, ANKOR YOK) ve boşta: çağrı listesi
       master (362197e0) ile BAYT-EŞ — 20 senaryo, tests/artifacts/t226d/.
  H6   Görünüm dönüşü: harita → kamera → harita (ve algı; model yüklenmez)
       sonrası harita çerçevesinin paket sırası, winfo_y, yüksekliği ve pack
       seçenekleri ilk açılıştakiyle aynı.
  K5   kamera_koprusu: cv2'de CAP_DSHOW/CAP_MSMF/CAP_V4L2 yoksa import
       düşmez (yedek 700/1400/200); varsa cv2'nin değeri kullanılır.

Mutasyon (elle koşuldu; betik ve ham çıktı results/fdr_sprint_20260910/
H9_MK15/t226/mutasyon_t226.py · mutasyon_ciktisi.txt). T226-D: mutasyon_t226d.py
(eski M1–M14 yeni koda uyarlanarak YENİDEN + N1–N9; aynı çıktı dosyasına eklendi).

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_yks_mk15_hakem_ekrani.py"
"""

import ast
import contextlib
import gc
import hashlib
import importlib.util
import io
import json
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
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


def _kisalt(metin):
    """T226-D küçük harita kısaltmaları: "✕ KAPALI" → "✕", "2·ORTA" → "2"."""
    if metin == yks_gui.KAPALI_SERIT_ETIKETI:
        return yks_gui.KAPALI_SERIT_ETIKETI_KISA
    for yol, ad in yks_gui.ROAD_LABEL.items():
        if metin == f"{yol}·{ad.upper()}":
            return str(yol)
    return metin


def _dolgulu(tuval, tur, renk):
    return [i for i in tuval.find_all()
            if tuval.type(i) == tur and tuval.itemcget(i, "fill") == renk]


# ── Gerçek kurucu + gerçek Tk + gerçek UDP (efemer) ─────────────────────────
class _GercekEkran(unittest.TestCase):
    def _kur(self, kamera_url=None, etiket=ETIKET, olcek=None):
        self.app = None
        self.kok = _tk_kok(self)
        if olcek is not None:
            # T226-D: main()'in DPI ölçeği (OLCEK) + Tk font pikseli (scaling);
            # fontlar `_arayuz_kur`da (kurucuda) bu ölçekle oluşur.
            self.kok.tk.call("tk", "scaling", olcek * 96.0 / 72.0)
            yama = mock.patch.object(yks_gui, "OLCEK", olcek)
            yama.start()
            self.addCleanup(yama.stop)          # LIFO: söküm SONRASI
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

    def _mesaj_ver(self, mesaj):
        """OPEN_ROUTE/NO_ROUTE'u gerçek UDP ile ver; ekran o seq'i işleyene dek
        bekle (H2c, H2e)."""
        self._rota_gonder(mesaj)
        alan = "rota" if mesaj["type"] == "OPEN_ROUTE" else "rota_yok"
        self.assertTrue(self._pompala(
            lambda: (getattr(self.app, alan) or {}).get("seq") == mesaj["seq"]),
            mesaj)
        self._pompala(lambda: False, 0.15)

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
        # H2c ile aynı DPI sözleşmesi: Tk font ölçeği ve ürün geometrisi
        # birlikte kurulur; işletim sisteminin örtük ölçeğine dayanılmaz.
        app = self._kur(olcek=1.0)
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

        def arena_kutulari():
            return [c.coords(i) for i in c.find_all()
                    if c.type(i) == "rectangle"
                    and c.itemcget(i, "outline") == yks_gui.CIZGI]

        def arena_hazir():
            kutular = arena_kutulari()
            return bool(kutular and c.winfo_height() > 1
                        and kutular[0][2] - kutular[0][0] > yks_gui.S(100))

        # Sabit 0,3 s uyku yerine Configure olayının gerçek sonucunu bekle.
        # Çizimi elle çağırma: ürün bağı koparsa bu kapı hâlâ düşmelidir.
        self.assertTrue(self._pompala(arena_hazir, 5.0),
                        f"küçük harita yerleşmedi: arena={arena_kutulari()}, "
                        f"tuval={c.winfo_width()}x{c.winfo_height()}, "
                        f"pencere={self.kok.geometry()}, "
                        f"tk_scaling={self.kok.tk.call('tk', 'scaling')}, "
                        f"font={app.f_mini.metrics()}")
        arena = arena_kutulari()
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
        # T226-D: sıkışık/henüz yerleşmemiş küçük haritada ad numaraya kısalır.
        self.assertIn(_kisalt(secili), [_kisalt(t) for t in yesil_metin])
        self.assertIn(yks_gui.SEMATIK_GOSTERIM_UYARISI, _metinler(mini))
        # Aynı yol: küçük haritanın metin kümesi ana haritanınkiyle birebir —
        # T226-D (D-448): kapalı şerit etiketi küçük haritada şeride SIĞMAZSA
        # "✕"e kısalır (belgelenmiş tek fark; iki yan da aynı eşlemeden geçer).
        # Sıkışık küçük haritada şerit adı yalnız NUMARAYA kısalabilir (T226-D).
        self.assertEqual(sorted(_kisalt(t) for t in _metinler(app.harita)),
                         sorted(_kisalt(t) for t in _metinler(mini)))
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


# ── T226-D (D-448): küçük harita etiket yerleşimi · ROTA YOK bant/uyarı ─────
H_HB_ISTISNASI = frozenset(("H", "HB (hedef)"))
UZUN_DETAY = ("koridor genişlik tavanı aşıldı · şerit 1 moloz · şerit 3 kapalı"
              " · costmap güvenli rota üretmedi · İKA başlangıçta bekler")


def _metin_kutulari(tuval):
    """Gerçek Tk'nin çizdiği METİN öğeleri: ``(metin, bbox, etiketler)``."""
    return [(tuval.itemcget(i, "text"), tuple(tuval.bbox(i)), tuval.gettags(i))
            for i in tuval.find_all()
            if tuval.type(i) == "text" and tuval.itemcget(i, "text")]


def _kesisen_ciftler(kutular):
    """Kutuları KESİŞEN (alanı > 0) metin çiftleri; tek istisna H ↔ HB (hedef)
    (T226 öncesinden ana haritada da var olan, H kutusunun kendi etiketi)."""
    ciftler = []
    for i, (ta, ba, _e) in enumerate(kutular):
        for tb, bb, _f in kutular[i + 1:]:
            if frozenset((ta, tb)) == H_HB_ISTISNASI:
                continue
            if ba[0] < bb[2] and bb[0] < ba[2] and ba[1] < bb[3] and bb[1] < ba[3]:
                ciftler.append((ta, ba, tb, bb))
    return ciftler


def _tasanlar(tuval, kutular):
    w, h = tuval.winfo_width(), tuval.winfo_height()
    return [(t, b) for t, b, _e in kutular
            if b[0] < 0 or b[1] < 0 or b[2] > w or b[3] > h]


class H2c_EtiketCakismasi(_GercekEkran):
    """T226-D (D-448) — GÖRÜNÜR pencere, gerçek Tk, gerçek UDP.

    ÇÜRÜTÜCÜ RED (77853afb, ölçüldü): 450×495 küçük haritada şerit 1/3
    seçiliyken "✕ KAPALI" yazıları üst üste ("✕ KAPA✕ KAPALI"); İKA-KB ↔
    "2·ORTA"/"3·SAG", ref ↔ İKA-KB, renk açıklaması ↔ HB (hedef) de kesişik;
    NO_ROUTE'ta bant metni ↔ SEMATİK uyarısı iki haritada da üst üste.
    Kapı: kamera görünümünde KÜÇÜK haritanın bütün metin kutuları ikişer
    ikişer kesişmez (istisna yalnız H ↔ HB (hedef)) ve tuvalden taşmaz —
    boşta, road 1/2/3 OPEN_ROUTE, NO_ROUTE (kısa + uzun detay); ROTA YOK'ta
    bant metni bandın İÇİNDE, uyarı bandın ALTINDA; ANA haritada (inset
    dahil) aynısı. Ölçek: `tk scaling` = OLCEK × 96/72 — main()'in DPI-duyarlı
    süreci (bu PC 144 DPI → OLCEK 1,5, scaling ≈ 2,0) DPI-duyarsız test
    sürecinde de kurulur; RED 1,5'te ölçülmüştü.
    """

    def _olcekli_kur(self, olcek):
        app = self._kur(olcek=olcek)
        self.kok.deiconify()
        # Gerçek akış: ekran HARİTA görünümünde açılır, sonra kameraya geçilir
        # (ana haritanın <Configure> bağı yok — bkz. rapor, açık kalem).
        self.assertTrue(self._pompala(
            lambda: app.harita.winfo_ismapped() and app.harita.winfo_height() > 1,
            5.0))
        self._pompala(lambda: False, 0.2)
        app.gorunum("kamera")
        self.assertTrue(self._pompala(
            lambda: app.mini_harita.winfo_ismapped()
            and app.mini_harita.winfo_width() > 1, 5.0))
        self._pompala(lambda: False, 0.3)
        return app

    def _bant_denetle(self, c, ad):
        bantlar = _dolgulu(c, "rectangle", yks_gui.KIRMIZI)
        self.assertEqual(1, len(bantlar), f"{ad}: ROTA YOK bandı yok/çok")
        _bx0, by0, _bx1, by1 = c.coords(bantlar[0])
        yazi = [i for i in c.find_all() if c.type(i) == "text"
                and c.itemcget(i, "text").startswith("ROTA YOK — ")]
        self.assertEqual(1, len(yazi), ad)
        _tx0, ty0, _tx1, ty1 = c.bbox(yazi[0])
        self.assertGreaterEqual(ty0, by0, f"{ad}: bant metni bandın ÜSTÜNE taştı")
        self.assertLessEqual(ty1, by1, f"{ad}: bant metni bandın ALTINA taştı "
                                       f"({ty1} > {by1})")
        uyari = [i for i in c.find_all() if c.type(i) == "text"
                 and c.itemcget(i, "text") == yks_gui.SEMATIK_GOSTERIM_UYARISI]
        self.assertEqual(1, len(uyari), ad)
        self.assertGreaterEqual(c.bbox(uyari[0])[1], by1,
                                f"{ad}: SEMATİK uyarısı bandın ALTINDA değil")

    def _mini_denetle(self, ad, mesaj):
        c = self.app.mini_harita
        boyut = f"{c.winfo_width()}x{c.winfo_height()}"
        kutular = _metin_kutulari(c)
        metinler = [t for t, _b, _e in kutular]
        acik = mesaj is not None and mesaj["type"] == "OPEN_ROUTE"
        # Çakışma etiket SİLİNEREK "çözülemez": beklenen metinler yerinde.
        beklenen = {yks_gui.SEMATIK_GOSTERIM_UYARISI, "İKA-KB", "H", "HB (hedef)"}
        if acik:
            beklenen |= {yks_gui.RENK_ACIKLAMASI, "ref"}
        self.assertLessEqual(beklenen, set(metinler), f"{ad} {boyut}: {metinler}")
        # Şerit adları: tam ("2·ORTA") ya da sıkışık tuvalde yalnız numara ("2").
        self.assertEqual(sorted(str(y) for y in yks_gui.ROAD_LABEL),
                         sorted(_kisalt(t) for t in metinler
                                if _kisalt(t) in {str(y) for y in yks_gui.ROAD_LABEL}),
                         f"{ad} {boyut}: {metinler}")
        if acik:
            kapali = [b for t, b, _e in kutular
                      if t in (yks_gui.KAPALI_SERIT_ETIKETI,
                               yks_gui.KAPALI_SERIT_ETIKETI_KISA)]
            self.assertEqual(2, len(kapali), f"{ad}: kapalı şerit etiketleri {kapali}")
            # Her kapalı şeridin etiketi KENDİ şeridinin yatay sınırı içinde.
            for yol, (xm, yg, _giris, _cikis) in yks_gui.SERIT_CIZIM_TABLOSU.items():
                if yol == mesaj["road"]:
                    continue
                sx0 = self.app._mxy(xm - yg, 0, c)[0]
                sx1 = self.app._mxy(xm + yg, 0, c)[0]
                self.assertTrue(
                    any(sx0 <= b[0] and b[2] <= sx1 for b in kapali),
                    f"{ad}: şerit {yol} ({sx0:.0f}..{sx1:.0f}) etiketsiz: {kapali}")
        self.assertEqual([], _kesisen_ciftler(kutular), f"{ad} {boyut}")
        self.assertEqual([], _tasanlar(c, kutular), f"{ad} {boyut}")
        # T226-D2 (çürütücü O6): küçük haritada "HB (hedef)" H kutusunun
        # ÜSTÜNDE durur — kutunun Tk bbox'ının (2 px çizgi dahil) üst kenarını
        # KESMEZ. H ↔ HB metin istisnası bu kuralı delmez. Ölçüldü (T226-D2
        # tasarım ölçümü): 1,0'da 1 px, 1,5'te 2 px boşluk; eski yerleşim
        # (hy-20, merkez çapa) 1,5'te HB'yi kutunun üst kenarına indiriyordu.
        hkutu = self._h_kutusu(c)
        hb = [b for t, b, _e in kutular if t == "HB (hedef)"]
        self.assertEqual(1, len(hb), f"{ad}: HB etiketi {hb}")
        self.assertLessEqual(hb[0][3], hkutu[1],
                             f"{ad} {boyut}: HB {hb[0]} H kutusunun {hkutu} "
                             "üst kenarını kesiyor")
        if mesaj is not None and mesaj["type"] == "NO_ROUTE":
            self._bant_denetle(c, f"küçük {ad}")

    def _h_kutusu(self, c):
        """H kutusunun Tk bbox'ı: "H" metninin merkezinde, KIRMIZI çerçeveli,
        dolgusuz TEK dikdörtgen (kapalı şerit/bant/arena dolguludur)."""
        h = [i for i in c.find_all()
             if c.type(i) == "text" and c.itemcget(i, "text") == "H"]
        self.assertEqual(1, len(h), "H metni bulunamadı/çok")
        hx, hy = c.coords(h[0])
        kutu = [i for i in c.find_all() if c.type(i) == "rectangle"
                and c.itemcget(i, "outline") == yks_gui.KIRMIZI
                and c.itemcget(i, "fill") == ""
                and abs((c.coords(i)[0] + c.coords(i)[2]) / 2 - hx) < 1
                and abs((c.coords(i)[1] + c.coords(i)[3]) / 2 - hy) < 1]
        self.assertEqual(1, len(kutu), "H kutusu bulunamadı/çok")
        return tuple(c.bbox(kutu[0]))

    def _ana_denetle(self, ad):
        c = self.app.harita
        # `_tik` inset'i (İHA-UB) YALNIZ harita görünümünde çizer: denetime dahil.
        self.assertTrue(self._pompala(
            lambda: any("inset" in c.gettags(i) for i in c.find_all()), 3.0))
        kutular = _metin_kutulari(c)
        boyut = f"{c.winfo_width()}x{c.winfo_height()}"
        self.assertEqual([], _kesisen_ciftler(kutular), f"ana {ad} {boyut}")
        self.assertEqual([], _tasanlar(c, kutular), f"ana {ad} {boyut}")
        self._bant_denetle(c, f"ana {ad}")

    def _h2c(self, olcek):
        self._olcekli_kur(olcek)
        seq = SEQ + 100
        durumlar = [("bos", None)]
        for yol in (1, 2, 3):
            seq += 1
            durumlar.append((f"road{yol}", dict(ROTA, seq=seq, road=yol,
                                                label=yks_gui.ROAD_LABEL[yol])))
        durumlar.append(("no_route", dict(YOK_ROTA, seq=seq + 1)))
        durumlar.append(("no_route_uzun", dict(YOK_ROTA, seq=seq + 2,
                                               detay=UZUN_DETAY)))
        for ad, mesaj in durumlar:
            with self.subTest(olcek=olcek, durum=ad):
                if mesaj is not None:
                    self._mesaj_ver(mesaj)
                self._mini_denetle(ad, mesaj)
        # ANA harita (harita görünümü, inset dahil): uzun ve kısa detaylı ROTA YOK.
        self.app.gorunum("harita")
        self.assertTrue(self._pompala(self.app.harita.winfo_ismapped, 3.0))
        with self.subTest(olcek=olcek, durum="ana_no_route_uzun"):
            self._ana_denetle("no_route_uzun")
        with self.subTest(olcek=olcek, durum="ana_no_route"):
            self._mesaj_ver(dict(YOK_ROTA, seq=seq + 3))
            self._ana_denetle("no_route")

    def test_H2c_olcek_1_0(self):
        self._h2c(1.0)

    def test_H2c_olcek_1_5_hakem_ekrani(self):
        self._h2c(1.5)


class _AltinTuval:
    """`results/.../t226/ana_harita_altin_uret.py` KayitTuval'ının AYNISI.

    Ölçüm yüzeyi (`bbox`/`coords`) bilerek YOK: ana harita OPEN_ROUTE/boşta
    font/DPI'ya bağlı ölçülü yerleşime girerse AttributeError ile düşer."""

    def __init__(self, w, h):
        self.w, self.h, self.cagrilar = w, h, []

    def winfo_width(self):
        return self.w

    def winfo_height(self):
        return self.h

    def delete(self, *a, **k):
        self.cagrilar.append(["delete", list(a), dict(sorted(k.items()))])

    def _kayit(self, ad, a, k):
        self.cagrilar.append([ad, [list(x) if isinstance(x, tuple) else x for x in a],
                              {kk: (list(v) if isinstance(v, tuple) else v)
                               for kk, v in sorted(k.items())}])
        return len(self.cagrilar)

    def create_line(self, *a, **k):
        return self._kayit("create_line", a, k)

    def create_rectangle(self, *a, **k):
        return self._kayit("create_rectangle", a, k)

    def create_text(self, *a, **k):
        return self._kayit("create_text", a, k)

    def create_oval(self, *a, **k):
        return self._kayit("create_oval", a, k)


class H2d_AnaHaritaMasterIleBaytEs(unittest.TestCase):
    """MİMAR KARARI (D-448 §4): ana haritanın çizimi YALNIZ `rota_yok`ta
    değişebilir. OPEN_ROUTE (road 1/2/3, ANKOR YOK) ve boşta öğe listesi +
    koordinatlar master (362197e0, T226 birleşmemiş) ile BAYT-EŞ: 4 boyut ×
    5 durum = 20 senaryo. Altın kayıt master kaynağından `git show` ile
    üretildi: results/fdr_sprint_20260910/H9_MK15/t226/ana_harita_altin_uret.py.
    Küçük harita fontu (`f_mini`) ana haritaya SIZARSA da düşer."""

    ALTIN = KOK / "tests" / "artifacts" / "t226d" / "ana_harita_master.json"
    MASTER = "362197e0"

    def test_H2d_open_route_ve_bosta_master_ile_bayt_es(self):
        veri = json.loads(self.ALTIN.read_text(encoding="utf-8"))
        self.assertEqual(f"{self.MASTER}:comms/yks_gui.py", veri["kaynak"])
        senaryolar = veri["senaryolar"]
        self.assertEqual(20, len(senaryolar))
        for ad, s in senaryolar.items():
            with self.subTest(senaryo=ad), \
                    mock.patch.object(yks_gui, "OLCEK", s["olcek"]):
                g = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)
                g.harita = _AltinTuval(s["w"], s["h"])
                g.f_kucuk, g.f_orta, g.f_mini = "f_kucuk", "f_orta", "f_mini"
                g.rota, g.rota_yok = s["rota"], None
                g.gorunum_adi = "harita"
                g._harita_ciz()
                self.assertEqual(
                    json.dumps(s["cagrilar"], ensure_ascii=False),
                    json.dumps(g.harita.cagrilar, ensure_ascii=False))

    def test_H2d_altin_kayit_master_kaynagindan(self):
        try:
            ham = subprocess.run(
                ["git", "-C", str(KOK), "show", f"{self.MASTER}:comms/yks_gui.py"],
                capture_output=True, check=True, timeout=60).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            self.skipTest(f"YAPILAMADI: git show {self.MASTER}: {exc!r}")
        veri = json.loads(self.ALTIN.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(ham).hexdigest(), veri["kaynak_sha256"])


class H2e_RotaYokSonrasiAnaHarita(_GercekEkran):
    """NEDEN: D-454/O5, NO_ROUTE yerleşimi sonraki OPEN_ROUTE'a sızmamalı."""

    def _cizim(self):
        self.app._harita_ciz()
        c = self.app.harita
        return [(c.type(i), c.coords(i),
                 {ad: bilgi[-1] for ad, bilgi in c.itemconfigure(i).items()},
                 c.tk.call("font", "actual", c.itemcget(i, "font"))
                 if c.type(i) == "text" else None)
                for i in c.find_all()]

    def _gecisleri_denetle(self, olcek):
        app = self._kur(olcek=olcek)
        app.harita.pack_configure(expand=False, fill="none")
        app.harita.configure(width=742, height=450)
        self.kok.deiconify()
        self.assertTrue(self._pompala(app.harita.winfo_ismapped))
        self._pompala(lambda: False, 0.2)
        seq = SEQ + 100
        for yol in (1, 2, 3):
            with self.subTest(yol=yol, olcek=olcek):
                seq += 1
                mesaj = dict(ROTA, road=yol, seq=seq)
                self._mesaj_ver(mesaj)
                ilk = self._cizim()
                for detay in ("", "Dar koridor nedeniyle rota bulunamadı. " * 16):
                    seq += 1
                    self._mesaj_ver(dict(YOK_ROTA, seq=seq, detay=detay))
                    self._cizim()
                    if detay:
                        self.assertIn(str(app.harita), app._olculu_alan,
                                      "Önkoşul: uzun NO_ROUTE arena alanını değiştirmeli")
                    seq += 1
                    self._mesaj_ver(dict(mesaj, seq=seq))
                    self.assertEqual(ilk, self._cizim(),
                                     "NO_ROUTE yerleşimi OPEN_ROUTE'a sızdı")
                    self.assertNotIn(str(app.harita), app._olculu_alan)

    def test_H2e_olcek_1_0(self):
        self._gecisleri_denetle(1.0)

    def test_H2e_olcek_1_5(self):
        self._gecisleri_denetle(1.5)


class H6_GorunumDonusSirasi(_GercekEkran):
    """MİMAR KARARI (D-448 §4): kamera/algı → harita dönüşünde harita
    çerçevesi ilk açılıştaki yerine (görünüm düğmelerinin HEMEN altı) döner.
    Kusur (T226 öncesinden): çıplak `pack()` çerçeveyi sol panelin SONUNA,
    senaryo/demo düğmelerinin altına ekliyordu."""

    def _durum(self, app):
        bilgi = dict(app.harita.pack_info())
        bilgi.pop("in", None)
        return ([str(w) for w in app.harita.master.pack_slaves()],
                app.harita.winfo_y(), app.harita.winfo_height(), bilgi)

    def _ilk(self):
        app = self._kur()
        self.kok.deiconify()
        self.assertTrue(self._pompala(
            lambda: app.harita.winfo_ismapped() and app.harita.winfo_height() > 1,
            5.0))
        self._pompala(lambda: False, 0.2)
        ilk = self._durum(app)
        sira = ilk[0]
        self.assertEqual(sira.index(str(app._gorunum_anahtari)) + 1,
                         sira.index(str(app.harita)), sira)
        return app, ilk

    def _harita_don(self, app):
        app.gorunum("harita")
        self.assertTrue(self._pompala(app.harita.winfo_ismapped, 3.0))
        self._pompala(lambda: False, 0.2)

    def test_H6_harita_kamera_harita_sonrasi_sira_ve_konum_ilk_acilistaki(self):
        app, ilk = self._ilk()
        app.gorunum("kamera")
        self.assertTrue(self._pompala(app.kamera_cerceve.winfo_ismapped, 3.0))
        self._harita_don(app)
        self.assertEqual(ilk, self._durum(app))
        # İki tur: dönüş tek seferlik değil.
        app.gorunum("kamera")
        self.assertTrue(self._pompala(app.kamera_cerceve.winfo_ismapped, 3.0))
        self._harita_don(app)
        self.assertEqual(ilk, self._durum(app))

    def test_H6b_algi_gorunumu_de_ilk_yerde_model_yuklenmez(self):
        app, ilk = self._ilk()
        # Algı görünümü model/GPU istemez bu testte: `_algi_iste` taklit.
        with mock.patch.object(app, "_algi_iste") as iste:
            app.gorunum("algi")
            self.assertTrue(self._pompala(app.algi_cerceve.winfo_ismapped, 3.0))
            sira = [str(w) for w in app.algi_cerceve.master.pack_slaves()]
            self.assertEqual(sira.index(str(app._gorunum_anahtari)) + 1,
                             sira.index(str(app.algi_cerceve)), sira)
            self._harita_don(app)
        iste.assert_called_once_with()
        self.assertEqual(ilk, self._durum(app))


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
        # MİMAR KURALI D-453 (T226-D2, çürütücü D1): belge kilidi yeni içeriği
        # ÇİZİLİ ARALIKLAR AYIKLANMIŞ metinde arar — `~~…~~` içine alınmış
        # (geri çekilmiş) cümle, ne başlık ne örnek olarak kilidi karşılar.
        metin = re.sub(r"~~.*?~~", "", SOZLESME.read_text(encoding="utf-8"),
                       flags=re.S)
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


class K5_Cv2SabitYedegi(unittest.TestCase):
    """MİMAR KARARI (D-448 iş 4): `ARKA_UC_API` modül YÜKLENİRKEN kurulur;
    cv2 derlemesinde (Jetson python3-opencv) CAP_DSHOW/CAP_MSMF/CAP_V4L2
    eksikse `cv2.CAP_DSHOW` AttributeError ile köprü importu — nvargus yolu
    dahil — düşerdi. Sahte cv2 modülüyle GERÇEK dosya yüklenir."""

    KOPRU = KOK / "scripts" / "kamera_koprusu.py"

    @staticmethod
    def _sahte_cv2(**ek):
        m = types.ModuleType("cv2")
        # Yalnız modül düzeyinde okunan, her derlemede bulunan sabitler.
        m.CAP_ANY = 0
        m.CAP_PROP_FRAME_WIDTH, m.CAP_PROP_FRAME_HEIGHT, m.CAP_PROP_FPS = 3, 4, 5
        for ad, deger in ek.items():
            setattr(m, ad, deger)
        return m

    def _yukle(self, sahte):
        spec = importlib.util.spec_from_file_location("_kamera_koprusu_k5", self.KOPRU)
        modul = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {"cv2": sahte}):
            spec.loader.exec_module(modul)
        return modul

    def test_K5_arka_uc_sabiti_eksik_cv2_ile_import_dusmez(self):
        sahte = self._sahte_cv2()
        for ad in ("CAP_DSHOW", "CAP_MSMF", "CAP_V4L2"):
            self.assertFalse(hasattr(sahte, ad))
        modul = self._yukle(sahte)
        self.assertEqual({"auto": 0, "dshow": 700, "msmf": 1400, "v4l2": 200},
                         modul.ARKA_UC_API)
        self.assertEqual(kk.ARKA_UC_SECENEKLERI, modul.ARKA_UC_SECENEKLERI)
        # Yedek sayılar OpenCV videoio enum'uyla aynı (bu PC'deki gerçek cv2).
        self.assertEqual((700, 1400, 200),
                         (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_V4L2))

    def test_K5b_sabit_varsa_cv2_degeri_kullanilir(self):
        modul = self._yukle(self._sahte_cv2(CAP_DSHOW=7001, CAP_MSMF=14001,
                                            CAP_V4L2=2001))
        self.assertEqual({"auto": 0, "dshow": 7001, "msmf": 14001, "v4l2": 2001},
                         modul.ARKA_UC_API)


if __name__ == "__main__":
    unittest.main()

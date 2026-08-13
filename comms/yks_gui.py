"""NEDEN: YKS, hakem onayını ve manuel İKA komutunu gerçek haberleşme
hedefine fail-closed biçimde ileterek şartname kilitlerini görünür kılmalıdır.

YKS (Yer Kontrol İstasyonu) — hakem ekranı GUI'si.

Şartname §2.2.3/§6.2: İHA'nın tespit ettiği güzergâh YKS'de CANLI görünmeli,
Alan Hakemi monitörden izleyip onaylamalı. Bu arayüz, yks_monitor.py'nin
terminal sürümünün yerini alan gerçek hakem ekranıdır:

  · gerçek protokol trafiği dinler (OPEN_ROUTE / IHA_LANDED / HEARTBEAT)
  · saha haritasında (50×50 m HTAB) rotayı ve açık yolu çizer
  · İHA/İKA bağlantı canlılığını gösterir (heartbeat yaşı)
  · hakem onayı BUTONLA verilir → ACK ancak o zaman döner
    (yks_monitor.py'deki "otomatik onay" bu ekranda kaldırıldı)

Kullanım:
  python yks_gui.py --ika 127.0.0.1:5006    # 0.0.0.0:5005 dinler (UDP)
  python yks_gui.py --bind 0.0.0.0:5005 --ika 127.0.0.1:5006
  python yks_gui.py --serial COM5            # SiK telsiz (saha)
  python yks_gui.py --demo                   # dahili İHA/İKA beslemesiyle tanıtım
  python yks_gui.py --demo --otokaydet 6     # 6 sn sonra pencere SS'i kaydet (rapor)

Sadece stdlib + (SS için) Pillow kullanır; tkinter Python ile gelir.
"""
import argparse
import math
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

from link import UDPLink, SerialLink
from ika_receiver import IkaReceiver
from protocol import (encode, ack, command, heartbeat, open_route,
                      FrameReader, ROAD_LABEL)

_PROJE_KOKU = Path(__file__).resolve().parents[1]
if str(_PROJE_KOKU / "codes") not in sys.path:
    sys.path.insert(0, str(_PROJE_KOKU / "codes"))
from karar_sozlesmesi import (ZEMIN_KAPLAMA_TAVANI,
                              ZEMIN_MASKESI_SUPHELI_SEBEBI,
                              olcek_gecerli_mi, rota_guven_reddi,
                              rota_olcek_reddi, zemin_kaplamasi)

# ── Renkler (koyu tema) ──────────────────────────────────────────────────────
BG      = "#0f1419"   # zemin
PANEL   = "#1a2129"   # panel zemini
CIZGI   = "#2a3441"   # panel kenarı
METIN   = "#e8edf2"
SOLUK   = "#8b98a5"
YESIL   = "#2ecc71"
SARI    = "#f0a437"
KIRMIZI = "#e15241"
MAVI    = "#4aa3df"

ARENA_M = 50.0        # HTAB 50×50 m (şartname)
OLCEK = 1.0           # main() ekran DPI'sine göre ayarlar (yüksek DPI okunurluk)


def S(px):
    """Piksel ölçüsünü ekran DPI ölçeğiyle çarp (yazı puntoları tk'de otomatik)."""
    return int(px * OLCEK)


def _udp_adres(deger):
    """Argparse için IPv4/host:port hedefini doğrula ve tuple'a dönüştür."""
    try:
        host, port_metni = deger.rsplit(":", 1)
        port = int(port_metni)
    except (AttributeError, TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("HOST:PORT biçimi gerekli") from exc
    if not host or not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("HOST dolu, PORT 1..65535 olmalı")
    return host, port


class YksArayuz:
    IHA_LIMIT = 900     # şartname: fırlatma → paraşütle iniş ≤ 15 dk
    IKA_LIMIT = 600     # şartname: teker dönüşü → HB temas ≤ 10 dk

    def __init__(
            self, kok, link, otomatik_onay=False, demo=False, ika_peer=None):
        self.kok = kok
        self.link = link
        self.reader = FrameReader()
        self.gelen = queue.Queue()
        self.otomatik_onay = otomatik_onay
        self.demo = demo
        self.demo_durum = {"iha_hb": True, "ika_hb": True}   # senaryo anahtarları

        self.rota = None            # son OPEN_ROUTE mesajı
        self.rota_yok = None        # son NO_ROUTE; kırmızı güvenlik bandı için
        self.rota_adr = None        # ACK dönülecek adres
        self.onaylandi = False
        self.son_hb = {}            # node -> zaman
        self.son_adr = {}           # node -> adres (CMD gönderimi için)
        self.sabit_adr = {}         # CLI ile pinlenen adres heartbeat ile değişmez
        if ika_peer is not None:
            self.son_adr["ika"] = ika_peer
            self.sabit_adr["ika"] = ika_peer
        self.sayac = {
            "OPEN_ROUTE": 0,
            "OPEN_ROUTE_RED": 0,
            "NO_ROUTE": 0,
            "IHA_LANDED": 0,
            "HEARTBEAT": 0,
            "ACK_TX": 0,
        }
        self.iha_landed_seq = None       # üretim İHA'sından gelen son iniş olayı
        self.arm_acik = False
        self.tespit_onayli = False          # §2.2.3 iki aşamalı onayın 1. adımı
        self.t_iha0 = self.t_iha1 = None    # İHA görev kronometresi
        self.t_ika0 = self.t_ika1 = None    # İKA görev kronometresi
        self.t_haz0 = self.t_haz1 = None    # hazırlık kronometresi (§6.2)
        self.ceza_toplam = 0                # birikmiş ceza puanı
        self.parasut_teyit = 0.0            # iki adımlı paraşüt emniyeti
        self.mod = {}                       # node -> uçuş modu (AUTO/MANUEL)
        self._manuel_uyarildi = False
        self.iha_iz = []                    # İHA-UB (300×300) içindeki konum izi
        self.tel = {}                       # node -> son telemetri alanları
        self.rx_alim = {}                   # seq -> kaç kez alındı (tekrar gönderim)
        self._detay_base = ""
        # canlı algı (v3 modeli ile gerçek çıkarım)
        self.algi_kuyruk = queue.Queue()
        self.algi_model = None
        self.algi_mesgul = False
        # T29 (D-39): Bu yalnız semptom yönetimidir; asıl sorun D-21'deki v21
        # arena/RescueNet domain boşluğudur. Gemini/val tanısal karşılaştırma için kalır.
        # AÇILIŞ KAYNAĞI listenin ilkidir: `kompozit` — üç-kapılı arena
        # mantığının GEÇERLİ olduğu tek küme (yer gerçeği manifest'te).
        # `drone` bir otoparktır ve orada koridor seçimi sınanmaz (D-53).
        self.algi_kaynak = self.ALGI_KAYNAKLAR[0]
        self.algi_idx = 0
        self._algi_foto = None              # ImageTk referansı (GC koruması)

        self._arayuz_kur()
        threading.Thread(target=self._dinle, daemon=True).start()
        self._tik()

    # ── Arayüz kurulumu ──────────────────────────────────────────────────────
    def _arayuz_kur(self):
        self.kok.title("NAVITAS — Yer Kontrol İstasyonu (YKS) · Hakem Ekranı")
        self.kok.configure(bg=BG)
        # ekran boyutuna göre pencere (yüksek DPI'da okunur kalır)
        sw, sh = self.kok.winfo_screenwidth(), self.kok.winfo_screenheight()
        w, h = min(S(1240), int(sw * 0.92)), min(S(940), int(sh * 0.90))
        self.kok.geometry(f"{w}x{h}")
        self.kok.minsize(S(1050), S(760))

        self.f_baslik = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.f_buyuk = tkfont.Font(family="Segoe UI", size=36, weight="bold")
        self.f_orta = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self.f_kucuk = tkfont.Font(family="Segoe UI", size=10)
        self.f_mono = tkfont.Font(family="Consolas", size=10)

        # Başlık şeridi
        ust = tk.Frame(self.kok, bg=BG)
        ust.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(ust, text="NAVITAS", font=self.f_baslik, fg=YESIL, bg=BG).pack(side="left")
        tk.Label(ust, text="  YER KONTROL İSTASYONU — HAKEM EKRANI", font=self.f_baslik,
                 fg=METIN, bg=BG).pack(side="left")
        self.lbl_saat = tk.Label(ust, text="", font=self.f_orta, fg=SOLUK, bg=BG)
        self.lbl_saat.pack(side="right")

        # Yazılım zinciri şeridi (parçaların bağlantısı)
        zincir = tk.Frame(self.kok, bg=PANEL, highlightbackground=CIZGI, highlightthickness=1)
        zincir.pack(fill="x", padx=14, pady=4)
        self.zincir_etiket = {}
        adimlar = ["Kamera (İHA)", "YOLOv8-seg", "Rota Üretimi",
                   "433 MHz TX", "YKS (bu ekran)", "İKA"]
        for i, ad in enumerate(adimlar):
            e = tk.Label(zincir, text=ad, font=self.f_kucuk, fg=SOLUK, bg=PANEL,
                         padx=10, pady=6)
            e.pack(side="left")
            self.zincir_etiket[ad] = e
            if i < len(adimlar) - 1:
                tk.Label(zincir, text="→", font=self.f_orta, fg=CIZGI, bg=PANEL).pack(side="left")

        govde = tk.Frame(self.kok, bg=BG)
        govde.pack(fill="both", expand=True, padx=14, pady=4)

        # Sol: iki görünüm — saha haritası / canlı algı (v3)
        _m = self.ALGI_MODEL_DOSYA.rsplit(".", 1)[0]
        sol = self._panel(govde, "SAHA HARİTASI — HTAB 50×50 m   |   "
                                 f"CANLI ALGI — {_m} (GERÇEK çıkarım)")
        sol.pack(side="left", fill="both", expand=True, padx=(0, 8))

        anahtar = tk.Frame(sol, bg=PANEL)
        anahtar.pack(fill="x", padx=10, pady=(4, 0))
        self.btn_gor_harita = tk.Button(anahtar, text="◈ Saha Haritası (V)",
                                        font=self.f_kucuk, fg=BG, bg=YESIL,
                                        relief="flat", padx=8, pady=3,
                                        command=lambda: self.gorunum("harita"))
        self.btn_gor_harita.pack(side="left", padx=(0, 6))
        self.btn_gor_algi = tk.Button(anahtar, text=f"◉ Canlı Algı — {_m} (V)",
                                      font=self.f_kucuk, fg=METIN, bg="#232e3a",
                                      relief="flat", padx=8, pady=3,
                                      command=lambda: self.gorunum("algi"))
        self.btn_gor_algi.pack(side="left")

        self.harita = tk.Canvas(sol, width=S(480), height=S(420), bg="#121920",
                                highlightthickness=0)
        self.harita.pack(padx=10, pady=(4, 6), fill="both", expand=True)

        # canlı algı görünümü (başta gizli)
        self.algi_cerceve = tk.Frame(sol, bg=PANEL)
        self.lbl_algi_img = tk.Label(self.algi_cerceve, bg="#121920",
                                     text=f"{_m} modeli ilk geçişte yüklenecek…",
                                     fg=SOLUK, font=self.f_kucuk)
        self.lbl_algi_img.pack(padx=10, pady=(4, 4), fill="both", expand=True)
        arow = tk.Frame(self.algi_cerceve, bg=PANEL)
        arow.pack(fill="x", padx=10)
        for ad, kom in (("◀ Önceki (←)", self.algi_onceki),
                        ("Sonraki (→) ▶", self.algi_sonraki),
                        ("Kaynak: gemini/val (K)", self.algi_kaynak_degistir)):
            tk.Button(arow, text=ad, font=self.f_kucuk, fg=METIN, bg="#232e3a",
                      activebackground=MAVI, activeforeground=BG, relief="flat",
                      padx=7, pady=3, command=kom).pack(side="left", padx=(0, 6))
        self.lbl_algi_bilgi = tk.Label(self.algi_cerceve, text="—",
                                       font=self.f_kucuk, fg=SOLUK, bg=PANEL,
                                       anchor="w", wraplength=S(640),
                                       justify="left")
        self.lbl_algi_bilgi.pack(fill="x", padx=10, pady=(2, 4))
        self.gorunum_adi = "harita"

        # Acil durum senaryo tatbikatı (yalnız --demo modunda etkin)
        tk.Label(sol, text="ACİL DURUM SENARYOLARI — arıza emniyet tatbikatı "
                           "(DDR B.3.3.1 tablosu; simülasyon)",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
                 wraplength=S(660), justify="left").pack(fill="x", padx=10)
        btnf = tk.Frame(sol, bg=PANEL)
        btnf.pack(fill="x", padx=10, pady=(2, 10))
        for i, (ad, kod) in enumerate((("F1 RC kaybı", "rc"), ("F2 YKS kaybı", "yks"),
                                       ("F3 İKA kaybı", "ika"), ("F4 Batarya", "bat"),
                                       ("F5 GNSS", "gnss"), ("F6 Algı aşımı", "algi"))):
            tk.Button(btnf, text=ad, font=self.f_kucuk, fg=METIN, bg="#232e3a",
                      activebackground=SARI, activeforeground=BG, relief="flat",
                      padx=7, pady=3,
                      state=("normal" if self.demo else "disabled"),
                      command=lambda k=kod: self.senaryo(k)
                      ).pack(side="left", padx=(0, 6))

        # Demo / SS kontrolleri ("hile tuşları") — onay akışını yeniden izlemek
        # ve ekran görüntüsü sahnelemek için
        tk.Label(sol, text="DEMO / SS KONTROLLERİ — kısayollar: F1–F6 senaryo · "
                           "N yeni tespit · R onayı sıfırla · A arm · V görünüm · "
                           "←/→ algı görüntüsü · K kaynak",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
                 wraplength=S(660), justify="left").pack(fill="x", padx=10)
        dkf = tk.Frame(sol, bg=PANEL)
        dkf.pack(fill="x", padx=10, pady=(2, 10))
        for ad, kom in (("Yeni tespit üret (N)", self.yeni_tespit),
                        ("Hakem onayını sıfırla (R)", self.onay_sifirla)):
            tk.Button(dkf, text=ad, font=self.f_kucuk, fg=METIN, bg="#232e3a",
                      activebackground=MAVI, activeforeground=BG, relief="flat",
                      padx=7, pady=3,
                      state=("normal" if self.demo else "disabled"),
                      command=kom).pack(side="left", padx=(0, 6))

        sag = tk.Frame(govde, bg=BG, width=S(440))
        sag.pack(side="left", fill="y")
        sag.pack_propagate(False)

        # Sağ 1: açık yol kararı
        p1 = self._panel(sag, "AÇIK YOL TESPİTİ")
        p1.pack(fill="x", pady=(0, 8))
        self.lbl_karar = tk.Label(p1, text="— BEKLENİYOR —", font=self.f_buyuk,
                                  fg=SOLUK, bg=PANEL)
        self.lbl_karar.pack(pady=(2, 0))
        self.lbl_detay = tk.Label(p1, text="İHA taraması sürüyor", font=self.f_kucuk,
                                  fg=SOLUK, bg=PANEL, wraplength=S(400), justify="center")
        self.lbl_detay.pack(pady=(0, 6))
        self.guven_cubuk = tk.Canvas(p1, width=S(380), height=S(20), bg="#121920",
                                     highlightthickness=0)
        self.guven_cubuk.pack(pady=(0, 12))

        # Sağ 2: hakem onayı
        p2 = self._panel(sag, "ALAN HAKEMİ ONAYI (şartname §6.2)")
        p2.pack(fill="x", pady=(0, 8))
        self.btn_onay = tk.Button(p2, text="TESPİTİ ONAYLA → ACK GÖNDER",
                                  font=self.f_orta, fg=BG, bg=SOLUK,
                                  activebackground=YESIL, relief="flat",
                                  state="disabled", command=self.onayla, pady=8)
        self.btn_onay.pack(fill="x", padx=10, pady=(4, 4))
        self.lbl_onay = tk.Label(p2, text="Onay bekleyen tespit yok", font=self.f_kucuk,
                                 fg=SOLUK, bg=PANEL, wraplength=S(400),
                                 justify="center")
        self.lbl_onay.pack(pady=(0, 8))

        # Sağ 2b: rota analizi (segment eksen değişimleri)
        p2b = self._panel(sag, "ROTA ANALİZİ — segment / eksen değişimleri")
        p2b.pack(fill="x", pady=(0, 8))
        rkap = tk.Frame(p2b, bg=PANEL)
        rkap.pack(fill="x", padx=10, pady=(2, 8))
        rkay = tk.Scrollbar(rkap, width=S(12))
        rkay.pack(side="right", fill="y")
        self.rota_metin = tk.Text(rkap, height=6, bg="#121920", fg=METIN, bd=0,
                                  font=self.f_mono, state="disabled", wrap="none",
                                  yscrollcommand=rkay.set)
        self.rota_metin.pack(side="left", fill="both", expand=True)
        rkay.config(command=self.rota_metin.yview)

        # Sağ 3: bağlantı durumu
        p3 = self._panel(sag, "BAĞLANTI / DÜĞÜM DURUMU")
        p3.pack(fill="x", pady=(0, 8))
        self.lbl_dugum = {}
        for ad in ("iha", "ika"):
            sat = tk.Frame(p3, bg=PANEL)
            sat.pack(fill="x", padx=10, pady=2)
            nokta = tk.Label(sat, text="●", font=self.f_orta, fg=KIRMIZI, bg=PANEL)
            nokta.pack(side="left")
            metin = tk.Label(sat, text=f"{ad.upper()}  — sinyal yok", font=self.f_kucuk,
                             fg=SOLUK, bg=PANEL, wraplength=S(390), justify="left")
            metin.pack(side="left", padx=6)
            self.lbl_dugum[ad] = (nokta, metin)
        self.lbl_ucus = tk.Label(p3, text="İHA UÇUŞ DURUMU: OTONOM GÖREV (AUTO)",
                                 font=self.f_orta, fg=YESIL, bg=PANEL,
                                 wraplength=S(410), justify="left")
        self.lbl_ucus.pack(padx=10, pady=(4, 0), anchor="w")
        self.lbl_sayac = tk.Label(p3, text="", font=self.f_mono, fg=SOLUK, bg=PANEL)
        self.lbl_sayac.pack(padx=10, pady=(2, 8), anchor="w")

        # Sağ 4: mesaj günlüğü
        p4 = self._panel(sag, "MESAJ GÜNLÜĞÜ (canlı protokol trafiği)")
        p4.pack(fill="both", expand=True)
        gkap = tk.Frame(p4, bg=PANEL)
        gkap.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        kaydirak = tk.Scrollbar(gkap, width=S(12))
        kaydirak.pack(side="right", fill="y")
        self.gunluk = tk.Text(gkap, height=9, bg="#121920", fg=METIN, bd=0,
                              font=self.f_mono, state="disabled", wrap="word",
                              yscrollcommand=kaydirak.set)
        self.gunluk.pack(side="left", fill="both", expand=True)
        kaydirak.config(command=self.gunluk.yview)
        for renk_ad, renk in (("yesil", YESIL), ("sari", SARI),
                              ("kirmizi", KIRMIZI), ("mavi", MAVI),
                              ("soluk", SOLUK)):
            self.gunluk.tag_configure(renk_ad, foreground=renk)

        # Alt durum çubuğu
        alt = tk.Frame(self.kok, bg=PANEL)
        alt.pack(fill="x", side="bottom")
        tasiyici = "SiK 433 MHz (seri)" if isinstance(self.link, SerialLink) \
            else f"UDP :{self.link.port}"
        tk.Label(alt, text=f"  Taşıyıcı: {tasiyici}   ·   Protokol: newline-JSON v1"
                           f"   ·   Çerçeve: OPEN_ROUTE / IHA_LANDED / "
                           f"HEARTBEAT / ACK / CMD",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, wraplength=S(1150),
                 justify="left").pack(side="left", pady=3)

        # Görev kontrol & kronometre şeridi — 2 satır:
        # 1) hazırlık akışı (§6.2 hands-off), 2) uçuş/intikal akışı + paraşüt
        gorev = tk.Frame(self.kok, bg=PANEL, highlightbackground=CIZGI,
                         highlightthickness=1)
        gorev.pack(fill="x", side="bottom", padx=14, pady=(0, 4))
        satir1 = tk.Frame(gorev, bg=PANEL)
        satir1.pack(fill="x")
        satir2 = tk.Frame(gorev, bg=PANEL)
        satir2.pack(fill="x")

        def gbuton(ana, metin, komut, aktif=True):
            b = tk.Button(ana, text=metin, font=self.f_kucuk, fg=METIN,
                          bg="#232e3a", activebackground=SARI, activeforeground=BG,
                          relief="flat", padx=8, pady=3, command=komut,
                          state=("normal" if aktif else "disabled"))
            b.pack(side="left", padx=5, pady=3)
            return b

        # satır 1 — hazırlık (§6.2: 15 dk, Takım Hazır'la durur; müdahale +100 ceza)
        self.btn_alan = gbuton(satir1, "ALAN GİRİŞİ", self.alan_girisi)
        self.btn_hazir = gbuton(satir1, "TAKIM HAZIR", self.takim_hazir, aktif=False)
        self.btn_mudahale = gbuton(satir1, "MÜDAHALE (−100)", self.mudahale,
                                   aktif=False)
        self.lbl_kron_haz = tk.Label(satir1, text="HAZIRLIK ⏱ --:-- / 15:00",
                                     font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_kron_haz.pack(side="right", padx=10)
        self.lbl_ceza = tk.Label(satir1, text="CEZA Σ 0", font=self.f_orta,
                                 fg=SOLUK, bg=PANEL)
        self.lbl_ceza.pack(side="right", padx=10)

        # satır 2 — uçuş/intikal
        self.btn_arm = gbuton(satir2, "ARM (A)", self.arm_degistir)
        self.btn_firlat = gbuton(satir2, "FIRLATMA", self.firlatma, aktif=False)
        self.btn_iha_indi = gbuton(satir2, "İHA İNDİ", self.iha_indi, aktif=False)
        self.btn_parasut = gbuton(satir2, "PARAŞÜT (manuel −50)", self.parasut)
        # §2.2.5 kilidini GÖSTERMEK için hep tıklanabilir — erken basılırsa reddeder
        self.btn_ika_go = gbuton(satir2, "İKA BAŞLAT", self.ika_baslat)
        self.btn_hb = gbuton(satir2, "HB TEMAS", self.hb_temas, aktif=False)

        self.lbl_arm = tk.Label(satir2, text="SİSTEM: DISARM — güvenli",
                                font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_arm.pack(side="left", padx=10)
        self.lbl_kron_ika = tk.Label(satir2, text="İKA ⏱ --:-- / 10:00",
                                     font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_kron_ika.pack(side="right", padx=10)
        self.lbl_kron_iha = tk.Label(satir2, text="İHA ⏱ --:-- / 15:00",
                                     font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_kron_iha.pack(side="right", padx=10)

        # kısayollar ("hile tuşları")
        for i, kod in enumerate(("rc", "yks", "ika", "bat", "gnss", "algi"), 1):
            self.kok.bind(f"<F{i}>", lambda e, k=kod: self.senaryo(k))
        self.kok.bind("<KeyPress-n>", lambda e: self.yeni_tespit())
        self.kok.bind("<KeyPress-r>", lambda e: self.onay_sifirla())
        self.kok.bind("<KeyPress-a>", lambda e: self.arm_degistir())
        self.kok.bind("<KeyPress-v>", lambda e: self.gorunum(
            "algi" if self.gorunum_adi == "harita" else "harita"))
        self.kok.bind("<KeyPress-k>", lambda e: self.algi_kaynak_degistir())
        self.kok.bind("<Left>", lambda e: self.algi_onceki())
        self.kok.bind("<Right>", lambda e: self.algi_sonraki())

        self._harita_ciz()

    def _panel(self, ebeveyn, baslik):
        p = tk.Frame(ebeveyn, bg=PANEL, highlightbackground=CIZGI, highlightthickness=1)
        tk.Label(p, text=baslik, font=self.f_kucuk, fg=SOLUK, bg=PANEL,
                 anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        return p

    # ── Harita ───────────────────────────────────────────────────────────────
    def _mxy(self, x_m, y_m):
        """Metre (0..50, y kuzey) → canvas pikseli."""
        w = self.harita.winfo_width() or 480
        h = self.harita.winfo_height() or 480
        kenar = S(34)
        olcek = min(w, h) - 2 * kenar
        px = kenar + (x_m / ARENA_M) * olcek
        py = h - kenar - (y_m / ARENA_M) * olcek   # y yukarı = kuzey
        return px, py

    def _harita_ciz(self):
        c = self.harita
        c.delete("all")
        # grid (5 m)
        for m in range(0, 51, 5):
            x0, y0 = self._mxy(m, 0)
            x1, y1 = self._mxy(m, 50)
            c.create_line(x0, y0, x1, y1, fill="#1c2630")
            x0, y0 = self._mxy(0, m)
            x1, y1 = self._mxy(50, m)
            c.create_line(x0, y0, x1, y1, fill="#1c2630")
        # arena çerçevesi
        x0, y0 = self._mxy(0, 0)
        x1, y1 = self._mxy(50, 50)
        c.create_rectangle(x0, y0, x1, y1, outline=CIZGI, width=2)

        # 3 yol koridoru — tespit sonrası: açık yol YEŞİL, geri kalan HER YER
        # (kapalı koridorlar + moloz sahası) KIRMIZI = gidilemez
        # Yeni NO_ROUTE, eski OPEN_ROUTE önbelleğini görsel olarak geçersiz
        # kılar: hakem ekranda yeşil bir rota görüp yanlış onay vermemelidir.
        acik = self.rota["road"] if self.rota and not self.rota_yok else None
        if acik is not None:
            c.create_rectangle(x0, y0, x1, y1, fill=KIRMIZI, stipple="gray12",
                               outline="")
            lx, ly = self._mxy(0.8, 51.8)
            c.create_text(lx, ly, text="■ yeşil = geçilebilir açık yol   "
                                       "■ kırmızı = gidilemez (moloz / kapalı)",
                          fill=SOLUK, font=self.f_kucuk, anchor="w")
        for yol, xm in ((1, 12.5), (2, 25.0), (3, 37.5)):
            secili = (yol == acik)
            px0, py0 = self._mxy(xm - 3, 4)
            px1, py1 = self._mxy(xm + 3, 46)
            if secili:
                c.create_rectangle(px0, py0, px1, py1, fill=YESIL,
                                   stipple="gray25", outline=YESIL, width=2)
            elif acik is not None:
                c.create_rectangle(px0, py0, px1, py1, fill=KIRMIZI,
                                   stipple="gray25", outline=KIRMIZI,
                                   width=1, dash=(3, 3))
            else:
                c.create_rectangle(px0, py0, px1, py1, outline="#25303c",
                                   width=1, dash=(3, 3))
            tx, ty = self._mxy(xm, -2.4)          # arena çerçevesinin ALTINA yaz
            c.create_text(tx, ty, text=f"{yol}·{ROAD_LABEL[yol].upper()}",
                          fill=YESIL if secili else SOLUK, font=self.f_kucuk)
            if not secili and acik is not None:
                kx, ky = self._mxy(xm, 25)
                c.create_text(kx, ky, text="✕ KAPALI", fill="#ff8878",
                              font=self.f_kucuk)

        # İKA-KB (başlangıç, güney) ve HB (hedef, kuzey)
        kx, ky = self._mxy(25, 2)
        c.create_rectangle(kx - 12, ky - 12, kx + 12, ky + 12, outline=MAVI, width=2)
        c.create_text(kx + 16, ky, text="İKA-KB", fill=MAVI, font=self.f_kucuk,
                      anchor="w")
        hx, hy = self._mxy(25, 48)
        c.create_rectangle(hx - 12, hy - 12, hx + 12, hy + 12, outline=KIRMIZI, width=2)
        c.create_text(hx, hy, text="H", fill=KIRMIZI, font=self.f_orta)
        c.create_text(hx, hy - 20, text="HB (hedef)", fill=KIRMIZI, font=self.f_kucuk)

        # rota: ref_xy + yerel waypoint'ler
        if self.rota and not self.rota_yok and self.rota.get("waypoints"):
            ref = self.rota.get("ref_xy") or [25.0, 2.0]
            noktalar = [(ref[0] + dx, ref[1] + dy) for dx, dy in self.rota["waypoints"]]
            noktalar.insert(0, (ref[0], ref[1]))
            pks = [self._mxy(x, y) for x, y in noktalar]
            for (ax, ay), (bx, by) in zip(pks, pks[1:]):
                c.create_line(ax, ay, bx, by, fill=YESIL, width=3, arrow="last")
            rx, ry = self._mxy(ref[0], ref[1])
            c.create_oval(rx - 5, ry - 5, rx + 5, ry + 5, fill=SARI, outline="")
            c.create_text(rx - 16, ry, text="ref", fill=SARI, font=self.f_kucuk, anchor="e")

        if self.rota_yok:
            sebep = self.rota_yok.get("sebep", "bilinmeyen neden")
            detay = self.rota_yok.get("detay")
            w, h = c.winfo_width() or S(480), c.winfo_height() or S(420)
            bant_h = max(S(42), h // 10)
            c.create_rectangle(0, 0, w, bant_h, fill=KIRMIZI, outline="")
            metin = f"ROTA YOK — {sebep} · İKA GÜVENLİ DURUŞTA"
            if detay:
                metin += f"\n{detay}"
            c.create_text(S(12), bant_h // 2, text=metin, fill="white",
                          font=self.f_kucuk, anchor="w", width=w - S(24))

    def _inset_ciz(self):
        """Mini genel-saha: İHA-UB 300×300 m çerçevesi + HTAB + İHA-İB (mavi)
        + İHA canlı konum izi (heartbeat x,y alanlarından)."""
        c = self.harita
        c.delete("inset")
        gw = int(c.winfo_width() or S(480))
        b = S(132)
        x1, y0 = gw - 8, 8
        x0, y1 = x1 - b, y0 + b
        c.create_rectangle(x0, y0, x1, y1, fill="#0d1318", outline=CIZGI,
                           tags="inset")

        def ub(px, py):        # İHA-UB metre (0-300, y kuzey) → inset pikseli
            return (x0 + px / 300 * b, y1 - py / 300 * b)

        c.create_text(x0 + 4, y0 + 8, text="İHA-UB 300×300 m", fill=SOLUK,
                      font=self.f_kucuk, anchor="w", tags="inset")
        hx0, hy0 = ub(125, 125)
        hx1, hy1 = ub(175, 175)
        c.create_rectangle(hx0, hy0, hx1, hy1, outline=SARI, tags="inset")
        c.create_text(*ub(150, 110), text="HTAB", fill=SARI,
                      font=self.f_kucuk, tags="inset")
        ix0, iy0 = ub(40, 230)
        ix1, iy1 = ub(70, 260)
        c.create_rectangle(ix0, iy0, ix1, iy1, outline=MAVI, fill=MAVI,
                           stipple="gray25", tags="inset")
        c.create_text(*ub(55, 215), text="İHA-İB", fill=MAVI,
                      font=self.f_kucuk, tags="inset")
        if len(self.iha_iz) >= 2:
            pts = []
            for mx, my in self.iha_iz:
                pts.extend(ub(mx, my))
            c.create_line(*pts, fill=YESIL, width=1, tags="inset")
            sx, sy = ub(*self.iha_iz[-1])
            c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=YESIL,
                          outline="", tags="inset")

    # ── Ağ dinleyici (arka plan iş parçacığı) ────────────────────────────────
    def _dinle(self):
        while True:
            try:
                d, adr = self.link.recv()
            except OSError as exc:
                # Soket GERÇEKTEN kapandıysa (pencere kapanıyor) çık. Aksi hâlde
                # bu geçici bir ağ hatasıdır ve dinleyiciyi KALICI öldürmemeli:
                # eskiden tek bir ölü akran hakem ekranını sessizce sağırlaştırıyordu
                # (ekran donmuyor ama hiçbir çerçeve işlenmiyordu).
                soket = getattr(self.link, "sock", None)
                if soket is None or soket.fileno() == -1:
                    return
                # Tk thread-güvenli değil; günlüğe ana döngü kuyruğundan yazılır.
                self.algi_kuyruk.put(
                    ("log", f"⚠ ağ hatası yok sayıldı: {type(exc).__name__}: {exc}"))
                continue
            if not d:
                continue
            for m in self.reader.feed(d):
                self.gelen.put((m, adr))

    # ── Ana döngü tiki ───────────────────────────────────────────────────────
    def _tik(self):
        while not self.gelen.empty():
            m, adr = self.gelen.get()
            # Tek bir BOZUK çerçeve hakem ekranını KALICI dondurmamalı: _tik
            # kendi zincirini `after(120)` ile kuruyor, burada fırlayan bir
            # istisna o zinciri kopartıyor ve saat, günlük, kronometreler,
            # butonlar hepsi ölüyordu. Ölçüldü: `ref_xy=None` taşıyan geçerli
            # bir OPEN_ROUTE (protokol buna izin veriyor, protocol.py:44-45)
            # `m['ref_xy'][0]` ile TypeError üretiyordu.
            try:
                self._mesaj_isle(m, adr)
            except Exception as exc:
                self._logla(f"⚠ BOZUK ÇERÇEVE yok sayıldı — "
                            f"{type(exc).__name__}: {exc}", "sari")
        while not self.algi_kuyruk.empty():
            paket = self.algi_kuyruk.get()
            if paket[0] == "sonuc":
                _, gorsel, bilgi, log_satiri = paket
                self._algi_sonucu_goster(gorsel, bilgi)
                self._logla(log_satiri, "yesil")
            elif paket[0] == "hata":
                # Worker hatasi yalniz gunluge dusunce algi paneli sonsuza dek
                # "isleniyor" gorunuyordu. Hatayi ayni panelde gorunur kil.
                self.lbl_algi_img.config(
                    image="", text="ALGİ HATASI — ayrıntı aşağıda")
                self.lbl_algi_bilgi.config(text=paket[1])
                self._logla(paket[1], "sari")
            else:
                self._logla(paket[1], "mavi")
        self._durum_tazele()
        self.kok.after(120, self._tik)

    def _mesaj_isle(self, m, adr):
        tip = m.get("type")
        if tip == "OPEN_ROUTE":
            guven_reddi = rota_guven_reddi(m.get("conf"))
            if guven_reddi is not None:
                self._open_route_guven_reddini_goster(m, guven_reddi)
                return
            self._dugum_adresini_ogren("iha", adr)
            yeni = (self.rota is None) or (m["seq"] != self.rota["seq"])
            self.rota, self.rota_adr = m, adr
            self.rota_yok = None
            self.rx_alim[m["seq"]] = self.rx_alim.get(m["seq"], 0) + 1
            if yeni:
                self.onaylandi = False
                self.tespit_onayli = False
                self.sayac["OPEN_ROUTE"] += 1
                self._logla(f"OPEN_ROUTE  yol={m['road']}({m['label']}) "
                            f"güven={m['conf']} seq={m['seq']} wp={len(m['waypoints'])}",
                            "yesil")
                if self.t_iha1:
                    self._logla("⚠ GEÇERSİZLİK RİSKİ: aktarım İHA inişinden SONRA "
                                "geldi — şartname §6.4: aktarım HAVADA tamamlanmalı!",
                                "sari")
                self.lbl_karar.config(text=f"{m['road']} · {m['label'].upper()}", fg=YESIL)
                # ref_xy protokolce None OLABILIR (protocol.py:44-45) ve
                # iha_sender geometri dogrulamasini yalniz ika/broadcast akrani
                # varken kosar — yani "--yks" tek hedefliyken None gelir.
                _ref = m.get("ref_xy") or ("—", "—")
                self._detay_base = (f"seq={m['seq']} · ref=({_ref[0]}, "
                                    f"{_ref[1]}) m · {len(m.get('waypoints') or [])} waypoint")
                self._rota_analiz(m)
                self.btn_onay.config(state="normal", bg=SARI,
                                     text="1) TESPİTİ DOĞRULA (§2.2.3)")
                self.lbl_onay.config(text="⚠ Hakem onayı BEKLENİYOR — İHA tekrar "
                                          "gönderimde (ACK yok)", fg=SARI)
                self._guven_ciz(m["conf"])
                self._harita_ciz()
                self._zincir(("Kamera (İHA)", "YOLOv8-seg", "Rota Üretimi",
                              "433 MHz TX", "YKS (bu ekran)"))
                if self.otomatik_onay:
                    self.kok.after(2500, self.onayla)
            # tekrar-gönderim mekanizması canlı izlensin (jüri: ACK'siz teslim yok)
            self.lbl_detay.config(
                text=f"{self._detay_base} · alım #{self.rx_alim[m['seq']]}")
        elif tip == "NO_ROUTE":
            self._dugum_adresini_ogren("iha", adr)
            onceki_seq = self.rota_yok.get("seq") if self.rota_yok else None
            yeni = m.get("seq") != onceki_seq
            self.rota_yok = m
            self.rx_alim[m["seq"]] = self.rx_alim.get(m["seq"], 0) + 1
            # NO_ROUTE da aktarımın teslim edildiğini kanıtlamalıdır. Bu bir
            # rota onayı değil, İKA'nın hareket etmeyeceği güvenlik bildirimidir.
            if adr is not None:
                self.link.send(encode(ack(m["seq"], "yks")), adr)
            elif isinstance(self.link, SerialLink):
                self.link.send(encode(ack(m["seq"], "yks")))
            self.sayac["ACK_TX"] += 1
            if yeni:
                sebep = m.get("sebep", "bilinmeyen neden")
                detay = m.get("detay")
                self.onaylandi = False
                self.tespit_onayli = False
                self.sayac["NO_ROUTE"] += 1
                self.lbl_karar.config(text="ROTA YOK", fg=KIRMIZI)
                self._detay_base = f"seq={m['seq']} · {sebep}"
                self.lbl_detay.config(text=self._detay_base +
                                      (f" · {detay}" if detay else ""))
                self.btn_onay.config(state="disabled", bg="#232e3a",
                                     text="ROTA YOK — ACK OTOMATİK GÖNDERİLDİ")
                self.lbl_onay.config(text="Costmap güvenli rota üretmedi; İKA hareket etmez.",
                                      fg=KIRMIZI)
                self._guven_ciz(0.0)
                self._harita_ciz()
                self._logla(f"NO_ROUTE · {sebep}"
                            + (f" · {detay}" if detay else "")
                            + " → güvenli duruş ACK'i gönderildi", "sari")
        elif tip == "IHA_LANDED":
            seq = m.get("seq")
            if (m.get("node") != "iha" or isinstance(seq, bool)
                    or not isinstance(seq, int)):
                return
            if adr is not None:
                self.link.send(encode(ack(seq, "yks")), adr)
            elif isinstance(self.link, SerialLink):
                self.link.send(encode(ack(seq, "yks")))
            self.sayac["ACK_TX"] += 1
            if seq != self.iha_landed_seq:
                self.iha_landed_seq = seq
                self.sayac["IHA_LANDED"] += 1
                self._logla(
                    f"IHA_LANDED · üretim uçuşu iniş kanıtı alındı → ACK ref={seq}",
                    "yesil",
                )
                # Operatör düğmesi güvenlik sinyali üretmez; tersine gerçek
                # protokol olayı mevcut UI/kronometre kaydını besler.
                self.iha_indi()
        elif tip == "HEARTBEAT":
            dugum = m.get("node", "?")
            self.son_hb[dugum] = time.time()
            self._dugum_adresini_ogren(dugum, adr)
            tel = {k: m[k] for k in ("alt", "hiz", "bat", "uydu") if k in m}
            if tel:
                self.tel[dugum] = tel
            if "mod" in m:
                self.mod[dugum] = m["mod"]
                if m["mod"] != "AUTO" and not self._manuel_uyarildi:
                    self._manuel_uyarildi = True
                    self._logla(f"⚠ {dugum.upper()} MANUEL MODA GEÇTİ — tam otonomi "
                                "ihlali: UÇUŞ GEÇERSİZ sayılır (§6.4)", "sari")
            if dugum == "iha" and "x" in m and "y" in m:
                self.iha_iz.append((float(m["x"]), float(m["y"])))
                del self.iha_iz[:-150]         # son 150 nokta
                # geofence: İHA-UB 300×300 dışına taşma = alan ihlali (§6.4)
                if not (0 <= m["x"] <= 300 and 0 <= m["y"] <= 300):
                    self._logla("⚠ ALAN İHLALİ: İHA-UB (300×300 m) dışına çıkıldı "
                                "— uçuş başarısız sayılır (§6.4)", "sari")
            self.sayac["HEARTBEAT"] += 1

    def _open_route_guven_reddini_goster(self, m, guven_reddi):
        """Eşik altı OPEN_ROUTE'u hakeme görünür kıl; rota ACK'i ASLA üretme."""
        sebep, detay = guven_reddi
        seq = m.get("seq")
        onceki_seq = (self.rota_yok.get("seq") if self.rota_yok else None)
        yeni = seq != onceki_seq
        self.rota_yok = {
            "type": "NO_ROUTE", "sebep": sebep, "detay": detay, "seq": seq,
            "kaynak_type": "OPEN_ROUTE",
        }
        self.rx_alim[seq] = self.rx_alim.get(seq, 0) + 1
        self.onaylandi = False
        self.tespit_onayli = False
        if yeni:
            self.sayac["OPEN_ROUTE_RED"] += 1
            self.lbl_karar.config(text="ROTA YOK", fg=KIRMIZI)
            self._detay_base = f"seq={seq} · {sebep}"
            self.lbl_detay.config(text=f"{self._detay_base} · {detay}")
            self.btn_onay.config(
                state="disabled", bg="#232e3a",
                text="DÜŞÜK GÜVEN — OPEN_ROUTE REDDEDİLDİ")
            self.lbl_onay.config(
                text="Rota güven eşiğinin altında; ACK gönderilmedi, İKA hareket etmez.",
                fg=KIRMIZI)
            self._guven_ciz(0.0)
            self._harita_ciz()
            self._logla(
                f"OPEN_ROUTE REDDEDİLDİ · {sebep} · {detay} · ACK YOK",
                "sari")
        self.lbl_detay.config(
            text=f"{self._detay_base} · alım #{self.rx_alim[seq]} · ACK YOK")

    def onayla(self):
        """Şartname §2.2.3 İKİ AŞAMALI hakem onayı: (1) güzergâh tespitinin
        doğrulanması, (2) İKA'ya aktarımın doğrulanması → ACK ancak 2. adımda."""
        if not self.rota or self.rota_yok or self.onaylandi:
            return
        if not self.tespit_onayli:
            self.tespit_onayli = True
            self._logla("HAKEM 1/2: güzergâh TESPİTİ doğrulandı (§2.2.3)", "sari")
            self.btn_onay.config(text="2) İKA'YA AKTARIMI ONAYLA → ACK", bg=SARI)
            self.lbl_onay.config(text="Tespit doğrulandı ✓ — İKA'ya aktarımın da "
                                      "onaylanması gerekiyor (§2.2.3 ikinci onay)",
                                 fg=SARI)
            return
        if self.rota_adr is not None:
            self.link.send(encode(ack(self.rota["seq"], "yks")), self.rota_adr)
        else:                                   # seri hat: adres kavramı yok
            self.link.send(encode(ack(self.rota["seq"], "yks")))
        self.onaylandi = True
        self.sayac["ACK_TX"] += 1
        if self.t_iha1 is not None:
            havada = " · ⚠ aktarım İHA inişinden SONRA (§6.4 geçersizlik riski)"
        elif self.iha_landed_seq is not None:
            havada = " · AKTARIM ZAMANI BİLİNMİYOR (IHA_LANDED kanıtı var)"
        else:
            havada = " · İHA henüz inmedi"
        self.btn_onay.config(state="disabled", bg=YESIL, text="ONAYLANDI ✓✓")
        self.lbl_onay.config(text=f"Hakem onayı tam — ACK(seq={self.rota['seq']}) "
                                  f"İHA'ya iletildi{havada}", fg=YESIL)
        self._logla(f"HAKEM 2/2: İKA'ya aktarım doğrulandı → ACK ref={self.rota['seq']}",
                    "sari")
        self._zincir(("Kamera (İHA)", "YOLOv8-seg", "Rota Üretimi",
                      "433 MHz TX", "YKS (bu ekran)", "İKA"))

    # ── Acil durum senaryoları (arıza emniyet tatbikatı) ─────────────────────
    # Davranışlar takım tasarımından: avionics_software.md "Arıza Emniyet
    # Senaryoları" tablosu + comms/ika_receiver.py gerçek failsafe'i + şartname
    # §6.4 (manuel müdahale = uçuş geçersiz → tüm aksiyonlar OTONOM olmalı).
    def senaryo(self, kod):
        if not self.demo:
            return
        if kod == "rc":
            self._logla("SENARYO · Kumanda (RC) bağlantısı KESİLDİ", "sari")
            self._logla("  → Görev tam otonom (AUTO): uçuş KESİNTİSİZ sürer.", "soluk")
            self._logla("  → Kumanda yalnız emniyet pilotu yetkisidir; şartname", "soluk")
            self._logla("    gereği manuel müdahale zaten uçuşu geçersiz kılar.", "soluk")
            self._ucus("RC YOK — OTONOM GÖREVE DEVAM (AUTO)", SARI)
            self.kok.after(6000, lambda: (
                self._ucus_normal(),
                self._logla("RC bağlantısı geri geldi — uçuş kipi değişmedi", "yesil")))
        elif kod == "yks":
            self.demo_durum["iha_hb"] = False
            self._logla("SENARYO · İHA↔YKS telsiz bağlantısı KESİLDİ", "sari")
            self._logla("  → İHA: tekrar gönderim + >3 sn'de güvenli bölgede", "soluk")
            self._logla("    LOITER; kesinti uzarsa OTONOM paraşütle iniş.", "soluk")
            self._ucus("BAĞLANTI KAYBI — GÜVENLİ BÖLGEDE LOITER", KIRMIZI)
            def yks_geri():
                self.demo_durum["iha_hb"] = True
                self._ucus_normal()
                self._logla("İHA bağlantısı DÖNDÜ — göreve devam", "yesil")
            self.kok.after(7000, yks_geri)
        elif kod == "ika":
            self.demo_durum["ika_hb"] = False
            self._logla("SENARYO · İKA bağlantısı KESİLDİ", "sari")
            self._logla("  → İKA failsafe (ika_receiver.py — GERÇEK davranış):", "soluk")
            self._logla("    GÜVENLİ DURMA; rota önbelleği KORUNUR.", "soluk")
            def ika_geri():
                self.demo_durum["ika_hb"] = True
                self._logla("İKA bağlantısı DÖNDÜ — kaldığı waypoint'ten devam", "yesil")
            self.kok.after(7000, ika_geri)
        elif kod == "bat":
            self._logla("SENARYO · Batarya KRİTİK (<%15)", "sari")
            self._logla("  → RTH + İHA-İB üzerinde OTONOM paraşüt inişi", "soluk")
            self._logla("    (manuel tetik -50 ceza; bu yüzden tetik otonom).", "soluk")
            self._ucus("KRİTİK BATARYA — RTH + OTONOM PARAŞÜT (İHA-İB)", KIRMIZI)
            self.kok.after(7000, self._ucus_normal)
        elif kod == "gnss":
            self._logla("SENARYO · GNSS fix KAYBI", "sari")
            self._logla("  → Barometrik irtifa tutuşu + yeniden fix bekleme;", "soluk")
            self._logla("    süre kritikleşirse otonom paraşütle güvenli iniş.", "soluk")
            self._ucus("GNSS YOK — BAROMETRİK TUTUŞ, FIX BEKLENİYOR", SARI)
            self.kok.after(7000, self._ucus_normal)
        elif kod == "algi":
            self._logla("SENARYO · Görüntü işleme zaman aşımı (>30 sn tespit yok)", "sari")
            self._logla("  → Tarama deseni BİR KEZ yinelenir; yine yoksa YKS'ye", "soluk")
            self._logla("    'TESPİT YOK' bildirilir (yanlış yönlendirme yasak;", "soluk")
            self._logla("    rota sağlamlık süzgeci <3 waypoint'te göndermez).", "soluk")
            self._ucus("ALGI ZAMAN AŞIMI — TARAMA YİNELENİYOR", SARI)
            self.kok.after(7000, self._ucus_normal)

    def _rota_analiz(self, m):
        """Segment bazlı eksen değişimi tablosu: Δx/Δy, uzunluk, yön, dönüş."""
        wps = m.get("waypoints") or []
        satirlar = []
        onceki = (0.0, 0.0)                 # referans noktasına göre yerel
        onceki_yon = None
        toplam = yanal = 0.0
        keskin = 0.0
        for i, (x, y) in enumerate(wps, 1):
            dx, dy = x - onceki[0], y - onceki[1]
            uz = math.hypot(dx, dy)
            toplam += uz
            yanal += abs(dx)
            yon = math.degrees(math.atan2(dx, dy))       # 0° = kuzey (ileri)
            kimden = "ref " if i == 1 else f"wp{i-1:<2}"
            satir = (f"{kimden}→wp{i:<2} Δx{dx:+5.1f} Δy{dy:+5.1f} · "
                     f"{uz:4.1f} m · yön {yon:+6.1f}°")
            if onceki_yon is not None:
                donus = (yon - onceki_yon + 180) % 360 - 180
                keskin = max(keskin, abs(donus))
                satir += f" · dönüş {donus:+5.1f}°"
            satirlar.append(satir)
            onceki, onceki_yon = (x, y), yon
        if satirlar:
            satirlar.append(f"TOPLAM {toplam:.1f} m yol · yanal |Δx| {yanal:.1f} m "
                            f"· en keskin dönüş {keskin:.0f}°")
        self.rota_metin.config(state="normal")
        self.rota_metin.delete("1.0", "end")
        self.rota_metin.insert("end", "\n".join(satirlar) or "rota verisi yok")
        self.rota_metin.config(state="disabled")

    def _ucus(self, metin, renk):
        self.lbl_ucus.config(text=f"İHA UÇUŞ DURUMU: {metin}", fg=renk)

    def _ucus_normal(self):
        self.lbl_ucus.config(text="İHA UÇUŞ DURUMU: OTONOM GÖREV (AUTO)", fg=YESIL)

    # ── Canlı algı: v3 modeliyle GERÇEK çıkarım ──────────────────────────────
    # Karar zinciri sahadakiyle AYNI: codes/rpi_inference.py'nin get_masks +
    # analyze_path fonksiyonları kullanılır (kopya algoritma yok).
    # `kompozit` ILK SIRADA ve acilis kaynagidir: uc-kapili arena mantiginin
    # GECERLI oldugu tek kume odur (yer gercegi manifest'te). Digerleri listede
    # KALIR — `drone` bir otopark, `gemini`/`val` afet/yol fotografi; domain
    # boslugunu hakeme gostermek icin degerlidirler (REVIEW_LOG D-53).
    ALGI_KAYNAKLAR = ("kompozit", "drone", "gemini", "test", "val")
    # T58 (kullanici karari, REVIEW_LOG D-82/D-83): uretim modeli v21 -> v24.
    # Bu sabit hakem ekranini SAHA DONANIMIYLA ayni modele baglar; `jetson_paket/
    # models/` ve HER IKI `JETSON_KILAVUZ.md` ayni surume cevrildi. Yalniz
    # burasi cevrilirse ekran ile saha FARKLI MODELE duser (D-58/D-60 sinifi).
    ALGI_MODEL_DOSYA = "navitas_seg_v24_best.pt"
    # T36: cikarim esigi URETIMDEN gelir. `codes/rpi_inference.py` `run_image`
    # yolunda predict esigi `--conf` argumaniyla verilir, varsayilani 0.30
    # (`:1116`). GUI kendi esigini SECMEZ; bu deger uretimin varsayilanidir ve
    # `tests/test_yks_gui_uretim_hizasi.py` onu kaynaktan okuyup kilitler —
    # uretim varsayilani degisirse test duser, ekran sessizce ayrismaz.
    ALGI_PREDICT_CONF = 0.30
    # Kompozit kume yer gercegi. SALT GOSTERIM: karar yoluna GIRMEZ (aksi hâlde
    # test kendi kendini dogrular). Bkz. test_beklenen_serit_karara_sizmiyor.
    ALGI_KOMPOZIT_DIZIN = ("data", "arena_kompozit")

    def _algi_gorseller(self):
        import pathlib
        kok_dizin = pathlib.Path(__file__).resolve().parents[1]
        dizinler = {
            "kompozit": kok_dizin.joinpath(*self.ALGI_KOMPOZIT_DIZIN) / "images",
            "gemini": kok_dizin / "test_images" / "gemini",
            "test": kok_dizin / "test_images" / "test" / "images",
            "val": kok_dizin / "dataset" / "rescuenet_yolo" / "images" / "val",
            "drone": kok_dizin / "data" / "raw_frames",
        }
        d = dizinler[self.algi_kaynak]
        if not d.is_dir():
            return []
        return sorted(p for p in d.rglob("*")
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg"))

    def _kompozit_yer_gercegi(self):
        """Kompozit kümenin manifest'inden {dosya_adı: beklenen_açık_şerit}.

        SALT GÖSTERİM. Bu değer karar yoluna GİRMEZ — girseydi ekran kendi
        beklentisini doğrulamış olurdu (D-15 sınıfı vakum kapı).

        Fail-closed: manifest okunamazsa sessizce boş dönmez, hatayı yükseltir;
        çağıran hatayı hakem günlüğüne yazar. "Yer gerçeği yok" ile "yer
        gerçeği okunamadı" ekranda aynı görünemez.
        """
        import json
        import pathlib
        kok_dizin = pathlib.Path(__file__).resolve().parents[1]
        mf = kok_dizin.joinpath(*self.ALGI_KOMPOZIT_DIZIN) / "manifest.json"
        veri = json.loads(mf.read_text(encoding="utf-8"))
        gercek = {}
        for ornek in veri.get("ornekler", []):
            arena = ornek.get("arena")
            cikti = ornek.get("cikti")
            if not arena or not cikti:
                continue
            serit = arena.get("acik_serit")
            if serit is not None:
                gercek[pathlib.Path(cikti).name] = int(serit)
        if not gercek:
            raise ValueError(f"manifest'te acik_serit taşıyan örnek yok: {mf}")
        return gercek

    def _kompozit_olcekleri(self):
        """Kompozit kümenin manifest'inden {dosya_adı: mpp}.

        T44 · Halka 5: ekran, ölçeği kaynağından okur. Kompozit küme
        `arena.mpp` taşır (kontrollü kompozit varsayımı — gerçek kamera
        ölçümü DEĞİL, manifest kendi böyle beyan ediyor).

        Fail-closed: manifest okunamaz/bozuksa yükseltir; çağıran hatayı
        hakem günlüğüne yazar ve ölçeksiz sayar. Sessiz varsayılan YOK.
        """
        import json
        import pathlib
        kok_dizin = pathlib.Path(__file__).resolve().parents[1]
        mf = kok_dizin.joinpath(*self.ALGI_KOMPOZIT_DIZIN) / "manifest.json"
        veri = json.loads(mf.read_text(encoding="utf-8"))
        olcekler = {}
        for ornek in veri.get("ornekler", []):
            arena = ornek.get("arena")
            cikti = ornek.get("cikti")
            if not arena or not cikti:
                continue
            mpp = arena.get("mpp")
            if olcek_gecerli_mi(mpp):
                olcekler[pathlib.Path(cikti).name] = float(mpp)
        if not olcekler:
            raise ValueError(f"manifest'te gecerli mpp tasiyan ornek yok: {mf}")
        return olcekler

    def _kaynak_olcegi(self, yol):
        """Kaynağa göre `(mpp, açıklama)`. Ölçek yoksa `(None, sebep)`.

        ⚠ **Ölçek uydurulmaz.** `drone` / `gemini` / `val` / `test` kümelerinde
        telemetri yok; ölçek de yok. Orada `mpp=None` dönmek "kısıt yok" değil,
        `rota_olcek_reddi` ile `OLCEK_YOK` demektir (CONTRACTS §5.2/1).
        """
        if self.algi_kaynak != "kompozit":
            return None, (f"{self.algi_kaynak} kümesinde telemetri/ölçek yok "
                          "— irtifa+FOV bilinmiyor")
        mpp = self._kompozit_olcekleri().get(yol.name)
        if mpp is None:
            return None, f"manifest'te {yol.name} için mpp yok"
        return mpp, "manifest (kontrollü kompozit varsayımı)"

    def gorunum(self, ad):
        self.gorunum_adi = ad
        if ad == "harita":
            self.algi_cerceve.pack_forget()
            self.harita.pack(padx=10, pady=(4, 6), fill="both", expand=True)
            self.btn_gor_harita.config(fg=BG, bg=YESIL)
            self.btn_gor_algi.config(fg=METIN, bg="#232e3a")
            self._harita_ciz()
        else:
            self.harita.pack_forget()
            self.algi_cerceve.pack(fill="both", expand=True)
            self.btn_gor_algi.config(fg=BG, bg=YESIL)
            self.btn_gor_harita.config(fg=METIN, bg="#232e3a")
            self._algi_iste()

    def algi_sonraki(self):
        if self.gorunum_adi != "algi":
            return
        self.algi_idx += 1
        self._algi_iste()

    def algi_onceki(self):
        if self.gorunum_adi != "algi":
            return
        self.algi_idx -= 1
        self._algi_iste()

    def algi_kaynak_degistir(self):
        if self.gorunum_adi != "algi":
            return
        sira = self.ALGI_KAYNAKLAR
        self.algi_kaynak = sira[(sira.index(self.algi_kaynak) + 1) % len(sira)]
        self.algi_idx = 0
        aciklama = {"kompozit": "kontrollü arena kompoziti — YER GERÇEĞİ var",
                    "gemini": "arena tipi görseller",
                    "test": "takım test seti (test_images/test)",
                    "val": "RescueNet doğrulama seti",
                    "drone": "gerçek nadir drone kareleri (OTOPARK, arena değil)"
                    }[self.algi_kaynak]
        self._logla(f"ALGI kaynağı: {self.algi_kaynak} ({aciklama})", "mavi")
        self._algi_iste()

    def _algi_iste(self):
        if self.algi_mesgul:
            return
        gorseller = self._algi_gorseller()
        if not gorseller:
            self.lbl_algi_bilgi.config(
                text=f"Kaynak boş: {self.algi_kaynak} — "
                     "val için dataset/rescuenet_yolo üretilmiş olmalı")
            return
        yol = gorseller[self.algi_idx % len(gorseller)]
        self.algi_mesgul = True
        self.lbl_algi_bilgi.config(text=f"{yol.name} işleniyor… "
                                        + ("( modeli yükleniyor — ilk sefer "
                                           "birkaç sn)" if self.algi_model is None
                                           else ""))
        threading.Thread(target=self._algi_kos, args=(yol,), daemon=True).start()

    def _algi_kos(self, yol):
        """Arka plan iş parçacığı: v ile gerçek çıkarım + saha karar zinciri."""
        try:
            import pathlib
            import sys as _sys
            import cv2
            import numpy as np
            kok_dizin = pathlib.Path(__file__).resolve().parents[1]
            _sys.path.insert(0, str(kok_dizin / "codes"))
            from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,
                                       _preprocess, _rota_kararini_esikle,
                                       analyze_path, get_masks)

            if self.algi_model is None:
                from ultralytics import YOLO
                model_yolu = kok_dizin / "models" / self.ALGI_MODEL_DOSYA
                self.algi_model = YOLO(str(model_yolu))
                import hashlib
                _h = hashlib.sha256()
                with open(model_yolu, "rb") as _fh:
                    for _blok in iter(lambda: _fh.read(1 << 20), b""):
                        _h.update(_blok)
                self.algi_kuyruk.put(("log",
                    f"{model_yolu.stem} modeli yüklendi: {model_yolu.name} "
                    f"(SHA {_h.hexdigest()[:8]})"))

            img = cv2.imread(str(yol))
            t0 = time.perf_counter()
            # ── ÜRETİM ALGI HATTI — GUI kendi hattını KURMAZ (T36 / madde 16) ──
            # `CONTRACTS.md` §11.2: Halka 3 (Çıkarım) ve Halka 4 (Maske) sahibi
            # `codes/rpi_inference.py`. Aşağıdaki sıra o dosyanın `run_image`
            # gövdesinin (:920-932) birebir aynısıdır ve parametreler oradan
            # okunur — çıplak sabit yazılmaz. Jetson saha paketi de bu dosyanın
            # BAYT-BİREBİR kopyasıdır, yani hakem ekranı sahanın gerçekten
            # koştuğu yolu gösterir.
            #
            # `simulation/scripts/iha_perceive.py` bilerek KULLANILMAZ: §11.1/1
            # `simulation/` altındaki hiçbir dosyanın halka sahibi olmasını
            # yasaklar ve o dosya saha paketinde hiç yoktur. İki üretim yolu
            # 67 gerçek karenin 13'ünde birbirinden ayrışıyor (REVIEW_LOG D-58);
            # hakem ekranı sözleşmenin sahip yazdığı yola hizalanır.
            sq, small, icerik = _preprocess(img)
            h, w = sq.shape[:2]
            sonuc = self.algi_model.predict(
                small, imgsz=INFER_SIZE, conf=self.ALGI_PREDICT_CONF,
                verbose=False)
            maskeler = get_masks(sonuc, h, w)
            maskeler = _maskeleri_icerige_kirp(maskeler, icerik)
            trav, blok = maskeler[0], maskeler[1]
            ms = (time.perf_counter() - t0) * 1000
            cikarim = "üretim (rpi_inference)"
            # Ham zemin maskesini koru: §6.4'te MASKE_YOK, modelin hiç zemin
            # ÜRETMEMESİ demektir. Engeli girdiden burada oyarsak model zemin
            # bulmuş olsa bile tam örtülen sahneyi yanlış MASKE_YOK raporlarız.
            trav_serbest = trav.copy()
            trav_serbest[blok > 0] = 0
            # ── ÖLÇEK (Halka 5) — T44 · CONTRACTS §5 ───────────────────────
            # T43 ölçek kapısını üç GÖREV çağrı yerine koydu; GUI onları
            # çağırmıyordu ve 16 otopark karesinin 16'sında ekran karar
            # verirken üretim `OLCEK_YOK` diyordu. İki ayrı kusur:
            #   (1) hakeme SİSTEM KISITI sahne kusuru gibi gösteriliyordu;
            #   (2) C-uzayı ekrana hiç ulaşmıyordu (mpp yok -> r_gerekli_px yok).
            # Üretimin kapısı KOPYALANMAZ, `rota_olcek_reddi` çağrılır.
            mpp, olcek_notu = None, None
            try:
                mpp, olcek_notu = self._kaynak_olcegi(yol)
            except Exception as _oe:      # fail-closed: sessiz varsayılan YOK
                olcek_notu = f"manifest okunamadı: {type(_oe).__name__}: {_oe}"
                self.algi_kuyruk.put(("log",
                    f"⚠ ÖLÇEK OKUNAMADI: {olcek_notu} — ölçeksiz sayılıyor, "
                    "rota yayınlanmaz"))
            olcek_reddi = rota_olcek_reddi(mpp)

            # Karar üretimin KENDİ çağrısıdır; `return_clean/reason/olcum`
            # yalnız GÖSTERİM için ek dönüşlerdir — aynı saf fonksiyon, aynı
            # girdi, aynı karar. İkinci bir predict yapılmaz.
            (ham_yol, guven, ham_wps, koridor,
             karar_reddi, rota_olcumu) = analyze_path(
                trav, icerik=icerik, engel_mask=blok, mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            # ONCELIK (CONTRACTS SS6.4/3): YAPISAL ret ezilmez. `analyze_path`
            # zaten reddettiyse sebebi KORUNUR — olcek eksikligi bir yapilandirma
            # boslugu, `ZEMIN_MASKESI_SUPHELI` ise ALGI ARIZASIDIR; hakeme
            # gosterilmesi gereken daha derin olandir.
            if olcek_reddi is not None and karar_reddi is None:
                # Ölçek yoksa gövde açıklığı doğrulanamaz -> rota YAYINLANMAZ.
                ham_yol, guven, ham_wps = None, 0.0, []
                karar_reddi = olcek_reddi
            # K-B üretimin kendi eşikleyicisiyle uygulanır — kopya eşik yok.
            yol_no, guven, wps, karar_reddi = _rota_kararini_esikle(
                ham_yol, guven, ham_wps, karar_reddi)

            # Görselleştirme İLKESİ: yalnızca kararın KULLANDIĞI temiz koridor
            # basılır (ham maskedeki gürültü blobları çizilmez — onlar kararı
            # zaten etkilemiyor). Koridor ORİJİNAL renkte kalır; geri kalan her
            # yer KIRMIZI (geçilemez), tespitli moloz KOYU kırmızı; sınır +
            # rota SARI. Yeşil kullanılmaz.
            gorsel = sq.copy()
            kirmizi = np.zeros_like(sq)
            kirmizi[:] = (40, 40, 210)                      # BGR kırmızı
            if yol_no is not None and wps:
                acik_ton = cv2.addWeighted(sq, 0.45, kirmizi, 0.55, 0)
                koyu_ton = cv2.addWeighted(sq, 0.20, kirmizi, 0.80, 0)
                # SÜRÜŞ KORİDORU: rota merkez hattı ± ölçülen yol yarıçapı
                # (distance transform medyanı), geçilebilir alanla kesişik —
                # İKA'nın gerçekten süreceği bant. Bilgi satırında etiketli.
                # Tamami gecilebilir bir maskede OpenCV, goruntu disinda
                # sifir sinir gormedigi icin FLT_MAX dondurebilir. Bu deger
                # ``int(median)`` ile cizgi kalinligina cevrilince ALGİ worker'i
                # sessizce dusuruyordu. Goruntu disini kapali sayan 1 px cerceve
                # hem geometrik olarak dogru hem de mesafeyi sonlu tutar.
                sinirli_koridor = cv2.copyMakeBorder(
                    koridor, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
                dist = cv2.distanceTransform(
                    sinirli_koridor, cv2.DIST_L2, 5)[1:-1, 1:-1]
                yarich = [dist[py, px] for (px, py) in wps if dist[py, px] > 0]
                yr = int(np.median(yarich)) if yarich else max(8, w // 20)
                yr = max(1, min(yr, max(1, min(h, w) // 2)))
                band = np.zeros((h, w), np.uint8)
                cv2.polylines(band, [np.array(wps, np.int32)], False, 1,
                              thickness=max(4, 2 * yr))
                band &= koridor
                gorsel[band == 0] = acik_ton[band == 0]     # bant dışı → kırmızı
                gorsel[blok > 0] = koyu_ton[blok > 0]       # moloz → koyu kırmızı
                # bant sınırı: yumuşatılmış, sadeleştirilmiş SARI kontur
                yumusak = cv2.GaussianBlur(band * 255, (0, 0),
                                           max(2.0, w / 500))
                yumusak = (yumusak > 127).astype(np.uint8)
                konturlar, _ = cv2.findContours(yumusak, cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
                for k in konturlar:
                    k = cv2.approxPolyDP(k, 0.002 * cv2.arcLength(k, True), True)
                    cv2.drawContours(gorsel, [k], -1, (0, 220, 255),
                                     max(3, w // 250))
            else:
                # TESPİT YOK: kırmızı sele boğma — dürüst uyarı bandı bas
                bant_h = max(60, h // 10)
                gorsel[:bant_h] = cv2.addWeighted(
                    sq[:bant_h], 0.25, kirmizi[:bant_h], 0.75, 0)
                ret_metin = (f"ROTA YOK: {karar_reddi[0]}"
                             if karar_reddi else
                             "ACIK YOL TESPIT EDILEMEDI")
                cv2.putText(gorsel, ret_metin + " (guvenli: rota gonderilmez)",
                            (16, int(bant_h * 0.65)),
                            cv2.FONT_HERSHEY_SIMPLEX, max(0.6, w / 1800),
                            (255, 255, 255), max(1, w // 900))
            # şerit sınırları — letterbox İÇERİK kutusundan (§8). Tuvalden
            # (w//3) çizmek dolgu kadar kaydırır ve ekranda gösterilen şerit
            # `analyze_path`'in kullandığı şeritle örtüşmezdi.
            _ix0, _iy0, _iw, _ih = icerik
            for _k in (1, 2):
                _x = int(_ix0 + _k * _iw / 3.0)
                cv2.line(gorsel, (_x, _iy0), (_x, _iy0 + _ih),
                         (110, 110, 110), 1)
            if wps:
                pts = np.array(wps, dtype=np.int32)
                cv2.polylines(gorsel, [pts], False, (0, 220, 255), max(2, w // 300))
                for (px, py) in wps:
                    cv2.circle(gorsel, (px, py), max(3, w // 150), (0, 220, 255), -1)
                # Kalin sari cizgi merkez hatti guvenli olsa bile arac
                # konturuna tasabilir. Engel katmanini en son basarak arac
                # etiketini rota cizgisinin altinda birakma.
                if yol_no is not None:
                    gorsel[blok > 0] = koyu_ton[blok > 0]

            trav_oran = 100.0 * trav_serbest.mean()
            blok_oran = 100.0 * blok.mean()
            karar = (f"{yol_no}·{ROAD_LABEL[yol_no].upper()}" if yol_no else
                     (f"ROTA YOK · {karar_reddi[0]}" if karar_reddi
                      else "TESPİT YOK"))
            try:
                guven_sayi = float(guven)
                if isinstance(guven, bool) or not math.isfinite(guven_sayi):
                    raise ValueError("gecersiz rota guveni")
                # K-B sinirinda iki hane, 0.199 gibi bir reddi 0.20 diye
                # gosterip operatoru yaniltir. Sozlesme esigi de uc hanelidir.
                guven_metin = f"{guven_sayi:.3f}"
            except (TypeError, ValueError, OverflowError):
                # Fail-closed guven reddi, hata metnini gosterirken tekrar
                # bicimlendirme istisnasiyla worker'i dusurmemeli.
                guven_metin = repr(guven)
            bilgi = (f"{self.algi_kaynak}/{yol.name} → karar: {karar} · "
                     f"güven {guven_metin} · {ms:.0f} ms · çıkarım: {cikarim} · "
                     f"predict conf {self.ALGI_PREDICT_CONF:.2f}"
                     + f" · traversable %{trav_oran:.0f} · blocked %{blok_oran:.0f}"
                      f" · gösterim: sürüş koridoru · model: {self.ALGI_MODEL_DOSYA}")
            if self.algi_kaynak == "kompozit":
                # YER GERÇEĞİ — yalnızca GÖSTERİM. Karar zaten yukarıda
                # verilmiştir; bu satır onu değiştirmez, yalnız hakemin
                # "sistem 2 dedi, beklenen 2" diye görmesini sağlar.
                try:
                    _beklenen = self._kompozit_yer_gercegi().get(yol.name)
                except Exception as _e:      # fail-closed: sessiz boş GÖSTERME
                    self.algi_kuyruk.put(("log",
                        f"⚠ KOMPOZİT YER GERÇEĞİ OKUNAMADI: "
                        f"{type(_e).__name__}: {_e} — beklenen şerit "
                        "gösterilemiyor (karar bundan etkilenmez)"))
                    bilgi += " · beklenen şerit: OKUNAMADI"
                else:
                    if _beklenen is None:
                        bilgi += " · beklenen şerit: manifest'te YOK"
                    else:
                        _uyum = ("UYUMLU" if yol_no == _beklenen
                                 else ("ÇEKİMSER" if yol_no is None
                                       else "UYUMSUZ"))
                        bilgi += (f" · beklenen şerit {_beklenen}"
                                  f" → {_uyum}")
            # T48 — ZEMİN MASKESİ ŞÜPHELİ: hakem sistemin NEDEN karar
            # vermediğini görmeli. Eşik sözleşmeden okunur, çıplak yazılmaz.
            if karar_reddi is not None                     and karar_reddi[0] == ZEMIN_MASKESI_SUPHELI_SEBEBI:
                _kap = 100.0 * zemin_kaplamasi(trav, icerik)
                bilgi += (f" · ⚠ ZEMİN MASKESİ ŞÜPHELİ · kaplama %{_kap:.0f}"
                          f" (tavan %{100.0 * ZEMIN_KAPLAMA_TAVANI:.0f})")
            # ÖLÇEK KANITI: hakem "C-uzayı uygulandı mı" sorusunu ekrandan
            # cevaplayabilmeli. Ölçeksiz kip SESSİZ kalamaz (§5.2/3).
            if mpp is not None and rota_olcumu is not None                     and rota_olcumu.get("r_gerekli_px"):
                bilgi += (f" · ölçek {mpp:.4f} m/px ({olcek_notu})"
                          f" · gövde açıklığı {rota_olcumu['r_gerekli_px']:.1f} px"
                          " · C-uzayı UYGULANDI")
            else:
                bilgi += (f" · ölçek YOK ({olcek_notu})"
                          " · C-uzayı UYGULANAMADI")
            if rota_olcumu is not None:
                # Kanıt satırı: güvenin NEREDEN geldiği ekranda görünür olmalı.
                n1, n2, n3 = rota_olcumu["seritler"]
                bilgi += (f" · darboğaz {rota_olcumu['darbogaz_px']:.1f} px"
                          f" @ şerit {rota_olcumu['darbogaz_serit']}"
                          f" · rota şerit dağılımı {n1}/{n2}/{n3} px")
                if rota_olcumu["cok_seritli"]:
                    bilgi += " · ⚠ ROTA ŞERİT DEĞİŞTİRİYOR (tek etiket eksik kalır)"
            if karar_reddi is not None:
                bilgi += f" · {karar_reddi[1]}"
            _ad = self.ALGI_MODEL_DOSYA.rsplit(".", 1)[0]
            if rota_olcumu is not None and rota_olcumu["cok_seritli"]:
                # Hakem bunu kaçırmamalı: tek `road` etiketi rotanın tamamını
                # anlatmıyor. Fail-closed değil — rota doğrulanmış, yalnız ADI
                # eksik; kararı yumuşatmadan görünür kılıyoruz (SS6.4/3).
                self.algi_kuyruk.put(("log",
                    f"⚠ ROTA ŞERİT DEĞİŞTİRİYOR: darboğaz şerit "
                    f"{rota_olcumu['darbogaz_serit']}, dağılım "
                    f"{rota_olcumu['seritler']} px — yayınlanan `road` "
                    "yalnız darboğaz şeridini adlandırır"))
            self.algi_kuyruk.put(("sonuc", gorsel, bilgi,
                                  f"ALGI({_ad}) {yol.name} → {karar} "
                                  f"güven={guven_metin} · {ms:.0f} ms"))
        except Exception as e:
            self.algi_kuyruk.put(
                ("hata", f"ALGI HATASI: {type(e).__name__}: {e}"))
        finally:
            self.algi_mesgul = False

    def _algi_sonucu_goster(self, gorsel_bgr, bilgi):
        import cv2
        from PIL import Image, ImageTk
        h, w = gorsel_bgr.shape[:2]
        hedef_w, hedef_h = S(660), S(430)
        olcek = min(hedef_w / w, hedef_h / h)
        yeni = cv2.resize(gorsel_bgr, (int(w * olcek), int(h * olcek)),
                          interpolation=cv2.INTER_AREA)   # keskin küçültme
        rgb = cv2.cvtColor(yeni, cv2.COLOR_BGR2RGB)
        self._algi_foto = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.lbl_algi_img.config(image=self._algi_foto, text="")
        self.lbl_algi_bilgi.config(text=bilgi)

    # ── Demo / SS kontrolleri ("hile tuşları") ───────────────────────────────
    def yeni_tespit(self):
        """(demo) Taze OPEN_ROUTE üret — hakem onay akışı baştan izlenebilir."""
        if not self.demo:
            return
        import random
        yol = random.choice((1, 2, 3))
        hedef_dx = {1: 12.5, 2: 25.0, 3: 37.5}[yol] - 25.0
        wps, dy = [], 4.0
        for f in (0.35, 0.55, 0.70, 0.82, 0.90, 0.96, 1.0, 1.0):
            wps.append([round(hedef_dx * f + random.uniform(-1.2, 1.2), 1),
                        round(dy, 1)])
            dy += 5.6
        m = open_route(road=yol, conf=round(random.uniform(0.72, 0.97), 2),
                       ref_xy=[25.0, 2.0], waypoints=wps)
        self._logla(f"(demo) yeni tespit üretildi — yol {yol}", "mavi")
        self._mesaj_isle(m, ("127.0.0.1", self.link.port))

    def onay_sifirla(self):
        """(demo) Onay durumunu geri al — 'BEKLENİYOR' hali tekrar görüntülenir."""
        if not self.demo or not self.rota:
            return
        self.onaylandi = False
        self.tespit_onayli = False
        self.btn_onay.config(state="normal", bg=SARI,
                             text="1) TESPİTİ DOĞRULA (§2.2.3)")
        self.lbl_onay.config(text="⚠ Hakem onayı BEKLENİYOR — İHA tekrar "
                                  "gönderimde (ACK yok)", fg=SARI)
        self._logla("(demo) hakem onayı sıfırlandı — akış baştan izlenebilir", "mavi")

    # ── Görev kontrol & kronometre (şartname süreleri + §2.2.5 kilidi) ───────
    def _dugum_adresini_ogren(self, dugum, adr):
        """Dinamik adresi öğren; CLI ile pinlenen hedefi asla ezme."""
        if adr is not None and dugum not in self.sabit_adr:
            self.son_adr[dugum] = adr

    def _cmd_gonder(self, cmd, hedef_dugum):
        adr = self.son_adr.get(hedef_dugum)
        komut_mesaji = command(cmd, hedef_dugum)
        mesaj = encode(komut_mesaji)
        try:
            if isinstance(self.link, SerialLink):
                self.link.send(mesaj)
            elif adr is not None and adr[1]:
                self.link.send(mesaj, adr)
            else:
                self._logla(
                    f"CMD GÖNDERİLEMEDİ → {hedef_dugum}: {cmd} — UDP adresi yok",
                    "kirmizi",
                )
                return False
        except (OSError, TypeError, ValueError) as exc:
            self._logla(
                f"CMD GÖNDERİLEMEDİ → {hedef_dugum}: {cmd} — {exc}", "kirmizi")
            return False
        self._logla(f"CMD → {hedef_dugum}: {cmd}", "mavi")
        return komut_mesaji["seq"]

    def arm_degistir(self):
        yeni_arm_acik = not self.arm_acik
        komut = "ARM" if yeni_arm_acik else "DISARM"
        if not self._cmd_gonder(komut, "iha"):
            return
        self.arm_acik = yeni_arm_acik
        if yeni_arm_acik:
            self.btn_arm.config(text="DISARM (A)", bg=KIRMIZI)
            self.lbl_arm.config(text="SİSTEM: ARM — uçuşa hazır", fg=SARI)
            self.btn_firlat.config(state="normal", bg=SARI)
        else:
            self.btn_arm.config(text="ARM (A)", bg="#232e3a")
            self.lbl_arm.config(text="SİSTEM: DISARM — güvenli", fg=SOLUK)
            self.btn_firlat.config(state="disabled", bg="#232e3a")

    def firlatma(self):
        if self.t_iha0:
            return
        self.t_iha0 = time.time()
        self._logla("GÖREV · FIRLATMA — İHA kronometresi başladı (limit 15:00)", "mavi")
        self.btn_firlat.config(state="disabled", bg="#232e3a")
        self.btn_iha_indi.config(state="normal", bg=SARI)

    def iha_indi(self):
        if not self.t_iha0 or self.t_iha1:
            return
        self.t_iha1 = time.time()
        sure = self.t_iha1 - self.t_iha0
        asim = sure > self.IHA_LIMIT
        self._logla(f"GÖREV · İHA İNDİ — uçuş süresi {sure/60:.1f} dk"
                    + (" → SÜRE AŞIMI: UÇUŞ GEÇERSİZ (şartname §6.4)" if asim else ""),
                    "sari" if asim else "yesil")
        if not self.onaylandi:
            self._logla("  ⚠ İHA indi ama aktarım havadayken hakem onayı YOKTU — "
                        "§6.4 geçersizlik riski!", "sari")
        self.btn_iha_indi.config(state="disabled", bg="#232e3a")
        self._ucus("İNİŞ TAMAM — PARAŞÜT (İHA-İB)", MAVI)

    def ika_baslat(self):
        # YAZILIM KİLİDİ — şartname §2.2.5: "İHA yere temas etmeden İKA
        # hareket edemez"; §6.2: intikal ancak onaylı veri sonrası. t_iha1
        # yalnız UI kronometresidir; sürüş izninin otoritesi protokol latch'idir.
        if self.iha_landed_seq is None:
            self._logla("KİLİT ✋ Üretim IHA_LANDED kanıtı alınmadan İKA "
                        "hareket EDEMEZ (şartname §2.2.5) — komut REDDEDİLDİ",
                        "sari")
            return
        if not self.onaylandi:
            self._logla("KİLİT ✋ Hakem onayı (ACK) olmadan İKA intikali "
                        "başlatılamaz (şartname §6.2) — komut REDDEDİLDİ", "sari")
            return
        if self.t_ika0:
            return
        if not self._cmd_gonder("IKA_GO", "ika"):
            return
        self.t_ika0 = time.time()
        self._logla("GÖREV · İKA İNTİKALİ BAŞLADI — kronometre limit 10:00 "
                    "(kilit koşulları sağlandı ✓)", "mavi")
        self.btn_ika_go.config(state="disabled", bg="#232e3a")
        self.btn_hb.config(state="normal", bg=SARI)

    def hb_temas(self):
        if not self.t_ika0 or self.t_ika1:
            return
        self.t_ika1 = time.time()
        s = self.t_ika1 - self.t_ika0
        ok = s <= self.IKA_LIMIT
        self._logla(f"GÖREV · HB TEMAS — İKA süresi {s/60:.1f} dk → "
                    + ("GÖREV BAŞARILI (P_görev = 600 puan)" if ok
                       else "SÜRE AŞIMI — İKA görevi BAŞARISIZ"),
                    "yesil" if ok else "sari")
        self.btn_hb.config(state="disabled", bg=YESIL if ok else KIRMIZI)

    # ── Hazırlık akışı (§6.2) + ceza + manuel paraşüt (§2.2.4) ───────────────
    def _ceza_ekle(self, puan, sebep):
        self.ceza_toplam += puan
        self.lbl_ceza.config(text=f"CEZA Σ −{self.ceza_toplam}", fg=KIRMIZI)
        self._logla(f"CEZA −{puan}: {sebep} (toplam −{self.ceza_toplam})", "sari")

    def alan_girisi(self):
        if self.t_haz0:
            return
        self.t_haz0 = time.time()
        self._logla("HAZIRLIK · Alan girişi — 15:00 hazırlık süresi başladı (§6.2)",
                    "mavi")
        self.btn_alan.config(state="disabled", bg="#232e3a")
        self.btn_hazir.config(state="normal", bg=SARI)

    def takim_hazir(self):
        if not self.t_haz0 or self.t_haz1:
            return
        self.t_haz1 = time.time()
        s = self.t_haz1 - self.t_haz0
        puan = max(0, int((900 - s) / 30))
        self._logla(f"HAZIRLIK · 'TAKIM HAZIR' — süre {s/60:.1f} dk (hands-off); "
                    f"tasarruf puanı ≈ +{puan} (§7 t_hazırlık)", "yesil")
        self.btn_hazir.config(state="disabled", bg="#232e3a")
        self.btn_mudahale.config(state="normal", bg=SARI)

    def mudahale(self):
        # §6.2: hands-off sonrası müdahale = −100 ceza + süre hazırlığa eklenir
        if not self.t_haz1:
            return
        self.t_haz0 += time.time() - self.t_haz1   # kronometre kaldığı yerden sürer
        self.t_haz1 = None
        self._ceza_ekle(100, "hands-off sonrası sisteme müdahale (§6.2)")
        self._logla("HAZIRLIK · kronometre DEVAM EDİYOR — müdahale süresi "
                    "hazırlığa ekleniyor; bitince tekrar TAKIM HAZIR verin", "sari")
        self.btn_hazir.config(state="normal", bg=SARI)
        self.btn_mudahale.config(state="disabled", bg="#232e3a")

    def parasut(self):
        # İki adımlı emniyet: yanlışlıkla tek tık paraşüt açamaz
        simdi = time.time()
        if simdi - self.parasut_teyit > 3.0:
            self.parasut_teyit = simdi
            self.btn_parasut.config(bg=KIRMIZI, text="EMİN MİSİN? tekrar bas (3 sn)")
            self.kok.after(3200, lambda: self.btn_parasut.config(
                bg="#232e3a", text="PARAŞÜT (manuel −50)"))
            return
        if not self._cmd_gonder("PARACHUTE", "iha"):
            return
        self._ceza_ekle(50, "manuel paraşüt tetikleme (§2.2.4)")
        self._ucus("PARAŞÜT — MANUEL TETİKLENDİ (−50)", KIRMIZI)
        self.btn_parasut.config(state="disabled", bg=KIRMIZI,
                                text="PARAŞÜT AÇILDI (manuel)")

    def _kron_metin(self, t0, t1, limit):
        if not t0:
            return "--:--", SOLUK
        kalan = limit - ((t1 or time.time()) - t0)
        dk, sn = divmod(int(abs(kalan)), 60)
        if kalan < 0:
            return f"-{dk:02d}:{sn:02d} AŞIM", KIRMIZI
        return f"{dk:02d}:{sn:02d}", (YESIL if kalan > 180 else
                                      SARI if kalan > 60 else KIRMIZI)

    # ── Yardımcılar ──────────────────────────────────────────────────────────
    def _guven_ciz(self, conf):
        c = self.guven_cubuk
        c.delete("all")
        w = S(380)
        c.create_rectangle(0, 0, w, S(20), outline=CIZGI)
        c.create_rectangle(0, 0, int(w * conf), S(20), fill=YESIL, outline="")
        c.create_text(w // 2, S(10), text=f"güven %{conf * 100:.0f}", fill=BG,
                      font=self.f_kucuk)

    def _zincir(self, aktifler):
        for ad, e in self.zincir_etiket.items():
            e.config(fg=YESIL if ad in aktifler else SOLUK,
                     bg="#15251b" if ad in aktifler else PANEL)

    def _durum_tazele(self):
        self.lbl_saat.config(text=time.strftime("%H:%M:%S"))
        simdi = time.time()
        for ad, (nokta, metin) in self.lbl_dugum.items():
            t = self.son_hb.get(ad)
            if t is None:
                nokta.config(fg=KIRMIZI)
                metin.config(text=f"{ad.upper()}  — sinyal yok")
            else:
                yas = simdi - t
                canli = yas < 3.0                      # ika_receiver failsafe eşiği
                nokta.config(fg=YESIL if canli else KIRMIZI)
                tel = self.tel.get(ad) or {}
                parcalar = []
                if "alt" in tel:
                    parcalar.append(f"{tel['alt']:.0f} m")
                if "hiz" in tel:
                    parcalar.append(f"{tel['hiz']:.1f} m/s")
                if "bat" in tel:
                    parcalar.append(f"{tel['bat']:.1f} V")
                if "uydu" in tel:
                    parcalar.append(f"{tel['uydu']} uydu")
                ek = (" · " + " · ".join(parcalar)) if parcalar else ""
                mod = self.mod.get(ad)
                if mod:
                    ek += f" · mod {mod}" + ("" if mod == "AUTO" else " ⚠GEÇERSİZ")
                metin.config(text=f"{ad.upper()} — hb {yas:.1f} sn{ek}"
                                  + ("" if canli else "  (BAĞLANTI KAYBI!)"))
        self.lbl_sayac.config(
            text=f"OPEN_ROUTE {self.sayac['OPEN_ROUTE']} · "
                 f"RED {self.sayac['OPEN_ROUTE_RED']} · "
                 f"NO_ROUTE {self.sayac['NO_ROUTE']} · "
                 f"LANDED {self.sayac['IHA_LANDED']} · "
                 f"HB {self.sayac['HEARTBEAT']} · "
                 f"ACK {self.sayac['ACK_TX']}")
        m1, r1 = self._kron_metin(self.t_iha0, self.t_iha1, self.IHA_LIMIT)
        self.lbl_kron_iha.config(text=f"İHA ⏱ {m1} / 15:00", fg=r1)
        m2, r2 = self._kron_metin(self.t_ika0, self.t_ika1, self.IKA_LIMIT)
        self.lbl_kron_ika.config(text=f"İKA ⏱ {m2} / 10:00", fg=r2)
        m3, r3 = self._kron_metin(self.t_haz0, self.t_haz1, 900)
        self.lbl_kron_haz.config(text=f"HAZIRLIK ⏱ {m3} / 15:00", fg=r3)
        if self.gorunum_adi == "harita":
            self._inset_ciz()

    def _logla(self, satir, renk="soluk"):
        self.gunluk.config(state="normal")
        self.gunluk.insert("end", time.strftime("[%H:%M:%S] ") + satir + "\n", renk)
        self.gunluk.see("end")
        self.gunluk.config(state="disabled")


# ── Demo beslemesi: gerçek protokolle sahte İHA + İKA ────────────────────────
def demo_besle(yks_port, durum):
    """Aynı comms primitifleriyle İHA/İKA davranışını üretir (tanıtım için).
    İHA: 1 Hz heartbeat + ACK gelene dek OPEN_ROUTE tekrar gönderimi.
    İKA: 1 Hz heartbeat. `durum` anahtarları senaryo butonlarıyla kesilir."""
    hedef = ("127.0.0.1", yks_port)

    def iha():
        link = UDPLink()
        reader = FrameReader()
        rota = open_route(
            road=2, conf=0.91, ref_xy=[25.0, 2.0],
            waypoints=[[0.6, 4.5], [-0.8, 9.0], [1.2, 14.0], [-0.4, 19.5],
                       [1.8, 25.0], [0.2, 31.0], [-1.0, 37.0], [0.0, 44.0]])
        onay = False
        t0 = time.time()
        sonra = t0 + 3.0                                   # 3 sn tarama süsü
        son_tx = 0.0
        while time.time() - t0 < 600:
            if durum["iha_hb"]:                            # YKS-kaybı senaryosu keser
                sn = time.time() - t0
                hb = heartbeat("iha")                      # ek telemetri alanları:
                hb.update(alt=round(30 + 1.8 * math.sin(sn / 5), 1),
                          hiz=round(16.5 + 1.2 * math.sin(sn / 3.7), 1),
                          bat=round(12.6 - 0.0012 * sn, 2),
                          uydu=14 + int(sn / 7) % 3,
                          mod="AUTO",                      # tam otonomi (§6.2)
                          x=round(150 + 85 * math.cos(sn / 11), 1),
                          y=round(150 + 62 * math.sin(sn / 11), 1))
                link.send(encode(hb), hedef)
                if time.time() >= sonra and not onay and time.time() - son_tx > 1.2:
                    link.send(encode(rota), hedef)         # ACK yok → tekrar
                    son_tx = time.time()
            d, _ = link.recv()
            for m in reader.feed(d) if d else []:
                if m.get("type") == "ACK" and m.get("ref") == rota["seq"]:
                    onay = True
            time.sleep(0.5)

    def ika():
        link = UDPLink()
        receiver = IkaReceiver(link)
        t0 = time.time()
        while time.time() - t0 < 600:
            if durum["ika_hb"]:                            # İKA-kaybı senaryosu keser
                sn = time.time() - t0
                hb = heartbeat("ika")
                hb.update(hiz=0.0, bat=round(11.9 - 0.0008 * sn, 2),
                          uydu=12 + int(sn / 9) % 3, mod="AUTO")
                link.send(encode(hb), hedef)
            # Demo da gerçek alıcı yolunu kullanır; IKA_GO latch + ACK yalnız
            # ekranda görünmekle kalmaz, aynı UDP soketinde gerçekten tüketilir.
            receiver.poll()
            time.sleep(1.0)

    threading.Thread(target=iha, daemon=True).start()
    threading.Thread(target=ika, daemon=True).start()


def main():
    ap = argparse.ArgumentParser(description="Navitas YKS hakem ekranı")
    ap.add_argument("--bind", default="0.0.0.0:5005")
    ap.add_argument("--ika", type=_udp_adres,
                    help="İKA komut hedefi host:port (UDP için zorunlu)")
    ap.add_argument("--serial", help="SiK telsiz seri portu (örn. COM5)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--demo", action="store_true",
                    help="dahili İHA/İKA beslemesi (tanıtım + otomatik hakem onayı)")
    ap.add_argument("--otokaydet", type=float, default=0,
                    help="N sn sonra pencere görüntüsünü PNG kaydet (rapor için)")
    ap.add_argument("--kaydet-yolu", default="yks_ekran.png")
    ap.add_argument("--kapat", action="store_true", help="otokaydet sonrası çık")
    args = ap.parse_args()

    if args.serial and args.demo:
        ap.error("--demo yalnız UDP kipinde kullanılabilir")
    if args.serial and args.ika:
        ap.error("--serial ile --ika birlikte kullanılamaz")
    if not args.serial and not args.demo and not args.ika:
        ap.error("UDP kipinde --ika HOST:PORT zorunlu")

    global OLCEK
    try:  # yüksek DPI: netlik + piksel ölçülerini ekrana göre büyüt (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        OLCEK = max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96.0)
    except Exception:
        pass

    if args.serial:
        link = SerialLink(args.serial, args.baud)
        ika_peer = None
    else:
        h, p = args.bind.split(":")
        link = UDPLink(bind=(h, int(p)))
        ika_peer = args.ika

    kok = tk.Tk()
    # otomatik onay YOK: hakem onay akışı elle incelenebilsin (buton/R kısayolu)
    app = YksArayuz(
        kok, link, otomatik_onay=False, demo=args.demo, ika_peer=ika_peer)
    app._logla(f"YKS hazır — dinleniyor: "
               f"{args.serial or args.bind}", "mavi")

    if args.demo:
        demo_besle(link.port, app.demo_durum)
        app._logla("DEMO modu: dahili İHA/İKA beslemesi başladı — "
                   "senaryo butonları etkin", "mavi")

    if args.otokaydet > 0:
        # SS modunda pencere HEP önde olsun — yoksa arkadaki pencere yakalanır
        kok.attributes("-topmost", True)
        kok.lift()

        def kaydet():
            from PIL import ImageGrab
            kok.lift()
            kok.focus_force()
            kok.update()
            x, y = kok.winfo_rootx(), kok.winfo_rooty()
            w, h = kok.winfo_width(), kok.winfo_height()
            ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(args.kaydet_yolu)
            print(f"SS kaydedildi: {args.kaydet_yolu}")
            if args.kapat:
                kok.destroy()
        kok.after(int(args.otokaydet * 1000), kaydet)

    kok.mainloop()
    link.close()


if __name__ == "__main__":
    main()

"""
YKS (Yer Kontrol İstasyonu) — hakem ekranı GUI'si.

Şartname §2.2.3/§6.2: İHA'nın tespit ettiği güzergâh YKS'de CANLI görünmeli,
Alan Hakemi monitörden izleyip onaylamalı. Bu arayüz, yks_monitor.py'nin
terminal sürümünün yerini alan gerçek hakem ekranıdır:

  · gerçek protokol trafiği dinler (OPEN_ROUTE / HEARTBEAT — comms.protocol)
  · saha haritasında (50×50 m HTAB) rotayı ve açık yolu çizer
  · İHA/İKA bağlantı canlılığını gösterir (heartbeat yaşı)
  · hakem onayı BUTONLA verilir → ACK ancak o zaman döner
    (yks_monitor.py'deki "otomatik onay" bu ekranda kaldırıldı)

Kullanım:
  python yks_gui.py                          # 0.0.0.0:5005 dinler (UDP)
  python yks_gui.py --bind 0.0.0.0:5005
  python yks_gui.py --serial COM5            # SiK telsiz (saha)
  python yks_gui.py --demo                   # dahili İHA/İKA beslemesiyle tanıtım
  python yks_gui.py --demo --otokaydet 6     # 6 sn sonra pencere SS'i kaydet (rapor)

Sadece stdlib + (SS için) Pillow kullanır; tkinter Python ile gelir.
"""
import argparse
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

from link import UDPLink, SerialLink
from protocol import (encode, ack, command, heartbeat, open_route,
                      FrameReader, ROAD_LABEL)

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


class YksArayuz:
    IHA_LIMIT = 900     # şartname: fırlatma → paraşütle iniş ≤ 15 dk
    IKA_LIMIT = 600     # şartname: teker dönüşü → HB temas ≤ 10 dk

    def __init__(self, kok, link, otomatik_onay=False, demo=False):
        self.kok = kok
        self.link = link
        self.reader = FrameReader()
        self.gelen = queue.Queue()
        self.otomatik_onay = otomatik_onay
        self.demo = demo
        self.demo_durum = {"iha_hb": True, "ika_hb": True}   # senaryo anahtarları

        self.rota = None            # son OPEN_ROUTE mesajı
        self.rota_adr = None        # ACK dönülecek adres
        self.onaylandi = False
        self.son_hb = {}            # node -> zaman
        self.son_adr = {}           # node -> adres (CMD gönderimi için)
        self.sayac = {"OPEN_ROUTE": 0, "HEARTBEAT": 0, "ACK_TX": 0}
        self.arm_acik = False
        self.t_iha0 = self.t_iha1 = None    # İHA görev kronometresi
        self.t_ika0 = self.t_ika1 = None    # İKA görev kronometresi
        self.tel = {}                       # node -> son telemetri alanları
        self.rx_alim = {}                   # seq -> kaç kez alındı (tekrar gönderim)
        self._detay_base = ""
        # canlı algı (v3 modeli ile gerçek çıkarım)
        self.algi_kuyruk = queue.Queue()
        self.algi_model = None
        self.algi_mesgul = False
        self.algi_kaynak = "gemini"
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
        sol = self._panel(govde, "SAHA HARİTASI — HTAB 50×50 m   |   "
                                 "CANLI ALGI — navitas_seg_v3 (GERÇEK çıkarım)")
        sol.pack(side="left", fill="both", expand=True, padx=(0, 8))

        anahtar = tk.Frame(sol, bg=PANEL)
        anahtar.pack(fill="x", padx=10, pady=(4, 0))
        self.btn_gor_harita = tk.Button(anahtar, text="◈ Saha Haritası (V)",
                                        font=self.f_kucuk, fg=BG, bg=YESIL,
                                        relief="flat", padx=8, pady=3,
                                        command=lambda: self.gorunum("harita"))
        self.btn_gor_harita.pack(side="left", padx=(0, 6))
        self.btn_gor_algi = tk.Button(anahtar, text="◉ Canlı Algı — v3 (V)",
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
                                     text="v3 modeli ilk geçişte yüklenecek…",
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
                              ("mavi", MAVI), ("soluk", SOLUK)):
            self.gunluk.tag_configure(renk_ad, foreground=renk)

        # Alt durum çubuğu
        alt = tk.Frame(self.kok, bg=PANEL)
        alt.pack(fill="x", side="bottom")
        tasiyici = "SiK 433 MHz (seri)" if isinstance(self.link, SerialLink) \
            else f"UDP :{self.link.port}"
        tk.Label(alt, text=f"  Taşıyıcı: {tasiyici}   ·   Protokol: newline-JSON v1"
                           f"   ·   Çerçeve: OPEN_ROUTE / HEARTBEAT / ACK / CMD",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, wraplength=S(1150),
                 justify="left").pack(side="left", pady=3)

        # Görev kontrol & kronometre şeridi (şartname süreleri + §2.2.5 kilidi)
        gorev = tk.Frame(self.kok, bg=PANEL, highlightbackground=CIZGI,
                         highlightthickness=1)
        gorev.pack(fill="x", side="bottom", padx=14, pady=(0, 4))

        def gbuton(metin, komut, aktif=True):
            b = tk.Button(gorev, text=metin, font=self.f_kucuk, fg=METIN,
                          bg="#232e3a", activebackground=SARI, activeforeground=BG,
                          relief="flat", padx=8, pady=4, command=komut,
                          state=("normal" if aktif else "disabled"))
            b.pack(side="left", padx=5, pady=5)
            return b

        self.btn_arm = gbuton("ARM (A)", self.arm_degistir)
        self.btn_firlat = gbuton("FIRLATMA", self.firlatma, aktif=False)
        self.btn_iha_indi = gbuton("İHA İNDİ", self.iha_indi, aktif=False)
        # §2.2.5 kilidini GÖSTERMEK için hep tıklanabilir — erken basılırsa reddeder
        self.btn_ika_go = gbuton("İKA BAŞLAT", self.ika_baslat)
        self.btn_hb = gbuton("HB TEMAS", self.hb_temas, aktif=False)

        self.lbl_arm = tk.Label(gorev, text="SİSTEM: DISARM — güvenli",
                                font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_arm.pack(side="left", padx=10)
        self.lbl_kron_ika = tk.Label(gorev, text="İKA ⏱ --:-- / 10:00",
                                     font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_kron_ika.pack(side="right", padx=10)
        self.lbl_kron_iha = tk.Label(gorev, text="İHA ⏱ --:-- / 15:00",
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

        # 3 yol koridoru (stilize) — sol/orta/sağ
        acik = self.rota["road"] if self.rota else None
        for yol, xm in ((1, 12.5), (2, 25.0), (3, 37.5)):
            renk = YESIL if yol == acik else "#25303c"
            for (ax, ay, bx, by) in [(xm - 3, 4, xm + 3, 46)]:
                px0, py0 = self._mxy(ax, ay)
                px1, py1 = self._mxy(bx, by)
                c.create_rectangle(px0, py0, px1, py1, outline=renk,
                                   width=2 if yol == acik else 1,
                                   dash=None if yol == acik else (3, 3))
            tx, ty = self._mxy(xm, -2.4)          # arena çerçevesinin ALTINA yaz
            c.create_text(tx, ty, text=f"{yol}·{ROAD_LABEL[yol].upper()}",
                          fill=renk if yol == acik else SOLUK, font=self.f_kucuk)
            if yol != acik and acik is not None:
                kx, ky = self._mxy(xm, 25)
                c.create_text(kx, ky, text="✕ KAPALI", fill=KIRMIZI, font=self.f_kucuk)

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
        if self.rota and self.rota.get("waypoints"):
            ref = self.rota.get("ref_xy") or [25.0, 2.0]
            noktalar = [(ref[0] + dx, ref[1] + dy) for dx, dy in self.rota["waypoints"]]
            noktalar.insert(0, (ref[0], ref[1]))
            pks = [self._mxy(x, y) for x, y in noktalar]
            for (ax, ay), (bx, by) in zip(pks, pks[1:]):
                c.create_line(ax, ay, bx, by, fill=YESIL, width=3, arrow="last")
            rx, ry = self._mxy(ref[0], ref[1])
            c.create_oval(rx - 5, ry - 5, rx + 5, ry + 5, fill=SARI, outline="")
            c.create_text(rx - 16, ry, text="ref", fill=SARI, font=self.f_kucuk, anchor="e")

    # ── Ağ dinleyici (arka plan iş parçacığı) ────────────────────────────────
    def _dinle(self):
        while True:
            try:
                d, adr = self.link.recv()
            except OSError:
                return                     # pencere kapanırken soket kapanır
            if not d:
                continue
            for m in self.reader.feed(d):
                self.gelen.put((m, adr))

    # ── Ana döngü tiki ───────────────────────────────────────────────────────
    def _tik(self):
        while not self.gelen.empty():
            m, adr = self.gelen.get()
            self._mesaj_isle(m, adr)
        while not self.algi_kuyruk.empty():
            paket = self.algi_kuyruk.get()
            if paket[0] == "sonuc":
                _, gorsel, bilgi, log_satiri = paket
                self._algi_sonucu_goster(gorsel, bilgi)
                self._logla(log_satiri, "yesil")
            else:
                self._logla(paket[1], "mavi")
        self._durum_tazele()
        self.kok.after(120, self._tik)

    def _mesaj_isle(self, m, adr):
        tip = m.get("type")
        if tip == "OPEN_ROUTE":
            self.son_adr["iha"] = adr
            yeni = (self.rota is None) or (m["seq"] != self.rota["seq"])
            self.rota, self.rota_adr = m, adr
            self.rx_alim[m["seq"]] = self.rx_alim.get(m["seq"], 0) + 1
            if yeni:
                self.onaylandi = False
                self.sayac["OPEN_ROUTE"] += 1
                self._logla(f"OPEN_ROUTE  yol={m['road']}({m['label']}) "
                            f"güven={m['conf']} seq={m['seq']} wp={len(m['waypoints'])}",
                            "yesil")
                self.lbl_karar.config(text=f"{m['road']} · {m['label'].upper()}", fg=YESIL)
                self._detay_base = (f"seq={m['seq']} · ref=({m['ref_xy'][0]}, "
                                    f"{m['ref_xy'][1]}) m · {len(m['waypoints'])} waypoint")
                self.btn_onay.config(state="normal", bg=SARI,
                                     text="TESPİTİ ONAYLA → ACK GÖNDER")
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
        elif tip == "HEARTBEAT":
            dugum = m.get("node", "?")
            self.son_hb[dugum] = time.time()
            self.son_adr[dugum] = adr
            tel = {k: m[k] for k in ("alt", "hiz", "bat", "uydu") if k in m}
            if tel:
                self.tel[dugum] = tel
            self.sayac["HEARTBEAT"] += 1

    def onayla(self):
        if not self.rota or self.onaylandi:
            return
        if self.rota_adr is not None:
            self.link.send(encode(ack(self.rota["seq"], "yks")), self.rota_adr)
        else:                                   # seri hat: adres kavramı yok
            self.link.send(encode(ack(self.rota["seq"], "yks")))
        self.onaylandi = True
        self.sayac["ACK_TX"] += 1
        self.btn_onay.config(state="disabled", bg=YESIL, text="ONAYLANDI ✓")
        self.lbl_onay.config(text=f"Hakem onayı verildi — ACK(seq={self.rota['seq']}) "
                                  f"İHA'ya iletildi", fg=YESIL)
        self._logla(f"ACK → iha   ref={self.rota['seq']} (HAKEM ONAYI)", "sari")
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

    def _ucus(self, metin, renk):
        self.lbl_ucus.config(text=f"İHA UÇUŞ DURUMU: {metin}", fg=renk)

    def _ucus_normal(self):
        self.lbl_ucus.config(text="İHA UÇUŞ DURUMU: OTONOM GÖREV (AUTO)", fg=YESIL)

    # ── Canlı algı: v3 modeliyle GERÇEK çıkarım ──────────────────────────────
    # Karar zinciri sahadakiyle AYNI: codes/rpi_inference.py'nin get_masks +
    # analyze_path fonksiyonları kullanılır (kopya algoritma yok).
    def _algi_gorseller(self):
        import pathlib
        kok_dizin = pathlib.Path(__file__).resolve().parents[1]
        if self.algi_kaynak == "gemini":
            d = kok_dizin / "test_images" / "gemini"
            return sorted(d.glob("*.png"), key=lambda p: int(p.stem)) \
                if d.is_dir() else []
        d = kok_dizin / "dataset" / "rescuenet_yolo" / "images" / "val"
        return sorted(d.glob("*.jpg")) if d.is_dir() else []

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
        self.algi_kaynak = "val" if self.algi_kaynak == "gemini" else "gemini"
        self.algi_idx = 0
        self._logla(f"ALGI kaynağı: {self.algi_kaynak} "
                    f"({'arena tipi sentetik' if self.algi_kaynak == 'gemini' else 'RescueNet doğrulama seti'})",
                    "mavi")
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
                                        + ("(v3 modeli yükleniyor — ilk sefer "
                                           "birkaç sn)" if self.algi_model is None
                                           else ""))
        threading.Thread(target=self._algi_kos, args=(yol,), daemon=True).start()

    def _algi_kos(self, yol):
        """Arka plan iş parçacığı: v3 ile gerçek çıkarım + saha karar zinciri."""
        try:
            import pathlib
            import sys as _sys
            import cv2
            import numpy as np
            kok_dizin = pathlib.Path(__file__).resolve().parents[1]
            _sys.path.insert(0, str(kok_dizin / "codes"))
            from rpi_inference import analyze_path, draw_masks, get_masks

            if self.algi_model is None:
                from ultralytics import YOLO
                model_yolu = kok_dizin / "models" / "navitas_seg_v3_best.pt"
                self.algi_model = YOLO(str(model_yolu))
                self.algi_kuyruk.put(("log",
                    f"v3 modeli yüklendi: {model_yolu.name} (SHA 8e8d46a6…)"))

            img = cv2.imread(str(yol))
            h, w = img.shape[:2]
            t0 = time.perf_counter()
            # saha/sim zinciriyle aynı strateji: TEK düşük eşikli çıkarım,
            # önce 0,30 ile süz; traversable boşsa 0,05'e düş (iha_perceive
            # CONF_FLOOR fallback'inin buradaki karşılığı)
            sonuc = self.algi_model.predict(img, imgsz=512, conf=0.05,
                                            verbose=False)
            ms = (time.perf_counter() - t0) * 1000
            esik = 0.30
            maskeler = get_masks(sonuc, h, w, min_conf=esik)
            if maskeler[0].sum() == 0:
                esik = 0.05
                maskeler = get_masks(sonuc, h, w, min_conf=esik)
            yol_no, guven, wps = analyze_path(maskeler[0])

            gorsel = draw_masks(img, maskeler)
            # şerit sınırları + waypoint zinciri (saha karar zinciri görünür olsun)
            for x in (w // 3, 2 * w // 3):
                cv2.line(gorsel, (x, 0), (x, h), (90, 90, 90), 1)
            if wps:
                pts = np.array(wps, dtype=np.int32)
                cv2.polylines(gorsel, [pts], False, (0, 220, 255), max(2, w // 300))
                for (px, py) in wps:
                    cv2.circle(gorsel, (px, py), max(3, w // 150), (0, 220, 255), -1)

            trav_oran = 100.0 * maskeler[0].mean()
            blok_oran = 100.0 * maskeler[1].mean()
            karar = (f"{yol_no}·{ROAD_LABEL[yol_no].upper()}" if yol_no
                     else "TESPİT YOK")
            bilgi = (f"{self.algi_kaynak}/{yol.name} → karar: {karar} · "
                     f"güven {guven:.2f} · çıkarım {ms:.0f} ms · eşik {esik:.2f}"
                     + (" (düşük-eşik fallback)" if esik < 0.30 else "")
                     + f" · traversable %{trav_oran:.0f} · blocked %{blok_oran:.0f}"
                     f" · model: navitas_seg_v3 (mAP50 0,627)")
            self.algi_kuyruk.put(("sonuc", gorsel, bilgi,
                                  f"ALGI(v3) {yol.name} → {karar} "
                                  f"güven={guven:.2f} · {ms:.0f} ms"))
        except Exception as e:
            self.algi_kuyruk.put(("log", f"ALGI HATASI: {e}"))
        finally:
            self.algi_mesgul = False

    def _algi_sonucu_goster(self, gorsel_bgr, bilgi):
        import cv2
        from PIL import Image, ImageTk
        h, w = gorsel_bgr.shape[:2]
        hedef_w, hedef_h = S(660), S(430)
        olcek = min(hedef_w / w, hedef_h / h)
        yeni = cv2.resize(gorsel_bgr, (int(w * olcek), int(h * olcek)))
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
        self.btn_onay.config(state="normal", bg=SARI,
                             text="TESPİTİ ONAYLA → ACK GÖNDER")
        self.lbl_onay.config(text="⚠ Hakem onayı BEKLENİYOR — İHA tekrar "
                                  "gönderimde (ACK yok)", fg=SARI)
        self._logla("(demo) hakem onayı sıfırlandı — akış baştan izlenebilir", "mavi")

    # ── Görev kontrol & kronometre (şartname süreleri + §2.2.5 kilidi) ───────
    def _cmd_gonder(self, cmd, hedef_dugum):
        adr = self.son_adr.get(hedef_dugum)
        if adr is not None and adr[1]:
            self.link.send(encode(command(cmd, hedef_dugum)), adr)
        elif isinstance(self.link, SerialLink):
            self.link.send(encode(command(cmd, hedef_dugum)))
        self._logla(f"CMD → {hedef_dugum}: {cmd}", "mavi")

    def arm_degistir(self):
        self.arm_acik = not self.arm_acik
        if self.arm_acik:
            self._cmd_gonder("ARM", "iha")
            self.btn_arm.config(text="DISARM (A)", bg=KIRMIZI)
            self.lbl_arm.config(text="SİSTEM: ARM — uçuşa hazır", fg=SARI)
            self.btn_firlat.config(state="normal", bg=SARI)
        else:
            self._cmd_gonder("DISARM", "iha")
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
        # hareket edemez"; §6.2: intikal ancak onaylı veri sonrası.
        if not self.t_iha1:
            self._logla("KİLİT ✋ İHA inişi tamamlanmadan İKA hareket EDEMEZ "
                        "(şartname §2.2.5) — komut REDDEDİLDİ", "sari")
            return
        if not self.onaylandi:
            self._logla("KİLİT ✋ Hakem onayı (ACK) olmadan İKA intikali "
                        "başlatılamaz (şartname §6.2) — komut REDDEDİLDİ", "sari")
            return
        if self.t_ika0:
            return
        self.t_ika0 = time.time()
        self._cmd_gonder("IKA_GO", "ika")
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
                metin.config(text=f"{ad.upper()} — hb {yas:.1f} sn{ek}"
                                  + ("" if canli else "  (BAĞLANTI KAYBI!)"))
        self.lbl_sayac.config(
            text=f"OPEN_ROUTE {self.sayac['OPEN_ROUTE']} · "
                 f"HB {self.sayac['HEARTBEAT']} · "
                 f"ACK {self.sayac['ACK_TX']}")
        m1, r1 = self._kron_metin(self.t_iha0, self.t_iha1, self.IHA_LIMIT)
        self.lbl_kron_iha.config(text=f"İHA ⏱ {m1} / 15:00", fg=r1)
        m2, r2 = self._kron_metin(self.t_ika0, self.t_ika1, self.IKA_LIMIT)
        self.lbl_kron_ika.config(text=f"İKA ⏱ {m2} / 10:00", fg=r2)

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
                          uydu=14 + int(sn / 7) % 3)       # (alıcılar yok sayar)
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
        t0 = time.time()
        while time.time() - t0 < 600:
            if durum["ika_hb"]:                            # İKA-kaybı senaryosu keser
                sn = time.time() - t0
                hb = heartbeat("ika")
                hb.update(hiz=0.0, bat=round(11.9 - 0.0008 * sn, 2),
                          uydu=12 + int(sn / 9) % 3)
                link.send(encode(hb), hedef)
            time.sleep(1.0)

    threading.Thread(target=iha, daemon=True).start()
    threading.Thread(target=ika, daemon=True).start()


def main():
    ap = argparse.ArgumentParser(description="Navitas YKS hakem ekranı")
    ap.add_argument("--bind", default="0.0.0.0:5005")
    ap.add_argument("--serial", help="SiK telsiz seri portu (örn. COM5)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--demo", action="store_true",
                    help="dahili İHA/İKA beslemesi (tanıtım + otomatik hakem onayı)")
    ap.add_argument("--otokaydet", type=float, default=0,
                    help="N sn sonra pencere görüntüsünü PNG kaydet (rapor için)")
    ap.add_argument("--kaydet-yolu", default="yks_ekran.png")
    ap.add_argument("--kapat", action="store_true", help="otokaydet sonrası çık")
    args = ap.parse_args()

    global OLCEK
    try:  # yüksek DPI: netlik + piksel ölçülerini ekrana göre büyüt (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        OLCEK = max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96.0)
    except Exception:
        pass

    if args.serial:
        link = SerialLink(args.serial, args.baud)
    else:
        h, p = args.bind.split(":")
        link = UDPLink(bind=(h, int(p)))

    kok = tk.Tk()
    # otomatik onay YOK: hakem onay akışı elle incelenebilsin (buton/R kısayolu)
    app = YksArayuz(kok, link, otomatik_onay=False, demo=args.demo)
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

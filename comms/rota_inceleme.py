"""NEDEN: Hakem, video olmadan gerçek rota paketinin geometrisini ve hareket sırasını görmelidir."""

import hashlib
import json
import math
import tkinter as tk
from tkinter import ttk
from iha_sender import rota_geometrisini_dogrula


BG = "#121920"
METIN = "#e8edf2"
SOLUK = "#9caab7"
MAVI = "#4aa3df"
SARI = "#f0a437"
YESIL = "#2ecc71"
KIRMIZI = "#e15241"
CERCEVE_NOTU = (
    "Rota çerçevesi / metre: X = ref_x + wp_x, Y = ref_y + wp_y. "
    "GPS/kuzey yönü değildir; İKA başlangıcına öteleme ayrıca uygulanır.")
KANIT_NOTU = (
    "Çizgi alınan PLANDIR; yol sınırı, engel maskesi veya gerçekleşmiş sürüş değildir. "
    "Son noktanın fiziksel hedefle eşleşmesi sahada doğrulanmalıdır.")


def nokta_oku(deger):
    if not isinstance(deger, (list, tuple)) or len(deger) != 2:
        raise ValueError("Koordinat iki sayı olmalıdır")
    if any(isinstance(sayi, bool) or not isinstance(sayi, (float, int)) for sayi in deger):
        raise ValueError("Koordinat sayısal olmalıdır")
    sonuc = tuple(float(sayi) for sayi in deger)
    if not all(math.isfinite(sayi) for sayi in sonuc):
        raise ValueError("Koordinat sonlu olmalıdır")
    return sonuc


def rota_plani(mesaj):
    if not isinstance(mesaj, dict):
        raise ValueError("Rota paketi yok")
    referans = nokta_oku(mesaj.get("ref_xy"))
    waypoints = mesaj.get("waypoints")
    if not isinstance(waypoints, (list, tuple)) or len(waypoints) < 2:
        raise ValueError("En az iki rota noktası gerekli")
    yerel = [nokta_oku(nokta) for nokta in waypoints]
    rota_geometrisini_dogrula(referans, yerel)
    noktalar = [nokta_oku([referans[0] + nokta[0], referans[1] + nokta[1]]) for nokta in yerel]
    ozet = hashlib.sha256(json.dumps({"ref_xy": referans, "waypoints": yerel},
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    onceki = noktalar[0]
    onceki_yon = None
    toplam = 0.0
    adimlar = []
    for sira, (yerel_nokta, nokta) in enumerate(zip(yerel, noktalar), 1):
        fark = (nokta[0] - onceki[0], nokta[1] - onceki[1])
        uzunluk = math.hypot(*fark)
        toplam += uzunluk
        if not math.isfinite(toplam):
            raise ValueError("Rota mesafesi sonlu değil")
        yon = math.degrees(math.atan2(fark[1], fark[0])) if uzunluk > 0 else None
        donus = None if yon is None or onceki_yon is None else (yon - onceki_yon + 180) % 360 - 180
        if sira == 1:
            hareket = "Başlangıç ankuru; ilk yönelim ölçülmedi"
        elif yon is None:
            hareket = "Aynı nokta; ilerleme yok"
        elif donus is None:
            hareket = f"İlk yönelim bilinmiyor; P{sira:02d}'e {uzunluk:.2f} m"
        elif abs(donus) < .05:
            hareket = f"Doğrultuyu koru; {uzunluk:.2f} m ilerle"
        else:
            taraf = "sola" if donus > 0 else "sağa"
            hareket = f"{abs(donus):.1f}° {taraf} yönel; {uzunluk:.2f} m ilerle"
        adimlar.append({"sira": sira, "yerel": yerel_nokta, "nokta": nokta,
                        "baslangic": onceki, "delta": fark, "mesafe": uzunluk,
                        "toplam": toplam, "yon": yon, "donus": donus, "hareket": hareket})
        onceki = nokta
        if yon is not None:
            onceki_yon = yon
    if toplam == 0:
        raise ValueError("Bütün rota noktaları aynı; hareket planı yok")
    return {"referans": referans, "noktalar": noktalar, "adimlar": adimlar,
            "toplam": toplam, "sha256": ozet, "seq": mesaj.get("seq")}


def harita_ciz(tuval, plan, *, durum="ALINAN PLAN", renk=MAVI, secili=None):
    tuval.delete("all")
    genislik = max(200, tuval.winfo_width())
    yukseklik = max(160, tuval.winfo_height())
    tuval.create_text(12, 8, text=durum, fill=renk, anchor="nw",
                       width=genislik - 24, font=("Segoe UI", 10, "bold"), tags="durum")
    if plan is None:
        tuval.create_text(genislik / 2, yukseklik / 2, text="GÖSTERİLECEK ROTA YOK\nTelsizden OPEN_ROUTE bekleniyor",
                           fill=SOLUK, width=genislik - 24, font=("Segoe UI", 11), tags="bos")
        return
    noktalar = [plan["referans"], *plan["noktalar"]]
    alt_x = min(nokta[0] for nokta in noktalar)
    alt_y = min(nokta[1] for nokta in noktalar)
    ust_x = max(nokta[0] for nokta in noktalar)
    ust_y = max(nokta[1] for nokta in noktalar)
    alan_w, alan_h = max(1, genislik - 120), max(1, yukseklik - 100)
    olcek = min(alan_w / max(1, ust_x - alt_x), alan_h / max(1, ust_y - alt_y))

    def piksel(nokta):
        return (genislik / 2 + (nokta[0] - (alt_x + ust_x) / 2) * olcek,
                (yukseklik + 20) / 2 - (nokta[1] - (alt_y + ust_y) / 2) * olcek)

    for oran in (0, .25, .5, .75, 1):
        konum_x = alt_x + (ust_x - alt_x) * oran
        konum_y = alt_y + (ust_y - alt_y) * oran
        ekran_x, ekran_y = piksel((konum_x, konum_y))
        tuval.create_line(ekran_x, 45, ekran_x, yukseklik - 30, fill="#25303c", tags="izgara")
        tuval.create_line(50, ekran_y, genislik - 35, ekran_y, fill="#25303c", tags="izgara")
    tuval.create_text(12, yukseklik - 14, text=f"X: {alt_x:+.2f}…{ust_x:+.2f} m   Y: {alt_y:+.2f}…{ust_y:+.2f} m",
                       fill=SOLUK, anchor="w", font=("Consolas", 9), tags="olcek")
    tuval.create_text(genislik - 14, 35, text="+Y ↑   +X →", fill=SOLUK, anchor="ne", tags="eksen")
    for adim in plan["adimlar"]:
        bas_x, bas_y = piksel(adim["baslangic"])
        son_x, son_y = piksel(adim["nokta"])
        tuval.create_line(bas_x, bas_y, son_x, son_y, fill=SARI if secili == adim["sira"] else renk,
                           width=4 if secili == adim["sira"] else 2, arrow="last", tags=("rota", f"p{adim['sira']}"))
        tuval.create_oval(son_x - 3, son_y - 3, son_x + 3, son_y + 3, fill=renk, outline="", tags="nokta")
        etiket_araligi = max(1, math.ceil(len(plan["adimlar"]) / 12))
        if adim["sira"] in (1, len(plan["adimlar"]), secili) or adim["sira"] % etiket_araligi == 0:
            tuval.create_text(son_x + 8, son_y - 5, text=f"P{adim['sira']:02d}", fill=METIN, anchor="w", tags="numara")
        tuval.tag_bind(f"p{adim['sira']}", "<Button-1>",
                        lambda olay, sira=adim["sira"]: tuval.event_generate("<<RotaNoktasi>>", x=sira))
    bas_x, bas_y = piksel(plan["referans"])
    son_x, son_y = piksel(plan["noktalar"][-1])
    tuval.create_oval(bas_x - 5, bas_y - 5, bas_x + 5, bas_y + 5, outline=SARI, width=2, tags="referans")
    tuval.create_text(bas_x - 8, bas_y + 12, text="REF", fill=SARI, anchor="e", tags="referans")
    tuval.create_rectangle(son_x - 6, son_y - 6, son_x + 6, son_y + 6, outline=METIN, width=2, tags="son")


class RotaInceleme(tk.Frame):
    def __init__(self, ebeveyn):
        super().__init__(ebeveyn, bg=BG)
        self.pack_propagate(False)
        self.plan = None
        self.secili = None
        self.durum = "ROTA BEKLENİYOR"
        self.renk = SOLUK
        self._imza = None
        self.baslik = tk.Label(self, bg=BG, fg=METIN, anchor="w", justify="left",
                                font=("Segoe UI", 11, "bold"))
        self.baslik.pack(fill="x", padx=10, pady=(6, 2))
        self.kaynak = tk.Label(self, bg=BG, fg=SARI, anchor="w", justify="left", font=("Segoe UI", 9))
        self.kaynak.pack(fill="x", padx=10)
        self.harita = tk.Canvas(self, bg=BG, highlightthickness=0, height=235)
        self.harita.pack(fill="both", expand=True)
        self.harita.bind("<Configure>", lambda olay: self.ciz())
        self.harita.bind("<<RotaNoktasi>>", lambda olay: self.sec(olay.x))
        self.detay = tk.Label(self, bg="#23303b", fg=METIN, anchor="w", justify="left", font=("Segoe UI", 10))
        self.detay.pack(fill="x", padx=10, pady=3)
        cerceve = tk.Frame(self, bg=BG)
        cerceve.pack(fill="x", padx=10)
        kolonlar = ("nokta", "x", "y", "mesafe", "toplam", "hareket")
        self.tablo = ttk.Treeview(cerceve, columns=kolonlar, show="headings", height=5, selectmode="browse")
        for ad, baslik, genislik in zip(kolonlar, ("Nokta", "X (m)", "Y (m)", "Adım m", "Σ m", "Planlanan hareket"),
                                       (55, 75, 75, 65, 65, 310)):
            self.tablo.heading(ad, text=baslik)
            self.tablo.column(ad, width=genislik, minwidth=genislik, stretch=ad == "hareket")
        kaydirma = ttk.Scrollbar(cerceve, orient="vertical", command=self.tablo.yview)
        yatay = ttk.Scrollbar(cerceve, orient="horizontal", command=self.tablo.xview)
        self.tablo.configure(yscrollcommand=kaydirma.set, xscrollcommand=yatay.set)
        self.tablo.grid(row=0, column=0, sticky="nsew")
        kaydirma.grid(row=0, column=1, sticky="ns")
        yatay.grid(row=1, column=0, sticky="ew")
        cerceve.columnconfigure(0, weight=1)
        self.tablo.bind("<<TreeviewSelect>>", self._secim)
        self.notlar = tk.Label(self, text=CERCEVE_NOTU + "\n" + KANIT_NOTU,
                               bg=BG, fg=SOLUK, justify="left", anchor="w", font=("Segoe UI", 9))
        self.notlar.pack(fill="x", padx=10, pady=(4, 6))
        self.notlar.pack_configure(side="bottom", before=self.harita)
        cerceve.pack_configure(side="bottom", before=self.harita)
        self.detay.pack_configure(side="bottom", before=self.harita)
        self.bind("<Configure>", self._boyut)

    def _boyut(self, olay):
        satir_sayisi = 3 if olay.height < 480 else 5
        if int(self.tablo.cget("height")) != satir_sayisi:
            self.tablo.configure(height=satir_sayisi)
        for etiket in (self.baslik, self.kaynak, self.detay, self.notlar):
            etiket.config(wraplength=max(160, olay.width - 24))

    def guncelle(self, mesaj, *, ret=None, bayat=False, kaynak="", onay="", video=""):
        try:
            plan = None if ret or mesaj is None else rota_plani(mesaj)
            hata = None
        except (ValueError, TypeError, OverflowError) as exc:
            plan, hata = None, str(exc)
        imza = (plan["seq"], plan["sha256"]) if plan else None
        if imza != self._imza:
            self.tablo.delete(*self.tablo.get_children())
            self.secili = None
            if plan:
                for adim in plan["adimlar"]:
                    self.tablo.insert("", "end", iid=str(adim["sira"]), values=(f"P{adim['sira']:02d}",
                                      f"{adim['nokta'][0]:+.2f}", f"{adim['nokta'][1]:+.2f}",
                                      f"{adim['mesafe']:.2f}", f"{adim['toplam']:.2f}", adim["hareket"]))
            self._imza = imza
        self.plan = plan
        if ret:
            self.durum, self.renk = "ROTA YOK — " + str(ret.get("sebep", "Ret alındı")), KIRMIZI
        elif hata:
            self.durum, self.renk = "GEOMETRİ GÖSTERİLEMİYOR — " + hata, KIRMIZI
        elif plan is None:
            self.durum, self.renk = "ROTA BEKLENİYOR", SOLUK
        elif bayat:
            self.durum, self.renk = "ESKİ PLAN — GÜNCELLİK YOK / ONAY İÇİN KULLANMAYIN", SARI
        else:
            self.durum, self.renk = "ALINAN TEK ROTA / PLANLANAN İLERLEME", MAVI
        self.baslik.config(text=(f"{len(plan['adimlar'])} nokta · {plan['toplam']:.2f} m · seq={plan['seq']} · "
                                f"rota izi {plan['sha256'][:10]}" if plan else self.durum))
        self.kaynak.config(text=" | ".join(alan for alan in (kaynak, video, onay) if alan))
        if plan and self.secili is None:
            self.sec(1)
        elif plan is None:
            self.detay.config(text="Hareket listesi yok. Yeni ve geçerli rota verisi bekleniyor.")
        self.ciz()

    def sec(self, sira):
        if self.plan is None or not 1 <= sira <= len(self.plan["adimlar"]):
            return
        self.secili = sira
        self.tablo.selection_set(str(sira))
        self.tablo.see(str(sira))
        self._detay_yaz()
        self.ciz()

    def _secim(self, olay):
        secim = self.tablo.selection()
        if secim and self.plan:
            self.secili = int(secim[0])
            self._detay_yaz()
            self.ciz()

    def _detay_yaz(self):
        adim = self.plan["adimlar"][self.secili - 1]
        self.detay.config(text=(f"P{self.secili:02d}: {adim['hareket']}\n"
                                f"wp=({adim['yerel'][0]:+.2f}, {adim['yerel'][1]:+.2f}) m · "
                                f"ΔX={adim['delta'][0]:+.2f} / ΔY={adim['delta'][1]:+.2f} m · "
                                "Geometrik açıklama; motor komutu / canlı konum değil."))

    def ciz(self):
        harita_ciz(self.harita, self.plan, durum=self.durum, renk=self.renk, secili=self.secili)

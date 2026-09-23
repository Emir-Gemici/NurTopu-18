"""NEDEN: FDA uçuş planı önizlenir; kalkış pilotta, görev sonu onayı hakemdedir."""

import time
import uuid

from fda_gorev import (
    CMD_FDA_HAZIRLA, GOREV_TEKRAR_ARALIGI_S, GOREV_TEKRAR_SAYISI,
    HAZIRLIK_TAZELIK_S, KALKIS_KONUM_TOLERANSI_M, KALKIS_YON_TOLERANSI_DERECE,
    VARSAYILAN_ILERI_M, VARSAYILAN_IRTIFA_M,
    VARSAYILAN_DRONE_TEST_ILERI_M, VARSAYILAN_DRONE_TEST_IRTIFA_M,
    DRONE_TEST_ARAMA_KARE_M, ayar_dogrula, hedef_konumu,
    konum_dogrula, mesafe_m, sonlu_sayi,
)
from komut_tekrar import AckliTekrar, BEKLIYOR, ONAYLANDI, VAZGECILDI
from protocol import kritik_komut_ack_gecerli_mi
from yki_canli_isleme import YKI_HEDEF_TAZELIK_S


class FdaGorevDenetleyici:
    def __init__(self, yks, saat=time.monotonic):
        self.yks = yks
        self.saat = saat
        self.drone_test = bool(getattr(yks, "fda_drone_test", False))
        self.ayar = None
        self.ika_baslangic = None
        self.drone_baslangic = None
        self._kare_kayitli = False
        self._kare_degeri = DRONE_TEST_ARAMA_KARE_M
        self._yukseklik_degeri = (VARSAYILAN_DRONE_TEST_IRTIFA_M
                                  if self.drone_test else VARSAYILAN_IRTIFA_M)
        self._ileri_degeri = (VARSAYILAN_DRONE_TEST_ILERI_M
                              if self.drone_test else VARSAYILAN_ILERI_M)
        self._yukseklik_kayitli = False
        self._ileri_kayitli = False
        self.durum = "Plan hazırlanmadı. Varsayılan: 30 m yükseklik / 40 m ileri."
        self.tekrar = AckliTekrar(yks._ham_gonder, GOREV_TEKRAR_ARALIGI_S,
                                 GOREV_TEKRAR_SAYISI, saat=saat)
        if self.drone_test:
            self.durum = (
                "Plan hazırlanmadı. Test drone: 20 m yükseklik / 30 m ileri / 6 m kare.")
        self.pencere = None

    def telemetri(self):
        if not getattr(self.yks, "fda_kipi", False) or getattr(self.yks, "demo", False):
            raise ValueError("Yalnız gerçek FDA çoklu rotor kipinde kullanılabilir")
        simdi = self.saat()
        for alan in ("son_hb", "mod_durum_zamani"):
            damga = getattr(self.yks, alan, {}).get("iha")
            if damga is None or not 0 <= simdi - damga <= HAZIRLIK_TAZELIK_S:
                raise ValueError("Taze İHA/Pixhawk telemetrisi bekleniyor")
        if not self.yks._arm_durumu_taze_mi(simdi):
            raise ValueError("ARM durumu güncel değil")
        veri = dict(self.yks.tel.get("iha") or {})
        if veri.get("pixhawk_canli") is not True:
            raise ValueError("Pixhawk bağlantısı canlı değil")
        direct_cube = getattr(type(getattr(self.yks, "link", None)),
                              "MISSION_PLANNER_FDA", False)
        if veri.get("gorev_hazir") is not True and not direct_cube:
            raise ValueError("FDA görev kapısı hazır değil; uçuş planı gönderilmedi")
        if direct_cube:
            veri["gorev_hazir"] = True
        veri["armed"] = self.yks.arm_acik
        veri["mod"] = self.yks.mod.get("iha")
        return veri

    def _yerde(self):
        veri = self.telemetri()
        if veri["armed"] is not False or veri["mod"] == "AUTO":
            raise ValueError("Hazırlık yalnız DISARM ve AUTO dışındayken yapılır")
        if sonlu_sayi(veri.get("gps_fix"), "GPS fix") < 3:
            raise ValueError("3D GPS konumu gerekli")
        if sonlu_sayi(veri.get("hiz"), "hız") > 0.5:
            raise ValueError("Araç hareketsiz olmalı")
        return veri

    def onizle(self, yukseklik, ileri):
        if self.tekrar.bekliyor:
            raise ValueError("Önceki yükleme sonucu bekleniyor")
        veri = self._yerde()
        if self.drone_baslangic is not None:
            veri = dict(self.drone_baslangic)
        plan = {
            "id": uuid.uuid4().hex, "lat": veri.get("lat"), "lon": veri.get("lon"),
            "yon": veri.get("yon"), "yukseklik_m": float(yukseklik), "ileri_m": float(ileri),
            "baslangic": {"lat": veri.get("lat"), "lon": veri.get("lon")},
        }
        if self.ika_baslangic is not None:
            plan["ika_baslangic"] = dict(self.ika_baslangic)
        if self.drone_test:
            plan["arama_kare_m"] = DRONE_TEST_ARAMA_KARE_M
        elif self._kare_kayitli:
            plan["arama_kare_m"] = float(self._kare_degeri)
        self.ayar = ayar_dogrula(plan)
        self.durum = "Önizleme hazır; henüz araca yüklenmedi."
        return self.ayar

    def _yerel_hedef_kaniti(self):
        isleme = getattr(self.yks, "yki_isleme", None)
        if isleme is None:
            raise ValueError("Canlı YKI işleme açık değil; kırmızı H kanıtı bekleniyor")
        snap = isleme.snapshot()
        yas = snap.get("frame_age_s")
        if yas is None or float(yas) > YKI_HEDEF_TAZELIK_S:
            raise ValueError("Kırmızı H karesi taze değil")
        hedef = snap.get("target")
        if not isinstance(hedef, dict) or hedef.get("lat") is None or hedef.get("lon") is None:
            raise ValueError("Kırmızı H GPS koordinatı henüz alınmadı")
        rota = snap.get("route")
        if not isinstance(rota, dict) or len(rota.get("waypoints") or ()) < 2:
            raise ValueError("Model rotası henüz üretilmedi")
        return hedef, rota

    def ika_baslangic_al(self):
        if not getattr(self.yks, "fda_kipi", False) or getattr(self.yks, "demo", False):
            raise ValueError("IKA koordinati yalniz gercek FDA kipinde alinabilir")
        veri = self._yerde()
        lat, lon = konum_dogrula(veri.get("lat"), veri.get("lon"))
        self.ika_baslangic = {
            "lat": lat,
            "lon": lon,
            "kaynak": "drone_gps_proxy",
        }
        self.durum = (
            f"IKA konumu drone GPS proxy'sinden kaydedildi: "
            f"{lat:.7f}, {lon:.7f}")
        return dict(self.ika_baslangic)

    def drone_baslangic_al(self):
        veri = self._yerde()
        self.drone_baslangic = dict(veri)
        self.durum = (f"Drone baslangic koordinati kaydedildi: "
                      f"{float(veri['lat']):.7f}, {float(veri['lon']):.7f}")
        return dict(self.drone_baslangic)

    def yukseklik_kaydet(self, deger):
        deger = sonlu_sayi(float(deger), "yukseklik_m")
        if not 0.0 < deger <= 1000.0:
            raise ValueError("Yukseklik 0..1000 m araliginda olmali")
        self._yukseklik_degeri = deger
        self._yukseklik_kayitli = True
        self.durum = f"Yukseklik kaydedildi: {deger:g} m"
        return deger

    def ileri_kaydet(self, deger):
        deger = sonlu_sayi(float(deger), "ileri_m")
        if not 0.0 < deger <= 1000.0:
            raise ValueError("Ileri mesafe 0..1000 m araliginda olmali")
        self._ileri_degeri = deger
        self._ileri_kayitli = True
        self.durum = f"Ileri mesafe kaydedildi: {deger:g} m"
        return deger

    def kare_kaydet(self, deger):
        deger = sonlu_sayi(float(deger), "arama_kare_m")
        if not 0.0 < deger <= 50.0:
            raise ValueError("Kare boyutu 0..50 m araliginda olmali")
        self._kare_degeri = deger
        self._kare_kayitli = True
        self.durum = f"Arama karesi kaydedildi: {deger:g} m"
        return deger

    def yukle(self):
        veri = self._yerde()
        ayar = ayar_dogrula(self.ayar)
        if self.yks._kanit_kilidi_var():
            raise ValueError("Hakem kanıt kaydı yazılamıyor")
        if mesafe_m((ayar["lat"], ayar["lon"]), (veri.get("lat"), veri.get("lon"))) > KALKIS_KONUM_TOLERANSI_M:
            raise ValueError("Konum değişti; önizlemeyi yeniden alın")
        yon = sonlu_sayi(veri.get("yon"), "burun yönü")
        if abs((yon - ayar["yon"] + 180.0) % 360.0 - 180.0) > KALKIS_YON_TOLERANSI_DERECE:
            raise ValueError("Burun yönü değişti; önizlemeyi yeniden alın")
        mesaj = self.yks._komut_mesaji(CMD_FDA_HAZIRLA, "iha")
        mesaj["gorev"] = dict(ayar)
        if not self.tekrar.baslat(mesaj):
            raise ValueError("Plan gönderilemedi veya önceki yükleme sürüyor")
        self.yks._kanit_yaz("FDA_PLAN_ISTEGI", gorev=ayar, hedef=list(hedef_konumu(ayar)))
        self.durum = "Yükleme, Pixhawk ACK ve geri okuma bekleniyor; ARM/AUTO gönderilmez."

    def ack(self, mesaj):
        bekleyen = self.tekrar.mesaj
        if not self.tekrar.bekliyor or not bekleyen:
            return
        if kritik_komut_ack_gecerli_mi(mesaj, bekleyen["seq"], CMD_FDA_HAZIRLA, node="iha"):
            self.tekrar.ack_geldi(mesaj)
            if getattr(type(getattr(self.yks, "link", None)),
                       "MISSION_PLANNER_FDA", False):
                self.durum = "Plan Orange Cube'a yüklenip geri okundu. Yönü değiştirmeyin; ARM ve AUTO kumandadan."
            else:
                self.durum = "Plan geri okunarak doğrulandı. Yönü değiştirmeyin; ARM ve AUTO pilotta."
            self.yks._kanit_yaz("FDA_PLAN_DOGRULANDI", gorev=bekleyen["gorev"])
        elif (mesaj.get("node") == "iha" and mesaj.get("sonuc") == "REJECTED"
              and mesaj.get("ref_tip") == "CMD" and mesaj.get("ref") == bekleyen["seq"]
              and mesaj.get("ref_cmd") == CMD_FDA_HAZIRLA
              and mesaj.get("oturum") == bekleyen.get("oturum")):
            self.tekrar.durum = VAZGECILDI
            self.durum = "PLAN KABUL EDİLMEDİ: " + str(mesaj.get("aciklama", mesaj.get("neden")))[:240]
            self.yks._logla(self.durum, "kirmizi")

    def basarili_rtl(self):
        veri = self.telemetri()
        if self.drone_test:
            if self.ayar is None or self.tekrar.durum != ONAYLANDI:
                raise ValueError("Pixhawk plan ACK ve geri okuma kaniti bekleniyor")
            if veri["armed"] is not True or veri["mod"] != "AUTO":
                raise ValueError("Test drone görevi için ARM ve AUTO teyidi gerekli")
            hedef, rota = self._yerel_hedef_kaniti()
            self.yks.acil_komut("RTL", teyit_anahtari="FDA_BASARILI_RTL",
                                teyit_metni="HAKEM: GÖREV BAŞARILI → RTL")
            self.yks._kanit_yaz(
                "FDA_HAKEM_RTL", gorev_id=veri.get("gorev_id"),
                hedef=hedef, rota=rota,
                komut_bekliyor=getattr(self.yks, "acil_bekleyen_komut", None) == "RTL")
            return
        if (veri["armed"] is not True or veri["mod"] != "AUTO"
                or veri.get("gorev_durum") != "ALGI_AKTIF" or not veri.get("gorev_id")):
            raise ValueError("Görev hedefinde aktif algı kanıtı yok; acil RTL düğmesi ayrı kullanılabilir")
        self.yks.acil_komut("RTL", teyit_anahtari="FDA_BASARILI_RTL",
                            teyit_metni="HAKEM: GÖREV BAŞARILI → RTL")
        self.yks._kanit_yaz("FDA_HAKEM_RTL", gorev_id=veri["gorev_id"],
                            komut_bekliyor=getattr(self.yks, "acil_bekleyen_komut", None) == "RTL")

    def tik(self):
        onceki = self.tekrar.durum
        if self.tekrar.bekliyor:
            try:
                self._yerde()
            except ValueError as exc:
                self.tekrar.durum = VAZGECILDI
                self.durum = f"Yükleme teyitsiz; tekrar durdu: {exc}. AUTO'ya geçmeyin."
            else:
                self.tekrar.tik()
        if onceki == BEKLIYOR and self.tekrar.durum == VAZGECILDI and self.durum.startswith("Yükleme,"):
            self.durum = "ACK alınamadı. Plan yüklendi sayılmaz; AUTO'ya geçmeyin."
        if self.pencere is not None and self.pencere.winfo_exists():
            try:
                veri = self.telemetri()
                durum = veri.get("gorev_durum", "Durum yok")
                if (self.ayar and veri.get("gorev_id") != self.ayar["id"]
                        and not getattr(type(getattr(self.yks, "link", None)),
                                       "MISSION_PLANNER_FDA", False)):
                    durum += " · yeni planın görev teyidi bekleniyor"
            except ValueError as exc:
                durum = str(exc)
            if self.drone_test:
                try:
                    hedef, rota = self._yerel_hedef_kaniti()
                    durum += (f" · KIRMIZI H {float(hedef['lat']):.7f},"
                              f" {float(hedef['lon']):.7f} · rota hazır")
                except ValueError as exc:
                    durum += f" · KIRMIZI H: {exc}"
            if self.yks._kritik_teyit_bekliyor("FDA_BASARILI_RTL"):
                self.hakem_dugmesi.config(text="GÖREV BAŞARILI → RTL? ONAYLAMAK İÇİN TEKRAR BAS")
            elif getattr(self.yks, "acil_bekleyen_komut", None) == "RTL":
                self.hakem_dugmesi.config(text="RTL: Pixhawk kabulü / taze mod teyidi bekleniyor")
            else:
                self.hakem_dugmesi.config(text="Hakem: GÖREV BAŞARILI → RTL (iki kez bas)")
            self.etiket.set(self.durum + "\n\nCANLI: " + durum)

    def ac(self):
        import tkinter as tk
        from tkinter import messagebox
        if self.pencere is not None and self.pencere.winfo_exists():
            self.pencere.lift()
            return
        self.pencere = tk.Toplevel(self.yks.kok)
        self.pencere.title("NAVITAS · FDA kalkış ve görev planı")
        self.pencere.geometry("760x700")
        self.pencere.configure(bg="#101923")
        self.etiket = tk.StringVar(self.pencere, value=self.durum)
        self.onizleme = tk.StringVar(
            self.pencere, value="1-5 adımlarını tamamlayın; sonra Pixhawk'a yükleyin.")
        varsayilan_irtifa = (VARSAYILAN_DRONE_TEST_IRTIFA_M if self.drone_test
                             else VARSAYILAN_IRTIFA_M)
        varsayilan_ileri = (VARSAYILAN_DRONE_TEST_ILERI_M if self.drone_test
                            else VARSAYILAN_ILERI_M)
        yukseklik = tk.StringVar(self.pencere, value=f"{varsayilan_irtifa:g}")
        ileri = tk.StringVar(self.pencere, value=f"{varsayilan_ileri:g}")
        kare = tk.StringVar(self.pencere, value="6")
        tk.Label(self.pencere, text="FDA GÖREV PLANI · 7 ADIM",
                 bg="#101923", fg="#58d4ef", font=("Segoe UI", 13, "bold")).pack(pady=18)
        for baslik, degisken in (("3 · Yükseklik (m)", yukseklik),
                                  ("4 · İleri mesafe (m)", ileri),
                                  ("5 · Arama karesi kenarı (m)", kare)):
            satir = tk.Frame(self.pencere, bg="#101923")
            satir.pack(pady=5)
            tk.Label(satir, text=baslik, width=45, anchor="w", bg="#101923", fg="white").pack(side="left")
            tk.Entry(satir, textvariable=degisken, width=10).pack(side="left")
        tk.Label(self.pencere, textvariable=self.onizleme, bg="#101923", fg="white",
                 justify="left", wraplength=710).pack(pady=16)

        def hata_koruma(islem):
            try:
                islem()
            except (ValueError, OSError) as exc:
                messagebox.showerror("FDA görevi", str(exc), parent=self.pencere)

        def plan_goster():
            if self.drone_baslangic is None:
                raise ValueError("Önce 2. adımla drone başlangıç koordinatını alın")
            ayar = self.onizle(yukseklik.get(), ileri.get())
            hedef = hedef_konumu(ayar)
            ika = ayar.get("ika_baslangic")
            ika_satir = (f"İKA konumu (drone GPS proxy): {ika['lat']:.7f}, {ika['lon']:.7f}\n"
                         if ika else "İKA başlangıç: alınmadı\n")
            self.onizleme.set(
                ika_satir
                + f"Drone başlangıç: {ayar['lat']:.7f}, {ayar['lon']:.7f} · burun {ayar['yon']:.1f}°\n"
                f"Önce {ayar['yukseklik_m']:g} m yüksel; sonra {ayar['ileri_m']:g} m ileri.\n"
                f"{'Beklenen merkez' if self.drone_test else 'Hedef'}: "
                f"{hedef[0]:.7f}, {hedef[1]:.7f} · hedefte sabit bekle / algıla.\n"
                + (f"Arama: {ayar['arama_kare_m']:g} m kare; KIRMIZI H koordinatı canlı videodan alınır.\n"
                   if "arama_kare_m" in ayar else "Arama karesi: belirtilmedi\n")
                + "Bu yön yükleme anında sabitlenir; sonradan aracı döndürürseniz yeniden hazırlayın.")

        def ika_al():
            self.ika_baslangic_al()
            self.onizleme.set(
                f"İKA konumu drone GPS proxy'sinden kaydedildi: {self.ika_baslangic['lat']:.7f}, "
                f"{self.ika_baslangic['lon']:.7f}")

        def drone_al():
            self.drone_baslangic_al()
            plan_goster()

        def yukseklik_al():
            self.yukseklik_kaydet(yukseklik.get())
            self.onizleme.set(f"Yükseklik kaydedildi: {self._yukseklik_degeri:g} m")

        def ileri_al():
            self.ileri_kaydet(ileri.get())
            self.onizleme.set(f"İleri mesafe kaydedildi: {self._ileri_degeri:g} m")

        def kare_al():
            self.kare_kaydet(kare.get())
            self.onizleme.set(f"Arama karesi kaydedildi: {self._kare_degeri:g} m")

        def yukle():
            if self.ika_baslangic is None:
                raise ValueError("Önce 1. adımla İKA konumundaki drone GPS'ini alın")
            if self.drone_baslangic is None:
                raise ValueError("Önce 2. adımla drone başlangıç koordinatını alın")
            if not (self._yukseklik_kayitli and self._ileri_kayitli and self._kare_kayitli):
                raise ValueError("Önce 3, 4 ve 5. adımlardaki değerleri kaydedin")
            plan_goster()
            if messagebox.askyesno("Pixhawk görevini değiştir",
                                  "Mevcut uçuş görevi bu planla değiştirilecek.\n"
                                  "Araç yerde ve DISARM olmalı. ARM/AUTO gönderilmez.\n"
                                  "Görev ACK/geri okuma ile doğrulanmadan AUTO'ya geçmeyin.\nDevam?",
                                  parent=self.pencere):
                self.yukle()

        tk.Button(
            self.pencere,
            text="1 · İKA KONUMUNU DRONE GPS'İNDEN AL",
                  command=lambda: hata_koruma(ika_al)).pack(pady=3)
        tk.Button(self.pencere, text="2 · DRONE BAŞLANGIÇ KOORDİNATINI AL",
                  command=lambda: hata_koruma(drone_al)).pack(pady=3)
        tk.Button(self.pencere, text="3 · YÜKSEKLİĞİ KAYDET",
                  command=lambda: hata_koruma(yukseklik_al)).pack(pady=3)
        tk.Button(self.pencere, text="4 · İLERİ MESAFEYİ KAYDET",
                  command=lambda: hata_koruma(ileri_al)).pack(pady=3)
        tk.Button(self.pencere, text="5 · ARAMA KARESİNİ KAYDET",
                  command=lambda: hata_koruma(kare_al)).pack(pady=3)
        tk.Button(self.pencere, text="6 · PLANI PIXHAWK'A YÜKLE / DOĞRULA",
                  command=lambda: hata_koruma(yukle)).pack(pady=3)
        self.hakem_dugmesi = tk.Button(
            self.pencere, text="7 · GÖREV BAŞARILI → EVE DÖN (RTL)", bg="#dcad45",
            command=lambda: hata_koruma(self.basarili_rtl))
        self.hakem_dugmesi.pack(pady=10)
        tk.Label(self.pencere, textvariable=self.etiket, bg="#101923", fg="#dbebf5",
                 wraplength=710, justify="left").pack(padx=15, pady=12)

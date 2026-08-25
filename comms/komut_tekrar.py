"""NEDEN: IKA_GO tek pakettir ve tek paket kaybı görevi geri dönülmez bitirir
(REVIEW_LOG D-02, şartname boşluk K4). Bu modül YKS'nin ACK'lı tekrar gönderim
durum makinesidir; Tk penceresine bağımlı DEĞİLDİR — GUI yalnız `tik()`'i
zamanlar ve `ack_geldi()`'yi besler, böylece mantık pencere açmadan test edilir.

Durumlar:
  BOS        → henüz komut yok
  BEKLIYOR   → gönderildi, ACK bekleniyor; her `tik` bir tekrar üretir
  ONAYLANDI  → İKA ACK döndü, tekrar durdu
  VAZGECILDI → üst sınır aşıldı, tekrar durdu (görev KAYBEDİLMEZ: çağıran
               düğmeyi yeniden açar, operatör tekrar tetikler)
"""
import time

BOS, BEKLIYOR, ONAYLANDI, VAZGECILDI = "BOS", "BEKLIYOR", "ONAYLANDI", "VAZGECILDI"


class AckliTekrar:
    """Tek bir komut mesajını ACK gelene dek sabit aralıkla, üst sınırlı tekrarla.

    gonder(mesaj) : taşıyıcıya AYNI mesajı (aynı seq) verir; True/False döner.
    aralik_s      : iki gönderim arası en az süre (karar_sozlesmesi'nden).
    ust_sinir     : toplam gönderim sayısı tavanı (ilk gönderim dâhil).
    saat          : monoton saat (test enjekte eder).
    """

    def __init__(self, gonder, aralik_s, ust_sinir, saat=time.monotonic):
        if aralik_s <= 0 or ust_sinir < 1:
            raise ValueError("aralik_s > 0 ve ust_sinir >= 1 olmalı")
        self._gonder = gonder
        self.aralik_s = float(aralik_s)
        self.ust_sinir = int(ust_sinir)
        self._saat = saat
        self.mesaj = None
        self.durum = BOS
        self.deneme = 0
        self.son_tx = None
        self.ack_zamani = None
        self.ack_mesaji = None

    # ── yaşam döngüsü ────────────────────────────────────────────────────────
    def baslat(self, mesaj):
        """İlk gönderim. Taşıyıcı reddederse BOS kalır ve False döner."""
        if self.durum == BEKLIYOR:
            return False                      # zaten uçuşta; ikinci başlatma yok
        self.mesaj = mesaj
        self.deneme = 0
        self.ack_zamani = self.ack_mesaji = None
        if not self._gonder(mesaj):
            self.durum = BOS
            return False
        self.deneme = 1
        self.son_tx = self._saat()
        self.durum = BEKLIYOR
        return True

    def tik(self):
        """Zamanlayıcı adımı. Dönen: durum (BEKLIYOR/ONAYLANDI/VAZGECILDI/BOS).

        Aralık dolmadıysa hiçbir şey yapmaz. Aralık dolduysa: üst sınıra
        ulaşılmışsa VAZGECILDI; değilse aynı mesajı yeniden gönderir.
        """
        if self.durum != BEKLIYOR:
            return self.durum
        simdi = self._saat()
        if simdi - self.son_tx < self.aralik_s:
            return self.durum
        if self.deneme >= self.ust_sinir:
            self.durum = VAZGECILDI
            return self.durum
        self.deneme += 1
        self.son_tx = simdi
        self._gonder(self.mesaj)              # taşıyıcı hatası = kayıp paket
        return self.durum

    def ack_geldi(self, ack_mesaji):
        """Gelen ACK bekleyen komuta aitse tekrarı durdur, True döner.

        Eşleme: ref == mesaj.seq; ACK `ref_tip` taşıyorsa mesaj tipiyle de
        eşleşmeli (CONTRACTS §6.6). Bekleyen yoksa ya da eşleşmezse False.
        """
        if self.durum != BEKLIYOR or self.mesaj is None:
            return False
        if ack_mesaji.get("type") != "ACK":
            return False
        if ack_mesaji.get("ref") != self.mesaj.get("seq"):
            return False
        ref_tip = ack_mesaji.get("ref_tip")
        if ref_tip is not None and ref_tip != self.mesaj.get("type"):
            return False
        self.durum = ONAYLANDI
        self.ack_zamani = self._saat()
        self.ack_mesaji = dict(ack_mesaji)
        return True

    @property
    def bekliyor(self):
        return self.durum == BEKLIYOR

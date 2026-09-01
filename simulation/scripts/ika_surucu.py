#!/usr/bin/env python3
"""P3/T149 (D-390) — İKA MOTOR SÜRÜCÜ SOYUTLAMASI.

NEDEN: `ika_nav` motor komutunu doğrudan `gz topic` subprocess'ine basıyordu;
gerçek İKA donanımı (seri/PWM) için hiçbir katman yoktu (T149). Ayrıca
`subprocess.run(..., timeout=1)` zaman aşımında istisna fırlatıyordu ve
navigate döngüsü bunu yakalamıyordu: donanım/simülatör takılırsa İKA "güvenli
duruş" değil ÇÖKME yaşardı.

Sözleşme (CONTRACTS §7.2):
  hiz_ver(sag, sol) -> bool   — tekerlek hızları (m/s); False = İLETİLEMEDİ.
                                İstisna SIZMAZ: her arıza False'tur.
  konum_al()        -> (x, y, z, yaw) ya da (None, None, None, None)
  durdur()          -> bool   — sıfır hız; arıza sayacına o da tabidir.
  saglikli()        -> bool   — ardışık hata < ARDISIK_HATA_TAVANI

Sağlık: ardışık `hiz_ver` hataları sayılır; başarı sayacı sıfırlar.
`ARDISIK_HATA_TAVANI = 3` — tek geçici aksama görevi durdurmasın, süreğen
arıza 3 turda (10 Hz'de ~0,3 s) güvenli duruşa çevrilsin. Tavan aşılınca
`ika_nav.navigate` son bir durdurma dener ve False döner (fail-closed).

Uygulamalar:
  GazeboSurucu — bugünkü gz yolu, BAYT-EŞ (T141 zinciri değişmez).
  SahteSurucu  — test: komut kaydı + poz dizisi + arıza enjeksiyonu.
  GercekSurucu — Faz B iskeleti: arka uçsuz kurulum DONANIM_YOK ile düşer
                 (sessiz NotImplementedError değil; 5 Eylül'de doldurulacak).
"""

import math
import re
import subprocess

#: Ardışık kaç hiz_ver arızası "sürücü yanıtsız" sayılır (ON_KAYIT §1.3).
ARDISIK_HATA_TAVANI = 3

VARSAYILAN_TOPIC = "~/ika/vel_cmd"
VARSAYILAN_MODEL = "ika"


class IkaSurucuHatasi(RuntimeError):
    """Sürücü kurulum/yapılandırma hatası (çalışma zamanı arızası DEĞİL)."""


class IkaSurucu:
    """Temel arayüz + ortak sağlık sözleşmesi. Alt sınıf `_hiz_ver`/`konum_al`."""

    def __init__(self):
        self.ardisik_hata = 0

    # --- ortak sözleşme ---

    def hiz_ver(self, sag, sol) -> bool:
        """Tekerlek hızlarını ilet; başarıyı bool dön. İstisna SIZMAZ."""
        try:
            iletildi = bool(self._hiz_ver(float(sag), float(sol)))
        except Exception:
            iletildi = False
        if iletildi:
            self.ardisik_hata = 0
        else:
            self.ardisik_hata += 1
        return iletildi

    def durdur(self) -> bool:
        return self.hiz_ver(0.0, 0.0)

    def saglikli(self) -> bool:
        return self.ardisik_hata < ARDISIK_HATA_TAVANI

    # --- alt sınıf yükümlülükleri ---

    def _hiz_ver(self, sag, sol) -> bool:
        raise NotImplementedError

    def konum_al(self):
        raise NotImplementedError


class GazeboSurucu(IkaSurucu):
    """DiffDrivePlugin'e gz CLI ile konuşur — komut biçimi BAYT-EŞ (T141).

    Eski `send_vel`/`get_pose` davranışının birebir taşınmasıdır; tek fark
    zaman aşımı/işletim hatasının artık istisna değil False olmasıdır.
    """

    def __init__(self, topic=VARSAYILAN_TOPIC, model=VARSAYILAN_MODEL):
        super().__init__()
        self.topic = topic
        self.model = model

    def _hiz_ver(self, sag, sol) -> bool:
        # T141 bayt-eşitlik: bu dizgi eski send_vel ile BİREBİR aynıdır.
        msg = f"position {{ x: {sag:.3f} y: {sol:.3f} z: 0 }}"
        try:
            subprocess.run(
                ["gz", "topic", "-p", self.topic, "-m", msg],
                capture_output=True, timeout=1
            )
        except (subprocess.TimeoutExpired, OSError):
            return False
        return True

    def konum_al(self):
        """`gz model -m <model> -p` çıktısını ayrıştır (eski get_pose kilidi)."""
        try:
            r = subprocess.run(
                ["gz", "model", "-m", self.model, "-p"],
                capture_output=True, text=True, timeout=2
            )
            text = r.stdout + r.stderr
        except (subprocess.TimeoutExpired, OSError):
            return None, None, None, None
        return self.ciktiyi_ayristir(text)

    @staticmethod
    def ciktiyi_ayristir(text):
        """Eski `get_pose`'un ayrıştırma davranışı — T2 kilidi altında."""
        try:
            # Format A: "position: (-23.0, -23.0, 0.12)"
            m = re.search(
                r'position[:\s(]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)'
                r'[,\s]+([+-]?\d+\.?\d*)',
                text
            )
            if m:
                x, y, z = (float(m.group(1)), float(m.group(2)),
                           float(m.group(3)))
                q = re.search(
                    r'orientation[:\s(]+([+-]?\d+\.?\d*)[,\s]+'
                    r'([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)[,\s]+'
                    r'([+-]?\d+\.?\d*)',
                    text
                )
                if q:
                    vals = [float(q.group(i)) for i in range(1, 5)]
                    if abs(vals[0]) >= abs(vals[3]):   # (w, x, y, z)
                        qw, qx, qy, qz = vals
                    else:                              # (x, y, z, w)
                        qx, qy, qz, qw = vals
                    yaw = math.atan2(2 * (qw * qz + qx * qy),
                                     1 - 2 * (qy * qy + qz * qz))
                else:
                    nums = re.findall(r'[+-]?\d+\.?\d*', text)
                    yaw = float(nums[5]) if len(nums) >= 6 else 0.0
                return x, y, z, yaw

            # Format B: sadece sayılar -> x y z roll pitch yaw
            nums = re.findall(r'[+-]?\d+\.?\d*', text)
            if len(nums) >= 6:
                return (float(nums[0]), float(nums[1]), float(nums[2]),
                        float(nums[5]))
        except Exception:
            pass
        return None, None, None, None


class SahteSurucu(IkaSurucu):
    """Test sürücüsü: komut kaydı, poz dizisi, arıza enjeksiyonu.

    ``arizali_cagrilar``: bu çağrı numaralarında (1 tabanlı) `_hiz_ver`
    False döner — "donanım sustu" senaryoları için.
    """

    def __init__(self, pozlar=None, arizali_cagrilar=()):
        super().__init__()
        self.komutlar = []
        self.pozlar = list(pozlar or [])
        self.arizali_cagrilar = set(arizali_cagrilar)
        self._cagri_no = 0

    def _hiz_ver(self, sag, sol) -> bool:
        self._cagri_no += 1
        if self._cagri_no in self.arizali_cagrilar:
            return False
        self.komutlar.append((sag, sol))
        return True

    def konum_al(self):
        if not self.pozlar:
            return None, None, None, None
        if len(self.pozlar) == 1:
            return self.pozlar[0]
        return self.pozlar.pop(0)


class GercekSurucu(IkaSurucu):
    """Gerçek donanım iskeleti — Faz B'de (5 Eylül) doldurulacak.

    Fail-loud (ON_KAYIT §1.4): arka uç verilmeden kurulamaz. Sessiz bir
    NotImplementedError yerine, kuru koşuda/sahada ANINDA görünen açık ret.
    """

    def __init__(self, arka_uc=None):
        if arka_uc is None:
            raise IkaSurucuHatasi(
                "DONANIM_YOK: GercekSurucu arka ucu henüz bağlanmadı — "
                "seri/PWM uygulaması Faz B'de (5 Eylül) doldurulacak. "
                "Simülasyon için GazeboSurucu, test için SahteSurucu kullan.")
        self.arka_uc = arka_uc
        super().__init__()

    def _hiz_ver(self, sag, sol) -> bool:
        return bool(self.arka_uc.hiz_ver(sag, sol))

    def konum_al(self):
        return self.arka_uc.konum_al()

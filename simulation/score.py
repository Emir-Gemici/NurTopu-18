#!/usr/bin/env python3
"""
Navitas TEKNOFEST 2026 — Puan Hesaplayıcı
Şartname V2 (13.04.2026) formülü
"""

from dataclasses import dataclass, field
from typing import Optional
import sys


@dataclass
class UcusVerisi:
    # Görev sonucu
    P_gorev: float = 0.0        # H'ye ulaştıysa 600, ulaşamadıysa 0

    # Ağırlıklar (gram)
    m_iha_gram: float = 25000   # İHA kalkış ağırlığı
    m_ika_gram: float = 10000   # İKA ağırlığı
    m_yuk_gram: float = 0       # Taşınan yük

    # Süreler (saniye)
    t_hazirlik_sn: float = 900  # Hazırlık süresi
    t_iha_sn: float = 900       # İHA görev süresi (fırlatma → iniş)
    t_ika_sn: float = 600       # İKA görev süresi (hareket → H teması)

    # Senaryo zorluğu
    K_zorluk: float = 1.0       # 1.0=Kolay, 1.5=Orta, 2.0=Zor

    # Ceza
    C_ceza: float = 0.0         # Ceza toplamı

    # Katılım puanları
    P_TI: float = 100           # Teknik muayene (100/50/0)
    P_ucus: float = 200         # Başarılı uçuş (senaryo başına 200)
    P_centilmenlik: float = 50  # Max 50

    # Rapor puanları (0-100 arası)
    ODR: float = 0
    DDR: float = 0
    FDA: float = 0
    UHDR: float = 0

    # Sapma (iniş)
    sapma_metre: float = 0.0    # İHA'nın iniş sapması

    # Manuel paraşüt açıldı mı?
    manuel_parasut: bool = False


def gecerlilik_kontrol(v: UcusVerisi) -> list[str]:
    """Geçersizlik koşullarını kontrol et, sorun listesi döndür."""
    sorunlar = []
    if v.m_iha_gram > 25000:
        sorunlar.append(f"KURAL İHLALİ: İHA MTOW ({v.m_iha_gram}g) > 25000g limiti!")
    if v.m_ika_gram > 10000:
        sorunlar.append(f"KURAL İHLALİ: İKA ağırlığı ({v.m_ika_gram}g) > 10000g limiti!")
    if v.t_iha_sn > 900:
        sorunlar.append(f"GEÇERSİZ: İHA görev süresi ({v.t_iha_sn}s) > 900s → uçuş geçersiz!")
    if v.t_ika_sn > 600:
        sorunlar.append(f"BAŞARISIZ: İKA süresi ({v.t_ika_sn}s) > 600s → görev başarısız!")
    if v.t_hazirlik_sn > 900:
        sorunlar.append(f"KURAL İHLALİ: Hazırlık süresi ({v.t_hazirlik_sn}s) > 900s limiti!")
    return sorunlar


def puan_hesapla(v: UcusVerisi, verbose: bool = True) -> dict:
    """
    TEKNOFEST şartname V2 formülüne göre toplam puan hesapla.
    Dönen dict: Puan2, P_katilim, Puan1, TOPLAM ve bileşenler.
    """

    # Geçerlilik kontrolü
    sorunlar = gecerlilik_kontrol(v)

    # Ceza eklemeleri
    C = v.C_ceza
    if v.sapma_metre > 0:
        C += v.sapma_metre * 5          # Her metre sapma -5 puan
    if v.manuel_parasut:
        C += 50                          # Manuel paraşüt -50 puan

    # Puan2 bileşenleri
    gorev_p   = v.P_gorev
    iha_agir  = (25000 - v.m_iha_gram) / 10
    iha_hiz   = (900   - v.t_iha_sn)   / 5
    hazirlik  = (900   - v.t_hazirlik_sn) / 30
    ika_agir  = (10000 - v.m_ika_gram)  / 15
    yuk_p     = v.m_yuk_gram * 0.01
    ika_hiz   = (600   - v.t_ika_sn)    / 15

    Puan2 = v.K_zorluk * (
        gorev_p + iha_agir + iha_hiz + hazirlik +
        ika_agir + yuk_p + ika_hiz - C
    )

    # Puan1 (rapor)
    Puan1 = (0.10 * v.ODR + 0.25 * v.DDR +
             0.55 * v.FDA + 0.10 * v.UHDR)

    # P (katılım)
    P = v.P_TI + v.P_ucus + v.P_centilmenlik

    # Genel puan
    Puan = 0.65 * Puan2 + 0.20 * P + 0.15 * Puan1

    sonuc = {
        # Bileşenler
        "Puan2_gorev":   round(gorev_p * v.K_zorluk, 2),
        "Puan2_iha_agr": round(iha_agir * v.K_zorluk, 2),
        "Puan2_iha_hiz": round(iha_hiz * v.K_zorluk, 2),
        "Puan2_hazrlk":  round(hazirlik * v.K_zorluk, 2),
        "Puan2_ika_agr": round(ika_agir * v.K_zorluk, 2),
        "Puan2_yuk":     round(yuk_p * v.K_zorluk, 2),
        "Puan2_ika_hiz": round(ika_hiz * v.K_zorluk, 2),
        "Puan2_ceza":    round(-C * v.K_zorluk, 2),
        # Toplamlar
        "Puan2_ucus":    round(Puan2, 2),
        "P_katilim":     round(P, 2),
        "Puan1_rapor":   round(Puan1, 2),
        "TOPLAM":        round(Puan, 2),
        # Durum
        "sorunlar":      sorunlar,
        "gecerli":       len(sorunlar) == 0,
    }

    if verbose:
        _print_sonuc(v, sonuc)

    return sonuc


def _print_sonuc(v: UcusVerisi, s: dict):
    senaryo_map = {1.0: "Kolay", 1.5: "Orta", 2.0: "Zor"}
    senaryo = senaryo_map.get(v.K_zorluk, f"{v.K_zorluk}x")

    print("\n" + "="*52)
    print("  NAVITAS TEKNOFEST 2026 — PUAN RAPORU")
    print("="*52)
    print(f"  Senaryo      : {senaryo} (K={v.K_zorluk})")
    print(f"  Görev sonucu : {'✓ BAŞARILI (H\'ye ulaşıldı)' if v.P_gorev >= 600 else '✗ BAŞARISIZ'}")
    print()
    print("  PUAN2 (Uçuş Performansı):")
    print(f"    Görev puanı        : {s['Puan2_gorev']:>8.1f}")
    print(f"    İHA hafifliği      : {s['Puan2_iha_agr']:>8.1f}  ({v.m_iha_gram}g)")
    print(f"    İHA hızı           : {s['Puan2_iha_hiz']:>8.1f}  ({v.t_iha_sn:.0f}s)")
    print(f"    Hazırlık hızı      : {s['Puan2_hazrlk']:>8.1f}  ({v.t_hazirlik_sn:.0f}s)")
    print(f"    İKA hafifliği      : {s['Puan2_ika_agr']:>8.1f}  ({v.m_ika_gram}g)")
    print(f"    Yük puanı          : {s['Puan2_yuk']:>8.1f}  ({v.m_yuk_gram}g)")
    print(f"    İKA hızı           : {s['Puan2_ika_hiz']:>8.1f}  ({v.t_ika_sn:.0f}s)")
    if s['Puan2_ceza'] != 0:
        print(f"    Ceza               : {s['Puan2_ceza']:>8.1f}")
    print(f"    ────────────��────────────────────")
    print(f"    PUAN2 TOPLAM       : {s['Puan2_ucus']:>8.1f}")
    print()
    print(f"  P   (Katılım puanı) : {s['P_katilim']:>8.1f}")
    print(f"  P1  (Rapor puanı)   : {s['Puan1_rapor']:>8.1f}")
    print()
    print(f"  GENEL TOPLAM: 0.65×{s['Puan2_ucus']:.1f} + 0.20×{s['P_katilim']:.1f} + 0.15×{s['Puan1_rapor']:.1f}")
    print(f"  ═══════════════════���══════════════════")
    print(f"  TOPLAM PUAN          : {s['TOPLAM']:>8.1f}")
    print("="*52)

    if s["sorunlar"]:
        print("\n  ⚠ UYARILAR / KURALLAR:")
        for u in s["sorunlar"]:
            print(f"    → {u}")
    print()


# ── Örnek senaryolar ─────────────────────────────────────────────────────────

ORNEKLER = {
    "hedef_zor": UcusVerisi(
        P_gorev=600, m_iha_gram=10000, t_iha_sn=180,
        t_hazirlik_sn=600, m_ika_gram=6500, m_yuk_gram=500,
        t_ika_sn=300, K_zorluk=2.0, C_ceza=0,
        P_TI=100, P_ucus=200, P_centilmenlik=40
    ),
    "hedef_orta": UcusVerisi(
        P_gorev=600, m_iha_gram=12000, t_iha_sn=300,
        t_hazirlik_sn=700, m_ika_gram=7000, m_yuk_gram=200,
        t_ika_sn=400, K_zorluk=1.5, C_ceza=0,
        P_TI=100, P_ucus=200, P_centilmenlik=30
    ),
    "inis_sapma": UcusVerisi(
        P_gorev=600, m_iha_gram=11000, t_iha_sn=250,
        t_hazirlik_sn=650, m_ika_gram=7500, m_yuk_gram=300,
        t_ika_sn=350, K_zorluk=1.5, sapma_metre=8.0,
        P_TI=100, P_ucus=200, P_centilmenlik=40
    ),
    "basarisiz": UcusVerisi(
        P_gorev=0, m_iha_gram=15000, t_iha_sn=600,
        t_hazirlik_sn=800, m_ika_gram=8000, m_yuk_gram=0,
        t_ika_sn=580, K_zorluk=1.0, C_ceza=0,
        P_TI=50, P_ucus=0, P_centilmenlik=20
    ),
}


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ORNEKLER:
        veri = ORNEKLER[sys.argv[1]]
        puan_hesapla(veri)
    else:
        print("Kullanım: python3 score.py [hedef_zor|hedef_orta|inis_sapma|basarisiz]")
        print("\nTüm örnek senaryolar:")
        for isim, veri in ORNEKLER.items():
            print(f"\n{'─'*40}")
            print(f"  Senaryo: {isim}")
            puan_hesapla(veri)


if __name__ == "__main__":
    main()

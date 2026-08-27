"""DEMO PROVASI — kaptan sunumunun MUTLU YOLU bastan sona kosulur (T175/D-323).

Tk PENCERESI ACILMADAN, gercek `demo_besle` beslemesi ve gercek protokol
yollariyla: OPEN_ROUTE -> hakem 1. onay -> IKA ACK kaniti -> hakem 2. onay ->
IHA_LANDED -> IKA BASLAT -> IKA_GO ACK -> HB TEMAS -> GOREV BASARILI.

NEDEN VAR: bu akis kaptanin onunde ILK KEZ denenmemeli. Bir adim tikanirsa
burada gorunur.

Kullanim:  <venv> results/demo_hazirlik/mutlu_yol.py
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[2]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui  # noqa: E402
from link import UDPLink  # noqa: E402


ADIMLAR = []


def _bekle(kosul, saniye, ne):
    """Kosul saglanana dek mesajlari isle; saglanmazsa False don."""
    bitis = time.time() + saniye
    while time.time() < bitis:
        if kosul():
            return True
        time.sleep(0.2)
    ADIMLAR.append((ne, False, f"{saniye:.0f} sn icinde olmadi"))
    return False


def main():
    link = UDPLink(bind=("127.0.0.1", 0))
    kok = mock.Mock()
    kok.after = lambda *a, **k: None

    with mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur"), \
         mock.patch.object(yks_gui.YksArayuz, "_tik"):
        g = yks_gui.YksArayuz(kok, link, demo=True)

    # Ekran bilesenlerini sahtele (mantik yolu ayni kalir). Ad listesi ELLE
    # yazilmaz — KAYNAKTAN turetilir; yoksa GUI'ye yeni bir dugme eklendiginde
    # prova, kusuru degil kendi eksigini bildirir (bir kez oyle oldu).
    _kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
    _widgetlar = set(re.findall(r"self\.(btn_[a-z0-9_]+|lbl_[a-z0-9_]+)", _kaynak))
    for ad in sorted(_widgetlar | {"rota_metin", "harita", "tuval"}):
        setattr(g, ad, mock.MagicMock())
    g.gunluk = mock.MagicMock()
    kayit = []
    g._logla = lambda satir, renk="soluk": kayit.append(satir)
    g._harita_ciz = lambda *a, **k: None
    g._kutu_ciz = lambda *a, **k: None
    g._inset_ciz = lambda *a, **k: None
    g._zincir = lambda *a, **k: None
    g._rota_analiz = lambda *a, **k: None

    yks_gui.demo_besle(link.port, g.demo_durum)

    # GUI'nin KENDI dinleyicisi (`_dinle`) mesajlari `g.gelen` kuyruguna koyar;
    # normalde Tk tiki (`_tik`) bosaltir. Tk yok, o yuzden kuyrugu BIZ bosaltiriz
    # — mesaj yolu yine uretimin kendi yolu.
    import threading
    dur = threading.Event()

    def dongusu():
        while not dur.is_set():
            try:
                while not g.gelen.empty():
                    m, adr = g.gelen.get()
                    try:
                        g._mesaj_isle(m, adr)
                    except Exception as exc:   # provada sessiz dusme YOK
                        kayit.append(
                            f"HATA _mesaj_isle: {type(exc).__name__}: {exc}")
            except Exception:
                pass
            time.sleep(0.05)

    t = threading.Thread(target=dongusu, daemon=True)
    t.start()

    ADIMLAR.append(("1 · OPEN_ROUTE geldi",
                    _bekle(lambda: g.rota is not None, 15, "OPEN_ROUTE"), ""))
    if g.rota is None:
        return _rapor()

    g.onayla()
    ADIMLAR.append(("2 · hakem 1. onay (tespit dogrulandi)", g.tespit_onayli, ""))

    ADIMLAR.append(("3 · IKA ACK kaniti (K8)",
                    _bekle(g.ika_aktarim_kaniti_var, 15, "IKA ACK"), ""))

    g.onayla()
    ADIMLAR.append(("4 · hakem 2. onay -> ACK", g.onaylandi, ""))

    ADIMLAR.append(("5 · IHA_LANDED inis kaniti",
                    _bekle(lambda: g.iha_landed_seq is not None, 25,
                           "IHA_LANDED"), ""))

    g.alan_girisi()
    g.ika_baslat()
    ADIMLAR.append(("6 · IKA BASLAT (SS2.2.5 kilidi acildi)",
                    g.t_ika0 is not None, ""))

    ADIMLAR.append(("7 · IKA_GO ACK (IKA ALDI)",
                    _bekle(lambda: g.ika_go_ack_zamani is not None, 20, "IKA_GO ACK"), ""))

    g.hb_temas()
    # NOT: gunluk metni TURKCE — "BAŞARILI" (S degil Ş). ASCII arayan bir
    # kontrol, gecen adimi DUSMUS gosterir (bir kez oyle oldu).
    ADIMLAR.append(("8 · HB TEMAS -> GOREV BASARILI",
                    any("BAŞARILI" in s for s in kayit), ""))

    dur.set()
    return _rapor(kayit)


def _rapor(kayit=None):
    print("=" * 62)
    print("DEMO MUTLU YOL PROVASI")
    print("=" * 62)
    tam = True
    for ad, ok, not_ in ADIMLAR:
        isaret = "OK  " if ok else "DUSTU"
        tam = tam and bool(ok)
        print(f"  [{isaret}] {ad}" + (f"  ({not_})" if not_ else ""))
    print("-" * 62)
    print("SONUC:", "MUTLU YOL TAM" if tam else "TIKANMA VAR")
    if kayit:
        print("\nson gunluk satirlari:")
        for s in kayit[-8:]:
            print("   ", s)
    return 0 if tam else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Q5: YKS tarafinda (gercek YksArayuz._ack_isle + AckliTekrar) capraz ACK karisikligi."""
import sys
from pathlib import Path
from unittest import mock
KOK = Path(r"O:\navitas")
for _y in (KOK / "comms", KOK / "codes"):
    sys.path.insert(0, str(_y))
from protocol import command, ack
from komut_tekrar import AckliTekrar, ONAYLANDI, BEKLIYOR
import yks_gui
from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S, IKA_GO_TEKRAR_UST_SINIRI,
                              PARASUT_TEKRAR_ARALIGI_S, PARASUT_TEKRAR_UST_SINIRI)

def yks_kur():
    y = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)      # Tk'siz (D-320 kalibi)
    y._logla = lambda *a, **k: None
    y._dugum_adresini_ogren = lambda *a, **k: None
    y._iha_havada_mi = lambda: True
    y.lbl_ika_go = mock.Mock(); y.btn_hb = mock.Mock(); y.btn_parasut = mock.Mock()
    y.rota = None; y.ika_rota_ack = {}; y.tespit_onayli = False; y.onaylandi = False
    y.t_ika0 = None; y.t_ika1 = None
    y.ika_go_tekrar = AckliTekrar(lambda m: True, IKA_GO_TEKRAR_ARALIGI_S, IKA_GO_TEKRAR_UST_SINIRI)
    y.parasut_tekrar = AckliTekrar(lambda m: True, PARASUT_TEKRAR_ARALIGI_S, PARASUT_TEKRAR_UST_SINIRI)
    return y

# Senaryo: IKA_GO seq=5 ve PARACHUTE seq=9 ayni anda bekliyor; YKS'nin rota seq'i 5 (IHA seq uzayi, capraz)
durumlar = [
    ("IKA'nin OPEN_ROUTE ACK'i ref=5 (rota seq=5 ile ayni sayi = IKA_GO seq)", ack(5, "ika", "OPEN_ROUTE")),
    ("IKA'nin IHA_LANDED ACK'i ref=5", ack(5, "ika", "IHA_LANDED")),
    ("IHA'nin CMD ACK'i ref=5 (yanlis dugum, dogru sayi)", ack(5, "iha", "CMD")),
    ("IKA'nin CMD ACK'i ref=9 (parasut seq'i ama dugum ika)", ack(9, "ika", "CMD")),
    ("ref_tip'siz ika ACK ref=5 (eski IKA)", ack(5, "ika")),
    ("DOGRU: IKA CMD ACK ref=5", ack(5, "ika", "CMD")),
    ("DOGRU: IHA CMD ACK ref=9", ack(9, "iha", "CMD")),
]
for ad, a in durumlar:
    y = yks_kur()
    y.ika_go_tekrar.baslat(command("IKA_GO", "ika", seq=5))
    y.parasut_tekrar.baslat(command("PARACHUTE", "iha", seq=9))
    y.rota = {"seq": 5, "type": "OPEN_ROUTE"}
    y._ack_isle(a, ("10.0.0.2", 5006))
    print(f"[{ad}]\n    ika_go={y.ika_go_tekrar.durum} parasut={y.parasut_tekrar.durum} "
          f"rota_ack_kaniti={list(y.ika_rota_ack)}")

"""SİM HAKEM — simülasyon zincirinde YKS hakemi + İHA uçuş-yazılımı olay üreticisi (T213).

⚠ SÖZLEŞME İSTİSNASI (CONTRACTS §6.7.x): Sahada `IHA_LANDED`'in TEK üreticisi
`comms/iha_inis_yayinci.py`'dir (Pixhawk iniş kanıtı) ve `IKA_GO` YKS operatörünün
manuel tetiğidir (§2.2.5). Bu modül YALNIZ `simulation/mujoco/` altında yaşar,
ürettiği her mesaj `"sim": true` alanı taşır ve SAHA KANITI SAYILMAZ. Üretim kodu
(`codes/`, `comms/`, `simulation/scripts/ika_nav.py`) bu modülü import ETMEZ
(kilit: tests/test_sim_mujoco_zincir.py grep testi). Alıcılar (`IkaReceiver`)
`sim` alanını yok sayar — davranış değişmez (bilinmeyen alan sözleşmesi §6.1).

Ne yapar (ON_KAYIT §5.4, H1-K4):
  · YKS ucu: OPEN_ROUTE gelince 1/2 "tespit doğrulandı" otomatik; İKA'nın
    OPEN_ROUTE ACK KOPYASI (K8 kanıtı, `IkaReceiver(yks_peer=hakem)`) görülünce
    2/2 "İKA'ya aktarıldı" ve İHA'ya `ACK(ref_tip="OPEN_ROUTE")`. Kanıt gelmezse
    ACK gitmez (fail-closed aynen). NO_ROUTE hemen ACK'lanır.
  · İHA zaman çizelgesi (iha_ucus.UcusProfili): sim saati `t_inis`'e gelince
    `IHA_LANDED` (node=iha, sim=true) İKA'ya, ACK'a dek tekrar; iniş sonrası
    `HEARTBEAT` (node=iha, sim=true) `IHA_INIS_HEARTBEAT_ARALIGI_S` ile sürer
    (K6 — link_lost yalnız heartbeat kesilince). Heartbeat iniş ÖNCESİNDE de
    akar (İHA havada heartbeat yayar, K1).
  · IKA_GO: İKA rota ACK kanıtı ∧ IHA_LANDED ACK'ı ∧ t ≥ t_inis → `CMD IKA_GO`
    (hedef=ika, sim=true), `AckliTekrar` ile (karar_sozlesmesi aralık/üst sınır)
    İKA ACK'ına dek aynı seq.
  Saat DIŞARIDAN verilir (`adimla(t)`); gerçek zaman kullanılmaz — sim saati
  fizikle birlikte ilerler, hakem her kontrol tikinde yoklanır (thread yok).
"""
from __future__ import annotations

import select
import sys
from pathlib import Path

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
for _p in (str(KOK / "comms"), str(KOK / "codes"), str(BURASI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from komut_tekrar import AckliTekrar                          # noqa: E402
from link import UDPLink                                      # noqa: E402
from protocol import (FrameReader, ack, command, encode,      # noqa: E402
                      heartbeat, iha_landed)
from karar_sozlesmesi import (IHA_INIS_HEARTBEAT_ARALIGI_S,   # noqa: E402
                              IKA_GO_TEKRAR_ARALIGI_S,
                              IKA_GO_TEKRAR_UST_SINIRI)

SIM_ALANI = "sim"
NODE_YKS = "yks"
NODE_IHA = "iha"


def sim_etiketle(msg: dict) -> dict:
    """Mesaja `sim: true` alanını koy (CONTRACTS §6.7.x) ve aynı sözlüğü döndür."""
    msg[SIM_ALANI] = True
    return msg


def sim_iha_landed(seq=None) -> dict:
    return sim_etiketle(iha_landed(seq))


def sim_ika_go(seq=None) -> dict:
    return sim_etiketle(command("IKA_GO", "ika", seq))


def sim_iha_heartbeat(seq=None) -> dict:
    return sim_etiketle(heartbeat(NODE_IHA, seq))


class SimHakem:
    def __init__(self, ika_addr, *, t_inis: float, saat, link=None,
                 hb_araligi: float = IHA_INIS_HEARTBEAT_ARALIGI_S,
                 ika_go_araligi: float = IKA_GO_TEKRAR_ARALIGI_S,
                 ika_go_ust_siniri: int = IKA_GO_TEKRAR_UST_SINIRI,
                 landed_araligi: float = 0.25, landed_ust_siniri: int = 40):
        self.ika_addr = (str(ika_addr[0]), int(ika_addr[1]))
        self.t_inis = float(t_inis)
        self.saat = saat
        self.link = link or UDPLink(bind=("127.0.0.1", 0), timeout=0.0)
        self.addr = ("127.0.0.1", self.link.port)
        self.hb_araligi = float(hb_araligi)
        self._son_hb = None
        self.iha_addr = None            # OPEN_ROUTE/NO_ROUTE'un geldiği adres
        self.rota = None                # kabul edilen OPEN_ROUTE
        self.rota_ack_kaniti = None     # İKA'nın OPEN_ROUTE ACK kopyası (K8)
        self.iha_ack_gonderildi = None  # İHA'ya giden OPEN_ROUTE ACK (2/2)
        self.no_route = None
        self.landed = AckliTekrar(self._ika_ya_gonder, landed_araligi, landed_ust_siniri, saat=saat)
        self.ika_go = AckliTekrar(self._ika_ya_gonder, ika_go_araligi, ika_go_ust_siniri, saat=saat)
        self.olaylar = []               # [{t, olay, ...}] hakem kaydı (sim)
        self.ack_listesi = []           # görülen tüm ACK'ler
        self.heartbeat_sayisi = 0
        self.t_landed = None
        self.t_ika_go = None
        self.t_ika_go_ack = None

    # ── gönderim ────────────────────────────────────────────────────────────
    def _ika_ya_gonder(self, msg) -> bool:
        try:
            self.link.send(encode(msg), self.ika_addr)
            return True
        except OSError:
            return False

    def _olay(self, olay, **alan):
        self.olaylar.append({"t": round(float(self.saat()), 3), "olay": olay, **alan})

    # ── alım ────────────────────────────────────────────────────────────────
    def _gelenleri_isle(self):
        sock = self.link.sock
        while True:
            hazir, _, _ = select.select([sock], [], [], 0)
            if not hazir:
                return
            try:
                d, addr = sock.recvfrom(4096)
            except (BlockingIOError, ConnectionResetError, ConnectionRefusedError, OSError):
                return
            for m in FrameReader().feed(d):
                self._mesaj(m, addr)

    def _mesaj(self, m, addr):
        tip = m.get("type")
        t = float(self.saat())
        if tip == "OPEN_ROUTE" and isinstance(m.get("seq"), int):
            self.iha_addr = addr
            if self.rota is None or self.rota.get("seq") != m["seq"]:
                self.rota = m
                self._olay("ROTA_ALINDI", seq=m["seq"], road=m.get("road"), conf=m.get("conf"),
                           waypoint=len(m.get("waypoints") or []))
                self._olay("HAKEM_ONAYI_1", seq=m["seq"], dayanak="SIM: otomatik")
            self._iki_bolu_iki_dene()
        elif tip == "NO_ROUTE" and isinstance(m.get("seq"), int):
            self.iha_addr = addr
            self.no_route = m
            self.link.send(encode(ack(m["seq"], NODE_YKS, "NO_ROUTE")), addr)
            self._olay("ROTA_YOK", seq=m["seq"], sebep=m.get("sebep"), detay=m.get("detay"))
        elif tip == "ACK" and isinstance(m.get("ref"), int):
            kayit = {"t": round(t, 3), "node": m.get("node"), "ref": m["ref"],
                     "ref_tip": m.get("ref_tip")}
            self.ack_listesi.append(kayit)
            self._olay("ACK_ALINDI", **{k: v for k, v in kayit.items() if k != "t"})
            if (m.get("node") == "ika" and m.get("ref_tip") == "OPEN_ROUTE"
                    and self.rota is not None and m["ref"] == self.rota.get("seq")):
                if self.rota_ack_kaniti is None:
                    self.rota_ack_kaniti = kayit
                    self._olay("IKA_AKTARIM_KANITI", seq=m["ref"])
                self._iki_bolu_iki_dene()
            if m.get("node") == "ika" and m.get("ref_tip") == "IHA_LANDED":
                self.landed.ack_geldi(m)
            if m.get("node") == "ika" and m.get("ref_tip") == "CMD":
                if self.ika_go.ack_geldi(m) and self.t_ika_go_ack is None:
                    self.t_ika_go_ack = t
                    self._olay("IKA_GO_ACK", seq=m["ref"])

    def _iki_bolu_iki_dene(self):
        """2/2 'İKA'ya aktarıldı' — yalnız K8 kanıtı varken İHA'ya ACK (fail-closed)."""
        if (self.rota is None or self.rota_ack_kaniti is None
                or self.iha_ack_gonderildi is not None or self.iha_addr is None):
            return
        seq = self.rota["seq"]
        self.link.send(encode(ack(seq, NODE_YKS, "OPEN_ROUTE")), self.iha_addr)
        self.iha_ack_gonderildi = {"t": round(float(self.saat()), 3), "seq": seq}
        self._olay("HAKEM_ONAYI_2", seq=seq, ref_tip="OPEN_ROUTE", dayanak="SIM: İKA ACK kopyası")

    # ── zaman çizelgesi ────────────────────────────────────────────────────
    def adimla(self, t=None):
        """Sim saati `t`'de hakemi yokla: gelenler, heartbeat, IHA_LANDED, IKA_GO."""
        t = float(self.saat() if t is None else t)
        self._gelenleri_isle()
        if self._son_hb is None or t - self._son_hb >= self.hb_araligi:
            self._ika_ya_gonder(sim_iha_heartbeat())
            self._son_hb = t
            self.heartbeat_sayisi += 1
        if t >= self.t_inis and self.t_landed is None:
            self.t_landed = t
            self.landed.baslat(sim_iha_landed())
            self._olay("IHA_INIS", seq=self.landed.mesaj["seq"], sim=True)
        self.landed.tik()
        if (self.t_landed is not None and self.landed.durum == "ONAYLANDI"
                and self.rota_ack_kaniti is not None and self.t_ika_go is None):
            self.t_ika_go = t
            self.ika_go.baslat(sim_ika_go())
            self._olay("IKA_GO", seq=self.ika_go.mesaj["seq"], sim=True)
        self.ika_go.tik()
        self._gelenleri_isle()

    def kapat(self):
        try:
            self.link.close()
        except OSError:
            pass

    def ozet(self) -> dict:
        return {
            "hakem_addr": list(self.addr), "t_inis": self.t_inis,
            "rota_seq": None if self.rota is None else self.rota.get("seq"),
            "rota_ack_kaniti": self.rota_ack_kaniti, "iha_ack_gonderildi": self.iha_ack_gonderildi,
            "no_route": None if self.no_route is None else {
                "seq": self.no_route.get("seq"), "sebep": self.no_route.get("sebep")},
            "t_landed": self.t_landed, "landed_durum": self.landed.durum, "landed_deneme": self.landed.deneme,
            "t_ika_go": self.t_ika_go, "t_ika_go_ack": self.t_ika_go_ack,
            "ika_go_durum": self.ika_go.durum, "ika_go_deneme": self.ika_go.deneme,
            "heartbeat_sayisi": self.heartbeat_sayisi,
            "ack_listesi": list(self.ack_listesi), "olaylar": list(self.olaylar),
            "sim": True,
        }

"""NEDEN: Rota, canlılık, manuel izin ve İHA iniş kanıtı UDP/seri taşıyıcıdan
bağımsız, çerçeveli ve ACK ile ilişkilendirilebilir mesajlar olmalıdır.

Navitas haberleşme protokolü — taşıyıcıdan BAĞIMSIZ çerçeveli JSON mesajları.

Aynı mesajlar hem dev/sim'de UDP üzerinden, hem sahada SiK Radio 433 MHz
(transparan seri) üzerinden gider. Çerçeveleme: newline ('\\n') ile ayrılmış
JSON satırları — hem UDP hem seri akış için güvenli.

Mesaj tipleri:
  OPEN_ROUTE — İHA'nın tespit ettiği açık yol (asıl görev verisi)
  HEARTBEAT  — bağlantı canlılığı (failsafe için)
  ACK        — alındı onayı (YKS/İKA → İHA)
  CMD        — YKS operatör komutu (ör. IKA_GO)
  IHA_LANDED — İHA uçuş yazılımının doğruladığı iniş tamam olayı
"""
import itertools
import json
import math
import re
import time

PROTOCOL_VERSION = 1
ROAD_LABEL = {1: "sol", 2: "orta", 3: "sag"}     # şartname yön kuralı
LABEL_ROAD = {v: k for k, v in ROAD_LABEL.items()}
ACK_SONUC_KABUL = "ACCEPTED"

# Kritik komut oturumu bir kimlik/yeniden-oynatma alanidir. Rastgeleligi bu
# modul URETMEZ (sahip YKS'dir), fakat tel uzerindeki bicimi burada tek yerde
# kilitler: UUID/hex/token-safe ASCII, bosluk ve ayirici JSON karakterleri yok.
OTURUM_EN_AZ_KARAKTER = 16
OTURUM_EN_COK_KARAKTER = 64
_OTURUM_DESENI = re.compile(
    rf"^[A-Za-z0-9_-]{{{OTURUM_EN_AZ_KARAKTER},{OTURUM_EN_COK_KARAKTER}}}$")

_seq = itertools.count(1)


# ── Mesaj üreticiler ──────────────────────────────────────────────────────────

def open_route(road, conf, waypoints=None, ref_xy=None, seq=None):
    """İHA → (YKS, İKA): açık yol = road (1=sol 2=orta 3=sag) + güven +
    referans noktası + yerel waypoint'ler.

    ref_xy    : İHA'nın ilan ettiği başlangıç referans noktası [x, y] (metre;
                İKA rotayı bu noktaya göre kendi çerçevesine oturtur).
    waypoints : referans noktasına GÖRE yerel [[x,y], ...] listesi (metre).
    """
    if road not in ROAD_LABEL:
        raise ValueError(f"road 1-3 olmalı, gelen: {road}")
    if isinstance(conf, bool):
        raise ValueError("conf sonlu ve 0..1 aralığında sayısal olmalı")
    try:
        conf = float(conf)
    except (TypeError, ValueError) as exc:
        raise ValueError("conf sonlu ve 0..1 aralığında sayısal olmalı") from exc
    if not math.isfinite(conf) or not 0.0 <= conf <= 1.0:
        raise ValueError("conf sonlu ve 0..1 aralığında olmalı")
    return {
        "v": PROTOCOL_VERSION, "type": "OPEN_ROUTE",
        "road": int(road), "label": ROAD_LABEL[road],
        # Guven kapisi esigin hemen altini ayirt edebilmelidir. Burada sabit
        # ondaliga yuvarlamak esik-altini esigin kendisine tasiyabiliyordu.
        "conf": conf,
        "ref_xy": ([round(float(ref_xy[0]), 2), round(float(ref_xy[1]), 2)]
                   if ref_xy else None),
        "waypoints": waypoints or [],          # [[x,y], ...] ref_xy'ye göre yerel
        "seq": next(_seq) if seq is None else int(seq),
        "t": round(time.time(), 3),
    }


def rota_yok(sebep, detay=None, seq=None):
    """İHA → (YKS, İKA): doğrulanmış rota üretilemedi bilgisini gönder.

    NEDEN ayrı bir mesaj türü: ``OPEN_ROUTE`` yalnız hareket edilecek yol
    kimliği ve geometri taşır. Costmap rota üretemediğinde sessizlik, bağlantı
    kesintisiyle güvenli ret kararını ayırt edilemez yapar.
    """
    sebep = str(sebep).strip()
    if not sebep:
        raise ValueError("NO_ROUTE için sebep gerekli")
    msg = {
        "v": PROTOCOL_VERSION, "type": "NO_ROUTE", "sebep": sebep,
        "seq": next(_seq) if seq is None else int(seq),
        "t": round(time.time(), 3),
    }
    if detay is not None:
        msg["detay"] = str(detay)
    return msg


# T162 (ON_KAYIT SS28): YKS heartbeat'teki `x`,`y` ile sartname SS6.2/SS6.4
# ALAN IHLALI denetimi yapiyor (`comms/yks_gui.py`), ama URETIMDE bu alanlari
# ureten hicbir yol yoktu — kapi sahada OLUYDU. Alanlar ISTEGE BAGLIDIR:
# verilmezse mesaj eskisiyle ALAN ALAN AYNIDIR (kilit: test_t162...).
# A2 (D-381): "karar_yas" — IHA'nin son ALGI KARARININ yasi (sn, monotonik).
# NEDEN HEARTBEAT'TE: IHA rotayi ACK alana kadar tekrarlar, ACK gelince SUSAR
# (T172/D-321); ACK'ten sonra da akmaya devam eden TEK kanal heartbeat'tir.
# D-374 olctu: gercek ucusta algi 45-51 s'lik sahne bagintili araliklarda HIC
# karar uretemiyor — o aralikta hat CANLI gorunur, algi OLUDUR. Bu alan ikisini
# ayirir. Alan YOKSA yas BILINMIYOR demektir; alici TAZE SAYMAZ (fail-closed).
HEARTBEAT_TELEMETRI_ALANLARI = (
    "x", "y", "alt", "hiz", "yon", "bat", "uydu", "karar_yas",
    # Ham GNSS yalnız sayısal YKİ gösterimi içindir; semantik saha haritasının
    # koordinat sistemi değildir. ``armed`` ise YKİ'nin komut gönderiminden
    # durum UYDURMASINI engelleyen, Pixhawk HEARTBEAT'inden gelen gerçektir.
    "lat", "lon", "gps_fix", "armed", "mod", "pixhawk_canli",
)


def heartbeat(node, seq=None, **telemetri):
    msg = {"v": PROTOCOL_VERSION, "type": "HEARTBEAT", "node": node,
           "seq": next(_seq) if seq is None else int(seq),
           "t": round(time.time(), 3)}
    for ad in HEARTBEAT_TELEMETRI_ALANLARI:
        deger = telemetri.get(ad)
        if deger is None:
            continue          # FAIL-CLOSED: bilinmeyen alan YAZILMAZ (sifir degil)
        msg[ad] = deger
    bilinmeyen = sorted(set(telemetri) - set(HEARTBEAT_TELEMETRI_ALANLARI))
    if bilinmeyen:
        raise ValueError(f"heartbeat'te sozlesme disi alan: {bilinmeyen}")
    return msg


def ack(ref_seq, node, ref_tip=None, *, ref_cmd=None, sonuc=None):
    """Alındı onayı. ``ref_tip`` (isteğe bağlı): onaylanan mesajın tipi
    (``"OPEN_ROUTE"``, ``"CMD"`` …). NEDEN: `seq` sayaçları düğüm başınadır;
    YKS'nin IKA_GO seq'i ile İHA'nın OPEN_ROUTE seq'i çakışabilir. YKS, İKA'dan
    gelen ACK'ı hangi bekleyene bağlayacağını `ref_tip` ile ayırt eder.
    ``ref_cmd`` onaylanan CMD'nin adını, ``sonuc`` ise uç birimin sonucunu
    taşır. Bu iki alan isteğe bağlıdır: eski üreticilerin ACK biçimi alan alan
    aynı kalır. Ancak ARM/DISARM gibi eyleyici durumları yalnız
    :func:`kritik_komut_ack_gecerli_mi` ile doğrulanan güçlü ACK'e dayanır.
    Alan yoksa genel alıcı yalnız `ref` ile eşler (geriye uyumlu,
    CONTRACTS §6.6)."""
    msg = {"v": PROTOCOL_VERSION, "type": "ACK", "ref": int(ref_seq),
           "node": node, "t": round(time.time(), 3)}
    if ref_tip is not None:
        msg["ref_tip"] = str(ref_tip)
    if ref_cmd is not None:
        msg["ref_cmd"] = str(ref_cmd)
    if sonuc is not None:
        msg["sonuc"] = str(sonuc)
    return msg


def kritik_komut_ack_gecerli_mi(mesaj, ref_seq, ref_cmd, node="iha"):
    """ARM/DISARM gibi eyleyici durumunu değiştirecek ACK'i sıkı doğrula.

    Genel ACK geriye uyumluluk için `ref_cmd`/`sonuc` taşımayabilir; bu eski
    biçim yalnız teslim tekrarını durdurabilir, aracın fiziksel durumuna kanıt
    olamaz. Kritik komutta düğüm, mesaj tipi, komut adı ve Pixhawk kabul
    sonucu birlikte eşleşmezse fail-closed ``False`` döner.
    """
    if not isinstance(mesaj, dict) or mesaj.get("type") != "ACK":
        return False
    if isinstance(ref_seq, bool) or not isinstance(ref_seq, int):
        return False
    mesaj_ref = mesaj.get("ref")
    if isinstance(mesaj_ref, bool) or not isinstance(mesaj_ref, int):
        return False
    return (
        mesaj_ref == ref_seq
        and mesaj.get("node") == node
        and mesaj.get("ref_tip") == "CMD"
        and mesaj.get("ref_cmd") == ref_cmd
        and mesaj.get("sonuc") == ACK_SONUC_KABUL
    )


def oturum_dogrula(oturum):
    """Kritik CMD yeniden-oynatma kimligini dogrula ve degistirmeden dondur."""
    if not isinstance(oturum, str) or _OTURUM_DESENI.fullmatch(oturum) is None:
        raise ValueError(
            "oturum yalniz ASCII harf/rakam/_/- iceren "
            f"{OTURUM_EN_AZ_KARAKTER}..{OTURUM_EN_COK_KARAKTER} karakter "
            "olmalidir")
    return oturum


def command(cmd, hedef, seq=None, *, oturum=None):
    """YKS → İHA/İKA operatör komutu (ör. ARM / DISARM / IKA_GO).

    Şartname §2.2.5: İKA intikali YKS'deki takım üyesince manuel tetiklenir —
    IKA_GO bu tetik içindir. Alıcılar bilmedikleri tipi yok sayar (geriye uyumlu).
    """
    mesaj = {"v": PROTOCOL_VERSION, "type": "CMD", "cmd": str(cmd),
             "hedef": hedef, "seq": next(_seq) if seq is None else int(seq),
             "t": round(time.time(), 3)}
    if oturum is not None:
        mesaj["oturum"] = oturum_dogrula(oturum)
    return mesaj


def iha_landed(seq=None):
    """İHA → (YKS, İKA): üretim uçuşu başarıyla tamamlanıp yere temas edildi.

    Bu olay operatör komutu değildir; YKS'deki manuel ``İHA İNDİ`` düğmesi
    güvenlik latch'ini kuramaz. Alıcı, ``node`` ve ``seq`` alanlarını latch'ten
    önce doğrular.
    """
    return {
        "v": PROTOCOL_VERSION,
        "type": "IHA_LANDED",
        "node": "iha",
        "seq": next(_seq) if seq is None else int(seq),
        "t": round(time.time(), 3),
    }


# ── Çerçeveleme (encode/decode) ───────────────────────────────────────────────

def encode(msg) -> bytes:
    """Mesaj dict → tek satır JSON + '\\n' (çerçeve)."""
    return (json.dumps(msg, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def decode(line: bytes) -> dict:
    """Tek çerçeve (satır) → mesaj dict."""
    return json.loads(line.decode("utf-8").strip())


#: Çerçevelenmemiş baytların tutulabileceği tavan (P2/D-388 · ön kayıt S5).
#: SiK hattında gürültü newline üretmeden uzun süre akabilir; tavansız tampon
#: 15 dakikalık uçuşta sessiz bellek büyümesi demektir (ölçüldü: 1 MiB çöp →
#: 1 MiB tampon). En uzun meşru çerçevemizin (< 4 KiB) on altı katıdır.
CERCEVE_TAMPON_TAVANI = 64 * 1024


class FrameReader:
    """Seri/UDP byte akışından newline çerçevelerini ayıklar (parçalı veri güvenli).

    Tampon ``CERCEVE_TAMPON_TAVANI`` ile sınırlıdır: içinde tek bir newline
    olmadan tavanı aşan birikim **çerçeve değildir**, atılır (``atilan_bayt``
    sayacına yazılır). Meşru bir çerçeve asla bu boyuta ulaşmaz; atma yalnız
    gürültü/senkron kaybı durumunda olur ve hat bir sonraki newline'da
    kendiliğinden toparlanır.
    """

    def __init__(self, tampon_tavani=CERCEVE_TAMPON_TAVANI):
        self._buf = b""
        self._tampon_tavani = int(tampon_tavani)
        self.atilan_bayt = 0

    def feed(self, data: bytes):
        """Gelen byte'ları besle, tamamlanan her mesajı yield et."""
        if not data:
            return
        self._buf += data
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            line = line.strip()
            if line:
                try:
                    yield decode(line)
                except (ValueError, UnicodeDecodeError, RecursionError):
                    # bozuk çerçeveyi at (RF gürültüsü).
                    # NEDEN RecursionError (D-405 · "Hub sureci derin ic ice
                    # JSON satirinda RecursionError ile OLUR"): json.loads
                    # `[[[[...` gibi derin iç içe TEK satırda ValueError değil
                    # RecursionError üretir (ölçüldü: b"["*3000+b"\n"). Bu bir
                    # çerçeve değildir; yutulmazsa seri hattın tek erişim
                    # noktası olan hub ve her tüketici (`IhaKomutAlici.poll`)
                    # tek satırla ölür. Tampon satırdan zaten arındırıldı;
                    # sonraki geçerli çerçeve geçer.
                    pass
        # Süzmeden SONRA bakılır: kalan artık newline içermez, yani tek bir
        # çerçeve sınırı taşımaz. Tavanı aşıyorsa çerçeve değil gürültüdür.
        if len(self._buf) > self._tampon_tavani:
            self.atilan_bayt += len(self._buf)
            self._buf = b""

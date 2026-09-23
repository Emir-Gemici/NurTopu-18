"""PC/YKS video kaynağı keşfi ve canlı akış doğrulaması.

Bu modül yalnızca video hattını yönetir. MAVLink, rota, hakem ACK'i veya uçuş
komutu üretmez. Kaynak, ilk kare gerçekten çözüldüğünde canlı kabul edilir;
yalnızca TCP portunun açık olması yeterli değildir.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import socket
import time
from typing import Callable, Iterable
from urllib.parse import urlparse


DEFAULT_RTSP_URL = "rtsp://192.168.144.25:8554/main.264"
DEFAULT_RTSP_PORT = 8554
DEFAULT_RTSP_PATHS = ("main.264", "video0", "video1", "live")
DEFAULT_HOSTS = (
    "192.168.144.25",
    "192.168.144.20",
    "192.168.144.11",
    "192.168.144.12",
    "192.168.43.1",
    "192.168.42.1",
)
DEFAULT_CACHE = Path("results") / "yki_rtsp" / "video_source.json"
TCP_TIMEOUT_S = 0.35
PROBE_TIMEOUT_S = 3.0


@dataclass(frozen=True)
class VideoAdayi:
    """Tek bir video kaynağı ve sıralama bilgisi."""

    url: str
    ad: str
    tur: str
    oncelik: int
    aciklama: str
    host: str | None = None
    port: int | None = None

    def sozluk(self) -> dict:
        return {
            "url": self.url,
            "ad": self.ad,
            "tur": self.tur,
            "oncelik": self.oncelik,
            "aciklama": self.aciklama,
            "host": self.host,
            "port": self.port,
        }


@dataclass(frozen=True)
class VideoSonucu:
    aday: VideoAdayi
    durum: str
    sebep: str
    ayrinti: dict
    sure_s: float

    @property
    def canli(self) -> bool:
        return self.durum == "CANLI"

    def sozluk(self) -> dict:
        return {
            **self.aday.sozluk(),
            "durum": self.durum,
            "sebep": self.sebep,
            "ayrinti": self.ayrinti,
            "sure_s": round(self.sure_s, 3),
        }


def _url_bilgisi(url: str) -> tuple[str, str | None, int | None]:
    metin = str(url).strip()
    if not metin:
        raise ValueError("video kaynağı boş olamaz")
    if "://" not in metin:
        return "cihaz", None, None
    parsed = urlparse(metin)
    tur = parsed.scheme.lower()
    if tur not in {"rtsp", "rtsps", "udp", "http", "https", "srt"}:
        raise ValueError(f"desteklenmeyen video protokolü: {parsed.scheme}")
    return tur, parsed.hostname, parsed.port


def aday_olustur(url: str, *, ad: str = "elle", oncelik: int = 0,
                 aciklama: str = "operatör kaynağı") -> VideoAdayi:
    tur, host, port = _url_bilgisi(url)
    return VideoAdayi(str(url).strip(), ad, tur, int(oncelik), aciklama,
                     host, port)


def yerel_ipv4ler() -> list[str]:
    """PC'deki IPv4 arayüzlerini ağ keşfi kanıtı olarak döndürür."""
    try:
        import psutil
    except Exception:
        return []
    sonuc = []
    for adresler in psutil.net_if_addrs().values():
        for adres in adresler:
            if adres.family == socket.AF_INET and adres.address not in sonuc:
                sonuc.append(adres.address)
    return sorted(sonuc)


def ayni_ag(host: str, *, yereller: Iterable[str] | None = None) -> bool:
    """Aday host, PC'nin doğrudan bağlı olduğu /24 ağlardan birinde mi?"""
    if not host:
        return False
    yereller = list(yereller if yereller is not None else yerel_ipv4ler())
    try:
        hedef = socket.inet_aton(host)
    except OSError:
        return False
    _ = hedef
    hedef_on = host.rsplit(".", 1)[0]
    return any(str(ip).rsplit(".", 1)[0] == hedef_on for ip in yereller)


def adaylari_uret(elle: str | None = None, *, hatirlanan: str | None = None,
                  hosts: Iterable[str] = DEFAULT_HOSTS,
                  rtsp_port: int = DEFAULT_RTSP_PORT,
                  yollar: Iterable[str] = DEFAULT_RTSP_PATHS,
                  udp_urls: Iterable[str] = ()) -> list[VideoAdayi]:
    """PC/MK15 için kaynak adaylarını öncelik sırasıyla üretir."""
    adaylar: list[VideoAdayi] = []
    if elle:
        adaylar.append(aday_olustur(elle, ad="elle", oncelik=0))
    if hatirlanan and hatirlanan != elle:
        adaylar.append(aday_olustur(
            hatirlanan, ad="önceki-canlı", oncelik=1,
            aciklama="son canlı doğrulanan kaynak"))
    yereller = yerel_ipv4ler()
    for host_no, host in enumerate(hosts):
        ag_onceligi = 0 if ayni_ag(host, yereller=yereller) else 20
        for yol_no, yol in enumerate(yollar):
            url = f"rtsp://{host}:{int(rtsp_port)}/{str(yol).lstrip('/')}"
            adaylar.append(VideoAdayi(
                url=url,
                ad=f"mk15-{host.rsplit('.', 1)[-1]}-{yol_no}",
                tur="rtsp",
                oncelik=10 + ag_onceligi + host_no * 3 + yol_no,
                aciklama=("MK15/Air Unit RTSP · aynı ağ" if ag_onceligi == 0
                          else "MK15/Air Unit RTSP · aday ağ"),
                host=host,
                port=int(rtsp_port),
            ))
    for no, url in enumerate(udp_urls):
        adaylar.append(aday_olustur(
            url, ad=f"udp-{no}", oncelik=60 + no,
            aciklama="MK15/Air Unit UDP video adayı"))
    sonuc = []
    gorulen = set()
    for aday in sorted(adaylar, key=lambda item: item.oncelik):
        if aday.url not in gorulen:
            gorulen.add(aday.url)
            sonuc.append(aday)
    return sonuc


def tcp_acik_mi(host: str, port: int, timeout_s: float = TCP_TIMEOUT_S) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout_s):
            return True
    except OSError:
        return False


def akis_dogrula(url: str, timeout_s: float = PROBE_TIMEOUT_S) -> tuple[bool | None, dict]:
    """Gerçek bir video karesi çözülüyor mu? ``None`` = OpenCV yok."""
    try:
        import cv2
    except Exception as exc:
        return None, {"sebep": f"OpenCV yok: {type(exc).__name__}"}
    parsed = urlparse(url) if "://" in str(url) else None
    if parsed is not None and parsed.scheme.lower() == "rtsp":
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            "rtsp_transport;tcp|stimeout;1000000|rw_timeout;1000000|"
            "fflags;nobuffer|flags;low_delay|max_delay;500000"
        )
    kaynak = int(url) if str(url).isdigit() else url
    bas = time.monotonic()
    try:
        cap = cv2.VideoCapture(kaynak, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap.release()
            return False, {"sebep": "VideoCapture açılamadı"}
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        while time.monotonic() - bas < float(timeout_s):
            ok, frame = cap.read()
            if ok and frame is not None and getattr(frame, "size", 0):
                return True, {
                    "yöntem": "opencv-ffmpeg",
                    "genişlik": int(frame.shape[1]),
                    "yükseklik": int(frame.shape[0]),
                    "geçen_ms": round((time.monotonic() - bas) * 1000, 1),
                }
        return False, {"sebep": "ilk kare zaman aşımında gelmedi"}
    except Exception as exc:
        return False, {"sebep": f"{type(exc).__name__}: {exc}"}
    finally:
        try:
            cap.release()
        except (UnboundLocalError, AttributeError):
            pass


def tara(adaylar: Iterable[VideoAdayi], *, probe: Callable = akis_dogrula,
         tcp_probe: Callable = tcp_acik_mi, ilk_canli_dur: bool = True,
         saat: Callable = time.monotonic) -> list[VideoSonucu]:
    """Adayları doğrular; kaynak bulunamazsa eski kare seçilmez."""
    sonuclar = []
    secildi = False
    tcp_cache: dict[tuple[str, int], bool] = {}
    for aday in adaylar:
        if secildi and ilk_canli_dur:
            sonuclar.append(VideoSonucu(
                aday, "ATLANDI", "önceki aday canlı bulundu", {}, 0.0))
            continue
        bas = saat()
        if aday.tur in {"rtsp", "rtsps", "http", "https"} and aday.host and aday.port:
            anahtar = (aday.host, aday.port)
            if anahtar not in tcp_cache:
                tcp_cache[anahtar] = bool(tcp_probe(aday.host, aday.port))
            if not tcp_cache[anahtar]:
                sonuclar.append(VideoSonucu(
                    aday, "PORT_KAPALI", "TCP uç noktası kapalı", {}, saat() - bas))
                continue
        ok, ayrinti = probe(aday.url)
        if ok is True:
            secildi = True
            durum, sebep = "CANLI", "gerçek video karesi çözüldü"
        elif ok is None:
            durum, sebep = "DOĞRULAMA_YOK", ayrinti.get("sebep", "doğrulayıcı yok")
        else:
            durum, sebep = "AKIŞ_YOK", ayrinti.get("sebep", "video karesi çözülemedi")
        sonuclar.append(VideoSonucu(
            aday, durum, sebep, dict(ayrinti), saat() - bas))
    return sonuclar


def sec(sonuclar: Iterable[VideoSonucu]) -> VideoSonucu | None:
    return next((sonuc for sonuc in sonuclar if sonuc.canli), None)


def hatirlanan_oku(yol: str | Path = DEFAULT_CACHE) -> str | None:
    try:
        veri = json.loads(Path(yol).read_text(encoding="utf-8"))
        kaynak = veri.get("url") if isinstance(veri, dict) else None
        return str(kaynak) if isinstance(kaynak, str) and kaynak.strip() else None
    except (OSError, ValueError, TypeError):
        return None


def hatirla(yol: str | Path, url: str, *, ayrinti: dict | None = None) -> None:
    hedef = Path(yol)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    veri = {"url": str(url), "kaydedildi": time.time(), "ayrinti": ayrinti or {}}
    gecici = hedef.with_suffix(hedef.suffix + ".tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    os.replace(gecici, hedef)


def kesfet(*, elle: str | None = None, onbellek: str | Path = DEFAULT_CACHE,
           hosts: Iterable[str] = DEFAULT_HOSTS,
           probe: Callable = akis_dogrula,
           tcp_probe: Callable = tcp_acik_mi) -> tuple[VideoSonucu | None, list[VideoSonucu]]:
    hatirlanan = hatirlanan_oku(onbellek)
    adaylar = adaylari_uret(elle, hatirlanan=hatirlanan, hosts=hosts)
    sonuclar = tara(adaylar, probe=probe, tcp_probe=tcp_probe)
    bulunan = sec(sonuclar)
    if bulunan is not None:
        hatirla(onbellek, bulunan.aday.url, ayrinti=bulunan.ayrinti)
    return bulunan, sonuclar

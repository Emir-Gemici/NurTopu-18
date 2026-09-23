"""YKS bilgisayarındaki kameradan güvenli, yerel canlı görüntü işleme.

Bu sınıf yalnız görüntü üretir. Rota, hakem ACK'i, telemetri veya araç komutu
göndermez; YKS'nin mevcut telsiz karar zincirine bilinçli olarak bağlanmaz.
OpenCV ve model modülleri tembel yüklenir, böylece YKS kamera sekmesi model
kurulu olmayan bilgisayarlarda da açılabilir.
"""

from __future__ import annotations

import os
import json
import math
import platform
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


YKI_MK15_YATAY_FOV_DERECE = 120.0
YKI_HEDEF_TAZELIK_S = 3.0
YKI_DUNYA_YARICAPI_M = 6378137.0


def kirmizi_h_tespit(cv2_mod: Any, image_bgr: Any) -> dict[str, Any] | None:
    """Kamera karesinde kırmızı H alanının güvenli görsel adayını bul."""
    if image_bgr is None or getattr(image_bgr, "ndim", 0) != 3:
        return None
    height, width = image_bgr.shape[:2]
    if height < 2 or width < 2:
        return None
    hsv = cv2_mod.cvtColor(image_bgr, cv2_mod.COLOR_BGR2HSV)
    alt = cv2_mod.inRange(hsv, (0, 80, 50), (12, 255, 255))
    ust = cv2_mod.inRange(hsv, (168, 80, 50), (179, 255, 255))
    mask = cv2_mod.bitwise_or(alt, ust)
    kernel = cv2_mod.getStructuringElement(cv2_mod.MORPH_ELLIPSE, (5, 5))
    mask = cv2_mod.morphologyEx(mask, cv2_mod.MORPH_OPEN, kernel)
    mask = cv2_mod.morphologyEx(mask, cv2_mod.MORPH_CLOSE, kernel)
    contours, _ = cv2_mod.findContours(mask, cv2_mod.RETR_EXTERNAL,
                                       cv2_mod.CHAIN_APPROX_SIMPLE)
    min_area = max(80.0, float(width * height) * 0.0008)
    adaylar = []
    for contour in contours:
        area = float(cv2_mod.contourArea(contour))
        if area < min_area:
            continue
        x, y, w, h = cv2_mod.boundingRect(contour)
        if w < 8 or h < 8:
            continue
        oran = w / float(h)
        if not 0.25 <= oran <= 4.0:
            continue
        adaylar.append((area, x, y, w, h))
    if not adaylar:
        return None
    area, x, y, w, h = max(adaylar, key=lambda aday: aday[0])
    guven = max(0.0, min(1.0, area / (width * height * 0.05)))
    return {
        "bbox": [int(x), int(y), int(w), int(h)],
        "pixel": [round(x + w / 2.0, 2), round(y + h / 2.0, 2)],
        "area_px": round(area, 1),
        "confidence": round(guven, 3),
        "source": "kirmizi_h_goruntu",
    }


def kirmizi_h_gps_konumu(hedef: dict[str, Any], telemetry: dict[str, Any],
                          frame_shape: tuple[int, ...],
                          yatay_fov_derece: float = YKI_MK15_YATAY_FOV_DERECE
                          ) -> dict[str, Any] | None:
    """Nadir kamera pikselini taze telemetriyle yaklaşık GPS konumuna çevir."""
    try:
        lat = float(telemetry["lat"])
        lon = float(telemetry["lon"])
        alt = float(telemetry["alt"])
        yaw = float(telemetry["yon"])
        px, py = (float(hedef["pixel"][0]), float(hedef["pixel"][1]))
        height, width = int(frame_shape[0]), int(frame_shape[1])
    except (KeyError, TypeError, ValueError, IndexError):
        return None
    if not all(math.isfinite(v) for v in (lat, lon, alt, yaw, px, py)):
        return None
    if alt <= 0.5 or width < 2 or height < 2 or not 0.0 < yatay_fov_derece < 179.0:
        return None
    yatay = 2.0 * alt * math.tan(math.radians(yatay_fov_derece) / 2.0)
    dikey = yatay * height / width
    sag = (px - width / 2.0) * yatay / width
    ileri = (height / 2.0 - py) * dikey / height
    yaw_rad = math.radians(yaw)
    kuzey = ileri * math.cos(yaw_rad) - sag * math.sin(yaw_rad)
    dogu = ileri * math.sin(yaw_rad) + sag * math.cos(yaw_rad)
    yeni_lat = lat + math.degrees(kuzey / YKI_DUNYA_YARICAPI_M)
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 1e-9:
        return None
    yeni_lon = lon + math.degrees(dogu / (YKI_DUNYA_YARICAPI_M * cos_lat))
    return {
        "lat": yeni_lat,
        "lon": (yeni_lon + 180.0) % 360.0 - 180.0,
        "ofset_kuzey_m": kuzey,
        "ofset_dogu_m": dogu,
        "alt_m": alt,
        "heading_deg": yaw % 360.0,
        "fov_deg": float(yatay_fov_derece),
    }


def _maskeli_gorunum(cv2_mod: Any, image_bgr: Any, masks: dict,
                     inference: Any, alpha: float = 0.24) -> Any:
    """Model maskesini ham görüntü ayrıntısını koruyarak üstüne bindirir.

    Ortak ``draw_masks`` fonksiyonu rapor/analiz çıktısı için yüzde 50 opaklıkta
    çalışır. YKS operatör panelinde aynı opaklık, geniş bir engel maskesinde
    tüm kamerayı kırmızıya boyayıp görüntü ayrıntısını gizler. Bu görünüm
    yalnızca görseldir; maske ve rota hesabı değişmez.
    """
    vis = image_bgr.copy()
    overlay = image_bgr.copy()
    renkler = getattr(inference, "CLASS_COLORS", {
        0: (0, 200, 0),
        1: (0, 0, 200),
    })
    maske_var = False
    for cls_id, mask in (masks or {}).items():
        if mask is None or not hasattr(mask, "any") or not bool(mask.any()):
            continue
        renk = renkler.get(cls_id, (128, 128, 128))
        overlay[mask > 0] = renk
        maske_var = True
    if not maske_var:
        return vis
    katsayi = max(0.0, min(1.0, float(alpha)))
    return cv2_mod.addWeighted(vis, 1.0 - katsayi, overlay, katsayi, 0.0)


class YkiCanliIsleme:
    """Yerel kamera karesini arka planda işler ve son kareyi sunar."""

    def __init__(self, source: str = "0", conf: float = 0.30,
                 mpp: float | None = None, model_path: str | None = None,
                 reconnect_delay: float = 1.0, log_path: str | Path | None = None,
                 mask_alpha: float = 0.24, telemetry_provider=None,
                 yatay_fov_derece: float = YKI_MK15_YATAY_FOV_DERECE,
                 kirmizi_h_etkin: bool = False):
        self.source = str(source).strip() or "0"
        self.conf = float(conf)
        self.mpp = mpp
        self.model_path = model_path
        self.reconnect_delay = max(0.2, float(reconnect_delay))
        self.mask_alpha = max(0.0, min(1.0, float(mask_alpha)))
        self.telemetry_provider = telemetry_provider
        self.yatay_fov_derece = float(yatay_fov_derece)
        self.kirmizi_h_etkin = bool(kirmizi_h_etkin)
        if log_path is None:
            kok = Path(__file__).resolve().parents[1]
            log_path = (kok / "results" / "yki_rtsp" /
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}.jsonl")
        self.log_path = str(Path(log_path))
        self._log_lock = threading.Lock()
        self._frame_count = 0
        self._log_frame_count = 0
        self._log_reconnect_count = 0
        self._last_interface_snapshot = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._frame = None
        self._raw_frame = None
        self._last_frame_at = None
        self._sequence = 0
        self._status = "KAPALI"
        self._error = None
        self._fps = 0.0
        self._route = None
        self._route_reason = None
        self._target = None
        self._last_target_signature = None
        self._mpp = None
        self._local_endpoint = None
        self._remote_endpoint = None
        self._model_ready = False

    @staticmethod
    def resolve_source(source: str | int) -> str | int:
        """Kamera indeksini tam sayıya, diğer kaynakları metne çevir."""
        if isinstance(source, int):
            return source
        text = str(source).strip()
        try:
            return int(text)
        except (TypeError, ValueError):
            return text

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        with self._lock:
            self._status = "BAŞLATILIYOR"
            self._error = None
            self._route = None
            self._route_reason = None
            self._target = None
            self._last_target_signature = None
            self._mpp = None
        self._thread = threading.Thread(target=self._run,
                                        name="yki-canli-isleme", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=max(0.0, float(timeout)))
        with self._lock:
            self._status = "DURDURULDU"

    def snapshot(self) -> dict[str, Any]:
        """Tk ana döngüsünün okuyabileceği kopyalanmış durum."""
        with self._lock:
            frame = None if self._frame is None else self._frame.copy()
            raw_frame = None if self._raw_frame is None else self._raw_frame.copy()
            return {
                "frame": frame,
                "raw_frame": raw_frame,
                "frame_age_s": (None if self._last_frame_at is None else
                                 max(0.0, time.monotonic() - self._last_frame_at)),
                "frame_ts_monotonic": self._last_frame_at,
                "sequence": self._sequence,
                "status": self._status,
                "error": self._error,
                "fps": self._fps,
                "route": self._route,
                "route_reason": self._route_reason,
                "target": (None if self._target is None else dict(self._target)),
                "mpp": self._mpp,
                "local_endpoint": self._local_endpoint,
                "remote_endpoint": self._remote_endpoint,
                "model_ready": self._model_ready,
                "source": self.source,
                "log_path": self.log_path,
                "running": self.running,
            }

    def _set(self, **values: Any) -> None:
        with self._lock:
            for key, value in values.items():
                setattr(self, f"_{key}", value)

    @staticmethod
    def _arayuz_kunyesi() -> dict[str, Any]:
        """İsteğe bağlı psutil ile yerel IPv4 arayüzlerini kanıta ekle."""
        sonuc: dict[str, Any] = {"hostname": socket.gethostname()}
        try:
            import psutil
            arayuzler = {}
            for ad, adresler in psutil.net_if_addrs().items():
                ipv4 = [a.address for a in adresler
                        if a.family == socket.AF_INET]
                if ipv4:
                    arayuzler[str(ad)] = ipv4
            sonuc["ipv4"] = arayuzler
        except Exception as exc:
            sonuc["ipv4_error"] = f"{type(exc).__name__}: {exc}"
        return sonuc

    def _log(self, event: str, **fields: Any) -> None:
        """Her olayÄ± tek satÄ±r JSONL olarak diske dayanÄ±klÄ± yaz."""
        kayit = {
            "ts_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "monotonic_s": round(time.monotonic(), 3),
            "event": event,
            "pid": os.getpid(),
            "source": self.source,
        }
        kayit.update(fields)
        try:
            yol = Path(self.log_path)
            yol.parent.mkdir(parents=True, exist_ok=True)
            with self._log_lock:
                with yol.open("a", encoding="utf-8") as dosya:
                    dosya.write(json.dumps(kayit, ensure_ascii=False,
                                           separators=(",", ":")) + "\n")
                    dosya.flush()
        except Exception:
            # Kamera/telemetri zinciri log diski yavaÅŸladÄ±ÄŸÄ± iÃ§in durdurulmaz.
            pass

    def _sinyal_yok(self) -> None:
        """Kopuk akışta eski kareyi canlı gibi göstermeyi engelle."""
        with self._lock:
            self._frame = None
            self._raw_frame = None
            self._last_frame_at = None
            self._fps = 0.0
            self._route = None
            self._route_reason = None
            self._target = None
            self._last_target_signature = None
            self._mpp = None
            self._local_endpoint = None
            self._remote_endpoint = None
            self._sequence += 1

    def _telemetri(self) -> dict[str, Any]:
        saglayici = self.telemetry_provider
        if not callable(saglayici):
            return {}
        try:
            veri = saglayici() or {}
        except Exception as exc:
            self._log("telemetry_read_error", error_type=type(exc).__name__,
                      error=str(exc))
            return {}
        return dict(veri) if isinstance(veri, dict) else {}

    def _dinamik_mpp(self, width_px: int, telemetry: dict[str, Any]) -> float | None:
        try:
            alt = float(telemetry.get("alt"))
            if not math.isfinite(alt) or alt <= 0.5:
                return None
            if not 0.0 < self.yatay_fov_derece < 179.0 or width_px <= 0:
                return None
            return (2.0 * alt * math.tan(math.radians(self.yatay_fov_derece) / 2.0)
                    / float(width_px))
        except (TypeError, ValueError):
            return None

    def _run(self) -> None:
        cap = None
        try:
            import cv2

            kaynak = self.resolve_source(self.source)
            scheme = (urlparse(kaynak).scheme.lower()
                      if isinstance(kaynak, str) and "://" in kaynak else "")
            network_stream = scheme in {"rtsp", "rtsps", "udp", "srt", "http", "https"}
            rtsp = scheme in {"rtsp", "rtsps"}
            adres = urlparse(kaynak) if network_stream else None
            self._log(
                "session_start",
                source_kind=(scheme or "camera"),
                rtsp_host=(adres.hostname if adres is not None else None),
                rtsp_port=(adres.port or 554 if adres is not None else None),
                platform=platform.platform(),
                python=platform.python_version(),
                opencv=getattr(cv2, "__version__", None),
                interface_snapshot=self._arayuz_kunyesi(),
            )
            self._last_interface_snapshot = self._arayuz_kunyesi()

            # Model yükleme başarısız olsa bile ham canlı görüntü gösterilir;
            # bu, kamera bağlantısını model eksikliğiyle karıştırmayı önler.
            inference = None
            model = None
            model_error = None
            model_started = time.perf_counter()
            try:
                import rpi_inference as inference
                model = inference.load_model(self.model_path)
            except Exception as exc:  # fail-closed: görsel var, karar yok
                model_error = f"model yüklenemedi: {type(exc).__name__}: {exc}"
            self._log(
                "model_load",
                ok=model is not None,
                elapsed_ms=round((time.perf_counter() - model_started) * 1000.0, 1),
                error=model_error,
            )
            self._set(model_ready=model is not None,
                      error=model_error,
                      status=("MODEL HAZIR · VİDEO BEKLENİYOR" if model is not None
                              else "MODEL YOK · VİDEO BEKLENİYOR"))

            def ac() -> Any:
                """Akışı aç; ağ gelene kadar güvenli biçimde bekle."""
                if rtsp or scheme in {"http", "https"}:
                    probe_started = time.perf_counter()
                    interface_snapshot = self._arayuz_kunyesi()
                    interface_changed = (self._last_interface_snapshot is not None and
                                         interface_snapshot != self._last_interface_snapshot)
                    self._last_interface_snapshot = interface_snapshot
                    try:
                        port = adres.port or 554
                        with socket.create_connection((adres.hostname, port), timeout=2.0) as soket:
                            yerel = soket.getsockname()
                            uzak = soket.getpeername()
                        self._set(local_endpoint=f"{yerel[0]}:{yerel[1]}",
                                  remote_endpoint=f"{uzak[0]}:{uzak[1]}")
                        self._log(
                            "rtsp_probe",
                            ok=True,
                            elapsed_ms=round((time.perf_counter() - probe_started) * 1000.0, 1),
                            local_endpoint=f"{yerel[0]}:{yerel[1]}",
                            remote_endpoint=f"{uzak[0]}:{uzak[1]}",
                            interface_changed=interface_changed,
                            interface_snapshot=interface_snapshot,
                        )
                    except (OSError, ValueError, TypeError) as exc:
                        self._log_reconnect_count += 1
                        self._log(
                            "rtsp_probe",
                            ok=False,
                            elapsed_ms=round((time.perf_counter() - probe_started) * 1000.0, 1),
                            error_type=type(exc).__name__,
                            error=str(exc),
                            reconnect_attempt=self._log_reconnect_count,
                            interface_changed=interface_changed,
                            interface_snapshot=interface_snapshot,
                        )
                        self._sinyal_yok()
                        self._set(
                            status="RTSP AĞI BEKLENİYOR",
                            error=(f"{adres.hostname}:{adres.port or 554} erişilemiyor: {exc}; "
                                   f"{self.reconnect_delay:.1f} s sonra yeniden denenecek"))
                        return None
                    if rtsp:
                        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                            "rtsp_transport;tcp|stimeout;1000000|rw_timeout;1000000|"
                            "fflags;nobuffer|flags;low_delay|max_delay;500000")
                    elif scheme == "udp":
                        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                            "fifo_size;1000000|overrun_nonfatal;1|"
                            "fflags;nobuffer|flags;low_delay|max_delay;500000")

                if network_stream:
                    # set() after open does not reliably constrain FFmpeg read().
                    # OpenCV 5 supports these parameters during construction.
                    params = []
                    for ad in ("CAP_PROP_OPEN_TIMEOUT_MSEC",
                               "CAP_PROP_READ_TIMEOUT_MSEC"):
                        ozellik = getattr(cv2, ad, None)
                        if ozellik is not None:
                            params.extend((ozellik, 1000))
                    try:
                        aday = cv2.VideoCapture(kaynak, cv2.CAP_FFMPEG, params)
                    except (TypeError, AttributeError, cv2.error):
                        aday = cv2.VideoCapture(kaynak, cv2.CAP_FFMPEG)
                else:
                    aday = cv2.VideoCapture(kaynak)
                if not aday.isOpened():
                    self._log(
                        "capture_open",
                        ok=False,
                        backend="ffmpeg_network" if network_stream else "opencv_default",
                        error="VideoCapture.isOpened() false",
                    )
                    try:
                        aday.release()
                    except Exception:
                        pass
                    self._sinyal_yok()
                    self._set(
                        status="KAMERA AÇILIŞI BEKLENİYOR",
                        error=(f"kaynak={self.source!r} açılamadı; "
                               f"{self.reconnect_delay:.1f} s sonra yeniden denenecek"))
                    return None
                # FFmpeg tamponu birikirse RTSP gecikmesi büyür.
                try:
                    aday.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass
                for ad in ("CAP_PROP_OPEN_TIMEOUT_MSEC", "CAP_PROP_READ_TIMEOUT_MSEC"):
                    ozellik = getattr(cv2, ad, None)
                    if ozellik is not None:
                        try:
                            aday.set(ozellik, 1000)
                        except Exception:
                            pass
                self._set(
                    status=("KAMERA CANLI · MODEL HAZIR" if model is not None
                            else "KAMERA CANLI · MODEL YOK"),
                    error=model_error)
                self._log(
                    "capture_open",
                    ok=True,
                    backend="ffmpeg_network" if network_stream else "opencv_default",
                    width=int(aday.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
                    height=int(aday.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
                    reconnect_attempt=self._log_reconnect_count,
                )
                return aday

            son_kare = time.perf_counter()
            fps_ort = []
            while not self._stop.is_set():
                if cap is None:
                    cap = ac()
                    if cap is None:
                        self._stop.wait(self.reconnect_delay)
                        continue
                ok, frame = cap.read()
                if not ok or frame is None:
                    self._log(
                        "frame_read_error",
                        error="VideoCapture.read() başarısız",
                        reconnect_attempt=self._log_reconnect_count + 1,
                        interface_snapshot=self._arayuz_kunyesi() if network_stream else None,
                    )
                    self._sinyal_yok()
                    self._set(status="VİDEO YENİDEN BAĞLANIYOR" if network_stream
                              else "KAMERA YENİDEN BAĞLANIYOR",
                              error="VideoCapture.read() başarısız")
                    try:
                        cap.release()
                    except Exception:
                        pass
                    cap = None
                    self._stop.wait(self.reconnect_delay)
                    continue
                self._frame_count += 1

                vis = frame
                route = None
                reason = None
                content = None
                telemetry = self._telemetri()
                target = None
                if self.kirmizi_h_etkin:
                    target = kirmizi_h_tespit(cv2, frame)
                    if target is not None:
                        geo = kirmizi_h_gps_konumu(
                            target, telemetry, frame.shape, self.yatay_fov_derece)
                        if geo is not None:
                            target.update(geo)
                        x, y, w, h = target["bbox"]
                        cv2.rectangle(vis, (x, y), (x + w, y + h),
                                      (0, 255, 255), 2)
                        cv2.putText(
                            vis, "KIRMIZI H" +
                            (" · GPS" if geo is not None else " · KOORDINAT BEKLENIYOR"),
                            (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (0, 255, 255), 2)
                        imza = (
                            tuple(target.get("bbox") or ()),
                            round(float(target.get("lat")), 7)
                            if target.get("lat") is not None else None,
                            round(float(target.get("lon")), 7)
                            if target.get("lon") is not None else None,
                        )
                        if imza != self._last_target_signature:
                            self._last_target_signature = imza
                            self._log("target_detected", target=dict(target),
                                      frame_no=self._frame_count)
                if model is not None and inference is not None:
                    try:
                        square, small, content = inference._preprocess(frame)
                        started = time.perf_counter()
                        results = model.predict(
                            small, imgsz=inference.INFER_SIZE,
                            conf=self.conf, verbose=False)
                        elapsed = time.perf_counter() - started
                        self._log_frame_count += 1
                        fps_ort.append(elapsed)
                        if len(fps_ort) > 30:
                            fps_ort.pop(0)
                        masks = inference.get_masks(results, *square.shape[:2])
                        masks = inference._maskeleri_icerige_kirp(masks, content)
                        if (self._log_frame_count % 10 == 0 or
                                elapsed >= 1.0):
                            self._log(
                                "inference",
                                frame_no=self._log_frame_count,
                                elapsed_ms=round(elapsed * 1000.0, 1),
                                frame_width=int(frame.shape[1]),
                                frame_height=int(frame.shape[0]),
                                mask_pixels={str(k): int(v.sum())
                                             for k, v in masks.items()},
                            )
                        vis = _maskeli_gorunum(
                            cv2, square, masks, inference, self.mask_alpha)
                        kare_mpp = self.mpp
                        if kare_mpp is None:
                            kare_mpp = self._dinamik_mpp(content[2], telemetry)
                        if kare_mpp is None:
                            reason = "ÖLÇEK YOK · yerel rota gösterilmedi"
                        else:
                            route, confidence, waypoints, reason = (
                                inference.analyze_path(
                                    masks.get(0), icerik=content,
                                    engel_mask=masks.get(1), mpp=kare_mpp,
                                    return_reason=True, goruntu=square))
                            if route:
                                draw = getattr(inference, "_draw_waypoints", None)
                                if draw is not None:
                                    vis = draw(vis, waypoints)
                                route = {
                                    "yol": int(route),
                                    "guven": float(confidence),
                                    "waypoint": len(waypoints),
                                    "waypoints": [[int(nokta[0]), int(nokta[1])]
                                                  for nokta in waypoints],
                                    "mpp": float(kare_mpp),
                                }
                            else:
                                route = None
                    except Exception as exc:
                        reason = f"çıkarım hatası: {type(exc).__name__}: {exc}"
                        self._set(error=reason)

                now = time.perf_counter()
                instantaneous = 1.0 / max(now - son_kare, 1e-6)
                son_kare = now
                live_fps = (1.0 / (sum(fps_ort) / len(fps_ort))
                            if fps_ort else instantaneous)
                if content is not None:
                    x0, y0, icerik_w, icerik_h = content
                    x1 = min(vis.shape[1], x0 + icerik_w)
                    y1 = min(vis.shape[0], y0 + icerik_h)
                    if x1 > x0 and y1 > y0:
                        vis = vis[y0:y1, x0:x1].copy()
                if target is not None:
                    # Target pixel coordinates are measured on the original
                    # camera frame; after letterbox crop the visible canvas is
                    # exactly that original content rectangle.
                    tx, ty, tw, th = target["bbox"]
                    if (0 <= tx < vis.shape[1] and 0 <= ty < vis.shape[0]):
                        cv2.rectangle(vis, (tx, ty),
                                      (min(vis.shape[1] - 1, tx + tw),
                                       min(vis.shape[0] - 1, ty + th)),
                                      (0, 255, 255), 2)
                        cv2.putText(
                            vis, "KIRMIZI H" +
                            (" · GPS" if target.get("lat") is not None
                             else " · KOORDINAT BEKLENIYOR"),
                            (tx, max(20, ty - 8)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (0, 255, 255), 2)
                cv2.putText(vis, "YKS YEREL CANLI İŞLEME",
                            (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.70,
                            (255, 255, 255), 2)
                cv2.putText(vis, f"FPS: {live_fps:.1f}",
                            (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (0, 255, 255), 2)
                if route:
                    label = (f"YEREL GÖSTERİM · YOL {route['yol']} · "
                             f"GÜVEN {route['guven']:.2f}")
                    colour = (0, 255, 0)
                elif reason:
                    label = str(reason)
                    colour = (0, 190, 255)
                else:
                    label = "ROTA ÜRETİLMEDİ"
                    colour = (0, 190, 255)
                cv2.putText(vis, label[:110], (10, 82),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.48, colour, 1)
                with self._lock:
                    self._frame = vis.copy()
                    self._raw_frame = frame.copy()
                    self._last_frame_at = time.monotonic()
                    self._sequence += 1
                    self._fps = float(live_fps)
                    self._route = route
                    self._route_reason = reason
                    self._target = target
                    self._mpp = (self.mpp if self.mpp is not None else
                                 self._dinamik_mpp(
                                     content[2] if content is not None else frame.shape[1],
                                     telemetry))
                if model is None and self._frame_count % 30 == 0:
                    self._log(
                        "frame_received",
                        frame_no=self._frame_count,
                        frame_width=int(frame.shape[1]),
                        frame_height=int(frame.shape[0]),
                    )
        except Exception as exc:
            self._sinyal_yok()
            self._log("worker_exception", error_type=type(exc).__name__,
                      error=str(exc))
            self._set(status="CANLI İŞLEME HATASI",
                      error=f"{type(exc).__name__}: {exc}")
        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            self._log(
                "session_end",
                status=("DURDURULDU" if self._stop.is_set()
                        else "CANLI İŞLEME SONLANDI"),
                frames=self._frame_count,
                reconnect_attempts=self._log_reconnect_count,
            )
            self._set(status=("DURDURULDU" if self._stop.is_set()
                              else "CANLI İŞLEME SONLANDI"))

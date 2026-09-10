#!/usr/bin/env python3
"""NEDEN: İKA, yalnız doğrulanmış dinamik rota ile güvenlik sinyalleri birlikte
izin verdiğinde hareket etmeli; haberleşme kaybında güvenli duruşa geçmelidir.

Navitas — İKA Otonom Navigasyon
Waypoint'ler arasında gezinir, DiffDrivePlugin'i gz topic ile kullanır.

Kullanım:
  python3 scripts/ika_nav.py [comms] [--bind 0.0.0.0:5006] \
      [--bekleme-suresi 900] [--surus-suresi 600]

İki AYRI son tarih vardır (K5, şartname §6.2):
  bekleme  — rota + IHA_LANDED + IKA_GO gelene kadar (İHA görev süresi, 15 dk)
  sürüş    — izin geldiği andan HB'ye kadar (İKA görev süresi, 10 dk)
"""

import functools
import math
import time
import sys
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# comms (dinamik A* rotasını İHA'dan al)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comms"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "codes"))
from protocol import ROAD_LABEL, MESAJ_NO_ROUTE
from karar_sozlesmesi import (IKA_AZAMI_HIZ_MS, IKA_BEKLEME_SURESI_S,
                              IKA_SURUS_SURESI_S)

# ── Kontrol parametreleri ─────────────────────────────────────────────────────
# T213 (D-438 f): 2,0 m/s DDR fiziksel tavanının (1,3 m/s) üstündeydi ve üç
# kopya hâlinde geziyordu. Tek kaynak CONTRACTS §4 → karar_sozlesmesi.
MAX_SPEED   = IKA_AZAMI_HIZ_MS   # m/s — DDR 200 rpm × π × Ø0,125 / 60
TURN_GAIN   = 1.8   # dönüş orantı katsayısı (T213 MuJoCo ölçümü: 1,3 m/s tabanda
                    # 45 GT koşumu ile ölçüldü; değer değiştirilmedi, README_T213B)
WP_RADIUS   = 0.5   # m — costmap takip payını aşmadan sonraki waypoint'e geç
FINAL_WP_RADIUS = 0.3  # m — HB son yaklaşım toleransı
CTRL_HZ     = 10    # Hz
MAX_WAYPOINTS = 64
MAX_SEGMENT_M = 2.10   # costmap WP_ARALIK_M (2.0) + seri yuvarlama payı
MAX_LOCAL_EXTENT_M = 60.0
SOURCE_TOLERANCE_M = 0.15


# ── Sürücü katmanı (P3/T149 · D-390) ────────────────────────────────────────
# Motor/konum artık `ika_surucu` soyutlamasından geçer. Modül fonksiyonlarının
# imzaları KORUNDU: mevcut testler `mock.patch.object(ika_nav, "send_vel", …)`
# ile yamalamaya devam eder; üretimde delege aktif sürücüdür.
import ika_surucu  # noqa: E402

_SURUCU = None


def surucu():
    """Aktif sürücü; hiç ayarlanmadıysa Gazebo (bugünkü davranış)."""
    global _SURUCU
    if _SURUCU is None:
        _SURUCU = ika_surucu.GazeboSurucu()
    return _SURUCU


def surucu_ayarla(yeni):
    """Sürücüyü değiştir (Sahte/Gercek); None eski varsayılana döndürür."""
    global _SURUCU
    _SURUCU = yeni


def surucu_saglikli():
    """Sürücü yanıt veriyor mu (hiç kullanılmadıysa sağlıklı sayılır)."""
    return _SURUCU is None or _SURUCU.saglikli()


def get_pose(model="ika"):
    """
    Konumu aktif sürücüden al (Gazebo'da: gz model -m ika -p ayrıştırması).
    Döner: (x, y, z, yaw) veya (None, None, None, None)
    """
    return surucu().konum_al()


def send_vel(right_spd, left_spd, topic="~/ika/vel_cmd"):
    """
    Tekerlek hızlarını aktif sürücüye ilet (Gazebo'da DiffDrivePlugin,
    bayt-eş komut). Dönüş: iletilebildi mi (D-390: istisna sızmaz).
    `topic` geriye dönük imza içindir; kaynağı sürücü yapılandırması belirler.
    """
    return surucu().hiz_ver(right_spd, left_spd)


def wrap(a):
    while a >  math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


def steer(heading_err, base=MAX_SPEED):
    """
    Heading hatası → (sağ_tekerlek, sol_tekerlek).
    err > 0 → sola dön: sağ tekerlek hızlı
    err < 0 → sağa dön: sol tekerlek hızlı
    """
    delta = TURN_GAIN * heading_err
    delta = max(-base, min(base, delta))
    r = max(-base, min(base, base + delta))
    l = max(-base, min(base, base - delta))
    return r, l


def _as_xy(value, field):
    """Bir JSON koordinatını sonlu ``(x, y)`` float çiftine dönüştür."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{field} [x, y] biçiminde olmalı")
    try:
        x, y = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} sayısal olmalı") from exc
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError(f"{field} sonlu sayılar içermeli")
    return x, y


def _road_label(road):
    """Yol kimliği varsa gösterge etiketi; koordinat rotasında genel etiket."""
    if isinstance(road, int):
        return ROAD_LABEL.get(road, "dinamik rota")
    return "dinamik rota"


def _waypointleri_dogrula(world_waypoints):
    """Aktarim sozlesmesinin fiziksel sinirlarini denetle."""
    if not 2 <= len(world_waypoints) <= MAX_WAYPOINTS:
        raise ValueError(f"Dinamik rota 2..{MAX_WAYPOINTS} waypoint icermeli")
    for i, (onceki, simdiki) in enumerate(zip(world_waypoints, world_waypoints[1:]), 1):
        mesafe = math.dist(onceki, simdiki)
        if mesafe > MAX_SEGMENT_M:
            raise ValueError(
                f"waypoint[{i - 1}]→waypoint[{i}] {mesafe:.2f} m; "
                f"azami {MAX_SEGMENT_M:.2f} m"
            )
    return world_waypoints


def route_to_world_waypoints(route):
    """Dinamik OPEN_ROUTE verisini Gazebo dünya waypoint'lerine dönüştür.

    ``protocol.open_route`` sözleşmesine göre ``waypoints`` listesi
    ``ref_xy`` referansına göre yereldir. İlk yerel nokta, costmap'in
    doğruladığı fiziksel başlangıç ankuru olan ``[0, 0]`` olmalıdır;
    İKA doğrulanmamış bir referans→rota segmenti EKLEMEZ.
    Bir rota bir koordinat dizisi olarak doğrudan da verilebilir; bu durumda
    noktaların zaten dünya koordinatında olması beklenir.

    Sayısal ``road`` yalnızca yol etiketi/kararıdır; geometrik rota değildir.
    Bu nedenle waypoint olmadan İKA'nın hareket etmesine izin verilmez.
    """
    protokol_rotasi = isinstance(route, dict) and (
        "waypoints" in route or "rota_yerel" in route
    )
    if isinstance(route, dict):
        raw_waypoints = route.get("waypoints")
        ref_xy = route.get("ref_xy")
        if raw_waypoints is None and "rota_yerel" in route:
            # iha_haritala'nin dosya formati; comms.iha_sender bunu OPEN_ROUTE
            # alanlarina cevirir, ancak dogrudan kullanimda da ayni geometriyi
            # kayipsiz kabul ediyoruz.
            raw_waypoints = route.get("rota_yerel")
            ref_xy = route.get("referans_xy")
        if not raw_waypoints and isinstance(route.get("road"), (list, tuple)):
            # Eski koordinatli road formati yalniz acik koordinat dizisi olarak
            # kabul edilir; sayisal road tek basina geometri degildir.
            raw_waypoints = route["road"]
    else:
        raw_waypoints, ref_xy = route, None

    if not isinstance(raw_waypoints, (list, tuple)) or not raw_waypoints:
        raise ValueError("Dinamik rota waypoint dizisi içermeli")
    if len(raw_waypoints) > MAX_WAYPOINTS:
        raise ValueError(f"Dinamik rota en fazla {MAX_WAYPOINTS} waypoint içerebilir")

    local_or_world = [
        _as_xy(point, f"waypoints[{index}]")
        for index, point in enumerate(raw_waypoints)
    ]

    if ref_xy is None:
        if protokol_rotasi:
            raise ValueError("OPEN_ROUTE için ref_xy zorunlu")
        world_waypoints = local_or_world
    else:
        ref_x, ref_y = _as_xy(ref_xy, "ref_xy")
        if math.hypot(*local_or_world[0]) > SOURCE_TOLERANCE_M:
            raise ValueError(
                "İlk yerel waypoint costmap başlangıç ankuru [0, 0] olmalı"
            )
        if any(math.hypot(x, y) > MAX_LOCAL_EXTENT_M for x, y in local_or_world):
            raise ValueError(f"Yerel waypoint HTAB sınırını ({MAX_LOCAL_EXTENT_M:g} m) aşıyor")
        world_waypoints = [(ref_x + x, ref_y + y) for x, y in local_or_world]

    return _waypointleri_dogrula(world_waypoints)


def receiver_rota_gecerli(receiver):
    """Alıcının en güncel kararının sürüşe uygun olduğunu tutarlı doğrula.

    ``last_no_route`` doğrudan okunmaz: OPEN_ROUTE/NO_ROUTE çifti alıcı
    thread'inde kilit altında güncellendiği için aynı karar nesline ait tek bir
    snapshot kullanılır. Geçersiz geometrili bir OPEN_ROUTE da güvenli duruşu
    yanlışlıkla açamaz.
    """
    if (not getattr(receiver, "ika_go", False)
            or not getattr(receiver, "iha_landed", False)):
        return False
    route, no_route, generation, _ = receiver.decision_snapshot()
    if route is None or no_route is not None:
        return False
    try:
        route_to_world_waypoints(route)
    except (TypeError, ValueError):
        return False

    # Geometri doğrulanırken yeni bir karar geldiyse sonucu eski snapshot'tan
    # üretme; bir sonraki kontrol turunda yeni karar baştan değerlendirilsin.
    current_route, current_no_route, current_generation, _ = (
        receiver.decision_snapshot()
    )
    return (
        current_no_route is None
        and current_generation == generation
        and current_route is route
    )


def receiver_korumali_hiz_gonder(receiver, right, left):
    """Karar kontrolü ile sıfır-olmayan motor komutunu atomik sırala."""
    def geometri_gecerli(route):
        try:
            route_to_world_waypoints(route)
        except (TypeError, ValueError):
            return False
        return True

    return receiver.run_if_route_valid(
        lambda: send_vel(right, left),
        validator=geometri_gecerli,
    )


def receiver_ika_go_bekle(receiver, timeout=None):
    """YKS manuel intikal izni gelene kadar İKA'yı sıfır hızda tut."""
    send_vel(0, 0)
    print("[ika_nav] YKS manuel IKA_GO komutu bekleniyor — İKA güvenli duruşta")
    if receiver.wait_ika_go(timeout):
        print("[ika_nav] ✓ YKS IKA_GO alındı — İKA sürüş izni açık")
        return True
    print("[ika_nav] ✗ YKS IKA_GO gelmedi (timeout) — İKA hareket etmez")
    return False


def receiver_surus_izni_bekle(
        receiver, timeout=None, deadline_monotonic=None, *,
        saat=None, bekle=None):
    """İki izni tek sürede ve ortak mutlak son tarih içinde bekle.

    ``saat``/``bekle`` (T213, ON_KAYIT §5.3 sim saati): verilmezse davranış
    BAYT-EŞ eskisidir (alıcının Event.wait'i, duvar saati). ``bekle`` verilirse
    bekleme ``bekle(dt)`` ile adım adım yapılır — simülasyonda ``bekle`` fizik
    saatini ilerletir; alıcı da AYNI saatle kurulmuş olmalıdır
    (``IkaReceiver(saat=...)``), yoksa deadline karşılaştırması anlamsızdır.
    """
    send_vel(0, 0)
    print("[ika_nav] YKS IKA_GO + İHA iniş kanıtı bekleniyor — "
          "İKA güvenli duruşta")
    if bekle is None:
        izin = receiver.wait_surus_izni(
            timeout, deadline_monotonic=deadline_monotonic)
    else:
        _saat = time.monotonic if saat is None else saat
        if deadline_monotonic is None:
            deadline = _saat() + max(0.0, float(timeout or 0.0))
        else:
            deadline = float(deadline_monotonic)
        izin = False
        while True:
            # timeout=0: Event yalnız YOKLANIR, gerçek zaman beklenmez.
            if receiver.wait_surus_izni(0.0, deadline_monotonic=deadline):
                izin = True
                break
            kalan = deadline - _saat()
            if kalan <= 0.0:
                break
            bekle(min(1.0 / CTRL_HZ, kalan))
    if izin:
        print("[ika_nav] ✓ IKA_GO ve IHA_LANDED alındı — İKA sürüş izni açık")
        return True
    eksik = []
    if not getattr(receiver, "ika_go", False):
        eksik.append("IKA_GO")
    if not getattr(receiver, "iha_landed", False):
        eksik.append("IHA_LANDED")
    print(f"[ika_nav] ✗ {' + '.join(eksik) or 'sürüş izni'} gelmedi "
          "(timeout) — İKA hareket etmez")
    return False


def navigate(
        wps, label="rota", verbose=True, link_ok=None, rota_gecerli=None,
        rota_korumali_gonder=None, surus_deadline_monotonic=None,
        saat=time.monotonic, bekle=None):
    """Waypoint'leri izle. ``surus_deadline_monotonic`` (K5) dolarsa
    İKA durur ve False döner: şartname §6.2 İKA görev süresi aşıldı.

    ``saat``/``bekle`` (T213, ON_KAYIT §5.3): 10 Hz döngü ve deadline bu saatle
    işler. ``bekle`` None ise ``time.sleep`` (çağrı anında çözülür; testlerin
    ``mock.patch.object(ika_nav.time, "sleep", …)`` yaması çalışmaya devam
    eder). Simülasyonda ``bekle(dt)`` fizik adımlarını koşturur ve ``saat``
    ``data.time`` okur — sürüş süresi SANAL saniyeyle ölçülür.
    """
    if len(wps) < 2:
        raise ValueError("Navigate için en az iki waypoint gerekli")
    dt = 1.0 / CTRL_HZ
    _bekle = time.sleep if bekle is None else bekle
    surus_deadline = (None if surus_deadline_monotonic is None
                      else float(surus_deadline_monotonic))

    # Heading'i konum geçmişinden tahmin edeceğiz
    prev_x = prev_y = None
    current_yaw = math.atan2(
        wps[1][1] - wps[0][1],
        wps[1][0] - wps[0][0]
    )  # başlangıç tahmini: ilk hedefe doğru

    print(f"\n[ika_nav] {label} | {len(wps)-1} segment")
    print(f"[ika_nav] Başlangıç: {wps[0]} → Hedef: {wps[-1]}")
    baglanti_kayip_yazildi = False
    rota_gecersiz_yazildi = False

    def rota_gecersiz_dur():
        """Motoru sıfırla ve güvenli duruşu bir kez görünür kıl."""
        nonlocal rota_gecersiz_yazildi
        send_vel(0, 0)
        if not rota_gecersiz_yazildi:
            print("[ika_nav] ⚠ Rota geçersiz/NO_ROUTE — GÜVENLİ DURMA")
            rota_gecersiz_yazildi = True

    def rota_kapisi_acik():
        """Rota karar kapısını denetle; kapalıysa motoru hemen sıfırla."""
        nonlocal rota_gecersiz_yazildi
        if rota_gecerli is None or rota_gecerli():
            if rota_gecersiz_yazildi:
                print(
                    "[ika_nav] ✓ Geçerli OPEN_ROUTE geldi — "
                    "aynı waypoint'ten devam"
                )
                rota_gecersiz_yazildi = False
            return True

        rota_gecersiz_dur()
        return False

    for idx, (wx, wy) in enumerate(wps[1:], 1):
        print(f"\n[ika_nav] ── Waypoint {idx}/{len(wps)-1}: ({wx:.1f}, {wy:.1f})")

        at_wp = False
        while not at_wp:
            if surus_deadline is not None and saat() >= surus_deadline:
                send_vel(0, 0)
                print("[ika_nav] ✗ İKA sürüş süresi doldu (şartname §6.2) — "
                      "GÜVENLİ DURMA, HB'ye ulaşılamadı")
                return False
            if not surucu_saglikli():
                # D-390 (T3): donanım sustu — son bir durdurma dene ve bırak.
                # Eski davranış subprocess istisnasıyla ÇÖKMEKTİ; şimdi görev
                # seviyesinde fail-closed: İKA durur, navigate False döner.
                send_vel(0, 0)
                print(f"[ika_nav] ✗ SÜRÜCÜ YANITSIZ (ardışık "
                      f"{ika_surucu.ARDISIK_HATA_TAVANI} hata) — "
                      "GÜVENLİ DURMA")
                return False
            if link_ok is not None and not link_ok():
                send_vel(0, 0)
                if not baglanti_kayip_yazildi:
                    print("[ika_nav] ⚠ İHA bağlantısı kayıp — GÜVENLİ DURMA")
                    baglanti_kayip_yazildi = True
                _bekle(1.0 / CTRL_HZ)
                continue
            if baglanti_kayip_yazildi:
                print("[ika_nav] ✓ İHA bağlantısı geri geldi — aynı waypoint'ten devam")
                baglanti_kayip_yazildi = False
            if not rota_kapisi_acik():
                _bekle(dt)
                continue

            cx, cy, cz, gz_yaw = get_pose("ika")

            if cx is None:
                print("[ika_nav]   Konum alınamadı, bekleniyor...")
                _bekle(0.5)
                continue

            # Yaw güncelleme: hareket vektöründen
            if prev_x is not None:
                ddx, ddy = cx - prev_x, cy - prev_y
                moved = math.hypot(ddx, ddy)
                if moved > 0.03:                # gürültüden kaçın
                    current_yaw = math.atan2(ddy, ddx)
            prev_x, prev_y = cx, cy

            dx, dy = wx - cx, wy - cy
            dist   = math.hypot(dx, dy)

            hedef_yaricapi = FINAL_WP_RADIUS if idx == len(wps) - 1 else WP_RADIUS
            if dist < hedef_yaricapi:
                send_vel(0, 0)
                print(f"[ika_nav]   ✓ Ulaşıldı (kalan: {dist:.2f}m)")
                at_wp = True
                _bekle(0.3)
                continue

            desired = math.atan2(dy, dx)
            err     = wrap(desired - current_yaw)

            r, l = steer(err)
            # Pose/steer hesabı sırasında NO_ROUTE gelmiş olabilir. Sıfır
            # olmayan tek motor çıkışından hemen önce kapıyı yeniden denetle.
            if not rota_kapisi_acik():
                _bekle(dt)
                continue
            if rota_korumali_gonder is None:
                send_vel(r, l)
            elif not rota_korumali_gonder(r, l):
                # Son bool kontrolünden hemen sonra NO_ROUTE işlenmiş olabilir.
                # Üretim callback'i karar kilidi altında nonzero komutu reddeder.
                rota_gecersiz_dur()
                _bekle(dt)
                continue

            if verbose:
                print(f"[ika_nav]   pos=({cx:.1f},{cy:.1f}) "
                      f"dist={dist:.1f}m err={math.degrees(err):.0f}° "
                      f"wheel=({r:.1f},{l:.1f})")

            _bekle(dt)

    send_vel(0, 0)
    print("\n[ika_nav] ══ HEDEF BÖLGEYE (HB) ULAŞILDI! ══")
    return True


def navigate_route(
        route, verbose=True, link_ok=None, rota_gecerli=None,
        rota_korumali_gonder=None, surus_deadline_monotonic=None,
        saat=time.monotonic, bekle=None):
    """Sadece İHA'dan gelen dinamik waypoint rotasını takip et."""
    wps = route_to_world_waypoints(route)
    road = (route.get("road", route.get("yol_no"))
            if isinstance(route, dict) else None)
    road_label = _road_label(road)
    return navigate(
        wps,
        f"Dinamik rota: {road_label.upper()}",
        verbose=verbose,
        link_ok=link_ok,
        rota_gecerli=rota_gecerli,
        rota_korumali_gonder=rota_korumali_gonder,
        surus_deadline_monotonic=surus_deadline_monotonic,
        saat=saat,
        bekle=bekle,
    )


def ika_gorevi(bind, bekleme_suresi=IKA_BEKLEME_SURESI_S,
               surus_suresi=IKA_SURUS_SURESI_S, *, saat=time.monotonic,
               bekle=None, rota_bekle=None, izin_bekle=None, sur=None,
               yks_peer=None):
    """İKA görevi: BEKLE (rota + IHA_LANDED + IKA_GO) sonra SÜR (HB'ye).

    K5 — iki AYRI son tarih (şartname §6.2):
      bekleme deadline = başlangıç + ``bekleme_suresi``   (İHA görev süresi)
      sürüş deadline   = izin anı  + ``surus_suresi``     (İKA görev süresi)
    Beklemede geçen süre sürüşten DÜŞÜLMEZ; sürüş saati izin geldiği an başlar.

    ``yks_peer`` (K8): OPEN_ROUTE/NO_ROUTE ACK kopyasının gideceği YKS adresi
    (host, port). OPEN_ROUTE sahada IKA_GO'dan ÖNCE geldiği için adres IKA_GO'dan
    öğrenilemez; verilmezse hakem 2. onayı UDP akışında hiç açılmaz.

    ``saat``/``bekle`` (T213): iki deadline de ``saat`` ile kurulur; ``bekle``
    varsayılan aşamalara (rota bekleme, izin bekleme, sürüş) geçirilir.
    Dışarıdan verilen ``rota_bekle``/``izin_bekle``/``sur`` geri çağrıları
    ESKİ imzalarıyla çağrılır (mevcut testler dokunulmadan geçer); saat
    enjeksiyonu isteyen çağıran bunu kendi geri çağrısına bağlar.

    Döner: 0 başarı · 1 rota gelmedi · 2 NO_ROUTE · 3 sürüş izni gelmedi ·
    4 sürüş süresi doldu / HB'ye ulaşılamadı.
    """
    if rota_bekle is None:
        rota_bekle = functools.partial(
            wait_open_route_from_comms, saat=saat, bekle=bekle)
    if izin_bekle is None:
        izin_bekle = functools.partial(
            receiver_surus_izni_bekle, saat=saat, bekle=bekle)
    if sur is None:
        sur = functools.partial(navigate_route, bekle=bekle)
    bekleme_suresi = max(0.0, float(bekleme_suresi))
    surus_suresi = max(0.0, float(surus_suresi))

    bekleme_deadline = saat() + bekleme_suresi
    alindi = rota_bekle(
        bind,
        bekleme_suresi,
        keep_receiver=True,
        deadline_monotonic=bekleme_deadline,
        yks_peer=yks_peer,
    )
    if alindi is None:
        print("[ika_nav] ✗ Geçerli dinamik rota gelmedi (bekleme süresi "
              f"{bekleme_suresi:.0f} s doldu) — İKA hareket etmez")
        return 1
    if isinstance(alindi, dict) and alindi.get("type") == MESAJ_NO_ROUTE:
        print("[ika_nav] ✗ Rota yok bildirimi alındı — timeout değil, güvenli ret")
        return 2
    route, receiver = alindi
    try:
        kalan = max(0.0, bekleme_deadline - saat())
        if not izin_bekle(receiver, kalan, deadline_monotonic=bekleme_deadline):
            return 3
        # Sürüş saati ŞİMDİ başlar — bekleme deadline'ından bağımsız.
        surus_deadline = saat() + surus_suresi
        print(f"[ika_nav] sürüş süresi başladı: {surus_suresi:.0f} s "
              "(şartname §6.2 İKA görev süresi)")
        basarili = sur(
            route,
            link_ok=lambda: receiver.link_ok,
            rota_gecerli=lambda: receiver_rota_gecerli(receiver),
            rota_korumali_gonder=lambda r, l: receiver_korumali_hiz_gonder(
                receiver, r, l
            ),
            surus_deadline_monotonic=surus_deadline,
            saat=saat,
        )
        return 0 if basarili else 4
    finally:
        # Durdurma komutu fiziksel olarak onemli, ama gonderim hatasi olsa bile
        # arka plan alicisini ve soketi kapatmak zorundayiz.
        try:
            send_vel(0, 0)
        finally:
            try:
                receiver.stop()
            finally:
                receiver.link.close()


def navigate_road(
        route, verbose=True, link_ok=None, rota_gecerli=None,
        rota_korumali_gonder=None):
    """Uyumluluk girişi: dinamik OPEN_ROUTE veya koordinat dizisini izle.

    Sayısal yol kimliği tek başına geometri taşımadığından
    ``route_to_world_waypoints`` tarafından reddedilir.
    """
    return navigate_route(
        route,
        verbose=verbose,
        link_ok=link_ok,
        rota_gecerli=rota_gecerli,
        rota_korumali_gonder=rota_korumali_gonder,
    )


def wait_open_route_from_comms(
        bind="0.0.0.0:5006", timeout=60, keep_receiver=False,
        deadline_monotonic=None, yks_peer=None, *, saat=None, bekle=None,
        link=None):
    """Şartname §2.2.5: İHA'nın dinamik rota verisi gelene kadar bekle.

    Geometrisi olmayan, yalnızca sayısal ``road`` içeren mesaj hareketi
    tetiklemez; sabit arena rotasına geri dönülmez. Tek bir ``NO_ROUTE`` karelik
    geçici bir algı sonucu olabilir: İKA güvenli duruşta kalır ama timeout
    dolana kadar daha yeni bir ``OPEN_ROUTE`` dinlemeyi sürdürür.

    ``yks_peer``: alıcıya bağlanan YKS adresi — rota ACK kopyası hakem ekranına
    (K8) buradan gider; OPEN_ROUTE IKA_GO'dan önce geldiğinden başka yol yok.

    ``saat``/``bekle`` (T213, ON_KAYIT §5.3): deadline ve dinleme döngüsü bu
    saatle işler; alıcı da AYNI saatle kurulur (``IkaReceiver(saat=…)``) —
    karar damgaları ile deadline aynı eksende olmazsa geçerli rota sessizce
    "deadline sonrası" sayılıp ATILIRDI (kilit: test_sim_mujoco_zincir).
    ``link``: önceden bağlanmış taşıyıcı (ephemeral port, 127.0.0.1:0 —
    port numarası göndericiye ancak bağlandıktan sonra söylenebilir); None ise
    ``bind`` ile UDPLink açılır (eski davranış).
    """
    from link import UDPLink
    from ika_receiver import IkaReceiver
    _saat = time.monotonic if saat is None else saat
    _bekle = time.sleep if bekle is None else bekle
    if yks_peer is not None:
        yks_peer = (str(yks_peer[0]), int(yks_peer[1]))
    if link is None:
        h, p = bind.split(":")
        link = UDPLink(bind=(h, int(p)))
        dinlenen = bind
    else:
        dinlenen = f"hazır link, port {getattr(link, 'port', '?')}"
    rx = IkaReceiver(link, yks_peer=yks_peer, saat=saat).start()
    print(f"[ika_nav] comms dinleniyor ({dinlenen}) — İHA açık yolu gönderecek...")
    if deadline_monotonic is None:
        deadline = _saat() + max(0.0, float(timeout))
    else:
        deadline = float(deadline_monotonic)
    rx.set_decision_deadline(deadline)
    son_gecersiz_nesil = -1
    son_no_route_nesil = -1
    sahiplik_devredildi = False
    try:
        while True:
            terminal_snapshot = _saat() >= deadline

            # OPEN_ROUTE ve NO_ROUTE ayrı thread'de güncellenir. İkisini tek
            # kilitli snapshot'tan okumak, doğrulama sırasında yeni durumla eski
            # rotayı eşleştirmeyi önler. ``latest`` içindeki eski rota önbelleği,
            # NO_ROUTE etkin olduğu sürece kesinlikle kullanılmaz.
            if terminal_snapshot:
                snapshot = rx.decision_deadline_snapshot()
            else:
                snapshot = rx.decision_snapshot()
            route, no_route, karar_nesli, karar_zamani = snapshot
            if karar_zamani is not None and karar_zamani > deadline:
                # Deadline sonrasında işlenen bir karar timeout sonucunu geriye
                # dönük değiştiremez. Receiver durdurulmaz: geçerli terminal rota
                # sahiplik devrinde heartbeat/NO_ROUTE dinlemeye devam etmelidir.
                route = no_route = None
            if route is not None and no_route is None:
                try:
                    waypoints = route_to_world_waypoints(route)
                except ValueError as exc:
                    if karar_nesli != son_gecersiz_nesil:
                        print(f"[ika_nav] ✗ Dinamik rota kullanılamaz: {exc} — bekleniyor")
                        son_gecersiz_nesil = karar_nesli
                else:
                    # Doğrulama sürerken yeni bir karar geldiyse eski snapshot'ı
                    # teslim etme; yeni durumu bir sonraki turda değerlendir.
                    if terminal_snapshot:
                        guncel_snapshot = rx.decision_deadline_snapshot()
                    else:
                        guncel_snapshot = rx.decision_snapshot()
                    (guncel_rota, guncel_no_route, guncel_nesil,
                     guncel_karar_zamani) = guncel_snapshot
                    if (guncel_nesil != karar_nesli
                            or guncel_rota is not route
                            or guncel_no_route is not None
                            or guncel_karar_zamani is None
                            or guncel_karar_zamani > deadline):
                        continue
                    road = route.get("road")
                    road_label = _road_label(road)
                    road_display = road if isinstance(road, int) else "koordinatlar"
                    print(f"[ika_nav] ✓ İHA'dan dinamik rota ALINDI: "
                          f"{road_label.upper()} ({road_display}) "
                          f"conf={route.get('conf')} wp={len(waypoints) - 1}")
                    if keep_receiver:
                        sahiplik_devredildi = True
                        return route, rx
                    return route

            if no_route is not None and karar_nesli != son_no_route_nesil:
                sebep = no_route.get("sebep", "bilinmeyen neden")
                detay = no_route.get("detay")
                print(f"[ika_nav] ✗ İHA NO_ROUTE bildirdi: {sebep}"
                      + (f" — {detay}" if detay else "")
                      + " — İKA güvenli duruşta; geçerli rota bekleniyor")
                son_no_route_nesil = karar_nesli

            if terminal_snapshot:
                return no_route

            kalan = deadline - _saat()
            _bekle(min(0.2, max(0.0, kalan)))
    finally:
        if not sahiplik_devredildi:
            rx.stop()
            rx.link.close()


# Eski çağrı adını koru; artık yol kimliği değil, tam OPEN_ROUTE mesajı döner.
wait_open_road_from_comms = wait_open_route_from_comms


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="İKA navigasyon (dinamik rota + comms)")
    ap.add_argument("mode", nargs="?", default="comms", choices=["comms"],
                    help="yalnızca comms ile gelen dinamik rota izlenir")
    ap.add_argument("--bind", default="0.0.0.0:5006", help="comms modu dinleme adresi")
    ap.add_argument("--bekleme-suresi", "--timeout", dest="bekleme_suresi",
                    type=float, default=IKA_BEKLEME_SURESI_S,
                    help="rota + IHA_LANDED + IKA_GO için azami bekleme (sn); "
                         "şartname §6.2 İHA görev süresi (varsayılan "
                         f"{IKA_BEKLEME_SURESI_S:.0f})")
    ap.add_argument("--surus-suresi", type=float, default=IKA_SURUS_SURESI_S,
                    help="izin geldikten sonra HB'ye ulaşma süresi (sn); "
                         "şartname §6.2 İKA görev süresi (varsayılan "
                         f"{IKA_SURUS_SURESI_S:.0f})")
    ap.add_argument("--yks", help="YKS adresi host:port — OPEN_ROUTE/NO_ROUTE "
                    "ACK kopyası hakem ekranına (K8). UDP'de verilmezse "
                    "'İKA'ya aktarıldı' 2. onayı YKS'de HİÇ açılmaz")
    args = ap.parse_args()
    yks_peer = None
    if args.yks:
        yh, yp = args.yks.rsplit(":", 1)
        yks_peer = (yh, int(yp))
    sys.exit(ika_gorevi(args.bind, args.bekleme_suresi, args.surus_suresi,
                        yks_peer=yks_peer))

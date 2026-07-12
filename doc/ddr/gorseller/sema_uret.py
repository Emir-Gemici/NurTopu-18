"""DDR blok şemaları — matplotlib ile rapor kalitesinde PNG üretir.
Kullanım: .venv/bin/python doc/ddr/gorseller/sema_uret.py
Çıktılar bu klasöre yazılır (blok_goruntu_isleme / blok_haberlesme /
akis_iha / akis_ika / ariza_mantik .png). Şemalar Word şablonuna eklenecek."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).parent
PAD = 0.10
RENK = {"islem": ("#eaf1fb", "#2b5aa0"), "veri": ("#fdf3e3", "#b07020"),
        "karar": ("#fdeaea", "#b03030"), "ok": "#444444"}


def kutu(ax, x, y, w, h, metin, tur="islem", fs=10):
    fc, ec = RENK[tur]
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle=f"round,pad={PAD}", lw=1.4, fc=fc, ec=ec))
    ax.text(x, y, metin, ha="center", va="center", fontsize=fs, color="#1a1a1a",
            linespacing=1.2)


def ok(ax, x0, y0, x1, y1, metin="", fs=9, ldx=0.15, ldy=0.0, lha="left",
       stil="-|>", renk=None):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=stil,
                                 mutation_scale=15, lw=1.4,
                                 color=renk or RENK["ok"]))
    if metin:
        ax.text((x0 + x1) / 2 + ldx, (y0 + y1) / 2 + ldy, metin, fontsize=fs,
                color=renk or "#555555", ha=lha, va="center")


def tuval(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    return fig, ax


def kaydet(fig, ad, baslik):
    fig.suptitle(baslik, fontsize=13, fontweight="bold", y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    p = OUT / ad
    fig.savefig(p, dpi=160, facecolor="white")
    plt.close(fig)
    print("✓", p)


def dikey_zincir(ax, adimlar, h, fs, y_ust=9.3, y_alt=0.6):
    """Kutuları dikey diz, aralarına ok koy (çakışmasız aralık hesapları)."""
    n = len(adimlar)
    ys = [y_ust - i * ((y_ust - y_alt) / (n - 1)) for i in range(n)]
    yarim = h / 2 + PAD + 0.06
    for (metin, tur), y in zip(adimlar, ys):
        kutu(ax, 5, y, 8.7, h, metin, tur, fs=fs)
    for y0, y1 in zip(ys, ys[1:]):
        ok(ax, 5, y0 - yarim, 5, y1 + yarim)


# ── 1. Görüntü işleme boru hattı ─────────────────────────────────────────────
fig, ax = tuval(7.4, 10.6)
dikey_zincir(ax, [
    ("Nadir kamera karesi (1 Hz) + çekim anı İHA pozu (x, y, z, yaw)", "veri"),
    ("ORTOMOZAİK — kareler kuzey-yukarı saha haritasına dizilir", "islem"),
    ("Letterbox 1024×1024 (en-boy korunur → çözünürlükten bağımsız)", "islem"),
    ("Işık normalizasyonu (karanlıksa gamma + CLAHE kopyasıyla yarış)", "islem"),
    ("YOLOv8n-seg → traversable / blocked piksel maskeleri", "islem"),
    ("Gürültü ayıklama — morfoloji + en büyük bağlı bileşen", "islem"),
    ("YOL KARARI: SOL / ORTA / SAĞ (üst bant centroid → saha üçte-birleri)", "karar"),
    ("Rota üretimi — distance-transform merkez hattı → waypoint (piksel→metre)", "islem"),
    ("SAĞLAMLIK SÜZGECİ — saha dışı / geri akış at; <3 nokta ise GÖNDERME", "karar"),
    ("OPEN_ROUTE (JSON): referans noktası + yerel waypoint listesi → İKA + YKS", "veri"),
], h=0.44, fs=9.6)
kaydet(fig, "blok_goruntu_isleme.png", "Görüntü İşleme Boru Hattı (İHA)")

# ── 2. Haberleşme mimarisi (mesaj-merkezli, çakışmasız yerleşim) ─────────────
fig, ax = tuval(9.2, 7.0)
kutu(ax, 5.0, 8.9, 3.6, 1.0, "İHA (Jetson)\nalgı + rota üretimi", "islem", 11)
kutu(ax, 5.0, 6.1, 4.6, 1.15,
     "OPEN_ROUTE (JSON)\nv · seq · t · güven · referans noktası + yerel wp", "veri", 10)
kutu(ax, 1.9, 3.4, 3.1, 1.0, "YKS\nhakem ekranı, canlı doğrulama", "islem", 10)
kutu(ax, 8.1, 3.4, 3.1, 1.0, "İKA (RPi 5)\nrota takibi", "islem", 10)
kutu(ax, 5.0, 0.9, 8.8, 0.95,
     "Taşıyıcı: geliştirme/sim = UDP · saha = 433 MHz RF (transparan seri) · çerçeve: newline-JSON",
     "veri", 9.5)
ok(ax, 5.0, 8.25, 5.0, 6.85, "yayın", ldx=0.2)
ok(ax, 3.9, 5.35, 2.3, 4.05, "OPEN_ROUTE", ldx=-1.75, lha="left")
ok(ax, 6.1, 5.35, 7.7, 4.05, "OPEN_ROUTE", ldx=0.35)
ok(ax, 1.4, 4.05, 3.5, 8.6, "ACK(seq)", ldx=-1.15, stil="-|>", renk="#2b7a2b")
ok(ax, 8.6, 4.05, 6.5, 8.6, "ACK(seq)", ldx=0.35, stil="-|>", renk="#2b7a2b")
ax.text(5.0, 4.55, "her iki ACK gelene dek TEKRAR GÖNDERİM (>%95 aktarım doğruluğu)",
        ha="center", fontsize=9.5, color="#b03030")
ax.text(5.0, 2.15, "HEARTBEAT (tüm düğümler) — kesilirse İKA GÜVENLİ DURMA",
        ha="center", fontsize=9.5, color="#555555")
kaydet(fig, "blok_haberlesme.png", "İHA ↔ İKA / YKS Haberleşme Mimarisi")

# ── 3. İHA görev akışı ───────────────────────────────────────────────────────
fig, ax = tuval(7.2, 9.2)
dikey_zincir(ax, [
    ("HAZIRLIK — öz-testler (kamera/GNSS/telemetri), YKS bağlantısı", "islem"),
    ("MANCINIK FIRLATMA (stall ×1,15) → kronometre başlar (≤15 dk)", "islem"),
    ("Tırmanış → 30 m tarama irtifası, HTAB'a giriş", "islem"),
    ("SERPANTİN TARAMA — 4 hat, ~20–30 s, 1 Hz kare + poz", "islem"),
    ("Ortomozaik + model tespiti (< 60 s) + rota üretimi", "islem"),
    ("VERİ AKTARIMI (HAVADA) — ACK'e dek tekrar, hakem canlı onay", "karar"),
    ("İHA-İB'ye sokulma → PARAŞÜT otonom (< 7 m/s) → iniş, süre durur", "islem"),
], h=0.56, fs=10)
kaydet(fig, "akis_iha.png", "İHA Görev Akışı")

# ── 4. İKA görev akışı ───────────────────────────────────────────────────────
fig, ax = tuval(7.2, 8.6)
dikey_zincir(ax, [
    ("BEKLEME — İKA-KB'de; OPEN_ROUTE önbelleğe, ACK dönülür\n(İHA inmeden hareket YASAK)", "islem"),
    ("BAŞLATMA — İHA iniş teyidi + YKS manuel başlat → süre başlar (≤10 dk)", "islem"),
    ("ROTA OTURTMA — referans noktası + GNSS/IMU/enkoder füzyonu + A*", "islem"),
    ("OTONOM SÜRÜŞ — diferansiyel waypoint takibi,\nkamera yerel doğrulama, telemetri YKS'ye", "islem"),
    ("Engel/sapma → DUR + yeniden planla (watchdog)", "karar"),
    ("HB'ye giriş → GÖREV BAŞARILI, dur, süre durur", "islem"),
], h=0.78, fs=10)
kaydet(fig, "akis_ika.png", "İKA Görev Akışı")

# ── 5. Arıza emniyet mantığı (3 kritik senaryo) ─────────────────────────────
fig, ax = tuval(10.8, 6.8)
kolon = [
    ("A1 — BAĞLANTI KAYBI", [
        ("HEARTBEAT zaman aşımı?", "karar"),
        ("İHA: yedek kanal +\ntekrar gönderim", "islem"),
        ("İKA: GÜVENLİ DURMA\nrota önbelleği korunur", "islem"),
        ("bağlantı dönerse\nkaldığı wp'den devam", "islem")]),
    ("A2 — GÜVENİLİR ROTA YOK", [
        ("sağlamlık süzgeci:\n< 3 geçerli waypoint?", "karar"),
        ("rota GÖNDERİLMEZ", "islem"),
        ("tarama bir kez yinelenir", "islem"),
        ("YKS'ye 'TESPİT YOK'\n(yanlış yönlendirme yasak)", "islem")]),
    ("A3 — İKA ENGEL / SAPMA", [
        ("sıfır ilerleme veya rota\nhatası eşiği? (watchdog)", "karar"),
        ("DUR → geri manevra", "islem"),
        ("A* yerel yeniden planlama", "islem"),
        ("N denemede ilerleme yok →\nGÜVENLİ DURMA + YKS uyarısı", "islem")]),
]
for k, (baslik, kutular) in enumerate(kolon):
    x = 1.85 + k * 3.15
    ax.text(x, 9.6, baslik, ha="center", fontsize=10.5, fontweight="bold")
    ys = [8.55 - i * 2.25 for i in range(len(kutular))]
    for (m, t), y in zip(kutular, ys):
        kutu(ax, x, y, 2.85, 1.0, m, t, fs=9.2)
    for y0, y1 in zip(ys, ys[1:]):
        ok(ax, x, y0 - 0.66, x, y1 + 0.66)
kaydet(fig, "ariza_mantik.png", "Arıza Emniyet Mantık Şemaları (yazılım katmanı)")

print("TAMAM — 5 şema üretildi.")

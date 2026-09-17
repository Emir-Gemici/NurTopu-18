"""T244 (D-462 A/D/E) — FDR Bölüm 3/4 İÇ ÇELİŞKİ NÖBETÇİSİ.

NEDEN (ölçülen kusur örüntüsü): FDR kendi **kapanmış** kalemlerini "açık kalem /
ölçülecek" diye gösteriyordu (D-462 A1–A6); bir ölçüm elde olduğu hâlde sonucu kötü
diye rapora hiç girmemişti (D-462 E); simülasyonun üretimde olmayan iki yardımı
sınırlar paragrafında yazılı değildi (D-462 D). Bu kapı, T244'te düzeltilen sekiz
yüzeyin her birini **kaynağından** (kod satırı, artefakt JSON, ikinci FDR belgesi)
yeniden bağlar ve çelişkinin sessizce geri gelmesini engeller.

  T1  §3.3.1.1.8 MAVLink tek-yazar kilidi: üç sürecin de kodda kilitli olduğu
      yazılı; eski "açık kalemdir" cümlesi YALNIZ çizili; atıflar gerçek kod
      satırlarıyla (`comms/inis_kaniti.py` + üç süreç) doğrulanır; 6 Eylül'de de
      koşulmadığı yazılı (ÖLÇÜLEMEDİ ≠ GEÇTİ)
  T2  §3.3.4.1.7 H1c damgası KOŞULDU/GEÇTİ; H1 %40 hükmü DÜŞTÜ KALIR; %40 ölçütü
      metinde TAM BİR KEZ (rakip eşik yok); sayılar `olcum_20260903.json`'dan
  T3  §3.3.4.2.1 künye + denklik notu + §3.4.1 A3 + Kanıt dizini: `.engine` sha
      kayıt defteriyle birebir; D-303 3/126 DÜŞTÜ hükmü üç yerde de olumluya
      çevrilmemiş; `DERLENINCE_YAZILIR` yalnız çizili
  T4  §4.4 girişi ölçülen/ölçülemeyen sayımıyla; 9 ekipman satırı; 6 Eylül
      hücreleri (döküm, ESC kalibrasyonu, pil, RC failsafe) dosya:satır ile
  T5  §4.8.3 · §4.1.3 · §4.13.3: "ölçülecek" cümleleri çizili, yerlerine 6 Eylül
      koşumları; systemd kipleri hâlâ ÖLÇÜLEMEDİ (yanlış kapanma yok)
  T6  §4.0 ↔ `YONERGE_HARITASI.md`: Y-4-M01…M12 durumları HİZALI (çelişki bir daha
      sessizce oluşamaz)
  T7  DÜRÜSTLÜK: simülasyonun iki yardımı + "İYİMSER ÜST SINIRDIR" cümlesi hem
      §3.3.3.2 hem §4.7'de ve ÇİZİLMEMİŞ; kod satırları doğrulanır
  T8  §3.3.4.2.8 (a) SENTETİK ışık/gölge kesiti: v2/v3 sayıları `k3b` artefaktından;
      "saha değil" ve D-441 öncesi yerleşim sınırı yazılı; §4.8 ve §4.8.4 tazelenmiş
  T9  KABUL ÖLÇÜTÜ BİÇİMİ (D-466, T244-B): iki bölümün TAMAMINDA yapısal kabul
      kilidi — hem KAPSAMA (48/48 mutant düşer) hem SINIR (6 sınıf kaçar)
      mutasyonla ölçülür; yanlış pozitif 5 meşru düzenlemeyle sınanır
  T10 kuru koşum `[YOK]` sayısı log'dan okunup rapora bağlanır (D-466 kusur 3)
  M1…M9  kurallar sentetik metinle iki yönde sınanır (boş kapı olmasın)

BELGE KİLİDİ (D-453 / D-460 / D-461 / D-463): tüm aramalar **normalleştirilmiş**
metinde yapılır — HTML varlıkları açılır, çizili aralıklar (`~~…~~`, tek tilde,
`<del>/<s>/<strike>`) **ayıklanır** (içerik silinir), kalın/italik/kod işaretleri
ve tipografik kesme/tırnak/tire düzleştirilir, Türkçe harfler ASCII'ye katlanır,
eş anlamlı geri dönüşler tek belirtece indirilir. Beyaz liste: bu üç çizme
sözdizimi dışında çizme işareti kalırsa kilit DÜŞER — U+0335…U+0338 birleştirici
çizik ve onun HTML varlık biçimi (`&#822;`, `&#x336;`) dâhil (D-463 (a): bu
biçim belgede üstü çizili görünüyor ama kalıpsız kaçıyordu). "≈/~" yaklaşık
işareti tek istisnadır ve ayrıca sınanır.

KABUL ÖLÇÜTÜ BİÇİMİ — YAPISAL KİLİT (D-466, T244-B): çelişkili ikinci kabul
hükmü taraması artık SÖZLÜKLE değil BİÇİMLE çalışır ve iki bölümün TAMAMINI
gezer. Ölçülen kusur (T244 çürütücüsü): eski `CELISKI_SOZCUKLERI` sözlüğü
8 büyük harfli ifadenin birebir geçmesiyle düşüyordu; kilitli kesitlerin
DIŞINA konan çelişkili ikinci hükümlerin **6/6'sı kaçtı** ("Gözden geçirilmiş
kapı" yakalanıyor, eş anlamlısı "Revize edilmiş kabul kapısı" kaçıyordu).
Yeni kilit (aşağıda "KABUL ÖLÇÜTÜ BİÇİMİ") iki yapısal kural arar (K1: sayı
taşıyan kabul ölçütü · K2: kip/edim biçimi) ve tutan her birimi ÖN KAYITLI
tam dizgi listesine bağlar (D-465 (1)).
  ÖLÇÜLEN KAPSAMA: 8 cümle × 2 bölüm × 3 konum = **48/48 mutant DÜŞTÜ**
  (`T9c`); mutasyonsuz iki bölüm ve 5 meşru düzenleme **0 yanlış pozitif**
  (`T9a`, `T9d`).
  ÖLÇÜLEN SINIR (kapanmayan, D-465 (4)): sayısız + kipsiz + kabul sözcüksüz
  olumlu hüküm, ölçütü iki tablo satırına bölme, eşiği yeni birim sözcüğüyle
  ya da sayıyı yazıyla yazma — **6 sınıfın 6'sı hâlâ kaçıyor** (`T9e`).
  D-463 (b) bu yüzeyde **daraltıldı, kapanmadı**; sınıf sayılarak yazılıdır.

⚠ NOT: kanonik `tests/belge_kilidi.py` şu an T240 dalında yazılıyor ve master'da
YOK. Bu dosyadaki normalleştirme fonksiyonları **tek yerde** (aşağıdaki
"BELGE KİLİDİ" bloğu) toplanmıştır ve **T242 ile kanonik yardımcıya geçirilecektir**;
kalıcı bir ikinci normalleştirme kopyası bırakılmaz.
"""

import html
import json
import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
FDR = KOK / "FDR"
B3 = FDR / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"
B4 = FDR / "BOLUM_4_TEST_FAALIYETLERI.md"
YONERGE = FDR / "YONERGE_HARITASI.md"
KAYIT = KOK / "config" / "model_registry.json"
ENGINE_JSON = (KOK / "results" / "jetson_20260906" / "jetson_log_20260906"
               / "engine_karar_denkligi.json")
H1C_JSON = KOK / "results" / "p5_histerezis" / "olcum_20260903.json"
K3B = KOK / "results" / "fdr_sprint_20260910" / "H1" / "k3b"
INIS = KOK / "comms" / "inis_kaniti.py"
PARAM = KOK / "config" / "pixhawk" / "arducopter_fda_20260906.param"


# ─────────────────────────────────────────────────────────────────────────────
# BELGE KİLİDİ — normalleştirme (TEK YER; T242 ile tests/belge_kilidi.py'ye geçer)
# ─────────────────────────────────────────────────────────────────────────────

# Beyaz liste: kabul edilen ÜÇ çizme sözdizimi. Çizili içerik AYIKLANIR (silinir),
# böylece çizilmiş bir iddia kilidi DOYURAMAZ.
_CIZIK_TILDE2 = re.compile(r"~~.+?~~", re.S)
_CIZIK_ETIKET = re.compile(r"<(del|s|strike)\b[^>]*>.*?</\1\s*>", re.S | re.I)
# Tek tilde (GFM yan-kanat kuralı): açan `~` boşlukla/satır başıyla önceli ve
# boşluksuz takipli; kapatan `~` boşluksuz öncelli. UZUNLUK SINIRI YOKTUR (D-461:
# `{1,40}` sınırı 40 karakterden uzun çiziği görmüyordu).
_CIZIK_TILDE1 = re.compile(r"(?<![~\w])~(?![~\s])[^\n~]+?(?<![~\s])~(?![~\w])")
# "yaklaşık" işareti çizme DEĞİLDİR: `~18:45`, `~%6`, `~1,35` — tek istisna.
_YAKLASIK = re.compile(r"(?<![\w~])~(?=[\d%.,])")
# Beyaz listede olmayan her çizme işareti (yeni sözdizimi kalıpsız yakalanır).
_CIZME_ARTIGI = re.compile(r"~|</?\s*(?:del|s|strike)\b|[̵-̸]", re.I)


def varlik_coz(metin):
    """HTML varlıklarını açar (D-463 (a)).

    U+0336 birleştirici çiziğin **varlık biçimi** (`&#822;`, `&#x336;`) belgede
    üstü çizili görünüyor ama kalıpsız kaçıyordu; `&#126;` ile yazılmış tilde de
    öyle. Varlıklar aramadan ÖNCE açılır.
    """
    return html.unescape(metin)

_KATLAMA = str.maketrans("İIıĞğÜüŞşÖöÇçÂâÎî", "IIiGgUuSsOoCcAaIi")
_TIPOGRAFI = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "−": "-", "­": "", "​": "",
    " ": " ", "…": "...",
}
# Eş anlamlı geri dönüşler tek belirtece iner (D-460 RED-2 / D-454 sınıfı).
_ESANLAM = (
    (r"\bEN AZ\b|≥|>=", " >= "),
    (r"\bASAN\b|\bASARSA\b", " > "),
    (r"\bOLCULMEDI\b|\bOLCULEMEZ\b|\bOLCUM YOK\b", "OLCULEMEDI"),
    (r"\bDOGRULANDI\b|\bKANITLANDI\b|\bTEYIT EDILDI\b|\bBASARILI OLDU\b|\bTUTAR\b|\bTUTUYOR\b",
     "OLUMLU_HUKUM"),
    (r"\bGECTI\b|\bGECER\b|\bSAGLANDI\b", "GECTI"),
)
# Kabul yüzeyinde ÇELİŞKİLİ İKİNCİ HÜKÜM sözcükleri (D-461 karar (d)).
# ⚠ Bu liste SONLU bir SÖZLÜKTÜR ve tek başına YETMEZ: eş anlamlısı kaçar
# (ölçüldü — D-466). Asıl kapsama aşağıdaki YAPISAL kilittedir; bu liste
# yalnız ek bir kat olarak durur ve düşük değerli anlatı yüzeyinde kalır.
CELISKI_SOZCUKLERI = (
    "GOZDEN GECIRILMIS", "GUNCELLENMIS KAPI", "KURAL KALDIRILDI",
    "ESIK GUNCELLENDI", "OLCUT GEVSETILDI", "YENIDEN DEGERLENDIRILDI",
    "BU KURAL UYGULANMAZ", "ARTIK GECERLI DEGIL",
)


def cizikleri_ayikla(metin):
    """Beyaz listedeki üç çizme sözdiziminin İÇERİĞİNİ siler (varlıklar önce açılır)."""
    metin = varlik_coz(metin)
    metin = _CIZIK_TILDE2.sub(" ", metin)
    metin = _CIZIK_ETIKET.sub(" ", metin)
    return _CIZIK_TILDE1.sub(" ", metin)


def cizme_artiklari(metin):
    """Ayıklamadan sonra kalan çizme işaretleri (yaklaşık işareti hariç)."""
    kalan = _YAKLASIK.sub("", cizikleri_ayikla(metin))
    return _CIZME_ARTIGI.findall(kalan)


def katla(metin):
    """Türkçe harfleri ASCII'ye katlar ve büyütür (aramada yazım farkı kalmasın)."""
    return metin.translate(_KATLAMA).upper()


def normalles(metin, cizigi_at=True):
    """Kilit araması için kanonik metin: çizik ayıkla → tipografi → vurgu → katla.

    Satır yapısı KORUNUR (satır bazlı denetimler için). Alt çizgi SİLİNMEZ —
    `NO_ROUTE`, `BATT_VOLT_MULT`, `gorev_kosumu.py` gibi belirteçler bozulmasın.
    """
    if cizigi_at:
        metin = cizikleri_ayikla(metin)
    metin = metin.replace("\r\n", "\n")
    for a, b in _TIPOGRAFI.items():
        metin = metin.replace(a, b)
    metin = re.sub(r"[*`]+", "", metin)           # kalın/italik/kod işaretleri
    metin = katla(metin)
    for kalip, yerine in _ESANLAM:
        metin = re.sub(kalip, yerine, metin)
    return re.sub(r"[ \t]+", " ", metin)


def tekhat(metin, cizigi_at=True):
    """`normalles` + TÜM boşluk dizileri tek boşluğa iner (satır kırığı aramayı bozmasın)."""
    return re.sub(r"\s+", " ", normalles(metin, cizigi_at)).strip()


def oku(p):
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def kesit(metin, bas, son=None):
    """`bas` çapasından `son` çapasına kadar olan HAM metin (son yoksa dosya sonu)."""
    i = metin.index(bas)
    j = metin.index(son, i + len(bas)) if son else len(metin)
    return metin[i:j]


def adet(metin, aranan):
    """Normalleştirilmiş (tek hatlı) metinde `aranan`ın geçiş sayısı."""
    return tekhat(metin).count(tekhat(aranan))


def eksikler(metin, gerekli):
    """gerekli = ((metin, tam_adet), ...) → kural ihlali listesi."""
    kusur = []
    for aranan, bekleyen in gerekli:
        bulunan = adet(metin, aranan)
        if bulunan != bekleyen:
            kusur.append("{!r}: {} kez (beklenen {})".format(aranan[:60], bulunan, bekleyen))
    return kusur


def yasaklar(metin, yasak):
    """Normalleştirilmiş metinde bulunmaması gereken ifadeler."""
    n = tekhat(metin)
    return ["{!r} normalleşmiş metinde VAR".format(y[:60]) for y in yasak if tekhat(y) in n]


def celiskili_ikinci_hukum(metin):
    n = tekhat(metin)
    return [s for s in CELISKI_SOZCUKLERI if s in n]



# ─────────────────────────────────────────────────────────────────────────────
# KABUL ÖLÇÜTÜ BİÇİMİ — YAPISAL KİLİT (D-466; D-465 (1)'in bu yüzeydeki karşılığı)
# ─────────────────────────────────────────────────────────────────────────────
#
# NEDEN (ölçülen kusur): yukarıdaki `CELISKI_SOZCUKLERI` taraması **sözlük**
# düzeyindeydi. T244 çürütücüsü ölçtü: kilitli kesitlerin DIŞINA konan çelişkili
# ikinci kabul hükümlerinin **6/6'sı kaçtı**; aynı yere konan "Gözden geçirilmiş
# kapı: engine kabul edilir." YAKALANDI ama eş anlamlısı "Revize edilmiş kabul
# kapısı: engine kabul edilir." KAÇTI (D-466). Sözlüğün kaçış yüzeyi sonsuzdur.
#
# Bu kilit sözlüğe değil BİÇİME bakar ve iki bölümün TAMAMINI gezer:
#
#   K1 — SAYI TAŞIYAN KABUL ÖLÇÜTÜ. Aynı birimde (a) karşılaştırma işareti
#        (≤ ≥ < >) YA DA "eşik / kapı / ölçüt / kabul" sözcüğü, (b) `n/m` ya da
#        `%x` (`%x,y`) sayısı ve (c) hüküm sözcüğü (GEÇTİ · KABUL · SAYILIR ·
#        YETERLİ · olumlu hüküm) birlikte geçiyorsa tutar.
#   K2 — KİP (edim) BİÇİMİ. Aynı birimde (i) hüküm nesnesi (KABUL · EŞİK · KAPI ·
#        ÖLÇÜT · GEÇTİ · DÜŞTÜ · ÖLÇÜLEMEDİ · KURAL · HÜKÜM) ve (ii) kip eki
#        (-ABİLİR / -MALIDIR / SAYILIR / EDİLİR / ALINIR) birlikte geçiyorsa
#        tutar. FDR'nin ölçüm dili KESİN kiptedir ("GEÇTİ", "DÜŞTÜ",
#        "ÖLÇÜLEMEDİ"); bir hükmün "sayılır / kabul edilir / kapatılabilir" diye
#        yazılması ölçüm RAPORU değil ölçüt REÇETESİDİR. K2, K1'in göremediği
#        SAYISIZ ikinci hükmü ("Revize edilmiş kabul kapısı: engine kabul
#        edilir.") yakalayan yapısal koldur.
#
# K1 ya da K2 tutan her birim, `ON_KAYITLI_KABUL_BIRIMLERI` içinde TAM DİZGİ
# olarak yoksa kapı DÜŞER (D-465 (1) "ön kayıtlı metin eşitliği"). Yani yeni bir
# kabul hükmü NEREYE konursa konsun — kilitli kesitin içine de dışına da — ön
# kayda eklenene kadar kapıyı düşürür.
#
# YAPI YORUMLANMAZ, SİLİNİR (D-465 (3)): burada çizik AYIKLANMAZ. Çizme
# işaretleri (`~~`, tek tilde, `<del>/<s>/<strike>`), birleştirici çizik
# (U+0335…U+0338), vurgu/kod imleri ve HTML varlıkları yalnız İŞARET olarak
# silinir, İÇERİK kalır ve taranır. Böylece "çizik/varlık içine saklama" yüzeyi
# açılmaz: çizili bir kabul hükmü de ön kayda girmek zorundadır.

_YAPI_SIL = re.compile(r"[\u0335-\u0338]|~~|~|</?\s*(?:del|s|strike)\b[^>]*>|[*`_]+", re.I)
_FENCE = re.compile(r"^\s*(?:```|~~~)")
# Cümle sınırı: nokta/ünlem/soru + boşluk + BÜYÜK harf. Metin zaten katlanmış ve
# büyütülmüş olduğu için `jetson_fps.py 120`, `%2,38`, `v4.5.7` bölünmez.
_CUMLE_BOL = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

_KARSILASTIRMA = re.compile(r"[≤≥<>]")
_ESIK_SOZ = re.compile(r"ESIK|KAPI|OLCUT|KABUL")
_OLCUM_SAYISI = re.compile(r"\d+\s*/\s*\d+|%\s?\d+(?:[.,]\d+)?")
_HUKUM_SOZ = re.compile(r"\bGECTI\b|KABUL|\bSAYILIR\b|\bYETERLI\b|OLUMLU_HUKUM")
_HUKUM_NESNESI = re.compile(r"KABUL|ESIK|KAPI|OLCUT|\bGECTI\b|\bDUSTU\b|OLCULEMEDI|"
                            r"\bYETERLI\b|HUKUM|\bKURAL\b|OLUMLU_HUKUM")
_KIP_EKI = re.compile(r"\b\w*(?:ABILIR|EBILIR|MALIDIR|MELIDIR)\b|\bSAYILIR\b|"
                      r"\bEDILIR\b|\bALINIR\b")


def yapisal_kanon(satir):
    """Bir SATIRIN kanonik biçimi: yapı imleri SİLİNİR (ayıklanmaz), içerik kalır."""
    s = varlik_coz(satir)
    s = _YAPI_SIL.sub(" ", s)
    for a, b in _TIPOGRAFI.items():
        s = s.replace(a, b)
    s = katla(s)
    for kalip, yerine in _ESANLAM:
        s = re.sub(kalip, yerine, s)
    return re.sub(r"[ \t]+", " ", s).strip()


def kabul_birimleri(metin):
    """Belgeyi tarama BİRİMLERİNE böler.

    Birim = bir tablo satırı · kod bloğu içinde bir satır · ya da bir paragrafın
    bir cümlesi. Paragrafın satırları ÖNCE birleştirilir: hükmü iki satıra bölerek
    ("Revize edilmiş kabul\nkapısı: …") kaçmak mümkün olmasın.
    """
    birim, blok, fence = [], [], False

    def bosalt():
        if blok:
            for cumle in _CUMLE_BOL.split(" ".join(blok)):
                cumle = cumle.strip()
                if cumle:
                    birim.append(cumle)
            del blok[:]

    for ham in metin.replace("\r\n", "\n").split("\n"):
        if _FENCE.match(ham):
            bosalt()
            fence = not fence
            continue
        s = yapisal_kanon(ham)
        if not s:
            bosalt()
            continue
        if fence or s.startswith("|"):
            bosalt()
            birim.append(s)
            continue
        blok.append(s)
    bosalt()
    return birim


def kabul_bicimi(birim):
    """Birimin hangi kabul-ölçütü biçimini taşıdığı: ('K1',) · ('K2',) · ('K1','K2') · ()."""
    kural = []
    if ((_KARSILASTIRMA.search(birim) or _ESIK_SOZ.search(birim))
            and _OLCUM_SAYISI.search(birim) and _HUKUM_SOZ.search(birim)):
        kural.append("K1")
    if _HUKUM_NESNESI.search(birim) and _KIP_EKI.search(birim):
        kural.append("K2")
    return tuple(kural)


def kabul_ihlalleri(metin):
    """Kabul-ölçütü biçimi taşıyıp ÖN KAYITTA OLMAYAN birimler (boş liste = temiz)."""
    return [(kabul_bicimi(b), b) for b in kabul_birimleri(metin)
            if kabul_bicimi(b) and b not in ON_KAYITLI_KABUL_BIRIMLERI]


# ── ÖN KAYIT: kabul/hüküm biçimi taşıyan 73 birim (12 Eylül 2026, D-466) ──
# Bu liste belgenin O ANKİ kabul yüzeyinin TAM DİZGİ dökümüdür. Bir sözcüğü
# değişirse kapı düşer; yeni bir kabul hükmü buraya EKLENMEDEN geçemez.
ON_KAYITLI_KABUL_BIRIMLERI = frozenset((
    "| GOREV BILGISAYARI | JETSON NANO 4GB (JETPACK 4.6.X) → JETSON ORIN NANO DEVELOPER KIT 4 GB (JETPACK 7.2.1, UBUNTU 24.04, PYTHON 3.12; 3 EYLUL BEYANI 'NANO 4GB' 6 EYLUL'DE KARTLA YANLISLANDI - D-431) | KURULDU 6 EYLUL - GENEL KAPI 15/15 · 15/15, FPS KAPISI GECTI; ARACA TAKILMADI, PIXHAWK/KAMERA BAGLI DEGIL - §3.3.1.1.12 |",
    "YKS'NIN IKA GO SEQ 'I ILE IHA'NIN OPEN ROUTE SEQ 'I CAKISABILIR; TIPSIZ ESLEME, HUB FAN-OUT'UNDA CAPRAZ KABUL URETIYORDU (OLCULDU, REVIEW LOG.MD D-405 Q4 / T206).",
    "KURAL BUGUN YALNIZ IHA KOMUT ALICI 'DA KODLA KILITLIDIR : SERI CIHAZ REDDEDILIR, --SERI-PIXHAWK-BILEREK ILE BILEREK ASILABILIR.",
    "NANO CPU 'DA 512'DE HIZI OLCULEMEDI VE FPS KAPISININ ALTINDA CIKABILIR.",
    "TENSORRT .ENGINE : VENV38'DE TENSORRT MODULU YOKTUR (JETPACK 4.6 BAGI PY3.6). .ENGINE BU KART ICIN OLCULEMEDI SAYILIR; PT/ONNX ILE UCULUR. → 6 EYLUL (D-431): ORIN NANO'DA TENSORRT 10.16.2 KURULDU; .ENGINE .PT 'DEN DERLENDI (530 S; 57 283 989 B; SHA BB9BD868...0300 , DEFTERE --TUREV-KAYDET ILE YAZILDI, TUREV ESLESTI ).",
    '| KABUL ZINCIRI K0-K8 + K5A (V36) | 10/10 GECTI |',
    '| T17 FPS (120 ORNEK) | PT 1,35/1,06 · ENGINE 1,58/1,33 FPS, ESIK 0,61 → GECTI |',
    '| 5 | ARKA UC | GERCEKSURUCU ( IKA SURUCU.PY:186 ): ARKA UCSUZ KURULUM DONANIM YOK ILE DUSER ( :196 ) - SESSIZ ISKELET YASAK; GAZEBOSURUCU ( :79 ; GZ BU MAKINEDE YOK); SAHTESURUCU ( :157 ; TEST VE KABUL); MUJOCOSURUCU (T213-B, SIMULATION/MUJOCO/ , AYNI ARAYUZ - BU GOREVDE DEGIL, H1-K5 ORADA OLCULUR) | SIMULATION/SCRIPTS/IKA SURUCU.PY , SCRIPTS/IKA SURUCU KABUL.PY | TESTS/TEST FAZ B IKA SURUCU KABUL.PY (EXIT 0/1/2 SOZLESMESI) |',
    'K3 GECTI EVET HIZ RAMPASI 0 -> 0.30 M/S, 5 ADIM: 5/5 ADIM; SON V=0.30 M/S',
    "SAHTE SURUCUNUN 6/6'SI SOZLESMENIN KANITIDIR, ARACIN DEGIL: RAMPA 0 → 0,30 M/S'DE ( RAMPA HEDEF MS , 5 ADIM, IKA SURUCU KABUL.PY:83-85 ) ARACIN HAREKETI GERCEK/SIM SURUCUDE GOZLE TEYIT ISTER - BETIK BU SATIRI BASAR, YAZILIM BUNU OLCEMEZ. ⚠ CIKTIDAKI MAX SPEED=2.0 M/S KABUL KOSUMU ANINDAKI (T213-B ONCESI) IKA NAV.PY:35 DEGERIDIR; DDR FIZIKSEL HIZ 1,3 M/S - UC KOPYALI SABIT CONTRACTS.MD §4'E TEK KAYNAK OLARAK TASINIYOR TASINDI (T213-B, D-438 §2F; BUGUN MAX SPEED IKA NAV.PY:39 = CODES/KARAR SOZLESMESI.PY:1996 IKA AZAMI HIZ MS 1,3 M/S - 10 EYLUL T214-B OKUMASI); KABUL RAMPASI (0,30) IKI DEGERIN DE ALTINDADIR, SONUC DEGISMEZ.",
    'DDR\'NIN "STM32 ↔ RPI5 ENTEGRASYON TESTI, PAKET KAYBI %0" KABULU (DDR YAZILIM TABLO 3.3.5.19) BURADA OLCULUR. 2.',
    '| H1-K5 | IKA OTONOM FIZIK SURUSU - YER GERCEGI ROTA | BASARI 45/45 · HARITA 15/15 | >= 12/15 HARITA × 3 TOHUM | GECTI |',
    "| H1-K5 | AYNI - URETIM BORU HATTI ROTA (KARE-BAZLI) | BASARI 0/15 · HARITA 0/5 KOSULAN (KALAN 10 HARITA K3'TE NO ROUTE → BASARISIZ SAYILIR) | >= 12/15 HARITA × 3 TOHUM | DUSTU |",
    '| YER GERCEGI | 45 | 45 · 45 | 0 · 0 | 45 | 45 | 0 | 45/45 | 15/15 | >= 12/15 | GECTI |',
    'ESIK DEGISTIRILMEDI ; BUNUN YERINE MEKANIZMANIN ASIL VAADI, BILESIM GORULMEDEN YAZILAN IKI YENI OLCUTLE SINANDI VE GECTI : H1A (AZINLIK SERIT→SERIT SIZINTISI 0/0 ) VE H1B (KESIN AZALMA).',
    "H1C (SINIFLANDIRILAMAYAN YAYIMLANMIS CEVRILME = 0) DAMGALANMADI VE BU RAPORUN KENDI KURALINCA ACIK SAYILIR. (12 EYLUL 2026'DA GECERSIZLESTI - D-462 A2; ESKI METIN SILINMEDI.) H1C 3 EYLUL 2026'DA KOSULDU VE GECTI (D-419 §3; ACIK KALEMLER.MD KALEM #24 KAPANDI ): AYNI MODEL/KUME/TOHUMLARLA ( H1C MODEL SHA256 = URETIM .PT 1D1CACA6... ; TOHUM 7 VE 42; Σ = 2; KARE BASINA 4 KOPYA) SINIFLANDIRILAMAYAN YAYIMLANMIS CEVRILME 0/0 OLCULDU - SINIFLAR YAYIMLANANI TAM ORTER (TOHUM 7: NO ROUTE 6 + COGUNLUK 1 = 7 ; TOHUM 42: NO ROUTE 9 + COGUNLUK 2 = 11 ; UCUNCU SINIF HIC OLUSMADI).",
    'OLCULEMEDI ≠ GECTI . > → 10 EYLUL 2026 (SENTETIK, §3.3.3.2): IKA YARISI MUJOCO FIZIGINDE KOSULDU - YER GERCEGI ROTAYLA 45/45 KOSUM HB 2×2 M KARESI ICINDE BITTI, TEMASLI KOSUM 0, VARIS MESAFESI MEDYAN 0,2 M.',
    "BUGUN: TUREVIN SHA256 'SI YER TUTUCU DEGILSE VE DISKTEKI DOSYANIN OZETIYLE BIREBIR AYNIYSA GECTI; KAYITSIZ/YABANCI .ENGINE RED ; KAYNAK SHA256 URETIM .PT OZETIYLE ESLESMEZSE TUREV YETIM SAYILIR VE RED .",
    "ON KAYIT KURALI ≤ 5/260 GECTI . ⚠ KOSUM CPU EP ILEDIR; TENSORRT MOTORUNUN KENDI DENKLIGI JETSON'DA AYRICA OLCULMELIDIR → 6 EYLUL 2026'DA JETSON ORIN NANO'DA OLCULDU VE DUSTU (D-431; 12 EYLUL'DE RAPORA ISLENDI, D-462 A3) - ASAGIDAKI SATIR. - FP16 KARAR DENKLIGI: ZARAR YONU (FP32 DOGRUYKEN FP16 YANLIS SERIT) 0 → GECTI; KARAR UYUSMASI 0,9968 (ESIK 0,98) → GECTI. - 🔴 TENSORRT .ENGINE ↔ .PT KARAR DENKLIGI (JETSON ORIN NANO, 6 EYLUL 2026) - DUSTU.",
    'OLCULEN: F1 ZARAR YONU 0 ( GECTI ) · F2 KARAR UYUSMASI 0,99526 (N = 633, ESIK 0,98 → GECTI ) · D-303 ORANSAL UYUSMAZLIK 3/126 = %2,38 > %1,92 (5/260) → DUSTU .',
    '| K0 | KORLUK YOK - MODEL BOS MASKE URETMIYOR, FIGURDE ZEMIN GORUYOR | FIGUR > 0 · BOS MASKE YOK | FIGUR ZEMIN %2,66 · HAM BOS 0/67 · COPY-PASTE BOS 0/393 | GECTI |',
    '| K1 | ROTA URETILEN KARE SAYISI | >= 230 / 260 | 256/260 | GECTI |',
    '| K2 | ROTANIN MOLOZDAN GECMESI | ≤ %15 | 6/256 = %2,34 | GECTI |',
    '| K3 | AGIR MOLOZ TEMASI | ≤ %3 | 0/256 = %0,00 | GECTI |',
    '| K4 | ARENA DISINA TASMA | ≤ %5 | 2/256 = %0,78 | GECTI |',
    '| K5 | BARIYER KESISIMI (POPULASYON) | = 0 PX , HER OLCULEBILIR KAREDE | 0/178 OLCULEBILIR KARE · TOPLAM 0 PX | GECTI |',
    '| K5A | BARIYER KESISIMI - ACILI BARIYER KUMESI | K5 ILE BIREBIR AYNI | 0/176 OLCULEBILIR KARE · 0 PX | GECTI |',
    '| K6 | YANLIS GUZERGAH (ROTA CIZGISININ YER GERCEGI SINIF 0 USTUNDEKI PAYI >= 0,90 VE SINIF 1 USTUNDE 0 WAYPOINT) | ≤ %5 | 2/256 = %0,78 | GECTI |',
    "| K7 | YAYINLANAN SERIT DOGRULUGU - 260'IN TAMAMI DEGIL, SERIT ETIKETI BILINEN 88 KARELIK ALT KUME UZERINDE | DOGRULUK >= %95 VE PAYDA >= 80/88 | 84/85 = %98,82 (85 KAREDE ROTA URETILDI, 84'U DOGRU SERITTE; YANLIS: SA 000090.JPG 2→3) | GECTI |",
    'TOPLU VERDIKT: 10/10 KAPI GECTI .',
    '| GERCEK KARE ZEMIN KAPLAMASI | TUVAL PAYDASI 0,2346 · ICERIK PAYDASI 0,4171 | BAGIMSIZ (MODELSIZ) TAHMINE GORE GERCEK SURULEBILIR ORAN %47-52\'DIR; V36 O ARALIGIN ALTINA DUSTU . YANI BU TERFI "DAHA AZ GORUYOR" YONUNDEDIR - KABUL EDILEN BEDEL BUDUR |',
    "BU MATRIS YONERGENIN ISTEDIGI MATRIS DEGILDIR VE SATIRI TEK BASINA KAPATMAZ: (I) KUME ARENA DEGIL, EGITIM UCUSLARI 0037/0039'DAN RASTGELE %15'TIR ( DATASET/DJI V7/IMAGES/VAL , N = 73) VE YALNIZ ERKEN DURDURMA ICINDIR ( CONFIG/MODEL REGISTRY.JSON → EGITIM ); (II) ORNEK DUZEYIDIR, PIKSEL DUZEYI DEGILDIR; (III) SINIF EKSENI MODELIN IKI SINIFIDIR - HB PEDI VE INCE BARIYER MODEL SINIFI DEGILDIR (§3.3.4.1.1); (IV) CALISMA NOKTASI URETIMDEN FARKLIDIR (URETIM CONF 0,30, 65 KABUL DENETCISI.PY:113 ); (V) DIZIN .GITIGNORE ( RUNS/ ) ILE DEPO DISIDIR, MAKINE OKUNUR MATRIS DOSYASI YOKTUR.",
    'COMMAND ACK YALNIZ YETKILI BILESEN KUMESINDEN KABUL EDILIR (K-3, ACK BASABILEN BILESENLER , IHA KOMUT ALICI.PY:523-542 ): MAVLINK BELIRTILMEMIS COMPONENT (= 0, :111 ) · MAV COMP ID AUTOPILOT1 · TARGET COMPONENT .',
    "KABUL EDILEN BEDEL (D-422 §4, IKI BAGIMSIZ CURUTUCU): SOGUK ALICIDA (OFSET OGRENILMEMIS, SALDIRGAN TEK KONUSAN) YAKALAMA YASI TAVANI 1800 S'DEN SINIRSIZA CIKTI, SALDIRGANA MALIYET 3 → 7 PAKET; MESRU YKS BIR KEZ KONUSUNCA 2 SAAT VE 1 GUN BAYAT CERCEVELER 40/40 REDDEDILIR.",
    '| VERI HIZI (BIT/S, PAKET/S) | RF HATTINDA OLCULEMEDI. HICBIR BETIK OLCMEZ ( SIK RF OLC.PY RTT VE KAYIP VERIR); 10 EYLUL (T216): SIK RF OLC.PY ARTIK BAYT/S, BIT/S VE PAKET/S SAYAR ( VERI HIZI ALANI; KILIT TESTS/TEST FAZ B SIK RF OLC.PY , 13 TEST, SAYAC MUTASYONU YAKALANDI) VE YAZILIM DUZENEKLERINDE OLCULDU - §3.3.4.3.3 "10 EYLUL" TABLOSU (UDP LOOPBACK / TCP-SERI KOPRUSU: IKA GO KADANSINDA ≈ 4,0 PKT/S · ≈ 322 B/S TX, PARASUT KADANSINDA ≈ 5,0 PKT/S · ≈ 403 B/S TX; KAYIP 0/200). BUNLAR KADANS YUKUDUR, HAT KAPASITESI DEGILDIR VE RF DEGILDIR . §3.3.4.3.2\'DEKI 4 PKT/S ( IKA GO ) VE 5 PKT/S ( PARACHUTE ) TASARIM ORANLARI BU OLCUMLE LOOPBACK\'TE OLUMLU_HUKUM ; "57600 BAUD\'DA 200 B CERCEVE + ACK < 100 MS" ( KARAR SOZLESMESI.PY:2075-2076 KARAR SOZLESMESI.PY:2089-2090 ) HALA TASARIM TAHMINIDIR - RF\'TE OLCULEMEDI |',
    '| A3 | TENSORRT .ENGINE DENKLIGI | NANO VENV38\'DE TENSORRT MODULU YOK; .ENGINE BU KART ICIN OLCULEMEDI → 6 EYLUL 2026 (D-431; 12 EYLUL\'DE ISLENDI, D-462 A3): KART ORIN NANO DEVELOPER KIT 4 GB CIKTI, TENSORRT 10.16.2 APT ILE KURULDU, FP16 ENGINE DERLENDI VE DENKLIK OLCULDU : F1 0 · F2 0,99526 GECTI, D-303 ORANSAL 3/126 = %2,38 > %1,92 → DUSTU ( RESULTS/JETSON 20260906/JETSON LOG 20260906/ENGINE KARAR DENKLIGI.JSON ). KALEM ARTIK "OLCULEMEDI" DEGIL "DENKLIK DUSTU" TUR: ENGINE URETIME ALINMADI, UCUS .PT ILE; T66 KABUL KUMESIYLE TEKRAR OLCUMU ACIK KALIR |',
    '1,58/1,33 FPS · ESIK 0,61 -> GECTI; ONNX KOLU HATA (CUDAERRORNOKERNELIMAGEFORDEVICE).',
    '| K1 256/260 · K2 6/256 · K3 0/256 · K4 3/256 · K6 3/256 · K5 0/178 · K5A 0/176 · K7 84/85 (%98,82) · K8 GECTI (0,0444) | SCRIPTS/OLCUM/RESULTS/T63/T199 OZDENETIM KABUL VERDIKT.JSON | SCRIPTS/OLCUM/65 KABUL DENETCISI.PY | 2026-08-28 21:25 |',
    '| K0 FIGUR ZEMIN %2,66 · HAM BOS 0/67 · CP BOS 0/393 | AYNI DOSYA ( OLCUM.K0 ) | 65 KABUL DENETCISI.PY | 2026-08-28 |',
    '| TERFI ANI: K1 255/260 · K2 %5,88 · K3 %0,39 · K4 %1,57 · K5 0/172 · K6 %2,75 | SCRIPTS/OLCUM/RESULTS/T63/GECE V7A KABUL VERDIKT.JSON · CONFIG/MODEL REGISTRY.JSON → METRICS | 65 KABUL DENETCISI.PY | 2026-08-26 |',
    '| ESIKLER (K1 >= 230 · K2≤%15 · K3≤%3 · K4≤%5 · K6≤%5 · K7 >= %95 VE PAYDA >= 80) | SCRIPTS/OLCUM/65 KABUL DENETCISI.PY:116-140 ( ESIK ) | ON KAYIT REVIEW LOG.MD D-107 | SONUC GORULMEDEN YAZILDI |',
    "| URETIM KIPI (BUGUNKU ZINCIR): K1 256/260 · K2 6/256 · K3 0/256 · K4 2/256 · K6 2/256 · K5 0/178 · K5A 0/176 · K7 84/85 · K8 0,0444 · VERDIKT TRUE | SCRIPTS/OLCUM/RESULTS/T63/T150 BAGLAMA V36 KABUL VERDIKT.JSON ( OLCUM. , GECTI , VERDIKT ) | SCRIPTS/OLCUM/65 KABUL DENETCISI.PY (T150 HEDEF BAGLAMASI, D-386) | 2026-09-01 23:30 · 5 EYLUL'DE JSON ILE YENIDEN KARSILASTIRILDI, FARK YOK |",
    '| IKA SURUCU KABUL TURU K1-K6 6/6 GECTI (SAHTE SURUCU, EXIT 0) · GAZEBO GZ YOK → K1/K3/K4/K6 DUSTU (EXIT 1) · GERCEK → DONANIM YOK (EXIT 2) | RESULTS/FDR SPRINT 20260910/H3/IKA SURUCU KABUL SAHTE.TXT + .JSON · IKA SURUCU KABUL GAZEBO GZ YOK.TXT · IKA SURUCU KABUL GERCEK DONANIM YOK.TXT | SCRIPTS/IKA SURUCU KABUL.PY --SURUCU SAHTE / GAZEBO / GERCEK | 2026-09-10 |',
    'ANAYASA MADDE 14: HER GOREVDEN SONRA BU KAPI KOSULUR; DUSERSE GOREV GERI ALINIR.',
    'GENEL KAPI (MADDE 14): GECTI - KOL1 15/15 - KOL2 SERIT 15/15',
    'YANLIS MODELLE OLCTURDUM. OLCUT SONUCTAN SONRA SECILIRSE RASYONALIZE EDILIR.',
    'OLCEN ARAC OLCULDU: ULTRALYTICS PREDICTOR\'I ILK CAGRIDA KURULUR, SONRAKI CAGRININ HALF=TRUE \'SU SESSIZCE YOK SAYILIR - IKI KOL DA FP32 KOSMUSTU. "GECTI", HICLIGIN OLCUMUYDU." SINIFIN ADI KAYDA GECTI: FARKSIZLIK ≠ DENKLIK .',
    'KABUL ZINCIRININ KENDI VAKUMU → K8 DOGDU. 2026-08-28\'DE V37 ADAYI K0\'DAN K7\'YE ZINCIRIN TAMAMINI GECTI (K1 258/260, K7 87/87 = %100,0) VE "URETIME ALINIR" VERDIKTI ALDI.',
    "OLCULDU (D-312): KABUL KUMESININ %54'U (105/193) BOYLEDIR VE SERIT AYRISMASININ %100'U ORADAN GELIR.",
    '| ONCEDEN YAZILMIS KABUL KAPISI KOSULDU - JETSON (FPS >= 0,61 → GECTI ) · FS-I6 (FAILSAFE KOLU → DUSTU ) | 2/9 |',
    "| EKIPMANIN KENDI KABUL OLCUMU YOK - RPI HQ (KAMERA HICBIR GUN BAGLANMADI; 6 EYLUL'DE ACILAN KOPRU OLCUMU JETSON'UNDUR, KAMERANIN DEGIL) · IKA EKIPMANLARI (HENUZ SECILMEDI) | 2/9 |",
    "| JETSON NANO 4GB JETSON ORIN NANO DEVELOPER KIT 4 GB (6 EYLUL'DE KARTLA OLCULDU - D-431) | PT VE ONNX ICIN P50 VE P95 FPS >= 0,61 (TURETIMI §4.8.2.3) | OLCULEMEDI - 5 EYLUL'DE JETSON ARACA TAKILMADI (D-426 §4) → 6 EYLUL OLCUM (D-431): GENEL KAPI KARTTA 15/15 · 15/15 ; JETSON FPS.PY 120 ORNEK: PT 1,35/1,06 FPS · ENGINE 1,58/1,33 FPS >= 0,61 → GECTI ; 10 DK SUREKLI 900 ORNEK, GPU ≤ 56,3 °C; ONNX HATA ( CUDAERRORNOKERNELIMAGEFORDEVICE ) → ONNX KOLU BU KARTTA GECMEDI, OLCULEMEDI; ENGINE↔PT DENKLIGI D-303 ORANSAL DUSTU → UCUS .PT ; KAMERA KOPRUSU DOSYA KAYNAGIYLA ACILDI. OLCULEMEDI: CSI KAMERA (BAGLI DEGIL), PIXHAWK MAVLINK KAPISI ( --KURU : [YOK] /DEV/TTYACM0 ). KANIT RESULTS/JETSON 20260906/ |",
    '| H1-K5 IKA OTONOM SURUS - YER GERCEGI | 45/45 (HARITA 15/15) | >= 12/15 HARITA | GECTI |',
    "ASAGIDAKI KABUL KUMESI SENTETIKTIR VE FARKLI ISIK ACISI / GOLGE CESITLILIGI ICERMEZ; (12 EYLUL 2026'DA DUZELTILDI - D-462 E; ESKI METIN SILINMEDI.) ASAGIDAKI KABUL KUMESI (N = 260 KADRAJ) SENTETIKTIR VE ISIK/GOLGE EKSENINDE BOLUNMEMISTIR; AMA AYRI BIR SENTETIK ISIK/GOLGE KESITI OLCULMUSTUR - T213-A MUJOCO RENDER VARYANTLARI, URETIM MODELI V36 ILE: ALCAK GUNES + GOLGE (V2) K3 0/15 , GOLGESIZ TABAN CIZGISI V1 3/15 ; GOLGE HTAB ENGEL ORANINI 0,1314 → 0,2380 CIKARDI (TAM TABLO, ISIK PARAMETRELERI VE YERLESIM SINIRI BOLUM 3 §3.3.4.2.8 (A); ARTEFAKT RESULTS/FDR SPRINT 20260910/H1/K3B/ ).",
    '| K0 | KORLUK YOK - BOS MASKE URETMIYOR | FIGUR ZEMIN > 0 · BOS MASKE 0 | FIGUR ZEMIN %2,66 · RAW 0/67 BOS · COPY-PASTE 0/393 BOS | GECTI |',
    '| K1 | ROTA URETILEN KARE | >= 230/260 | 256/260 | GECTI |',
    '| K2 | ROTANIN MOLOZDAN GECMESI | ≤ %15 | 6/256 (%2,3) | GECTI |',
    '| K3 | AGIR MOLOZ TEMASI | ≤ %3 | 0/256 | GECTI |',
    '| K4 | ARENA DISINA TASMA | ≤ %5 | 2/256 | GECTI |',
    '| K5 | BARIYER KESISIMI (DIK NUFUS) | = 0 PX | 0 PX · OLCULEBILIR KARE 178 / BARIYERLI 181 | GECTI |',
    '| K5A | BARIYER KESISIMI ( ACILI NUFUS, T189) | = 0 PX | 0 PX · OLCULEBILIR KARE 176 / BARIYERLI 185 | GECTI |',
    '| K6 | YANLIS GUZERGAH | ≤ %5 | 2/256 (%0,78) - SA 000013 , SA 000090 | GECTI |',
    '| K7 | YAYINLANAN SERIT REFERANSLA AYNI MI | DOGRULUK >= %95 VE ROTA URETILEN >= 80/88 | 84/85 = %98,8 · ROTA URETILEN 85/88 | GECTI |',
    '| F2 · KARAR UYUSMASI | >= 0,98 | 631/633 = 0,9968 | GECTI |',
    'FP16 PAYI BU YUZDEN KAPANMADI . ⚠ SINIR: S KUMESI T66 KABUL KUMESI DEGILDIR VE D-303 T66 ICIN YAZILMISTI; 3 UYUSMAZLIGIN UCUNDE .PT DE YANLISTIR (IKI KOL YER GERCEGINDE 52/126).',
    'DUZELTME: CERCEVE TAMPON TAVANI = 64 1024 SOZLESMEYE GIRDI (MADDE 16 - TEST BU SABITI ICE AKTARIR , YENIDEN YAZMAZ), FRAMEREADER ONCE SUZER, SONRA ATAR (TERSI OLSAYDI MESRU BIR CERCEVENIN PESINDEKI DEV COP O CERCEVEYI DE YUTARDI; KAPI S5D BUNU KILITLER), ATILAN BAYT SAYACI GOZLEMLENEBILIR KILAR.',
    'KABUL GEREKCESI OLCULDU: MESRU YKS BIR KEZ KONUSUNCA DELIK KAPANIR (2 SAAT VE 1 GUN BAYAT ICIN 40/40 RED, ESKI VE YENI KODDA); DELIK ZATEN VARDI (≤ 10 DK BAYAT CERCEVE ESKI KODDA 3.',
    'ROTA BUL: [ICERIK YOK LETTERBOX SUPHESI: ICERIK=NONE ILE TUVAL LETTERBOX GORUNUMLU - ZEMIN SAGLAMLIK KAPISI BU PAYDADA OLU OLABILIR; CAGIRAN ICERIK GECIRMELI]',
    '| 2 | JETSON NANO GERCEK FPS → OLCULDU 6 EYLUL (D-431) - KART ORIN NANO DEVELOPER KIT 4 GB | 5 EYLUL: JETSON ARACA TAKILMADI (D-426 §4) → 6 EYLUL KARTTA: PT 1,35/1,06 · ENGINE 1,58/1,33 FPS (120 ORNEK), 10 DK 900 ORNEK, ONNX HATA | 6 EYLUL | >= 0,61 FPS P50 VE P95 → GECTI ; ESIK GEVSETILMEDI. SINIR: KAMERA BAGLI DEGIL, KARELER DISKTEN ( RESULTS/JETSON 20260906/JETSON FPS 20260906 ORIN NANO/OZET.JSON ) |',
    "| 20 | URETIM MODELIYLE SIMULASYONDA ROTA TESPITI VE UCTAN UCA SURUS (H1-K3, H1-K5) | OLCULDU VE DUSTU (10 EYLUL 2026): ROTA TESPITI MOZAIK 6/15, KARE-BAZLI 1/15; SURUS URETIM MODELI 9/45, URETIM BORU HATTI 0/15 (YER GERCEGI 45/45 GECTI). ESIK GEVSETILMEDI; SIM'E OZEL EGITIM YAPILMAZ (ON KAYIT §5.2). TESHIS: KAREYE GORELI SERIT ETIKETI, KB ILE HB AYNI KAREDE GORULMUYOR (§3.3.3.2) | - (SONUC RAPORA OLDUGU GIBI GIRER; URETIM KODU KARARI MIMARIN) | >= 12/15 |",
    '| 4 | KAMERA KOPRUSU K5 KAPISI API ADI DENETLEMIYOR (YALNIZ SOZ DIZIMI) | PY3.6 UYUMU SESSIZCE BOZULABILIR | D-407 |',
    "| 30 | K7 ALT KUME GEREKCESI: KABUL KUMESININ %54'U (105/193) KOTU KOSULLU | CONTRACTS.MD §12.1 · CONFIG/K7 IYI KOSULLU KUME.JSON (88 KARE) | D-312 OLCUMU | 2026-08-27 |",
    '| 50 | 5 EYLUL KABUL TUTANAGI: ARDUCOPTER V4.5.7 (2A3DC4B7) · FRAME: QUAD/X · U-BLOX 1 HW: 000A0000 SW: ROM SPG 5.10 · RCINPUT: DECODING IBUS(1) · PREARM PIL/EMNIYET SATIRLARININ KAYBOLMASI · STARTING/FINISHED MOTOR TEST | REVIEW LOG.MD D-426 §1 (SATIR 29819-29829) | MISSION PLANNER MESSAGES SEKMESI, BIREBIR YAPISTIRMA (OLCUM); 4/4 YON, SIK, MOD ANAHTARI BEYAN | 2026-09-05 |',
))

# ─────────────────────────────────────────────────────────────────────────────
# Kilitlenen yüzeyler
# ─────────────────────────────────────────────────────────────────────────────

def b3(bas, son=None):
    return kesit(oku(B3), bas, son)


def b4(bas, son=None):
    return kesit(oku(B4), bas, son)


# T244'ün kilitlediği YÜZEYLER — beyaz liste ve çelişkili ikinci hüküm denetimi
# hepsinde TOPLUCA koşar (yeni bir yüzey eklenince kapı da kendiliğinden kapsar).
def kilitli_yuzeyler():
    return (("3.3.1.1.8", b3("##### 3.3.1.1.8 ", "##### 3.3.1.1.9 ")),
            ("3.3.3.2", b3("#### 3.3.3.2 ", "#### 3.3.3.3 ")),
            ("3.3.4.1.7", b3("##### 3.3.4.1.7 ", "##### 3.3.4.1.8 ")),
            ("3.3.4.2.1", b3("##### 3.3.4.2.1 ", "##### 3.3.4.2.2 ")),
            ("3.3.4.2.8", b3("##### 3.3.4.2.8 ", "#### 3.3.4.3 ")),
            ("3.4.1", b3("### 3.4.1 ", "### 3.4.2 ")),
            ("4.0", b4("## 4.0 ", "## 4.1 ")),
            ("4.1.3", b4("### 4.1.3 ", "## 4.2 ")),
            ("4.4", b4("## 4.4 ", "## 4.5 ")),
            ("4.7", b4("## 4.7 ", "## 4.8 ")),
            ("4.8 girişi", b4("## 4.8 ", "### 4.8.1 ")),
            ("4.8.3", b4("### 4.8.3 ", "### 4.8.4 ")),
            ("4.8.4", b4("### 4.8.4 ", "## 4.9 ")),
            ("4.13.3", b4("### 4.13.3 ", "#### 4.13.3.1 ")))


class T0_CapaDosyalar(unittest.TestCase):
    def test_capa_dosyalar_var(self):
        for p in (B3, B4, YONERGE, KAYIT, ENGINE_JSON, H1C_JSON, INIS, PARAM):
            self.assertTrue(p.is_file(), p)
        for ad in ("taban_15harita.json", "v1_15harita.json", "v2_15harita.json",
                   "v3_15harita.json", "v1_15harita_yerlesim_d441.json", "ozet_k3b.json"):
            self.assertTrue((K3B / ad).is_file(), K3B / ad)

    def test_cizme_isareti_beyaz_liste(self):
        """Kilitli yüzeylerde beyaz listede OLMAYAN çizme işareti kalmamalı."""
        for ad, m in kilitli_yuzeyler():
            self.assertEqual([], cizme_artiklari(m), ad)

    def test_celiskili_ikinci_hukum_HICBIR_yuzeyde_yok(self):
        """D-461 (d): SÖZLÜK katı — 8 ifadenin hiçbiri iki belgede geçmemeli.

        ⚠ BU KAPI TEK BAŞINA D-463 (b)'yi KAPATMAZ. Ölçüldü (D-466): tarama iki
        bölümün tamamını gezse de yalnız bu SONLU sözlükle eşleştiği için eş
        anlamlı ikinci hüküm ("Revize edilmiş kabul kapısı") KAÇIYORDU. D-463
        (b) daraltması `T9_KabulOlcutuBicimiKilidi` sınıfındaki YAPISAL kilitle
        yapılır; orada kapsama da SINIR da mutasyonla ölçülüdür. Bu kapı yalnız
        ek bir kat olarak durur.
        """
        for ad, m in kilitli_yuzeyler():
            self.assertEqual([], celiskili_ikinci_hukum(m), ad)
        for p in (B3, B4):
            self.assertEqual([], celiskili_ikinci_hukum(oku(p)), p.name)


class T1_MavlinkTekYazarKilidi(unittest.TestCase):
    def _b(self):
        return b3("##### 3.3.1.1.8 ", "##### 3.3.1.1.9 ")

    def test_T1_uc_surecte_de_kodlu_yazili(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("kilit ÜÇ SÜREÇTE DE KODLUDUR", 1),
            ("tests/test_seri_pixhawk_kilidi.py", 1),
            ("13/13", 1),
        )))
        # Eski "açık kalem" hükmü YALNIZ çizili olabilir: ayıklanmış metinde olmamalı
        self.assertEqual([], yasaklar(m, ("açık kalemdir", "hâlâ kabul eder")))

    def test_T1b_atiflar_gercek_kod_satirlariyla(self):
        """Rapordaki `dosya:satır` atıfları kaynakta gerçekten o satırda."""
        m = tekhat(self._b())
        inis = oku(INIS).splitlines()
        for ad, satir in (("SERI_PIXHAWK_BILEREK_BAYRAGI", 101),
                          ("def seri_pixhawk_yolu_mu", 107),
                          ("def seri_pixhawk_kilit_metni", 122),
                          ("def seri_pixhawk_bayragini_ekle", 129),
                          ("def seri_pixhawk_kilidini_uygula", 136)):
            self.assertTrue(inis[satir - 1].startswith(ad), (ad, satir, inis[satir - 1][:40]))
        self.assertIn("COMMS/INIS_KANITI.PY:101-143", m)
        for dosya, ekle, uygula in (
                (KOK / "codes" / "rpi_inference.py", 2569, 2728),
                (KOK / "comms" / "iha_inis_yayinci.py", 432, 475),
                (KOK / "comms" / "iha_komut_alici.py", 855, 899)):
            satirlar = oku(dosya).splitlines()
            self.assertIn("seri_pixhawk_bayragini_ekle", satirlar[ekle - 1], (dosya.name, ekle))
            self.assertIn("seri_pixhawk_kilidini_uygula", satirlar[uygula - 1], (dosya.name, uygula))
            self.assertIn(":{}".format(ekle), m, (dosya.name, ekle))
            self.assertIn(":{}".format(uygula), m, (dosya.name, uygula))

    def test_T1c_6_eylul_de_kosulmadi_gecti_yazilmaz(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("6 Eylül'de de", 1),
            ("jetson_baslat.sh --kuru", 1),
            ("çıkış 3", 1),
        )))
        n = tekhat(m)
        self.assertIn("OLCULEMEDI", n)
        self.assertNotIn("MAVLINK_DOGRULA 3/3 GECTI", n)
        self.assertEqual([], celiskili_ikinci_hukum(m))


class T2_H1cDamgasi(unittest.TestCase):
    def _b(self):
        return b3("##### 3.3.4.1.7 ", "##### 3.3.4.1.8 ")

    def test_T2_h1c_kosuldu_ve_gecti(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("H1c 3 Eylül 2026'da KOŞULDU ve GEÇTİ", 1),
            ("H1 %40 hükmü DÜŞTÜ olarak KALIR", 1),
            ("tests/test_p5_h1c_damgasi.py", 1),
            ("23/23", 1),
        )))
        self.assertEqual([], yasaklar(m, ("damgalanmadı",)))
        self.assertEqual([], celiskili_ikinci_hukum(m))

    def test_T2b_sayilar_artefakttan(self):
        d = json.loads(H1C_JSON.read_text(encoding="utf-8"))
        self.assertTrue(d["H1c"])
        self.assertFalse(d["H1_ozgun"])
        m = tekhat(self._b())
        for tohum in ("7", "42"):
            t = d["tohumlar"][tohum]
            self.assertEqual(0, t["h1c_siniflandirilamayan"], tohum)
            siniflar = t["h1c_yayin_cevrilme_siniflari"]
            self.assertEqual(t["yayimlanan_cevrilme"], sum(siniflar.values()), tohum)
            for ad, sayi in siniflar.items():
                self.assertIn("{} {}".format(katla(ad), sayi), m, (tohum, ad))

    def test_T2c_esik_TEKLIGI_rakip_esik_yok(self):
        """D-461: ön kayıtlı ölçüt metinde TAM BİR KEZ; ikinci/gevşek eşik yasak."""
        n = tekhat(self._b())
        self.assertEqual(1, n.count("HAM CEVRILMENIN %40'I"), "H1 ölçütü tam bir kez geçmeli")
        oranlar = set(re.findall(r"HAM CEVRILMENIN %(\d+)", n))
        self.assertEqual({"40"}, oranlar, "rakip eşik (ikinci yüzde) var")


class T3_EngineDenkligi(unittest.TestCase):
    def _kunye(self):
        return b3("##### 3.3.4.2.1 ", "##### 3.3.4.2.2 ")

    def _a3(self):
        satir = [s for s in oku(B3).splitlines() if s.startswith("| A3 |")]
        self.assertEqual(1, len(satir), "§3.4.1 A3 satırı tek olmalı")
        return satir[0]

    def _kanit(self):
        return b3("### Model künyesi ve denklik", "### Zamanlama ve gecikme")

    def test_T3_engine_sha_kayit_defteriyle(self):
        d = json.loads(KAYIT.read_text(encoding="utf-8"))
        turev = d["profiles"]["competition"]["turevler"]["navitas_seg_v36_best_512_fp16.engine"]
        sha = turev["sha256"]
        self.assertNotEqual("DERLENINCE_YAZILIR", sha)
        self.assertEqual(d["profiles"]["competition"]["sha256"], turev["kaynak_sha256"])
        n = tekhat(self._kunye())
        self.assertIn(sha.upper(), n, "künye tablosu engine sha'sını taşımıyor")
        self.assertIn(sha[:8].upper(), tekhat(self._kanit()), "Kanıt dizini engine sha'sız")

    def test_T3b_yer_tutucu_hukmu_yalniz_cizili(self):
        for ad, m in (("künye", self._kunye()), ("A3", self._a3()), ("kanıt", self._kanit())):
            self.assertEqual([], yasaklar(m, ("DERLENINCE_YAZILIR",)), ad)

    def test_T3c_d303_dustu_uc_yerde_de_olumluya_CEVRILMEMIS(self):
        d = json.loads(ENGINE_JSON.read_text(encoding="utf-8"))
        h = d["hukum"]
        self.assertEqual("DUSTU", h["D303_S"]["durum"])
        self.assertEqual(3, h["D303_S"]["uyusmazlik"])
        self.assertEqual(126, h["D303_S"]["n"])
        self.assertEqual("GECTI", h["F1"]["durum"])
        self.assertEqual("GECTI", h["F2"]["durum"])
        for ad, m in (("künye", self._kunye()), ("A3", self._a3()),
                      ("kanıt", self._kanit()), ("§4.8.3", b4("### 4.8.3 ", "### 4.8.4 "))):
            n = tekhat(m)
            self.assertIn("3/126", n, ad)
            self.assertIn("DUSTU", n, ad)
            # Ölçümün YANINDAKİ hüküm denetlenir: her "3/126" geçişinin ±140
            # karakterlik penceresi "DÜŞTÜ" taşımalı ve olumlu hükme çevrilmemiş
            # olmalı. Bölümün BAŞKA yerindeki bir DÜŞTÜ bu pencereyi doyuramaz
            # (kapının kendi mutasyon bulgusu MZ3: tek satıra indirilmiş metinde
            # komşu cümledeki DÜŞTÜ, çizilmiş hükmü örtüyordu).
            yerler = [mm.start() for mm in re.finditer(r"3/126", n)]
            self.assertTrue(yerler, ad)
            for i in yerler:
                pencere = n[max(0, i - 140):i + 140]
                self.assertIn("DUSTU", pencere, (ad, pencere))
                self.assertNotIn("OLUMLU_HUKUM", pencere, (ad, pencere))
            self.assertEqual([], celiskili_ikinci_hukum(m), ad)

    def test_T3d_f2_ve_esik_artefaktla(self):
        d = json.loads(ENGINE_JSON.read_text(encoding="utf-8"))
        f2 = d["hukum"]["F2"]["uyusma"]
        n = tekhat(self._kunye()) + tekhat(b4("### 4.8.3 ", "### 4.8.4 "))
        self.assertIn(str(f2).replace(".", ","), n, "F2 uyuşması artefakttan yazılmamış")


class T4_EkipmanKabulTablosu(unittest.TestCase):
    def _b(self):
        return b4("## 4.4 ", "## 4.5 ")

    def _ekipman_satirlari(self):
        """`| ekipman | koşulacak kabul kapısı | bugünkü sonuç |` tablosunun veri satırları."""
        tablo = kesit(self._b(), "| ekipman | koşulacak kabul kapısı | bugünkü sonuç |")
        satirlar = []
        for s in tablo.splitlines()[2:]:          # başlık + hizalama satırı atlanır
            if not s.startswith("|"):
                break
            satirlar.append(s)
        return satirlar

    def test_T4_giris_olculen_olculemeyen_sayimi(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("KISMEN — ekipman kabul testleri bugün tamamlanmış DEĞİLDİR", 1),
            ("9 ekipman", 1),
            ("2/9", 2), ("4/9", 1), ("1/9", 1),
        )))
        # Eski "hiçbir sayı yoktur" hükmü yalnız çizili olabilir
        self.assertEqual([], yasaklar(m, (
            "hiçbir ekipmanın fiziksel kabul testi yapılmadı",
            "Sağ sütunda bugün hiçbir sayı yoktur",
            "Donanım kutusu\n5 Eylül 2026'da açılacak",
        )))
        self.assertEqual([], celiskili_ikinci_hukum(m))

    def test_T4b_ekipman_satiri_sayisi_dokuz(self):
        """Girişteki 2+4+1+2 = 9 sayımı, tablonun GERÇEK satır sayısıyla tutmalı."""
        satirlar = self._ekipman_satirlari()
        self.assertEqual(9, len(satirlar), "\n".join(satirlar))
        n = tekhat(self._b())
        toplam = sum(int(a) for a in re.findall(r"\b(\d)/9\b", n))
        self.assertEqual(9, toplam, "giriş sayımı 9'a tamamlanmıyor")
        # her satırın SON hücresi doludur (boş bırakılmaz)
        for s in satirlar:
            son = [h.strip() for h in s.strip().strip("|").split("|")][-1]
            self.assertTrue(son, s)

    def test_T4c_6_eylul_hucreleri_dosya_satirla(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("config/pixhawk/arducopter_fda_20260906.param", 1),
            ("6 Eylül 20:22 dökümü repoda", 1),
            ("Hobbywing Skywalker 60A V2", 2),
            ("6 Eylül: RC failsafe ÖLÇÜLDÜ ve DÜŞTÜ", 1),
        )))
        # pil satırındaki sayı dökümden
        params = {}
        for s in oku(PARAM).splitlines():
            if "," in s and not s.startswith("#"):
                ad, _, deger = s.partition(",")
                params[ad.strip()] = deger.strip()
        self.assertEqual("18.18", params["BATT_VOLT_MULT"])
        self.assertIn("BATT_VOLT_MULT,18.18", normalles(m).replace(" ", ""))

    def test_T4d_olculmeyen_hucreler_GECTI_yazmaz(self):
        n = normalles(self._b())
        for anahtar in ("MAVLINK_DOGRULA.PY 3/3", "MENZIL"):
            for satir in [s for s in n.splitlines() if anahtar in s]:
                self.assertIn("OLCULEMEDI", satir, satir[:90])
        # pervane 6 Eylül'de takıldı ama akım/VIBE hâlâ ölçülemedi
        self.assertIn("TAM YUKTE AKIM VE VIBE HALA OLCULEMEDI", tekhat(self._b()))


class T5_OlculmusAmaOlcuelecekDiyenler(unittest.TestCase):
    def test_T5a_483_engine_olculdu_ve_dustu(self):
        m = b4("### 4.8.3 ", "### 4.8.4 ")
        self.assertEqual([], eksikler(m, (
            ("Jetson Orin Nano'da ÖLÇÜLDÜ ve DÜŞTÜ", 1),
            ("scripts/olcum/170_engine_karar_denkligi.py", 1),
        )))
        self.assertEqual([], yasaklar(m, ("Jetson'da `.engine` ile ölçülecektir",)))
        # eşik TEKLİĞİ (D-461): D-303 kabul ölçütü metinde TAM BİR KEZ, tek değerde
        n = tekhat(m)
        self.assertEqual(1, n.count("5/260"), "D-303 eşiği tam bir kez geçmeli")
        self.assertEqual(1, n.count("%1,92"), "D-303 eşik yüzdesi tam bir kez geçmeli")
        # RAKİP EŞİK YASAĞI: bölümde `≤ n/m = %x,y` biçiminde BAŞKA kabul ölçütü olamaz
        self.assertEqual(["5/260 = %1,92"],
                         re.findall(r"≤\s*(\d+/\d+\s*=\s*%\d+,\d+)", n),
                         "rakip/gevşetilmiş ikinci eşik var")
        self.assertEqual([], celiskili_ikinci_hukum(m))
        self.assertIn("%2,38", n)

    def test_T5b_413_jetson_baslat_ve_tensorrt(self):
        m = b4("### 4.1.3 ", "## 4.2 ")
        self.assertEqual([], eksikler(m, (
            ("kartın kendisinde koştu", 1),
            ("jetson_baslat_kuru.log", 1),
            ("ölçüm **Jetson Orin Nano'da koşuldu**", 1),
        )))
        self.assertEqual([], yasaklar(m, (
            "Jetson'daki ilk koşum ilk kanıt olacak",
        )))
        # systemd kipleri HÂLÂ ölçülemedi — yanlış kapanma yok
        n = normalles(m)
        self.assertIn("HALA KOSULMADI", n)
        self.assertIn("OLCULEMEDI", n)

    def test_T5c_4133_denetim_borcu_acik_kalir(self):
        m = b4("### 4.13.3 ", "#### 4.13.3.1 ")
        self.assertEqual([], eksikler(m, (
            ("6 Eylül'de kartta gerçek koşum yapıldı", 1),
            ("systemd kipleri (`--kur` / `--kapi` / `--dogrudan`) hâlâ KOŞULMADI", 1),
            ("genel kapı **15/15 · 15/15**", 1),
        )))
        self.assertEqual([], yasaklar(m, (
            "5 Eylül'de Jetson'daki ilk gerçek koşum",
            "Jetson'daki ilk koşum ilk kanıttır",
        )))
        n = tekhat(m)
        self.assertIn("BORC ACIK", n)
        self.assertIn("OLCULEMEDI ≠ GECTI", n)


class T6_YonergeHizasi(unittest.TestCase):
    """§4.0 kapsama tablosu ile YONERGE_HARITASI Y-4-M01…M12 durumları HİZALI."""

    KIMLIKLER = tuple("Y-4-M{:02d}".format(i) for i in range(1, 13))
    # Kanonik durum sözcükleri (normalleşmiş); çizili olan ESKİ değer sayılmaz.
    DURUMLAR = ("VAR", "KISMEN", "YOK")

    @classmethod
    def durum_coz(cls, hucre):
        """Bir tablo hücresindeki GÜNCEL durum (çizili eski değer AYIKLANMIŞ).

        Hücrenin İLK durum sözcüğü alınır — sıralama sözcük listesinden değil
        METİNDEKİ KONUMDAN gelir; yoksa gerekçe metnindeki "…var" / "…yok"
        kelimeleri hükmü kaçırırdı (kapının kendi çürütücü bulgusu).
        """
        n = tekhat(hucre)
        bulunanlar = [(m.start(), d) for d in cls.DURUMLAR
                      for m in re.finditer(r"\b{}\b".format(d), n)]
        return min(bulunanlar)[1] if bulunanlar else None

    @classmethod
    def b4_durumlari(cls):
        sonuc = {}
        for s in b4("## 4.0 ", "## 4.1 ").splitlines():
            m = re.match(r"\|\s*`?(Y-4-M\d\d)`?\s*\|(.*)\|\s*$", s)
            if m:
                hucreler = [h.strip() for h in m.group(2).split("|")]
                sonuc[m.group(1)] = cls.durum_coz(hucreler[-1])
        return sonuc

    @classmethod
    def yonerge_durumlari(cls):
        sonuc = {}
        for s in oku(YONERGE).splitlines():
            m = re.match(r"\|\s*`?(Y-4-M\d\d)`?\s*\|(.*)\|\s*$", s)
            if m:
                hucreler = [h.strip() for h in m.group(2).split("|")]
                sonuc[m.group(1)] = cls.durum_coz(hucreler[-1])
        return sonuc

    def test_T6_iki_belge_ayni_kimlikleri_tasir(self):
        self.assertEqual(set(self.KIMLIKLER), set(self.b4_durumlari()))
        self.assertEqual(set(self.KIMLIKLER), set(self.yonerge_durumlari()))

    def test_T6b_durumlar_HIZALI(self):
        a, b = self.b4_durumlari(), self.yonerge_durumlari()
        fark = {k: (a[k], b[k]) for k in self.KIMLIKLER if a[k] != b[k]}
        self.assertEqual({}, fark,
                         "§4.0 ↔ YONERGE_HARITASI çelişkisi (D-462 A6 bir daha oluştu)")

    def test_T6c_m04_m06_kismen_eski_deger_cizili(self):
        satirlar = {s.split("|")[1].strip().strip("`"): s
                    for s in b4("## 4.0 ", "## 4.1 ").splitlines()
                    if re.match(r"\|\s*`?Y-4-M\d\d`?\s*\|", s)}
        for kimlik in ("Y-4-M04", "Y-4-M06"):
            s = satirlar[kimlik]
            self.assertIn("~~YOK~~", s, kimlik)          # eski değer SİLİNMEDİ
            self.assertEqual("KISMEN", self.durum_coz(s.split("|")[-2]), kimlik)


class T7_Durustluk(unittest.TestCase):
    CUMLE = "bu yüzden üretim sayıları sahaya göre İYİMSER ÜST SINIRDIR"

    def _yuzeyler(self):
        return (("§3.3.3.2", b3("#### 3.3.3.2 ", "#### 3.3.3.3 ")),
                ("§4.7", b4("## 4.7 ", "## 4.8 ")))

    def test_T7_cumle_iki_yerde_ve_CIZILMEMIS(self):
        for ad, m in self._yuzeyler():
            self.assertEqual([], eksikler(m, ((self.CUMLE, 1),)), ad)
            # çizili varyant kilidi doyuramaz: ham metinde ~~…~~ içinde olmamalı
            for kalip in (_CIZIK_TILDE2, _CIZIK_TILDE1, _CIZIK_ETIKET):
                for cizik in kalip.findall(m):
                    parca = cizik if isinstance(cizik, str) else cizik[0]
                    self.assertNotIn(normalles(self.CUMLE, cizigi_at=False),
                                     normalles(parca, cizigi_at=False), (ad, parca[:60]))

    def test_T7b_iki_yardim_kod_satiriyla(self):
        gorev = oku(KOK / "simulation" / "mujoco" / "gorev_kosumu.py").splitlines()
        toplayici = oku(KOK / "simulation" / "mujoco" / "sim_karar_toplayici.py").splitlines()
        self.assertIn('kb = H["kb"]', gorev[311])                 # :312
        self.assertIn("ref = [round(float(kb[0]), 2)", gorev[312])  # :313
        self.assertIn("k = ceyrek_tur(yaw)", toplayici[182])      # :183
        self.assertIn("np.rot90(img, k)", toplayici[183])         # :184
        self.assertTrue(any("def ceyrek_tur" in s for s in toplayici))
        for ad, m in self._yuzeyler():
            n = tekhat(m)
            self.assertIn("GOREV_KOSUMU.PY:313", n, ad)
            self.assertIn("SIM_KARAR_TOPLAYICI.PY:183-184", n, ad)
            self.assertEqual([], celiskili_ikinci_hukum(m), ad)


class T8_IsikGolgeKesiti(unittest.TestCase):
    def _b3(self):
        return b3("##### 3.3.4.2.8 ", "#### 3.3.4.3 ")

    def _varyant_satirlari(self):
        """Işık/gölge sonuç tablosunun SATIRLARI: {varyant: [hücreler]}.

        Satır bazlıdır — bölümün başka bir yerindeki aynı sayı bir hücre sapmasını
        DOYURAMAZ (kapının kendi mutasyon bulgusu M8).
        """
        sonuc = {}
        for s in self._b3().splitlines():
            if not s.startswith("| "):
                continue
            hucreler = [h.strip() for h in s.strip().strip("|").split("|")]
            n0 = tekhat(hucreler[0])
            for varyant in ("TABAN", "V1", "V2", "V3"):
                if len(hucreler) == 7 and re.match(r"^{}\b".format(varyant), n0):
                    sonuc.setdefault(varyant.lower(), hucreler)
        return sonuc

    def test_T8_varyant_sayilari_artefakttan(self):
        satirlar = self._varyant_satirlari()
        self.assertEqual({"taban", "v1", "v2", "v3"}, set(satirlar), sorted(satirlar))
        ozet = json.loads((K3B / "ozet_k3b.json").read_text(encoding="utf-8"))
        ozetler = {v["varyant"]: v for v in ozet["varyantlar"]}
        self.assertAlmostEqual(0.1314, ozetler["v1"]["htab_engel_ort"], places=4)
        self.assertAlmostEqual(0.2380, ozetler["v2"]["htab_engel_ort"], places=4)
        for dosya, varyant in (("taban_15harita.json", "taban"), ("v1_15harita.json", "v1"),
                               ("v2_15harita.json", "v2"), ("v3_15harita.json", "v3")):
            o = json.loads((K3B / dosya).read_text(encoding="utf-8"))["ozet"]
            self.assertEqual(15, o["harita_n"], varyant)
            h = satirlar[varyant]
            # sütunlar: varyant | rota bulunan | doğru etiket | engel | geçilebilir | açık yol | durumlar
            self.assertEqual("{}/15".format(o["rota_bulunan"]), tekhat(h[1]), (varyant, "rota"))
            self.assertEqual("{}/15".format(o["dogru_etiket"]), tekhat(h[2]), (varyant, "doğru"))
            for sutun, alan in ((3, "htab_engel_ort"), (4, "htab_gecilebilir_ort"),
                                (5, "acik_yol_gecilebilir_ort")):
                beklenen = ("%.4f" % ozetler[varyant][alan]).replace(".", ",")
                self.assertEqual(beklenen, tekhat(h[sutun]), (varyant, alan))

    def test_T8b_isik_parametreleri_koddan(self):
        arena = oku(KOK / "simulation" / "mujoco" / "arena_mjcf.py")
        self.assertIn('"v2": ("-0.62 0.45 -0.64", "0.85 0.83 0.78", "0.18 0.18 0.19"', arena)
        self.assertIn('"taban": ("-0.35 0.25 -0.90", "0.58 0.58 0.55", "0.30 0.30 0.30"', arena)
        self.assertIn('castshadow="true"', arena)
        m = tekhat(self._b3())
        for deger in ("-0.62 0.45 -0.64", "-0.35 0.25 -0.90", "0.85 0.83 0.78",
                      "0.18 0.18 0.19", "0.30 0.30 0.30"):
            self.assertIn(katla(deger), m, deger)

    def test_T8c_saha_degil_ve_yerlesim_siniri(self):
        m = self._b3()
        self.assertEqual([], eksikler(m, (
            ("saha değil, SENTETİK render", 1),
            ("D-441 ÖNCESİ", 1),
            ("v2 ve v3 yeni yerleşimle yeniden ölçülmedi", 1),
        )))
        # eski "ayrı bir ölçüm yapılmamıştır" hükmü YALNIZ çizili
        self.assertEqual([], yasaklar(m, (
            "Farklı ışık açısı ve gölge kesitlerinde\nayrı bir ölçüm yapılmamıştır",)))
        n = tekhat(m)
        self.assertIn("OLCULEMEDI", n)
        self.assertEqual([], celiskili_ikinci_hukum(m))

    def test_T8d_bolum4_48_ve_484_tazelendi(self):
        giris = b4("## 4.8 ", "### 4.8.1 ")
        self.assertEqual([], eksikler(giris, (
            ("SENTETİK ışık/gölge kesiti ÖLÇÜLMÜŞTÜR", 1),
            ("0,1314 → 0,2380", 1),
        )))
        self.assertEqual([], yasaklar(giris, (
            "sentetiktir ve farklı ışık açısı /\ngölge çeşitliliği içermez",)))
        sinir = b4("### 4.8.4 ", "## 4.9 ")
        self.assertEqual([], eksikler(sinir, (("karışıklık matrisi değildir", 1),)))
        self.assertIn("OLCULEMEDI", tekhat(sinir))



class T9_KabulOlcutuBicimiKilidi(unittest.TestCase):
    """D-466: kabul ölçütü kilidi SÖZLÜK değil BİÇİM. Ölçülen kapsama ve SINIR.

    ÖLÇÜLEN (mutasyonla gösterildi, `test_T9c`): çürütücünün kaçan 6 cümlesi +
    eski sözlüğün 2 örneği, iki bölümün TAMAMINDA üç ayrı konuma (baş · orta ·
    son) konarak sınandı → **48/48 DÜŞTÜ**.
    ÖLÇÜLEN (yanlış pozitif, `test_T9a` ve `test_T9d`): mutasyonsuz iki gerçek
    bölüm YEŞİL; beş meşru düzenleme (yazım düzeltmesi · satır yeniden sarma ·
    yeni ÖLÇÜM satırı · yeni D atfı cümlesi · tablo satırı yer değiştirme)
    **0 yanlış pozitif**.
    SINIR — KAPANMAYAN SINIF (`test_T9e`, sayılarak yazıldı, D-465 (4)): altı
    kaçış sınıfı ölçüldü ve **altısı da kaçıyor**. Sayısız + kipsiz + kabul
    sözcüksüz olumlu hüküm ("Engine kolu artık yeşildir.", "Bu kalem tamamdır.",
    "…bir sorun görülmemiştir."), ölçütü İKİ TABLO SATIRINA bölme, eşiği yeni
    bir birim sözcüğüyle yazma ve sayıyı YAZIYLA yazma bu kilidin DIŞINDADIR.
    D-465 (4) tehdit modeli: kilit iyi niyetli aşınmayı durdurur, el yapımı
    düşmanı değil; bu sınıflar kovalanmaz, SAYILARAK yazılır.
    """

    # Çürütücünün ölçtüğü 6 kaçan cümle (D-466) + eski sözlüğün yakaladığı 2 örnek.
    KACAN_CUMLELER = (
        "Not (12 Eylül): D-303 için %3'lük ikinci oransal eşik de kabul sayılır; "
        "engine bu eşikle GEÇER.",
        "Not: H1 için ham çevrilmenin %60'ı da kabul eşiği sayılır.",
        "Revize edilmiş kabul kapısı: engine kabul edilir.",
        "RC failsafe sonucu tekrar değerlendirildiğinde GEÇTİ sayılmalıdır.",
        "Bu bölümdeki ÖLÇÜLEMEDİ kalemleri beyanla kapatılabilir.",
        "D-303 oransal eşiği yerine %3'lük ikinci eşik de kabul sayılır.",
        "Gözden geçirilmiş kapı: engine kabul edilir.",
        "Sahada gözden geçirilmiş kapı ≥ 6/15 alınır.",
    )
    # SINIR: bu sınıflar BUGÜN kaçıyor; sayı beyanı bu ölçüme bağlıdır.
    SINIR_KACANLAR = (
        "Engine kolu artık yeşildir.",
        "Bu kalem tamamdır.",
        "RC failsafe için bugün bir sorun görülmemiştir.",
        "| yeni ölçüt | ≥ 6/15 |\n| sonuç | GEÇTİ |",
        "Engine için yeni sınır üç birimdir ve karşılanmıştır.",
        "Engine için ikinci eşik yüzde üçtür ve sağlanmıştır.",
    )
    KONUMLAR = ("bas", "orta", "son")

    @staticmethod
    def _yerlestir(metin, cumle, nere):
        satirlar = metin.split("\n")
        i = {"bas": 3, "orta": len(satirlar) // 2, "son": len(satirlar) - 1}[nere]
        return "\n".join(satirlar[:i] + ["", cumle, ""] + satirlar[i:])

    def _tarama(self, cumleler):
        """Her cümleyi iki bölümün üç konumuna koyar; YAKALANMAYANLARI döndürür."""
        kacan = []
        for cumle in cumleler:
            hedef = [yapisal_kanon(s) for s in cumle.split("\n")]
            for ad, p in (("B3", B3), ("B4", B4)):
                temiz = oku(p)
                for nere in self.KONUMLAR:
                    mutant = self._yerlestir(temiz, cumle, nere)
                    self.assertNotEqual(temiz, mutant, "MUTASYON UYGULANMADI")
                    ihlal = [b for _, b in kabul_ihlalleri(mutant)]
                    if not any(h in b for h in hedef for b in ihlal):
                        kacan.append((cumle.replace("\n", " ")[:48], ad, nere))
        return kacan

    def test_T9a_gercek_iki_bolum_MUTASYONSUZ_YESIL(self):
        """YANLIŞ POZİTİF ÖLÇÜMÜ: dokunulmamış belgelerde kilit YEŞİL olmalı."""
        for p in (B3, B4):
            self.assertEqual([], kabul_ihlalleri(oku(p)), p.name)

    def test_T9b_on_kayit_OLU_girdi_tasimaz(self):
        """Beyaz listedeki her dizgi belgede GERÇEKTEN var; sayısı ön kayıtlı."""
        bulunan = set()
        for p in (B3, B4):
            bulunan.update(kabul_birimleri(oku(p)))
        self.assertEqual([], [b for b in ON_KAYITLI_KABUL_BIRIMLERI if b not in bulunan])
        self.assertEqual(73, len(ON_KAYITLI_KABUL_BIRIMLERI), "ön kayıt sayısı değişti")

    def test_T9c_KACAN_cumleler_HER_KONUMDA_duser(self):
        """D-466 RED sebebi: 8 cümle × 2 bölüm × 3 konum = 48 mutant, 48'i de DÜŞER."""
        kacan = self._tarama(self.KACAN_CUMLELER)
        self.assertEqual([], kacan, "{}/{} mutant KAÇTI".format(
            len(kacan), len(self.KACAN_CUMLELER) * 2 * len(self.KONUMLAR)))

    def test_T9d_MESRU_duzenleme_YANLIS_POZITIF_uretmez(self):
        """Beş meşru düzenleme kilidi düşürmemeli (aşırı sıkı kapı da kusurdur)."""
        m3, m4 = oku(B3), oku(B4)

        # 1) yazım düzeltmesi (anlatı cümlesi, kabul yüzeyi değil)
        a = m4.replace("kuru koşu bunu **gizlemez, raporlar**",
                       "kuru koşu bunu **gizlemez, raporlar.**", 1)
        # 2) satır yeniden sarma: bir paragrafın iki satırı birleştirilir
        sat = m3.split("\n")
        k = next(i for i in range(1, len(sat) - 1)
                 if sat[i].strip() and sat[i + 1].strip()
                 and not sat[i].lstrip().startswith(("|", "#", ">", "`"))
                 and not sat[i + 1].lstrip().startswith(("|", "#", ">", "`")))
        b = "\n".join(sat[:k] + [sat[k].rstrip() + " " + sat[k + 1].lstrip()] + sat[k + 2:])
        # 3) yeni ÖLÇÜM satırı (kabul ölçütü DEĞİL — sayı var, hüküm yok)
        c = m4.replace("## 4.5 ", "> 12 Eylül ek ÖLÇÜM: `jetson_fps.py` 120 örnek, "
                                  "p50 1,35 FPS · p95 1,06 FPS.\n\n## 4.5 ", 1)
        # 4) yeni D atfı cümlesi
        d = m3.replace("## 3.4 Yönerge dışı ek kanıt",
                       "Bu bölüm 12 Eylül 2026'da D-466 kapsamında yeniden okundu; "
                       "sayılar değişmedi.\n\n## 3.4 Yönerge dışı ek kanıt", 1)
        # 5) tablo satırı yer değiştirme (ön kayıtlı iki satır yer değiştirir)
        sat4 = m4.split("\n")
        i3 = next(i for i, s in enumerate(sat4) if s.startswith("| **K3** |"))
        i4 = next(i for i, s in enumerate(sat4) if s.startswith("| **K4** |"))
        sat4[i3], sat4[i4] = sat4[i4], sat4[i3]
        e = "\n".join(sat4)

        for ad, temiz, duzenli in (("yazım düzeltmesi", m4, a),
                                   ("satır yeniden sarma", m3, b),
                                   ("yeni ÖLÇÜM satırı", m4, c),
                                   ("yeni D atfı cümlesi", m3, d),
                                   ("tablo satırı yer değiştirme", m4, e)):
            self.assertNotEqual(temiz, duzenli, "DÜZENLEME UYGULANMADI: " + ad)
            # Ölçülen şey düzenlemenin KENDİ etkisidir: belgede zaten duran bir
            # ihlal bu kapıya yazılmaz (yoksa her mutasyon bu kapıyı da düşürür
            # ve yanlış pozitif ölçümü okunamaz hâle gelir).
            yeni = set(kabul_ihlalleri(duzenli)) - set(kabul_ihlalleri(temiz))
            self.assertEqual(set(), yeni, ad)

    def test_T9e_SINIR_kapanmayan_sinif_SAYILARAK_yazildi(self):
        """D-465 (4): kapanmayan kaçışlar KOVALANMAZ, SAYILIR — ve sayı ölçülür.

        Bu kapı, sınıf sayısını ölçüme bağlar: kilit güçlenir ya da zayıflarsa
        test DÜŞER ve beyan (sınıf docstring'i · `KANIT.md`) güncellenmek
        zorunda kalır. Bugünkü ölçüm: 6 sınıfın 6'sı kaçıyor.
        """
        kacan = self._tarama(self.SINIR_KACANLAR)
        kacan_sinif = {ad for ad, _, _ in kacan}
        self.assertEqual(6, len(kacan_sinif),
                         "SINIR degisti — beyani olcume cek: " + repr(sorted(kacan_sinif)))
        self.assertEqual(len(self.SINIR_KACANLAR) * 2 * len(self.KONUMLAR), len(kacan),
                         "siniflardan biri artik KISMEN yakalaniyor; beyan guncellensin")


class T10_KuruKosumYokSayisi(unittest.TestCase):
    """D-466 (çürütücü küçük kusur 3): rapordaki `[YOK]` sayısı LOG'dan doğrulanır."""

    LOGLAR = (("jetson_baslat_kuru.log", 2), ("jetson_baslat_kuru2.log", 1))

    def test_T10_log_YOK_sayilari_ve_rapor_HIZALI(self):
        dizin = KOK / "results" / "jetson_20260906" / "jetson_log_20260906"
        for ad, beklenen in self.LOGLAR:
            metin = oku(dizin / ad)
            self.assertEqual(beklenen, len(re.findall(r"^\[YOK\]", metin, re.M)), ad)
            m = re.search(r"KURU SONUC:.*?\[YOK\]: (\d+)", metin)
            self.assertIsNotNone(m, ad)
            self.assertEqual(beklenen, int(m.group(1)), ad)
        # Rapor artık "tek [YOK]" demiyor: dört yerde de düzeltme cümlesi var.
        duzeltme = ("`jetson_baslat_kuru2.log`'da **tek** `[YOK]`, "
                    "ilk kuru koşumda **iki**")
        self.assertEqual(2, adet(oku(B3), duzeltme), "Bölüm 3 düzeltmesi eksik")
        self.assertEqual(2, adet(oku(B4), duzeltme), "Bölüm 4 düzeltmesi eksik")
        # ve eski fazla beyan yalnız ÇİZİLİ olabilir
        for p in (B3, B4):
            self.assertEqual([], yasaklar(oku(p), ("tek `[YOK]` satırı",
                                                   "tek `[YOK]` `Pixhawk",
                                                   "`[YOK]` yalnız")), p.name)


class MutasyonKontrolu(unittest.TestCase):
    """Kurallar sentetik metinle İKİ YÖNDE sınanır — boş kapı olmasın (D-370).

    Gerçek dosya mutasyonları ayrıca `results/fdr_sprint_20260910/T244/mutasyon_t244.py`
    ile koşulur (10 mutant; ham çıktı `mutasyon_ciktisi.txt`).
    """

    def test_M1_cizili_iddia_kilidi_DOYURAMAZ(self):
        dogru = "Kilit **üç süreçte de kodludur** (D-419)."
        self.assertEqual([], eksikler(dogru, (("üç süreçte de kodludur", 1),)))
        for mutant in ("~~Kilit **üç süreçte de kodludur** (D-419).~~",
                       "~Kilit **üç süreçte de kodludur** (D-419).~",
                       "<del>Kilit **üç süreçte de kodludur** (D-419).</del>",
                       "<s>Kilit **üç süreçte de kodludur** (D-419).</s>",
                       "<strike>Kilit **üç süreçte de kodludur** (D-419).</strike>"):
            self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
            self.assertEqual(1, len(eksikler(mutant, (("üç süreçte de kodludur", 1),))), mutant)

    def test_M2_tek_tilde_UZUN_metinde_de_yakalanir(self):
        """D-461: `{1,40}` sınırı 40 karakterden uzun tek tilde çiziği görmüyordu."""
        uzun = "Kilit üç süreçte de kodludur ve bu satır kırk karakterden çok daha uzundur"
        self.assertGreater(len(uzun), 40)
        mutant = "~" + uzun + "~"
        self.assertEqual(1, len(eksikler(mutant, (("üç süreçte de kodludur", 1),))))

    def test_M3_yaklasik_isareti_cizme_SAYILMAZ(self):
        metin = "bağlantı ~18:45 kuruldu; HTAB geçilebilir ~%6; pt ~1,35 FPS ve ölçüm DÜŞTÜ"
        self.assertEqual([], cizme_artiklari(metin))
        self.assertIn("DUSTU", normalles(metin))
        self.assertIn("~18:45", metin)

    def test_M4_olumlu_hukme_CEVIRME_yakalanir(self):
        dogru = "| D-303 oransal 3/126 | **DÜŞTÜ** |"
        n = normalles(dogru)
        self.assertIn("DUSTU", n)
        self.assertNotIn("OLUMLU_HUKUM", n)
        for kelime in ("doğrulandı", "kanıtlandı", "teyit edildi", "tutar",
                       "dogrulandı", "Doğ**rulan**dı", "doğ­rulandı"):
            mutant = dogru.replace("**DÜŞTÜ**", "~~**DÜŞTÜ**~~ " + kelime)
            self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
            nm = normalles(mutant)
            self.assertNotIn("DUSTU", nm, kelime)
            self.assertIn("OLUMLU_HUKUM", nm, kelime)

    def test_M5_CELISKILI_IKINCI_HUKUM_yakalanir(self):
        dogru = "Eşik ≥ 12/15; ölçüm 0/15 → DÜŞTÜ."
        self.assertEqual([], celiskili_ikinci_hukum(dogru))
        for ek in (" Sahada **gözden geçirilmiş** kapı ≥ 6/15 alınır.",
                   " Bu kural kaldırıldı.",
                   " Eşik güncellendi: en az 6/15.",
                   " Ölçüt gevşetildi."):
            mutant = dogru + ek
            self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
            self.assertTrue(celiskili_ikinci_hukum(mutant), ek)

    def test_M6_ESIK_TEKLIGI_ikinci_esik_yakalanir(self):
        dogru = "Ön kayıt: yayımlanan çevrilme ≤ ham çevrilmenin %40'ı."
        n = normalles(dogru)
        self.assertEqual(1, n.count("HAM CEVRILMENIN %40'I"))
        self.assertEqual({"40"}, set(re.findall(r"HAM CEVRILMENIN %(\d+)", n)))
        mutant = dogru + " Gözden geçirilmiş ölçüt: ham çevrilmenin %60'ı."
        nm = normalles(mutant)
        self.assertEqual({"40", "60"}, set(re.findall(r"HAM CEVRILMENIN %(\d+)", nm)))
        # eş anlamlı geri dönüş de yakalanır: "en az" → ">="
        self.assertIn(">=", normalles("eşik en az 12/15"))
        self.assertIn(">=", normalles("eşik ≥ 12/15"))

    def test_M7_esanlamli_OLCULMEDI_geri_donusu_tek_belirtec(self):
        for varyant in ("ÖLÇÜLEMEDİ", "ölçülmedi", "ölçüm yok", "ölçülemez"):
            self.assertIn("OLCULEMEDI", normalles(varyant), varyant)

    def test_M8_bilinmeyen_cizme_sozdizimi_beyaz_liste_disi(self):
        self.assertEqual([], cizme_artiklari("düz metin, çizik yok"))
        self.assertTrue(cizme_artiklari("<del>yarım etiket"))
        self.assertTrue(cizme_artiklari("kapanmayan ~çizik"))

    def test_M9_D463_birlestirici_cizik_ve_HTML_varligi_YAKALANIR(self):
        """D-463 (a): U+0336 ve HTML varlık biçimi (`&#822;` / `&#x336;`) kaçıyordu."""
        dogru = "D-303 oransal 3/126 DÜŞTÜ"
        self.assertEqual([], cizme_artiklari(dogru))
        self.assertEqual([], eksikler(dogru, (("DÜŞTÜ", 1),)))
        mutantlar = {
            "çıplak U+0336": "".join(c + "̶" for c in dogru),
            "ondalık varlık": "".join(c + "&#822;" for c in dogru),
            "onaltılık varlık": "".join(c + "&#x336;" for c in dogru),
            "U+0335 kısa çizik": "".join(c + "̵" for c in dogru),
        }
        for ad, mutant in mutantlar.items():
            self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
            self.assertTrue(cizme_artiklari(mutant), ad)
            self.assertEqual(1, len(eksikler(mutant, (("DÜŞTÜ", 1),))), ad)
        # varlıkla gizlenmiş ÇİZİK SÖZDİZİMİ de görünür olur: `&#126;&#126;…&#126;&#126;`
        gizli = "&#126;&#126;" + dogru + "&#126;&#126;"
        self.assertEqual(1, len(eksikler(gizli, (("DÜŞTÜ", 1),))),
                         "HTML varlığıyla yazılmış çizik kaçtı")


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
NAVITAS 12–15 Eylül 2026 uçuş analizi — tablo üretici.

Kaynak dosyalardaki (RAPOR.md, performans_zarfi/tablolar.json, E_1240_ivme/ozet.json,
F_1311_aski_4S_13Ah/ozet.json, parametre_zaman_cizgisi.md/.json, tum_loglar.json, A/B/C/D/E ozet.json)
tabloları TEK çalışma kitabına (her tablo ayrı sayfa) ve her tablo için bir PNG'ye kopyalar.

KURAL: sayılar kaynaktan KOPYALANIR, yeniden hesaplanmaz. Tek istisna birim dönüşümüdür:
zarf tablolarındaki "v_üst km/h" = v_üst m/s × 3,6 (kaynak ozet_md'de de aynı dönüşümle verilir).

Çalıştırma:  O:\\navitas-local-train\\venv\\Scripts\\python.exe tablolar_uret.py
Bağımlılık:  openpyxl, matplotlib, numpy (SciPy kullanılmaz).
"""
import json
import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.hyperlink import Hyperlink

BURASI = Path(__file__).resolve().parent            # .../TABLOLAR
KOK = BURASI.parent                                  # .../ucus_analiz_20260915
PNG_DIZIN = BURASI / "png"
XLSX = BURASI / "NAVITAS_ucus_analizi_tablolar.xlsx"

plt.rcParams["font.family"] = "DejaVu Sans"


# ----------------------------------------------------------------------------- yardımcılar
def oku_json(goreli):
    with open(KOK / goreli, encoding="utf-8") as f:
        return json.load(f)


def oku_metin(goreli):
    with open(KOK / goreli, encoding="utf-8") as f:
        return f.read()


def temizle(h):
    """Markdown hücre metnini sadeleştirir: kalın işareti, ters tırnak, kaçışlı boru."""
    h = h.strip().replace("\\|", "|")
    h = re.sub(r"\*\*(.+?)\*\*", r"\1", h)
    h = h.replace("`", "")
    return h


def md_hucreler(s):
    s = s.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [temizle(p) for p in re.split(r"(?<!\\)\|", s)]


def md_tablolar(metin):
    """Metindeki tüm markdown tablolarını sırayla (başlık, satırlar) olarak döndürür."""
    satirlar = metin.split("\n")
    sonuc = []
    i = 0
    while i < len(satirlar):
        s = satirlar[i]
        if s.startswith("|") and i + 1 < len(satirlar) and re.match(r"^\|\s*:?-", satirlar[i + 1]):
            baslik = md_hucreler(s)
            i += 2
            govde = []
            while i < len(satirlar) and satirlar[i].startswith("|"):
                h = md_hucreler(satirlar[i])
                if len(h) < len(baslik):
                    h += [""] * (len(baslik) - len(h))
                govde.append(h[: len(baslik)])
                i += 1
            sonuc.append((baslik, govde))
        else:
            i += 1
    return sonuc


def tablo_bul(tablolar, imza, atla=0):
    """Başlığı verilen ön-ek listesiyle başlayan tabloyu bulur (atla: kaçıncı eşleşme)."""
    n = 0
    for baslik, govde in tablolar:
        if baslik[: len(imza)] == imza:
            if n == atla:
                return baslik, govde
            n += 1
    raise KeyError(f"tablo bulunamadı: {imza}")


_SAYI = re.compile(r"[+\-\u2212]?\d{1,3}(?:[ \u202f]\d{3})+(?:[.,]\d+)?|[+\-\u2212]?\d+(?:[.,]\d+)?")


def sayi(h):
    """Hücre salt sayı ise int/float (Türkçe virgül ya da nokta), değilse metin."""
    if h is None or isinstance(h, (int, float)) and not isinstance(h, bool):
        return h
    if isinstance(h, bool):
        return "evet" if h else "hayır"
    t = str(h).strip()
    if not _SAYI.fullmatch(t):
        return t
    u = t.replace("\u202f", "").replace(" ", "").replace("\u2212", "-").replace(",", ".")
    try:
        f = float(u)
    except ValueError:
        return t
    if re.fullmatch(r"[+-]?\d+", u):
        return int(u)
    return f


def yuvarla_metin(v):
    """PNG için gösterim: sayı → Türkçe virgül, None → boş, liste → '; '."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "evet" if v else "hayır"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v != v:  # NaN
            return ""
        s = repr(v)
        if "e" in s or "E" in s:
            s = f"{v:.4g}"
        if s.endswith(".0"):
            s = s[:-2]
        return s.replace(".", ",")
    if isinstance(v, (list, tuple)):
        return "; ".join(yuvarla_metin(x) for x in v)
    return str(v)


def ondalik_bicim(v):
    """openpyxl sayı biçimi: kaynaktaki ondalık basamak sayısı kadar (en çok 4)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    if isinstance(v, int):
        return "0"
    s = repr(float(v))
    if "e" in s:
        # bilimsel gösterim: mantisin ondalık basamağı kadar (en çok 5) — 4.84873e-07 → 4.84873E-07
        mant = s.split("e")[0]
        n = min(len(mant.split(".")[1].rstrip("0")) if "." in mant else 0, 5)
        return ("0." + "0" * n if n else "0") + "E+00"
    kesir = s.split(".")[1] if "." in s else ""
    n = min(len(kesir.rstrip("0")), 4)
    return "0" if n == 0 else "0." + "0" * n


def T(ad, baslik, sutunlar, satirlar, kaynak, aciklama="", not_=""):
    """Tablo tanımı. ad ≤ 31 karakter, ASCII."""
    ad = ad[:31]
    assert re.fullmatch(r"[A-Za-z0-9_ ]+", ad), ad
    satirlar = [[sayi(v) if isinstance(v, str) else (v if not isinstance(v, bool) else ("evet" if v else "hayır"))
                 for v in r] for r in satirlar]
    return dict(ad=ad, baslik=baslik, sutunlar=list(sutunlar), satirlar=satirlar,
                kaynak=kaynak, aciklama=aciklama, not_=not_)


def transpoze(tb, etiket_fn, ilk="büyüklük"):
    """Az satırlı / çok sütunlu tabloyu çevirir: sütunlar → satırlar (okunabilirlik için)."""
    sut = [ilk] + [etiket_fn(r) for r in tb["satirlar"]]
    satirlar = [[tb["sutunlar"][j]] + [r[j] for r in tb["satirlar"]] for j in range(len(tb["sutunlar"]))]
    tb = dict(tb, sutunlar=sut, satirlar=satirlar)
    tb["aciklama"] = (tb.get("aciklama", "") + " Tablo çevrildi: her sütun bir pencere/uçuş, her satır bir büyüklük.").strip()
    return tb


def g(d, *yol, vars_=None):
    """Sözlükte güvenli derin erişim."""
    for k in yol:
        if d is None:
            return vars_
        if isinstance(d, dict):
            d = d.get(k)
        elif isinstance(d, (list, tuple)) and isinstance(k, int) and k < len(d):
            d = d[k]
        else:
            return vars_
    return vars_ if d is None else d


def ist(d, anahtarlar=("n", "ort", "p50", "p05", "p95", "min", "maks", "std")):
    d = d or {}
    return [d.get(k) for k in anahtarlar]


# ----------------------------------------------------------------------------- RAPOR.md
def rapor_tablolari():
    metin = oku_metin("RAPOR.md")
    tb = md_tablolar(metin)
    K = "RAPOR.md"
    out = []
    b, s = tablo_bul(tb, ["Metrik"])
    out.append(T("R1_Konfig_x_Metrik", "RAPOR §1 — Konfigürasyon × metrik (A–F)", b, s, K + " §1",
                 "Her sütun bir konfigürasyon; hücreler raporun metniyle birebir (bileşik değerler metin olarak)."))
    b, s = tablo_bul(tb, ["Kıyas ekseni"])
    out.append(T("R3_Titresim_Adil_Kiyas", "RAPOR §3 — B ve D titreşiminin A ve C ile adil kıyası", b, s, K + " §3"))
    b, s = tablo_bul(tb, ["Kullanıcı gözlemi"])
    out.append(T("R4_E_Logu_Gozlemler", "RAPOR §4 — E logu (15 Eyl 12-40-55, tam gaz): gözlem / kanıt / hüküm", b, s, K + " §4"))
    b, s = tablo_bul(tb, ["Gerekçe"])
    out.append(T("R5_1_Oneri_Gerekce", "RAPOR §5.1 — 21 Eylül önerisi: 4S 13 000 mAh + 9x5x3 gerekçesi", b, s, K + " §5.1"))
    b, s = tablo_bul(tb, ["Parametre", "Mevcut"])
    out.append(T("R5_2_Parametre_Onerileri", "RAPOR §5.2 — Parametre önerileri (mevcut değerler F logu 13-11-32 PARM)", b, s, K + " §5.2"))
    b, s = tablo_bul(tb, ["Adım"])
    out.append(T("R5_3_Kabul_Testi", "RAPOR §5.3 — Kabul testi (21 Eylül sabahı, görevden önce)", b, s, K + " §5.3"))
    b, s = tablo_bul(tb, ["Risk"])
    out.append(T("R6_Riskler", "RAPOR §6 — Riskler", b, s, K + " §6"))
    b, s = tablo_bul(tb, ["Eksik"])
    out.append(T("R7_Veri_Boslugu", "RAPOR §7 — Veri boşluğu", b, s, K + " §7"))
    return out


# ----------------------------------------------------------------------------- performans zarfı
def zarf_tablolari():
    Z = oku_json("performans_zarfi/tablolar.json")
    K = "performans_zarfi/tablolar.json"
    out = []
    sut = ["θ (°)", "senaryo", "pil V_açık (V)", "gereken T/W", "T_max/W", "irtifa tutar", "a_z (m/s²)",
           "a0 (m/s²)", "v_üst (m/s)", "v_üst (km/h)", "%95 v_üst süresi (s)", "0–60 km/h (s)", "0–100 km/h (s)",
           "tam gaz A", "V_yük tam gaz (V)", "v_üst'te A", "azami rüzgar (m/s)", "1 dk mAh", "%80 pil (dk)",
           "sınırlayıcı", "rejim"]
    for k in Z["konfigler"]:
        satirlar = []
        for r in k["satirlar"]:
            v_ust = r["v_ust"]
            kmh = round(v_ust * 3.6, 1)
            asimptot = f"✗ (asimptot {round(v_ust * 3.6)} km/h)"
            gerek = r["gerek_TW"]
            if gerek == "inf":
                gerek = "∞"
            satirlar.append([
                r["theta_deg"], r["senaryo"], r["V_acik"], gerek, r["TW_max"],
                "✓" if r["tutar"] else "✗", r.get("a_z"),
                r["a0"], v_ust, kmh, r["t95"],
                r["t60"] if r["t60"] is not None else asimptot,
                r["t100"] if r["t100"] is not None else asimptot,
                r["I_TG_A"], r["V_yuk_TG"], r["I_ust_A"],
                r["ruzgar"] if r["ruzgar"] is not None else "— (" + r["ruzgar_notu"] + ")",
                r["mAh_1dk"], r["sure80_dk"], r["sinir"], r["rejim"]])
        assert len(satirlar) == 18, len(satirlar)
        ad = "Z_" + k["kimlik"] + "_zarf"
        out.append(T(ad, f"Performans zarfı — {k['ad']} (18 satır: 6 eğim × 3 pil senaryosu)", sut, satirlar,
                     K + f" › konfigler[{k['kimlik']}].satirlar",
                     "v_üst km/h = m/s × 3,6 (birim dönüşümü). Yazılımsal sınırlar (ANGLE_MAX, LOIT/WPNAV_SPEED) YOK SAYILDI; "
                     "kütle VARSAYIM (4S 3,0 kg / 3S 2,5 kg); 4S T/W 1,91 hava direnci ihmal edilmiş ALT SINIR."))
    # theta_max
    sut = ["konfig", "senaryo", "V_açık (V)", "T_max/W", "θ_max (°)", "rüzgar (m/s)", "rüzgar (km/h)",
           "I (A)", "I motor (A)", "V_yük (V)", "v_pitch (m/s)", "not"]
    satirlar = []
    for k in Z["konfigler"]:
        for r in k["theta_max"]:
            satirlar.append([k["ad"], r["senaryo"], r["V_acik"], r["TW_max"], r["theta_max_deg"], r["ruzgar_ms"],
                             r["ruzgar_kmh"], r["I_A"], r["I_motor_A"], r["V_yuk"], r["v_pitch"], r["notu"]])
    out.append(T("Z_theta_max", "Performans zarfı — irtifa tutarak azami eğim θ_max ve o eğimde konum tutulabilen rüzgar",
                 sut, satirlar, K + " › konfigler[*].theta_max"))
    # parametre + kalibrasyon
    P = Z["parametreler"]
    KA = Z["kalibrasyon"]
    k4, k3 = P["konfigler"]
    sut = ["grup", "parametre", "ortak", "4S 13 Ah + 9x5x3", "3S 8 Ah + 1045", "kaynak / not"]
    satirlar = []
    for ad in ["g", "rho", "CdA0", "CdA_egim_k", "MOT_SPIN_MIN", "MOT_SPIN_MAX", "MOT_THST_EXPO", "KV_rpm_per_V",
               "ESC_surekli_A_motor", "ESC_tepe_A_motor", "PM06_surekli_A", "PM06_tepe_A", "kullanilabilir_pil",
               "ust_hiz_orani", "dt_s"]:
        satirlar.append(["genel", ad, P[ad], None, None, P["PM06_notu"] if ad.startswith("PM06") else ""])
    satirlar.append(["genel", "egimler_deg", ", ".join(str(x) for x in P["egimler_deg"]), None, None, ""])
    satirlar.append(["genel", "yazilimsal_sinirlar", Z["meta"]["yazilimsal_sinirlar"], None, None, ""])
    satirlar.append(["genel", "kapali_form_vs_rk4_maks_sapma_pct", Z["meta"]["kapali_form_vs_rk4_maks_sapma_pct"], None, None, ""])
    for ad in ["kutle_kg", "kapasite_Ah", "hucre", "R_paket_ohm", "pervane", "pitch_m", "aski_pwm_olculen_orani"]:
        satirlar.append(["konfig", ad, None, k4.get(ad), k3.get(ad), "kütle VARSAYIM (logda yok)" if ad == "kutle_kg" else ""])
    for ad in ["ThO", "V_yuk", "I_A", "sure_s"]:
        satirlar.append(["askı ankrajı", ad, None, k4["aski"][ad], k3["aski"][ad], ""])
    satirlar.append(["askı ankrajı", "kaynak", None, k4["aski"]["kaynak"], k3["aski"]["kaynak"], ""])
    for ad in ["TW", "V_yuk", "I_A", "a_ms2", "rcou_maks"]:
        satirlar.append(["tam gaz ankrajı", ad, None, k4["tam_gaz"][ad], None, "3S için tam gaz ölçümü YOK"])
    satirlar.append(["tam gaz ankrajı", "kaynak", None, k4["tam_gaz"]["kaynak"], None, ""])
    for i in range(3):
        satirlar.append(["pil senaryosu", f"senaryo {i + 1}", None,
                         f"{k4['pil_senaryolari'][i][0]}: {yuvarla_metin(k4['pil_senaryolari'][i][1])} V",
                         f"{k3['pil_senaryolari'][i][0]}: {yuvarla_metin(k3['pil_senaryolari'][i][1])} V", ""])
    ik = k4["ikinci_aski_kontrol"]
    for ad in ["ThO", "V_yuk", "I_A"]:
        satirlar.append(["ikinci askı kontrolü (D)", ad, None, ik[ad], None, ik["kaynak"]])
    c4, c3 = KA["4S_13Ah_9x5x3"], KA["3S_8Ah_1045"]
    for ad in ["W_N", "u_eff_aski_model", "pwm_aski_model_us", "pwm_aski_expo_suz_us", "pwm_aski_olculen_us", "rpm_aski_KV",
               "k_T_N_per_rpm2", "k_P_W_per_rpm3", "P_aski_W", "T_motor_aski_N", "P_motor_aski_W", "s_TG", "s_TG_kaynak", "c_T"]:
        satirlar.append(["kalibrasyon", ad, None, c4.get(ad), c3.get(ad), ""])
    for ad in ["TW_tam_gaz_KV_modeli", "TW_tam_gaz_olculen", "TW_tam_gaz_expo_suz_model", "P_tam_gaz_model_W",
               "P_tam_gaz_olculen_W", "P_tam_gaz_sapma_pct", "I_tam_gaz_model_A", "I_tam_gaz_olculen_A",
               "rpm_tam_gaz_model", "T_motor_tam_gaz_N"]:
        satirlar.append(["kalibrasyon (tam gaz)", ad, None, c4.get(ad), None, ""])
    for ad in ["TW_dolu_sTG", "TW_dolu_sTG1"]:
        satirlar.append(["kalibrasyon (3S dolu)", ad, None, None, c3.get(ad), "s_TG=1 üst sınırı: TW_dolu_sTG1"])
    ik2 = c4["ikinci_aski_kontrol"]
    for ad in ["TW_model", "I_model_A", "I_olculen_A"]:
        satirlar.append(["ikinci askı kontrolü (D)", ad, None, ik2[ad], None, ""])
    out.append(T("Z_Parametre_Kalibrasyon", "Performans zarfı — model parametreleri, ankrajlar ve kalibrasyon", sut, satirlar,
                 K + " › parametreler, kalibrasyon, meta"))
    satirlar = [[i + 1, u] for i, u in enumerate(Z["uyarilar"])]
    out.append(T("Z_Model_Uyarilari", "Performans zarfı — model uyarıları (varsayımlar ve geçerlilik sınırları)",
                 ["no", "uyarı"], satirlar, K + " › uyarilar"))
    return out


# ----------------------------------------------------------------------------- E logu (12-40-55)
def e_tablolari():
    E = oku_json("E_1240_ivme/ozet.json")
    K = "E_1240_ivme/ozet.json"
    out = []
    # 0 → hız eşik süreleri
    tr = E["tirmanma_hizi"]
    x, c = tr["XKF1_negVD"], tr["CTUN_CRt"]
    fark = tr["kaynak_farki"]["esik_sure_farki_s"]
    sut = ["eşik / ölçüt", "XKF1 −VD", "CTUN.CRt", "CTUN − XKF1 (s)", "IMU0 integre hız", "IMU1 integre hız", "not"]
    satirlar = []
    for esik in ["0.1", "1", "2", "3", "4", "5"]:
        satirlar.append([f"{esik.replace('.', ',')} m/s — ilk örnek (s)", x["esik_sureleri_s"][esik]["ilk_ornek_s"],
                         c["esik_sureleri_s"][esik]["ilk_ornek_s"], None, None, None, ""])
        satirlar.append([f"{esik.replace('.', ',')} m/s — ara değer (s)", x["esik_sureleri_s"][esik]["ara_deger_s"],
                         c["esik_sureleri_s"][esik]["ara_deger_s"], fark[esik], None, None, ""])
    I0, I1 = E["IMU"]["IMU0"], E["IMU"]["IMU1"]
    satirlar.append(["tepe hız (m/s)", x["tepe_ms"], c["tepe_ms"], tr["kaynak_farki"]["maks_mutlak_ms"],
                     I0["integre_hiz_tepe_ms"], I1["integre_hiz_tepe_ms"], "IMU: yerde durgun ortalama çıkarılıp integre edildi"])
    satirlar.append(["tepe t (s, t0'dan)", x["tepe_t_s"], c["tepe_t_s"], None, I0["integre_hiz_tepe_t_s"], I1["integre_hiz_tepe_t_s"], ""])
    satirlar.append(["IMU − XKF1 tepe farkı (m/s)", None, None, None, I0["integre_hiz_XKF1_tepe_farki_ms"],
                     I1["integre_hiz_XKF1_tepe_farki_ms"], ""])
    satirlar.append(["t0 (mutlak s)", E["t0"]["t_mutlak_s"], None, None, None, None, E["t0"]["tanim"] + "; " + E["t0"]["not"]])
    satirlar.append(["hareket eşiği (m/s)", tr["hareket_esigi_ms"], None, None, None, None, tr["not"]])
    out.append(T("E_Hiz_Esik_Sureleri", "E logu (15 Eyl 12-40-55) — 0 → hız eşik süreleri: XKF1 / CTUN.CRt / IMU integrali",
                 sut, satirlar, K + " › tirmanma_hizi, IMU"))
    # irtifa
    ir = E["irtifa"]
    sut = ["eşik / ölçüt", "ilk örnek (s)", "ara değer (s)", "not"]
    satirlar = [[f"{k} irtifa", v["ilk_ornek_s"], v["ara_deger_s"], ""] for k, v in ir["esikler"].items()]
    satirlar += [["ilk hareket 0,05 m (s)", ir["ilk_hareket_0p05m_s"], None, ""],
                 ["irtifa maks (m)", ir["maks_m"], None, f"t = {yuvarla_metin(ir['maks_t_s'])} s"],
                 ["irtifa maks t (s)", ir["maks_t_s"], None, ""],
                 ["XKF1 PD maks (m)", ir["XKF1_PD_maks_m"], None, ""],
                 ["taban CTUN.Alt (m)", ir["taban_m_CTUN_Alt"], None, ir["BARO_BAlt_not"]]]
    out.append(T("E_Irtifa_Esikleri", "E logu — irtifa eşik süreleri (t0'dan)", sut, satirlar, K + " › irtifa"))
    # ivme ve T/W
    iv, tw = E["ivme"], E["TW"]
    sut = ["kaynak", "yöntem", "değer", "birim", "t (s)", "not"]
    satirlar = [
        ["XKF1 −VD", "ham tepe", iv["XKF1"]["ham_tepe_ms2"], "m/s²", iv["XKF1"]["ham_tepe_t_s"], iv["yontem"]],
        ["XKF1 −VD", "yumuşak tepe", iv["XKF1"]["yumusak_tepe_ms2"], "m/s²", iv["XKF1"]["yumusak_tepe_t_s"], ""],
        ["CTUN.CRt", "ham tepe", iv["CTUN_CRt"]["ham_tepe_ms2"], "m/s²", iv["CTUN_CRt"]["ham_tepe_t_s"], ""],
        ["CTUN.CRt", "yumuşak tepe", iv["CTUN_CRt"]["yumusak_tepe_ms2"], "m/s²", iv["CTUN_CRt"]["yumusak_tepe_t_s"], ""],
        ["XKF1", "ortalama ivme (hareket başı → tepe)", iv["ortalama_hareket_basi_tepe_ms2"], "m/s²",
         f"{yuvarla_metin(iv['ortalama_pencere_s'][0])}–{yuvarla_metin(iv['ortalama_pencere_s'][1])}", ""],
    ]
    for ad, I in (("IMU0", I0), ("IMU1", I1)):
        satirlar += [
            [ad, "durgun AccZ ort", I["durgun_AccZ_ort_ms2"], "m/s²", f"{I['durgun_pencere_s'][0]}…{I['durgun_pencere_s'][1]}", f"std {yuvarla_metin(I['durgun_AccZ_std_ms2'])}"],
            [ad, "basit ham tepe", I["basit_ham_tepe_ms2"], "m/s²", None, ""],
            [ad, "basit yumuşak tepe", I["basit_yumusak_tepe_ms2"], "m/s²", I["basit_yumusak_tepe_t_s"], ""],
            [ad, "döndürülmüş ham tepe", I["dondurulmus_ham_tepe_ms2"], "m/s²", None, ""],
            [ad, "döndürülmüş yumuşak tepe", I["dondurulmus_yumusak_tepe_ms2"], "m/s²", I["dondurulmus_yumusak_tepe_t_s"], f"tilt maks {yuvarla_metin(I['tilt_maks_deg_t0_1p5s'])}° (t0…1,5 s)"],
        ]
    satirlar += [
        ["T/W", "alt sınır (ham XKF1)", tw["TW_alt_sinir"], "—", None, tw["formul"] + "; a_maks " + yuvarla_metin(tw["a_maks_kullanilan_ms2"])],
        ["T/W", "alt sınır (yumuşak)", tw["TW_alt_sinir_yumusak"], "—", None, ""],
        ["T/W", "IMU0 döndürülmüş yumuşak", tw["TW_alt_sinir_IMU_dondurulmus_yumusak"]["IMU0"], "—", None, ""],
        ["T/W", "IMU1 döndürülmüş yumuşak", tw["TW_alt_sinir_IMU_dondurulmus_yumusak"]["IMU1"], "—", None, ""],
        ["T/W", "ortalama ivme ile", tw["TW_alt_sinir_ortalama_ivme"], "—", None, tw["kutle_notu"]],
    ]
    for i, n in enumerate(tw["neden_alt_sinir"]):
        satirlar.append(["T/W", f"neden alt sınır {i + 1}", None, "", None, n])
    out.append(T("E_Ivme_TW", "E logu — tepe ivme (EKF, CTUN, IMU) ve T/W alt sınırı", sut, satirlar, K + " › ivme, IMU, TW"))
    # pil
    p = E["pil"]
    sut = ["büyüklük", "değer", "birim", "not"]
    satirlar = [
        ["pencere (t0'dan)", f"{p['pencere_s'][0]}–{p['pencere_s'][1]}", "s", ""],
        ["hücre (beyan)", p["hucre_beyan"], "", ""],
        ["V0 kalkış öncesi ort", p["V0_kalkis_oncesi_ort"], "V", ""],
        ["V0 hücre", p["V0_hucre"], "V/hücre", ""],
        ["I maks", p["I_maks_A"], "A", f"t = {yuvarla_metin(p['I_maks_t_s'])} s"],
        ["V @ I maks", p["V_at_Imaks"], "V", ""],
        ["V min", p["V_min"], "V", f"t = {yuvarla_metin(p['V_min_t_s'])} s"],
        ["V min hücre", p["V_min_hucre"], "V/hücre", ""],
        ["sarkma", p["sarkma_V"], "V", "V0 → V_min"],
        ["sarkma hücre", p["sarkma_hucre_V"], "V/hücre", ""],
        ["polyfit V–I eğim", p["polyfit_V_I"]["egim_ohm"], "Ω", f"n = {p['polyfit_V_I']['n']}, R² = {yuvarla_metin(p['polyfit_V_I']['R2'])}"],
        ["R paket (polyfit)", p["polyfit_V_I"]["R_paket_mohm"], "mΩ", ""],
        ["R hücre (polyfit)", p["polyfit_V_I"]["R_hucre_mohm"], "mΩ", ""],
        ["V açık devre (kesim)", p["polyfit_V_I"]["V_acik_devre_kesim"], "V", ""],
        ["R paket tepe nokta", p["tepe_nokta_R_paket_mohm"], "mΩ", ""],
        ["BAT.Res FC ort", p["BAT_Res_AP_tahmini_ohm"]["ort"], "Ω", ""],
        ["BAT.Res FC maks", p["BAT_Res_AP_tahmini_ohm"]["maks"], "Ω", ""],
        ["BAT.Res FC son", p["BAT_Res_AP_tahmini_ohm"]["son"], "Ω", ""],
        ["mAh ilk 3 s", p["mAh_ilk3s"], "mAh", ""],
        ["güç tepe", p["guc_tepe_W"], "W", ""],
        ["tam gaz penceresi V ort", p["tam_gaz_penceresi"]["V_ort"], "V", f"süre {yuvarla_metin(p['tam_gaz_penceresi']['sure_s'])} s"],
        ["tam gaz penceresi I ort", p["tam_gaz_penceresi"]["I_ort_A"], "A", ""],
        ["BATT_MONITOR", p["sensor"]["BATT_MONITOR"], "", p["sensor"]["not"]],
        ["BATT_AMP_PERVLT", p["sensor"]["BATT_AMP_PERVLT"], "A/V", ""],
        ["BATT_VOLT_MULT", p["sensor"]["BATT_VOLT_MULT"], "", ""],
        ["BATT_LOW_VOLT", p["BATT_esikleri"]["BATT_LOW_VOLT"], "V", p["BATT_esikleri"]["not"]],
        ["BATT_CRT_VOLT", p["BATT_esikleri"]["BATT_CRT_VOLT"], "V", ""],
        ["BATT_CAPACITY", p["BATT_esikleri"]["BATT_CAPACITY"], "mAh", ""],
    ]
    out.append(T("E_Pil_Sarkma_IcDirenc", "E logu — pil sarkması, iç direnç ve eşikler (tam gaz, 115 A)", sut, satirlar, K + " › pil"))
    # motorlar
    m = E["motor"]
    sut = ["kanal", "motor", "tepe µs", "tepe t (s)", "doygun örnek (10 Hz)", "ilk doygun t (s)"]
    esle = {"C9": "M4 arka-sağ CW", "C10": "M2 arka-sol CCW", "C11": "M1 ön-sağ CCW", "C12": "M3 ön-sol CW"}
    satirlar = [[k, esle[k], v["tepe_us"], v["tepe_t_s"], v["doygun_ornek_10Hz"], v["ilk_doygun_t_s"]] for k, v in m["motorlar"].items()]
    satirlar.append(["—", "yayılım tam gazda maks / ort", m["tam_gaz_motorlar_arasi_yayilim_us"]["maks"],
                     m["tam_gaz_motorlar_arasi_yayilim_us"]["ort"], None, None])
    satirlar.append(["—", "PWM tavanı (SPIN_MAX 0,95)", m["pwm_tavan_hesap_us"], None, None, None])
    satirlar.append(["—", "ThO = 1,0 süresi (s)", m["ThO_1p0_suresi_s"], m["ThO_1p0_bas_s"], None, m["ThO_1p0_son_s"]])
    out.append(T("E_Motor_Tam_Gaz", "E logu — tam gazda motor çıkışları (RCOU C9–C12) ve doyum", sut, satirlar,
                 K + " › motor", not_=m["cikislar"] + " · " + " ".join(m["etki"])))
    # yazılım hız sınırları
    ys = E["yazilim_hiz_sinirlari"]
    sut = ["kip", "yatay maks (m/s)", "tırmanma maks (m/s)", "iniş maks (m/s)", "yatay ivme (m/s²)", "dikey ivme (m/s²)", "kaynak parametreler"]
    satirlar = [[r["kip"], r["yatay_maks_ms"], r["tirmanma_maks_ms"], r["inis_maks_ms"], r["yatay_ivme_ms2"], r["dikey_ivme_ms2"], r["kaynak"]]
                for r in ys["tablo"]]
    out.append(T("E_Yazilim_Hiz_Sinirlari", "E logu — kip başına yazılımsal hız/ivme sınırları (PARM, ArduCopter 4.5.7)", sut, satirlar,
                 K + " › yazilim_hiz_sinirlari", not_=ys["yorum"]))
    # ThO bandına göre VIBE (E vs D)
    ET = oku_json("E_1240_tam_gaz/ozet.json")
    kd = ET["kiyas_D"]
    sut = ["kaynak", "ThO bandı", "n (CTUN)", "IMU0 X ort", "X p95", "X maks", "IMU0 Y ort", "Y p95", "Y maks",
           "IMU0 Z ort", "Z p95", "Z maks", "IMU1 Z ort", "IMU1 Z p95", "IMU1 Z maks",
           "M1 µs", "M2 µs", "M3 µs", "M4 µs", "anlık yayılım ort µs", "CCW−CW (yaw)", "ön−arka (pitch)", "sağ−sol (roll)"]

    def bant_satiri(kaynak, bant, b):
        def v(imu, ek, k):
            d = g(b, imu, ek) or {}
            return d.get(k, d.get("p95_maks") if k == "p95" else None)
        rc = b.get("rcou") or {}
        mo = rc.get("M_ort_pwm") or {}
        cf = rc.get("cift_farklari_pwm") or {}
        return [kaynak, bant, b.get("n_ctun"),
                v("IMU0", "X", "ort"), v("IMU0", "X", "p95"), v("IMU0", "X", "maks"),
                v("IMU0", "Y", "ort"), v("IMU0", "Y", "p95"), v("IMU0", "Y", "maks"),
                v("IMU0", "Z", "ort"), v("IMU0", "Z", "p95"), v("IMU0", "Z", "maks"),
                v("IMU1", "Z", "ort"), v("IMU1", "Z", "p95"), v("IMU1", "Z", "maks"),
                mo.get("M1"), mo.get("M2"), mo.get("M3"), mo.get("M4"), rc.get("anlik_yayilim_ort"),
                cf.get("CCW(M1+M2)-CW(M3+M4)_yaw"), cf.get("on(M1+M3)-arka(M2+M4)_pitch"), cf.get("sag(M1+M4)-sol(M2+M3)_roll")]

    satirlar = [bant_satiri("E 12-40-55 (tam gaz)", bant, b) for bant, b in kd["E_12-40-55"].items()]
    for logad, d in kd["D"].items():
        for bant, b in (d.get("bantlar_birlesik") or {}).items():
            satirlar.append(bant_satiri("D " + logad.replace(".bin", ""), bant, b))
        ab = d.get("aski_birlesik")
        if ab:
            r = bant_satiri("D " + logad.replace(".bin", ""), "askı (birleşik)", ab)
            r[20:23] = [None, None, None]  # askı bloğunda çift farkları uçuş başına liste; K_D sayfasında
            satirlar.append(r)
    out.append(T("E_VIBE_Gaz_Bandi", "E (tam gaz) ve D (askı) — CTUN.ThO bandına göre VIBE ve motor çıkışı", sut, satirlar,
                 "E_1240_tam_gaz/ozet.json › kiyas_D", not_=kd["yontem"]))
    return out


# ----------------------------------------------------------------------------- F logu (13-11-32)
def f_tablolari():
    F = oku_json("F_1311_aski_4S_13Ah/ozet.json")
    K = "F_1311_aski_4S_13Ah/ozet.json"
    out = []
    a = F["aski"]
    sut = ["büyüklük", "birim", "n", "ort", "p50", "p05", "p95", "min", "maks", "std"]
    satirlar = [["ThO (CTUN)", "—"] + ist(a["ThO"]), ["ThI (pilot/komut)", "—"] + ist(a["ThI"]),
                ["V (ham)", "V"] + ist(a["V"]), ["VoltR (sarkma telafili, FC)", "V"] + ist(a["VoltR_dinlenme_tahmini_FC"]),
                ["I", "A"] + ist(a["I_A"]), ["P", "W"] + ist(a["P_W"]), ["irtifa", "m"] + ist(a["alt_m"]),
                ["V hücre", "V/hücre", None, a["V_hucre"]["ort"], None, None, None, a["V_hucre"]["min"], a["V_hucre"]["maks"], None]]
    out.append(T("F_Aski_Istatistik", "F logu (15 Eyl 13-11-32, 4S 13 Ah + 9x5x3, GUIDED) — askı dağılım istatistikleri (n = 629, 62,9 s)",
                 sut, satirlar, K + " › aski"))
    # uçuş özeti (skalar)
    u, p, tu, rc, ek, ho = F["ucus"], F["pil"], F["tutum"], F["rcou"], F["ekf_olaylar"], F["ucus"]["hover_ogrenme"]
    c9 = rc["C9_C12_motorlar_aski"]
    sut = ["grup", "büyüklük", "değer", "birim / not"]
    S = []
    S += [["uçuş", "arm t", u["arm_t"], "s (" + u["arm_yontemi"] + ", " + u["kip_arm"] + ")"],
          ["uçuş", "disarm t", u["disarm_t"], "s (" + u["disarm_yontemi"] + ")"],
          ["uçuş", "pencere", u["pencere_s"], "s"], ["uçuş", "motorlu", u["motorlu_s"], "s"],
          ["uçuş", "askı", u["aski_s"], "s"], ["uçuş", "irtifa maks", u["alt_maks_m"], "m (CTUN.Alt)"],
          ["uçuş", "irtifa maks POS.RelHomeAlt", u["alt_maks_m_POS_RelHomeAlt"], "m"],
          ["uçuş", "irtifa taban", u["alt_taban_m_CTUN_Alt"], "m"],
          ["uçuş", "ThO motorlu ort / p50 / p95", f"{yuvarla_metin(u['ThO_motorlu']['ort'])} / {yuvarla_metin(u['ThO_motorlu']['p50'])} / {yuvarla_metin(u['ThO_motorlu']['p95'])}", ""],
          ["askı", "n", a["n"], "örnek"], ["askı", "dilim n", a["dilim_n"], ""],
          ["askı", "en uzun dilim", a["en_uzun_dilim_s"], f"s ({a['en_uzun_dilim_t'][0]}–{a['en_uzun_dilim_t'][1]})"],
          ["askı", "|vz| ort", a["vz_abs_ort_ms"], "m/s"], ["askı", "mAh/s", a["mAh_per_s"], ""], ["askı", "mAh/dk", a["mAh_per_dk"], ""],
          ["askı", "MOT_THST_HOVER", a["MOT_THST_HOVER_vs_ThO"]["MOT_THST_HOVER"], ""],
          ["askı", "ThO askı ort", a["MOT_THST_HOVER_vs_ThO"]["ThO_aski_ort"], ""],
          ["askı", "ThH − ThO fark", a["MOT_THST_HOVER_vs_ThO"]["fark"], f"%{yuvarla_metin(a['MOT_THST_HOVER_vs_ThO']['fark_pct_ThO'])} (ThO'ya göre)"],
          ["öğrenme", "MOT_HOVER_LEARN", ho["MOT_HOVER_LEARN"], ""], ["öğrenme", "havada s", ho["havada_s_EV28_EV17"], "s"],
          ["öğrenme", "uygun s", ho["uygun_s"], "s (GUIDED'da öğrenme çalışmaz)"],
          ["öğrenme", "is_zero(PSCD.DVD) oranı", ho["kosul_oranlari_havada"]["is_zero(PSCD.DVD)"], ho["not"]],
          ["öğrenme", "|VD|<0,6 m/s oranı", ho["kosul_oranlari_havada"]["|VD|<0.6m/s"], ""],
          ["öğrenme", "|roll|,|pitch|<5° oranı", ho["kosul_oranlari_havada"]["|roll|,|pitch|<5deg"], ""],
          ["pil", "V ilk (log)", p["V_ilk_log"], "V"], ["pil", "V ilk hücre", p["V_ilk_hucre"], "V/hücre (dolu değil)"],
          ["pil", "V arm öncesi 5 s ort", p["V_arm_oncesi_5s_ort"], "V"], ["pil", "V min", p["V_min"], f"V @ {yuvarla_metin(p['V_min_I'])} A, t {yuvarla_metin(p['V_min_t'])}"],
          ["pil", "V min hücre", p["V_min_hucre"], "V/hücre"], ["pil", "VoltR min", p["VoltR_min"], "V"],
          ["pil", "sarkma ilk → askı", p["sarkma_V_ilk_askiya"], "V"], ["pil", "sarkma ilk → min", p["sarkma_V_ilk_min"], "V"],
          ["pil", "sarkma hücre ilk → min", p["sarkma_V_hucre_ilk_min"], "V/hücre"],
          ["pil", "toparlanma disarm+10 s", p["toparlanma_V_disarm_10s"], "V"],
          ["pil", "I motorlu ort / p95 / maks", f"{yuvarla_metin(p['I_motorlu']['ort'])} / {yuvarla_metin(p['I_motorlu']['p95'])} / {yuvarla_metin(p['I_motorlu']['maks'])}", "A"],
          ["pil", "mAh pencere", p["mAh_pencere"], "mAh"], ["pil", "mAh motorlu", p["mAh_motorlu"], "mAh"],
          ["pil", "Wh pencere", p["Wh_pencere"], "Wh"], ["pil", "mAh log toplam", p["mAh_log_toplam"], "mAh"],
          ["pil", "RemPct son (BATT_CAPACITY 8000)", p["RemPct_son_log_BATT_CAPACITY_8000"], "%"],
          ["pil", "RemPct 13000 ile HESAP", p["RemPct_13000_ile_HESAP"], "% (HESAP)"],
          ["pil", "BAT.Temp", p["BAT_Temp"], ""],
          ["tutum askı", "roll RMS hata", tu["aski"]["roll_rms_hata_deg"], "°"], ["tutum askı", "pitch RMS hata", tu["aski"]["pitch_rms_hata_deg"], "°"],
          ["tutum askı", "yaw RMS hata", tu["aski"]["yaw_rms_hata_deg"], "°"],
          ["tutum askı", "roll hız RMS hata", tu["aski_hiz"]["roll_rate_rms_hata_dps"], "°/s"],
          ["tutum askı", "pitch hız RMS hata", tu["aski_hiz"]["pitch_rate_rms_hata_dps"], "°/s"],
          ["tutum askı", "yaw hız RMS hata", tu["aski_hiz"]["yaw_rate_rms_hata_dps"], "°/s"],
          ["tutum askı", "ROut / POut / YOut ort", f"{yuvarla_metin(tu['aski_hiz']['ROut_ort'])} / {yuvarla_metin(tu['aski_hiz']['POut_ort'])} / {yuvarla_metin(tu['aski_hiz']['YOut_ort'])}", tu["aski_hiz"]["not"]],
          ["yaw", "askı hata RMS", tu["yaw"]["aski_hata_rms_deg"], "°"], ["yaw", "askı hata maks", tu["yaw"]["aski_hata_maks_abs_deg"], "°"],
          ["yaw", "askı hata p95", tu["yaw"]["aski_hata_p95_abs_deg"], "°"],
          ["yaw", "GyrZ FFT baskın", "; ".join(f"{yuvarla_metin(t['f_hz'])} Hz ({yuvarla_metin(t['genlik'])} rad/s)" for t in tu["yaw"]["GyrZ_FFT_IMU0_baskin"]), tu["yaw"]["not"]],
          ["yaw", "YOut maks |·| / p95", f"{yuvarla_metin(tu['yaw']['YOut_maks_abs'])} / {yuvarla_metin(tu['yaw']['YOut_p95_abs'])}", ""],
          ["motor (C9–C12, askı)", "M1 / M2 / M3 / M4 ort", " / ".join(yuvarla_metin(c9["M_ort_us"][m]) for m in ["M1", "M2", "M3", "M4"]), "µs"],
          ["motor (C9–C12, askı)", "yayılım ort", c9["yayilim_ort_us"], f"µs (%{yuvarla_metin(c9['yayilim_pct_aralik'])})"],
          ["motor (C9–C12, askı)", "CCW−CW (yaw)", c9["cift_farklari_us"]["CCW(M1+M2)-CW(M3+M4)_yaw"], "µs toplam ölçek"],
          ["motor (C9–C12, askı)", "ön−arka (pitch)", c9["cift_farklari_us"]["on(M1+M3)-arka(M2+M4)_pitch"], "µs"],
          ["motor (C9–C12, askı)", "sağ−sol (roll)", c9["cift_farklari_us"]["sag(M1+M4)-sol(M2+M3)_roll"], "µs"],
          ["motor (C9–C12, askı)", "ort PWM oranı", c9["ort_pwm_orani"], ""],
          ["motor (C9–C12, askı)", "ThO'dan beklenen PWM (HESAP)", rc["ThO_aski_beklenen_pwm_HESAP"], "µs"],
          ["EKF", "SV / SP / SH / SM maks (çekirdek 0)", " / ".join(yuvarla_metin(ek["cekirdek"]["0"][k]) for k in ["SV_maks", "SP_maks", "SH_maks", "SM_maks"]), ""],
          ["EKF", "lane switch n", ek["lane_switch_n"], ""], ["EKF", "innov > 1 n", ek["cekirdek"]["0"]["innov_>1_n"], ""],
          ["GPS", "NSats min–maks", f"{ek['gps']['NSats_min_maks'][0]}–{ek['gps']['NSats_min_maks'][1]}", ""],
          ["GPS", "HDop min–maks", f"{yuvarla_metin(ek['gps']['HDop_min_maks'][0])}–{yuvarla_metin(ek['gps']['HDop_min_maks'][1])}", ""],
          ["olaylar", "ERR uçuş içinde n", ek["ERR_ucus_icinde_n"], ek["yorum"]],
          ["VIBE", "clip toplam", F["vibe"]["clip_toplam"], ""],
          ["VIBE", "askı p95 X/Y/Z (birleşik)", " / ".join(yuvarla_metin(x) for x in F["vibe"]["esik_kiyasi"]["aski_p95_XYZ"]), F["vibe"]["esik_kiyasi"]["hukum"]],
          ["log", "dosya", F["meta"]["log"]["dosya"], "sha256 " + F["meta"]["log"]["sha256"][:12]],
          ["log", "IMU Hz", F["meta"]["imu_hz"], F["meta"]["imu_not"]]]
    out.append(T("F_Ucus_Ozeti", "F logu — uçuş, askı, pil, tutum, motor, EKF özet değerleri", sut, S, K + " › ucus, aski, pil, tutum, rcou, ekf_olaylar, vibe"))
    # failsafe eşikleri
    fs = F["failsafe"]
    lp, hm, on, bl = fs["logdaki_parametreler"], fs["hucre_basina_mevcut"], fs["oneri"], fs["bu_logda_gerilim_vs_onerilen_esikler"]
    sut = ["parametre / ölçüm", "mevcut (log)", "mevcut V/hücre", "öneri", "not"]
    satirlar = [
        ["BATT_LOW_VOLT", lp["BATT_LOW_VOLT"], hm["LOW"], on["BATT_LOW_VOLT"], ""],
        ["BATT_CRT_VOLT", lp["BATT_CRT_VOLT"], hm["CRT"], on["BATT_CRT_VOLT"], ""],
        ["BATT_ARM_VOLT", lp["BATT_ARM_VOLT"], hm["ARM"], on["BATT_ARM_VOLT"], on["BATT_ARM_VOLT_not"]],
        ["BATT_CAPACITY", lp["BATT_CAPACITY"], None, on["BATT_CAPACITY"], "mAh"],
        ["BATT_LOW_MAH", lp["BATT_LOW_MAH"], None, on["BATT_LOW_MAH_oneri_HESAP"], "HESAP (%25 × 13 000)"],
        ["BATT_CRT_MAH", lp["BATT_CRT_MAH"], None, on["BATT_CRT_MAH_oneri_HESAP"], "HESAP (%15 × 13 000)"],
        ["BATT_FS_LOW_ACT / CRT_ACT", f"{yuvarla_metin(lp['BATT_FS_LOW_ACT'])} / {yuvarla_metin(lp['BATT_FS_CRT_ACT'])}", None, "koru", on["act_not"]],
        ["BATT_FS_VOLTSRC", lp["BATT_FS_VOLTSRC"], None, "1 (ya da LOW ham 13,6)", on["BATT_FS_VOLTSRC_not"]],
        ["BATT_LOW_TIMER", lp["BATT_LOW_TIMER"], None, None, "s"],
        ["BATT_VOLT_MULT", lp["BATT_VOLT_MULT"], None, None, ""], ["BATT_AMP_PERVLT", lp["BATT_AMP_PERVLT"], None, None, ""],
        ["BATT_MONITOR / FS_OPTIONS", f"{yuvarla_metin(lp['BATT_MONITOR'])} / {yuvarla_metin(lp['FS_OPTIONS'])}", None, None, ""],
        ["hüküm", fs["hukum"], None, None, ""],
        ["ölçüm: V min ham", bl["V_min_ham"], bl["V_min_ham_hucre"], None, f"t {yuvarla_metin(bl['V_min_t'])} s, I {yuvarla_metin(bl['V_min_I_A'])} A"],
        ["ölçüm: LOW 14,0 V marjı", bl["LOW_14.0V_marj_V"], None, None, "V (negatif = altına indi)"],
        ["ölçüm: CRT 13,2 V marjı", bl["CRT_13.2V_marj_V"], None, None, "V"],
        ["ölçüm: ham V < LOW toplam", bl["ham_V_LOW_altinda_toplam_s"], None, None, "s"],
        ["ölçüm: ham V < LOW en uzun koşu", bl["ham_V_LOW_altinda_en_uzun_kosu_s"], None, None, f"s (> BATT_LOW_TIMER {yuvarla_metin(bl['BATT_LOW_TIMER_s'])} s)"],
        ["ölçüm: ham V < LOW örnek oranı (motorlu)", bl["ham_V_LOW_altinda_ornek_orani_motorlu"], None, None, ""],
        ["ölçüm: ham V < CRT toplam", bl["ham_V_CRT_altinda_toplam_s"], None, None, "s"],
        ["ölçüm: VoltR < LOW toplam", bl["VoltR_LOW_altinda_toplam_s"], None, None, "s"],
        ["ölçüm: VoltR min", bl["VoltR_min"], None, None, "V"],
        ["LOW tetiklenir miydi (ham)", "evet" if bl["LOW_tetiklenir_miydi_ham"] else "hayır", None, None, ""],
        ["LOW tetiklenir miydi (VoltR)", "evet" if bl["LOW_tetiklenir_miydi_VoltR"] else "hayır", None, None, ""],
        ["ARM 14,4 V ile kalkış", bl["ARM_14.4V_ile_kalkis"], None, None, ""],
        ["mevcut 10 V eşiğine marj", bl["mevcut_10V_esigine_marj_V"], None, None, "V"],
    ]
    out.append(T("F_Failsafe_Esikleri", "F logu — pil failsafe eşikleri: mevcut (3S değerleri) vs 4S önerisi ve bu logdaki gerilim",
                 sut, satirlar, K + " › failsafe"))
    # iç direnç yöntemleri
    ic = p["ic_direnc"]
    sut = ["yöntem", "n", "I aralığı (A)", "R paket (Ω)", "R paket (mΩ)", "R hücre (mΩ)", "V kesim I=0 (V)", "r²", "seçilen"]
    satirlar = []
    for k in ["a_kalkis_gecisi", "b_inis_gecisi", "c_tum_pencere", "d_yalniz_aski"]:
        d = ic[k]
        satirlar.append([k, d["n"], f"{yuvarla_metin(d['I_aralik_A'][0])}–{yuvarla_metin(d['I_aralik_A'][1])}", d["R_paket_ohm"],
                         d["R_paket_mohm"], d["R_hucre_mohm"], d["V_kesim_I0"], d["r2"], "✓" if ic["secilen_kaynak"] == k else ""])
    e = ic["e_arm_oncesi_vs_aski"]
    satirlar.append(["e_arm_oncesi_vs_aski (D yöntemi)", None, None, e["R_paket_ohm"], None, e["R_hucre_mohm"], None, None, ""])
    f6 = ic["f_BAT_Res_FC"]
    satirlar.append(["f_BAT_Res_FC (askı ort)", None, f"pencere {yuvarla_metin(f6['pencere_min_maks_ohm'][0])}–{yuvarla_metin(f6['pencere_min_maks_ohm'][1])} Ω",
                     f6["aski_ort_ohm"], None, f6["aski_ort_mohm_hucre"], None, None, ""])
    satirlar.append(["sarkma HESAP askıda (I·R)", None, None, ic["sarkma_HESAP_askida_V"], None, None, None, None, "V"])
    satirlar.append(["sarkma ölçülen ilk → askı", None, None, ic["sarkma_olculen_ilk_askiya_V"], None, None, None, None, "V"])
    out.append(T("F_Ic_Direnc_Yontemleri", "F logu — paket iç direnci: altı yöntem (seçilen: kalkış geçişi polyfit)", sut, satirlar,
                 K + " › pil.ic_direnc", not_=ic["yontem"]))
    # uçuş süresi tahmini
    us = F["ucus_suresi"]
    y2 = us["yontem_2_3.5V_hucre"]
    sut = ["yöntem", "büyüklük", "değer", "birim", "geçerlilik / not"]
    satirlar = [
        ["1 (%80 × beyan)", "I askı", us["I_aski_A"], "A", us["yontem_1"]],
        ["1", "I motorlu", us["I_motorlu_A"], "A", ""], ["1", "P askı", us["P_aski_W"], "W", ""],
        ["1", "kullanılabilir mAh", us["kullanilabilir_mAh"], "mAh", ""],
        ["1", "tahmin (askı akımı)", us["tahmin_dk_aski_akimi"], "dk", "HESAP, dolu pil varsayımı"],
        ["1", "tahmin (motorlu ort akım)", us["tahmin_dk_motorlu_ort_akim"], "dk", ""],
        ["1", "tahmin (askı p95 akım)", us["tahmin_dk_aski_p95_akim"], "dk", ""],
        ["1", "tahmin (%100 kapasite)", us["tahmin_dk_%100_kapasite"], "dk", ""],
        ["2 (3,5 V/hücre)", "sarkma I·R", y2["sarkma_I_R_V"], "V", y2["aciklama"]],
        ["2", "V hedef yüklü", y2["V_hedef_yuklu"], "V", ""],
        ["2", "V hedef dinlenme eşdeğeri (yüklü)", y2["V_hedef_dinlenme_esdeger_yuklu"], "V", ""],
        ["2", "ölçüm: yüklü 14,0 V ilk iniş", y2["olculen_yuklu_14.0V_ilk_inis"]["aski_basindan_s"], "s (askı başından)",
         f"t {yuvarla_metin(y2['olculen_yuklu_14.0V_ilk_inis']['t'])}, {yuvarla_metin(y2['olculen_yuklu_14.0V_ilk_inis']['aski_basindan_mAh'])} mAh; " + y2["olculen_yuklu_14.0V_ilk_inis"]["not"]],
    ]
    i1 = y2["i_tum_aski_uydurma"]
    satirlar += [["2-i tüm askı", "eğim", i1["egim_V_per_Ah"], "V/Ah", i1["gecerlilik"]],
                 ["2-i", "eğim std hata", i1["egim_std_hata_V_per_Ah"], "V/Ah", ""], ["2-i", "r²", i1["r2"], "", f"n {i1['n']}"],
                 ["2-i", "yüklü 14,0 V kalan (askı başından)", i1["yuklu_14.0V_kalan_mAh_aski_basindan"], "mAh", ""],
                 ["2-i", "dinlenme 3,5 V kalan (askı başından)", i1["dinlenme_3.5V_kalan_mAh_aski_basindan"], "mAh", ""],
                 ["2-i", "dinlenme 3,5 V kalan", i1["dinlenme_3.5V_kalan_dk"], "dk", ""]]
    i2 = y2["ii_plato_uydurma_TERCIH"]
    satirlar += [["2-ii plato (TERCİH)", "eğim", i2["egim_V_per_Ah"], "V/Ah", i2["gecerlilik"]],
                 ["2-ii", "eğim std hata", i2["egim_std_hata_V_per_Ah"], "V/Ah", f"t {i2['t_aralik'][0]}–{i2['t_aralik'][1]} s, n {i2['n']}"],
                 ["2-ii", "r²", i2["r2"], "", ""], ["2-ii", "V aralık ort", i2["V_aralik_ort"], "V", i2["yuklu_14.0V"]],
                 ["2-ii", "dinlenme 3,5 V kalan (askı sonundan)", i2["dinlenme_3.5V_kalan_mAh_aski_sonundan"], "mAh", ""],
                 ["2-ii", "dinlenme 3,5 V kalan (askı akımı)", i2["dinlenme_3.5V_kalan_dk_aski_akimi"], "dk", ""],
                 ["2-ii", "dinlenme 3,5 V toplam (log başından)", i2["dinlenme_3.5V_toplam_mAh_log_basindan"], "mAh", ""],
                 ["2-ii", "toplam (log başından) HESAP", i2["toplam_dk_log_basindan_HESAP"], "dk", ""]]
    i3 = y2["iii_dinlenme_gerilimi_egimi"]
    satirlar += [["2-iii dinlenme eğimi", "V log başı yüksüz", i3["V_log_basi_yuksuz"], "V", i3["not"]],
                 ["2-iii", "V log sonu yüksüz", i3["V_log_sonu_yuksuz"], "V", f"disarm sonrası {yuvarla_metin(i3['disarm_sonrasi_s'])} s"],
                 ["2-iii", "mAh", i3["mAh"], "mAh", ""], ["2-iii", "eğim", i3["egim_V_per_Ah"], "V/Ah", ""],
                 ["2-iii", "dinlenme 3,5 V kalan (ALT SINIR)", i3["dinlenme_3.5V_kalan_mAh_log_sonundan_ALT_SINIR"], "mAh", ""],
                 ["not", "—", None, "", y2["not"]]]
    out.append(T("F_Ucus_Suresi_Tahmini", "F logu — uçuş süresi tahminleri (HESAP; beyan kapasite ve gerilim ekstrapolasyonu)", sut, satirlar,
                 K + " › ucus_suresi"))
    # VIBE kapsam
    v = F["vibe"]
    sut = ["kapsam", "IMU", "eksen", "n", "ort", "p50", "p05", "p95", "min", "maks", "std"]
    satirlar = []
    for kap, ad in (("kapsam_pencere", "pencere"), ("kapsam_motorlu", "motorlu"), ("kapsam_aski", "askı")):
        for imu, dd in v[kap].items():
            for ex in ["X", "Y", "Z"]:
                satirlar.append([ad, imu, ex] + ist(dd[ex]))
    satirlar.append(["clip", "IMU0", "artış", v["clip"]["IMU0"]["artis"], None, None, None, None, None, None, None])
    satirlar.append(["clip", "IMU1", "artış", v["clip"]["IMU1"]["artis"], None, None, None, None, None, None, None])
    satirlar.append(["kalkış dilimi maks", "IMU0", "X/Y/Z", None, None, None, None, None, None, " / ".join(yuvarla_metin(x) for x in v["kalkis_dilimi_maks_XYZ"]), None])
    satirlar.append(["iniş dilimi maks", "IMU0", "X/Y/Z", None, None, None, None, None, None, " / ".join(yuvarla_metin(x) for x in v["inis_dilimi_maks_XYZ"]), None])
    out.append(T("F_VIBE_Kapsam", "F logu — VIBE (FC ivme std, m/s²) pencere / motorlu / askı × IMU0, IMU1, birleşik", sut, satirlar,
                 K + " › vibe", not_=v["esik_kiyasi"]["hukum"] + f" (eşikler {yuvarla_metin(v['esik_kiyasi']['esik_iyi_ms2'])}/{yuvarla_metin(v['esik_kiyasi']['esik_kotu_ms2'])})"))
    return out


# ----------------------------------------------------------------------------- parametre zaman çizgisi
def parametre_tablolari():
    md = oku_metin("parametre_zaman_cizgisi.md")
    J = oku_json("parametre_zaman_cizgisi.json")
    tb = md_tablolar(md)
    KM, KJ = "parametre_zaman_cizgisi.md", "parametre_zaman_cizgisi.json"
    out = []
    b, s = tablo_bul(tb, ["#", "BOOT", "hesaplanan başlangıç (yerel)"])
    out.append(T("P_Kronoloji", "Parametre zaman çizgisi §1 — 27 benzersiz log, STAT_BOOTCNT sırası", b, s, KM + " §1"))
    b, s = tablo_bul(tb, ["#", "önceki log"])
    out.append(T("P_Gorunmeyen_Sure", "Parametre zaman çizgisi §1 — loglar arası görünmeyen süre (RUNTIME / FLTTIME / takvim)", b, s, KM + " §1"))
    b, s = tablo_bul(tb, ["#", "BOOT", "log", "PARM n"])
    out.append(T("P_Sifirlama_Hipotezi", "Parametre zaman çizgisi §2 — 'parametre sıfırlaması' hipotezi imza parametreleri (DESTEKLENMEDİ)", b, s, KM + " §2"))
    b, s = tablo_bul(tb, ["#", "BOOT", "log", "MOT_THST_HOVER"])
    out.append(T("P_Izlenen_Parametreler", "Parametre zaman çizgisi §3 — izlenen parametreler, log başındaki değer (a→b: log içinde değişti)", b, s, KM + " §3"))
    # segmentler (JSON) — sayaç parametreleri hariç
    sut = ["parametre", "segment", "değer", "ilk #", "ilk log", "son #", "son log"]
    satirlar = []
    for ad, seg in J["segmentler"].items():
        if ad.startswith("STAT_") or len(seg) < 2:
            continue
        for i, sg in enumerate(seg, 1):
            satirlar.append([ad, i, sg["deger"], sg["ilk_sira"], sg["ilk_log"], sg["son_sira"], sg["son_log"]])
    out.append(T("P_Parametre_Segmentleri", "Parametre zaman çizgisi §3a — en az bir kez değişen izlenen parametrelerin değer segmentleri (STAT_* hariç)",
                 sut, satirlar, KJ + " › segmentler"))
    # kullanıcı / öğrenme / kalibrasyon değişimleri (JSON)
    sut = ["#", "BOOT", "log", "yer", "t (s)", "saat", "parametre", "eski", "yeni", "default", "sınıf", "kim", "armed"]
    satirlar = [[x["sira"], x["BOOTCNT"], x["log"], x["yer"], x["t_s"], x["saat"], x["ad"], x["eski"], x["yeni"], x["default"],
                 x["sinif"], x["kim"], x.get("armed")] for x in J["degisimler"] if x["sinif"] in ("KULLANICI", "OGRENME", "KALIBRASYON")]
    out.append(T("P_Kullanici_Degisimleri", "Parametre zaman çizgisi §4a — kullanıcı / öğrenme / kalibrasyon değişimleri (SAYAC, OTOMATIK, GCS_AKIS hariç)",
                 sut, satirlar, KJ + " › degisimler (sinif ∈ KULLANICI, OGRENME, KALIBRASYON)"))
    b, s = tablo_bul(tb, ["#", "log", "t s"])
    out.append(T("P_Kritik_Olaylar", "Parametre zaman çizgisi §5a — kritik olaylar (ERR, failsafe MODE, failsafe/thrust-loss/EKF/kip-red/motor-test MSG)", b, s, KM + " §5a"))
    b, s = tablo_bul(tb, ["#", "log", "arm", "arm_ret"])
    out.append(T("P_Olay_Matrisi", "Parametre zaman çizgisi §6 — olay sınıfı × log matrisi", b, s, KM + " §6"))
    # sayımlar
    sut = ["grup", "anahtar", "n"]
    satirlar = []
    for grup in ["degisim_sayim", "degisim_sayim_izlenen", "olay_sayim", "olay_sayim_tur", "kritik_olay_sayim"]:
        for k, v in J[grup].items():
            satirlar.append([grup, k, v])
    for m in re.finditer(r"^- `([A-Z0-9_]+)` \((\w+)\): (\d+) kez", md, flags=re.M):
        satirlar.append(["otomatik/sayaç/GCS-akış değişimi (§4b)", f"{m.group(1)} ({m.group(2)})", int(m.group(3))])
    out.append(T("P_Sayimlar", "Parametre zaman çizgisi — değişim ve olay sayımları (§4, §4b, §5, §5a)", sut, satirlar, KJ + " › *_sayim; " + KM + " §4b"))
    return out


# ----------------------------------------------------------------------------- tum_loglar.json envanteri
def _fl(u, *yol):
    return g(u, *yol)


def log_tablolari():
    L = oku_json("tum_loglar.json")
    P = oku_json("parametre_zaman_cizgisi.json")
    saatler = {x["ad"]: x["saat"] for x in P["loglar"]}
    beyanlar = {x["ad"]: x["beyan"] for x in P["loglar"]}
    siralar = {x["ad"]: x["sira"] for x in P["loglar"]}
    out = []
    sut = ["#", "dosya", "başlangıç (yerel)", "BOOT", "MP no", "kopya", "süre (s)", "hücre", "V ilk", "konfig", "pil (beyan)", "pervane (beyan)",
           "uçuş n", "kısa sıçrama n", "yalnız arm n", "motorlu toplam (s)", "askı toplam (s)", "irtifa maks (m)",
           "askı ThO p50 (uçuş başına)", "askı I ort A (uçuş başına)", "askı VibeZ ort (uçuş başına)", "VibeZ maks (motorlu)",
           "VibeZ maks (pencere)", "clip artışı", "failsafe n", "ThH log sonu", "sha256"]
    satirlar = []
    for x in sorted(L["loglar"], key=lambda z: (z["sira"]["STAT_BOOTCNT"], z["sira"]["STAT_RUNTIME_ilk_s"])):
        ad = Path(x["dosya"]).name
        oz = x["ozet"]
        ucuslar = [u for u in x["ucuslar"] if u["tur"] == "ucus"]
        aski_top = round(sum(u["aski_s"] for u in ucuslar), 1) if ucuslar else 0.0
        tho = " / ".join(yuvarla_metin(_fl(u, "aski", "ThO_p50")) for u in ucuslar if _fl(u, "aski")) or "—"
        iak = " / ".join(yuvarla_metin(_fl(u, "bat", "aski", "I_ort")) for u in ucuslar if _fl(u, "bat", "aski")) or "—"
        vz = " / ".join(yuvarla_metin(_fl(u, "vibe", "aski", "Z")) for u in ucuslar if _fl(u, "vibe", "aski")) or "—"
        clip = sum((_fl(u, "vibe", "clip_toplam") or 0) for u in x["ucuslar"])
        thh = x["ucuslar"][-1]["ThH_son"] if x["ucuslar"] else x["parm"].get("MOT_THST_HOVER")
        satirlar.append([siralar.get(ad), ad, saatler.get(ad), x["sira"]["STAT_BOOTCNT"], x["mp_no"],
                         "; ".join(Path(k).name for k in x["kopyalar"]) or "", x["log_suresi_s"], x["hucre"]["n"], x["hucre"]["V_ilk"],
                         x["kullanici_beyani"]["etiket"] or beyanlar.get(ad), x["kullanici_beyani"]["pil"], x["kullanici_beyani"]["pervane"],
                         oz["ucus_n"], oz["kisa_sicrama_n"], oz["arm_yalniz_n"], oz["toplam_motorlu_s"], aski_top, oz["alt_maks_m"],
                         tho, iak, vz, oz["vibeZ_maks"], oz["vibeZ_pencere_maks"], clip, oz["failsafe_n"], thh, x["sha256"][:12]])
    # E ve F logları (ayrı analiz klasörleri)
    ET = oku_json("E_1240_tam_gaz/ozet.json")
    e = ET["log"]
    eu = e["ucuslar"][0]
    satirlar.append([28, Path(e["dosya"]).name, "2026-09-15 12:40:55 (dosya adı)", None, None, "", e["log_suresi_s"], e["hucre"]["n"], e["hucre"]["V_ilk"],
                     "E", e["kullanici_beyani"]["pil"], e["kullanici_beyani"]["pervane"], 1, 0, 0, eu["motorlu_s"], eu["aski"]["s"], eu["alt_maks_m"],
                     "— (askı yok)", "—", "—", g(eu, "vibe", "kapsam_motorlu", "IMU0", "Z", "maks"), g(eu, "vibe", "kapsam_pencere", "IMU0", "Z", "maks"),
                     g(eu, "vibe", "kapsam_pencere", "IMU0", "clip_artis"), 0, eu["ThH"]["son"], e["sha256"][:12]])
    F = oku_json("F_1311_aski_4S_13Ah/ozet.json")
    fl, fu, fa = F["meta"]["log"], F["ucus"], F["aski"]
    satirlar.append([29, Path(fl["dosya"]).name, "2026-09-15 13:11:32 (dosya adı)", fl["STAT_BOOTCNT"], None, "", round(fl["log_t_son"] - fl["log_t_ilk"], 1),
                     F["pil"]["hucre_n"], F["pil"]["V_ilk_log"], "F", F["meta"]["kullanici_beyani"]["pil"], F["meta"]["kullanici_beyani"]["pervane"],
                     1, 0, 0, fu["motorlu_s"], fu["aski_s"], fu["alt_maks_m"], yuvarla_metin(fa["ThO"]["p50"]), yuvarla_metin(fa["I_A"]["ort"]),
                     yuvarla_metin(g(F, "vibe", "kapsam_aski", "IMU0", "Z", "ort")), g(F, "vibe", "kapsam_motorlu", "IMU0", "Z", "maks"),
                     g(F, "vibe", "kapsam_pencere", "IMU0", "Z", "maks"), F["vibe"]["clip_toplam"], F["ekf_olaylar"]["ERR_ucus_icinde_n"], fu["ThH_son"], fl["sha256"][:12]])
    out.append(T("L_Log_Envanteri", "Log envanteri — 27 benzersiz log (tum_loglar.json) + E (12-40-55) + F (13-11-32) = 29", sut, satirlar,
                 "tum_loglar.json › loglar[*].ozet/ucuslar; parametre_zaman_cizgisi.json › saat; E_1240_tam_gaz/ozet.json; F_1311_aski_4S_13Ah/ozet.json",
                 "askı toplam = aynı logdaki uçuş pencerelerinin askı sürelerinin toplamı; uçuş başına değerler '/' ile ayrılmış metin. "
                 "E/F satırlarında süre = log_t_son − log_t_ilk (F) ve log_suresi_s (E). RCOU C1–C4 alanı bu dosyada motor dengesi için GEÇERSİZ, tabloya alınmadı."))
    # arm pencereleri
    sut = ["log", "konfig", "no", "tür", "kip (arm)", "arm t (s)", "disarm t (s)", "pencere (s)", "motorlu (s)", "irtifa maks (m)", "askı n", "askı s",
           "ThO motorlu ort", "ThO maks", "askı ThO ort", "askı ThO p50", "askı ThO p95", "askı irtifa ort (m)", "V baş", "V min", "V min t", "I ort A", "I p95 A", "I maks A", "mAh",
           "askı V ort", "askı I ort", "askı I p95", "askı P W", "VibeX ort", "VibeY ort", "VibeZ ort", "VibeZ p95", "VibeZ maks (pencere)",
           "askı VibeX", "askı VibeY", "askı VibeZ", "clip artışı", "roll RMS hata °", "pitch RMS hata °", "askı roll RMS °", "askı pitch RMS °",
           "EKF SV maks (C0)", "EKF SM maks (C0)", "lane switch n", "iniş kipi", "iniş nedeni", "failsafe n", "ThH baş", "ThH son", "notlar"]
    satirlar = []
    for x in sorted(L["loglar"], key=lambda z: (z["sira"]["STAT_BOOTCNT"], z["sira"]["STAT_RUNTIME_ilk_s"])):
        ad = Path(x["dosya"]).name
        for u in x["ucuslar"]:
            b, v, a, at, ek = u.get("bat") or {}, u.get("vibe") or {}, u.get("aski") or {}, u.get("att") or {}, u.get("ekf") or {}
            satirlar.append([ad, x["kullanici_beyani"]["etiket"], u["no"], u["tur"], u.get("kip_arm"), u["arm_t"], u["disarm_t"], u["pencere_s"], u["motorlu_s"], u["alt_maks_m"],
                             u["aski_n"], u["aski_s"], u.get("ThO_motorlu_ort"), u.get("ThO_maks"), a.get("ThO_ort"), a.get("ThO_p50"), a.get("ThO_p95"), a.get("alt_ort_m"),
                             b.get("V_bas"), b.get("V_min"), b.get("V_min_t"), b.get("I_ort"), b.get("I_p95"), b.get("I_maks"), b.get("mAh"),
                             g(b, "aski", "V_ort"), g(b, "aski", "I_ort"), g(b, "aski", "I_p95"), g(b, "aski", "P_W"),
                             g(v, "X", "ort"), g(v, "Y", "ort"), g(v, "Z", "ort"), g(v, "Z", "p95"), g(v, "pencere_maks", "Z"),
                             g(v, "aski", "X"), g(v, "aski", "Y"), g(v, "aski", "Z"), v.get("clip_toplam"),
                             at.get("roll_rms_hata_deg"), at.get("pitch_rms_hata_deg"), g(at, "aski", "roll_rms_hata_deg"), g(at, "aski", "pitch_rms_hata_deg"),
                             g(ek, "cekirdek", "0", "SV_maks"), g(ek, "cekirdek", "0", "SM_maks"), len(ek.get("lane_switch") or []),
                             g(u, "inis", "kip"), g(u, "inis", "rsn_ad"), len(u.get("failsafe") or []), u.get("ThH_bas"), u.get("ThH_son"),
                             "; ".join(u.get("notlar") or [])])
    out.append(T("L_Arm_Pencereleri", "Arm pencereleri — 27 logdaki tüm uçuş / kısa sıçrama / yalnız-arm pencereleri (ortak araç, ucus_bin_analiz.py)",
                 sut, satirlar, "tum_loglar.json › loglar[*].ucuslar[*]",
                 "VIBE sütunları IMU0, kapsam motorlu (askı sütunları askı örneklemi). Kısa sıçrama < 5 s motorlu; askı istatistiği yalnız ≥ 10 örnekte."))
    return out


# ----------------------------------------------------------------------------- konfigürasyon bazlı (A/B/C/D + F)
def konfig_tablolari():
    A = oku_json("A_3S_1045/ozet.json")
    B = oku_json("B_4S_1045/ozet.json")
    C = oku_json("C_3S_9x5x3/ozet.json")
    D = oku_json("D_4S_9x5x3/ozet.json")
    F = oku_json("F_1311_aski_4S_13Ah/ozet.json")
    out = []
    # --- sayısal konfig karşılaştırması (A/B/C/D: D ozet; F: F ozet kıyas bloğu)
    kk = D["konfig_karsilastirma"]["konfig"]
    fb = F["kiyas_C_D"]["F_bu_log"]
    sut = ["metrik", "A 3S+1045", "B 4S+1045", "C 3S+9x5x3", "D 4S+9x5x3", "F 4S 13Ah+9x5x3 (ref.)"]

    def ar(v):
        return None if v is None else (f"{yuvarla_metin(v[0])}–{yuvarla_metin(v[1])}" if isinstance(v, list) else v)
    satirlar = [
        ["pil + pervane"] + [kk[k]["pil_pervane"] for k in "ABCD"] + [fb["pil_pervane"]],
        ["uçuş n"] + [kk[k]["ucus_n"] for k in "ABCD"] + [fb["ucus_n"]],
        ["kısa sıçrama n"] + [kk[k]["kisa_sicrama_n"] for k in "ABCD"] + [0],
        ["askı toplam (s)"] + [kk[k]["aski_toplam_s"] for k in "ABCD"] + [fb["aski_s"]],
        ["askı ThO p50 (ağırlıklı)"] + [kk[k]["aski_ThO_p50_agirlikli"] for k in "ABCD"] + [fb["aski_ThO_p50"]],
        ["askı VibeZ ort (ağırlıklı, IMU0)"] + [kk[k]["aski_VibeZ_ort_agirlikli"] for k in "ABCD"] + [fb["vibe_aski_ort_XYZ"][2]],
        ["askı I ort (A, ağırlıklı)"] + [kk[k]["aski_I_ort_agirlikli"] for k in "ABCD"] + [fb["aski_I_A"]],
        ["askı V ort (V, ağırlıklı)"] + [kk[k]["aski_V_ort_agirlikli"] for k in "ABCD"] + [fb["aski_V"]],
        ["askı P (W, ağırlıklı)"] + [kk[k]["aski_P_W_agirlikli"] for k in "ABCD"] + [fb["aski_P_W"]],
        ["kısa sıçrama VibeZ p95 ort"] + [kk[k]["kisa_sicrama_VibeZ_p95_ort"] for k in "ABCD"] + [None],
        ["MOT_THST_HOVER log sonu aralığı"] + [ar(kk[k]["ThH_son_araligi"]) for k in "ABCD"] + [fb["MOT_THST_HOVER"]],
        ["V ilk aralığı (V)"] + [ar(kk[k]["V_ilk_araligi"]) for k in "ABCD"] + [F["pil"]["V_ilk_log"]],
        ["askı VIBE p95 X/Y/Z (bu analiz)", None, None, " / ".join(yuvarla_metin(x) for x in F["kiyas_C_D"]["C"]["vibe_aski_p95_XYZ"]),
         " / ".join(yuvarla_metin(x) for x in F["kiyas_C_D"]["D"]["vibe_aski_p95_XYZ"]), " / ".join(yuvarla_metin(x) for x in fb["vibe_aski_p95_XYZ"])],
        ["clip (uçuş)", A["titresim"]["clip_toplam_ucus"], B["ozet_sayilar"]["clip_artisi_09-26-58"]["toplam"], F["kiyas_C_D"]["C"]["clip"],
         F["kiyas_C_D"]["D"]["clip_ucus"], fb["clip"]],
    ]
    fd = F["kiyas_C_D"]["F_vs_D_ayni_konfig"]
    satirlar.append(["F − D farkı (aynı konfig)", None, None, None, None,
                     f"ThO ort {yuvarla_metin(fd['ThO_ort_fark'])} (%{yuvarla_metin(fd['ThO_ort_fark_pct'])}); I {yuvarla_metin(fd['I_fark_A'])} A; "
                     f"P {yuvarla_metin(fd['P_fark_W'])} W (%{yuvarla_metin(fd['P_fark_pct'])}); V {yuvarla_metin(fd['V_fark'])}; VibeZ ort {yuvarla_metin(fd['VibeZ_ort_fark'])}"])
    out.append(T("K_Konfig_Sayisal", "Konfigürasyon karşılaştırması — sayısal özet (A/B/C/D: tum_loglar.json ağırlıklı; F: F analizi)", sut, satirlar,
                 "D_4S_9x5x3/ozet.json › konfig_karsilastirma; F_1311_aski_4S_13Ah/ozet.json › kiyas_C_D; A/B ozet.json › clip",
                 "A/B/C/D değerleri tum_loglar.json'dan askı süresi ağırlıklı (yalnız tur=ucus); B'de askı yok."))

    # --- A uçuş bazında (16 askılı uçuş): kaynakları etiketle birleştir
    def anahtar(etiket):
        on, n = etiket.rsplit(" #", 1)
        return on, int(n)
    tho = {anahtar(e[0]): e for e in A["aski_gazi"]["ucus_bazinda_ThO_p50"]}
    vib = {anahtar(e[0]): e for e in A["titresim"]["ucus_bazinda_aski_IMU0"]}
    mot = {anahtar(e["ucus"]): e for e in A["motor_dengesi"]["ucus_bazinda"]}
    clp = {anahtar(e[0]): e for e in A["titresim"]["clipli_ucuslar"]}
    taban = {}
    for r in C["taban_satirlari"]["A"]:
        taban[(r["log"].replace(".bin", ""), r["ucus"])] = r

    def taban_bul(on, n):
        for (lg, nn), r in taban.items():
            if nn == n and lg.startswith(on):
                return r
        return {}
    sut = ["uçuş", "kip", "askı s", "askı ThO p50", "askı ThO ort", "askı V (V)", "askı I (A)", "askı P (W)", "askı irtifa (m)",
           "VibeX ort", "VibeY ort", "VibeZ ort", "VibeZ p95", "M1 µs", "M2 µs", "M3 µs", "M4 µs", "CCW−CW (yaw)", "ön−arka (pitch)", "sağ−sol (roll)",
           "yaw hız RMS °/s", "yaw hata RMS °", "clip", "pencere VIBE maks X/Y/Z"]
    satirlar = []
    for k, e in tho.items():
        on, n = k
        v, m, c, tb_ = vib.get(k), mot.get(k), clp.get(k), taban_bul(on, n)
        mm = (m or {}).get("M1_M4") or {}
        satirlar.append([e[0], e[3], e[2], e[1], tb_.get("ThO_aski"), tb_.get("V_aski"), tb_.get("I_aski"), tb_.get("P_aski"), tb_.get("alt_aski_m"),
                         v[1] if v else None, v[2] if v else None, v[3] if v else None, v[4] if v else None,
                         mm.get("M1"), mm.get("M2"), mm.get("M3"), mm.get("M4"), (m or {}).get("ccw_eksi_cw"), (m or {}).get("on_eksi_arka"), (m or {}).get("sag_eksi_sol"),
                         (m or {}).get("yaw_rate_rms_dps"), (m or {}).get("yaw_hata_rms_deg"), c[1] if c else 0,
                         " / ".join(yuvarla_metin(c[2][x]) for x in "XYZ") if c else ""])
    out.append(T("K_A_Ucus_Bazinda", "A (3S + 1045, 12–13 Eyl) — askılı 16 uçuşun uçuş bazında değerleri", sut, satirlar,
                 "A_3S_1045/ozet.json › aski_gazi.ucus_bazinda_ThO_p50, titresim.ucus_bazinda_aski_IMU0, motor_dengesi.ucus_bazinda, titresim.clipli_ucuslar; "
                 "C_3S_9x5x3/ozet.json › taban_satirlari.A (askı V/I/P/irtifa)",
                 "Çift farkları toplam ölçek (M1+M2)−(M3+M4) vb. µs; motor kanalları C9–C12. Askı ThO ort/V/I/P sütunları tum_loglar.json kökenli (C analizi taban satırları)."))
    # A pil failsafe gözlemi
    pf = A["aski_akim_guc"]["pil_failsafe_gozlemi"]
    sut = ["uçuş", "arm t", "FS t", "arm'dan FS (s)", "motorludan FS (s)", "mAh FS anına kadar", "V baş", "V min uçuş", "VoltR min uçuş", "V FS anında",
           "BATT_LOW_VOLT o anda", "BATT_CRT_VOLT o anda", "BATT_LOW_TIMER", "V ilk 10 V altı t", "V ilk eşik altı t", "mesaj"]
    satirlar = [[x["ucus"], x["arm_t"], x["fs_t"], x["armdan_fs_s"], x["motorludan_fs_s"], x["mAh_fs_anina_kadar"], x["V_bas"], x["V_min_ucus"], x["VoltR_min_ucus"],
                 x["V_fs_aninda"], x["BATT_LOW_VOLT_o_anda"], x["BATT_CRT_VOLT_o_anda"], x["BATT_LOW_TIMER"], x["V_ilk_10V_alti_t"], x["V_ilk_esik_alti_t"],
                 "; ".join(x["msg"])] for x in pf]
    gs = A["gerilim_sarkmasi"]
    ks = A["kisa_sicramalar"]
    satirlar.append(["— A havuzu: uçuş sarkma V/hücre ort / p95", gs["ucus_sarkma_hucre_V"]["ort"], gs["ucus_sarkma_hucre_V"]["p95"], None, None, None, gs["ucus_V_bas_ort"],
                     gs["ucus_V_min_ort"], None, None, None, None, None, None, None, "askı sarkma ort " + yuvarla_metin(gs["aski_sarkma_hucre_V"]["ort"]) + "; R uydurma p50 " + yuvarla_metin(gs["R_uydurma_ohm_paket"]["p50"]) + " Ω; BAT.Res ort " + yuvarla_metin(gs["Res_FC_ohm"]["ort"]) + " Ω"])
    satirlar.append(["— A kısa sıçramalar (12)", None, None, None, None, None, None, ks["V_min_V"]["min"], None, None, None, None, None, None, None,
                     f"V_min hücre {yuvarla_metin(ks['V_min_hucre_min'])} V; I maks {yuvarla_metin(ks['I_maks_A']['maks'])} A; clip {ks['clip_toplam']}; " + ks["not"]])
    out.append(T("K_A_Pil_Failsafe", "A (3S + 1045) — dört pil failsafe olayı ve sarkma havuzu", sut, satirlar,
                 "A_3S_1045/ozet.json › aski_akim_guc.pil_failsafe_gozlemi, gerilim_sarkmasi, kisa_sicramalar"))

    # --- B sıçramalar
    sa = B["sicrama_yer_hava_ayrimi"]
    sut = ["sıçrama no", "kip", "motorlu (s)", "irtifa maks (m)", "havada n (alt>0,2)", "yerde motorlu n", "askı vekili n", "ThO vekil ort",
           "VibeZ IMU0 havada ort", "VibeZ IMU0 yerde ort", "roll hız RMS hata havada (°/s)", "roll hız RMS hata yerde (°/s)",
           "|R| maks (°/s)", "ROut maks", "GyrX FFT tepe (Hz)", "GyrX FFT genlik (rad/s)", "V min hücre", "sarkma V/hücre", "I havada ort (A)", "clip artışı"]
    penc = {p_["no"]: p_ for L in B["loglar"] for p_ in (L.get("pencereler") or []) if Path(L["dosya"]).name.startswith("2026-09-13 09-26-58")}
    satirlar = []
    for x in sa:
        p_ = penc.get(x["no"], {})
        rt = g(p_, "rate", "havada") or g(p_, "rate", "motorlu") or {}
        fft = g(p_, "imu_fft", "IMU0", "GyrX", "tepeler", 0) or {}
        satirlar.append([x["no"], x["kip"], x["motorlu_s"], x["alt_maks_rel_m"], x["hava_alt>0.2_n"], x["yer_motorlu_n"], x["aski_vekil_n"], x["ThO_vekil_ort"],
                         x["VibeZ_IMU0_hava_ort"], x["VibeZ_IMU0_yer_ort"], x["roll_rate_rms_hata_hava_dps"], x["roll_rate_rms_hata_yer_dps"],
                         rt.get("R_maks_abs_dps"), rt.get("ROut_maks_abs"), fft.get("f_hz"), fft.get("genlik"),
                         g(p_, "bat", "hucre_min_V"), g(p_, "bat", "sarkma_V_hucre"), g(p_, "bat", "I_havada", "ort"),
                         (g(p_, "vibe", "IMU0", "clip_artisi") or 0) + (g(p_, "vibe", "IMU1", "clip_artisi") or 0)])
    out.append(T("K_B_Sicramalar", "B (4S + 1045, 13 Eyl 09-26-58) — altı kısa sıçramanın yer/hava ayrımı ve ~4 Hz salınım ölçütleri", sut, satirlar,
                 "B_4S_1045/ozet.json › sicrama_yer_hava_ayrimi, loglar[09-26-58].pencereler[*].rate/imu_fft/bat/vibe",
                 "Gerçek uçuş yok; askı ölçütü hiçbir pencerede sağlanmadı. |R| maks / ROut / GyrX FFT pencere 'havada' (yoksa 'motorlu') kapsamı."))
    # B havuz
    hv = B["havuz_6_sicrama_09-26-58"]
    sut = ["büyüklük", "motorlu", "havada (alt > 0,2 m)", "yerde motorlu", "askı vekili"]
    kaps = ["motorlu", "hava_alt", "yer_alt", "aski_vekil"]

    def hv_sat(ad, *yol):
        return [ad] + [g(hv[k], *yol) for k in kaps]
    satirlar = [hv_sat("n (CTUN)", "n_ctun")]
    for buy in ["ThO", "I_A", "P_W"]:
        for st in ["ort", "p50", "p95", "maks", "min"]:
            satirlar.append(hv_sat(f"{buy} {st}", buy, st))
    for imu in ["VIBE_IMU0", "VIBE_IMU1"]:
        for ex in "XYZ":
            for st in ["ort", "p95", "maks"]:
                satirlar.append(hv_sat(f"{imu} {ex} {st}", imu, ex, st))
    satirlar.append(["RCOU M1/M2/M3/M4 ort µs"] + [" / ".join(yuvarla_metin(v) for v in (g(hv[k], "RCOU_M1_M4_ort") or [])) or None for k in kaps])
    satirlar.append(hv_sat("RCOU yayılım µs", "RCOU_yayilim_pwm"))
    satirlar.append(["RCOU M1–M4 std µs"] + [" / ".join(yuvarla_metin(v) for v in (g(hv[k], "RCOU_M1_M4_std") or [])) or None for k in kaps])
    satirlar.append(hv_sat("roll hız RMS hata °/s", "roll_rate_rms_hata_dps"))
    satirlar.append(hv_sat("pitch hız RMS hata °/s", "pitch_rate_rms_hata_dps"))
    out.append(T("K_B_Havuz", "B (4S + 1045) — 6 sıçrama havuzu: motorlu / havada / yerde / askı vekili", sut, satirlar,
                 "B_4S_1045/ozet.json › havuz_6_sicrama_09-26-58"))
    # B komşu 3S kıyası
    ks3 = B["karsilastirma_3S_1045_komsu_loglar"]["satirlar"]
    sut = ["log (3S+1045, komşu)", "kip", "motorlu (s)", "ThH baş", "ThH son",
           "kalkış 5 s: ThO ort", "I ort (A)", "VibeZ ort", "VibeZ p95", "roll hız RMS (°/s)", "pitch hız RMS (°/s)", "|R| maks (°/s)", "ROut maks", "GyrX FFT tepe (Hz)", "GyrX genlik (rad/s)", "GyrX RMS (rad/s)",
           "askı dilimi: s", "ThO ort", "I ort (A)", "V ort", "VibeZ ort", "VibeZ p95", "RCOU M1–M4 ort", "roll hız RMS (°/s)", "ROut maks", "GyrX FFT tepe (Hz)", "GyrX genlik", "GyrX RMS",
           "V baş", "V min", "sarkma V", "R uyum (Ω)", "mAh", "BAT.Res ort (Ω)", "clip artışı IMU0/IMU1"]
    satirlar = []
    for r in ks3:
        k5, ad_ = r["kalkis_5s"], r["aski_dilim"]
        satirlar.append([r["log"], r["kip"], r["motorlu_s"], r["ThH"][0], r["ThH"][1],
                         g(k5, "ThO", "ort"), g(k5, "I", "ort"), g(k5, "VibeZ", "ort"), g(k5, "VibeZ", "p95"), k5.get("roll_rate_rms_hata_dps"), k5.get("pitch_rate_rms_hata_dps"),
                         k5.get("R_maks_abs_dps"), k5.get("ROut_maks_abs"), g(r, "kalkis_5s_GyrX_fft_tepe", "f_hz"), g(r, "kalkis_5s_GyrX_fft_tepe", "genlik"), r.get("kalkis_5s_GyrX_rms_rads"),
                         ad_.get("s"), g(ad_, "ThO", "ort"), g(ad_, "I", "ort"), g(ad_, "V", "ort"), g(ad_, "VibeZ", "ort"), g(ad_, "VibeZ", "p95"),
                         " / ".join(yuvarla_metin(v) for v in (ad_.get("RCOU_ort") or [])), ad_.get("roll_rate_rms_hata_dps"), ad_.get("ROut_maks_abs"),
                         g(r, "aski_GyrX_fft_tepe", "f_hz"), g(r, "aski_GyrX_fft_tepe", "genlik"), r.get("aski_GyrX_rms_rads"),
                         g(r, "bat", "V_bas"), g(r, "bat", "V_min"), g(r, "bat", "sarkma_V"), g(r, "bat", "R_uyum_ohm"), g(r, "bat", "mAh"), r.get("Res_log_ohm_ort"),
                         " / ".join(str(v) for v in r["clip_artisi"])])
    out.append(transpoze(T("K_B_3S_Komsu_Kiyas", "B kıyas tabanı — aynı gün / aynı pervane / aynı PID ile 3S+1045 komşu uçuşları (boot 118 ve 120)", sut, satirlar,
                 "B_4S_1045/ozet.json › karsilastirma_3S_1045_komsu_loglar.satirlar", B["karsilastirma_3S_1045_komsu_loglar"]["not"]),
                          lambda r: str(r[0]).replace("(boot ", " (boot ")))

    # --- C uçuş bazında
    sut = ["log", "uçuş", "askı s", "askı ThO ort", "askı ThO p50", "askı V", "askı I (A)", "askı P (W)", "askı irtifa (m)", "ThH baş", "ThH son", "ThH değişim",
           "öğrenme aktif (s)", "ilk aktif gecikme (s)", "V dinlenme arm öncesi", "V min", "I @ V min", "sarkma dinlenme→min (V/hücre)", "sarkma pencere başı→min (V/hücre)",
           "V min BATT_LOW marjı (V)", "BAT.Res medyan (mΩ)", "VibeX ort", "VibeY ort", "VibeZ ort", "VibeX p95", "VibeY p95", "VibeZ p95", "VibeZ maks", "clip",
           "M1 µs", "M2 µs", "M3 µs", "M4 µs", "yayılım µs", "en yüksek", "M1 en yüksek oranı", "CCW−CW (yaw)", "ön−arka (pitch)", "sağ−sol (roll)",
           "roll RMS hata °", "pitch RMS hata °", "yaw RMS hata °", "YOut p95", "yaw hata min/maks °", "EKF SV maks", "EKF SM maks", "HDop maks", "NSats min", "failsafe n"]
    satirlar = []
    cs = {(r["log"], r["ucus"]): r for r in C["C_ucus_satirlari"]}
    for L in C["loglar"]:
        ad = Path(L["dosya"]).name
        for u in L["ucuslar"]:
            if u["tur"] != "ucus":
                continue
            r = cs.get((ad, u["no"]), {})
            pl, og, vb, md_, tt, ek = u["pil"], u["ogrenme"], u["vibe"], u["motor_dengesi"], u["tutum"], u["ekf"]
            v0 = g(vb, "aski", "IMU0") or {}
            kb = md_.get("karisim_bileseni_pwm") or {}
            satirlar.append([ad, u["no"], u["aski_s"], r.get("ThO_aski"), r.get("ThO_p50"), r.get("V_aski"), r.get("I_aski"), r.get("P_aski"), r.get("alt_aski_m"),
                             og["ThH_bas"], og["ThH_son"], og["degisim"], og["ogrenme_aktif_s"], g(og, "olu_bant_kosu", "olu_bant_kosulari_>=3s", 0, "ilk_aktif_gecikme_s"),
                             pl["V_dinlenme_arm_oncesi"], pl["V_min"], pl["I_V_min_aninda"], pl["sarkma_hucre_V"], pl.get("sarkma_hucre_V_pencere_basi"),
                             pl["V_min_BATT_LOW_VOLT_marji_V"], pl.get("BAT_Res_AP_tahmin_mohm_medyan_motorlu"),
                             g(v0, "X", "ort"), g(v0, "Y", "ort"), g(v0, "Z", "ort"), g(v0, "X", "p95"), g(v0, "Y", "p95"), g(v0, "Z", "p95"), g(v0, "Z", "maks"), v0.get("clip_artisi"),
                             g(md_, "M1", "ort"), g(md_, "M2", "ort"), g(md_, "M3", "ort"), g(md_, "M4", "ort"), md_.get("yayilim_pwm"), md_.get("en_yuksek_ort"), g(md_, "en_yuksek_olma_orani", "M1"),
                             kb.get("yaw_CCW_eksi_CW"), kb.get("pitch_on_eksi_arka"), kb.get("roll_sag_eksi_sol"),
                             g(tt, "aski", "roll_rms_hata_deg"), g(tt, "aski", "pitch_rms_hata_deg"), g(tt, "aski", "yaw_rms_hata_deg"), g(tt, "yaw", "RATE_YOut_p95_abs"),
                             f"{yuvarla_metin(g(tt, 'yaw', 'yaw_hata_min_deg'))} / {yuvarla_metin(g(tt, 'yaw', 'yaw_hata_maks_deg'))}",
                             g(ek, "cekirdek", "0", "SV_maks"), g(ek, "cekirdek", "0", "SM_maks"), g(ek, "gps", "HDop_maks"), g(ek, "gps", "NSats_min"), u.get("failsafe_n")])
    out.append(transpoze(T("K_C_Ucus_Bazinda", "C (3S + 9x5x3, 14 Eyl mp68/mp69) — üç uçuşun uçuş bazında değerleri", sut, satirlar,
                 "C_3S_9x5x3/ozet.json › C_ucus_satirlari, loglar[*].ucuslar[*] (pil, ogrenme, vibe, motor_dengesi, tutum, ekf)",
                 "Çift farkları toplam ölçek (revizyon 2026-09-15). VIBE askı IMU0."), lambda r: f"{r[0]} uçuş {r[1]}"))

    # --- D pencereleri
    sut = ["log", "no", "tür", "kip (arm)", "arm yöntemi", "disarm yöntemi", "pencere (s)", "motorlu (s)", "irtifa maks (m)", "askı n", "askı s", "en uzun dilim (s)",
           "askı ThO ort", "askı ThO p50", "askı ThO p95", "ThO motorlu ort", "ThO motorlu maks", "gaz çubuğu ort µs", "ölü bölge içi oranı",
           "V baş", "V min", "I @ V min", "sarkma V", "sarkma V/hücre", "toparlanma V", "I motorlu ort", "I motorlu p95", "I motorlu maks", "mAh pencere",
           "askı V ort", "askı V/hücre", "askı I ort", "askı I p95", "askı P W ort", "askı P p95", "BAT.Res ort (Ω)", "R iç HESAP (Ω)", "dThO/dV (1/V)", "korr ThO–V", "korr ThO–I",
           "VibeX ort", "VibeY ort", "VibeZ ort", "VibeZ p95", "VibeZ maks", "clip IMU0+IMU1",
           "M1 µs", "M2 µs", "M3 µs", "M4 µs", "yayılım µs", "CCW−CW (yaw)", "ön−arka (pitch)", "sağ−sol (roll)",
           "roll RMS hata °", "pitch RMS hata °", "yaw RMS hata °", "roll hız RMS °/s", "pitch hız RMS °/s", "yaw hata maks °", "YDes p90 °/s",
           "EKF SV maks", "EKF SM maks", "HDop maks", "NSats min", "lane switch n", "ThH baş", "ThH son", "öğrenme uygun (s)", "failsafe n", "notlar"]
    satirlar = []
    for L in D["loglar"]:
        ad = Path(L["dosya"]).name
        for u in L["ucuslar"]:
            a, b, vb, rc, at, ah, ek, ho = u.get("aski") or {}, u.get("bat") or {}, u.get("vibe") or {}, u.get("rcou") or {}, u.get("att") or {}, g(u, "att", "aski_hiz") or {}, u.get("ekf") or {}, u.get("hover_ogrenme") or {}
            ba = b.get("aski") or {}
            vk = g(vb, "kapsam_aski", "IMU0") or g(vb, "kapsam_motorlu", "IMU0") or {}
            mo = rc.get("M_ort_pwm") or {}
            cf = rc.get("cift_farklari_pwm") or {}
            satirlar.append([ad, u["no"], u["tur"], u.get("kip_arm"), u.get("arm_yontemi"), u.get("disarm_yontemi"), u["pencere_s"], u["motorlu_s"], u["alt_maks_m"], u["aski_n"], u["aski_s"], a.get("en_uzun_dilim_s"),
                             g(a, "ThO", "ort"), g(a, "ThO", "p50"), g(a, "ThO", "p95"), g(u, "ThO_motorlu", "ort"), g(u, "ThO_motorlu", "maks"), g(a, "gaz_cubugu_RCIN_C3", "ort_us"), g(a, "gaz_cubugu_RCIN_C3", "olu_bolge_ici_orani"),
                             b.get("V_bas"), b.get("V_min"), b.get("V_min_I"), b.get("sarkma_V"), b.get("sarkma_V_hucre"), b.get("toparlanma_V"), g(b, "I_motorlu", "ort"), g(b, "I_motorlu", "p95"), g(b, "I_motorlu", "maks"), b.get("mAh_pencere"),
                             g(ba, "V", "ort"), ba.get("V_hucre_ort"), g(ba, "I", "ort"), g(ba, "I", "p95"), g(ba, "P_W", "ort"), g(ba, "P_W", "p95"), ba.get("BAT_Res_ort_ohm"), ba.get("R_ic_hesap_ohm"), ba.get("dThO_dV_egim"),
                             g(ba, "dThO_dV_gecerlilik", "korr_ThO_V"), g(ba, "dThO_dV_gecerlilik", "korr_ThO_I"),
                             g(vk, "X", "ort"), g(vk, "Y", "ort"), g(vk, "Z", "ort"), g(vk, "Z", "p95"), g(vk, "Z", "maks"), (g(vb, "clip", "IMU0", "artis") or 0) + (g(vb, "clip", "IMU1", "artis") or 0),
                             mo.get("M1"), mo.get("M2"), mo.get("M3"), mo.get("M4"), rc.get("yayilim_pwm"), cf.get("CCW(M1+M2)-CW(M3+M4)_yaw"), cf.get("on(M1+M3)-arka(M2+M4)_pitch"), cf.get("sag(M1+M4)-sol(M2+M3)_roll"),
                             g(at, "aski", "roll_rms_hata_deg"), g(at, "aski", "pitch_rms_hata_deg"), g(at, "aski", "yaw_rms_hata_deg"), ah.get("roll_rate_rms_hata_dps"), ah.get("pitch_rate_rms_hata_dps"), ah.get("yaw_hata_maks_abs_deg"), ah.get("YDes_p90_dps"),
                             g(ek, "cekirdek", "0", "SV_maks"), g(ek, "cekirdek", "0", "SM_maks"), g(ek, "gps", "HDop_maks"), g(ek, "gps", "NSats_min"), ek.get("lane_switch_n"), u.get("ThH_bas"), u.get("ThH_son"), ho.get("uygun_s"),
                             len(u.get("failsafe") or []), "; ".join(u.get("notlar") or [])])
    out.append(transpoze(T("K_D_Pencereleri", "D (4S + 9x5x3, 15 Eyl 11-14-33 / 11-18-16) — dört arm penceresinin (3 uçuş + 1 kısa sıçrama + 1 yalnız-arm) değerleri", sut, satirlar,
                 "D_4S_9x5x3/ozet.json › loglar[*].ucuslar[*]", "VIBE kapsam askı (askı yoksa motorlu), IMU0. Çift farkları toplam ölçek. MOT_THST_HOVER 0,506 = 3S+9x5x3 değeri (GEÇERSİZ)."),
                          lambda r: f"{r[0]} #{r[1]} ({r[2]})"))
    return out


# ----------------------------------------------------------------------------- XLSX yazımı
BASLIK_DOLGU = PatternFill("solid", fgColor="D9E1F2")
NOT_FONT = Font(italic=True, size=9, color="555555")


def sayfa_yaz(wb, tb, png_ad):
    ws = wb.create_sheet(tb["ad"])
    ws.append(tb["sutunlar"])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = BASLIK_DOLGU
        c.alignment = Alignment(wrap_text=True, vertical="top")
    genislik = [len(str(s)) for s in tb["sutunlar"]]
    for r in tb["satirlar"]:
        ws.append([("; ".join(yuvarla_metin(x) for x in v) if isinstance(v, (list, tuple)) else v) for v in r])
        rr = ws.max_row
        for j, v in enumerate(r, 1):
            c = ws.cell(row=rr, column=j)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                c.number_format = ondalik_bicim(v)
                c.alignment = Alignment(horizontal="right", vertical="top")
                uz = len(yuvarla_metin(v))
            else:
                s = "" if v is None else str(c.value)
                uz = min(max((len(p) for p in s.split("\n")), default=0), 70)
                c.alignment = Alignment(wrap_text=len(s) > 40, vertical="top")
            genislik[j - 1] = max(genislik[j - 1], uz)
    for j, w in enumerate(genislik, 1):
        ws.column_dimensions[get_column_letter(j)].width = min(max(w * 1.05 + 2, 6), 72)
    ws.freeze_panes = "A2"
    n = ws.max_row + 2
    kaynak = f"Kaynak: {tb['kaynak']} · sayılar kaynaktan kopyalandı, yeniden hesaplanmadı · üretim: TABLOLAR/tablolar_uret.py · PNG: png/{png_ad}"
    if tb.get("aciklama"):
        kaynak += " · " + tb["aciklama"]
    if tb.get("not_"):
        kaynak += " · Not: " + tb["not_"]
    c = ws.cell(row=n, column=1, value=kaynak)
    c.font = NOT_FONT
    c.alignment = Alignment(wrap_text=False)
    return ws


def indeks_yaz(wb, tablolar, png_adlari):
    ws = wb.active
    ws.title = "INDEKS"
    ws.append(["sayfa", "tablo", "kaynak dosya / bölüm", "satır", "sütun", "PNG", "açıklama"])
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = BASLIK_DOLGU
    for tb, png in zip(tablolar, png_adlari):
        ws.append([tb["ad"], tb["baslik"], tb["kaynak"], len(tb["satirlar"]), len(tb["sutunlar"]), "png/" + png, tb.get("aciklama", "")])
        c = ws.cell(row=ws.max_row, column=1)
        c.hyperlink = Hyperlink(ref=c.coordinate, location=f"'{tb['ad']}'!A1", display=tb["ad"])
        c.font = Font(color="0563C1", underline="single")
        for j in (2, 3, 7):
            ws.cell(row=ws.max_row, column=j).alignment = Alignment(wrap_text=True, vertical="top")
    for j, w in ((1, 30), (2, 70), (3, 60), (4, 7), (5, 7), (6, 34), (7, 60)):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "A2"
    n = ws.max_row + 2
    ws.cell(row=n, column=1, value="Kaynak: results/ucus_analiz_20260915/ (RAPOR.md, performans_zarfi/tablolar.json, E_1240_ivme/ozet.json, "
            "F_1311_aski_4S_13Ah/ozet.json, parametre_zaman_cizgisi.md/.json, tum_loglar.json, A/B/C/D/E ozet.json) · üretim: TABLOLAR/tablolar_uret.py · "
            "sayılar kopyalandı, yeniden hesaplanmadı (tek istisna: km/h = m/s × 3,6)").font = NOT_FONT


# ----------------------------------------------------------------------------- PNG çizimi
def png_ciz(tb, yol, dpi=170):
    sut = tb["sutunlar"]
    satirlar = tb["satirlar"]
    n_sut = len(sut)
    metin_sut = [any(isinstance(r[j], str) and len(r[j]) > 24 for r in satirlar) for j in range(n_sut)]
    if n_sut <= 4:
        fs, maksw = 9, 60
    elif n_sut <= 8:
        fs, maksw = 9, 42
    elif n_sut <= 14:
        fs, maksw = 8, 30
    else:
        fs, maksw = 7.5, 22
    if len(satirlar) > 60:
        fs = min(fs, 8)
    # hücre metinlerini sar
    hucreler, satir_satir = [], []
    for r in satirlar:
        h = []
        for v in r:
            s = yuvarla_metin(v)
            h.append(textwrap.fill(s, width=maksw, break_long_words=True) if len(s) > maksw else s)
        hucreler.append(h)
    basliklar = [textwrap.fill(str(s), width=min(maksw, 18)) for s in sut]
    tum = [basliklar] + hucreler
    kol_w = []
    for j in range(n_sut):
        w_b = max(len(p) for p in basliklar[j].split("\n")) * 1.45 + 1  # kalın başlık daha geniş
        w = max([w_b] + [max(len(p) for p in h[j].split("\n")) for h in hucreler])
        kol_w.append(max(w, 3) + 1)
    sat_h = [max(h[j].count("\n") + 1 for j in range(n_sut)) for h in tum]
    kar_w = fs * 0.70 / 72  # inç / karakter
    sat_in = fs * 1.55 / 72  # inç / satır
    genislik_in = sum(w * kar_w + 0.12 for w in kol_w) + 0.4
    yukseklik_in = sum(h * sat_in + 0.06 for h in sat_h) + 1.1
    genislik_in = max(6.5, min(genislik_in, 60))
    yukseklik_in = max(2.5, min(yukseklik_in, 200))
    fig = plt.figure(figsize=(genislik_in, yukseklik_in), dpi=dpi)
    ust = 0.55 / yukseklik_in
    alt = 0.45 / yukseklik_in
    ax = fig.add_axes([0.02, alt, 0.96, 1 - ust - alt])
    ax.axis("off")
    tablo = ax.table(cellText=hucreler, colLabels=basliklar, cellLoc="left", colLoc="left", loc="upper left", bbox=[0, 0, 1, 1])
    tablo.auto_set_font_size(False)
    tablo.set_fontsize(fs)
    top_w = sum(kol_w)
    top_h = sum(sat_h)
    for (i, j), hucre in tablo.get_celld().items():
        hucre.set_width(kol_w[j] / top_w)
        hucre.set_height(sat_h[i] / top_h)
        hucre.set_edgecolor("#bbbbbb")
        hucre.set_linewidth(0.5)
        hucre.PAD = 0.03
        if i == 0:
            hucre.set_facecolor("#d9e1f2")
            hucre.get_text().set_fontweight("bold")
        elif i % 2 == 0:
            hucre.set_facecolor("#f4f6fa")
        if i > 0 and isinstance(satirlar[i - 1][j], (int, float)) and not isinstance(satirlar[i - 1][j], bool):
            hucre._loc = "right"
    fig.text(0.02, 1 - 0.28 / yukseklik_in, tb["baslik"], fontsize=fs + 2.5, fontweight="bold", va="center", ha="left")
    kaynak = f"Kaynak: {tb['kaynak']} — sayılar kopyalandı, yeniden hesaplanmadı (tablolar_uret.py)"
    if tb.get("aciklama"):
        kaynak += ". " + tb["aciklama"]
    fig.text(0.02, 0.2 / yukseklik_in, textwrap.fill(kaynak, width=int(genislik_in * 72 / (fs * 0.62)) - 4)[:1200], fontsize=max(fs - 1.5, 6),
             va="center", ha="left", color="#444444")
    fig.savefig(yol, dpi=dpi)
    plt.close(fig)


# ----------------------------------------------------------------------------- ana akış
def kisa_ad(ad):
    return re.sub(r"[^A-Za-z0-9]+", "_", ad).strip("_")


def main():
    PNG_DIZIN.mkdir(parents=True, exist_ok=True)
    tablolar = []
    for uretici in (rapor_tablolari, zarf_tablolari, e_tablolari, f_tablolari, parametre_tablolari, log_tablolari, konfig_tablolari):
        tablolar += uretici()
    adlar = [t["ad"] for t in tablolar]
    assert len(adlar) == len(set(adlar)), "sayfa adı tekrarı"
    for t in tablolar:
        assert len(t["ad"]) <= 31
        for r in t["satirlar"]:
            assert len(r) == len(t["sutunlar"]), (t["ad"], len(r), len(t["sutunlar"]), r[:3])
    png_adlari = [f"{i + 1:02d}_{kisa_ad(t['ad'])}.png" for i, t in enumerate(tablolar)]
    wb = Workbook()
    indeks_yaz(wb, tablolar, png_adlari)
    for t, png in zip(tablolar, png_adlari):
        sayfa_yaz(wb, t, png)
    wb.save(XLSX)
    for t, png in zip(tablolar, png_adlari):
        png_ciz(t, PNG_DIZIN / png)
        print(f"PNG {png}: {len(t['satirlar'])}x{len(t['sutunlar'])}")
    print(f"XLSX: {XLSX} — {len(tablolar)} tablo + INDEKS; PNG: {len(png_adlari)}")
    return tablolar, png_adlari


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

"""NEDEN: T130 terfi kaydini artefakt dizgeleriyle mekanik olarak caprazlar.

Bu betik model dosyalarini acmaz ve SHA-256 hesaplamaz. Yalniz committed metin
ve JSON alanlarini karsilastirir; mimarin denetimi veya model onayi degildir.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


KOK = Path(__file__).resolve().parents[2]
VARSAYILAN_RAPOR = Path(__file__).with_name("t130_capraz_denetim.json")

BEKLENEN_MODEL_ID = "navitas-seg-v35-512"
BEKLENEN_PT = "navitas_seg_v35_best.pt"
BEKLENEN_V34_PT = "navitas_seg_v34_best.pt"
BEKLENEN_IMGSZ = 512
BEKLENEN_ASIL_SURUM = "v35"

MODEL_ID_DESENI = re.compile(r"^navitas-seg-v(?P<surum>[0-9]+)-(?P<imgsz>[0-9]+)$")
PT_ADI_DESENI = re.compile(r"^navitas_seg_v(?P<surum>[0-9]+)_best[.]pt$")
SHA256_DESENI = re.compile(r"^[0-9a-f]{64}$")
ASIL_MODEL_DESENI = re.compile(r"[*][*]ASIL MODEL:\s*(v[0-9]+)[*][*]")
V34_DOSYA_DESENI = re.compile(r"navitas_seg_v34[A-Za-z0-9_.-]*")
SEVIYE_IKI_BASLIK = re.compile(r"^## (?!#)(?P<baslik>.+)$")
D_BOLUMU_DESENI = re.compile(
    r"^### D-(?P<numara>[0-9]+)\b.*?(?=^### D-[0-9]+\b|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _basename(deger: object) -> str:
    return str(deger).replace("\\", "/").rsplit("/", 1)[-1]


def _satir_no(metin: str, aranan: str) -> int | None:
    for numara, satir in enumerate(metin.splitlines(), start=1):
        if aranan in satir:
            return numara
    return None


def _kanit(dosya: str, *, satir: int | None = None, alan: str = "", deger: Any = None) -> dict:
    kanit = {"dosya": dosya}
    if satir is not None:
        kanit["satir"] = satir
    if alan:
        kanit["alan"] = alan
    if deger is not None:
        kanit["deger"] = deger
    return kanit


def _durum(*, bulgular: Sequence[dict], olcum: Mapping[str, Any] | None = None) -> dict:
    return {
        "durum": "GECTI" if not bulgular else "DUSTU",
        "bulgular": list(bulgular),
        "olcum": dict(olcum or {}),
    }


def yaprak_farklari(sol: Any, sag: Any, yol: str = "") -> list[dict]:
    """Iki JSON degerini yaprak alanlarina kadar karsilastiran saf fonksiyon."""
    if isinstance(sol, Mapping) and isinstance(sag, Mapping):
        farklar: list[dict] = []
        for anahtar in sorted(set(sol) | set(sag), key=str):
            alt_yol = f"{yol}.{anahtar}" if yol else str(anahtar)
            if anahtar not in sol:
                farklar.append({"alan": alt_yol, "neden": "sol_eksik", "sag": sag[anahtar]})
            elif anahtar not in sag:
                farklar.append({"alan": alt_yol, "neden": "sag_eksik", "sol": sol[anahtar]})
            else:
                farklar.extend(yaprak_farklari(sol[anahtar], sag[anahtar], alt_yol))
        return farklar
    if isinstance(sol, list) and isinstance(sag, list):
        farklar = []
        if len(sol) != len(sag):
            farklar.append(
                {"alan": yol, "neden": "liste_uzunlugu", "sol": len(sol), "sag": len(sag)}
            )
        for indis, (sol_deger, sag_deger) in enumerate(zip(sol, sag)):
            farklar.extend(yaprak_farklari(sol_deger, sag_deger, f"{yol}[{indis}]"))
        return farklar
    if type(sol) is not type(sag):
        return [
            {
                "alan": yol,
                "neden": "tip_farki",
                "sol": {"tip": type(sol).__name__, "deger": sol},
                "sag": {"tip": type(sag).__name__, "deger": sag},
            }
        ]
    if sol != sag:
        return [{"alan": yol, "neden": "deger_farki", "sol": sol, "sag": sag}]
    return []


def kontrol_registry_ikizligi(sol_registry: Mapping[str, Any], sag_registry: Mapping[str, Any]) -> dict:
    """Kontrol 1: competition profillerini alan alan karsilastirir."""
    bulgular = []
    try:
        sol = sol_registry["profiles"]["competition"]
        sag = sag_registry["profiles"]["competition"]
    except (KeyError, TypeError) as exc:
        bulgular.append({"neden": "competition_profili_okunamadi", "hata": str(exc)})
        return _durum(bulgular=bulgular)
    farklar = yaprak_farklari(sol, sag, "profiles.competition")
    bulgular.extend(farklar)
    return _durum(bulgular=bulgular, olcum={"fark_sayisi": len(farklar)})


def kontrol_surum_adi(profil: Mapping[str, Any]) -> dict:
    """Kontrol 2: model kimligi, PT adi ve imgsz arasindaki surumu caprazlar."""
    bulgular = []
    model_id = profil.get("model_id")
    yol = profil.get("path")
    imgsz = profil.get("imgsz")
    pt_adi = _basename(yol)
    model_eslesmesi = MODEL_ID_DESENI.fullmatch(model_id) if isinstance(model_id, str) else None
    pt_eslesmesi = PT_ADI_DESENI.fullmatch(pt_adi)

    if model_id != BEKLENEN_MODEL_ID:
        bulgular.append(
            {"alan": "profiles.competition.model_id", "beklenen": BEKLENEN_MODEL_ID, "gercek": model_id}
        )
    if pt_adi != BEKLENEN_PT:
        bulgular.append(
            {"alan": "profiles.competition.path", "beklenen_basename": BEKLENEN_PT, "gercek": pt_adi}
        )
    if type(imgsz) is not int or imgsz != BEKLENEN_IMGSZ:
        bulgular.append(
            {"alan": "profiles.competition.imgsz", "beklenen": BEKLENEN_IMGSZ, "gercek": imgsz}
        )
    if model_eslesmesi is None:
        bulgular.append({"alan": "profiles.competition.model_id", "neden": "surum_deseni_gecersiz"})
    if pt_eslesmesi is None:
        bulgular.append({"alan": "profiles.competition.path", "neden": "pt_adi_deseni_gecersiz"})
    if model_eslesmesi is not None and pt_eslesmesi is not None:
        kimlik_surumu = int(model_eslesmesi.group("surum"))
        kimlik_boyutu = int(model_eslesmesi.group("imgsz"))
        pt_surumu = int(pt_eslesmesi.group("surum"))
        if kimlik_surumu != pt_surumu:
            bulgular.append(
                {"neden": "model_id_pt_surumu_farkli", "model_id": kimlik_surumu, "pt": pt_surumu}
            )
        if type(imgsz) is int and kimlik_boyutu != imgsz:
            bulgular.append(
                {"neden": "model_id_imgsz_farkli", "model_id": kimlik_boyutu, "imgsz": imgsz}
            )

    return _durum(
        bulgular=bulgular,
        olcum={"model_id": model_id, "path_basename": pt_adi, "imgsz": imgsz},
    )


def _paket_girdileri(manifest: Mapping[str, Any], dosya_adi: str) -> list[Mapping[str, Any]]:
    icerik = manifest.get("paket_icerigi", [])
    if not isinstance(icerik, list):
        return []
    return [girdi for girdi in icerik if isinstance(girdi, Mapping) and girdi.get("dosya") == dosya_adi]


def kontrol_sha_dizesi(profil: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict:
    """Kontrol 3: dosyaya dokunmadan registry ve paket SHA dizgelerini karsilastirir."""
    bulgular = []
    pt_adi = _basename(profil.get("path"))
    registry_sha = profil.get("sha256")
    girdiler = _paket_girdileri(manifest, pt_adi)
    if len(girdiler) != 1:
        bulgular.append(
            {"alan": "paket_icerigi", "neden": "pt_girdisi_tekil_degil", "dosya": pt_adi, "adet": len(girdiler)}
        )
        paket_sha = None
    else:
        paket_sha = girdiler[0].get("sha256")
    if not isinstance(registry_sha, str) or SHA256_DESENI.fullmatch(registry_sha) is None:
        bulgular.append({"alan": "profiles.competition.sha256", "neden": "sha256_dizgesi_gecersiz"})
    if not isinstance(paket_sha, str) or SHA256_DESENI.fullmatch(paket_sha) is None:
        bulgular.append({"alan": f"paket_icerigi[{pt_adi}].sha256", "neden": "sha256_dizgesi_gecersiz"})
    if registry_sha != paket_sha:
        bulgular.append(
            {"neden": "sha256_dizgeleri_farkli", "registry": registry_sha, "paket_manifest": paket_sha}
        )
    return _durum(
        bulgular=bulgular,
        olcum={"dosya": pt_adi, "registry_sha256": registry_sha, "paket_sha256": paket_sha},
    )


def _komut_modeli(komut: object) -> str | None:
    if not isinstance(komut, str):
        return None
    eslesme = re.search(r"(?:^|\s)model=(\S+)", komut)
    return _basename(eslesme.group(1)) if eslesme else None


def kontrol_kunye_registry(profil: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict:
    """Kontrol 4: PT/ONNX kimligini registry, kunye, liste ve komutta caprazlar."""
    bulgular = []
    pt_adi = _basename(profil.get("path"))
    asil_pt = manifest.get("asil_model_pt")
    asil_onnx = manifest.get("asil_model")
    imgsz = profil.get("imgsz")
    pt_eslesmesi = PT_ADI_DESENI.fullmatch(pt_adi)
    beklenen_onnx = None
    if pt_eslesmesi is not None and type(imgsz) is int:
        beklenen_onnx = f"navitas_seg_v{pt_eslesmesi.group('surum')}_best_{imgsz}_fp16.onnx"

    if asil_pt != pt_adi:
        bulgular.append({"neden": "asil_model_pt_registryden_farkli", "registry": pt_adi, "manifest": asil_pt})
    if asil_onnx != beklenen_onnx:
        bulgular.append(
            {"neden": "asil_model_uretilen_onnx_adindan_farkli", "beklenen": beklenen_onnx, "manifest": asil_onnx}
        )

    onnxler = manifest.get("onnxler")
    if not isinstance(onnxler, list) or len(onnxler) != 1:
        bulgular.append({"alan": "onnxler", "neden": "tek_onnx_bekleniyor", "gercek": onnxler})
        onnx_adlari = []
    else:
        onnx_adlari = [_basename(onnxler[0])]
        if onnx_adlari[0] != asil_onnx:
            bulgular.append(
                {"neden": "onnxler_asil_modelden_farkli", "onnxler_0": onnx_adlari[0], "asil_model": asil_onnx}
            )

    komutlar = manifest.get("jetson_komutlari")
    if not isinstance(komutlar, list) or not komutlar:
        bulgular.append({"alan": "jetson_komutlari", "neden": "komut_yok"})
        komut_modelleri = []
    else:
        komut_modelleri = [_komut_modeli(komut) for komut in komutlar]
        for indis, model in enumerate(komut_modelleri):
            if model != asil_onnx:
                bulgular.append(
                    {
                        "alan": f"jetson_komutlari[{indis}]",
                        "neden": "komut_asil_modeli_kullanmiyor",
                        "beklenen": asil_onnx,
                        "gercek": model,
                    }
                )

    return _durum(
        bulgular=bulgular,
        olcum={
            "registry_pt": pt_adi,
            "manifest_asil_model_pt": asil_pt,
            "manifest_asil_model": asil_onnx,
            "onnx_basename": onnx_adlari,
            "jetson_komut_modeli": komut_modelleri,
        },
    )


def _v34_sinifi(seviye_iki_baslik: str | None) -> str:
    if seviye_iki_baslik is None:
        return "KAPSAM_DISI"
    if re.match(r"^6C[.]\s+BİRİNCİL→YEDEK MODEL GEÇİŞ YORDAMI\b", seviye_iki_baslik):
        return "SS6C_YEDEK"
    if re.match(r"^0-T[0-9]+[.]\s+GÜNCELLEME\b", seviye_iki_baslik):
        return "SS0_TARIHSEL"
    return "KAPSAM_DISI"


def kilavuz_durumu(metin: str) -> dict:
    """Tek kilavuzdaki ASIL MODEL ve v34 gecislerinin saf durumunu olcer."""
    bulgular = []
    asil_surumluler = []
    v34_gecisleri = []
    guncel_bolum = None
    for satir_no, satir in enumerate(metin.splitlines(), start=1):
        baslik = SEVIYE_IKI_BASLIK.match(satir)
        if baslik:
            guncel_bolum = baslik.group("baslik")
        for eslesme in ASIL_MODEL_DESENI.finditer(satir):
            asil_surumluler.append({"satir": satir_no, "surum": eslesme.group(1), "metin": satir})
        for eslesme in V34_DOSYA_DESENI.finditer(satir):
            sinif = _v34_sinifi(guncel_bolum)
            kayit = {
                "satir": satir_no,
                "dize": eslesme.group(0),
                "bolum": guncel_bolum,
                "sinif": sinif,
            }
            v34_gecisleri.append(kayit)
            if sinif == "KAPSAM_DISI":
                bulgular.append({"neden": "v34_mesru_bolum_disinda", **kayit})
    if len(asil_surumluler) != 1:
        bulgular.append({"neden": "ASIL_MODEL_satiri_tekil_degil", "adet": len(asil_surumluler)})
    elif asil_surumluler[0]["surum"] != BEKLENEN_ASIL_SURUM:
        bulgular.append(
            {
                "neden": "ASIL_MODEL_v35_degil",
                "beklenen": BEKLENEN_ASIL_SURUM,
                "gercek": asil_surumluler[0]["surum"],
                "satir": asil_surumluler[0]["satir"],
            }
        )
    return _durum(
        bulgular=bulgular,
        olcum={"asil_model_satirlari": asil_surumluler, "v34_gecisleri": v34_gecisleri},
    )


def kontrol_kilavuzlar(kilavuzlar: Mapping[str, str]) -> dict:
    """Kontrol 5: iki kilavuzu ayni saf kuralla tarar."""
    bulgular = []
    dosya_olcumleri = {}
    if len(kilavuzlar) != 2:
        bulgular.append({"neden": "iki_kilavuz_bekleniyor", "adet": len(kilavuzlar)})
    for dosya, metin in kilavuzlar.items():
        durum = kilavuz_durumu(metin)
        dosya_olcumleri[dosya] = durum["olcum"]
        bulgular.extend({"dosya": dosya, **bulgu} for bulgu in durum["bulgular"])
    return _durum(bulgular=bulgular, olcum={"kilavuzlar": dosya_olcumleri})


def _iddia_hedefi(dugum: ast.AST) -> str | None:
    if (
        isinstance(dugum, ast.Attribute)
        and isinstance(dugum.value, ast.Name)
        and dugum.value.id == "path"
        and dugum.attr == "name"
    ):
        return "path.name"
    if isinstance(dugum, ast.Subscript) and isinstance(dugum.value, ast.Name) and dugum.value.id == "spec":
        dilim = dugum.slice
        if isinstance(dilim, ast.Constant) and isinstance(dilim.value, str):
            return f"spec[{dilim.value!r}]"
    return None


def ast_model_iddialari(kod: str) -> list[dict]:
    """Yorum/docstring yerine gercek assertEqual cagrilarini cikarir."""
    agac = ast.parse(kod)
    hedefler = [
        dugum
        for dugum in ast.walk(agac)
        if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef))
        and dugum.name == "test_default_is_verified_v35_competition_model"
    ]
    if len(hedefler) != 1:
        raise ValueError(
            "test_default_is_verified_v35_competition_model tekil degil: "
            f"{len(hedefler)}"
        )
    iddialar = []
    for dugum in ast.walk(hedefler[0]):
        if not isinstance(dugum, ast.Call) or len(dugum.args) < 2:
            continue
        if not isinstance(dugum.func, ast.Attribute) or dugum.func.attr != "assertEqual":
            continue
        sol_hedef = _iddia_hedefi(dugum.args[0])
        sag_hedef = _iddia_hedefi(dugum.args[1])
        if sol_hedef and isinstance(dugum.args[1], ast.Constant):
            iddialar.append({"hedef": sol_hedef, "deger": dugum.args[1].value, "satir": dugum.lineno})
        elif sag_hedef and isinstance(dugum.args[0], ast.Constant):
            iddialar.append({"hedef": sag_hedef, "deger": dugum.args[0].value, "satir": dugum.lineno})
    return iddialar


def kontrol_test_iddiasi(kod: str) -> dict:
    """Kontrol 6: testin v35 iddialarini AST uzerinden dogrular."""
    beklenen = {
        "path.name": BEKLENEN_PT,
        "spec['imgsz']": BEKLENEN_IMGSZ,
        "spec['status']": "competition",
        "spec['model_id']": BEKLENEN_MODEL_ID,
    }
    try:
        iddialar = ast_model_iddialari(kod)
    except (SyntaxError, ValueError) as exc:
        return _durum(bulgular=[{"neden": "AST_ayristirma_hatasi", "hata": str(exc)}])
    bulunan = {iddia["hedef"]: iddia for iddia in iddialar}
    bulgular = []
    for hedef, deger in beklenen.items():
        kayit = bulunan.get(hedef)
        if kayit is None:
            bulgular.append({"neden": "AST_iddiasi_eksik", "hedef": hedef, "beklenen": deger})
        elif kayit["deger"] != deger:
            bulgular.append(
                {"neden": "AST_iddiasi_farkli", "hedef": hedef, "beklenen": deger, "gercek": kayit["deger"]}
            )
    return _durum(bulgular=bulgular, olcum={"iddialar": iddialar})


def d_bolumu(defter: str, numara: int) -> tuple[str | None, int | None]:
    """Tam level-3 D kaydini saf olarak ayirir; ayni numara tekil olmalidir."""
    eslesmeler = [e for e in D_BOLUMU_DESENI.finditer(defter) if int(e.group("numara")) == numara]
    if len(eslesmeler) != 1:
        return None, None
    eslesme = eslesmeler[0]
    satir = defter.count("\n", 0, eslesme.start()) + 1
    return eslesme.group(0), satir


def _tr_sayi(deger: str) -> float:
    return float(deger.replace(",", "."))


def _kesir_yuzde(kesir: str) -> float:
    pay, payda = (int(parca) for parca in kesir.split("/", 1))
    if payda <= 0:
        raise ValueError(f"gecersiz kesir paydasi: {kesir}")
    return round(100.0 * pay / payda, 2)


def d256_sayilari(bolum: str) -> tuple[dict, list[dict]]:
    """D-256 metnindeki gorevce istenen sayilari ayiklar."""
    hatalar = []
    sayilar: dict[str, Any] = {}

    k0 = re.search(
        r"K0\s+GECTI\s+%([0-9]+,[0-9]+)\s+\(taban\s+%([0-9]+,[0-9]+)\s+·\s+oran\s+([0-9]+,[0-9]+)\)",
        bolum,
    )
    if k0:
        sayilar.update(
            {
                "K0_figur_yuzde": _tr_sayi(k0.group(1)),
                "K0_taban_yuzde": _tr_sayi(k0.group(2)),
                "K0_figur_orani": _tr_sayi(k0.group(3)),
            }
        )
    else:
        hatalar.append({"neden": "D256_K0_sayilari_ayristirilamadi"})

    k14 = re.search(
        r"K1\s+([0-9]+/[0-9]+)\s+·\s+K2\s+([0-9]+/[0-9]+)\s+·\s*"
        r"K3\s+([0-9]+/[0-9]+)\s+·\s+K4\s+([0-9]+/[0-9]+)",
        bolum,
    )
    if k14:
        for indis, ad in enumerate(("K1", "K2", "K3", "K4"), start=1):
            sayilar[ad] = k14.group(indis)
    else:
        hatalar.append({"neden": "D256_K1_K4_sayilari_ayristirilamadi"})

    k5 = re.search(r"K5\s+GECTI\s+([0-9]+)/([0-9]+)", bolum)
    if k5:
        sayilar["K5_kesen"] = int(k5.group(1))
        sayilar["K5_olculebilir"] = int(k5.group(2))
    else:
        hatalar.append({"neden": "D256_K5_sayilari_ayristirilamadi"})

    k2_maliyet = re.search(
        r"K2\s+moloza\s+basma:\s*%([0-9]+,[0-9]+)\s*→\s*%([0-9]+,[0-9]+)[*]{0,2}\s*"
        r"\(v34\s+([0-9]+/[0-9]+)\s*→\s*v35\s+([0-9]+/[0-9]+)\)",
        bolum,
    )
    if k2_maliyet:
        sayilar.update(
            {
                "K2_v34_yuzde": _tr_sayi(k2_maliyet.group(1)),
                "K2_v35_yuzde": _tr_sayi(k2_maliyet.group(2)),
                "K2_v34_kesir": k2_maliyet.group(3),
                "K2_v35_kesir": k2_maliyet.group(4),
            }
        )
    else:
        hatalar.append({"neden": "D256_K2_maliyet_sayilari_ayristirilamadi"})

    karar = re.search(r"KARAR KARARLILIĞI:\s*([0-9]+)/([0-9]+)\s*→\s*([0-9]+)/([0-9]+)", bolum)
    if karar:
        sayilar.update(
            {
                "v34_kararsiz": int(karar.group(1)),
                "v34_n": int(karar.group(2)),
                "v35_kararsiz": int(karar.group(3)),
                "v35_n": int(karar.group(4)),
            }
        )
    else:
        hatalar.append({"neden": "D256_kararlilik_sayilari_ayristirilamadi"})

    sigma = re.search(r"sigma\s+([0-9]+(?:,[0-9]+)?)/255,\s*tekrar\s+([0-9]+),\s*tohum\s+([0-9]+)", bolum)
    if sigma:
        sayilar["sigma_255"] = _tr_sayi(sigma.group(1))
        sayilar["tekrar"] = int(sigma.group(2))
        sayilar["tohum"] = int(sigma.group(3))
    else:
        hatalar.append({"neden": "D256_sigma_tekrar_ayristirilamadi"})

    sha = re.search(
        r"sha256\s+\([^\n]*\):[*]{0,2}\s*`([0-9a-f]{64})`",
        bolum,
        re.IGNORECASE,
    )
    onnx_sha = re.search(r"ONNX:\s*`([0-9a-f]{64})`", bolum)
    if sha:
        sayilar["pt_sha256"] = sha.group(1).lower()
    else:
        hatalar.append({"neden": "D256_PT_SHA_ayristirilamadi"})
    if onnx_sha:
        sayilar["onnx_sha256"] = onnx_sha.group(1).lower()
    else:
        hatalar.append({"neden": "D256_ONNX_SHA_ayristirilamadi"})
    return sayilar, hatalar


def _esit_ekle(bulgular: list[dict], alan: str, kayit: Any, artefakt: Any) -> None:
    if kayit != artefakt:
        bulgular.append({"alan": alan, "neden": "D256_artefakt_uyusmazligi", "D256": kayit, "artefakt": artefakt})


def kontrol_d256_sayilari(
    defter: str,
    verdikt: Mapping[str, Any],
    v35_kararlilik: Mapping[str, Any],
    v34_kararlilik: Mapping[str, Any],
    registry: Mapping[str, Any],
    paket_manifest: Mapping[str, Any],
    export_manifest: Mapping[str, Any],
) -> dict:
    """Kontrol 7: D-256 sayilarini committed JSON alanlariyla caprazlar."""
    bulgular = []
    notlar = []
    bolum, bolum_satiri = d_bolumu(defter, 256)
    if bolum is None:
        return _durum(bulgular=[{"neden": "D256_bolumu_tekil_degil_veya_yok"}])
    kayit, ayiklama_hatalari = d256_sayilari(bolum)
    bulgular.extend(ayiklama_hatalari)

    try:
        olcum = verdikt["olcum"]
        k0 = olcum["K0"]
        profil = registry["profiles"]["competition"]
        registry_k2 = profil["metrics"]["k2_moloza_basma_yuzde"]
    except (KeyError, TypeError) as exc:
        bulgular.append({"neden": "artefakt_semasi_okunamadi", "hata": str(exc)})
        return _durum(bulgular=bulgular, olcum={"D256": kayit})

    artefakt_modelleri = {
        "verdikt.model": _basename(verdikt.get("model")),
        "kararlilik_v35.model": _basename(v35_kararlilik.get("model")),
        "kararlilik_v34.model": _basename(v34_kararlilik.get("model")),
    }
    for alan, beklenen in (
        ("verdikt.model", BEKLENEN_PT),
        ("kararlilik_v35.model", BEKLENEN_PT),
        ("kararlilik_v34.model", BEKLENEN_V34_PT),
    ):
        if artefakt_modelleri[alan] != beklenen:
            bulgular.append(
                {
                    "alan": alan,
                    "neden": "artefakt_model_kimligi_farkli",
                    "beklenen": beklenen,
                    "gercek": artefakt_modelleri[alan],
                }
            )

    if "K0_figur_yuzde" in kayit:
        _esit_ekle(bulgular, "K0.figur_yuzde", kayit["K0_figur_yuzde"], round(float(k0["figur"]) * 100, 2))
        _esit_ekle(bulgular, "K0.taban_yuzde", kayit["K0_taban_yuzde"], round(float(k0["figur_tabani"]) * 100, 2))
        _esit_ekle(bulgular, "K0.figur_orani", kayit["K0_figur_orani"], round(float(k0["figur_orani"]), 2))
    for kayit_adi, artefakt_adi in (
        ("K1", "K1_rota"),
        ("K2", "K2_basma"),
        ("K3", "K3_agir"),
        ("K4", "K4_arena_disi"),
    ):
        if kayit_adi in kayit:
            _esit_ekle(bulgular, f"olcum.{artefakt_adi}", kayit[kayit_adi], olcum.get(artefakt_adi))

    if "K2_v35_yuzde" in kayit:
        _esit_ekle(bulgular, "D256.K2_v35_kesir", kayit["K2_v35_kesir"], olcum.get("K2_basma"))
        _esit_ekle(
            bulgular,
            "D256.K2_v35_yuzde_kesirden",
            kayit["K2_v35_yuzde"],
            _kesir_yuzde(kayit["K2_v35_kesir"]),
        )
        _esit_ekle(
            bulgular,
            "D256.K2_v35_yuzde_registry",
            kayit["K2_v35_yuzde"],
            float(registry_k2.get("olculen")),
        )
        _esit_ekle(
            bulgular,
            "D256.K2_v34_yuzde_kesirden",
            kayit["K2_v34_yuzde"],
            _kesir_yuzde(kayit["K2_v34_kesir"]),
        )
        registry_k2_notu = registry_k2.get("not", "")
        registry_k2_eslesmesi = re.search(
            r"v34\s+%([0-9]+,[0-9]+)\s+\(([0-9]+/[0-9]+)\)\s*->\s*"
            r"v35\s+%([0-9]+,[0-9]+)\s+\(([0-9]+/[0-9]+)\)",
            registry_k2_notu,
        )
        if registry_k2_eslesmesi is None:
            bulgular.append({"alan": "profiles.competition.metrics.k2.not", "neden": "K2_maliyet_notu_ayristirilamadi"})
        else:
            registry_k2_kaydi = {
                "K2_v34_yuzde": _tr_sayi(registry_k2_eslesmesi.group(1)),
                "K2_v34_kesir": registry_k2_eslesmesi.group(2),
                "K2_v35_yuzde": _tr_sayi(registry_k2_eslesmesi.group(3)),
                "K2_v35_kesir": registry_k2_eslesmesi.group(4),
            }
            for alan, deger in registry_k2_kaydi.items():
                _esit_ekle(bulgular, f"D256.registry_K2_notu.{alan}", kayit[alan], deger)
    if "K5_kesen" in kayit:
        _esit_ekle(bulgular, "olcum.K5_kesen_kare", kayit["K5_kesen"], olcum.get("K5_kesen_kare"))
        _esit_ekle(
            bulgular,
            "olcum.K5_olculebilir_kare",
            kayit["K5_olculebilir"],
            olcum.get("K5_olculebilir_kare"),
        )

    for surum, artefakt in (("v35", v35_kararlilik), ("v34", v34_kararlilik)):
        for alan in ("kararsiz", "n"):
            kayit_anahtari = f"{surum}_{alan}"
            if kayit_anahtari in kayit:
                _esit_ekle(bulgular, f"{surum}.{alan}", kayit[kayit_anahtari], artefakt.get(alan))
        cevrilenler = artefakt.get("cevrilenler")
        if not isinstance(cevrilenler, list) or len(cevrilenler) != artefakt.get("kararsiz"):
            bulgular.append(
                {
                    "alan": f"{surum}.cevrilenler",
                    "neden": "liste_kararsiz_sayisiyla_uyusmuyor",
                    "liste": len(cevrilenler) if isinstance(cevrilenler, list) else None,
                    "kararsiz": artefakt.get("kararsiz"),
                }
            )

    _esit_ekle(bulgular, "kararlilik.sigma_v35_v34", v35_kararlilik.get("sigma"), v34_kararlilik.get("sigma"))
    _esit_ekle(bulgular, "kararlilik.tekrar_v35_v34", v35_kararlilik.get("tekrar"), v34_kararlilik.get("tekrar"))
    if "sigma_255" in kayit:
        _esit_ekle(bulgular, "D256.sigma_255", kayit["sigma_255"], v35_kararlilik.get("sigma"))
        _esit_ekle(bulgular, "D256.tekrar", kayit["tekrar"], v35_kararlilik.get("tekrar"))
    if "tohum" not in v35_kararlilik or "tohum" not in v34_kararlilik:
        notlar.append(
            "Kararlilik JSON payloadlarinda `tohum` alani yok; tohum 7 yalniz dosya adlarinda kayitli."
        )

    pt_adi = _basename(profil.get("path"))
    pt_girdileri = _paket_girdileri(paket_manifest, pt_adi)
    asil_onnx = paket_manifest.get("asil_model")
    onnx_girdileri = _paket_girdileri(paket_manifest, str(asil_onnx))
    pt_paket_sha = pt_girdileri[0].get("sha256") if len(pt_girdileri) == 1 else None
    onnx_paket_sha = onnx_girdileri[0].get("sha256") if len(onnx_girdileri) == 1 else None
    if "pt_sha256" in kayit:
        _esit_ekle(bulgular, "D256.pt_sha_registry", kayit["pt_sha256"], profil.get("sha256"))
        _esit_ekle(bulgular, "D256.pt_sha_paket", kayit["pt_sha256"], pt_paket_sha)
    if "onnx_sha256" in kayit:
        _esit_ekle(bulgular, "D256.onnx_sha_paket", kayit["onnx_sha256"], onnx_paket_sha)

    export_onnxler = export_manifest.get("onnxler")
    export_onnx = _basename(export_onnxler[0]) if isinstance(export_onnxler, list) and len(export_onnxler) == 1 else None
    _esit_ekle(bulgular, "export_manifest.onnxler[0]", asil_onnx, export_onnx)
    if "sha256" not in export_manifest:
        notlar.append(
            "ONNX export manifesti SHA alani tasimiyor; ONNX SHA yalniz paket manifesti dizgesinden caprazlandi."
        )

    return _durum(
        bulgular=bulgular,
        olcum={
            "D256_baslangic_satiri": bolum_satiri,
            "D256": kayit,
            "artefakt_modelleri": artefakt_modelleri,
            "verdikt": {
                "K0_figur": k0.get("figur"),
                "K0_figur_tabani": k0.get("figur_tabani"),
                "K0_figur_orani": k0.get("figur_orani"),
                "K1": olcum.get("K1_rota"),
                "K2": olcum.get("K2_basma"),
                "K3": olcum.get("K3_agir"),
                "K4": olcum.get("K4_arena_disi"),
                "K5_kesen": olcum.get("K5_kesen_kare"),
                "K5_olculebilir": olcum.get("K5_olculebilir_kare"),
            },
            "kararlilik_v35": {
                "kararsiz": v35_kararlilik.get("kararsiz"),
                "n": v35_kararlilik.get("n"),
                "sigma": v35_kararlilik.get("sigma"),
                "tekrar": v35_kararlilik.get("tekrar"),
            },
            "kararlilik_v34": {
                "kararsiz": v34_kararlilik.get("kararsiz"),
                "n": v34_kararlilik.get("n"),
                "sigma": v34_kararlilik.get("sigma"),
                "tekrar": v34_kararlilik.get("tekrar"),
            },
            "pt_sha256_registry": profil.get("sha256"),
            "pt_sha256_paket": pt_paket_sha,
            "onnx_sha256_paket": onnx_paket_sha,
            "export_onnx_basename": export_onnx,
            "notlar": notlar,
        },
    )


def sentetik_mutasyon_sinamalari() -> list[dict]:
    """T120 dersi: uc mutasyonun gercek kontrolu DUSURDUGUNU olcer."""
    sonuclar = []

    registry = {"profiles": {"competition": {"model_id": BEKLENEN_MODEL_ID, "imgsz": 512}}}
    bozuk_registry = copy.deepcopy(registry)
    bozuk_registry["profiles"]["competition"]["imgsz"] = 640
    pozitif = kontrol_registry_ikizligi(registry, copy.deepcopy(registry))
    sonuc = kontrol_registry_ikizligi(registry, bozuk_registry)
    sonuclar.append(
        {
            "mutasyon": "registry_ikizligini_boz",
            "hedef_kontrol": 1,
            "beklenen": "DUSTU",
            "gercek": sonuc["durum"],
            "pozitif_kontrol": pozitif["durum"],
            "durum": "GECTI" if pozitif["durum"] == "GECTI" and sonuc["durum"] == "DUSTU" else "DUSTU",
            "kanit": sonuc["bulgular"],
        }
    )

    sha = "a" * 64
    profil = {"path": f"models/{BEKLENEN_PT}", "sha256": sha}
    manifest = {"paket_icerigi": [{"dosya": BEKLENEN_PT, "sha256": sha}]}
    bozuk_manifest = copy.deepcopy(manifest)
    bozuk_manifest["paket_icerigi"][0]["sha256"] = "b" + sha[1:]
    pozitif = kontrol_sha_dizesi(profil, manifest)
    sonuc = kontrol_sha_dizesi(profil, bozuk_manifest)
    sonuclar.append(
        {
            "mutasyon": "manifest_sha_tek_karakter_degistir",
            "hedef_kontrol": 3,
            "beklenen": "DUSTU",
            "gercek": sonuc["durum"],
            "pozitif_kontrol": pozitif["durum"],
            "durum": "GECTI" if pozitif["durum"] == "GECTI" and sonuc["durum"] == "DUSTU" else "DUSTU",
            "kanit": sonuc["bulgular"],
        }
    )

    temiz = (
        "> **ASIL MODEL: v35**\n\n"
        "## 6C. BİRİNCİL→YEDEK MODEL GEÇİŞ YORDAMI (T123)\n"
        "navitas_seg_v34_best.pt\n"
    )
    bozuk = temiz + "\n## 5. NORMAL BOLUM\nnavitas_seg_v34_best.pt\n"
    pozitif = kontrol_kilavuzlar({"bir.md": temiz, "iki.md": temiz})
    sonuc = kontrol_kilavuzlar({"bir.md": bozuk, "iki.md": temiz})
    sonuclar.append(
        {
            "mutasyon": "SS6C_disina_v34_satiri_ekle",
            "hedef_kontrol": 5,
            "beklenen": "DUSTU",
            "gercek": sonuc["durum"],
            "pozitif_kontrol": pozitif["durum"],
            "durum": "GECTI" if pozitif["durum"] == "GECTI" and sonuc["durum"] == "DUSTU" else "DUSTU",
            "kanit": sonuc["bulgular"],
        }
    )
    return sonuclar


def _json_oku(yol: Path) -> Any:
    return json.loads(yol.read_text(encoding="utf-8"))


def _metin_oku(yol: Path) -> str:
    return yol.read_text(encoding="utf-8")


def _kontrol_calistir(no: int, ad: str, islem: Callable[[], tuple[dict, list[dict]] | dict]) -> dict:
    """Bir kontrol hata verse de yedi sonucun tamamini raporda tutar."""
    try:
        ham = islem()
        if isinstance(ham, tuple):
            durum, kanit = ham
        else:
            durum, kanit = ham, []
    except Exception as exc:  # Rapor tamamlanmali; hata basari sayilmaz.
        durum = _durum(
            bulgular=[{"neden": "kontrol_calisma_hatasi", "tip": type(exc).__name__, "hata": str(exc)}]
        )
        kanit = []
    return {
        "no": no,
        "ad": ad,
        "durum": durum["durum"],
        "bulgu_sayisi": len(durum["bulgular"]),
        "bulgular": durum["bulgular"],
        "kanit": kanit,
        "olcum": durum["olcum"],
    }


def rapor_uret(kok: Path) -> dict:
    """Gercek dosyalari okur; kaynaklar uzerinde hicbir mutasyon yapmaz."""
    yollar = {
        "registry": kok / "config/model_registry.json",
        "paket_registry": kok / "jetson_paket/config/model_registry.json",
        "paket_manifest": kok / "jetson_paket/models/jetson_derleme_manifest.json",
        "kok_kilavuz": kok / "JETSON_KILAVUZ.md",
        "paket_kilavuz": kok / "jetson_paket/JETSON_KILAVUZ.md",
        "registry_test": kok / "tests/test_model_registry.py",
        "defter": kok / "REVIEW_LOG.md",
        "verdikt": kok / "scripts/olcum/results/t63/t130_v35_dogrulama_kabul_verdikt.json",
        "kararlilik_v35": kok / "results/t130_kararlilik_tohum7.json",
        "kararlilik_v34": kok / "results/t130_kararlilik_v34_tohum7.json",
        "export_manifest": kok / "results/onnx_export_v35_20260821/jetson_derleme_manifest.json",
    }

    registry = _json_oku(yollar["registry"])
    paket_registry = _json_oku(yollar["paket_registry"])
    paket_manifest = _json_oku(yollar["paket_manifest"])
    profil = registry["profiles"]["competition"]
    registry_metni = _metin_oku(yollar["registry"])
    paket_manifest_metni = _metin_oku(yollar["paket_manifest"])

    kontroller = []
    kontroller.append(
        _kontrol_calistir(
            1,
            "REGISTRY IKIZLIGI",
            lambda: (
                kontrol_registry_ikizligi(registry, paket_registry),
                [
                    _kanit("config/model_registry.json", satir=_satir_no(registry_metni, '"competition": {'), alan="profiles.competition"),
                    _kanit("jetson_paket/config/model_registry.json", satir=_satir_no(_metin_oku(yollar["paket_registry"]), '"competition": {'), alan="profiles.competition"),
                ],
            ),
        )
    )
    kontroller.append(
        _kontrol_calistir(
            2,
            "SURUM ADI TUTARLILIGI",
            lambda: (
                kontrol_surum_adi(profil),
                [
                    _kanit("config/model_registry.json", satir=_satir_no(registry_metni, '"model_id"'), alan="profiles.competition.model_id", deger=profil.get("model_id")),
                    _kanit("config/model_registry.json", satir=_satir_no(registry_metni, '"path"'), alan="profiles.competition.path", deger=profil.get("path")),
                    _kanit("config/model_registry.json", satir=_satir_no(registry_metni, '"imgsz"'), alan="profiles.competition.imgsz", deger=profil.get("imgsz")),
                ],
            ),
        )
    )
    kontroller.append(
        _kontrol_calistir(
            3,
            "SHA DIZE TUTARLILIGI",
            lambda: (
                kontrol_sha_dizesi(profil, paket_manifest),
                [
                    _kanit("config/model_registry.json", satir=_satir_no(registry_metni, '"sha256"'), alan="profiles.competition.sha256", deger=profil.get("sha256")),
                    _kanit("jetson_paket/models/jetson_derleme_manifest.json", satir=_satir_no(paket_manifest_metni, f'"dosya": "{_basename(profil.get("path"))}"'), alan=f"paket_icerigi[{_basename(profil.get('path'))}].sha256"),
                ],
            ),
        )
    )
    kontroller.append(
        _kontrol_calistir(
            4,
            "KUNYE REGISTRY",
            lambda: (
                kontrol_kunye_registry(profil, paket_manifest),
                [
                    _kanit("config/model_registry.json", satir=_satir_no(registry_metni, '"path"'), alan="profiles.competition.path"),
                    _kanit("jetson_paket/models/jetson_derleme_manifest.json", satir=_satir_no(paket_manifest_metni, '"onnxler"'), alan="onnxler[0]"),
                    _kanit("jetson_paket/models/jetson_derleme_manifest.json", satir=_satir_no(paket_manifest_metni, '"asil_model"'), alan="asil_model"),
                    _kanit("jetson_paket/models/jetson_derleme_manifest.json", satir=_satir_no(paket_manifest_metni, '"asil_model_pt"'), alan="asil_model_pt"),
                    _kanit("jetson_paket/models/jetson_derleme_manifest.json", satir=_satir_no(paket_manifest_metni, '"jetson_komutlari"'), alan="jetson_komutlari"),
                ],
            ),
        )
    )

    kok_kilavuz = _metin_oku(yollar["kok_kilavuz"])
    paket_kilavuz = _metin_oku(yollar["paket_kilavuz"])
    kontroller.append(
        _kontrol_calistir(
            5,
            "KILAVUZ x2",
            lambda: (
                kontrol_kilavuzlar(
                    {"JETSON_KILAVUZ.md": kok_kilavuz, "jetson_paket/JETSON_KILAVUZ.md": paket_kilavuz}
                ),
                [
                    _kanit("JETSON_KILAVUZ.md", satir=_satir_no(kok_kilavuz, "ASIL MODEL:"), alan="ASIL MODEL"),
                    _kanit("jetson_paket/JETSON_KILAVUZ.md", satir=_satir_no(paket_kilavuz, "ASIL MODEL:"), alan="ASIL MODEL"),
                    *[
                        _kanit(dosya, satir=kayit["satir"], alan="navitas_seg_v34", deger={"dize": kayit["dize"], "sinif": kayit["sinif"], "bolum": kayit["bolum"]})
                        for dosya, metin in (("JETSON_KILAVUZ.md", kok_kilavuz), ("jetson_paket/JETSON_KILAVUZ.md", paket_kilavuz))
                        for kayit in kilavuz_durumu(metin)["olcum"]["v34_gecisleri"]
                    ],
                ],
            ),
        )
    )

    test_kodu = _metin_oku(yollar["registry_test"])
    kontroller.append(
        _kontrol_calistir(
            6,
            "TEST IDDIASI AST",
            lambda: (
                kontrol_test_iddiasi(test_kodu),
                [
                    _kanit("tests/test_model_registry.py", satir=iddia["satir"], alan=iddia["hedef"], deger=iddia["deger"])
                    for iddia in ast_model_iddialari(test_kodu)
                ],
            ),
        )
    )

    defter = _metin_oku(yollar["defter"])
    verdikt = _json_oku(yollar["verdikt"])
    v35_kararlilik = _json_oku(yollar["kararlilik_v35"])
    v34_kararlilik = _json_oku(yollar["kararlilik_v34"])
    export_manifest = _json_oku(yollar["export_manifest"])
    d256_bolum, d256_satir = d_bolumu(defter, 256)
    kontroller.append(
        _kontrol_calistir(
            7,
            "D256 SAYILARI ARTEFAKTLARLA TUTARLI MI",
            lambda: (
                kontrol_d256_sayilari(
                    defter,
                    verdikt,
                    v35_kararlilik,
                    v34_kararlilik,
                    registry,
                    paket_manifest,
                    export_manifest,
                ),
                [
                    _kanit("REVIEW_LOG.md", satir=d256_satir, alan="D-256"),
                    _kanit("scripts/olcum/results/t63/t130_v35_dogrulama_kabul_verdikt.json", alan="olcum.K0/K1_rota/K2_basma/K3_agir/K4_arena_disi/K5_*"),
                    _kanit("results/t130_kararlilik_tohum7.json", alan="kararsiz/n/sigma/tekrar"),
                    _kanit("results/t130_kararlilik_v34_tohum7.json", alan="kararsiz/n/sigma/tekrar"),
                    _kanit("config/model_registry.json", alan="profiles.competition.sha256"),
                    _kanit("jetson_paket/models/jetson_derleme_manifest.json", alan="paket_icerigi[v35 PT/ONNX].sha256"),
                    _kanit("results/onnx_export_v35_20260821/jetson_derleme_manifest.json", alan="onnxler[0] (SHA alani yok)"),
                ],
            ),
        )
    )

    mutasyonlar = sentetik_mutasyon_sinamalari()
    gecti = sum(kontrol["durum"] == "GECTI" for kontrol in kontroller)
    dustu = len(kontroller) - gecti
    bulgu_sayisi = sum(kontrol["bulgu_sayisi"] for kontrol in kontroller)
    mutasyon_basarili = sum(m["durum"] == "GECTI" for m in mutasyonlar)
    return {
        "gorev": "T130 SONRASI MEKANIK CAPRAZ DENETIM",
        "hukum_siniri": "Bu rapor mimarin T130 denetiminin yerine gecmez; onay veya terfi hukmu vermez.",
        "sha_siniri": (
            "models/*.pt ve jetson_paket/models/*.pt|*.onnx artefaktlari bu ortamda yoktur. "
            "sha DOSYADAN dogrulanmadi; yalniz committed JSON/metin SHA dizgeleri caprazlandi."
        ),
        "diger_sinirlar": [
            "Kararlilik JSON payloadlarinda `tohum` alani yok; tohum 7 yalniz dosya adinda kayitli.",
            "ONNX export manifestinde SHA alani yok; ONNX SHA paket manifesti dizgesinden caprazlandi.",
            "kapilar kosulMADI (yerel)",
        ],
        "ozet": {
            "kontrol": len(kontroller),
            "GECTI": gecti,
            "DUSTU": dustu,
            "bulgu": bulgu_sayisi,
            "sentetik_mutasyon": len(mutasyonlar),
            "sentetik_mutasyon_beklendigi_gibi_DUSTU": mutasyon_basarili,
        },
        "kontroller": kontroller,
        "sentetik_mutasyon_sinamalari": mutasyonlar,
    }


def _argumanlar() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T130 sonrasi mekanik capraz denetim")
    parser.add_argument("--kok", type=Path, default=KOK)
    parser.add_argument("--rapor", type=Path, default=VARSAYILAN_RAPOR)
    return parser.parse_args()


def main() -> int:
    args = _argumanlar()
    rapor = rapor_uret(args.kok.resolve())
    metin = json.dumps(rapor, ensure_ascii=False, indent=2) + "\n"
    args.rapor.parent.mkdir(parents=True, exist_ok=True)
    args.rapor.write_text(metin, encoding="utf-8", newline="\n")
    print(metin, end="")
    mutasyon_dustu = rapor["ozet"]["sentetik_mutasyon_beklendigi_gibi_DUSTU"]
    basarili = rapor["ozet"]["DUSTU"] == 0 and mutasyon_dustu == rapor["ozet"]["sentetik_mutasyon"]
    return 0 if basarili else 1


if __name__ == "__main__":
    raise SystemExit(main())

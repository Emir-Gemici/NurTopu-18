# `data/kabul/` — üretim modelinin KABUL KÜMELERİ (T220 · K2, 10 Eylül 2026)

> Neden burada: `config/model_registry.json` `kabul_kumesi*` alanları eskiden çıplak
> `O:/navitas-local-train/calisma/...` yolu taşıyordu (madde 16 ihlali). Jetson'da
> (`~/navitas`) `65_kabul_denetcisi` ve `170_engine_karar_denkligi.py --s-kume kabul`
> dizini bulamıyor, K5/K5A kolları ve engine↔pt kabul kararı **ÖLÇÜLEMİYORDU**
> (`JETSON_OTURUM_DURUMU_20260909.md` §5.1, `results/jetson_20260906/K10_LISTE.md` #3/#4).
> Karar (T220 ön kaydı): toplam boyut < 150 MB ise depoya, değilse sıkıştırılmış paket.
> **Ölçüldü: T66 37 MB (547 dosya) + T189 34 MB (524 dosya) = 71 MB → depoya alındı.**

| dizin | ne | dosya | parmak izi (`65_kabul_denetcisi.kume_parmak_izi`, ad+boyut) |
|---|---|---|---|
| `sentetik_arena_kadraj_t66/` | K1–K4/K7 **yatay** kabul kümesi (T66; tohum 7, 260 kare, mpp 0,078125) | 547 | `sha256:604c037f…` = registry `kabul_kumesi_parmak_izi` (n=547) |
| `sentetik_arena_kadraj_ACILI_t189/` | K5A **açılı** bariyer kolu (T189; `--bariyer-acisi 90`) | 524 | `sha256:735ecc81…` |

**Bayt-eş kopya.** İki dizin `O:/navitas-local-train/calisma/` altındaki kaynaktan olduğu
gibi kopyalandı (T220'de parmak izi kaynak ↔ kopya **EŞ** ölçüldü); içlerine dosya
**eklenmez, silinmez, değiştirilmez** — küme dondurulmuştur (D-263 §4.3, K1/K7 çapaları
buna bağlı). Bu yüzden `data.yaml` içindeki tarihsel `path:` satırı da olduğu gibi durur
(o alan yalnız YOLO eğitim/val komutları içindir; kabul zinciri onu okumaz).

**Okuyucular (göreli yolu depo köküne çözer):** `scripts/olcum/65_kabul_denetcisi.py`
(`kabul_kumesi_yolu`, `kabul_kumesi_acili_yolu`), `170_engine_karar_denkligi.s_kumesi`,
`comms/yks_gui._kabul_kumesi_koku`, `151_k7_serit_dogrulugu`, `162_yaw_kadraj_zarfi`.
`.gitignore`'daki genel `images/` kalıbı için istisna: `!data/kabul/*/images/`.

**Jetson'a aktarım:** depo klonundan (`~/proje/github/navitas_github`) paket köküne
`data/kabul/` **olduğu gibi** kopyalanır (sparse klonda `git sparse-checkout add data/kabul`).
Sonra: `python scripts/olcum/170_engine_karar_denkligi.py --s-kume kabul --r-genislik 1280 --json <çıktı>`
(K2 nihai kararı; D-303 oransal eşiği 5/260). Nöbetçi: `tests/test_t220_jetson_istekleri.py`.

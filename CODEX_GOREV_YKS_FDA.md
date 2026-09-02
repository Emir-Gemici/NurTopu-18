# CODEX GÖREVİ — `yks_gui` FDA görev kipi (21 Eylül Adıyaman uçuşu)

> **Yapıştırılabilir prompt.** Zincir: mimar (Claude 2) → amele (Codex).
> Sözleşme: `CONTRACTS.md` **§6.7** (bağlayıcı, tablo dahil oku).
> Disiplin: `CODEX_WORKERS.md` (yorumlayıcı tam yolu, kapıyı gerçekten koş, AI atfı yok,
> commit yazarı depo yapılandırmasından).

---

## Niçin (tek cümle)

21 Eylül'de hakem "tespiti onayla" dediğinde **YKS ekranı onayı tamamlayamıyor**: 2/2 adımı
İKA'nın ACK kanıtını şart koşuyor, o uçuşta İKA yok. Şartname §5.3.2 hakem onayını zorunlu
kıldığı için bu, uçuşu geçersiz kılar. `--fda` bugün yalnız süre bütçesini değiştiriyor;
görev akışının kalanı hâlâ yarışma günü görevini (§2.2 mancınık + paraşüt + İKA) varsayıyor.

## Ne yapılacak

`comms/yks_gui.py` içinde **`--fda` kipini tamamla**. Davranış tablosu `CONTRACTS.md §6.7`.
Özet:

1. **Hakem onayı 2/2:** FDA kipinde `ika_aktarim_kaniti_var()` şartı **aranmaz**; onay
   tamamlanır ve İHA'ya `ack(seq, "yks", ref_tip)` gider (§6.6 — `ref_tip` **zorunlu**).
   Ekranda gerekçe görünür: `FDA §5.3.2: İKA yok — onay YKS aktarımına dayanır`.
   Yarışma kipinde davranış **bayt-eş aynı** kalır (K8 fail-closed korunur).
2. **PARAŞÜT:** FDA'da düğme kapalı **ve** `parasut()` çağrılsa bile link'e hiçbir şey
   yazılmaz; KIRMIZI log: `FDA kipinde paraşüt yok (çoklu rotor)`. Etiket `PARAŞÜT (FDA dışı)`.
3. **İKA BAŞLAT:** FDA'da kapalı; `ika_baslat()` `IKA_GO` **yazmaz**; etiket `İKA (FDA dışı)`.
4. **FIRLATMA → `KALKIŞ`:** FDA'da etiket değişir, damga kalkış anıdır. **ARM kilidi aynen**
   (taze HEARTBEAT + ARM olmadan damga yok — D-393; bu kilit gevşetilmez).
5. Kip **açılışta** belirlenir, koşarken değişmez, ekranda sürekli görünür.

**Dokunma:** `comms/protocol.py`, `comms/link.py`, `codes/*` (sabit gerekiyorsa
`codes/karar_sozlesmesi.py`'ye NEDEN yorumlu ekle — çıplak sayı yasak, madde 16).

## Testler — `tests/test_faz_b_yks_fda_kipi.py` (yeni)

Tk'siz `YksArayuz.__new__` kalıbı repoda var (`tests/test_p9abc_yks.py`,
`tests/test_yks_gui_komut_durustlugu.py`); gerçek `UDPLink` loopback kullan, sahte link değil.

| # | kilit |
|---|---|
| 1 | FDA'da 2/2 onay **İKA kanıtı olmadan** tamamlanır; link'e giden ACK `ref_tip` taşır ve `ref == rota["seq"]` |
| 2 | Yarışma kipinde (varsayılan) aynı senaryo **REDDEDİLİR** ve ACK gitmez (regresyon yok) |
| 3 | FDA'da `parasut()` sonrası link'e `PARACHUTE` **yazılmadı**; KIRMIZI log var |
| 4 | FDA'da `ika_baslat()` sonrası link'e `IKA_GO` **yazılmadı** |
| 5 | FDA'da FIRLATMA etiketi `KALKIŞ`; ARM doğrulanmadan damga **atılmaz** (mevcut kilit korunur) |
| 6 | FDA'da İHA limiti `SARTNAME_FDA_OPERASYON_SURESI_S`, yarışma kipinde `SARTNAME_IHA_GOREV_SURESI_S` |

**Mutasyon (raporunda ham çıktı ver):** FDA kontrolünü tek satır `if False:` yapıp
testleri koş — 1, 3, 4 düşmeli. Düşmeyen varsa test eksiktir.

## Kapılar (hepsi koşulacak, ham çıktı raporda)

```
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_faz_b_yks_fda_kipi.py" -v
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_yks_gui_*.py"
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_p9abc_yks.py"
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_ika_go_*.py"
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_t170*.py"
O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py        # 15/15
```

⚠ **Şu an aynı dosyada yarım işin var** (`GORUNUM_SECENEKLERI`'ne `"kamera"` eklendi ama
`self.gorunum("kamera")` çağrısı yok → `test_yks_gui_uretim_hizasi.py::
test_gorunum_eslemesi_URETIMIN_IC_ADLARIYLA_AYNI` **DÜŞÜYOR**). Bu görevden **önce** onu
kapat; suit kırmızıyken commit/push yok (D-360).

## Teslim

Türkçe commit; `comms/yks_gui.py` + yeni test + (gerekirse) `karar_sozlesmesi.py`.
Raporunda: değişen dosyalar, **ham** test çıktıları, mutasyon sonucu, YAPILAMADI listesi.
Denetimi **Claude 2** yapar — kendi işini onaylamazsın (madde 19).

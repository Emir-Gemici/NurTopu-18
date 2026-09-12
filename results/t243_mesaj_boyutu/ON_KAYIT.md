# T243 ön kayıt — mesaj paket boyutu + gerçek görev veri hızı (Y-3.3.4-M03)

**Tarih:** 12 Eylül 2026, ölçümden önce yazıldı (D-462 C).

## Ölçülecek

1. **Boyut tablosu (worst-case, `comms/protocol.py` `encode()` ile, gerçek çağrı):**
   her mesaj tipi için en büyük gerçekçi gövde. Worst-case seçimi kaynaklıdır,
   uydurulmaz:
   - `OPEN_ROUTE`: `waypoints` sayısı 0 ve `codes/costmap_path_finder.py:118`
     `MAKS_WP=64` (kaynak sabiti, elle yazılmayacak); koordinatlar
     `CONTRACTS.md` §"İHA-UB 300×300 m" sınırına göre en geniş işaretli
     ondalıklı değer (`-150.000`/`149.999` gibi).
   - `NO_ROUTE`: `sebep` en uzun gerçek sabit — `codes/karar_sozlesmesi.py`
     içindeki sabitler taranır, en uzunu kullanılır (bugün
     `ICERIK_YOK_LETTERBOX_SUPHESI`, 28 karakter); `detay` boş DEĞİL, aynı
     uzunlukta örnek metin.
   - `HEARTBEAT`: `comms/protocol.py:116` `HEARTBEAT_TELEMETRI_ALANLARI`
     **tam dolu** (hiçbir alan atlanmaz).
   - `ACK`: `ref_tip`, `ref_cmd`, `sonuc` üçü de dolu, en uzun gerçek
     sabitlerle (`ref_cmd="PARACHUTE"`, `sonuc="ACCEPTED"`).
   - `CMD`: en uzun gerçek `cmd`/`hedef` çifti.
   - `IHA_LANDED`.
2. **Gerçek UDP loopback veri hızı:** `tests/test_rpi_telsiz_yayin.py`'deki
   `_Alicilar`/`KararYayinci` altyapısı yeniden kullanılır (sahte soket
   DEĞİL, gerçek `127.0.0.1` UDP). 10 saniye boyunca gerçek karar akışı
   (OPEN_ROUTE `repeat=4`) + `IHA_HEARTBEAT_ARALIK_S` aralıklı HEARTBEAT +
   gerçek `IkaReceiver` ACK'i çalıştırılır; gönderilen TOPLAM bayt sayaçla
   ölçülür (uydurulmaz).
3. **SiK 57600 8N1 doluluk oranı:** ölçülen bayt/s, nominal 57600 baud 8N1
   kapasitesine (`57600/10` = 5760 B/s, start+stop biti dahil) oranlanır.

## Kabul ölçütü (eşik yok, yalnız RAPOR)

Bu bir kapı testi değildir — yönergenin istediği **görünürlüktür** (Y-3.3.4-M03
"nihai paket yapısı ve veri hızı"). Sayı ne çıkarsa FDR'ye öyle yazılır;
"iyi/kötü" hükmü verilmez, yalnız T250'nin (ECC ile ~%71/%143 doluluk)
bağlamına bir veri noktası daha eklenir.

## Ham çıktı

`results/t243_mesaj_boyutu/olcum.json` — betik: `scripts/mesaj_boyutu_ve_veri_hizi.py`.

# ONARIM-03c — İKA da eşleşmeyle bulunur (kod altyapısı; Raspberry Pi henüz kurulmadı)

**Durum:** KAPANDI (yazılım, PC'de testli) · RPi üzerinde koşu **YOK** (kullanıcı: "rp sistemi daha kurulmadı, temel mantığı ve kod altyapısını kur")
**Tarih:** 17 Eylül 2026

## Yapılan
- `comms/yks_kesif.py` genelleşti: `DUGUM_TURLERI = ("YKS", "IKA")`; duyuru tipi `<TUR>_DUYURU` **imzalı gövdenin içinde** → YKS duyurusu İKA diye kabul edilemez (tür değiştirme = İMZA_RED). `DugumSecici` (= `YksSecici`), seçici kendi türü dışındaki duyuruyu `BASKA_TUR` sayar. Eski (tür alansız) eşleşme dosyaları YKS sayılır. `KesifDinleyici` iplik (YKS'de İKA'yı dinlemek için).
- `comms/ika_receiver.py --eslesme DOSYA`: İKA kendini duyurur (tür IKA şart; seri kipte başlamaz); hedefler broadcast + `--yks` host'u.
- `comms/yks_gui.py --ika-eslesme DOSYA` (`--ika` ile birlikte verilmez): İKA adresi duyurudan öğrenilir; **kaynak kilidi açık kalır** — İKA bulunana dek İKA verisi reddedilir (fail-closed), bulununca `sabit_adr["ika"]` pinlenir, günlüğe `İKA KEŞFİ`.
- `comms/seri_hub.py --lan-ika-eslesme DOSYA` (`--lan-yks-eslesme` ile, aynı 5010 soketi): İKA bulununca Jetson çerçeveleri (rota, iniş, heartbeat) **İKA'ya da** aynalanır — YKS henüz bulunmamış olsa bile; İKA IP'sinden gelen çerçeve (ACK) tüketicilere gider.
- `jetson_baslat.sh`: `IKA_ESLESME` → hub `--lan-ika-eslesme`; `YKS_ESLESME` olmadan `[YOK]`.
- `scripts/yks_eslestir.py`: `yeni/esle --tur IKA`; `tara` tür:kimlik listeler.

## RPi kurulumunda yapılacak (insan)
1. RPi'de: `python3 scripts/yks_eslestir.py yeni --tur IKA --dosya ~/.config/navitas/ika_eslesme.json` → kod not edilir.
2. Aynı dosya YKS PC'sine (`--ika-eslesme`) ve Jetson'a (`/etc/navitas/ika_eslesme.json`, n4vitas 0600) kopyalanır; kodlar karşılaştırılır.
3. RPi: `ika_receiver.py --bind 0.0.0.0:5006 --yks <PC>:5005 --eslesme …` · Jetson `saha_beyan.env`: `IKA_ESLESME=/etc/navitas/ika_eslesme.json` → `sudo jetson_baslat.sh`.

## Kanıt
```
tests/test_onarim03c_ika_kesfi.py  Ran 7  OK
  I1 tür ayrımı + tür değiştirme İMZA_RED + eski dosya YKS · I2 YKS kaynak kilidi: bulunmadan ret, sonra kabul; CLI çakışması
  I3 İKA duyurusu (tür şartı, seri kipte yok, hedefler) · I4 hub İKA aynası (YKS'siz) + İKA ACK tüketiciye · I5 jetson_baslat IKA_ESLESME
mutasyon: tür denetimi kaldırıldı -> FAIL; geri alınca OK
test_onarim03_yks_kesif OK · test_onarim09_coklu_hat OK · test_jetson_comms_paketi OK · test_kilavuz_kurulum_yordami OK
test_yks_hakem_kanit_olaylari OK · test_ika_go_gate OK · test_dalga2_k1_k5_k8_kusurlari OK · test_faz_b_jetson_baslat OK · test_faz_b_seri_hub OK · test_belge_kilidi OK
test_yks_mk15_hakem_ekrani: yalnız önceden kırmızı H2c
```

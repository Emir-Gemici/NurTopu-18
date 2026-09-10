# Akış diyagramı (c) — düğüm → dosya:satır tablosu

Kaynak: `FDR/sekiller/akis_c.mmd` · koddan türetildi: commit `4ee70d9`, 2026-09-10 · üretici: `scripts/akis_diyagram_dogrula.py --tablo`

Düğüm kuralı: **fonksiyon** = `def ad()` ve satır o tanımın başı; **karar** = koşul metni koddan birebir; **blok** = deyim koddan birebir. Doğrulama sütunu: `tam` = tam satır, `±n` = n satır sapma (tolerans 3). Başka düğüm tipi yoktur.

| # | düğüm | tür | alt-grafik | metin | dosya:satır | doğrulama |
|---|---|---|---|---|---|---|
| 1 | `sC1` | fonksiyon | — | `def main()` | `comms/iha_inis_yayinci.py:467` | tam |
| 2 | `c01` | fonksiyon | sC1 | `def seri_pixhawk_kilidini_uygula()` | `comms/inis_kaniti.py:136` | tam |
| 3 | `c02` | karar | sC1 | `if args.serial and (args.ika or args.yks):` | `comms/iha_inis_yayinci.py:477` | tam |
| 4 | `c03` | fonksiyon | sC1 | `def mavlink_baglantisi_ac()` | `comms/inis_kaniti.py:73` | tam |
| 5 | `c04` | blok | sC1 | `son_tarih = time.monotonic() + args.kanit_timeout ⏎ mav.inis_kaniti_deadline_monotonic = son_tarih` | `comms/iha_inis_yayinci.py:515` | tam |
| 6 | `c05` | fonksiyon | sC1 | `def AkisIstekcisi.iste()` | `comms/iha_inis_yayinci.py:200` | tam |
| 7 | `c06` | fonksiyon | sC1 | `def AkisGozcusu.__init__()` | `comms/iha_inis_yayinci.py:327` | tam |
| 8 | `c07` | karar | sC1 | `while not yerde and time.monotonic() < son_tarih:` | `comms/iha_inis_yayinci.py:531` | tam |
| 9 | `c09` | karar | sC1 | `if not yerde:` | `comms/iha_inis_yayinci.py:537` | tam |
| 10 | `c10` | blok | sC1 | `return 3` | `comms/iha_inis_yayinci.py:540` | tam |
| 11 | `c11` | karar | sC1 | `if args.serial:` | `comms/iha_inis_yayinci.py:542` | tam |
| 12 | `c12` | blok | sC1 | `link = (SerialLink(args.serial, args.baud)` | `comms/iha_inis_yayinci.py:544` | tam |
| 13 | `c14` | blok | sC1 | `return 0 if basarili else 5` | `comms/iha_inis_yayinci.py:559` | tam |
| 14 | `c15` | fonksiyon | sC1 | `def _mavlink_kapat()` | `comms/iha_inis_yayinci.py:458` | tam |
| 15 | `sC2` | fonksiyon | — | `def AkisIstekcisi.bakim()` | `comms/iha_inis_yayinci.py:281` | tam |
| 16 | `c20` | karar | sC2 | `if self._son_istek is None:` | `comms/iha_inis_yayinci.py:283` | tam |
| 17 | `c21` | karar | sC2 | `if self._bekleyen and mav_hedefi_biliniyor_mu(self._mav):` | `comms/iha_inis_yayinci.py:286` | tam |
| 18 | `c22` | karar | sC2 | `if not self._sessiz and sessizlik > self._sessizlik_tavani_s:` | `comms/iha_inis_yayinci.py:291` | tam |
| 19 | `c23` | karar | sC2 | `if simdi - self._son_istek >= self._istek_araligi_s:` | `comms/iha_inis_yayinci.py:298` | tam |
| 20 | `c24` | blok | sC2 | `return False` | `comms/iha_inis_yayinci.py:300` | tam |
| 21 | `sC3` | fonksiyon | — | `def _yerde_mi_sahipli()` | `comms/inis_kaniti.py:937` | tam |
| 22 | `c33` | karar | sC3 | `while dogrulanan < ardisik:` | `comms/inis_kaniti.py:994` | tam |
| 23 | `c34` | karar | sC3 | `if kalan <= 0:` | `comms/inis_kaniti.py:996` | tam |
| 24 | `c35` | blok | sC3 | `mesaj = mav.recv_match(` | `comms/inis_kaniti.py:999` | tam |
| 25 | `c36` | fonksiyon | sC3 | `def AkisGozcusu.recv_match()` | `comms/iha_inis_yayinci.py:337` | tam |
| 26 | `c37` | fonksiyon | sC3 | `def AkisIstekcisi.gozle()` | `comms/iha_inis_yayinci.py:260` | tam |
| 27 | `c38` | karar | sC3 | `if mesaj is None:` | `comms/inis_kaniti.py:1006` | tam |
| 28 | `c39` | karar | sC3 | `if tip == MESAJ_EXTENDED_SYS_STATE:` | `comms/inis_kaniti.py:1012` | tam |
| 29 | `c40` | karar | sC3 | `if kanit_kaynagi is None:` | `comms/inis_kaniti.py:1017` | tam |
| 30 | `c41` | blok | sC3 | `kanit_kaynagi = kaynak` | `comms/inis_kaniti.py:1018` | tam |
| 31 | `c42` | karar | sC3 | `elif kaynak != kanit_kaynagi:` | `comms/inis_kaniti.py:1019` | tam |
| 32 | `c43` | karar | sC3 | `if isinstance(durum, bool) or not isinstance(durum, int):` | `comms/inis_kaniti.py:1027` | tam |
| 33 | `c44` | karar | sC3 | `if durum != yerde_degeri:` | `comms/inis_kaniti.py:1030` | tam |
| 34 | `c45` | blok | sC3 | `dogrulanan = 0 ⏎ irtifa_bekleniyor = False` | `comms/inis_kaniti.py:1035` | tam |
| 35 | `c46` | blok | sC3 | `irtifa_bekleniyor = True` | `comms/inis_kaniti.py:1038` | tam |
| 36 | `c47` | karar | sC3 | `if tip == MESAJ_GLOBAL_POSITION_INT:` | `comms/inis_kaniti.py:1041` | tam |
| 37 | `c48` | karar | sC3 | `if not irtifa_bekleniyor:` | `comms/inis_kaniti.py:1042` | tam |
| 38 | `c49` | karar | sC3 | `if kaynak is None or kaynak != kanit_kaynagi:` | `comms/inis_kaniti.py:1045` | tam |
| 39 | `c50` | fonksiyon | sC3 | `def _bagil_irtifa_m()` | `comms/inis_kaniti.py:179` | tam |
| 40 | `c51` | karar | sC3 | `if bagil_irtifa is None:` | `comms/inis_kaniti.py:1050` | tam |
| 41 | `c52` | karar | sC3 | `if bagil_irtifa >= tavan:` | `comms/inis_kaniti.py:1053` | tam |
| 42 | `c53` | blok | sC3 | `dogrulanan = 0 ⏎ irtifa_bekleniyor = False` | `comms/inis_kaniti.py:1056` | tam |
| 43 | `c54` | blok | sC3 | `dogrulanan += 1 ⏎ irtifa_bekleniyor = False` | `comms/inis_kaniti.py:1059` | tam |
| 44 | `c55` | blok | sC3 | `return True` | `comms/inis_kaniti.py:1065` | tam |
| 45 | `c56` | blok | sC3 | `return False` | `comms/inis_kaniti.py:1063` | tam |
| 46 | `c57` | blok | sC3 | `return False` | `comms/inis_kaniti.py:997` | tam |
| 47 | `c58` | blok | sC3 | `return False` | `comms/inis_kaniti.py:1029` | tam |
| 48 | `c59` | blok | sC3 | `return False` | `comms/inis_kaniti.py:1052` | tam |
| 49 | `sC4` | fonksiyon | — | `def iha_inisini_yayinla()` | `comms/iha_inis_yayinci.py:361` | tam |
| 50 | `c60` | fonksiyon | sC4 | `def IhaSender.send_iha_landed()` | `comms/iha_sender.py:264` | tam |
| 51 | `c61` | blok | sC4 | `aktarim_tam = acked >= beklenen` | `comms/iha_inis_yayinci.py:389` | tam |
| 52 | `c62` | karar | sC4 | `if heartbeat_until is None and hb_deadline is None:` | `comms/iha_inis_yayinci.py:401` | tam |
| 53 | `c63` | karar | sC4 | `while True:` | `comms/iha_inis_yayinci.py:406` | tam |
| 54 | `c64` | karar | sC4 | `if kalan <= 0.0:` | `comms/iha_inis_yayinci.py:409` | tam |
| 55 | `c65` | karar | sC4 | `if durdur.wait(bekle):` | `comms/iha_inis_yayinci.py:414` | tam |
| 56 | `c66` | fonksiyon | sC4 | `def IhaSender.send_heartbeat()` | `comms/iha_sender.py:247` | tam |
| 57 | `c67` | blok | sC4 | `return aktarim_tam` | `comms/iha_inis_yayinci.py:417` | tam |
| 58 | `c68` | blok | sC4 | `link.close()` | `comms/iha_inis_yayinci.py:419` | tam |
| 59 | `c30` | fonksiyon | — | `def yerde_mi()` | `comms/inis_kaniti.py:925` | tam |
| 60 | `c31` | karar | — | `if not _mav_sahiplen(mav, sahip):` | `comms/inis_kaniti.py:928` | tam |
| 61 | `c32` | fonksiyon | — | `def _mav_sahiplen()` | `comms/inis_kaniti.py:45` | tam |
| 62 | `c00` | fonksiyon | — | `def _arg_parser()` | `comms/iha_inis_yayinci.py:422` | tam |

Toplam 62 düğüm — blok: 19 · fonksiyon: 17 · karar: 26 · tam satır: 62/62

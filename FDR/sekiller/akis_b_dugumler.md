# Akış diyagramı (b) — düğüm → dosya:satır tablosu

Kaynak: `FDR/sekiller/akis_b.mmd` · koddan türetildi: commit `f3441b4`, 2026-09-07 · üretici: `scripts/akis_diyagram_dogrula.py --tablo`

Düğüm kuralı: **fonksiyon** = `def ad()` ve satır o tanımın başı; **karar** = koşul metni koddan birebir; **blok** = deyim koddan birebir. Doğrulama sütunu: `tam` = tam satır, `±n` = n satır sapma (tolerans 3). Başka düğüm tipi yoktur.

| # | düğüm | tür | alt-grafik | metin | dosya:satır | doğrulama |
|---|---|---|---|---|---|---|
| 1 | `sB1` | fonksiyon | — | `def main()` | `comms/iha_komut_alici.py:879` | tam |
| 2 | `b01` | karar | sB1 | `if args.izinli_kaynak is None:` | `comms/iha_komut_alici.py:888` | tam |
| 3 | `b02` | blok | sB1 | `parser.error("--izinli-kaynak HOST:PORT saha komutlari icin zorunlu; "` | `comms/iha_komut_alici.py:889` | tam |
| 4 | `b03` | karar | sB1 | `if args.serial:` | `comms/iha_komut_alici.py:891` | tam |
| 5 | `b04` | fonksiyon | sB1 | `def seri_pixhawk_kilidini_uygula()` | `comms/inis_kaniti.py:136` | tam |
| 6 | `b05` | fonksiyon | sB1 | `def mavlink_baglantisi_ac()` | `comms/inis_kaniti.py:73` | tam |
| 7 | `b06` | blok | sB1 | `link = UDPLink(bind=(h, int(p)))` | `comms/iha_komut_alici.py:916` | tam |
| 8 | `b07` | fonksiyon | sB1 | `def IhaKomutAlici.__init__()` | `comms/iha_komut_alici.py:312` | tam |
| 9 | `b08` | fonksiyon | sB1 | `def IhaKomutAlici.calistir()` | `comms/iha_komut_alici.py:815` | tam |
| 10 | `b09` | fonksiyon | sB1 | `def _kapat()` | `comms/iha_komut_alici.py:870` | tam |
| 11 | `sB2` | fonksiyon | — | `def IhaKomutAlici.poll()` | `comms/iha_komut_alici.py:797` | tam |
| 12 | `b10` | karar | sB2 | `while not self._dur.is_set():` | `comms/iha_komut_alici.py:822` | tam |
| 13 | `b11` | blok | sB2 | `d, adr = self.link.recv()` | `comms/iha_komut_alici.py:803` | tam |
| 14 | `b12` | karar | sB2 | `for m in okuyucu.feed(d):` | `comms/iha_komut_alici.py:810` | tam |
| 15 | `b13` | fonksiyon | sB2 | `def IhaKomutAlici._mavlink_gelen_kutusunu_bosalt()` | `comms/iha_komut_alici.py:782` | tam |
| 16 | `sB3` | fonksiyon | — | `def IhaKomutAlici.isle()` | `comms/iha_komut_alici.py:630` | tam |
| 17 | `b20` | karar | sB3 | `if not isinstance(mesaj, dict) or mesaj.get("type") != MESAJ_TIPI_CMD:` | `comms/iha_komut_alici.py:632` | tam |
| 18 | `b21` | karar | sB3 | `if mesaj.get("hedef") != self.node:` | `comms/iha_komut_alici.py:634` | tam |
| 19 | `b22` | karar | sB3 | `if self.izinli_kaynak is not None:` | `comms/iha_komut_alici.py:636` | tam |
| 20 | `b23` | karar | sB3 | `if gelen != self.izinli_kaynak:` | `comms/iha_komut_alici.py:641` | tam |
| 21 | `b24` | blok | sB3 | `self.sayac["kaynak_red"] += 1` | `comms/iha_komut_alici.py:642` | tam |
| 22 | `b25` | karar | sB3 | `if (isinstance(seq, bool) or not isinstance(seq, int) ⏎ or not isinstance(cmd, str)):` | `comms/iha_komut_alici.py:650` | tam |
| 23 | `b26` | karar | sB3 | `if cmd not in KOMUT_ADLARI:` | `comms/iha_komut_alici.py:658` | tam |
| 24 | `b27` | fonksiyon | sB3 | `def IhaKomutAlici._saat_ofseti()` | `comms/iha_komut_alici.py:447` | tam |
| 25 | `b28` | fonksiyon | sB3 | `def IhaKomutAlici._yerel_saat_adimi()` | `comms/iha_komut_alici.py:420` | tam |
| 26 | `b29` | fonksiyon | sB3 | `def IhaKomutAlici._kestir()` | `comms/iha_komut_alici.py:362` | tam |
| 27 | `b30` | blok | sB3 | `ham = float(simdi) - float(damga) ⏎ yas = ham - (0.0 if ofset is None else ofset)` | `comms/iha_komut_alici.py:680` | tam |
| 28 | `b31` | blok | sB3 | `tavan = KOMUT_YAS_TAVANI_S[cmd]` | `comms/iha_komut_alici.py:682` | tam |
| 29 | `b32` | karar | sB3 | `if ham is not None and (zaman_kabul or ofset is None):` | `comms/iha_komut_alici.py:685` | tam |
| 30 | `b33` | fonksiyon | sB3 | `def IhaKomutAlici._saat_ofseti_ornekle()` | `comms/iha_komut_alici.py:493` | tam |
| 31 | `b34` | karar | sB3 | `if not zaman_kabul:` | `comms/iha_komut_alici.py:697` | tam |
| 32 | `b35` | blok | sB3 | `self.sayac["zaman_red"] += 1` | `comms/iha_komut_alici.py:698` | tam |
| 33 | `b36` | karar | sB3 | `if oturum is not None:` | `comms/iha_komut_alici.py:707` | tam |
| 34 | `b37` | fonksiyon | sB3 | `def oturum_dogrula()` | `comms/protocol.py:174` | tam |
| 35 | `b38` | blok | sB3 | `anahtar = (oturum, seq, cmd)` | `comms/iha_komut_alici.py:715` | tam |
| 36 | `b39` | karar | sB3 | `if anahtar in self._komut_sonuclari:` | `comms/iha_komut_alici.py:716` | tam |
| 37 | `b40` | karar | sB3 | `if self._komut_sonuclari[anahtar]:` | `comms/iha_komut_alici.py:718` | tam |
| 38 | `b41` | karar | sB3 | `if self.mav is None:` | `comms/iha_komut_alici.py:741` | tam |
| 39 | `b42` | karar | sB3 | `if not mav_hedefi_biliniyor_mu(self.mav):` | `comms/iha_komut_alici.py:746` | tam |
| 40 | `b43` | fonksiyon | sB3 | `def IhaKomutAlici._aktar()` | `comms/iha_komut_alici.py:510` | tam |
| 41 | `b44` | blok | sB3 | `self.mav.mav.command_long_send(` | `comms/iha_komut_alici.py:513` | tam |
| 42 | `b49` | karar | sB3 | `if anahtar is not None:` | `comms/iha_komut_alici.py:768` | tam |
| 43 | `b50` | blok | sB3 | `self._komut_sonuclari[anahtar] = bool(kabul)` | `comms/iha_komut_alici.py:769` | tam |
| 44 | `b51` | karar | sB3 | `if not kabul:` | `comms/iha_komut_alici.py:770` | tam |
| 45 | `b52` | blok | sB3 | `self.sayac["aktarilan"] += 1` | `comms/iha_komut_alici.py:776` | tam |
| 46 | `b57` | blok | sB3 | `return False` | `comms/iha_komut_alici.py:633` | tam |
| 47 | `b58` | blok | sB3 | `return False` | `comms/iha_komut_alici.py:635` | tam |
| 48 | `b59` | blok | sB3 | `self.sayac["hata"] += 1` | `comms/iha_komut_alici.py:652` | tam |
| 49 | `b60` | blok | sB3 | `self.sayac["bilinmeyen"] += 1` | `comms/iha_komut_alici.py:659` | tam |
| 50 | `b61` | blok | sB3 | `self.sayac["tekrar"] += 1` | `comms/iha_komut_alici.py:717` | tam |
| 51 | `b62` | blok | sB3 | `self.sayac["hata"] += 1` | `comms/iha_komut_alici.py:742` | tam |
| 52 | `b63` | blok | sB3 | `self.sayac["hata"] += 1` | `comms/iha_komut_alici.py:747` | tam |
| 53 | `b64` | blok | sB3 | `self.sayac["hata"] += 1` | `comms/iha_komut_alici.py:771` | tam |
| 54 | `sB4` | fonksiyon | — | `def IhaKomutAlici._komut_ack_bekle()` | `comms/iha_komut_alici.py:544` | tam |
| 55 | `b45` | karar | sB4 | `if kalan <= 0:` | `comms/iha_komut_alici.py:557` | tam |
| 56 | `b46` | blok | sB4 | `cevap = self.mav.recv_match(type="COMMAND_ACK", blocking=True,` | `comms/iha_komut_alici.py:561` | tam |
| 57 | `b47` | karar | sB4 | `if cevap is None:` | `comms/iha_komut_alici.py:565` | tam |
| 58 | `b48` | karar | sB4 | `if int(getattr(cevap, "command", -1)) != int(mav_cmd):` | `comms/iha_komut_alici.py:570` | tam |
| 59 | `b65` | karar | sB4 | `if kaynak != self.target_system:` | `comms/iha_komut_alici.py:579` | tam |
| 60 | `b66` | karar | sB4 | `if bilesen not in self._ack_basabilen_bilesenler(m):` | `comms/iha_komut_alici.py:600` | tam |
| 61 | `b67` | karar | sB4 | `if sonuc == m.MAV_RESULT_ACCEPTED:` | `comms/iha_komut_alici.py:606` | tam |
| 62 | `sB5` | fonksiyon | — | `def IhaKomutAlici._ack_gonder()` | `comms/iha_komut_alici.py:610` | tam |
| 63 | `b53` | blok | sB5 | `data = encode(ack(seq, self.node, MESAJ_TIPI_CMD,` | `comms/iha_komut_alici.py:611` | tam |
| 64 | `b54` | karar | sB5 | `if adr is None:` | `comms/iha_komut_alici.py:614` | tam |
| 65 | `b55` | blok | sB5 | `self.link.send(data)` | `comms/iha_komut_alici.py:615` | tam |
| 66 | `b56` | blok | sB5 | `self.link.send(data, adr)` | `comms/iha_komut_alici.py:617` | tam |
| 67 | `b68` | blok | sB5 | `self.sayac["ack"] += 1` | `comms/iha_komut_alici.py:624` | tam |
| 68 | `b00` | fonksiyon | — | `def _arg_parser()` | `comms/iha_komut_alici.py:833` | tam |

Toplam 68 düğüm — blok: 24 · fonksiyon: 18 · karar: 26 · tam satır: 68/68

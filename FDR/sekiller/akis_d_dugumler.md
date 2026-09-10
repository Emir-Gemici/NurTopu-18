# Akış diyagramı (d) — düğüm → dosya:satır tablosu

Kaynak: `FDR/sekiller/akis_d.mmd` · koddan türetildi: commit `dcf6edcf`, 2026-09-10 · üretici: `scripts/akis_diyagram_dogrula.py --tablo`

Düğüm kuralı: **fonksiyon** = `def ad()` ve satır o tanımın başı; **karar** = koşul metni koddan birebir; **blok** = deyim koddan birebir. Doğrulama sütunu: `tam` = tam satır, `±n` = n satır sapma (tolerans 3). Başka düğüm tipi yoktur.

| # | düğüm | tür | alt-grafik | metin | dosya:satır | doğrulama |
|---|---|---|---|---|---|---|
| 1 | `sD1` | fonksiyon | — | `def main()` | `comms/yks_gui.py:4560` | tam |
| 2 | `d01` | karar | sD1 | `if not args.serial and not args.demo and not args.iha:` | `comms/yks_gui.py:4637` | tam |
| 3 | `d02` | karar | sD1 | `if args.serial:` | `comms/yks_gui.py:4649` | tam |
| 4 | `d03` | blok | sD1 | `link = SerialLink(args.serial, args.baud)` | `comms/yks_gui.py:4650` | tam |
| 5 | `d04` | fonksiyon | sD1 | `def yks_udp_linki_ac()` | `comms/yks_gui.py:472` | tam |
| 6 | `d05` | fonksiyon | sD1 | `def yki_oturum_kunyesi()` | `comms/yks_gui.py:519` | tam |
| 7 | `d06` | fonksiyon | sD1 | `def varsayilan_hakem_log_yolu()` | `comms/hakem_kaydi.py:21` | tam |
| 8 | `d07` | fonksiyon | sD1 | `def YksArayuz.__init__()` | `comms/yks_gui.py:761` | tam |
| 9 | `d08` | fonksiyon | sD1 | `def YksArayuz._arayuz_kur()` | `comms/yks_gui.py:940` | tam |
| 10 | `d09` | karar | sD1 | `if args.fda:` | `comms/yks_gui.py:4716` | tam |
| 11 | `d10` | fonksiyon | sD1 | `def YksArayuz.fda_kipini_uygula()` | `comms/yks_gui.py:3826` | tam |
| 12 | `d11` | blok | sD1 | `self.fda_kipi = True ⏎ self.IHA_LIMIT = SARTNAME_FDA_OPERASYON_SURESI_S` | `comms/yks_gui.py:3834` | tam |
| 13 | `d12` | blok | sD1 | `kok.mainloop()` | `comms/yks_gui.py:4768` | tam |
| 14 | `d13` | fonksiyon | sD1 | `def kapanis_kaynaklarini_temizle()` | `comms/yks_gui.py:4534` | tam |
| 15 | `sD2` | fonksiyon | — | `def YksArayuz._dinle()` | `comms/yks_gui.py:1561` | tam |
| 16 | `d20` | blok | sD2 | `d, adr = self.link.recv()` | `comms/yks_gui.py:1564` | tam |
| 17 | `d21` | karar | sD2 | `if soket is None or soket.fileno() == -1:` | `comms/yks_gui.py:1571` | tam |
| 18 | `d22` | karar | sD2 | `for m in okuyucu.feed(d):` | `comms/yks_gui.py:1584` | tam |
| 19 | `d23` | blok | sD2 | `self.gelen.put((m, adr))` | `comms/yks_gui.py:1585` | tam |
| 20 | `sD3` | fonksiyon | — | `def YksArayuz._tik()` | `comms/yks_gui.py:1588` | tam |
| 21 | `d30` | karar | sD3 | `while not self.gelen.empty():` | `comms/yks_gui.py:1589` | tam |
| 22 | `d31` | fonksiyon | sD3 | `def YksArayuz._kamera_tazele()` | `comms/yks_gui.py:2748` | tam |
| 23 | `d32` | fonksiyon | sD3 | `def YksArayuz._durum_tazele()` | `comms/yks_gui.py:4126` | tam |
| 24 | `d33` | blok | sD3 | `self.kok.after(120, self._tik)` | `comms/yks_gui.py:1628` | tam |
| 25 | `sD4` | fonksiyon | — | `def YksArayuz._mesaj_isle()` | `comms/yks_gui.py:1646` | tam |
| 26 | `d40` | karar | sD4 | `if getattr(self, "protokol_kilidi", False):` | `comms/yks_gui.py:1647` | tam |
| 27 | `d41` | karar | sD4 | `if getattr(self, "kaynak_kilidi", False):` | `comms/yks_gui.py:1656` | tam |
| 28 | `d42` | fonksiyon | sD4 | `def mesaj_kaynagi_dogrula()` | `comms/yks_gui.py:711` | tam |
| 29 | `d43` | karar | sD4 | `if tip == MESAJ_OPEN_ROUTE:` | `comms/yks_gui.py:1668` | tam |
| 30 | `d44` | karar | sD4 | `if guven_reddi is not None:` | `comms/yks_gui.py:1670` | tam |
| 31 | `d45` | fonksiyon | sD4 | `def YksArayuz._open_route_guven_reddini_goster()` | `comms/yks_gui.py:1915` | tam |
| 32 | `d46` | blok | sD4 | `self.rota, self.rota_adr = m, adr` | `comms/yks_gui.py:1675` | tam |
| 33 | `d47` | karar | sD4 | `if yeni:` | `comms/yks_gui.py:1688` | tam |
| 34 | `d48` | blok | sD4 | `self._kanit_yaz("ROTA_ALINDI", seq=m.get("seq"),` | `comms/yks_gui.py:1694` | tam |
| 35 | `d49` | karar | sD4 | `elif tip == MESAJ_NO_ROUTE:` | `comms/yks_gui.py:1748` | tam |
| 36 | `d50` | blok | sD4 | `self._kanit_yaz("ROTA_YOK", seq=m.get("seq"), sebep=sebep,` | `comms/yks_gui.py:1771` | tam |
| 37 | `d51` | karar | sD4 | `elif tip == MESAJ_ACK:` | `comms/yks_gui.py:1788` | tam |
| 38 | `d52` | karar | sD4 | `elif tip == MESAJ_IHA_LANDED:` | `comms/yks_gui.py:1790` | tam |
| 39 | `d53` | karar | sD4 | `if seq != self.iha_landed_seq:` | `comms/yks_gui.py:1802` | tam |
| 40 | `d54` | blok | sD4 | `self.iha_landed_seq = seq` | `comms/yks_gui.py:1803` | tam |
| 41 | `d55` | fonksiyon | sD4 | `def YksArayuz.iha_indi()` | `comms/yks_gui.py:3689` | tam |
| 42 | `d56` | karar | sD4 | `elif tip == MESAJ_HEARTBEAT:` | `comms/yks_gui.py:1825` | tam |
| 43 | `d57` | blok | sD4 | `self._kanit_yaz( ⏎ "IHA_INIS_KANITI", seq=seq,` | `comms/yks_gui.py:1807` | tam |
| 44 | `d58` | blok | sD4 | `self._erken_ika_rota_ack_esle(m["seq"])` | `comms/yks_gui.py:1743` | tam |
| 45 | `sD5` | fonksiyon | — | `def YksArayuz._ack_isle()` | `comms/yks_gui.py:2130` | tam |
| 46 | `d60` | blok | sD5 | `self._kanit_yaz("ACK_ALINDI", node=m.get("node"), ref=ref,` | `comms/yks_gui.py:2140` | tam |
| 47 | `d61` | karar | sD5 | `if m.get("node") == "iha":` | `comms/yks_gui.py:2142` | tam |
| 48 | `d62` | karar | sD5 | `if m.get("node") != "ika":` | `comms/yks_gui.py:2196` | tam |
| 49 | `d63` | karar | sD5 | `if self.ika_go_tekrar.ack_geldi(m):` | `comms/yks_gui.py:2200` | tam |
| 50 | `d64` | karar | sD5 | `if ref_tip in (None, MESAJ_OPEN_ROUTE) and ref not in self.ika_rota_ack:` | `comms/yks_gui.py:2208` | tam |
| 51 | `d68` | karar | sD5 | `if self.rota and ref == self.rota["seq"]:` | `comms/yks_gui.py:2209` | tam |
| 52 | `d69` | karar | sD5 | `elif ref_tip == MESAJ_OPEN_ROUTE:` | `comms/yks_gui.py:2211` | tam |
| 53 | `sD10` | fonksiyon | — | `def YksArayuz._ika_rota_ack_bagla()` | `comms/yks_gui.py:2216` | tam |
| 54 | `d84` | karar | sD10 | `if erken:` | `comms/yks_gui.py:2231` | tam |
| 55 | `d65` | blok | sD10 | `self._kanit_yaz("IKA_AKTARIM_KANITI", **alanlar)` | `comms/yks_gui.py:2233` | tam |
| 56 | `d66` | karar | sD10 | `if self.tespit_onayli and not self.onaylandi:` | `comms/yks_gui.py:2242` | tam |
| 57 | `d67` | fonksiyon | sD10 | `def YksArayuz._aktarim_onay_dugmesini_kur()` | `comms/yks_gui.py:2103` | tam |
| 58 | `sD11` | fonksiyon | — | `def YksArayuz._erken_ika_rota_ack_sakla()` | `comms/yks_gui.py:2247` | tam |
| 59 | `d85` | blok | sD11 | `tampon[ref] = (time.time(), simdi, self._iha_havada_mi())` | `comms/yks_gui.py:2267` | tam |
| 60 | `sD12` | fonksiyon | — | `def YksArayuz._erken_ika_rota_ack_esle()` | `comms/yks_gui.py:2277` | tam |
| 61 | `d86` | blok | sD12 | `kayit = tampon.pop(seq, None)` | `comms/yks_gui.py:2286` | tam |
| 62 | `d87` | karar | sD12 | `if kayit is None or seq in self.ika_rota_ack:` | `comms/yks_gui.py:2287` | tam |
| 63 | `d88` | karar | sD12 | `if time.monotonic() - gelis > IKA_ROTA_ACK_ERKEN_TAMPON_S:` | `comms/yks_gui.py:2290` | tam |
| 64 | `d89` | blok | sD12 | `self._ika_rota_ack_bagla(seq, damga, havada, erken=True)` | `comms/yks_gui.py:2296` | tam |
| 65 | `sD6` | fonksiyon | — | `def YksArayuz.onayla()` | `comms/yks_gui.py:1970` | tam |
| 66 | `d70` | karar | sD6 | `if not self.rota or self.rota_yok or self.onaylandi:` | `comms/yks_gui.py:1973` | tam |
| 67 | `d71` | karar | sD6 | `if self._kanit_kilidi_var():` | `comms/yks_gui.py:1955` | tam |
| 68 | `d72` | karar | sD6 | `if rota_ankor_uyarisi(self.rota):` | `comms/yks_gui.py:1988` | tam |
| 69 | `d73` | karar | sD6 | `if self._tespiti_yaslandir():` | `comms/yks_gui.py:1996` | tam |
| 70 | `d74` | karar | sD6 | `if not self.tespit_onayli:` | `comms/yks_gui.py:2002` | tam |
| 71 | `d75` | blok | sD6 | `self.tespit_onayli = True` | `comms/yks_gui.py:2003` | tam |
| 72 | `d76` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_1", seq=self.rota.get("seq"),` | `comms/yks_gui.py:2006` | tam |
| 73 | `d77` | karar | sD6 | `if not self.fda_kipi and not self.ika_aktarim_kaniti_var():` | `comms/yks_gui.py:2017` | tam |
| 74 | `d78` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1990` | tam |
| 75 | `d79` | blok | sD6 | `rota_ack = ack(self.rota["seq"], "yks",` | `comms/yks_gui.py:2028` | tam |
| 76 | `d80` | blok | sD6 | `self.onaylandi = True` | `comms/yks_gui.py:2034` | tam |
| 77 | `d81` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_2", seq=self.rota.get("seq"),` | `comms/yks_gui.py:2050` | tam |
| 78 | `d82` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1990` | tam |
| 79 | `d83` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1990` | tam |
| 80 | `sD7` | fonksiyon | — | `def YksArayuz._kanit_yaz()` | `comms/yks_gui.py:4337` | tam |
| 81 | `d91` | karar | sD7 | `if kayit is None or self._kanit_kilidi_var():` | `comms/yks_gui.py:4339` | tam |
| 82 | `d92` | fonksiyon | sD7 | `def HakemKaydi.yaz()` | `comms/hakem_kaydi.py:96` | tam |
| 83 | `d93` | karar | sD7 | `except Exception as exc:` | `comms/yks_gui.py:4343` | tam |
| 84 | `d94` | fonksiyon | sD7 | `def YksArayuz._kanit_hatasini_goster()` | `comms/yks_gui.py:4313` | tam |
| 85 | `d95` | fonksiyon | sD7 | `def YksArayuz._kanit_kilidi_var()` | `comms/yks_gui.py:4248` | tam |
| 86 | `d96` | blok | sD7 | `return getattr(self, "kanit_kaydi_hatasi", None) is not None` | `comms/yks_gui.py:4261` | tam |
| 87 | `sD8` | fonksiyon | — | `def YksArayuz.firlatma()` | `comms/yks_gui.py:3652` | tam |
| 88 | `d100` | karar | sD8 | `if self._kanit_kilidi_var():` | `comms/yks_gui.py:3659` | tam |
| 89 | `d101` | karar | sD8 | `if (not self._arm_durumu_taze_mi()` | `comms/yks_gui.py:3668` | tam |
| 90 | `d102` | blok | sD8 | `self.t_iha0 = time.monotonic()` | `comms/yks_gui.py:3680` | tam |
| 91 | `d103` | blok | sD8 | `self._kanit_yaz("KRONOMETRE_BASLADI", kron="iha",` | `comms/yks_gui.py:3683` | tam |
| 92 | `sD9` | fonksiyon | — | `def YksArayuz.ika_baslat()` | `comms/yks_gui.py:3706` | tam |
| 93 | `d110` | karar | sD9 | `if self.fda_kipi:` | `comms/yks_gui.py:3709` | tam |
| 94 | `d111` | karar | sD9 | `if self.iha_landed_seq is None:` | `comms/yks_gui.py:3716` | tam |
| 95 | `d112` | karar | sD9 | `if not self.onaylandi:` | `comms/yks_gui.py:3700` | tam |
| 96 | `d113` | blok | sD9 | `komut_mesaji = command("IKA_GO", "ika")` | `comms/yks_gui.py:3728` | tam |
| 97 | `d90` | blok | — | `KANIT_OLAYLARI = (` | `comms/yks_gui.py:145` | tam |
| 98 | `d00` | blok | — | `ap = argparse.ArgumentParser(description="Navitas YKS hakem ekranı")` | `comms/yks_gui.py:4561` | tam |

Toplam 98 düğüm — blok: 31 · fonksiyon: 28 · karar: 39 · tam satır: 98/98

# Akış diyagramı (d) — düğüm → dosya:satır tablosu

Kaynak: `FDR/sekiller/akis_d.mmd` · koddan türetildi: commit `f3441b4`, 2026-09-07 · üretici: `scripts/akis_diyagram_dogrula.py --tablo`

Düğüm kuralı: **fonksiyon** = `def ad()` ve satır o tanımın başı; **karar** = koşul metni koddan birebir; **blok** = deyim koddan birebir. Doğrulama sütunu: `tam` = tam satır, `±n` = n satır sapma (tolerans 3). Başka düğüm tipi yoktur.

| # | düğüm | tür | alt-grafik | metin | dosya:satır | doğrulama |
|---|---|---|---|---|---|---|
| 1 | `sD1` | fonksiyon | — | `def main()` | `comms/yks_gui.py:4341` | tam |
| 2 | `d01` | karar | sD1 | `if not args.serial and not args.demo and not args.iha:` | `comms/yks_gui.py:4406` | tam |
| 3 | `d02` | karar | sD1 | `if args.serial:` | `comms/yks_gui.py:4418` | tam |
| 4 | `d03` | blok | sD1 | `link = SerialLink(args.serial, args.baud)` | `comms/yks_gui.py:4419` | tam |
| 5 | `d04` | fonksiyon | sD1 | `def yks_udp_linki_ac()` | `comms/yks_gui.py:393` | tam |
| 6 | `d05` | fonksiyon | sD1 | `def yki_oturum_kunyesi()` | `comms/yks_gui.py:440` | tam |
| 7 | `d06` | fonksiyon | sD1 | `def varsayilan_hakem_log_yolu()` | `comms/hakem_kaydi.py:21` | tam |
| 8 | `d07` | fonksiyon | sD1 | `def YksArayuz.__init__()` | `comms/yks_gui.py:682` | tam |
| 9 | `d08` | fonksiyon | sD1 | `def YksArayuz._arayuz_kur()` | `comms/yks_gui.py:854` | tam |
| 10 | `d09` | karar | sD1 | `if args.fda:` | `comms/yks_gui.py:4477` | tam |
| 11 | `d10` | fonksiyon | sD1 | `def YksArayuz.fda_kipini_uygula()` | `comms/yks_gui.py:3607` | tam |
| 12 | `d11` | blok | sD1 | `self.fda_kipi = True ⏎ self.IHA_LIMIT = SARTNAME_FDA_OPERASYON_SURESI_S` | `comms/yks_gui.py:3615` | tam |
| 13 | `d12` | blok | sD1 | `kok.mainloop()` | `comms/yks_gui.py:4529` | tam |
| 14 | `d13` | fonksiyon | sD1 | `def kapanis_kaynaklarini_temizle()` | `comms/yks_gui.py:4315` | tam |
| 15 | `sD2` | fonksiyon | — | `def YksArayuz._dinle()` | `comms/yks_gui.py:1436` | tam |
| 16 | `d20` | blok | sD2 | `d, adr = self.link.recv()` | `comms/yks_gui.py:1439` | tam |
| 17 | `d21` | karar | sD2 | `if soket is None or soket.fileno() == -1:` | `comms/yks_gui.py:1446` | tam |
| 18 | `d22` | karar | sD2 | `for m in okuyucu.feed(d):` | `comms/yks_gui.py:1459` | tam |
| 19 | `d23` | blok | sD2 | `self.gelen.put((m, adr))` | `comms/yks_gui.py:1460` | tam |
| 20 | `sD3` | fonksiyon | — | `def YksArayuz._tik()` | `comms/yks_gui.py:1463` | tam |
| 21 | `d30` | karar | sD3 | `while not self.gelen.empty():` | `comms/yks_gui.py:1464` | tam |
| 22 | `d31` | fonksiyon | sD3 | `def YksArayuz._kamera_tazele()` | `comms/yks_gui.py:2545` | tam |
| 23 | `d32` | fonksiyon | sD3 | `def YksArayuz._durum_tazele()` | `comms/yks_gui.py:3907` | tam |
| 24 | `d33` | blok | sD3 | `self.kok.after(120, self._tik)` | `comms/yks_gui.py:1503` | tam |
| 25 | `sD4` | fonksiyon | — | `def YksArayuz._mesaj_isle()` | `comms/yks_gui.py:1521` | tam |
| 26 | `d40` | karar | sD4 | `if getattr(self, "protokol_kilidi", False):` | `comms/yks_gui.py:1522` | tam |
| 27 | `d41` | karar | sD4 | `if getattr(self, "kaynak_kilidi", False):` | `comms/yks_gui.py:1531` | tam |
| 28 | `d42` | fonksiyon | sD4 | `def mesaj_kaynagi_dogrula()` | `comms/yks_gui.py:632` | tam |
| 29 | `d43` | karar | sD4 | `if tip == "OPEN_ROUTE":` | `comms/yks_gui.py:1543` | tam |
| 30 | `d44` | karar | sD4 | `if guven_reddi is not None:` | `comms/yks_gui.py:1545` | tam |
| 31 | `d45` | fonksiyon | sD4 | `def YksArayuz._open_route_guven_reddini_goster()` | `comms/yks_gui.py:1787` | tam |
| 32 | `d46` | blok | sD4 | `self.rota, self.rota_adr = m, adr` | `comms/yks_gui.py:1550` | tam |
| 33 | `d47` | karar | sD4 | `if yeni:` | `comms/yks_gui.py:1563` | tam |
| 34 | `d48` | blok | sD4 | `self._kanit_yaz("ROTA_ALINDI", seq=m.get("seq"),` | `comms/yks_gui.py:1569` | tam |
| 35 | `d49` | karar | sD4 | `elif tip == "NO_ROUTE":` | `comms/yks_gui.py:1620` | tam |
| 36 | `d50` | blok | sD4 | `self._kanit_yaz("ROTA_YOK", seq=m.get("seq"), sebep=sebep,` | `comms/yks_gui.py:1643` | tam |
| 37 | `d51` | karar | sD4 | `elif tip == "ACK":` | `comms/yks_gui.py:1660` | tam |
| 38 | `d52` | karar | sD4 | `elif tip == "IHA_LANDED":` | `comms/yks_gui.py:1662` | tam |
| 39 | `d53` | karar | sD4 | `if seq != self.iha_landed_seq:` | `comms/yks_gui.py:1674` | tam |
| 40 | `d54` | blok | sD4 | `self.iha_landed_seq = seq` | `comms/yks_gui.py:1675` | tam |
| 41 | `d55` | fonksiyon | sD4 | `def YksArayuz.iha_indi()` | `comms/yks_gui.py:3470` | tam |
| 42 | `d56` | karar | sD4 | `elif tip == "HEARTBEAT":` | `comms/yks_gui.py:1697` | tam |
| 43 | `d57` | blok | sD4 | `self._kanit_yaz( ⏎ "IHA_INIS_KANITI", seq=seq,` | `comms/yks_gui.py:1679` | tam |
| 44 | `sD5` | fonksiyon | — | `def YksArayuz._ack_isle()` | `comms/yks_gui.py:2002` | tam |
| 45 | `d60` | blok | sD5 | `self._kanit_yaz("ACK_ALINDI", node=m.get("node"), ref=ref,` | `comms/yks_gui.py:2012` | tam |
| 46 | `d61` | karar | sD5 | `if m.get("node") == "iha":` | `comms/yks_gui.py:2014` | tam |
| 47 | `d62` | karar | sD5 | `if m.get("node") != "ika":` | `comms/yks_gui.py:2068` | tam |
| 48 | `d63` | karar | sD5 | `if self.ika_go_tekrar.ack_geldi(m):` | `comms/yks_gui.py:2072` | tam |
| 49 | `d64` | karar | sD5 | `if (self.rota and ref == self.rota["seq"]` | `comms/yks_gui.py:2080` | tam |
| 50 | `d65` | blok | sD5 | `self._kanit_yaz("IKA_AKTARIM_KANITI", seq=ref, iha_havada=havada)` | `comms/yks_gui.py:2090` | tam |
| 51 | `d66` | karar | sD5 | `if self.tespit_onayli and not self.onaylandi:` | `comms/yks_gui.py:2097` | tam |
| 52 | `d67` | fonksiyon | sD5 | `def YksArayuz._aktarim_onay_dugmesini_kur()` | `comms/yks_gui.py:1975` | tam |
| 53 | `sD6` | fonksiyon | — | `def YksArayuz.onayla()` | `comms/yks_gui.py:1842` | tam |
| 54 | `d70` | karar | sD6 | `if not self.rota or self.rota_yok or self.onaylandi:` | `comms/yks_gui.py:1845` | tam |
| 55 | `d71` | karar | sD6 | `if self._kanit_kilidi_var():` | `comms/yks_gui.py:1852` | tam |
| 56 | `d72` | karar | sD6 | `if rota_ankor_uyarisi(self.rota):` | `comms/yks_gui.py:1860` | tam |
| 57 | `d73` | karar | sD6 | `if self._tespiti_yaslandir():` | `comms/yks_gui.py:1868` | tam |
| 58 | `d74` | karar | sD6 | `if not self.tespit_onayli:` | `comms/yks_gui.py:1874` | tam |
| 59 | `d75` | blok | sD6 | `self.tespit_onayli = True` | `comms/yks_gui.py:1875` | tam |
| 60 | `d76` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_1", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1878` | tam |
| 61 | `d77` | karar | sD6 | `if not self.fda_kipi and not self.ika_aktarim_kaniti_var():` | `comms/yks_gui.py:1889` | tam |
| 62 | `d78` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1893` | tam |
| 63 | `d79` | blok | sD6 | `rota_ack = ack(self.rota["seq"], "yks",` | `comms/yks_gui.py:1900` | tam |
| 64 | `d80` | blok | sD6 | `self.onaylandi = True` | `comms/yks_gui.py:1906` | tam |
| 65 | `d81` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_2", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1922` | tam |
| 66 | `d82` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1862` | tam |
| 67 | `d83` | blok | sD6 | `self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),` | `comms/yks_gui.py:1871` | tam |
| 68 | `sD7` | fonksiyon | — | `def YksArayuz._kanit_yaz()` | `comms/yks_gui.py:4118` | tam |
| 69 | `d91` | karar | sD7 | `if kayit is None or self._kanit_kilidi_var():` | `comms/yks_gui.py:4120` | tam |
| 70 | `d92` | fonksiyon | sD7 | `def HakemKaydi.yaz()` | `comms/hakem_kaydi.py:96` | tam |
| 71 | `d93` | karar | sD7 | `except Exception as exc:` | `comms/yks_gui.py:4124` | tam |
| 72 | `d94` | fonksiyon | sD7 | `def YksArayuz._kanit_hatasini_goster()` | `comms/yks_gui.py:4094` | tam |
| 73 | `d95` | fonksiyon | sD7 | `def YksArayuz._kanit_kilidi_var()` | `comms/yks_gui.py:4029` | tam |
| 74 | `d96` | blok | sD7 | `return getattr(self, "kanit_kaydi_hatasi", None) is not None` | `comms/yks_gui.py:4042` | tam |
| 75 | `sD8` | fonksiyon | — | `def YksArayuz.firlatma()` | `comms/yks_gui.py:3433` | tam |
| 76 | `d100` | karar | sD8 | `if self._kanit_kilidi_var():` | `comms/yks_gui.py:3440` | tam |
| 77 | `d101` | karar | sD8 | `if (not self._arm_durumu_taze_mi()` | `comms/yks_gui.py:3449` | tam |
| 78 | `d102` | blok | sD8 | `self.t_iha0 = time.monotonic()` | `comms/yks_gui.py:3461` | tam |
| 79 | `d103` | blok | sD8 | `self._kanit_yaz("KRONOMETRE_BASLADI", kron="iha",` | `comms/yks_gui.py:3464` | tam |
| 80 | `sD9` | fonksiyon | — | `def YksArayuz.ika_baslat()` | `comms/yks_gui.py:3487` | tam |
| 81 | `d110` | karar | sD9 | `if self.fda_kipi:` | `comms/yks_gui.py:3490` | tam |
| 82 | `d111` | karar | sD9 | `if self.iha_landed_seq is None:` | `comms/yks_gui.py:3497` | tam |
| 83 | `d112` | karar | sD9 | `if not self.onaylandi:` | `comms/yks_gui.py:3502` | tam |
| 84 | `d113` | blok | sD9 | `komut_mesaji = command("IKA_GO", "ika")` | `comms/yks_gui.py:3509` | tam |
| 85 | `d90` | blok | — | `KANIT_OLAYLARI = (` | `comms/yks_gui.py:127` | tam |
| 86 | `d00` | blok | — | `ap = argparse.ArgumentParser(description="Navitas YKS hakem ekranı")` | `comms/yks_gui.py:4342` | tam |

Toplam 86 düğüm — blok: 27 · fonksiyon: 25 · karar: 34 · tam satır: 86/86

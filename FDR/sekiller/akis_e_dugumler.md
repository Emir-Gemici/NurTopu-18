# Akış diyagramı (e) — düğüm → dosya:satır tablosu

Kaynak: `FDR/sekiller/akis_e.mmd` · koddan türetildi: commit `4ee70d9`, 2026-09-10 · üretici: `scripts/akis_diyagram_dogrula.py --tablo`

Düğüm kuralı: **fonksiyon** = `def ad()` ve satır o tanımın başı; **karar** = koşul metni koddan birebir; **blok** = deyim koddan birebir. Doğrulama sütunu: `tam` = tam satır, `±n` = n satır sapma (tolerans 3). Başka düğüm tipi yoktur.

| # | düğüm | tür | alt-grafik | metin | dosya:satır | doğrulama |
|---|---|---|---|---|---|---|
| 1 | `sE1` | fonksiyon | — | `def ika_gorevi()` | `simulation/scripts/ika_nav.py:477` | tam |
| 2 | `e01` | blok | sE1 | `bekleme_deadline = saat() + bekleme_suresi` | `simulation/scripts/ika_nav.py:512` | tam |
| 3 | `e03` | karar | sE1 | `if alindi is None:` | `simulation/scripts/ika_nav.py:520` | tam |
| 4 | `e04` | blok | sE1 | `return 1` | `simulation/scripts/ika_nav.py:523` | tam |
| 5 | `e05` | karar | sE1 | `if isinstance(alindi, dict) and alindi.get("type") == MESAJ_NO_ROUTE:` | `simulation/scripts/ika_nav.py:524` | tam |
| 6 | `e06` | blok | sE1 | `return 2` | `simulation/scripts/ika_nav.py:526` | tam |
| 7 | `e08` | karar | sE1 | `if not izin_bekle(receiver, kalan, deadline_monotonic=bekleme_deadline):` | `simulation/scripts/ika_nav.py:530` | tam |
| 8 | `e09` | blok | sE1 | `return 3` | `simulation/scripts/ika_nav.py:531` | tam |
| 9 | `e10` | blok | sE1 | `surus_deadline = saat() + surus_suresi` | `simulation/scripts/ika_nav.py:533` | tam |
| 10 | `e11` | fonksiyon | sE1 | `def navigate_route()` | `simulation/scripts/ika_nav.py:455` | tam |
| 11 | `e12` | blok | sE1 | `return 0 if basarili else 4` | `simulation/scripts/ika_nav.py:546` | tam |
| 12 | `e13` | blok | sE1 | `send_vel(0, 0)` | `simulation/scripts/ika_nav.py:450` | tam |
| 13 | `e14` | blok | sE1 | `receiver.stop()` | `simulation/scripts/ika_nav.py:554` | tam |
| 14 | `e15` | blok | sE1 | `receiver.link.close()` | `simulation/scripts/ika_nav.py:556` | tam |
| 15 | `sE2` | fonksiyon | — | `def wait_open_route_from_comms()` | `simulation/scripts/ika_nav.py:576` | tam |
| 16 | `e20` | blok | sE2 | `rx = IkaReceiver(link, yks_peer=yks_peer, saat=saat).start()` | `simulation/scripts/ika_nav.py:610` | tam |
| 17 | `e21` | fonksiyon | sE2 | `def IkaReceiver.start()` | `comms/ika_receiver.py:317` | tam |
| 18 | `e22` | fonksiyon | sE2 | `def IkaReceiver._loop()` | `comms/ika_receiver.py:313` | tam |
| 19 | `e23` | fonksiyon | sE2 | `def IkaReceiver._handle()` | `comms/ika_receiver.py:236` | tam |
| 20 | `e24` | karar | sE2 | `while True:` | `simulation/scripts/ika_nav.py:621` | tam |
| 21 | `e25` | blok | sE2 | `terminal_snapshot = _saat() >= deadline` | `simulation/scripts/ika_nav.py:622` | tam |
| 22 | `e26` | fonksiyon | sE2 | `def IkaReceiver.decision_snapshot()` | `comms/ika_receiver.py:79` | tam |
| 23 | `e27` | karar | sE2 | `if karar_zamani is not None and karar_zamani > deadline:` | `simulation/scripts/ika_nav.py:633` | tam |
| 24 | `e28` | karar | sE2 | `if route is not None and no_route is None:` | `simulation/scripts/ika_nav.py:638` | tam |
| 25 | `e29` | fonksiyon | sE2 | `def route_to_world_waypoints()` | `simulation/scripts/ika_nav.py:149` | tam |
| 26 | `e30` | karar | sE2 | `except ValueError as exc:` | `simulation/scripts/ika_nav.py:641` | tam |
| 27 | `e31` | karar | sE2 | `if (guncel_nesil != karar_nesli` | `simulation/scripts/ika_nav.py:654` | tam |
| 28 | `e32` | karar | sE2 | `if keep_receiver:` | `simulation/scripts/ika_nav.py:666` | tam |
| 29 | `e33` | blok | sE2 | `return route, rx` | `simulation/scripts/ika_nav.py:668` | tam |
| 30 | `e34` | karar | sE2 | `if no_route is not None and karar_nesli != son_no_route_nesil:` | `simulation/scripts/ika_nav.py:671` | tam |
| 31 | `e35` | karar | sE2 | `if terminal_snapshot:` | `simulation/scripts/ika_nav.py:628` | tam |
| 32 | `e36` | blok | sE2 | `return no_route` | `simulation/scripts/ika_nav.py:680` | tam |
| 33 | `sE3` | fonksiyon | — | `def receiver_surus_izni_bekle()` | `simulation/scripts/ika_nav.py:265` | tam |
| 34 | `e40` | blok | sE3 | `send_vel(0, 0)` | `simulation/scripts/ika_nav.py:256` | tam |
| 35 | `e41` | fonksiyon | sE3 | `def IkaReceiver.wait_surus_izni()` | `comms/ika_receiver.py:119` | tam |
| 36 | `e42` | karar | sE3 | `if not self._surus_izni_event.wait(timeout):` | `comms/ika_receiver.py:127` | tam |
| 37 | `e43` | fonksiyon | sE3 | `def IkaReceiver._surus_izni_gecerli_unlocked()` | `comms/ika_receiver.py:132` | tam |
| 38 | `e44` | karar | sE3 | `if not self.ika_go or not self.iha_landed:` | `comms/ika_receiver.py:134` | tam |
| 39 | `sE4` | fonksiyon | — | `def navigate()` | `simulation/scripts/ika_nav.py:311` | tam |
| 40 | `e50` | karar | sE4 | `for idx, (wx, wy) in enumerate(wps[1:], 1):` | `simulation/scripts/ika_nav.py:366` | tam |
| 41 | `e51` | karar | sE4 | `while not at_wp:` | `simulation/scripts/ika_nav.py:370` | tam |
| 42 | `e52` | karar | sE4 | `if surus_deadline is not None and saat() >= surus_deadline:` | `simulation/scripts/ika_nav.py:371` | tam |
| 43 | `e53` | blok | sE4 | `return False` | `simulation/scripts/ika_nav.py:308` | tam |
| 44 | `e54` | karar | sE4 | `if not surucu_saglikli():` | `simulation/scripts/ika_nav.py:376` | tam |
| 45 | `e55` | fonksiyon | sE4 | `def surucu_saglikli()` | `simulation/scripts/ika_nav.py:74` | tam |
| 46 | `e56` | karar | sE4 | `if link_ok is not None and not link_ok():` | `simulation/scripts/ika_nav.py:385` | tam |
| 47 | `e57` | fonksiyon | sE4 | `def IkaReceiver.link_ok()` | `comms/ika_receiver.py:74` | tam |
| 48 | `e58` | karar | sE4 | `if not rota_kapisi_acik():` | `simulation/scripts/ika_nav.py:395` | tam |
| 49 | `e59` | fonksiyon | sE4 | `def rota_kapisi_acik()` | `simulation/scripts/ika_nav.py:351` | tam |
| 50 | `e60` | fonksiyon | sE4 | `def receiver_rota_gecerli()` | `simulation/scripts/ika_nav.py:208` | tam |
| 51 | `e61` | karar | sE4 | `if (not getattr(receiver, "ika_go", False)` | `simulation/scripts/ika_nav.py:216` | tam |
| 52 | `e62` | karar | sE4 | `if route is None or no_route is not None:` | `simulation/scripts/ika_nav.py:220` | tam |
| 53 | `e63` | fonksiyon | sE4 | `def get_pose()` | `simulation/scripts/ika_nav.py:79` | tam |
| 54 | `e64` | karar | sE4 | `if cx is None:` | `simulation/scripts/ika_nav.py:401` | tam |
| 55 | `e65` | karar | sE4 | `if dist < hedef_yaricapi:` | `simulation/scripts/ika_nav.py:418` | tam |
| 56 | `e66` | fonksiyon | sE4 | `def steer()` | `simulation/scripts/ika_nav.py:102` | tam |
| 57 | `e67` | karar | sE4 | `if not rota_kapisi_acik():` | `simulation/scripts/ika_nav.py:395` | tam |
| 58 | `e68` | karar | sE4 | `if rota_korumali_gonder is None:` | `simulation/scripts/ika_nav.py:434` | tam |
| 59 | `e69` | fonksiyon | sE4 | `def receiver_korumali_hiz_gonder()` | `simulation/scripts/ika_nav.py:239` | tam |
| 60 | `e70` | fonksiyon | sE4 | `def IkaReceiver.run_if_route_valid()` | `comms/ika_receiver.py:85` | tam |
| 61 | `e71` | karar | sE4 | `if (self.last_rx is None or self.link_lost` | `comms/ika_receiver.py:96` | tam |
| 62 | `e72` | karar | sE4 | `elif not rota_korumali_gonder(r, l):` | `simulation/scripts/ika_nav.py:436` | tam |
| 63 | `e73` | fonksiyon | sE4 | `def rota_gecersiz_dur()` | `simulation/scripts/ika_nav.py:343` | tam |
| 64 | `e77` | blok | sE4 | `return True` | `simulation/scripts/ika_nav.py:452` | tam |
| 65 | `e78` | blok | sE4 | `return False` | `simulation/scripts/ika_nav.py:364` | tam |
| 66 | `sE5` | fonksiyon | — | `def send_vel()` | `simulation/scripts/ika_nav.py:87` | tam |
| 67 | `e75` | fonksiyon | sE5 | `def surucu()` | `simulation/scripts/ika_nav.py:60` | tam |
| 68 | `e76` | blok | sE5 | `_SURUCU = ika_surucu.GazeboSurucu()` | `simulation/scripts/ika_nav.py:64` | tam |
| 69 | `e79` | fonksiyon | sE5 | `def surucu_ayarla()` | `simulation/scripts/ika_nav.py:68` | tam |
| 70 | `e00` | blok | — | `ap = argparse.ArgumentParser(description="İKA navigasyon (dinamik rota + comms)")` | `simulation/scripts/ika_nav.py:696` | tam |

Toplam 70 düğüm — blok: 19 · fonksiyon: 24 · karar: 27 · tam satır: 70/70

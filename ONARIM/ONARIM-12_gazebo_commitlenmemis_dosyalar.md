# ONARIM-12 — Gazebo oturumunun commitlenmemiş iki dosyası birleştirildi

**Durum:** KAPANDI · **Tarih:** 17 Eylül 2026 · **Liste:** madde 12
**Dosyalar:** `simulation/scripts/world_generator.py`, `simulation/plugins/navitas_anim.cc` (bu PC'deki Gazebo oturumu `7e39d664`, REVIEW_LOG D-488/D-489/D-490 — kayıtlar master'da, kod değildi; D-491 §7a bilinçli olarak push etmemişti çünkü bir testi düşürüyordu).

## İçerik (bağımsız inceleme — yazan oturum değil)
- `world_generator.py`:
  - `IKA_SPEED` artık `karar_sozlesmesi.IKA_AZAMI_HIZ_MS` (1,3 m/s) tek kaynağından (D-438f üç-kopya kusuru).
  - `PHASE_SPEED["parasut"]` 5,5 → **3,0 m/s** (kullanıcı isteği 2–4 m/s bandı, D-488).
  - `_seg_box_dist` + `_cluster_route_gap`: moloz/tıkama/chicane kümelerinin **collision kutuları** açık rota şeridine (lane_w/2) giremez; tıkama/dağınık moloz taşarsa atlanır, chicane en çok 6 kez dışarı itilir (D-490: orta/zor İKA'yı fiziksel kilitliyordu). İlk deneme RNG tüketimi eskisiyle aynı; yalnız reddedilen kümelerde dünya değişir.
- `navitas_anim.cc`: `IKA_SPEED` 1,1 → 1,3 (aynı tek kaynak değeri); `/tmp/navitas_model_log.csv` 1 Hz eklemeli, tüm modeller (İHA, paraşüt aşamaları, İKA: wp/rota/durum). `/tmp/navitas_simtime` değişmedi. Include'lar (`<fstream>`, `<cmath>`) mevcut. İmajla derleme + kolay seviye tam koşu kanıtı: D-488, `simulation/recordings/demo_bilinen_rota_kolay_20260915_114300/`.

## Düşen test — kök neden ÖLÇÜLDÜ
`test_sim_mujoco_zincir … test_duman_60s_altinda_ve_metrik_semasi`: `sure_sim_iha_profil 38.81 != 36.98`.
- Değişikliklerin hepsi yerindeyken: **FAIL 38,81**.
- Yalnız `parasut` 3,0 → 5,5 geri alınınca: **OK (36,98)**.
→ Fark yalnız bilinçli paraşüt hızı değişikliğinden (daha yavaş iniş = daha uzun profil). Test beklentisi **38,81**'e güncellendi, gerekçe test içinde. Eşik/tolerans değişmedi (places=1).

## Kanıt — simülasyon testleri, önce (HEAD temiz worktree) ↔ sonra
13 dosya (`find tests -name 'test_*' | grep sim|gazebo|arena|dogrula` + dosyaları anan testler): **fark yok** (tek fark `test_gercek_arena_kapisi` atlanan sayısı 6↔2 — worktree'de izlenmeyen veri yok, ortam). Sonrası: `test_sim_mujoco_zincir` OK · `test_sim_mujoco_video` OK · `test_arena_sinir_dedektoru` OK · `test_copy_paste_arena` OK · `test_navitas_sim_reporting` OK · `test_sim_mission_demo_port` OK · `test_yks_harita_yerlesimi` OK · `test_faz_b_mavlink_dogrula` OK · `test_t135_kamera_dogrula_icerik` OK.
İki tarafta da aynı kırmızı (bu işten bağımsız): `test_p8_sim_katmani` (F1 E3), `test_sim_mujoco_arena` (F2 E3), `test_sim_mujoco_olcum` (F4).

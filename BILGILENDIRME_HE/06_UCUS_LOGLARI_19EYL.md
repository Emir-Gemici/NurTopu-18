# 06 — 19 Eylül uçuş logları

Kanıtlar: defter D-505 (+ek 1–4), D-506 (+kapanış). Loglar `results/ucus_20260919/`, betikler `results/ucus_20260919/betikler/`.

## 12:59 logu — dört askı uçuşu, "havada kayma"

Log: `2026-09-19 12-59-14.bin` (521 s). 3115 motorlar ve yeni parametre dosyası takılıydı.

- Uçuşlar temiz. Sonuç: tahrik ve ayar yeterli.

| Ölçü | Değer |
|---|---|
| roll RMS | 1,3° |
| pitch RMS | 1,7° |
| VibeZ ortalama | 1,4 |
| clip | 0 |
| hover | 0,347 (öğrenildi) |
| akım tepe | 52 A |

- **Kayma:** gerçek ama 1–2 m. GPS gezinmesi RTK'sız GPS için olağan (HDop 0,6–0,8).
  Sabahki sabit sol eğim ve kalkıştaki sağa kayma, öğleden sonraki logla karşılaştırınca **rüzgâr** çıktı.
  Motor montajı ya da PID kaynaklı değil. Gövdeye bağlı ~2° burun aşağı eğim 12 Eyl'den beri var; zararsız.
- 🔴 **GCS failsafe, GUIDED'da:** 456 s'de GUIDED'dayken LAND'a düştü. Mission Planner telsizden bağlıydı, heartbeat 5 s koptu.
  Jetson açıkken bu olmaz (04 §GCS failsafe).

## 14:09 logu — 14:18 düşüşü

Log: `2026-09-19 14-09-54.bin` (527 s). Dört uçuş var; kaza dördüncü uçuşta.

Zaman çizgisi:

1. 431–498 s: Loiter'da 11 m'ye tırmanış. Sallanma yok.
2. 498,4 s: pilot LAND seçti.
3. 506–508 s: **ön-sol motor (M3)** diğerlerinden daha çok güç istemeye başladı. İtki düşüyordu.
4. 508,8–509,2 s: M3 0,4 s'de tavana (1949 µs) vurdu. Roll −22°, pitch −25°. Ön-sol köşe düşüyordu.
5. 509–511 s: kart 3 motorla tutundu.
6. 511 s: çapraz motor tabana indi, yalnız iki motor kaldı.
7. 511,5 s: **~1 m'den 6,4 g çarpma.**

- **Elenenler:** pil ve ESC gerilim kesmesi (çökme M3 kaybından sonra geldi), failsafe, PID, titreşim, GPS/EKF.
- **Pilot beyanı "çok iyi kontrol ettim":** 509–511,5 s arası çubuklar ortadaydı. Toparlamayı kart yaptı. LAND kipinde pilot yalnız konumu kaydırabilir.
- **Sebep (Halil beyanı, 19:15):** **sol ön pervane somunu.** Giderildi. Fiziksel kanıt ya da fotoğraf yok.
  Log imzası somun gevşemesiyle uyumlu: 3 s süren kademeli itki kaybı, sonra motor tavanda.
- ⚠ **Örüntü:** 17 Eyl düşüşü **ön-sağ** (M1) köşedeydi (D-491), 19 Eyl düşüşü **ön-sol** (M3).
  İki düşüş, iki farklı köşe, aynı imza. **Pervane tutma sistemi** ortak şüpheli.
  Her uçuştan önce dört somun elle kontrol edilmeli (08).
- Yan bulgu: dördüncü uçuş başında pil dinlenik 14,0 V idi (~%25–35). 72 A çekişte 12,1 V'a düştü. Düşük pille uçulmamalı.

## Log okurken

- Motor kanalları **C9–C12**: C9 = M4 arka-sağ, C10 = M2 arka-sol, C11 = M1 ön-sağ, C12 = M3 ön-sol.
- "in-flight yaw alignment complete" her uçuşta bir kez gelir. Bu `EK3_MAG_CAL 3` rutinidir, arıza değil.
- Analiz betiği: `scripts/ucus_bin_analiz.py`. Askı eğimi betiği: `results/ucus_20260919/betikler/aski_egim.py`.

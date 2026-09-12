# A11 — CAMDAN CAMA VİDEO GECİKMESİ · **HESAP** (ölçüm değil)
**13 Eylül 2026 · Kamera ve MK15 yer birimi elde olmadığı için bütçe hesabı yapıldı.**
**Ölçüm planı: 21 Eylül uçuş öncesi, kronometre yöntemi (bu dosyanın §4'ü).**

## 1. Zincir (kumandada HDMI portu YOK → RTSP çekme yolu, D-471/T255)

```
sahne → IMX477 sensör → Jetson ISP (nvargus) → SIYI HDMI→Ethernet dönüştürücü (H.264)
      → MK15 hava birimi → 5,8 GHz → MK15 yer birimi → RTSP çekme (PC)
      → çözme → YKS Qt video paneli → monitör
```

## 2. Gecikme bütçesi

| # | Bileşen | En iyi | Tipik | En kötü | Dayanak |
|---|---|---|---|---|---|
| 1 | Sensör pozlama + okuma (1080p30) | 33 | 33 | 33 | 1 kare @30 fps = 33,3 ms |
| 2 | Jetson ISP / nvargus tampon | 66 | 83 | 100 | 2–3 kare tamponu (Argus varsayılanı) |
| 3 | Dönüştürücü H.264 kodlama | 33 | 50 | 66 | 1–2 kare; NVENC yok, dönüştürücü kendi kodluyor |
| 4 | MK15 radyo hattı (hava+yer) | 130 | 190 | 250 | **ÜRETİCİ VERİSİ** — SIYI MK15, `H9_MK15/TASARIM.md:18` |
| 5 | RTSP çekme + oynatma tamponu | 40 | 100 | 200 | `nobuffer`+`low_delay` ile 40; varsayılan tamponla 200 |
| 6 | YKS Qt çizim + monitör | 26 | 26 | 26 | 1 kare (16,7) + panel (≈10) |
| | **TOPLAM** | **328** | **482** | **675** | |

## 3. Hüküm
**Kabul eşiği: ≤ 1000 ms** (`results/fdr_sprint_20260910/H9_MK15/TASARIM.md:73`).
En kötü hâlde **675 ms** → **%32,5 pay**. Üç senaryoda da eşik sağlanıyor.
**En büyük tek kalem hattın kendisi değil (4), oynatma tamponudur (5)** — bu yazılımla kontrol edilebilir:
RTSP açılışında `nobuffer` / `low_delay` bayrakları ve UDP taşıyıcı zorunlu kılınır.
Bu, tasarım kararıdır ve `comms/yks_gui.py` video yolunda uygulanır.

⚠ **Bu tablo ÖLÇÜM DEĞİLDİR.** 4. satır üretici verisi, kalanı kare-süresi hesabıdır.
Gerçek sayı §4 ile ölçülür.

## 4. Ölçüm yordamı (donanım gelince, 30 dk)
1. PC'de **Saat → Kronometre** tam ekran; YKS video paneli onun **yanında**.
2. Jetson kamerası bu ekrana bakar → kronometrenin canlısı ve videodaki kopyası aynı karede.
3. Telefonla **60 fps** PC ekranı çekilir (≥10 s).
4. Videoda **5 farklı karede** iki kronometre okunur; fark = gecikme.
5. `A11_gecikme.txt`: 5 satır + p50 + **maks**. Hüküm **maksimum** üzerinden verilir (ön kayıt).

# TAM PROVA SENARYOSU — fırlatma → … → HB TEMAS (P8 · D-392)

> **Amaç:** şartname görev zincirinin 8 fazını TEK koşuda, hakem_log
> damgalarıyla kanıtlamak. Faz C saha provalarının şablonudur; her prova bu
> senaryonun bir koşusudur ve çıktısı UHDR video/log kanıtına girer (§5.5).
>
> ⚠ **Bu senaryo Gazebo ister.** Ana geliştirme PC'sinde gz/WSL YOK
> (2026-09-02'de ölçüldü) — Podman'lı makinede koşulur (`KULLANIM.md §0`;
> Gazebo temelini kuran: trs-1342). `OLCULEMEDI != GECTI`: bu dosyanın
> varlığı kanıt değildir, koşulmuş hali kanıttır.

## 0. Ön koşullar

- Podman + `simulation/` (KULLANIM.md §0-1); repo HEAD güncel (`git pull`).
- Bu HEAD şunları içermeli (prova bunların üstünde anlamlı):
  D-389 (iniş kanıtı bekler), D-390 (İKA sürücü katmanı fail-closed),
  D-391 (varış = FINAL_WP_RADIUS < ped yarı-kenarı).

## 1. Zincirin 8 fazı ve kanıt damgaları

| # | faz | kanıt (hakem_log / çıktı) |
|---|---|---|
| 1 | Fırlatma + otonom geçiş | `iha_flight` başladı; rampa→kalkış damgası |
| 2 | Tarama (≥30 m FDA / görev irtifası) | seyir z=20 damgaları (sim ölçeği) |
| 3 | Açık güzergâh tespiti | MODEL çıktısı: yol + güven (künye kayıt defterinden) |
| 4 | YKS'ye canlı aktarım + hakem onayı | OPEN_ROUTE + ACK(yks); onay İKİ AŞAMALI (yks_gui — `yks_monitor` EMEKLİ, D-392) |
| 5 | İKA'ya aktarım (İHA HAVADAYKEN) | ACK(ika) damgası, iniş damgasından ÖNCE (P9c göstergesi) |
| 6 | İniş + iniş kanıtı | `iha_flight` iniş damgası; IHA_LANDED ACK'li |
| 7 | IKA_GO + otonom intikal | `ika_nav` izin damgası; sürüş süresi ≤ 600 s |
| 8 | **HB'ye TEMAS** | son pozisyon ped merkezine < `FINAL_WP_RADIUS` (0,3 m) → gövde pedin üstünde (D-391) |

## 2. Koşum (Podman'lı makinede)

```bash
cd simulation
./docker/record.sh                  # dünya + kayıt (recordings/v<id>/)
# konteyner içinde ya da ikinci uçbirimde:
python3 scripts/navitas_sim.py kolay        # tam zincir (İHA + İKA + comms)
python3 scripts/hakem_log.py --all \
    --detections recordings/v<id>/detections.json \
    --out recordings/v<id>/hakem_log.txt
```

## 3. GEÇTİ ölçütü (koşumdan önce bağlayıcı)

1. `navitas_sim` çıkış kodu 0; İKA yalnız doğrulanmış rota + IHA_LANDED +
   IKA_GO üçlüsünden sonra hareket etti (aksi zaten exit≠0).
2. `hakem_log.txt` içinde 8 fazın damgası da var; faz 5 damgası faz 6'dan
   önce (aktarım-havada).
3. İKA son konumu ped merkezine < 0,3 m (navigate çıktısındaki son `dist`).
4. Koşum videosu `recordings/v<id>/navitas.mp4` saklanır (UHDR kanıtı).

Sonuç, `results/prova/` altına tarih damgalı klasörle taşınır ve
`REVIEW_LOG.md`'ye koşum kaydı düşülür.

## 4. Bilinen sınırlar

- Sim kanıtı saha kanıtı DEĞİLDİR (CONTRACTS 11.1) — bu şablon zincir
  bütünlüğünü ve regresyonu yakalar; gerçek donanım kanıtı Faz B/C provaları.
- `zor`/`orta` senaryoları da en az birer kez koşulmalı (Kzorluk 1.0/1.5/2.0
  üç güzergâh konfigürasyonuna karşılık gelir; hangi yol açık önceden
  bilinmez — §2.1).

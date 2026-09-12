# akis_kapsam.txt — okuma notu (T248)

`results/fdr_sprint_20260910/H9_MK15/t226/akis_kapsam_t226d.py --taban 776f0254~1`
**EXIT=1** döner ve iki satır yazar:

```
HATA d59  [YENI]: tabanda yok -> comms/yks_gui.py:1973
HATA d59b [YENI]: tabanda yok -> comms/yks_gui.py:1981
```

Bu **beklenen** sonuçtur ve bir gerileme değildir: `YENI`, "yeni mmd'de olup
tabanda olmayan düğüm" demektir. T248 düzeltmesi ürüne **gerçek bir dal**
ekledi (`elif rota_yok_temizlendi:` → `self._harita_ciz()`), diyagram da bu
dalı göstermek zorunda — göstermeseydi FDR şekli ürünü YANLIŞ anlatırdı.

Doğrulayan kapı `scripts/akis_diyagram_dogrula.py`dir ve **TEMİZDİR**:
`FDR/sekiller/akis_d.mmd: 100 düğüm · 100 tuttu · tam satır 100 · hata 0`
(iki yeni düğüm dâhil; `SONUÇ: TÜM DÜĞÜMLER TUTTU`).

Ayrıca `--taban` tazelemesinin **bir yanlış eşlemesi elle düzeltildi**:
`akis_satir_tazele.py` d47'yi (`if yeni:`) 1915'te bıraktı, oysa T248'in
eklediği yorum bloğu yüzünden deyim 1920'ye kaydı; `akis_diyagram_dogrula`
bunu `DEYIM_YOK` ile yakaladı ve atıf 1920 yapıldı. Tazeleme çıktısı:
`akis_satir_tazele.txt` (75 düğüm tazelendi).

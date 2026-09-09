# H1 · T212 SIM-1 kanıtları (MuJoCo arena + araçlar + İHA uçuşu + tarama)

Üreteç: `simulation/mujoco/` (arena_mjcf, araclar, iha_ucus, on_olcum_k3, kanit_ozeti).
Tümü ölçümden yazılır; elle düzenlenmez. Koşum komutları:

```
venv python simulation/mujoco/iha_ucus.py --hepsi --res 1280
venv python simulation/mujoco/arena_mjcf.py --hepsi --kanit-kok results/fdr_sprint_20260910/H1
venv python simulation/mujoco/on_olcum_k3.py --haritalar 1:kolay,1:orta,1:zor
venv python simulation/mujoco/on_olcum_k3.py --haritalar <15 harita> --cikti .../on_olcum_K3_15harita.json
venv python simulation/mujoco/on_olcum_k3.py --haritalar 1:kolay,1:orta,1:zor --kok .../varyant_asfalt --yol-dokusu asfalt --cikti .../on_olcum_K3_asfalt_varyant.json
venv python simulation/mujoco/kanit_ozeti.py
```

| dosya | ne |
|---|---|
| `ozet_T212.json` | K1 / K2 ön-ölçüm / K3 ön-ölçüm özeti (kanit_ozeti.py) |
| `arena_ozeti_15.json`, `harita_<h>_<lv>/arena_<h>_<lv>.json` | MJCF sha256, geom sayıları, yönerge kontrolü, üretim/yükleme süresi |
| `tarama_ozeti_15.json`, `harita_*/iha_scan/tarama_ozeti.json` | kare sayısı, kabul edilen kare, HTAB kapsaması, render ms/kare |
| `harita_*/onizleme_*.jpg` | üçüncü şahıs (başlangıç, tarama, iniş) + nadir genel |
| `harita_*/iha_scan/poses.csv`, `meta.txt` | `navitas_scan_cam.cc` sözleşmesi (n,t,x,y,z,yaw) + host meta |
| `harita_*/iha_scan/kareler/scan_%05d.jpg` | **git dışı** (142 MB; `iha_ucus.py --hepsi` ile bayt-eş yeniden üretilir) |
| `harita_*/iha_scan/ortomozaik.jpg`, `algi.jpg`, `detection.json` | `iha_haritala.haritala` çıktısı (v36, OBB kapalı) |
| `on_olcum_K3.json` | K3 ön-ölçümü (3 harita) — **sonuç ne çıktıysa o** |
| `on_olcum_K3_15harita.json` | aynı zincir 15 haritada |
| `on_olcum_K3_asfalt_varyant.json`, `varyant_asfalt/` | TEŞHİS: yol dokusu asfalt (asıl ölçüm değil) |

SINIRLAR: İHA uçuşu kinematik (mocap); aerodinamik yok. Modeller basitleştirilmiş (D-438 ek).
OBB araç maskesi sim'de kapalı. Hakem onayı/İKA sürüşü bu görevde yok (H1.4–H1.5).


## MUHUR ATLATMA — scripts/surum_dondur.py + tests/test_faz_b_surum_dondurma.py (sartname §6.1). Yontem: gercek depo SALT OKUNUR; ayni commit'in (07a9b8d) iki seyrek klonu scratchpad'de (klon_crlf: core.autocrlf=true, klon_lf: core.autocrlf=false = Linux/Jetson benzetimi) + models/navitas_seg_v36_best.pt kopyasi; gercek --dondur/--dogrula/unittest kosumlari; git'siz ucuncu kopyada 3 mutasyon. Sürücü: scratchpad\repro_muhur.py, ham cikti: scratchpad\repro_muhur_cikti.txt.

### [KRITIK] S6 · Ozet CALISMA AGACI baytina bagli (CRLF): kunye ayni commit'in baska checkout'unda tutmuyor — Jetson/Linux'ta 18/19, baska Windows klonunda 2/19 FARKLI; Jetson'da dogrulama ne planli ne mumkun
REPRO: Sistem: `git config --show-origin core.autocrlf` -> C:/Program Files/Git/etc/gitconfig true; `.gitattributes` YOK; `git ls-files --eol jetson_paket/kod/*.py config/model_registry.json` -> 14/17 paket dosyasi + defter `i/lf w/crlf`, arac_maskesi.py / karisim_arena.yaml / jetson_baslat.sh `w/lf`. codes/model_registry.py:50 `_sha256` ham bayt okur (normalize yok). Repro: scratchpad\repro_muhur.py adim 1,7,8,9 — klon_crlf'te --dondur, kunyeyi klon_lf'e (autocrlf=false, AYNI commit) kopyala, --dogrula; ayni kunyeyle gercek O:\navitas uzerinde salt-okunur sd.farklari_bul. Ayrica: `grep -rn surum_dondur --include=*.md` -> JETSON_KILAVUZ/JETSON_BASLAT/SAHA_RUNBOOK'ta HIC yok; KOPYALAR'da surum_dondur.py ve bagimliligi scripts/jetson_paket_hazirla.py YOK (satir 60 import).
HAM: klon_lf (autocrlf=false, HEAD 07a9b8d, status ''): --dogrula -> exit 1
[DONDURMA] MUHUR IHLALI: 18/19 dosya kunyeden sapiyor:
  FARKLI defter config/model_registry.json
  FARKLI paket  jetson_paket/config/model_registry.json
  FARKLI paket  jetson_paket/kod/arac_maskesi.py ... (17 paket dosyasinin 17'si) ... seri_hub.py
FARKLI sayisi: 18 / 19  (tek AYNI: models/navitas_seg_v36_best.pt — ikili)

Gercek depo O:\navitas (AYNI commit 07a9b8d, Windows) — klon_crlf kunyesiyle farklari_bul:
  FARKLI paket jetson_paket/kod/arac_maskesi.py  kunye=1be7045d9c60 disk=0915d77ae3ee (w/lf)
  FARKLI paket jetson_paket/kod/karisim_arena.yaml kunye=b069b7a797aa disk=b6623b4386c5 (w/lf)
fark sayisi: 2 -> ayni commit, iki Windows checkout'u, kunye UYUSMUYOR

Blob kiyasi (gercek depo): jetson_paket/kod/rpi_inference.py disk CR=2627 sha=77414cfa.. | git blob CR=0 sha=b4da9d86.. | disk==CRLF(blob): True -> kunyedeki ozet git'teki icerigin ozeti DEGIL.
Oneri olcumu (adim 9): CRLF->LF normalize sha klonlar arasi esit: 17/17 paket + defter True.
Kunyedeki test_komutu: 'O:\navitas-local-train\venv\Scripts\python.exe scripts/surum...' (Windows mutlak yol).
ONERI: Ciddiyet gerekcesi: muhrun tek amaci §6.1 kaniti; bu haliyle (a) yarisan cihazda (Jetson) hic dogrulanamiyor, (b) git_head'den YENIDEN URETILEMIYOR (baska makine/klon 2-18 dosyada 'ihlal' der) — kanit tek makineye bagli, saha gunu yanlis 'MUHUR IHLALI' alarmi olasi. Duzeltme: (1) Ozeti icerik-kanonik yap: izlenen metin dosyalari icin `git hash-object`/`git ls-files -s` blob id'si ya da CRLF->LF normalize sha256 (olculdu: 17/17 esit), ikililer (.pt/.onnx/.engine) ham sha256; kunyeye `ozet_yontemi` alani. (2) Depoya `.gitattributes` (`* text=auto eol=lf`, `*.pt/*.onnx/*.engine binary`) — jetson_baslat.sh'in CR korumasi zaten bu derdi kabul ediyor. (3) Jetson'da kosacak bagimsiz bir `--dogrula` yolu: surum_dondur.py + kunyeyi KOPYALAR'a al ve jetson_paket_hazirla importunu kaldir (PAKET_ESLEMESI'yi kunyeden oku); JETSON_BASLAT'a 'kalkistan once --dogrula' adimi. (4) test_komutu'nda sys.executable yerine `python3`/goreli.

### [ONEMLI] S4 · Jetson'a GIDEN model kopyalari (jetson_paket/models/*.pt, *.onnx — gitignore'lu, kilavuz `cp models/* ~/navitas/models/`) kunye DISI: sahte .pt/.onnx ile --dondur 0 ve --dogrula BIREBIR
REPRO: scratchpad\repro_muhur.py adim 5 + ek kosum: klon_crlf'te kunye commit'li; `printf 'SAHTE AGIRLIK' > jetson_paket/models/navitas_seg_v36_best.pt`, ayni sekilde navitas_seg_v36_best_512_fp16.onnx; `git status --porcelain`; `surum_dondur.py --dondur --etiket ikinci --tarih 2026-09-03`; `--dogrula`. Kaynak: .gitignore:134 `jetson_paket/models/*.pt`, :141 `jetson_paket/models/*.onnx`; kunye yalniz `models/navitas_seg_v36_best.pt` (kanonik) ozetler; JETSON_KILAVUZ.md:362 `cp models/* ~/navitas/models/`; jetson_derleme_manifest.json `jetson_komutlari: yolo export model=navitas_seg_v36_best_512_fp16.onnx format=engine`.
HAM: git status --porcelain: []   (sahte .pt/.onnx gorunmez — ignore'lu)
--dondur -> exit=0  [DONDURMA] DONDURULDU: etiket=ikinci ... model=models/navitas_seg_v36_best.pt (1d1caca6f6da...) paket=17 dosya
--dogrula -> exit 0  [DONDURMA] BIREBIR: 19 dosya kunyeyle ayni (model + defter + 17 paket)
check-ignore: .gitignore:134:jetson_paket/models/*.pt  /  .gitignore:141:jetson_paket/models/*.onnx
Not: tam suit tests/test_uretim_modeli_hizasi.py:121 (paket .pt sha == depo .pt) ve :141 (paket ONNX depodaki ONNX kumesinde) bunu YAKALAR — ama kunyenin kendi `test_komutu` yalniz --dogrula + test_faz_b_surum_dondurma kosar; --dogrula'nin 'BIREBIR' hukmu sahaya giden agirlik icin bos.
ONERI: Kunyeye `paket_modelleri` kategorisi: defterin etkin profilinden `jetson_paket/models/<path.name>` (.pt) ve `turevler` anahtarlarindaki .onnx adlari (jetson_paket/models altinda) ham sha256 ile; --dondur'da bunlarin kanonik `models/` kopyasiyla bayt-es olmasini RED kosulu yap (paket_ozetleri kalibi). Ek olarak kunyenin test_komutu'na tests/test_uretim_modeli_hizasi.py ve tests/test_jetson_comms_paketi.py eklensin.

### [ONEMLI] Dondurma SIRASI tanimsiz: Jetson'da .engine derlenip `--turev-kaydet` ile deftere yazilinca defter + ayna degisir -> muhur ihlali 2/19; defter bugun `DERLENINCE_YAZILIR` (engine kayitsiz), muhur ondan once basilirsa engine fail-closed yuklenmez
REPRO: klon_crlf: kunye commit'li; `printf 'SAHTE ENGINE' > models/navitas_seg_v36_best_512_fp16.engine`; `python codes/model_registry.py --turev-kaydet models/navitas_seg_v36_best_512_fp16.engine --kaynak-pt models/navitas_seg_v36_best.pt`; `git status --porcelain`; `scripts/surum_dondur.py --dogrula`. Kaynak: config/model_registry.json turevler[*.engine].sha256 = "DERLENINCE_YAZILIR"; codes/model_registry.py:176 turev_kaydet defteri + aynayi yazar; JETSON_KILAVUZ.md:498 derleme sonrasi --turev-kaydet; codes/rpi_inference.py:648 _turev_kayit_dogrula yer tutucu -> RED.
HAM: turev-kaydet exit=0
git status --porcelain:
 M config/model_registry.json
 M jetson_paket/config/model_registry.json
?? models/navitas_seg_v36_best_512_fp16.engine
--dogrula -> exit=1
[DONDURMA] MUHUR IHLALI: 2/19 dosya kunyeden sapiyor:
  FARKLI defter config/model_registry.json
  FARKLI paket  jetson_paket/config/model_registry.json
Ayrica: `.engine` .gitignore'da YOK -> Jetson agacinda engine varken --dondur 'KIRLI' ile RED (adim 5: `?? jetson_paket/models/navitas_seg_v36_best.engine` -> exit 2).
ONERI: FAZ_B_GUN_PLANI / JETSON_KILAVUZ'a sira kurali: (1) Jetson'da engine derle + --turev-kaydet, (2) defteri PC'ye geri tasi (ayna dahil) ve commit et, (3) ANCAK SONRA --dondur. surum_dondur --dondur'a RED kosulu: etkin profilin `turevler` icinde `backend: tensorrt` girdisi yer tutucuysa 'engine kayitsiz — muhur erken' (fail-closed; `--engine-kayitsiz-bilerek` ile asilir ve kunyeye yazilir). `.gitignore`'a `*.engine` eklenmesi de dusunulmeli (kunye engine sha'sini defter uzerinden zaten tasir).

### [ONEMLI] S3 · Kunye git'e BAGLI DEGIL: ayna degisip kunyedeki sha elle guncellenince --dogrula BIREBIR (exit 0); kunye HEAD'deki haliyle kiyaslanmiyor, --dondur sonrasi untracked; 'agac KIRLI' yalniz bilgi
REPRO: scratchpad\repro_muhur.py adim 4: klon_crlf'te --dondur sonrasi `jetson_paket/kod/rpi_inference.py`'ye satir ekle; kunye['paket'][...rpi_inference.py] = yeni sha256 yaz; `surum_dondur.py --dogrula`; `git status --porcelain`; `git ls-files config/DONDURMA_KUNYESI.json`. Kod: scripts/surum_dondur.py:276-321 farklari_bul/dogrula — kunye icerigi hicbir dis referansla (HEAD blob'u, imza) kiyaslanmaz; :304-309 git bilgisi yalniz print.
HAM: --dogrula -> exit 0
[DONDURMA] kunye: etiket=curutucu-deneme tarih=2026-09-02 git_head=07a9b8d6e300 kirli=False
[DONDURMA] git HEAD simdi=07a9b8d6e300 -> AYNI; agac KIRLI
[DONDURMA] BIREBIR: 19 dosya kunyeyle ayni (model + defter + 17 paket)
git status --porcelain:
 M jetson_paket/kod/rpi_inference.py
?? config/DONDURMA_KUNYESI.json
kunye izleniyor mu (git ls-files): ''  check-ignore: ''   (izlenmiyor, ignore da degil)
ONERI: --dogrula'ya fail-closed iki kosul: (1) kunye izlenmeli ve `git show HEAD:config/DONDURMA_KUNYESI.json` ile bayt-es olmali (degilse 'KUNYE DEGISTIRILMIS' exit 1; untracked ise 'KUNYE COMMIT EDILMEMIS' exit 1 — dondurma yordami 'commit et' adimini zorlar); (2) kunyedeki paket/defter yollari icin `git status --porcelain -- <yollar>` bos olmali, degilse exit 1 (bugun yalniz bilgi). Testler: 'kunye sha elle guncellendi -> 1', 'kunye untracked -> 1'.

### [ONEMLI] S2 · --dogrula yalniz AYNAYI (jetson_paket/kod) kiyaslar; kaynak codes/ comms/ muhur sonrasi degisince BIREBIR exit 0 — kunyenin test_komutu bunu yakalayan test_jetson_comms_paketi'ni KOSMAZ
REPRO: scratchpad\repro_muhur.py adim 3: klon_crlf'te --dondur sonrasi `codes/rpi_inference.py`'ye satir ekle (ayna dokunulmadi); `surum_dondur.py --dogrula`; `git status --porcelain`. Kod: surum_dondur.py:227-241 kunye yalniz hedef (ayna) ozetlerini tasir; :278-280 beklenenler model+defter+paket(hedef) — kaynak yollari PAKET_ESLEMESI'de var ama kunyeye yazilmaz. Kilit baska yerde: tests/test_jetson_comms_paketi.py:56-58 kaynak.read_bytes()==hedef.read_bytes() (tam suitte).
HAM: --dogrula -> exit 0  (git status: 'M codes/rpi_inference.py\n?? config/DONDURMA_KUNYESI.json')
[DONDURMA] git HEAD simdi=07a9b8d6e300 -> AYNI; agac KIRLI
[DONDURMA] BIREBIR: 19 dosya kunyeyle ayni (model + defter + 17 paket)
Gercek depoda bugun ayna==kaynak: 17/17 AYNI (cmp). Kunye test_komutu: '... --dogrula && ... -m unittest discover -s tests -p test_faz_b_surum_dondurma.py' (yalniz bu dosya).
ONERI: Kunyeye kaynak yollarini da yaz (`paket_kaynak: {kaynak_g: sha}` — PAKET_ESLEMESI zaten ikisini tasir) ve farklari_bul ikisini de kiyaslasin; ya da en az test_komutu'na tests/test_jetson_comms_paketi.py eklensin. Kapi mantigi: 'sahaya giden ayna' + 'PC'de test edilen kaynak' ikisi de muhurlu olmali; biri sapinca ad soylenmeli.

### [ONEMLI] S1 · Kunye DISI ama Jetson davranisini belirleyen dosyalar: jetson_baslat.sh (SYSID pini), systemd/*.service (ExecStart uclari), kod/requirements_rpi.txt (surum pini YOK), kalibrasyon/kalibrasyon.yaml — dordu de degistirilmisken --dogrula BIREBIR; YKS/IKA belgeli kapsam disi
REPRO: scratchpad\repro_muhur.py adim 6: klon_crlf'te `SYSID="${SYSID:-1}"`->`:-2` (jetson_baslat.sh:52), navitas-iha-komut-alici.service ExecStart `--mavlink udp:127.0.0.1:14552`->`--mavlink /dev/ttyACM0` (CONTRACTS 7.4 ihlali), requirements_rpi.txt'e `ultralytics==0.0.1`, kalibrasyon.yaml'a satir; `surum_dondur.py --dogrula`. Kapsam kaniti: scripts/jetson_paket_hazirla.py KOPYALAR 17 girdi — bu dosyalar yok; `cat jetson_paket/kod/requirements_rpi.txt` -> ultralytics/opencv-python/numpy/pyserial/pymavlink (hicbirinde surum yok). YKS/IKA: comms/yks_gui.py:346-351 IKA_GO/PARACHUTE tekrar gonderimi, simulation/scripts/ika_nav.py:145,268 OPEN_ROUTE tuketimi + IKA_GO/IHA_LANDED kilidi; comms/komut_tekrar.py yks_gui'den import; surum_dondur.py:34-37 docstring kapsam disi ilan eder; REVIEW_LOG.md:27942 'kapsam karari mimarindir, verilmedi' ACIK.
HAM: git status --porcelain:
 M jetson_paket/jetson_baslat.sh
 M jetson_paket/kalibrasyon/kalibrasyon.yaml
 M jetson_paket/kod/requirements_rpi.txt
 M jetson_paket/systemd/navitas-iha-komut-alici.service
?? config/DONDURMA_KUNYESI.json
--dogrula -> exit 0 | [DONDURMA] BIREBIR: 19 dosya kunyeyle ayni (model + defter + 17 paket)
Hukum (dosya basina 'sahada davranisi degistirir mi'): jetson_baslat.sh EVET (SYSID/KIP/portlar/KANIT_TIMEOUT -> /etc/navitas.env); systemd/*.service EVET (ExecStart argumanlari = sureclerin fiili komut satiri); requirements_rpi.txt EVET (pinsiz ultralytics -> Jetson'da kurulan surum belirsiz, cikarim davranisi degisebilir); kalibrasyon.yaml KOSULLU (yalniz INT8/Q8 engine derlenirse); codes/karar_sozlesmesi.py HAYIR-sorun (KOPYALAR'da, kunye ICINDE); comms/yks_gui.py + komut_tekrar.py EVET (PARACHUTE/ARM/IKA_GO komutlari YKS'den cikar); simulation/scripts/ika_nav.py EVET (rota tuketimi, surus izni); dataset/karisim_arena.yaml kunye ICINDE (kod/karisim_arena.yaml). Not: tests/test_faz_b_jetson_baslat.py .service/baslat'i CONTRACTS 7.4 ile kilitler (sozlesme kilidi, dondurma DEGIL).
ONERI: surum_dondur.py'ye ikinci liste `DONDURMA_EK_KAPSAM` (koke goreli): jetson_paket/jetson_baslat.sh, jetson_paket/systemd/*.service, jetson_paket/kod/requirements_rpi.txt, jetson_paket/kalibrasyon/kalibrasyon.yaml + dogruluk_kapisi_kareleri.json; kunyede ayri `saha_yapilandirma` kategorisi. YKS/IKA icin mimar karari gerekiyor — oneri: `yks_ika` kategorisi (comms/yks_gui.py, comms/komut_tekrar.py, simulation/scripts/ika_nav.py) cunku §6.1 'yarisan yazilim' yalniz Jetson degil. requirements_rpi.txt'e Jetson'da olculen surumler pinlenmeli (`pip freeze` ciktisi 30 Agustos kosumundan). KUNYE_ZORUNLU_ALANLAR'a yeni kategoriler eklensin ki eski kunye yeni betikle sessiz gecmesin.

### [KUCUK] Test boslugu (vacuity): 3/3 mutasyon 21 testi dusurmuyor — degismis IZLENEN dosya kirli sayilmayinca, zorunlu alan denetimi kalkinca, paketin son dosyasi hic kiyaslanmayinca suit yesil
REPRO: scratchpad\klon_mut (git'siz kopya; codes/comms/scripts/tests/config/jetson_paket/kod): scripts/surum_dondur.py'de sirasiyla (M-B) `if s.strip()` -> `if s.strip() and s.startswith("??")` (:117), (M-C) `eksik = [a for a in KUNYE_ZORUNLU_ALANLAR if a not in veri]` -> `eksik = []` (:190), (M-D) `sorted(kunye["paket"].items())` -> `[:-1]` (:280); her biri icin `python tests/test_faz_b_surum_dondurma.py`.
HAM: == taban (mutasyonsuz) == (0, ['Ran 21 tests in 8.975s', 'OK'])
== M-B git_bilgisi: yalniz '??' kirli sayilir, DEGISMIS IZLENEN dosya kirli sayilmaz == unittest exit 0 -> HAYATTA KALDI: ['Ran 21 tests in 8.491s', 'OK']
== M-C kunye_oku: zorunlu alan denetimi kaldirildi == unittest exit 0 -> HAYATTA KALDI: ['Ran 21 tests in 8.299s', 'OK']
== M-D farklari_bul: paketin SON dosyasi (sorted -> seri_hub.py) hic karsilastirilmaz == unittest exit 0 -> HAYATTA KALDI: ['Ran 21 tests in 8.376s', 'OK']
Sebep: test_DONDUR_kirli_agac yalniz YENI (untracked) dosya kullanir; bozuk-kunye testi yalniz JSON hatasi ('{bozuk'); dogrula testleri yalniz rpi_inference.py/protocol.py'yi bozar.
ONERI: Uc test: (1) izlenen dosyayi commit etmeden degistir -> --dondur 2 ve 'M ' satiri ciktida; (2) gecerli JSON ama `paket`/`model` alani eksik kunye -> --dogrula 1 'eksik alanli'; (3) kunyedeki HER paket dosyasi icin dongude tek tek boz -> --dogrula 1 ve o dosyanin adi listede (subTest).

CURUTULEMEDI:
- S5 (kunye VARKEN gercek kok testi): CURUTULEMEDI — klon_crlf'te --dondur sonrasi 21/21 OK; ayna jetson_paket/kod/rpi_inference.py degistirilince `python tests/test_faz_b_surum_dondurma.py` exit 1, `FAIL: test_KUNYE_VARSA_PAKET_MODEL_DEFTER_KUNYEYLE_BIREBIR`, mesajda 'MUHUR IHLALI'; --dogrula exit 1 '1/19 dosya kunyeden sapiyor: FARKLI paket jetson_paket/kod/rpi_inference.py'. Test --kok vermeden BETIK'i kosuyor (KOK=parents[1]) -> gercek depoda ayni davranir.
- Kirli agac reddi: CURUTULEMEDI — untracked dosya (kunyenin kendisi dahil) ve untracked .engine ile --dondur exit 2 'calisma agaci KIRLI'; --kirli-bilerek kirliligi kunyeye yaziyor (test_DONDUR_kirli_bilerek gercek git ile). Yan not: ilk --dondur'dan sonra kunye untracked oldugu icin ikinci --dondur commit'siz REDDEDILIR (tasarim tutarli).
- Bayat ayna reddi: CURUTULEMEDI — paket_ozetleri kaynak sha != hedef sha -> RED (test_DONDUR_paket_kaynaktan_bayatsa_RED gercek dosyalarla); gercek depoda bugun 17/17 kaynak==ayna bayt-es (cmp).
- codes/karar_sozlesmesi.py kapsam sorusu: CURUTULEMEDI — KOPYALAR'da (jetson_paket_hazirla.py:21) ve kunyede (jetson_paket/kod/karar_sozlesmesi.py); dataset/karisim_arena.yaml de icerde.
- Model/defter tutarsizligi: CURUTULEMEDI — disk .pt sha != defter sha -> RED; model yok -> RED; defter alani degisince --dogrula 1 'defter' adiyla (testler gercek hashlib ile). _sha256 tek kaynak (codes/model_registry.py:50), betik kendi ozetini yazmiyor.
- Cikis kodlari: CURUTULEMEDI — 0/1/2/3 ayirt edilebilir; bozuk kunye -> 1 (fail-closed), kunye yok -> 3 ('DONDURULMADI' gorunur not, skip degil); gercek depoda bugun kunye yok -> exit 3 (FAZ_B_GUN_PLANI:23 beklentisiyle ayni).
- Gitignore'lu kanonik model (models/*.pt): CURUTULEMEDI — kirlilik sayilmasa da sha kunyede; degisince --dogrula 1 (test_DOGRULA_model_degisince). Kusur yalniz jetson_paket/models KOPYALARI icin (bulgu 2).
- Oneri olcumu: CRLF->LF normalize sha256 iki klon arasinda 17/17 paket + defter esit — bulgu 1'in duzeltmesi olculebilir sekilde calisiyor.

## PROTOKOL/ACK DOGRULUGU — comms/seri_hub.py + tests/test_faz_b_seri_hub.py (CONTRACTS §7.5, D-403/D-404). Gercek bilesenlerle (SeriHub, SikKoprusu socket:// pyserial uclari, UDPLink, FrameReader/protocol, IhaSender, IhaKomutAlici+_SahteMav, YksArayuz._ack_isle+AckliTekrar) repro; mutasyon kontrolu scratchpad kopyasinda. Repo'ya dokunulmadi. Taban: `O:\navitas-local-train\venv\Scripts\python.exe tests\test_faz_b_seri_hub.py -v` -> Ran 11 tests in 17.463s OK. Betikler: C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\{_hub_kur.py,r_q1_q2.py,r_q3.py,r_q3_proc.py,r_q4_q6.py,r_seq_uzayi.py,r_q5.py,r_cift_bind.py,mut_kos.py}

### [ONEMLI] Hub sureci derin ic ice JSON satirinda RecursionError ile OLUR (FrameReader yalniz ValueError/UnicodeDecodeError yutar; calistir() yalniz KeyboardInterrupt yakalar) — SiK hattinin TEK erisim noktasi cokuyor
REPRO: cd <scratchpad> && O:\navitas-local-train\venv\Scripts\python.exe r_q3.py  (bolum Q3d)  ;  O:\navitas-local-train\venv\Scripts\python.exe r_q3_proc.py  (gercek `comms/seri_hub.py` CLI sureci, socket:// kopru; YKS ucundan b'['*3000+b'\n' yazilir)
HAM: r_q3.py: json.loads('['*3000) -> RecursionError | hub.poll istisna: RecursionError | maximum recursion depth exceeded while decoding a JSON array from a unicode string | traceback: File ...json/decoder.py line 361 raw_decode -> scan_once | hub.calistir() bu istisnayi yakalar mi? -> yalniz KeyboardInterrupt (seri_hub.py:375-381)
r_q3_proc.py: hub sureci yasiyor mu (once): True | ... saglikli cerceve seri_cerceve=1 ... | hub sureci cikis kodu: 1 | stderr: RecursionError: maximum recursion depth exceeded while decoding a JSON array from a unicode string
Karsilastirma (hedef disi, ayni sinif): IhaKomutAlici(link, None).poll() ayni datagramda -> RecursionError. Not: 3000 bayt < FrameReader tavani (64 KiB) ve tek newline ile biter, yani tampon savunmasi devreye girmez. RF gurultusunden cikmasi olasi degil; kasitli/hatali bir kaynak icin yeterli. systemd Restart=always RestartSec=2 sinirlar: ~2-3 s boyunca uc tuketici de sagir/dilsiz (UDP->seri datagramlar ICMP ile sessizce kaybolur, ogrenilen kume sifirlanir), rpi_inference'in 4x0,25 s'lik bir karar penceresi tamamen kaybolabilir; PARACHUTE 40x0,20 s penceresi atlatir.
ONERI: protocol.FrameReader.feed'de `except (ValueError, UnicodeDecodeError, RecursionError)` (tum tuketiciler de kazanir) VE hub'da savunma derinligi: `_cerceveleri_isle` icinde feed/decode'u `except Exception` ile sarip `bozuk += 1` + KIRMIZI log (hub tek erisim noktasi, hicbir cerceve onu oldurmemeli). Kilit testi: YKS ucundan b'['*3000+b'\n' -> hub.poll istisnasiz, bozuk artar, sonraki gecerli cerceve gecer (r_q3.py Q3d'nin devami zaten bunu olcuyor: elle surdurulunce seq=99 gecti).

### [ONEMLI] Hub'in 'portu TEK BASINA acar' garantisi kodda zorlanmiyor: UDP ucu SO_REUSEADDR ile acilir (ikinci hub ayni 127.0.0.1:5100'e sessizce baglanir), SerialLink `exclusive` gecmez (Linux'ta ikinci surec ayni /dev/ttyUSB0'i acar) — cift baslatma sessiz
REPRO: cd <scratchpad> && O:\navitas-local-train\venv\Scripts\python.exe r_cift_bind.py  ;  grep -n exclusive O:\navitas\comms\link.py (bos)  ;  grep -n "exclusive\|flock" O:\navitas-local-train\venv\Lib\site-packages\serial\serialposix.py
HAM: r_cift_bind.py: ikinci bind 127.0.0.1:63251 -> BASARILI (SO_REUSEADDR); b.port=63251 | ilk soket aldi : [b'dg0', b'dg1', b'dg2', b'dg3', b'dg4'] | ikinci soket aldi: []  (ikinci hub UDP'de hicbir sey almaz, hata da vermez — main() exit 3 yolu tetiklenmez)
link.py: `exclusive` gecen satir YOK (SerialLink.__init__: serial_for_url(port, baud, timeout=timeout)). pyserial 3.5 serialposix.py:381-389: `if self._exclusive is not None: if self._exclusive: fcntl.flock(self.fd, LOCK_EX|LOCK_NB)` — varsayilan None -> kilit yok. ⚠ Linux seri yarisi bu makinede OLCULMEDI (Windows COM'u OS zaten tekil acar); kaynak koduna dayanir. Baglam: SAHA_RUNBOOK.md:76 manuel `python3 jetson_paket/kod/seri_hub.py --port /dev/ttyUSB0 --bind 127.0.0.1:5100 ...` komutu + navitas-seri-hub.service Restart=always ayni anda var; operatorun manuel kosumu + systemd birimi = iki hub, iki seri yazar (bayt karisimi), seri okuma ikiye bolunur (her iki FrameReader'da bozuk artar) — hub'in kurulus nedeni olan olgu hub'in kendisinde yeniden. Mercek disi ama olculdu.
ONERI: 1) Hub bind'inde SO_REUSEADDR KULLANMA (UDPLink'e `reuse=False` parametresi ya da hub kendi soketini acsin) -> ikinci hub `UDP ucu acilamadi` ile exit 3. 2) `SerialLink(..., exclusive=True)` (pyserial>=3.3; hub ve seri acan tum surecler) -> ikinci acilis SerialException 'Could not exclusively lock port' -> exit 4. 3) Kilit testi: ayni --bind ile ikinci SeriHub/UDPLink OSError; runbook'taki manuel komutun basina `systemctl stop navitas-seri-hub` notu.

### [KUCUK] Q1 — newline'siz datagram seride SONRAKI cerceveye yapisir, IKI cerceve de YKS'de sessizce kaybolur; hub seri_yazilan=2 bozuk=0 sayar (sessiz basari). Repo ici ureticilerin hepsi encode() kullanir (kosullu)
REPRO: cd <scratchpad> && O:\navitas-local-train\venv\Scripts\python.exe r_q1_q2.py  (bolum Q1)  ;  grep -n "\.send(" comms/iha_sender.py comms/iha_komut_alici.py comms/iha_inis_yayinci.py comms/ika_receiver.py | grep -v "encode(\|data" (bos)
HAM: seride cikan ham: b'{..."seq":11,...}{..."seq":12,...}\n' | YKS FrameReader: [] | hub sayac: {'udp_alinan': 2, 'seri_yazilan': 2} | SONUC Q1: IKI CERCEVE DE KAYIP (sessiz). Uretici taramasi: encode()/data disinda send cagrisi YOK (iha_sender, iha_komut_alici, iha_inis_yayinci, ika_receiver). Mutasyon V4 (hub eksik newline'i ekler) mevcut 11 testi kirmiyor -> duzeltme test-uyumlu.
ONERI: `_udp_turu`: `if not veri.endswith(b'\n'): veri += b'\n'; sayac['newline_eklenen'] += 1` (KIRMIZI log ilkinde) — uyumlu ureticiler icin bayt-es kalir (test_1), sozlesme disi bir uretici cerceveyi komsusuyla birlikte oldurmez; kilit testi: newline'siz datagram + gecerli cerceve -> YKS ikisini de okur, sayac 1.

### [KUCUK] Q4 — IhaSender ACK eslemesi yalniz `ref` (ref_tip/node tipi denetimi yok); hub fan-out ile her tuketici HERKESIN ACK'ini gorur; seq uzaylari surec basina 1'den baslar. Capraz eslesme MEKANIK olarak mumkun, pratik cakisma bulunamadi (tesadufen guvenli)
REPRO: cd <scratchpad> && O:\navitas-local-train\venv\Scripts\python.exe r_q4_q6.py (bolum Q4)  ;  for i in 1 2 3; do O:\navitas-local-train\venv\Scripts\python.exe r_seq_uzayi.py; done
HAM: r_q4_q6.py Q4: seride gorulen (type, seq): [('OPEN_ROUTE', 7), ('IHA_LANDED', 7)] | YKS'nin gonderdigi: ack(7,'yks') [ref_tip yok, yks_gui.py:1077/1108 tarzi], ack(7,'ika','IHA_LANDED') | A(OPEN_ROUTE seq7): acked=['ika','yks'] | B(IHA_LANDED seq7): acked=['ika','yks'] | -> A (OPEN_ROUTE) IHA_LANDED tipli IKA ACK'ini de kabul etti mi: True | kanit iha_sender.py: `if m.get("type") == "ACK" and m.get("ref") == msg["seq"]: acked.add(m.get("node"))`.
r_seq_uzayi.py (3/3 taze surec, KararYayinci.start() ile ayni anda karar): ilk cerceveler [('HEARTBEAT', 1), ('OPEN_ROUTE', 2)] -> rpi_inference'in ACK bekleyen hicbir mesaji seq=1 olamaz; iha_inis_yayinci'nin ACK bekleyen TEK mesaji IHA_LANDED seq=1 (surecin ilk cercevesi), heartbeat'leri ACK'lanmaz -> uretimde ref cakismasi icin yol bulunamadi. Ayrica YKS'nin OPEN_ROUTE/NO_ROUTE/IHA_LANDED ACK'lerinde ref_tip YOK (yks_gui.py:1077,1079,1108,1110) — ref_tip olsa bile IhaSender bakmiyor.
ONERI: Ucuz sertlestirme: IhaSender._tekrarli_gonder'de `ref_tip = m.get('ref_tip'); if ref_tip is not None and ref_tip != msg['type']: continue` (AckliTekrar.ack_geldi ile ayni kural, CONTRACTS §6.6); YKS ACK'lerine `ack(seq, 'yks', m['type'])` ile ref_tip ekle. Kilit testi: r_q4_q6.py Q4 senaryosu -> A acked={'yks'} (IHA_LANDED tipli ika ACK'i reddedilir).

### [KUCUK] Test vacuity — seri->UDP yonunde ACK fan-out'u (YKS ACK -> hub -> ogrenilen rpi_inference/iha_inis_yayinci; 'ogrenilen' kumesinin var olma nedeni) HICBIR testte yok: mutasyon 'ACK tipli cerceveler fan-out edilmez' 11/11 GECIYOR. Yeniden acmada FrameReader sifirlama ve ogrenilen tavani da testsiz
REPRO: cd <scratchpad> && O:\navitas-local-train\venv\Scripts\python.exe mut_kos.py  (scratchpad/mut/ altinda degistirilmis seri_hub kopyalari sys.modules'e konur, GERCEK tests/test_faz_b_seri_hub.py kosulur)
HAM: K1_ogrenilen_fanout_disi ran=11 fail=1 -> YAKALANDI [test_2]
K2_ham_parca_fanout ran=11 fail=1 err=5 -> YAKALANDI [test_5,test_2,test_3,test_6,test_7,test_4]
K3_dict_kontrolu_yok ran=11 fail=1 -> YAKALANDI [test_6]
V1_ACK_fanout_edilmez ran=11 fail=0 err=0 -> GECTI (vacuity)
V2_ensure_ascii_true_yeniden_kodlama ran=11 fail=0 -> GECTI (zararsiz; sadakat iddiasi yalniz ASCII mesajla olculuyor)
V3_yeniden_acmada_okuyucu_sifirlanmaz ran=11 fail=0 -> GECTI (vacuity)
V4_udp_seri_newline_eklenir ran=11 fail=0 -> GECTI (Q1 duzeltmesi uyumlu)
V5_ogrenilen_tavani_yok ran=11 fail=0 -> GECTI (vacuity)
V6_fanout_hedef_sirasi_ters ran=11 fail=0 -> GECTI (zararsiz)
Kontroller (K1-K3) yakalandi -> kosucu gecerli. Gercek yolun calistigi r_q4_q6.py Q4 ile ayrica olculdu (A/B acked={'ika','yks'}); yani kod dogru, kilit yok.
ONERI: Test ekle: (a) YKS seri ucundan ack(N,'yks') -> hub -> gonderdigi icin ogrenilmis GERCEK IhaSender._tekrarli_gonder(wait_ack=True) acked=={'yks'} ve tekrar sayisi 1 (r_q4_q6.py Q4 kalibi); (b) seri ariza + yeniden acma: yarim cerceve eski hatta kalir, yeni hattaki cerceve bozuk sayilmaz; (c) OGRENILEN_TAVANI+1 gonderen -> en eski dusurulur, KIRMIZI log; (d) sadakat testine Turkce karakterli NO_ROUTE(sebep='güven') ekle.

CURUTULEMEDI:
- Q2 (bir datagramda birden cok cerceve) — r_q1_q2.py: UDP->seri tek datagramda iki cerceve: YKS okudu [('CMD',21),('HEARTBEAT',22)] esit=True (hub udp_alinan=1 seri_yazilan=1); seri->UDP tek seri parcasinda iki cerceve: statik tuketiciye 2 datagram, her biri tam 1 newline (seri_cerceve=2 fanout_gonderim=2); iha_komut_alici datagram-basina taze FrameReader iki CMD'yi de isledi (sayac cmd=2). Ters yonde de kayip yok.
- Q3 (encode(decode(x)) sadakati) — r_q3.py: bosluklu JSON / float 0.910->0.91, 1E2->100.0, 5.0 / ü kacisi -> ham UTF-8 / alan sirasi (bayt-es True, Py3.7+ dict sirali) / cift anahtar (son kazanir, tuketici de ayni) / CRLF: hepsinde decode(cikan)==decode(giren) True, encode(decode(cikan))==cikan True. protocol.py'de hmac/crc/checksum/imza YOK (inspect: []) -> bayt farki imza/ref eslemesini bozamaz; ref/seq tamsayilari birebir. NaN/Infinity/1e400: dogrudan decode kabul ederdi (conf=nan/inf), hub `encode(allow_nan=False)` ile bozuk sayip DUSURUYOR (bozuk 0->1->2->3, datagram yok) — hub tuketiciden daha siki, fail-closed. En uzun mesru OPEN_ROUTE (64 wp, -59.99 koordinat, seq=2**31) 1622 bayt < UDPLink.recv 4096.
- Q5 (iki tuketici ayni seq ile gonderirse YKS karisikligi) — r_q5.py, GERCEK YksArayuz._ack_isle (Tk'siz __new__ kalibi) + AckliTekrar, IKA_GO seq=5 ve PARACHUTE seq=9 beklerken rota seq=5: IKA OPEN_ROUTE ACK ref=5 -> ika_go BEKLIYOR, rota kaniti [5] (dogru); IKA IHA_LANDED ACK ref=5 -> hicbiri; IHA CMD ACK ref=5 -> hicbiri (dugum yonlendirmesi); IKA CMD ACK ref=9 -> hicbiri; dogru ACK'ler (ika CMD ref=5 / iha CMD ref=9) yalniz kendi bekleyenini ONAYLANDI yapti. Tek istisna ref_tip'siz IKA ACK ref=5 hem IKA_GO'yu hem rota kanitini tatmin etti — bu CONTRACTS §6.6 geriye-uyum kurali, ika_receiver daima ref_tip gonderir (ika_receiver.py:167,186). YKS tarafinda OPEN_ROUTE (rpi_inference) ve IHA_LANDED (iha_inis_yayinci) ayri alanlarda tutulur (rota / iha_landed_seq), rx_alim ayni surecin seq'leriyle beslenir.
- Q6 (iha_komut_alici ACK'i nereye yollar) — r_q4_q6.py Q6, alici UDPLink(bind=('0.0.0.0',P)) uretimdeki gibi, hub statik ('127.0.0.1',P): alici.isle'nin gordugu adr = ('127.0.0.1', hub_port) == hub_adr True -> ACK datagramin geldigi HUB soketine gider (iha_komut_alici.py `_ack_gonder`: adr None degilse gonderene), hub seriye yazar, YKS seride {'type':'ACK','ref':41,'node':'iha','ref_tip':'CMD'} okudu; hub.ogrenilen [('127.0.0.1',P)] = statik ile ayni -> hedefler tekil (cift datagram yok). Test 5 tam bu mekanizmayla gecer; sahte degil.
- Q1'in 'tuketici encode'u newline koyuyor mu' yarisi — protocol.encode her zaman '\n' ekler (protocol.py:154-157); repo ici tum ureticiler (IhaSender, IhaKomutAlici._ack_gonder, ika_receiver) encode() ile gonderir (grep: encode/data disi send yok). Yapisma yalniz sozlesme disi bir uretici ile mumkundur (bulgu 3'te kosullu olarak kaydedildi).
- Hub'in kendi eslestirme mantigi yok (dogru): hub ACK/CMD icerigine bakmaz, node/hedef suzmez, seq uretmez — protokol kararlari tuketicilerde kalir; bu yuzden hub'in kendisinde ACK yanlis eslemesi uretilemedi. Denenip bulunamayanlar: seri->UDP parca datagram (test_3 + Q2b), fan-out cift gonderim (test_7 + Q6), yeniden kodlamada ref/seq tipi bozulmasi (Q3a: int int kaldi), CRLF/bos satir kilitlenmesi (Q3a CRLF gecti).

## ARIZA / YENIDEN ACMA / KAYNAK — comms/seri_hub.py + tests/test_faz_b_seri_hub.py (CONTRACTS §7.5, D-403/D-404). Yorumlayici O:\navitas-local-train\venv\Scripts\python.exe (pyserial 3.5, Py 3.13.7, Windows). Repro betikleri: C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\hub\ (r1_cpu.py, r2_gecikme.py, r3_yarim_cerceve.py, r4_tavan.py, r5_buyuk.py, r6_kaynak.py, r7_cikis.py, mut_yap.py, mut_kos.py; mutantlar M1..M9 + kontrol K1). Repo dosyalarina dokunulmadi: `cmp comms/seri_hub.py <scratchpad>/seri_hub_orijinal.py` -> BAYT-ES; `git diff --stat -- comms/seri_hub.py tests/test_faz_b_seri_hub.py` bos. Taban: suit 11/11 OK (17,6 s, -X dev ile ResourceWarning yok). Mutasyon kontrolu calisiyor: K1 (1 s yeniden acma araligi kaldirildi) test_4 ile, M7 (SERI_TUR_TAVANI=1) test_7 ile YAKALANDI; asagidaki bulgular bu kontrole gore okunmali.

### [ONEMLI] D-403'un asil dersi (seri okuma zaman asimi 0,3 s) ve hub UDP zaman asimi 0,3 s gerilemeleri test suitinden GECIYOR — hub gecikmesi icin kapi yok (D-404 §7.2 'OLCULMEDI' hala acik; simdi olculdu)
REPRO: PY=O:\navitas-local-train\venv\Scripts\python.exe; S=<scratchpad>\hub;  %PY% %S%\mut_yap.py && %PY% %S%\mut_kos.py %S%\M8_seri_zaman_asimi_300ms.py && %PY% %S%\mut_kos.py %S%\M9_udp_zaman_asimi_300ms.py   (M8: `SERI_OKUMA_ZAMAN_ASIMI_S = 0.3`, M9: `UDP_OKUMA_ZAMAN_ASIMI_S = 0.3`; suit tests/test_faz_b_seri_hub.py mutanta karsi kosulur).  Olcum: %PY% %S%\r2_gecikme.py  (SikKoprusu + gercek SerialLink socket://, hub calistir() ipliginde, 50 PARACHUTE tekrari 0,20 s aralikla, 2 kez kosuldu)
HAM: MUTANT M8_seri_zaman_asimi_300ms.py: ran=11 fail=0 err=0 -> HAYATTA (hicbir test dusmedi)
MUTANT M9_udp_zaman_asimi_300ms.py: ran=11 fail=0 err=0 -> HAYATTA (hicbir test dusmedi)
(kontrol) MUTANT K1_aralik_yok.py: ran=11 fail=1 err=0 -> YAKALANDI ['test_4_seri_okuma_arizasi_hub_cokmez_dusurur_yeniden_acar']
(kontrol) MUTANT M7_seri_tur_tavani_1.py: ran=11 fail=1 err=0 -> YAKALANDI ['test_7_statik_ve_ogrenilen_ayni_adres_TEK_datagram_alir']
REPO hub gecikmesi (kosum 1 / kosum 2):
A UDP->seri (seri girisi bos): n=50 eksik=[] p50=10.56 ms p95=31.04 ms max=32.19 ms  /  p50=9.97 p95=31.19 max=32.15
B UDP->seri (seri girisinde 20 Hz HB): n=50 eksik=[] p50=45.50 ms p95=70.84 ms max=74.16 ms  /  p50=47.06 p95=76.80 max=79.68
C seri->UDP (YKS CMD -> tuketici): n=50 eksik=[] p50=8.94 ms p95=16.24 ms max=16.41 ms  /  p50=7.00 p95=15.17 max=16.17
D hub'siz kopru (taban): n=50 p50=1.14 ms p95=1.33 ms  /  p50=0.51 p95=0.96
hub sayac: udp_alinan=100 seri_yazilan=100 seri_cerceve=249 fanout_gonderim=746 bozuk=0 dusurulen=0
ONERI: Suit bugun hub'in ZAMANLAMA sozlesmesini hic kilitlemiyor; D-403'te 622 ms'lik ACK turu ureten deger geri gelse 11/11 yesil kalir. (1) Sabit kilidi: `SERI_OKUMA_ZAMAN_ASIMI_S <= 0.05`, `UDP_OKUMA_ZAMAN_ASIMI_S <= 0.01`, kurulan hub'da `hub.seri_link.ser.timeout == SERI_OKUMA_ZAMAN_ASIMI_S` ve `hub.udp_link.sock.gettimeout() == UDP_OKUMA_ZAMAN_ASIMI_S` iddiasi (madde 16 ruhu: parasut tekrar araligi 0,20 s'nin altinda kalma gerekcesiyle). (2) test_S8 kalibinda on kayitli gecikme kapisi: hub uzerinden UDP->seri p95 < 100 ms ve seri->UDP p95 < 50 ms (yerel kopru, 20 ornek; r2_gecikme.py dogrudan test kalibina cevrilebilir). M8 mutanti bu kapiyi dusurmelidir (mutasyon kontrolu on kayda yazilsin). Not: Windows'ta 20 ms zaman asimi 15,6 ms zamanlayici tanecigiyle ~31 ms'e yuvarlaniyor (A p95=31 ms bunun olcumu); Jetson/Linux'ta beklenen tavan ~21 ms.

### [KUCUK] Yeniden acmada FrameReader sifirlama davranisi TESTSIZ (M1 hayatta): mutantta arizadan kalan yarim bayt yeni hattin ILK cercevesine yapisiyor, ilk PARACHUTE/ACK cercevesi bozuk sayilip kayboluyor
REPRO: %PY% %S%\r3_yarim_cerceve.py   (repo)   ;   %PY% %S%\r3_yarim_cerceve.py %S%\M1_tampon_sifirlanmaz.py   (mutant: `_seri_bagla` icindeki `self.okuyucu = FrameReader()` satiri kaldirildi)   ;   %PY% %S%\mut_kos.py %S%\M1_tampon_sifirlanmaz.py
HAM: R3 hub=REPO
  yarim tampon (ariza oncesi)      : b'{"v":1,"type":"CMD","cmd":"PARA'
  ariza sonrasi seri_link          : None
  yeniden acma sonrasi seri_link   : yeni
  yeniden acma sonrasi tampon      : b''
  yeni hattaki ILK cerceve tuketiciye: 1 datagram -> [True]
  sayac bozuk=0 seri_cerceve=1 yeniden_acma=1
R3 hub=M1_tampon_sifirlanmaz.py
  yeniden acma sonrasi tampon      : b'{"v":1,"type":"CMD","cmd":"PARA'
  yeni hattaki ILK cerceve tuketiciye: 0 datagram -> []
  sayac bozuk=1 seri_cerceve=0 yeniden_acma=1
MUTANT M1_tampon_sifirlanmaz.py: ran=11 fail=0 err=0 -> HAYATTA (hicbir test dusmedi)
ONERI: Kod bugun dogru (satir 211 sifirliyor; soru 3 curutulemedi) ama davranis kilitsiz. test_4'e ekle: arizadan ONCE YKS ucundan newline'siz yarim cerceve yaz ve birkac tur pompala (`hub.okuyucu._buf` dolu oldugunu dogrula), arizayi enjekte et, yeniden acmadan sonra `hub.okuyucu._buf == b""` ve yeni koprudeki ilk gecerli cercevenin `bozuk == 0` ile fan-out edildigini iddia et. M1 mutanti bu testi dusurmeli.

### [KUCUK] Ogrenilen kume tavani (32) SAYI tabanli: 32 farkli yeni kaynak gelince o an sessiz ama canli tuketici dusuyor ve seriden gelen cerceveleri (ACK) bir daha almiyor; tavan ve tazelik (sona tasima) testsiz (M3/M4 hayatta)
REPRO: %PY% %S%\r4_tavan.py   (S1: A bir kez gonderir, 32 efemer UDPLink birer HB yollar, sonra YKS seriden CMD yazar; S2: A ortada bir HB daha yollar)   ;   %PY% %S%\mut_kos.py %S%\M3_tavan_yok.py ; %PY% %S%\mut_kos.py %S%\M4_tazelik_yok.py
HAM: R4 S1 A sessiz (bir kez gonderdi): A ogrenildi=True | 32 efemer sonra A kumede=False kume=32 | seri cerceve -> statik 1 datagram, A 0 datagram | fanout_gonderim=33
   ilk tavan logu: [SERI_HUB] t=1000.960 KIRMIZI ogrenilen tavani (32) asildi; en eski dusuruldu: 127.0.0.1:65021 (toplam 1)
R4 S2 A ortada bir kez daha gonderdi (HB): A ogrenildi=True | 32 efemer sonra A kumede=True kume=32 | seri cerceve -> statik 1 datagram, A 1 datagram | fanout_gonderim=33
MUTANT M3_tavan_yok.py: ran=11 fail=0 err=0 -> HAYATTA
MUTANT M4_tazelik_yok.py: ran=11 fail=0 err=0 -> HAYATTA
Kosul (kod): codes/karar_sozlesmesi.py:145 `IHA_HEARTBEAT_ARALIK_S = 1.0` (rpi_inference her 1 s HB ile tazelenir, S2 bunu gosterir); iha_komut_alici statik (--tuketici); hub `--bind 127.0.0.1:5100` (yalniz yerel surecler gonderebilir); jetson_baslat.sh:113 sik kipinde `RPI_TELSIZ_ARGS="--yks-hedef 127.0.0.1:5100"`.
ONERI: Belgelenen topolojide tetikleyici yok (1 s HB penceresinde 32 FARKLI yerel kaynak gerekir), o yuzden KUCUK; ama mekanizma kor: dusurme 'en az tazelenen'e gore, tuketicinin sessizligi = olum sayiliyor ve tuketici bunu ogrenmiyor (yalniz hub KIRMIZI loglar). (1) Tavani zaman tabanli yap: son gorulmesi > N s (orn. 60 s) olan girdiyi dusur, sayi tavani yalniz emniyet (256); ya da (2) en azindan uzun omurlu her tuketicinin --tuketici ile STATIK verilmesini CONTRACTS §7.5'te kural yap. Her durumda test: 33. kaynak gelince tazelenen tuketicinin kaldigi (M4'u dusurur) ve tavanin uygulandigi (M3'u dusurur).

### [KUCUK] 4096 B'den buyuk UDP datagram: hub `udp_link.recv()`'i varsayilan bufsize 4096 ile cagiriyor — Windows'ta OSError yakalanmadan sizar, calistir() dongusu cikar (exit 1 -> systemd Restart=always, ~2 s kor pencere); Linux'ta datagram budanip newline'siz seriye yazilir (Linux ayagi OLCULMEDI, WSL yok)
REPRO: %PY% %S%\r5_buyuk.py   (R5a: 4096/4097/65000 B datagram -> hub.poll())   ;   %PY% %S%\r7_cikis.py   (R7b: modul.main([... loop:// ...]) calisirken 5000 B datagram)   ;   en buyuk mesru cerceve: %PY% -c "from protocol import encode, open_route; from iha_sender import MAX_WAYPOINTS; ..."
HAM: R5a — buyuk UDP datagram (hub.udp_link.recv() bufsize=4096 varsayilan)
  4096 B: poll() sessiz; udp_alinan=1 seri_yazilan=1 dusurulen=0
  4097 B: poll() ISTISNA SIZDIRDI -> OSError: [WinError 10040] Bir veri birimi yuvasına gönderilen bir ileti, iç ileti arabelleğinden ... büyüktü ... (calistir() dongusu bunu YAKALAMAZ; hub cikar)
  65000 B: poll() ISTISNA SIZDIRDI -> OSError: [WinError 10040] ...
R7b 5000 B datagram -> main() ISTISNA SIZDIRDI: OSError: [WinError 10040] ...
    kapat() kostu mu: udp fileno=-1 seri_link=None udp_alinan=0   (finally kapat() ve son sayac logu KOSTU; `raise SystemExit(main())` -> cikis 1)
MAX_WAYPOINTS= 64 en buyuk OPEN_ROUTE cerceve= 1407 bayt; hub recv bufsize=4096
R5c (ayni mekanizmanin seri tarafi): 3000 B cop + gecerli cerceve: tuketiciye 0 datagram; bozuk=1 ; ikinci gecerli cerceve: tuketiciye 1 datagram
ONERI: Mesru gonderici asamaz (1407 B < 4096), Jetson Linux'ta cokme yok -> KUCUK. Yine de iki satirlik kapanis: `_udp_turu`'nda `self.udp_link.recv(65535)` (UDPLink.recv zaten bufsize alir) ve recv'i `except OSError` ile sar: `udp_hata` sayaci + KIRMIZI log, hub CIKMASIN (calistir yalniz KeyboardInterrupt yakaliyor). Linux budama sonucu 4096 B'lik newline'siz parca seriye gider ve YKS'de bir SONRAKI gecerli cerceveyi de yer (R5c ayni olgu) — bunu da recv tavaniyla degil, gonderici tarafinda tutmak yeterli; Linux davranisi belgelenmis recv(2) semantigidir, burada olculmedi.

### [KUCUK] SIGTERM isleyicisi yok: systemd `stop`/yeniden baslatmada calistir() finally'si, kapat() ve son `sayac` logu kosmaz (Python varsayilani surec aninda olur); TimeoutStopSec=5 fiilen anlamsiz
REPRO: grep -n "signal\|SIGTERM\|SIGINT" O:\navitas\comms\seri_hub.py   (0 satir, rc=1)   ;   %PY% %S%\r7_cikis.py   (R7a: modul yuklendikten sonra signal.getsignal)
HAM: signal_grep_rc=1 (eslesme yok)
R7a SIGTERM isleyici = 0 ; SIGINT isleyici = default_int_handler
(0 = SIG_DFL; Linux'ta varsayilan eylem: aninda sonlanma, `finally` calismaz)
jetson_paket/systemd/navitas-seri-hub.service: Restart=always / RestartSec=2 / TimeoutStopSec=5
ONERI: Islevsel zarar yok (cekirdek fd'leri kapatir, port serbest kalir; KeyboardInterrupt yolu temiz — test_10 ve R6 S1) ama journal'daki son sayac satiri (dusurulen/bozuk/fanout_hata) her stop'ta kaybolur, saha sonrasi tani zorlasir. `main()`'de hub kurulduktan sonra `signal.signal(signal.SIGTERM, lambda *_: hub.durdur())` — dongu `_dur` ile temiz cikar, finally sayaci basar, cikis 0. Test: SIGTERM isleyicisinin `durdur()`u cagirdigi (Windows'ta isleyiciyi dogrudan cagirarak).

### [KUCUK] Diger hayatta kalan mutantlar (vakum): kapat() UDP soketini kapatmasa (M6), seri kapaliyken bos tur beklemesi kalksa (M2), hub UDP zaman asimini kurmasa (M5) suit fark etmiyor
REPRO: %PY% %S%\mut_kos.py %S%\M6_kapat_udp_kapatmaz.py ; %PY% %S%\mut_kos.py %S%\M2_sicak_dongu.py ; %PY% %S%\mut_kos.py %S%\M5_udp_zaman_asimi_yok.py ; %PY% %S%\r1_cpu.py %S%\M2_sicak_dongu.py
HAM: MUTANT M6_kapat_udp_kapatmaz.py: ran=11 fail=0 err=0 -> HAYATTA (hicbir test dusmedi)
MUTANT M2_sicak_dongu.py: ran=11 fail=0 err=0 -> HAYATTA
MUTANT M5_udp_zaman_asimi_yok.py: ran=11 fail=0 err=0 -> HAYATTA
R1 hub=M2_sicak_dongu.py sure=3.01s cpu=0.000s cpu_orani=0.0% poll_tur=193 tur_hizi=64/s seri_ac_cagri=2   (Windows'ta 1 ms UDP zaman asimi ~15 ms'e yuvarlanip fren oluyor; Linux'ta ~1000 tur/s beklenir, select icinde uyur — CPU riski dusuk ama tasarlanan 20 ms bekleme kilitsiz)
ONERI: test_10'a `hub.udp_link.sock.fileno() == -1` (kapat() UDP'yi de birakti); M5 icin `_HubKurulum` udp'sini bilerek 0,3 s ile kurup hub'in 1 ms'e cektigini iddia et (`sock.gettimeout() == UDP_OKUMA_ZAMAN_ASIMI_S`); M2 icin seri kapali hub'da gercek saatle 0,5 s calistir() ve tur sayisinin ~25±10 oldugunu (sicak dongu degil) iddia et.

CURUTULEMEDI:
- (1) seri_ac surekli exception: CURUTULEMEDI. r1_cpu.py (repo, 3 s, seri_link=None, seri_ac her cagrida SerialException): `cpu=0.016s cpu_orani=0.5% poll_tur=64 tur_hizi=21/s seri_ac_cagri=2 yeniden_acma_hatasi=2 saat_tipi=builtin_function_or_method`; loglar t=+1.03 s ve +2.07 s'de (1 s araligi gercek, `self.saat()`=time.monotonic ile; `_ariza_t` deneme ONCESI kuruluyor, seri_ac'in kendi suresi araliga eklenmiyor). Tur hizi 21/s = Windows 15,6 ms tanecigi (20 ms wait ~31 ms + 1 ms UDP ~15 ms); Linux'ta ~47/s beklenir.
- (2) UDP->seri gecikmesi (0,20 s parasut tekrari): CURUTULEMEDI — r2_gecikme.py iki kosum, 50 ornek/kosul: A (bos seri girisi) p50 10,6/10,0 ms p95 31,0/31,2 ms; B (seri girisinde 20 Hz HB) p50 45,5/47,1 ms p95 70,8/76,8 ms max 79,7 ms; C seri->UDP p50 8,9/7,0 ms p95 16,2/15,2 ms; taban (hub'siz kopru) p50 1,1/0,5 ms. Hepsi 200 ms'in altinda, kayip 0/50. B'deki artis socket:// artefakti agirlikli (in_waiting 0/1 -> 2 bayt/recv, 100 B HB = 50 recv + 5 iplikli GIL); gercek seride in_waiting toplu doner. Windows tanecigi p95'i sisiriyor (20 ms -> 31 ms). Bulgu 1: bu olcumun suitte kapisi yok.
- (3) Yeniden acmada yarim bayt: CURUTULEMEDI (kod). r3_yarim_cerceve.py repo: ariza oncesi tampon b'{"v":1,"type":"CMD","cmd":"PARA', yeniden acma sonrasi b'', yeni hattaki ilk cerceve 1 datagram birebir, bozuk=0. `_seri_bagla` satir 211 her baglamada taze FrameReader kuruyor. Bulgu 2: yalniz testsiz.
- (5b) Seride newline'siz sonsuz akis: CURUTULEMEDI. r5_buyuk.py R5b, 1 MiB \xff: parca=115 B -> 0,13 s, azami tampon 65435 B (tavan 65536), tepe bellek 128 KiB, atilan_bayt=983250; parca=2 B (socket:// artefakti) -> 6,09 s, azami tampon 65536 B, tepe 142 KiB. Hub varsayilan FrameReader(CERCEVE_TAMPON_TAVANI) kullaniyor, tavan geçerli; `atilan_bayt` periyodik logda gorunur. Cop sonrasi ikinci gecerli cerceve gecti (hat toparlaniyor; ilk gecerli cop'a yapisip kaybolmasi newline cerceveleme dogasi, protokolde belgeli).
- (6) durdur()/kapat() soket kapanisi: CURUTULEMEDI. r6_kaynak.py (-X dev): S1 main()+durdur (finally kapat) -> cikis 0, udp fileno=-1, seri_link=None, ResourceWarning 0; S2 okuma arizasi -> `hub_seri.ser.is_open=False`, kapat sonrasi udp fileno=-1, ResourceWarning 0; S3 yalniz durdur() (kapat yok) -> udp fileno=536 acik, 1 ResourceWarning — tasarim geregi (durdur yalniz bayrak; main() finally'de kapat() cagiriyor, test_10 bu yolu kosuyor). Suitin tamami -X dev -W always::ResourceWarning ile 11/11, uyari yok.
- (7) Ctrl-C ile temiz cikis: CURUTULEMEDI — SIGINT isleyicisi default_int_handler -> KeyboardInterrupt calistir()'da yakalaniyor, finally sayac + main() finally kapat() (test_10, R6 S1 cikis 0). Beklenmeyen istisna yolu (R7b): kapat() ve son sayac KOSUYOR, sonra istisna `raise SystemExit(main())` ile cikis 1 -> Restart=always 2 s sonra kaldirir. SIGTERM'e isleyici yok (Bulgu 5, KUCUK).
- (4) 32 tavani: mekanizma repro edildi (Bulgu 3) ama belgelenen topolojide tetikleyici bulunamadi: rpi_inference sik kipinde tek UDPLink() soketiyle 1,0 s HB (karar_sozlesmesi.py:145) -> S2'de tazelik korudu; iha_inis_yayinci IHA_LANDED'i ACK'li tekrarlarla (0,25 s) gonderip HB'ye gecer; iha_komut_alici statik+ogrenilen ayni adres (test_7). Hub 127.0.0.1'e bagli, dis kaynak yok.
- Denendi/degerlendirildi, kanit uretilemedi (donanim/Linux yok): (a) gercek ttyUSB'de `SerialLink.send` write_timeout=None ile bloklama (tek iplik iki yonu baglar) — analitik tavan: tty TX tamponu ~4 KB / 5,76 KB/s ≈ 0,7 s; kararli trafik (1 karar/0,25 s × ≤1,4 KB + HB) hattin altinda, tetiklenmesi beklenmez; (b) USB yeniden numaralandirmada /dev/ttyUSB0 -> ttyUSB1 kaymasi (hub eski fd'yi ilk hatada kapatiyor, `link.close()` satir 231; by-id yolu SAHA_RUNBOOK karari); (c) Linux recvfrom(4096) budamasi. Mercek disi gozlem (bulgu degil): sik kipinde hub topolojisi rpi_inference'i UDP kipine aldigi icin `yayinci_kur` wait_ack=True (iha_sender.py: seri dalinda `kw.setdefault("wait_ack", False)`, UDP dalinda KararYayinci varsayilani True) — her karar YKS ACK'i icin 4×0,25 s bekler/tekrarlar; `--telsiz-seri` kipinde ates-unut idi. 'Tuketici kodu degismez' dogru, davranis degisiyor; mimar karari.

## KURU vs GERCEK AYRISMASI — jetson_baslat.sh kurulum/kapi/dogrudan kipleri Git Bash'te sahte systemctl/sudo/id/python3/mavproxy.py PATH shim'leriyle PROVA edildi (scratchpad/prova.sh); CRLF kopya, ozel karakterli beyan, mutasyon (scratchpad/mut.sh, 7 mutasyon) ve IhaSender bant genisligi olcumu (scratchpad/q6_sender.py) ile desteklendi. Hicbir repo dosyasi degistirilmedi.

### [ONEMLI] Yeniden `--kur` degisen beyani canli surece uygulamaz: `systemctl enable --now` calisan birimi yeniden baslatmaz, betikte `restart` yok — `--kuru` 'systemd AYNEN bunu kosar' derken kosan surec ESKI argumanlarla surer
REPRO: S=scratchpad; $S/prova.sh rerun1 KIP=udp YKS_IP=10.0.0.1 IKA_IP=10.0.0.2 FOV=78 -- --kur; $S/prova.sh rerun2 KIP=udp YKS_IP=10.0.0.9 IKA_IP=10.0.0.2 FOV=90 -- --kur; grep systemctl $S/log/shim_rerun2.log; grep -n restart jetson_paket/jetson_baslat.sh | grep -v 'Restart=\|NRestarts\|yeniden-baslatma'
HAM: 2. kosum systemctl cagrilari:
systemctl daemon-reload
systemctl disable --now navitas-seri-hub.service
systemctl enable --now navitas-cogullayici.service navitas-rpi-inference.service navitas-iha-inis-yayinci.service navitas-iha-komut-alici.service
2. kosumda env: RPI_EK_ARGS=--fov 90 RPI_TELSIZ_ARGS=--yks-hedef 10.0.0.9:5005 --ika-hedef 10.0.0.2:5006
betikte restart gecen satir: (yok)
-> systemd 'start' aktif birimde no-op'tur; /etc/navitas.env yeni degeri tasir ama surecler eski --yks-hedef 10.0.0.1 ile calismaya devam eder. Sahada yanlis YKS_IP'yi duzeltip yeniden kosmak ETKISIZDIR; --durum 'active' der, --kuru yeni komutu gosterir.
ONERI: kur_systemd: `systemctl enable $(birim_listesi)` + `systemctl restart $(birim_listesi)` (daemon-reload zaten var). kapi: cogullayici icin de `restart` (PIXHAWK_SERI/BAUD degismis olabilir). JETSON_BASLAT.md'ye 'beyan degistiyse --durdur sonra --kur' notu YERINE betikte restart; tests'e shim'li kosumda 'restart cagrildi' kilidi.

### [ONEMLI] K8 davranissal CRLF testi Windows'ta BOS (vacuous): MSYS grep CR'i gormuyor, MSYS bash CRLF'i tolere ediyor — koruma dali (mktemp/tr/exec/trap) hicbir testte kosmadi; Jetson'da ILK KEZ kosacak
REPRO: cd scratchpad; grep -q $'\r' paket_crlf/jetson_baslat.sh; echo $?  # 1 = CR gormedi (od -c CR'i gosterir); printf 'set -euo pipefail\r\necho ok\r\n' > m.sh; bash m.sh  # hatasiz; KIP=sik FOV=78 PATH=$PWD/bin_mktemp:$PATH bash paket_crlf/jetson_baslat.sh --kuru 2>&1 >/dev/null  # MKTEMP CAGRILDI satiri YOK; scratchpad/mut.sh M7 ... (koruma satiri silinir)
HAM: od -c: '#!/usr/bin/env bash\r\n' (CR baytlari VAR)
Git Bash grep -q $'\r' dogrudan: grep: CR GORMEDI (exit 1); grep --binary-files=text -c $'\r' -> 0; grep (GNU grep) 3.0 [MSYS]
mini CRLF betik (set -euo pipefail\r): 'CRLF betik kostu' EXIT=0  (bash 5.2.37 MSYS CR'i yutuyor)
mktemp shim ile CRLF --kuru: (bos ise koruma dali HIC kosmadi) -> bos
[M7_CR_koruma_satiri_SILINDI] FAIL: test_K8_cr_korumasi_set_e_den_ONCE_ve_ilk_komut (yalniz METIN kilidi); test_K8_crlf_kopya_ayni_env_ve_birim_ciktisi GECTI -> Ran 24, FAILED (failures=1)
Zorlamali (grep shim CR baytina gore 0 doner): 'MKTEMP CAGRILDI', EXIT=0, --kuru ciktisi LF ile birebir (yalniz paket yolu farkli), tmp kalinti 0, --help calisti -> dal mekanik olarak DOGRU; ama gercek tetikleyici (Linux grep) burada olculemedi (WSL yok).
Alternatif algi Git Bash'te calisiyor: [[ "$(head -c 4096 dosya)" == *$'\r'* ]] -> CRLF: CR GORDU, LF: CR yok.
ONERI: Algiyi bash-ici yap: `case "$(head -c 4096 "$0")" in *$'\r'*) ... esac` (Git Bash'te de tetiklenir -> K8 dali gercekten kosturur). Dalin kostugunu ciktiya bas (`# jetson_baslat.sh --kuru ... (CR'siz kopya)` veya NAVITAS_CR_KOPYA'yi env bolumune ekle) ve K8 bunu assert etsin; Windows'ta dal kosmuyorsa `skipTest('YAPILAMADI: MSYS CR yutuyor')` — sessiz gecis degil.

### [ONEMLI] `--kapi` uc ucu SIRALI kosuyor: CONTRACTS 7.4 / FAZ_B_GUN_PLANI 1 'uc uc AYNI ANDA acikken GECTI' der; sirali kosum bunu sinamaz ve thazirlik'e +22..+52 s ekler (6.2: 30 s = 1 puan). Cikis kodu mantigi ve fail-closed DOGRU
REPRO: scratchpad/prova.sh kapi_gec KIP=sik FOV=78 FAKE_SURE=2 -- --kapi; cat scratchpad/log/shim_kapi_gec.log | grep sudo; scratchpad/prova.sh kapi_dus KIP=udp YKS_IP=10.0.0.1 IKA_IP=10.0.0.2 FOV=78 FAKE_DUSEN=udp:127.0.0.1:14551 -- --kapi; grep -n 'MAVLINK_DOGRULAMA_SURESI_S\|HEARTBEAT_TAVAN_S\|ACK_TAVAN_S' codes/karar_sozlesmesi.py scripts/mavlink_dogrula.py
HAM: shim log (2 s sahte dogrula): 145.348 sudo -u navitas ... --mavlink udp:127.0.0.1:14550 | 147.466 ... 14551 | 149.593 ... 14552 -> her biri oncekinin BITISINDEN sonra (sirali); 'thazirlik (bu betik, kapi dahil): 14 s'
Gercek sabitler: MAVLINK_DOGRULAMA_SURESI_S = 10.0, HEARTBEAT_TAVAN_S = 15.0, ACK_TAVAN_S = 1.0, BIRIKINTI 0.2 -> uc basina 11.2..26 s, sirali 34..78 s + sleep 3 + sleep 2; paralel olsa 11..26 s.
kapi_dus: [GECTI] 14550 / [DUSTU] 14551 / [GECTI] 14552 -> 'HATA: kapi 2/3 — tuketiciler BASLATILMADI' EXIT=1; shim logda tuketici enable YOK (dogru), cogullayici enable --now kalir.
kapi_gec: 3/3 -> 'systemctl enable --now navitas-rpi-inference.service navitas-iha-inis-yayinci.service navitas-iha-komut-alici.service' (dogru).
ONERI: Ucu paralel baslat: `for uc in ...; do (sudo -u ... "$d" --mavlink "$uc" --sysid "$SYSID" > "$LOG_DIZIN/kapi_$port.log" 2>&1; echo $? > "$LOG_DIZIN/kapi_$port.rc") & done; wait`; sonra rc dosyalarindan 3/3 say. Boylece CONTRACTS'in 'ayni anda' kosulu gercekten sinanir ve thazirlik ~25 s kisalir.

### [ONEMLI] Birimlerde `User=navitas` ve `Environment=PATH=/home/navitas/.local/bin` SABIT: NAVITAS_KOK/SERVIS_KULLANICI ezilse de yalniz kok ve python yolu sed'lenir; kilavuz kullanici adini zorlamiyor (`~/navitas`, adduser yok) — kullanici `navitas` degilse --kuru 'tamam', --kur dosya denetimini gecer, systemd 217/USER ile SONSUZ restart dongusu
REPRO: scratchpad/prova.sh kur_udp KIP=udp YKS_IP=10.0.0.1 IKA_IP=10.0.0.2 FOV=78 -- --kur; grep -H '^User\|^WorkingDirectory\|^Environment=PATH' scratchpad/etc/systemd/kur_udp/navitas-cogullayici.service; grep -n 'id "\$SERVIS\|getent\|id -u "\$SERVIS' jetson_paket/jetson_baslat.sh; grep -rn 'adduser\|useradd\|User=navitas' jetson_paket/*.md
HAM: kurulu navitas-cogullayici.service:
  User=navitas
  WorkingDirectory=/c/.../scratchpad/kok   <- NAVITAS_KOK sed'lendi
  Environment=PATH=/home/navitas/.local/bin:/usr/local/bin:/usr/bin:/bin   <- SABIT
betikte kullanici varligi denetimi: (yok)
kilavuzlarda kullanici adi zorunlulugu: (yok); JETSON_KILAVUZ '~/navitas' gecen satir: 28
-> Betik SERVIS_KULLANICI degiskenini yalniz chown / MAVPROXY_PATH / sudo -u icin kullanir; birim dosyasina ISLENMEZ. Jetson'da login kullanicisi navitas degilse (kilavuz bunu hic kurdurmuyor) bes birim 'Failed to determine user credentials' ile Restart=always + StartLimitIntervalSec=0 altinda sonsuz dongude kalir; --kuru bunu gormez.
ONERI: birimleri_kur sed'ine `-e "s#^User=navitas#User=$SERVIS_KULLANICI#" -e "s#/home/navitas/.local/bin#/home/$SERVIS_KULLANICI/.local/bin#"` ekle; dosya_denetle'ye `id -u "$SERVIS_KULLANICI" >/dev/null 2>&1 || hata "kullanici yok: $SERVIS_KULLANICI"`; --kuru'ya `[VAR]/[YOK] kullanici $SERVIS_KULLANICI`; SERVIS_KULLANICI'yi JETSON_BASLAT.md degisken listesine yaz (su an belgede yok); varsayilani `${SUDO_USER:-navitas}` yapmak da dusunulebilir.

### [ONEMLI] SiK topolojisi belge<->kod celiskisi: CONTRACTS 7.5 ve SAHA_RUNBOOK 3 `--yks-hedef 5100 --ika-hedef 5100` + `--bind 0.0.0.0:5007` yazar, betik yalniz `--yks-hedef 5100` + `--bind 127.0.0.1:5007` verir (K2 kilitler). OLCUM: belgedeki topoloji hub'a ayni cerceveyi tur icinde 1 kez yazar ama 'ika' ACK'i hic gelmedigi icin 8 tekrar / 2.11 s (8x 433 MHz yuku); betik topolojisi 1 gonderim
REPRO: O:/navitas-local-train/venv/Scripts/python.exe scratchpad/q6_sender.py; KIP=sik FOV=78 bash jetson_paket/jetson_baslat.sh --kuru | grep -c 5100; sed -n '/Topoloji (SiK kipi/,/0.0.0.0:5007/p' CONTRACTS.md; sed -n 76,80p SAHA_RUNBOOK.md
HAM: BETIK (yalniz --yks-hedef 5100): send() cagrisi=1 acked=['yks'] sure=0.00s ; heartbeat send()=1
CONTRACTS 7.5 (--yks-hedef 5100 --ika-hedef 5100): send() cagrisi=8 acked=['yks'] sure=2.11s ; heartbeat send()=1
(iha_sender._tekrarli_gonder: `peer in gonderilen_hedefler` tur icinde tekillestirir; `acked >= set(self.peers)` 'ika' dugumu bekler -> noktadan noktaya SiK'te 8 tur dolar)
--kuru KIP=sik: rpi_inference ... --yks-hedef 127.0.0.1:5100 (tek hedef); iha_komut_alici ... --bind 127.0.0.1:5007
CONTRACTS 7.5: `rpi_inference --yks-hedef 127.0.0.1:5100 --ika-hedef 127.0.0.1:5100` · `iha_inis_yayinci --yks 127.0.0.1:5100 --ika 127.0.0.1:5100` · `iha_komut_alici --bind 0.0.0.0:5007`
SAHA_RUNBOOK 78-80: ayni iki-hedefli satirlar.
HUKUM (Q6): hub ayni cerceveyi seriye iki kez YAZMAZ (betikte ikinci hedef yok; belgedeki cift hedefte de tur ici tekillestirme var) — ama belgeye 'uyduran' 8x tekrar alir; ayrica betik topolojisinde IKA'ya OPEN_ROUTE/IHA_LANDED'in nasil ulasacagi JETSON_BASLAT.md'de 'ACIK' birakilmis.
ONERI: CONTRACTS 7.5 ve SAHA_RUNBOOK 3 topoloji satirlarini betikle hizala (tek hedef, --bind 127.0.0.1:5007) ya da betigi belgeye cekmeden once iha_sender'da ACK muhasebesini ADRES bazli yap (ayni adresli akranlar tek ACK ile kapanir). IKA hattina karar (SiK cok-noktali mi, WiFi `--ika-hedef <IKA_IP>:5006` mi) cumartesiden once verilip K2'ye kilitlenmeli.

### [KUCUK] Test K3 birim BOLUMUNU izlemiyor: `StartLimitIntervalSec=0` [Service]'e tasininca (systemd sessizce yok sayar -> 10 s'de 5 cokuste pes eder, hands-off ihlali) 24 test yine OK. Bugunku dosyalar DOGRU ([Unit] altinda) — kilit bos
REPRO: scratchpad/mut.sh M1 jetson_paket/systemd/navitas-cogullayici.service '/^StartLimitIntervalSec=0$/d; /^Type=simple$/a StartLimitIntervalSec=0'; grep -n 'StartLimit\|^\[' jetson_paket/systemd/*.service
HAM: [M1_StartLimit_Service_bolumune] diff: 13d12 < StartLimitIntervalSec=0 / 16a16 > StartLimitIntervalSec=0 (artik [Service] altinda, satir 16)
[M1_StartLimit_Service_bolumune] Ran 24 tests in 11.476s / OK
Gercek dosyalar (cat -A): bes birimde de `[Unit]` ... `StartLimitIntervalSec=0` ... `[Service]` sirasi -> Q7: dogru bolumde.
_birim_oku: `if not satir or satir.startswith('#') or satir.startswith('['): continue` -> bolum bilgisi atilir.
ONERI: _birim_oku bolum->alan sozlugu dondursun; K3 `a['Unit']['StartLimitIntervalSec']==['0']`, `a['Service']['Restart']==['always']`, `a['Install']['WantedBy']` diye kilitlesin.

### [KUCUK] `--kur/--kapi/--dogrudan/--durdur` yollari hic test edilmiyor: kapi esigi 3->2, kurulumda `tr -d '\r'` kaldirma, `enable --now`->`enable` mutasyonlarinda 24 test OK (kontrol mutasyonu Restart=on-failure ise yakalaniyor)
REPRO: scratchpad/mut.sh M2 jetson_paket/jetson_baslat.sh 's/\[ "\$gecen" -eq 3 \]/[ "$gecen" -ge 2 ]/'; scratchpad/mut.sh M3 jetson_paket/jetson_baslat.sh 's/tr -d .... < "\$(birim_dosyasi "\$b")"/cat "$(birim_dosyasi "$b")"/'; scratchpad/mut.sh M5 jetson_paket/jetson_baslat.sh 's/systemctl enable --now \$(birim_listesi)/systemctl enable $(birim_listesi)/'; scratchpad/mut.sh M4 jetson_paket/systemd/navitas-rpi-inference.service 's/^Restart=always$/Restart=on-failure/'
HAM: [M2_kapi_2_of_3_gecer] 329c329 -eq 3 -> -ge 2 ; Ran 24 / OK
[M3_birim_kurulurken_CR_silinmez] 291c291 tr -d '\r' < ... -> cat ... ; Ran 24 / OK
[M5_enable_now_yerine_enable] 305c305 ; Ran 24 / OK
[M4_KONTROL_Restart_on_failure] FAIL: test_K3_gozcu_alanlari_her_birimde ; FAILED (failures=1)  <- test tamamen bos degil, ama kurulum yollari kapsam disi.
Shim provasi bu yollarin test edilebilir oldugunu gosterdi: scratchpad/prova.sh (systemctl/sudo/id/python3/mavproxy.py sahte, PATH basinda) ile --kur/--kapi/--dogrudan/--durdur tamami kostu.
ONERI: tests/test_faz_b_jetson_baslat.py'ye shim tabanli K10: gecici dizine sahte systemctl/sudo/id (bash betikleri) + PYTHON3/PIXHAWK_SERI/NAVITAS_KOK/ENV_DOSYA/SYSTEMD_DIZIN/LOG_DIZIN ile `--kur` ve `--kapi` (FAKE_DUSEN) kos; systemctl cagri logunu ve yazilan env/birim dosyalarini (CR'siz, sed'lenmis) assert et.

### [KUCUK] `--kuru` ile `--dogrudan` ayrisir: `nohup $k` tirnaksiz -> glob genislemesi (cwd=NAVITAS_KOK); bosluklu deger uc yerde de ayni bolunur ama --kuru uyarmaz; env dosyasinda tirnaklama yok (systemd/bash ikisi de bosluktan boler)
REPRO: FAKE_SLEEP=2 scratchpad/prova.sh dog_glob KIP=udp YKS_IP=10.0.0.1 IKA_IP=10.0.0.2 FOV=78 KAMERA='*' -- --dogrudan | grep 'BASLAT.*rpi'; grep -A3 'ARGV\[--kaynak\]' scratchpad/log/jetson_log_dog_glob/navitas-rpi-inference.log; FAKE_SLEEP=6 scratchpad/prova.sh dog KIP=udp YKS_IP=10.0.0.1 IKA_IP=10.0.0.2 FOV=78 KAMERA='/tmp/a b.mp4' -- --dogrudan; cat scratchpad/log/jetson_log_dog/navitas-rpi-inference.log
HAM: [BASLAT] navitas-rpi-inference: ... --fov 78 --kaynak * --yks-hedef ...   (kuru/BASLAT satiri)
ARGV[--kaynak] ARGV[codes] ARGV[comms] ARGV[config]   (dogrudan'in gercekte kostugu)
KAMERA='/tmp/a b.mp4': kuru '--kaynak /tmp/a b.mp4'; dogrudan ARGV[--kaynak] ARGV[/tmp/a] ARGV[b.mp4]; env dosyasi 'RPI_EK_ARGS=--fov 78 --senaryo HTAB --kaynak /tmp/a b.mp4' (tirnaksiz; systemd $RPI_EK_ARGS da bosluktan boler -> ayni yanlis, tutarli). Jetson'da KAMERA indeks//dev/videoN/http oldugu icin (rpi_inference --kaynak help; CSI/gst RPi tarafinda) risk dusuk.
ONERI: dogrudan() icinde `set -f` (nohup satirindan once), kuru()'da ENV_ANAHTARLAR degerlerinde `[[:space:]*?\[\\"']` gorulurse `[UYARI] <anahtar> bosluk/glob/kacis iceriyor — systemd ve bash bunu BOLER` bas; birim ExecStart'inda `${KAMERA}` gibi tek-arguman kalibi ancak ayri anahtar acilirsa mumkun.

### [KUCUK] ENV_DOSYA / SYSTEMD_DIZIN ezildiginde --kuru ile systemd ayrisir: env `$ENV_DOSYA`'ya yazilir, kurulu birimler `EnvironmentFile=/etc/navitas.env` sabit okur (test bu anahtarlari taniyor: BEYAN_ANAHTARLARI)
REPRO: scratchpad/prova.sh kur_udp KIP=udp YKS_IP=10.0.0.1 IKA_IP=10.0.0.2 FOV=78 -- --kur | head -2; grep -H '^EnvironmentFile' scratchpad/etc/systemd/kur_udp/*.service
HAM: [YAZILDI] /c/.../scratchpad/etc/navitas_kur_udp.env
...kur_udp/navitas-cogullayici.service:EnvironmentFile=/etc/navitas.env  (bes birimde ayni)
-> ENV_DOSYA ezilmisse systemd eski/olmayan /etc/navitas.env'i okur; dosya yoksa birim hic baslamaz ('-' oneki yok).
ONERI: birimleri_kur sed'ine `-e "s#^EnvironmentFile=/etc/navitas.env#EnvironmentFile=$ENV_DOSYA#"` ekle ya da ENV_DOSYA/SYSTEMD_DIZIN'i test-ici kabul edip belgeden/degisken listesinden dus.

### [KUCUK] CR kopyasinda hata mesaji `$0`'i basar: 'root gerekli: sudo -E bash /tmp/tmp.XXXX' — trap'in sildigi gecici dosyayi kosmayi onerir; --kuru ise dogru olarak $PAKET_DIZIN kullanir
REPRO: cd scratchpad; PATH=$PWD/bin_grep:$PATH bash paket_crlf/jetson_baslat.sh --kur 2>&1 | head -1   # bin_grep: CR baytina gore -q 0 donen shim; ls /tmp/tmp.* | wc -l
HAM: HATA: root gerekli: sudo -E bash /tmp/tmp.CKd91II4hR
sonraki tmp kalinti: 0   (trap dosyayi sildi -> onerilen komut calismaz)
Karsilastirma --kuru: 'KURU SONUC: tamam — kurmak icin: sudo -E bash /c/.../paket_crlf/jetson_baslat.sh' (dogru yol).
ONERI: birimleri_kur: `hata "root gerekli: sudo -E bash $PAKET_DIZIN/jetson_baslat.sh ${1:-}"`; yardim() icin de `$PAKET_DIZIN/jetson_baslat.sh` (tmp kopyada calisiyor ama tutarlilik).

### [KUCUK] `--kuru` `[YOK] mavproxy.py (PATH)` iken 'KURU SONUC: tamam' + cikis 0 der; Jetson'da pip eksikse kuru 'tamam', --kur ise dosya_denetle'de HATA ile durur (fail-closed ama kuru yaniltir)
REPRO: KIP=udp YKS_IP=10.0.0.1 IKA_IP=10.0.0.2 FOV=78 bash jetson_paket/jetson_baslat.sh --kuru | tail -8; echo EXIT=$?
HAM: ## paket denetimi (/o/navitas/jetson_paket/kod)
[YOK] mavproxy.py (PATH) <- Jetson'da: pip3 install MAVProxy
[VAR] rpi_inference.py
[VAR] iha_inis_yayinci.py
[VAR] iha_komut_alici.py
## beyan denetimi
[TAM] beyanlar tam
KURU SONUC: tamam — kurmak icin: sudo -E bash /o/navitas/jetson_paket/jetson_baslat.sh
EXIT=0
ONERI: kuru(): paket denetiminde herhangi bir [YOK] varsa `KURU SONUC: eksik (paket/PATH) — gercek kosum DURUR` ve `kod=3`; Jetson'da ek olarak `-e $PIXHAWK_SERI`, `-x $PYTHON3`, `id $SERVIS_KULLANICI` satirlarini da [VAR]/[YOK] olarak bas (salt okunur, ucuz).

CURUTULEMEDI:
- Q1 UC YER ESITLIGI — CURUTULEMEDI: --kuru ciktisi, kurulu birim ExecStart'i (${VAR} tek-arguman, $VAR bosluktan bolme; tum ${...} anahtarlarinin betikte varsayilani var, bos kalamaz) ve --dogrudan'in sahte python3 ARGV logu (scratchpad/log/jetson_log_dog/*.log) ayni argüman dizisini verdi; K5 (bagimsiz Python yerine-koyma) 24/24 gecti. Tek ayrisma glob/set -f (KUCUK bulgu).
- Q2 ENV TIRNAKLAMA — kismen: env dosyasi tirnaksiz yazilir (cat -A: CR yok, 'RPI_EK_ARGS=--fov 78 --senaryo HTAB --kaynak /dev/video1'); systemd EnvironmentFile tirnaksiz degerde bosluk korur ve $VAR bosluktan boler, bash nohup $k de ayni boler -> tutarli. Ters bolu (systemd kacis yer, bash yemez) ve basta tirnak halleri Jetson'da gercekci deger olmadigi icin (KAMERA: indeks//dev/videoN/http; SENARYO choices HTAB/IHA_IB/FDA) olculmedi.
- Q3 CRLF — CURUTULEMEDI (mekanik): CRLF betik + CRLF birimler ile --kuru/--help/--kur (shim) kostu; kurulu 5 birimde CR=0, env CR=0 (cat -A), cikti LF ile birebir; zorlamali dalda mktemp/tr/exec/trap calisti, tmp temizlendi. Linux'ta gercek tetikleyicinin (`grep -q $'\r'` -> 0) kostugu burada OLCULEMEDI (WSL yok; MSYS grep CR gormuyor) — ONEMLI bulgu olarak yazildi.
- Q4 CIKIS KODU — CURUTULEMEDI: `if sudo -u ... python3 dogrula; then GECTI` mavlink_dogrula'nin `return 0 if rapor['gecti'] else 1` ile uyumlu; 2/3 -> HATA exit 1, tuketici enable yok; 3/3 -> tuketiciler enable --now. Sirali kosum ONEMLI bulgu olarak yazildi.
- Q5 sudo -E / PATH — OLCULEMEDI (sudoers yok): betik secure_path'i bilerek asiyor (MAVPROXY_PATH=/home/$SERVIS_KULLANICI/.local/bin:...; `PATH=... command -v` deyimi Git Bash'te dogrulandi: BULDU), cogullayici biriminde `Environment=PATH=/home/navitas/.local/bin:/usr/local/bin:/usr/bin:/bin` VAR; tuketiciler mutlak /usr/bin/python3 kullanir. sudoers'ta komut `ALL` ise SETENV ortuk olup `-E` ve `sudo -E KIP=... bash` bicimi calisir (sudoers(5)); dar Cmnd_Alias varsa 'not allowed to preserve the environment' riski kanitsiz kaldi.
- Q7 StartLimitIntervalSec — CURUTULEMEDI: bes .service dosyasinda da `[Unit]` altinda (cat -A dokumu); yalniz testin bolumu kilitlemedigi KUCUK bulgu.
- MAVProxy secenek adlari (--daemon --non-interactive --state-basedir) — DOGRULANAMADI: venv'de MAVProxy yok (ModuleNotFoundError); Jetson'da `mavproxy.py --help | grep state-basedir` ile kontrol edilmeli.
- --durdur nohup pid'leri: FAKE_SLEEP=25 ile dort surecin (cogullayici dahil) [OLDURULDU] oldugu teyit edildi; ilk kosumdaki eksik satir sahte surecin zaten bitmis olmasiydi.
- bash -n jetson_baslat.sh: SYNTAX OK; tests/test_faz_b_jetson_baslat.py gercek kosum: Ran 24 tests, OK; --kuru udp/sik cikislari K1/K2 beklentileriyle ayni (5100 tek hedef, /dev/ttyUSB0 yalniz hub satirinda).
- kapi basarisiz kalinca cogullayici enable --now kalir ve tuketiciler yalniz stop edilir (onceki kurulumdan enable kaldiysa acilista kapisiz kalkar) — tasarim/hands-off gerekcesiyle bulgu yazilmadi.

## TEST VAKUMU / MUTASYON — comms/seri_hub.py + tests/test_faz_b_seri_hub.py (CONTRACTS §7.5, D-404 §7.2 denetim borcu). Yordam: seri_hub.py bayt-eş kopyası scratchpad'e alındı (cmp ile doğrulandı), 25 mutant üretildi (uret.py; her değişim hedefi orijinalde TAM BİR kez bulunmak zorunda), her mutant sys.modules['seri_hub'] enjeksiyonuyla repo suitine (11 test) koşuldu (kos_mutant.py; orijinal kopya 11/11 OK ile harness doğrulandı). Sonuç: 13 YAKALANDI / 12 KAÇTI. Kaçan her mutant için eksik test yazıldı (ek_testler.py, 9 test), orijinalde 9/9 geçti, mutantlara karşı koşuldu: 11/12 yakalandı (l bilerek yazılmadı). Ayrıca Windows zamanlayıcı granülerliği, hub tur süresi ve UDP↔seri uçtan uca gecikme ölçüldü (olc_granul.py, rastgele fazlı). Repo değişmedi (git status boş, seri_hub.py bayt-eş). Ham loglar: C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub\log_*.txt ve eklog_*.txt. Yorumlayıcı: O:\navitas-local-train\venv\Scripts\python.exe; pytest kurulu değil, unittest ile koşuldu.

### [ONEMLI] İki ÖĞRENİLEN tüketici hiç sınanmıyor — mutant b (öğrenilenlerden yalnız EN SON gönderene fan-out) 11/11 testten kaçtı; üretim topolojisinde tam iki öğrenilen var (rpi_inference + iha_inis_yayinci)
REPRO: cd C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub && O:\navitas-local-train\venv\Scripts\python.exe kos_mutant.py m_b_ogrenilen_yalniz_son_gonderen.py ; O:\navitas-local-train\venv\Scripts\python.exe kos_ek.py m_b_ogrenilen_yalniz_son_gonderen.py TestEksik.test_b_iki_ogrenilen_ikisi_de_alir ; O:\navitas-local-train\venv\Scripts\python.exe kos_ek.py seri_hub_orig.py
HAM: Mutant (_fanout icinde): hedefler = list(dict.fromkeys(self.tuketiciler + list(self.ogrenilen)[-1:]))
Repo suiti: MUTANT m_b_ogrenilen_yalniz_son_gonderen.py: KACTI ran=11 fail=0 err=0 sure=17.7s
Ek test: EK-MUTANT m_b_ogrenilen_yalniz_son_gonderen.py: YAKALANDI ran=9 fail=1 err=0 sure=15.3s
  -> test_b_iki_ogrenilen_ikisi_de_alir: AssertionError: 1 != 0 : ILK ogrenilen (a) cerceve almadi
Orijinal ile ek testler: EK-MUTANT seri_hub_orig.py: KACTI ran=9 fail=0 err=0 sure=12.3s
Neden kacti: test_2 = statik + 1 ogrenilen; test_7 ve test_5 = statik adres ayni zamanda ogrenilen (tekil). Hicbir testte hub basina IKI ayri ogrenilen yok; 'statik ∪ ogrenilenlerin HEPSINE' (CONTRACTS §7.5) iddiasinin 'hepsi' kismi sinanmiyor.
ONERI: ek_testler.py::test_b_iki_ogrenilen_ikisi_de_alir'i tests/test_faz_b_seri_hub.py'ye tasi: a ve b ikisi de gonderir (b EN SON), YKS'den cerceve gelir, a ve b'nin ikisi de 1 datagram alir, fanout_gonderim == 2. Kod bugun dogru; bu bir vakum bulgusudur — sahada bu hata olsaydi YKS ACK'i rpi_inference'a ulasmaz, OPEN_ROUTE AckliTekrar tukenirdi.

### [ONEMLI] 'Arızada kuyruklanmaz, bayat rota yayınlanmaz' iddiası TELDE sınanmıyor — c2 (sessiz kuyruk boşaltma) kaçtı; c1 yalnızca seri_yazilan SAYACIYLA yakalandı; test_4 _seri_cerceve_bekle'nin 'toplanan' listesini atıyor
REPRO: cd C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub && O:\navitas-local-train\venv\Scripts\python.exe kos_mutant.py m_c2_kuyruk_yeniden_acinca_yazilir_sessiz.py ; O:\navitas-local-train\venv\Scripts\python.exe kos_mutant.py m_c1_kuyruk_yeniden_acinca_yazilir_sayacli.py ; O:\navitas-local-train\venv\Scripts\python.exe kos_ek.py m_c2_kuyruk_yeniden_acinca_yazilir_sessiz.py TestEksik.test_c_arizada_dusen_datagram_yeniden_acinca_TELDE_yok
HAM: Mutant c1/c2: arizada `self._kuyruk.append(veri)` (dusurulen sayaci KORUNDU), `_seri_bagla` icinde kuyruk `link.send(_eski)` ile bosaltilir; c1 seri_yazilan'i artirir, c2 artirmaz.
MUTANT m_c2_kuyruk_yeniden_acinca_yazilir_sessiz.py: KACTI ran=11 fail=0 err=0 sure=17.6s
MUTANT m_c1_kuyruk_yeniden_acinca_yazilir_sayacli.py: YAKALANDI ran=11 fail=1 err=0 sure=17.5s
  -> test_4_seri_okuma_arizasi_hub_cokmez_dusurur_yeniden_acar: AssertionError: 1 != 2   (yalniz `assertEqual(1, k.hub.sayac["seri_yazilan"])`)
EK-MUTANT m_c2_...sessiz.py: YAKALANDI ran=9 fail=1 err=0
  -> test_c_arizada_dusen_datagram_yeniden_acinca_TELDE_yok: AssertionError: 3 unexpectedly found in [3, 4] : bayat (dusurulen) cerceve telde gorundu: [{'v': 1, 'type': 'CMD', 'cmd': 'PARACHUTE', 'hedef': 'iha', 'seq': 3, ...}, {... 'seq': 4 ...}]
(c1 de ayni ek testle yakalandi: 3 unexpectedly found in [3, 4])
Kok: tests/test_faz_b_seri_hub.py:376 `m, _ = _seri_cerceve_bekle(yks2, FrameReader(), lambda x: x.get("seq") == 4, ...)` — kosul seq==4; seq=3 (arizada dusurulmus PARACHUTE) telde ONCE gorunse bile test gecer.
ONERI: test_4'te tek satir: `m, hepsi = _seri_cerceve_bekle(...)` ve `self.assertEqual([4], [x.get('seq') for x in hepsi], 'bayat cerceve telde')`. Boylece 'kuyruklanmaz' iddiasi sayac degil TEL ile kilitlenir (sayac mutasyonla bagimsiz olarak yanlis kalabilir). Alternatif: ek_testler.py::test_c'yi tasi.

### [ONEMLI] OGRENILEN_TAVANI (32) tahliye mantığı hiç sınanmıyor — 3 mutant kaçtı (i1: en YENİ düşer, i2: tavan yok, j: tazelik güncellenmez → uzun ömürlü tüketici tahliye edilir); D-404 §7.2 madde 2'nin açık sorusu
REPRO: cd C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub && for m in i1_tavan_en_yeni_dusurulur i2_tavan_yok j_tazelik_guncellenmez; do O:\navitas-local-train\venv\Scripts\python.exe kos_mutant.py m_$m.py; O:\navitas-local-train\venv\Scripts\python.exe kos_ek.py m_$m.py TestEksik.test_i_ogrenilen_tavani_en_eski_dusurulur_uzun_omurlu_kalir; done ; O:\navitas-local-train\venv\Scripts\python.exe kos_ek.py seri_hub_orig.py TestEksik.test_i_ogrenilen_tavani_en_eski_dusurulur_uzun_omurlu_kalir
HAM: Repo suiti:
MUTANT m_i1_tavan_en_yeni_dusurulur.py: KACTI ran=11 fail=0 err=0 sure=17.6s
MUTANT m_i2_tavan_yok.py: KACTI ran=11 fail=0 err=0 sure=17.6s
MUTANT m_j_tazelik_guncellenmez.py: KACTI ran=11 fail=0 err=0 sure=17.5s
Ek test (L uzun omurlu, her 8 kisa omurlude bir heartbeat; 36 kisa omurlu):
EK-MUTANT seri_hub_orig.py: KACTI ran=1 fail=0 err=0 sure=4.6s   (kod DOGRU: L kalir, en eski duser, len==32, L fan-out alir)
EK-MUTANT m_i1_...: YAKALANDI -> AssertionError: ('127.0.0.1', 56764) unexpectedly found in {...}  (EN ESKI dusmedi)
EK-MUTANT m_i2_...: YAKALANDI -> AssertionError: 32 != 37 : tavan uygulanmadi
EK-MUTANT m_j_...:  YAKALANDI -> AssertionError: 'dusuruldu: 127.0.0.1:56724' unexpectedly found in '[SERI_HUB] ... tuketici ogrenildi: 127.0.0.1:56724 ...'  (L ARADA tahliye edildi)
NOT: j mutanti ek testin ILK surumunden de kacti — L tam tahliye turunda yeniden heartbeat atip yeniden ogreniliyordu, sonuc kumesi dogru gorunuyordu. Ancak tahliye OLAYINA (log satiri + 'ogrenildi: L' sayisi == 1) bakinca yakalandi: tahliye-ile-yeniden-ogrenme arasindaki her fan-out kayiptir.
ONERI: ek_testler.py::test_i'yi tasi (sikilastirilmis surum: hem sonuc kumesi hem tahliye logu hem L'nin tek kez ogrenilmesi). `_ogren`'daki 'sona tasi' (pop+insert) ve `next(iter(...))` en-eski secimi tek satirlik, sessizce bozulabilen mantiktir; 8-9 saatlik provada systemd Restart=always dongusu 32 farkli efemer port uretebilir. Kod bugun dogru; risk test vakumundadir.

### [KUCUK] Yeniden açmada FrameReader sıfırlaması sınanmıyor — mutant h (eski yarım çerçeve yeni akışa taşınır) kaçtı; etki: yeniden açma sonrası ilk çerçeve bozuk sayılıp kaybolur
REPRO: cd C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub && O:\navitas-local-train\venv\Scripts\python.exe kos_mutant.py m_h_okuyucu_sifirlanmaz.py ; O:\navitas-local-train\venv\Scripts\python.exe kos_ek.py m_h_okuyucu_sifirlanmaz.py TestEksik.test_h_yeniden_acmada_yarim_cerceve_atilir
HAM: Mutant: `_seri_bagla` icinde `self.okuyucu = FrameReader()` satiri kaldirildi.
MUTANT m_h_okuyucu_sifirlanmaz.py: KACTI ran=11 fail=0 err=0 sure=17.6s
EK-MUTANT m_h_okuyucu_sifirlanmaz.py: YAKALANDI ran=9 fail=1 err=0 sure=15.4s
  -> test_h_yeniden_acmada_yarim_cerceve_atilir: AssertionError: 1 != 0 : yeniden acma sonrasi ilk cerceve gelmedi
Neden kacti: test_4'te ariza aninda okuyucu tamponu BOS (heartbeat tamamen tuketilmis); yarim cerceve senaryosu yok. Etki sinirli: bir cerceve kaybi, sonraki newline'da toparlanir; PARACHUTE 40 tekrar ile gelir.
ONERI: ek_testler.py::test_h'yi tasi: YKS newline'siz yarim cerceve gonderir, hub okur (on kosul: okuyucu._buf == yarim), recv OSError -> ariza -> yeniden acma, yeni hattan gelen ilk tam cerceve bozuk=0 ile statik tuketiciye ulasir.

### [KUCUK] Fail-visible sayaç ve koruma yolları vakumda: 5 mutant kaçtı — k (seri kapalıyken boş tur beklemesi yok = sıcak döngü), p (UDP tur tavanı 1), u (seri_ac None dönünce None bağlanır + 'YENIDEN ACILDI' yalanı), m (hedefsiz fan-out sessiz), n (fan-out OSError yükselir → poll patlar); l (arızada gönderen öğrenilmez) de kaçtı, davranış farkı marjinal
REPRO: cd C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub && for m in k_bos_tur_beklemez p_udp_tur_tek_datagram u_seri_ac_none_baglanir m_hedefsiz_sessiz n_fanout_hatasi_yukselir l_arizada_ogrenmez; do O:\navitas-local-train\venv\Scripts\python.exe kos_mutant.py m_$m.py; O:\navitas-local-train\venv\Scripts\python.exe kos_ek.py m_$m.py; done
HAM: Repo suiti (hepsi): MUTANT m_k_bos_tur_beklemez.py: KACTI ran=11 fail=0 · m_p_udp_tur_tek_datagram.py: KACTI · m_u_seri_ac_none_baglanir.py: KACTI · m_m_hedefsiz_sessiz.py: KACTI · m_n_fanout_hatasi_yukselir.py: KACTI · m_l_arizada_ogrenmez.py: KACTI
Ek testler:
EK-MUTANT m_k_...: YAKALANDI -> test_k_seri_kapaliyken_bos_tur_bekler: AssertionError: 10 != 0   (_dur.wait hic cagrilmadi)
EK-MUTANT m_p_...: YAKALANDI -> test_p_tek_turda_datagram_patlamasi_hepsi_seriye: AssertionError: 10 != 1 : tek turda hepsi yazilmadi
EK-MUTANT m_u_...: YAKALANDI -> test_u_seri_ac_None_donerse_baglanmaz: AssertionError: 1 != 0   (yeniden_acma_hatasi sayilmadi)
EK-MUTANT m_m_...: YAKALANDI -> test_m_hedefsiz_fanout_sayilir_ve_kirmizi_loglanir: AssertionError: 1 != 0
EK-MUTANT m_n_...: YAKALANDI -> test_n_fanout_oserror_hub_yasar_sayilir: OSError: ENOBUFS   (poll'dan yukseldi, hub olurdu)
EK-MUTANT m_l_...: KACTI (ek test yazilmadi; tuketici AckliTekrar ile yeniden gonderince zaten ogrenilir)
Dokstring 'sessiz basari yalani yok: hedefsiz, yazilamayan fan-out, dusurulen — hepsi sayilir' diyor; hedefsiz ve fanout_hata sayaclarina hicbir test dokunmuyor. k icin: Windows'ta UDP 1 ms zaman asimi zaten 15,6 ms oldugundan sicak dongu gorunmez, Linux'ta ~1000 tur/s olur.
ONERI: ek_testler.py test_k/p/u/m/n'yi tasi (toplam ~2 s, mock ile; gercek soket yok). n icin: udp_link.send OSError -> poll yasar, fanout_hata==1, 'yazilamadi' KIRMIZI log. l icin test gerekmez.

### [KUCUK] Zaman tavanları / Windows zamanlayıcı granülerliği: repoda 'Windows select granülerliği' notu YOK; ölçüm: 1 ms UDP zaman aşımı fiilen 15,6 ms, 20 ms seri zaman aşımı 31,3 ms, boş hub.poll 46,8 ms (nominal 21 ms × 2,2). Linux'ta testler KIRILGAN DEĞİL — ama mutant o'nun test_7'de yakalanması Windows'a özgü bir tesadüf: Linux'ta kaçar
REPRO: O:\navitas-local-train\venv\Scripts\python.exe C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub\olc_granul.py ; cd ...\mut_seri_hub && O:\navitas-local-train\venv\Scripts\python.exe kos_mutant.py m_o_seri_tur_tek_okuma.py ; grep -rn -i 'granül\|granul\|Windows select' O:\navitas\tests O:\navitas\comms O:\navitas\*.md (bos)
HAM: 3.13.7 win32 (Windows 11 10.0.26200)
UDP recv timeout=1ms: n=200 mean=15.54ms p50=15.58ms p95=16.11ms max=16.59ms
Event.wait(0.02): n=100 mean=31.41ms p50=31.50ms p95=32.09ms
socket:// read(1) timeout=20ms bos: n=100 mean=31.16ms p50=31.29ms p95=32.05ms
hub.poll seri ACIK idle: n=100 mean=46.79ms p50=46.80ms p95=48.03ms max=48.38ms
hub.poll seri KAPALI (seri_ac=None): n=100 mean=46.66ms p50=46.83ms
Repo suiti Windows: 11 test 17,5 s; en uzun test_3 9,50 s (100 bayt × ~47 ms tur), diger pozitif beklemeler < 1,9 s; TAVAN_S=3,0 s.
MUTANT m_o_seri_tur_tek_okuma.py: YAKALANDI ran=11 fail=1 -> test_7_statik_ve_ogrenilen_ayni_adres_TEK_datagram_alir: AssertionError: 1 != 0 : cerceve 0 kez geldi   (tavan_s=1.0)
test_7 PARACHUTE cerceve boyu: 80 bayt. Hesap: mutant o turda 1 recv = 2 bayt (socket:// in_waiting 0/1). Windows: 1,0 s / 47 ms ≈ 21 tur × 2 = 42 bayt < 80 -> cerceve tamamlanmaz -> DUSER. Linux (1 ms ve 20 ms zaman asimlari gercek): 1,0 s / ~21 ms ≈ 47 tur × 2 = 94 ≥ 80 -> cerceve gelir -> mutant KACAR (hesap; Linux'ta olculmedi).
Kirilganlik degerlendirmesi: pozitif tavanlar (3 s) gercek ise (< 100 ms) karsi ≥30×; negatif pencereler (test_3/6: 0,2 s = Windows'ta 4 tur, Linux'ta ~9; test_7: 1,0 s) Linux'ta DAHA COK tur icerir, yani daha guclu. test_5 join(2 s): hub dongusu ≤ 1 tur icinde cikar. test_10 Timer 0,2 s: yeterli. Linux'ta yanlis dusme beklenmez. seri_hub.py dokstringindeki 'tur gecikmesi tavani yine 20 ms' iddiasi Windows'ta tutmaz (47 ms), Jetson/Linux'ta tutar — hub yalniz Jetson'da kosar.
ONERI: (1) SERI_TUR_TAVANI'nin gercek bir korumasi yok: test_7'nin tesadufi yakalamasi yerine 'tek poll'da ≥ N bayt tuketilir' turunden tur-sayili (zaman-sayisiz) bir test ekle (ek test_p'nin seri ikizi). (2) Test dosyasi bas dokstringine olculen degerleri not et: Windows'ta poll ≈ 47 ms, Linux'ta ≈ 21 ms; 0,2 s negatif pencere Windows'ta yalniz ~4 tur demektir. (3) seri_hub.py satir 83-84'teki '20 ms tavan' iddiasina 'Linux' kaydi dus.

CURUTULEMEDI:
- Repo suiti 25 mutanttan 13'unu yakaladi (ham: log_*.txt): a fan-out yalniz statik -> test_2 'ogrenilen tuketici cerceve almadi'; c1 kuyruk (sayacli) -> test_4 seri_yazilan 1 != 2; d1 bozuk ham fan-out -> test_6 JSONDecodeError; d2 dict-olmayan fan-out -> test_6 '{...} != 42'; e yazma hatasi yutulur -> test_4b 'SerialLink is not None'; f 1 s beklemez -> test_4 '0 != 2 : 1 s dolmadan yeniden acma denendi'; g1 +newline -> test_1 birebir bayt farki; g2 newline kirpilir -> test_1, test_4, test_5 (3 test); q arizada kapatmaz -> test_4 'arizali port gercekten kapanmali'; s bozuk sayilmaz -> test_6 '2 != 1'; v aralik siniri <= -> test_4 '2 != 1'; w hedefler tekil degil -> test_5 ve test_7 cift adres; o (Windows tesadufu, bulgu 6). CONTRACTS §7.5 yon tablosunun cekirdegi (UDP->seri birebir, seri->UDP tam cerceve = datagram, statik dinleyici, ariza: kapat + dusur + 1 s) CURUTULEMEDI.
- D-404 §7.2 madde 2 'ogrenilen kume 32 tavaninda uzun omurlu tuketicinin dusme riski': ek test_i orijinal kodda GECTI (EK-MUTANT seri_hub_orig.py: KACTI ran=1 fail=0) — L her 8 kisa omurlude bir tazelenirken 36 kisa omurlu icinde tavan 32 uygulandi, L dusmedi, en eski dustu, L fan-out aldi, tahliye logunda L yok. Kod dogru; risk yalniz test vakumunda (bulgu 3).
- D-404 §7.2 'tek iplikli dongude UDP->seri gecikmesi (0,20 s parasut tekrar araligina karsi) OLCULMEDI': olculdu (olc_granul.py, hub.calistir ayri iplikte, rastgele fazli 60 ornek, Windows): UDP->seri p50 9,49 ms / p95 31,11 ms / max 31,84 ms (tavan = seri okuma zaman asimi; Linux'ta ~21 ms beklenir); seri->UDP p50 0,97 ms / p95 15,12 ms / max 15,78 ms (tavan = UDP zaman asimi; Linux'ta ~1 ms). 200 ms'nin ≥ 6 kat altinda. Ilk olcum faz kilitliydi (p50 0,31 ms) — rastgele bekleme eklenince duzeltildi; rapor edilen degerler ikinci olcumdur.
- D-404 §7.2 'encode(decode()) yeniden kodlamanin cerceve butunlugu': tests `_tek_cerceve_dogrula` (tek newline sonda, decode == mesaj, encode(decode(d)) == d idempotens) uc testte kullaniliyor; d1/d2 mutantlari yakalandi. Python float repr round-trip kayipsiz, allow_nan=False ile NaN bozuk sayilir, ensure_ascii=False normalizasyonu anlamsal esitligi bozmaz. Curutulemedi.
- Fan-out ACK capraz karismasi (YKS ACK'i IKA beklentisine sayilir mi): comms/iha_sender.py `_tekrarli_gonder` TEK link kullanir ve `acked.add(m.get('node'))` ile NODE anahtarli kumeler; fan-out ile ayni ACK'in cok kez gelmesi zararsiz. Curutulemedi.
- UDP recv tamponu 4096 vs cerceve boyu: comms/iha_sender.py MAX_WAYPOINTS = 64 -> OPEN_ROUTE < 4 KiB (protocol.py 'en uzun mesru cerceve < 4 KiB'); kesilme/newline kaybi senaryosu yok.
- Jetson/Linux'ta test kirilganligi: pozitif tavan 3 s vs gercek is < 100 ms; Linux'ta tur 47 ms yerine ~21 ms (daha hizli), negatif pencereler daha cok tur icerir; gethostbyname('localhost') Ubuntu /etc/hosts ile 127.0.0.1; test_9 'COM_YOK_BOYLE_BIR_PORT' Linux'ta da SerialException(OSError) -> cikis 4. Yanlis dusme mekanizmasi bulunamadi (Linux'ta kosulmadi; olcum + hesap).
- Salt-okunurluk: git status --short bos (arada baska ajan 096a672 commit'ini atmis), `cmp O:\navitas\comms\seri_hub.py <scratchpad kopyasi>` bayt-es; O:\navitas altina hicbir yazma yapilmadi. Tum betikler/mutantlar/loglar: C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_seri_hub\ (uret.py, kos_mutant.py, kos_ek.py, ek_testler.py, olc_granul.py, m_*.py, log_*.txt, eklog_*.txt).

# PUSH TALİMATI — 2026-08-28

> **Durum:** kullanıcı push dondurmasını kaldırdı (*"pushları yap"*). Ama push
> **GitHub tarafından reddedilir** ve sebebi aşağıda ölçülerek yazılmıştır.
> Bu dosya, komutları sohbet kaydında kaybetmemek için vardır.

---

## 1. Neden push şu an başarısız olur

`1323fbb` (T159/T160) commit'inde `git add -A` iki dev dosyayı süpürmüş:

| dosya | boyut | uzakta var mı |
|---|---|---|
| `dronesolid/Bambu_Studio_win-v02.08.02.61.exe` | **409 MB** | **hayır** |
| `navitas_depo.bundle` | **290 MB** | **hayır** |

GitHub, **100 MB/dosya** sınırını aşan hiçbir push'u kabul etmez — dosya
sonradan silinse bile **nesne pakette kalır**. İkisinin de uzakta olmadığı
`git cat-file -e origin/master:<yol>` ile doğrulandı.

**Bu iki dosya depoya ait değil:**
- `.exe` bir **üçüncü taraf kurulum dosyasıdır** (Bambu Studio dilimleyici);
  internetten yeniden indirilir.
- `.bundle` **deponun kendi yedeğidir** — yani deponun içinde deponun kopyası
  (`yedek_drive.sh` üretiyor). Kendine gönderme yapan bir şişme.

⚠ `dronesolid/` klasörünün geri kalanı (STL, 3MF, CAD) **gerçek proje
dosyalarıdır ve kalır** — yalnız `.exe` çıkar.

---

## 2. GÜVENLE ŞİMDİ İTİLEBİLİR: 138 commit

`1323fbb`'den **önceki** geçmiş iki dosyadan da temizdir (doğrulandı:
`git ls-tree -r --name-only 1323fbb~1 | grep -ic "bambu\|navitas_depo.bundle"`
→ **0**).

```
git push origin 1323fbb~1:master --progress
```

Bu, uzak depoyu **166 commit geriden 28 commit geriye** çeker ve hiçbir şeyi
yeniden yazmaz. **Önce bunu koş.**

---

## 3. Kalan 28 commit — geçmiş temizliği gerekir

Kalan commit'ler o iki nesneyi taşıdığı için, ancak nesneler **itilmemiş
geçmişten** çıkarılırsa itilebilir.

**Güvenlik dalı zaten kuruldu:**
```
yedek_push_oncesi_20260828  ->  0c39e5c
```

### 3a. Adımlar

```bash
cd /o/navitas

# 1) Diskteki dosyalar KORUNSUN diye git dışına al (SİLİNMEZ)
#    (zaten .gitignore'a eklendi mi diye bak; değilse ekle)
grep -q "navitas_depo.bundle" .gitignore || {
  printf '\n# depo yedegi ve ucuncu taraf kurulum dosyasi — depoya girmez\nnavitas_depo.bundle\ndronesolid/*.exe\n' >> .gitignore
  git add .gitignore && git commit -m "navitas_depo.bundle ve dronesolid/*.exe artik izlenmiyor"
}

# 2) Itilmemis gecmisten iki nesneyi CIKAR (calisma agacina DOKUNMAZ)
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --index-filter \
  "git rm --cached --ignore-unmatch navitas_depo.bundle 'dronesolid/Bambu_Studio_win-v02.08.02.61.exe'" \
  -- origin/master..HEAD

# 3) Dogrula: 100 MB ustu nesne kalmamali
git ls-tree -r -l HEAD | awk '$4 > 100000000 {print $4/1048576 " MB  " $5}'

# 4) Dosyalar DISKTE duruyor mu (durmali)
ls -la navitas_depo.bundle dronesolid/Bambu_Studio_win-v02.08.02.61.exe

# 5) Genel kapi + suit HALA gecmeli
O:/navitas-local-train/venv/Scripts/python.exe codes/test_rota_sentetik.py
O:/navitas-local-train/venv/Scripts/python.exe -m unittest discover -s tests

# 6) Push
git push origin master --progress
```

### 3b. Ters gitmesi hâlinde

```bash
git reset --hard yedek_push_oncesi_20260828
```
Güvenlik dalı `0c39e5c`'yi gösteriyor; ayrıca `filter-branch` kendi yedeğini
`refs/original/` altında bırakır.

---

## 4. Neden bunu ben (Claude 2) yapmadım

`git filter-branch` ve `git push` bu oturumda **izin katmanınca engellendi** —
geçmiş yeniden yazan ve dışa dönük işlemler otomatik kipte kapalı. Makul bir
kısıt; kararı insana bırakıyor. Yukarıdaki komutlar **denenmiş sırayla**
yazıldı ve her adımın doğrulaması yanında.

---

## 5. Bundan sonra tekrarlamaması için

`git add -A` bu kazayı bir kez daha yapabilir. `.gitignore` satırları eklendiği
için aynı iki dosya bir daha girmez, ama **genel koruma** için:

```bash
# 50 MB ustu YENI dosya varsa commit'i durdur (ornek pre-commit kancasi)
git config core.hooksPath .githooks
```
*(Kanca yazılmadı — bu bir öneridir, uygulanması insan kararıdır.)*

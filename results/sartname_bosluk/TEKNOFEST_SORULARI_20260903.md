# TEKNOFEST'E İLETİLECEK SORU PAKETİ (2026-09-03 · plan v2 §0 + K3/K9)

> Kullanıcı sabah kopyalayıp iletebilir. Her sorunun yanında, CEVAP GELMEZSE
> uygulayacağımız fail-safe yorum yazılıdır (plan v2 §0 kararı — cevap gelene
> dek bağlayıcı).

## 1. Görev bitişi: sınıra girmek mi, brandaya temas mı?

Şartname §2.2.6 görev başarısını *"İKA'nın … HB sınırları içerisine
girmesi"* ile tanımlıyor; SS7 puan tablosu Pgörev için *"branda üzerine
(H noktası) fiziksel olarak temas"* şartı koyuyor. **Puanlama için brandaya
fiziksel temas mı gereklidir, HB alanına girmek yeterli midir?**

*Fail-safe yorumumuz:* temas hedeflenir (aracımız ped merkezine sürer;
CONTRACTS §7.3).

## 2. İHA→İKA güzergâh aktarımında YKS üzerinden röle kabul mü?

§2.2.3 güzergâhın *"yer istasyonuna ve İKA'ya"* aktarılmasını istiyor ancak
İKA'ya aktarımın **doğrudan İHA→İKA linkiyle mi** yapılması gerektiği, yoksa
**YKS üzerinden aktarmanın (röle)** kabul olup olmadığı yazılı değil. Ayrıca
hakemin "İKA'ya aktarıldı" onayı için beklenen **kanıt biçimi** (ekranda ACK
göstergesi yeterli mi) tanımsız. **Röle kabul müdür; kanıt olarak ne
gösterilmelidir?**

*Fail-safe yorumumuz:* doğrudan İHA→İKA linki kuruyoruz; YKS ekranında İKA'nın
ACK kanıtı gösteriliyor (iki aşamalı hakem onayı).

## 3. Manuel paraşüt ile "manuel müdahale = uçuş geçersiz" sınırı

§2.2.4 paraşütün YKS'den manuel tetiklenmesine (−50 ceza ile) açıkça izin
veriyor; §6.4 ise *"uçuşun herhangi bir aşamasında … manuel moda alınması"*
durumunda uçuşu başarısız sayıyor. **Manuel paraşüt tetikleme §6.4 kapsamında
uçuşu geçersiz kılar mı, yoksa yalnız −50 ceza ile geçerli kalır mı?**

*Fail-safe yorumumuz:* manuel paraşüt yalnız son çare emniyet aksiyonu olarak
tutuluyor; birincil tetik otonom.

## 4. (K3) HB zemin/harf renk düzeni ve temin

§2.1 HB'yi *"üzerinde kırmızı H harfinin bulunacağı"* 2×2 m branda olarak
tanımlıyor. **Zemin/harf renk düzeni (beyaz zemin + kırmızı H mi, kırmızı
zemin + beyaz H mi) ve brandanın yarışmada organizasyonca mı temin edileceği**
konusunda teyit rica ederiz. *(Kendi sahamızdaki baskıda beyaz zemin +
kırmızı H kullanıyoruz; algı katmanımız bu düzene göre doğrulandı.)*

## 5. (K9) FDA 20×20 m test alanı iç yerleşimi

§5.3.2 FDA test uçuşu için 20×20 m simüle alan tanımlıyor ancak **alanın iç
yerleşimi (şerit/güzergâh genişlikleri, engel düzeni, HB konumu)** şartnamede
yok; tam ölçekli HTAB şerit genişlikleri 20 m'ye sığmıyor. **FDA alanının
iç yerleşim krokisi paylaşılacak mı; takımlar kendi yerleşimini mi
kuracak?**

*Fail-safe yorumumuz:* HTAB düzeninin orantılı küçültülmüş bir profili ile
çalışıyoruz; kroki gelirse profil güncellenecek (kapı iki profilde koşuyor).

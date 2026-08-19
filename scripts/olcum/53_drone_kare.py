"""DRONE KARESİ → ZEMİN DOKU BANKASI (gerçek saha arka planı)

NEDEN: sentetik sahnelerin zemini şu an RescueNet'ten geliyor — Florida'da
kasırga sonrası çekilmiş hava görüntüleri. Bizim sahamız değil. Ölçülen transfer
boşluğunun büyük kısmı bu. Gerçek drone karesi gerçek zemin dokusunu, ışığı,
lensi, yüksekliği ve hareket bulanıklığını getirir.

NEDEN MOLOZU DA ÜRETKEN MODELE EKLETTİRMİYORUZ: üretken model piksel verir,
ETİKET vermez. Bizim kıt kaynağımız etiket. Moloz dışarıdan eklenirse maskesi
bilinmez → v16'daki "etiketsiz moloz" hatası tekrarlanır (moloza basma
%2,7 → %31,6). Bu yüzden: ZEMİN gerçek, MOLOZ/ŞERİT üreteçten → maske kusursuz.

İKİ TUZAK, İKİSİ DE BURADA ENGELLENİYOR:
  1. AŞIRI ÖRNEKLEME — 10 dk × 30 fps = 18.000 kare ama belki 100-200 farklı
     bakış var. Hepsi alınırsa veri seti büyük görünür, çeşitliliği sıfırdır ve
     karışımda gerçek RescueNet'i ezer. Varsayılan: 2,5 saniyede bir kare.
  2. BENZER KARE — drone havada asılı kaldığında ardışık kareler neredeyse
     aynıdır. Algısal hash ile yakın kopyalar elenir.

Kareler `doku_bankasi/zemin/` içine `saha_*.png` adıyla yazılır; 51_sentetik_arena
zaten oradan okuyor, ek bir değişiklik gerekmez. Dağınıklık süzgeci (TEMIZ_ORAN)
kalabalık kareleri kendiliğinden eler.

Kullanım:
  venv\\Scripts\\python.exe 53_drone_kare.py --girdi O:\\...\\ucus.mp4
  venv\\Scripts\\python.exe 53_drone_kare.py --girdi <klasör> --aralik 2.5 --kenar 96
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

BANKA = Path(__file__).parent / "doku_bankasi" / "zemin"
VIDEO_UZANTI = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
GORUNTU_UZANTI = {".jpg", ".jpeg", ".png", ".bmp"}


def ahash(im, n=12):
    """Algısal hash — neredeyse aynı kareleri yakalamak için."""
    g = cv2.resize(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), (n, n),
                   interpolation=cv2.INTER_AREA)
    return (g > g.mean()).flatten()


def farkli_mi(h, gecmis, esik=0.12):
    """Hamming mesafesi eşiğin altındaysa yakın kopya say."""
    for g in gecmis:
        if np.count_nonzero(h != g) / h.size < esik:
            return False
    return True


def kare_kaydet(im, ad, kenar, sayac):
    """Karenin ortasından en büyük KARE yamayı al, bankaya yaz."""
    h, w = im.shape[:2]
    k = min(h, w)
    y, x = (h - k) // 2, (w - k) // 2
    yama = im[y:y + k, x:x + k]
    if k < kenar:
        return False
    # 512'den büyükse küçült: doku yaması olarak kullanılacak, dev olması gereksiz
    if k > 512:
        yama = cv2.resize(yama, (512, 512), interpolation=cv2.INTER_AREA)
    hedef = BANKA / f"saha_{ad}_{sayac:05d}.png"
    gec = hedef.with_name(f".{hedef.stem}.tmp{hedef.suffix}")
    if not cv2.imwrite(str(gec), yama):
        return False
    gec.replace(hedef)
    return True


def videodan(yol: Path, aralik, kenar, en_fazla, esik):
    cap = cv2.VideoCapture(str(yol))
    if not cap.isOpened():
        print(f"  açılamadı: {yol.name}")
        return 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    toplam = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    adim = max(1, int(round(fps * aralik)))
    print(f"  {yol.name}: {fps:.1f} fps · {toplam} kare · her {adim}. kare alınacak")

    gecmis, yazilan, i = [], 0, 0
    while yazilan < en_fazla:
        ok = cap.grab()
        if not ok:
            break
        if i % adim == 0:
            ok, im = cap.retrieve()
            if ok and im is not None:
                h = ahash(im)
                if farkli_mi(h, gecmis, esik):
                    if kare_kaydet(im, yol.stem, kenar, yazilan):
                        gecmis.append(h)
                        yazilan += 1
        i += 1
    cap.release()
    print(f"  → {yazilan} kare yazıldı ({i} kare tarandı, yakın kopyalar elendi)")
    return yazilan


def klasorden(yol: Path, kenar, en_fazla, esik):
    gecmis, yazilan = [], 0
    dosyalar = sorted(p for p in yol.iterdir() if p.suffix.lower() in GORUNTU_UZANTI)
    for p in dosyalar:
        if yazilan >= en_fazla:
            break
        im = cv2.imread(str(p))
        if im is None:
            continue
        h = ahash(im)
        if farkli_mi(h, gecmis, esik) and kare_kaydet(im, yol.name, kenar, yazilan):
            gecmis.append(h)
            yazilan += 1
    print(f"  → {yazilan} kare yazıldı ({len(dosyalar)} dosya tarandı)")
    return yazilan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", required=True, help="video dosyası veya görüntü klasörü")
    ap.add_argument("--aralik", type=float, default=2.5,
                    help="videodan kaç saniyede bir kare alınsın (varsayılan 2,5)")
    ap.add_argument("--kenar", type=int, default=96, help="en küçük kabul edilen kenar")
    ap.add_argument("--en-fazla", type=int, default=400,
                    help="kaynak başına yazılacak azami kare — aşırı örneklemeyi engeller")
    ap.add_argument("--benzerlik", type=float, default=0.12,
                    help="bu orandan az farklı kareler yakın kopya sayılır")
    ap.add_argument("--temizle", action="store_true",
                    help="önceki saha_* karelerini sil")
    args = ap.parse_args()

    BANKA.mkdir(parents=True, exist_ok=True)
    if args.temizle:
        n = 0
        for p in BANKA.glob("saha_*.png"):
            p.unlink()
            n += 1
        print(f"{n} eski saha karesi silindi")

    girdi = Path(args.girdi)
    if not girdi.exists():
        raise SystemExit(f"girdi yok: {girdi}")

    kaynaklar = []
    if girdi.is_file():
        kaynaklar = [girdi]
    else:
        kaynaklar = [p for p in sorted(girdi.iterdir())
                     if p.suffix.lower() in VIDEO_UZANTI]
        if not kaynaklar:
            kaynaklar = [girdi]          # düz görüntü klasörü

    toplam = 0
    for k in kaynaklar:
        print(f"\n{k}")
        if k.is_dir():
            toplam += klasorden(k, args.kenar, args.en_fazla, args.benzerlik)
        else:
            toplam += videodan(k, args.aralik, args.kenar, args.en_fazla,
                               args.benzerlik)

    mevcut = len(list(BANKA.glob("*.png")))
    saha = len(list(BANKA.glob("saha_*.png")))
    print(f"\n{'=' * 62}")
    print(f"ZEMİN BANKASI: {mevcut} yama · bunların {saha}'ü GERÇEK SAHA karesi")
    print(f"Klasör: {BANKA}")
    print("""
SIRADAKİ ADIM:
  venv\\Scripts\\python.exe 51_sentetik_arena.py --adet 3300 --val-orani 0.09
  → üreteç zemini artık gerçek saha karelerinden de seçecek; moloz ve şeritler
    yine üreteçten geldiği için MASKE KUSURSUZ kalır.

UNUTMA: gerçek engelli kareleri EĞİTİME DEĞİL, elle etiketleyip TEST kümesine
koyun. Şu anki arena ölçümümüz n=2 ve YZ üretimi görüntülere dayanıyor; asıl
zayıf halka orası.""")


if __name__ == "__main__":
    main()

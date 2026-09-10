# HESAP (olcum degil): FDA 20x20 alaninda kare-goreli ucte-bir etiketi, HQ 6 mm, nadir, kare alana ortali.
import math
hfov = 2*math.degrees(math.atan(6.287/12.0))
for h in (30.0, 32.0):
    W = 2*h*math.tan(math.radians(hfov)/2)
    s = W/6.0  # orta ucte-bir yari genisligi
    print(f"h={h} m  kare genisligi {W:.2f} m  orta ucte-bir |x|<{s:.2f} m ; alan-goreli (20 m) |x|<{20/6:.2f} m")
    for aralik in (4.0, 5.0, 6.0, 6.67, 8.0):
        yollar = (-aralik, 0.0, aralik)
        kare = [1 if x < -s else (2 if x < s else 3) for x in yollar]
        alan = [1 if x < -20/6 else (2 if x < 20/6 else 3) for x in yollar]
        print(f"   yol araligi {aralik:5.2f} m -> kare-goreli {kare}  alan-goreli {alan}")

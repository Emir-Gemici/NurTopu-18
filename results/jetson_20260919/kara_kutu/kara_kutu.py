#!/usr/bin/env python3
"""NAVITAS Jetson KARA KUTU (19 Eyl 2026, D-512): ani kapanmalari (guc kesintisi / asiri akim / isinma) yakalamak icin
0,5 s'de bir guc, alarm, sicaklik, yuk, bellek ve fan durumunu diske YAZAR ve HER SATIRI fsync'ler — ani kesintide son
satirlar kaybolmaz. Her acilista (crontab @reboot) yeni dosya: ~/kara_kutu/kutu_<acilis>.csv. Ucus yoluna DOKUNMAZ.
Okuma: kapanmadan sonra bir onceki dosyanin son satirlari = kesintiden hemen onceki durum."""
import glob, os, time
DIZIN = os.path.expanduser("~/kara_kutu"); ARALIK_S = 0.5; AZAMI_B = 50 * 1024 * 1024
def oku(yol, v=None):
    try:
        with open(yol) as f: return f.read().strip()
    except Exception: return v
INA = (glob.glob("/sys/bus/i2c/drivers/ina3221/*/hwmon/hwmon*") or [None])[0]
GPU = next((p for p in ("/sys/devices/platform/bus@0/17000000.gpu/load", "/sys/devices/platform/bus@0/gpu.0/load") if os.path.exists(p)), None)
FAN_RPM = (glob.glob("/sys/class/hwmon/*/rpm") or [None])[0]
FAN_PWM = (glob.glob("/sys/devices/platform/pwm-fan/hwmon/hwmon*/pwm1") or [None])[0]
ISI = {oku(z + "/type"): z + "/temp" for z in glob.glob("/sys/class/thermal/thermal_zone*")}
def cpu_orneği():
    p = open("/proc/stat").readline().split()[1:]; v = list(map(int, p)); return sum(v), v[3] + v[4]
def mem_avail():
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable"): return int(l.split()[1]) // 1024
def main():
    os.makedirs(DIZIN, exist_ok=True)
    acilis = (oku("/proc/sys/kernel/random/boot_id", "x") or "x")[:8]
    yol = os.path.join(DIZIN, f"kutu_{time.strftime('%Y%m%d_%H%M%S')}_{acilis}.csv")
    f = open(yol, "a", buffering=1)
    f.write("zaman,uptime_s,vin_mV,iin_mA,pin_mW,icpugpu_mA,isoc_mA,akim_alarm,cpu_C,gpu_C,cpu_yuk,gpu_yuk,bellek_MB,fan_rpm,fan_pwm\n"); f.flush(); os.fsync(f.fileno())
    onceki = cpu_orneği()
    while True:
        time.sleep(ARALIK_S)
        try:
            vin = int(oku(f"{INA}/in1_input", 0) or 0) if INA else 0
            i1, i2, i3 = (int(oku(f"{INA}/curr{k}_input", 0) or 0) if INA else 0 for k in (1, 2, 3))
            alarm = "".join(oku(f"{INA}/curr{k}_{t}_alarm", "0") for k in (1, 2, 3) for t in ("max", "crit")) if INA else ""
            simdi = cpu_orneği(); dt = simdi[0] - onceki[0]; yuk = 100.0 * (1 - (simdi[1] - onceki[1]) / dt) if dt else 0.0; onceki = simdi
            cpu = int(oku(ISI.get("cpu-thermal", ""), 0) or 0) / 1000; gpu = int(oku(ISI.get("gpu-thermal", ""), 0) or 0) / 1000
            gy = int(oku(GPU, 0) or 0) / 10 if GPU else -1
            satir = (f"{time.strftime('%H:%M:%S')}.{int(time.time()*10)%10},{oku('/proc/uptime','0 0').split()[0]},{vin},{i1},{vin*i1//1000},{i2},{i3},{alarm},"
                     f"{cpu:.1f},{gpu:.1f},{yuk:.0f},{gy:.0f},{mem_avail()},{oku(FAN_RPM,'')},{oku(FAN_PWM,'')}\n")
            f.write(satir); f.flush(); os.fsync(f.fileno())
            if f.tell() > AZAMI_B: f.close(); f = open(yol, "w", buffering=1)
        except Exception as e:
            f.write(f"# HATA {type(e).__name__}: {e}\n"); f.flush()
if __name__ == "__main__":
    main()

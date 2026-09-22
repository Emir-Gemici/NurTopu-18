"""NEDEN: Canlı tanı, eski kayıt ve algı sonucunu birbirine karıştırmadan göster."""
import json
import math
import time
from collections import deque
from pathlib import Path

TANI_TAZELIK_S = 5.0  # Yalnız ekran teşhisi; uçuş/failsafe eşiği değildir.
DOSYA_TAVANI = 1024 * 1024
ARSIV_SATIR_TAVANI = 2000


def sayi(value):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value))


def snapshot_oku(path):
    with Path(path).open('rb') as stream:
        data = stream.read(DOSYA_TAVANI + 1)
    if len(data) > DOSYA_TAVANI:
        raise ValueError('Tanı dosyası boyut sınırını aşıyor')
    value = json.loads(data)
    if not isinstance(value, dict) or value.get('v') != 1:
        raise ValueError('Tanı dosyası biçimi geçersiz')
    remote=value.get('remote')
    if remote is not None:
        if not isinstance(remote,dict):raise ValueError('Uzak tanı nesnesi geçersiz')
        health=remote.get('health')
        if health is not None and not isinstance(health,dict):raise ValueError('Sağlık kaydı geçersiz')
        if health and not isinstance(health.get('nedenler',[]),list):raise ValueError('Sağlık nedenleri geçersiz')
        if not isinstance(remote.get('journal',[]),list):raise ValueError('Günlük listesi geçersiz')
    return value


def jetson_ozeti(snapshot, mono=None, wall=None):
    mono = time.monotonic() if mono is None else mono
    wall = time.time() if wall is None else wall
    empty = dict(jetson='VERİ YOK', model='BİLİNMİYOR', kamera='BİLİNMİYOR',
                 karar='—', detay='Jetson tanı aktarımı bağlı değil.', yas=None)
    if not isinstance(snapshot, dict):
        return empty
    mt, wt = snapshot.get('pc_mono'), snapshot.get('pc_unix')
    if not sayi(mt) or not sayi(wt):
        return dict(empty, jetson='GEÇERSİZ VERİ', detay='Alım zamanı doğrulanamadı.')
    ages = (mono - mt, wall - wt)
    if min(ages) < 0 or max(ages) > TANI_TAZELIK_S:
        return dict(empty, jetson='VERİ BAYAT', yas=max(ages),
                    detay='Yeni Jetson tanısı gelmiyor. Güç kesilmesi nedeni kanıtlanmış değil.')
    if snapshot.get('ok') is not True:
        return dict(empty, jetson='BAĞLANTI HATASI', yas=max(ages),
                    detay=str(snapshot.get('error', 'Jetson okunamadı'))[:400])
    remote = snapshot.get('remote')
    if not isinstance(remote, dict):
        return dict(empty, jetson='YANIT EKSİK')
    health = remote.get('health') or {}
    if not isinstance(health, dict):
        health = {}
    remote_mono = remote.get('mono')
    kontrol = health.get('kontrol_mono')
    watcher_ok = (sayi(remote_mono) and sayi(kontrol)
                  and 0 <= remote_mono - kontrol <= TANI_TAZELIK_S)
    if not watcher_ok:
        return dict(empty, jetson='YANIT VAR', yas=max(ages),
                    detay='Sağlık gözetmeni kaydı yok/bayat; model sağlıklı sayılamaz.')
    elapsed = remote_mono - kontrol + max(ages)
    model_age = health.get('model_yasi_s')
    camera_age = health.get('kamera_yasi_s')
    reasons = health.get('nedenler') or []
    model_ok = (sayi(model_age) and 0 <= model_age + elapsed <= TANI_TAZELIK_S
                and 'MODEL_SONUCU_BAYAT_VEYA_YOK' not in reasons)
    camera_ok = (sayi(camera_age) and 0 <= camera_age + elapsed <= TANI_TAZELIK_S
                 and 'KAMERA_BAYAT_VEYA_YOK' not in reasons)
    return dict(jetson='YANIT VAR', model='KARE İŞLİYOR' if model_ok else 'YOK / BAYAT',
                kamera='KARE GELİYOR' if camera_ok else 'YOK / BAYAT',
                karar=str(health.get('karar_reddi') or 'Ret bildirilmedi'), yas=max(ages),
                detay='boot={} · PID={} · kare={} · Algı sonucu bağlantı sağlığından ayrıdır.'.format(
                    health.get('boot', '?'), health.get('pid', '?'), health.get('son_kare', '?')))


def pixhawk_ozeti(telemetry, hb_age, threshold, *, demo=False, mode=None):
    telemetry = telemetry if isinstance(telemetry, dict) else {}
    fresh = sayi(hb_age) and 0 <= hb_age < threshold
    live = fresh and telemetry.get('pixhawk_canli') is True
    return dict(durum=('CANLI TELEMETRİ' if live else 'BAĞLI DEĞİL / VERİ YOK-BAYAT'),
                kaynak='DEMO — gerçek araç değil' if demo else 'YKİ mevcut telemetri hattı',
                canli=live, yas=hb_age if sayi(hb_age) else None,
                mod=(mode or telemetry.get('mod') or '—') if live else '—',
                armed=telemetry.get('armed') if live else None,
                bat=telemetry.get('bat') if live else None,
                bat_yuzde=telemetry.get('bat_yuzde') if live else None)


def arsiv_oku(path, stop=None, limit=ARSIV_SATIR_TAVANI):
    """Yalnız mevcut dosya açar; seri port/UDP/araç bağlantısı oluşturmaz."""
    path = Path(path)
    if not path.is_file():
        raise ValueError('Mevcut bir kayıt dosyası seçilmeli')
    rows = deque(maxlen=limit)
    bad = 0
    scanned = 0
    def cancelled():
        return stop is not None and stop.is_set()
    if path.suffix.lower() in ('.bin', '.tlog'):
        from pymavlink import DFReader, mavutil
        # Dosya varlığı yukarıda zorunlu. Live mavlink bağlantısı kullanılmaz.
        reader = (DFReader.DFReader_binary(str(path)) if path.suffix.lower() == '.bin'
                  else mavutil.mavlogfile(str(path), robust_parsing=True))
        selected = {'MSG', 'ERR', 'EV', 'POWR', 'BAT', 'MODE', 'STATUSTEXT',
                    'HEARTBEAT', 'SYS_STATUS', 'BATTERY_STATUS', 'POWER_STATUS'}
        try:
            while not cancelled():
                msg = reader.recv_msg()
                if msg is None:
                    break
                scanned += 1
                if msg.get_type() in selected:
                    rows.append(dict(arsiv=True, kaynak='Pixhawk', dosya=path.name, veri=msg.to_dict()))
        finally:
            reader.close()
    else:
        with path.open('rb') as stream:
            # Büyük metin günlüklerini UI belleğine bütünüyle yükleme.
            size=path.stat().st_size
            start=max(0, size-8*1024*1024)
            stream.seek(start)
            if start: stream.readline()
            while not cancelled():
                line=stream.readline(65537)
                if not line: break
                if len(line)>65536:
                    bad+=1
                    while line and not line.endswith(b'\n'):
                        line=stream.readline(65537)
                    continue
                scanned+=1
                text=line.decode('utf-8',errors='replace').strip()
                if not text: continue
                try: value=json.loads(text)
                except ValueError:
                    value={'metin':text}
                    if path.suffix.lower()=='.jsonl': bad+=1
                source='Arşiv'
                if isinstance(value,dict):
                    event=str(value.get('olay',''))
                    source=('Jetson' if event.startswith('JETSON_') or event=='KARE'
                            else 'YKİ' if event else 'Arşiv')
                rows.append(dict(arsiv=True,kaynak=source,dosya=path.name,veri=value))
    return dict(rows=list(rows),scanned=scanned,bad=bad,cancelled=cancelled(),
                note='ARŞİV — canlı bağlantı veya güncel sağlık kanıtı değildir.')


def filtrele(rows, query='', source='Tümü'):
    query=query.casefold().strip()
    return [row for row in rows if (source=='Tümü' or row.get('kaynak')==source)
            and (not query or query in json.dumps(row,ensure_ascii=False).casefold())]


def satir_metni(row):
    prefix='ARŞİV · ' if row.get('arsiv') else ''
    when=row.get('ts','')
    source=row.get('kaynak','?')
    if 'mesaj' in row:
        detail=str(row['mesaj'])
        if row.get('journal_cursor'):
            detail='Cihaz günlüğü · '+str(row.get('unit') or '')+' · '+detail
    else:
        data=row.get('veri')
        if isinstance(data,dict):
            when=data.get('ts',data.get('TimeUS',when))
            kind=data.get('olay',data.get('mavpackettype',''))
            fields={key:value for key,value in data.items() if key not in ('ts','olay','mavpackettype')}
            detail=str(kind)+' · '+' · '.join(str(key)+'='+str(value) for key,value in fields.items())
        else:detail=str(data)
    return '{}[{}] {} | {}'.format(prefix,when,source,detail.replace('\n',' | ')[:4000])

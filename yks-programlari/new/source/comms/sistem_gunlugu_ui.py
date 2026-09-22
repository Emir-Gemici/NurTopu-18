"""NEDEN: NEW YKİ içinde Jetson/Pixhawk tanılarını ve arşivleri ayrı göster."""
import json
import queue
import threading
import time
import tkinter as tk
from collections import deque
from pathlib import Path
from tkinter import filedialog, ttk

from sistem_gunlugu import snapshot_oku, jetson_ozeti, pixhawk_ozeti, arsiv_oku, filtrele, satir_metni


class SistemGunlugu:
    def __init__(self, app, path, tazelik):
        self.app=app
        self.path=Path(path)
        self.tazelik=tazelik
        self.rows=deque(maxlen=2000)
        self.archive=[]
        self.archive_mode=False
        self.queue=queue.Queue(maxsize=4)
        self.stop=threading.Event()
        self.seen=set()
        self.last_states=None
        self.last_sig=None
        self.snapshot=None
        self.closed=False
        self.after_id=None
        self.worker=None
        self.win=tk.Toplevel(app.kok)
        self.win.title('NAVITAS YKI NEW — Sistem günlükleri')
        self.win.geometry('1100x730')
        self.win.minsize(780,540)
        self.win.protocol('WM_DELETE_WINDOW',self.kapat)
        self.bg='#111923'; self.fg='#e7edf5'
        self.win.configure(bg=self.bg)
        tk.Label(self.win,text='NEW · SİSTEM GÜNLÜKLERİ',bg=self.bg,fg='#5eb9ed',
                 font=('Segoe UI',17,'bold')).pack(anchor='w',padx=16,pady=(12,4))
        tk.Label(self.win,text='Günlükler ve bağlantı teşhisi · Araç komutu üretmez',
                 bg=self.bg,fg='#a4b3c5',font=('Segoe UI',10)).pack(anchor='w',padx=16)
        cards=tk.Frame(self.win,bg=self.bg); cards.pack(fill='x',padx=16,pady=10)
        self.jetson=tk.StringVar();self.pixhawk=tk.StringVar()
        for variable,title in ((self.jetson,'JETSON'),(self.pixhawk,'PIXHAWK')):
            box=tk.LabelFrame(cards,text=title,bg='#1c2936',fg='#84c9f1',padx=12,pady=10)
            box.pack(side='left',fill='both',expand=True,padx=(0,8))
            tk.Label(box,textvariable=variable,bg='#1c2936',fg=self.fg,justify='left',
                     anchor='nw',wraplength=490,font=('Segoe UI',10)).pack(fill='both',expand=True)
        bar=tk.Frame(self.win,bg=self.bg);bar.pack(fill='x',padx=16)
        self.query=tk.StringVar()
        tk.Label(bar,text='Ara:',bg=self.bg,fg=self.fg).pack(side='left')
        tk.Entry(bar,textvariable=self.query,width=25).pack(side='left',padx=5)
        self.query.trace_add('write',lambda *a:self.render())
        self.source=tk.StringVar(value='Tümü')
        selector=ttk.Combobox(bar,textvariable=self.source,values=('Tümü','Jetson','Pixhawk','YKİ','Arşiv'),
                              state='readonly',width=10)
        selector.pack(side='left',padx=5);selector.bind('<<ComboboxSelected>>',lambda e:self.render())
        self.load_button=tk.Button(bar,text='Geçmiş kayıt aç',command=self.open_archive)
        self.load_button.pack(side='left',padx=5)
        tk.Button(bar,text='Görüneni dışarı aktar',command=self.export).pack(side='left',padx=5)
        tk.Button(bar,text='Canlıya dön',command=self.live).pack(side='left',padx=5)
        self.follow=tk.BooleanVar(value=True)
        self.raw=tk.BooleanVar(value=False)
        options=tk.Frame(self.win,bg=self.bg);options.pack(fill='x',padx=16,pady=(5,0))
        for label,variable in (('Otomatik kaydır',self.follow),('Ham alanları göster',self.raw)):
            tk.Checkbutton(options,text=label,variable=variable,command=self.render,bg=self.bg,
                           fg=self.fg,selectcolor='#243647',activebackground=self.bg).pack(side='left',padx=(0,12))
        self.note=tk.StringVar(value='CANLI TANI · Arşiv yüklenmedi')
        tk.Label(self.win,textvariable=self.note,bg=self.bg,fg='#ffca73',anchor='w',
                 wraplength=1000).pack(fill='x',padx=16,pady=8)
        frame=tk.Frame(self.win,bg=self.bg);frame.pack(fill='both',expand=True,padx=16,pady=(0,8))
        scroll=tk.Scrollbar(frame);scroll.pack(side='right',fill='y')
        self.text=tk.Text(frame,bg='#0d131b',fg=self.fg,font=('Consolas',10),wrap='word',
                          state='disabled',yscrollcommand=scroll.set)
        self.text.pack(fill='both',expand=True);scroll.config(command=self.text.yview)
        self.footer=tk.StringVar(value='Jetson aktarımı: '+str(self.path))
        tk.Label(self.win,textvariable=self.footer,bg=self.bg,fg='#a4b3c5',anchor='w',
                 wraplength=1000).pack(fill='x',padx=16,pady=(0,10))
        log=getattr(app,'hakem_kaydi',None)
        root=Path(log.yol).parent if log is not None else Path(__file__).resolve().parents[1]/'results'/'yki_new_tani'
        root.mkdir(parents=True,exist_ok=True)
        self.event_path=root/('sistem_gunlugu_'+str(time.time_ns())+'.jsonl')
        self.log=self.event_path.open('x',encoding='utf-8')
        self.add('YKİ','Pencere açıldı; tanı kaydı: '+str(self.event_path))
        self.tick()

    def add(self,source,message,**extra):
        row=dict(ts=time.strftime('%Y-%m-%d %H:%M:%S'),pc_mono=time.monotonic(),
                 kaynak=source,mesaj=message,**extra)
        self.rows.append(row)
        try:
            self.log.write(json.dumps(row,ensure_ascii=False,default=str)+'\n');self.log.flush()
        except OSError as exc:
            self.footer.set('Kayıt yazılamıyor: '+str(exc))

    def tick(self):
        if self.closed:return
        try:
            stat=self.path.stat();sig=(stat.st_mtime_ns,stat.st_size)
            if sig!=self.last_sig:
                self.snapshot=snapshot_oku(self.path);self.last_sig=sig
            error=None
        except (OSError,ValueError) as exc:
            self.snapshot=None;error=str(exc)
        now=time.monotonic()
        j=jetson_ozeti(self.snapshot,now)
        hb=getattr(self.app,'son_hb',{}).get('iha')
        p=pixhawk_ozeti(getattr(self.app,'tel',{}).get('iha'),None if hb is None else now-hb,
                       self.tazelik,demo=bool(getattr(self.app,'demo',False)),
                       mode=getattr(self.app,'mod',{}).get('iha'))
        self.jetson.set('{}\nModel: {} · Kamera: {}\nAlgı: {}\n{}'.format(
            j['jetson'],j['model'],j['kamera'],j['karar'],j['detay']))
        armed={True:'ARMED',False:'DISARMED',None:'—'}.get(p['armed'],'—')
        self.pixhawk.set('{}\n{}\nMod: {} · {}\nPil: {} V · {} %'.format(
            p['durum'],p['kaynak'],p['mod'],armed,
            p['bat'] if p['bat'] is not None else '—',
            p['bat_yuzde'] if p['bat_yuzde'] is not None else '—'))
        states=(j['jetson'],j['model'],j['kamera'],j['karar'],p['durum'],p['mod'],armed,p['kaynak'])
        if states!=self.last_states:
            self.add('Jetson',self.jetson.get().replace('\n',' | '))
            self.add('Pixhawk',self.pixhawk.get().replace('\n',' | '))
            self.last_states=states
        if self.snapshot and self.snapshot.get('ok'):
            events=(self.snapshot.get('remote') or {}).get('journal',[])
            for event in events[-100:]:
                if not isinstance(event,dict):continue
                ident=(event.get('_BOOT_ID'),event.get('__CURSOR'))
                if not ident[1] or ident in self.seen:continue
                self.seen.add(ident)
                self.add('Jetson',str(event.get('MESSAGE',''))[:4000],
                         journal_cursor=ident[1],boot=ident[0],
                         remote_monotonic_us=event.get('__MONOTONIC_TIMESTAMP'),
                         unit=event.get('_SYSTEMD_UNIT'),remote_timestamp=event.get('__REALTIME_TIMESTAMP'))
            if len(self.seen)>5000:self.seen=set(list(self.seen)[-2000:])
        try:
            outcome=self.queue.get_nowait()
        except queue.Empty:
            outcome=None
        if outcome:
            self.load_button.config(state='normal')
            if 'error' in outcome:self.note.set('Arşiv okunamadı: '+outcome['error'])
            else:
                self.archive=outcome['rows'];self.archive_mode=True;self.source.set('Tümü')
                self.note.set('{} Okunan: {}, gösterilen son kayıt: {}, bozuk satır: {}'.format(
                    outcome['note'],outcome['scanned'],len(self.archive),outcome['bad']))
        if error:self.footer.set('Jetson tanı kaynağı bekleniyor: '+str(self.path))
        self.render()
        self.after_id=self.win.after(1000,self.tick)

    def visible(self):
        return filtrele(self.archive if self.archive_mode else list(self.rows),self.query.get(),self.source.get())

    def render(self):
        if self.closed:return
        text='\n'.join(json.dumps(row,ensure_ascii=False,default=str) if self.raw.get()
                       else satir_metni(row) for row in self.visible())
        if text==getattr(self,'last_text',None):return
        self.last_text=text
        position=self.text.yview()[0]
        self.text.config(state='normal');self.text.delete('1.0','end')
        self.text.insert('1.0',text);self.text.config(state='disabled')
        if self.follow.get():self.text.see('end')
        else:self.text.yview_moveto(position)

    def open_archive(self):
        if self.worker and self.worker.is_alive():return
        path=filedialog.askopenfilename(parent=self.win,title='Geçmiş kayıt — canlı değildir',
            filetypes=[('Günlükler','*.jsonl *.log *.txt *.bin *.tlog'),('Tüm dosyalar','*.*')])
        if not path:return
        self.note.set('ARŞİV okunuyor… Canlı bağlantı durumu üstte ayrı kalır.')
        self.load_button.config(state='disabled')
        def work():
            try: outcome=arsiv_oku(path,self.stop)
            except Exception as exc:outcome={'error':str(exc)}
            if not self.stop.is_set():self.queue.put_nowait(outcome)
        self.worker=threading.Thread(target=work,daemon=True);self.worker.start()

    def live(self):
        self.archive=[];self.archive_mode=False;self.note.set('CANLI TANI · Yerel alım saati; Jetson saati farklı olabilir.')
        self.render()

    def export(self):
        path=filedialog.asksaveasfilename(parent=self.win,defaultextension='.jsonl',
             initialfile='YKI_NEW_sistem_gunlugu.jsonl',filetypes=[('JSONL','*.jsonl')])
        if not path:return
        try:
            with Path(path).open('w',encoding='utf-8') as stream:
                for row in self.visible():stream.write(json.dumps(row,ensure_ascii=False,default=str)+'\n')
            self.note.set('Dışarı aktarıldı: '+path)
        except OSError as exc:self.note.set('Dışarı aktarılamadı: '+str(exc))

    def kapat(self):
        if self.closed:return
        self.closed=True;self.stop.set()
        if self.after_id:
            try:self.win.after_cancel(self.after_id)
            except tk.TclError:pass
        self.log.close();self.win.destroy()

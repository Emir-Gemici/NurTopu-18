#!/usr/bin/env python3
"""
Navitas — Harita Stüdyosu.

Normal bir masaüstü programı gibi: açılışta karşılama ekranı, oradan "Yeni Harita
Oluştur" / "Geçmiş Haritalar" ile stüdyo ekranına geçilir; harita oluştur (seviye/
harita no/seed/layout), geçmişte oluşturduğun haritaları küçük-resimli galeride gör,
seçtiğin haritayla tek tuşla GERÇEK Gazebo GUI penceresini (host ekranında, podman
üzerinden) başlat.

Çalıştırma:
    .venv/bin/python simulation/harita_studyo.py
ya da (kurulan kısayollardan biriyle) çift tıkla.
"""
import json
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk

HERE = Path(__file__).resolve().parent           # simulation/
REPO = HERE.parent
SCRIPTS = HERE / "scripts"
sys.path.insert(0, str(SCRIPTS))

import arena                                       # noqa: E402
from world_generator import build_world             # noqa: E402
from harita_render import render_harita_png          # noqa: E402

HIST = HERE / "harita_gecmisi"
HIST.mkdir(exist_ok=True)
ICON_PNG = Path.home() / ".local/share/icons/navitas/harita_studyo.png"

BG = "#0f1419"; PANEL = "#1a2129"; CIZGI = "#2a3441"
METIN = "#e8edf2"; SOLUK = "#8b98a5"
YESIL = "#2ecc71"; SARI = "#f0a437"; KIRMIZI = "#e15241"; MAVI = "#4aa3df"

SCENARIOS = list(arena.SCENARIOS)


def _yeni_id():
    return time.strftime("%Y%m%d_%H%M%S")


def olustur_harita(senaryo, harita_no, seed, layout):
    """Dünya + önizleme PNG + meta üretir, harita_gecmisi/<id>/ altına kaydeder."""
    eid = _yeni_id()
    edir = HIST / eid
    edir.mkdir(parents=True, exist_ok=True)
    world_path = edir / "dunya.world"
    png_path = edir / "onizleme.png"

    world_str, fz = build_world(seed, senaryo, record=True, road=None,
                                 layout=layout, harita_id=harita_no)
    world_path.write_text(world_str, encoding="utf-8")
    info = render_harita_png(senaryo, harita_no, seed, str(png_path))

    meta = {
        "id": eid, "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "senaryo": senaryo, "harita_no": harita_no, "seed": seed, "layout": layout,
        "acik_yol": info["open_label"],
        "world": str(world_path), "png": str(png_path),
    }
    (edir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    return meta


def gecmis_yukle():
    out = []
    for d in sorted(HIST.iterdir(), reverse=True):
        mp = d / "meta.json"
        if mp.exists():
            try:
                out.append(json.loads(mp.read_text(encoding="utf-8")))
            except Exception:
                pass
    return out


class Studyo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Navitas — Harita Stüdyosu")
        self.geometry("1180x760")
        self.configure(bg=BG)
        if ICON_PNG.exists():
            try:
                self._app_icon = tk.PhotoImage(file=str(ICON_PNG))
                self.iconphoto(True, self._app_icon)
            except Exception:
                pass

        self.baslik_f = tkfont.Font(family="DejaVu Sans", size=13, weight="bold")
        self.baslik_buyuk_f = tkfont.Font(family="DejaVu Sans", size=22, weight="bold")
        self.altbaslik_f = tkfont.Font(family="DejaVu Sans", size=11)
        self.normal_f = tkfont.Font(family="DejaVu Sans", size=10)
        self.kucuk_f = tkfont.Font(family="DejaVu Sans", size=8)

        self.sim_proc = None
        self.sim_name = None
        self.secili = None          # şu an önizlemede gösterilen meta dict
        self._thumb_refs = []       # PhotoImage referansları (GC engellemek için)
        self._buyuk_ref = None
        self._ana_ref = None

        self.kok = tk.Frame(self, bg=BG)
        self.kok.pack(fill="both", expand=True)

        self.sayfa_ana = tk.Frame(self.kok, bg=BG)
        self.sayfa_studyo = tk.Frame(self.kok, bg=BG)

        self._ui_kur_ana()
        self._ui_kur_studyo()
        self._galeri_yenile()
        self._ana_sayfa_goster()

    # ── KARŞILAMA EKRANI ────────────────────────────────────────────────────
    def _ui_kur_ana(self):
        s = self.sayfa_ana
        orta = tk.Frame(s, bg=BG)
        orta.place(relx=0.5, rely=0.42, anchor="center")

        tk.Label(orta, text="🗺  Navitas Harita Stüdyosu", font=self.baslik_buyuk_f,
                 bg=BG, fg=METIN).pack(pady=(0, 6))
        tk.Label(orta, text="Görev haritası oluştur, geçmişini gör, gerçek Gazebo "
                            "simülasyonunu başlat.",
                 font=self.altbaslik_f, bg=BG, fg=SOLUK).pack(pady=(0, 26))

        kartlar = tk.Frame(orta, bg=BG)
        kartlar.pack()

        def kart(parent, emoji, baslik, aciklama, renk, komut):
            f = tk.Frame(parent, bg=PANEL, highlightbackground=CIZGI,
                         highlightthickness=1, width=250, height=150, cursor="hand2")
            f.pack_propagate(False)
            tk.Label(f, text=emoji, font=("DejaVu Sans", 28), bg=PANEL, fg=renk
                      ).pack(pady=(16, 4))
            tk.Label(f, text=baslik, font=self.baslik_f, bg=PANEL, fg=METIN).pack()
            tk.Label(f, text=aciklama, font=self.kucuk_f, bg=PANEL, fg=SOLUK,
                     wraplength=210, justify="center").pack(pady=(4, 0))
            for w in (f, *f.winfo_children()):
                w.bind("<Button-1>", lambda e: komut())
            return f

        kart(kartlar, "➕", "Yeni Harita Oluştur",
             "Seviye, harita no, seed seç ve oluştur", MAVI,
             lambda: self._studyo_goster("yeni")).grid(row=0, column=0, padx=10)
        kart(kartlar, "🗂", "Geçmiş Haritalar",
             "Daha önce oluşturduğun haritaların galerisi", SARI,
             lambda: self._studyo_goster("galeri")).grid(row=0, column=1, padx=10)

        self.ana_son_cerceve = tk.Frame(orta, bg=BG)
        self.ana_son_cerceve.pack(pady=(28, 0), fill="x")

    def _ana_ozet_yenile(self):
        for w in self.ana_son_cerceve.winfo_children():
            w.destroy()
        entries = gecmis_yukle()
        if not entries:
            tk.Label(self.ana_son_cerceve, text="Henüz harita yok — yukarıdan başla.",
                     bg=BG, fg=SOLUK, font=self.kucuk_f).pack()
            return
        son = entries[0]
        satir = tk.Frame(self.ana_son_cerceve, bg=PANEL, highlightbackground=CIZGI,
                         highlightthickness=1)
        satir.pack(fill="x", padx=4)
        try:
            from PIL import Image, ImageTk
            im = Image.open(son["png"]); im.thumbnail((70, 70))
            self._ana_ref = ImageTk.PhotoImage(im)
            tk.Label(satir, image=self._ana_ref, bg=PANEL).pack(side="left", padx=10, pady=8)
        except Exception:
            pass
        tk.Label(satir, bg=PANEL, fg=METIN, font=self.kucuk_f, justify="left",
                 text=f"Son harita: {son['harita_no']} · {son['senaryo']} · "
                      f"seed {son['seed']}\n{son['created_at']}"
                 ).pack(side="left", padx=6)
        tk.Button(satir, text="▶ Bununla Aç", bg=YESIL, fg="#0a0e12", relief="flat",
                  command=lambda: self._son_haritayla_ac(son)
                  ).pack(side="right", padx=10)

    def _son_haritayla_ac(self, meta):
        self._studyo_goster("galeri")
        self._sec(meta)
        self.nb.select(self.tab_onizle)

    def _ana_sayfa_goster(self):
        self.sayfa_studyo.pack_forget()
        self._ana_ozet_yenile()
        self.sayfa_ana.pack(fill="both", expand=True)

    def _studyo_goster(self, hedef="yeni"):
        self.sayfa_ana.pack_forget()
        self.sayfa_studyo.pack(fill="both", expand=True)
        if hedef == "galeri":
            self._galeri_yenile()
            self.nb.select(self.tab_galeri)
        else:
            self.nb.select(self.tab_onizle)

    # ── STÜDYO EKRANI (harita oluştur + galeri + sim) ──────────────────────
    def _ui_kur_studyo(self):
        s = self.sayfa_studyo
        sol = tk.Frame(s, bg=PANEL, width=260)
        sol.pack(side="left", fill="y")
        sol.pack_propagate(False)

        tk.Button(sol, text="⌂  Ana Sayfa", font=self.normal_f, bg=BG, fg=SOLUK,
                  relief="flat", anchor="w", command=self._ana_sayfa_goster
                  ).pack(fill="x", padx=14, pady=(14, 0))

        tk.Label(sol, text="Yeni Harita", font=self.baslik_f, bg=PANEL, fg=METIN
                 ).pack(anchor="w", padx=14, pady=(16, 8))

        def etiket(t):
            tk.Label(sol, text=t, font=self.normal_f, bg=PANEL, fg=SOLUK
                      ).pack(anchor="w", padx=14, pady=(8, 2))

        etiket("Seviye")
        self.v_senaryo = tk.StringVar(value="orta")
        ttk.Combobox(sol, textvariable=self.v_senaryo, values=SCENARIOS,
                     state="readonly").pack(fill="x", padx=14)

        etiket("Harita No (1-5)")
        self.v_harita = tk.IntVar(value=1)
        tk.Spinbox(sol, from_=1, to=arena.HARITA_N, textvariable=self.v_harita,
                   font=self.normal_f).pack(fill="x", padx=14)

        etiket("Seed")
        seed_f = tk.Frame(sol, bg=PANEL); seed_f.pack(fill="x", padx=14)
        self.v_seed = tk.IntVar(value=42)
        tk.Entry(seed_f, textvariable=self.v_seed, font=self.normal_f
                  ).pack(side="left", fill="x", expand=True)
        tk.Button(seed_f, text="🎲", command=self._rastgele_seed, width=3
                  ).pack(side="left", padx=(4, 0))

        etiket("Saha Düzeni")
        self.v_layout = tk.StringVar(value="field")
        lf = tk.Frame(sol, bg=PANEL); lf.pack(anchor="w", padx=10)
        for val, lbl in (("field", "moloz saha"), ("clean", "net koridor")):
            tk.Radiobutton(lf, text=lbl, value=val, variable=self.v_layout,
                           bg=PANEL, fg=METIN, selectcolor=BG,
                           activebackground=PANEL, font=self.kucuk_f
                           ).pack(anchor="w")

        tk.Button(sol, text="Harita Oluştur", font=self.normal_f, bg=MAVI, fg="#0a0e12",
                  activebackground=MAVI, relief="flat",
                  command=self._olustur_tikla).pack(fill="x", padx=14, pady=(14, 4))

        ttk.Separator(sol, orient="horizontal").pack(fill="x", padx=14, pady=14)

        tk.Label(sol, text="Simülasyon", font=self.baslik_f, bg=PANEL, fg=METIN
                 ).pack(anchor="w", padx=14, pady=(0, 8))
        self.btn_baslat = tk.Button(
            sol, text="▶  Bu Haritayla Başlat", font=self.normal_f, bg=YESIL,
            fg="#0a0e12", relief="flat", state="disabled", command=self._sim_baslat)
        self.btn_baslat.pack(fill="x", padx=14, pady=4)
        self.btn_durdur = tk.Button(
            sol, text="■  Durdur", font=self.normal_f, bg=KIRMIZI, fg="#0a0e12",
            relief="flat", state="disabled", command=self._sim_durdur)
        self.btn_durdur.pack(fill="x", padx=14, pady=4)

        self.durum = tk.StringVar(value="Hazır.")
        tk.Label(sol, textvariable=self.durum, font=self.kucuk_f, bg=PANEL, fg=SOLUK,
                 wraplength=230, justify="left").pack(anchor="w", padx=14, pady=(10, 10))

        # ── sağ: sekmeler ────────────────────────────────────────────────
        sag = tk.Frame(s, bg=BG)
        sag.pack(side="left", fill="both", expand=True)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=PANEL, foreground=METIN, padding=(14, 6))
        style.map("TNotebook.Tab", background=[("selected", BG)])

        self.nb = ttk.Notebook(sag)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_onizle = tk.Frame(self.nb, bg=BG)
        self.tab_galeri = tk.Frame(self.nb, bg=BG)
        self.nb.add(self.tab_onizle, text="Önizleme")
        self.nb.add(self.tab_galeri, text="Geçmiş Haritalar")

        self.onizle_img_lbl = tk.Label(self.tab_onizle, bg=BG)
        self.onizle_img_lbl.pack(pady=(20, 10))
        self.onizle_bilgi = tk.Label(self.tab_onizle, text="Henüz harita oluşturulmadı.",
                                      font=self.normal_f, bg=BG, fg=METIN, justify="left")
        self.onizle_bilgi.pack()

        gal_top = tk.Frame(self.tab_galeri, bg=BG)
        gal_top.pack(fill="x")
        tk.Button(gal_top, text="⟳ Yenile", command=self._galeri_yenile
                  ).pack(anchor="e", padx=6, pady=6)

        gal_wrap = tk.Frame(self.tab_galeri, bg=BG)
        gal_wrap.pack(fill="both", expand=True)
        self.gal_canvas = tk.Canvas(gal_wrap, bg=BG, highlightthickness=0)
        gal_scroll = ttk.Scrollbar(gal_wrap, orient="vertical", command=self.gal_canvas.yview)
        self.gal_grid = tk.Frame(self.gal_canvas, bg=BG)
        self.gal_grid.bind("<Configure>", lambda e: self.gal_canvas.configure(
            scrollregion=self.gal_canvas.bbox("all")))
        self.gal_canvas.create_window((0, 0), window=self.gal_grid, anchor="nw")
        self.gal_canvas.configure(yscrollcommand=gal_scroll.set)
        self.gal_canvas.pack(side="left", fill="both", expand=True)
        gal_scroll.pack(side="right", fill="y")

    # ── eylemler ────────────────────────────────────────────────────────────
    def _rastgele_seed(self):
        import random
        self.v_seed.set(random.randint(1, 999999))

    def _olustur_tikla(self):
        senaryo = self.v_senaryo.get()
        harita_no = int(self.v_harita.get())
        seed = int(self.v_seed.get())
        layout = self.v_layout.get()
        self.durum.set(f"Harita oluşturuluyor: {senaryo} / harita {harita_no} / seed {seed}...")
        self.update_idletasks()
        try:
            meta = olustur_harita(senaryo, harita_no, seed, layout)
        except Exception as e:
            messagebox.showerror("Hata", f"Harita oluşturulamadı:\n{e}")
            self.durum.set("Hata (yukarıdaki pencereye bak).")
            return
        self.durum.set("Harita oluşturuldu.")
        self._sec(meta)
        self._galeri_yenile()
        self.nb.select(self.tab_onizle)

    def _sec(self, meta):
        self.secili = meta
        try:
            from PIL import Image, ImageTk
            im = Image.open(meta["png"])
            im.thumbnail((520, 520))
            self._buyuk_ref = ImageTk.PhotoImage(im)
            self.onizle_img_lbl.configure(image=self._buyuk_ref)
        except Exception as e:
            self.onizle_img_lbl.configure(image="", text=f"(önizleme yüklenemedi: {e})")
        self.onizle_bilgi.configure(text=(
            f"Harita {meta['harita_no']}  ·  Seviye: {meta['senaryo']}  ·  "
            f"Seed: {meta['seed']}  ·  Düzen: {meta['layout']}\n"
            f"Açık yol (ground-truth, yalnız stüdyoda görünür): {meta['acik_yol']}\n"
            f"Oluşturulma: {meta['created_at']}"
        ))
        self.btn_baslat.configure(state="normal")

    def _galeri_yenile(self):
        for w in self.gal_grid.winfo_children():
            w.destroy()
        self._thumb_refs.clear()
        entries = gecmis_yukle()
        if not entries:
            tk.Label(self.gal_grid, text="Henüz hiç harita yok — 'Yeni Harita' ile oluştur.",
                      bg=BG, fg=SOLUK, font=self.normal_f).grid(row=0, column=0, padx=10, pady=10)
            return
        cols = 4
        from PIL import Image, ImageTk
        for i, meta in enumerate(entries):
            r, c = divmod(i, cols)
            cell = tk.Frame(self.gal_grid, bg=PANEL, highlightbackground=CIZGI,
                             highlightthickness=1)
            cell.grid(row=r, column=c, padx=8, pady=8)
            try:
                im = Image.open(meta["png"]); im.thumbnail((190, 190))
                ref = ImageTk.PhotoImage(im)
                self._thumb_refs.append(ref)
                btn_img = tk.Label(cell, image=ref, bg=PANEL, cursor="hand2")
            except Exception:
                btn_img = tk.Label(cell, text="(resim yok)", bg=PANEL, fg=SOLUK, width=24, height=10)
            btn_img.pack()
            btn_img.bind("<Button-1>", lambda e, m=meta: self._galeriden_sec(m))
            tk.Label(cell, bg=PANEL, fg=METIN, font=self.kucuk_f, justify="left",
                     text=f"harita {meta['harita_no']} · {meta['senaryo']} · seed {meta['seed']}\n"
                          f"{meta['created_at']}").pack(padx=6, pady=(0, 6))

    def _galeriden_sec(self, meta):
        self._sec(meta)
        self.nb.select(self.tab_onizle)

    def _sim_baslat(self):
        if not self.secili:
            return
        if self.sim_proc is not None:
            messagebox.showinfo("Bilgi", "Zaten bir simülasyon çalışıyor.")
            return
        world_abs = self.secili["world"]
        self.sim_name = f"navitas-canli-{self.secili['id']}"
        self.btn_baslat.configure(state="disabled")
        self.btn_durdur.configure(state="normal")
        self.durum.set(f"Gazebo açılıyor... ({self.sim_name})\n"
                        "(ilk çalıştırmada imaj derleniyorsa birkaç dakika sürebilir)")

        def _calistir():
            script = HERE / "docker" / "sim_baslat.sh"
            proc = subprocess.Popen(
                ["bash", str(script), world_abs, self.sim_name],
                cwd=str(HERE), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True)
            self.sim_proc = proc
            log_tail = []
            for line in proc.stdout:
                log_tail.append(line.rstrip())
                log_tail[:] = log_tail[-5:]
                self.after(0, lambda t="\n".join(log_tail): self.durum.set(t))
            proc.wait()
            self.after(0, self._sim_bitti)

        threading.Thread(target=_calistir, daemon=True).start()

    def _sim_bitti(self):
        self.sim_proc = None
        self.sim_name = None
        self.btn_baslat.configure(state="normal" if self.secili else "disabled")
        self.btn_durdur.configure(state="disabled")
        self.durum.set("Gazebo kapandı.")

    def _sim_durdur(self):
        if self.sim_name:
            self.durum.set("Durduruluyor...")
            threading.Thread(
                target=lambda: subprocess.run(["podman", "stop", "-t", "3", self.sim_name],
                                               capture_output=True),
                daemon=True).start()

    def destroy(self):
        if self.sim_name:
            try:
                subprocess.run(["podman", "stop", "-t", "3", self.sim_name],
                                capture_output=True, timeout=10)
            except Exception:
                pass
        super().destroy()


if __name__ == "__main__":
    app = Studyo()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()

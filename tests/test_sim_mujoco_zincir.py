"""T213-B · MuJoCo görev zinciri nöbetçileri (ON_KAYIT H1-K4/K5/K8, §5.3–5.6).

Kapılar:
  A  İKA kinematik sabitleri TEK KAYNAK (CONTRACTS §4 → karar_sozlesmesi): ika_nav,
     araclar, costmap_path_finder aynı adı OKUR, sayı yazmaz (AST) + mutasyon.
  B  MuJoCoSurucu `IkaSurucu` sözleşmesi: hiz_ver → teker hızı (rad/s = v/r), kırpma,
     ileri/dönüş işareti fizikte, temas sayacı, işaret boyaları çarpışmasız, saat.
  C  Sim saati enjeksiyonu: navigate 600 s deadline'ı ENJEKTE saatle tetiklenir,
     time.sleep HİÇ çağrılmaz (mutasyon: bekle yok sayılırsa sleep çağrılır).
  D  wait_open_route_from_comms enjekte saatle rota KABUL eder (alıcı aynı saat);
     mutasyon: alıcı duvar saatiyle kurulursa rota sessizce ATILIR.
  E  sim_hakem: sim=true alanı, loopback ACK akışı (K8 kanıtı → İHA ACK → IHA_LANDED
     @ t_inis → IKA_GO ACK); kanıt yoksa İHA'ya ACK gitmez; üretim kodunda import yok.
  F  gorev_kosumu duman (1 harita, gt, düşük çözünürlük, < 60 s) + metrik şeması +
     rota_bol (D-438 c: ham GT rotası sözleşmeyi geçmez, bölünmüşü geçer).
Portlar: yalnız ephemeral (127.0.0.1:0). GPU çıkarımı YOK (model yolu K3'te ölçülür).
"""
from __future__ import annotations

import ast
import contextlib
import io
import json
import math
import re
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _p in (str(KOK / "simulation" / "mujoco"), str(KOK / "simulation" / "scripts"),
           str(KOK / "codes"), str(KOK / "comms"), str(KOK / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mujoco                                   # noqa: E402
import arena                                    # noqa: E402
import arena_mjcf                               # noqa: E402
import araclar                                  # noqa: E402
import ika_nav                                  # noqa: E402
import ika_surucu                               # noqa: E402
import ika_receiver                             # noqa: E402
import karar_sozlesmesi as ks                   # noqa: E402
import costmap_path_finder as cpf               # noqa: E402
import gorev_kosumu                             # noqa: E402
import sim_hakem                                # noqa: E402
from ika_surucu_mujoco import MuJoCoSurucu, ISARET_GEOMLARI   # noqa: E402
from ika_receiver import IkaReceiver            # noqa: E402
from iha_sender import IhaSender, rota_geometrisini_dogrula   # noqa: E402
from link import UDPLink                        # noqa: E402
from protocol import FrameReader, encode, open_route, rota_yok   # noqa: E402

_GERCEK_UYKU = time.sleep      # yama ÖNCESİ yakalanır: test yardımcıları thread'e nefes verir


def _sar(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class SahteSaat:
    def __init__(self, t0=0.0):
        self.t = float(t0)
        self.bekle_n = 0

    def __call__(self):
        return self.t

    def bekle(self, dt):
        self.bekle_n += 1
        self.t += float(dt)


def _uyku_yasak(_s):
    raise AssertionError("time.sleep çağrıldı — sim saati enjeksiyonu delindi")


def _atama_isim(kaynak: str, hedef: str):
    """`hedef = <Name>` atamasının RHS adını döndür; sayı/başka ifade ise None."""
    agac = ast.parse(kaynak)
    for dugum in agac.body:
        if isinstance(dugum, ast.Assign) and len(dugum.targets) == 1 \
                and isinstance(dugum.targets[0], ast.Name) and dugum.targets[0].id == hedef:
            return dugum.value.id if isinstance(dugum.value, ast.Name) else None
    return None


# ── A · tek kaynak ─────────────────────────────────────────────────────────
class A_TekKaynakSabitler(unittest.TestCase):
    def test_degerler_ddr(self):
        self.assertEqual(ks.IKA_TEKER_YARICAP_M, 0.0625)
        self.assertEqual(ks.IKA_IZ_GENISLIGI_M, 0.39)
        self.assertEqual(ks.IKA_AZAMI_HIZ_MS, 1.3)
        # DDR: 200 rpm × π × Ø0,125 / 60 = 1,309 → 1,3
        self.assertAlmostEqual(200 * math.pi * 0.125 / 60, 1.309, places=3)
        self.assertLessEqual(ks.IKA_AZAMI_HIZ_MS, 200 * math.pi * 0.125 / 60)

    def test_ika_nav_ve_araclar_tek_kaynaktan_okur(self):
        self.assertEqual(ika_nav.MAX_SPEED, ks.IKA_AZAMI_HIZ_MS)
        self.assertEqual(araclar.IKA_VMAX_MS, ks.IKA_AZAMI_HIZ_MS)
        self.assertEqual(araclar.IKA_TEKER_R, ks.IKA_TEKER_YARICAP_M)
        self.assertEqual(araclar.IKA_IZ_M, ks.IKA_IZ_GENISLIGI_M)
        self.assertEqual(cpf.IKA_AZAMI_HIZ_MS, ks.IKA_AZAMI_HIZ_MS)
        self.assertEqual(cpf.IKA_TEKER_YARICAP_M, ks.IKA_TEKER_YARICAP_M)
        self.assertEqual(cpf.IKA_IZ_GENISLIGI_M, ks.IKA_IZ_GENISLIGI_M)
        # AST: sayı değil AD okunuyor
        nav = (KOK / "simulation" / "scripts" / "ika_nav.py").read_text(encoding="utf-8")
        ara = (KOK / "simulation" / "mujoco" / "araclar.py").read_text(encoding="utf-8")
        self.assertEqual(_atama_isim(nav, "MAX_SPEED"), "IKA_AZAMI_HIZ_MS")
        self.assertEqual(_atama_isim(ara, "IKA_VMAX_MS"), "IKA_AZAMI_HIZ_MS")
        self.assertEqual(_atama_isim(ara, "IKA_TEKER_R"), "IKA_TEKER_YARICAP_M")
        self.assertEqual(_atama_isim(ara, "IKA_IZ_M"), "IKA_IZ_GENISLIGI_M")
        cp = (KOK / "codes" / "costmap_path_finder.py").read_text(encoding="utf-8")
        self.assertIsNone(_atama_isim(cp, "IKA_AZAMI_HIZ_MS"), "costmap yeniden tanımlamamalı")

    def test_MUTASYON_ciplak_sayi_yakalanir(self):
        nav = (KOK / "simulation" / "scripts" / "ika_nav.py").read_text(encoding="utf-8")
        mutant = re.sub(r"^MAX_SPEED\s*=\s*IKA_AZAMI_HIZ_MS", "MAX_SPEED = 1.3", nav, count=1,
                        flags=re.M)
        self.assertNotEqual(nav, mutant, "MUTASYON UYGULANMADI")
        self.assertIsNone(_atama_isim(mutant, "MAX_SPEED"), "çıplak 1.3 yakalanmadı")

    def test_contracts_s4_ika_kinematik_tablosu(self):
        """CONTRACTS §4 üç sabiti adıyla ve tek kaynak dosyasıyla anar (belge↔kod kilidi)."""
        c = (KOK / "CONTRACTS.md").read_text(encoding="utf-8")
        b4 = c.split("## 4. Geometri sabitleri", 1)[1].split("\n## 5.", 1)[0]
        for ad in ("IKA_TEKER_YARICAP_M", "IKA_IZ_GENISLIGI_M", "IKA_AZAMI_HIZ_MS"):
            self.assertIn(f"`{ad}`", b4, f"CONTRACTS §4'te {ad} yok")
        self.assertIn("karar_sozlesmesi", b4)
        self.assertIn("TAHMİN", b4, "iz genişliği TAHMİN etiketi §4'te olmalı")
        self.assertIn("0.0625", b4); self.assertIn("0.39", b4); self.assertIn("1.3", b4)

    def test_kabul_rampasi_yeni_tavanin_altinda(self):
        from ika_surucu_kabul import RAMPA_HEDEF_MS
        self.assertLessEqual(RAMPA_HEDEF_MS, ika_nav.MAX_SPEED)
        self.assertEqual(ika_nav.steer(0.0), (ika_nav.MAX_SPEED, ika_nav.MAX_SPEED))


# ── B · MuJoCoSurucu ───────────────────────────────────────────────────────
class B_MuJoCoSurucu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = arena_mjcf.yukle(1, "kolay", 42, kam_res=96)

    def _kur(self, **kw):
        d = mujoco.MjData(self.m)
        return MuJoCoSurucu(self.m, d, **kw), d

    def test_arayuz_sozlesmesi(self):
        s, _ = self._kur()
        self.assertIsInstance(s, ika_surucu.IkaSurucu)
        self.assertIsNot(MuJoCoSurucu._hiz_ver, ika_surucu.IkaSurucu._hiz_ver)
        self.assertIsNot(MuJoCoSurucu.konum_al, ika_surucu.IkaSurucu.konum_al)
        for ad in ("hiz_ver", "konum_al", "durdur", "saglikli", "adimla", "saat"):
            self.assertTrue(callable(getattr(s, ad)), ad)
        self.assertTrue(s.durdur())
        self.assertTrue(s.saglikli())
        x, y, z, yaw = s.konum_al()
        self.assertEqual(len(s.konum_al()), 4)
        self.assertAlmostEqual(yaw, math.pi / 2, places=3)     # KB'de kuzeye bakar

    def test_konum_al_adim_oncesi_kb_pozu(self):
        """Regresyon (10 Eyl): taze MjData'da mj_forward'sız xpos/xmat sıfırdı →
        konum_al (0,0,0,0) veriyordu; sürücü kurulumda mj_forward koşar."""
        s, _ = self._kur()
        H = arena.harita(1, "kolay")
        x, y, z, yaw = s.konum_al()
        self.assertAlmostEqual(x, H["kb"][0], places=3)
        self.assertAlmostEqual(y, H["kb"][1], places=3)
        self.assertAlmostEqual(z, araclar.IKA_BASLANGIC_Z, places=3)
        self.assertAlmostEqual(yaw, math.pi / 2, places=3)

    def test_MUTASYON_nan_kirpmadan_once_denetlenmezse_tam_gaz(self):
        """Mutant (kırp → sonra denetle): min(w, nan) = w → NaN komut tam gaz olur."""
        s, d = self._kur()
        w = s.w_maks
        mutant = max(-w, min(w, float("nan")))
        self.assertTrue(math.isfinite(mutant) and mutant == w, "mutant kanıtı: NaN → w_maks")
        # gerçek kod: False ve ctrl DEĞİŞMEZ
        s.hiz_ver(0.5, 0.5)
        onceki = s.teker_hedefleri()
        self.assertFalse(s.hiz_ver(float("nan"), 0.0))
        self.assertFalse(s.hiz_ver(float("inf"), 0.0))
        self.assertEqual(s.teker_hedefleri(), onceki)
        self.assertEqual(s.ardisik_hata, 2)

    def test_hiz_ver_teker_hizi_donusumu(self):
        s, d = self._kur()
        r = ks.IKA_TEKER_YARICAP_M
        self.assertTrue(s.hiz_ver(1.3, 0.65))
        sag, sol = s.teker_hedefleri()
        self.assertAlmostEqual(sag, 1.3 / r, places=9)
        self.assertAlmostEqual(sol, 0.65 / r, places=9)
        self.assertAlmostEqual(sag, 20.8, places=9)
        for i in s.sag_akt:
            self.assertAlmostEqual(float(d.ctrl[i]), 1.3 / r)
        # kırpma: ctrlrange = ±v_maks/r
        self.assertTrue(s.hiz_ver(5.0, -5.0))
        sag, sol = s.teker_hedefleri()
        self.assertAlmostEqual(sag, ks.IKA_AZAMI_HIZ_MS / r, places=6)
        self.assertAlmostEqual(sol, -ks.IKA_AZAMI_HIZ_MS / r, places=6)
        # sonlu olmayan komut: False, istisna yok, arıza sayacı
        self.assertFalse(s.hiz_ver(float("nan"), 0.0))
        self.assertEqual(s.ardisik_hata, 1)
        self.assertTrue(s.hiz_ver(0, 0))
        self.assertEqual(s.ardisik_hata, 0)

    def test_fizikte_ileri_gider_ve_sag_hizli_sola_doner(self):
        s, d = self._kur()
        s.adimla(0.5)                                  # yerleşme
        x0, y0, _, yaw0 = s.konum_al()
        s.hiz_ver(1.0, 1.0)
        t = s.adimla(3.0)
        self.assertAlmostEqual(t, 3.5, places=6)
        self.assertAlmostEqual(s.saat(), float(d.time))
        x1, y1, _, yaw1 = s.konum_al()
        yol = math.hypot(x1 - x0, y1 - y0)
        self.assertGreater(yol, 2.0, f"3 s'de 1 m/s komutla {yol:.2f} m")
        self.assertGreater(y1 - y0, 1.9, "kuzeye (gövde +X) gitmeli")
        self.assertLess(abs(_sar(yaw1 - yaw0)), math.radians(5))
        self.assertEqual(s.kararsiz_adim, 0, "fizik kararsız (armature yok mu?)")
        s.hiz_ver(1.3, 0.4)
        s.adimla(2.0)
        _, _, _, yaw2 = s.konum_al()
        self.assertGreater(_sar(yaw2 - yaw1), math.radians(20),
                           "sağ hızlı → sola (CCW) dönmeli (ika_nav.steer sözleşmesi)")
        self.assertEqual(s.temas_sayisi, 0)

    def test_temas_sayaci_moloza_surunce_sayar(self):
        s, d = self._kur()
        g = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, "moloz_0")
        self.assertGreaterEqual(g, 0)
        mx, my = float(self.m.geom_pos[g][0]), float(self.m.geom_pos[g][1])
        # İKA'yı molozun 2 m güneyine, kuzeye bakar koy; ileri sür
        d.qpos[0:3] = [mx, my - 2.5, araclar.IKA_TEKER_R + 0.02]
        d.qpos[3:7] = [math.cos(math.pi / 4), 0, 0, math.sin(math.pi / 4)]
        mujoco.mj_forward(self.m, d)
        s.adimla(0.3)
        self.assertEqual(s.temas_sayisi, 0)
        s.hiz_ver(1.0, 1.0)
        s.adimla(4.0)
        self.assertGreaterEqual(s.temas_sayisi, 1)
        self.assertIn("moloz_0", s.temas_geomlari)
        self.assertIsNotNone(s.ilk_temas_t)
        self.assertGreater(s.temas_adim, 0)

    def test_isaret_boyalari_carpismasiz(self):
        m2 = arena_mjcf.yukle(1, "kolay", 42, kam_res=96)
        g = mujoco.mj_name2id(m2, mujoco.mjtObj.mjOBJ_GEOM, "hb_ped")
        self.assertNotEqual(int(m2.geom_contype[g]), 0, "arena MJCF'inde ped çarpışıyor (kusur kaydı)")
        s = MuJoCoSurucu(m2, mujoco.MjData(m2))
        self.assertEqual(sorted(s.isaretler_degisti), sorted(a for a in ISARET_GEOMLARI
                                                            if mujoco.mj_name2id(m2, mujoco.mjtObj.mjOBJ_GEOM, a) >= 0))
        self.assertEqual(int(m2.geom_contype[g]), 0)
        self.assertEqual(int(m2.geom_conaffinity[g]), 0)
        m3 = arena_mjcf.yukle(1, "kolay", 42, kam_res=96)
        s3 = MuJoCoSurucu(m3, mujoco.MjData(m3), isaretler_carpismasiz=False)
        self.assertEqual(s3.isaretler_degisti, [])
        g3 = mujoco.mj_name2id(m3, mujoco.mjtObj.mjOBJ_GEOM, "hb_ped")
        self.assertNotEqual(int(m3.geom_contype[g3]), 0)


# ── C · sim saati: navigate deadline ───────────────────────────────────────
class C_SimSaatiNavigate(unittest.TestCase):
    def tearDown(self):
        ika_nav.surucu_ayarla(None)

    def test_600s_deadline_enjekte_saatle_tetiklenir_sleep_yok(self):
        saat = SahteSaat(1000.0)
        gonderilen = []
        surucu = ika_surucu.SahteSurucu(pozlar=[(0.0, 0.0, 0.0, 0.0)])   # hiç ilerlemez
        ika_nav.surucu_ayarla(surucu)
        with mock.patch.object(ika_nav.time, "sleep", _uyku_yasak), \
             mock.patch.object(ika_nav, "send_vel",
                               lambda r, l, topic=None: gonderilen.append((r, l))), \
             contextlib.redirect_stdout(io.StringIO()):
            sonuc = ika_nav.navigate([(0.0, 0.0), (50.0, 0.0)], "sim", verbose=False,
                                     surus_deadline_monotonic=saat() + ks.IKA_SURUS_SURESI_S,
                                     saat=saat, bekle=saat.bekle)
        self.assertFalse(sonuc)
        self.assertEqual(gonderilen[-1], (0, 0))
        self.assertGreaterEqual(saat(), 1000.0 + ks.IKA_SURUS_SURESI_S)
        self.assertLess(saat(), 1000.0 + ks.IKA_SURUS_SURESI_S + 1.0)
        self.assertAlmostEqual(saat.bekle_n, ks.IKA_SURUS_SURESI_S * ika_nav.CTRL_HZ, delta=2)
        print(f"[C] deadline={ks.IKA_SURUS_SURESI_S:.0f}s sim → bekle çağrısı {saat.bekle_n}, sleep 0")

    def test_MUTASYON_bekle_yok_sayilirsa_sleep_cagrilir(self):
        """bekle verilmezse döngü time.sleep'e düşer (mutant: bekle parametresi yok sayıldı)."""
        surucu = ika_surucu.SahteSurucu(pozlar=[(0.0, 0.0, 0.0, 0.0)])
        ika_nav.surucu_ayarla(surucu)
        with mock.patch.object(ika_nav.time, "sleep", _uyku_yasak), \
             mock.patch.object(ika_nav, "send_vel", lambda r, l, topic=None: None), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(AssertionError):
                ika_nav.navigate([(0.0, 0.0), (50.0, 0.0)], "x", verbose=False,
                                 surus_deadline_monotonic=1e12, saat=lambda: 0.0)


# ── D · sim saati: rota bekleme (gerçek UDP loopback) ──────────────────────
class D_SimSaatiRotaBekleme(unittest.TestCase):
    ROTA = dict(road=1, conf=0.9, waypoints=[[0, 0], [0, 1.5], [0, 3.0]], ref_xy=[0.0, -23.0])

    def _gonderici(self):
        g = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        self.addCleanup(g.close)
        return g

    def test_enjekte_saatle_rota_kabul_edilir(self):
        saat = SahteSaat(5000.0)
        link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        g = self._gonderici()
        gonderildi = {"n": 0}

        def bekle(dt):
            saat.bekle(dt)
            if gonderildi["n"] == 0:
                g.send(encode(open_route(**self.ROTA, seq=77)), ("127.0.0.1", link.port))
                gonderildi["n"] = 1
            _GERCEK_UYKU(0.02)                   # alıcı thread'i datagramı alsın (test yardımı)

        with mock.patch.object(ika_nav.time, "sleep", _uyku_yasak), \
             contextlib.redirect_stdout(io.StringIO()):
            sonuc = ika_nav.wait_open_route_from_comms(
                "127.0.0.1:0", 30.0, keep_receiver=True, saat=saat, bekle=bekle, link=link)
        self.assertIsInstance(sonuc, tuple, f"rota kabul edilmedi: {sonuc!r}")
        rota, rx = sonuc
        try:
            self.assertEqual(rota["seq"], 77)
            _, _, _, damga = rx.decision_snapshot()
            self.assertGreaterEqual(damga, 5000.0, "alıcı damgası enjekte saat ekseninde değil")
            self.assertLess(damga, 5000.0 + 30.0)
        finally:
            rx.stop(); rx.link.close()
        print(f"[D] enjekte saat: rota seq=77 kabul, damga={damga:.2f} (saat 5000+)")

    def test_MUTASYON_alici_duvar_saatiyle_kurulursa_rota_atilir(self):
        """Alıcı `saat` almazsa (mutant) karar damgası duvar saatinde, deadline sim
        saatinde: geçerli rota 'deadline sonrası' sayılıp SESSİZCE atılır."""
        saat = SahteSaat(5000.0)
        link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        self.addCleanup(link.close)
        g = self._gonderici()
        gonderildi = {"n": 0}

        class DuvarSaatliAlici(IkaReceiver):
            def __init__(self, *a, saat=None, **k):
                super().__init__(*a, saat=None, **k)

        def bekle(dt):
            saat.bekle(dt)
            if gonderildi["n"] == 0:
                g.send(encode(open_route(**self.ROTA, seq=78)), ("127.0.0.1", link.port))
                gonderildi["n"] = 1
            _GERCEK_UYKU(0.02)

        with mock.patch.object(ika_receiver, "IkaReceiver", DuvarSaatliAlici), \
             contextlib.redirect_stdout(io.StringIO()):
            sonuc = ika_nav.wait_open_route_from_comms(
                "127.0.0.1:0", 5.0, keep_receiver=True, saat=saat, bekle=bekle, link=link)
        self.assertIsNone(sonuc, "mutant rota kabul etti — kilit anlamsız")

    def test_rota_gelmezse_enjekte_saatle_zaman_asimi(self):
        saat = SahteSaat(100.0)
        link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        with mock.patch.object(ika_nav.time, "sleep", _uyku_yasak), \
             contextlib.redirect_stdout(io.StringIO()):
            sonuc = ika_nav.wait_open_route_from_comms(
                "127.0.0.1:0", 12.0, saat=saat, bekle=saat.bekle, link=link)
        self.assertIsNone(sonuc)
        self.assertGreaterEqual(saat(), 112.0)
        self.assertGreaterEqual(saat.bekle_n, 60)          # 12 s / 0,2 s

    def test_izin_bekleme_bekle_ile_yoklanir(self):
        """receiver_surus_izni_bekle(bekle=…): Event.wait yerine yoklama + bekle."""
        saat = SahteSaat(0.0)
        link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        rx = IkaReceiver(link, saat=saat)
        self.addCleanup(link.close)
        with mock.patch.object(ika_nav, "send_vel", lambda r, l, topic=None: None), \
             mock.patch.object(ika_nav.time, "sleep", _uyku_yasak), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(ika_nav.receiver_surus_izni_bekle(rx, 3.0, saat=saat, bekle=saat.bekle))
        self.assertGreaterEqual(saat(), 3.0)
        rx.iha_inisini_bildir(saat())
        with rx._decision_lock:
            rx.ika_go = True; rx.ika_go_monotonic = saat(); rx._surus_iznini_guncelle_unlocked()
        with mock.patch.object(ika_nav, "send_vel", lambda r, l, topic=None: None), \
             mock.patch.object(ika_nav.time, "sleep", _uyku_yasak), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(ika_nav.receiver_surus_izni_bekle(
                rx, 3.0, deadline_monotonic=saat() + 3.0, saat=saat, bekle=saat.bekle))


# ── E · sim_hakem ──────────────────────────────────────────────────────────
class E_SimHakem(unittest.TestCase):
    def test_sim_alani_ve_uretici_disiplini(self):
        m = sim_hakem.sim_iha_landed(seq=5)
        self.assertEqual((m["type"], m["node"], m["seq"]), ("IHA_LANDED", "iha", 5))
        self.assertIs(m["sim"], True)
        g = sim_hakem.sim_ika_go(seq=6)
        self.assertEqual((g["type"], g["cmd"], g["hedef"]), ("CMD", "IKA_GO", "ika"))
        self.assertIs(g["sim"], True)
        hb = sim_hakem.sim_iha_heartbeat()
        self.assertEqual((hb["type"], hb["node"], hb["sim"]), ("HEARTBEAT", "iha", True))
        # sim=true olmadan üretilen (saha) mesajda alan YOK — ayrım korunur
        from protocol import iha_landed
        self.assertNotIn("sim", iha_landed())

    def test_hakem_acki_de_sim_alani_tasir(self):
        """Hakemin ürettiği ACK (NO_ROUTE / OPEN_ROUTE 2/2) da sim=true taşır."""
        saat = SahteSaat(0.0)
        link = UDPLink(bind=("127.0.0.1", 0), timeout=0.01)
        hakem = sim_hakem.SimHakem(("127.0.0.1", 1), t_inis=99.0, saat=saat, link=link)
        self.addCleanup(hakem.kapat)
        giden = []
        hakem.link.send = lambda b, addr: giden.append((b, addr))
        hakem._mesaj(rota_yok("KARAR_YOK", seq=41), ("127.0.0.1", 2))
        self.assertEqual(len(giden), 1)
        m = list(FrameReader().feed(giden[0][0]))[0]
        self.assertEqual((m["type"], m["node"], m["ref"], m["ref_tip"]), ("ACK", "yks", 41, "NO_ROUTE"))
        self.assertIs(m["sim"], True)
        # saha ACK'ında alan yok
        from protocol import ack
        self.assertNotIn("sim", ack(41, "yks", "NO_ROUTE"))

    def test_uretim_kodunda_sim_hakem_importu_yok(self):
        desen = re.compile(r"^\s*(from|import)\s+.*sim_hakem", re.M)
        vuran = []
        for kok in (KOK / "codes", KOK / "comms", KOK / "simulation" / "scripts", KOK / "scripts"):
            for p in kok.glob("*.py"):
                if desen.search(p.read_text(encoding="utf-8", errors="replace")):
                    vuran.append(str(p.relative_to(KOK)))
        self.assertEqual(vuran, [], f"üretim kodu sim_hakem'e bağlandı: {vuran}")
        self.assertTrue((KOK / "simulation" / "mujoco" / "sim_hakem.py").is_file())

    def test_erken_ika_ack_kopyasi_rota_gelince_eslesir(self):
        """Regresyon (gt 1 orta 44): İKA ACK kopyası OPEN_ROUTE'tan ÖNCE gelirse
        kanıt saklanır; rota gelince 2/2 verilir ve İHA'ya ACK gider.
        Mutasyon: tampon devre dışı → kanıt None, İHA'ya ACK yok (eski kilitlenme)."""
        from protocol import ack
        for tampon in (True, False):
            saat = SahteSaat(0.0)
            link = UDPLink(bind=("127.0.0.1", 0), timeout=0.01)
            hakem = sim_hakem.SimHakem(("127.0.0.1", 1), t_inis=99.0, saat=saat, link=link)
            self.addCleanup(hakem.kapat)
            giden = []
            hakem.link.send = lambda b, addr, _g=giden: _g.append((list(FrameReader().feed(b))[0], addr))
            if not tampon:
                hakem._erken_kanit = mock.MagicMock()      # mutant: saklamaz, hiç eşlemez
                hakem._erken_kanit.pop.return_value = None
            hakem._mesaj(ack(5, "ika", "OPEN_ROUTE"), ("127.0.0.1", 3))
            self.assertIsNone(hakem.rota_ack_kaniti)
            hakem._mesaj(open_route(1, 0.9, [[0, 0], [0, 1.5]], [0.0, -23.0], seq=5), ("127.0.0.1", 2))
            if tampon:
                self.assertIsNotNone(hakem.rota_ack_kaniti, "erken kanıt eşlenmedi")
                self.assertEqual([(m["type"], m["ref_tip"], addr[1]) for m, addr in giden],
                                 [("ACK", "OPEN_ROUTE", 2)])
                self.assertTrue(any(o["olay"] == "IKA_AKTARIM_KANITI" and o.get("erken") for o in hakem.olaylar))
            else:
                self.assertIsNone(hakem.rota_ack_kaniti, "mutant kanıt buldu — kilit anlamsız")
                self.assertEqual(giden, [])

    def test_contracts_s67_sim_istisnasi_yazili(self):
        c = (KOK / "CONTRACTS.md").read_text(encoding="utf-8")
        b = c.split("### 6.7 FDA görev kipi", 1)[1].split("\n### 6.8", 1)[0]
        self.assertIn("Simülasyon istisnası", b)
        self.assertIn("sim_hakem", b)
        self.assertIn('"sim": true', b)
        self.assertIn("saha kanıtı", b)
        self.assertIn("simulation/mujoco/", b)

    def _akis(self, yks_peer_ver: bool, t_inis=10.0):
        saat = SahteSaat(0.0)
        ika_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.01)
        ika_addr = ("127.0.0.1", ika_link.port)
        hakem = sim_hakem.SimHakem(ika_addr, t_inis=t_inis, saat=saat)
        rx = IkaReceiver(ika_link, yks_peer=hakem.addr if yks_peer_ver else None, saat=saat)
        iha_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        sender = IhaSender(iha_link, {"ika": ika_addr, "yks": hakem.addr})
        sonuc = {}

        def gonder():
            sonuc["seq"], sonuc["acked"] = sender.send_open_route(
                1, 0.9, [[0, 0], [0, 1.5]], [0.0, -23.0], repeat=4, interval=0.15)

        thr = threading.Thread(target=gonder, daemon=True)
        thr.start()
        landed_once_gorulen = None
        try:
            for k in range(300):
                saat.bekle(0.1)
                rx.poll()
                hakem.adimla(saat())
                rx.poll()
                if saat() < t_inis - 0.05 and rx.iha_landed and landed_once_gorulen is None:
                    landed_once_gorulen = saat()
                if hakem.t_ika_go_ack is not None:
                    break
                _GERCEK_UYKU(0.002)
            thr.join(3.0)
            rx.poll()
        finally:
            hakem.kapat(); ika_link.close(); iha_link.close()
        return saat, hakem, rx, sonuc, landed_once_gorulen

    def test_loopback_ack_akisi_k8_kaniti_sonra_iha_ack_landed_t_inis_ika_go(self):
        saat, hakem, rx, sonuc, landed_erken = self._akis(yks_peer_ver=True)
        self.assertEqual(sonuc.get("acked"), {"ika", "yks"}, "H1-K4: OPEN_ROUTE ACK ['ika','yks']")
        self.assertIsNotNone(hakem.rota_ack_kaniti, "K8 kanıtı (İKA ACK kopyası) gelmedi")
        self.assertIsNotNone(hakem.iha_ack_gonderildi)
        self.assertGreaterEqual(hakem.iha_ack_gonderildi["t"], hakem.rota_ack_kaniti["t"])
        olaylar = [o["olay"] for o in hakem.olaylar]
        self.assertLess(olaylar.index("IKA_AKTARIM_KANITI"), olaylar.index("HAKEM_ONAYI_2"))
        self.assertIsNone(landed_erken, "IHA_LANDED t_inis'ten ÖNCE latch'lendi")
        self.assertIsNotNone(hakem.t_landed)
        self.assertGreaterEqual(hakem.t_landed, 10.0)
        self.assertTrue(rx.iha_landed and rx.ika_go)
        self.assertEqual(hakem.ika_go.durum, "ONAYLANDI")
        self.assertIsNotNone(hakem.t_ika_go_ack)
        self.assertGreaterEqual(hakem.t_ika_go, hakem.t_landed)
        tipler = [a["ref_tip"] for a in hakem.ack_listesi]
        for t in ("OPEN_ROUTE", "IHA_LANDED", "CMD"):
            self.assertIn(t, tipler)
        self.assertGreater(hakem.heartbeat_sayisi, 10)
        self.assertTrue(rx.link_ok)
        print(f"[E] acked={sorted(sonuc['acked'])} kanıt t={hakem.rota_ack_kaniti['t']} "
              f"landed t={hakem.t_landed:.1f} ika_go t={hakem.t_ika_go:.1f} ack t={hakem.t_ika_go_ack:.1f}")

    def test_MUTASYON_k8_kaniti_yoksa_ihaya_ack_gitmez_ika_go_yok(self):
        """İKA ACK kopyasını YKS'ye yansıtmazsa (yks_peer yok) hakem 2/2 veremez:
        İHA yalnız 'ika' ACK'ı görür, IKA_GO hiç çıkmaz (fail-closed aynen)."""
        saat, hakem, rx, sonuc, _ = self._akis(yks_peer_ver=False)
        self.assertEqual(sonuc.get("acked"), {"ika"})
        self.assertIsNone(hakem.rota_ack_kaniti)
        self.assertIsNone(hakem.iha_ack_gonderildi)
        self.assertIsNone(hakem.t_ika_go)
        self.assertFalse(rx.ika_go)
        self.assertTrue(rx.iha_landed, "iniş olayı yine t_inis'te üretilir")


# ── F · gorev_kosumu ───────────────────────────────────────────────────────
class F_GorevKosumu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        t0 = time.perf_counter()
        with contextlib.redirect_stdout(io.StringIO()):
            cls.r = gorev_kosumu.kos(1, "kolay", 42, "gt", res=96, out=Path(cls.tmp.name),
                                     fizik_tarama=False)
        cls.sure = time.perf_counter() - t0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_duman_60s_altinda_ve_metrik_semasi(self):
        self.assertLess(self.sure, 60.0, f"duman {self.sure:.1f} s")
        eksik = [k for k in gorev_kosumu.METRIK_ANAHTARLARI if k not in self.r]
        self.assertEqual(eksik, [])
        r = self.r
        self.assertEqual(r["rota_kaynak"], "gt")
        self.assertTrue(r["rota_bulundu"] and r["rota_dogru"])
        self.assertLessEqual(r["maks_segment_m"], ika_nav.MAX_SEGMENT_M)
        self.assertEqual(r["open_route_ack"], ["ika", "yks"])
        self.assertIsNotNone(r["t_ika_go_ack"])
        self.assertGreaterEqual(r["t_ika_go"], r["t_inis"])
        self.assertIsInstance(r["hb_icinde"], bool)
        self.assertIsInstance(r["temas_sayisi"], int)
        self.assertEqual(r["cikis_kodu"], 0, r)
        self.assertTrue(r["hb_icinde"], r["varis_mesafesi_m"])
        self.assertEqual(r["temas_sayisi"], 0, r["temas_geomlari"])
        self.assertTrue(r["basari"])
        self.assertGreater(r["sure_sim_ika"], 0.0)
        self.assertLessEqual(r["sure_sim_ika"], ks.SARTNAME_IKA_GOREV_SURESI_S)
        # ONARIM-12 (17 Eyl 2026): 36,98 -> 38,81. Tek neden world_generator PHASE_SPEED
        # "parasut" 5,5 -> 3,0 m/s (kullanici istegi 2-4 m/s bandi, D-488); yalniz bu deger
        # 5,5'e geri alininca test 36,98 ile GECTI (izolasyon olcumu, ONARIM-12).
        self.assertAlmostEqual(r["sure_sim_iha_profil"], 38.81, places=1)
        self.assertEqual(r["kararsiz_adim"], 0)
        self.assertTrue((Path(self.tmp.name) / "gt_1_kolay_42.json").is_file())
        oz = gorev_kosumu.ozet_kur(Path(self.tmp.name))
        self.assertEqual(oz["kaynaklar"]["gt"]["n"], 1)
        self.assertEqual(oz["kaynaklar"]["gt"]["basari_n"], 1)
        print(f"[F] duman {self.sure:.1f} s · sürüş {r['sure_sim_ika']} sim-s · varış "
              f"{r['varis_mesafesi_m']} m · temas {r['temas_sayisi']} · ack {r['open_route_ack']}")

    def test_rota_engel_acikligi_teshis_metrigi(self):
        """Açıklık = rota örnekleri → geom OBB uzaklığı; merkezden geçen rota 0, uzak rota
        büyük; kutu kenarından 0,30 m geçen hat ≈ 0,30; duman koşumunda alan bool."""
        m = arena_mjcf.yukle(1, "kolay", 42, kam_res=64)
        g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "tikama_2_0_0")
        self.assertGreaterEqual(g, 0)
        cx, cy = float(m.geom_pos[g][0]), float(m.geom_pos[g][1])
        a, ad = gorev_kosumu.rota_engel_acikligi(m, [(cx - 3, cy), (cx + 3, cy)])
        self.assertLessEqual(a, 1e-6, "merkezden geçen hat içeride → 0")
        self.assertTrue(ad.startswith(("moloz_", "tikama_", "chicane_", "bariyer_", "ub_duvar_")))
        # eksen hizalı yapay kutu: (0,0) merkez, yarı kenar 0,4, yaw 0 → y=0,7 hattı 0,30 açıklık
        import numpy as np
        yerel_m = mujoco.MjModel.from_xml_string(
            '<mujoco><worldbody><geom name="moloz_x" type="box" size="0.4 0.4 0.3" pos="0 0 0.3"/>'
            '</worldbody></mujoco>')
        a2, ad2 = gorev_kosumu.rota_engel_acikligi(yerel_m, [(-2.0, 0.7), (2.0, 0.7)])
        self.assertAlmostEqual(a2, 0.30, places=2); self.assertEqual(ad2, "moloz_x")
        a3, _ = gorev_kosumu.rota_engel_acikligi(yerel_m, [(-2.0, 0.55), (2.0, 0.55)])
        self.assertAlmostEqual(a3, 0.15, places=2)
        self.assertLess(a3, gorev_kosumu.IKA_YARI_GENISLIK_M)       # inşaat gereği geçilemez
        a4, _ = gorev_kosumu.rota_engel_acikligi(m, [(400.0, 400.0), (401.0, 401.0)])
        self.assertGreater(a4, 50.0)
        self.assertIn(self.r["rota_insaat_geregi_gecilemez"], (True, False))
        self.assertAlmostEqual(self.r["ika_yari_genislik_m"], (ks.IKA_IZ_GENISLIGI_M + araclar.IKA_TEKER_W) / 2, places=3)
        self.assertIsInstance(self.r["rota_engel_aciklik_m"], float)
        print(f"[F] 1 kolay 42 GT rota açıklığı {self.r['rota_engel_aciklik_m']} m ({self.r['rota_engel_aciklik_geom']})")

    def test_readme_olcumden_bayt_es(self):
        """README_T213B.md üreteç çıktısıyla BAYT-EŞ (elle düzenlenmedi); duman klasöründe de üretilir."""
        import kosum_readme
        gorev_kosumu.ozet_kur(Path(self.tmp.name))
        metin = kosum_readme.uret(Path(self.tmp.name))
        self.assertIn("| gt (YER GERÇEĞİ) | 1 |", metin)
        self.assertIn("| model | 0 |", metin)                  # ölçülmemiş kaynak ÖLÇÜLMEDİ satırı
        self.assertIn("ÖLÇÜLMEDİ", metin)
        self.assertIn("| gt | 1 | kolay | 42 |", metin)
        self.assertIn("TAHMİN", metin); self.assertIn("saha kanıtı sayılmaz", metin)
        kosum = gorev_kosumu.KOSUM_KOK
        if (kosum / kosum_readme.README_ADI).is_file() and (kosum / "ozet_kosum.json").is_file():
            disk = (kosum / kosum_readme.README_ADI).read_text(encoding="utf-8")
            self.assertEqual(disk, kosum_readme.uret(kosum), "README elle düzenlenmiş / bayat — kosum_readme.py ile üret")
            oz = json.loads((kosum / "ozet_kosum.json").read_text(encoding="utf-8"))
            for k, o in oz["kaynaklar"].items():
                self.assertIn(f"**{o['basari_n']}/{o['n']} ({o['basari_orani']:.3f})**", disk)

    def test_rota_bol_d438c(self):
        H = arena.harita(1, "kolay")
        ham = arena.route_waypoints(H["open"], "kolay", 1)
        ref = ham[0]
        yerel_ham = [[x - ref[0], y - ref[1]] for x, y in ham]
        with self.assertRaises(ValueError):            # D-438 c: 3,3 m segment sözleşmeyi geçmez
            rota_geometrisini_dogrula([ref[0], ref[1]], yerel_ham)
        bol = gorev_kosumu.rota_bol(ham)
        self.assertEqual(bol[0], tuple(map(float, ham[0])))
        self.assertAlmostEqual(bol[-1][0], ham[-1][0]); self.assertAlmostEqual(bol[-1][1], ham[-1][1])
        self.assertLessEqual(max(math.dist(a, b) for a, b in zip(bol, bol[1:])), ika_nav.MAX_SEGMENT_M)
        self.assertLessEqual(len(bol), ika_nav.MAX_WAYPOINTS)
        yerel = [[round(x - ref[0], 2), round(y - ref[1], 2)] for x, y in bol]
        rota_geometrisini_dogrula([ref[0], ref[1]], yerel)   # geçer
        # bölünmüş noktalar ham polyline üzerinde (geometri EKLENMEDİ)
        for p in bol:
            self.assertLess(arena.dist_to_path(p[0], p[1], ham), 1e-6)


if __name__ == "__main__":
    unittest.main()

// Navitas TEKNOFEST 2026 — Animasyon + İKA FİZİK Sürüş Dünya Plugin'i
//
// İHA / paraşüt : KİNEMATİK — zaman-interp yol noktaları boyunca SetWorldPose
//                 (uçuş; yer çarpışması gerekmez, deterministik akıcı hareket).
//                 "iha" modeli ayrıca GERÇEKÇİ TAVIR alır: tırmanışta burun yukarı /
//                 alçalmada aşağı (pitch) ve dönüşte koordineli YATIŞ (bank,
//                 phi = atan(v·yawRate/g)) — yörüngeden türetilir, alçak-geçiren
//                 filtreyle yumuşatılır.
// İKA (ika*)    : FİZİK — SINIRLI KUVVET kontrolüyle waypoint takibi (AddForce/AddTorque).
//                 Hız DOĞRUDAN atanmaz (SetLinearVel temas kuvvetlerini EZER → engelden
//                 geçer). Bunun yerine motor traksiyonu gibi SINIRLI kuvvet uygulanır:
//                 katı (static) moloza çarpınca temas kuvveti bizimkini yener → İKA DURUR,
//                 içinden GEÇEMEZ. Gerçek fizik. Alçak ağırlık merkezi → devrilmez.
//
// SDF:
//   <plugin name="navitas_anim" filename="libnavitas_anim.so">
//     <model name="iha">       <waypoint>t x y z yaw</waypoint> ... </model>
//     <model name="ika_kolay"> <waypoint>t x y z yaw</waypoint> ... </model>
//   </plugin>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <ignition/math/Pose3.hh>
#include <ignition/math/Vector3.hh>
#include <fstream>
#include <functional>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <cmath>

namespace gazebo
{
  struct Waypoint { double t, x, y, z, yaw; };

  class NavitasAnim : public WorldPlugin
  {
    private: physics::WorldPtr world;
    private: event::ConnectionPtr updateConn;
    private: std::map<std::string, std::vector<Waypoint>> traj;
    private: std::map<std::string, size_t> ikaIdx;     // İKA waypoint takip indeksi
    private: double ihaRoll = 0.0, ihaPitch = 0.0;     // İHA tavır (alçak-geçiren durum)

    // İKA ROTA KAYNAĞI — dürüst haritalandırma zinciri:
    //   İHA tarama kareleri → host'ta iha_haritala.py (mozaik + model) → /tmp/navitas_route
    //   (satır başına "x y" DÜNYA koordinatı, güney→kuzey). Dosya gelirse İKA MODELİN
    //   haritasını sürer. Geçerli dinamik rota gelmezse SDF'deki geometrinin
    //   kullanılması yasaktır; İKA güvenli şekilde yerinde bekler.
    private: std::map<std::string, std::string> ikaRouteSrc;   // "bekliyor"|"model"|"rota_yok"
    private: const char *ROUTE_FILE = "/tmp/navitas_route";
    private: const double ROUTE_WAIT = 45.0;   // s — İHA inişinden sonra rota bekleme süresi

    // İHA tavır limitleri (gerçekçi küçük sabit kanat)
    private: const double PITCH_MAX = 0.45;   // rad (~26°) burun yukarı/aşağı
    private: const double ROLL_MAX  = 0.70;   // rad (~40°) yatış
    private: const double ATT_TAU   = 0.25;   // s — tavır yumuşatma zaman sabiti

    // İKA sürüş parametreleri
    // İLERİ: SINIRLI KUVVET (AddForce) → katı engeli aşamaz, içinden geçemez (gerçek fizik).
    // DÖNÜŞ: SetAngularVel (doğrudan) → skid-steer 4 sabit teker yüksek sürtünmede tork ile
    //        dönemeyeceği için yaw doğrudan atanır (çarpışma bütünlüğü ileri eksende korunur).
    private: const double IKA_SPEED    = 1.3;   // m/s — DDR fiziksel tavan (4×KGX38 24V
                                                 // 200rpm × Ø0,125m teker; karar_sozlesmesi.
                                                 // IKA_AZAMI_HIZ_MS ile eş; D-438f üç-kopya
                                                 // tutarsızlığını (2,0/1,1/0,30) kapatır)
    private: const double WP_RADIUS    = 0.5;   // m — costmap takip payını aşmaz
    private: const double FINAL_WP_RADIUS = 0.3; // m — HB son yaklaşım toleransı
    private: const double YAW_GAIN     = 2.5;   // hedef yaw hatasından açısal hıza kazanç
    private: const double YAW_RATE_MAX = 1.6;   // rad/s — dönüş hız limiti
    private: const double FORCE_GAIN   = 60.0;  // (v_hedef - v) → kuvvet kazancı (N/(m/s))
    private: const double FORCE_MAX    = 80.0;  // N — motor traksiyon limiti (engeli AŞAMAZ)

    public: void Load(physics::WorldPtr _world, sdf::ElementPtr _sdf) override
    {
      this->world = _world;
      if (_sdf->HasElement("model"))
      {
        for (auto m = _sdf->GetElement("model"); m; m = m->GetNextElement("model"))
        {
          std::string name = m->Get<std::string>("name");
          std::vector<Waypoint> wps;
          if (m->HasElement("waypoint"))
          {
            for (auto w = m->GetElement("waypoint"); w; w = w->GetNextElement("waypoint"))
            {
              std::stringstream ss(w->Get<std::string>());
              Waypoint wp{0, 0, 0, 0, 0};
              ss >> wp.t >> wp.x >> wp.y >> wp.z >> wp.yaw;
              wps.push_back(wp);
            }
          }
          if (!wps.empty())
          {
            this->traj[name] = wps;
            this->ikaIdx[name] = 1;
            if (isIka(name)) this->ikaRouteSrc[name] = "bekliyor";
            gzmsg << "[navitas_anim] '" << name << "' " << wps.size()
                  << " yol noktası.\n";
          }
        }
      }
      this->updateConn = event::Events::ConnectWorldUpdateBegin(
          std::bind(&NavitasAnim::OnUpdate, this));
    }

    private: static bool isIka(const std::string &n)
    {
      return n.rfind("ika", 0) == 0;        // "ika" ile başlıyorsa İKA
    }

    // MODEL rotasını dene: /tmp/navitas_route, satır başına "x y" (DÜNYA koordinatı,
    // güney→kuzey). Başarıyla ≥2 nokta okunursa İKA'nın waypoint'leri BUNLARLA değişir
    // (başlangıç zamanı/noktası SDF'ten kalır — İHA inişini bekleme davranışı bozulmaz).
    private: bool tryLoadRoute(const std::string &name)
    {
      std::ifstream f(ROUTE_FILE);
      if (!f.good()) return false;
      auto &sdfWps = this->traj[name];
      std::vector<Waypoint> wps{sdfWps.front()};
      std::string line;
      double x, y;
      while (std::getline(f, line))
      {
        std::stringstream ss(line);
        if (ss >> x >> y)
          wps.push_back(Waypoint{0, x, y, sdfWps.front().z, 0});
      }
      if (wps.size() < 3) return false;      // bozuk/yarım dosya — sonraki tick tekrar
      this->traj[name] = wps;
      this->ikaIdx[name] = 1;
      this->ikaRouteSrc[name] = "model";
      gzmsg << "[navitas_anim] '" << name << "' İHA MODEL haritası yüklendi: "
            << (wps.size() - 1) << " rota noktası (" << ROUTE_FILE << ")\n";
      return true;
    }

    private: static double wrap(double a)
    {
      while (a >  M_PI) a -= 2 * M_PI;
      while (a < -M_PI) a += 2 * M_PI;
      return a;
    }

    private: double lastSimWrite = -1e9;
    private: bool modelLogHeaderWritten = false;
    // Her modelin (İHA + paraşüt aşamaları + İKA) 1 Hz konum/hız kaydı —
    // /tmp/navitas_simtime (üstteki tek-satır anlık durum, record_in_container.sh
    // BURAYI ayrıştırıyor, dokunma) İLE KARIŞTIRILMAZ; bu EKLEMELİ (append) tam geçmiş
    // kaydıdır, kullanıcı isteği (2026-09-15): "ika log tutsun her model log tutacak".
    private: const char *MODEL_LOG_FILE = "/tmp/navitas_model_log.csv";

    private: void SetFlatView(const std::string &name, double x, double y,
                              double z, double yaw, double forward = 0.0,
                              double side = 0.0)
    {
      if (auto v = this->world->ModelByName(name))
      {
        double px = x + forward * std::cos(yaw) - side * std::sin(yaw);
        double py = y + forward * std::sin(yaw) + side * std::cos(yaw);
        v->SetWorldPose(ignition::math::Pose3d(px, py, z, 0, 0, yaw));
      }
    }

    private: void OnUpdate()
    {
      double t = this->world->SimTime().Double();

      // SİM SAATİ → dosya (kayıt betiği okur). gz stats/transport GÜVENİLMEZ
      // (yük altında sessiz, ara sıra SIGABRT) — dosya deterministik.
      if (t - this->lastSimWrite >= 1.0)
      {
        std::ofstream f("/tmp/navitas_simtime");
        f << static_cast<long>(t) << "\n";
        // İKA telemetrisi (hata ayıklama + hakem logu): konum, hız, hedef wp, rota kaynağı
        for (auto &kv : this->traj)
          if (isIka(kv.first))
            if (auto m = this->world->ModelByName(kv.first))
            {
              auto p = m->WorldPose().Pos();
              auto v = m->WorldLinearVel();
              f << kv.first << " x=" << p.X() << " y=" << p.Y()
                << " v=" << std::hypot(v.X(), v.Y())
                << " wp=" << this->ikaIdx[kv.first]
                << " rota=" << this->ikaRouteSrc[kv.first]
                // rota bitti (son wp'ye ulaşıldı) → kayıt betiği klibi erken keser
                << (this->ikaIdx[kv.first] >= kv.second.size() ? " durum=BITTI" : "")
                << (this->ikaRouteSrc[kv.first] == "rota_yok" ? " durum=ROTA_YOK" : "")
                << "\n";
            }
        if (auto b = this->world->ModelByName("aftershock_barrier"))
        {
          double bz = (t < 45.0) ? 8.0 : 0.65;
          auto bp = b->WorldPose();
          b->SetWorldPose(ignition::math::Pose3d(bp.Pos().X(), bp.Pos().Y(), bz,
                                                 bp.Rot().Roll(), bp.Rot().Pitch(),
                                                 bp.Rot().Yaw()));
          f << "aftershock_barrier z=" << bz << "\n";
        }
        if (auto iha = this->world->ModelByName("iha"))
        {
          auto p = iha->WorldPose();
          this->SetFlatView("iha_view_footprint", p.Pos().X(), p.Pos().Y(),
                            0.13, p.Rot().Yaw());
        }
        // (İHA poz logu artık navitas_scan_cam plugin'inde — kareyle AYNI olayda
        //  yazılır, birebir senkron; buradaki 1 Hz kopya kaldırıldı.)

        // HER MODELİN tam geçmiş kaydı (eklemeli CSV) — İHA, paraşüt aşamaları
        // (packed/partial/full) ve İKA dahil, `traj`'daki HERKES.
        std::ofstream lg(this->MODEL_LOG_FILE, std::ios::app);
        if (lg.good())
        {
          if (!this->modelLogHeaderWritten)
          {
            lg << "t,model,x,y,z,yaw,v,wp,rota,durum\n";
            this->modelLogHeaderWritten = true;
          }
          for (auto &kv : this->traj)
          {
            auto m = this->world->ModelByName(kv.first);
            if (!m) continue;
            auto pose = m->WorldPose();
            auto pos = pose.Pos();
            auto vel = m->WorldLinearVel();
            double spd = std::hypot(vel.X(), vel.Y());
            std::string wpCol, rotaCol, durumCol;
            if (isIka(kv.first))
            {
              wpCol = std::to_string(this->ikaIdx[kv.first]);
              rotaCol = this->ikaRouteSrc[kv.first];
              if (this->ikaIdx[kv.first] >= kv.second.size()) durumCol = "BITTI";
              else if (this->ikaRouteSrc[kv.first] == "rota_yok") durumCol = "ROTA_YOK";
            }
            lg << t << "," << kv.first << "," << pos.X() << "," << pos.Y() << ","
               << pos.Z() << "," << pose.Rot().Yaw() << "," << spd << ","
               << wpCol << "," << rotaCol << "," << durumCol << "\n";
          }
        }

        this->lastSimWrite = t;
      }

      for (auto &kv : this->traj)
      {
        auto model = this->world->ModelByName(kv.first);
        if (!model) continue;
        const auto &wps = kv.second;

        // ── İKA: FİZİK — SINIRLI KUVVET kontrolü (engelden GEÇEMEZ) ──
        if (isIka(kv.first))
        {
          auto link = model->GetLink("base_link");
          double startT = wps.front().t;
          if (t < startT)
          {
            // İHA inişini bekle — yerinde dur (fizik yerçekimi oturtur)
            model->SetLinearVel(ignition::math::Vector3d::Zero);
            model->SetAngularVel(ignition::math::Vector3d::Zero);
            this->ikaIdx[kv.first] = 1;
            continue;
          }

          // ── ROTA KAYNAĞI: yalnız MODEL haritası (/tmp/navitas_route). ──
          // Geçerli A* waypoint dizisi yoksa SDF'deki sabit rota asla sürülmez.
          std::string &src = this->ikaRouteSrc[kv.first];
          if (src != "model")
          {
            if (!this->tryLoadRoute(kv.first))
            {
              if (src == "bekliyor" && t >= startT + ROUTE_WAIT)
              {
                src = "rota_yok";
                gzmsg << "[navitas_anim] '" << kv.first << "' MODEL rotası "
                      << ROUTE_WAIT << "s içinde gelmedi → GÜVENLİ DURMA; "
                         "SDF ground-truth rota KULLANILMADI.\n";
              }
              model->SetLinearVel(ignition::math::Vector3d::Zero);
              model->SetAngularVel(ignition::math::Vector3d::Zero);
              continue;                            // dinamik rota gelene dek bekle
            }
          }
          size_t &idx = this->ikaIdx[kv.first];
          if (idx < 1) idx = 1;
          if (idx >= wps.size())
          {
            model->SetLinearVel(ignition::math::Vector3d::Zero);   // HB'ye ulaştı, dur
            model->SetAngularVel(ignition::math::Vector3d::Zero);
            continue;
          }
          if (!link) continue;
          auto pose = model->WorldPose();
          double cx = pose.Pos().X(), cy = pose.Pos().Y();
          std::string sfx = kv.first.substr(4);  // ika_<seviye> -> <seviye>
          this->SetFlatView("ika_view_" + sfx + "_center", cx, cy, 0.16,
                            pose.Rot().Yaw(), 6.5, 0.0);
          this->SetFlatView("ika_view_" + sfx + "_left", cx, cy, 0.16,
                            pose.Rot().Yaw() + 0.60, 6.2, 0.0);
          this->SetFlatView("ika_view_" + sfx + "_right", cx, cy, 0.16,
                            pose.Rot().Yaw() - 0.60, 6.2, 0.0);
          double dx = wps[idx].x - cx, dy = wps[idx].y - cy;
          double dist = std::hypot(dx, dy);
          double hedefRadius = (idx + 1 >= wps.size()) ? FINAL_WP_RADIUS : WP_RADIUS;
          if (dist < hedefRadius) { idx++; continue; } // sonraki waypoint/HB

          // Hedef hız (XY) → istenen hız vektörü
          double inv = 1.0 / dist;
          double vdx = dx * inv * IKA_SPEED, vdy = dy * inv * IKA_SPEED;

          // İLERİ — SINIRLI traksiyon kuvveti = clamp((v_hedef - v_mevcut) * kazanç).
          // Engel katıysa (static moloz) temas kuvveti bunu yener → İKA durur, GEÇEMEZ.
          // (Tekerler serbest döner; diff_drive eklentisi YOK ki fren yapıp kilitlemesin.)
          auto vel = model->WorldLinearVel();
          double fx = (vdx - vel.X()) * FORCE_GAIN;
          double fy = (vdy - vel.Y()) * FORCE_GAIN;
          double fmag = std::hypot(fx, fy);
          if (fmag > FORCE_MAX) { fx *= FORCE_MAX / fmag; fy *= FORCE_MAX / fmag; }
          link->AddForce(ignition::math::Vector3d(fx, fy, 0));

          // DÖNÜŞ — burnu hareket yönüne çevir (doğrudan açısal hız, limitli).
          // DİKKAT: model->SetAngularVel TÜM link'lere (tekerlekler dahil) hız
          // dayatır → tekerlek dönemez, araç sürtünerek 0.2 m/s'ye saplanır.
          // Sadece GÖVDEYE uygula: tekerlekler akslarında serbest yuvarlanır.
          double desiredYaw = std::atan2(dy, dx);
          double dyaw = wrap(desiredYaw - pose.Rot().Yaw());
          double wz = YAW_GAIN * dyaw;
          if (wz >  YAW_RATE_MAX) wz =  YAW_RATE_MAX;
          if (wz < -YAW_RATE_MAX) wz = -YAW_RATE_MAX;
          link->SetAngularVel(ignition::math::Vector3d(0, 0, wz));
          continue;
        }

        // ── İHA / paraşüt: KİNEMATİK interp (SetWorldPose) ──
        double x, y, z, yaw;
        samplePose(wps, t, x, y, z, yaw);

        double roll = 0.0, pitch = 0.0;
        if (kv.first == "iha")
        {
          // Yörüngeden hız + yaw hızı türet (ileri fark) → gerçekçi tavır:
          //   pitch = -atan2(vz, v_yatay)  (tırmanışta burun YUKARI)
          //   roll  = atan(v·yawRate / g)  (koordineli dönüş yatışı)
          const double DT = 0.10;
          double x2, y2, z2, yaw2;
          samplePose(wps, t + DT, x2, y2, z2, yaw2);
          double vx = (x2 - x) / DT, vy = (y2 - y) / DT, vz = (z2 - z) / DT;
          double vxy = std::hypot(vx, vy);
          double yawRate = wrap(yaw2 - yaw) / DT;

          double pT = -std::atan2(vz, std::max(vxy, 1.0));
          double rT = std::atan((vxy * yawRate) / 9.8);
          if (pT >  PITCH_MAX) pT =  PITCH_MAX;
          if (pT < -PITCH_MAX) pT = -PITCH_MAX;
          if (rT >  ROLL_MAX)  rT =  ROLL_MAX;
          if (rT < -ROLL_MAX)  rT = -ROLL_MAX;

          // alçak-geçiren yumuşatma (ani tavır zıplaması olmaz)
          double step = this->world->Physics()->GetMaxStepSize();
          double a = std::min(1.0, step / ATT_TAU);
          this->ihaPitch += a * (pT - this->ihaPitch);
          this->ihaRoll  += a * (rT - this->ihaRoll);
          roll = this->ihaRoll; pitch = this->ihaPitch;
        }
        model->SetWorldPose(ignition::math::Pose3d(x, y, z, roll, pitch, yaw));
        if (kv.first == "iha")
          this->SetFlatView("iha_view_footprint", x, y, 0.13, yaw);
      }
    }

    // Zaman-interp: t anındaki (x,y,z,yaw). Yaw en kısa açı farkıyla interp edilir.
    private: static void samplePose(const std::vector<Waypoint> &wps, double t,
                                    double &x, double &y, double &z, double &yaw)
    {
      if (t <= wps.front().t)
      { x = wps.front().x; y = wps.front().y; z = wps.front().z; yaw = wps.front().yaw; return; }
      if (t >= wps.back().t)
      { x = wps.back().x; y = wps.back().y; z = wps.back().z; yaw = wps.back().yaw; return; }
      x = wps.back().x; y = wps.back().y; z = wps.back().z; yaw = wps.back().yaw;
      for (size_t i = 0; i + 1 < wps.size(); ++i)
      {
        if (t >= wps[i].t && t <= wps[i + 1].t)
        {
          double dt = wps[i + 1].t - wps[i].t;
          double f = (dt > 1e-9) ? (t - wps[i].t) / dt : 0.0;
          x = wps[i].x + (wps[i + 1].x - wps[i].x) * f;
          y = wps[i].y + (wps[i + 1].y - wps[i].y) * f;
          z = wps[i].z + (wps[i + 1].z - wps[i].z) * f;
          yaw = wps[i].yaw + wrap(wps[i + 1].yaw - wps[i].yaw) * f;
          return;
        }
      }
    }
  };

  GZ_REGISTER_WORLD_PLUGIN(NavitasAnim)
}

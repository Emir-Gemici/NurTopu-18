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
#include <limits>

namespace gazebo
{
  struct Waypoint { double t, x, y, z, yaw; };

  class NavitasAnim : public WorldPlugin
  {
    private: physics::WorldPtr world;
    private: event::ConnectionPtr updateConn;
    private: std::map<std::string, std::vector<Waypoint>> traj;
    private: std::map<std::string, size_t> ikaIdx;     // İKA waypoint takip indeksi
    private: std::map<std::string, double> ikaBestDist;
    private: std::map<std::string, double> ikaLastProgressT;
    private: std::map<std::string, bool> ikaStuck;
    private: double ihaRoll = 0.0, ihaPitch = 0.0;     // İHA tavır (alçak-geçiren durum)

    // İKA ROTA KAYNAĞI — dürüst haritalandırma zinciri:
    //   İHA tarama kareleri → host'ta iha_haritala.py (mozaik + model) → /tmp/navitas_route
    //   (satır başına "x y" DÜNYA koordinatı, güney→kuzey). Dosya gelirse İKA MODELİN
    //   haritasını sürer. Yarışma profilinde (allowGroundTruthFallback=false) geçerli
    //   dinamik rota gelmezse SDF'deki geometrinin kullanılması yasaktır; İKA güvenli
    //   şekilde yerinde bekler. Açık demo modunda ROUTE_WAIT sonunda ground-truth'a düşülür.
    private: std::map<std::string, std::string> ikaRouteSrc;   // "bekliyor"|"model"|"yok"|"fallback"
    private: const char *ROUTE_FILE = "/tmp/navitas_route";
    private: const double ROUTE_WAIT = 45.0;   // s — İHA inişinden sonra rota bekleme süresi
    private: bool requireManualTrigger = true;
    private: bool allowGroundTruthFallback = false;
    private: std::string triggerFile = "/tmp/navitas_ika_trigger";

    // İHA tavır limitleri (gerçekçi küçük sabit kanat)
    private: const double PITCH_MAX = 0.45;   // rad (~26°) burun yukarı/aşağı
    private: const double ROLL_MAX  = 0.70;   // rad (~40°) yatış
    private: const double ATT_TAU   = 0.25;   // s — tavır yumuşatma zaman sabiti

    // İKA sürüş parametreleri
    // İLERİ: SINIRLI KUVVET (AddForce) → katı engeli aşamaz, içinden geçemez (gerçek fizik).
    // DÖNÜŞ: SetAngularVel (doğrudan) → skid-steer 4 sabit teker yüksek sürtünmede tork ile
    //        dönemeyeceği için yaw doğrudan atanır (çarpışma bütünlüğü ileri eksende korunur).
    private: const double IKA_SPEED    = 1.1;   // m/s — gerçekçi rover seyir hızı
    private: const double WP_RADIUS    = 0.5;   // m — costmap takip payını aşmaz
    private: const double FINAL_WP_RADIUS = 0.3; // m — HB son yaklaşım toleransı
    private: const double YAW_GAIN     = 2.5;   // hedef yaw hatasından açısal hıza kazanç
    private: const double YAW_RATE_MAX = 1.6;   // rad/s — dönüş hız limiti
    private: const double FORCE_GAIN   = 60.0;  // (v_hedef - v) → kuvvet kazancı (N/(m/s))
    private: const double FORCE_MAX    = 80.0;  // N — motor traksiyon limiti (engeli AŞAMAZ)

    public: void Load(physics::WorldPtr _world, sdf::ElementPtr _sdf) override
    {
      this->world = _world;
      if (_sdf->HasElement("require_manual_trigger"))
        this->requireManualTrigger = _sdf->Get<bool>("require_manual_trigger");
      if (_sdf->HasElement("allow_ground_truth_fallback"))
        this->allowGroundTruthFallback = _sdf->Get<bool>("allow_ground_truth_fallback");
      if (_sdf->HasElement("trigger_file"))
        this->triggerFile = _sdf->Get<std::string>("trigger_file");
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
            if (isIka(name))
            {
              this->ikaRouteSrc[name] = "bekliyor";
              this->ikaBestDist[name] = std::numeric_limits<double>::infinity();
              this->ikaLastProgressT[name] = 0.0;
              this->ikaStuck[name] = false;
            }
            gzmsg << "[navitas_anim] '" << name << "' " << wps.size()
                  << " yol noktası.\n";
          }
        }
      }
      this->updateConn = event::Events::ConnectWorldUpdateBegin(
          std::bind(&NavitasAnim::OnUpdate, this));
      gzmsg << "[navitas_anim] manuel İKA tetik=" << this->requireManualTrigger
            << " fallback=" << this->allowGroundTruthFallback
            << " dosya=" << this->triggerFile << "\n";
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
      this->ikaBestDist[name] = std::numeric_limits<double>::infinity();
      this->ikaLastProgressT[name] = this->world->SimTime().Double();
      this->ikaStuck[name] = false;
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
        {
          if (isIka(kv.first))
          {
            if (auto m = this->world->ModelByName(kv.first))
            {
              auto p = m->WorldPose().Pos();
              auto v = m->WorldLinearVel();
              f << kv.first << " x=" << p.X() << " y=" << p.Y()
                << " v=" << std::hypot(v.X(), v.Y())
                << " wp=" << this->ikaIdx[kv.first]
                << " rota=" << this->ikaRouteSrc[kv.first]
                << " tetik=" << ((!this->requireManualTrigger ||
                                   std::ifstream(this->triggerFile).good()) ? "hazir" : "bekliyor")
                // rota bitti (son wp'ye ulaşıldı) → kayıt betiği klibi erken keser
                << (this->ikaIdx[kv.first] >= kv.second.size() ? " durum=BITTI" :
                    (this->ikaStuck[kv.first] ? " durum=TIKANDI" :
                     (this->ikaRouteSrc[kv.first] == "yok" ? " durum=ROTA_YOK" : "")))
                << "\n";
            }
          }
          else if (kv.first == "aftershock_barrier")
          {
            if (auto m = this->world->ModelByName(kv.first))
            {
              auto p = m->WorldPose().Pos();
              f << "aftershock_barrier x=" << p.X() << " y=" << p.Y()
                << " z=" << p.Z() << "\n";
            }
          }
        }
        // (İHA poz logu artık navitas_scan_cam plugin'inde — kareyle AYNI olayda
        //  yazılır, birebir senkron; buradaki 1 Hz kopya kaldırıldı.)
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

          // ── ROTA KAYNAĞI: önce MODEL haritası (/tmp/navitas_route). Yarışma
          // profilinde (allowGroundTruthFallback=false) rota inişe kadar gelmezse
          // SDF ground-truth ASLA sürülmez, İKA kalıcı olarak güvenli durur; yalnız
          // açık demo modunda ROUTE_WAIT kadar beklenip ground-truth'a düşülür. ──
          std::string &src = this->ikaRouteSrc[kv.first];
          if (src == "bekliyor")
          {
            if (!this->tryLoadRoute(kv.first))
            {
              // Yarışma profili: rota İHA havadayken gelmiş olmalıdır; inişten sonra
              // ek bekleme yok. Yalnız açık demo fallback modunda ROUTE_WAIT beklenir.
              const double routeWait = this->allowGroundTruthFallback ? ROUTE_WAIT : 0.0;
              if (t < startT + routeWait)
              {
                model->SetLinearVel(ignition::math::Vector3d::Zero);
                model->SetAngularVel(ignition::math::Vector3d::Zero);
                continue;                        // İHA haritası henüz gelmedi — bekle
              }
              if (!this->allowGroundTruthFallback)
              {
                src = "yok";
                gzerr << "[navitas_anim] '" << kv.first << "' MODEL rotası "
                      << "İHA inişine kadar gelmedi → ROTA_YOK, araç güvenli duruşta "
                         "(SDF ground-truth rota KULLANILMADI).\n";
                model->SetLinearVel(ignition::math::Vector3d::Zero);
                model->SetAngularVel(ignition::math::Vector3d::Zero);
                continue;
              }
              src = "fallback";
              this->ikaBestDist[kv.first] = std::numeric_limits<double>::infinity();
              this->ikaLastProgressT[kv.first] = t;
              gzmsg << "[navitas_anim] '" << kv.first << "' MODEL rotası "
                    << ROUTE_WAIT << "s içinde gelmedi → DEMO ground-truth FALLBACK "
                       "(model başarısı SAYILMAZ).\n";
            }
          }

          if (src == "yok")
          {
            model->SetLinearVel(ignition::math::Vector3d::Zero);
            model->SetAngularVel(ignition::math::Vector3d::Zero);
            continue;
          }

          // Şartname §2.2.5: İHA yere indikten sonra YKS operatörü görevi manuel
          // tetikler; tetikten sonra sürüş bütünüyle otonomdur. Dosya, kayıt/YKS
          // sürecinin açık bir olay üretmesini sağlar ve otomatik zaman başlangıcını önler.
          if (this->requireManualTrigger && !std::ifstream(this->triggerFile).good())
          {
            model->SetLinearVel(ignition::math::Vector3d::Zero);
            model->SetAngularVel(ignition::math::Vector3d::Zero);
            continue;
          }

          size_t &idx = this->ikaIdx[kv.first];
          if (idx < 1) idx = 1;
          if (this->ikaStuck[kv.first])
          {
            model->SetLinearVel(ignition::math::Vector3d::Zero);
            model->SetAngularVel(ignition::math::Vector3d::Zero);
            continue;
          }
          if (idx >= wps.size())
          {
            model->SetLinearVel(ignition::math::Vector3d::Zero);   // HB'ye ulaştı, dur
            model->SetAngularVel(ignition::math::Vector3d::Zero);
            continue;
          }
          if (!link) continue;
          auto pose = model->WorldPose();
          double cx = pose.Pos().X(), cy = pose.Pos().Y();
          double dx = wps[idx].x - cx, dy = wps[idx].y - cy;
          double dist = std::hypot(dx, dy);
          if (dist + 0.05 < this->ikaBestDist[kv.first])
          {
            this->ikaBestDist[kv.first] = dist;
            this->ikaLastProgressT[kv.first] = t;
          }
          if (t - this->ikaLastProgressT[kv.first] > 15.0)
          {
            this->ikaStuck[kv.first] = true;
            gzerr << "[navitas_anim] '" << kv.first << "' 15s ilerleme yok → TIKANDI\n";
            model->SetLinearVel(ignition::math::Vector3d::Zero);
            model->SetAngularVel(ignition::math::Vector3d::Zero);
            continue;
          }
          double hedefRadius = (idx + 1 >= wps.size()) ? FINAL_WP_RADIUS : WP_RADIUS;
          if (dist < hedefRadius)
          {
            idx++;
            this->ikaBestDist[kv.first] = std::numeric_limits<double>::infinity();
            this->ikaLastProgressT[kv.first] = t;
            continue;
          }

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

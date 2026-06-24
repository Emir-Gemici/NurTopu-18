// Navitas TEKNOFEST 2026 — Kinematik Animasyon Dünya Plugin'i
//
// Modelleri (İHA, İKA) zamana bağlı yol noktaları boyunca pürüzsüz hareket
// ettirir. Her simülasyon adımında SetWorldPose çağrılır → video fps'inden
// bağımsız akıcı, deterministik, her zaman tamamlanan hareket.
//
// CLI tabanlı kontrolün (~0.8s/çağrı) aksine kayıt için güvenilirdir.
// Sadece kayıt dünyalarında kullanılır (world_generator.py --record).
//
// SDF kullanımı:
//   <plugin name="navitas_anim" filename="libnavitas_anim.so">
//     <model name="iha">
//       <waypoint>t x y z yaw</waypoint>
//       ...
//     </model>
//     <model name="ika"> ... </model>
//   </plugin>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <ignition/math/Pose3.hh>
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

    public: void Load(physics::WorldPtr _world, sdf::ElementPtr _sdf) override
    {
      this->world = _world;

      if (_sdf->HasElement("model"))
      {
        for (auto m = _sdf->GetElement("model"); m;
             m = m->GetNextElement("model"))
        {
          std::string name = m->Get<std::string>("name");
          std::vector<Waypoint> wps;
          if (m->HasElement("waypoint"))
          {
            for (auto w = m->GetElement("waypoint"); w;
                 w = w->GetNextElement("waypoint"))
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
            gzmsg << "[navitas_anim] '" << name << "' için "
                  << wps.size() << " yol noktası yüklendi.\n";
          }
        }
      }

      this->updateConn = event::Events::ConnectWorldUpdateBegin(
          std::bind(&NavitasAnim::OnUpdate, this));
    }

    private: void OnUpdate()
    {
      double t = this->world->SimTime().Double();

      for (auto &kv : this->traj)
      {
        auto model = this->world->ModelByName(kv.first);
        if (!model)
          continue;

        const auto &wps = kv.second;
        double x, y, z, yaw;

        if (t <= wps.front().t)
        {
          x = wps.front().x; y = wps.front().y;
          z = wps.front().z; yaw = wps.front().yaw;
        }
        else if (t >= wps.back().t)
        {
          x = wps.back().x; y = wps.back().y;
          z = wps.back().z; yaw = wps.back().yaw;
        }
        else
        {
          x = wps.back().x; y = wps.back().y;
          z = wps.back().z; yaw = wps.back().yaw;
          for (size_t i = 0; i + 1 < wps.size(); ++i)
          {
            if (t >= wps[i].t && t <= wps[i + 1].t)
            {
              double dt = wps[i + 1].t - wps[i].t;
              double f = (dt > 1e-9) ? (t - wps[i].t) / dt : 0.0;
              x = wps[i].x + (wps[i + 1].x - wps[i].x) * f;
              y = wps[i].y + (wps[i + 1].y - wps[i].y) * f;
              z = wps[i].z + (wps[i + 1].z - wps[i].z) * f;
              double dyaw = wps[i + 1].yaw - wps[i].yaw;
              while (dyaw > M_PI)  dyaw -= 2 * M_PI;
              while (dyaw < -M_PI) dyaw += 2 * M_PI;
              yaw = wps[i].yaw + dyaw * f;
              break;
            }
          }
        }

        model->SetWorldPose(ignition::math::Pose3d(x, y, z, 0, 0, yaw));
      }
    }
  };

  GZ_REGISTER_WORLD_PLUGIN(NavitasAnim)
}

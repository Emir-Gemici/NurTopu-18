// Navitas — İHA tarama kamerası SENKRON plugin'i.
//
// SORUN (v15): Gazebo'nun <save enabled> kare kaydı ile plugin'in 1 Hz poz logu
// AYRI saatlerde koşuyordu → kare↔poz eşleşmesi ~1 s (≈10 m) kayıyor, ortomozaik
// bozuluyordu (İHA-haritalama yanlış rota → İKA duvara sürdü).
//
// ÇÖZÜM: kare kaydını ve poz logunu AYNI olayda yap. Her yeni karede (OnNewFrame):
//   1) kareyi /tmp/iha_scan/scan_<n>.jpg olarak kaydet,
//   2) O ANIN sim zamanını + İHA dünya pozunu /tmp/iha_scan/poses.csv'ye ekle:
//        n,t,x,y,z,yaw
// Böylece n. kare ↔ n. satır BİREBİR; ofset kalibrasyonuna gerek kalmaz.
//
// SDF (models/iha/model.sdf, scan_camera sensörünün içinde):
//   <plugin name="navitas_scan_cam" filename="libnavitas_scan_cam.so"/>

#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo/plugins/CameraPlugin.hh>
#include <gazebo/rendering/Camera.hh>
#include <cstdio>
#include <fstream>
#include <sys/stat.h>

namespace gazebo
{
  class NavitasScanCam : public CameraPlugin
  {
    private: unsigned int n = 0;
    private: physics::WorldPtr world;

    public: void Load(sensors::SensorPtr _sensor, sdf::ElementPtr _sdf) override
    {
      CameraPlugin::Load(_sensor, _sdf);
      mkdir("/tmp/iha_scan", 0777);
      this->world = physics::get_world();          // tek dünya (navitas_arena)
      gzmsg << "[navitas_scan_cam] hazır — kare+poz SENKRON kayıt (/tmp/iha_scan)\n";
    }

    public: void OnNewFrame(const unsigned char * /*_image*/,
                            unsigned int /*_w*/, unsigned int /*_h*/,
                            unsigned int /*_d*/, const std::string & /*_fmt*/) override
    {
      if (!this->world) return;
      char path[64];
      std::snprintf(path, sizeof(path), "/tmp/iha_scan/scan_%05u.jpg", this->n);
      this->camera->SaveFrame(path);               // kare TAM ŞU ANKİ render

      double t = this->world->SimTime().Double();
      double x = 0, y = 0, z = 0, yaw = 0;
      if (auto m = this->world->ModelByName("iha"))
      {
        auto p = m->WorldPose();
        x = p.Pos().X(); y = p.Pos().Y(); z = p.Pos().Z(); yaw = p.Rot().Yaw();
      }
      std::ofstream f("/tmp/iha_scan/poses.csv", std::ios::app);
      f << this->n << "," << t << "," << x << "," << y << "," << z << "," << yaw << "\n";
      this->n++;
    }
  };

  GZ_REGISTER_SENSOR_PLUGIN(NavitasScanCam)
}

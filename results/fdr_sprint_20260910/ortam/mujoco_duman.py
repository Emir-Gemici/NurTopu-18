"""MuJoCo ekransiz render duman testi: kutu + kamera sahnesi -> PNG; drone STL mesh yukleme."""
import sys, time, os
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import mujoco
print("mujoco", mujoco.__version__)

XML = """
<mujoco>
  <visual><global offwidth="1280" offheight="720"/></visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1=".2 .3 .4" rgb2=".1 .15 .2" width="300" height="300"/>
    <material name="grid" texture="grid" texrepeat="8 8" reflectance=".2"/>
  </asset>
  <worldbody>
    <light pos="0 0 10" dir="0 0 -1" diffuse="1 1 1"/>
    <geom type="plane" size="30 30 0.1" material="grid"/>
    <body name="h" pos="5 5 0.01"><geom type="box" size="1 1 0.01" rgba="0.9 0.1 0.1 1"/></body>
    <body name="moloz" pos="-4 3 0.3"><geom type="box" size="0.6 0.4 0.3" rgba="0.5 0.5 0.5 1"/></body>
    <body name="kamera_tasiyici" pos="0 0 30">
      <camera name="iha_kam" pos="0 0 0" euler="0 0 0" fovy="67.3"/>
    </body>
  </worldbody>
</mujoco>
"""
m = mujoco.MjModel.from_xml_string(XML)
d = mujoco.MjData(m)
mujoco.mj_forward(m, d)
t0 = time.time()
r = mujoco.Renderer(m, height=720, width=1280)
r.update_scene(d, camera="iha_kam")
img = r.render()
dt = time.time() - t0
print("render", img.shape, img.dtype, f"{dt*1000:.0f} ms ilk kare; benzersiz renk", len(np.unique(img.reshape(-1, 3), axis=0)))
import cv2
out = os.path.join(os.path.dirname(__file__), "mujoco_duman.png")
cv2.imwrite(out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
print("yazildi", out)
# 10 kare hiz
t0 = time.time()
for _ in range(10):
    r.update_scene(d, camera="iha_kam"); r.render()
print(f"10 kare {(time.time()-t0)*1000:.0f} ms")
r.close()

import trimesh
stl = r"O:\navitas\dronesolid\Drone_Frame_STL.STL"
mesh = trimesh.load(stl)
print("STL", os.path.basename(stl), "ucgen", len(mesh.faces), "boyut mm", np.round(mesh.extents, 1), "su gecirmez", mesh.is_watertight)

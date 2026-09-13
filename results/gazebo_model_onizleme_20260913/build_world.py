import re

OUT = "/tmp/claude-1000/-home-trs-projects-navitas-unified-20260822/ef38ad42-a7f6-4810-a5d2-5108c40101ae/scratchpad/gz_out"

def extract_model(path, new_pose, name_suffix=""):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"(<model name='[^']*')(>)(.*)</model>", txt, re.S)
    head, _, body = m.group(1), m.group(2), m.group(3)
    inner = f"{head}>\n<static>true</static>\n<pose>{new_pose}</pose>\n{body}</model>"
    return inner

ika = extract_model(f"{OUT}/ika.sdf", "0 0 0.9 1.5708 0 0")
manc = extract_model(f"{OUT}/manc.sdf", "5 0 0 0 0 0")
uav = extract_model(f"{OUT}/uav.sdf", "-6 3 1.2 0 0 2.6")

def camera(name, pose, path):
    return f"""
<model name="{name}"><static>true</static>
  <pose>{pose}</pose>
  <link name="link">
    <sensor name="cam" type="camera">
      <camera>
        <horizontal_fov>0.9</horizontal_fov>
        <image><width>1280</width><height>960</height><format>R8G8B8</format></image>
        <clip><near>0.05</near><far>200</far></clip>
        <save enabled="true"><path>{path}</path></save>
      </camera>
      <always_on>1</always_on>
      <update_rate>0.5</update_rate>
    </sensor>
  </link>
</model>"""

world = f"""<?xml version="1.0"?>
<sdf version="1.6">
  <world name="onizleme">
    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>0</real_time_factor>
    </physics>
    <scene>
      <ambient>0.6 0.6 0.6 1</ambient>
      <background>0.75 0.82 0.9 1</background>
      <shadows>true</shadows>
      <grid>false</grid>
    </scene>
    <include><uri>model://sun</uri></include>
    <include><uri>model://ground_plane</uri></include>

    {ika}
    {manc}
    {uav}

    {camera("cam_ika", "-1.89 -1.59 1.70 0 0.314 0.698", "/evidence/ika")}
    {camera("cam_manc", "2.25 3.28 1.39 0 0.314 -0.873", "/evidence/manc")}
    {camera("cam_uav", "-2.95 4.11 2.51 0 0.384 -2.793", "/evidence/uav")}
    {camera("cam_all", "2 -13 6 0 0.35 1.75", "/evidence/all")}
  </world>
</sdf>
"""

open(f"{OUT}/onizleme.world", "w", encoding="utf-8").write(world)
print("written", f"{OUT}/onizleme.world", len(world), "bytes")

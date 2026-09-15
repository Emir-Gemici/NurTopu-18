"""NEDEN: Gazebo Classic için UV'li, tekrar üretilebilir yüzey ve mesh varlıkları."""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np


MATERIALS = {
    "concrete": {"rgb": (155, 150, 138), "mu": 0.8, "restitution": 0.05},
    "brick": {"rgb": (135, 87, 64), "mu": 0.75, "restitution": 0.04},
    "timber": {"rgb": (110, 87, 60), "mu": 0.6, "restitution": 0.08},
    "steel": {"rgb": (95, 88, 77), "mu": 0.5, "restitution": 0.05},
    "asphalt": {"rgb": (113, 111, 103), "mu": 0.85, "restitution": 0.02},
    "soil": {"rgb": (145, 132, 109), "mu": 0.7, "restitution": 0.02},
}


def transform(pose):
    values = [float(value) for value in (pose or "0 0 0 0 0 0").split()]
    if len(values) != 6 or not np.isfinite(values).all():
        raise ValueError(f"Geçersiz poz: {pose}")
    px, py, pz, roll, pitch, yaw = values
    cosine = math.cos
    sine = math.sin
    rotation_x = np.array([[1, 0, 0], [0, cosine(roll), -sine(roll)],
                           [0, sine(roll), cosine(roll)]])
    rotation_y = np.array([[cosine(pitch), 0, sine(pitch)], [0, 1, 0],
                           [-sine(pitch), 0, cosine(pitch)]])
    rotation_z = np.array([[cosine(yaw), -sine(yaw), 0],
                           [sine(yaw), cosine(yaw), 0], [0, 0, 1]])
    result = np.eye(4)
    result[:3, :3] = rotation_z @ rotation_y @ rotation_x
    result[:3, 3] = [px, py, pz]
    return result


def transform_vertices(vertices, matrix):
    return np.asarray(vertices) @ matrix[:3, :3].T + matrix[:3, 3]


def load_obj(path):
    vertices, triangles = [], []
    for line in Path(path).read_text().splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            vertices.append([float(value) for value in fields[1:4]])
        elif fields[0] == "f":
            indices = [int(value.split("/")[0]) for value in fields[1:]]
            indices = [value - 1 if value > 0 else len(vertices) + value for value in indices]
            triangles.extend((indices[0], indices[index], indices[index + 1])
                             for index in range(1, len(indices) - 1))
    points = np.asarray(vertices, dtype=float)
    faces = np.asarray(triangles, dtype=int)
    if not len(points) or not len(faces) or not np.isfinite(points).all():
        raise ValueError(f"Boş/geçersiz OBJ: {path}")
    if faces.min() < 0 or faces.max() >= len(points):
        raise ValueError(f"Geçersiz yüz indeksi: {path}")
    return points, faces


def hollow_pipe(bounds, segments=16):
    minimum, maximum = np.asarray(bounds)
    center = (minimum + maximum) / 2
    radius = float(min(maximum[1:] - minimum[1:]) / 2)
    if radius <= 0 or maximum[0] <= minimum[0]:
        raise ValueError("Boru boyutları pozitif olmalı")
    vertices, triangles = [], []
    for axial in (minimum[0], maximum[0]):
        for ring_radius in (radius, radius * 0.72):
            for index in range(segments):
                angle = 2 * math.pi * index / segments
                vertices.append((axial, center[1] + ring_radius * math.cos(angle),
                                 center[2] + ring_radius * math.sin(angle)))
    for index in range(segments):
        following = (index + 1) % segments
        quads = ((index, following, 2 * segments + following, 2 * segments + index),
                 (segments + following, segments + index, 3 * segments + index, 3 * segments + following),
                 (following, index, segments + index, segments + following),
                 (2 * segments + index, 2 * segments + following, 3 * segments + following, 3 * segments + index))
        for first, second, third, fourth in quads:
            triangles.extend(((first, second, third), (first, third, fourth)))
    return np.asarray(vertices), np.asarray(triangles, dtype=int)


def write_collada(path, vertices, triangles, uv_scale=1.0, ground_extent=None):
    points = np.asarray(vertices, dtype=float)[np.asarray(triangles)].reshape(-1, 3)
    grouped = points.reshape(-1, 3, 3)
    normals = np.cross(grouped[:, 1] - grouped[:, 0], grouped[:, 2] - grouped[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    if not np.isfinite(points).all() or np.any(lengths < 1e-10):
        raise ValueError("Dejenere veya sonlu olmayan mesh")
    normals /= lengths[:, None]
    if ground_extent is not None:
        uv = points[:, :2] / ground_extent + 0.5
    else:
        axes = np.argmax(np.abs(normals), axis=1)
        uv = np.empty((len(points), 2))
        for index, axis in enumerate(axes):
            plane = [component for component in range(3) if component != axis]
            uv[index * 3:index * 3 + 3] = grouped[index][:, plane] / uv_scale
    normals = np.repeat(normals, 3, axis=0)
    namespace = "http://www.collada.org/2005/11/COLLADASchema"
    ET.register_namespace("", namespace)
    root = ET.Element("COLLADA", xmlns=namespace, version="1.4.1")
    asset = ET.SubElement(root, "asset")
    ET.SubElement(asset, "created").text = "2026-09-10T00:00:00Z"
    ET.SubElement(asset, "modified").text = "2026-09-10T00:00:00Z"
    ET.SubElement(asset, "unit", name="meter", meter="1")
    ET.SubElement(asset, "up_axis").text = "Z_UP"
    library = ET.SubElement(root, "library_geometries")
    geometry = ET.SubElement(library, "geometry", id="surface", name="surface")
    mesh = ET.SubElement(geometry, "mesh")
    for name, array, labels in (("positions", points, "XYZ"),
                                ("normals", normals, "XYZ"), ("uv", uv, "ST")):
        source = ET.SubElement(mesh, "source", id=name)
        ET.SubElement(source, "float_array", id=name + "-array", count=str(array.size)).text = (
            " ".join(f"{value:.6f}" for value in array.flat))
        technique = ET.SubElement(source, "technique_common")
        accessor = ET.SubElement(technique, "accessor", source="#" + name + "-array",
                                 count=str(len(array)), stride=str(len(labels)))
        for label in labels:
            ET.SubElement(accessor, "param", name=label, type="float")
    vertex_node = ET.SubElement(mesh, "vertices", id="vertices")
    ET.SubElement(vertex_node, "input", semantic="POSITION", source="#positions")
    faces = ET.SubElement(mesh, "triangles", count=str(len(grouped)))
    for offset, (semantic, source) in enumerate((('VERTEX', '#vertices'),
                                                ('NORMAL', '#normals'), ('TEXCOORD', '#uv'))):
        attributes = {"semantic": semantic, "source": source, "offset": str(offset)}
        if semantic == "TEXCOORD":
            attributes["set"] = "0"
        ET.SubElement(faces, "input", attributes)
    ET.SubElement(faces, "p").text = " ".join(str(index) for index in range(len(points)) for _ in range(3))
    scenes = ET.SubElement(root, "library_visual_scenes")
    scene = ET.SubElement(scenes, "visual_scene", id="scene")
    node = ET.SubElement(scene, "node", id="surface-node")
    ET.SubElement(node, "instance_geometry", url="#surface")
    ET.SubElement(ET.SubElement(root, "scene"), "instance_visual_scene", url="#scene")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def texture(seed, material, size=1024, paths=None, extent=50.0):
    rng = np.random.default_rng(seed)
    noise = np.zeros((size, size), np.float32)
    amplitudes = (3, 3, 2, 4) if material == "soil" else (6, 4, 3, 3)
    for cells, amplitude in zip((4, 17, 81, size), amplitudes):
        layer = rng.normal(0, 1, (cells, cells)).astype(np.float32)
        noise += amplitude * cv2.resize(layer, (size, size), interpolation=cv2.INTER_CUBIC)
    base = np.array(MATERIALS[material]["rgb"], np.float32)
    rgb = base + noise[..., None]
    if material in ("soil", "asphalt"):
        dust = cv2.resize(rng.uniform(0, 1, (9, 9)).astype(np.float32),
                          (size, size), interpolation=cv2.INTER_CUBIC)
        rgb += dust[..., None] * np.array([9, 7, 3])
        if paths:
            mask = np.zeros((size, size), np.uint8)
            for route in paths.values():
                coordinates = np.round((np.asarray(route) / extent + 0.5) * (size - 1)).astype(np.int32)
                cv2.polylines(mask, [coordinates], False, 255, max(1, round(size * 2.8 / extent)), cv2.LINE_AA)
            mask = cv2.GaussianBlur(mask, (0, 0), size * 0.55 / extent).astype(np.float32) / 255
            rgb -= mask[..., None] * np.array([9, 8, 7])
        if material == "asphalt":
            for _ in range(size // 18):
                start = rng.integers(0, size, 2).astype(float)
                points = [start.copy()]
                direction = rng.uniform(0, 2 * math.pi)
                for _ in range(int(rng.integers(3, 11))):
                    direction += rng.uniform(-0.6, 0.6)
                    start += rng.uniform(3, 17) * np.array([math.cos(direction), math.sin(direction)])
                    points.append(start.copy())
                cv2.polylines(rgb, [np.asarray(points, np.int32)], False, (72, 69, 63), 1, cv2.LINE_AA)
    elif material == "concrete":
        for _ in range(size * 3):
            center = tuple(int(value) for value in rng.integers(0, size, 2))
            shade = float(rng.uniform(90, 180))
            cv2.circle(rgb, center, int(rng.integers(1, 3)), (shade, shade - 2, shade - 7), -1)
    elif material == "timber":
        grain = cv2.resize(rng.normal(0, 9, (size, 8)).astype(np.float32), (size, size))
        rgb += grain[..., None]
    elif material == "steel":
        corrosion = cv2.resize(rng.random((27, 27)).astype(np.float32), (size, size), interpolation=cv2.INTER_CUBIC)
        rust = np.clip((corrosion - 0.48) * 2.5, 0, 1)
        rgb = rgb * (1 - rust[..., None]) + np.array([119, 65, 36]) * rust[..., None]
    elif material == "brick":
        for row in range(0, size, max(1, size // 8)):
            rgb[row:row + 3] = [166, 153, 131]
            offset = (row // max(1, size // 8) % 2) * size // 8
            for column in range(offset, size, max(1, size // 4)):
                rgb[row:row + size // 8, column:column + 3] = [166, 153, 131]
    return cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)


def write_material(path, name, texture_name, metallic=False):
    specular = "0.22 0.20 0.18 1 22" if metallic else "0.025 0.025 0.025 1 8"
    path.write_text(f"""material {name}
{{
  technique
  {{
    pass
    {{
      ambient 1 1 1 1
      diffuse 1 1 1 1
      specular {specular}
      texture_unit
      {{
        texture {texture_name}
        filtering anisotropic
        max_anisotropy 8
        tex_address_mode wrap
      }}
    }}
  }}
}}
""")

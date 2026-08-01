#!/usr/bin/env python3
"""Data-driven Gazebo scenario profiles with strict, fail-fast validation."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parents[1] / "scenarios"
ZONE_NAMES = ("kolay", "orta", "zor")

DEFAULT_PROFILE = {
    "schema_version": 1,
    "id": "baseline",
    "author": "navitas",
    "title_tr": "Temel gündüz senaryosu",
    "description_tr": "Resmî boyutlarda, açık havada temel görev doğrulaması.",
    "seed": 42,
    "active_zone": "orta",
    "map_ids": {"kolay": 1, "orta": 2, "zor": 3},
    "environment": {
        "ambient": [0.50, 0.50, 0.50, 1.0],
        "background": [0.75, 0.80, 0.85, 1.0],
        "sun_diffuse": [0.90, 0.90, 0.85, 1.0],
        "sun_direction": [-0.4, 0.2, -0.9],
        "fog": {"enabled": False, "type": "linear", "color": [0.7, 0.7, 0.7, 1.0],
                "start": 35.0, "end": 140.0, "density": 0.0},
        "wind": [0.0, 0.0, 0.0],
        "ground_friction": 0.8,
        "ground_color": [0.30, 0.29, 0.27],
    },
    "terrain": {
        "layout": "field",
        "lane_width_multiplier": 1.0,
        "debris_multiplier": 1.0,
        "rubble_height_multiplier": 1.0,
        "chicane_count": 5,
    },
    "flight": {
        "scan_altitude_m": 30.0,
        "scan_tilt_deg": 0.0,
        "lateral_jitter_m": 0.0,
    },
    "mission": {
        "require_manual_trigger": True,
        "allow_ground_truth_fallback": False,
        "route_delivery_delay_s": 0.5,
        "packet_loss_percent": 0,
        "dynamic_obstacle": "none",
    },
    "acceptance": [],
}


def _merge(base, override):
    out = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def _reject_unknown(template, value, path="profile"):
    if not isinstance(value, dict):
        return
    unknown = set(value) - set(template)
    if unknown:
        raise ValueError(f"{path}: bilinmeyen alan(lar): {sorted(unknown)}")
    for key, child in value.items():
        if isinstance(child, dict) and isinstance(template.get(key), dict):
            _reject_unknown(template[key], child, f"{path}.{key}")


def _finite_vector(value, size, name):
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"{name}: {size} elemanlı liste olmalı")
    if not all(isinstance(v, (int, float)) and abs(v) < 1e6 for v in value):
        raise ValueError(f"{name}: sonlu sayılardan oluşmalı")


def validate_profile(profile):
    if profile["schema_version"] != 1:
        raise ValueError("yalnız scenario schema_version=1 destekleniyor")
    if not profile["id"].replace("_", "").isalnum():
        raise ValueError("profile id yalnız harf, rakam ve alt çizgi içerebilir")
    if profile["active_zone"] not in ZONE_NAMES:
        raise ValueError(f"active_zone şu değerlerden biri olmalı: {ZONE_NAMES}")
    if set(profile["map_ids"]) != set(ZONE_NAMES):
        raise ValueError("map_ids kolay/orta/zor anahtarlarının tamamını içermeli")
    if not all(isinstance(v, int) and v > 0 for v in profile["map_ids"].values()):
        raise ValueError("map_ids pozitif tam sayı olmalı")
    for key, size in (("ambient", 4), ("background", 4), ("sun_diffuse", 4),
                      ("sun_direction", 3), ("wind", 3), ("ground_color", 3)):
        _finite_vector(profile["environment"][key], size, f"environment.{key}")
    fog = profile["environment"]["fog"]
    if fog["type"] not in ("linear", "exp", "exp2"):
        raise ValueError("fog.type linear, exp veya exp2 olmalı")
    _finite_vector(fog["color"], 4, "environment.fog.color")
    if profile["terrain"]["layout"] not in ("clean", "field"):
        raise ValueError("terrain.layout clean veya field olmalı")
    for key in ("lane_width_multiplier", "debris_multiplier", "rubble_height_multiplier"):
        if not 0.25 <= float(profile["terrain"][key]) <= 4.0:
            raise ValueError(f"terrain.{key} güvenli [0.25, 4.0] aralığında olmalı")
    if not 0 <= int(profile["mission"]["packet_loss_percent"]) <= 100:
        raise ValueError("packet_loss_percent 0..100 olmalı")
    if not 0 <= float(profile["mission"]["route_delivery_delay_s"]) <= 40:
        raise ValueError("route_delivery_delay_s 0..40 s olmalı")
    if profile["mission"]["dynamic_obstacle"] not in ("none", "aftershock_barrier"):
        raise ValueError("dynamic_obstacle yalnız none veya aftershock_barrier olabilir")
    return profile


def profile_files():
    return sorted(PROFILE_DIR.glob("*.json")) if PROFILE_DIR.exists() else []


def available_profiles():
    return [p.stem for p in profile_files()]


def load_profile(profile_id=None):
    if not profile_id or profile_id == "baseline":
        return validate_profile(deepcopy(DEFAULT_PROFILE))
    path = PROFILE_DIR / f"{profile_id}.json"
    if not path.is_file():
        raise ValueError(f"bilinmeyen senaryo profili: {profile_id}; mevcut={available_profiles()}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    _reject_unknown(DEFAULT_PROFILE, raw)
    merged = _merge(DEFAULT_PROFILE, raw)
    if merged["id"] != profile_id:
        raise ValueError(f"profil dosya adı/id uyuşmuyor: {path.name} != {merged['id']}")
    return validate_profile(merged)

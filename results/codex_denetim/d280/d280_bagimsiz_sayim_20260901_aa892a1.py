"""D-280 icin aa892a1 ham artefaktlarindan bagimsiz, salt-okunur sayim."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_suffix(".json")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one_model(doc: dict) -> dict:
    assert len(doc["modeller"]) == 1
    return next(iter(doc["modeller"].values()))


def states(model: dict) -> dict[str, str]:
    pairs = [
        (row["kare"], row.get("olceksiz_sebep") or "ROTA")
        for row in model["kareler"]
    ]
    assert len(pairs) == 59
    assert len(dict(pairs)) == 59
    return dict(pairs)


def main() -> int:
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    assert head == "aa892a1f6964450228b34d5904bccf9da506dd3e"

    hist_path = (
        ROOT
        / "scripts"
        / "olcum"
        / "results"
        / "t63"
        / "dji_kirsal_v1_kabul_verdikt.json"
    )
    cur_path = (
        ROOT
        / "results"
        / "codex_denetim"
        / "d280"
        / "d280_reaudit_20260901_aa892a1_kabul_verdikt.json"
    )
    hist = read_json(hist_path)
    cur = read_json(cur_path)
    h = hist["olcum"]
    c = cur["olcum"]

    aday = one_model(read_json(ROOT / "results/dji_kirsal/bakir_0038.json"))
    v35 = read_json(ROOT / "results/dji_kirsal/bakir_0038_taban.json")[
        "modeller"
    ]["navitas_seg_v35_best.pt"]
    aday_state = states(aday)
    v35_state = states(v35)
    assert set(aday_state) == set(v35_state)
    matrix = Counter(
        (v35_state[name], aday_state[name]) for name in sorted(aday_state)
    )
    categories = ("MASKE_YOK", "ROTA", "UC_BANT_TEMAS_YOK")
    row_totals = {
        state: sum(n for (old, _new), n in matrix.items() if old == state)
        for state in categories
    }
    col_totals = {
        state: sum(n for (_old, new), n in matrix.items() if new == state)
        for state in categories
    }

    csv_path = ROOT / "codes/runs/segment/dji_kirsal_v1/results.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        csv_rows = [
            {key.strip(): value.strip() for key, value in row.items()}
            for row in csv.DictReader(stream)
        ]
    map_key = "metrics/mAP50-95(M)"
    max_map_row = max(csv_rows, key=lambda row: float(row[map_key]))

    best_path = ROOT / "codes/runs/segment/dji_kirsal_v1/weights/best.pt"
    checkpoint = torch.load(best_path, map_location="cpu", weights_only=False)
    train_metrics = checkpoint["train_metrics"]
    common = sorted(key for key in train_metrics if key in csv_rows[0])
    matching_epochs = [
        int(float(row["epoch"]))
        for row in csv_rows
        if all(
            math.isclose(
                float(row[key]),
                float(train_metrics[key]),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            for key in common
        )
    ]

    comparison_path = ROOT / "results/dji_kirsal/kiyas_109.txt"
    comparison = {}
    for line in comparison_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("t127_temiz ") or line.startswith("dji_kirsal_v1 "):
            name, body = line.split(" ", 1)
            comparison[name] = json.loads(body)
    v35_ground = comparison["t127_temiz"]["figur_zemin_orani"]
    dji_ground = comparison["dji_kirsal_v1"]["figur_zemin_orani"]
    ratio = dji_ground / v35_ground
    t127_path = ROOT / "codes/runs/segment/t127_temiz/weights/best.pt"
    v35_path = ROOT / "models/navitas_seg_v35_best.pt"

    result = {
        "head": head,
        "historical_artifact": str(hist_path),
        "current_artifact": str(cur_path),
        "historical_verdikt": hist["verdikt"],
        "current_verdikt": cur["verdikt"],
        "historical_vs_current_K0_K5": {
            "K0": {
                "historical_gate": hist["gecti"]["K0"],
                "current_gate": cur["gecti"]["K0"],
                "historical_figur": h["K0"]["figur"],
                "current_figur": c["K0"]["figur"],
                "historical_raw_bos_n": [
                    h["K0"]["raw_frames"]["bos"],
                    h["K0"]["raw_frames"]["n"],
                ],
                "current_raw_bos_n": [
                    c["K0"]["raw_frames"]["bos"],
                    c["K0"]["raw_frames"]["n"],
                ],
                "historical_cp_bos_n": [
                    h["K0"]["copy_paste"]["bos"],
                    h["K0"]["copy_paste"]["n"],
                ],
                "current_cp_bos_n": [
                    c["K0"]["copy_paste"]["bos"],
                    c["K0"]["copy_paste"]["n"],
                ],
                "historical_taban_orani": h["K0"].get("figur_orani"),
                "current_taban_orani": c["K0"].get("figur_orani"),
            },
            "K1": [h["K1_rota"], c["K1_rota"]],
            "K2": [h["K2_basma"], c["K2_basma"]],
            "K3": [h["K3_agir"], c["K3_agir"]],
            "K4": [h["K4_arena_disi"], c["K4_arena_disi"]],
            "K5": {
                "historical": [
                    h["K5_kesen_kare"],
                    h["K5_olculebilir_kare"],
                    h["K5_kesisim_px"],
                ],
                "current": [
                    c["K5_kesen_kare"],
                    c["K5_olculebilir_kare"],
                    c["K5_kesisim_px"],
                ],
                "historical_gate": hist["gecti"]["K5"],
                "current_gate": cur["gecti"]["K5"],
            },
        },
        "current_extra_gates": {
            key: cur["gecti"][key] for key in ("K6", "K7", "K8", "K5A")
        },
        "bakir_59": {
            "keysets_equal_unique": True,
            "matrix": {
                f"{old} -> {new}": n
                for (old, new), n in sorted(matrix.items())
            },
            "row_totals_v35": row_totals,
            "column_totals_aday": col_totals,
            "maske_yoktan_cikan": sum(
                n
                for (old, new), n in matrix.items()
                if old == "MASKE_YOK" and new != "MASKE_YOK"
            ),
            "bunlardan_rota": matrix[("MASKE_YOK", "ROTA")],
            "maske_yoka_gerileyen": sum(
                n
                for (old, new), n in matrix.items()
                if old != "MASKE_YOK" and new == "MASKE_YOK"
            ),
        },
        "epoch": {
            "csv_rows": len(csv_rows),
            "mask_mAP50_95_max_epoch": int(float(max_map_row["epoch"])),
            "mask_mAP50_95_max": float(max_map_row[map_key]),
            "checkpoint_epoch_field": checkpoint.get("epoch"),
            "checkpoint_train_metrics_matching_csv_epochs": matching_epochs,
            "matching_common_metric_count": len(common),
            "checkpoint_date": checkpoint.get("date"),
            "best_pt_sha256": sha256(best_path),
        },
        "kiyas_109": {
            "v35_figur_zemin": v35_ground,
            "dji_figur_zemin": dji_ground,
            "dji_bolu_v35": ratio,
            "rounded_ratio_1_decimal": round(ratio, 1),
            "v35_kaplama67_icerik_medyan": comparison["t127_temiz"][
                "kaplama67_icerik_medyan"
            ],
            "dji_kaplama67_icerik_medyan": comparison["dji_kirsal_v1"][
                "kaplama67_icerik_medyan"
            ],
            "t127_temiz_equals_v35_bytes": sha256(t127_path) == sha256(v35_path),
            "t127_sha256": sha256(t127_path),
            "v35_sha256": sha256(v35_path),
        },
    }
    OUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"JSON={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

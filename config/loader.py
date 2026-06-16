from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def deep_merge(base: dict, override: dict) -> dict:
    result = deepcopy(base)

    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


class ConfigLoader:
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        self.method_root = self.data_root / "_methods"

    def load_experiment_config(self, experiment_path: Path) -> dict:
        experiment_path = Path(experiment_path)
        metadata_path = experiment_path / "metadata.json"

        metadata = read_json(metadata_path)

        method_name = metadata.get("method")
        if method_name is None:
            raise KeyError(f"Missing 'method' in {metadata_path}")

        method_path = self.method_root / f"{method_name}.json"
        method = read_json(method_path) 

        return deep_merge(method, metadata)
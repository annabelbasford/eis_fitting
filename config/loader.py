from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigLoader:
    def __init__(self, global_config: dict[str, Any]):
        self.global_config = global_config

        paths_config = self.global_config["paths"]

        self.data_root = Path(paths_config["data_path"])

        methods_path = paths_config.get("methods_path")

        if methods_path is None:
            self.methods_path = self.data_root / "_methods"
        else:
            self.methods_path = Path(methods_path)

    # --------------- Json Helpers --------------- #

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def load_global_config(cls, path: str | Path) -> dict[str, Any]:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Global config file not found: {path}")

        config = cls.read_json(path)

        cls._validate_global_config(config)

        return config

    @staticmethod
    def _validate_global_config(config: dict[str, Any]) -> None:
        required_top_level = [
            "paths",
            "run",
            "save_preferences",
        ]

        for key in required_top_level:
            if key not in config:
                raise KeyError(f"Missing key in global config: {key}")

        required_paths = [
            "data_path",
            "user",
            "project",
            "output_mode",
        ]

        for key in required_paths:
            if key not in config["paths"]:
                raise KeyError(f"Missing key in global config paths: {key}")

        output_mode = config["paths"].get("output_mode")

        if output_mode not in {"local", "workspace"}:
            raise ValueError(
                "paths.output_mode must be either 'local' or 'workspace'. "
                f"Got {output_mode!r}."
            )

        if output_mode == "workspace" and config["paths"].get("output_path") is None:
            raise ValueError(
                "paths.output_path is required when output_mode='workspace'."
            )

    # --------------- Method loading --------------- #

    def load_method_config(self, method_name: str) -> dict[str, Any]:
        method_path = self.methods_path / f"{method_name}.json"

        if not method_path.exists():
            raise FileNotFoundError(
                f"Method config '{method_name}' not found at {method_path}"
            )

        method_config = self.read_json(method_path)

        if "geometry" not in method_config:
            raise KeyError(
                f"Method config '{method_name}' must contain a 'geometry' section."
            )

        return method_config


    # --------------- Experiment loading --------------- #


    def load_experiment_config(self, experiment_path: Path) -> dict[str, Any]:
        metadata_path = experiment_path / "metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"metadata.json not found in {experiment_path}"
            )

        metadata = self.read_json(metadata_path)

        if "method" not in metadata:
            raise KeyError(f"Missing 'method' in {metadata_path}")

        if "circuits" not in metadata:
            raise KeyError(f"Missing 'circuits' in {metadata_path}")

        method_config = self.load_method_config(metadata["method"])

        config = {
            # Experiment-level metadata
            "method": metadata["method"],
            "description": metadata.get("description", ""),
            "circuits": metadata["circuits"],

            # Method-level scientific parameters
            "geometry": method_config["geometry"],

            # Global execution parameters
            "run": self.global_config.get("run", {}),
            "validation" : self.global_config.get("validation", {}),
            "save_preferences": self.global_config.get("save_preferences", {}),
            "plotting": self.global_config.get("plotting", {}),
    

            # Keep original blocks available if needed
            "metadata": metadata,
            "method_config": method_config,
            "global_config": self.global_config,

            "full_terminal" : self.global_config.get("full_terminal", True)
        }

        return config
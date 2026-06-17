import numpy as np
import pandas as pd


class EISAnalyser:
    def __init__(self, circuits: dict):
        self.circuits = circuits

    def run(self, experiment) -> None:
        for circuit_name in experiment.circuits:
            parameters_csv = experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"

            if not parameters_csv.exists():
                print(f"Skipping missing file: {parameters_csv}")
                continue

            self.add_conductivity_columns(
                parameters_csv,
                experiment.geometry,
            )


    @staticmethod
    def get_element_columns(parameters_csv, first_chars):
        df = pd.read_csv(parameters_csv)

        return {
            col
            for col in df.columns
            if col.startswith(first_chars)
            and not col.endswith("error")
        }

    def add_conductivity_columns(self, parameters_csv, geometry):
        df = pd.read_csv(parameters_csv)

        thickness_cm = geometry["thickness_cm"]
        sd_thickness_cm = geometry["SD_thickness_cm"]
        area_cm2 = geometry["area_cm2"]
        sd_area_cm2 = geometry["SD_area_cm2"]

        resistance_names = [
            col
            for col in df.columns
            if col.startswith("R")
            and not col.startswith("SD_")
            and not col.endswith("error")
        ]

        for resistance_name in resistance_names:
            sd_col = f"SD_{resistance_name}"

            if sd_col not in df.columns:
                print(f"Skipping conductivity for {resistance_name}: no {sd_col}")
                continue

            conductivity = thickness_cm / (df[resistance_name] * area_cm2)

            sd_conductivity = conductivity * np.sqrt(
                (sd_thickness_cm / thickness_cm) ** 2
                + (sd_area_cm2 / area_cm2) ** 2
                + (df[sd_col] / df[resistance_name]) ** 2
            )

            df[f"conductivity_S_cm_{resistance_name}"] = conductivity
            df[f"SD_conductivity_S_cm_{resistance_name}"] = sd_conductivity

        df.to_csv(parameters_csv, index=False)

   
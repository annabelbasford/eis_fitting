import numpy as np
import pandas as pd


class EISAnalyser:
    def __init__(self, circuits: dict):
        self.circuits = circuits

    def run(self, experiment) -> None:
        for circuit_name in experiment.circuits:
            parameters_csv = experiment.paths.fits / f"eis_fit_parameters_{circuit_name}.csv"

            if not parameters_csv.exists():
                print(f"Skipping missing file: {parameters_csv}")
                continue

            self.add_conductivity_columns(
                parameters_csv,
                experiment.geometry,
            )

            self.add_ceff_columns(parameters_csv)

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

    def add_ceff_columns(self, parameters_csv, sigma_omega=0):
        df = pd.read_csv(parameters_csv)

        if "omega_max" not in df.columns:
            print(f"Skipping Ceff for {parameters_csv}: no omega_max")
            return

        omega = df["omega_max"].astype(float)

        if "SD_omega_max" in df.columns:
            sigma_omega = df["SD_omega_max"].astype(float)

        for q_col in [c for c in df.columns if c.startswith("Q_")]:
            name = q_col.split("_", maxsplit=1)[1]

            alpha_col = f"alpha_{name}"
            dq_col = f"SD_Q_{name}"
            dalpha_col = f"SD_alpha_{name}"

            required = [alpha_col, dq_col, dalpha_col]

            if not all(col in df.columns for col in required):
                print(f"Skipping incomplete CPE {name}")
                continue

            q = df[q_col].astype(float)
            dq = df[dq_col].astype(float)
            n = df[alpha_col].astype(float)
            dn = df[dalpha_col].astype(float)

            ceff = q * omega ** (n - 1)

            rel = np.sqrt(
                (dq / q) ** 2
                + ((n - 1) * sigma_omega / omega) ** 2
                + (np.log(omega) * dn) ** 2
            )

            df[f"Ceff_{name}"] = ceff
            df[f"SD_Ceff_{name}"] = ceff * rel

        df.to_csv(parameters_csv, index=False)
import shutil

import pandas as pd
import numpy as np
from impedance.models.circuits import CustomCircuit

import warnings

from eis_fitting.io.readers import EISCSVReader


class EISFitter:
    def __init__(self, circuits: dict):
        self.circuits = circuits
        self.reader = EISCSVReader()

    def run(self, experiment, full_terminal = True) -> None:
        output_folder = experiment.paths.fits
        pre_plot_folder = experiment.paths.pre_plots

        if pre_plot_folder.is_dir():
            shutil.rmtree(pre_plot_folder)

        output_folder.mkdir(parents=True, exist_ok=True)

        selected_circuits = experiment.circuits

        circuits_to_fit = {
            name: self.circuits[name]
            for name in selected_circuits
            if name in self.circuits
        }

        all_results = []
        all_fit_data = {circuit_name: {} for circuit_name in circuits_to_fit}

        csv_files = sorted(experiment.paths.csv.glob("*.csv"))

        for csv_path in csv_files:
            sample_name = csv_path.stem
            if full_terminal :
                print(f"\nFitting: {sample_name}")

            freq, z = self.reader.read_impedance(csv_path)

            for circuit_name, circuit_info in circuits_to_fit.items():
                result = self._fit_one(
                    sample_name=sample_name,
                    circuit_name=circuit_name,
                    circuit_info=circuit_info,
                    freq=freq,
                    z=z,
                    full_terminal=full_terminal
                )

                all_results.append(result["row"])

                if result["success"]:
                    all_fit_data[circuit_name][sample_name] = {
                        "freq": freq,
                        "Z": z,
                        "Z_fit": result["z_fit"],
                    }

        self._save_results(
            all_results=all_results,
            output_folder=output_folder,
            experiment_name=experiment.name,
        )

        return all_fit_data

    def _fit_one(self, sample_name, circuit_name, circuit_info, freq, z, full_terminal = True):
        circuit_string = circuit_info["string"]
        initial_guess = circuit_info["guess"]
        circuit_mapping = circuit_info["mapping"]

        if full_terminal :
            print(f"  Trying circuit: {circuit_name}")

        try:
            circuit = CustomCircuit(
                circuit=circuit_string,
                initial_guess=initial_guess,
                name=circuit_name,
            )

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="Covariance computation failed"
                )
                circuit.fit(freq, z, weight_by_modulus=True)

            z_fit = circuit.predict(freq)

            chi_square, reduced_chi_square = self.compute_chi_square(
                Z_exp=z,
                Z_fit=z_fit,
                n_parameters=len(circuit.initial_guess),
                relative=True,
            )

            param_names = circuit.get_param_names()[0]
            mapped_names = [circuit_mapping[param]["name"] for param in param_names]

            row = {
                "sample": sample_name,
                "circuit_name": circuit_name,
                "circuit_string": circuit_string,
                "fit_success": True,
                "chi_square": chi_square,
                "reduced_chi_square": reduced_chi_square,
            }

            for name, value in zip(mapped_names, circuit.parameters_):
                row[name] = value

            if hasattr(circuit, "conf_"):
                for name, sd in zip(mapped_names, circuit.conf_):
                    row[f"SD_{name}"] = sd
                    row[f"{name}_percent_error"] = 100 * sd / row[name]

            return {
                "success": True,
                "row": row,
                "z_fit": z_fit,
            }

        except Exception as exc:
            if full_terminal :
                print(f"Fit failed: {exc}")

            return {
                "success": False,
                "row": {
                    "sample": sample_name,
                    "circuit_name": circuit_name,
                    "circuit_string": circuit_string,
                    "fit_success": False,
                    "error": str(exc),
                    "chi_square": np.nan,
                    "reduced_chi_square": np.nan,
                },
                "z_fit": None,
            }

    def _save_results(
        self,
        all_results,
        output_folder,
        experiment_name,
    ):
        """
        Save one parameter CSV per circuit.

        Each CSV only contains:
        - metadata columns
        - fit-quality columns
        - parameters belonging to that circuit
        - SD and percent-error columns for those parameters
        """

        results_df = pd.DataFrame(all_results)

        if results_df.empty:
            return

        base_columns = [
            "sample",
            "circuit_name",
            "circuit_string",
            "fit_success",
            "fit_status",
            "covariance_warning",
            "chi_square",
            "reduced_chi_square",
            "omega_max",
            "error",
        ]

        output_folder.mkdir(parents=True, exist_ok=True)

        for circuit_name in results_df["circuit_name"].dropna().unique():
            circuit_df = results_df[results_df["circuit_name"] == circuit_name].copy()

            if circuit_df.empty:
                continue

            ordered_columns = [col for col in base_columns if col in circuit_df.columns]

            parameter_columns = self._get_circuit_parameter_columns(
                circuit_name=circuit_name,
                df=circuit_df,
            )

            for param in parameter_columns:
                if param in circuit_df.columns:
                    ordered_columns.append(param)

                sd_col = f"SD_{param}"
                if sd_col in circuit_df.columns:
                    ordered_columns.append(sd_col)

                err_col = f"{param}_percent_error"
                if err_col in circuit_df.columns:
                    ordered_columns.append(err_col)

            # Keep any useful non-empty columns that were not explicitly ordered.
            # This avoids accidentally losing a diagnostic column.
            remaining_columns = [
                col
                for col in circuit_df.columns
                if col not in ordered_columns and not circuit_df[col].isna().all()
            ]

            ordered_columns.extend(remaining_columns)

            circuit_df = circuit_df[ordered_columns]

            save_path = output_folder / f"{experiment_name}_{circuit_name}.csv"

            circuit_df.to_csv(save_path, index=False)

    def _get_circuit_parameter_columns(
        self,
        circuit_name,
        df,
    ):
        """
        Return only the fitted parameter columns that belong to one circuit.

        Supports both cases:
        1. CSV columns use raw impedance.py names:
           R_1, CPE_1_0, CPE_1_1

        2. CSV columns use mapped display names:
           R_i, Q_DL, alpha_DL
        """

        circuit = self.circuits[circuit_name]
        mapping = circuit.get("mapping", {})

        parameter_columns = []

        for raw_name, info in mapping.items():
            display_name = info.get("name")

            if raw_name in df.columns:
                parameter_columns.append(raw_name)

            elif display_name in df.columns:
                parameter_columns.append(display_name)

        return parameter_columns

    @staticmethod
    def compute_chi_square(Z_exp, Z_fit, n_parameters, relative=True):
        """
        Compute chi-square and reduced chi-square for a complex EIS fit.
        Parameters
        ----------
        Z_exp : array-like of complex
            Experimental impedance values.
        Z_fit : array-like of complex
            Fitted/model impedance values.
        n_parameters : int
            Number of fitted circuit parameters.
        relative : bool
            If True, normalize residuals by |Z_exp|².
            This is usually more useful for EIS because impedance magnitude
            can vary strongly across frequency. Also the reason why we fit with
            "weight_by_modulus"=True
        Returns
        -------
        chi_square : float
            Chi-square value.
        reduced_chi_square : float
            Chi-square divided by degrees of freedom.
        """
        Z_exp = np.asarray(Z_exp, dtype=complex)
        Z_fit = np.asarray(Z_fit, dtype=complex)
        residual = Z_exp - Z_fit
        residual_squared = residual.real**2 + residual.imag**2
        if relative:
            denominator = np.abs(Z_exp) ** 2
            valid = (
                np.isfinite(residual_squared)
                & np.isfinite(denominator)
                & (denominator > 0)
            )
            chi_terms = residual_squared[valid] / denominator[valid]
        else:
            valid = np.isfinite(residual_squared)
            chi_terms = residual_squared[valid]
        n_valid_points = np.sum(valid)
        if n_valid_points == 0:
            return np.nan, np.nan
        chi_square = np.sum(chi_terms)
        degrees_of_freedom = (2 * n_valid_points) - n_parameters
        if degrees_of_freedom <= 0:
            reduced_chi_square = np.nan
        else:
            reduced_chi_square = chi_square / degrees_of_freedom
        return chi_square, reduced_chi_square

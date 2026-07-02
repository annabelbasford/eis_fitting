import shutil

import pandas as pd
import numpy as np
from impedance.models.circuits import CustomCircuit

import warnings

from ..io import EISCSVReader
from .fit_metrics import FitMetrics


class EISFitter:
    def __init__(self, circuits: dict):
        self.circuits = circuits
        self.reader = EISCSVReader()

    def run(self, experiment, full_terminal=True) -> None:
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

        fitting_frequency_range = self._get_fitting_frequency_range(experiment)

        if full_terminal and fitting_frequency_range is not None:
            print(
                f"\nUsing fitting frequency range: "
                f"{fitting_frequency_range[0]} Hz to {fitting_frequency_range[1]} Hz"
            )

        all_results = []
        all_fit_data = {circuit_name: {} for circuit_name in circuits_to_fit}

        csv_files = sorted(experiment.paths.csv.glob("*.csv"))

        for csv_path in csv_files:
            sample_name = csv_path.stem
            if full_terminal:
                print(f"\nFitting: {sample_name}")

            freq, z = self.reader.read_impedance(csv_path)

            try:
                freq, z = self._apply_fitting_frequency_range(
                    freq=freq,
                    z=z,
                    fitting_frequency_range=fitting_frequency_range,
                )

            except Exception as exc:
                if full_terminal:
                    print(
                        "\033[91m"
                        + "\033[1m"
                        + "/!\\"
                        + "\033[0m"
                        + f"  Could not apply fitting frequency range: {exc}"
                    )

            for circuit_name, circuit_info in circuits_to_fit.items():
                result = self._fit_one(
                    sample_name=sample_name,
                    circuit_name=circuit_name,
                    circuit_info=circuit_info,
                    freq=freq,
                    z=z,
                    full_terminal=full_terminal,
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

    def _fit_one(
        self, sample_name, circuit_name, circuit_info, freq, z, full_terminal=True
    ):
        circuit_string = circuit_info["string"]
        initial_guess = circuit_info["guess"]
        circuit_mapping = circuit_info["mapping"]

        if full_terminal:
            print(f"  Trying circuit: {circuit_name}")

        try:
            circuit = CustomCircuit(
                circuit=circuit_string,
                initial_guess=initial_guess,
                name=circuit_name,
            )

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="Covariance computation failed",
                )
                circuit.fit(freq, z, weight_by_modulus=True)

            z_fit = circuit.predict(freq)

            n_parameters = len(circuit.parameters_)

            chi_square = FitMetrics.chi_square(
                Z_exp=z,
                Z_fit=z_fit,
                relative=True,
            )

            reduced_chi_square = FitMetrics.reduced_chi_square(
                Z_exp=z,
                Z_fit=z_fit,
                n_parameters=n_parameters,
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

            # Reject fits for which at least one fitted parameter has
            # a standard error larger than 100% of the fitted value.
            bad_parameters = []

            if hasattr(circuit, "conf_") and circuit.conf_ is not None:

                for name, value, sd in zip(
                    mapped_names,
                    circuit.parameters_,
                    circuit.conf_,
                ):
                    row[f"SD_{name}"] = sd

                    if value == 0 or not np.isfinite(value) or not np.isfinite(sd):
                        percent_error = np.inf
                    else:
                        percent_error = abs(100 * sd / value)

                    row[f"{name}_percent_error"] = percent_error

                    if percent_error > 100:
                        bad_parameters.append(f"{name}: {percent_error:.1f}%")

            else:
                raise RuntimeError(
                    "Fit rejected: covariance/standard errors unavailable"
                )

            if bad_parameters:
                raise RuntimeError(
                    "Fit rejected: parameter uncertainty above 100% for "
                    + ", ".join(bad_parameters)
                )

            return {
                "success": True,
                "row": row,
                "z_fit": z_fit,
            }

        except Exception as exc:
            print("\033[91m" + "\033[1m" + "/!\\" + "\033[0m" + f"  Fit failed: {exc}")

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
            "mean_real_residual_percent",
            "mean_imag_residual_percent",
            "mean_abs_residual_percent",
            "max_abs_residual_percent",
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

            circuit_df.to_csv(save_path, index=False, float_format="%.10e")

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

    def _get_fitting_frequency_range(self, experiment):
        """
        Return fitting frequency range from experiment.run.

        Expected format:
            None
            [f_min, f_max]
            [f_min, None]
            [None, f_max]

        Frequencies are in Hz.
        """

        frequency_range = experiment.run.get("fitting_frequency_range", None)

        if frequency_range is None:
            return None

        if len(frequency_range) != 2:
            raise ValueError("\033[91m" + "\033[1m" + "/!\\" + "\033[0m" + "fitting_frequency_range must be None or [f_min, f_max]")

        f_min, f_max = frequency_range

        if f_min is not None:
            f_min = float(f_min)

        if f_max is not None:
            f_max = float(f_max)

        if f_min is not None and f_max is not None and f_min >= f_max:
            raise ValueError("\033[91m" + "\033[1m" + "/!\\" + "\033[0m" +
                f"Invalid fitting_frequency_range: {frequency_range}. "
                "Expected f_min < f_max."
            )

        return f_min, f_max

    def _apply_fitting_frequency_range(
        self,
        freq,
        z,
        fitting_frequency_range,
    ):
        """
        Select only the frequencies used for fitting.
        """

        if fitting_frequency_range is None:
            return freq, z

        f_min, f_max = fitting_frequency_range

        mask = np.ones_like(freq, dtype=bool)

        if f_min is not None:
            mask &= freq >= f_min

        if f_max is not None:
            mask &= freq <= f_max

        freq_fit = freq[mask]
        z_fit_input = z[mask]

        if len(freq_fit) < 3:
            raise ValueError("\033[91m" + "\033[1m" + "/!\\" + "\033[0m" +
                "Fitting frequency range selected fewer than 3 points. "
                f"Range: {fitting_frequency_range}"
            )

        return freq_fit, z_fit_input

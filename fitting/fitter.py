import shutil

import pandas as pd
import numpy as np
from scipy.stats import mstats
from impedance.models.circuits import CustomCircuit

import warnings

from ..io import EISCSVReader
from .fit_metrics import FitMetrics
from .lin_kk_validation import LinKKValidator


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

        fitting_frequency_range = experiment.validation.get(
            "fitting_frequency_range", [None, None]
        )

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

            freq, z, outlier_info = self._remove_quantile_outliers(
                freq=freq,
                z=z,
                outlier_config=experiment.outlier_removal,
                sample_name=sample_name,
                full_terminal=full_terminal,
            )

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
                    validation_parameters=experiment.validation,
                    full_terminal=full_terminal,
                    outlier_info=outlier_info
                )

                all_results.append(result["row"])

                if result["success"]:
                    all_fit_data[circuit_name][sample_name] = {
                        "freq": freq,
                        "Z": z,
                        "Z_fit": result["z_fit"],
                        "lin_kk": result.get("lin_kk", {}),
                        "n_outliers_removed": outlier_info.get(
                            "n_outliers_removed",
                            np.nan,
                        ),
                    }

        self._save_results(
            all_results=all_results,
            output_folder=output_folder,
            experiment_name=experiment.name,
            full_terminal=experiment.config.get("full_terminal", True),
        )

        return all_fit_data

    def _fit_one(
        self,
        sample_name,
        circuit_name,
        circuit_info,
        freq,
        z,
        validation_parameters=None,
        full_terminal=True,
        outlier_info=None,
    ):

        if validation_parameters is None:
            validation_parameters = {}

        if outlier_info is None:
            outlier_info = {
                "n_points_before_outlier_removal": np.nan,
                "n_points_after_outlier_removal": np.nan,
                "n_outliers_removed": np.nan,
            }

        lin_kk_result = {}
        lin_kk_config = validation_parameters.get("lin_kk", {})

        try:
            if lin_kk_config.get("enabled", False):
                validator = LinKKValidator(
                    c=lin_kk_config.get("c", 0.85),
                    max_M=lin_kk_config.get("max_M", 50),
                    fit_type=lin_kk_config.get("fit_type", "complex"),
                    add_cap=lin_kk_config.get("add_cap", True),
                )

                lin_kk_result = validator.run(freq, z)

            self._check_lin_kk_acceptance(
                lin_kk_result=lin_kk_result,
                lin_kk_config=lin_kk_config,
            )

            circuit_string = circuit_info["string"]
            initial_guess = circuit_info["guess"]
            circuit_mapping = circuit_info["mapping"]

            if full_terminal:
                print(f"  Trying circuit: {circuit_name}")

            circuit = CustomCircuit(
                circuit=circuit_string,
                initial_guess=initial_guess,
                name=circuit_name,
            )

            error_percent_param_threshold=validation_parameters.get("error_percent_param_threshold", 100)


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
                "lin_kk_success": lin_kk_result.get("lin_kk_success", np.nan),
                "lin_kk_error": lin_kk_result.get("lin_kk_error", ""),
                "lin_kk_M": lin_kk_result.get("lin_kk_M", np.nan),
                "lin_kk_mu": lin_kk_result.get("lin_kk_mu", np.nan),
                "n_outliers_removed": outlier_info.get(
                    "n_outliers_removed",
                    np.nan,
                ),
            }

            for name, value in zip(mapped_names, circuit.parameters_):
                row[name] = value

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

                    if percent_error > error_percent_param_threshold:
                        bad_parameters.append(f"{name}: {percent_error:.1f}%")

            else:
                raise RuntimeError(
                    "Fit rejected: covariance/standard errors unavailable"
                )

            if bad_parameters:
                raise RuntimeError(
                    f"Fit rejected: parameter uncertainty above {error_percent_param_threshold}% for "
                    + ", ".join(bad_parameters)
                )

            row["lin_kk"] = lin_kk_result

            return {
                "success": True,
                "row": row,
                "z_fit": z_fit,
                "lin_kk": lin_kk_result,
            }

        except Exception as exc:
            print("\033[91m" + "\033[1m" + "/!\\" + "\033[0m" + f"  Fit failed: {exc}")

            return {
                "success": False,
                "row": {
                    "sample": sample_name,
                    "circuit_name": circuit_name,
                    "circuit_string": circuit_info["string"],
                    "fit_success": False,
                    "error": str(exc),
                    "chi_square": np.nan,
                    "reduced_chi_square": np.nan,
                    "lin_kk_success": lin_kk_result.get("lin_kk_success", np.nan),
                    "lin_kk_error": lin_kk_result.get("lin_kk_error", ""),
                    "lin_kk_M": lin_kk_result.get("lin_kk_M", np.nan),
                    "lin_kk_mu": lin_kk_result.get("lin_kk_mu", np.nan),
                    "lin_kk_max_abs_residual_percent": lin_kk_result.get(
                        "lin_kk_max_abs_residual_percent",
                        np.nan,
                    ),
                    "lin_kk_mean_abs_residual_percent": lin_kk_result.get(
                        "lin_kk_mean_abs_residual_percent",
                        np.nan,
                    ),
                    "n_points_before_outlier_removal": outlier_info.get(
                        "n_points_before_outlier_removal",
                        np.nan,
                    ),
                    "n_points_after_outlier_removal": outlier_info.get(
                        "n_points_after_outlier_removal",
                        np.nan,
                    ),
                    "n_outliers_removed": outlier_info.get(
                        "n_outliers_removed",
                        np.nan,
                    ),
                },
                "z_fit": None,
                "lin_kk": lin_kk_result,
            }

    def _save_results(
        self, all_results, output_folder, experiment_name, full_terminal=True
    ):
        """
        Save one parameter CSV per circuit.

        Each CSV only contains:
        - metadata columns
        - fit-quality columns
        - parameters belonging to that circuit
        - SD and percent-error columns for those parameters
        """

        csv_results = []

        # removes lin_kk dictionary so it's not parsed in the csv
        for result in all_results:
            result_for_csv = result.copy()
            result_for_csv.pop("lin_kk", None)
            csv_results.append(result_for_csv)

        results_df = pd.DataFrame(csv_results)

        if results_df.empty:
            return

        base_columns = [
            "sample",
            "circuit_name",
            "circuit_string",
            "fit_success",
            "chi_square",
            "reduced_chi_square",
            "n_outliers_removed",
            "lin_kk_success",
            "lin_kk_error",
            "lin_kk_M",
            "lin_kk_mu",
            "error",
        ]

        output_folder.mkdir(parents=True, exist_ok=True)

        for circuit_name in results_df["circuit_name"].dropna().unique():
            circuit_df = results_df[results_df["circuit_name"] == circuit_name].copy()

            if circuit_df.empty:
                continue

            ordered_columns = [col for col in base_columns if col in circuit_df.columns]

            parameter_columns = self._get_circuit_parameter_columns(
                circuit_name=circuit_name, df=circuit_df, full_terminal=full_terminal
            )

            if parameter_columns is None:
                continue

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

    def _get_circuit_parameter_columns(self, circuit_name, df, full_terminal):
        """
        Return only the fitted parameter columns that belong to one circuit.

        Supports both cases:
        1. CSV columns use raw impedance.py names:
           R_1, CPE_1_0, CPE_1_1

        2. CSV columns use mapped display names:
           R_i, Q_DL, alpha_DL
        """

        circuit = self.circuits.get(circuit_name, None)

        if circuit is None:

            return None
        mapping = circuit.get("mapping", {})

        parameter_columns = []

        for raw_name, info in mapping.items():
            display_name = info.get("name")

            if raw_name in df.columns:
                parameter_columns.append(raw_name)

            elif display_name in df.columns:
                parameter_columns.append(display_name)

        return parameter_columns

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
            raise ValueError(
                "\033[91m"
                + "\033[1m"
                + "/!\\"
                + "\033[0m"
                + "Fitting frequency range selected fewer than 3 points. "
                f"Range: {fitting_frequency_range}"
            )

        return freq_fit, z_fit_input

    def load_fit_data(self, experiment, validation_parameters=None):
        if validation_parameters is None:
            validation_parameters = experiment.validation
        """
        Load existing fitted parameter CSVs and rebuild the fitted impedance
        curves so Bode, Nyquist and residual plots can be regenerated without
        refitting.
        """

        def read_impedance_csv(csv_path):
            df = pd.read_csv(csv_path)

            freq = pd.to_numeric(df["freq/Hz"], errors="coerce")

            z_real = pd.to_numeric(df["Re(Z)/Ohm"], errors="coerce")
            z_imag = -pd.to_numeric(df["-Im(Z)/Ohm"], errors="coerce")

            Z = z_real.to_numpy() + 1j * z_imag.to_numpy()
            freq = freq.to_numpy(dtype=float)

            valid = (
                np.isfinite(freq)
                & (freq > 0)
                & np.isfinite(Z.real)
                & np.isfinite(Z.imag)
            )

            return freq[valid], Z[valid]

        def find_sample_csv(sample_name):
            direct_path = experiment.paths.csv / f"{sample_name}.csv"

            if direct_path.exists():
                return direct_path

            matches = sorted(experiment.paths.csv.glob(f"{sample_name}*.csv"))

            if matches:
                return matches[0]

            return None

        def extract_parameters(row, raw_param_names, mapping):
            values = []

            for raw_name in raw_param_names:
                mapped_name = mapping.get(raw_name, {}).get("name", raw_name)

                if mapped_name in row.index and pd.notna(row[mapped_name]):
                    value = row[mapped_name]

                elif raw_name in row.index and pd.notna(row[raw_name]):
                    value = row[raw_name]

                else:
                    print(f"Missing fitted parameter: " f"{raw_name} / {mapped_name}")
                    return None

                values.append(float(value))

            return np.asarray(values, dtype=float)

        all_fit_data = {}

        for circuit_name in experiment.circuits:
            parameter_csv = (
                experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"
            )

            if not parameter_csv.exists():
                print(f"Skipping missing fit file: {parameter_csv}")
                continue

            df_params = pd.read_csv(parameter_csv)

            circuit_config = self.circuits.get(circuit_name, None)
            if circuit_config is None:
                continue

            circuit_string = circuit_config["string"]
            initial_guess = circuit_config["guess"]
            mapping = circuit_config.get("mapping", {})

            temp_circuit = CustomCircuit(
                circuit=circuit_string,
                initial_guess=initial_guess,
            )

            raw_param_names = temp_circuit.get_param_names()[0]

            for _, row in df_params.iterrows():
                sample_name = str(row["sample"])

                if sample_name.upper() == "MEAN" or not row["fit_success"]:
                    continue

                sample_csv = find_sample_csv(sample_name)

                fitted_parameters = extract_parameters(
                    row=row,
                    raw_param_names=raw_param_names,
                    mapping=mapping,
                )

                if fitted_parameters is None:
                    continue

                freq, Z_exp = read_impedance_csv(sample_csv)

                lin_kk_result = {}

                lin_kk_config = validation_parameters.get("lin_kk", {})

                if lin_kk_config.get("enabled", False):
                    validator = LinKKValidator(
                        c=lin_kk_config.get("c", 0.85),
                        max_M=lin_kk_config.get("max_M", 50),
                        fit_type=lin_kk_config.get("fit_type", "complex"),
                        add_cap=lin_kk_config.get("add_cap", True),
                    )

                    lin_kk_result = validator.run(freq, Z_exp)

                fitted_circuit = CustomCircuit(
                    circuit=circuit_string,
                    initial_guess=list(fitted_parameters),
                )

                fitted_circuit.parameters_ = fitted_parameters

                Z_fit = fitted_circuit.predict(freq)

                fit_entry = row.to_dict()

                fit_entry.update(
                    {
                        "sample": sample_name,
                        "circuit_name": circuit_name,
                        "circuit_string": circuit_string,
                        "freq": freq,
                        "Z": Z_exp,
                        "Z_fit": Z_fit,
                        "lin_kk": lin_kk_result,
                        "fitted_parameters": fitted_parameters,
                        "raw_param_names": raw_param_names,
                        "sample_csv": sample_csv,
                        "parameter_csv": parameter_csv,
                    }
                )

                all_fit_data.setdefault(circuit_name, {})
                all_fit_data[circuit_name][sample_name] = fit_entry

        return all_fit_data

    def _check_lin_kk_acceptance(self, lin_kk_result, lin_kk_config):
        """
        Reject the fit if Lin-KK validation is enabled and failed.
        """

        if not lin_kk_config.get("enabled", False):
            return

        if not lin_kk_config.get("reject_on_fail", False):
            return

        if not lin_kk_result.get("lin_kk_success", False):
            error = lin_kk_result.get("lin_kk_error", "unknown Lin-KK error")

            raise RuntimeError(f"Fit rejected: Lin-KK validation failed ({error})")

    def _remove_quantile_outliers(
        self,
        freq,
        z,
        outlier_config,
        sample_name=None,
        full_terminal=True,
    ):
        """
        Remove EIS points using a quantile/IQR rule.

        A point is removed if any selected feature falls outside:

            Q1 - threshold * IQR
            Q3 + threshold * IQR

        Features can be:
            - log_modulus
            - phase
            - real
            - imag
        """

        if not outlier_config.get("enabled", False):
            print(outlier_config)
            return freq, z, {
                "n_outliers_removed": 0,
            }

        threshold = float(outlier_config.get("threshold", 1.5))
        features = outlier_config.get(
            "features",
            ["log_modulus", "phase"],
        )

        freq = np.asarray(freq, dtype=float)
        z = np.asarray(z, dtype=complex)

        valid = (
            np.isfinite(freq)
            & (freq > 0)
            & np.isfinite(z.real)
            & np.isfinite(z.imag)
            & (np.abs(z) > 0)
        )

        keep = valid.copy()

        feature_data = {}

        if "log_modulus" in features:
            feature_data["log_modulus"] = np.log10(np.abs(z))

        if "phase" in features:
            feature_data["phase"] = np.angle(z, deg=True)

        if "real" in features:
            feature_data["real"] = z.real

        if "imag" in features:
            feature_data["imag"] = z.imag

        for feature_name, values in feature_data.items():
            values = np.asarray(values, dtype=float)

            feature_valid = np.isfinite(values) & valid

            if np.sum(feature_valid) < 4:
                continue

            q1, q3 = mstats.mquantiles(
                values[feature_valid],
                prob=[0.25, 0.75],
            )

            iqr = q3 - q1

            if not np.isfinite(iqr) or iqr == 0:
                continue

            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr

            feature_keep = np.isfinite(values) & (values >= lower) & (values <= upper)

            keep &= feature_keep

        n_points_before = int(len(freq))
        n_points_valid = int(np.sum(valid))
        n_points_after = int(np.sum(keep))

        n_invalid_removed = n_points_before - n_points_valid
        n_quantile_outliers_removed = n_points_valid - n_points_after
        n_total_removed = n_points_before - n_points_after

        if full_terminal and n_total_removed > 0:
            prefix = f"{sample_name}: " if sample_name else ""
            print(
                f"{prefix}removed {n_total_removed} point(s) "
                f"({n_invalid_removed} invalid, "
                f"{n_quantile_outliers_removed} quantile/IQR outlier(s)) "
                f"using threshold={threshold}"
            )

        

        return freq[keep], z[keep], {
            "n_points_before_outlier_removal": n_points_before,
            "n_points_after_outlier_removal": n_points_after,
            "n_invalid_points_removed": n_invalid_removed,
            "n_quantile_outliers_removed": n_quantile_outliers_removed,
            "n_outliers_removed": n_total_removed,
        }

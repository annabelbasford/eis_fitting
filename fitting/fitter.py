import shutil

import pandas as pd
from impedance.models.circuits import CustomCircuit

import warnings

from eis_fitting.io.readers import EISCSVReader

class EISFitter:
    def __init__(self, circuits: dict):
        self.circuits = circuits
        self.reader = EISCSVReader()

    def run(self, experiment) -> None:
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
            print(f"\nFitting: {sample_name}")

            freq, z = self.reader.read_impedance(csv_path)

            for circuit_name, circuit_info in circuits_to_fit.items():
                result = self._fit_one(
                    sample_name=sample_name,
                    circuit_name=circuit_name,
                    circuit_info=circuit_info,
                    freq=freq,
                    z=z,
                )

                all_results.append(result["row"])

                if result["success"]:
                    all_fit_data[circuit_name][sample_name] = {
                        "freq": freq,
                        "Z": z,
                        "Z_fit": result["z_fit"],
                    }

        self._save_results(all_results, output_folder, circuits_to_fit, experiment)

        return all_fit_data

    def _fit_one(self, sample_name, circuit_name, circuit_info, freq, z):
        circuit_string = circuit_info["string"]
        initial_guess = circuit_info["guess"]
        circuit_mapping = circuit_info["mapping"]

        print(f"  Trying circuit: {circuit_name}")

        try:
            circuit = CustomCircuit(
                circuit=circuit_string,
                initial_guess=initial_guess,
                name=circuit_name,
            )

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Covariance computation failed")
                circuit.fit(freq, z, weight_by_modulus=True)

            z_fit = circuit.predict(freq)

            param_names = circuit.get_param_names()[0]
            mapped_names = [circuit_mapping[param]["name"] for param in param_names]

            row = {
                "sample": sample_name,
                "circuit_name": circuit_name,
                "circuit_string": circuit_string,
                "fit_success": True,
            }

            for name, value in zip(mapped_names, circuit.parameters_):
                row[name] = value

            if hasattr(circuit, "conf_"):
                for name, sd in zip(mapped_names, circuit.conf_):
                    row[f"SD_{name}"] = sd
                    row[f"{name}_percent_error"] = 100 * sd / row[name]

            for key, value in list(row.items()):
                if isinstance(value, float):
                    row[key] = round(value, 6)

            return {
                "success": True,
                "row": row,
                "z_fit": z_fit,
            }

        except Exception as exc:
            print(f"    Fit failed: {exc}")

            return {
                "success": False,
                "row": {
                    "sample": sample_name,
                    "circuit_name": circuit_name,
                    "circuit_string": circuit_string,
                    "fit_success": False,
                    "error": str(exc),
                },
                "z_fit": None,
            }

    def _save_results(self, all_results, output_folder, circuits_to_fit, experiment):
        results_df = pd.DataFrame(all_results)

        if results_df.empty:
            return

        base_columns = [
            "sample",
            "circuit_name",
            "circuit_string",
            "fit_success",
        ]

        ordered_columns = [col for col in base_columns if col in results_df.columns]

        parameter_names = []

        for col in results_df.columns:
            if (
                col not in base_columns
                and not col.startswith("SD_")
                and not col.endswith("_percent_error")
                and col != "error"
            ):
                parameter_names.append(col)

        parameter_names = list(dict.fromkeys(parameter_names))

        for param in parameter_names:
            ordered_columns.append(param)

            sd_col = f"SD_{param}"
            if sd_col in results_df.columns:
                ordered_columns.append(sd_col)

            err_col = f"{param}_percent_error"
            if err_col in results_df.columns:
                ordered_columns.append(err_col)

        remaining_cols = [
            col for col in results_df.columns
            if col not in ordered_columns
        ]

        ordered_columns.extend(remaining_cols)
        results_df = results_df[ordered_columns]

        for circuit_name in circuits_to_fit:
            circuit_df = results_df[
                results_df["circuit_name"] == circuit_name
            ].copy()

            circuit_csv = output_folder / f"{experiment.name}_{circuit_name}.csv"
            circuit_df.to_csv(circuit_csv, index=False, float_format="%.6g")
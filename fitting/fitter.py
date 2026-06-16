from pathlib import Path
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from impedance.models.circuits import CustomCircuit

from eis_fitting.io.readers import EISCSVReader
from eis_fitting.utils.figures import FigureSaver


class FitPlotter:
    def __init__(self, figure_saver: FigureSaver):
        self.figure_saver = figure_saver

    def plot_nyquist(self, freq, z, z_fit, title, save_path):
        fig, ax = plt.subplots(figsize=(9, 5))

        ax.plot(
            z.real,
            -z.imag,
            "-",
            label="Data",
            linewidth=2,
            color="navy",
            alpha=0.7,
        )

        ax.plot(
            z_fit.real,
            -z_fit.imag,
            "--",
            label="Fit",
            linewidth=2,
            color="lightskyblue",
        )

        ax.set_xlabel(r"Re(Z) ($\Omega$)", fontsize=14)
        ax.set_ylabel(r"-Im(Z) ($\Omega$)", fontsize=14)
        ax.set_title(title, fontsize=13)
        ax.margins(x=0.05, y=0.1)
        ax.legend()

        self.figure_saver.save(save_path, fig, {ax})

    def plot_bode(self, freq, z, z_fit, title, save_path):
        zmod = np.abs(z)
        phase = np.angle(z, deg=True)

        zmod_fit = np.abs(z_fit)
        phase_fit = np.angle(z_fit, deg=True)

        fig, axes = plt.subplots(2, 1, figsize=(7, 6), sharex=True)

        axes[0].plot(freq, zmod, "-", label="Data", color="navy", linewidth=2, alpha=0.7)
        axes[0].plot(freq, zmod_fit, "--", label="Fit", color="lightskyblue", linewidth=2)
        axes[0].set_xscale("log")
        axes[0].set_yscale("log")
        axes[0].set_ylabel(r"|Z| ($\Omega$)", fontsize=14)
        axes[0].legend()

        axes[1].plot(freq, phase, "-", label="Data", color="navy", linewidth=2, alpha=0.7)
        axes[1].plot(freq, phase_fit, "--", label="Fit", color="lightskyblue", linewidth=2)
        axes[1].set_xscale("log")
        axes[1].set_xlabel(r"Frequency ($Hz$)", fontsize=14)
        axes[1].set_ylabel(r"Phase ($°$)", fontsize=14)

        fig.suptitle(title)

        self.figure_saver.save(save_path, fig, {axes[0], axes[1]})

    def plot_all_files_for_circuit(self, fit_data_dict, circuit_name, save_folder):
        save_folder = Path(save_folder)
        save_folder.mkdir(parents=True, exist_ok=True)

        n = len(fit_data_dict)
        palette = sns.color_palette("Paired", 2 * n)

        fig, ax = plt.subplots(figsize=(9, 5))

        for i, (sample_name, data) in enumerate(fit_data_dict.items()):
            data_colour = palette[2 * i]
            fit_colour = palette[2 * i + 1]

            ax.plot(
                data["Z"].real,
                -data["Z"].imag,
                "-",
                color=data_colour,
                label=f"{sample_name} data",
                linewidth=2,
            )

            ax.plot(
                data["Z_fit"].real,
                -data["Z_fit"].imag,
                "--",
                color=fit_colour,
                label=f"{sample_name} fit",
                linewidth=2,
            )

        ax.set_xlabel(r"Re(Z) ($\Omega$)", fontsize=14)
        ax.set_ylabel(r"-Im(Z) ($\Omega$)", fontsize=14)
        ax.set_title(f"{circuit_name} | Nyquist", fontsize=13)
        ax.margins(x=0.05, y=0.1)
        ax.legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")

        self.figure_saver.save(
            save_folder / f"all_files_{circuit_name}_nyquist",
            fig,
            {ax},
        )

        fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

        for i, (sample_name, data) in enumerate(fit_data_dict.items()):
            data_colour = palette[2 * i]
            fit_colour = palette[2 * i + 1]

            freq = data["freq"]
            z = data["Z"]
            z_fit = data["Z_fit"]

            axes[0].plot(freq, np.abs(z), "-", color=data_colour, label=f"{sample_name} data")
            axes[0].plot(freq, np.abs(z_fit), "--", color=fit_colour, label=f"{sample_name} fit")

            axes[1].plot(freq, np.angle(z, deg=True), "-", color=data_colour, label=f"{sample_name} data")
            axes[1].plot(freq, np.angle(z_fit, deg=True), "--", color=fit_colour, label=f"{sample_name} fit")

        axes[0].set_xscale("log")
        axes[0].set_yscale("log")
        axes[0].set_ylabel(r"|Z| ($\Omega$)", fontsize=14)
        axes[0].legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")

        axes[1].set_xscale("log")
        axes[1].set_xlabel(r"Frequency ($Hz$)", fontsize=14)
        axes[1].set_ylabel(r"Phase ($°$)", fontsize=14)

        fig.suptitle(f"{circuit_name} | Bode", fontsize=13)

        self.figure_saver.save(
            save_folder / f"all_files_{circuit_name}_bode",
            fig,
            {axes[0], axes[1]},
        )


class EISFitter:
    def __init__(self, circuits: dict):
        self.circuits = circuits
        self.reader = EISCSVReader()

    def run(self, experiment) -> None:
        output_folder = experiment.paths.fits

        if output_folder.exists():
            shutil.rmtree(output_folder)

        output_folder.mkdir(parents=True, exist_ok=True)

        figure_saver = FigureSaver(experiment.save_preferences)
        plotter = FitPlotter(figure_saver)

        plot = experiment.run.get("plot", True)
        plot_folder = experiment.paths.plots

        if plot:
            plot_folder.mkdir(parents=True, exist_ok=True)

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

            sample_plot_folder = plot_folder / sample_name

            if plot:
                sample_plot_folder.mkdir(parents=True, exist_ok=True)

            freq, z = self.reader.read_impedance(csv_path)
            omega_max = self.reader.omega_max(csv_path)

            for circuit_name, circuit_info in circuits_to_fit.items():
                result = self._fit_one(
                    sample_name=sample_name,
                    circuit_name=circuit_name,
                    circuit_info=circuit_info,
                    freq=freq,
                    z=z,
                    omega_max=omega_max,
                )

                all_results.append(result["row"])

                if result["success"]:
                    all_fit_data[circuit_name][sample_name] = {
                        "freq": freq,
                        "Z": z,
                        "Z_fit": result["z_fit"],
                    }

                    if plot:
                        circuit_plot_folder = sample_plot_folder / circuit_name
                        circuit_plot_folder.mkdir(parents=True, exist_ok=True)

                        plotter.plot_nyquist(
                            freq,
                            z,
                            result["z_fit"],
                            title=f"{sample_name} | {circuit_name}",
                            save_path=circuit_plot_folder / f"{sample_name}_{circuit_name}_nyquist",
                        )

                        plotter.plot_bode(
                            freq,
                            z,
                            result["z_fit"],
                            title=f"{sample_name} | {circuit_name}",
                            save_path=circuit_plot_folder / f"{sample_name}_{circuit_name}_bode",
                        )

        if plot and len(csv_files) > 1:
            all_plot_folder = plot_folder / "all_runs"

            for circuit_name, fit_data_dict in all_fit_data.items():
                if fit_data_dict:
                    plotter.plot_all_files_for_circuit(
                        fit_data_dict,
                        circuit_name,
                        all_plot_folder,
                    )

        self._save_results(all_results, output_folder, circuits_to_fit)

    def _fit_one(self, sample_name, circuit_name, circuit_info, freq, z, omega_max):
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

            circuit.fit(freq, z, weight_by_modulus=True)
            z_fit = circuit.predict(freq)

            param_names = circuit.get_param_names()[0]
            mapped_names = [circuit_mapping[param]["name"] for param in param_names]

            row = {
                "sample": sample_name,
                "circuit_name": circuit_name,
                "circuit_string": circuit_string,
                "fit_success": True,
                "omega_max": omega_max,
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
                    "omega_max": omega_max,
                    "error": str(exc),
                },
                "z_fit": None,
            }

    def _save_results(self, all_results, output_folder, circuits_to_fit):
        results_df = pd.DataFrame(all_results)

        if results_df.empty:
            return

        base_columns = [
            "sample",
            "circuit_name",
            "circuit_string",
            "fit_success",
            "omega_max",
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

        combined_csv = output_folder / "eis_fit_parameters_all_circuits.csv"
        results_df.to_csv(combined_csv, index=False, float_format="%.6g")

        for circuit_name in circuits_to_fit:
            circuit_df = results_df[
                results_df["circuit_name"] == circuit_name
            ].copy()

            circuit_csv = output_folder / f"eis_fit_parameters_{circuit_name}.csv"
            circuit_df.to_csv(circuit_csv, index=False, float_format="%.6g")
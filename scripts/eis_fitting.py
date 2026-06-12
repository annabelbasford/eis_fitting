import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from impedance.models.circuits import CustomCircuit
import shutil

from .utils import save_fig

# ------- Helper functions ------- #


def load_eis_csv(path):
    df = pd.read_csv(path)
    freq = df["freq/Hz"].to_numpy(dtype=float)
    z_real = df["Re(Z)/Ohm"].to_numpy(dtype=float)
    z_minus_imag = df["-Im(Z)/Ohm"].to_numpy(dtype=float)

    # Because column is -Im(Z), the complex impedance is:
    Z = z_real - 1j * z_minus_imag

    return freq, Z


def get_omega_max(input_path):
    # input_folder : pathlib Path to clean csv file

    # finding omega_max
    df = pd.read_csv(input_path)

    # Clean possible whitespace in column names
    df.columns = df.columns.str.strip()

    freq = df["freq/Hz"]
    minus_imag = df["-Im(Z)/Ohm"]

    idx_max = minus_imag.idxmax()
    f_max = freq.loc[idx_max]

    omega_max = 2 * np.pi * f_max

    return omega_max


def plot_nyquist_fit(freq, Z, Z_fit, title, save_path, save_preferences):
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(
        Z.real,
        -Z.imag,
        "-",
        label="Data",
        linewidth=2,
        color="navy",
        alpha=0.7,
    )

    ax.plot(
        Z_fit.real,
        -Z_fit.imag,
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

    save_fig(save_path, fig, {ax}, save_preferences)


def plot_bode_fit(freq, Z, Z_fit, title, save_path, save_preferences):

    zmod = np.abs(Z)
    phase = np.angle(Z, deg=True)
    zmod_fit = np.abs(Z_fit)
    phase_fit = np.angle(Z_fit, deg=True)
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

    save_fig(save_path, fig, {axes[0], axes[1]}, save_preferences)


def plot_all_files_for_circuit(
    fit_data_dict, circuit_name, save_folder, save_preferences
):
    """
    Plot all CSV files on the same Nyquist and Bode plots for one circuit.
    Data = solid colour
    Fit  = dashed paired colour
    """
    save_folder = Path(save_folder)
    save_folder.mkdir(exist_ok=True, parents=True)
    n = len(fit_data_dict)
    palette = sns.color_palette("Paired", 2 * n)

    print(f"Plotting all samples for {circuit_name}")

    # ------- Nyquist plot ------- #
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, (sample_name, data) in enumerate(fit_data_dict.items()):
        freq = data["freq"]
        Z = data["Z"]
        Z_fit = data["Z_fit"]
        data_colour = palette[2 * i]
        fit_colour = palette[2 * i + 1]
        ax.plot(
            Z.real,
            -Z.imag,
            "-",
            color=data_colour,
            label=f"{sample_name} data",
            linewidth=2,
        )
        ax.plot(
            Z_fit.real,
            -Z_fit.imag,
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

    save_fig(
        save_folder / f"all_files_{circuit_name}_nyquist", fig, {ax}, save_preferences
    )

    # ------- Bode plot ------- #
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for i, (sample_name, data) in enumerate(fit_data_dict.items()):
        freq = data["freq"]
        Z = data["Z"]
        Z_fit = data["Z_fit"]
        data_colour = palette[2 * i]
        fit_colour = palette[2 * i + 1]

        axes[0].plot(
            freq,
            np.abs(Z),
            "-",
            color=data_colour,
            label=f"{sample_name} data",
            linewidth=2,
        )
        axes[0].plot(
            freq,
            np.abs(Z_fit),
            "--",
            color=fit_colour,
            label=f"{sample_name} fit",
            linewidth=2,
        )
        axes[1].plot(
            freq,
            np.angle(Z, deg=True),
            "-",
            color=data_colour,
            label=f"{sample_name} data",
            linewidth=2,
        )
        axes[1].plot(
            freq,
            np.angle(Z_fit, deg=True),
            "--",
            color=fit_colour,
            label=f"{sample_name} fit",
            linewidth=2,
        )

    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_ylabel(r"|Z| ($\Omega$)", fontsize=14)
    axes[0].legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")
    axes[1].set_xscale("log")
    axes[1].set_xlabel(r"Frequency ($Hz$)", fontsize=14)
    axes[1].set_ylabel(r"Phase ($°$)", fontsize=14)
    fig.suptitle(f"{circuit_name} | Bode", fontsize=13)

    save_fig(
        save_folder / f"all_files_{circuit_name}_bode.png",
        fig,
        {axes[0], axes[1]},
        save_preferences,
    )


def eis_fitting(input_folder, output_folder, CIRCUITS, save_preferences, plot=False):
    """
    input_folder : pathlib Path class to the clean csv folder
    output_folder : pathlib Path class to the folder where fit results + plots will be saved
    CIRCUITS : dictionary following impendance CustomCircuit naming rule
    with the following structure :
        CIRCUITS = {
            "circuit_name": {
            "string": "in naming conventions",
            "guess": [values in the same order as in the string item],
    mapping : dict {"R_1" : "R_e"}
    },
    """

    if output_folder.exists():
        print(f"Output folder {output_folder} already exists. It will be deleted and recreated.")
        shutil.rmtree(output_folder)
    output_folder.mkdir(exist_ok=True)

    if plot:
        plot_folder = output_folder / "plots"
        plot_folder.mkdir(exist_ok=True)

    # ------- Batch fitting ------- #
    all_results = []

    csv_files = sorted(input_folder.glob("*.csv"))

    all_fit_data = {circuit_name: {} for circuit_name in CIRCUITS.keys()}

    for csv_path in csv_files:
        sample_name = csv_path.stem
        print(f"\nFitting: {sample_name}")

        if plot:
            sample_folder_path = plot_folder / sample_name
            sample_folder_path.mkdir()

        freq, Z = load_eis_csv(csv_path)

        for circuit_name, circuit_info in CIRCUITS.items():
            circuit_string = circuit_info["string"]
            initial_guess = circuit_info["guess"]
            circuit_mapping = circuit_info["mapping"]

            print(f"  Trying circuit: {circuit_name}")

            omega_max = get_omega_max(csv_path)

            try:
                circuit = CustomCircuit(
                    circuit=circuit_string,
                    initial_guess=initial_guess,
                    name=circuit_name,
                )

                circuit.fit(freq, Z, weight_by_modulus=True)
                # weight_by_modulus=True to make sure high magnitude points
                # (low frequencies) don't weight too much in the fitting
                Z_fit = circuit.predict(freq)

                all_fit_data[circuit_name][sample_name] = {
                    "freq": freq,
                    "Z": Z,
                    "Z_fit": Z_fit,
                }

                param_names = circuit.get_param_names()[0]
                mapped_names = [circuit_mapping[param]["name"] for param in param_names]

                param_values = circuit.parameters_

                result = {
                    "sample": sample_name,
                    "circuit_name": circuit_name,
                    "circuit_string": circuit_string,
                    "fit_success": True,
                    "omega_max": omega_max,
                }

                for name, value in zip(mapped_names, param_values):
                    result[name] = value

                if hasattr(circuit, "conf_"):
                    for name, sd in zip(mapped_names, circuit.conf_):
                        result[f"SD_{name}"] = sd
                        result[f"{name}_percent_error"] = 100 * sd / result[name]

                for key in result.keys():
                    if isinstance(result[key], float):
                        result[key] = round(result[key], 6)

                all_results.append(result)

                if plot:
                    # Save plots
                    nyquist_path = (
                        sample_folder_path / f"{sample_name}_{circuit_name}_nyquist"
                    )
                    bode_path = (
                        sample_folder_path / f"{sample_name}_{circuit_name}_bode"
                    )

                    plot_nyquist_fit(
                        freq,
                        Z,
                        Z_fit,
                        title=f"{sample_name} | {circuit_name}",
                        save_path=nyquist_path,
                        save_preferences=save_preferences,
                    )

                    plot_bode_fit(
                        freq,
                        Z,
                        Z_fit,
                        title=f"{sample_name} | {circuit_name}",
                        save_path=bode_path,
                        save_preferences=save_preferences,
                    )

            except Exception as e:
                print(f"    Fit failed: {e}")

                all_results.append(
                    {
                        "sample": sample_name,
                        "circuit_name": circuit_name,
                        "circuit_string": circuit_string,
                        "fit_success": False,
                        "error": str(e),
                        "omega_max": omega_max,
                    }
                )

    if plot and len(csv_files) > 1:
        for circuit_name, fit_data_dict in all_fit_data.items():
            if fit_data_dict:
                plot_all_folder = plot_folder / "_all_files"
                plot_all_folder.mkdir(exist_ok=True)

                plot_all_files_for_circuit(
                    fit_data_dict=fit_data_dict,
                    circuit_name=circuit_name,
                    save_folder=plot_all_folder,
                    save_preferences=save_preferences,
                )

    # Save summary tables
    results_df = pd.DataFrame(all_results)

    # Reorder parameter columns
    base_columns = [
        "sample",
        "circuit_name",
        "circuit_string",
        "fit_success",
    ]

    ordered_columns = base_columns.copy()

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

    remaining_cols = [col for col in results_df.columns if col not in ordered_columns]

    ordered_columns.extend(remaining_cols)

    results_df = results_df[ordered_columns]

    # Append if CSV already exists
    combined_csv = output_folder / "eis_fit_summary_all_circuits.csv"

    if combined_csv.exists():
        existing_df = pd.read_csv(combined_csv)

        # combine old + new
        results_df = pd.concat(
            [existing_df, results_df],
            ignore_index=True,
        )

    # save updated combined csv
    results_df.to_csv(
        combined_csv,
        index=False,
        float_format="%.6g",
    )

    # ---- Save separate circuit CSVs ---- #
    for circuit_name in CIRCUITS.keys():

        circuit_df = results_df[results_df["circuit_name"] == circuit_name].copy()

        circuit_csv = output_folder / f"eis_fit_parameters_{circuit_name}.csv"

        circuit_df.to_csv(
            circuit_csv,
            index=False,
            float_format="%.6g",
        )

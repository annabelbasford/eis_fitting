import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from os import unlink
from math import sqrt

# ------- Helper functions ------- #

def save_fig(save_path, fig, axes, save_to_png, save_to_svg):
    """
    save_path : pathlib class structured like
    .../fits/plots/sample_name/sample_name_{circuit_name}_nyquist.png"

    fig : see matplotlib
    axes : set of matplotlib axes
    save_to_png/csv : Boolean
    """

    fig.tight_layout()

    if save_to_png:
        file_path = save_path.with_suffix(".png")
        fig.savefig(file_path, format="png", dpi=300, bbox_inches="tight")
    if save_to_svg:
        file_path = save_path.with_suffix(".svg")

        # transparent background
        fig.patch.set_alpha(0)
        # transparent plotting area for each figure
        for ax in axes:
            ax.patch.set_alpha(0)

        fig.savefig(
            file_path, format="svg", transparent=True, dpi=300, bbox_inches="tight"
        )

    plt.close(fig)


def get_element_columns(csv_file, first_chars):
    """
    csv_file : pathlib Path class pointing towards eis_fit_parameters_circuit_name.csv
    first_chars : str like 'R' to get resistances or 'Ceff' for effective capacitances
    """
    df = pd.read_csv(csv_file)

    matching_columns = {
        col
        for col in df.columns
        if (col.startswith(first_chars) and (not col.endswith("error")))
    }
    return matching_columns


def add_conductivity_columns(
    parameters_csv, thickness_cm, sd_thickness_cm, area_cm2, sd_area_cm2
):
    """
    parameters_csv : pathlib Path class pointing to eis_fit_parameters_circuit_name.csv
    resistance name : str like "R_1" matching impendance.py naming convention
    thickness_cm, area_cm2 : floats parsed in metadata.json
    """

    resistances_names = get_element_columns(parameters_csv, "R")

    for resistance_name in resistances_names:
        df = pd.read_csv(parameters_csv)

        conductivity = thickness_cm / (df[resistance_name] * area_cm2)
        sd_conductivity = conductivity * np.sqrt(
            (sd_thickness_cm / thickness_cm) ** 2
            + (sd_area_cm2 / area_cm2) ** 2
            + (df[f"SD_{resistance_name}"] / df[resistance_name]) ** 2
        )

        df[f"conductivity_S_cm_{resistance_name}"] = conductivity
        df[f"SD_conductivity_S_cm_{resistance_name}"] = sd_conductivity

        df.to_csv(parameters_csv, index=False)


def add_Ceff_columns(parameters_csv, sigma_omega=0):
    """
    parameters_csv : pathlib Path to "eis_fit_parameters_circuit_name.csv
    sigma_omega : uncertainty over sigma_omega
    """
    df = pd.read_csv(parameters_csv)

    # Check omega_max exists
    if "omega_max" not in df.columns:
        raise ValueError("Missing required column: 'omega_max'")

    omega = df["omega_max"].astype(float)

    # Optional: assume no uncertainty on omega if not provided
    # In case we manage to get it from the script at some point
    if "SD_omega_max" in df.columns:
        sigma_omega = df["SD_omega_max"].astype(float)
    else:
        sigma_omega = sigma_omega

    # Detect CPE indices
    cpe_ids = sorted(
        {
            col.split("_")[1]
            for col in df.columns
            if col.startswith("CPE_") and col.endswith("_0")
        }
    )

    # Loop over CPEs
    for i in cpe_ids:

        Q_col = f"CPE_{i}_0"
        dQ_col = f"SD_CPE_{i}_0"
        n_col = f"CPE_{i}_1"
        dn_col = f"SD_CPE_{i}_1"

        if not all(col in df.columns for col in [Q_col, dQ_col, n_col, dn_col]):
            print(f"Skipping incomplete CPE_{i}")
            continue

        Q = df[Q_col].astype(float)
        dQ = df[dQ_col].astype(float)
        n = df[n_col].astype(float)
        dn = df[dn_col].astype(float)

        Ceff = Q * omega ** (n - 1)

        # Uncertainty propagation (we sure ???)
        rel = np.sqrt(
            (dQ / Q) ** 2
            + ((n - 1) * sigma_omega / omega) ** 2
            + (np.log(omega) * dn) ** 2
        )

        dCeff = Ceff * rel

        # Store results
        df[f"Ceff_{i}"] = Ceff
        df[f"SD_Ceff_{i}"] = dCeff

    df.to_csv(parameters_csv, index=False)


def plot_fit_parameters_dual_axis_for_sample(
    data_dir,
    circuit_name,
    sample,
    resistance_columns,
    capacitance_columns,
    save_to_png=True,
    save_to_svg=True,
):
    """
    data_dir : pathlib Path pointing towards --/eis_fitting/processed/dataset/fits/
    circuit_name, sample : str
    resistance_columns / capacitance_columns : arrays of str (typically from get_element_columns)
    save_to_png/svg : Boolean
    """

    parameters_csv = data_dir / f"eis_fit_parameters_{circuit_name}.csv"

    save_folder = data_dir / "plots" / sample / "bar_charts"
    save_folder.mkdir(exist_ok=True, parents=True)

    df = pd.read_csv(parameters_csv)

    # Keep only selected sample
    df_sample = df[df["sample"] == sample]

    if df_sample.empty:
        print(f"Sample '{sample}' not found.")
        return

    # Usually only one row per sample/circuit
    row = df_sample.iloc[0]

    sample_name = row["sample"]

    resistance_params = []
    resistance_values = []
    resistance_errors = []

    capacitance_params = []
    capacitance_values = []
    capacitance_errors = []

    # Collect resistance params
    for param in resistance_columns:

        if param not in df.columns:
            print(f"Skipping {param}: not found in dataframe")
            continue

        value = row[param]

        sd_col = f"SD_{param}"
        error = row[sd_col] if sd_col in df.columns else 0

        if pd.isna(value):
            continue

        resistance_params.append(param)
        resistance_values.append(value)
        resistance_errors.append(error if not pd.isna(error) else 0)

    # Collect capacitance params
    for param in capacitance_columns:

        if param not in df.columns:
            print(f"Skipping {param}: not found in dataframe")
            continue

        value = row[param]

        sd_col = f"SD_{param}"
        error = row[sd_col] if sd_col in df.columns else 0

        if pd.isna(value):
            continue

        capacitance_params.append(param)
        capacitance_values.append(value)
        capacitance_errors.append(error if not pd.isna(error) else 0)

    # Nothing to plot error handling
    if not resistance_params and not capacitance_params:
        print(f"No valid parameters found for {sample_name}")
        return

    # Plot
    fig, ax_res = plt.subplots(figsize=(8, 5))

    ax_cap = ax_res.twinx()

    resistance_colours = sns.color_palette(
        "Reds",
        n_colors=len(resistance_params) + 2,
    )[2:]

    capacitance_colours = sns.color_palette(
        "Blues",
        n_colors=len(capacitance_params) + 2,
    )[2:]

    all_params = resistance_params + capacitance_params

    x_positions = np.arange(len(all_params))

    resistance_x = [all_params.index(param) for param in resistance_params]

    capacitance_x = [all_params.index(param) for param in capacitance_params]

    # Resistance bars
    if resistance_params:

        for i, (
            xpos,
            value,
            error,
            param,
        ) in enumerate(
            zip(
                resistance_x,
                resistance_values,
                resistance_errors,
                resistance_params,
            )
        ):

            ax_res.bar(
                xpos,
                value,
                yerr=error,
                width=0.25,
                capsize=5,
                alpha=0.9,
                color=resistance_colours[i],
                edgecolor="black",
                linewidth=1.2,
                label=param,
            )

    # Capacitance bars
    if capacitance_params:

        for i, (
            xpos,
            value,
            error,
            param,
        ) in enumerate(
            zip(
                capacitance_x,
                capacitance_values,
                capacitance_errors,
                capacitance_params,
            )
        ):

            ax_cap.bar(
                xpos,
                value,
                yerr=error,
                width=0.25,
                capsize=5,
                alpha=0.9,
                color=capacitance_colours[i],
                edgecolor="black",
                linewidth=1.2,
                label=param,
            )

    # Axes formatting
    ax_res.set_xticks(x_positions)

    ax_res.set_xticklabels(
        all_params,
        fontweight="bold",
    )

    ax_res.set_ylabel(
        "Resistance / Ω",
        color="darkred",
        fontsize=12,
        fontweight="bold",
    )

    ax_cap.set_ylabel(
        "Capacitance / F",
        color="darkblue",
        fontsize=12,
        fontweight="bold",
    )

    ax_res.set_yscale("log")
    ax_cap.set_yscale("log")

    ax_res.set_ylim(bottom=1e1, top=1e15)
    ax_cap.set_ylim(bottom=1e-12, top=1e-2)

    ax_res.set_title(f"{sample_name} | {circuit_name}")

    save_fig(
        save_folder / f"{sample_name}_{circuit_name}_dual_axis_parameters",
        fig,
        {ax_res, ax_cap},
        save_to_png,
        save_to_svg,
    )


def plot_Q_and_capacitances(
    data_dir,
    circuit_name,
    sample,
    q_columns,
    effective_capacitance_columns,
    save_to_png=True,
    save_to_svg=True,
):

    parameters_csv = data_dir / f"eis_fit_parameters_{circuit_name}.csv"

    save_folder = data_dir / "plots" / sample / "bar_charts"
    save_folder.mkdir(exist_ok=True, parents=True)

    df = pd.read_csv(parameters_csv)

    df_sample = df[df["sample"] == sample]

    if df_sample.empty:
        print(f"Sample '{sample}' not found.")
        return

    row = df_sample.iloc[0]

    q_params = []
    q_values = []
    q_errors = []

    ceff_params = []
    ceff_values = []
    ceff_errors = []

    # Collect Q values
    for param in q_columns:

        if param not in df.columns:
            print(f"Skipping {param}: not found in dataframe")
            continue

        value = row[param]

        sd_col = f"SD_{param}"
        error = row[sd_col] if sd_col in df.columns else 0

        if pd.isna(value):
            continue

        q_params.append(param)
        q_values.append(value)
        q_errors.append(error if not pd.isna(error) else 0)

    # Collect effective capacitances
    for param in effective_capacitance_columns:

        if param not in df.columns:
            print(f"Skipping {param}: not found in dataframe")
            continue

        value = row[param]

        sd_col = f"SD_{param}"
        error = row[sd_col] if sd_col in df.columns else 0

        if pd.isna(value):
            continue

        ceff_params.append(param)
        ceff_values.append(value)
        ceff_errors.append(error if not pd.isna(error) else 0)

    if not q_params and not ceff_params:
        print(f"No capacitance parameters found for {sample}")
        return

    # Plot
    fig, ax_q = plt.subplots(figsize=(8, 5))

    ax_ceff = ax_q.twinx()

    q_colours = sns.color_palette(
        "Blues",
        n_colors=len(q_params) + 2,
    )[2:]

    ceff_colours = sns.color_palette(
        "Greens",
        n_colors=len(ceff_params) + 2,
    )[2:]

    all_params = q_params + ceff_params

    x_positions = np.arange(len(all_params))

    q_x = [all_params.index(param) for param in q_params]

    ceff_x = [all_params.index(param) for param in ceff_params]

    # Q bars
    for i, (
        xpos,
        value,
        error,
        param,
    ) in enumerate(
        zip(
            q_x,
            q_values,
            q_errors,
            q_params,
        )
    ):

        ax_q.bar(
            xpos,
            value,
            yerr=error,
            width=0.25,
            capsize=5,
            alpha=0.9,
            color=q_colours[i],
            edgecolor="black",
            linewidth=1.2,
            label=param,
        )

    # Effective capacitance bars
    for i, (
        xpos,
        value,
        error,
        param,
    ) in enumerate(
        zip(
            ceff_x,
            ceff_values,
            ceff_errors,
            ceff_params,
        )
    ):

        ax_ceff.bar(
            xpos,
            value,
            yerr=error,
            width=0.25,
            capsize=5,
            alpha=0.9,
            color=ceff_colours[i],
            edgecolor="black",
            linewidth=1.2,
            label=param,
        )

    # Formatting
    ax_q.set_xticks(x_positions)

    ax_q.set_xticklabels(
        all_params,
        fontweight="bold",
    )

    ax_q.set_ylabel(
        "fitted pseudo-capacitance Q",
        color="darkblue",
        fontsize=12,
        fontweight="bold",
    )

    ax_ceff.set_ylabel(
        "Effective capacitance / F",
        color="darkgreen",
        fontsize=12,
        fontweight="bold",
    )

    ax_q.set_yscale("log")
    ax_ceff.set_yscale("log")

    ax_q.set_title(f"{sample} | {circuit_name}")

    save_fig(
        save_folder / f"{sample}_{circuit_name}_Q_and_capacitance",
        fig,
        {ax_q, ax_ceff},
        save_to_png,
        save_to_svg,
    )

def plot_conductivities(
    data_dir,
    circuit_name,
    sample,
    conductivity_columns,
    save_to_png=True,
    save_to_svg=True,
):

    parameters_csv = data_dir / f"eis_fit_parameters_{circuit_name}.csv"

    save_folder = data_dir / "plots" / sample / "bar_charts"
    save_folder.mkdir(exist_ok=True, parents=True)

    df = pd.read_csv(parameters_csv)

    df_sample = df[df["sample"] == sample]

    if df_sample.empty:
        print(f"Sample '{sample}' not found.")
        return

    row = df_sample.iloc[0]

    conductivity_params = []
    conductivity_values = []
    conductivity_errors = []

    # Collect conductivity values
    for param in conductivity_columns:

        if param not in df.columns:
            print(f"Skipping {param}: not found in dataframe")
            continue

        value = row[param]

        sd_col = f"SD_{param}"
        error = row[sd_col] if sd_col in df.columns else 0

        if pd.isna(value):
            continue

        conductivity_params.append(param)
        conductivity_values.append(value)
        conductivity_errors.append(
            error if not pd.isna(error) else 0
        )

    if not conductivity_params:
        print(f"No conductivity parameters found for {sample}")
        return

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))

    conductivity_colours = sns.color_palette(
        "Purples",
        n_colors=len(conductivity_params) + 2,
    )[2:]

    x_positions = np.arange(len(conductivity_params))

    # Conductivity bars
    for i, (
        xpos,
        value,
        error,
        param,
    ) in enumerate(
        zip(
            x_positions,
            conductivity_values,
            conductivity_errors,
            conductivity_params,
        )
    ):

        ax.bar(
            xpos,
            value,
            yerr=error,
            width=0.25,
            capsize=5,
            alpha=0.9,
            color=conductivity_colours[i],
            edgecolor="black",
            linewidth=1.2,
            label=param,
        )

    # Formatting
    ax.set_xticks(x_positions)

    ax.set_xticklabels(
        conductivity_params,
        fontweight="bold",
    )

    ax.set_ylabel(
        "Conductivity / S.cm$^{-1}$",
        color="indigo",
        fontsize=12,
        fontweight="bold",
    )

    ax.set_yscale("log")

    ax.set_title(f"{sample} | {circuit_name}")

    save_fig(
        save_folder / f"{sample}_{circuit_name}_conductivities",
        fig,
        {ax},
        save_to_png,
        save_to_svg,
    )


# ----------------------- analysing function ----------------------- #


def eis_analysis(
    data_dir,
    CIRCUITS,
    thickness_cm,
    sd_thickness_cm,
    area_cm2,
    sd_area_cm2,
    sigma_omega,
    save_to_png,
    save_to_svg,
):
    """
    data_dir : a pathlib PATH pointing towards --/eis_fitting/processed/dataset/fits/
    thickness_cm & area_cm2 : float
    save_to_png/svg : Boolean
    """

    for circuit_name in CIRCUITS:

        circuit_data = data_dir / f"eis_fit_parameters_{circuit_name}.csv"

        add_conductivity_columns(
            circuit_data,
            thickness_cm,
            sd_thickness_cm,
            area_cm2,
            sd_area_cm2,
        )
        add_Ceff_columns(circuit_data, sigma_omega)

        plots_path = data_dir / "plots/"

        for dir_path in plots_path.iterdir():
            sample = dir_path.name

            # excepts the "_all_files" plot
            if not sample.startswith("_"):
                dir_path = plots_path / sample

                resistance_columns = get_element_columns(circuit_data, "R")
                capacitance_columns = get_element_columns(circuit_data, "Ceff")
                conductivity_columns = get_element_columns(circuit_data, "conductivity")

                # get_element_columns also gives n values, hence the condition since Q is "CPE_i_0" and n "CPE_i_1"
                Q_columns = {
                    el
                    for el in get_element_columns(circuit_data, "CPE")
                    if el.endswith("0")
                }

                plot_fit_parameters_dual_axis_for_sample(
                    data_dir,
                    circuit_name,
                    sample,
                    resistance_columns,
                    capacitance_columns,
                    save_to_png,
                    save_to_svg,
                )

                plot_Q_and_capacitances(
                    data_dir,
                    circuit_name,
                    sample,
                    Q_columns,
                    capacitance_columns,
                    save_to_png,
                    save_to_svg,
                )

                plot_conductivities(
                    data_dir,
                    circuit_name,
                    sample,
                    conductivity_columns,
                    save_to_png,
                    save_to_svg,
                )

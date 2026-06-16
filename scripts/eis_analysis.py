import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb, to_hex
import seaborn as sns

from .utils import save_fig

# ------- Style functions ------- #


def adjust_colour(colour, factor=0.2):
    """
    factor > 0 : lighten
    factor < 0 : darken
    """

    rgb = np.array(to_rgb(colour))

    if factor >= 0:
        rgb = rgb + (1 - rgb) * factor
    else:
        rgb = rgb * (1 + factor)

    return to_hex(rgb)


def get_parameter_style(param, display_mapping):
    """
    Gets colour/order for raw and derived parameters.

    Raw:
        R_i
        Q_DL

    Derived:
        conductivity_S_cm_R_i -> inherits R_i
        Ceff_DL              -> inherits Q_DL
    """

    is_derived = False
    base_param = param

    if param.startswith("conductivity_S_cm_"):
        base_param = param.replace("conductivity_S_cm_", "")
        is_derived = True

    elif param.startswith("Ceff_"):
        base_param = "Q_" + param.replace("Ceff_", "")
        is_derived = True

    style = display_mapping.get(base_param, {})

    colour = style.get("colour", "gray")
    order = style.get("order", float("inf"))

    if is_derived:
        colour = adjust_colour(colour, factor=-0.35)

    return order, colour


def get_associated_alpha(param):
    """
    Returns the alpha column associated with Q or Ceff parameters.
    """

    if param.startswith("Q_"):
        return param.replace("Q_", "alpha_")

# ------- Helper functions ------- #


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

    for Q_col in [c for c in df.columns if c.startswith("Q_")]:

        name = Q_col.split("_")[1]

        alpha_col = f"alpha_{name}"
        dQ_col = f"SD_Q_{name}"
        dalpha_col = f"SD_alpha_{name}"

        if not all(col in df.columns for col in [alpha_col, dQ_col, dalpha_col]):
            print(f"Skipping incomplete CPE {name}")
            continue

        Q = df[Q_col].astype(float)
        dQ = df[dQ_col].astype(float)
        n = df[alpha_col].astype(float)
        dn = df[dalpha_col].astype(float)

        Ceff = Q * omega ** (n - 1)

        rel = np.sqrt(
            (dQ / Q) ** 2
            + ((n - 1) * sigma_omega / omega) ** 2
            + (np.log(omega) * dn) ** 2
        )

        df[f"Ceff_{name}"] = Ceff
        df[f"SD_Ceff_{name}"] = Ceff * rel

    df.to_csv(parameters_csv, index=False)


def plot_parameter_bars(
    data_dir,
    circuit_name,
    sample,
    left_columns,
    left_axis_label,
    figure_name,
    mapping,
    right_columns=None,
    right_axis_label=None,
    save_preferences=None,
    left_ylim=None,
    right_ylim=None,
    show_alpha=True,
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
    sample_name = row["sample"]

    # ---------------- Mapping ---------------- #

    display_mapping = {
        info["name"]: {
            "colour": info["colour"],
            "order": info["order"],
        }
        for info in mapping.values()
    }

    # ---------------- Helper to collect plotting data ---------------- #

    def collect_axis_data(columns):

        axis_data = []

        if columns is None:
            return axis_data

        for param in columns:

            if param not in df.columns:
                continue

            value = row[param]

            if pd.isna(value):
                continue

            sd_col = f"SD_{param}"
            error = (
                row[sd_col] if sd_col in df.columns and not pd.isna(row[sd_col]) else 0
            )

            order, colour = get_parameter_style(param, display_mapping)

            alpha_label = None

            alpha_col = get_associated_alpha(param)

            if show_alpha and alpha_col is not None and alpha_col in row.index:

                alpha_value = row[alpha_col]
            
                if not pd.isna(alpha_value):
                
                    sd_alpha_col = f"SD_{alpha_col}"
            
                    if sd_alpha_col in row.index and not pd.isna(row[sd_alpha_col]):
                        sd_alpha = row[sd_alpha_col]
                        alpha_label = (
                            fr"$\boldsymbol{{\alpha}}$="
                            f"{alpha_value:.3f}"
                            "\n"
                            fr"$\boldsymbol{{\pm}}$"
                            f"{sd_alpha:.3f}"
                        )
                    else:
                        alpha_label = fr"$\boldsymbol{{\alpha}}$={alpha_value:.3f}"

            axis_data.append(
                (
                    order,
                    param,
                    value,
                    error,
                    colour,
                    alpha_label,
                )
            )

        axis_data.sort(key=lambda x: x[0])

        return axis_data

    left_data = collect_axis_data(left_columns)
    right_data = collect_axis_data(right_columns)

    # ---------------- Check ---------------- #

    if not left_data and not right_data:
        print(f"No valid parameters found for {sample_name}")
        return

    # ---------------- Unpack ---------------- #

    left_params = [x[1] for x in left_data]
    left_values = [x[2] for x in left_data]
    left_errors = [x[3] for x in left_data]
    left_colours = [x[4] for x in left_data]
    left_alpha_labels = [x[5] for x in left_data]

    right_params = [x[1] for x in right_data]
    right_values = [x[2] for x in right_data]
    right_errors = [x[3] for x in right_data]
    right_colours = [x[4] for x in right_data]
    right_alpha_labels = [x[5] for x in right_data]

    # ---------------- Plot ---------------- #

    fig, ax_left = plt.subplots(figsize=(8, 5))

    ax_right = ax_left.twinx() if right_columns is not None else None

    all_params = left_params + right_params

    x_positions = np.arange(len(all_params))
    left_x = np.arange(len(left_params))
    right_x = np.arange(len(left_params), len(all_params))

    def plot_axis_bars(
        ax,
        x_values,
        values,
        errors,
        params,
        colours,
        alpha_labels,
    ):

        for xpos, value, error, param, colour, alpha_label in zip(
            x_values,
            values,
            errors,
            params,
            colours,
            alpha_labels,
        ):

            ax.bar(
                xpos,
                value,
                yerr=error,
                width=0.25,
                capsize=5,
                alpha=0.9,
                color=colour,
                edgecolor="black",
                linewidth=1.2,
                label=param,
            )

            if alpha_label is not None:

                y_text = value * 1.03

                if error is not None and not pd.isna(error) and error > 0:
                    y_text = (value + error) * 1.03

                ax.text(
                    xpos,
                    y_text,
                    alpha_label,
                    ha="center",
                    va="bottom",
                    fontsize=12,
                    color=colour,
                    fontweight="bold",
                )

    plot_axis_bars(
        ax_left,
        left_x,
        left_values,
        left_errors,
        left_params,
        left_colours,
        left_alpha_labels,
    )

    if ax_right is not None:

        plot_axis_bars(
            ax_right,
            right_x,
            right_values,
            right_errors,
            right_params,
            right_colours,
            right_alpha_labels,
        )

    ax_left.set_xticks(x_positions)
    ax_left.set_xticklabels(
        all_params,
        fontsize=14,
        fontweight="bold",
    )

    ax_left.set_ylabel(left_axis_label, fontsize=16)
    ax_left.set_yscale("log")

    if left_ylim is not None:
        ax_left.set_ylim(*left_ylim)

    if ax_right is not None:

        ax_right.set_ylabel(
            right_axis_label,
            fontsize=16,
        )

        ax_right.set_yscale("log")

        if right_ylim is not None:
            ax_right.set_ylim(*right_ylim)

    ax_left.set_title(f"{sample_name} | {circuit_name}")

    axes = {ax_left}

    if ax_right is not None:
        axes.add(ax_right)

    save_fig(
        save_folder / f"{sample_name}_{circuit_name}_{figure_name}",
        fig,
        axes,
        save_preferences,
    )


# ----------------------- analysing function ----------------------- #


def eis_analysis(
    input_file,
    CIRCUITS,
    thickness_cm,
    sd_thickness_cm,
    area_cm2,
    sd_area_cm2,
    sigma_omega,
    save_preferences=None,
    plot=False,
):
    """
    data_dir : a pathlib PATH pointing towards --/eis_fitting/processed/dataset/fits/
    thickness_cm & area_cm2 : float
    save_preferences : dict with keys "png" and "svg" and boolean values
    """
    data_dir = input_file / "fits/"

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

        if not plot:
            continue

        csv_path = input_file / "csv/"

        for file_path in csv_path.iterdir():
            sample = file_path.stem

            resistance_columns = get_element_columns(circuit_data, "R")
            capacitance_columns = get_element_columns(circuit_data, "Ceff")
            conductivity_columns = get_element_columns(circuit_data, "conductivity")

            # get_element_columns also gives n values, hence the condition since Q is "CPE_i_0" and n "CPE_i_1"
            Q_columns = get_element_columns(circuit_data, "Q")
            plot_parameter_bars(
                data_dir=data_dir,
                circuit_name=circuit_name,
                sample=sample,
                left_columns=resistance_columns,
                right_columns=Q_columns,
                left_axis_label=r"Resistance ($\Omega$)",
                right_axis_label=r"Pseudo Capacitance ($F\times s^{\alpha-1}$)",
                figure_name="R_and_Q",
                mapping=CIRCUITS[circuit_name]["mapping"],
                left_ylim=(1e1, 1e15),
                right_ylim=(1e-12, 1e-2),
                save_preferences=save_preferences,
            )
            """plot_parameter_bars(
                data_dir=data_dir,
                circuit_name=circuit_name,
                sample=sample,
                left_columns=Q_columns,
                right_columns=capacitance_columns,
                left_axis_label=r"Pseudo-capacitance Q ($F\times s^{\alpha-1}$)",
                right_axis_label=r"Effective capacitance ($F$)",
                figure_name="Q_and_Ceff",
                mapping=CIRCUITS[circuit_name]["mapping"],
                left_ylim=(1e-7, 1e-5),
                save_preferences=save_preferences,
            )"""
            plot_parameter_bars(
                data_dir=data_dir,
                circuit_name=circuit_name,
                sample=sample,
                left_columns=conductivity_columns,
                left_axis_label=r"Conductivity ($S.cm^{-1}$)",
                figure_name="conductivities",
                mapping=CIRCUITS[circuit_name]["mapping"],
                left_ylim=(1e-8, 3e-3),
                save_preferences=save_preferences,
            )

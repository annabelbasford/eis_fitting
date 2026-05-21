import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns


# -------------------------
# User inputs
# -------------------------
data_dir = Path("/home/abasford/projects/eis_fitting/fits/")

thickness_cm = 0.1   # change this, e.g. 1 mm = 0.1 cm
area_cm2 = 1.0       # change this to electrode/sample area


# -------------------------
# Helper functions
# -------------------------
def calc_conductivity(R_bulk, thickness_cm, area_cm2):
    """
    Calculate conductivity in S/cm.

    sigma = L / (R * A)

    Parameters
    ----------
    R_bulk : float
        Bulk resistance in ohms.
    thickness_cm : float
        Sample thickness in cm.
    area_cm2 : float
        Electrode/sample area in cm2.
    """
    return thickness_cm / (R_bulk * area_cm2)


def add_conductivity_column(df, resistance_column, thickness_cm, area_cm2):
    df = df.copy()

    df["R_bulk_used"] = df[resistance_column]

    df["conductivity_S_cm"] = calc_conductivity(
        R_bulk=df["R_bulk_used"],
        thickness_cm=thickness_cm,
        area_cm2=area_cm2,
    )

    df["conductivity_S_m"] = df["conductivity_S_cm"] * 100

    return df


# -------------------------
# Read fitted parameter CSVs
# -------------------------
randles_data = pd.read_csv(data_dir / "eis_fit_parameters_randles_cpe.csv")
interface_bulk_data = pd.read_csv(data_dir / "eis_fit_parameters_interface_bulk.csv")


# -------------------------
# Calculate conductivity
# -------------------------

# Randles circuit:
# R_1-p(CPE_1,R_2)
# R_2 is used as the main fitted resistance
randles_data = add_conductivity_column(
    df=randles_data,
    resistance_column="R_2",
    thickness_cm=thickness_cm,
    area_cm2=area_cm2,
)

# Interface-bulk circuit:
# R_1-p(CPE_1,R_2)-p(R_3,CPE_2)
# R_3 is used as the bulk hydrogel resistance
interface_bulk_data = add_conductivity_column(
    df=interface_bulk_data,
    resistance_column="R_3",
    thickness_cm=thickness_cm,
    area_cm2=area_cm2,
)


# -------------------------
# Save processed outputs
# -------------------------
randles_data.to_csv(
    data_dir / "eis_fit_parameters_randles_cpe_with_conductivity.csv",
    index=False,
    float_format="%.6g",
)

interface_bulk_data.to_csv(
    data_dir / "eis_fit_parameters_interface_bulk_with_conductivity.csv",
    index=False,
    float_format="%.6g",
)


print("Done.")
print("Saved:")
print(data_dir / "eis_fit_parameters_randles_cpe_with_conductivity.csv")
print(data_dir / "eis_fit_parameters_interface_bulk_with_conductivity.csv")

def plot_fit_parameters_dual_axis_per_sample(
    df,
    circuit_name,
    resistance_columns,
    cpe_columns,
    sample_column="sample",
    save_folder=None,
):
    """
    For each row/sample, plot resistance parameters and CPE Q parameters
    on the same bar plot using two y-axes.

    Left y-axis:
        Resistance parameters, e.g. R_1, R_2, R_3

    Right y-axis:
        CPE Q parameters, e.g. CPE_1_0, CPE_2_0

    Error bars are taken from:
        SD_R_1, SD_CPE_1_0, etc.
    """

    save_folder = Path(save_folder)
    save_folder.mkdir(exist_ok=True, parents=True)


    for _, row in df.iterrows():
        sample_name = row[sample_column]

        resistance_params = []
        resistance_values = []
        resistance_errors = []

        cpe_params = []
        cpe_values = []
        cpe_errors = []

        # -------------------------
        # Collect resistance params
        # -------------------------
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

        # -------------------------
        # Collect CPE params
        # -------------------------
        for param in cpe_columns:
            if param not in df.columns:
                print(f"Skipping {param}: not found in dataframe")
                continue

            value = row[param]
            sd_col = f"SD_{param}"
            error = row[sd_col] if sd_col in df.columns else 0

            if pd.isna(value):
                continue

            cpe_params.append(param)
            cpe_values.append(value)
            cpe_errors.append(error if not pd.isna(error) else 0)

        if not resistance_params and not cpe_params:
            print(f"No valid parameters found for {sample_name}")
            continue

        # -------------------------
        # Plot
        # -------------------------
        fig, ax_res = plt.subplots(figsize=(8, 5))
        ax_cpe = ax_res.twinx()

        resistance_colours = sns.color_palette("Reds", n_colors=len(resistance_params) + 2)[2:]
        cpe_colours = sns.color_palette("Blues", n_colors=len(cpe_params) + 2)[2:]

        all_params = resistance_params + cpe_params
        x_positions = np.arange(len(all_params))

        resistance_x = [
            all_params.index(param)
            for param in resistance_params
        ]

        cpe_x = [
            all_params.index(param)
            for param in cpe_params
        ]

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
                    width=0.25,           # thinner bars
                    capsize=5,
                    alpha=0.9,
                    color=resistance_colours[i],
                    edgecolor="black",    # black border
                    linewidth=1.2,
                    label=param,
                )

        if cpe_params:
            for i, (
                xpos,
                value,
                error,
                param,
            ) in enumerate(
                zip(
                    cpe_x,
                    cpe_values,
                    cpe_errors,
                    cpe_params,
                )
            ):

                ax_cpe.bar(
                    xpos,
                    value,
                    yerr=error,
                    width=0.25,
                    capsize=5,
                    alpha=0.9,
                    color=cpe_colours[i],
                    edgecolor="black",
                    linewidth=1.2,
                    label=param,
                )

        ax_res.set_xticks(x_positions)
        ax_res.set_xticklabels(all_params, fontweight='bold')

        ax_res.set_ylabel("Resistance / Ω", color='darkred', fontsize=12, fontweight='bold')
        ax_cpe.set_ylabel("CPE Q / pseudo-capacitance", color='darkblue', fontsize=12, fontweight='bold')

        ax_res.set_yscale("log")
        ax_cpe.set_yscale("log")

        ax_res.set_ylim(bottom=1e1,top=1e15) 
        ax_cpe.set_ylim(bottom=1e-6, top=1e-3) 

        #ax_res.set_xlabel("Fitted parameter")
        ax_res.set_title(f"{sample_name} | {circuit_name}")

        fig.tight_layout()

        safe_sample_name = (
            str(sample_name)
            .replace("/", "_")
            .replace(" ", "_")
            .replace(":", "_")
        )

        fig.savefig(
            save_folder / f"{safe_sample_name}_{circuit_name}_dual_axis_parameters.png",
            dpi=300,
            bbox_inches="tight",
        )

        plt.close(fig)

plot_fit_parameters_dual_axis_per_sample(
    df=randles_data,
    circuit_name="randles_cpe",
    resistance_columns=["R_1", "R_2"],
    cpe_columns=["CPE_1_0"],
    save_folder=data_dir / "parameter_bar_plots",
)

plot_fit_parameters_dual_axis_per_sample(
    df=interface_bulk_data,
    circuit_name="interface_bulk",
    resistance_columns=["R_1", "R_2", "R_3"],
    cpe_columns=["CPE_1_0", "CPE_2_0"],
    save_folder=data_dir / "parameter_bar_plots",
)
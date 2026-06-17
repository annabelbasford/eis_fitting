import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex, to_rgb

from eis_fitting.utils.figures import FigureSaver


class AnalysisPlotter:
    def __init__(self, circuits: dict):
        self.circuits = circuits

    def run(self, experiment) -> None:
        figure_saver = FigureSaver(experiment.save_preferences)

        for circuit_name in experiment.circuits:
            parameters_csv = experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"

            if not parameters_csv.exists():
                continue

            for csv_path in experiment.paths.csv.glob("*.csv"):
                sample = csv_path.stem

                resistance_columns = self.get_element_columns(parameters_csv, "R")
                q_columns = self.get_element_columns(parameters_csv, "Q")
                conductivity_columns = self.get_element_columns(parameters_csv, "conductivity")

                self.plot_parameter_bars(
                    parameters_csv=parameters_csv,
                    circuit_name=circuit_name,
                    sample=sample,
                    left_columns=resistance_columns,
                    right_columns=q_columns,
                    left_axis_label=r"Resistance ($\Omega$)",
                    right_axis_label=r"Pseudo capacitance ($F\times s^{\alpha-1}$)",
                    figure_name="R_and_Q",
                    mapping=self.circuits[circuit_name]["mapping"],
                    save_root=experiment.paths.plots,
                    figure_saver=figure_saver,
                    left_ylim=(1e1, 1e15),
                    right_ylim=(1e-12, 1e-2),
                    show_alpha=True,
                )

                self.plot_parameter_bars(
                    parameters_csv=parameters_csv,
                    circuit_name=circuit_name,
                    sample=sample,
                    left_columns=conductivity_columns,
                    left_axis_label=r"Conductivity ($S.cm^{-1}$)",
                    figure_name="conductivities",
                    mapping=self.circuits[circuit_name]["mapping"],
                    save_root=experiment.paths.plots,
                    figure_saver=figure_saver,
                    left_ylim=(1e-8, 3e-3),
                    show_alpha=False,
                )

    @staticmethod
    def adjust_colour(colour, factor=0.2):
        rgb = np.array(to_rgb(colour))

        if factor >= 0:
            rgb = rgb + (1 - rgb) * factor
        else:
            rgb = rgb * (1 + factor)

        return to_hex(rgb)

    @staticmethod
    def get_element_columns(parameters_csv, first_chars):
        df = pd.read_csv(parameters_csv)

        return {
            col
            for col in df.columns
            if col.startswith(first_chars)
            and not col.endswith("error")
        }

    def get_parameter_style(self, param, display_mapping):
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
            colour = self.adjust_colour(colour, factor=-0.35)

        return order, colour

    @staticmethod
    def get_associated_alpha(param):
        if param.startswith("Q_"):
            return param.replace("Q_", "alpha_")

        return None

    def plot_parameter_bars(
        self,
        parameters_csv,
        circuit_name,
        sample,
        left_columns,
        left_axis_label,
        figure_name,
        mapping,
        save_root,
        figure_saver,
        right_columns=None,
        right_axis_label=None,
        left_ylim=None,
        right_ylim=None,
        show_alpha=True,
    ):
        save_folder = save_root / sample / circuit_name
        save_folder.mkdir(parents=True, exist_ok=True)

        df = pd.read_csv(parameters_csv)
        df_sample = df[df["sample"] == sample]

        if df_sample.empty:
            print(f"Sample '{sample}' not found.")
            return

        row = df_sample.iloc[0]

        display_mapping = {
            info["name"]: {
                "colour": info["colour"],
                "order": info["order"],
            }
            for info in mapping.values()
        }

        left_data = self._collect_axis_data(
            row,
            df.columns,
            left_columns,
            display_mapping,
            show_alpha,
        )

        right_data = self._collect_axis_data(
            row,
            df.columns,
            right_columns,
            display_mapping,
            show_alpha,
        )

        if not left_data and not right_data:
            print(f"No valid parameters found for {sample}")
            return

        fig, ax_left = plt.subplots(figsize=(8, 5))
        ax_right = ax_left.twinx() if right_columns is not None else None

        left_params, left_values, left_errors, left_colours, left_alpha_labels = self._unpack_axis_data(left_data)
        right_params, right_values, right_errors, right_colours, right_alpha_labels = self._unpack_axis_data(right_data)

        all_params = left_params + right_params

        x_positions = np.arange(len(all_params))
        left_x = np.arange(len(left_params))
        right_x = np.arange(len(left_params), len(all_params))

        self._plot_axis_bars(
            ax_left,
            left_x,
            left_values,
            left_errors,
            left_params,
            left_colours,
            left_alpha_labels,
        )

        if ax_right is not None:
            self._plot_axis_bars(
                ax_right,
                right_x,
                right_values,
                right_errors,
                right_params,
                right_colours,
                right_alpha_labels,
            )

        ax_left.set_xticks(x_positions)
        ax_left.set_xticklabels(all_params, fontsize=14, fontweight="bold")

        ax_left.set_ylabel(left_axis_label, fontsize=16)
        ax_left.set_yscale("log")

        if left_ylim is not None:
            ax_left.set_ylim(*left_ylim)

        if ax_right is not None:
            ax_right.set_ylabel(right_axis_label, fontsize=16)
            ax_right.set_yscale("log")

            if right_ylim is not None:
                ax_right.set_ylim(*right_ylim)

        ax_left.set_title(f"{sample} | {circuit_name}")

        axes = {ax_left}

        if ax_right is not None:
            axes.add(ax_right)

        figure_saver.save(
            save_folder / f"{sample}_{circuit_name}_{figure_name}",
            fig,
            axes,
        )

    def _collect_axis_data(self, row, columns, selected_columns, display_mapping, show_alpha):
        axis_data = []

        if selected_columns is None:
            return axis_data

        for param in selected_columns:
            if param not in columns:
                continue

            value = row[param]

            if pd.isna(value):
                continue

            sd_col = f"SD_{param}"
            error = row[sd_col] if sd_col in columns and not pd.isna(row[sd_col]) else 0

            order, colour = self.get_parameter_style(param, display_mapping)

            alpha_label = None
            alpha_col = self.get_associated_alpha(param)

            if show_alpha and alpha_col is not None and alpha_col in row.index:
                alpha_value = row[alpha_col]

                if not pd.isna(alpha_value):
                    sd_alpha_col = f"SD_{alpha_col}"

                    if sd_alpha_col in row.index and not pd.isna(row[sd_alpha_col]):
                        alpha_label = (
                            fr"$\boldsymbol{{\alpha}}$="
                            f"{alpha_value:.3f}"
                            "\n"
                            fr"$\boldsymbol{{\pm}}$"
                            f"{row[sd_alpha_col]:.3f}"
                        )
                    else:
                        alpha_label = fr"$\boldsymbol{{\alpha}}$={alpha_value:.3f}"

            axis_data.append((order, param, value, error, colour, alpha_label))

        axis_data.sort(key=lambda x: x[0])

        return axis_data

    @staticmethod
    def _unpack_axis_data(axis_data):
        if not axis_data:
            return [], [], [], [], []

        params = [x[1] for x in axis_data]
        values = [x[2] for x in axis_data]
        errors = [x[3] for x in axis_data]
        colours = [x[4] for x in axis_data]
        alpha_labels = [x[5] for x in axis_data]

        return params, values, errors, colours, alpha_labels

    @staticmethod
    def _plot_axis_bars(ax, x_values, values, errors, params, colours, alpha_labels):
        for xpos, value, error, param, colour, alpha_label in zip(
            x_values,
            values,
            errors,
            params,
            colours,
            alpha_labels,
        ):
            if not np.isfinite(value):
                continue

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
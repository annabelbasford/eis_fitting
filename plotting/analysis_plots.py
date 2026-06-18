import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.colors import to_rgb, to_hex

from eis_fitting.utils.figures import FigureSaver


class AnalysisPlotter:
    def __init__(self, circuits: dict, plotting_limits: dict | None = None):
        self.circuits = circuits
        self.plotting_limits = plotting_limits or {}

    """
    Plot fitted and derived parameters as bar charts.

    This class reads analysed/fitted parameter CSVs and creates the
    parameter summary plots:

    processed/
    └── fits/
        └── plots/
            └── sample/
                └── circuit/
                    ├── sample_circuit_R_and_Q.png
                    └── sample_circuit_conductivities.png
    """

    def run(self, experiment) -> None:
        """
        Plot analysis bar charts for each sample and selected circuit.
        """

        figure_saver = FigureSaver(experiment.save_preferences)

        for circuit_name in experiment.circuits:
            parameters_csv = (
                experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"
            )

            if not parameters_csv.exists():
                print(f"Skipping missing file: {parameters_csv}")
                continue

            for csv_path in sorted(experiment.paths.csv.glob("*.csv")):
                sample = csv_path.stem

                resistance_columns = self.get_element_columns(
                    parameters_csv,
                    "R",
                )

                q_columns = self.get_element_columns(
                    parameters_csv,
                    "Q",
                )

                capacitance_columns = self.get_element_columns(
                    parameters_csv,
                    "C",
                )

                conductivity_columns = self.get_element_columns(
                    parameters_csv,
                    "conductivity",
                )

                right_columns = q_columns

                right_axis_label = r"Pseudo capacitance " r"($F\times s^{\alpha-1}$)"

                if not right_columns:
                    right_columns = capacitance_columns
                    right_axis_label = r"Capacitance ($F$)"

                r_and_q_limits = self.get_limits("R_and_Q")

                self.plot_parameter_bars(
                    parameters_csv=parameters_csv,
                    circuit_name=circuit_name,
                    sample=sample,
                    left_columns=resistance_columns,
                    right_columns=right_columns,
                    left_axis_label=r"Resistance ($\Omega$)",
                    right_axis_label=right_axis_label,
                    figure_name="R_and_Q",
                    mapping=self.circuits[circuit_name]["mapping"],
                    save_root=experiment.paths.plots,
                    figure_saver=figure_saver,
                    left_ylim=r_and_q_limits.get("left_ylim"),
                    right_ylim=r_and_q_limits.get("right_ylim"),
                    show_alpha=True,
                )

                conductivity_limits = self.get_limits("conductivities")

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
                    left_ylim=conductivity_limits.get("left_ylim"),
                    right_ylim=conductivity_limits.get("right_ylim"),
                    show_alpha=False,
                )

    def get_parameter_style(self, param, display_mapping):
        """
        Return plotting order and colour for a parameter.

        Derived parameters inherit the style of their parent parameter.
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
            colour = self.adjust_colour(colour, factor=-0.35)

        return order, colour

    def get_limits(self, figure_name: str) -> dict:
        return self.plotting_limits.get(figure_name, {})

    @staticmethod
    def get_element_columns(parameters_csv, first_chars):
        """
        Return fitted/derived parameter columns starting with first_chars.

        Excludes:
        - standard deviation columns
        - percent error columns
        - metadata/status columns
        """

        df = pd.read_csv(parameters_csv)

        excluded = {
            "sample",
            "circuit_name",
            "circuit_string",
            "fit_success",
            "fit_status",
            "covariance_warning",
            "error",
        }

        matching_columns = {
            col
            for col in df.columns
            if col.startswith(first_chars)
            and not col.startswith("SD_")
            and not col.endswith("_percent_error")
            and col not in excluded
        }

        return matching_columns

    @staticmethod
    def adjust_colour(colour, factor=0.2):
        """
        Lighten or darken a colour.

        factor > 0 : lighten
        factor < 0 : darken
        """

        rgb = np.array(to_rgb(colour))

        if factor >= 0:
            rgb = rgb + (1 - rgb) * factor
        else:
            rgb = rgb * (1 + factor)

        return to_hex(rgb)

    @staticmethod
    def get_associated_alpha(param):
        """
        Return the alpha column associated with a Q or Ceff parameter.
        """

        if param.startswith("Q_"):
            return param.replace("Q_", "alpha_")

        if param.startswith("Ceff_"):
            return "alpha_" + param.replace("Ceff_", "")

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
        """
        Plot one bar-chart figure for one sample and one circuit.
        """

        save_folder = save_root / sample / circuit_name

        save_folder.mkdir(parents=True, exist_ok=True)

        df = pd.read_csv(parameters_csv)
        df = self._clean_numeric_dataframe(df)

        df_sample = df[df["sample"] == sample]

        if df_sample.empty:
            print(f"Sample '{sample}' not found in {parameters_csv.name}")
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
            row=row,
            columns=df.columns,
            selected_columns=left_columns,
            display_mapping=display_mapping,
            show_alpha=show_alpha,
        )

        right_data = self._collect_axis_data(
            row=row,
            columns=df.columns,
            selected_columns=right_columns,
            display_mapping=display_mapping,
            show_alpha=show_alpha,
        )

        if not left_data and not right_data:
            print(f"No valid parameters found for {sample} | {circuit_name}")
            return

        fig, ax_left = plt.subplots(figsize=(8, 5))
        ax_right = ax_left.twinx() if right_data else None

        (
            left_params,
            left_values,
            left_errors,
            left_colours,
            left_alpha_labels,
        ) = self._unpack_axis_data(left_data)

        (
            right_params,
            right_values,
            right_errors,
            right_colours,
            right_alpha_labels,
        ) = self._unpack_axis_data(right_data)

        all_params = left_params + right_params

        x_positions = np.arange(len(all_params))
        left_x = np.arange(len(left_params))
        right_x = np.arange(
            len(left_params),
            len(left_params) + len(right_params),
        )

        self._plot_axis_bars(
            ax=ax_left,
            x_values=left_x,
            values=left_values,
            errors=left_errors,
            params=left_params,
            colours=left_colours,
            alpha_labels=left_alpha_labels,
        )

        if ax_right is not None:
            self._plot_axis_bars(
                ax=ax_right,
                x_values=right_x,
                values=right_values,
                errors=right_errors,
                params=right_params,
                colours=right_colours,
                alpha_labels=right_alpha_labels,
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
            ax_right.set_ylabel(right_axis_label, fontsize=16)
            ax_right.set_yscale("log")

            if right_ylim is not None:
                ax_right.set_ylim(*right_ylim)

        ax_left.set_title(f"{sample} | {circuit_name}")

        axes = {ax_left}

        if ax_right is not None:
            axes.add(ax_right)

        figure_saver.save(
            save_path=save_folder / f"{sample}_{circuit_name}_{figure_name}",
            fig=fig,
            axes=axes,
        )

    @staticmethod
    def _clean_numeric_dataframe(df):
        """
        Replace +/- inf by NaN for all numeric columns.
        """

        numeric_cols = df.select_dtypes(include="number").columns

        df[numeric_cols] = df[numeric_cols].replace(
            [np.inf, -np.inf],
            np.nan,
        )

        return df

    def _collect_axis_data(
        self,
        row,
        columns,
        selected_columns,
        display_mapping,
        show_alpha,
    ):
        axis_data = []

        if selected_columns is None:
            return axis_data

        for param in selected_columns:
            if param not in columns:
                continue

            value = self._finite_positive_or_none(row.get(param, np.nan))

            if value is None:
                continue

            sd_col = f"SD_{param}"
            error = None

            if sd_col in columns:
                error_candidate = self._finite_non_negative_or_none(
                    row.get(sd_col, np.nan)
                )

                if error_candidate is not None and value - error_candidate > 0:
                    error = error_candidate

            order, colour = self.get_parameter_style(
                param,
                display_mapping,
            )

            alpha_label = None
            alpha_col = self.get_associated_alpha(param)

            if show_alpha and alpha_col is not None and alpha_col in row.index:
                alpha_value = self._finite_or_none(row.get(alpha_col, np.nan))

                if alpha_value is not None:
                    sd_alpha_col = f"SD_{alpha_col}"
                    sd_alpha = None

                    if sd_alpha_col in row.index:
                        sd_alpha = self._finite_non_negative_or_none(
                            row.get(sd_alpha_col, np.nan)
                        )

                    if sd_alpha is not None:
                        alpha_label = (
                            rf"$\boldsymbol{{\alpha}}$="
                            f"{alpha_value:.3f}"
                            "\n"
                            rf"$\boldsymbol{{\pm}}$"
                            f"{sd_alpha:.3f}"
                        )

                    else:
                        alpha_label = rf"$\boldsymbol{{\alpha}}$=" f"{alpha_value:.3f}"

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
    def _plot_axis_bars(
        ax,
        x_values,
        values,
        errors,
        params,
        colours,
        alpha_labels,
    ):
        """
        Plot bars robustly.

        Invalid values are never passed to matplotlib.
        Invalid error bars are omitted.
        """

        for xpos, value, error, param, colour, alpha_label in zip(
            x_values,
            values,
            errors,
            params,
            colours,
            alpha_labels,
        ):
            if value is None:
                continue

            if not np.isfinite(value):
                continue

            kwargs = {}

            if error is not None and np.isfinite(error) and error >= 0:
                kwargs["yerr"] = error
                kwargs["capsize"] = 5

            ax.bar(
                xpos,
                value,
                width=0.25,
                alpha=0.9,
                color=colour,
                edgecolor="black",
                linewidth=1.2,
                label=param,
                **kwargs,
            )

            if alpha_label is not None:
                y_text = value * 1.03

                if error is not None and np.isfinite(error):
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

    @staticmethod
    def _finite_or_none(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None

        if not np.isfinite(value):
            return None

        return value

    @staticmethod
    def _finite_positive_or_none(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None

        if not np.isfinite(value):
            return None

        if value <= 0:
            return None

        return value

    @staticmethod
    def _finite_non_negative_or_none(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None

        if not np.isfinite(value):
            return None

        if value < 0:
            return None

        return value

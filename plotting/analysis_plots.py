import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ..utils import FigureSaver


class AnalysisPlotter:
    def __init__(self, circuits: dict, plotting: dict | None = None):
        self.circuits = circuits
        self.plotting = plotting or {}

    def run(self, experiment) -> None:
        """
        Plot analysis bar charts.

        For each circuit:
        1. Plot R/Q or R/C bar charts for each sample.
           Saved in:
               exp/fits/plots/<sample>/<circuit>/

        2. Plot one R_i conductivity summary chart for the whole experiment.
           Saved in:
               exp/fits/plots/
        """

        figure_saver = FigureSaver(experiment.save_preferences)

        for circuit_name in experiment.circuits:
            parameters_csv = (
                experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"
            )

            if not parameters_csv.exists():
                print(f"Skipping missing file: {parameters_csv}")
                continue

            # Per-sample R/Q or R/C bar charts
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

            right_columns = q_columns
            right_axis_label = r"Pseudo capacitance " r"($F\times s^{\alpha-1}$)"

            df_params = pd.read_csv(parameters_csv)

            if not right_columns:
                right_columns = capacitance_columns
                right_axis_label = r"Capacitance ($F$)"

            r_and_q_limits = self.plotting.get("R_and_Q", {})

            conductivities_limits = self.plotting.get("conductivities", {})

            for csv_path in sorted(experiment.paths.csv.glob("*.csv")):
                sample = csv_path.stem

                # checking if fit was successful for this sample and circuit before plotting
                row = df_params[
                    (df_params["sample"] == sample)
                    & (df_params["circuit_name"] == circuit_name)
                ]

                if row.empty or not row.iloc[0]["fit_success"]:
                    continue

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
                    dpi=experiment.save_preferences.get("dpi", 300),
                )

            conductivities_parameters = experiment.plotting["conductivities"]
            # One experiment-level R_i conductivity chart
            self.plot_conductivities_summary(
                experiment=experiment,
                parameters_csv=parameters_csv,
                figure_saver=figure_saver,
                circuit_name=circuit_name,
            )

    def plot_conductivities_summary(
        self,
        experiment,
        parameters_csv,
        circuit_name,
        figure_saver,
        dpi=300,
    ):
        """
        Plot one experiment-level conductivity summary per conductivity type.

        Settings are read from:

            experiment.plotting["conductivities"]

        Expected global.json structure:

            "plotting": {
                "conductivities": {
                    "left_ylim": [null, null],
                    "normalize": true,
                    "cmap_name": "viridis",
                    "log_scale": false,
                    "legend": {
                        "rotation": 0,
                        "ha": "center",
                        "fontsize": 14
                    }
                }
            }
        """

        conductivity_config = experiment.plotting.get("conductivities", {})

        y_lim = conductivity_config.get("left_ylim", [None, None])
        normalize = conductivity_config.get("normalize", False)
        cmap_name = conductivity_config.get("cmap_name", "viridis")
        log_scale = conductivity_config.get("log_scale", False)

        label_config = conductivity_config.get("legend", {})
        label_rotation = label_config.get("rotation", 0)
        label_ha = label_config.get("ha", "center")
        label_fontsize = label_config.get("fontsize", 14)

        experiment_name = experiment.name
        save_root = experiment.paths.plots

        def get_conductivity_label(conductivity_col):
            resistance_name = conductivity_col.replace(
                "conductivity_S_cm_",
                "",
            )

            if resistance_name.startswith("R_"):
                suffix = resistance_name.replace("R_", "")
                return rf"$\sigma_{{\mathrm{{{suffix}}}}}$"

            return rf"$\sigma_{{\mathrm{{{resistance_name}}}}}$"

        def get_output_suffix(conductivity_col):
            resistance_name = conductivity_col.replace(
                "conductivity_S_cm_",
                "",
            )

            safe_name = resistance_name.replace("_", "")
            return f"{safe_name}_conductivity"

        df = pd.read_csv(parameters_csv)
        df = self._clean_numeric_dataframe(df)

        if "sample" not in df.columns:
            print(
                "\n"
                + "\033[93m"
                + "\033[1m"
                + ":/"
                + "\033[0m"
                + f"  Skipping conductivity plot: no sample column in {parameters_csv.name}"
            )
            return

        conductivity_columns = [
            col
            for col in df.columns
            if col.startswith("conductivity_S_cm_")
            and not col.startswith("SD_")
            and not col.endswith("_percent_error")
        ]

        if not conductivity_columns:
            print(
                "\n"
                + "\033[93m"
                + "\033[1m"
                + ":/"
                + "\033[0m"
                + f"  Skipping conductivity plot: no conductivity columns found in {parameters_csv.name}"
            )
            return

        save_root.mkdir(parents=True, exist_ok=True)

        for conductivity_col in conductivity_columns:
            sd_col = f"SD_{conductivity_col}"

            values = pd.to_numeric(
                df[conductivity_col],
                errors="coerce",
            )

            valid = values.notna()
            valid &= np.isfinite(values)
            valid &= values > 0

            if "fit_success" in df.columns:
                fit_success = (
                    df["fit_success"].astype(str).str.lower().isin(["true", "1", "yes"])
                )
                valid &= fit_success

            plot_columns = ["sample", conductivity_col]

            if sd_col in df.columns:
                plot_columns.append(sd_col)

            plot_df = df.loc[valid, plot_columns].copy()

            if plot_df.empty:
                print(
                    "\n"
                    + "\033[93m"
                    + "\033[1m"
                    + ":/"
                    + "\033[0m"
                    + f"  No valid values found for {conductivity_col} in {circuit_name}"
                )
                continue

            plot_df[conductivity_col] = pd.to_numeric(
                plot_df[conductivity_col],
                errors="coerce",
            )

            if sd_col in plot_df.columns:
                plot_df[sd_col] = pd.to_numeric(
                    plot_df[sd_col],
                    errors="coerce",
                )
            else:
                plot_df[sd_col] = np.nan

            samples = plot_df["sample"].astype(str).tolist()
            conductivities = plot_df[conductivity_col].to_numpy(dtype=float)
            errors = plot_df[sd_col].to_numpy(dtype=float)

            if normalize:
                reference_value = np.nanmax(conductivities)

                if np.isfinite(reference_value) and reference_value > 0:
                    conductivities = conductivities / reference_value
                    errors = errors / reference_value
                else:
                    print(
                        "\n"
                        + "\033[93m"
                        + "\033[1m"
                        + ":/"
                        + "\033[0m"
                        + f"  Could not normalize {conductivity_col}: invalid reference value"
                    )
                    continue

            x_values = np.arange(len(samples))

            cmap = plt.get_cmap(cmap_name)
            colours = cmap(np.linspace(0.15, 0.85, len(samples)))

            fig_width = max(8, len(samples) * 0.65)
            fig, ax = plt.subplots(figsize=(fig_width, 5))

            if log_scale:
                ax.set_yscale("log")

            for xpos, conductivity, error, colour in zip(
                x_values,
                conductivities,
                errors,
                colours,
            ):
                if not np.isfinite(conductivity) or conductivity <= 0:
                    continue

                bar_kwargs = {}

                if np.isfinite(error) and error >= 0:
                    if not log_scale or conductivity - error > 0:
                        bar_kwargs["yerr"] = error
                        bar_kwargs["capsize"] = 5

                ax.bar(
                    xpos,
                    conductivity,
                    width=0.25,
                    alpha=0.9,
                    color=colour,
                    edgecolor="black",
                    linewidth=1.2,
                    **bar_kwargs,
                )

            conductivity_label = get_conductivity_label(conductivity_col)

            ax.set_xticks(x_values)
            ax.set_xticklabels(
                samples,
                rotation=label_rotation,
                ha=label_ha,
                fontsize=label_fontsize,
            )

            if normalize:
                ylabel = "Normalized " + conductivity_label + r" conductivity"
                output_prefix = "normalized_"
            else:
                ylabel = conductivity_label + r" conductivity ($\mathrm{S.cm^{-1}}$)"
                output_prefix = ""

            ax.set_ylabel(ylabel, fontsize=14)

            ax.set_title(
                rf"{experiment_name} | {circuit_name} | {conductivity_label} conductivity",
                fontsize=14,
            )

            ax.autoscale(axis="y")
            ax.margins(y=0.15)

            if y_lim is not None and len(y_lim) == 2:
                if y_lim != [None, None]:
                    ax.set_ylim(*y_lim)

            output_suffix = get_output_suffix(conductivity_col)

            figure_saver.save(
                save_path=save_root
                / f"{experiment_name}_{circuit_name}_{output_prefix}{output_suffix}_all_samples",
                fig=fig,
                axes={ax},
                dpi=dpi,
            )

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
        dpi=300,
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
            dpi=dpi,
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

        return order, colour

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
    def get_associated_alpha(param):
        """
        Return the alpha column associated with a Q or Ceff parameter.
        """

        if param.startswith("Q_"):
            return param.replace("Q_", "alpha_")

        if param.startswith("Ceff_"):
            return "alpha_" + param.replace("Ceff_", "")

        return None

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

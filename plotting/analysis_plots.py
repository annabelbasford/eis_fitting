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
        1. Plot per-sample R/Q or R/C bar charts.
           Saved in:
               experiment.paths.plots / <sample> / <circuit_name> /

        2. Plot experiment-level conductivity summaries.
           Saved in:
               experiment.paths.plots /
        """

        figure_saver = FigureSaver(experiment.save_preferences)

        for circuit_name in experiment.circuits:
            parameters_csv = (
                experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"
            )

            if not parameters_csv.exists():
                print(f"Skipping missing file: {parameters_csv}")
                continue

            df_params = self._read_parameters_csv(parameters_csv)

            resistance_columns = self.get_element_columns(
                df=df_params,
                first_chars="R",
            )

            q_columns = self.get_element_columns(
                df=df_params,
                first_chars="Q",
            )

            capacitance_columns = self.get_element_columns(
                df=df_params,
                first_chars="C",
            )

            right_columns = q_columns
            right_axis_label = r"Pseudo capacitance ($F\times s^{\alpha-1}$)"

            if not right_columns:
                right_columns = capacitance_columns
                right_axis_label = r"Capacitance ($F$)"

            for sample in self._get_successful_sample_names(df_params):
                self.plot_parameter_bars(
                    experiment=experiment,
                    df=df_params,
                    circuit_name=circuit_name,
                    sample=sample,
                    left_columns=resistance_columns,
                    right_columns=right_columns,
                    right_axis_label=right_axis_label,
                    figure_saver=figure_saver,
                )

            self.plot_conductivities_summary(
                experiment=experiment,
                df=df_params,
                parameters_csv_name=parameters_csv.name,
                circuit_name=circuit_name,
                figure_saver=figure_saver,
            )

    def plot_conductivities_summary(
        self,
        experiment,
        df,
        parameters_csv_name,
        circuit_name,
        figure_saver,
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
                + f"  Skipping conductivity plot: "
                f"no conductivity columns found in {parameters_csv_name}"
            )
            return

        save_root = experiment.paths.plots
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
            valid &= df["sample"].astype(str).str.upper() != "MEAN"

            if "fit_success" in df.columns:
                valid &= df["fit_success"].apply(self._is_truthy)

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
                    + f"  No valid values found for {conductivity_col} "
                    f"in {circuit_name}"
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
                        + f"  Could not normalize {conductivity_col}: "
                        "invalid reference value"
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

            conductivity_label = self.get_conductivity_label(conductivity_col)

            ax.set_xticks(x_values)
            ax.set_xticklabels(
                samples,
                rotation=label_rotation,
                ha=label_ha,
                fontsize=label_fontsize,
            )

            if normalize:
                ylabel = "Normalized " + conductivity_label + " conductivity"
                output_prefix = "normalized_"
            else:
                ylabel = (
                    conductivity_label
                    + r" conductivity ($\mathrm{S.cm^{-1}}$)"
                )
                output_prefix = ""

            ax.set_ylabel(ylabel, fontsize=14)

            ax.set_title(
                rf"{experiment.name} | {circuit_name} | "
                rf"{conductivity_label} conductivity",
                fontsize=14,
            )

            ax.autoscale(axis="y")
            ax.margins(y=0.15)

            self._apply_y_limits(ax, y_lim)

            output_suffix = self.get_conductivity_output_suffix(conductivity_col)

            figure_saver.save(
                save_path=save_root
                / (
                    f"{experiment.name}_{circuit_name}_"
                    f"{output_prefix}{output_suffix}_all_samples"
                ),
                fig=fig,
                axes={ax},
                dpi=experiment.save_preferences.get("dpi", 300),
            )

    def plot_parameter_bars(
        self,
        experiment,
        df,
        circuit_name,
        sample,
        left_columns,
        right_columns,
        right_axis_label,
        figure_saver,
        figure_name="R_and_Q",
    ):
        """
        Plot one R/Q or R/C bar-chart figure for one sample and one circuit.

        Settings are read from:

            experiment.plotting["R_and_Q"]
        """

        r_and_q_config = experiment.plotting.get("R_and_Q", {})

        left_ylim = r_and_q_config.get("left_ylim", None)
        right_ylim = r_and_q_config.get("right_ylim", None)

        save_folder = experiment.paths.plots / sample / circuit_name
        save_folder.mkdir(parents=True, exist_ok=True)

        df_sample = df[df["sample"].astype(str) == str(sample)]

        if df_sample.empty:
            print(f"Sample '{sample}' not found in parameter table.")
            return

        row = df_sample.iloc[0]

        mapping = self.circuits[circuit_name]["mapping"]

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
            show_alpha=True,
        )

        right_data = self._collect_axis_data(
            row=row,
            columns=df.columns,
            selected_columns=right_columns,
            display_mapping=display_mapping,
            show_alpha=True,
        )

        if not left_data and not right_data:
            print(
                "\n"
                + "\033[93m"
                + "\033[1m"
                + ":/"
                + "\033[0m"
                + f"  No plottable parameters for {sample} | {circuit_name}"
            )
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

        ax_left.set_ylabel(r"Resistance ($\Omega$)", fontsize=16)
        ax_left.set_yscale("log")

        self._apply_y_limits(ax_left, left_ylim)

        if ax_right is not None:
            ax_right.set_ylabel(right_axis_label, fontsize=16)
            ax_right.set_yscale("log")

            self._apply_y_limits(ax_right, right_ylim)

        ax_left.set_title(f"{sample} | {circuit_name}")

        axes = {ax_left}

        if ax_right is not None:
            axes.add(ax_right)

        figure_saver.save(
            save_path=save_folder / f"{sample}_{circuit_name}_{figure_name}",
            fig=fig,
            axes=axes,
            dpi=experiment.save_preferences.get("dpi", 300),
        )

    @staticmethod
    def get_conductivity_label(conductivity_col):
        """
        Convert conductivity_S_cm_R_i -> sigma_i.
        Convert conductivity_S_cm_R_bulk -> sigma_bulk.
        """

        resistance_name = conductivity_col.replace(
            "conductivity_S_cm_",
            "",
        )

        if resistance_name.startswith("R_"):
            suffix = resistance_name.replace("R_", "")
            return rf"$\sigma_{{\mathrm{{{suffix}}}}}$"

        return rf"$\sigma_{{\mathrm{{{resistance_name}}}}}$"

    @staticmethod
    def get_conductivity_output_suffix(conductivity_col):
        """
        Convert conductivity_S_cm_R_i -> Ri_conductivity.
        Convert conductivity_S_cm_R_bulk -> Rbulk_conductivity.
        """

        resistance_name = conductivity_col.replace(
            "conductivity_S_cm_",
            "",
        )

        safe_name = resistance_name.replace("_", "")

        return f"{safe_name}_conductivity"

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
            colour = self.lighten_colour(colour, factor=0.2)

        return order, colour

    @staticmethod
    def get_element_columns(df, first_chars):
        """
        Return fitted/derived parameter columns starting with first_chars.

        Excludes:
        - metadata/status columns
        - standard deviation columns
        - percent error columns
        """

        excluded = {
            "sample",
            "circuit_name",
            "circuit_string",
            "fit_success",
            "fit_status",
            "covariance_warning",
            "chi_square",
            "reduced_chi_square",
            "error",
        }

        return [
            col
            for col in df.columns
            if col.startswith(first_chars)
            and not col.startswith("SD_")
            and not col.endswith("_percent_error")
            and col not in excluded
        ]

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
    def _read_parameters_csv(parameters_csv):
        df = pd.read_csv(parameters_csv)
        return AnalysisPlotter._clean_numeric_dataframe(df)

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

    def _get_successful_sample_names(self, df):
        if "sample" not in df.columns:
            return []

        valid = df["sample"].astype(str).str.upper() != "MEAN"

        if "fit_success" in df.columns:
            valid &= df["fit_success"].apply(self._is_truthy)

        return df.loc[valid, "sample"].astype(str).tolist()

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

            alpha_label = self._get_alpha_label(
                row=row,
                param=param,
                show_alpha=show_alpha,
            )

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

    def _get_alpha_label(self, row, param, show_alpha):
        if not show_alpha:
            return None

        alpha_col = self.get_associated_alpha(param)

        if alpha_col is None or alpha_col not in row.index:
            return None

        alpha_value = self._finite_or_none(row.get(alpha_col, np.nan))

        if alpha_value is None:
            return None

        sd_alpha_col = f"SD_{alpha_col}"
        sd_alpha = None

        if sd_alpha_col in row.index:
            sd_alpha = self._finite_non_negative_or_none(
                row.get(sd_alpha_col, np.nan)
            )

        if sd_alpha is not None:
            return (
                rf"$\boldsymbol{{\alpha}}$="
                f"{alpha_value:.3f}"
                "\n"
                rf"$\boldsymbol{{\pm}}$"
                f"{sd_alpha:.3f}"
            )

        return rf"$\boldsymbol{{\alpha}}$=" f"{alpha_value:.3f}"

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

            bar_kwargs = {}

            if error is not None and np.isfinite(error) and error >= 0:
                bar_kwargs["yerr"] = error
                bar_kwargs["capsize"] = 5

            ax.bar(
                xpos,
                value,
                width=0.25,
                alpha=0.9,
                color=colour,
                edgecolor="black",
                linewidth=1.2,
                label=param,
                **bar_kwargs,
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
    def _apply_y_limits(ax, y_lim):
        if y_lim is None:
            return

        if len(y_lim) != 2:
            return

        if y_lim == [None, None]:
            return

        ax.set_ylim(*y_lim)

    @staticmethod
    def _is_truthy(value):
        if pd.isna(value):
            return False

        if isinstance(value, (bool, np.bool_)):
            return bool(value)

        if isinstance(value, (int, float, np.integer, np.floating)):
            return value == 1

        return str(value).strip().lower() in {
            "true",
            "1",
            "yes",
            "y",
            "success",
        }

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

    @staticmethod
    def lighten_colour(colour, factor=0.2):
        """
        Lighten a matplotlib-compatible colour.

        factor = 0 keeps the original colour.
        factor = 1 gives white.
        """

        import matplotlib.colors as mcolors

        rgb = np.asarray(mcolors.to_rgb(colour))
        white = np.asarray([1.0, 1.0, 1.0])

        return rgb + factor * (white - rgb)
import numpy as np
import pandas as pd

from .fit_plots import FitPlotter
from .analysis_plots import AnalysisPlotter
from ..utils import FigureSaver


class EISPlotter:
    def __init__(self, circuits: dict, plotting: dict | None = None):
        self.circuits = circuits
        self.plotting = plotting or {}

    """
    High-level plotting orchestrator.

    This class knows about the experiment structure and decides where plots
    are saved. The actual plotting is delegated to:

    - FitPlotter
    - AnalysisPlotter
    """

    def run(
        self,
        experiment,
        all_fit_data=None,
        plot_fits=True,
        plot_analysis=True,
        plot_residuals=True,
        display_chi_square=True,
    ) -> None:
        """
        Run plotting stage.

        Parameters
        ----------
        experiment
            Experiment object.

        all_fit_data : dict or None
            Fit data returned by EISFitter.run().

        plot_fits : bool
            Whether to plot Nyquist/Bode fit overlays.

        plot_analysis : bool
            Whether to plot parameter bar charts.

        plot_residuals : bool
            Whether to plot residuals.
        """

        if plot_fits and all_fit_data is not None:
            self.plot_fit_results(
                experiment=experiment,
                all_fit_data=all_fit_data,
                display_chi_square=display_chi_square,
                plot_residuals=plot_residuals,
            )

        if plot_analysis:
            self.plot_analysis_results(
                experiment=experiment,
            )

    # Plot Nyquist/Bode overlays from in-memory fit results.
    def plot_fit_results(
        self, experiment, all_fit_data, display_chi_square, plot_residuals
    ) -> None:

        if not all_fit_data:
            print("No fit data available for plotting.")
            return

        figure_saver = FigureSaver(experiment.save_preferences)

        fit_plotter = FitPlotter(
            figure_saver=figure_saver,
        )

        plot_root = experiment.paths.plots
        plot_root.mkdir(parents=True, exist_ok=True)

        for circuit_name, fit_data_dict in all_fit_data.items():
            if not fit_data_dict:
                continue

            for sample_name, data in fit_data_dict.items():
                circuit_plot_folder = plot_root / sample_name / circuit_name

                circuit_fit_parameter_file = (
                    experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"
                )

                df_params = pd.read_csv(circuit_fit_parameter_file)

                row = df_params[
                    (df_params["sample"] == sample_name)
                    & (df_params["circuit_name"] == circuit_name)
                ]

                if row.empty or not display_chi_square:
                    chi_square = None
                    reduced_chi_square = None
                else:
                    chi_square = row.iloc[0]["chi_square"]
                    reduced_chi_square = row.iloc[0]["reduced_chi_square"]

                
                circuit_plot_folder.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                fit_plotter.plot_nyquist(
                    freq=data["freq"],
                    z=data["Z"],
                    z_fit=data["Z_fit"],
                    title=f"{sample_name} | {circuit_name}",
                    save_folder=(
                        circuit_plot_folder / f"{sample_name}_{circuit_name}_nyquist"
                    ),
                    chi_square=chi_square,
                    reduced_chi_square=reduced_chi_square,
                    dpi=experiment.save_preferences.get("dpi", 300),
                )

                fit_plotter.plot_bode(
                    freq=data["freq"],
                    z=data["Z"],
                    z_fit=data["Z_fit"],
                    title=f"{sample_name} | {circuit_name}",
                    save_folder=(
                        circuit_plot_folder / f"{sample_name}_{circuit_name}_bode"
                    ),
                    chi_square=chi_square,
                    reduced_chi_square=reduced_chi_square,
                    dpi=experiment.save_preferences.get("dpi", 300),
                )

                if plot_residuals:
                    fit_plotter.plot_residuals(
                        frequencies=data["freq"],
                        Z_exp=data["Z"],
                        Z_fit=data["Z_fit"],
                        sample=sample_name,
                        circuit_name=circuit_name,
                        save_folder=(
                            circuit_plot_folder
                            / f"{sample_name}_{circuit_name}_residuals"
                        ),
                        chi_square=chi_square,
                        reduced_chi_square=reduced_chi_square,
                        dpi=experiment.save_preferences.get("dpi", 300),
                    )

        self.plot_all_runs(
            experiment=experiment,
            all_fit_data=all_fit_data,
            fit_plotter=fit_plotter,
        )

    # Plot combined all-sample Bode and Nyquist plots for each circuit.

    def plot_all_runs(
        self,
        experiment,
        all_fit_data,
        fit_plotter,
    ) -> None:

        all_runs_folder = experiment.paths.plots / "all_runs"

        for circuit_name, fit_data_dict in all_fit_data.items():
            if len(fit_data_dict) <= 1:
                continue

            fit_plotter.plot_all_files_for_circuit(
                fit_data_dict=fit_data_dict,
                circuit_name=circuit_name,
                save_folder=all_runs_folder,
                dpi=experiment.save_preferences.get("dpi", 300),
            )

    def plot_analysis_results(self, experiment) -> None:
        analysis_plotter = AnalysisPlotter(
            circuits=self.circuits,
            plotting=self.plotting,
        )

        analysis_plotter.run(
            experiment=experiment,
        )

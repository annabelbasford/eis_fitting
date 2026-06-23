import pandas as pd

from eis_fitting.plotting.fit_plots import FitPlotter
from eis_fitting.plotting.analysis_plots import AnalysisPlotter
from eis_fitting.utils.figures import FigureSaver


class EISPlotter:
    def __init__(self, circuits: dict, plotting_limits: dict | None = None):
        self.circuits = circuits
        self.plotting_limits = plotting_limits or {}

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
        """

        if plot_fits and all_fit_data is not None:
            self.plot_fit_results(
                experiment=experiment,
                all_fit_data=all_fit_data,
                display_chi_square=display_chi_square
            )

        if plot_analysis:
            self.plot_analysis_results(
                experiment=experiment,
            )

    def plot_fit_results(self, experiment, all_fit_data, display_chi_square) -> None:
        """
        Plot Nyquist/Bode overlays from in-memory fit results.
        """

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
                    save_path=(
                        circuit_plot_folder / f"{sample_name}_{circuit_name}_nyquist"
                    ),
                    chi_square=chi_square,
                    reduced_chi_square=reduced_chi_square,
                )

                fit_plotter.plot_bode(
                    freq=data["freq"],
                    z=data["Z"],
                    z_fit=data["Z_fit"],
                    title=f"{sample_name} | {circuit_name}",
                    save_path=(
                        circuit_plot_folder / f"{sample_name}_{circuit_name}_bode"
                    ),
                    chi_square=chi_square,
                    reduced_chi_square=reduced_chi_square,
                )

        self.plot_all_runs(
            experiment=experiment,
            all_fit_data=all_fit_data,
            fit_plotter=fit_plotter,
        )

    def plot_all_runs(
        self,
        experiment,
        all_fit_data,
        fit_plotter,
    ) -> None:
        """
        Plot combined all-sample Bode and Nyquist plots for each circuit.
        """

        all_runs_folder = experiment.paths.plots / "all_runs"

        for circuit_name, fit_data_dict in all_fit_data.items():
            if len(fit_data_dict) <= 1:
                continue

            fit_plotter.plot_all_files_for_circuit(
                fit_data_dict=fit_data_dict,
                circuit_name=circuit_name,
                save_folder=all_runs_folder,
            )

    def plot_analysis_results(self, experiment) -> None:
        analysis_plotter = AnalysisPlotter(
            circuits=self.circuits,
            plotting_limits=self.plotting_limits,
        )

        analysis_plotter.run(
            experiment=experiment,
        )

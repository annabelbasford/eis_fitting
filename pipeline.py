from pathlib import Path

from eis_fitting.config.loader import ConfigLoader
from eis_fitting.core.experiment import Experiment
from eis_fitting.preprocessing.preprocessor import EISPreprocessor
from eis_fitting.fitting.fitter import EISFitter
from eis_fitting.analysis.analyser import EISAnalyser
from eis_fitting.plotting.plotter import EISPlotter

from tqdm import tqdm


class EISPipeline:
    def __init__(
        self,
        data_root: Path,
        circuits: dict,
        output_mode: str = "local",
        output_root: Path | None = None,
    ):
        self.data_root = Path(data_root)
        self.circuits = circuits

        self.output_mode = output_mode
        self.output_root = Path(output_root) if output_root is not None else None

        self.config_loader = ConfigLoader(self.data_root)

    def load_experiment(self, experiment_path: Path) -> Experiment:
        config = self.config_loader.load_experiment_config(experiment_path)

        return Experiment(
            path=experiment_path,
            config=config,
            data_root=self.data_root,
            output_mode=self.output_mode,
            output_root=self.output_root,
        )

    def run_experiment(self, experiment_path: Path, full_terminal=True) -> None:
        experiment = self.load_experiment(experiment_path)

        if full_terminal :
            print(f"\n=== Running experiment: {experiment.name} ===")
            print(f"Description: {experiment.description}")
            print(f"Input folder: {experiment.paths.input}")
            print(f"Processed output: {experiment.paths.processed_root}")

        # Preprocesses the data if it doesn't already have a processed folder
        # or if preplot was required. In which case, no fitting nor analysis will happen afterwards
        if not experiment.paths.processed_root.is_dir() or experiment.run.get(
            "pre_plot", True
        ):
            EISPreprocessor().run(experiment)

        # only proceeds if no pre_plotting was required and "fits" folder hasn't been created yet
        if (
            not experiment.run.get("pre_plot", False)
            and not experiment.paths.fits.is_dir()
        ):
            # note that the Bode and Nyquist plotting in EISFitter does
            # check the experiment.run.get("plot") during it's execution
            all_fit_data = EISFitter(self.circuits).run(experiment, full_terminal)

            EISAnalyser(self.circuits).run(experiment)

            if experiment.run.get("plot", True):
                plotting_limits = {
                    "R_and_Q": {
                        "left_ylim": (1e-1, 1e15),
                        "right_ylim": (1e-12, 1e-2),
                    },
                    "conductivities": {
                        "left_ylim": (1e-10, 1e-4),
                        "right_ylim": None,
                    },
                }

                EISPlotter(
                    self.circuits,
                    plotting_limits=plotting_limits,
                ).run(
                    experiment=experiment,
                    all_fit_data=all_fit_data,
                    plot_fits=all_fit_data is not None,
                    plot_analysis=True,
                    display_chi_square=True
                )

    def run_project(self, person: str, project: str, full_terminal = True) -> None:
        project_path = self.data_root / person / project

        if not project_path.exists():
            raise FileNotFoundError(f"Project folder not found: {project_path}")

        for experiment_path in tqdm(sorted(project_path.iterdir()), unit="sample"):
            if not experiment_path.is_dir():
                continue

            if not (experiment_path / "metadata.json").exists():
                continue

            self.run_experiment(experiment_path, full_terminal)

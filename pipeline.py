from pathlib import Path

from .config import ConfigLoader
from .core import Experiment
from .preprocessing import EISPreprocessor
from .fitting import EISFitter
from .analysis import EISAnalyser
from .plotting import EISPlotter, PreprocessPlotter

from tqdm import tqdm


class EISPipeline:
    def __init__(
        self,
        global_config: dict,
        circuits: dict,
    ):
        self.global_config = global_config
        self.circuits = circuits

        paths_config = self.global_config["paths"]

        self.data_path = Path(paths_config["data_path"])
        self.person = paths_config["user"]
        self.project = paths_config["project"]

        self.output_mode = paths_config.get("output_mode", "workspace")

        output_path = paths_config.get("output_path")
        self.output_root = Path(output_path) if output_path is not None else None

        self.full_terminal = self.global_config.get("full_terminal", True)

        self.config_loader = ConfigLoader(self.global_config)

    def load_experiment(self, experiment_path: Path) -> Experiment:
        config = self.config_loader.load_experiment_config(experiment_path)

        return Experiment(
            path=experiment_path,
            config=config,
            data_path=self.data_path,
            output_mode=self.output_mode,
            output_root=self.output_root,
        )

    def run_experiment(self, experiment_path: Path) -> None:
        experiment = self.load_experiment(experiment_path)

        run_parameters = experiment.run
        validation_parameters = experiment.validation

        if self.full_terminal:
            print(
                "\033[1m"
                + f"\n\n# ----- Running experiment: {experiment.name} ----- #\n"
                + "\033[0m"
            )
            print(
                "\x1b[4m" + "Description" + "\x1b[24m" + f": {experiment.description}"
            )
            print(
                "\nInput folder: " + "\x1b[3m" + str(experiment.paths.input) + "\x1b[0m"
            )
            print(
                f"Processed output: "
                + "\x1b[3m"
                + str(experiment.paths.processed_root)
                + "\x1b[0m"
            )

        # --------------- Preprocessing --------------- #

        # If the experiment has never been processed, preprocess it.
        if not experiment.paths.processed_root.is_dir():
            print("\nPreprocessing the raw data")
            EISPreprocessor().run(experiment)

        # --------------- Pre-plot / manual-cleaning mode --------------- #

        if run_parameters.get("pre_plot", False) and not experiment.paths.fits.is_dir():
            PreprocessPlotter().plot_folder(
                input_folder=experiment.paths.csv,
                output_folder=experiment.paths.pre_plots,
            )

            if self.full_terminal:
                print("\nPre-plot mode enabled")
                print("Stopping before fitting so clean CSVs can be edited by hand\n")

            # to stop execution before fitting and allow for manual preprocessing
            return

        # --------------- Fitting --------------- #

        all_fit_data = None

        if run_parameters.get("fit", True):

            if not experiment.paths.fits.is_dir():

                all_fit_data = EISFitter(self.circuits).run(
                    experiment,
                )

            else:
                if self.full_terminal:
                    print("Fits folder already exists. Skipping fitting.")
                all_fit_data = EISFitter(self.circuits).load_fit_data(
                    experiment=experiment,
                    validation_parameters=experiment.validation,
                )

                if not all_fit_data:
                    if self.full_terminal:
                        print("No existing fit data found. Running fitting instead.")

                    all_fit_data = EISFitter(self.circuits).run(
                        experiment,
                        full_terminal=self.full_terminal,
                    )

        # --------------- Analysis and plotting --------------- #

        # Analysis can be run from newly generated fits or existing fit CSVs.
        if experiment.paths.fits.is_dir():

            EISAnalyser(self.circuits).run(experiment)

            # --------------- Plotting --------------- #
            if run_parameters.get("plot", True) and not experiment.paths.plots.is_dir():

                EISPlotter(
                    self.circuits,
                    plotting=experiment.plotting,
                ).run(
                    experiment=experiment,
                    all_fit_data=all_fit_data,
                    plot_fits=all_fit_data is not None,
                    plot_analysis=True,
                    plot_residuals=validation_parameters.get("plot_residuals", True),
                    display_chi_square=validation_parameters.get(
                        "display_chi_square", True
                    ),
                )

        else:
            print("No fits folder found. Skipping analysis and plotting.")

    def run_project(self) -> None:
        project_path = self.data_path / self.person / self.project

        if not project_path.exists():
            raise FileNotFoundError(f"Project folder not found: {project_path}")

        for experiment_path in tqdm(
            sorted(project_path.iterdir()),
            unit="experiment",
        ):
            if not experiment_path.is_dir():
                continue

            if not (experiment_path / "metadata.json").exists():
                continue

            self.run_experiment(experiment_path)

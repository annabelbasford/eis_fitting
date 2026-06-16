from pathlib import Path

from eis_fitting.config.loader import ConfigLoader
from eis_fitting.core.experiment import Experiment
from eis_fitting.preprocessing.preprocessor import EISPreprocessor
from eis_fitting.fitting.fitter import EISFitter
from eis_fitting.analysis.analyser import EISAnalyser
from eis_fitting.plotting.plotter import AnalysisPlotter


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

    def run_experiment(self, experiment_path: Path) -> None:
        experiment = self.load_experiment(experiment_path)

        print(f"\n=== Running experiment: {experiment.name} ===")
        print(f"Description: {experiment.description}")
        print(f"Input folder: {experiment.paths.input}")
        print(f"Processed output: {experiment.paths.processed_root}")

        if experiment.run.get("preprocess", True):
            EISPreprocessor().run(experiment)

        if experiment.run.get("fit", True):
            EISFitter(self.circuits).run(experiment)

        if experiment.run.get("analyse", True):
            EISAnalyser(self.circuits).run(experiment)

        if experiment.run.get("plot", True):
            AnalysisPlotter(self.circuits).run(experiment)

    def run_project(self, person: str, project: str) -> None:
        project_path = self.data_root / person / project

        if not project_path.exists():
            raise FileNotFoundError(f"Project folder not found: {project_path}")

        for experiment_path in sorted(project_path.iterdir()):
            if not experiment_path.is_dir():
                continue

            if not (experiment_path / "metadata.json").exists():
                continue

            self.run_experiment(experiment_path)
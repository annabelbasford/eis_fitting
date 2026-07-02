from pathlib import Path

class ExperimentPaths:
    def __init__(
        self,
        experiment_path: Path,
        data_path: Path,
        output_mode: str = "local",
        output_root: Path | None = None,
    ):
        self.root = Path(experiment_path)

        # looks redundant but this way we can change how we handle the input more easily later
        # were we to change the data structure
        self.input = self.root

        self.data_path = Path(data_path)

        self.metadata = self.root / "metadata.json"

        if output_mode == "local":
            self.processed_root = self.root / "processed"

        elif output_mode == "workspace":
            if output_root is None:
                raise ValueError("output_root must be provided when output_mode='workspace'.")

            relative_experiment_path = self.root.relative_to(self.data_path)
            self.processed_root = Path(output_root) / relative_experiment_path

        else:
            raise ValueError("output_mode must be either 'local' or 'workspace'.")

        # Keep old processed structure:
        # processed/
        # ├── csv/
        # └── fits/
        #     └── plots/
        self.csv = self.processed_root / "csv"
        self.fits = self.processed_root / "fits"
        self.plots = self.fits / "plots"

        # Optional preprocessing plots, only used if pre_plot=True.
        self.pre_plots = self.processed_root / "pre_plots"

class Experiment:
    def __init__(
        self,
        path,
        config,
        data_path,
        output_mode="workspace",
        output_root=None,
    ):
        self.paths = ExperimentPaths(
            experiment_path=path,
            data_path=data_path,
            output_mode=output_mode,
            output_root=output_root,
        )
        
        self.path = path
        self.config = config
        self.data_path = data_path

        self.name = path.name
        self.description = config.get("description", "")

        self.method = config["method"]
        self.circuits = config["circuits"]

        self.geometry = config["geometry"]
        self.run = config["run"]
        self.plotting_limits = config.get("plotting_limits", {})
        self.save_preferences = config["save_preferences"]
from pathlib import Path


class ExperimentPaths:
    def __init__(
        self,
        experiment_root: Path,
        data_root: Path,
        output_mode: str = "local",
        output_root: Path | None = None,
    ):
        self.root = Path(experiment_root)

        # looks redundant but this way we can change how we handle the input more easily later
        # were we to change the data structure
        self.input = self.root

        self.data_root = Path(data_root)

        self.metadata = self.root / "metadata.json"

        if output_mode == "local":
            self.processed_root = self.root / "processed"

        elif output_mode == "workspace":
            if output_root is None:
                raise ValueError("output_root must be provided when output_mode='workspace'.")

            relative_experiment_path = self.root.relative_to(self.data_root)
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

    def create_output_folders(self) -> None:
        self.csv.mkdir(parents=True, exist_ok=True)
        self.fits.mkdir(parents=True, exist_ok=True)
        self.plots.mkdir(parents=True, exist_ok=True)


class Experiment:
    def __init__(
        self,
        path: Path,
        config: dict,
        data_root: Path,
        output_mode: str = "local",
        output_root: Path | None = None,
    ):
        self.paths = ExperimentPaths(
            experiment_root=path,
            data_root=data_root,
            output_mode=output_mode,
            output_root=output_root,
        )
        self.config = config

    @property
    def name(self) -> str:
        return self.paths.root.name

    @property
    def description(self) -> str:
        return self.config.get("description", "")

    @property
    def geometry(self) -> dict:
        return self.config["geometry"]

    @property
    def processing(self) -> dict:
        return self.config.get("processing", {})

    @property
    def run(self) -> dict:
        return self.config.get("run", {})

    @property
    def save_preferences(self) -> dict:
        return self.config.get(
            "save_preferences",
            {
                "transparent": False,
                "png": True,
                "svg": False,
            },
        )

    @property
    def circuits(self) -> list[str]:
        return self.config.get("circuits", [])
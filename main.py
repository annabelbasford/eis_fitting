from pathlib import Path

from eis_fitting.circuits import CIRCUITS
from eis_fitting.pipeline import EISPipeline


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

PERSON = "Annabel"
PROJECT = "eis_flex"

# Choose one:
# OUTPUT_MODE = "local"
# OUTPUT_ROOT = None

# Or use external workspace:
OUTPUT_MODE = "workspace"
OUTPUT_ROOT = PROJECT_ROOT / "data_processed"


def main():
    pipeline = EISPipeline(
        data_root=DATA_ROOT,
        circuits=CIRCUITS,
        output_mode=OUTPUT_MODE,
        output_root=OUTPUT_ROOT,
    )

    pipeline.run_project(
        person=PERSON,
        project=PROJECT,
    )


if __name__ == "__main__":
    main()
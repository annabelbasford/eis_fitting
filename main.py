from pathlib import Path

from eis_fitting.circuits import CIRCUITS
from eis_fitting.pipeline import EISPipeline

# adapt the number of .parent calls to your architecture
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

# pipeline.run_project will take these as arguments to formate input directory path data_root / person / project
PERSON = "laura"
PROJECT = "eis_fitting"

"""
Two output modes are available :
   - local : the processed data is saved along the raw data
   - workspace (recommended) : processed data is stored in a distinct folder
"""

# uncomment the following lines if you want to save in local mode
# OUTPUT_MODE = "local"
# OUTPUT_ROOT = None

# comment the following lines if you want to save in local mode
OUTPUT_MODE = "workspace"
OUTPUT_ROOT = PROJECT_ROOT / "data_processed"


def main():
    pipeline = EISPipeline(
        data_root=DATA_ROOT,
        circuits=CIRCUITS,
        output_mode=OUTPUT_MODE,
        output_root=OUTPUT_ROOT,
    )

    pipeline.run_project(person=PERSON, project=PROJECT, full_terminal=True)


if __name__ == "__main__":
    main()

from pathlib import Path

from eis_fitting import CIRCUITS, EISPipeline
from .config import ConfigLoader


PROJECT_ROOT = Path(__file__).resolve().parent
GLOBAL_CONFIG_PATH = PROJECT_ROOT / "global.json"


def main():
    global_config = ConfigLoader.load_global_config(GLOBAL_CONFIG_PATH)

    pipeline = EISPipeline(
        global_config=global_config,
        circuits=CIRCUITS,
    )

    pipeline.run_project()


if __name__ == "__main__":
    main()
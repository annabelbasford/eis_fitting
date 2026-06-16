from pathlib import Path
from scripts.eis_preprocess import *
from scripts.eis_fitting import *
from scripts.eis_analysis import eis_analysis
import json
import shutil

# Convention : paths in caps

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA = PROJECT_ROOT / "data"
PROCESSED = PROJECT_ROOT / "projects/eis_fitting/processed"

PROCESSED.mkdir(exist_ok=True)

s_data = {el.name for el in DATA.iterdir() if el.is_dir()}
s_processed = {el.name for el in PROCESSED.iterdir() if el.is_dir()}

# Dictionary of circuits that the fitting process will try based on metadata
CIRCUITS = {
    "circuit_1": {
        "string": "p(R_1-CPE_1,R_2)",
        "guess": [
            100,
            1e-6,
            0.9,
            1000,
        ],
        "mapping": {
            "R_1": {
                "name": "R_i",
                "colour": "#80D4F8",
                "order": 0,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
                "order": 1,
            },
            "CPE_1_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_1_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
        },
    },
    "circuit_2": {
        "string": "R_1-p(R_3-CPE_1,CPE_2,R_2)",
        "guess": [
            20,
            750,
            1e-5,
            0.9,
            1e-4,
            0.7,
            200,
        ],
        "mapping": {
            "R_1": {
                "name": "R_c",
                "colour": "#69BC86",
                "order": 2,
            },
            "R_3": {
                "name": "R_i",
                "colour": "#80D4F8",
                "order": 0,
            },
            "R_2": {
                "name": "R_e",
                "colour": "#F37F8C",
                "order": 1,
            },
            "CPE_1_0": {
                "name": "Q_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_2_0": {
                "name": "Q_g",
                "colour": "#F49A80",
                "order": 1,
            },
            "CPE_1_1": {
                "name": "alpha_DL",
                "colour": "#7C84C2",
                "order": 0,
            },
            "CPE_2_1": {
                "name": "alpha_g",
                "colour": "#F49A80",
                "order": 1,
            },
        },
    },
}

# data folders that shouldn't be processed
exceptFolders_preprocess = {"mpr", "femke", "testFemke", "juan"}

for dir_name in s_data:

    if dir_name in exceptFolders_preprocess:
        continue

    # ------- Path handling ------- #
    PROCESSED_DATASET_FOLDER = PROCESSED / dir_name
    CLEAN_CSV_FOLDER = PROCESSED_DATASET_FOLDER / "csv"
    DATASET = DATA / dir_name
    FITS_FOLDER = PROCESSED_DATASET_FOLDER / "fits"
    PRE_PLOT_FOLDER = PROCESSED_DATASET_FOLDER / "pre_plots"

    # ------- Metadata handling ------- #
    with open(DATASET / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    run = metadata.get("run", {})

    pre_plot = run.get("pre_plot", False)
    plot = run.get("plot", True)

    thickness_cm = metadata["thickness_cm"]
    sd_thickness_cm = metadata["SD_thickness_cm"]
    area_cm2 = metadata["area_cm2"]
    sd_area_cm2 = metadata["SD_area_cm2"]
    save_preferences = metadata["save_preferences"]
    sigma_omega = metadata["sigma_f"] * 2 * np.pi
    circuits_to_try = metadata["circuits"]

    circuits_for_dataset = {
        key: value for key, value in CIRCUITS.items() if key in circuits_to_try
    }

    # ------- Data pre-processing ------- #
    if dir_name not in s_processed or pre_plot:

        print(f"Processing {dir_name} dataset")

        PROCESSED_DATASET_FOLDER.mkdir(exist_ok=True)

        if PRE_PLOT_FOLDER.exists():
            shutil.rmtree(PRE_PLOT_FOLDER)
        else:
            eis_metrohm_data_clean(DATASET, CLEAN_CSV_FOLDER)
            eis_mpr_data_conversion(DATASET, CLEAN_CSV_FOLDER)
            split_non_monotonic_frequency_csv(CLEAN_CSV_FOLDER)

        if pre_plot:
            eis_preprocess_plot(CLEAN_CSV_FOLDER, PRE_PLOT_FOLDER)
            continue

        print("Data processed")

    # ------- Fitting ------- #
    if not FITS_FOLDER.exists():

        if PRE_PLOT_FOLDER.exists():
            shutil.rmtree(PRE_PLOT_FOLDER)

        eis_fitting(
            CLEAN_CSV_FOLDER,
            FITS_FOLDER,
            circuits_for_dataset,
            save_preferences,
            plot=plot,
        )

        print("Data fitted")

        # ------- Analysis ------- #
        eis_analysis(
            PROCESSED_DATASET_FOLDER,
            circuits_for_dataset,
            thickness_cm,
            sd_thickness_cm,
            area_cm2,
            sd_area_cm2,
            sigma_omega,
            save_preferences,
            plot,
        )

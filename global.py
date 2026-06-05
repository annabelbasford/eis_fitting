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

# Dictionary of circuits that the fitting process will try
CIRCUITS = {
    "circuit_1": {
        "string": "p(R_1-CPE_1,R_2)",
        "guess": [100, 1e-6, 0.9, 1000],
    },
    "circuit_2": {
        "string": "R_1-p(R_3-CPE_1,CPE_2,R_2)",
        "guess": [20, 750, 1e-5, 0.9, 1e-4, 0.7, 200],
    },
    "circuit_3": {
        "string": "R_1-p(R_2-CPE_1,CPE_2)",
        "guess": [20, 500, 1e-4, 0.5, 1e-5, 0.9],
    },

}

# data folders that shouldn't be processed
exceptFolders_preprocess = {"femke", "juan","testJuan", "mpr"}

for dir_name in s_data:

    if (dir_name not in s_processed) and (dir_name not in exceptFolders_preprocess):
        print("Processing %s dataset" % dir_name)

        PROCESSED_DATASET_FOLDER = PROCESSED / dir_name
        CLEAN_CSV_FOLDER = PROCESSED_DATASET_FOLDER / "csv/"
        DATASET = DATA / dir_name

        # creates a directory for the processed data of this set
        PROCESSED_DATASET_FOLDER.mkdir(exist_ok=True)

        # ------- Metadata handling ------- #
        with open(DATASET / "metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)

        thickness_cm = metadata["thickness_cm"]
        sd_thickness_cm = metadata["SD_thickness_cm"]
        area_cm2 = metadata["area_cm2"]
        sd_area_cm2 = metadata["SD_area_cm2"]
        save_to_png = metadata["png"]
        save_to_svg = metadata["svg"]
        sigma_omega = metadata["sigma_f"] * 2 * np.pi

        # ------- Data pre-processing ------- #
        eis_metrohm_data_clean(DATASET, CLEAN_CSV_FOLDER)
        eis_mpr_data_conversion(DATASET, CLEAN_CSV_FOLDER)
        split_non_monotonic_frequency_csv(CLEAN_CSV_FOLDER)
        print("Data processed")

        # ------- Fitting ------- #
        FITS_FOLDER = PROCESSED_DATASET_FOLDER / "fits"
        eis_fitting(CLEAN_CSV_FOLDER, FITS_FOLDER, CIRCUITS, save_to_png, save_to_svg)
        print("Data fitted")

        # ------- Analysis ------- #

        eis_analysis(
            FITS_FOLDER,
            CIRCUITS,
            thickness_cm,
            sd_thickness_cm,
            area_cm2,
            sd_area_cm2,
            sigma_omega,
            save_to_png,
            save_to_svg,
        )


# If manual data managment had to be done by hand, reruns the fitting and analysing

re_fit_analyse_experiments = {'testFemke'}

for dir_name in s_data:

    if dir_name in re_fit_analyse_experiments:
        print("Re_fitting %s dataset" % dir_name)

        PROCESSED_DATASET_FOLDER = PROCESSED / dir_name
        CLEAN_CSV_FOLDER = PROCESSED_DATASET_FOLDER / "csv/"
        DATASET = DATA / dir_name

        # ------- Metadata handling ------- #
        with open(DATASET / "metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)

        thickness_cm = metadata["thickness_cm"]
        sd_thickness_cm = metadata["SD_thickness_cm"]
        area_cm2 = metadata["area_cm2"]
        sd_area_cm2 = metadata["SD_area_cm2"]
        save_to_png = metadata["png"]
        save_to_svg = metadata["svg"]
        sigma_omega = metadata["sigma_f"] * 2 * np.pi

        # ------- Fitting ------- #
        FITS_FOLDER = PROCESSED_DATASET_FOLDER / "new_fits"
        # if that's not the first re-run on this folder
        if FITS_FOLDER.exists():
            # Delete existing /fits folder if present
            shutil.rmtree(PROCESSED_DATASET_FOLDER / "fits")

            # Rename new_fits -> fits
            FITS_FOLDER.rename(PROCESSED_DATASET_FOLDER / "fits")

        eis_fitting(CLEAN_CSV_FOLDER, FITS_FOLDER, CIRCUITS, save_to_png, save_to_svg)
        print("Data fitted")

        # ------- Analysis ------- #

        eis_analysis(
            FITS_FOLDER,
            CIRCUITS,
            thickness_cm,
            sd_thickness_cm,
            area_cm2,
            sd_area_cm2,
            sigma_omega,
            save_to_png,
            save_to_svg,
        )





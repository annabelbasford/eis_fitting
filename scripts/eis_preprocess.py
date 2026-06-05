from pathlib import Path
from os import unlink
import csv
import sys
import re
import pandas as pd
import numpy as np
import glob
from galvani import BioLogic

from tqdm import tqdm

# ----------------------- metrhom data cleaning ----------------------- #

def eis_metrohm_data_clean(input_folder, output_folder):
    # input_folder and output_folder are meant to be pathlib PATH classes
    output_folder.mkdir(exist_ok=True)

    #glob.glob() expects a json string, hence the str()
    input_files = glob.glob(str(input_folder / "*.csv"))


    SECTION_MAP = {
        "bodephase": "bode",
        "bodezmod": "bodeZmod",
        "nyquist": "nyquist",
    }


    def detect_section(line: str):
        lower = line.lower().strip()
        for key, out_name in SECTION_MAP.items():
            if lower.endswith(f"#{key}"):
                return out_name
        return None


    def clean_column_name(col: str) -> str:
        col = col.replace('"', "").strip()

        mapping = {
            "Freq (Hz)": "freq/Hz",
            "Freq(Hz)": "freq/Hz",
            "-Phase (deg)": "Phase(Z)/deg",
            "Phase (deg)": "Phase(Z)/deg",
            "|Z| (Ohm)": "|Z|/Ohm",
            "|Z|(Ohm)": "|Z|/Ohm",
            "Z' (Ohm)": "Re(Z)/Ohm",
            "Z'(Ohm)": "Re(Z)/Ohm",
            "-Z'' (Ohm)": "-Im(Z)/Ohm",
            "-Z''(Ohm)": "-Im(Z)/Ohm",
        }

        return mapping.get(col, col)


    def clean_numeric_value(value: str):
        value = value.replace('"', "").strip()
        if value == "":
            return None
        return float(value)


    def split_eis_file(input_file: str, output_dir: str | None = None):
        input_path = Path(input_file)

        if output_dir is None:
            output_path = input_path.parent
        else:
            output_path = Path(output_dir)

        output_path.mkdir(parents=True, exist_ok=True)

        datasets = {
            "bode": [],
            "bodeZmod": [],
            "nyquist": [],
        }

        current_section = None
        header_found = False

        with open(input_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.replace('"', "").strip()

                if not line:
                    continue

                new_section = detect_section(line)
                if new_section is not None:
                    current_section = new_section
                    header_found = False
                    continue

                if current_section is None:
                    continue

                row = [item.strip() for item in line.split(";")]

                if not header_found:
                    cleaned_header = [clean_column_name(c) for c in row]
                    datasets[current_section].append(cleaned_header)
                    header_found = True
                else:
                    cleaned_row = [clean_numeric_value(x) for x in row]
                    datasets[current_section].append(cleaned_row)

        # Convert each section into a dataframe
        dfs = {}

        for section_name, rows in datasets.items():
            if not rows:
                print(f"Warning: no data found for section '{section_name}'")
                continue

            header = rows[0]
            data = rows[1:]

            df = pd.DataFrame(data, columns=header)

            # Remove duplicate columns if needed
            df = df.loc[:, ~df.columns.duplicated()]

            dfs[section_name] = df

        # Merge everything into one CSV using freq/Hz
        combined_df = dfs["bode"]

        if "bodeZmod" in dfs:
            combined_df = combined_df.merge(
                dfs["bodeZmod"],
                on="freq/Hz",
                how="outer"
            )

        if "nyquist" in dfs:
            combined_df = combined_df.merge(
                dfs["nyquist"],
                on="freq/Hz",
                how="outer"
            )

        # Optional: reorder columns
        preferred_order = [
            "freq/Hz",
            "Phase(Z)/deg",
            "|Z|/Ohm",
            "Re(Z)/Ohm",
            "-Im(Z)/Ohm",
        ]

        existing_cols = [col for col in preferred_order if col in combined_df.columns]
        other_cols = [col for col in combined_df.columns if col not in existing_cols]

        combined_df = combined_df[existing_cols + other_cols]

        out_file = output_path / f"{input_path.stem}.csv"
        combined_df.to_csv(out_file, index=False)

        return [out_file]
        
    for input_file in input_files:
        files = split_eis_file(input_file, output_folder)

# ----------------------- mpr data conversion ----------------------- #

def eis_mpr_data_conversion(input_folder, output_folder):
    # input_path and output_path are meant to be pathlib PATH classes
    for mpr_path in input_folder.glob("*.mpr"):
        mpr = BioLogic.MPRfile(str(mpr_path))
        df = pd.DataFrame(mpr.data)

        csv_path = output_folder / f"{mpr_path.stem}.csv"
        df.to_csv(csv_path, index=False)

# ----------------------- csv file splitting ----------------------- #

"""
This function's purpose it to make sure to only fit monotonous sequences of 
frequencies : the function thus looks for any change of monotony, and if there is 
one it splits the file as many times as needed
"""

def split_non_monotonic_frequency_csv(input_folder):
    # input_folder and output_folder are meant to be pathlib PATH classes

    for input_file in input_folder.iterdir():

        df = pd.read_csv(input_file)

        if "freq/Hz" not in df.columns:
            raise ValueError("Column 'freq/Hz' not found.")

        freq = df["freq/Hz"].to_numpy()

        # Determine initial trend
        trend = None
        segments = []
        start_idx = 0

        i = 1

        for i in range(1, len(freq)):

            diff = freq[i] - freq[i - 1]

            current_trend = 1 if diff > 0 else -1

            if trend is None:
                trend = current_trend
                continue

            # Monotonicity break detected
            if current_trend != trend:
        
                segments.append(df.iloc[start_idx:i].copy())

                start_idx = i             

        # makes sure that if there was no splitting necessary 
        # the name of the file remains unchanged
        if start_idx == 0:
            continue

        # Add final segment
        segments.append(df.iloc[start_idx:].copy())

        stem = input_file.stem
        suffix = input_file.suffix
        parent = input_file.parent

        for idx, segment_df in enumerate(segments, start=1):

            output_path = parent / f"{stem}_{idx}{suffix}"

            segment_df.to_csv(output_path, index=False)

        # gets rid of the original file
        input_file.unlink()
        

    
  
    
    
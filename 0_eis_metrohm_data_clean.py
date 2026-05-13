from pathlib import Path
import csv
import sys
import re
import pandas as pd
import glob

input_folder = Path("/home/abasford/projects/eis_fitting/metrohm")
output_folder = Path("/home/abasford/projects/eis_fitting/csv/")
output_folder.mkdir(exist_ok=True)

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

    out_file = output_path / f"{input_path.stem}_clean.csv"
    combined_df.to_csv(out_file, index=False)

    return [out_file]


if __name__ == "__main__":
    for input_file in input_files:
        files = split_eis_file(input_file, output_folder)

    print("Created files:")
    for file in files:
        print(f" - {file}")
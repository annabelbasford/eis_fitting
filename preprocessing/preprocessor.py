from pathlib import Path

import glob
import matplotlib.pyplot as plt
import pandas as pd
import shutil

from eis_fitting.io.readers import BioLogicConverter

class MetrohmCSVCleaner:
    SECTION_MAP = {
        "bodephase": "bode",
        "bodezmod": "bodeZmod",
        "nyquist": "nyquist",
    }

    COLUMN_MAPPING = {
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

    def clean_folder(self, input_folder: Path, output_folder: Path) -> None:
        output_folder.mkdir(parents=True, exist_ok=True)

        input_files = glob.glob(str(input_folder / "*.csv"))

        for input_file in input_files:
            self.clean_file(Path(input_file), output_folder)

    def clean_file(self, input_file: Path, output_folder: Path) -> Path:
        datasets = {
            "bode": [],
            "bodeZmod": [],
            "nyquist": [],
        }

        current_section = None
        header_found = False

        with open(input_file, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.replace('"', "").strip()

                if not line:
                    continue

                new_section = self._detect_section(line)

                if new_section is not None:
                    current_section = new_section
                    header_found = False
                    continue

                if current_section is None:
                    continue

                row = [item.strip() for item in line.split(";")]

                if not header_found:
                    datasets[current_section].append(
                        [self._clean_column_name(c) for c in row]
                    )
                    header_found = True
                else:
                    datasets[current_section].append(
                        [self._clean_numeric_value(x) for x in row]
                    )

        dfs = {}

        for section_name, rows in datasets.items():
            if not rows:
                print(f"Warning: no data found for section '{section_name}'")
                continue

            header = rows[0]
            data = rows[1:]

            df = pd.DataFrame(data, columns=header)
            df = df.loc[:, ~df.columns.duplicated()]
            dfs[section_name] = df

        if "bode" not in dfs:
            raise ValueError(f"No bode section found in {input_file}")

        combined_df = dfs["bode"]

        if "bodeZmod" in dfs:
            combined_df = combined_df.merge(
                dfs["bodeZmod"],
                on="freq/Hz",
                how="outer",
            )

        if "nyquist" in dfs:
            combined_df = combined_df.merge(
                dfs["nyquist"],
                on="freq/Hz",
                how="outer",
            )

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

        out_file = output_folder / f"{input_file.stem}.csv"
        combined_df.to_csv(out_file, index=False)

        return out_file

    def _detect_section(self, line: str):
        lower = line.lower().strip()

        for key, out_name in self.SECTION_MAP.items():
            if lower.endswith(f"#{key}"):
                return out_name

        return None

    def _clean_column_name(self, col: str) -> str:
        col = col.replace('"', "").strip()
        return self.COLUMN_MAPPING.get(col, col)

    def _clean_numeric_value(self, value: str):
        value = value.replace('"', "").strip()

        if value == "":
            return None

        return float(value)


class FrequencySplitter:
    def split_folder(self, input_folder: Path) -> None:
        for input_file in input_folder.glob("*.csv"):
            self.split_file(input_file)

    def split_file(self, input_file: Path) -> None:
        df = pd.read_csv(input_file)

        if "freq/Hz" not in df.columns:
            raise ValueError("Column 'freq/Hz' not found.")

        freq = df["freq/Hz"].to_numpy()

        trend = None
        segments = []
        start_idx = 0

        for i in range(1, len(freq)):
            diff = freq[i] - freq[i - 1]
            current_trend = 1 if diff > 0 else -1

            if trend is None:
                trend = current_trend
                continue

            if current_trend != trend:
                segments.append(df.iloc[start_idx:i].copy())
                start_idx = i

        if start_idx == 0:
            return

        segments.append(df.iloc[start_idx:].copy())

        for idx, segment_df in enumerate(segments, start=1):
            output_path = (
                input_file.parent / f"{input_file.stem}_{idx}{input_file.suffix}"
            )
            segment_df.to_csv(output_path, index=False)

        input_file.unlink()


class PreprocessPlotter:
    def plot_folder(self, input_folder: Path, output_folder: Path) -> None:
        output_folder.mkdir(parents=True, exist_ok=True)

        for input_file in input_folder.glob("*.csv"):
            self.plot_file(input_file, output_folder)

    def plot_file(self, input_file: Path, output_folder: Path) -> None:
        df = pd.read_csv(input_file)

        if "freq/Hz" not in df.columns:
            raise ValueError("Column 'freq/Hz' not found.")

        freq = df["freq/Hz"].to_numpy()

        fig = plt.figure(figsize=(12, 5))

        if "Phase(Z)/deg" in df.columns:
            ax = fig.add_subplot(1, 2, 1)
            ax.semilogx(freq, df["Phase(Z)/deg"], marker="o")
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Phase(Z) (deg)")
            ax.set_title("Bode Phase Plot")
            ax.grid(True)

        if "|Z|/Ohm" in df.columns:
            ax = fig.add_subplot(1, 2, 2)
            ax.loglog(freq, df["|Z|/Ohm"], marker="o")
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("|Z| (Ohm)")
            ax.set_title("Bode Magnitude Plot")
            ax.grid(True)

        out_file = output_folder / f"{input_file.stem}.png"

        fig.tight_layout()
        fig.savefig(out_file, dpi=300)
        plt.close(fig)


class EISPreprocessor:
    def __init__(self):
        self.metrohm_cleaner = MetrohmCSVCleaner()
        self.biologic_converter = BioLogicConverter()
        self.frequency_splitter = FrequencySplitter()
        self.preview_plotter = PreprocessPlotter()

    def run(self, experiment) -> None:
        experiment.paths.create_output_folders()

        input_folder = experiment.paths.input
        csv = experiment.paths.csv

        mpr_files = list(input_folder.glob("*.mpr"))
        csv_files = list(input_folder.glob("*.csv"))

        if experiment.paths.pre_plots.is_dir():
            shutil.rmtree(experiment.paths.pre_plots)
        else :
            if mpr_files:
                self.biologic_converter.convert_folder(
                    input_folder,
                    csv,
                )
    
            if csv_files:
                self.metrohm_cleaner.clean_folder(
                    input_folder,
                    csv,
                )
    
            self.frequency_splitter.split_folder(csv)

        if experiment.run.get("pre_plot", False):
            self.preview_plotter.plot_folder(
                csv,
                experiment.paths.pre_plots,
            )

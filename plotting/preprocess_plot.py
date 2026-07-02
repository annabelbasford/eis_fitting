import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

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
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from ..utils import FigureSaver


class PreprocessPlotter:
    def __init__(self, save_preferences):
        self.save_preferences = save_preferences
        self.figure_saver = FigureSaver(save_preferences)

    def plot_folder(self, input_folder: Path, output_folder: Path) -> None:
        output_folder.mkdir(parents=True, exist_ok=True)

        for input_file in input_folder.glob("*.csv"):
            self.plot_file(input_file, output_folder)

    def plot_file(self, input_file: Path, output_folder: Path) -> None:
        df = pd.read_csv(input_file)

        if "freq/Hz" not in df.columns:
            raise ValueError("Column 'freq/Hz' not found.")

        freq = df["freq/Hz"].to_numpy()

        self._plot_bode(
            df=df,
            freq=freq,
            input_file=input_file,
            output_folder=output_folder,
        )

        self._plot_nyquist(
            df=df,
            input_file=input_file,
            output_folder=output_folder,
        )

    def _plot_bode(self, df, freq, input_file, output_folder):
        fig = plt.figure(figsize=(12, 5))
        axes = set()

        if "Phase(Z)/deg" in df.columns:
            ax_phase = fig.add_subplot(1, 2, 1)
            ax_phase.semilogx(
                freq,
                df["Phase(Z)/deg"],
                marker="o",
                linestyle="-",
            )
            ax_phase.set_xlabel("Frequency (Hz)", fontsize=16)
            ax_phase.set_ylabel(r"Phase $\varphi$ (deg)", fontsize=16)
            ax_phase.grid(False)
            axes.add(ax_phase)

        if "|Z|/Ohm" in df.columns:
            ax_modulus = fig.add_subplot(1, 2, 2)
            ax_modulus.loglog(
                freq,
                df["|Z|/Ohm"],
                marker="o",
                linestyle="-",
            )
            ax_modulus.set_xlabel("Frequency (Hz)", fontsize=16)
            ax_modulus.set_ylabel(r"|Z| ($\Omega$)", fontsize=16)
            ax_modulus.grid(False)
            axes.add(ax_modulus)

        if not axes:
            plt.close(fig)
            return

        fig.tight_layout()

        self.figure_saver.save(
            save_path=output_folder / f"{input_file.stem}_bode",
            fig=fig,
            axes=axes,
        )

        plt.close(fig)

    def _plot_nyquist(self, df, input_file, output_folder):
        required_columns = ["Re(Z)/Ohm", "-Im(Z)/Ohm"]

        if not all(col in df.columns for col in required_columns):
            return

        fig, ax = plt.subplots(figsize=(6, 5))

        ax.plot(
            df["Re(Z)/Ohm"],
            df["-Im(Z)/Ohm"],
            marker="o",
            linestyle="-",
        )

        ax.set_xlabel(r"$Z'$ ($\Omega$)", fontsize=16)
        ax.set_ylabel(r"$-Z''$ ($\Omega$)", fontsize=16)
        ax.grid(False)

        fig.tight_layout()

        self.figure_saver.save(
            save_path=output_folder / f"{input_file.stem}_nyquist",
            fig=fig,
            axes={ax},
        )

        plt.close(fig)
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from eis_fitting.utils.figures import FigureSaver


class FitPlotter:
    """
    Low-level plotting class for fitted EIS spectra.

    This class does not know about experiments, metadata, circuits.py,
    or the pipeline. It only receives arrays and save paths.
    """

    def __init__(self, figure_saver: FigureSaver):
        self.figure_saver = figure_saver

    def plot_nyquist(
        self,
        freq,
        z,
        z_fit,
        title,
        save_path,
        chi_square=None,
        reduced_chi_square=None,
    ):
        """
        Plot measured and fitted Nyquist spectra.
        """

        fig, ax = plt.subplots(figsize=(9, 5))

        ax.plot(
            z.real,
            -z.imag,
            "-",
            label="Data",
            linewidth=2,
            color="navy",
            alpha=0.7,
        )

        ax.plot(
            z_fit.real,
            -z_fit.imag,
            "--",
            label="Fit",
            linewidth=2,
            color="lightskyblue",
        )

        ax.set_xlabel(r"Re(Z) ($\Omega$)", fontsize=14)
        ax.set_ylabel(r"-Im(Z) ($\Omega$)", fontsize=14)
        ax.set_title(title, fontsize=13)
        ax.margins(x=0.05, y=0.1)
        ax.legend()

        self._add_fit_statistics_box(
            ax=ax,
            chi_square=chi_square,
            reduced_chi_square=reduced_chi_square,
        )
        self.figure_saver.save(
            save_path=save_path,
            fig=fig,
            axes={ax},
        )

    def plot_bode(
        self,
        freq,
        z,
        z_fit,
        title,
        save_path,
        chi_square=None,
        reduced_chi_square=None,
    ):
        """
        Plot measured and fitted Bode magnitude/phase spectra.
        """

        zmod = np.abs(z)
        phase = np.angle(z, deg=True)

        zmod_fit = np.abs(z_fit)
        phase_fit = np.angle(z_fit, deg=True)

        fig, axes = plt.subplots(
            2,
            1,
            figsize=(7, 6),
            sharex=True,
        )

        axes[0].plot(
            freq,
            zmod,
            "-",
            label="Data",
            color="navy",
            linewidth=2,
            alpha=0.7,
        )

        axes[0].plot(
            freq,
            zmod_fit,
            "--",
            label="Fit",
            color="lightskyblue",
            linewidth=2,
        )

        axes[0].set_xscale("log")
        axes[0].set_yscale("log")
        axes[0].set_ylabel(r"|Z| ($\Omega$)", fontsize=14)
        axes[0].legend()

        axes[1].plot(
            freq,
            phase,
            "-",
            label="Data",
            color="navy",
            linewidth=2,
            alpha=0.7,
        )

        axes[1].plot(
            freq,
            phase_fit,
            "--",
            label="Fit",
            color="lightskyblue",
            linewidth=2,
        )

        axes[1].set_xscale("log")
        axes[1].set_xlabel(r"Frequency ($Hz$)", fontsize=14)
        axes[1].set_ylabel(r"Phase ($°$)", fontsize=14)

        fig.suptitle(title)

        self._add_fit_statistics_box(
            ax=axes[1],
            chi_square=chi_square,
            reduced_chi_square=reduced_chi_square,
        )

        self.figure_saver.save(
            save_path=save_path,
            fig=fig,
            axes={axes[0], axes[1]},
        )

    def plot_all_files_for_circuit(
        self,
        fit_data_dict,
        circuit_name,
        save_folder,
    ):
        """
        Plot all samples for one circuit on combined Nyquist and Bode plots.

        Parameters
        ----------
        fit_data_dict : dict
            Dictionary structured as:
            {
                sample_name: {
                    "freq": freq,
                    "Z": Z,
                    "Z_fit": Z_fit,
                }
            }

        circuit_name : str
            Name of the fitted circuit.

        save_folder : pathlib.Path
            Folder where the combined plots are saved.
        """

        save_folder = Path(save_folder)
        save_folder.mkdir(parents=True, exist_ok=True)

        n_samples = len(fit_data_dict)

        if n_samples == 0:
            return

        palette = sns.color_palette("Paired", 2 * n_samples)

        self._plot_all_nyquist(
            fit_data_dict=fit_data_dict,
            circuit_name=circuit_name,
            save_folder=save_folder,
            palette=palette,
        )

        self._plot_all_bode(
            fit_data_dict=fit_data_dict,
            circuit_name=circuit_name,
            save_folder=save_folder,
            palette=palette,
        )

    def _plot_all_nyquist(
        self,
        fit_data_dict,
        circuit_name,
        save_folder,
        palette,
    ):
        fig, ax = plt.subplots(figsize=(9, 5))

        for i, (sample_name, data) in enumerate(fit_data_dict.items()):
            data_colour = palette[2 * i]
            fit_colour = palette[2 * i + 1]

            z = data["Z"]
            z_fit = data["Z_fit"]

            ax.plot(
                z.real,
                -z.imag,
                "-",
                color=data_colour,
                label=f"{sample_name} data",
                linewidth=2,
            )

            ax.plot(
                z_fit.real,
                -z_fit.imag,
                "--",
                color=fit_colour,
                label=f"{sample_name} fit",
                linewidth=2,
            )

        ax.set_xlabel(r"Re(Z) ($\Omega$)", fontsize=14)
        ax.set_ylabel(r"-Im(Z) ($\Omega$)", fontsize=14)
        ax.set_title(f"{circuit_name} | Nyquist", fontsize=13)
        ax.margins(x=0.05, y=0.1)
        ax.legend(
            fontsize=8,
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
        )

        self.figure_saver.save(
            save_path=save_folder / f"all_files_{circuit_name}_nyquist",
            fig=fig,
            axes={ax},
        )

    def _plot_all_bode(
        self,
        fit_data_dict,
        circuit_name,
        save_folder,
        palette,
    ):
        fig, axes = plt.subplots(
            2,
            1,
            figsize=(9, 7),
            sharex=True,
        )

        for i, (sample_name, data) in enumerate(fit_data_dict.items()):
            data_colour = palette[2 * i]
            fit_colour = palette[2 * i + 1]

            freq = data["freq"]
            z = data["Z"]
            z_fit = data["Z_fit"]

            axes[0].plot(
                freq,
                np.abs(z),
                "-",
                color=data_colour,
                label=f"{sample_name} data",
                linewidth=2,
            )

            axes[0].plot(
                freq,
                np.abs(z_fit),
                "--",
                color=fit_colour,
                label=f"{sample_name} fit",
                linewidth=2,
            )

            axes[1].plot(
                freq,
                np.angle(z, deg=True),
                "-",
                color=data_colour,
                label=f"{sample_name} data",
                linewidth=2,
            )

            axes[1].plot(
                freq,
                np.angle(z_fit, deg=True),
                "--",
                color=fit_colour,
                label=f"{sample_name} fit",
                linewidth=2,
            )

        axes[0].set_xscale("log")
        axes[0].set_yscale("log")
        axes[0].set_ylabel(r"|Z| ($\Omega$)", fontsize=14)
        axes[0].legend(
            fontsize=8,
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
        )

        axes[1].set_xscale("log")
        axes[1].set_xlabel(r"Frequency (Hz)", fontsize=14)
        axes[1].set_ylabel(r"Phase (°)", fontsize=14)

        fig.suptitle(f"{circuit_name} | Bode", fontsize=13)

        self.figure_saver.save(
            save_path=save_folder / f"all_files_{circuit_name}_bode",
            fig=fig,
            axes={axes[0], axes[1]},
        )

    def _add_fit_statistics_box(
        self,
        ax,
        chi_square=None,
        reduced_chi_square=None,
        x=0.03,
        y=0.97,
    ):
        """
        Add chi-square and reduced chi-square as a text box on a plot.
        """

        text = self._format_fit_statistics(
            chi_square=chi_square,
            reduced_chi_square=reduced_chi_square,
        )

        if text is None:
            return

        ax.text(
            x,
            y,
            text,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=11,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": "black",
                "alpha": 0.85,
            },
        )

    @staticmethod
    def _format_fit_statistics(chi_square=None, reduced_chi_square=None):
        """
        Format chi-square statistics for display on fit plots.
        """

        lines = []

        if chi_square is not None and np.isfinite(chi_square):
            lines.append(rf"$\chi^2$ = {chi_square:.3e}")

        if reduced_chi_square is not None and np.isfinite(reduced_chi_square):
            lines.append(rf"$\chi^2_\mathrm{{red}}$ = {reduced_chi_square:.3e}")

        if not lines:
            return None

        return "\n".join(lines)

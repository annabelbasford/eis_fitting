from pathlib import Path

import numpy as np
import pandas as pd
from galvani import BioLogic


class EISCSVReader:
    @staticmethod
    def read_impedance(path: Path):
        df = pd.read_csv(path)

        freq = df["freq/Hz"].to_numpy(dtype=float)
        z_real = df["Re(Z)/Ohm"].to_numpy(dtype=float)
        z_minus_imag = df["-Im(Z)/Ohm"].to_numpy(dtype=float)

        z = z_real - 1j * z_minus_imag

        return freq, z

    @staticmethod
    def omega_max(path: Path) -> float:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()

        idx_max = df["-Im(Z)/Ohm"].idxmax()
        f_max = df.loc[idx_max, "freq/Hz"]

        return 2 * np.pi * f_max


class BioLogicConverter:
    def convert_folder(self, input_folder: Path, output_folder: Path) -> None:
        output_folder.mkdir(parents=True, exist_ok=True)

        for mpr_path in input_folder.glob("*.mpr"):
            mpr = BioLogic.MPRfile(str(mpr_path))
            df = pd.DataFrame(mpr.data)

            csv_path = output_folder / f"{mpr_path.stem}.csv"
            df.to_csv(csv_path, index=False)
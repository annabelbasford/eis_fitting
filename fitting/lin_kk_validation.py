import traceback

import numpy as np

import contextlib
import io

import impedance.validation as impedance_validation
from impedance.validation import linKK

# Patch impedance.py Lin-KK eval namespace.
# The error:
#     NameError: name 'np' is not defined
# comes from impedance.validation.eval_linKK(), not from this file.
if hasattr(impedance_validation, "circuit_elements"):
    impedance_validation.circuit_elements["np"] = np


class LinKKValidator:
    def __init__(
        self,
        c=0.85,
        max_M=50,
        fit_type="complex",
        add_cap=True,
    ):
        self.c = c
        self.max_M = max_M
        self.fit_type = fit_type
        self.add_cap = add_cap

    def run(self, freq, z):
        freq = np.asarray(freq, dtype=float)
        z = np.asarray(z, dtype=complex)

        valid = (
            np.isfinite(freq)
            & (freq > 0)
            & np.isfinite(z.real)
            & np.isfinite(z.imag)
            & (np.abs(z) > 0)
        )

        freq = freq[valid]
        z = z[valid]

        if freq.size < 8:
            return self._failed_result("Not enough valid frequency points.")

        try:
            # to silence impedance.validation.linKK prints in the terminal
            with contextlib.redirect_stdout(io.StringIO()):
                M, mu, z_lin_kk, res_real, res_imag = linKK(
                    freq,
                    z,
                    c=self.c,
                    max_M=self.max_M,
                    fit_type=self.fit_type,
                    add_cap=self.add_cap,
                )

            res_real_percent = 100 * np.asarray(res_real, dtype=float)
            res_imag_percent = 100 * np.asarray(res_imag, dtype=float)

            abs_residual_percent = np.sqrt(res_real_percent**2 + res_imag_percent**2)

            return {
                "lin_kk_success": True,
                "lin_kk_error": "",
                "lin_kk_M": int(M),
                "lin_kk_mu": float(mu),
                "lin_kk_max_abs_residual_percent": float(
                    np.nanmax(abs_residual_percent)
                ),
                "lin_kk_mean_abs_residual_percent": float(
                    np.nanmean(abs_residual_percent)
                ),
                "lin_kk_freq": freq,
                "lin_kk_Z_fit": z_lin_kk,
                "lin_kk_res_real_percent": res_real_percent,
                "lin_kk_res_imag_percent": res_imag_percent,
            }

        except Exception as error:
            print("\nLin-KK validation failed with traceback:")
            traceback.print_exc()
            return self._failed_result(str(error))

    def _failed_result(self, error):
        return {
            "lin_kk_success": False,
            "lin_kk_error": error,
            "lin_kk_M": np.nan,
            "lin_kk_mu": np.nan,
            "lin_kk_max_abs_residual_percent": np.nan,
            "lin_kk_mean_abs_residual_percent": np.nan,
            "lin_kk_freq": None,
            "lin_kk_Z_fit": None,
            "lin_kk_res_real_percent": None,
            "lin_kk_res_imag_percent": None,
        }

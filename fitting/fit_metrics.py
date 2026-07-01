import numpy as np


class FitMetrics:
    """
    Numerical fit-quality metrics for complex EIS fits.
    """

    @staticmethod
    def residuals(Z_exp, Z_fit):
        """
        Complex residuals.

        residual = Z_exp - Z_fit
        """

        Z_exp = np.asarray(Z_exp, dtype=complex)
        Z_fit = np.asarray(Z_fit, dtype=complex)

        return Z_exp - Z_fit

    @staticmethod
    def relative_residuals_percent(Z_exp, Z_fit):
        """
        Relative residuals in percent.

        The residuals are normalised by |Z_exp| so that high-impedance
        points do not dominate the visual interpretation.
        """

        Z_exp = np.asarray(Z_exp, dtype=complex)
        Z_fit = np.asarray(Z_fit, dtype=complex)

        denominator = np.abs(Z_exp)

        valid = (
            np.isfinite(Z_exp.real)
            & np.isfinite(Z_exp.imag)
            & np.isfinite(Z_fit.real)
            & np.isfinite(Z_fit.imag)
            & np.isfinite(denominator)
            & (denominator > 0)
        )

        real_residual = np.full_like(denominator, np.nan, dtype=float)
        imag_residual = np.full_like(denominator, np.nan, dtype=float)
        abs_residual = np.full_like(denominator, np.nan, dtype=float)

        real_residual[valid] = (
            100 * (Z_exp.real[valid] - Z_fit.real[valid]) / denominator[valid]
        )

        imag_residual[valid] = (
            100 * (Z_exp.imag[valid] - Z_fit.imag[valid]) / denominator[valid]
        )

        abs_residual[valid] = (
            100 * np.abs(Z_exp[valid] - Z_fit[valid]) / denominator[valid]
        )

        return {
            "real_percent": real_residual,
            "imag_percent": imag_residual,
            "abs_percent": abs_residual,
            "valid": valid,
        }

    @staticmethod
    def residual_summary(Z_exp, Z_fit):
        """
        Summary statistics for the residuals.

        These values can be saved in the parameter CSV.
        """

        residuals = FitMetrics.relative_residuals_percent(
            Z_exp=Z_exp,
            Z_fit=Z_fit,
        )

        real_residual = residuals["real_percent"]
        imag_residual = residuals["imag_percent"]
        abs_residual = residuals["abs_percent"]

        return {
            "mean_real_residual_percent": FitMetrics._safe_nanmean(real_residual),
            "mean_imag_residual_percent": FitMetrics._safe_nanmean(imag_residual),
            "mean_abs_residual_percent": FitMetrics._safe_nanmean(abs_residual),
            "max_abs_residual_percent": FitMetrics._safe_nanmax(abs_residual),
        }

    @staticmethod
    def chi_square(Z_exp, Z_fit, relative=True):
        """
        Compute chi-square for complex EIS data.
        """

        Z_exp = np.asarray(Z_exp, dtype=complex)
        Z_fit = np.asarray(Z_fit, dtype=complex)

        residual = Z_exp - Z_fit
        residual_squared = residual.real**2 + residual.imag**2

        if relative:
            denominator = np.abs(Z_exp) ** 2

            valid = (
                np.isfinite(residual_squared)
                & np.isfinite(denominator)
                & (denominator > 0)
            )

            terms = residual_squared[valid] / denominator[valid]

        else:
            valid = np.isfinite(residual_squared)
            terms = residual_squared[valid]

        if terms.size == 0:
            return np.nan

        return float(np.sum(terms))

    @staticmethod
    def reduced_chi_square(Z_exp, Z_fit, n_parameters, relative=True):
        """
        Reduced chi-square.

        For complex EIS data, each frequency contributes two values:
        Z' and Z''.
        """

        Z_exp = np.asarray(Z_exp, dtype=complex)
        Z_fit = np.asarray(Z_fit, dtype=complex)

        valid = (
            np.isfinite(Z_exp.real)
            & np.isfinite(Z_exp.imag)
            & np.isfinite(Z_fit.real)
            & np.isfinite(Z_fit.imag)
        )

        n_points = int(np.sum(valid))

        if n_points == 0:
            return np.nan

        chi_square = FitMetrics.chi_square(
            Z_exp=Z_exp[valid],
            Z_fit=Z_fit[valid],
            relative=relative,
        )

        degrees_of_freedom = 2 * n_points - n_parameters

        if degrees_of_freedom <= 0:
            return np.nan

        return float(chi_square / degrees_of_freedom)

    @staticmethod
    def _safe_nanmean(values):
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        if values.size == 0:
            return np.nan

        return float(np.mean(values))

    @staticmethod
    def _safe_nanmax(values):
        values = np.asarray(values, dtype=float)
        values = values[np.isfinite(values)]

        if values.size == 0:
            return np.nan

        return float(np.max(values))
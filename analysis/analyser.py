import numpy as np
import pandas as pd


class EISAnalyser:
    def __init__(self, circuits: dict):
        self.circuits = circuits

    def run(self, experiment) -> None:
        for circuit_name in experiment.circuits:
            parameters_csv = (
                experiment.paths.fits / f"{experiment.name}_{circuit_name}.csv"
            )

            if not parameters_csv.exists():
                print(f"Skipping missing file: {parameters_csv}")
                continue

            self.add_conductivity_columns(
                parameters_csv=parameters_csv,
                circuit_name=circuit_name,
                geometry=experiment.geometry,
                normalize=experiment.plotting["conductivities"].get("normalize", False),
            )

            if experiment.run.get("compute_mean_parameters", False):
                df = pd.read_csv(parameters_csv)
                df = self._append_mean_parameter_row(
                    df=df,
                    circuit_name=circuit_name,
                )

                df.to_csv(
                    parameters_csv,
                    index=False,
                    float_format="%.10e",
                )

    def add_conductivity_columns(
        self, parameters_csv, circuit_name, geometry, normalize
    ):
        df = pd.read_csv(parameters_csv)

        thickness_cm = geometry["thickness_cm"]
        sd_thickness_cm = geometry["SD_thickness_cm"]
        area_cm2 = geometry["area_cm2"]
        sd_area_cm2 = geometry["SD_area_cm2"]

        mapping = self.circuits[circuit_name]["mapping"]

        resistance_names = []

        for raw_name, info in mapping.items():

            if not raw_name.startswith("R_"):
                continue

            if info.get("compute_conductivity", False):
                resistance_names.append(info["name"])

        for resistance_name in resistance_names:
            sd_col = f"SD_{resistance_name}"

            if sd_col not in df.columns:
                print(f"\nSkipping conductivity for {resistance_name}: no {sd_col}")
                continue
            
            conductivity = None
            sd_conductivity = None

            if not normalize:
                conductivity = thickness_cm / (df[resistance_name] * area_cm2)

                sd_conductivity = conductivity * np.sqrt(
                    (sd_thickness_cm / thickness_cm) ** 2
                    + (sd_area_cm2 / area_cm2) ** 2
                    + (df[sd_col] / df[resistance_name]) ** 2
                )
            else : 
                conductivity = 1 / (df[resistance_name])
                min_conductivity = conductivity.min()
                conductivity = conductivity / min_conductivity

                # propagated uncertainty for normalized conductivity
                sd_conductivity = df[sd_col]/df[resistance_name]**2

                


            df[f"conductivity_S_cm_{resistance_name}"] = conductivity
            df[f"SD_conductivity_S_cm_{resistance_name}"] = sd_conductivity

        df.to_csv(parameters_csv, index=False)
        df = self._append_mean_parameter_row(df, circuit_name)
        return df

    def _append_mean_parameter_row(self, df, circuit_name):
        """
        Append one mean row to a circuit parameter dataframe.

        Means are computed over successful fits only.

        For fitted parameters with SD_<parameter> columns:
            SD_mean = sqrt(sum(SD_i^2)) / n

        For chi_square and reduced_chi_square:
            SD is the sample standard deviation across successful fits.
        """

        has_mean_row = (
            df["sample"].astype(str).str.strip().str.upper() == "MEAN"
        ).any()

        if "fit_success" not in df.columns or has_mean_row:
            return df

        successful_df = df[df["fit_success"] == True].copy()

        if successful_df.empty:
            return df

        n_samples = len(successful_df)

        mean_row = {col: np.nan for col in df.columns}

        first_row = successful_df.iloc[0]

        mean_row["sample"] = "MEAN"
        mean_row["circuit_name"] = circuit_name
        mean_row["circuit_string"] = first_row.get("circuit_string", np.nan)
        mean_row["fit_success"] = np.nan
        mean_row["fit_status"] = "mean_successful_samples"
        mean_row["n_mean_samples"] = n_samples

        metadata_columns = {
            "sample",
            "circuit_name",
            "circuit_string",
            "fit_success",
            "fit_status",
            "error",
            "n_mean_samples",
        }

        fit_metrics = {
            "chi_square",
            "reduced_chi_square",
        }

        for col in df.columns:

            if col in metadata_columns:
                continue

            if col.startswith("SD_"):
                continue

            if col.endswith("_percent_error"):
                continue

            values = pd.to_numeric(
                successful_df[col],
                errors="coerce",
            )

            values = values[np.isfinite(values)]

            if values.empty:
                continue

            mean_value = values.mean()
            mean_row[col] = mean_value

            sd_col = f"SD_{col}"
            percent_error_col = f"{col}_percent_error"

            if sd_col in successful_df.columns:
                sd_values = pd.to_numeric(
                    successful_df.loc[values.index, sd_col],
                    errors="coerce",
                )

                sd_values = sd_values[np.isfinite(sd_values)]

                if not sd_values.empty:
                    propagated_sd = np.sqrt(np.sum(sd_values**2)) / len(values)

                    mean_row[sd_col] = propagated_sd

                    if mean_value != 0 and np.isfinite(mean_value):
                        mean_row[percent_error_col] = abs(
                            100 * propagated_sd / mean_value
                        )

            elif col in fit_metrics:
                if len(values) > 1:
                    mean_row[f"SD_{col}"] = values.std(ddof=1)
                else:
                    mean_row[f"SD_{col}"] = 0.0

        mean_df = pd.DataFrame([mean_row])

        return pd.concat(
            [df, mean_df],
            ignore_index=True,
            sort=False,
        )

    @staticmethod
    def get_element_columns(parameters_csv, first_chars):
        df = pd.read_csv(parameters_csv)

        return {
            col
            for col in df.columns
            if col.startswith(first_chars) and not col.endswith("error")
        }

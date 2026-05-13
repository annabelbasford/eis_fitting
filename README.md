# EIS Analysis and Equivalent Circuit Fitting

Python workflow for processing, fitting, and visualising electrochemical impedance spectroscopy (EIS) data.

This repository provides tools for:

- Cleaning and restructuring raw EIS export files into unified CSV format
- Fitting impedance spectra to equivalent circuit models
- Extracting fitted circuit parameters and uncertainties
- Generating publication-ready Nyquist and Bode plots
- Batch processing multiple EIS datasets

---

# Features

## Raw EIS Data Processing

The preprocessing scripts:

- Parse raw instrument MPR exports and converting into CSV format
- Parse raw instrument CSV exports from Metrohm equipment
- Detect Bode phase, Bode magnitude, and Nyquist sections
- Standardise EIS column naming conventions
- Combine all measurements per experiment into a single structured CSV

Output format:

| freq/Hz | Phase(Z)/deg | \|Z\|/Ohm | Re(Z)/Ohm | -Im(Z)/Ohm |
|---|---|---|---|---|

---

## Equivalent Circuit Fitting

Supports fitting multiple equivalent circuit models using:

- `impedance.py`
- open-source Python package

Currently implemented models include:

### Randles + CPE

```text
R_1-p(CPE_1,R_2)
```

### Interface + Bulk Model

```text
R_1-p(CPE_1,R_2)-p(R_3,CPE_2)
```

Additional circuit models can be added through the `CIRCUITS` dictionary.

---

## Plotting

Automatically generates:

### Nyquist plots

- Experimental data
- Circuit fit overlay
- Multi-sample comparison plots

### Bode plots

- Magnitude response
- Phase response
- Data vs fitted model

Plots are saved as PNG files.

---

# Repository Structure

```text
.
├── csv/                              # Input EIS CSV files
├── fits/                             # Output fitting results
│   ├── plots/                        # Generated figures
│   └── *.csv                         # Fitted parameter tables
├── 1_eis_analysis.py                 # Main fitting workflow
├── 0_eis_mpr_data_conversion.py      # Raw EIS mpr file preprocessing script
├── 0_eis_metrohm_data_clean.py       # Raw EIS metrohm preprocessing script
└── README.md
```

---

# Installation

## Clone the repository

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
```

---

## Create environment

Using conda:

```bash
conda create -n eis_analysis python=3.11
conda activate eis_analysis
```

---

## Install dependencies

```bash
pip install numpy pandas matplotlib seaborn impedance
```

---

# Usage

## 1. Preprocess raw EIS export

```bash
python 0_eis_mpr_data_conversion.py
```

This converts the mpr data into CSV files.

```bash
python 0_eis_metrohn_data_clean.py
```

This generates a cleaned combined CSV file of the Metrohm data.

---

## 2. Run equivalent circuit fitting

```bash
python 1_eis_analysis.py
```

Outputs:

- Fitted parameter tables
- Confidence intervals
- Percentage fitting errors
- Nyquist plots
- Bode plots

---

# Example Output

## Summary CSV

| sample | circuit_name | R_1 | SD_R_1 | R_1_percent_error | CPE_1_0 | SD_CPE_1_0 | CPE_1_0_percent_error | CPE_1_1 | SD_CPE_1_1 | CPE_1_1_percent_error | R_2 | SD_R_2 | R_2_percent_error | R_3 | SD_R_3 | R_3_percent_error | CPE_2_0 | SD_CPE_2_0 | CPE_2_0_percent_error | CPE_2_1 | SD_CPE_2_1 | CPE_2_1_percent_error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Full CSV has the following columns of the fit:



---

# Dependencies

- Python 3.11+
- numpy
- pandas
- matplotlib
- seaborn
- impedance.py

---

# License

MIT License

---

# Acknowledgements

Built using:

- [`impedance.py`](https://github.com/ECSHackWeek/impedance.py)
- NumPy
- pandas
- matplotlib
- seaborn

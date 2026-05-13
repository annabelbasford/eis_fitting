# EIS Analysis and Equivalent Circuit Fitting

Python workflow for processing, fitting, and visualising electrochemical impedance spectroscopy (EIS) data.

This repository provides tools for:

- Cleaning and restructuring raw EIS export files
- Combining Bode and Nyquist datasets into a unified CSV format
- Fitting impedance spectra to equivalent circuit models
- Extracting fitted circuit parameters and uncertainties
- Generating publication-ready Nyquist and Bode plots
- Batch processing multiple EIS datasets

---

# Features

## Raw EIS Data Processing

The preprocessing scripts:

- Parse raw instrument CSV exports
- Detect Bode phase, Bode magnitude, and Nyquist sections
- Standardise EIS column naming conventions
- Combine all measurements into a single structured CSV

Output format:

| freq/Hz | Phase(Z)/deg | \|Z\|/Ohm | Re(Z)/Ohm | -Im(Z)/Ohm |
|---|---|---|---|---|

---

## Equivalent Circuit Fitting

Supports fitting multiple equivalent circuit models using:

- `impedance.py`
- Non-linear least squares optimisation

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

Plots are saved as high-resolution PNG files.

---

# Repository Structure

```text
.
├── csv/                  # Input EIS CSV files
├── fits/                 # Output fitting results
│   ├── plots/            # Generated figures
│   └── *.csv             # Fitted parameter tables
├── eis_analysis.py       # Main fitting workflow
├── split_eis_csv.py      # Raw EIS preprocessing script
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
python split_eis_csv.py raw_export.csv
```

This generates a cleaned combined CSV file.

---

## 2. Run equivalent circuit fitting

```bash
python eis_analysis.py
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

| sample | circuit_name | R_1 | SD_R_1 | R_1_percent_error |
|---|---|---|---|---|

---

# Dependencies

- Python 3.11+
- numpy
- pandas
- matplotlib
- seaborn
- impedance.py

---

# Future Improvements

Potential future additions include:

- Automatic circuit selection
- Fit quality metrics
- Residual analysis
- Conductivity extraction workflows
- Batch statistics and comparison tools
- Interactive plotting
- Bayesian or global optimisation fitting methods

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

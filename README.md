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
- If need be, slices datasets into strictly monotonic frequency sweeps

Output format:

| freq/Hz | Phase(Z)/deg | \|Z\|/Ohm | Re(Z)/Ohm | -Im(Z)/Ohm |
|---|---|---|---|---|

---

## Equivalent Circuit Fitting

Supports fitting multiple equivalent circuit models using:

- `impedance.py`
- open-source Python package

Currently implemented models include:

### Circuit 1 : pseudo-Randles

> **p(R_1-CPE_1,R_2)**
```text
                ┌─ CPE1 ── R1 ─┐
────────────────┤              ├────────────
                └───── R2 ─────┘
```

### Interface + Bulk Model

> **R_1-p(R_3-CPE_1,CPE_2,R_2)**
```text
                 ┌─ R3 ─ CPE1 ┐
                 │            │
───── R1 ────────┼─── CPE2 ───┼─────────────
                 │            │
                 └──── R2 ────┘
```

Additional circuit models can be added through the `CIRCUITS` dictionary by respecting the following structure :

```json
"circuit_1": {
        "string": "p(R_1-CPE_1,R_2)",
        "guess": [100, 1e-6, 0.9, 1000],
    }
```

> The *"guess"* key is used during the fitting methode as a starting point and should thus be **carefully chosen**. We'll also note that these guesses ought to be given **in the same order as the components** in the *"string"* key and that two guesses are expected for a CPE : Q and n

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

## Analysis

During the preprocessing, omega_max is determined and added in a column of the clean csv. 

yada yada still a lot of stuff to write here 

---
---

# Repository Structure

## Recommended general structure

```text
.
├── data  
│   ├─── experiment_1                                        # experimental data folder (.mpr or metrohm csv)
│   └─── ...                                                 
├── projects                                                  
│   └─── eis_fitting                                         
│        ├─── global.py                                      # main script calling functions from scripts/
│        ├─── scripts                                        # contains preprocessing, fitting and analysis scripts
│        └─── processed                                      
│             ├─── experiment_1                              # see subsection "Output Folder structure"
│             └─── ...
└  
```

> NB : you can use your own architecture by changing the **PROJECT_ROOT** path in `global.py`

## Experimental data folder structure

```text
.
├── experiment_1
|   ├─── metrohm_raw_data.csv
|   ├─── raw_data_run1.mpr
|   .
|   .
|   └─── metadata.json                                       # see "Usage" section
└ 
```
> NB : mpr files can contain multiple frenquencies swipe in a raw thanks to the *split_non_monotonic_frequency_csv* in **scripts/eis_preprocess**
> ⚠️ sample's name **MUST NOT** contain full stops : instead of *"P2U1.2"* use *"P2U1_2"* otherwise everything after the full stop will be read as an extension and won't be processed.

---

# Installation

## Clone the repository

```bash
git clone https://github.com/annabelbasford/eis_fitting.git
cd eis_fitting
```

---

## Create environment

Using conda:

```bash
conda create -n eis_fitting python=3.11
conda activate eis_fitting
```

---

## Install dependencies

```bash
pip install numpy pandas matplotlib seaborn impedance galvani
```

---

# Usage

Before trying to run the code, make sure your environment is ordered like shown in section "Recomended general Structure"

## 1. Make sure your data folder is properly ordered (see "Experimental data folder" subsection)  

`metadata.json` file template 
```json
{
    "thickness_cm": 0.1,
    "SD_thickness_cm": 0.01,
    "area_cm2": 1.0,
    "SD_area_cm2": 0.2,
    "png" : true,
    "svg": false,     
    "sigma_f":20    
}
```

> The *"png"* and *"svg"* keys tells the script if it has to save the plots as .png files and/or transparent .svg files 
> sigma_f, in Hz, should reflect how precisely the frequency at which -Im(Z) is maximum can be determined

## 2. If need be, fill in the expectFolders set

# Example Output

Outputs:

- Fitted parameter tables
- Confidence intervals
- Percentage fitting errors
- Nyquist plots
- Bode plots
- parameters bar charts

> NB : Effective capacitances are obtained from CPEs parameters using Hsu-Mansfeld's relation

---

## Summary CSV

| sample | circuit_name | R_1 | SD_R_1 | R_1_percent_error | CPE_1_0 | SD_CPE_1_0 | CPE_1_0_percent_error | CPE_1_1 | SD_CPE_1_1 | CPE_1_1_percent_error | R_2 | SD_R_2 | R_2_percent_error | ... |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Processed folder structure

```text
.
├─── processed 
│    ├─── experiment_1                                       # see below for recommended naming conventions
│    |    ├─── csv                                           # clean csv data
│    |    ├─── fits                                          
│    |    │    ├─── plots                                    
│    |    │    │    ├─── sample_1                               
│    |    │    |    |    ├─── circuit 1                      # Bode, Nyquist and parameter bar charts
│    .    │    |    .    .
│    .    │    |    .    └             
│    │    │    │    └─── all_runs                            # Bode and Nyquist plots                   
│    |    │    ├─── eis_fit_parameters_circuit_1.csv         
│    |    .    .
│    |    .    .
│    |    │    └─── eis_fit_parameters_all_circuits.csv      
└    └    └ 
```

Naming conventions for data folder : INITIALS_experiment-name_date

---


---
# Important notes

Before implementing new circuits, it is highly recommended to check how the `impedance.py` library handles equivalent circuits : *https://impedancepy.readthedocs.io/en/latest/fitting.html*

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

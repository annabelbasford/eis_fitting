# EIS Fitting

A Python package for the automated preprocessing, fitting, analysis and visualisation of Electrochemical Impedance Spectroscopy (EIS) data.

The package is primarily designed for conductive hydrogels but can easily be adapted to other electrochemical systems through configurable equivalent circuits and experiment profiles.

---

## Features

- Import BioLogic (`.mpr`) and Metrohm (`.csv`) EIS data
- Automatic preprocessing and data cleaning
- Automatic splitting of non-monotonic frequency sweeps
- Equivalent circuit fitting using `impedance.py`
- Multiple equivalent circuits per experiment
- Automatic conductivity calculation
- Effective capacitance (`C_eff`) calculation from CPE elements
- Publication-quality Nyquist and Bode plots
- Automatic parameter bar charts
- Reusable experiment profiles
- Modular object-oriented architecture

---

# Installation

Clone the repository

```bash
git clone https://github.com/<username>/eis_fitting.git
cd eis_fitting
```

Create a Python environment

```bash
conda create -n eis python=3.12
conda activate eis
```

Install the required packages

```bash
pip install -r requirements.txt
```

or install the package in editable mode

```bash
pip install -e .
```

---

# Project structure

```
eis_fitting/
│
├── analysis/
├── config/
├── core/
├── fitting/
├── io/
├── plotting/
├── preprocessing/
├── utils/
│
├── circuits.py
├── pipeline.py
├── main.py
└── README.md
```

---

# Data organisation

Experiments are organised by

```
Person
    ↓
Project
    ↓
Experiment
```

The recommended structure is

```
data/
│
├── profiles/
│   ├── profile_1.json
│   ├── profile_2.json
│   └── ...
│
└── person/
    └── project/
        ├── experiment_001/
        │   ├── metadata.json
        │   ├── sample_1.mpr
        │   ├── sample_2.mpr
        │   └── ...
        │
        ├── experiment_002/
        └── ...
```

---

# Profiles

Profiles contain reusable defaults shared by many experiments.

Typical information includes

- sample geometry
- processing parameters
- save preferences

Example

```json
{
    "geometry": {
        "thickness_cm": 0.10,
        "SD_thickness_cm": 0.01,
        "area_cm2": 1.00,
        "SD_area_cm2": 0.20
    },

    "processing": {
        "sigma_f": 20
    },

    "save_preferences": {
        "transparent": false,
        "png": true,
        "svg": false
    }
}
```

---

# Experiment metadata

Each experiment contains a `metadata.json` describing only experiment-specific information.

Example

```json
{
    "profile": "profile_1",

    "description": "PEDOT:PSS hydrogel",

    "run": {
        "preprocess": true,
        "fit": true,
        "analyse": true,
        "pre_plot": false,
        "plot": true
    },

    "circuits": [
        "circuit_1"
    ]
}
```

The package automatically combines the selected profile with the experiment metadata before processing.

---

# Output modes

The pipeline supports two output modes.

## Local mode

Processed data are stored next to the experiment.

```
experiment_001/
│
├── metadata.json
├── <experimental_file>
└── processed/                   # if set in local output mode
```

---

## Workspace mode

Processed data are written to a separate workspace.

```
workspace/
└── processed/
    └── person/
        └── project/
            └── experiment_001/
```

This allows raw experimental data to remain untouched while centralising all processed outputs.

---

# Processed data structure

Each processed experiment follows the structure

```
processed/
│
├── csv/
│
├── fits/
│   ├── plots/
│   │   ├── sample_1/
│   │   │   ├── circuit_1/
│   │   │   ├── circuit_2/
│   │   │   └── ...
│   │   │
│   │   └── all_runs/
│   │
│   ├── eis_fit_parameters_circuit_1.csv
│   ├── eis_fit_parameters_circuit_2.csv
│   └── eis_fit_parameters_all_circuits.csv
│
└── pre_plots/
```

---

# Running the pipeline

Edit `main.py`

```python
PERSON = "enzo"

PROJECT = "EIS_hydrogels"

OUTPUT_MODE = "local"

OUTPUT_ROOT = None
```

or

```python
OUTPUT_MODE = "workspace"

OUTPUT_ROOT = Path("/home/user/eis_results")
```

Run

```bash
python -m eis_fitting.main
```

---

# Equivalent circuits

Equivalent circuits are defined in

```
circuits.py
```

Each circuit contains

- impedance model
- initial parameter guesses
- plotting colours
- parameter display names
- plotting order

Example

```python
"circuit_1": {

    "string": "p(R_1-CPE_1,R_2)",

    "guess": [...],

    "mapping": {

        ...

    }

}
```

Adding a new equivalent circuit simply requires adding a new entry to `CIRCUITS`.

---

# Pipeline

The processing pipeline consists of four independent stages

```
Raw data
    │
    ▼
Preprocessing
    │
    ▼
Equivalent circuit fitting
    │
    ▼
Analysis
    │
    ▼
Plot generation
```

Each stage is implemented as an independent class, making the package easy to extend and maintain.

---

# Package architecture

```
main.py

        │

        ▼

EISPipeline

        │

        ▼

Experiment

        │

        ├── Preprocessor

        ├── Fitter

        ├── Analyser

        └── Plotter
```

The pipeline orchestrates the complete workflow while each processing stage remains independent.

---

# Dependencies

- NumPy
- Pandas
- Matplotlib
- SciPy
- impedance.py
- seaborn
- galvani

---

# Citation

If this package contributes to your research, please cite the associated publication(s).

---

# License

MIT License
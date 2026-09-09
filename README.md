# MTS-UncertainEnvironment (`sarenv-mts`)

Framework for Intelligent UAV Trajectory Optimization in Search and Rescue (SAR) missions over realistic uncertain environments.

This repository branch (`sarenv-mts`) integrates open vector cartography from **OpenStreetMap (OSM)**, empirical search theory based on **Robert Koester's Lost Person Behavior (LPB)**, and bio-inspired metaheuristic path planners (**Ant Colony Optimization - ACO**, **Artificial Bee Colony - ABC**, and **Black Hole Algorithm - BHA**).

Developed as part of the Master's Thesis at **Universidad Carlos III de Madrid (UC3M)** by **Juan Carlos Estefania**, supervised by **Prof. Jesus Garcia Herrero** and **Prof. Juan Pedro Llerena Cana**, building upon the MTS framework foundation by **Yago Broton Gutierrez**.

---

## Key Features

- **Empirical LPB Probability Modeling (`sarenv`):** Automated generation of topological Probability of Area (POA) maps combining OpenStreetMap features (paths, forests, water, structures) with Koester's behavioral dispersion distributions (Dementia, Autistic, Hiker).
- **Physical Hard Constraint Masking:** Spatial index filtering (R-Tree / `sindex`) enforcing strict zero probability ($P = 0.0$) over non-traversable geometries (deep water bodies and closed structures).
- **Spatial Middleware:** Coordinate transformation pipeline converting global UTM coordinates (EPSG:32630) into local discrete 2D simulation grids ($\delta = 10\text{ m/cell}$).
- **Sensor Observation Model:** Realistic circular sensor footprint ($R_d = 50\text{ m}$) derived from optical flight parameters ($h = 50\text{ m}$, $\theta_{\text{FoV}} = 90^\circ$), with dynamic residual belief map updates via Recursive Bayesian Filtering (RBF).
- **Bio-inspired Metaheuristic Planners:** ACO, ABC, and BHA path planners optimized via Bayesian hyperparameter tuning (Optuna, 30 trials per profile).
- **Standardized Evaluation (`metrics`):** Centralized `PathEvaluatorTFM` module computing 5 official SAR metrics: Success Rate (%), Steps to Goal, Reduced Belief (%), Covered Area ($\text{km}^2$), and Total Flight Length (km).

---

## Repository Structure

```text
.
├── sarenv/               # Topological SAR probability modeling package
│   ├── env.py            # Environment builder and OSM polygon fetcher
│   ├── base.py           # Layer rasterization and normalization
│   └── profiles/         # Koester LPB statistical profiles (Dementia, Autistic, Hiker)
├── busquedas/            # Trajectory planning algorithms
│   ├── aco/              # Ant Colony Optimization (ACO)
│   ├── abc/              # Artificial Bee Colony (ABC)
│   ├── bha/              # Black Hole Algorithm (BHA)
│   ├── voraz/            # Greedy local search baseline
│   └── geometricas/      # Lawnmower and Expanding Spiral baselines
├── metrics/              # Centralized evaluation module
│   └── evaluator.py      # PathEvaluatorTFM (5 SAR metrics calculation)
├── middleware/           # System bridge tools
│   ├── utils_pipeline.py # Coordinate projections (UTM <-> Discrete Grid)
│   └── generar_json.py   # Scenario exporter to MTS format
├── extra/                # Additional utilities and figure generation scripts
├── TFM_JC/               # Master Thesis artifacts, notebooks and experimental data
│   ├── notebooks/        # Interactive Jupyter Notebooks
│   │   ├── Notebook_Demo_Rapida_Interactiva.ipynb    # Real-time interactive flight demo
│   │   ├── Analisis_Resultados.ipynb                 # Statistical analysis & boxplots
│   │   └── Benchmark_Perfiles_Real_Interactivo.ipynb # Full profile comparison
│   └── resultados/       # Master CSV database of 900 Monte Carlo simulations
├── requirements.txt      # Python dependencies
└── environment.yml       # Conda environment specification
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.10 and 3.11)
- Conda (recommended) or standard venv

### Option A: Using Conda (Recommended)
```bash
git clone -b sarenv-mts https://github.com/Jompy-GitHub/MTS-UncertainEnvironment.git
cd MTS-UncertainEnvironment
conda env create -f environment.yml
conda activate mts-sarenv
```

### Option B: Using Pip
```bash
git clone -b sarenv-mts https://github.com/Jompy-GitHub/MTS-UncertainEnvironment.git
cd MTS-UncertainEnvironment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

---

## Interactive Notebooks Guide

The framework includes three dedicated, production-ready Jupyter Notebooks located in `TFM_JC/notebooks/`:

Launch Jupyter Lab or Notebook to interact with them:

```bash
jupyter lab
```

### 1. `Notebook_Demo_Rapida_Interactiva.ipynb` (Quick Dual-Panel Flight Demo)
- **Purpose:** Fast, visual, and interactive demonstration of individual search missions.
- **Features:** 
  - Dual real-time GUI: Left panel renders the 2D UAV flight path advancing over the residual belief map $b(v^k)$; right panel displays live radar/step charts of the 5 official SAR metrics.
  - Dropdown selectors to swap between behavioral profiles (Dementia, Autistic, Hiker) and algorithms (ABC, BHA, ACO, Greedy, Lawnmower).
  - Fast execution mode with caching for instant interactive demonstrations and tribunal presentations.

### 2. `Benchmark_Perfiles_Real_Interactivo.ipynb` (Full Pipeline & Advanced Benchmark)
- **Purpose:** Comprehensive, end-to-end mission engineering and multi-algorithm benchmarking panel.
- **Features:**
  - Full configuration of OpenStreetMap multilayer weights (`FEATURE_PROBABILITIES`) and Robert Koester's empirical LPB dispersion models.
  - Parameter customization: sensor footprint radius, altitude, flight budget (battery steps), and initial seed distributions.
  - Side-by-side trajectory execution and spatial overlay comparison between bio-inspired planners (ABC vs. BHA vs. ACO) and geometric baselines.
  - Telemetry generation and direct export to CSV/JSON format for validation.

### 3. `Analisis_Resultados.ipynb` (Statistical Analysis & Figure Generation)
- **Purpose:** Post-processing and rigorous statistical analysis of the 900 Monte Carlo simulation runs.
- **Features:**
  - Automated loading of the master database (`TFM_JC/resultados/resultados_totales.csv`).
  - Descriptive statistics calculation: means, medians, standard deviations, and Interquartile Ranges (IQR).
  - High-resolution (300 DPI) reproduction of all paper and thesis figures, boxplots, success rate charts, and temporal belief decay curves.

---

## Experimental Benchmark (900 Monte Carlo Runs)

The system was evaluated over a massive benchmark of 900 simulations in the Casa de Campo scenario ($17.22\text{ km}^2$, discretized into a $458 \times 481$ grid at $10\text{ m/cell}$):
- **3 Behavioral Profiles:** Dementia, Autistic, Hiker.
- **6 Planners:** ACO, ABC, BHA, Greedy, Lawnmower, Expanding Spiral.
- **50 Independent Seeds** per algorithm/profile combination.
- **Optuna Tuning:** 30 Bayesian optimization trials per metaheuristic.

All aggregated telemetry, raw data, and statistical figures (300 DPI) are located in `TFM_JC/resultados/`.

---

## Citation & References

If you use this software or results in your research, please cite:

```bibtex
@mastersthesis{estefania2026tfm,
  author       = {Juan Carlos Estefania},
  title        = {{Optimizacion Inteligente de Rutas de Busqueda y Salvamento con Drones mediante la Integracion de SAREnv y MTS en Entornos de Incertidumbre}},
  school       = {Universidad Carlos III de Madrid (UC3M)},
  year         = {2026},
  type         = {Trabajo de Fin de Master}
}
```

Acknowledgements to the **Applied Artificial Intelligence Group (GIAA)** at Universidad Carlos III de Madrid.

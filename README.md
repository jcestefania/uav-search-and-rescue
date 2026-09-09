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

## Interactive Quick Start

Launch Jupyter Lab or Notebook to explore the interactive simulation:

```bash
jupyter lab
```

Open `TFM_JC/notebooks/Notebook_Demo_Rapida_Interactiva.ipynb`:
1. Select the operational profile (Dementia, Autistic, Hiker).
2. Choose the planning algorithm (ABC, BHA, ACO, Voraz, Lawnmower).
3. Execute the cells to visualize the dual real-time panel: flight trajectory evolution over the belief map and step-by-step SAR metrics.

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

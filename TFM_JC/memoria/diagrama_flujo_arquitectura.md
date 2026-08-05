# Arquitectura General y Diagramas Modularizados del Sistema (SAREnv + Middleware + MTS + PathEvaluatorTFM)

Este documento contiene la arquitectura general simplificada (de nivel de sistema) y la descomposición en **diagramas desacoplados por módulo**. La explicación y redacción del documento está en español, mientras que **los diagramas de flujo internos están en inglés** para facilitar su inserción directa en las figuras de la Memoria.

---

## 🏛️ 1. Diagrama General de Arquitectura (Nivel Sistema / Propuesta)

Este diagrama sintetiza el flujo de datos principal entre los 5 módulos funcionales del sistema sin recargar la vista.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e2e8f0', 'primaryBorderColor': '#64748b', 'primaryTextColor': '#0f172a', 'lineColor': '#334155', 'fontSize': '14px'}}}%%
graph LR
    M1["<b>Module 1</b><br/>Environment Generation<br/><i>(SAREnv & LPB)</i>"] -->|Baseline Heatmap| M2["<b>Module 2</b><br/>Constraints Filtering<br/><i>(Sindex R-Tree)</i>"]
    M2 -->|Filtered Probabilistic Map| M3["<b>Module 3</b><br/>Coordinate Middleware<br/><i>(UTM to Local Grid)</i>"]
    M3 -->|Scenario JSON / NPY| M4["<b>Module 4</b><br/>Simulation Execution<br/><i>(MTS & SAREnv)</i>"]
    M4 -->|Trajectories & Snapshots| M5["<b>Module 5</b><br/>Unified Evaluation<br/><i>(PathEvaluatorTFM)</i>"]

    style M1 fill:#f8fafc,stroke:#475569,stroke-width:1.5px
    style M2 fill:#f8fafc,stroke:#475569,stroke-width:1.5px
    style M3 fill:#f8fafc,stroke:#475569,stroke-width:1.5px
    style M4 fill:#f8fafc,stroke:#475569,stroke-width:1.5px
    style M5 fill:#f8fafc,stroke:#475569,stroke-width:1.5px
```

---

## 📦 2. Diagramas Desacoplados por Módulo

### 🔹 Módulo 1: Generación de Cartografía y Probabilidad (SAREnv)

Combina la cartografía vectorial real de OpenStreetMap con el modelo estadístico *Lost Person Behavior* (LPB - Robert Koester) y una distribución Log-Normal espacial centrada en la Última Posición Conocida (LKP).

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e2e8f0', 'primaryBorderColor': '#64748b', 'primaryTextColor': '#0f172a', 'lineColor': '#334155', 'fontSize': '13px'}}}%%
graph TD
    OSM["OpenStreetMap Vector Data<br/><i>(Casa de Campo)</i>"] --> FeatureMap["Land Cover Feature Map<br/><i>(Paths, Forests, Buildings, Water)</i>"]
    LPB["Koester LPB Manual<br/><i>(Autistic, Dementia, Hiker)</i>"] --> Weights["Profile-Specific Statistical Weights"]
    Weights --> FeatureMap
  
    LKP["Last Known Position (LKP)"] --> LogNormal["Spatial Log-Normal Distribution<br/><i>(LPB Percentiles)</i>"]
  
    FeatureMap --> Fusion["Weighted Fusion & Normalization"]
    LogNormal --> Fusion
    Fusion --> HeatmapOut["Combined Baseline Heatmap<br/><i>(.npy Matrix)</i>"]

    style FeatureMap fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style Weights fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style LogNormal fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style Fusion fill:#e2e8f0,stroke:#334155,stroke-width:2px
    style HeatmapOut fill:#f1f5f9,stroke:#0f172a,stroke-width:2px
```

---

### 🔹 Módulo 2: Filtrado de Restricciones Físicas (`Sindex`)

Utiliza indexación espacial mediante $R\text{-Tree}$ (`Sindex`) para proyectar geometrías no transitables (agua profunda y edificaciones urbanas) como restricciones duras con probabilidad $0.0$.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e2e8f0', 'primaryBorderColor': '#64748b', 'primaryTextColor': '#0f172a', 'lineColor': '#334155', 'fontSize': '13px'}}}%%
graph TD
    HeatmapIn["Combined Baseline Heatmap<br/><i>(Module 1)</i>"] --> FilterProcess["Spatial Masking Pipeline"]
  
    GISGeom["OSM Geometries<br/><i>(Deep Lakes & Buildings)</i>"] --> SindexTree["Sindex R-Tree Spatial Indexing"]
    SindexTree --> BinaryMask["2D Binary Mask<br/><i>(Water / Buildings = 0.0, Other = 1.0)</i>"]
  
    FilterProcess <--> BinaryMask
    FilterProcess --> HardConstraint["Hard Constraint Enforcement<br/><i>(Probability = 0.0)</i>"]
    HardConstraint --> Renorm["Probabilistic Matrix Renormalization"]
    Renorm --> FilteredHeatmap["Filtered Probabilistic Map<br/><i>(Normalized Matrix)</i>"]

    style SindexTree fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style BinaryMask fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style HardConstraint fill:#e2e8f0,stroke:#334155,stroke-width:2px
    style FilteredHeatmap fill:#f1f5f9,stroke:#0f172a,stroke-width:2px
```

---

### 🔹 Módulo 3: Transformación del Middleware de Coordenadas

Transforma las coordenadas métricas UTM globales ($\text{EPSG:32630}$) en la rejilla local discreta de $10\text{ m} \times 10\text{ m}$ utilizada por el simulador MTS.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e2e8f0', 'primaryBorderColor': '#64748b', 'primaryTextColor': '#0f172a', 'lineColor': '#334155', 'fontSize': '13px'}}}%%
graph TD
    FilteredHeatmap["Filtered Probabilistic Map<br/><i>(Module 2)</i>"] --> UTMCoords["Global UTM Coordinates<br/><i>(EPSG:32630 in meters)</i>"]
  
    UTMCoords --> Transform["Middleware Coordinate Transformation<br/><i>(Origin: Bottom-Left Corner)</i>"]
    Transform --> Rescale["Discretization & Rescaling<br/><b>Resolution: 10m x 10m per cell</b>"]
  
    Rescale --> ScenarioJSON["Scenario JSON / NPY Export<br/><i>(MTS & SAREnv Compatible)</i>"]

    style Transform fill:#e2e8f0,stroke:#334155,stroke-width:2px
    style Rescale fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style ScenarioJSON fill:#f1f5f9,stroke:#0f172a,stroke-width:2px
```

---

### 🔹 Módulo 4: Ejecución de Simulaciones y Marcas Temporales

Ejecuta los algoritmos bioinspirados de MTS junto con los patrones canónicos de SAREnv mientras registra marcas de tiempo o hitos temporales ($t = 0, 100, 300, 500$).

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e2e8f0', 'primaryBorderColor': '#64748b', 'primaryTextColor': '#0f172a', 'lineColor': '#334155', 'fontSize': '13px'}}}%%
graph TD
    ScenarioJSON["Scenario JSON / NPY<br/><i>(Module 3)</i>"] --> AlgMTS["MTS Bio-inspired Algorithms<br/><i>(ACO, ABC, BHA, Greedy)</i>"]
    ScenarioJSON --> AlgSAREnv["SAREnv Canonical Patterns<br/><i>(Lawnmower, Random Walk, Expanding Square)</i>"]
  
    subgraph SimExec["Parallel Execution (Seeds 0-49)"]
        AlgMTS --> SimEngine["Simulation Engine"]
        AlgSAREnv --> SimEngine
    end
  
    SimEngine --> CaptureSnapshots["Temporal Snapshot Capture<br/><i>(t = 0, 100, 300, 500)</i>"]
    CaptureSnapshots --> ExportTraj["Trajectories & Snapshots Export<br/><i>(JSON / NPY)</i>"]

    style SimEngine fill:#e2e8f0,stroke:#334155,stroke-width:2px
    style CaptureSnapshots fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style ExportTraj fill:#f1f5f9,stroke:#0f172a,stroke-width:2px
```

---

### 🔹 Módulo 5: Módulo Evaluador Unificado (`PathEvaluatorTFM`)

Calcula de forma homogénea las 5 métricas de rendimiento del benchmark y genera las gráficas de evolución temporal y las tablas comparativas.

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e2e8f0', 'primaryBorderColor': '#64748b', 'primaryTextColor': '#0f172a', 'lineColor': '#334155', 'fontSize': '13px'}}}%%
graph TD
    ExportTraj["Trajectories & Snapshots<br/><i>(Module 4)</i>"] --> Evaluator["PathEvaluatorTFM<br/><i>(Homogeneous Assessment)</i>"]
  
    Evaluator --> MetricsCalculated["Unified Metric Computation"]
  
    subgraph MetricsSet["TFM Benchmark Metrics"]
        MetricsCalculated --> SuccessRate["Success Rate (%)"]
        MetricsCalculated --> Steps["Steps to Target"]
        MetricsCalculated --> CumProb["Accumulated Probability"]
        MetricsCalculated --> AreaSwept["Covered Area (m²)"]
        MetricsCalculated --> Distance["Total Distance (m)"]
    end
  
    MetricsSet --> NotebookOutput["Notebook 3: Analisis_Resultados.ipynb"]
    NotebookOutput --> Visuals["Temporal Evolution Plots & Comparative Tables"]

    style Evaluator fill:#e2e8f0,stroke:#334155,stroke-width:2px
    style MetricsCalculated fill:#f8fafc,stroke:#64748b,stroke-width:1.5px
    style Visuals fill:#f1f5f9,stroke:#0f172a,stroke-width:2px
```

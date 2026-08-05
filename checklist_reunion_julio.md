# 📋 Checklist de Verificación TFM

---

### 1. 🚫 Restricción de Lagos y Edificios en Probabilidad Inicial

- [X] **Verificación a 0.0:** Comprobado que la probabilidad inicial en lagos y estructuras físicas está fijada estrictamente a **$0.0$**.
- [X] **Aserción Numérica:** Implementada en `utils_pipeline.py` con la función `verificar_restriccion_agua_edificios()` (`max_restricted = 0.00000000`).

---

### 2. 🗺️ Diagrama de Flujo del Sistema General (Memoria)

- [X] **Diagrama Arquitectónico Completo:** Creado en `TFM_JC/memoria/diagrama_flujo_arquitectura.md` (Mermaid) mostrando los 5 módulos:
  $$
  \text{SAREnv} \longrightarrow \text{Filtro Sindex} \longrightarrow \text{Middleware UTM-Local} \longrightarrow \text{MTS} \longrightarrow \text{PathEvaluatorTFM}
  $$
- [X] Uicación documentada para su inclusión en el Capítulo 4 de la Memoria LaTeX.

---

### 3. ⚙️ Modificar y Duplicar el Módulo PathEvaluator

- [X] **SAREnv Intocado:** `sarenv.analytics.metrics.PathEvaluator` se mantiene 100% original sin modificar una sola línea.
- [X] **Módulo Duplicado y Renombrado:** Creado `PathEvaluatorTFM` en `TFM_JC/scripts/path_evaluator_tfm.py` integrando las métricas cruzadas de MTS y SAREnv.

---

### 4. 🚀 Automatizar Lanzamiento de Pruebas Masivas

- [X] **Confirmación de Automatización:** Script `Lanzar_Simulaciones_Masivas.ipynb` listo para ejecución headless en el servidor.
- [X] **Cobertura Completa:** 900 simulaciones totales (50 semillas $\times$ 6 algoritmos $\times$ 3 perfiles LPB).

---

### 5. 📓 Estructura Modular de Notebooks

- [X] **Notebook 1 (`Benchmark_Perfiles_Real_Interactivo.ipynb`):** Pruebas básicas y dashboard interactivo ipywidgets.
- [X] **Notebook 2 (`Lanzar_Simulaciones_Masivas.ipynb`):** Pruebas masivas en lote para el servidor del laboratorio.
- [X] **Notebook 3 (`Analisis_Resultados.ipynb`):** Evaluación y análisis exclusivo. Aquí se importa `PathEvaluatorTFM`, se generan los boxplots y las métricas.

---

### 6. 📈 Evolución Temporal del Mapa de Creencias ($b(v^k)$)

- [X] **Paneles Temporales:** Renderizado de la trayectoria y huella barrida por el dron ($100\text{ m}$) en los instantes temporales $t=[0, 250, 500, 1000]$.
- [X] **Comparativa Lado a Lado:** Panel comparativo de 2 filas de algoritmos (ABC vs BHA) en el Notebook 3.

---

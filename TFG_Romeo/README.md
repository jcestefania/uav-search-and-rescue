# Trabajo de Fin de Grado: Búsqueda en tiempo mínimo en espacios con incertidumbre mediante algoritmos bioinspirados

**Autor:** Romeo Bernal Alcelay
**Supervisores:** Juan Pedro Llerena
**Universidad:** Universidad de Alcalá de Henares
**Curso:** 2025-2026
**Referencia:** [TFG_Romeo_Bernal_Alcelay.pdf](TFG_Romeo_Bernal_Alcelay.pdf)

Este repositorio contiene el código, las simulaciones y los cuadernos de análisis desarrollados en el marco del Trabajo de Fin de Grado.
El objetivo principal es evaluar la eficiencia y eficacia de algoritmos bioinspirados frente
a algoritmos tradicionales para la búsqueda con UAVs en entornos con incertidumbre mediante simulación.

---

## Resumen del proyecto

> Este proyecto aborda la búsqueda de objetivos con UAVs en espacios con incertidumbre, donde la ubicación
> exacta del objetivo no se conoce pero se dispone de información probabilística sobre ella.
> El TFG implementa y compara tres algoritmos bioinspirados: **Ant Colony Optimization (ACO)**,
> **Artificial Bee Colony (ABC)** y **Black Hole Algorithm (BHA)**, optimizando cuatro funciones objetivo
> diferentes: **Expected Time**, **Discounted Time Reward**, **Maximum Slope** y **Minimum Entropy**.
> Esto se hace con el objetivo de analizar el comportamiento de estos métodos de búsqueda bioinspirados,
> proporcionando una base para futuros desarrollos en la planificación de trayectorias de UAVs en espacios inciertos.

---

## Requisitos del sistema

Este proyecto fue desarrollado en **Python 3.10+** y requiere las siguientes librerías:

- numpy
- pandas
- plotly
- pillow
- scipy

### Montar el entorno con Conda

Para crear un entorno virtual compatible con todas las dependencias, ejecuta en terminal:

```bash
conda env create -f environment.yml
conda activate mts-uncertain-search-bio
```

---

## Cómo ejecutar las simulaciones

Puedes ejecutar las simulaciones de forma individual o automatizada.

### Desde línea de comandos

Ejecuta un algoritmo sobre un archivo de prueba específico:

```bash
python3 <algoritmo>.py pruebas/<archivo_de_prueba>.json
```

> Sustituye `<algoritmo>.py` por el nombre del algoritmo de búsqueda según el algoritmo deseado.

### Desde Jupyter Notebook

Abre el cuaderno de las pruebas básicas con:

```bash
jupyter notebook pruebas_básicas.ipynb
```

Este cuaderno permite ejecutar simulaciones de forma individual y comparar la evolución de las funciones objetivo.

Abre el cuaderno de las pruebas masivas con:

```bash
jupyter notebook pruebas_masivas.ipynb
```

Este cuaderno permite ejecutar simulaciones de forma masiva para todos los algoritmos con diferente número de indicios y diferente número de agentes
en el entorno.

---

## Algoritmos implementados

### Ant Colony Optimization (ACO)

Algoritmo inspirado en el comportamiento de las hormigas, que utilizan feromonas para encontrar caminos óptimos hacia fuentes de alimento.

### Artificial Bee Colony (ABC)

Algoritmo basado en el comportamiento de búsqueda de alimento de las abejas melíferas, con roles de abejas exploradoras, trabajadoras y observadoras.

### Black Hole Algorithm (BHA)

Algoritmo inspirado en el fenómeno astrofísico de los agujeros negros, donde las soluciones son atraídas hacia la mejor solución encontrada.

---

## Funciones objetivo

Cada algoritmo optimiza cuatro funciones objetivo diferentes adaptadas al contexto de búsqueda con UAVs, que habrá que optimizar para explorar el mapa de probabilidad:

1. **Expected Time:** Minimiza el tiempo esperado de detección del objetivo
2. **Discounted Time Reward:** Maximiza la recompensa descontada por el tiempo de búsqueda
3. **Maximum Slope:** Maximiza la pendiente de incremento de probabilidad de detección
4. **Minimum Entropy:** Minimiza la entropía de la distribución de probabilidad

---

## Casos de prueba

Los archivos `.json` dentro del directorio `pruebas/` definen distintos escenarios de simulación.

### Estructura de los archivos `.json`

Cada archivo incluye:

- Tamaño del entorno de búsqueda
- Posición y peso de los indicios
- Semilla aleatoria
- Posición inicial de los UAVs
- Parámetros de sensores
- Parámetros específicos de cada algoritmo bioinspirado
- Configuración de las funciones objetivo

> Una explicación detallada de cada parámetro en los archivos de prueba `.json` se puede
> encontrar en el script [generar-json2.py](/generar-json2.py)

### Tabla de casos de prueba

Incluye aquí una tabla o imagen de referencia.

[Tabla de pruebas (Google Sheets)](https://docs.google.com/spreadsheets/d/e/2PACX-1vRLJnhT5WI1-autzNrDDxAIw6PKOBSrm1mNe09J6y_rBDWasL869ojAjvPsbAo7jzR3MfNMmwHn6iZH/pubhtml)

---

### Cuadernos disponibles

- `analisis-resultados.ipynb`: comparación entre ACO, ABC y BHA con diferentes funciones objetivo

### Métricas evaluadas

- **Tasa de éxito (%):** porcentaje de veces que se localiza el objetivo
- **Pasos hasta detección:** media de iteraciones necesarias para encontrar el objetivo
- **Distancia recorrida:** suma total de movimiento de los UAVs

---

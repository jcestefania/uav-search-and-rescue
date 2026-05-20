# 🛰️ Trabajo de Fin de Grado:  Revisión de estrategias de búsqueda en tiempo mínimo en espacios con incertidumbre 

**Autor:** Yago Brotón Gutiérrez  
**Supervisores:** Juan Pedro Llerena y Jesús García  
**Universidad:** Universidad Carlos III de Madrid  
**Curso:** 2024-2025  
**Referencia:** [TFG_Yago_Brotón.pdf](TFG_Yago_Brotón.pdf)

Este repositorio contiene el código, las simulaciones y los cuadernos de análisis desarrollados en el marco del Trabajo de Fin de Grado.
El objetivo principal es evaluar la eficiencia y eficacia de estrategias de búsqueda en entornos con incertidumbre mediante la simualción.

---

## Resumen del proyecto

> En este proyecto se aborda la búsqueda de objetivos en espacios con incertidumbre, donde su ubicación
> exacta no se conoce pero se dispone de indicios de probabilidad sobre ella.
> El TFG revisa varias estrategias de búsqueda usando un enfoque basado en el Filtro Bayesiano Recursivo
> y el modelado por restricciones.
> Esto se hace con el objetivo de analizar el comportamiento de estos métodos de búsqueda,
> proporcionando una base para futuros desarrollos en la búsqueda de objetivos en espacios inciertos.

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

    conda env create -f environment.yml
    conda activate mts-uncertain-search

---

## Cómo ejecutar las simulaciones

Puedes ejecutar las simulaciones de forma individual o automatizada.

### Desde línea de comandos

Ejecuta un algoritmo sobre un archivo de prueba específico:

    python3 <algoritmo>.py pruebas/<archivo_de_prueba>.json

> Sustituye `<algoritmo>.py` por el nombre del script deseado.

### Desde Jupyter Notebook

Abre el cuaderno principal con:

    jupyter notebook lanzar-pruebas.ipynb

Este cuaderno permite ejecutar todas las simulaciones de forma organizada.

---

## Casos de prueba

Los archivos `.json` dentro del directorio `pruebas/` definen distintos escenarios de simulación.

### Estructura de los archivos `.json`

Cada archivo incluye:
- Tamaño del entorno
- Posición y peso de los indicios
- Semilla aleatoria 
- Posición de los agentes
- Parámetros de sensores y de los algortimos

> Una explicación de cada parámetro en los archivos de prueba `.json` se puede
encontrar en el script [generar-json.py](/generar-json.py)

### Tabla de casos de prueba

Incluye aquí una tabla o imagen de referencia.  

[Tabla de pruebas (Google Sheets)](https://docs.google.com/spreadsheets/d/e/2PACX-1vRLJnhT5WI1-autzNrDDxAIw6PKOBSrm1mNe09J6y_rBDWasL869ojAjvPsbAo7jzR3MfNMmwHn6iZH/pubhtml)

---

## Análisis de resultados

Los resultados generados se analizan con cuadernos Jupyter interactivos.

### Cuadernos disponibles

- `analisis-resultados.ipynb`: comparación general de estrategias  
- `analisis-resultados-multiagente.ipynb`: impacto del número de agentes  
- `analisis-resultados-multiindicio.ipynb`: varios indicios en simultáneo

### Métricas evaluadas

- **Tasa de éxito (%):** veces que se localiza el objetivo  
- **Pasos hasta detección:** media de iteraciones necesarias  
- **Distancia recorrida:** suma total de movimiento de los agentes  

---

## Referencias destacadas

- Tabla de pruebas: [Google Sheets](https://docs.google.com/spreadsheets/d/e/2PACX-1vRLJnhT5WI1-autzNrDDxAIw6PKOBSrm1mNe09J6y_rBDWasL869ojAjvPsbAo7jzR3MfNMmwHn6iZH/pubhtml)  

---

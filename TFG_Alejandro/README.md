# 🛰️ Trabajo de Fin de Grado: [Título del trabajo]

**Autor:** Alejandro Blanco Fernández 
**Supervisores:** Juan Pedro Llerena y Jesús García  
**Universidad:** Universidad Carlos III de Madrid  
**Curso:** 2024/2025
**Referencia:** Técnicas de búsqueda para navegación de UAVs en entornos con incertidumbre

Este repositorio contiene el código, las simulaciones y los cuadernos de análisis desarrollados en el marco del Trabajo de Fin de Grado. El objetivo principal es [describir brevemente el propósito general del proyecto: p. ej. evaluar estrategias de búsqueda eficientes en entornos con incertidumbre mediante simulación].

---

## Resumen del proyecto

> En este Trabajo de Fin de Grado se presenta un sistema de reparto de mercancías para vehículos aéreos no tripulados empleando un sistema de búsqueda de la zona de entrega que se sustenta en diferentes estrategias de búsqueda en espacios con incertidumbre. Concretamente, se presenta un caso de uso de reparto en el contexto del Campus de Colmenarejo, la Universidad Carlos III de Madrid en el que se modela la incertidumbre del espacio de búsqueda y la procedente de sistema de detección.

---

## Requisitos del sistema

Este proyecto fue desarrollado en **Python 3.9+** y requiere las siguientes librerías:

- numpy  
- pandas  
- plotly==5.23.0

### Montar el entorno con Conda

Para crear un entorno virtual compatible con todas las dependencias, ejecuta en terminal:

    conda env create -f environment.yml
    conda activate mts-uncertain-search

### NOTA: recuerda descargar e incluir el archivo `environment.yml`

Este archivo debe incluirse en el repositorio.  
Para generarlo desde un entorno activo:

    conda env export --no-builds > environment.yml

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
- Parámetros de sensores y visibilidad
- Posición de los agentes
- Semilla aleatoria (opcional)

> Se recomienda incluir un ejemplo comentado de un archivo `.json`.

### Tabla de casos de prueba

Incluye aquí una tabla o imagen de referencia.  
Ejemplo:

[Tabla de pruebas (Google Sheets)](https://...)

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
- **Cobertura:** porcentaje del entorno explorado  

---

## Referencias destacadas

Algunos de las herramientas o servicios utilizados son:

- [Cesium](https://cesium.com/) — para visualización 3D de entornos geoespaciales  
- [OpenStreetMap](https://www.openstreetmap.org/) — para mapas de entorno y rutas  

---

# Índice Detallado de la Memoria del TFM

**Título del TFM:** Optimización de Búsqueda y Rescate (SAR) con Drones mediante Algoritmos Bioinspirados en Entornos Inciertos
**Autor:** Juan Carlos Estefanía
**Tutores:** Jesús y Jompy

---

## Estructura Detallada por Capítulos

### Capítulo 1: Introducción y Objetivos

* 1.1 Contexto y Motivación de las Operaciones SAR con Drones (UAVs)
* 1.2 Planteamiento del Problema en Entornos Complejos (Casa de Campo de Madrid)
* 1.3 Objetivos del TFM
  * 1.3.1 Objetivo General
  * 1.3.2 Objetivos Específicos
* 1.4 Estructura de la Memoria

### Capítulo 2: Estado del Arte

* 2.1 Estadísticas Oficiales de Comportamiento de Desaparecidos (*Lost Person Behavior - LPB*)
* 2.2 Modelado de Incertidumbre Espacial: Enfoque Bayesiano y Generación de Heatmaps
* 2.3 Algoritmos de Cobertura y Búsqueda SAR
  * 2.3.1 Patrones Deterministas y Aleatorios (Lawnmower, Random Walk, Expanding Square)
  * 2.3.2 Algoritmos Bioinspirados e Inteligencia de Enjambre (ACO, ABC, BHA, Greedy)
* 2.4 Entornos de Simulación: SAREnv y MTS

### Capítulo 3: Modelado del Entorno y Sensor

* 3.1 Integración de Cartografía Abierta (OpenStreetMap)
* 3.2 Asignación de Pesos Estadísticos por Perfil de Víctima (Autista, Demencia, Senderista)
* 3.3 Modelo de Distancia Espacial Log-Normal
* 3.4 Modelo de Observación del Sensor del Dron (Sensor Ideal de Nivel 1)
  * 3.4.1 Geometría del Campo de Visión (FoV) y Altitud de Vuelo
  * 3.4.2 Matriz de Detección Binaria ($P=1$ en FoV, $P=0$ fuera)
  * 3.4.3 Discretización Espacial (Celda de $10\text{ m} \times 10\text{ m}$)

### Capítulo 4: Desarrollo e Integración Middleware

* 4.1 Restricciones Físicas y Filtrado con Indexación Espacial (`Sindex` R-Tree)
  * 4.1.1 Demostración de Restricción Dura ($0.0$ en Agua y Edificaciones)
* 4.2 Middleware de Transformación de Coordenadas
  * 4.2.1 Proyección UTM ($\text{EPSG:32630}$) a Rejilla Discreta Local $(X,Y)$
* 4.3 Arquitectura del Evaluador Unificado (`PathEvaluatorTFM`)

### Capítulo 5: Experimentación y Benchmarking

* 5.1 Definición de Escenarios Canónicos y Generación de Víctimas por Montecarlo
* 5.2 Configuración del Entorno Experimental Server (50 Semillas / 1000 Pasos)
* 5.3 Métricas de Evaluación Unificadas (Tasa Acierto, Pasos a Meta, Probabilidad Acumulada, Área, Distancia)

### Capítulo 6: Análisis de Resultados y Discusión

* 6.1 Análisis Comparativo por Perfil de Víctima
  * 6.1.1 Perfil Autista (Atracción por Estructuras)
  * 6.1.2 Perfil Demencia (Orientación a Bosques)
  * 6.1.3 Perfil Senderista (Recorrido de Redes Lineales)
* 6.2 Evolución Temporal de la Búsqueda (Instantes $t = 0, 100, 300, 500$)
* 6.3 Comparativa Lado a Lado de Algoritmos Bioinspirados vs. Baselines

### Capítulo 7: Conclusiones y Trabajo Futuro

* 7.1 Conclusiones Principales
* 7.2 Limitaciones del Trabajo
  * 7.2.1 Ausencia de Penalización en el Vector de Control Dinámico de Vuelo
  * 7.2.2 Asunción de Objetivos/Víctimas Estáticas
* 7.3 Líneas de Trabajo Futuro (Víctimas Dinámicas Markovianas)

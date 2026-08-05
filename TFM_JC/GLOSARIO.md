# Glosario de Algoritmos y Métricas de Búsqueda (SAREnv + MTS)

Este documento detalla la formulación teórica y el funcionamiento de los algoritmos de búsqueda y las métricas de rendimiento empleadas en el proyecto TFM para la optimización de búsquedas y rescates (SAR) con drones en la Casa de Campo.

---

## Algoritmos de Búsqueda

Los algoritmos se clasifican en dos grandes familias: **ciegos o geométricos** (que no conocen la distribución de probabilidad de la víctima) e **informados o heurísticos/bioinspirados** (que planifican su vuelo basándose en el mapa de calor).

### 1. Algoritmos Ciegos (Exhaustivos / Geométricos)

* **Lawnmower (Barrido Sistemático o Cortacésped):**

  * *Funcionamiento:* Realiza un barrido lineal paralelo de ida y vuelta barriendo la rejilla de extremo a extremo. Es el patrón estándar utilizado en la aviación civil de rescate cuando no se dispone de indicios espaciales de la víctima.
  * *Ventaja:* Garantiza cobertura uniforme del espacio a largo plazo.
  * *Desventaja:* Tarda mucho tiempo en cubrir zonas alejadas de los extremos y no prioriza zonas calientes.
* **Expanding Square (Espiral Cuadrada en Expansión):**

  * *Funcionamiento:* Inicia la búsqueda en el centro (LKP/IPP) y va describiendo una espiral concéntrica de forma cuadrada hacia el exterior, aumentando el radio de giro a cada vuelta.
  * *Ventaja:* Prioriza las zonas cercanas al punto de inicio (LKP), lo cual es coherente si se asume que la víctima no se ha desplazado muy lejos.
  * *Desventaja:* Ignora por completo la topología física y las probabilidades geográficas.

---

### 2. Algoritmos Informados (Heurísticos / Swarm Intelligence)

* **Voraz Heurístico (Greedy Search):**

  * *Funcionamiento:* En cada paso de simulación, el dron evalúa las celdas vecinas a su alcance y se desplaza hacia aquella que contenga la mayor densidad de probabilidad en el mapa de calor acumulado.
  * *Ventaja:* Comportamiento rápido y de explotación intensiva de zonas de alta probabilidad a corto plazo.
  * *Desventaja:* Muy propenso a quedarse atrapado en máximos locales (islas de calor) y dejar zonas secundarias sin explorar.
* **ACO (Ant Colony Optimization - Optimización de Colonias de Hormigas):**

  * *Funcionamiento:* Algoritmo metaheurístico bioinspirado basado en el comportamiento de las hormigas al buscar alimento. Las hormigas ficticias recorren la rejilla depositando rastros de *feromona* en los caminos que producen mejores detecciones. Las hormigas de iteraciones siguientes eligen probabilísticamente seguir los rastros de feromona o explorar nuevos caminos.
  * *Ventaja:* Excelente capacidad para encontrar rutas óptimas globales que conectan múltiples focos de calor.
  * *Desventaja:* Alto coste computacional debido a las múltiples iteraciones de las hormigas.
* **ABC (Artificial Bee Colony - Colonia de Abejas Artificiales):**

  * *Funcionamiento:* Inspirado en el comportamiento de recolección de las abejas. Divide la colonia en abejas obreras (explotan fuentes de néctar conocidas/zonas de alta probabilidad), abejas observadoras (seleccionan probabilísticamente las mejores fuentes basándose en la información de las obreras) y abejas exploradoras (buscan aleatoriamente nuevas fuentes para salir de máximos locales).
  * *Ventaja:* Gran equilibrio entre exploración (búsqueda de nuevas zonas calientes) y explotación (barrido de zonas de máxima probabilidad).
* **BHA (Black Hole Algorithm - Algoritmo del Agujero Negro):**

  * *Funcionamiento:* Algoritmo basado en fenómenos astronómicos. La mejor solución de la población (la ruta con mayor probabilidad de detección acumulada) se define como el *Agujero Negro*, y el resto de soluciones candidatas actúan como *estrellas* que son atraídas hacia él. Si una estrella cruza el horizonte de sucesos (se acerca demasiado), es absorbida y sustituida por una nueva estrella aleatoria en el espacio de búsqueda.
  * *Ventaja:* Rápida convergencia y gran dinamismo para saltar máximos locales gracias a la regeneración de estrellas absorbidas.

---

## Métricas de Evaluación Cruzada

Las trayectorias de vuelo generadas por los drones se evalúan a través de un motor de análisis unificado en SAREnv (`PathEvaluator`), calculando cuatro métricas clave:

### 1. Tasa de Acierto (Success Rate) [%]

Representa el porcentaje de víctimas que habrían sido rescatadas con éxito durante el vuelo.

* **Siembras de Montecarlo:** Se generan $1000$ víctimas ficticias aplicando restricciones físicas (no pueden aparecer en agua profunda ni edificios).
  * *Acierto Informado:* Las víctimas se distribuyen proporcionalmente al mapa de calor probabilístico (simula que la víctima sigue el comportamiento real predicho por el manual).
  * *Acierto Ciego:* Las víctimas se distribuyen uniformemente por todo el polígono de búsqueda (simula que la víctima no sigue ningún patrón y está perdida al azar).
* **Condición de detección:** Una víctima es "hallada" si entra dentro del radio de barrido del sensor del dron ($50\text{ metros}$) en cualquier instante del vuelo.

### 2. Distancia de Vuelo (Path Length) [km]

Es la longitud física acumulada de la trayectoria del dron:

$$
L = \sum_{t=1}^{T} d(\mathbf{p}_{t}, \mathbf{p}_{t-1})
$$

Donde $d(\cdot)$ es la distancia euclídea en metros entre posiciones UTM sucesivas del dron, dividida por $1000$ para expresarse en kilómetros.

* *Relevancia:* Mide la autonomía física consumida. A menor distancia para encontrar a la víctima, mayor eficiencia.

### 3. Área Barrida (Area Covered) [$km^2$]

Representa la extensión de terreno física única explorada por el sensor del dron a lo largo del vuelo.

* **Cálculo:** Se calcula aplicando un buffer circular de radio $R = 50\text{ m}$ sobre la trayectoria lineal del dron, y calculando el área de la unión poligonal resultante en metros cuadrados (evitando duplicar el área de zonas por las que el dron pasa varias veces). Se divide entre $1.000.000$ para expresarlo en kilómetros cuadrados.

### 4. Likelihood Score (Factor de Descuento Bayesiano)

Mide la cantidad de probabilidad total barrida, ponderada por el tiempo de llegada. Penaliza severamente las búsquedas lentas:

$$
LS = \sum_{t=1}^{T} \gamma^{t} \cdot P(\mathbf{s}_{t})
$$

Donde $P(\mathbf{s}_{t})$ es la probabilidad de la celda de la rejilla explorada en el instante $t$, y $\gamma = 0.999$ es el factor de descuento temporal.

* *Relevancia:* Premia a los algoritmos que barren las zonas de máxima probabilidad en los primeros instantes del vuelo (minimizando el tiempo de supervivencia de la víctima).

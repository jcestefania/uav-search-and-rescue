# 🛰️ Trabajo de Fin de Grado: [Título del trabajo]

**Autor:** Álvaro Gómez Lázaro  
**Supervisores:** Juan Pedro Llerena y Jesús García  
**Universidad:** Universidad Carlos III de Madrid  
**Curso:** 2024-2025  
**Referencia:** [TFG_Alvaro_Gomez.pdf](TFG_Alvaro_Gómez-comprimido.pdf)

Este repositorio contiene el código, las simulaciones y los cuadernos de análisis desarrollados en el marco del Trabajo de Fin de Grado. El objetivo principal es evaluar estrategias de búsqueda eficientes en entornos con incertidumbre mediante una simulación hiperrealista.

---

## Resumen del proyecto

> En este proyecto se aborda el problema de búsqueda en entornos con incertidumbre, donde el estado del objetivo no se conoce con seguridad. Para ello se porponen una serie de estrategias basadas en el Filtro Bayesiano Recursivo, que permite realizar una estimacion de la posición del objetivo en cada paso del algoritmo.
> Para la experimentación, el problema se lleva a un simulador hiperrelasta donde, con la ayuda de un dron y el sistema AirSim, se pueden diseñar escenarios de búsqueda en los cuales diseñar misiones para estudiar estas estrategias que se diseñan.
> Para asegurarnos de que los datos que se obtienen de cada simulación son aceptables para analizar las estrategias de búsqueda, es necesario realizar un estudio de la coherencia entre la planificación y la simulación, comparando las trayectorias para ver anomalías del simulador.

---

## Requisitos del sistema

Este proyecto fue desarrollado en **Python 3.9+** y requiere las siguientes librerías:

- numpy  
- pandas  
- plotly==5.23.0
- matplotlib
- pyproj
- json
- os
- math
- re
- seaborn
- scipy
- sklearn
- fastdtw

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

Para ejecutar los cuadernos será necesario haber llevado a cabo una misión anteriormente y los datos obtenidos se almacenan en la carpeta mission_data. Dependiendo de la estrategia que se haya ejecutado, en el cuaderno correspondiente se debe establecer en la parte inicial el nombre de cada uno de los archivos que se desea analizar. Una vez hecho esto se puede ejecutar de manera automatica.

Al final de cada uno de los cuadernos de estrategias se genereran dos archivos diferentes: resultados_DTW y resultado_error, los cuales sirven para el cuaderno de análisis de las estrategias en conjunto.

## Casos de prueba

Los archivos `.csv` dentro del directorio `mission_data/` recogen los resultados de cada una de las misiones ejecutadas.

### Estructura de los archivos `.csv`

Encontramos cuatro archivos diferentes:

#### gt.csv

Contiene el ground truth o información que se considera real
- time, timestamp
- x_position, coordenada norte en sistema NED
- y_position, coordenada este en sistema NED
- z_position, coordenada down en sistema NED
- x_vel, velocidad en coordenada norte
- y_vel, velocidad en coordenada este
- z_vel, velocidad en coordenada down
- state, estado en el que se encuentra el vehiculo

#### telemetry.csv

Contiene información obtenida por el propio dron
- time, timestamp
- latitud_deg, coordenada latitud en sistema global WGS84
- longitude_deg, coordenada longitud en sistema global WGS84
- absolute_altitude_m, altitud respecto al nivel del mar
- relative_altitude_m, altitud relativa respecto al suelo
- north_m_s, velocidad en coordenada norte en sistema NED
- east_m_s, velocidad en coordenada este en sistema NED
- down_m_s. velocidad en coordenada down en sistema NED
- state, estado en el que se encuentra el vehiculo

#### sensor.csv

Contiene la información que se obtiene a traves del sensor
- time, timestamp
- detected, si el sensor ha detectado el objetivo o no
- X_dist, distancia entre el sensor y el objetivo en coordenada este en sistema ENU
- Y_dist, distancia entre el sensor y el objetivo en coordenada norte en sistema ENU
- Z_dist, distancia entre el sensor y el objetivo en coordenada up en sistema ENU
- sensor_ROLL, rotación en eje longitudinal X
- sensor_PITCH, rotacion en eje transversal Y
- sensor_YAW, rotacion en eje vertical Z

#### reference.csv

Contiene la trayectoria de referencia a partir de la cual se genera toda la misión
- step, paso de la misión
- X, coordenada este en sistema ENU
- Y, coordenada norte en sistema ENU
- Z, coordenada up en sistema ENU

> Se recomienda incluir un ejemplo comentado de un archivo `.json`.

## Análisis de resultados

Los resultados generados se analizan con cuadernos Jupyter interactivos.

### Cuadernos disponibles

- `bf_expanding.ipynb`: analisis de trayectorias obtenidas en mision que utiliza la estrategia bf-expanding.  
- `bf_lawnmower.ipynb`: analisis de trayectorias obtenidas en mision que utiliza la estrategia bf-lawnmower.   
- `ldfs_heur.ipynb`: analisis de trayectorias obtenidas en mision que utiliza la estrategia ldfs-heur.
- `ldfs_miope.ipynb`: analisis de trayectorias obtenidas en mision que utiliza la estrategia ldfs-miope.
- `comparación_metodos.ipynb`: análisis de resultados obtenidos en los cuadernos anteriores, donde se puede comparar las distintas estrategias.  

### Métricas evaluadas

- **Distancia recorrida:** distancia hasta detección  
- **Tiempo de ejecución:** tiempo hasta detección
- **RMSE:** error entre trayectorias de referencia y simulación
- **DTW:** aplicado a las trayectorias de referencia y simulación

---

## Referencias destacadas

- [Cesium](https://cesium.com/) - para visualización 3D de entornos geoespaciales
- [AirSim](https://microsoft.github.io/AirSim/) - simulador para probar drones en entornos virtuales
- [QGroundControl](https://qgroundcontrol.com/) - estación de control terrestre
- [MAVLink](https://mavlink.io/en/) - protocolo de comunicación con el dron
- [MAVSDK](https://mavsdk.mavlink.io/main/en/index.html) - biblioteca para programar con MAVLink

---

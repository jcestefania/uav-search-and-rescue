# Explicación Técnica de la Integración (SAREnv + MTS)

Este documento recopila de forma estructurada y detallada todas las modificaciones, justificaciones científicas y optimizaciones implementadas para conectar los mapas reales probabilísticos de **SAREnv** con el framework de simulación **MTS**. 

Está diseñado para servir como guía de referencia rápida para tu memoria del TFM y para que puedas explicarle los cambios a tus tutores con total seguridad.

---

## 📂 Índice de Componentes Modificados
1. **Núcleo de SAREnv (`sarenv/core/generation.py`)** - *Fusión de Capas*
2. **Saneamiento del Workspace de MTS** - *Corrección de Rutas del TFM*
3. **Middleware de Conversión (`TFM_JC/scripts/generar_json_real.py`)** - *Proyección UTM y Rejilla Local*
4. **Generador del Objetivo Real (`bf-busqueda.py`)** - *Muestreo Ponderado del Heatmap*
5. **Optimización de Interfaz (`extra/interfaz.py`)** - *Submuestreo de Fotogramas y Visibilidad Z*

---

## 1. Fusión de Capas en SAREnv (`sarenv/core/generation.py`)

*   **Cambio Realizado:** Sustitución del operador `np.maximum` por una **suma ponderada y posterior normalización global** en el método `get_combined_heatmap()`. El código del operador de máximo original se ha dejado comentado en el archivo por seguridad.
*   **Justificación para los Tutores:**
    El paper original de SAREnv (*"SAREnv: An Open-Source Dataset and Benchmark Tool for Informed Wilderness Search and Rescue Using UAVs"*, pág. 14) destaca como una limitación del operador `max` el hecho de ignorar el efecto acumulativo de probabilidad cuando convergen múltiples características favorables en una misma zona (ej. la intersección de un sendero principal forestal con el borde de un lago). 
    Para solventarlo, se reformuló el método de combinación:
    1. **Suma Ponderada:**
       $$\mathbf{POA}_{\text{unnorm}}(i, j) = \sum_{k} \mathbf{M}_k(i, j) \cdot \alpha_k$$
       Donde $\mathbf{M}_k(i, j)$ representa la presencia binaria de la capa $k$ en la celda $(i, j)$ y $\alpha_k$ es su peso base de probabilidad.
    2. **Normalización:**
       $$\mathbf{POA}_{\text{norm}}(i, j) = \frac{\mathbf{POA}_{\text{unnorm}}(i, j)}{\sum \mathbf{POA}_{\text{unnorm}}}$$
    Debido a que la topología de OpenStreetMap genera capas de suelo (bosques, agua, prados) geográficamente disjuntas (no se solapan), la suma no diluye el mapa de calor; en su lugar, mantiene definidos los senderos y el agua e incrementa con realismo la probabilidad acumulada de sus intersecciones directas.

---

## 2. Saneamiento de Rutas en el Workspace de MTS

*   **Cambio Realizado:** Corrección masiva de todas las cadenas de texto que apuntaban al directorio obsoleto `TFM-JuanCarlos` para usar de forma consistente `TFM_JC` en todos los archivos de configuración (`generar_escenario_real_jc.py`, `ini-pos.py`, `generar-json.py`) y en el panel de control de simulación [experimentos_casacampo.ipynb](file:///c:/Users/juanc/Desktop/TFM/TFM-Juan%20Carlos/Software/framwork-MTS/MTS-UncertainEnvironment-Algoritmos-bioinspirados/TFM_JC/pruebas/experimentos_casacampo.ipynb).
*   **Justificación:** Garantizar la consistencia con la estructura de directorios del sistema de archivos real y evitar errores de tipo `FileNotFoundError` al ejecutar los scripts de simulación y análisis de métricas.

---

## 3. El Middleware de Conversión de Coordenadas (`generar_json_real.py`)

*   **Ubicación:** [generar_json_real.py](file:///c:/Users/juanc/Desktop/TFM/TFM-Juan%20Carlos/Software/framwork-MTS/MTS-UncertainEnvironment-Algoritmos-bioinspirados/TFM_JC/scripts/generar_json_real.py)
*   **Misión:** Leer el GeoJSON (`features.geojson`) y la matriz de probabilidad de SAREnv (`heatmap.npy`) y generar el JSON de escenario configurado para MTS con las dimensiones correctas de la rejilla local y la posición exacta de inicio del dron.
*   **Matemática de la Conversión de Coordenadas (Lat/Lon $\rightarrow$ X/Y local):**
    1. **Lectura Geográfica:** Se extrae el `center_point` `[longitud, latitud]` (que representa el LKP/IPP) y los límites geográficos `bounds` `[minx, miny, maxx, maxy]` (esquinas en metros proyectados UTM) de la metadata del GeoJSON.
    2. **Proyección UTM:** Se calcula el huso UTM de la región (para Madrid es el huso 30 Norte, EPSG:32630) y se transforma el punto de inicio `(lon, lat)` a metros proyectados `(center_x, center_y)` usando la librería `pyproj.Proj`.
    3. **Cálculo de Distancias al Origen:** Sabiendo que el origen $(0,0)$ de la rejilla de MTS corresponde a la esquina inferior izquierda del mapa (`minx`, `miny`), calculamos la distancia en metros desde el origen al LKP/IPP:
        $$dx = center\_x - minx$$
        $$dy = center\_y - miny$$
    4. **Discretización a la Rejilla:** Dividimos la distancia métrica por la resolución del mapa en metros por píxel (`meter_per_bin` o $\delta$, habitualmente $20\text{ metros}$):
        $$X_{\text{local}} = \left\lfloor \frac{dx}{\delta} \right\rfloor$$
        $$Y_{\text{local}} = \left\lfloor \frac{dy}{\delta} \right\rfloor$$
    El par resultante $(X_{\text{local}}, Y_{\text{local}})$ (ej. `[102, 110]`) es la posición discreta exacta en la matriz de MTS donde el dron debe iniciar el vuelo, representando fielmente el LKP/IPP real.

---

## 4. Generación Real de la Víctima (`bf-busqueda.py`)

*   **Cambio Realizado:** Modificación de la inicialización de la posición del objetivo (víctima) en `bf-busqueda.py` cuando se define `goal_pos = None` (Modo Aleatorio) y hay cargado un mapa real.
*   **Por qué se hizo:** El generador sintético original de MTS (`random_target`) dibujaba un recuadro uniforme en un rango muy estrecho de celdas (basado en la matriz `"cov"`) alrededor del inicio, haciendo que la víctima siempre apareciera al lado del dron.
*   **Cómo funciona el nuevo método:** Cuando se carga una simulación con mapa real (`ruta_real`), el script aplana la matriz de probabilidad de creencia y realiza un muestreo probabilístico con pesos:
    ```python
    flat_bk = bk.flatten()
    flat_idx = np.random.choice(len(flat_bk), p=flat_bk)
    y_goal, x_goal = np.unravel_index(flat_idx, bk.shape)
    goal = np.array([x_goal, y_goal], dtype=float)
    ```
    Esto garantiza que la víctima se genere de forma verdaderamente aleatoria por todo el parque de la Casa de Campo, y que la probabilidad de aparecer en cada celda sea exactamente proporcional al peso de esa celda en el mapa de calor (respetando los senderos, el lago y las áreas críticas).

---

## 5. Optimización y Visibilidad 3D en `extra/interfaz.py`

Se han introducido dos mejoras cruciales en la visualización interactiva de Plotly:

### A. Submuestreo de Fotogramas (Evitar el `RangeError` de Memoria)
*   **Problema Histórico:** Al ejecutar simulaciones largas (1000 pasos de batería), Plotly intentaba guardar 1000 matrices completas de relieve 3D. El objeto resultante pesaba cientos de megabytes y superaba el límite de tamaño de cadenas de texto en JavaScript, provocando el error `RangeError: Invalid string length` y colgando el navegador.
*   **Solución:** Se implementó una lógica de muestreo que calcula un salto dinámico si los pasos superan los 100:
    ```python
    step_skip = 1
    if steps > 100:
        step_skip = int(np.ceil(steps / 100))
    ```
    El bucle de renderizado salta fotogramas (ej. dibuja un frame cada 10 pasos si el total es 1000), limitando los fotogramas de la animación a un máximo de 100. La animación corre de forma fluida e instantánea en el navegador web sin consumir memoria en exceso.

### B. Visibilidad Dinámica de la Víctima (X roja)
*   **Problema Histórico:** La coordenada Z (altura) de la X roja de la víctima estaba fijada de manera estática a `z = 0.2` (a ras de suelo). En las zonas con relieve o picos de probabilidad altos del mapa 3D (multiplicados por el factor de escala 25), la montaña de probabilidad superaba la altura del suelo y ocultaba por completo el marcador rojo debajo de la superficie.
*   **Solución:** Se calcula la altura Z de la víctima de manera dinámica en función del valor del heatmap en esa celda específica en cada instante:
    ```python
    y_target = max(0, min(int(goal[k][1]), BK[k].shape[0] - 1))
    x_target = max(0, min(int(goal[k][0]), BK[k].shape[1] - 1))
    z_target = BK[k][y_target, x_target] * 25 + 1.5
    ```
    Esto eleva el marcador rojo $1.5$ metros por encima del relieve local de probabilidad, garantizando que flote visiblemente y nunca sea cubierto por las colinas 3D de la animación.

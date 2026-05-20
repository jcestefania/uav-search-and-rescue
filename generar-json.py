"""Archivo para generar un archivo .json con los parámetros de la simulación"""

import json
import os

dir = "TFG-Yago/pruebas/"
file_name = "grande-indicios-2-agentes-1-fixed.json"

# Comprobar primero que el archivo no existe y si existe preguntar
# antes de sobreescribirlo
file_path = os.path.join(dir, file_name)
if os.path.exists(file_path):
    res = input(
        f"El archivo {file_path} ya existe, ¿desea sobreescribirlo? (s/N): "
    )
    if res.lower() != "s":
        exit()

out_file = open(file_path, "w")

data = {
    # --- Parámetros generales de simulación ---
    "version": "1.1",
    "size": [100, 100],  # Tamaño del mapa: [x, y]
    "cov": [  # Matriz de covarianza o lista de matrices de covarianza
        [1, 0],
        [0, 1],
    ],
    "indicios": [  # Lista con las posiciones de los indicios: [x0, y0], [x1,y1]...
        [24, 20],
        [70, 75],
    ],
    "pesos": [  # Lista con los pesos asociados a cada indicio. None: se asigna el mismo peso para todos
        0.6,
        0.4,
    ],
    "obj_pos": [  # Si escogemos None escogerá una posición dentro del rango de confianza de uno de los indicios. Si no especificar posición [x, y]
        None
    ],
    "p_transicion": [  # Matriz con las probabilidades de que el objetivo se mueva en esa dirección. Direcciones de movimiento:
        [0.0, 0.0, 0.0],  # [-1, -1], [0, -1], [1, -1]
        [0.0, 1.0, 0.0],  # [-1,  0], [0,  0], [1,  0]
        [0.0, 0.0, 0.0],  # [-1,  1], [0,  1], [1,  1]
    ],
    "indicio": -1,  # Indicio alrededor del que se genera el objetivo. -1: elige uno de los indicios de forma aleatoria, N: elige el indicio con índice N, None: posición definida
    "semilla": 0,  # Semilla para la generación de números aleatorios
    "num_agents": 1,  # Número de agentes
    "height": 10,  # Altura del vuelo los drones, actualmente solo se usa en la simulación
    "init_pos": [  # Lista con la posición inicial de cada agente: [x, y], None: posición aleatoria (selecciona una posicion cerca del borde del mapa)
        [80, 40],
    ],
    "mov_delta": 1,  # Distancia de movimiento
    "posible_moves": "8 dir",  # Movimientos disponibles para el agente: "8 dir" direcciones cardinales y diagonales; "cruz" únicamente direcciones cardinales
    "min_dist": 3,  # Distancia mínima que debe haber entre los drones
    "lambda": 0.5,  # Peso de la distancia al punto de mayor en la heurística
    # Parametros del sensor
    "pdmax": 0.8,  # Probabilidad máxima de detección. Probabilidad de que el sensor lo detecte cuando se encuentra cerca
    "dmax": 2.1,  # Distancia máxima de detección
    "sigma": 0.7,  # Sensibilidad a la distancia / Factor de caida exp. Cuanto mayor sea más rápido decae la probabilidad de detección
    # Parametros necesarios solo si se busca con heurística
    "num_steps": 1200,  # Tamaño total del horizonte de búsqueda
    "itersteps": 100,  # Tamaño de los subhorizontes de búsqueda
    # Para los algoritmos de búsqueda por fuerza bruta
    "separation": 2,  # Separación entre los tramos de la trayectoria
    "plan": False,  # Hacer la planificación de la trayectoria, implica la generación del .plan y obviar el criterio de parada cuando se detecta el objetivo.
    
    # ============================================================================
    # CONFIGURACIÓN DE ALGORITMOS BIOINSPIRADOS
    # ============================================================================
    # Parámetros comunes a todos los algoritmos
    "bio_algoritmo": None,  # Algoritmo a usar: "ACO", "ABC", "BHA", None para no usar
    "funcion_objetivo": None,  # Función objetivo: ET, DTR, ME, MS (debe importarse desde extra.funciones)
    "optimization": "min",  # Modo de optimización: "min" o "max"
    "show_evolution": True,  # Mostrar y guardar evolución del algoritmo
    
    # --- ACO (Ant Colony Optimization) ---
    "n_ants": 30,  # Número de hormigas en la colonia
    "n_iterations_aco": 10,  # Número de iteraciones ACO
    "alpha": 1.0,  # Influencia del rastro de feromonas
    "beta": 3.0,  # Influencia de la heurística
    "rho": 0.1,  # Tasa de evaporación de feromonas (0-1)
    "local_rho": 0.05,  # Tasa de evaporación local de feromonas en ACO (actualización durante construcción de soluciones)
    "Q": 1.0,  # Constante de depósito de feromonas
    
    # --- ABC (Artificial Bee Colony) ---
    "n_iterations_abc": 10,  # Número de iteraciones ABC
    "limit": 10,  # Límite de intentos antes de abandonar una solución
    "n_onlookers": 1,  # Número de abejas observadoras
    "n_employed": 1,  # Número de abejas empleadas
    
    # --- BHA (Black Hole Algorithm) ---
    "n_iterations_bha": 10,  # Número de iteraciones BHA
    "n_stars": 5  # Número de estrellas (soluciones candidatas)
}

json.dump(data, out_file, indent=4)
out_file.close()

print(f"Archivo de configuración {file_path} generado con éxito")

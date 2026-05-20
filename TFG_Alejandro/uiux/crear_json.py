"""Archivo para generar un archivo .json con los parámetros de la simulación"""

import json

def data_json(map_size, grid_size, matriz_indicios, origen, coords_dron, reference_system, tam_cuadricula, target_pos, radio, coords_perimetro_global):
    
    dir = "./"
    file_name = "prueba.json"

    # Comprobar primero que el archivo no existe y si existe preguntar
    # antes de sobreescribirlo
    try:
        with open(dir + file_name, "r"):
            res = input(
                f"El archivo {dir + file_name} ya existe, ¿desea sobreescribirlo? (s/N): "
            )
            if res.lower() != "s":
                exit()
    except FileNotFoundError:
        pass
    out_file = open(dir + file_name, "w")

    data = {
        "size": grid_size,  # Tamaño del mapa: [x, y] esclado con tamaño de cuadrícula
        "size_a": map_size, # Tamaño del mapa: [x, y] real
        "cov": [
            [[3, 0], [3, 2]],
            [[2, 0], [0, 1]],
        ],  # Matriz de covarianza o lista de matrices de covarianza
        "indicios": [  # Lista con las posiciones de los indicios: [x0, y0], [x1,y1]...
            [15, 35]
        ],
        "indicio": 1,  # Indicio alrededor del que se genera el objetivo. -1: elige uno de los indicios de forma aleatoria, N: elige el indicio con índice N
        "semilla": 10,  # Semilla para la generación de números aleatorios
        "num_agents": 1,  # Número de agentes
        "height": 10,  # Altura del vuelo los drones, actualmente solo se usa en la simulación
        "init_pos": [  # Lista con la posición inicial de cada agente: [y, x], None: posición aleatoria (selecciona una posicion cerca del borde del mapa)
            coords_dron # Posición inicial del dron en función del tamaño del mapa y de la cuadrídcula (si es 700x700 y tc = 10)
        ],
        "obj_pos": [target_pos],
        "search_space_global_coords": [coords_perimetro_global],
        "mov_delta": 1,  # Distancia de movimiento
        "tam_cuadricula": tam_cuadricula,
        "posible_moves": "8 dir",  # Movimientos disponibles para el agente: "8 dir" direcciones cardinales y diagonales; "cruz" únicamente direcciones cardinales
        "min_dist": 3,  # Distancia mínima que debe haber entre los drones
        "lambda": 0.5,  # Peso de la distancia al punto de mayor en la heurística
        # Parametros del sensor
        "pdmax": 0.8,
        "dmax": 2.1,
        "sigma": 0.7,
        # Parametros necesarios solo si se busca con heurística
        "num_steps": 90,  # Tamaño total del horizonte de búsqueda
        "itersteps": 30,  # Tamaño de los subhorizontes de búsqueda
        # Para los algoritmos de búsqueda por fuerza bruta
        "separation": 2,  # Separación entre los tramos de la trayectoria
        "reference_coordinate": coords_perimetro_global[-1], # En coordenadas globales (es la esquina inferior izquierda del espacio de búsqueda)
        "reference_system": reference_system, # ENU o NED
        "radio": radio,
        "init_map": matriz_indicios # Matriz de 0s y 1s
    }

    json.dump(data, out_file, indent=4)
    print(f"Archivo de prueba {dir + file_name} generado con éxito")

"""
if __name__ == "__main__":

    dir = "pruebas/"
    file_name = "mediano-indicios-2-agentes-3.json"

    # Comprobar primero que el archivo no existe y si existe preguntar
    # antes de sobreescribirlo
    try:
        with open(dir + file_name, "r"):
            res = input(
                f"El archivo {dir + file_name} ya existe, ¿desea sobreescribirlo? (s/N): "
            )
            if res.lower() != "s":
                exit()
    except FileNotFoundError:
        pass
    out_file = open(dir + file_name, "w")

    #data = create_json()"""
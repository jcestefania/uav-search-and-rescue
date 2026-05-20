"""Búsqueda voraz (Limited Depth First Search) usando la heurística para evitar miopía"""

import json
import sys
from functools import partial

import numpy as np

from busquedas import rh_search
from busquedas.heuristicas import heur_correcion_miopia
from busquedas.rbf import rbf
from configurar import (
    calcular_prob,
    celda_mas_cercana,
    random_border_pos,
    random_target,
)
from coordinates import to_plan
from extra import crear_dataframe, dibujar_animacion, guardar_dataframe
from sensor.square_sensor import SquareSensor, SquareSensorPlan

# Comprobar si se ha pasado un archivo de configuración
if len(sys.argv) not in [2, 3]:
    print(
        f"Uso: python {sys.argv[0]} <archivo_configuracion> [generar archivo plan y/[n]]"
    )
    sys.exit(1)

# Comprobar si se genera el archivo .plan
GENERAR_PLAN = False
if len(sys.argv) == 3:
    generar = sys.argv[2]
    if generar in ["yes", "y"]:
        GENERAR_PLAN = True
    elif generar not in ["no", "n"]:
        print(
            f"Uso: python {sys.argv[0]} <archivo_configuracion> [generar archivo plan y/[n]]"
        )
        sys.exit(1)

# Leer el archivo de configuración
file = sys.argv[1]

params = json.load(open(file))
seed = params["semilla"]
np.random.seed(seed)
GENERAR_PLAN = params.get("plan", GENERAR_PLAN)

size = np.array(params["size"])
COV = np.array(params["cov"])
pesos = np.array(params.get("pesos", [None]))

indicios = np.array(params["indicios"])

# Si solo hay una covarianza, se asume que es la misma para todos los indicios
if len(COV.shape) == 2:
    COV = np.array([COV] * len(indicios))

bk = calcular_prob(size, COV, indicios, pesos)

N_AGENTS = params["num_agents"]
HEIGHT = params["height"]

init_pos = np.array(params["init_pos"])
min_dist = params["min_dist"]  # Distancia minima entre drones
border = np.ceil(np.mean(size) * 1 / 4)
agent_seed = None
# Si las posiciones iniciales son None, generarlas de forma aleatoria
if np.array_equal(init_pos, np.array([None])):
    init_pos = random_border_pos(size, N_AGENTS, min_dist, border)
    agent_seed = seed
# Comprobar que el número de agentes y posiciones iniciales coinciden
np.testing.assert_equal(
    len(init_pos), N_AGENTS, "Please, check the number of agents and initial positions"
)
# Añadir la altura a las posiciones iniciales
heights = np.array([np.repeat(HEIGHT, N_AGENTS)])
init_pos = np.concatenate((init_pos, heights.T), axis=1)

delta: float = params["mov_delta"]

# Direcciones de movimiento
match params["posible_moves"]:
    case "8 dir":
        moves = np.array(
            [
                [-delta, -delta],
                [-delta, 0],
                [-delta, delta],
                [0, -delta],
                [0, 0],
                [0, delta],
                [delta, -delta],
                [delta, 0],
                [delta, delta],
            ]
        )
    case "cruz":
        moves = np.array(
            [
                [-delta, 0],
                [0, -delta],
                [0, 0],
                [0, delta],
                [delta, 0],
            ]
        )
    case _:
        print(f"Tipo de movimiento \"{params['posible_moves']}\" no reconocido")
        exit()

lambda_ = params["lambda"]  # Peso de la distancia, para la heurística
# Configurar la heurística para la búsqueda
heur = partial(heur_correcion_miopia, dist_min=min_dist, lambda_=lambda_)

# Parametros del sensor
pdmax = params["pdmax"]
dmax = params["dmax"]
sigma = params["sigma"]

if GENERAR_PLAN:
    sensor = SquareSensorPlan(pdmax, dmax, sigma)
else:
    sensor = SquareSensor(pdmax, dmax, sigma)

indicio_elegido = params["indicio"]
goal = params["obj_pos"]
goal_seed = None
if indicio_elegido == None:
    # Comprobar que la posición para el objetivo no es None también
    np.testing.assert_raises(
        AssertionError,
        np.testing.assert_array_equal,
        np.array(indicio_elegido),
        np.array(goal),
        err_msg="El indicio elegido y la posición inicial del objetivo no pueden ser nulos al mismo tiempo",
    )


if indicio_elegido == -1:
    indicio_elegido = np.random.randint(0, len(indicios))

if goal == [None]:
    goal = random_target(indicios, COV, indicio_elegido, 3)
    goal_seed = seed
goal = celda_mas_cercana(goal, bk)

obj_estatico = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])

transicion = np.array(params.get("p_transicion", obj_estatico))
filtro = partial(rbf, p_transicion=transicion, sensor=sensor)

# Variables para la búsqueda
finder = None
total_steps = params["num_steps"]

# Inicializar listas para guardar los caminos
list_x = [np.array(pos[0]) for pos in init_pos]
list_y = [np.array(pos[1]) for pos in init_pos]
list_z = [np.array(pos[2]) for pos in init_pos]
BK = [bk]

new_list_x, new_list_y, new_list_z, steps, finder, new_bk, list_target = rh_search(
    size,
    init_pos,
    N_AGENTS,
    moves,
    goal,
    heur,
    filtro,
    bk,
    total_steps,
)

for i in range(N_AGENTS):
    list_x[i] = np.append(list_x[i], new_list_x[i])
    list_y[i] = np.append(list_y[i], new_list_y[i])
    list_z[i] = np.append(list_z[i], new_list_z[i])

BK += new_bk
steps = len(BK)  # Ajustar al nuevo tamaño de la lista

df = crear_dataframe(
    N_AGENTS, list_x, list_y, list_z, list_target, finder, agent_seed, goal_seed
)
guardar_dataframe(
    df, "TFG-Yago/resultados/", "ldfs-heur", file.split("/")[-1].split(".")[0]
)

dibujar_animacion(
    N_AGENTS,
    list_x,
    list_y,
    list_z,
    BK,
    list_target,
    size,
    steps,
    seed,
    sensor.perimetro,
    height=HEIGHT,
)

# Generar archvo .plan
if GENERAR_PLAN:
    latitude_0, longitude_0 = [40.543595, -4.012085]
    altitude_0 = 0.0  # 880 m
    to_plan(list_x, list_y, list_z, altitude_0, latitude_0, longitude_0, "plan")

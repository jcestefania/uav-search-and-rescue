"""
Archivo unificado para todos los algoritmos de búsqueda:
- Fuerza Bruta: expanding_sq, lawnmower
- Búsqueda Voraz: voraz-heur, voraz-myope
- Bioinspirados: ACO, ABC, BHA
"""

import json
import sys
import numpy as np
from functools import partial

from busquedas.rbf import rbf
from configurar import calcular_prob, celda_mas_cercana, random_pos, random_border_pos, random_target
from coordinates import to_plan
from extra import crear_dataframe, dibujar_animacion, guardar_dataframe
from sensor.square_sensor import SquareSensor, SquareSensorPlan
from busquedas import expanding_sq, lawnmower, rh_search
from busquedas.heuristicas import heur_correcion_miopia
from busquedas.aco import aco_search
from busquedas.abc import abc_search
from busquedas.bha import bha_search
from extra.funciones import ET, DTR, MS, ME


def _ensure_ndarray(arr):
    """Asegura que arr sea un ndarray con al menos 1 dimensión"""
    arr = np.array(arr)
    return arr.reshape(1) if arr.ndim == 0 else arr


def seleccionar_funcion_objetivo(nombre):
    """Retorna la función objetivo según el nombre"""
    return {"ET": ET, "DTR": DTR, "MS": MS, "ME": ME}.get(nombre)


def crear_movimientos(tipo, delta):
    """Crea el array de movimientos posibles según el tipo"""
    movimientos = {
        "8 dir": [[-delta, -delta], [-delta, 0], [-delta, delta],
                  [0, -delta], [0, delta],
                  [delta, -delta], [delta, 0], [delta, delta]],
        "cruz": [[-delta, 0], [0, -delta], [0, delta], [delta, 0]]
    }
    if tipo not in movimientos:
        raise ValueError(f"Tipo de movimiento '{tipo}' no reconocido")
    return np.array(movimientos[tipo])


def inicializar_listas_agentes(init_pos):
    """Inicializa las listas de posiciones x, y, z para cada agente"""
    return (
        [np.array([pos[0]]) for pos in init_pos],
        [np.array([pos[1]]) for pos in init_pos],
        [np.array([pos[2]]) for pos in init_pos]
    )


def preparar_posiciones_iniciales(init_pos, N_AGENTS, HEIGHT, size, min_dist=None, border=None, seed=None):
    """Genera y prepara las posiciones iniciales de los agentes"""
    agent_seed = None
    
    if np.array_equal(init_pos, np.array([None])):
        if min_dist is not None and border is not None:
            init_pos = random_border_pos(size, N_AGENTS, min_dist, border)
        else:
            init_pos = random_pos(size, N_AGENTS)
        agent_seed = seed
    
    np.testing.assert_equal(len(init_pos), N_AGENTS, 
                           "Por favor, verifica el número de agentes y posiciones iniciales")
    
    init_pos = np.concatenate((init_pos, np.ones((N_AGENTS, 1)) * HEIGHT), axis=1)
    return init_pos, agent_seed


def sincronizar_list_target(list_target, list_x):
    """Sincroniza list_target con la longitud de las trayectorias"""
    T_total = len(list_x[0])
    while len(list_target) < T_total:
        list_target.append(list_target[-1])
    return list_target[:T_total]


def actualizar_trayectorias(list_x, list_y, list_z, new_x, new_y, new_z, N_AGENTS):
    """Actualiza las trayectorias de todos los agentes"""
    new_x = _ensure_ndarray(new_x)
    new_y = _ensure_ndarray(new_y)
    new_z = _ensure_ndarray(new_z)
    
    for i in range(N_AGENTS):
        list_x[i] = np.concatenate((list_x[i], new_x[i] if new_x.ndim == 2 else new_x))
        list_y[i] = np.concatenate((list_y[i], new_y[i] if new_y.ndim == 2 else new_y))
        list_z[i] = np.concatenate((list_z[i], new_z[i] if new_z.ndim == 2 else new_z))


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

if len(sys.argv) not in [2, 3]:
    print(f"Uso: python {sys.argv[0]} <config> [generar plan y/n]")
    sys.exit(1)

GENERAR_PLAN = sys.argv[2].lower() in ["yes", "y"] if len(sys.argv) == 3 else False

# Cargar configuración
params = json.load(open(sys.argv[1]))

# ------------------------------------------------------------
# PARÁMETROS COMUNES
# ------------------------------------------------------------
seed = params["semilla"]
np.random.seed(seed)

GENERAR_PLAN = params.get("plan", GENERAR_PLAN)
size = np.array(params["size"])
COV = np.array(params["cov"])
pesos = np.array(params.get("pesos", [None]))
indicios = np.array(params["indicios"])

if len(COV.shape) == 2:
    COV = np.array([COV] * len(indicios))

bk = calcular_prob(size, COV, indicios, pesos)

# Configuración agentes
N_AGENTS = params["num_agents"]
HEIGHT = params["height"]
init_pos = np.array(params["init_pos"])
delta = params["mov_delta"]
total_steps = params["num_steps"]

# Sensor
pdmax, dmax, sigma = params["pdmax"], params["dmax"], params["sigma"]
sensor = SquareSensorPlan(pdmax, dmax, sigma) if GENERAR_PLAN else SquareSensor(pdmax, dmax, sigma)

# Objetivo
indicio_elegido = params["indicio"]
goal = params["obj_pos"]
goal_seed = None

if indicio_elegido is None:
    np.testing.assert_raises(AssertionError, np.testing.assert_array_equal,
                            np.array(indicio_elegido), np.array(goal),
                            err_msg="El indicio y la posición del objetivo no pueden ser nulos simultáneamente")

if indicio_elegido == -1:
    indicio_elegido = np.random.randint(0, len(indicios))

if goal == [None]:
    goal = random_target(indicios, COV, indicio_elegido, 3)
    goal_seed = seed

goal = celda_mas_cercana(goal, bk)

# Filtro bayesiano
obj_estatico = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])
transicion = np.array(params.get("p_transicion", obj_estatico))
filtro = partial(rbf, p_transicion=transicion, sensor=sensor)

# ------------------------------------------------------------
# SELECCIÓN Y EJECUCIÓN DEL ALGORITMO
# ------------------------------------------------------------
algoritmo = params["algoritmo_busqueda"]
list_target = []
df_alg = None

match algoritmo:
    case "expanding_sq":
        init_pos, agent_seed = preparar_posiciones_iniciales(init_pos, N_AGENTS, HEIGHT, size, seed=seed)
        elegido = np.random.randint(N_AGENTS)
        
        list_x, list_y, list_z = inicializar_listas_agentes(init_pos)
        BK = [bk]
        
        new_list_x, new_list_y, new_list_z, steps, finder, bk_list, list_target = expanding_sq(
            size, bk, goal, filtro, init_pos[elegido], delta, params["separation"], total_steps
        )
        
        for i in range(N_AGENTS):
            list_x[i] = np.append(list_x[i], new_list_x)
            list_y[i] = np.append(list_y[i], new_list_y)
            list_z[i] = np.append(list_z[i], new_list_z)
        
        BK += bk_list
        nombre_alg = "expanding"
    
    case "lawnmower":
        init_pos, agent_seed = preparar_posiciones_iniciales(init_pos, N_AGENTS, HEIGHT, size, seed=seed)
        elegido = np.random.randint(N_AGENTS)
        
        list_x, list_y, list_z = inicializar_listas_agentes(init_pos)
        BK = [bk]
        
        new_list_x, new_list_y, new_list_z, steps, finder, bk_list, list_target = lawnmower(
            size, bk, goal, filtro, dmax, init_pos[elegido], delta, params["separation"], total_steps
        )
        
        for i in range(N_AGENTS):
            list_x[i] = np.append(list_x[i], new_list_x)
            list_y[i] = np.append(list_y[i], new_list_y)
            list_z[i] = np.append(list_z[i], new_list_z)
        
        BK += bk_list
        nombre_alg = "lawnmower"
    
    case "voraz-heur" | "voraz-myope":
        min_dist = params["min_dist"]
        border = int(np.ceil(np.mean(size) / 4))
        init_pos, agent_seed = preparar_posiciones_iniciales(init_pos, N_AGENTS, HEIGHT, size, min_dist, border, seed)
        
        moves = crear_movimientos(params["posible_moves"], delta)
        heur = partial(heur_correcion_miopia, dist_min=min_dist, lambda_=params["lambda"])
        
        list_x, list_y, list_z = inicializar_listas_agentes(init_pos)
        BK = [bk]
        
        new_list_x, new_list_y, new_list_z, steps, finder, new_bk, list_target = rh_search(
            size, init_pos, N_AGENTS, moves, goal, heur, filtro, bk, total_steps
        )
        
        for i in range(N_AGENTS):
            list_x[i] = np.append(list_x[i], new_list_x[i])
            list_y[i] = np.append(list_y[i], new_list_y[i])
            list_z[i] = np.append(list_z[i], new_list_z[i])
        
        BK += new_bk
        nombre_alg = algoritmo
    
    case "ACO":
        min_dist = params["min_dist"]
        border = int(np.ceil(np.mean(size) / 4))
        init_pos, agent_seed = preparar_posiciones_iniciales(init_pos, N_AGENTS, HEIGHT, size, min_dist, border, seed)
        
        moves = crear_movimientos(params["posible_moves"], delta)
        heur = partial(heur_correcion_miopia, dist_min=min_dist, lambda_=params["lambda"])
        funcion_objetivo = seleccionar_funcion_objetivo(params["funcion_objetivo"])
        
        if funcion_objetivo is None:
            raise ValueError("Función objetivo inválida")
        
        list_x, list_y, list_z = inicializar_listas_agentes(init_pos)
        BK = [bk]
        
        new_list_x, new_list_y, new_list_z, steps, finder, new_bk, list_target, df_alg = aco_search(
            grid_size=size,
            bk=bk,
            target=goal,
            heur=heur,
            filter=filtro,
            dmax=params["dmax"],
            init_pos=init_pos,
            moves=moves,
            n_agents=N_AGENTS,
            separation=params["min_dist"],
            max_steps=params["num_steps"],
            funcion_objetivo=funcion_objetivo,
            show_evolution=params["show_evolution"],
            eps=params.get("eps", 1e-12),
            iterations=params["n_iterations_aco"],
            alpha=params["alpha"],
            beta=params["beta"],
            rho=params["rho"],
            Q=params["Q"],
            local_rho=params["local_rho"]
        )
        
        nombre_alg = f"bf_aco_{params['funcion_objetivo']}"
        actualizar_trayectorias(list_x, list_y, list_z, new_list_x, new_list_y, new_list_z, N_AGENTS)
        BK += new_bk if isinstance(new_bk, list) else [new_bk]
        list_target = sincronizar_list_target(list_target, list_x)
    
    case "ABC":
        min_dist = params["min_dist"]
        border = int(np.ceil(np.mean(size) / 4))
        init_pos, agent_seed = preparar_posiciones_iniciales(init_pos, N_AGENTS, HEIGHT, size, min_dist, border, seed)
        
        moves = crear_movimientos(params["posible_moves"], delta)
        heur = partial(heur_correcion_miopia, dist_min=min_dist, lambda_=params["lambda"])
        funcion_objetivo = seleccionar_funcion_objetivo(params["funcion_objetivo"])
        
        if funcion_objetivo is None:
            raise ValueError("Función objetivo inválida")
        
        list_x, list_y, list_z = inicializar_listas_agentes(init_pos)
        BK = [bk]
        
        new_list_x, new_list_y, new_list_z, steps, finder, new_bk, list_target, df_alg = abc_search(
            grid_size=size,
            bk=bk,
            target=goal,
            heur=heur,
            filter=filtro,
            dmax=params["dmax"],
            init_pos=init_pos,
            moves=moves,
            n_agents=N_AGENTS,
            separation=params["min_dist"],
            max_steps=params["num_steps"],
            funcion_objetivo=funcion_objetivo,
            show_evolution=params["show_evolution"],
            eps=params.get("eps", 1e-12),
            iterations=params["n_iterations_abc"],
            n_employed=params["n_employed"],
            n_onlooker=params["n_onlookers"],
            limit=params["limit"]
        )
        
        nombre_alg = f"bf_abc_{params['funcion_objetivo']}"
        actualizar_trayectorias(list_x, list_y, list_z, new_list_x, new_list_y, new_list_z, N_AGENTS)
        BK += new_bk if isinstance(new_bk, list) else [new_bk]
        list_target = sincronizar_list_target(list_target, list_x)
    
    case "BHA":
        min_dist = params["min_dist"]
        border = int(np.ceil(np.mean(size) / 4))
        init_pos, agent_seed = preparar_posiciones_iniciales(init_pos, N_AGENTS, HEIGHT, size, min_dist, border, seed)
        
        moves = crear_movimientos(params["posible_moves"], delta)
        heur = partial(heur_correcion_miopia, dist_min=min_dist, lambda_=params["lambda"])
        funcion_objetivo = seleccionar_funcion_objetivo(params["funcion_objetivo"])
        
        if funcion_objetivo is None:
            raise ValueError("Función objetivo inválida")
        
        list_x, list_y, list_z = inicializar_listas_agentes(init_pos)
        BK = [bk]
        
        new_list_x, new_list_y, new_list_z, steps, finder, new_bk, list_target, df_alg = bha_search(
            grid_size=size,
            bk=bk,
            target=goal,
            heur=heur,
            filter=filtro,
            dmax=params["dmax"],
            init_pos=init_pos,
            moves=moves,
            n_agents=N_AGENTS,
            separation=params["min_dist"],
            max_steps=params["num_steps"],
            funcion_objetivo=funcion_objetivo,
            show_evolution=params["show_evolution"],
            eps=params.get("eps", 1e-12),
            n_stars=params["n_stars"],
            iterations=params["n_iterations_bha"]
        )
        
        nombre_alg = f"bf_bha_{params['funcion_objetivo']}"
        actualizar_trayectorias(list_x, list_y, list_z, new_list_x, new_list_y, new_list_z, N_AGENTS)
        BK += new_bk if isinstance(new_bk, list) else [new_bk]
        list_target = sincronizar_list_target(list_target, list_x)
    
    case _:
        raise ValueError(
            f"algoritmo_busqueda '{algoritmo}' no reconocido. "
            "Opciones: expanding_sq, lawnmower, voraz-heur, voraz-myope, ACO, ABC, BHA"
        )

steps = len(BK)

# ------------------------------------------------------------
# GUARDAR RESULTADOS Y VISUALIZACIÓN
# ------------------------------------------------------------
df = crear_dataframe(N_AGENTS, list_x, list_y, list_z, list_target, finder, agent_seed, goal_seed)
guardar_dataframe(df, "resultados/", nombre_alg, sys.argv[1].split("/")[-1].split(".")[0])

"""
dibujar_animacion(N_AGENTS, list_x, list_y, list_z, BK, list_target, size, steps, 
                  seed, sensor.perimetro, height=HEIGHT)
"""

if GENERAR_PLAN:
    to_plan(list_x, list_y, list_z, 0.0, 40.543595, -4.012085, "plan")


print("OK")

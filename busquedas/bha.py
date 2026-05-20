import numpy as np
import pandas as pd
from datetime import datetime
import os

# ===================================
# BHA MULTI-UAV (con random_seed)
# ===================================
def bha_search(
    grid_size,
    bk,
    target,
    heur,
    filter,
    dmax,
    init_pos,
    moves,
    n_agents=1,
    separation=1,
    max_steps=100,
    funcion_objetivo=None,
    show_evolution=False,
    iterations=50,
    n_stars=20,
    eps=1e-12,
    w_star=1.0,
    w_heur=0.4,
    random_seed=None
):
    """
    Algoritmo Black Hole Algorithm (BHA) aplicado a búsqueda Multi-UAV.
    Las "estrellas" representan soluciones que son atraídas hacia el "agujero negro"
    (la mejor solución encontrada). Las estrellas dentro del horizonte de eventos
    son reinicializadas aleatoriamente.

    Parámetros
    ----------
    grid_size : 
        Tamaño de la cuadrícula de búsqueda
    bk : 
        Mapa de creencias inicial (probabilidades sobre la localización del objetivo)
    target : 
        Posición real del objetivo (solo para simulación / evaluación)
    heur : 
        Heurística η(bk, next, current, agents) que guía la selección de movimientos
    filter : 
        Función que actualiza el mapa de creencias al mover un agente
        Devuelve (bk_actualizado, nueva_pos_obj, encontrado_bool)
    dmax : 
        Distancia máxima de detección (puede usarse dentro de `filter`)
    init_pos : 
        Posiciones iniciales de los agentes
    moves : 
        Movimientos permitidos desde cada celda
    n_agents : 
        Número de UAVs simultáneos por trayectoria
    separation : 
        Distancia mínima deseada entre agentes (no fuertemente aplicada aquí; placeholder)
    max_steps : 
        Límite de pasos por trayectoria (horizonte)
    funcion_objetivo : 
        Calcula la calidad de una trayectoria (ET, DTR, etc.)
        Debe aceptar la representación de la trayectoria y devolver el valor objetivo
    show_evolution : 
        Si True, intenta mostrar la evolución con una utilidad externa y guarda archivo
    iterations : 
        Número de iteraciones BHA
    n_stars : 
        Número de estrellas (soluciones candidatas)
    eps : 
        Epsilon para evitar divisiones por cero
    w_star : 
        Peso de la influencia de la estrella en la selección de movimientos
    w_heur : 
        Peso de la heurística en la selección de movimientos
    random_seed : 
        Semilla para reproducibilidad. Si es None, usa tiempo actual

    Retorna
    -------
    best_tracks_x, best_tracks_y, best_tracks_z : 
        Trayectorias (x,y,z) de la mejor solución encontrada (una lista por agente)
    best_steps : 
        Número de pasos de la mejor solución
    best_finder : 
        Índice del agente que encontró el objetivo (si aplica)
    best_BK : 
        Secuencia de mapas de creencia de la mejor solución
    best_target_pos : 
        Posiciones estimadas del objetivo a lo largo del tiempo (de la mejor solución)
    df_evolution : 
        Registro de evolución por iteración con "Mejor Obj" y "Obj Actual"
    """
    # =============================
    # INICIALIZACIÓN RANDOM SEED
    # =============================
    if random_seed is not None:
        np.random.seed(random_seed)
    else:
        np.random.seed(int(datetime.now().timestamp() * 1e6) % (2**32))

    rows, cols = grid_size
    n_moves = len(moves)

    _, mode, FO_name = funcion_objetivo([], bk.copy(), filter=filter, target=target)

    # Inicializar estrellas
    stars = []
    fitness_values = []
    for _ in range(n_stars):
        star = np.random.uniform(0.5, 2.0, (rows, cols, n_moves))
        stars.append(star)
        fitness_values.append(float('inf') if mode == "min" else float('-inf'))

    black_hole_idx = 0
    best_obj = float('inf') if mode == "min" else float('-inf')
    best_tracks_x = None
    best_tracks_y = None
    best_tracks_z = None
    best_steps = 0
    best_finder = None
    best_BK = []
    best_target_pos = [target]
    evolution_data = []

    # =============================
    # BUCLE PRINCIPAL BHA
    # =============================
    for it in range(iterations):
        for i in range(n_stars):

            tracks_x, tracks_y, tracks_z, steps_iter, finder_iter, BK_iter, target_pos_iter, found = \
                construct_trajectory_simultaneous(
                    stars[i], init_pos, bk, target, moves, grid_size,
                    max_steps, n_agents, heur, filter,
                    w_star=w_star, w_heur=w_heur, eps=eps
                )

            obj_value = evaluate_trajectory(
                tracks_x, tracks_y, bk, target, filter, funcion_objetivo, mode, n_agents
            )
            fitness_values[i] = obj_value

            if is_better_solution(obj_value, best_obj, mode):
                best_obj = obj_value
                black_hole_idx = i
                best_tracks_x = [t.copy() for t in tracks_x]
                best_tracks_y = [t.copy() for t in tracks_y]
                best_tracks_z = [t.copy() for t in tracks_z]
                best_steps = steps_iter
                best_finder = finder_iter
                best_BK = BK_iter.copy()
                best_target_pos = target_pos_iter.copy()

        # ====================================
        # MOVIMIENTO DE ESTRELLAS HACIA EL AGUJERO NEGRO
        # ====================================
        black_hole = stars[black_hole_idx].copy()
        event_horizon_radius = calculate_event_horizon(fitness_values, black_hole_idx, mode)

        for i in range(n_stars):
            if i == black_hole_idx:
                continue
            rand_factor = np.random.uniform(0, 1, stars[i].shape)
            stars[i] = stars[i] + rand_factor * (black_hole - stars[i])
            stars[i] = np.clip(stars[i], 0.1, 3.0)

        # ====================================
        # REINICIALIZACIÓN DE ESTRELLAS ABSORBIDAS
        # ====================================
        for i in range(n_stars):
            if i == black_hole_idx:
                continue

            distance = calculate_distance(stars[i], stars[black_hole_idx])
            if distance < event_horizon_radius:
                stars[i] = np.random.uniform(0.5, 2.0, (rows, cols, n_moves))

        current_best = min(fitness_values) if mode == "min" else max(fitness_values)
        evolution_data.append({
            "Iteración": it + 1,
            "Mejor Obj": best_obj,
            "Obj Actual": current_best
        })

    # =============================
    # GENERAR DATAFRAME EVOLUCIÓN
    # =============================
    df_evolution = pd.DataFrame(evolution_data)

    save_path = "TFG_Romeo\\resultados\\funciones_obj"
    os.makedirs(save_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"BHA_evolution_{mode}_agents{n_agents}_iter{iterations}_FO{FO_name}_{timestamp}.csv"
    filepath = os.path.join(save_path, filename)

    with open(filepath, 'w') as f:
        f.write(f"# BHA Multi-UAV Evolution Results\n")
        f.write(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Mode: {mode}\n")
        f.write(f"# Agents: {n_agents}\n")
        f.write(f"# Stars: {n_stars}\n")
        f.write(f"# Iterations: {iterations}\n")
        f.write(f"# Random Seed: {random_seed}\n")
        f.write(f"# Best Objective: {best_obj}\n")
        f.write(f"# Grid Size: {grid_size}\n")
        f.write("#\n")

    df_evolution.to_csv(filepath, mode='a', index=False)
    print(f"Evolución guardada en: {filepath}")

    if show_evolution:
        try:
            from extra.plot_evolution import plot_evolution
            plot_evolution(df_evolution, optimization=mode, title=f"BHA Evolution ({mode})")
        except ImportError:
            print("plot_utils no disponible")

    if best_tracks_x is None:
        best_tracks_x = [np.array([]) for _ in range(n_agents)]
        best_tracks_y = [np.array([]) for _ in range(n_agents)]
        best_tracks_z = [np.array([]) for _ in range(n_agents)]

    return (
        best_tracks_x,
        best_tracks_y,
        best_tracks_z,
        best_steps,
        best_finder,
        best_BK,
        best_target_pos,
        df_evolution
    )


# ============================================================
# RESTO DE FUNCIONES (construct_trajectory_simultaneous, etc.)
# ============================================================

def construct_trajectory_simultaneous(star, init_pos, bk, target, moves, grid_size,
                                     max_steps, n_agents, heur, filter,
                                     w_star=1.0, w_heur=0.3, eps=1e-12):

    found = False
    finder = None
    steps = 0

    curr = np.array(init_pos, dtype=float)
    if curr.ndim == 1:
        curr = curr.reshape(1, -1)
    if curr.shape[1] == 2:
        curr = np.hstack([curr, np.ones((curr.shape[0], 1)) * 10])
    curr = curr.copy()

    bk_iter = bk.copy().astype(float)
    s = bk_iter.sum()
    if s > 0:
        bk_iter /= s

    list_track_x = [np.empty(1) for _ in range(n_agents)]
    list_track_y = [np.empty(1) for _ in range(n_agents)]
    list_track_z = [np.empty(1) for _ in range(n_agents)]

    BK = []
    target_pos = [target]

    while not found and steps < max_steps:

        next_positions = []
        for agent in range(n_agents):

            ax, ay = int(curr[agent, 0]), int(curr[agent, 1])

            dirs = np.random.permutation(len(moves))
            fs = np.column_stack([
                curr[agent, 0] + moves[dirs, 0],
                curr[agent, 1] + moves[dirs, 1],
                np.ones(len(moves)) * curr[agent, 2],
            ])

            mask = (
                (fs[:, 0] >= 0) & (fs[:, 0] < grid_size[0]) &
                (fs[:, 1] >= 0) & (fs[:, 1] < grid_size[1])
            )
            fs = fs[mask]
            dirs_valid = dirs[mask]

            if len(fs) == 0:
                next_positions.append(curr[agent].copy())
                continue

            eta_vals = heur(bk=bk_iter, next=fs, current=curr[agent], agents=curr)
            eta_vals = np.maximum(eta_vals, eps)

            star_vals = np.array([star[ax, ay, m] for m in dirs_valid])

            eta_norm = eta_vals / (eta_vals.sum() + eps)
            star_norm = star_vals / (star_vals.sum() + eps)

            combined = (star_norm ** w_star) * (eta_norm ** w_heur)
            prob = combined / (combined.sum() + eps)

            best_idx = np.random.choice(len(fs), p=prob)
            next_positions.append(fs[best_idx])

        for agent in range(n_agents):
            curr[agent] = next_positions[agent]
            list_track_x[agent] = np.append(list_track_x[agent], curr[agent, 0])
            list_track_y[agent] = np.append(list_track_y[agent], curr[agent, 1])
            list_track_z[agent] = np.append(list_track_z[agent], curr[agent, 2])

        for agent in range(n_agents):
            bk_iter, new_target, agent_found = filter(
                bk=bk_iter, pos_agente=(curr[agent, 0:2]), pos_obj=target_pos[-1]
            )
            if agent_found and not found:
                finder = agent
                found = True

        if len(BK) == steps:
            BK.append(bk_iter)
            target_pos.append(new_target)
        else:
            BK[steps] = bk_iter

        steps += 1

    list_track_x = [np.delete(t, 0) for t in list_track_x]
    list_track_y = [np.delete(t, 0) for t in list_track_y]
    list_track_z = [np.delete(t, 0) for t in list_track_z]

    return list_track_x, list_track_y, list_track_z, steps, finder, BK, target_pos, found


def evaluate_trajectory(tracks_x, tracks_y, bk, target, filter, funcion_objetivo, mode, n_agents):
    trayectoria_eval = []
    max_len = max(len(t) for t in tracks_x) if any(len(t) > 0 for t in tracks_x) else 0
    
    for step_idx in range(max_len):
        for agent in range(n_agents):
            if step_idx < len(tracks_x[agent]):
                trayectoria_eval.append((
                    int(tracks_x[agent][step_idx]),
                    int(tracks_y[agent][step_idx])
                ))

    if funcion_objetivo is None:
        return len(trayectoria_eval)

    try:
        result = funcion_objetivo(trayectoria_eval, bk.copy(), filter=filter, target=target)
        obj, _, _ = result
        return obj
    except:
        return float('inf') if mode == "min" else float('-inf')


# Helpers
def calculate_event_horizon(fitness, idx, mode):
    best = fitness[idx]
    if mode == "min":
        return abs(best) / (sum(fitness) + 1e-9)
    else:
        return abs(best) / (sum(fitness) + 1e-9)

def calculate_distance(a, b):
    return np.linalg.norm(a - b)

def is_better_solution(val, best, mode):
    return (mode == "min" and val < best) or (mode == "max" and val > best)
import numpy as np
import pandas as pd
from datetime import datetime
import os
# ===================================
# ABC MULTI-UAV - VERSIÓN MEJORADA CON DIVERSIDAD
# ===================================
def abc_search(
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
    n_employed=10,
    n_onlooker=10,
    limit=5,
    eps=1e-12,
    random_seed=None,
    exploration_rate=0.15,
    temperature=0.5
):
    """
    Algoritmo Artificial Bee Colony (ABC) aplicado a búsqueda Multi-UAV.
    Cada "abeja" representa una solución (food source) que guía la construcción
    de trayectorias para n_agents (UAVs). Se usa una representación local de
    "calidad" por celda y movimiento (food_sources) análoga a la feromona.

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
        Número de iteraciones ABC (ciclos employed/onlooker/scout)
    n_employed : 
        Número de food sources / abeja empleada
    n_onlooker : 
        Número de abeja observadora por iteración
    limit : 
        Límite de intentos sin mejorar tras el cual una food source se re-inicializa (scout)
    eps : 
        Epsilon para evitar divisiones por cero
    random_seed : 
        Semilla para reproducibilidad. Si es None, usa tiempo actual
    exploration_rate : 
        Probabilidad de hacer movimientos completamente aleatorios (0.0-1.0)
    temperature : 
        Parámetro para suavizar probabilidades (mayor = más determinista)

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
    # === INICIALIZACIÓN DE ALEATORIEDAD ===
    if random_seed is not None:
        np.random.seed(random_seed)
    else:
        # Generar semilla basada en tiempo para máxima aleatoriedad
        np.random.seed(int(datetime.now().timestamp() * 1000000) % (2**32))
    
    rows, cols = grid_size
    n_moves = len(moves)

    _, mode, FO_name = funcion_objetivo([], bk.copy(), filter=filter, target=target)

    # Food sources: para cada food source tenemos una matriz (rows, cols, n_moves)
    # que asigna una "calidad" (preferencia) por moverse desde cada celda en cada acción.
    food_sources = []
    fitness_values = []
    trial_counters = np.zeros(n_employed, dtype=int)

    # === INICIALIZACIÓN CON MAYOR DIVERSIDAD ===
    for i in range(n_employed):
        # Cada food source tiene un rango diferente para mayor diversidad
        min_val = np.random.uniform(0.01, 0.5)
        max_val = np.random.uniform(2.0, 10.0)
        food_source = np.random.uniform(min_val, max_val, (rows, cols, n_moves))
        food_sources.append(food_source)
        fitness_values.append(float('inf') if mode == "min" else float('-inf'))

    # Variables para almacenar la mejor solución global encontrada
    best_obj = float('inf') if mode == "min" else float('-inf')
    best_tracks_x = None
    best_tracks_y = None
    best_tracks_z = None
    best_steps = 0
    best_finder = None
    best_BK = []
    best_target_pos = [target]

    evolution_data = []

    # === CICLO PRINCIPAL ABC ===
    for it in range(iterations):
        # Temperatura adaptativa: más exploración al inicio, más explotación al final
        current_temperature = temperature * (1 + 2 * (iterations - it) / iterations)
        current_exploration = exploration_rate * (iterations - it) / iterations

        # === FASE 1: EMPLOYED BEES ===
        for i in range(n_employed):
            # Construir trayectoria guiada por la food_source actual
            tracks_x, tracks_y, tracks_z, steps_iter, finder_iter, BK_iter, target_pos_iter, found = \
                construct_trajectory_simultaneous(
                    food_sources[i], init_pos, bk, target, moves, grid_size,
                    max_steps, n_agents, heur, filter, eps,
                    exploration_rate=current_exploration,
                    temperature=current_temperature
                )

            # Evaluar la trayectoria generada
            obj_value = evaluate_trajectory(
                tracks_x, tracks_y, bk, target, filter, funcion_objetivo, mode, n_agents
            )

            # Generar vecino (perturbación tipo ABC)
            neighbor_food = generate_neighbor_food_source(
                food_sources[i], food_sources, i, rows, cols, n_moves
            )

            # Construir trayectoria con el vecino y evaluar
            tracks_x_new, tracks_y_new, tracks_z_new, steps_new, finder_new, BK_new, target_pos_new, found_new = \
                construct_trajectory_simultaneous(
                    neighbor_food, init_pos, bk, target, moves, grid_size,
                    max_steps, n_agents, heur, filter, eps,
                    exploration_rate=current_exploration,
                    temperature=current_temperature
                )

            obj_value_new = evaluate_trajectory(
                tracks_x_new, tracks_y_new, bk, target, filter, funcion_objetivo, mode, n_agents
            )

            # Selección golosa: si el vecino es mejor, lo reemplaza
            if is_better_solution(obj_value_new, fitness_values[i], mode):
                food_sources[i] = neighbor_food
                fitness_values[i] = obj_value_new
                trial_counters[i] = 0

                # Actualizar la mejor global si procede
                if is_better_solution(obj_value_new, best_obj, mode):
                    best_obj = obj_value_new
                    best_tracks_x = [t.copy() for t in tracks_x_new]
                    best_tracks_y = [t.copy() for t in tracks_y_new]
                    best_tracks_z = [t.copy() for t in tracks_z_new]
                    best_steps = steps_new
                    best_finder = finder_new
                    best_BK = BK_new.copy()
                    best_target_pos = target_pos_new.copy()
            else:
                # No mejoró: incrementar contador de trials para este food source
                trial_counters[i] += 1

                # Si era la primera evaluación (fitness todavía infinito/-inf), guardamos el resultado
                if fitness_values[i] == (float('inf') if mode == "min" else float('-inf')):
                    fitness_values[i] = obj_value
                    if is_better_solution(obj_value, best_obj, mode):
                        best_obj = obj_value
                        best_tracks_x = [t.copy() for t in tracks_x]
                        best_tracks_y = [t.copy() for t in tracks_y]
                        best_tracks_z = [t.copy() for t in tracks_z]
                        best_steps = steps_iter
                        best_finder = finder_iter
                        best_BK = BK_iter.copy()
                        best_target_pos = target_pos_iter.copy()

        # === FASE 2: ONLOOKER BEES ===
        probabilities = calculate_selection_probabilities(fitness_values, mode)

        for _ in range(n_onlooker):
            # Selección por ruleta
            selected_idx = np.random.choice(n_employed, p=probabilities)

            # Generar vecino y evaluarlo
            neighbor_food = generate_neighbor_food_source(
                food_sources[selected_idx], food_sources, selected_idx, rows, cols, n_moves
            )

            tracks_x_new, tracks_y_new, tracks_z_new, steps_new, finder_new, BK_new, target_pos_new, found_new = \
                construct_trajectory_simultaneous(
                    neighbor_food, init_pos, bk, target, moves, grid_size,
                    max_steps, n_agents, heur, filter, eps,
                    exploration_rate=current_exploration,
                    temperature=current_temperature
                )

            obj_value_new = evaluate_trajectory(
                tracks_x_new, tracks_y_new, bk, target, filter, funcion_objetivo, mode, n_agents
            )

            # Si mejora, reemplaza la food source seleccionada
            if is_better_solution(obj_value_new, fitness_values[selected_idx], mode):
                food_sources[selected_idx] = neighbor_food
                fitness_values[selected_idx] = obj_value_new
                trial_counters[selected_idx] = 0

                if is_better_solution(obj_value_new, best_obj, mode):
                    best_obj = obj_value_new
                    best_tracks_x = [t.copy() for t in tracks_x_new]
                    best_tracks_y = [t.copy() for t in tracks_y_new]
                    best_tracks_z = [t.copy() for t in tracks_z_new]
                    best_steps = steps_new
                    best_finder = finder_new
                    best_BK = BK_new.copy()
                    best_target_pos = target_pos_new.copy()
            else:
                trial_counters[selected_idx] += 1

        # === FASE 3: SCOUT BEES ===
        for i in range(n_employed):
            if trial_counters[i] >= limit:
                # Nueva food source aleatoria con diversidad
                min_val = np.random.uniform(0.01, 0.5)
                max_val = np.random.uniform(2.0, 10.0)
                food_sources[i] = np.random.uniform(min_val, max_val, (rows, cols, n_moves))
                trial_counters[i] = 0
                
                # Re-evaluar la nueva food source
                tracks_x, tracks_y, tracks_z, steps_iter, finder_iter, BK_iter, target_pos_iter, found = \
                    construct_trajectory_simultaneous(
                        food_sources[i], init_pos, bk, target, moves, grid_size,
                        max_steps, n_agents, heur, filter, eps,
                        exploration_rate=current_exploration,
                        temperature=current_temperature
                    )
                fitness_values[i] = evaluate_trajectory(
                    tracks_x, tracks_y, bk, target, filter, funcion_objetivo, mode, n_agents
                )

        # Guardar métricas de evolución
        current_best = min(fitness_values) if mode == "min" else max(fitness_values)
        evolution_data.append({
            "Iteración": it + 1,
            "Mejor Obj": best_obj,
            "Obj Actual": current_best
        })

    df_evolution = pd.DataFrame(evolution_data)

    # === GUARDAR RESULTADOS ===
    save_path = "TFG_Romeo\\resultados\\funciones_obj"

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ABC_evolution_{mode}_agents{n_agents}_iter{iterations}_FO{FO_name}_{timestamp}.csv"
    filepath = os.path.join(save_path, filename)

    with open(filepath, 'w') as f:
        f.write(f"# ABC Multi-UAV Evolution Results\n")
        f.write(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Mode: {mode}\n")
        f.write(f"# Agents: {n_agents}\n")
        f.write(f"# Iterations: {iterations}\n")
        f.write(f"# Employed Bees: {n_employed}\n")
        f.write(f"# Onlooker Bees: {n_onlooker}\n")
        f.write(f"# Limit: {limit}\n")
        f.write(f"# Exploration Rate: {exploration_rate}\n")
        f.write(f"# Temperature: {temperature}\n")
        f.write(f"# Random Seed: {random_seed}\n")
        f.write(f"# Best Objective: {best_obj}\n")
        f.write(f"# Grid Size: {grid_size}\n")
        f.write("#\n")

    df_evolution.to_csv(filepath, mode='a', index=False)
    print(f"Evolución guardada en: {filepath}")

    if show_evolution:
        try:
            from extra.plot_evolution import plot_evolution
            plot_evolution(df_evolution, optimization=mode, title=f"ABC Evolution ({mode})")
        except ImportError:
            print("plot_utils no disponible, omitiendo gráfica de evolución")

    # Asegurar que retornamos listas vacías si no hay solución
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


# === FUNCIONES AUXILIARES ===

def construct_trajectory_simultaneous(food_source, init_pos, bk, target, moves, grid_size,
                                     max_steps, n_agents, heur, filter, eps,
                                     exploration_rate=0.15, temperature=0.5):
    """
    Construye una trayectoria para n_agents usando un food_source como guía.
    Los agentes deciden sus movimientos SIMULTÁNEAMENTE.
    
    Parámetros adicionales
    ----------------------
    exploration_rate : float
        Probabilidad de hacer un movimiento completamente aleatorio (0.0-1.0)
    temperature : float
        Parámetro para suavizar probabilidades. Valores más altos = más determinista.
        Valores más bajos = más aleatorio.
    """
    found = False
    finder = None
    steps = 0

    # Asegurar formato de posiciones iniciales: (n_agents, 3)
    curr = np.array(init_pos, dtype=float)
    if curr.ndim == 1:
        curr = curr.reshape(1, -1)
    if curr.shape[1] == 2:
        z_col = np.ones((curr.shape[0], 1)) * 10
        curr = np.hstack([curr, z_col])
    curr = curr.copy()

    # Normalizar bk local
    bk_iter = bk.copy().astype(float)
    s = bk_iter.sum()
    if s > 0:
        bk_iter /= s

    # Inicializar contenedores de trayectoria
    list_track_x = [np.empty(1) for _ in range(n_agents)]
    list_track_y = [np.empty(1) for _ in range(n_agents)]
    list_track_z = [np.empty(1) for _ in range(n_agents)]

    BK = []
    target_pos = [target]

    # Bucle de construcción
    while not found and steps < max_steps:
        # === FASE 1: TODOS LOS AGENTES DECIDEN SU MOVIMIENTO ===
        next_positions = []
        
        for agent in range(n_agents):
            ax, ay = int(curr[agent, 0]), int(curr[agent, 1])

            # Generar sucesores válidos
            dirs = np.random.permutation(len(moves))
            fs = np.column_stack([
                curr[agent, 0] + moves[dirs, 0],
                curr[agent, 1] + moves[dirs, 1],
                np.ones(len(moves)) * curr[agent, 2],
            ])

            # Filtrar fuera de límites
            mask = (
                (fs[:, 0] >= 0) & (fs[:, 0] < grid_size[0]) &
                (fs[:, 1] >= 0) & (fs[:, 1] < grid_size[1])
            )
            fs = fs[mask]
            dirs_valid = dirs[mask]

            if len(fs) == 0:
                # Sin movimientos válidos -> quedarse en el sitio
                next_positions.append(curr[agent].copy())
                continue

            # === EXPLORACIÓN ALEATORIA ===
            if np.random.random() < exploration_rate:
                # Movimiento completamente aleatorio para diversidad
                best_idx = np.random.randint(len(fs))
                next_positions.append(fs[best_idx])
                continue

            # Calcular heurística considerando TODAS las posiciones actuales
            eta_vals = heur(bk=bk_iter, next=fs, current=curr[agent], agents=curr)
            eta_vals = np.maximum(eta_vals, eps)

            # Obtener valores de food_source
            food_vals = np.array([food_source[ax, ay, m] for m in dirs_valid])

            # === CALCULAR PROBABILIDADES CON TEMPERATURA ===
            numerator = food_vals * eta_vals
            
            # Aplicar temperatura para suavizar/agudizar distribución
            if temperature > 0:
                numerator = np.power(numerator, 1.0 / temperature)
            
            total = numerator.sum()
            if total > eps:
                prob = numerator / total
            else:
                prob = np.ones(len(fs)) / len(fs)

            # Selección estocástica
            best_idx = np.random.choice(len(fs), p=prob)
            next_positions.append(fs[best_idx])

        # === FASE 2: TODOS LOS AGENTES SE MUEVEN SIMULTÁNEAMENTE ===
        for agent in range(n_agents):
            curr[agent] = next_positions[agent]

            # Guardar trayectoria
            list_track_x[agent] = np.append(list_track_x[agent], curr[agent, 0])
            list_track_y[agent] = np.append(list_track_y[agent], curr[agent, 1])
            list_track_z[agent] = np.append(list_track_z[agent], curr[agent, 2])

        # === FASE 3: ACTUALIZAR MAPA DE CREENCIAS CON TODAS LAS OBSERVACIONES ===
        new_target = target_pos[-1]
        for agent in range(n_agents):
            bk_iter, new_target, agent_found = filter(
                bk=bk_iter, pos_agente=(curr[agent, 0:2]), pos_obj=target_pos[-1]
            )

            if agent_found and not found:
                finder = agent
                found = True

        # Guardar estado después de que TODOS se hayan movido
        if len(BK) == steps:
            BK.append(bk_iter)
            target_pos.append(new_target)
        else:
            BK[steps] = bk_iter

        steps += 1

    # Eliminar primer elemento vacío
    list_track_x = [np.delete(t, 0) for t in list_track_x]
    list_track_y = [np.delete(t, 0) for t in list_track_y]
    list_track_z = [np.delete(t, 0) for t in list_track_z]

    return list_track_x, list_track_y, list_track_z, steps, finder, BK, target_pos, found


def generate_neighbor_food_source(food_source, all_food_sources, current_idx, rows, cols, n_moves):
    """
    Genera un vecino de `food_source` usando la fórmula clásica ABC:
        x_new = x_old + phi * (x_old - x_partner)
    """
    neighbor = food_source.copy()

    partners = [i for i in range(len(all_food_sources)) if i != current_idx]
    if len(partners) > 0:
        partner_idx = np.random.choice(partners)
        partner = all_food_sources[partner_idx]

        # phi aleatorio en [-1,1] para cada dimensión
        phi = np.random.uniform(-1, 1, (rows, cols, n_moves))
        
        # Aplicar perturbación en un subconjunto de dimensiones (30-50%)
        mask_prob = np.random.uniform(0.3, 0.5)
        mask = np.random.random((rows, cols, n_moves)) < mask_prob

        neighbor[mask] = food_source[mask] + phi[mask] * (food_source[mask] - partner[mask])
        
        # Mantener valores en rango razonable
        neighbor = np.clip(neighbor, 0.1, 10.0)

    return neighbor


def evaluate_trajectory(tracks_x, tracks_y, bk, target, filter, funcion_objetivo, mode, n_agents):
    """
    Evalúa la calidad de una trayectoria construida.
    """
    trayectoria_eval = []
    max_len = max(len(t) for t in tracks_x) if any(len(t) > 0 for t in tracks_x) else 0

    for step_idx in range(max_len):
        for agent in range(n_agents):
            if step_idx < len(tracks_x[agent]):
                trayectoria_eval.append((
                    int(tracks_x[agent][step_idx]),
                    int(tracks_y[agent][step_idx])
                ))

    if funcion_objetivo is not None and trayectoria_eval:
        try:
            result = funcion_objetivo(trayectoria_eval, bk.copy(), filter=filter, target=target)
            obj_value, _, _ = result
        except Exception:
            obj_value = len(trayectoria_eval) if mode == "min" else 0
    else:
        obj_value = len(trayectoria_eval) if mode == "min" else -len(trayectoria_eval)

    return obj_value


def calculate_selection_probabilities(fitness_values, mode):
    """
    Convierte un vector de fitness en probabilidades para selección por ruleta.
    """
    fitness_array = np.array(fitness_values, dtype=float)

    valid_mask = np.isfinite(fitness_array)
    if not valid_mask.any():
        return np.ones(len(fitness_values)) / len(fitness_values)

    if mode == "min":
        max_fit = fitness_array[valid_mask].max()
        adjusted_fitness = np.where(valid_mask, max_fit - fitness_array + 1.0, 0.0)
    else:
        min_fit = fitness_array[valid_mask].min()
        adjusted_fitness = np.where(valid_mask, fitness_array - min_fit + 1.0, 0.0)

    total = adjusted_fitness.sum()
    if total > 0:
        probabilities = adjusted_fitness / total
    else:
        probabilities = np.ones(len(fitness_values)) / len(fitness_values)

    return probabilities


def is_better_solution(new_obj, current_obj, mode):
    """Comprueba si new_obj es mejor que current_obj según el modo de optimización."""
    if mode == "min":
        return new_obj < current_obj
    else:
        return new_obj > current_obj
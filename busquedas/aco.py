import numpy as np
import pandas as pd
from datetime import datetime
import os

# ===================================
# ACO MULTI-UAV
# ===================================

"""
Ant Colony Optimization (ACO) para búsqueda Multi-UAV con feromona 2D.
Implementa ACO con Sistema de Feromona de Colonia de Hormigas Max-Min (MMAS)
para optimizar trayectorias de múltiples UAVs en búsqueda de objetivos.

Basado en: S. P. Carabaza, Multi-UAS minimum time search in dynamic and uncertain environments. Springer Nature, 2021.
"""
def aco_search(
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
    alpha=1.0,
    beta=2.0,
    rho=0.1,
    Q=1.0,
    local_rho=0.05,
    eps=1e-12,
    tau_min=0.01,
    tau_max=10.0,
    random_seed=None
):
    """
    Parámetros de entrada:
    ----------
    grid_size : 
        Dimensiones del mapa de búsqueda (filas, columnas)
    bk : 
        Mapa de creencias inicial (distribución de probabilidad del objetivo)
    target : 
        Posición real del objetivo en el mapa
    heur : 
        Función heurística para calcular deseabilidad de movimientos
        Firma: heur(bk, next, current, agents) -> valor heurístico
    filter : 
        Función de actualización bayesiana del mapa de creencias
        Firma: filter(bk, pos_agente, pos_obj) -> (bk_updated, new_target, found)
    dmax : 
        Distancia máxima de detección (no usado actualmente, para compatibilidad)
    init_pos : 
        Posiciones iniciales de los agentes
    moves : 
        Matriz de movimientos posibles
        Ejemplo: [[0,1], [1,0], [0,-1], [-1,0]] para movimientos cardinales
    
    n_agents : 
        Número de UAVs/agentes en la búsqueda
    separation : 
        Separación mínima entre agentes (no implementado actualmente)
    max_steps : 
        Número máximo de pasos por iteración antes de terminar
    funcion_objetivo : 
        Función para evaluar calidad de trayectorias (ET, DTR, ME, MS)
        Si None, usa número de pasos como métrica
    show_evolution : 
        Si True, guarda y visualiza la evolución del algoritmo
    
    iterations : 
        Número de iteraciones ACO (generaciones de hormigas)
    alpha : 
        Peso de la feromona en la probabilidad de selección (τ^α)
    beta : 
        Peso de la heurística en la probabilidad de selección (η^β)
    rho : 
        Tasa de evaporación global de feromona (0 < rho < 1)
        Mayor rho = más olvido de soluciones pasadas
    Q : 
        Constante para calcular cantidad de feromona depositada
    local_rho : 
        Tasa de evaporación local durante construcción de trayectoria
    eps : 
        Valor mínimo para evitar divisiones por cero
    tau_min : 
        Límite inferior de feromona (MMAS)
    tau_max : 
        Límite superior de feromona (MMAS)
    random_seed : 
        Semilla para reproducibilidad de resultados aleatorios.
        Si None, usa timestamp actual para máxima aleatoriedad.
    
    Salida:
    -------
    best_tracks_x : 
        Coordenadas X de las trayectorias óptimas de cada agente
    best_tracks_y : 
        Coordenadas Y de las trayectorias óptimas de cada agente
    best_tracks_z : 
        Coordenadas Z (altitud) de las trayectorias óptimas de cada agente
    best_steps : 
        Número de pasos de la mejor solución encontrada
    best_finder : 
        Índice del agente que encontró el objetivo (None si no se encontró)
    best_BK : 
        Evolución del mapa de creencias en la mejor solución
    best_target_pos : 
        Evolución de la posición del objetivo (para objetivos móviles)
    df_evolution : 
        DataFrame con evolución del algoritmo por iteración
        Columnas: ["Iteración", "Mejor Obj", "Obj Actual"]
    """
    # ===================================
    # INICIALIZACIÓN DE ALEATORIEDAD
    # ===================================
    if random_seed is not None:
        np.random.seed(random_seed)
    else:
        # Generar semilla basada en tiempo para máxima aleatoriedad
        np.random.seed(int(datetime.now().timestamp() * 1000000) % (2**32))

    rows, cols = grid_size

    _, mode, FO_name = funcion_objetivo([], bk.copy(), filter=filter, target=target)

    # MEJORA 1: Feromona 2D (por celda, no por movimiento)
    pheromone = np.random.uniform(tau_min, tau_max, (rows, cols))

    # Mejor solución global
    best_obj = float('inf') if mode == "min" else float('-inf')
    best_tracks_x = None
    best_tracks_y = None
    best_tracks_z = None
    best_steps = 0
    best_finder = None
    best_BK = []
    best_target_pos = [target]
    best_path = None  # Guardar celdas visitadas de la MEJOR solución

    evolution_data = []

    # ===================================
    # BUCLE PRINCIPAL ACO
    # ===================================
    for it in range(iterations):
        # === FASE 1: Construcción de trayectorias ===
        found = False
        finder_iter = None
        steps_iter = 0

        # Inicializar posiciones de agentes
        curr = np.array(init_pos, dtype=float)
        if curr.ndim == 1:
            curr = curr.reshape(1, -1)
        if curr.shape[1] == 2:
            z_col = np.ones((curr.shape[0], 1)) * 10
            curr = np.hstack([curr, z_col])
        curr = curr.copy()

        # Inicializar mapa de creencias de la iteración
        bk_iter = bk.copy().astype(float)
        s = bk_iter.sum()
        if s > 0:
            bk_iter /= s

        # Listas para trayectorias de cada agente
        list_track_x = [np.empty(1) for _ in range(n_agents)]
        list_track_y = [np.empty(1) for _ in range(n_agents)]
        list_track_z = [np.empty(1) for _ in range(n_agents)]

        # MEJORA 2: Guardar celdas visitadas en ORDEN para depósito de feromona
        visited_cells = []

        BK_iter = []
        target_pos_iter = [target]

        # Construcción de trayectoria paso a paso
        while not found and steps_iter < max_steps:
            for agent in range(n_agents):
                agent_pos = curr[agent]
                ax, ay = int(curr[agent, 0]), int(curr[agent, 1])
                az = curr[agent, 2]
                
                # Generar sucesores en orden aleatorio
                dirs = np.random.permutation(len(moves))
                fs = np.column_stack([
                    curr[agent, 0] + moves[dirs, 0],
                    curr[agent, 1] + moves[dirs, 1],
                    np.ones(len(moves)) * curr[agent, 2],
                ])
                
                # Filtrar sucesores dentro del mapa
                mask = (
                    (fs[:, 0] >= 0) &
                    (fs[:, 0] < grid_size[0]) &
                    (fs[:, 1] >= 0) &
                    (fs[:, 1] < grid_size[1])
                )
                fs = fs[mask]
                
                if len(fs) == 0:
                    continue
                
                # Calcular heurística
                eta_vals = heur(bk=bk_iter, next=fs, current=agent_pos, agents=curr)
                eta_vals = np.maximum(eta_vals, eps)
                
                # MEJORA 3: Leer feromona 2D directamente de celdas destino
                tau_vals = np.array([
                    pheromone[int(f[0]), int(f[1])] for f in fs
                ])
                
                # Probabilidades ACO: p = (tau^alpha * eta^beta) / sum
                numerator = (tau_vals ** alpha) * (eta_vals ** beta)
                total = numerator.sum()
                if total > eps:
                    prob = numerator / total
                else:
                    prob = np.ones(len(fs)) / len(fs)
                
                # Selección del mejor movimiento
                best_idx = np.random.choice(len(fs), p=prob)

                curr[agent] = fs[best_idx]
                nx, ny = int(curr[agent, 0]), int(curr[agent, 1])
                
                # MEJORA 4: Evaporación local en celda destino (no en origen)
                pheromone[nx, ny] *= (1 - local_rho)
                pheromone[nx, ny] = max(pheromone[nx, ny], tau_min)
                
                # Guardar celda visitada
                visited_cells.append((nx, ny))

                # Guardar trayectoria del agente
                list_track_x[agent] = np.append(list_track_x[agent], curr[agent, 0])
                list_track_y[agent] = np.append(list_track_y[agent], curr[agent, 1])
                list_track_z[agent] = np.append(list_track_z[agent], curr[agent, 2])

                # Actualizar mapa de creencias (filtro Bayesiano)
                bk_iter, new_target, agent_found = filter(
                    bk=bk_iter, pos_agente=(curr[agent, 0:2]), pos_obj=target_pos_iter[-1]
                )
                if len(BK_iter) == steps_iter:
                    BK_iter.append(bk_iter if os.environ.get("MTS_SAVE_BK_HISTORY", "True") != "False" else None)
                    target_pos_iter.append(new_target)
                else:
                    BK_iter[steps_iter] = bk_iter if os.environ.get("MTS_SAVE_BK_HISTORY", "True") != "False" else None

                # Verificar si encontró el objetivo
                if agent_found and not found:
                    finder_iter = agent
                    found = True

            steps_iter += 1

        # Eliminar el primer elemento vacío de las trayectorias
        list_track_x = [np.delete(t, 0) for t in list_track_x]
        list_track_y = [np.delete(t, 0) for t in list_track_y]
        list_track_z = [np.delete(t, 0) for t in list_track_z]
        
        # === FASE 2: Evaluar solución con función objetivo ===
        if funcion_objetivo is not None:
            # Construir trayectoria completa intercalando agentes
            trayectoria_eval = []
            max_len = max(len(t) for t in list_track_x) if any(len(t) > 0 for t in list_track_x) else 0
            
            for step_idx in range(max_len):
                for agent in range(n_agents):
                    if step_idx < len(list_track_x[agent]):
                        trayectoria_eval.append((
                            int(list_track_x[agent][step_idx]),
                            int(list_track_y[agent][step_idx])
                        ))
            
            # Evaluar con la función objetivo (ET, DTR, ME, MS)
            if trayectoria_eval:
                try:
                    result = funcion_objetivo(trayectoria_eval, bk.copy(), filter=filter, target=target)
                    obj_value, _, _ = result

                except Exception as e:
                    print(f"Error evaluando función objetivo en iteración {it}: {e}")
                    obj_value = float('inf') if mode == "min" else float('-inf')
            else:
                obj_value = float('inf') if mode == "min" else float('-inf')
        else:
            # Sin función objetivo: usar número de pasos
            obj_value = steps_iter if mode == "min" else -steps_iter

        # === FASE 3: Actualizar mejor solución ===
        is_better = (mode == "min" and obj_value < best_obj) or \
                    (mode == "max" and obj_value > best_obj)

        if is_better:
            best_obj = obj_value
            best_tracks_x = [t.copy() for t in list_track_x]
            best_tracks_y = [t.copy() for t in list_track_y]
            best_tracks_z = [t.copy() for t in list_track_z]
            best_steps = steps_iter
            best_finder = finder_iter
            best_BK = BK_iter.copy()
            best_target_pos = target_pos_iter.copy()
            best_path = visited_cells.copy()  # MEJORA 5: Guardar path de mejor solución

        evolution_data.append({
            "Iteración": it + 1, 
            "Mejor Obj": best_obj,
            "Obj Actual": obj_value
        })

        # === FASE 4: Actualización de feromona ===
        # Evaporación global
        pheromone *= (1 - rho)

        # MEJORA 6: Depositar SOLO en la mejor solución histórica (no en la actual)
        if best_path is not None and abs(best_obj) > eps:
            delta = Q / abs(best_obj) if mode == "min" else Q * abs(best_obj)
            
            # Depositar en todas las celdas de la mejor trayectoria
            for (x, y) in best_path:
                if 0 <= x < rows and 0 <= y < cols:
                    pheromone[x, y] += delta

        # Límites MMAS (Max-Min Ant System)
        pheromone = np.clip(pheromone, tau_min, tau_max)

    # ===================================
    # POST-PROCESAMIENTO Y SALIDA
    # ===================================
    # DataFrame de evolución
    df_evolution = pd.DataFrame(evolution_data)

    # Mostrar y guardar evolución si se solicita
    
    save_path = "TFG_Romeo\\resultados\\funciones_obj"
    os.makedirs(save_path, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ACO_evolution_{mode}_agents{n_agents}_iter{iterations}_FO{FO_name}_{timestamp}.csv"
    filepath = os.path.join(save_path, filename)

    with open(filepath, 'w') as f:
        f.write(f"# ACO Multi-UAV Evolution Results\n")
        f.write(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Mode: {mode}\n")
        f.write(f"# Agents: {n_agents}\n")
        f.write(f"# Iterations: {iterations}\n")
        f.write(f"# Alpha: {alpha}\n")
        f.write(f"# Beta: {beta}\n")
        f.write(f"# Rho: {rho}\n")
        f.write(f"# Random Seed: {random_seed}\n")
        f.write(f"# Best Objective: {best_obj}\n")
        f.write(f"# Grid Size: {grid_size}\n")
        f.write("#\n")

    df_evolution.to_csv(filepath, mode='a', index=False)
    print(f"Evolución guardada en: {filepath}")

    if show_evolution:
        try:
            from extra.plot_evolution import plot_evolution
            plot_evolution(df_evolution, optimization=mode, title=f"ACO Evolution ({mode})")
        except ImportError:
            print("plot_utils no disponible, omitiendo gráfica de evolución")


    # Retornar en formato compatible
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
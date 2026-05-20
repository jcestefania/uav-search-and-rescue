# Archivo con los distintos algoritmos de busqueda

import numpy as np


def rh_search(
    grid_size, init_pos, n_agents, moves, target, heur, filter, bk, horizon=100
):
    """
    Calcula la trayectoria de un agente realizando una búsqueda voraz permitiendo
    Parametros:
        grid_size: tamaño del mapa
        init_pos: posición inicial del agente
        n_agents: número de agentes
        moves: lista con los movimientos posibles (arriba, abajo, izquierda, derecha, diagonal,...)
        target: coordenadas del objetivo
        heur: heurística para la búsqueda
        filter: filtro para actualizar la creencia
        bk: mapa de probabilidad inicial
        horizon: número máximo de pasos
    Devuelve:
        track_x, track_y, track_z: trayectorias del agente
        steps: número de pasos realizados
        finder: agente que encontró el objetivo (None si no se encontró)
        BK: lista con los mapas de probabilidad
        target_pos: lista con las posiciones del objetivo
    """
    found = False
    finder = None
    steps = 0
    curr = init_pos.copy()

    # Listas para guardar las posiciones de los drones
    list_track_x = [np.empty(1) for _ in range(n_agents)]
    list_track_y = [np.empty(1) for _ in range(n_agents)]
    list_track_z = [np.empty(1) for _ in range(n_agents)]

    # Listas para guardar los mapas de probabilidad y movimiento del objetivo
    BK = []
    target_pos = [target]

    while not found and steps < horizon:
        for agent, agent_pos in enumerate(curr):
            # Generar sucesores en orden aleatorio
            dirs = np.random.permutation(len(moves))
            fs = np.column_stack(
                [
                    curr[agent, 0] + moves[dirs, 0],
                    curr[agent, 1] + moves[dirs, 1],
                    np.ones(len(moves)) * curr[agent, 2],
                ]
            )
            # Filtrar los sucesores que estén dentro del mapa
            mask = (
                (fs[:, 0] >= 0)
                & (fs[:, 0] < grid_size[0])
                & (fs[:, 1] >= 0)
                & (fs[:, 1] < grid_size[1])
            )
            fs = fs[mask]
            info = heur(bk=bk, next=fs, current=agent_pos, agents=curr)
            best = np.argmax(info)
            curr[agent] = fs[best]

            # Guardar trayectoria
            list_track_x[agent] = np.append(list_track_x[agent], curr[agent, 0])
            list_track_y[agent] = np.append(list_track_y[agent], curr[agent, 1])
            list_track_z[agent] = np.append(list_track_z[agent], curr[agent, 2])

            # Actualizar mapa de creencias
            bk, target, agent_found = filter(
                bk=bk, pos_agente=(curr[agent, 0:2]), pos_obj=target_pos[-1]
            )
            if len(BK) == steps:
                BK.append(bk)
                target_pos.append(target)
            else:
                BK[steps] = bk

            # Verificar si encontró al objetivo
            # y no sobreescribir el resultado de los otros
            if agent_found and not found:
                finder = agent
                found = True

        steps += 1

    # Eliminar el primer elemento de las listas de trayectorias (está vacio)
    list_track_x = [np.delete(i, 0) for i in list_track_x]
    list_track_y = [np.delete(i, 0) for i in list_track_y]
    list_track_z = [np.delete(i, 0) for i in list_track_z]
    return list_track_x, list_track_y, list_track_z, steps, finder, BK, target_pos

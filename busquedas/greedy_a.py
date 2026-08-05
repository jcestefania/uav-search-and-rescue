# Archivo con los distintos algoritmos de busqueda

import numpy as np
import os

from busquedas.heuristicas import heur_correcion_miopia

def rh_search_a(
    grid_size,
    init_pos,
    n_agents,
    drone_dist,
    moves,
    target,
    heur,
    lambda_,
    bk,
    horizon=100,
):
    found = False
    finder = None
    steps = 0
    curr = init_pos.copy()
    coords = np.mgrid[1 : grid_size[0] + 1, 1 : grid_size[1] + 1]
    pdmax = 0.8
    dmax = 2.1
    sigma = 0.7

    list_track_x = [np.empty(1) for _ in range(n_agents)]
    list_track_y = [np.empty(1) for _ in range(n_agents)]
    list_track_z = [np.empty(1) for _ in range(n_agents)]

    BK = []
    
    # Track visited positions for each agent
    visited_positions = [set() for _ in range(n_agents)]

    while not found and steps < horizon:
        for agent, agent_pos in enumerate(curr):
            dirs = np.random.permutation(len(moves))
            fs = np.column_stack(
                [
                    curr[agent, 0] + moves[dirs, 0],
                    curr[agent, 1] + moves[dirs, 1],
                    np.ones(len(moves)) * curr[agent, 2],
                ]
            )

            # Filter out moves that are out of bounds
            mask = (
                (fs[:, 0] >= 0)
                & (fs[:, 0] < grid_size[0])
                & (fs[:, 1] >= 0)
                & (fs[:, 1] < grid_size[1])
            )
            fs = fs[mask]

            # Only positions not yet visited are valid
            fs = np.array([pos for pos in fs if tuple(pos) not in visited_positions[agent]])

            # If no valid moves are left, the drone stays in place
            if len(fs) == 0:
                continue  # Skip this drone's move

            # Choose the best move based on the heuristic
            info = heur(bk=bk, next=fs, current=agent_pos, agents=curr)
            best = np.argmax(info)
            curr[agent] = fs[best]

            # **NEW: Mark position as visited**
            visited_positions[agent].add(tuple(curr[agent]))

            # Store trajectory
            list_track_x[agent] = np.append(list_track_x[agent], curr[agent, 0])
            list_track_y[agent] = np.append(list_track_y[agent], curr[agent, 1])
            list_track_z[agent] = np.append(list_track_z[agent], curr[agent, 2])

            # Update belief map
            distance = np.sqrt(
                (coords[1] - curr[agent, 0]) ** 2 + (coords[0] - curr[agent, 1]) ** 2
            )
            obs = pdmax * np.exp(-sigma * (distance / dmax) ** 2)
            bk = (1 - obs) * bk
            bk = bk / np.sum((1 - obs) * bk)

            if len(BK) == steps:
                BK.append(bk if os.environ.get("MTS_SAVE_BK_HISTORY", "True") != "False" else None)
            else:
                BK[steps] = bk if os.environ.get("MTS_SAVE_BK_HISTORY", "True") != "False" else None

            # Check if the target has been found
            dist_obj_x = np.abs(curr[agent, 0] - target[0])
            dist_obj_y = np.abs(curr[agent, 1] - target[1])

            if dist_obj_x <= dmax and dist_obj_y <= dmax:
                found = True
                finder = agent

        steps += 1

    # Remove the first empty element from the trajectory lists
    list_track_x = [np.delete(i, 0) for i in list_track_x]
    list_track_y = [np.delete(i, 0) for i in list_track_y]
    list_track_z = [np.delete(i, 0) for i in list_track_z]
    
    return list_track_x, list_track_y, list_track_z, steps, finder, BK

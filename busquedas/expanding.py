import numpy as np
import os


def expanding_sq(grid_size, bk, target, filter, init_pos, mov_d, separation, max_steps):
    """Calcula una trayectoria de Cuadrado creciente (Expanding Square Search, ESS) para un agente
    Parametros:
        grid_size: tamaño del mapa
        bk: mapa de probabilidad inicial
        target: coordenadas del objetivo
        filter: filtro para actualizar la creencia
        init_pos: posición inicial del agente
        mov_d: delta de movimiento
        separation: separación entre los tramos
        max_steps: número máximo de pasos que puede tomar
    Devuelve:
        track_x, track_y, track_z: trayectorias del agente
        steps: número de pasos realizados
        finder: agente que encontró el objetivo (None si no se encontró)
        BK: lista con los mapas de probabilidad
        target_pos: lista con las posiciones del objetivo
    """

    # Inicializar las listas con las posiciones
    track_x = np.empty(1)
    track_y = np.empty(1)
    track_z = np.empty(1)

    # Posición "actual" (current)
    c_x, c_y, c_z = init_pos

    # Dirs: derecha, arriba, izquierda, abajo
    dirs = [(mov_d, 0), (0, -mov_d), (-mov_d, 0), (0, mov_d)]
    loop_size = 1
    steps = 0
    finder = None
    found = False
    BK = []
    target_pos = [target]

    # Primero: Ir al centro
    while np.abs(c_x - grid_size[0] / 2) > 1 or np.abs(c_y - grid_size[1] / 2) > 1:
        if np.abs(c_x - grid_size[0] / 2) > 1:
            c_x += mov_d if c_x < grid_size[0] / 2 else -mov_d
        if np.abs(c_y - grid_size[1] / 2) > 1:
            c_y += mov_d if c_y < grid_size[1] / 2 else -mov_d

        track_x = np.append(track_x, c_x)
        track_y = np.append(track_y, c_y)
        track_z = np.append(track_z, c_z)
        steps += 1

        # Actualizar mapa de creencias
        bk, target, found = filter(bk=bk, pos_agente=(c_x, c_y), pos_obj=target)
        BK.append(bk if os.environ.get("MTS_SAVE_BK_HISTORY", "True") != "False" else None)
        target_pos.append(target)

        # Verificar si encontró al objetivo
        if found:
            finder = 0
            break
        if max_steps < steps:
            break

    # Hacer el cuadrado
    while 0 <= c_x and c_x < grid_size[0] and 0 <= c_y and c_y < grid_size[1]:
        for dx, dy in dirs:
            for _ in range(int(loop_size * separation)):
                c_x += dx
                c_y += dy

                track_x = np.append(track_x, c_x)
                track_y = np.append(track_y, c_y)
                track_z = np.append(track_z, c_z)
                steps += 1

                # Actualizar mapa de creencias
                bk, target, found = filter(bk=bk, pos_agente=(c_x, c_y), pos_obj=target)
                BK.append(bk if os.environ.get("MTS_SAVE_BK_HISTORY", "True") != "False" else None)
                target_pos.append(target)

                # Verificar si encontró al objetivo
                if found:
                    finder = 0
                    break

                if max_steps < steps:
                    break

            if found or max_steps < steps:
                break

            if (dx, dy) == (mov_d, 0) or (dx, dy) == (-mov_d, 0):
                loop_size += 1

        if found or max_steps < steps:
            break

    # Borrar el primer valor que introducimos al principio
    track_x = np.delete(track_x, 0)
    track_y = np.delete(track_y, 0)
    track_z = np.delete(track_z, 0)

    # Empaquetar los valores
    track_x = np.array([track_x])
    track_y = np.array([track_y])
    track_z = np.array([track_z])
    return track_x, track_y, track_z, steps, finder, BK, target_pos

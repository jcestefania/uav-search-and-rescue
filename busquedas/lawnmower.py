import numpy as np
import os


def lawnmower(
    grid_size, bk, target, filter, dmax, init_pos, mov_d, separation, max_steps
):
    """Calcula una trayectoria de cortacesped (Lawnmower Search, LS) para un agente
    Parametros:
        grid_size: tamaño del mapa
        bk: mapa de probabilidad inicial
        target: coordenadas del objetivo
        filter: filtro para actualizar la creencia
        dmax: distancia máxima de detección
        init_pos: posición inicial del agente
        mov_d: delta de movimiento
        separation: separación entre los tramos
        max_steps: número máximo de pasos que puede tomar
    Devuelve:
        track_x, track_y, track_z: trayectorias del agente
        steps: número de pasos realizados
        finder: agente que encontró el objetivo (None si no se encontró)
        BK: lista con los mapas de probabilidad
    """

    # Inicializar las listas de coordenadas
    track_x = np.empty(1)
    track_y = np.empty(1)
    track_z = np.empty(1)
    c_x, c_y, c_z = init_pos

    steps = 0
    BK = []
    target_pos = [target]
    found = False
    finder = None

    # Función para calcular la esquina más cercana a la posición actual
    def esquina_mas_cercana(grid_size, margin, pos):
        """
        Devuelve las coordenadas de la esquina más cercana a la posición actual
        """
        corners = [
            (margin, margin),  # abajo izq
            (margin, grid_size[1] - margin),  # arriba izq
            (grid_size[0] - margin, margin),  # abajo der
            (grid_size[0] - margin, grid_size[1] - margin),  # arriba der
        ]

        # Calcular distancias
        dist = [np.sqrt((pos[0] - c[0]) ** 2 + (pos[1] - c[1]) ** 2) for c in corners]

        min_dist = np.argmin(dist)
        chosen = corners[min_dist]

        return chosen

    # Calcular cual es la esquina más cercana
    esquina = esquina_mas_cercana(grid_size, dmax, init_pos)
    # True si se van a mover en dirección que aumenta el valor: 0 → grid_size
    mover_der = esquina[0] == dmax
    mover_arriba = esquina[1] == dmax
    sentido = 1 if mover_der else -1  # Sentido horizontal inicial

    # Mover el agente a la esquina más cercana
    while (c_x != esquina[0]) or (c_y != esquina[1]):
        if c_x != esquina[0]:
            dist_x = esquina[0] - c_x
            c_x += np.sign(dist_x) * min(abs(dist_x), mov_d)
        if c_y != esquina[1]:
            dist_y = esquina[1] - c_y
            c_y += np.sign(dist_y) * min(abs(dist_y), mov_d)
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

    # Definir los límites para permitir movimiento en cualquier posición de la grilla
    x_limit = lambda x: dmax <= x <= grid_size[0] - dmax
    y_limit = lambda y: dmax <= y <= grid_size[1] - dmax

    # Iniciar la búsqueda
    while y_limit(c_y) and not found:
        # Horizontal
        while x_limit(c_x) and not found:
            # Guardar las coordenadas
            track_x = np.append(track_x, c_x)
            track_y = np.append(track_y, c_y)
            track_z = np.append(track_z, c_z)
            c_x += sentido * mov_d
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

        # Vertical
        c_x -= sentido * mov_d
        v_dir = 1 if mover_arriba else -1
        v_limit = grid_size[1] - dmax if v_dir > 0 else dmax

        target_y = c_y + separation * v_dir
        # Asegurarse de no pasarse del borde
        target_y = min(target_y, v_limit) if v_dir > 0 else max(target_y, v_limit)
        while (v_dir > 0 and c_y < target_y) or (v_dir < 0 and c_y > target_y):
            c_y += mov_d * v_dir
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

        sentido = -sentido
        if max_steps < steps:
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

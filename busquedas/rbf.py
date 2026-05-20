"""Filtro recursivo bayesiano"""

import numpy as np
from scipy.signal import convolve2d


def rbf(bk, pos_agente, pos_obj, p_transicion, sensor):
    """Calcula una iteración del filtro bayesiano recursivo:
        Actualizar la creencia, simular el movimiento del objetivo y comprobar si
        el agente lo ha encontrado
    Parametros:
        bk: mapa de probabilidad
        pos_agente: posición del agente (x,y)
        pos_obj: posición del objetivo (x,y)
        sensor: objeto Sensor para realizar las observaciones y detectar el objetivo
    Devuelve:
        new_bk: mapa de probabilidad actualizado
        next_t: nueva posición del objetivo (x,y)
        found: Booleano, True si ha encontrado el objetivo
    """

    size = bk.shape
    size = np.array(size)
    coords = np.mgrid[1 : size[0] + 1, 1 : size[1] + 1]

    # Predicción
    bk = convolve2d(bk, p_transicion, mode="same")
    bk = bk / np.sum(bk)

    # Actualizar creencia
    c_x, c_y = pos_agente
    distance = np.sqrt((coords[1] - c_x) ** 2 + (coords[0] - c_y) ** 2)
    obs = sensor.observar(distance)
    bk = (1 - obs) * bk
    bk = bk / np.sum(bk)

    # Movimiento del objetivo
    found = False

    # Verificar si encontró al objetivo
    # comprueba si el objetivo está en el rango de detección
    # antes de moverse
    found = sensor.detectar(pos_agente, pos_obj)
    if found:
        return bk, pos_obj, found

    movimiento = [
        [-1, -1],
        [0, -1],
        [1, -1],
        [-1, 0],
        [0, 0],
        [1, 0],
        [-1, 1],
        [0, 1],
        [1, 1],
    ]

    probs = p_transicion.flatten()
    probs = probs / probs.sum()
    mov = movimiento[np.random.choice(len(movimiento), p=probs)]

    mov = np.array(mov)
    pos_obj = np.array(pos_obj)
    next_t = np.clip(pos_obj + mov, [0, 0], size - 1)  # Hacemos que no se salga

    # Verificar si encontró al objetivo
    # comprueba si el objetivo está en el rango de detección
    # después de moverse
    found = sensor.detectar(pos_agente, next_t)
    return bk, pos_obj, found

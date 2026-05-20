"""Heurísticas para el algoritmo voraz"""

import numpy as np


def heur_local(bk, next, sensor, **kwargs):
    """
    Devuelve la información que aporta cada sucesor en función de la probabilidad de observación.
    Esta heurística es susceptible a la localidad de la información y no tiene en cuenta la información global. (miopía)
    El mejor sucesor es aquel que maximiza la información
    Parametros:
        bk: mapa de probabilidad
        next (array): sucesores de la posición actual
        sensor: sensor con el que medir la información que ofrece cada sucesor
    Devuelve:
        info (array): lista con la información que aporta cada sucesor
    """
    info = np.zeros(len(next))
    coords = np.mgrid[0 : bk.shape[0], 0 : bk.shape[1]]
    for i, cs in enumerate(next):
        distance = np.sqrt((coords[1] - cs[0]) ** 2 + (coords[0] - cs[1]) ** 2)
        obs = sensor.observar(distance)
        obs = 1 - obs
        info[i] = 1 - np.sum(obs * bk)
    return info


def heur_correcion_miopia(
    bk,
    current,
    next,
    agents,
    dist_min=2,
    lambda_=0.5,
):
    """
    Devuelve la información que aporta cada sucesor en función de la heurística tomada del Criterio de correción de la miopia de
    Perez Carabaza, 2019: "MODELADO Y OPTIMIZACIÓN DE MISIONES DE BÚSQUEDA DE OBJETIVOS MEDIANTE UAVs
    también incluye penalización por cercanía a otros agentes
    El mejor sucesor es aquel que maximiza la información
    Parametros:
        bk: mapa de probabilidad
        current (array): posición actual
        next (array): sucesores de la posición actual
        agents (array): posiciones de todos los agentes
        dist_min: distancia minima entre los agentes
        lambda_: peso de la distancia en la heurística, 0 < λ < 1
    Devuelve:
        info (array): lista con la información que aporta cada sucesor
    """
    max_idx = np.argmax(bk)
    max_prob = np.unravel_index(max_idx, bk.shape)  # Punto con mayor probabilidad
    info = np.zeros(len(next))
    for i, cs in enumerate(next):
        # Trabajar con tipos de número de numpy para mayor precisión
        # Calcular la distancia al punto con mayor probabilidad
        dist = np.sqrt((max_prob[1] - cs[0]) ** 2 + (max_prob[0] - cs[1]) ** 2)
        heur = np.int64(1) - np.exp(np.log(lambda_) * dist)  # H = 1 - λ^d
        info[i] = np.int64(1) - np.sum(heur * bk)
        if len(agents) > 1:
            # Penalizar infinitamente las posiciones cercanas a otros drones
            info[i] = (
                info[i] if mantener_distancia(current, agents, dist_min) else -np.inf
            )

    return info


def mantener_distancia(curr_pos, all, r=2) -> bool:
    """
    Comprueba si la distancia entre el agente actual y todos los otros drones es mayor o igual a r
    Parametros:
        curr_pos: posicion del agente
        all: posiciones de todos los agentes
        r: radio de seguridad
    """
    for _, pos in enumerate(all):
        if not np.array_equal(pos, curr_pos):  # isclose(pos, curr_pos).all():
            dist = np.sqrt((curr_pos[0] - pos[0]) ** 2 + (curr_pos[1] - pos[1]) ** 2)
            if dist < r:
                return False
    return True

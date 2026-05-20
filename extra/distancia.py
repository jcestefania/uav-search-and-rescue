"""Funciones para calcular distancias entre puntos y celdas"""

import numpy as np


def calcular_distancia(track_x: list, track_y: list, track_z) -> float:
    """Devuelve la distancia que ha recorrido el agente, agregando la diferencia
    de desplazamiento en cada uno de los pasos dados
    """
    np.testing.assert_equal(
        len(track_x),
        len(track_y),
        "Las listas de coordenadas deben tener la misma longitud",
    )
    np.testing.assert_equal(
        len(track_x),
        len(track_z),
        "Las listas de coordenadas deben tener la misma longitud",
    )
    dist = 0.0
    prev = np.array([track_x[0], track_y[0], track_z[0]])
    for i in range(1, len(track_x)):
        curr = np.array([track_x[i], track_y[i], track_z[i]])
        dist += np.linalg.norm(curr - prev)
        prev = curr
    return np.round(dist, 4)

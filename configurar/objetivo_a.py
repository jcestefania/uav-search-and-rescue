"""Funciones para la selección del objetivo."""

import numpy as np


def random_target2(matriz_indicios):
    """
    Encuentra una posición aleatoria para el objetivo
    """    

    """    
    if np.all(target_pos!=0):
        return target_pos
    
    np.random.seed(seed)"""
    # Obtener las posiciones con valor distinto de 0
    posiciones_con_indicio = np.argwhere(matriz_indicios != 0)

    if len(posiciones_con_indicio) == 0:
        raise ValueError("La matriz de indicios no tiene valores distintos de 0.")

    indice_aleatorio = np.random.choice(len(posiciones_con_indicio))
    posicion_aleatoria = posiciones_con_indicio[indice_aleatorio]

    posicion_aleatoria = np.array([posicion_aleatoria[1], posicion_aleatoria[0]])  # Intercambiar

    return posicion_aleatoria


def celda_mas_proxima(coordenada, bk):
    """
    Ajusta las coordenadas de la posición objetivo a las celdas del mapa de probabilidades bk y
    devuelve las coordenadas de la celda más cercana.
    Parámetros:
        coordenada (array): coordenadas de la posición objetivo.
        bk (array): mapa de probabilidades.
    Devolución:
        punto (array): coordenadas de la celda más cercana.
    """
    distancias = np.sqrt(
        (np.arange(bk.shape[0])[:, None] - coordenada[0]) ** 2
        + (np.arange(bk.shape[1]) - coordenada[1]) ** 2
    )

    indice_celda_mas_cercana = np.unravel_index(np.argmin(distancias), distancias.shape)
    punto = np.array(indice_celda_mas_cercana)

    return punto

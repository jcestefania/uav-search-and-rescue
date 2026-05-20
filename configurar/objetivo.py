"""Funciones para la selección del objetivo."""

import numpy as np


def random_target(lista_indicios, COV, elegido, n=3):
    """
    Encuentra las coordenadas de todos los puntos en el mapa de probabilidades bk que tengan al menos el
    nivel de probabilidad objetivo y devuelve un punto aleatorio perteneciente a esa lista.

    Parámetros:
        lista_indicios (array): lista de las posiciones de las medias de las distribuciones gaussianas.
        COV (array): lista de matrices de covarianza.
        elegido: indice del indicio elegido
        n: Intervalo de confianza por defecto n=3, esto es 99,74%

    Devolución:
        goal (array): coordenadas del objetivo.
    """
    bk = lista_indicios[elegido]
    cov = COV[elegido]
    min_x = bk[0] - n * np.sqrt(cov[0, 0])
    min_y = bk[1] - n * np.sqrt(cov[1, 1])
    max_x = bk[0] + n * np.sqrt(cov[0, 0])
    max_y = bk[1] + n * np.sqrt(cov[1, 1])

    goal_x = np.random.uniform(min_x, max_x)
    goal_y = np.random.uniform(min_y, max_y)

    goal = np.array([goal_x, goal_y])

    return goal


def celda_mas_cercana(coordenada, bk):
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
        (np.arange(bk.shape[1])[:, None] - coordenada[0]) ** 2
        + (np.arange(bk.shape[0]) - coordenada[1]) ** 2
    )

    indice_celda_mas_cercana = np.unravel_index(np.argmin(distancias), distancias.shape)
    punto = np.array(indice_celda_mas_cercana)

    return punto

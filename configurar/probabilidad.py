"""Funciones relacionas con la probabilidad de encontrar el objetivo en cada punto del mapa"""

import numpy as np


def calcular_prob(grid_size, COV, list_b, weights=None):
    """Crea el mapa con la probabilidad de encontrar el objetivo en cada punto del mapa
    usando una combinación de gaussianas con pesos específicos
    Parametros:
        grid_size (array): tamaño del mapa
        COV (array): lista de matrices de covarianza, una para cada indicio
        list_b (array): lista con las coordenadas de los indicios
        weights (array): lista de pesos para cada gaussiana. Si es None, se usan pesos iguales
    Devuelve:
        bk (array): mapa inicial de probabilidades
    """
    # Si no se proporcionan pesos, usar pesos iguales
    weights = np.asarray(weights)
    if not np.all(weights):
        weights = np.ones(len(list_b)) / len(list_b)

    coords = np.mgrid[1 : grid_size[1] + 1, 1 : grid_size[0] + 1]
    bk = np.zeros(grid_size[1] * grid_size[0])
    bk = np.reshape(bk, (grid_size[1], grid_size[0]))  # WARNING: BK → (y, x)

    for i in range(grid_size[1]):
        for j in range(grid_size[0]):
            bk[i, j] = 0
            for idx, b in enumerate(list_b):
                bk[i, j] += weights[idx] * np.exp(
                    -0.5
                    * np.dot((coords[:, j, i] - b).T, np.linalg.inv(COV[idx])).dot(
                        coords[:, j, i] - b
                    )
                )
    # Normalizar
    bk = bk / np.sum(bk)
    return bk


def fusionar_horizontes(bk, limited_bk, pos):
    """Fusiona el mapa de probabilidades bk con el horizonte limitado limited_bk
    centrado en la posición pos
    Parametros:
        bk (array): mapa de probabilidades
        limited_bk (array): mapa de probabilidades con horizonte limitado
        pos (array): posición desde la que se ha creado el mapa limited_bk
    Devuelve:
        fused_bk (array): mapa de probabilidades fusionado
    """
    fused_bk = np.copy(bk)
    size = np.array(limited_bk.shape)
    offset = size // 2
    for i in range(size[1]):
        for j in range(size[0]):
            fused_bk[pos[0] - offset[0] + i, pos[1] - offset[1] + j] = min(
                bk[pos[0] - offset[0] + i, pos[1] - offset[1] + j], limited_bk[i, j]
            )
    return fused_bk


def crear_mapa_horizonte(bk, horizonte, pos):
    """Crea un nuevo mapa de probabilidad con
    Parametros:
        bk (array): mapa de probabilidades
        horizonte (int): tamaño del horizonte desde la posición actual
        pos (array): posición actual
    Devuelve:
        new_bk (array): nuevo mapa de probabilidades
    """
    length = 2 * horizonte + 1
    new_bk = np.zeros([length, length])
    for i in range(length):
        for j in range(length):
            new_bk[i, j] = bk[pos[0] - horizonte + i, pos[1] - horizonte + j]
    return new_bk

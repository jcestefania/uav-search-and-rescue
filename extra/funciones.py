# Código actualizado con comentarios de fuentes IEEE y explicación del modo de optimización

import numpy as np
import pandas as pd

# =======================================================
# MÉTRICA 1: EXPECTED TIME (ET)
# Fuente (IEEE): S. P. Carabaza et al., "Multi-UAS minimum time search in dynamic and uncertain environments,"
# IEEE International Conference on Unmanned Aircraft Systems (ICUAS), 2013.
# =======================================================
def ET(trayectoria, matriz_inicial, filter=None, target=None):
    """
    Expected Time (ET).

    Parámetros:
    trayectoria : lista de tuplas que representan las celdas visitadas secuencialmente
    matriz_inicial : matriz numpy con el mapa de creencias inicial
    filter : función opcional que implementa la actualización bayesiana de creencias
    target : tupla opcional que indica la posición del objetivo

    Retorna:
    expected_time : valor total de ET calculado
    mode : modo de optimización recomendado
    """

    bk = matriz_inicial.copy()

    expected_time = 0.0
    found = False

    for paso_num, (i, j) in enumerate(trayectoria, start=1):
        et_paso = float(bk.sum() - bk[i, j])
        expected_time += et_paso

        if filter is not None:
            try:
                bk, _, found = filter(bk=bk, pos_agente=(i, j), pos_obj=target)
            except Exception:
                bk[i, j] = 0.0
                found = False
        else:
            bk[i, j] = 0.0
            found = False

        suma = bk.sum()
        if suma > 0:
            bk = bk / suma
        else:
            bk = np.ones_like(bk) / bk.size

        if found:
            break

    return expected_time, "min", "ET"


# =======================================================
# MÉTRICA 2: DISCOUNTED TIME REWARD (DTR)
# Fuente (IEEE): P. Lanillos, E. Besada-Portas, J. A. Lopez-Orozco y J. M. De la Cruz,
# "Minimum Time Search in Uncertain Domains with Probabilistic Models," ECMR 2012.
# =======================================================
def DTR(trayectoria, matriz_inicial, gamma=0.8, filter=None, target=None):
    """
    Discounted Time Reward (DTR).

    Parámetros:
    trayectoria : lista de tuplas que representan las celdas visitadas secuencialmente
    matriz_inicial : matriz numpy con el mapa de creencias inicial
    gamma : factor de descuento temporal que penaliza recompensas futuras
    filter : función opcional que implementa la actualización bayesiana de creencias
    target : tupla opcional que indica la posición del objetivo

    Retorna:
    dtr_reward : recompensa acumulada con descuento temporal
    mode : modo de optimización recomendado
    """

    bk = matriz_inicial.copy()
    dtr_reward = 0.0
    found = False

    for t, (i, j) in enumerate(trayectoria, start=1):
        prob_celda = bk[i, j]
        discount_factor = gamma ** (t - 1)
        dtr_reward += discount_factor * prob_celda

        if filter is not None:
            try:
                bk, _, found = filter(bk=bk, pos_agente=(i, j), pos_obj=None)
            except Exception:
                bk[i, j] = 0.0
        else:
            bk[i, j] = 0.0

        s = bk.sum()
        if s > 0:
            bk = bk / s
        else:
            bk = np.ones_like(bk) / bk.size

    return dtr_reward, "max", "DTR"


# =======================================================
# MÉTRICA 3: MAXIMUM SLOPE (MS)
# Fuente (IEEE): G. A. Hollinger y G. S. Sukhatme,
# "Sampling-based robotic information gathering algorithms," IJRR, 2014.
# =======================================================
def MS(trayectoria, matriz_inicial, filter=None, target=None):
    """
    Maximum Slope (MS).

    Parámetros:
    trayectoria : lista de tuplas que representan las celdas visitadas secuencialmente
    matriz_inicial : matriz numpy con el mapa de creencias inicial
    filter : función opcional que implementa la actualización bayesiana de creencias
    target : tupla opcional que indica la posición del objetivo

    Retorna:
    max_slope_total : pendiente máxima encontrada durante la trayectoria
    mode : modo de optimización recomendado
    """

    bk = matriz_inicial.copy()
    max_slope_total = -np.inf
    found = False

    for idx, (i, j) in enumerate(trayectoria):
        if idx > 0:
            i_prev, j_prev = trayectoria[idx - 1]
            distancia = np.hypot(i - i_prev, j - j_prev)
            slope = (bk[i, j] - bk[i_prev, j_prev]) / distancia if distancia > 0 else 0.0
        else:
            slope = 0.0

        slope = max(0.0, slope)

        if filter is not None:
            try:
                bk, _, found = filter(bk=bk, pos_agente=(i, j), pos_obj=target)
            except Exception:
                bk[i, j] = 0.0
        else:
            bk[i, j] = 0.0

        if found:
            max_slope_total = 1.0
            break

        if slope > max_slope_total:
            max_slope_total = slope

        s = bk.sum()
        if s > 0:
            bk = bk / s
        else:
            bk = np.ones_like(bk) / bk.size

    if max_slope_total == -np.inf:
        max_slope_total = 0.0

    return max_slope_total, "max", "MS"


# =======================================================
# MÉTRICA 4: MINIMUM ENTROPY (ME)
# Fuente (IEEE): F. Bourgault et al., "Information based adaptive robotic exploration," IROS 2002.
# Además: C. E. Shannon, "A mathematical theory of communication," Bell Labs, 1948.
# =======================================================
def ME(trayectoria, matriz_inicial, filter=None, target=None):
    """
    Minimum Entropy (ME).

    Parámetros:
    trayectoria : lista de tuplas que representan las celdas visitadas secuencialmente
    matriz_inicial : matriz numpy con el mapa de creencias inicial
    filter : función opcional que implementa la actualización bayesiana de creencias
    target : tupla opcional que indica la posición del objetivo

    Retorna:
    entropia_final : entropía de Shannon calculada al final de la trayectoria
    mode : modo de optimización recomendado
    """

    def calcular_entropia(p):
        p_flat = p.flatten()
        p_flat = p_flat[p_flat > 0]
        if len(p_flat) == 0:
            return 0.0
        return -np.sum(p_flat * np.log2(p_flat))

    bk = matriz_inicial.copy().astype(float)
    bk /= bk.sum()

    found = False

    for (i, j) in trayectoria:
        if filter is not None:
            try:
                bk, _, found = filter(bk=bk, pos_agente=(i, j), pos_obj=target)
            except Exception:
                bk[i, j] = 0.0
                found = False
        else:
            bk[i, j] = 0.0
            found = False

        if found:
            return 0.0, "min", "ME"

        s = bk.sum()
        if s > 0:
            bk = bk / s
        else:
            bk = np.ones_like(bk) / bk.size

    entropia_final = calcular_entropia(bk)
    return entropia_final, "min", "ME"
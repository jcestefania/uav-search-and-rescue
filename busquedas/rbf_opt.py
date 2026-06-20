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
    
    # 1. Predicción: omitir convolve2d si el objetivo es estático (p_transicion es la identidad)
    is_static = (
        p_transicion.shape == (3, 3) and 
        p_transicion[1, 1] > 0.9999 and 
        (p_transicion.sum() - p_transicion[1, 1]) < 1e-4
    )
    
    if not is_static:
        bk = convolve2d(bk, p_transicion, mode="same")
        bk_sum = np.sum(bk)
        if bk_sum > 0:
            bk = bk / bk_sum
            
    # 2. Actualizar creencia localmente en la vecindad del sensor para optimizar rendimiento
    c_x, c_y = pos_agente
    dmax = getattr(sensor, 'dmax', 5.0)
    
    # Usamos un margen de 6 veces dmax, garantizando que obs sea prácticamente cero fuera
    window_size = int(np.ceil(6.0 * dmax))
    
    x_min = max(0, int(c_x - window_size))
    x_max = min(size[1], int(c_x + window_size + 1))
    y_min = max(0, int(c_y - window_size))
    y_max = min(size[0], int(c_y + window_size + 1))
    
    # Rango de coordenadas de la sub-grilla local
    x_grid = np.arange(x_min + 1, x_max + 1)
    y_grid = np.arange(y_min + 1, y_max + 1)
    
    # Distancia calculada con broadcasting de numpy para máxima velocidad
    distance = np.sqrt((x_grid[None, :] - c_x) ** 2 + (y_grid[:, None] - c_y) ** 2)
    obs_sub = sensor.observar(distance)
    
    # Multiplicar localmente la creencia
    bk[y_min:y_max, x_min:x_max] *= (1 - obs_sub)
    
    bk_sum = np.sum(bk)
    if bk_sum > 0:
        bk = bk / bk_sum

    # 3. Comprobar si el dron ha detectado al objetivo
    found = sensor.detectar(pos_agente, pos_obj)
    if found:
        return bk, pos_obj, found

    # 4. Movimiento del objetivo
    if is_static:
        next_t = pos_obj
    else:
        movimiento = [
            [-1, -1], [0, -1], [1, -1],
            [-1, 0],  [0, 0],  [1, 0],
            [-1, 1],  [0, 1],  [1, 1]
        ]
        probs = p_transicion.flatten()
        probs = probs / probs.sum()
        mov = movimiento[np.random.choice(len(movimiento), p=probs)]
        mov = np.array(mov)
        pos_obj = np.array(pos_obj)
        next_t = np.clip(pos_obj + mov, [0, 0], np.array(size) - 1)

    found = sensor.detectar(pos_agente, next_t)
    return bk, pos_obj, found

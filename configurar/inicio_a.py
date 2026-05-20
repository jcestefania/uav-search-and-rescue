"""Funciones para elegir la posicion inicial de los drones."""

import numpy as np
import random


# NOTE: Hay que hacerlo así para que siempre empiece en el borde
# Si no, se puede hacer con: init_pos = np.random.randint(0, size, (N_AGENTS, 2))
def random_pos_parcela_indicios(matriz_indicios, delta):
    """
    Genera posiciones aleatorias en el borde de la parcela de indicios (no del mapa).

    """
    filas, columnas = matriz_indicios.shape
    posiciones_borde = []

    for i in range(filas):
        for j in range(columnas):
            if matriz_indicios[i, j] > 0:
                # Se comprueban 8 celdas de alrededor
                for dx, dy in [(-delta, -delta), (-delta, 0), (-delta, delta), (0, -delta), (0, delta), (delta, -delta), (delta, 0), (delta, delta)]:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < filas and 0 <= nj < columnas and matriz_indicios[ni, nj] == 0:
                        posiciones_borde.append((i, j))
                        break  

    if not posiciones_borde:
        raise ValueError("No se encontraron posiciones en el borde.")

    init_pos = np.array(random.choice(posiciones_borde))
    #print(init_pos)

    return [init_pos]

def random_pos_espacio_busq(matriz_indicios):
    """
    Genera posiciones aleatorias en los bordes del mapa (matriz completa).
    """
    filas, columnas = matriz_indicios.shape
    posiciones_borde = []

    # Agregar posiciones en los bordes (primera y última fila, primera y última columna)
    for i in range(filas):
        for j in range(columnas):
            if i == 0 or i == filas - 1 or j == 0 or j == columnas - 1:  # Condición de borde
                posiciones_borde.append((i, j))

    if not posiciones_borde:
        raise ValueError("No se encontraron posiciones en el borde.")

    init_pos = np.array(random.choice(posiciones_borde))
    return [init_pos]

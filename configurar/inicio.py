"""Funciones para elegir la posicion inicial de los drones."""

import numpy as np


# NOTE: Hay que hacerlo así para que siempre empiece en el borde
# Si no, se puede hacer con: init_pos = np.random.randint(0, size, (N_AGENTS, 2))
def random_pos(size, N_AGENTS):
    """
    Genera posiciones aleatorias (exactamente) en el borde del mapa.

    Parámetros:
        size (tupla): tamaño del mapa
        N_AGENTS (int): número de drones

    Devolución:
        init_pos (array): posiciones iniciales de los drones
    """
    init_pos = np.empty((N_AGENTS, 2))

    for i in range(N_AGENTS):
        lado = np.random.randint(0, 4)
        match lado:
            case 0:  # Borde izquierdo
                x = 0
                y = np.random.randint(0, size[1])
            case 1:  # Borde derecho
                x = size[0]
                y = np.random.randint(0, size[1])
            case 2:  # Borde superior
                x = np.random.randint(0, size[0])
                y = 0
            case _:  # Borde inferior
                x = np.random.randint(0, size[0])
                y = size[1]
        init_pos[i] = np.array([y, x])

    return init_pos


def random_border_pos(size, N_AGENTS, min_dist, border_width=3):
    """
    Genera posiciones aleatorias dentro de una zona en el borde,
    manteniendo la distancia mínima entre los agentes.

    Parámetros:
        size (tupla): tamaño del mapa
        N_AGENTS (int): número de drones
        min_dist (float): distancia mínima requerida entre agentes
        border_width (int): ancho de la zona del borde (por defecto: 3)

    Devuelve:
        init_pos (array): posiciones iniciales de los drones
    """

    def calculate_distances(positions, new_pos):
        """Calcular distancias entre posición nueva y el resto"""
        return np.sqrt(np.sum((positions - new_pos) ** 2, axis=1))

    def generate_border_point():
        """Genera posiciones aleatorias en el borde del mapa, teniendo en cuenta el ancho del borde"""
        lado = np.random.randint(0, 4)
        match lado:
            case 0:  # Borde izquierdo
                x = np.random.randint(0, border_width)
                y = np.random.randint(0, size[1])
            case 1:  # Borde derecho
                x = np.random.randint(size[0] - border_width, size[0])
                y = np.random.randint(0, size[1])
            case 2:  # Borde superior
                x = np.random.randint(0, size[0])
                y = np.random.randint(0, border_width)
            case _:  # Borde inferior
                x = np.random.randint(0, size[0])
                y = np.random.randint(size[1] - border_width, size[1])
        return np.array([y, x])

    # Calcula área aproximada de la zona frontera
    # Simplificado de: A = S_0*S_1 - [(S_0-2M)*(S_1-2M)]
    # S: size; M: margen/tamaño de borde
    border_area = (
        2 * border_width * size[0]
        + 2 * border_width * size[1]
        - 4 * border_width * border_width
    )

    # Estimar el número de agentes que caben en el borde
    max_agents = border_area / (min_dist * min_dist)
    if N_AGENTS > max_agents:
        raise ValueError(
            f"No es posible colocar {N_AGENTS} agentes con distancia mínima {min_dist} en un borde de ancho {border_width}"
        )

    # Initialize array for positions
    positions = np.empty((N_AGENTS, 2))

    # Place first agent
    positions[0] = generate_border_point()

    # Place remaining agents
    agentes_colocados = 1
    max_attempts = 10_000  # Para prevenir bucles infinitos

    while agentes_colocados < N_AGENTS:
        attempts = 0
        while attempts < max_attempts:
            new_pos = generate_border_point()
            distances = calculate_distances(positions[:agentes_colocados], new_pos)

            # Check if position is valid (maintains minimum distance)
            if np.all(distances >= min_dist):
                positions[agentes_colocados] = new_pos
                agentes_colocados += 1
                break

            attempts += 1

        if attempts >= max_attempts:
            raise RuntimeError(
                f"Could not find valid position for agent {agentes_colocados} after {max_attempts} attempts"
            )

    return positions

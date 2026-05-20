import math

import numpy as np


def sectorial(centro, num_sectors, radius, init_pos):
    centro_x, centro_y = centro

    coord_x = []
    coord_y = []
    coord_z = []
    initial_z = init_pos[2]

    # Calcular el incremento de angulo entre sectores
    angle_increment = 360 / num_sectors

    # Generar los puntos para cada sector
    for sector in range(num_sectors):
        start_angle = sector * angle_increment
        end_angle = start_angle + angle_increment

        for angle in np.arange(start_angle, end_angle, 1):
            angle_radians = math.radians(angle)
            for r in np.arange(0, radius + 1, 1):
                point_x = centro_x + r * math.cos(angle_radians)
                point_y = centro_y + r * math.sin(angle_radians)

                if r <= radius:
                    coord_x.append(point_x)
                    coord_y.append(point_y)
                    coord_z.append(initial_z)

    return coord_x, coord_y, coord_z

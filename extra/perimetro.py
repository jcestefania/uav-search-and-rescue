import numpy as np


def perimetro_circulo(centro, radio, n_puntos=10) -> tuple[list[float], list[float]]:
    """
    Genera una lista con las coordenadas de n puntos que aproximan la forma de un circulo
    Parametros:
        centro: Coordenadas del centro del circulo [x, y]
        radio: Radio del circulo
        n_puntos: Número de puntos que forman el circulo
    """
    c_x, c_y = centro
    perimetro_x = []
    perimetro_y = []

    for ang_grados in range(0, 360, int(np.ceil(360 / n_puntos))):
        radianes = np.radians(ang_grados)

        # Calcular las coordenadas del punto
        p_x = c_x + radio * np.cos(radianes)
        p_y = c_y + radio * np.sin(radianes)
        p_x = np.round(p_x, 2)
        p_y = np.round(p_y, 2)

        perimetro_x.append(p_x)
        perimetro_y.append(p_y)

    # Añadir el primer punto otra vez para completar el circulo
    perimetro_x.append(perimetro_x[0])
    perimetro_y.append(perimetro_y[0])
    return perimetro_x, perimetro_y


def perimetro_cuadrado(centro, apotema: float) -> tuple[list[float], list[float]]:
    """
    Genera una lista con las coordenadas de los puntos en las esquinas de un cuadrado
    Parametros:
        centro: Coordenadas del centro del cuadrado [x, y]
        apotema: Longitud desde el centro a uno de los lados del cuadrado
    """
    c_x, c_y = centro
    square_x = [
        c_x - apotema,
        c_x + apotema,
        c_x + apotema,
        c_x - apotema,
        c_x - apotema,
    ]
    square_y = [
        c_y - apotema,
        c_y - apotema,
        c_y + apotema,
        c_y + apotema,
        c_y - apotema,
    ]
    return square_x, square_y

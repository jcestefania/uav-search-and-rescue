"""Sensores con el área de detección cuadrada"""

import numpy as np

from extra.perimetro import perimetro_cuadrado
from sensor import Sensor


class SquareSensor(Sensor):
    """
    Sensor ideal con area de detección cuadrada
    """

    def __init__(self, pdmax: float, dmax: float, sigma: float):
        """
        pdmax: Probabilidad máxima de detección. Probabilidad de que el sensor lo detecte cuando se encuentra cerca
        dmax: Distancia máxima de detección
        sigma: Sensibilidad a la distancia / Factor de caida exp. Cuanto mayor sea más rápido decae la probabilidad de detección
        """
        self.pdmax = pdmax
        self.dmax = dmax
        self.sigma = sigma

    def observar(self, dist: float) -> float:
        """
        Parametros:
        dist: distancia del agente a cada punto del mapa
        Devuelve:
        obs: La probabilidad de encontrar el objetivo en cada punto del mapa
        """
        return self.pdmax * np.exp(-self.sigma * (dist / self.dmax) ** 2)

    def detectar(self, curr: tuple[float, float], obj: tuple[float, float]) -> bool:
        dist_obj_x = np.abs(curr[0] - obj[0])
        dist_obj_y = np.abs(curr[1] - obj[1])

        if dist_obj_x <= self.dmax and dist_obj_y <= self.dmax:
            return True
        return False

    def perimetro(self, curr) -> tuple[list[float], list[float]]:
        return perimetro_cuadrado(curr, self.dmax)


class SquareSensorPlan(Sensor):
    """
    Sensor con area de detección cuadrada, sin la condición de parada por detección
    """

    def __init__(self, pdmax: float, dmax: float, sigma: float):
        """
        pdmax: Probabilidad máxima de detección. Probabilidad de que el sensor lo detecte cuando se encuentra cerca
        dmax: Distancia máxima de detección
        sigma: Sensibilidad a la distancia / Factor de caida exp. Cuanto mayor sea más rápido decae la probabilidad de detección
        """
        self.pdmax = pdmax
        self.dmax = dmax
        self.sigma = sigma

    def observar(self, distance) -> float:
        return self.pdmax * np.exp(-self.sigma * (distance / self.dmax) ** 2)

    def detectar(self, curr: tuple[float, float], obj: tuple[float, float]) -> bool:
        _ = curr, obj  # No se usan los parámetros, que solo están por compatibilidad
        return False

    def perimetro(self, curr) -> tuple[list[float], list[float]]:
        return perimetro_cuadrado(curr, self.dmax)

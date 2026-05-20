from typing import Any, Protocol


class Sensor(Protocol):
    """Interfaz de clase para modelar un sensor"""

    # No se han hecho asunciones de los atributos que debe recibir cada método
    # Cada subclase definirá la firma de sus própios métodos
    # Solo se especifica el tipo de dato de retorno

    def __init__(self):
        pass

    def observar(self, *args: Any, **kwargs: Any) -> float:
        """
        Calcula la probabilidad de detección del objetivo por el agente en
        funciónde de su posición actual y el entorno
        """
        ...

    def detectar(self, *args: Any, **kwargs: Any) -> bool:
        """
        Comprueba si el sensor ha detectado el objetivo
        """
        ...

    def perimetro(self, *args: Any, **kwargs: Any) -> tuple[list[float], list[float]]:
        """
        Devuelve la lista de pares de coordenadas que forman el perímetro
        del sensor
        """
        ...

"""
Funciones para configurar el problema, como generar el mapa de probabilidad o
establecer la posición del objetivo
"""

from .inicio import random_border_pos, random_pos
from .objetivo import celda_mas_cercana, random_target
from .probabilidad import calcular_prob, crear_mapa_horizonte, fusionar_horizontes

__all__ = [
    "random_border_pos",
    "random_pos",
    "random_target",
    "celda_mas_cercana",
    "calcular_prob",
    "crear_mapa_horizonte",
    "fusionar_horizontes",
]

"""
Funciones de busqueda:
    - rh_search
    - lawnmower
    - expanding_sq
Y métodos auxiliares para la búsqueda: heurísticas, filtros...
"""

from .expanding import expanding_sq as expanding_sq
from .greedy import rh_search as rh_search
from .lawnmower import lawnmower as lawnmower
from .lineal import tracking_line as tracking_line
from .sectorial import sectorial as sectorial

# Algoritmos clásicos sacados del artículo "Análisis y planificación de misiones
# búsqueda y rescate en el retorno marítimo", Eva Besada 2019

__all__ = ["expanding_sq", "rh_search", "lawnmower", "sectorial", "tracking_line"]

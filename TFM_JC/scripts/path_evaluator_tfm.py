# TFM_JC/scripts/path_evaluator_tfm.py
"""
PathEvaluatorTFM: Módulo de evaluación unificado para el TFM.
Mantiene la compatibilidad con el PathEvaluator original de SAREnv sin modificar la librería original.
Añade métricas específicas de MTS (Probabilidad Acumulada, Tasa de Acierto, Pasos a la Meta, Área Cubierta y Distancia Total)
tanto para trayectorias de SAREnv como de MTS.
"""
import os
import json
import numpy as np
import geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from scipy.interpolate import RegularGridInterpolator

class PathEvaluatorTFM:
    """
    Evaluador unificado de trayectorias para el TFM.
    Soporta la evaluación cruzada entre algoritmos bioinspirados de MTS y baselines de SAREnv.
    """
    def __init__(self, heatmap: np.ndarray, extent: tuple, victims: gpd.GeoDataFrame, fov_deg: float = 60.0, altitude: float = 50.0, meters_per_bin: int = 10):
        """
        Inicializa el evaluador.

        Args:
            heatmap (np.ndarray): Matriz 2D de la densidad de probabilidad (heatmap.npy).
            extent (tuple): Límites (minx, miny, maxx, maxy) en UTM o coordenadas locales.
            victims (gpd.GeoDataFrame): GeoDataFrame con los puntos de las víctimas.
            fov_deg (float): Campo de visión de la cámara del dron en grados.
            altitude (float): Altitud de vuelo del dron en metros.
            meters_per_bin (int): Tamaño de celda de la rejilla en metros.
        """
        self.heatmap = heatmap
        self.extent = extent
        self.victims = victims
        self.meters_per_bin = meters_per_bin
        
        # Radio de detección de la cámara según altitud y ángulo FoV (Nivel 1: Sensor Ideal)
        self.detection_radius = altitude * np.tan(np.radians(fov_deg / 2.0))
        
        # Tamaño de celda en X e Y
        minx, miny, maxx, maxy = self.extent
        self.cell_size_x = (maxx - minx) / heatmap.shape[1]
        self.cell_size_y = (maxy - miny) / heatmap.shape[0]

    def eval_trajectory(self, path_coords: list, goal_coord: tuple = None, max_steps: int = 1000) -> dict:
        """
        Evalúa una trayectoria dada como lista de coordenadas [(x0, y0), (x1, y1), ...] o LineString.

        Args:
            path_coords (list): Lista de tuplas/listas con coordenadas (x, y) de cada posición del dron.
            goal_coord (tuple, optional): Coordenadas (x, y) del objetivo/víctima.
            max_steps (int): Presupuesto máximo de pasos de la simulación.

        Returns:
            dict: Diccionario con las 5 métricas unificadas del TFM.
        """
        if not path_coords or len(path_coords) == 0:
            return {
                "success_rate": 0.0,
                "steps_to_goal": max_steps,
                "cumulative_probability": 0.0,
                "area_covered_m2": 0.0,
                "total_distance_m": 0.0
            }

        # 1. Tasa de acierto (success_rate) y pasos hasta la meta (steps_to_goal)
        success = 0.0
        steps_to_goal = max_steps
        
        # Si se pasa un objetivo, comprobar si alguna posición de la trayectoria cae dentro del radio de detección
        if goal_coord is not None:
            gx, gy = goal_coord
            for step_idx, (x, y) in enumerate(path_coords):
                dist_to_goal = np.sqrt((x - gx)**2 + (y - gy)**2)
                if dist_to_goal <= self.detection_radius or dist_to_goal <= (self.meters_per_bin / 2.0):
                    success = 1.0
                    steps_to_goal = step_idx + 1
                    break
        elif not self.victims.empty:
            # Comprobar contra el GeoDataFrame de víctimas
            for step_idx, (x, y) in enumerate(path_coords):
                pt = Point(x, y)
                for v_pt in self.victims.geometry:
                    if pt.distance(v_pt) <= self.detection_radius:
                        success = 1.0
                        steps_to_goal = step_idx + 1
                        break
                if success == 1.0:
                    break

        # 2. Probabilidad acumulada en celdas unívocas visitadas (cumulative_probability)
        minx, miny, _, _ = self.extent
        visited_cells = set()
        for x, y in path_coords:
            col = int((x - minx) / self.cell_size_x)
            row = int((y - miny) / self.cell_size_y)
            if 0 <= row < self.heatmap.shape[0] and 0 <= col < self.heatmap.shape[1]:
                visited_cells.add((row, col))
                
        cumulative_prob = sum(self.heatmap[r, c] for r, c in visited_cells)

        # 3. Área cubierta en metros cuadrados (area_covered_m2)
        area_m2 = len(visited_cells) * (self.cell_size_x * self.cell_size_y)

        # 4. Distancia total recorrida (total_distance_m)
        dist_m = 0.0
        for i in range(1, len(path_coords)):
            x0, y0 = path_coords[i-1]
            x1, y1 = path_coords[i]
            dist_m += np.sqrt((x1 - x0)**2 + (y1 - y0)**2)

        return {
            "success_rate": success,
            "steps_to_goal": steps_to_goal,
            "cumulative_probability": float(cumulative_prob),
            "area_covered_m2": float(area_m2),
            "total_distance_m": float(dist_m)
        }

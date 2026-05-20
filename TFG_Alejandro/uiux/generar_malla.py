"""Módulo que contiene toda la lógica para la generación del mapa y de malla. El mapa tiene como punto de referencia el centro de la calle y, a partir de ahí, crea las 4 esquinas sabiendo el radio.
El mapa, ya sea en coordenadas locales o globales, es una lista con listas dentro. Cada una de esas listas representa un cuadrado, que se define como las coordenadas (insisto, en locales o globales)
de las esquinas, o sea que dentro de cada una de esas listas hay 4 listas que definen puntos de la forma [lon, lat] o (x, y).
La malla consiste en una matriz donde cada posición define un cuadrado del mapa. Es decir, que la posición (i,j) de la malla en realidad corresponde con una de las filas del mapa que forma un cuadrado.
La matriz de indicios tiene la misma estructura que la malla, pero 
"""

#Crear en coords locales, luego pasar a gloables y almacenar ambas

import numpy as np
from shapely.geometry import LineString, Point, Polygon
import pymap3d as pm

def calculo_centro_area(coordenadas: list) -> tuple:
    """Calcula lo que será el punto central de del area (media de la longitud y latitud) a partir de las coordenadas de la calle inicial. Devuelve el centroide"""
    if not coordenadas:
        return None
    
    total_lon = 0
    total_lat = 0

    for lon, lat in coordenadas:
        total_lon += lon
        total_lat += lat

    return (total_lon/len(coordenadas), total_lat/len(coordenadas))

def numero_cuadriculas(radio, tam_cuadricula):
    """Calcula el número de cuadrículas que se necesitarán para definir el área"""

    cuadriculas_ancho = (2*radio) / tam_cuadricula
    cuadriculas_largo = (2*radio) / tam_cuadricula
  
    #total_cuadriculas = cuadriculas_ancho * cuadriculas_largo

    return cuadriculas_ancho, cuadriculas_largo # Aunque sea un cuadrado, paso ambos por si en un futuro cambio la forma del perímetro

def all_in_one_magic(centroide, radio, tam_cuadricula):
    """Crea el mapa en coordenadas locales, hace la conversión a globales y almacena los mapas en ambos sistemas de referencia"""

    filas = int(2 * radio / tam_cuadricula)
    columnas = int(2 * radio / tam_cuadricula)
    x_0 = -radio
    y_0 = -radio

    lon_ref, lat_ref = centroide

    coords_mapa_local = []
    coords_mapa_global = []

    for i in range(filas):
        for j in range(columnas):
            # Calcular las coordenadas de los vértices del cuadrado en locales
            x_min = x_0 + (j * tam_cuadricula)
            x_max = x_min + tam_cuadricula
            y_max = y_0 + (i * tam_cuadricula)
            y_min = y_max + tam_cuadricula

            cuadrado_local = [
                [x_min, y_max],  # Esquina noroeste
                [x_max, y_max],  # Esquina noreste
                [x_max, y_min],  # Esquina sureste
                [x_min, y_min],  # Esquina suroeste
                [x_min, y_max],  # Repetir para cerrar el polígono
            ]
            coords_mapa_local.append(cuadrado_local)

            # Convertir las coordenadas locales a globales
            cuadrado_global = [(float(lon), float(lat)) for lat, lon in (pm.enu2geodetic(x, y, 0, lat_ref, lon_ref, 0)[:2] for x, y in cuadrado_local)]

            coords_mapa_global.append(cuadrado_global)

    # Coordenadas locales de las esquinas de la malla
    esquina_inferior_izquierda_local = [x_0, y_0]
    esquina_inferior_derecha_local = [x_0 + (columnas * tam_cuadricula), y_0]
    esquina_superior_derecha_local = [x_0 + (columnas * tam_cuadricula), y_0 + (filas * tam_cuadricula)]
    esquina_superior_izquierda_local = [x_0, y_0 + (filas * tam_cuadricula)]


    esquinas_locales = [
        esquina_superior_izquierda_local,
        esquina_superior_derecha_local,
        esquina_inferior_derecha_local,
        esquina_inferior_izquierda_local]

    # Convertir las esquinas locales a globales
    esquina_superior_izquierda_global = tuple(float(coord) for coord in pm.enu2geodetic(
        esquina_superior_izquierda_local[0], esquina_superior_izquierda_local[1], 0, lat_ref, lon_ref, 0)[:2][::-1]) #[:2] para que no coger la altitud del punto y [::-1] para que me lo de en (lon, lat) y no (lat, lon)

    esquina_superior_derecha_global = tuple(float(coord) for coord in pm.enu2geodetic(
        esquina_superior_derecha_local[0], esquina_superior_derecha_local[1], 0, lat_ref, lon_ref, 0)[:2][::-1])

    esquina_inferior_izquierda_global = tuple(float(coord) for coord in pm.enu2geodetic(
        esquina_inferior_izquierda_local[0], esquina_inferior_izquierda_local[1], 0, lat_ref, lon_ref, 0)[:2][::-1])

    esquina_inferior_derecha_global = tuple(float(coord) for coord in pm.enu2geodetic(
        esquina_inferior_derecha_local[0], esquina_inferior_derecha_local[1], 0, lat_ref, lon_ref, 0)[:2][::-1])
        
    esquinas_globales = [
        esquina_superior_izquierda_global,
        esquina_superior_derecha_global,
        esquina_inferior_derecha_global,
        esquina_inferior_izquierda_global]

    return coords_mapa_local, coords_mapa_global, esquinas_locales, esquinas_globales


def generar_matriz_indicios(coords_mapa_global, coords_uni, grid_size):
    """Transforma las coordenadas del mapa global a una matriz de indicios donde cada posición de la matriz representa un cuadrado"""

    poligono_parcela = Polygon(coords_uni)

    matriz_indicios = np.zeros(grid_size, dtype=int) 
    
    for idx, cuadrado in enumerate(coords_mapa_global): # Paso clave que asigna a cada cuadrado (una lista en el mapa) una posición i, j en la malla
        fila = idx // grid_size[1]  # Fila
        columna = idx % grid_size[1]  # Columna
        
        # Si algún punto de un cuadrado está dentro del área se le asigna un 1
        if any(poligono_parcela.contains(Point(coord)) for coord in cuadrado):
            matriz_indicios[fila, columna] = 1  
    
    #print(matriz_indicios)
    return matriz_indicios

def coords_globales_a_locales(origen, coords):

    # Convertir el centroide (que será el origen) a ENU
    lon_ref, lat_ref = origen
    x_ref, y_ref, _ = pm.geodetic2enu(lat_ref, lon_ref, 0, lat_ref, lon_ref, 0)  # MIRAR ALTITUD

    # comprobar primero si lo que le he pasado son las coords del dron
    if len(coords) <= 1:
        lon, lat = coords[0][0],coords[0][1]
        x, y, _ = pm.geodetic2enu(lat, lon, 0, lat_ref, lon_ref, 0)
        print(f'{[float(x), float(y)]} en locales A')
        return [float(x), float(y)]

def coords_locales_a_malla(pos_init_dron, radio, dim_mapa, dim_malla):
    """Transforma las coordenadas del mapa en las coordenadas de la malla"""

    x_local, y_local = pos_init_dron

    i = int(((x_local + radio) / dim_mapa[0]) * (dim_malla[0] - 1))
    j = int(((radio - y_local) / dim_mapa[1]) * (dim_malla[1] - 1))
    
    print(f'{[i,j]} en la malla')
    return [int(i), int(j)]

def translation_point(point, radio):
    """ Transforma las coordenadas locales de la posición inicial del dron del sistema de referencia A al Y
    Se usa en 2D porque la altura (z) ya se le pasa en el JSON.

    Translates a 2D point using a homogeneous transformation matrix.
    Ensures that (-350, -350) in System A becomes (0,0) in System B.

    Parameters:
    - point: Tuple (x_A, y_A), a point in System A.

    Returns:
    - Transformed point in System B (x_B, y_B).
    """

    point_homogeneous = np.array([point[0], point[1], 1]) # el 1 es para la simetría de la matriz
    
    # Matriz de transformación de la matriz A a Y
    transformation_matrix = np.array([
        [1, 0, radio],  # Shift X by +radio
        [0, 1, radio],  # Shift Y by +radio
        [0, 0, 1]
    ])

    # Transformación P_Y = T * P_A
    transformed_point_homogeneous = transformation_matrix @ point_homogeneous

    transformed_point = [round(coord) for coord in transformed_point_homogeneous[:2]]
    print(f'El punto ({point[0]},{point[1]}) en el sistema de referencia A es el punto {transformed_point} en locales en el sistema Y')
    
    return transformed_point

def reescalado(coordenadas, tc):
    return [coordenadas[0]/tc, coordenadas[1]/tc]

if __name__ == "__main__":
    pass
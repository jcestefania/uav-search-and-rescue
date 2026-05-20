"""Módulo principal que contiene la estructura del código. A partir de consultas a Overpass API, probar algoritmos de búsqueda de heurísticas"""

import consultas_overpass as co
#import otras_visualizaciones as ov
import generar_malla as gm
import main_visualizacion as main_visu
#import interfaz_parametros as ip
import crear_json
import numpy as np


if __name__ == "__main__":

    """  user_input = ip.user_parameters()
    
    pais = user_input["pais"]
    municipio = user_input["municipio"]
    calle = user_input["calle"]
    radio = int(user_input["radio"])
    tipo = user_input["tipo"]
    dinamico = user_input["dinamico"]
    tam_cuadricula = int(user_input["tam_cuadricula"])
    escala = 1"""
        
    pais = "España"
    municipio = "Colmenarejo"
    calle = "Avenida Gregorio Peces-Barba Martínez"
    radio = 350 #en metros
    tipo = "rectangular"
    escala = 1
    dinamico = False # Booleano para definir que el objetivo sea estático o dinámico

    #num_puntos = 36 # Cambiar sólo para el circular (36 puntos para que cada 10 grados haya un punto)
    #tam_cuadricula = 4 #en metros"""
    tam_cuadricula = 10 #en metros

    archivo_calle = co.coordenadas_calle(pais, municipio, calle) # 1) Query con Overpass API de la calle y almacenar en JSON sus coordenadas
    coordenadas_calle = co.extraer_coordenadas_calle(archivo_calle) # 2) Extraer coordenadas del JSON a una lista
    centroide = gm.calculo_centro_area(coordenadas_calle) # 3) Calcular media de las coordenadas (centro del área)

    print(f'Punto medio de la calle: {centroide}')

    #coordenadas_perimetro = area(centroide, radio, tipo, escala) # 4) Calcular del centroide las coordenadas que definen el perímetro
    archivo_edificios = co.coordenadas_edificios(centroide, radio) # 5 Query para obtener las coordenadas de todos los edificios
    archivo_calles = co.coordenadas_calles(centroide, radio) # 6) Query para obtener las coordenadas de todos las calles
    archivo_uni = co.coordenadas_universidad(centroide, radio) # 7) Query para obtener las coordenadas de la universidad

    coordenadas_edificios = co.extraer_coordenadas(archivo_edificios) # 8) Extraer coordenadas de los edificios
    coordenadas_calles = co.extraer_coordenadas(archivo_calles) # 9) Extraer coordenadas de las calles
    coordenadas_universidad = co.extraer_coordenadas(archivo_uni) # 10) Extraer coordenadas de la universidad

    coordenadas_universidad = coordenadas_universidad[0] # Se almacena como una lista dentro de otra lista, así que cojo el primer elemento, o sea, la lista entera
    # coordenadas_universidad es una lista de tuplas (lon,lat)
    # coordenadas_edificios y coordenadas_calles es una lista con listas y dentro tuplas (lon,lat)

    # Número de cuadrículas
    cuadriculas_ancho, cuadriculas_alto = gm.numero_cuadriculas(radio, tam_cuadricula)
    mapa = [radio*2, radio*2]
    map_size = (int(radio*2), int(radio*2))
    grid_size = (int(cuadriculas_ancho), int(cuadriculas_alto))

    coords_malla_local, coords_malla_global, coords_perimetro_local, coords_perimetro_global = gm.all_in_one_magic(centroide, radio, tam_cuadricula)
    # Las mallas son listas de listas, y dentro de estas tienen cinco listas de [lon,lat]
    # Las coordenadas del perímetro local es una lista con cinco listas del estilo [lon,lat]
    # Las coordenadas del perímetro global es una lista con cinco tuplas del estilo (lon,lat)
    print(coords_perimetro_global)
    # Matriz llena de 0s y 1s (los 1s indican que están dentro de la parcela)
    matriz_indicios = gm.generar_matriz_indicios(coords_malla_global, coordenadas_universidad, grid_size)

    matriz_indicios = np.array(matriz_indicios)
    matriz_indicios = matriz_indicios / np.sum(matriz_indicios) # Normalizar para sacar las probabilidades


    # Visualización del mapa y devuleve la posición incial del dron (donde el usuario ha dado click)
    coords_inicio_dron = main_visu.visualizar_malla_gpd(calle, municipio, radio, escala, tipo, coords_perimetro_global, coordenadas_edificios, coordenadas_calles, coordenadas_universidad, coords_malla_global, tam_cuadricula, matriz_indicios)

    # En caso de no haber hecho click en el map para determinar la pos inicial, establezco el centroide como posición inicial
    if len(coords_inicio_dron) == 0:
        coords_inicio_dron.clear()
        coords_inicio_dron.append(centroide)


    coords_inicio_dron_local = gm.coords_globales_a_locales(centroide, coords_inicio_dron)

    #HAY QUE HACER UNA DISTINCIÓN ENTRE EL ESPACIO DE BÚSQUEDA (MAPA) Y LA MALLA (pasar de coordenadas locales a las coordenadas en la malla)
    #coords_inicio_dron_malla = gm.coords_locales_a_malla(coords_inicio_dron_local, radio, mapa, grid_size)

    #Hay que hacer una transformación para la representación en el sistema Y del planificador 
    coords_inicio_dron_transf = gm.translation_point(coords_inicio_dron_local, radio) #Deja las coordenadas en 700x700 

    #Hay que cambiarlo al tamaño del sistema de cuadrículas de bk (es decir, cuántos cuadrados hay por alto y por ancho)
    coords_inicio_dron_reesc = gm.reescalado(coords_inicio_dron_transf, tam_cuadricula)
    print(coords_inicio_dron_reesc)

    # Guardar coordenadas GLOBALES en un archivo JSON
    co.guardar_coordenadas_json("coordenadas_segmentadas.json", coords_perimetro_global, coordenadas_edificios, coordenadas_calles, coordenadas_universidad, coords_inicio_dron)

    # Fichero JSON con la información para la misión
    reference_system = "ENU" #NED
    target_pos = [None, None] # Para fijar una posición del objetivo
    crear_json.data_json(list(map_size), list(grid_size), matriz_indicios.tolist(), centroide, coords_inicio_dron_reesc, reference_system, tam_cuadricula, target_pos, radio, coords_perimetro_global)

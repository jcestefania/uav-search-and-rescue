import os
from pathlib import Path
import numpy as np
import pandas as pd

from .distancia import calcular_distancia


def crear_dataframe(
    N_AGENTS,
    list_track_x,
    list_track_y,
    list_track_z,
    goal,
    finder,
    agent_seed,
    goal_seed,
):
    """
    Crea un DataFrame con la información de los agentes, el objetivo, distacia recorrida
    Parametros:
        N_AGENTS (int): Número de agentes
        list_track_x (list): Lista con la coordenada x de los caminos de los agentes
        list_track_y (list): Lista con la coordenada y de los caminos de los agentes
        list_track_z (list): Lista con la coordenada z de los caminos de los agentes
        goal (list): Coordenadas del objetivo P(x, y)
        finder (int/None): Indice del agente que encontró el objetivo (None si no se ha encontrado)
        agent_seed (int/None): semilla usada para elegir las posiciones de los agentes (None si estaban hardcodeadas)
        goal_seed (int/None): semilla usada para elegir la posicion del objetivo (None si estaba hardcodeada)
    Devuelve:
        df (pd.DataFrame): DataFrame con la información de los agentes
    """
    data = {}

    list_track_x = np.array(list_track_x)
    list_track_y = np.array(list_track_y)
    list_track_z = np.array(list_track_z)

    if list_track_x.size == 0 or list_track_y.size == 0 or list_track_z.size == 0:
        raise ValueError("List of positions is empty")

    if agent_seed is None:
        agent_seed = "-"

    for i in range(N_AGENTS):
        start = np.array([list_track_x[i][0], list_track_y[i][0]])
        end = np.array([list_track_x[i][-1], list_track_y[i][-1]])
        d = calcular_distancia(list_track_x[i], list_track_y[i], list_track_z[i])
        steps = len(list_track_x[i]) - 1  # Restar 1 porque el primer paso no cuenta
        merit = True if finder == i else False
        data[f"Agent {i}"] = [start, end, d, steps, merit, agent_seed]

    if goal_seed is None:
        goal_seed = "-"

    goal = np.array(goal)
    last_goal = goal[0]
    steps_goal = 0
    d_goal = calcular_distancia(goal.T[0], goal.T[1], np.zeros(len(goal)))
    for pos in goal:
        if np.array_equal(pos, last_goal):  # El objetivo puede estar quieto
            continue  # Para conservar el comportamiento anterior
        last_goal = pos
        steps_goal += 1
    data["Target"] = [goal[0], goal[-1], d_goal, steps_goal, finder, goal_seed]
    labels = [
        "Initial position",
        "Final position",
        "Distance",
        "Steps taken",
        "Found Target",
        "Semilla",
    ]
    df = pd.DataFrame(data, index=labels)

    return df


def guardar_dataframe(df, dir, busq, prueba):
    """
    Guarda el dataFrame en un archivo CSV siguiendo el formato resultados/prueba/busq-num.csv.
    Si no existe alguna de las carpetas, las crea. Num es un número que se incrementa
    si ya existe un archivo con el mismo nombre, para permitir varias pruebas para la misma
    combinación de búsqueda y archivo de configuración.
    Parametros:
        df (pd.DataFrame): DataFrame a guardar
        dir (str): Nombre de la carpeta que contiente todas las pruebas
        busq (str): Nombre identificador del algorítmo de búsqueda
        prueba (str): Nombre de la prueba (únicamente el nombre del archivo, no el PATH)
    """
    # Usar Path para manejar rutas correctamente en Windows y Linux
    dir_base = Path(dir)
    
    # Crear carpeta base si no existe
    dir_base.mkdir(parents=True, exist_ok=True)
    
    # Crear carpeta de la prueba
    carpeta_prueba = dir_base / prueba
    carpeta_prueba.mkdir(parents=True, exist_ok=True)
    
    # Buscar el siguiente número disponible
    num = 0
    while (carpeta_prueba / f"{busq}-{num}.csv").exists():
        num += 1
    
    # Guardar el archivo
    archivo_csv = carpeta_prueba / f"{busq}-{num}.csv"
    df.to_csv(archivo_csv)
    print("Resultados guardados en:", archivo_csv)
"""Genera una visualización con las posiciones iniciales de todas las búsquedas"""

# Este script es altamente específico a la prueba y a veces
# es necesario adaptarlo en gran medida para la visualización
# Es más bien un hack

import json
import os

import numpy as np
import pandas as pd

from configurar import calcular_prob, celda_mas_cercana, random_target
from extra import dibujar_animacion
from sensor.square_sensor import SquareSensor


def get_positions_from_csv(file_path, get_finder=False):
    """
    Toma el archivo CSV y lee las posiciones iniciales de los agentes
    Si get_finder es True, solo devolverá la posición del agente que encontró
    el objetivo y en caso de que no se haya encontrado, devuelve la del agente 0
    Devuelve dos listas con las coordenadas x e y
    """
    df = pd.read_csv(file_path, header=0, index_col=0)
    if get_finder:
        finder = df.loc["Found Target", "Target"]
        found = not np.isnan(float(finder))
        pos = np.array(
            [
                np.fromstring(
                    str(
                        df.loc["Initial position", "Agent " + str(finder)]
                        if found
                        else df.loc["Initial position", "Agent 0"]
                    )[1:-1],
                    sep=" ",
                )
            ]
        )
    else:  # Tomar las de todos
        agent_columns = [col for col in df.columns if col.startswith("Agent")]
        pos = np.array(
            [
                np.fromstring(df.loc["Initial position", agent][1:-1], sep=" ")
                for agent in agent_columns
            ]
        )
    return pos[:, 0], pos[:, 1]


def process_all(directory):
    # Toma todos los archivos csv de la carpeta y los "procesa" (tomar la posicion inicial)
    lista_x = np.array([])
    lista_y = np.array([])

    for filename in os.listdir(directory):
        if not filename.endswith(".csv"):
            continue

        file_path = os.path.join(directory, filename)
        x, y = get_positions_from_csv(file_path, GET_ONLY_FINDER)
        lista_x = np.append(lista_x, x)
        lista_y = np.append(lista_y, y)

    return lista_x, lista_y


# Para muchos agentes la visualización podría quedar demasiado llena y no se vería muy claro
# Mostramos 1 posición/Búsqueda
GET_ONLY_FINDER = False
caso_prueba = "mediano-indicios-1-agentes-1-fixed"
pos_x, pos_y = process_all("./TFG-Yago/resultados/" + caso_prueba)

# Para hacer la visualización necesitamos al menos 1 paso (2 posiciones)
# Tomar la posicion inicial y duplicarla
double_x = np.zeros((len(pos_x), 2))
double_y = np.zeros((len(pos_y), 2))
for i in range(len(pos_x)):
    double_x[i] = np.append(pos_x[i], pos_x[i])
    double_y[i] = np.append(pos_y[i], pos_y[i])


# Generar la visualización
# WARNING: No vamos a realizar comprobación de errores
# Como las pruebas ya se han ejecutado, asumimos que la configuración es correcta

params = json.load(open(f"./TFG-Yago/pruebas/{caso_prueba}.json"))

size = np.array(params["size"])
COV = np.array(params["cov"])
pesos = np.array(params.get("pesos", [None]))
indicios = np.array(params["indicios"])
if len(COV.shape) == 2:
    COV = np.array([COV] * len(indicios))

bk = calcular_prob(size, COV, indicios, pesos)
BK = [bk, bk]  # Duplicamos por la misma razón

indicio_elegido = params["indicio"]
indicio_elegido = int(indicio_elegido)
if indicio_elegido == -1:
    indicio_elegido = np.random.randint(0, len(indicios))
goal = params["obj_pos"]
if goal == [None]:
    goal = random_target(indicios, COV, indicio_elegido, 3)
goal = celda_mas_cercana(goal, bk) * np.ones_like(double_x)

double_z = params["height"] * np.ones_like(double_x)
pdmax = params["pdmax"]
dmax = params["dmax"]
sigma = params["sigma"]
sensor = SquareSensor(pdmax, dmax, sigma)


dibujar_animacion(
    len(double_x),
    double_x,
    double_y,
    double_z,
    BK,
    goal,
    size,
    1,
    0,
    sensor.perimetro,
    box_offset=0,
    agent_offset=0,
)

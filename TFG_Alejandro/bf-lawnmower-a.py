"""Búsqueda usando el algoritmo de fuerza bruta: Barrido de cortaceped (lawnmower search)"""

import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import numpy as np

from busquedas import lawnmower
from configurar import random_pos
from configurar.objetivo_a import celda_mas_proxima, random_target2
from configurar.inicio_a import random_pos_espacio_busq
from coordinates import plan_a
from extra import crear_dataframe, dibujar_animacion, guardar_dataframe
from extra import interfaz_a, dataframe

# Comprobar si se ha pasado un archivo de configuración
if len(sys.argv) not in [2, 3]:
    print(
        f"Uso: python {sys.argv[0]} <archivo_configuracion> [generar archivo plan y/[n]]"
    )
    sys.exit(1)

# Comprobar si se genera el archivo .plan
GENERAR_PLAN = True
if len(sys.argv) == 3:
    generar = sys.argv[2]
    if generar in ["yes", "y"]:
        GENERAR_PLAN = True
    elif generar not in ["no", "n"]:
        print(
            f"Uso: python {sys.argv[0]} <archivo_configuracion> [generar archivo plan y/[n]]"
        )
        sys.exit(1)

# Leer el archivo de configuración
file = sys.argv[1]

params = json.load(open(file))
#print(params)
seed = params["semilla"]
np.random.seed(seed)

size = np.array(params["size"])
COV = np.array(params["cov"])

indicios = np.array(params["indicios"])

# Si solo hay una covarianza, se asume que es la misma para todos los indicios
if len(COV.shape) == 2:
    COV = np.array([COV] * len(indicios))

bk = np.array(params["init_map"])

N_AGENTS = params["num_agents"]
HEIGHT = params["height"]

init_pos = np.array(params["init_pos"])
agent_seed = None

delta: float = params["mov_delta"]

init_pos_global = params["init_pos_global"][0] #Es una lista dentro de una lista, cojo la primera
#print(init_pos_global)
#Están al revés las coordenadas, se les da la vuelta
init_pos_global[0], init_pos_global[1] = init_pos_global[1], init_pos_global[0]

reference_coordinate = list(params["reference_coordinate"])
#Están al revés las coordenadas, se les da la vuelta
reference_coordinate[0], reference_coordinate[1] = reference_coordinate[1], reference_coordinate[0]

radio = params["radio"]

# Si las posiciones iniciales son None, generarlas de forma aleatoria

if np.all(init_pos==None):
    init_pos = random_pos_espacio_busq(bk)
    agent_seed = seed
# Comprobar que el número de agentes y posiciones iniciales coinciden
np.testing.assert_equal(
    len(init_pos), N_AGENTS, "Please, check the number of agents and initial positions"
)
# Añadir height a las posicones iniciales
heights = np.array([np.repeat(HEIGHT, N_AGENTS)])
init_pos = np.concatenate((init_pos, heights.T), axis=1)

separation = params["separation"]
# Parametros del sensor
pdmax = params["pdmax"]
dmax = params["dmax"]
sigma = params["sigma"]

indicio_elegido = params["indicio"]

goal = np.array(params["obj_pos"])
goal_seed = None
if indicio_elegido == None:
    # Comprobar que la posición para el objetivo no es None también
    np.testing.assert_raises(
        AssertionError,
        np.testing.assert_array_equal,
        np.array(indicio_elegido),
        np.array(goal),
        err_msg="El indicio elegido y la posición inicial del objetivo no pueden ser nulos al mismo tiempo",
    )


if indicio_elegido == -1:
    indicio_elegido = np.random.randint(0, len(indicios))

print(goal)
if np.all(goal==None):   
    goal = random_target2(bk) # Si no se ha definido la posición del objetivo, crear una aleatoria y asignar la como fija con la semilla
    print(goal)
    goal_seed = seed
else:
    goal = goal[0] # En caso de que se haya definido la posición inicial del objetivo, coger la lista de dentro
goal = celda_mas_proxima(goal, bk)

"""if goal == [None]:
    goal = random_target(indicios, COV, indicio_elegido, 3)
    goal_seed = seed
goal = celda_mas_cercana(goal, bk)"""

# Variables para la búsqueda
finder = None
total_steps = params["num_steps"]

tc = params["tam_cuadricula"]

# También se almacenan las coordenadas que definen el cuadrado del espacio de búsqueda (y se coge la primera lista y se le dan la vuelta a las posiciones de las coordenadas)
search_space_global_coords = params["search_space_global_coords"]
search_space_global_coords = search_space_global_coords[0]
for i in range(len(search_space_global_coords)):
    search_space_global_coords[i][0], search_space_global_coords[i][1] = search_space_global_coords[i][1], search_space_global_coords[i][0] 

print(search_space_global_coords)

# Seleccionar de entre las posiciones iniciales
elegido = np.random.randint(N_AGENTS)

# Inicializar listas para guardar los caminos
list_x = [np.array(pos[0]) for pos in init_pos]
list_y = [np.array(pos[1]) for pos in init_pos]
list_z = [np.array(pos[2]) for pos in init_pos]
BK = [bk]

new_list_x, new_list_y, new_list_z, steps, finder, bk_list = lawnmower(
    size, bk, goal, dmax, pdmax, sigma, init_pos[elegido], delta, separation, total_steps
)

# Guardar los nuevos valores
for i in range(N_AGENTS):
    list_x[i] = np.append(list_x[i], new_list_x)
    list_y[i] = np.append(list_y[i], new_list_y)
    list_z[i] = np.append(list_z[i], new_list_z)

BK += bk_list

# Mostrar resultados
df = crear_dataframe(
    N_AGENTS, list_x, list_y, list_z, goal, finder, agent_seed, goal_seed
)
print(df)
guardar_dataframe(
    df, "./resultados/", "lawnmower", file.split("/")[-1].split(".")[0]
)
#Lo estoy lanzando desde mi carpeta (TFG_Alejandro)
"""
dibujar_animacion(
    1, new_list_x, new_list_y, new_list_z, BK, goal, size, steps, seed, dmax, HEIGHT
)"""

# Reescalado de las coordenadas
list_x[0][1:] *= tc
list_y[0][1:] *= tc

# Dibujar el mapa con las dimensiones iniciales (las realistas, no los índices de la malla)
"""interfaz_a.dibujar_animacion_a(
    N_AGENTS, list_x, list_y, list_z, BK, goal, size, steps, seed, tc, dmax, HEIGHT
)"""

# Generar archvo .plan
if GENERAR_PLAN:
    latitude_0, longitude_0 = init_pos_global #mis coordenadas del centro del espacio de búsqueda
    altitude_0 = 0.0  # 880 m
    
    for i in range(len(list_x)):
        list_x[i] *= tc
        list_y[i] *= tc
    #Hay que pasar los arrays a listas (NO dejarlos como NumPy arrays)
    list_x = np.concatenate(list_x).tolist()
    list_y = np.concatenate(list_y).tolist()
    list_z = np.concatenate(list_z).tolist()
    #Tiene las coordenadas actualizadas de la parte de visualización
    plan_a.to_plan_a(list_x, list_y, list_z, altitude_0, latitude_0, longitude_0, "plan_prueba", radio, search_space_global_coords) #Las coordenads del polígono son las esquinas que definen el cuadrado del espacio de búsqueda

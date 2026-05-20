import json
import copy
import random
from pathlib import Path
import subprocess
from tqdm import tqdm
import requests
import os

TELEGRAM_TOKEN = "8340887367:AAG-uOUAQ2oVMrfhjM4wLeXA8hHxCGIt26E"
CHAT_ID = "2114172581"

def enviar_mensaje_telegram(mensaje):
    """
    Envía un mensaje de notificación vía Telegram
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Error enviando mensaje a Telegram:", e)


# Obtener el directorio donde está el script
SCRIPT_DIR = Path(__file__).parent.resolve()

# Crear carpetas necesarias (relativas al script)
CARPETA_JSON = SCRIPT_DIR / "json"
CARPETA_RESULTADOS = SCRIPT_DIR / "resultados_pruebas_masivas"

CARPETA_JSON.mkdir(exist_ok=True)
CARPETA_RESULTADOS.mkdir(exist_ok=True)

print(f"Carpetas creadas/verificadas:")
print(f"  - {CARPETA_JSON}")
print(f"  - {CARPETA_RESULTADOS}")

# Rutas de mapas (relativas al script)
mapa_mediano = SCRIPT_DIR / "pruebas" / "mediano-indicios-1-agentes-1-random.json"
mapa_grande = SCRIPT_DIR / "pruebas" / "grande-indicios-1-agentes-1-random.json"

# Verificar que existen los archivos
MAPAS = []
for mapa in [mapa_mediano, mapa_grande]:
    if mapa.exists():
        MAPAS.append(str(mapa))
        print(f"Encontrado: {mapa.name}")
    else:
        print(f"No encontrado: {mapa}")

if not MAPAS:
    print("\nERROR: No se encontraron archivos de mapas.")
    print(f"Directorio de búsqueda: {SCRIPT_DIR / 'pruebas'}")
    print(f"\nArchivos disponibles en pruebas/:")
    pruebas_dir = SCRIPT_DIR / "pruebas"
    if pruebas_dir.exists():
        for f in sorted(pruebas_dir.glob("*.json")):
            print(f"  - {f.name}")
    exit(1)

print(f"\nMapas a procesar: {len(MAPAS)}")

# Algoritmos a probar
ALGORITMOS = [
    "voraz-myope", "voraz-heur", "lawnmower", "expanding_sq",
    "ACO", "ABC", "BHA"
]

# Ruta del simulador (está en el directorio padre de TFG_Romeo)
alg = SCRIPT_DIR.parent / "bf-busqueda.py"

print(f"\nBuscando simulador en: {alg}")
if not alg.exists():
    print(f"No se encontró el simulador")
    # Intentar buscar en la misma carpeta
    alg_local = SCRIPT_DIR / "bf-busqueda.py"
    if alg_local.exists():
        alg = alg_local
        print(f"Encontrado en: {alg}")
    else:
        print("\nArchivos .py disponibles en el directorio padre:")
        for f in sorted(SCRIPT_DIR.parent.glob("*.py")):
            print(f"  - {f.name}")
        alg_input = input("\nIngresa la ruta correcta al simulador bf-busqueda.py: ")
        alg = Path(alg_input)
else:
    print(f"Simulador encontrado")

alg = str(alg)

# Funciones objetivo (solo para ACO, ABC, BHA)
FUNCIONES_OBJ = ["ET", "DTR", "MS", "ME"]

# Variaciones de agentes e indicios
NUM_AGENTES = [1, 3, 10]
NUM_INDICIOS = [1, 3, 10]

# Número de iteraciones por configuración
N_ITERACIONES = 1000

print("\n" + "="*60)
print("CONFIGURACIÓN CARGADA")
print("="*60)
print(f"  - Mapas: {len(MAPAS)}")
print(f"  - Algoritmos: {len(ALGORITMOS)}")
print(f"  - Iteraciones por configuración: {N_ITERACIONES}")
print(f"  - Carpeta JSON: {CARPETA_JSON}")
print(f"  - Carpeta resultados: {CARPETA_RESULTADOS}")
print("="*60 + "\n")


def modificar_config(base_config, algoritmo, funcion_obj, n_agents, n_indicios):
    """
    Modifica una configuración base con nuevos parámetros
    """
    config = copy.deepcopy(base_config)
    config["algoritmo_busqueda"] = algoritmo
    config["funcion_objetivo"] = funcion_obj if algoritmo in ["ACO", "ABC", "BHA"] else None
    config["num_agents"] = n_agents
    
    # Generar indicios aleatorios dentro del mapa
    size_x, size_y = config["size"]
    config["indicios"] = [
        [random.randint(0, size_x-5), random.randint(0, size_y-5)]
        for _ in range(n_indicios)
    ]
    
    # Configurar la carpeta de resultados con ruta absoluta
    # Usar str() para convertir Path a string, ya que JSON no soporta objetos Path
    config["carpeta_resultados"] = str(CARPETA_RESULTADOS.resolve()).replace("\\", "/")
    
    return config

def guardar_config(config, filename):
    """
    Guarda una configuración en formato JSON en la carpeta json/
    """
    ruta_completa = CARPETA_JSON / filename
    with open(ruta_completa, "w") as f:
        json.dump(config, f, indent=4)
    return str(ruta_completa)

def ejecutar_simulacion(ruta_config, n_iteraciones, simulador):
    """
    Ejecuta múltiples iteraciones de una simulación
    """
    # Cargar la configuración base UNA SOLA VEZ
    with open(ruta_config, "r") as f:
        base_config = json.load(f)
    
    for i in tqdm(range(n_iteraciones), desc="Iteraciones", unit="iter"):
        # Modificar solo la semilla
        config = copy.deepcopy(base_config)
        config["semilla"] = i
        
        # Sobrescribir el archivo de configuración con la nueva semilla
        with open(ruta_config, "w") as f:
            json.dump(config, f, indent=4)

        # Ejecutar el simulador
        result = subprocess.run(
            ["python3", simulador, ruta_config],
            capture_output=True, 
            text=True
        )
        
        # Opcional: mostrar errores si los hay
        if result.returncode != 0:
            print(f"\nError en iteración {i}:")
            print(result.stderr)

print("Funciones definidas")


for mapa in MAPAS:
    print(f"\n{'='*60}")
    print(f"Procesando mapa: {mapa}")
    print(f"{'='*60}\n")

    with open(mapa, "r") as f:
        config_base = json.load(f)

    # Calcular total de combinaciones
    total_combinaciones = (
        len(ALGORITMOS) * 
        len(NUM_AGENTES) * 
        len(NUM_INDICIOS) * 
        max(len(FUNCIONES_OBJ), 1)
    )
    
    with tqdm(total=total_combinaciones, desc="Combinaciones", unit="comb") as pbar:
        for algoritmo in ALGORITMOS:
            for n_agents in NUM_AGENTES:
                for n_indicios in NUM_INDICIOS:
                    # Solo usar funciones objetivo con algoritmos metaheurísticos
                    funciones = FUNCIONES_OBJ if algoritmo in ["ACO", "ABC", "BHA"] else [None]
                    
                    for funcion in funciones:
                        # Generar nombre corto del archivo de configuración
                        # Formato: mediano_ACO_ET_a1_i1.json (más corto para evitar problemas)
                        mapa_nombre = "med" if "mediano" in Path(mapa).stem else "gde"
                        filename = f"{mapa_nombre}_{algoritmo}"
                        if funcion:
                            filename += f"_{funcion}"
                        filename += f"_a{n_agents}_i{n_indicios}.json"
                        
                        # Crear y guardar configuración
                        config_mod = modificar_config(
                            config_base, algoritmo, funcion, n_agents, n_indicios
                        )
                        ruta_config = guardar_config(config_mod, filename)

                        # Ejecutar simulación
                        ejecutar_simulacion(ruta_config, N_ITERACIONES, alg)

                        # Notificar progreso
                        mensaje = (
                            f"Completado: {algoritmo} / FO={funcion} / "
                            f"agents={n_agents} / indicios={n_indicios}"
                        )
                        enviar_mensaje_telegram(mensaje)
                        print(mensaje)
                        
                        pbar.update(1)

enviar_mensaje_telegram("Todas las simulaciones han terminado.")
print("\n" + "="*60)
print("TODAS LAS SIMULACIONES HAN TERMINADO")
print("="*60)
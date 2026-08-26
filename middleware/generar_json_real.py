"""
Script de Middleware para el TFM de Juan Carlos
Traduce un mapa real exportado de SAREnv (matriz .npy y metadatos .geojson)
al formato JSON esperado por el simulador MTS, realizando la transformación
de coordenadas geográficas globales (Lat/Lon) a coordenadas de rejilla locales (X, Y).
"""

import os
import json
import shutil
import argparse
import numpy as np
from pyproj import Proj

def get_utm_epsg(lon: float, lat: float) -> str:
    """Calcula el código EPSG de la zona UTM para un punto geográfico dado."""
    zone = int((lon + 180) / 6) + 1
    return f"EPSG:{326 if lat >= 0 else 327}{zone}"

def main():
    parser = argparse.ArgumentParser(
        description="Traduce mapas de SAREnv (.npy + .geojson) al formato de simulación de MTS."
    )
    parser.add_argument(
        "--geojson",
        required=True,
        help="Ruta al archivo features.geojson exportado por SAREnv (contiene metadatos)."
    )
    parser.add_argument(
        "--npy",
        required=True,
        help="Ruta al archivo heatmap.npy exportado por SAREnv (matriz de probabilidad)."
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Ruta donde se guardará el archivo JSON de configuración para MTS."
    )
    parser.add_argument(
        "--agents",
        type=int,
        default=1,
        help="Número de agentes (drones) en la simulación (defecto: 1)."
    )
    parser.add_argument(
        "--algorithm",
        default="voraz-heur",
        help="Algoritmo de búsqueda por defecto en la simulación (defecto: voraz-heur)."
    )
    parser.add_argument(
        "--init_pos",
        help="Posición inicial manual de los agentes en formato 'x1,y1;x2,y2'. Si no se define, se calcula desde el LKP/IPP."
    )

    args = parser.parse_args()

    # 1. Comprobar que los archivos de entrada existen
    if not os.path.exists(args.geojson):
        print(f"Error: No se encontró el archivo GeoJSON en: {args.geojson}")
        return
    if not os.path.exists(args.npy):
        print(f"Error: No se encontró el archivo numpy .npy en: {args.npy}")
        return

    # 2. Cargar metadatos desde el GeoJSON de SAREnv
    print(f"Cargando metadatos desde: {args.geojson}")
    with open(args.geojson, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    try:
        center_point = metadata["center_point"] # [lon, lat]
        meter_per_bin = metadata["meter_per_bin"]
        bounds = metadata["bounds"] # [minx, miny, maxx, maxy] en metros proyectados
        env_type = metadata.get("environment_type", "flat")
        climate = metadata.get("climate", "temperate")
    except KeyError as e:
        print(f"Error: El archivo GeoJSON no contiene el campo de metadatos requerido: {e}")
        return

    # 3. Cargar la matriz de probabilidad
    print(f"Cargando matriz de probabilidad desde: {args.npy}")
    heatmap = np.load(args.npy)
    rows, cols = heatmap.shape
    size_mts = [cols, rows]
    print(f"Dimensiones del mapa leídas de .npy: {cols} columnas (X) x {rows} filas (Y)")

    # 4. Transformación de coordenadas del punto central (LKP/IPP) a la rejilla local
    lon, lat = center_point
    epsg_zone = get_utm_epsg(lon, lat)
    print(f"Punto de inicio geográfico (LKP/IPP): Lon={lon:.6f}, Lat={lat:.6f}")
    print(f"Zona UTM determinada: {epsg_zone}")

    # Proyección de WGS84 a UTM en metros
    proj_utm = Proj(epsg_zone)
    center_x, center_y = proj_utm(lon, lat)
    print(f"Coordenadas del centro en metros (UTM): X={center_x:.2f}, Y={center_y:.2f}")

    # Esquina inferior izquierda del mapa en metros proyectados
    minx, miny, _, _ = bounds
    print(f"Esquina inferior izquierda (bounds minx, miny): X={minx:.2f}, Y={miny:.2f}")

    # Distancia en metros y conversión a píxeles discretos (rejilla local)
    dx = center_x - minx
    dy = center_y - miny
    pixel_x = int(dx / meter_per_bin)
    pixel_y = int(dy / meter_per_bin)

    # Validar que caiga dentro de los límites de la matriz
    pixel_x = max(0, min(pixel_x, cols - 1))
    pixel_y = max(0, min(pixel_y, rows - 1))
    print(f"Posición calculada del LKP/IPP en la rejilla local de MTS: [{pixel_x}, {pixel_y}]")

    # 5. Configurar posiciones iniciales de los agentes
    init_positions = []
    if args.init_pos:
        # Parsear posiciones manuales ej. "10,10;15,15"
        try:
            for part in args.init_pos.split(";"):
                x_str, y_str = part.split(",")
                init_positions.append([int(x_str), int(y_str)])
            print(f"Usando posiciones iniciales manuales: {init_positions}")
        except Exception as e:
            print(f"Error al parsear --init_pos '{args.init_pos}': {e}. Se usará el LKP por defecto.")
            init_positions = []

    if not init_positions:
        # Usar la posición del LKP/IPP como posición inicial para todos los agentes
        # Si hay más de un agente, añadimos un pequeño desplazamiento para evitar que colisionen en la misma celda de inicio
        for i in range(args.agents):
            offset = i * 2 # desplazamiento ligero en diagonal
            ax = max(0, min(pixel_x + offset, cols - 1))
            ay = max(0, min(pixel_y + offset, rows - 1))
            init_positions.append([ax, ay])
        print(f"Usando posiciones iniciales generadas desde LKP/IPP: {init_positions}")

    # 6. Preparar el JSON de configuración para MTS
    # El archivo binario de la matriz (.npy) se llamará igual que el JSON pero con extensión .npy
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    
    json_filename = os.path.basename(args.out)
    base_name, _ = os.path.splitext(json_filename)
    npy_filename = f"{base_name}.npy"
    npy_dest_path = os.path.join(out_dir, npy_filename)

    # Copiar el archivo .npy al destino con el nombre del escenario
    print(f"Copiando matriz .npy al directorio de destino: {npy_dest_path}")
    shutil.copy(args.npy, npy_dest_path)

    # Identificar el punto de máxima probabilidad global en el mapa para colocar los indicios de MTS
    idx_max = np.unravel_index(np.argmax(heatmap), heatmap.shape)
    y_max, x_max = int(idx_max[0]), int(idx_max[1])
    print(f"Punto de máxima probabilidad en la matriz (índice global): [{x_max}, {y_max}] (Probabilidad: {heatmap[y_max, x_max]:.6e})")

    # Estructura del JSON compatible con MTS
    data = {
        "version": "1.1-SAREnv-Real",
        "size": size_mts,
        "ruta_mapa_real": npy_filename, # Nombre relativo del archivo .npy en la misma carpeta
        "num_agents": args.agents,
        "height": 10,
        "init_pos": init_positions,
        "mov_delta": 1,
        "posible_moves": "8 dir",
        "min_dist": 3,
        "lambda": 0.5,
        "num_steps": 1000,
        "pdmax": 0.8,
        "dmax": 2.1,
        "sigma": 0.7,
        "separation": 2,
        "plan": False,
        "algoritmo_busqueda": args.algorithm,
        "funcion_objetivo": "ET",
        "optimization": "min",
        "show_evolution": True,
        
        # Parámetros para algoritmos bioinspirados por si acaso
        "__COMENTARIO_ACO__": "=== PARAMETROS ACO (HORMIGAS) ===",
        "n_ants": 20,
        "n_iterations_aco": 5,
        "alpha": 1.0,
        "beta": 3.0,
        "rho": 0.1,
        "local_rho": 0.05,
        "Q": 1.0,

        "__COMENTARIO_ABC__": "=== PARAMETROS ABC (ABEJAS) ===",
        "n_iterations_abc": 10,
        "limit": 10,
        "n_onlookers": 1,
        "n_employed": 1,

        "__COMENTARIO_BHA__": "=== PARAMETROS BHA (AGUJERO NEGRO) ===",
        "n_iterations_bha": 10,
        "n_stars": 5,

        # Configuración de indicios para la búsqueda
        "indicios": [[pixel_x, pixel_y]], # El LKP/IPP actúa como indicio principal
        "cov": [[2, 0], [0, 2]],
        "pesos": [1.0],
        "obj_pos": [None], # MTS ubicará dinámicamente al objetivo en la simulación
        "indicio": -1,
        "semilla": 0
    }

    # Guardar archivo JSON
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print(f"Archivo de configuración JSON generado con éxito en: {args.out}")
    print(f"Dimensiones inyectadas: X={cols}, Y={rows}")
    print(f"Middleware finalizado correctamente.\n")

if __name__ == "__main__":
    main()

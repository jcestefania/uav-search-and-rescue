import os
import sys
import json
import subprocess
import glob

# Resolucion dinamica y automatica de rutas (detecta SAREnv y raiz de MTS)
search_dir = os.path.abspath(os.getcwd())
while search_dir and search_dir != os.path.dirname(search_dir):
    sarenv_candidate = os.path.join(search_dir, "SAREnv")
    if os.path.exists(sarenv_candidate) and sarenv_candidate not in sys.path:
        sys.path.insert(0, sarenv_candidate)
    sarenv_pkg = os.path.join(search_dir, "sarenv")
    if os.path.isdir(sarenv_pkg) and search_dir not in sys.path:
        sys.path.insert(0, search_dir)
    if os.path.isdir(os.path.join(search_dir, "TFM_JC")) and search_dir not in sys.path:
        sys.path.insert(0, search_dir)
    search_dir = os.path.dirname(search_dir)

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely.geometry
from shapely.geometry import Point, LineString
from sarenv import DataGenerator, CLIMATE_TEMPERATE, ENVIRONMENT_TYPE_FLAT
import sarenv.utils.lost_person_behavior as lpb
from sarenv.analytics.metrics import PathEvaluator

# Polígono exacto de la Casa de Campo de Madrid
CASA_DE_CAMPO_POLY = shapely.geometry.Polygon([
    [-3.753046089833776, 40.44343778644211],
    [-3.771067897299357, 40.43808936530237],
    [-3.780967823387276, 40.41887000168707],
    [-3.773618938561301, 40.40203996553611],
    [-3.724145972222016, 40.41588490845162],
    [-3.753046089833776, 40.44343778644211]
])

# ==============================================================================
# CONFIGURACIÓN OFICIAL DEL MANUAL DE ROBERT KOESTER (LOST PERSON BEHAVIOR)
# ==============================================================================

# 1. Perfil Autista (Estructura 45%, Carretera 18%, Agua 9%, Matorral 9%, Bosque 9%, Campo 9%)
AUTISTA_WEIGHTS = {
    'structure': 0.45, 'road': 0.18, 'water': 0.09,
    'brush': 0.09, 'woodland': 0.09, 'field': 0.09
}
AUTISTA_RADIIS = [0.6, 1.6, 3.7, 15.2]

# 2. Perfil Demencia (Estructura 20%, Carretera 18%, Bosque 17%, Campo 14%, Lineal 9%, Drenaje 9%, Agua 7%, Maleza 6%)
DEMENCIA_WEIGHTS = {
    'structure': 0.20, 'road': 0.18, 'woodland': 0.17, 'field': 0.14,
    'linear': 0.09, 'drainage': 0.09, 'water': 0.07, 'scrub': 0.06
}
DEMENCIA_RADIIS = [0.3, 1.0, 2.4, 12.8]

# 3. Perfil Senderista (Lineal 25%, Campo 14%, Estructura 13%, Carretera 13%, Drenaje 12%, Agua 8%, Bosque 7%, Rocoso 4%, Matorral 3%, Maleza 2%)
SENDERISTA_WEIGHTS = {
    'linear': 0.25, 'field': 0.14, 'structure': 0.13, 'road': 0.13,
    'drainage': 0.12, 'water': 0.08, 'woodland': 0.07, 'rock': 0.04,
    'brush': 0.03, 'scrub': 0.02
}
SENDERISTA_RADIIS = [0.6, 1.8, 3.2, 9.9]


def generar_mapa_perfil(nombre_perfil, pesos, radios):
    """
    Genera el heatmap probabilístico, aplica el filtro físico de restricciones (agua y estructuras),
    normaliza el mapa resultante y genera los archivos vectoriales para un perfil LPB específico.
    """
    print(f"=== Iniciando generación para el perfil: {nombre_perfil.upper()} ===")
    
    # Instanciamos el generador de SAREnv
    data_gen = DataGenerator()
    
    # 1. Inyectar pesos personalizados en el lost_person_behavior de SAREnv
    lpb.FEATURE_PROBABILITIES = pesos
    lpb.RADIUS_FLAT_TEMPERATE = radios
    
    # Definir ruta de salida
    output_dir = f"TFM_JC/resultados/casa_de_campo_{nombre_perfil}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. Exportar el dataset a partir del polígono de la Casa de Campo
    # Usamos resolución de 10 metros por celda para coincidir con la Memoria
    print(f"Descargando datos cartográficos y calculando probabilidades para {nombre_perfil}...")
    data_gen.export_dataset_from_polygon(
        polygon=CASA_DE_CAMPO_POLY,
        output_directory=output_dir,
        environment_climate=CLIMATE_TEMPERATE,
        environment_type=ENVIRONMENT_TYPE_FLAT,
        meter_per_bin=10,
    )
    
    # 3. Aplicar Filtro de Restricciones (Agua y Estructuras)
    heatmap_path = os.path.join(output_dir, "heatmap.npy")
    geojson_path = os.path.join(output_dir, "features.geojson")
    
    if os.path.exists(heatmap_path) and os.path.exists(geojson_path):
        with open(geojson_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        bounds = metadata["bounds"] # [minx, miny, maxx, maxy]
        meter_per_bin = metadata["meter_per_bin"]
        center_point = metadata["center_point"]
        
        lon, lat = center_point
        zone = int((lon + 180) / 6) + 1
        epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
        
        # Cargar la matriz original
        heatmap = np.load(heatmap_path)
        rows, cols = heatmap.shape
        
        # Guardar una copia sin filtrar para visualizaciones de "Antes y Después"
        np.save(os.path.join(output_dir, "heatmap_unfiltered.npy"), heatmap)
        
        # Cargar los elementos vectoriales en UTM
        gdf = gpd.read_file(geojson_path).to_crs(epsg)
        
        # Identificar capas físicas de agua profunda y edificaciones
        restrictive_features = gdf[gdf["feature_type"].isin(["water", "structure"])]
        geometries = restrictive_features.geometry.tolist()
        
        if len(geometries) > 0:
            from affine import Affine
            from rasterio.features import rasterize
            
            # Usamos escala Y positiva para origin='lower' (row 0 = miny)
            minx, miny, _, _ = bounds
            transform = Affine(meter_per_bin, 0, minx, 0, meter_per_bin, miny)
            
            # Generar máscara binaria (0 en agua/estructuras, 1 fuera)
            mask = rasterize(
                geometries,
                out_shape=(rows, cols),
                transform=transform,
                fill=1,
                default_value=0
            )
        else:
            mask = np.ones((rows, cols), dtype=np.uint8)
            
        # Multiplicar el heatmap original por la máscara de restricciones
        filtered_heatmap = heatmap * mask
        sum_filtered = np.sum(filtered_heatmap)
        
        # Volver a normalizar para asegurar que sume 1.0
        if sum_filtered > 0:
            heatmap = filtered_heatmap / sum_filtered
        else:
            heatmap = filtered_heatmap
            
        # Sobrescribir el heatmap.npy en disco con la versión filtrada y normalizada
        np.save(heatmap_path, heatmap)
        feat_path = os.path.join(output_dir, "heatmap_features.npy")
        if os.path.exists(feat_path):
            feat_map = np.load(feat_path)
            feat_filtered = feat_map * mask
            f_sum = np.sum(feat_filtered)
            if f_sum > 0:
                feat_map = feat_filtered / f_sum
            np.save(feat_path, feat_map)
        print(f"¡Filtro físico aplicado con éxito! {len(geometries)} polígonos (agua/estructuras) puestos a 0.")
        print(f"Mapa de calor normalizado y sobrescrito en: {heatmap_path}\n")
    else:
        print("Error: No se encontró heatmap.npy o features.geojson para aplicar restricciones.")

def ejecutar_middleware(nombre_perfil):
    """
    Invoca el script de middleware para transformar los datos de SAREnv al JSON de MTS.
    """
    geojson_path = f"TFM_JC/resultados/casa_de_campo_{nombre_perfil}/features.geojson"
    npy_path = f"TFM_JC/resultados/casa_de_campo_{nombre_perfil}/heatmap.npy"
    out_json = f"TFM_JC/resultados/casa_de_campo_{nombre_perfil}/escenario_{nombre_perfil}.json"
    
    # Argumentos para el middleware
    cmd = [
        sys.executable,
        "TFM_JC/scripts/generar_json_real.py",
        "--geojson", geojson_path,
        "--npy", npy_path,
        "--out", out_json,
        "--agents", "1",            # 1 Dron de búsqueda (evita colisiones en MTS)
        "--algorithm", "voraz-heur"   # Algoritmo base inicial
    ]
    
    print(f"Ejecutando middleware para: escenario_{nombre_perfil}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"¡JSON generado correctamente en!: {out_json}")
    else:
        print(f"Error al ejecutar middleware para {nombre_perfil}:\n{res.stderr}")

def lanzar_benchmark_simulaciones(semillas_count=50, bateria_pasos=1000, num_drones=1, pdmax=0.8, dmax=2.1, sigma=0.7, goal_pos=None):
    """
    Ejecuta en lote todas las combinaciones de perfiles, algoritmos y semillas
    inyectando los parámetros configurados.
    """
    perfiles = ["autista", "demencia", "senderista"]
    algoritmos = ["voraz-heur", "ACO", "ABC", "BHA", "lawnmower", "expanding_sq"]
    semillas = range(semillas_count)
    
    MTS_DIR = os.getcwd()
    total_runs = len(perfiles) * len(algoritmos) * semillas_count
    print(f"Iniciando benchmark masivo en {MTS_DIR}.")
    print(f"Total de ejecuciones planeadas: {total_runs}\n")
    
    for perfil in perfiles:
        json_path = os.path.abspath(f"TFM_JC/resultados/casa_de_campo_{perfil}/escenario_{perfil}.json")
        
        # Leer la configuración base
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        # Configurar para ejecución desatendida/headless e inyectar parámetros
        config["dibujar_animacion"] = False
        config["show_evolution"] = False
        config["num_steps"] = bateria_pasos
        config["num_agents"] = num_drones
        config["pdmax"] = pdmax
        config["dmax"] = dmax
        config["sigma"] = sigma
        
        # Inyectar posición del objetivo (víctima)
        if goal_pos is None:
            config["obj_pos"] = [None]
        else:
            config["obj_pos"] = goal_pos
            
        # Si hay más de un agente, reposicionamos en diagonal para evitar colisiones iniciales
        if num_drones > 1:
            lkp_x, lkp_y = config["init_pos"][0]
            config["init_pos"] = [[lkp_x + i*2, lkp_y + i*2] for i in range(num_drones)]
        
        print(f"===============================================")
        print(f"Iniciando simulaciones para el Perfil: {perfil.upper()}")
        print(f"===============================================")
        
        for alg in algoritmos:
            print(f"-> Ejecutando algoritmo: {alg}...")
            for seed in semillas:
                # Determinar nombre del archivo de trayectoria para comprobar si ya existe
                alg_file = "expanding" if alg == "expanding_sq" else (
                    "lawnmower" if alg == "lawnmower" else (
                        f"bf_{alg.lower()}_ET" if alg in ["ACO", "ABC", "BHA"] else alg
                    )
                )
                resultados_dir = os.path.abspath(f"TFM_JC/resultados/escenario_{perfil}")
                traj_file = os.path.join(resultados_dir, f"{alg_file}-{seed}-traj.json")
                if os.path.exists(traj_file):
                    continue
                
                config["algoritmo_busqueda"] = alg
                config["semilla"] = seed
                
                # Guardar en caliente para que bf-busqueda.py lo lea
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                
                # Lanzar el proceso de búsqueda en MTS
                cmd = [sys.executable, "bf-busqueda.py", json_path]
                res = subprocess.run(cmd, cwd=MTS_DIR, capture_output=True, text=True)
                
                if res.returncode != 0:
                    print(f"   [ERROR] Falló semilla {seed} de {alg}: {res.stderr}")
                    break
            print(f"   Completadas las {semillas_count} semillas para {alg}.")

def generar_y_guardar_victimas_montecarlo(nombre_perfil, n_victimas=1000):
    """
    Genera 1000 víctimas informadas y 1000 ciegas aplicando restricciones físicas de agua y estructuras.
    """
    output_dir = f"TFM_JC/resultados/casa_de_campo_{nombre_perfil}"
    geojson_path = os.path.join(output_dir, "features.geojson")
    heatmap_path = os.path.join(output_dir, "heatmap.npy")
    
    # Cargar metadatos y features
    with open(geojson_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    bounds = metadata["bounds"]  # [minx, miny, maxx, maxy] en UTM
    center_point = metadata["center_point"]
    meter_per_bin = metadata["meter_per_bin"]
    
    # Proyección UTM de la Casa de Campo
    lon, lat = center_point
    zone = int((lon + 180) / 6) + 1
    epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
    
    # Cargar el GeoJSON y reproyectar a UTM
    gdf = gpd.read_file(geojson_path).to_crs(epsg)
    heatmap = np.load(heatmap_path)
    
    # Identificar capas físicas restrictivas
    water_bodies = gdf[gdf["feature_type"] == "water"]
    structures = gdf[gdf["feature_type"] == "structure"]
    
    minx, miny, _, _ = bounds
    
    # 1. GENERACIÓN DE VÍCTIMAS INFORMADAS (Por Heatmap)
    flat_heatmap = heatmap.flatten()
    flat_indices = np.arange(len(flat_heatmap))
    probs = flat_heatmap / np.sum(flat_heatmap)
    
    informadas = []
    intentos = 0
    while len(informadas) < n_victimas and intentos < 100:
        # Muestreamos lotes grandes para eficiencia espacial
        batch = np.random.choice(flat_indices, size=(n_victimas - len(informadas)) * 5, p=probs)
        for idx in batch:
            y_idx, x_idx = np.unravel_index(idx, heatmap.shape)
            x_utm = minx + x_idx * meter_per_bin + 0.5 * meter_per_bin
            y_utm = miny + y_idx * meter_per_bin + 0.5 * meter_per_bin
            pt = Point(x_utm, y_utm)
            
            # Filtros de transitabilidad
            in_water = False
            if not water_bodies.empty:
                matches = water_bodies.sindex.query(pt, predicate="intersects")
                if len(matches) > 0 and any(water_bodies.iloc[matches].intersects(pt)):
                    in_water = True
            
            in_struct = False
            if not structures.empty:
                matches = structures.sindex.query(pt, predicate="intersects")
                if len(matches) > 0 and any(structures.iloc[matches].intersects(pt)):
                    in_struct = True
            
            if not in_water and not in_struct:
                informadas.append(pt)
                if len(informadas) == n_victimas:
                    break
        intentos += 1
        
    # 2. GENERACIÓN DE VÍCTIMAS CIEGAS (Uniforme en Casa de Campo)
    casa_de_campo_utm = gpd.GeoDataFrame(geometry=[CASA_DE_CAMPO_POLY], crs="EPSG:4326").to_crs(epsg).geometry.iloc[0]
    c_minx, c_miny, c_maxx, c_maxy = casa_de_campo_utm.bounds
    
    ciegas = []
    intentos = 0
    while len(ciegas) < n_victimas and intentos < 100:
        xs = np.random.uniform(c_minx, c_maxx, size=(n_victimas - len(ciegas)) * 10)
        ys = np.random.uniform(c_miny, c_maxy, size=(n_victimas - len(ciegas)) * 10)
        for x_val, y_val in zip(xs, ys):
            pt = Point(x_val, y_val)
            
            if not casa_de_campo_utm.contains(pt):
                continue
                
            in_water = False
            if not water_bodies.empty:
                matches = water_bodies.sindex.query(pt, predicate="intersects")
                if len(matches) > 0 and any(water_bodies.iloc[matches].intersects(pt)):
                    in_water = True
            
            in_struct = False
            if not structures.empty:
                matches = structures.sindex.query(pt, predicate="intersects")
                if len(matches) > 0 and any(structures.iloc[matches].intersects(pt)):
                    in_struct = True
            
            if not in_water and not in_struct:
                ciegas.append(pt)
                if len(ciegas) == n_victimas:
                    break
        intentos += 1
        
    # Guardar en formato GeoJSON para auditoría visual e inyección en el evaluador
    gdf_inf = gpd.GeoDataFrame(geometry=informadas, crs=epsg)
    gdf_inf.to_file(os.path.join(output_dir, "victimas_informadas.geojson"), driver="GeoJSON")
    
    gdf_blind = gpd.GeoDataFrame(geometry=ciegas, crs=epsg)
    gdf_blind.to_file(os.path.join(output_dir, "victimas_ciegas.geojson"), driver="GeoJSON")
    
    print(f"Perfil {nombre_perfil.upper()}: 1000 víctimas informadas y 1000 ciegas generadas con éxito.")

def evaluar_todas_las_pruebas():
    """
    Carga todas las trayectorias JSON guardadas por MTS y calcula las métricas usando PathEvaluator.
    """
    perfiles = ["autista", "demencia", "senderista"]
    # Los nombres de archivos creados por el wrapper unificado de MTS
    mapeo_alg = {
        "voraz-heur": "voraz-heur",
        "ACO": "bf_aco_ET",
        "ABC": "bf_abc_ET",
        "BHA": "bf_bha_ET",
        "lawnmower": "lawnmower",
        "expanding_sq": "expanding"
    }
    
    resultados_filas = []
    
    for perfil in perfiles:
        output_dir = f"TFM_JC/resultados/casa_de_campo_{perfil}"
        geojson_path = os.path.join(output_dir, "features.geojson")
        heatmap_path = os.path.join(output_dir, "heatmap.npy")
        
        # Cargar mapa e información geográfica
        with open(geojson_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        bounds = metadata["bounds"]  # [minx, miny, maxx, maxy]
        center_point = metadata["center_point"]
        meter_per_bin = metadata["meter_per_bin"]
        
        lon, lat = center_point
        zone = int((lon + 180) / 6) + 1
        epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
        
        heatmap = np.load(heatmap_path)
        
        # Cargar las víctimas previamente guardadas
        g_inf = gpd.read_file(os.path.join(output_dir, "victimas_informadas.geojson"))
        g_blind = gpd.read_file(os.path.join(output_dir, "victimas_ciegas.geojson"))
        
        # Instanciar los evaluadores de SAREnv (uno para informadas y otro para ciegas)
        pe_inf = PathEvaluator(
            heatmap=heatmap,
            extent=bounds,
            victims=g_inf,
            fov_deg=90.0,      # FOV de la memoria
            altitude=50.0,     # Altitud de la memoria
            meters_per_bin=meter_per_bin
        )
        
        pe_blind = PathEvaluator(
            heatmap=heatmap,
            extent=bounds,
            victims=g_blind,
            fov_deg=90.0,
            altitude=50.0,
            meters_per_bin=meter_per_bin
        )
        
        # Directorio donde MTS guardó los resultados de la simulación
        resultados_dir = f"TFM_JC/resultados/escenario_{perfil}"
        
        minx, miny, _, _ = bounds
        
        print(f"Evaluando resultados en: {resultados_dir}...")
        
        for alg_display, alg_file in mapeo_alg.items():
            # Buscar todas las trayectorias de este algoritmo
            pattern = os.path.join(resultados_dir, f"{alg_file}-*-traj.json")
            traj_files = glob.glob(pattern)
            
            if not traj_files:
                print(f"   [AVISO] No se encontraron archivos de trayectorias para {alg_display} ({pattern})")
                continue
                
            for t_file in traj_files:
                base = os.path.basename(t_file)
                seed = int(base.split("-")[-2])
                
                with open(t_file, "r", encoding="utf-8") as f:
                    data_t = json.load(f)
                
                list_x = data_t["list_x"][0]
                list_y = data_t["list_y"][0]
                
                coords = []
                for x_idx, y_idx in zip(list_x, list_y):
                    x_utm = minx + x_idx * meter_per_bin + 0.5 * meter_per_bin
                    y_utm = miny + y_idx * meter_per_bin + 0.5 * meter_per_bin
                    coords.append((x_utm, y_utm))
                
                if len(coords) < 2:
                    linea_dron = LineString([coords[0], coords[0]]) if coords else LineString()
                else:
                    linea_dron = LineString(coords)
                
                res_inf = pe_inf.calculate_all_metrics([linea_dron], discount_factor=0.999)
                res_blind = pe_blind.calculate_all_metrics([linea_dron], discount_factor=0.999)
                
                resultados_filas.append({
                    "Perfil": perfil,
                    "Algoritmo": alg_display,
                    "Semilla": seed,
                    "Pasos": len(list_x) - 1,
                    "Distancia_km": res_inf["total_path_length"],
                    "Area_Covered_km2": res_inf["area_covered"],
                    "Likelihood_Score": res_inf["total_likelihood_score"],
                    "Acierto_Informada": res_inf["victim_detection_metrics"]["percentage_found"],
                    "Acierto_Ciega": res_blind["victim_detection_metrics"]["percentage_found"]
                })
                
    df_global = pd.DataFrame(resultados_filas)
    df_global.to_csv("TFM_JC/resultados/resultados_evaluacion_tfm.csv", index=False)
    print(f"\n¡Evaluación finalizada! Tabla general de resultados guardada en: TFM_JC/resultados/resultados_evaluacion_tfm.csv")
    return df_global


def verificar_restriccion_agua_edificios(nombre_perfil):
    """
    Verifica mediante aserción en código y estadísticas que los polígonos de agua y edificaciones
    tienen una probabilidad de exactamente 0.0 en el heatmap final.
    """
    output_dir = f"TFM_JC/resultados/casa_de_campo_{nombre_perfil}"
    heatmap_path = os.path.join(output_dir, "heatmap.npy")
    geojson_path = os.path.join(output_dir, "features.geojson")
    
    if not (os.path.exists(heatmap_path) and os.path.exists(geojson_path)):
        raise FileNotFoundError(f"No se encontraron archivos de mapa para {nombre_perfil}")
        
    heatmap = np.load(heatmap_path)
    with open(geojson_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    bounds = meta["bounds"]
    meter_per_bin = meta["meter_per_bin"]
    center_point = meta["center_point"]
    
    lon, lat = center_point
    zone = int((lon + 180) / 6) + 1
    epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
    
    gdf = gpd.read_file(geojson_path).to_crs(epsg)
    restrictive_features = gdf[gdf["feature_type"].isin(["water", "structure"])]
    geometries = restrictive_features.geometry.tolist()
    
    if len(geometries) > 0:
        from affine import Affine
        from rasterio.features import rasterize
        
        minx, miny, _, _ = bounds
        transform = Affine(meter_per_bin, 0, minx, 0, meter_per_bin, miny)
        
        mask = rasterize(
            geometries,
            out_shape=heatmap.shape,
            transform=transform,
            fill=1,
            default_value=0
        )
        
        restricted_vals = heatmap[mask == 0]
        mean_restricted = float(np.mean(restricted_vals)) if len(restricted_vals) > 0 else 0.0
        max_restricted = float(np.max(restricted_vals)) if len(restricted_vals) > 0 else 0.0
        
        print(f"=== Comprobación de Restricción Física a 0.0 ({nombre_perfil.upper()}) ===")
        print(f"Número de polígonos restringidos (agua/edificios): {len(geometries)}")
        print(f"Media de densidad de probabilidad en celdas restringidas: {mean_restricted:.8f}")
        print(f"Máximo valor de probabilidad en celdas restringidas: {max_restricted:.8f}")
        
        assert np.isclose(max_restricted, 0.0), f"Error: Se detectó probabilidad > 0 ({max_restricted}) en celdas restringidas."
        print("OK - ASERCION CORRECTA: Las masas de agua y edificaciones valen exactamente 0.0.\n")
        return True, mean_restricted, max_restricted
    else:
        print("No se encontraron geometrías de agua/estructuras para comprobar.")
        return True, 0.0, 0.0

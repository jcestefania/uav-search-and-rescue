import os
import sys
# Inyectar la ruta local de SAREnv para que pueda ser importado
sys.path.insert(0, r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\SAREnv")
import json
import subprocess
import numpy as np
import shapely.geometry
from shapely.geometry import Point, LineString
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob

# Configurar UTF-8 para evitar problemas de codificación en consola Windows
if sys.platform.startswith('win'):
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 1. Definición de Constantes y Polígono de la Casa de Campo
CASA_DE_CAMPO_POLY = shapely.geometry.Polygon([
    [-3.753046089833776, 40.44343778644211],
    [-3.771067897299357, 40.43808936530237],
    [-3.780967823387276, 40.41887000168707],
    [-3.773618938561301, 40.40203996553611],
    [-3.724145972222016, 40.41588490845162],
    [-3.753046089833776, 40.44343778644211]
])

AUTISTA_WEIGHTS = {
    "structure": 0.45, "road": 0.18, "water": 0.09, "brush": 0.045, 
    "scrub": 0.045, "woodland": 0.09, "field": 0.09, "linear": 0.0, 
    "drainage": 0.0, "rock": 0.0
}
AUTISTA_RADIUS = [0.6, 1.6, 3.7, 15.2]

DEMENCIA_WEIGHTS = {
    "structure": 0.20, "road": 0.18, "woodland": 0.17, "field": 0.14,
    "linear": 0.09, "drainage": 0.09, "water": 0.07, "brush": 0.03, 
    "scrub": 0.03, "rock": 0.0
}
DEMENCIA_RADIUS = [0.3, 1.0, 2.4, 12.8]

SENDERISTA_WEIGHTS = {
    "linear": 0.25, "field": 0.14, "structure": 0.13, "road": 0.13,
    "drainage": 0.12, "water": 0.08, "woodland": 0.07, "rock": 0.04, 
    "brush": 0.03, "scrub": 0.02
}
SENDERISTA_RADIUS = [0.6, 1.8, 3.2, 9.9]

def main():
    print("=========================================================================")
    print("INICIANDO AUTOMATIZACIÓN DE EXPERIMENTOS DE EXPERIMENTACIÓN TFM (FASE 5)")
    print("=========================================================================")
    
    # Directorio base de ejecución: asumimos que se ejecuta desde la raíz de MTS
    MTS_DIR = os.getcwd()
    print(f"Directorio de trabajo actual (MTS Root): {MTS_DIR}")
    
    # -------------------------------------------------------------------------
    # FASE 1: Generación de Mapas de Calor con SAREnv
    # -------------------------------------------------------------------------
    print("\n>>> FASE 1: Generando mapas de calor en SAREnv con resolución de 10 metros...")
    from sarenv import DataGenerator, CLIMATE_TEMPERATE, ENVIRONMENT_TYPE_FLAT
    
    def generar_mapa(nombre, pesos, radios):
        print(f"-> Generando mapa para perfil: {nombre.upper()}")
        data_gen = DataGenerator()
        import sarenv.utils.lost_person_behavior as lpb
        lpb.FEATURE_PROBABILITIES = pesos
        lpb.RADIUS_FLAT_TEMPERATE = radios
        
        output_dir = f"TFM_JC/resultados/casa_de_campo_{nombre}"
        os.makedirs(output_dir, exist_ok=True)
        
        data_gen.export_dataset_from_polygon(
            polygon=CASA_DE_CAMPO_POLY,
            output_directory=output_dir,
            environment_climate=CLIMATE_TEMPERATE,
            environment_type=ENVIRONMENT_TYPE_FLAT,
            meter_per_bin=10
        )
        print(f"   [OK] Perfil {nombre} guardado en {output_dir}")
        
    generar_mapa("autista", AUTISTA_WEIGHTS, AUTISTA_RADIUS)
    generar_mapa("demencia", DEMENCIA_WEIGHTS, DEMENCIA_RADIUS)
    generar_mapa("senderista", SENDERISTA_WEIGHTS, SENDERISTA_RADIUS)
    
    # -------------------------------------------------------------------------
    # FASE 2: Ejecutar el Middleware (Conversión a JSON de MTS)
    # -------------------------------------------------------------------------
    print("\n>>> FASE 2: Traduciendo mapas reales al formato JSON de MTS...")
    
    def ejecutar_mid(nombre):
        geojson_path = f"TFM_JC/resultados/casa_de_campo_{nombre}/features.geojson"
        npy_path = f"TFM_JC/resultados/casa_de_campo_{nombre}/heatmap.npy"
        out_json = f"TFM_JC/resultados/casa_de_campo_{nombre}/escenario_{nombre}.json"
        
        cmd = [
            sys.executable,
            "TFM_JC/scripts/generar_json_real.py",
            "--geojson", geojson_path,
            "--npy", npy_path,
            "--out", out_json,
            "--agents", "1",
            "--algorithm", "voraz-heur"
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"   [OK] Escenario JSON para {nombre} creado con éxito.")
        else:
            print(f"   [ERROR] Error en middleware para {nombre}:\n{res.stderr}")
            
    ejecutar_mid("autista")
    ejecutar_mid("demencia")
    ejecutar_mid("senderista")
    
    # -------------------------------------------------------------------------
    # FASE 3: Lanzar Simulaciones Masivas en MTS (50 semillas x 4 algoritmos)
    # -------------------------------------------------------------------------
    print("\n>>> FASE 3: Ejecutando simulaciones masivas en MTS (600 corridas en total)...")
    perfiles = ["autista", "demencia", "senderista"]
    algoritmos = ["voraz-heur", "ACO", "ABC", "BHA", "lawnmower", "expanding_sq"]
    num_semillas = 50
    
    for perfil in perfiles:
        json_path = f"TFM_JC/resultados/casa_de_campo_{perfil}/escenario_{perfil}.json"
        
        # Asegurar directorio de resultados del escenario
        resultados_dir = f"TFM_JC/resultados/escenario_{perfil}"
        os.makedirs(resultados_dir, exist_ok=True)
        
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        config["dibujar_animacion"] = False
        config["num_steps"] = 1000
        config["show_evolution"] = False
        
        print(f"-> Perfil: {perfil.upper()}")
        for alg in algoritmos:
            print(f"   - Ejecutando algoritmo: {alg} ({num_semillas} semillas)...")
            for seed in range(num_semillas):
                # Determinar nombre del archivo de trayectoria para comprobar si ya existe
                alg_file = "expanding" if alg == "expanding_sq" else (
                    "lawnmower" if alg == "lawnmower" else (
                        f"bf_{alg.lower()}_ET" if alg in ["ACO", "ABC", "BHA"] else alg
                    )
                )
                traj_file = os.path.join(resultados_dir, f"{alg_file}-{seed}-traj.json")
                if os.path.exists(traj_file):
                    continue
                    
                config["algoritmo_busqueda"] = alg
                config["semilla"] = seed
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                    
                cmd = [sys.executable, "bf-busqueda.py", json_path]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    print(f"     [ERROR] Falló semilla {seed} de {alg}: {res.stderr}")
                    break
            print(f"     Completado.")
            
    # -------------------------------------------------------------------------
    # FASE 4: Siembra de Víctimas de Montecarlo con Filtros Geográficos
    # -------------------------------------------------------------------------
    print("\n>>> FASE 4: Sembrando 1000 víctimas virtuales por perfil (Informadas y Ciegas)...")
    
    def generar_victimas(nombre, n_victimas=1000):
        output_dir = f"TFM_JC/resultados/casa_de_campo_{nombre}"
        geojson_path = os.path.join(output_dir, "features.geojson")
        heatmap_path = os.path.join(output_dir, "heatmap.npy")
        
        with open(geojson_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        bounds = metadata["bounds"]
        center_point = metadata["center_point"]
        meter_per_bin = metadata["meter_per_bin"]
        
        lon, lat = center_point
        zone = int((lon + 180) / 6) + 1
        epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
        
        gdf = gpd.read_file(geojson_path).to_crs(epsg)
        heatmap = np.load(heatmap_path)
        
        water_bodies = gdf[gdf["feature_type"] == "water"]
        structures = gdf[gdf["feature_type"] == "structure"]
        
        minx, miny, _, _ = bounds
        
        # 1. Víctimas Informadas
        flat_heatmap = heatmap.flatten()
        flat_indices = np.arange(len(flat_heatmap))
        probs = flat_heatmap / np.sum(flat_heatmap)
        
        informadas = []
        while len(informadas) < n_victimas:
            batch = np.random.choice(flat_indices, size=(n_victimas - len(informadas)) * 5, p=probs)
            for idx in batch:
                y_idx, x_idx = np.unravel_index(idx, heatmap.shape)
                x_utm = minx + x_idx * meter_per_bin + 0.5 * meter_per_bin
                y_utm = miny + y_idx * meter_per_bin + 0.5 * meter_per_bin
                pt = Point(x_utm, y_utm)
                
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
                        
        # 2. Víctimas Ciegas (Uniforme)
        casa_de_campo_utm = gpd.GeoDataFrame(geometry=[CASA_DE_CAMPO_POLY], crs="EPSG:4326").to_crs(epsg).geometry.iloc[0]
        c_minx, c_miny, c_maxx, c_maxy = casa_de_campo_utm.bounds
        
        ciegas = []
        while len(ciegas) < n_victimas:
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
                        
        gpd.GeoDataFrame(geometry=informadas, crs=epsg).to_file(os.path.join(output_dir, "victimas_informadas.geojson"), driver="GeoJSON")
        gpd.GeoDataFrame(geometry=ciegas, crs=epsg).to_file(os.path.join(output_dir, "victimas_ciegas.geojson"), driver="GeoJSON")
        print(f"   [OK] Generadas 1000 informadas y 1000 ciegas para {nombre}")
        
    generar_victimas("autista")
    generar_victimas("demencia")
    generar_victimas("senderista")
    
    # -------------------------------------------------------------------------
    # FASE 5: Evaluación de Trayectorias (Métricas de SAREnv)
    # -------------------------------------------------------------------------
    print("\n>>> FASE 5: Evaluando trayectorias con PathEvaluator de SAREnv...")
    from sarenv.analytics.metrics import PathEvaluator
    
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
        
        with open(geojson_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        bounds = metadata["bounds"]
        center_point = metadata["center_point"]
        meter_per_bin = metadata["meter_per_bin"]
        
        lon, lat = center_point
        zone = int((lon + 180) / 6) + 1
        epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
        
        heatmap = np.load(heatmap_path)
        g_inf = gpd.read_file(os.path.join(output_dir, "victimas_informadas.geojson"))
        g_blind = gpd.read_file(os.path.join(output_dir, "victimas_ciegas.geojson"))
        
        pe_inf = PathEvaluator(heatmap, bounds, g_inf, fov_deg=90.0, altitude=50.0, meters_per_bin=meter_per_bin)
        pe_blind = PathEvaluator(heatmap, bounds, g_blind, fov_deg=90.0, altitude=50.0, meters_per_bin=meter_per_bin)
        
        resultados_dir = f"TFM_JC/resultados/escenario_{perfil}"
        minx, miny, _, _ = bounds
        
        print(f"-> Evaluando escenario_{perfil}...")
        
        for alg_display, alg_file in mapeo_alg.items():
            pattern = os.path.join(resultados_dir, f"{alg_file}-*-traj.json")
            traj_files = glob.glob(pattern)
            
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
                    
                linea_dron = LineString(coords) if len(coords) >= 2 else (LineString([coords[0], coords[0]]) if coords else LineString())
                
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
    os.makedirs("TFM_JC/resultados", exist_ok=True)
    df_global.to_csv("TFM_JC/resultados/resultados_evaluacion_tfm.csv", index=False)
    print("   [OK] Archivo resultados_evaluacion_tfm.csv guardado con éxito.")
    
    # -------------------------------------------------------------------------
    # FASE 6: Generación de Gráficas de Resultados
    # -------------------------------------------------------------------------
    print("\n>>> FASE 6: Generando gráficas de cajas comparativas...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    
    for i, perfil in enumerate(perfiles):
        sub_df = df_global[df_global["Perfil"] == perfil]
        
        df_melt = sub_df.melt(
            id_vars=["Algoritmo"],
            value_vars=["Acierto_Informada", "Acierto_Ciega"],
            var_name="Tipo de Búsqueda",
            value_name="Tasa de Acierto (%)"
        )
        df_melt["Tipo de Búsqueda"] = df_melt["Tipo de Búsqueda"].map({
            "Acierto_Informada": "Informada (Bayesiana)",
            "Acierto_Ciega": "Ciega (Uniforme)"
        })
        
        alg_map_display = {
            "voraz-heur": "Voraz",
            "ACO": "ACO",
            "ABC": "ABC",
            "BHA": "BHA",
            "lawnmower": "Lawnm.",
            "expanding_sq": "Expand."
        }
        df_melt["Algoritmo"] = df_melt["Algoritmo"].map(alg_map_display)
        
        sns.boxplot(
            data=df_melt, 
            x="Algoritmo", 
            y="Tasa de Acierto (%)", 
            hue="Tipo de Búsqueda", 
            ax=axes[i], 
            palette="Set2",
            order=["Voraz", "ACO", "ABC", "BHA", "Lawnm.", "Expand."]
        )
        axes[i].set_title(f"Perfil: {perfil.upper()}", fontsize=14, fontweight='bold')
        axes[i].set_xlabel("Algoritmo de Búsqueda", fontsize=12)
        if i == 0:
            axes[i].set_ylabel("Tasa de Acierto (%)", fontsize=12)
        else:
            axes[i].set_ylabel("")
            
    plt.tight_layout()
    os.makedirs("TFM_JC/resultados/graficas", exist_ok=True)
    graph_path = "TFM_JC/resultados/graficas/comparativa_acierto_perfiles.png"
    plt.savefig(graph_path, dpi=300)
    print(f"   [OK] Gráfica guardada en {graph_path}")
    
    print("\n=========================================================================")
    print("BENCHMARK COMPLETADO CON ÉXITO. TODO EL CONTEXTO ESTÁ POPULADO EN EL DISCO.")
    print("=========================================================================")

if __name__ == "__main__":
    main()

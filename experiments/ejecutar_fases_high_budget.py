import os
import sys
import json
import shutil
import glob
import subprocess
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from shapely.geometry import LineString

# Resolucion dinamica y automatica de rutas
search_dir = os.path.abspath(os.getcwd())
mts_root = None
while search_dir and search_dir != os.path.dirname(search_dir):
    sarenv_candidate = os.path.join(search_dir, "SAREnv")
    if os.path.exists(sarenv_candidate) and sarenv_candidate not in sys.path:
        sys.path.insert(0, sarenv_candidate)
    sarenv_pkg = os.path.join(search_dir, "sarenv")
    if os.path.isdir(sarenv_pkg) and search_dir not in sys.path:
        sys.path.insert(0, search_dir)
    if os.path.isfile(os.path.join(search_dir, "bf-busqueda.py")):
        mts_root = search_dir
    search_dir = os.path.dirname(search_dir)

if mts_root is None:
    mts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from sarenv.analytics.metrics import PathEvaluator

# Configurar UTF-8 para evitar problemas de consola Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Constantes
MTS_DIR = mts_root
BF_BUSQUEDA_PATH = os.path.join(MTS_DIR, "bf-busqueda.py")
DIR_ORIG = os.path.join(MTS_DIR, "TFM_JC/resultados")
DIR_HB = os.path.join(MTS_DIR, "TFM_JC/resultados_high_budget")

def set_optimizacion_y_outdir(enable_opt=True, out_dir_hb=True):
    """Edita bf-busqueda.py para configurar optimización y ruta de salida."""
    print(f"-> Modificando bf-busqueda.py (opt={enable_opt}, out_dir_hb={out_dir_hb})...")
    with open(BF_BUSQUEDA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Modificar USAR_OPTIMIZACION
    target_true = "USAR_OPTIMIZACION = True"
    target_false = "USAR_OPTIMIZACION = False"
    if enable_opt:
        if target_false in content:
            content = content.replace(target_false, target_true)
    else:
        if target_true in content:
            content = content.replace(target_true, target_false)
            
    # 2. Modificar out_dir
    target_hb = 'out_dir = "TFM_JC/resultados_high_budget/"'
    target_orig = 'out_dir = "TFM_JC/resultados/"'
    if out_dir_hb:
        if target_orig in content:
            content = content.replace(target_orig, target_hb)
    else:
        if target_hb in content:
            content = content.replace(target_hb, target_orig)
            
    with open(BF_BUSQUEDA_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("   [OK] bf-busqueda.py configurado.")

def main():
    print("=========================================================================")
    print("INICIANDO AUTOMATIZACIÓN DE SIMULACIÓN DE HIGH BUDGET (5.000 PASOS)")
    print("=========================================================================")
    
    # 1. Asegurar directorios de salida y copiar mapas base (evitando descargas lentas de OSM)
    perfiles = ["autista", "demencia", "senderista"]
    print("\n>>> Fase 1: Copiando mapas de calor y features geográficas...")
    for perfil in perfiles:
        src_folder = os.path.join(DIR_ORIG, f"casa_de_campo_{perfil}")
        dst_folder = os.path.join(DIR_HB, f"casa_de_campo_{perfil}")
        os.makedirs(dst_folder, exist_ok=True)
        
        # Copiar archivos clave
        for fname in ["heatmap.npy", "features.geojson", "victimas_informadas.geojson", "victimas_ciegas.geojson"]:
            src_file = os.path.join(src_folder, fname)
            dst_file = os.path.join(dst_folder, fname)
            if os.path.exists(src_file):
                shutil.copy(src_file, dst_file)
        print(f"   [OK] Copiados mapas para perfil: {perfil}")
        
    # 2. Ejecutar Middleware en resultados_high_budget
    print("\n>>> Fase 2: Ejecutando middleware para generar configuraciones JSON...")
    for perfil in perfiles:
        geojson_path = os.path.join(DIR_HB, f"casa_de_campo_{perfil}/features.geojson")
        npy_path = os.path.join(DIR_HB, f"casa_de_campo_{perfil}/heatmap.npy")
        out_json = os.path.join(DIR_HB, f"casa_de_campo_{perfil}/escenario_{perfil}.json")
        
        cmd = [
            sys.executable,
            "TFM_JC/scripts/generar_json_real.py",
            "--geojson", geojson_path,
            "--npy", npy_path,
            "--out", out_json,
            "--agents", "1",
            "--algorithm", "voraz-heur"
        ]
        res = subprocess.run(cmd, cwd=MTS_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"   [OK] JSON generado para {perfil}")
        else:
            print(f"   [ERROR] Error en middleware para {perfil}: {res.stderr}")
            return
            
    # 3. Lanzar simulaciones (5 semillas, 5.000 pasos, 6 algoritmos)
    print("\n>>> Fase 3: Ejecutando simulaciones masivas (5.000 pasos)...")
    algoritmos = ["voraz-heur", "ACO", "ABC", "BHA", "lawnmower", "expanding_sq"]
    semillas_count = 5
    
    # Activar la optimización de RBF y configurar out_dir para resultados_high_budget
    set_optimizacion_y_outdir(enable_opt=True, out_dir_hb=True)
    
    try:
        for perfil in perfiles:
            json_path = os.path.join(DIR_HB, f"casa_de_campo_{perfil}/escenario_{perfil}.json")
            
            with open(json_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                
            config["dibujar_animacion"] = False
            config["show_evolution"] = False
            config["num_steps"] = 5000
            config["num_agents"] = 1
            config["out_dir"] = "TFM_JC/resultados_high_budget/"
            
            print(f"\n--- Corriendo simulaciones para el perfil: {perfil.upper()} ---")
            for alg in algoritmos:
                print(f"   -> Algoritmo: {alg}...")
                for seed in range(semillas_count):
                    # Determinar nombre del archivo de trayectoria para comprobar si ya existe
                    alg_file = "expanding" if alg == "expanding_sq" else (
                        "lawnmower" if alg == "lawnmower" else (
                            f"bf_{alg.lower()}_ET" if alg in ["ACO", "ABC", "BHA"] else alg
                        )
                    )
                    traj_file = os.path.join(DIR_HB, f"escenario_{perfil}", f"{alg_file}-{seed}-traj.json")
                    if os.path.exists(traj_file):
                        continue
                        
                    config["algoritmo_busqueda"] = alg
                    config["semilla"] = seed
                    
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=4)
                        
                    cmd = [sys.executable, "bf-busqueda.py", json_path]
                    res = subprocess.run(cmd, cwd=MTS_DIR, capture_output=True, text=True)
                    if res.returncode != 0:
                        print(f"      [ERROR] Falló semilla {seed} de {alg}: {res.stderr}")
                        break
                print(f"      Completado.")
    finally:
        # Devolver bf-busqueda.py al estado por defecto (sin optimizar y con resultados normales)
        set_optimizacion_y_outdir(enable_opt=False, out_dir_hb=False)
        
    # 4. Evaluar trayectorias resultantes
    print("\n>>> Fase 4: Evaluando trayectorias con PathEvaluator original...")
    csv_final = os.path.join(DIR_HB, "resultados_evaluacion_tfm.csv")
    resultados_filas = []
    evaluados_set = set() # (Perfil, Algoritmo, Semilla)
    
    if os.path.exists(csv_final):
        try:
            df_existente = pd.read_csv(csv_final)
            resultados_filas = df_existente.to_dict('records')
            for row in resultados_filas:
                evaluados_set.add((row["Perfil"], row["Algoritmo"], int(row["Semilla"])))
            print(f"   [Cargados {len(resultados_filas)} registros ya evaluados desde {csv_final}]")
        except Exception as e:
            print(f"   [Aviso] No se pudo leer CSV existente: {e}. Se empezará de cero.")
            
    for perfil in perfiles:
        output_dir = os.path.join(DIR_HB, f"casa_de_campo_{perfil}")
        geojson_path = os.path.join(output_dir, "features.geojson")
        heatmap_path = os.path.join(output_dir, "heatmap.npy")
        
        with open(geojson_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        bounds = metadata["bounds"]
        meter_per_bin = metadata["meter_per_bin"]
        minx, miny, _, _ = bounds
        
        heatmap = np.load(heatmap_path)
        g_inf = gpd.read_file(os.path.join(output_dir, "victimas_informadas.geojson"))
        g_blind = gpd.read_file(os.path.join(output_dir, "victimas_ciegas.geojson"))
        
        pe_inf = PathEvaluator(heatmap, bounds, g_inf, fov_deg=90.0, altitude=50.0, meters_per_bin=meter_per_bin)
        pe_blind = PathEvaluator(heatmap, bounds, g_blind, fov_deg=90.0, altitude=50.0, meters_per_bin=meter_per_bin)
        
        # Opcional: Para el budget de 5000 pasos en local, dejamos la resolución interpolación por defecto (5)
        # para mantener 100% de coherencia matemática con el benchmark de 1000 pasos si el usuario lo desea.
        # Dado que no es un budget de 20.000, correrá rápido sin problemas.
        
        resultados_dir = os.path.join(DIR_HB, f"escenario_{perfil}")
        
        for alg in algoritmos:
            # Traducir nombre de archivo
            alg_file = "expanding" if alg == "expanding_sq" else (
                "lawnmower" if alg == "lawnmower" else (
                    f"bf_{alg.lower()}_ET" if alg in ["ACO", "ABC", "BHA"] else alg
                )
            )
            
            pattern = os.path.join(resultados_dir, f"{alg_file}-*-traj.json")
            traj_files = glob.glob(pattern)
            
            for t_file in traj_files:
                base = os.path.basename(t_file)
                seed = int(base.split("-")[-2])
                
                # Verificar si ya está evaluado para saltarlo
                if (perfil, alg, seed) in evaluados_set:
                    continue
                    
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
                
                nueva_fila = {
                    "Perfil": perfil,
                    "Algoritmo": alg,
                    "Semilla": seed,
                    "Pasos": len(list_x) - 1,
                    "Distancia_km": res_inf["total_path_length"],
                    "Area_Covered_km2": res_inf["area_covered"],
                    "Likelihood_Score": res_inf["total_likelihood_score"],
                    "Acierto_Informada": res_inf["victim_detection_metrics"]["percentage_found"],
                    "Acierto_Ciega": res_blind["victim_detection_metrics"]["percentage_found"]
                }
                resultados_filas.append(nueva_fila)
                evaluados_set.add((perfil, alg, seed))
                
                # Guardar inmediatamente en caliente
                df_temp = pd.DataFrame(resultados_filas)
                df_temp.to_csv(csv_final, index=False)
                print(f"      [OK] Evaluado {perfil} - {alg} - Semilla {seed} (Guardado en CSV)")
                
                # Pausa de 1.0 segundos para mantener la CPU fresca
                import time
                time.sleep(1.0)
                
    print(f"\n   [OK] Tabla general guardada y actualizada en: {csv_final}")
    
    # 5. Generar gráficas comparativas Boxplot
    print("\n>>> Fase 5: Generando gráficos comparativos de pasos...")
    df_global = pd.DataFrame(resultados_filas)
    
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    
    for i, perfil in enumerate(perfiles):
        sub_df = df_global[df_global["Perfil"] == perfil]
        if sub_df.empty:
            continue
            
        # Mapear nombres en la gráfica
        alg_map_display = {
            "voraz-heur": "Voraz",
            "ACO": "ACO",
            "ABC": "ABC",
            "BHA": "BHA",
            "lawnmower": "Lawnm.",
            "expanding_sq": "Expand."
        }
        sub_df["Algoritmo_Disp"] = sub_df["Algoritmo"].map(alg_map_display)
        
        sns.boxplot(
            data=sub_df, 
            x="Algoritmo_Disp", 
            y="Pasos", 
            ax=axes[i], 
            palette="Set2",
            order=["Voraz", "ACO", "ABC", "BHA", "Lawnm.", "Expand."]
        )
        axes[i].set_title(f"Perfil: {perfil.upper()}", fontsize=14, fontweight='bold')
        axes[i].set_xlabel("Algoritmo de Búsqueda", fontsize=12)
        if i == 0:
            axes[i].set_ylabel("Pasos hasta localización", fontsize=12)
        else:
            axes[i].set_ylabel("")
            
    plt.tight_layout()
    graficas_dir = os.path.join(DIR_HB, "graficas")
    os.makedirs(graficas_dir, exist_ok=True)
    graph_path = os.path.join(graficas_dir, "comparativa_pasos_alto_budget.png")
    plt.savefig(graph_path, dpi=300)
    plt.close()
    print(f"   [OK] Gráfica guardada en {graph_path}")
    
    print("\n=========================================================================")
    print("SIMULACIÓN DE HIGH BUDGET COMPLETADA CON ÉXITO.")
    print("=========================================================================")

if __name__ == "__main__":
    main()

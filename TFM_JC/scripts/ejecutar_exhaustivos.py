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

# Inyectar la ruta local de SAREnv
sys.path.insert(0, r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\SAREnv")
from sarenv.analytics.metrics import PathEvaluator

# Configurar UTF-8 para evitar problemas de consola Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Constantes
MTS_DIR = os.path.abspath(r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\framwork-MTS\MTS-UncertainEnvironment-Algoritmos-bioinspirados")
BF_BUSQUEDA_PATH = os.path.join(MTS_DIR, "bf-busqueda.py")
MEMORIA_TEX_PATH = r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\memoria\chapters\6-AnalisisDeResultados.tex"

def set_optimizacion_en_bf_busqueda(enable=True):
    """Edita bf-busqueda.py para activar o desactivar la optimización."""
    print(f"-> Modificando USAR_OPTIMIZACION a {enable} en {BF_BUSQUEDA_PATH}...")
    with open(BF_BUSQUEDA_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    target_true = "USAR_OPTIMIZACION = True"
    target_false = "USAR_OPTIMIZACION = False"
    
    if enable:
        if target_false in content:
            content = content.replace(target_false, target_true)
        elif target_true not in content:
            # Fallback en caso de que no coincida exactamente
            content = content.replace("USAR_OPTIMIZACION = False", target_true)
    else:
        if target_true in content:
            content = content.replace(target_true, target_false)
        elif target_false not in content:
            content = content.replace("USAR_OPTIMIZACION = True", target_false)
            
    with open(BF_BUSQUEDA_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("   [OK] Archivo modificado.")

def simular_y_evaluar_exhaustivos(dir_resultados, semillas_count=50):
    """
    Ejecuta las simulaciones de lawnmower y expanding_sq y las evalúa con PathEvaluator.
    Devuelve una lista de filas de resultados para agregar al CSV.
    """
    perfiles = ["autista", "demencia", "senderista"]
    algoritmos = ["lawnmower", "expanding_sq"]
    mapeo_alg = {
        "lawnmower": "lawnmower",
        "expanding_sq": "expanding"
    }
    
    nuevas_filas = []
    
    for perfil in perfiles:
        output_dir = os.path.join(dir_resultados, f"casa_de_campo_{perfil}")
        json_path = os.path.join(output_dir, f"escenario_{perfil}.json")
        geojson_path = os.path.join(output_dir, "features.geojson")
        heatmap_path = os.path.join(output_dir, "heatmap.npy")
        
        if not os.path.exists(json_path):
            print(f"[ERROR] Escenario base no encontrado: {json_path}")
            continue
            
        print(f"\n====== Simulación y Evaluación: Perfil {perfil.upper()} ({semillas_count} semillas) ======")
        
        # Leer configuración base
        with open(json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
        config["dibujar_animacion"] = False
        config["show_evolution"] = False
        config["num_steps"] = 1000
        config["num_agents"] = 1
        
        # Cargar metadatos y features
        with open(geojson_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        bounds = metadata["bounds"]
        center_point = metadata["center_point"]
        meter_per_bin = metadata["meter_per_bin"]
        minx, miny, _, _ = bounds
        
        # Cargar mapas y víctimas previamente sembradas
        heatmap = np.load(heatmap_path)
        g_inf = gpd.read_file(os.path.join(output_dir, "victimas_informadas.geojson"))
        g_blind = gpd.read_file(os.path.join(output_dir, "victimas_ciegas.geojson"))
        
        pe_inf = PathEvaluator(heatmap, bounds, g_inf, fov_deg=90.0, altitude=50.0, meters_per_bin=meter_per_bin)
        pe_blind = PathEvaluator(heatmap, bounds, g_blind, fov_deg=90.0, altitude=50.0, meters_per_bin=meter_per_bin)
        
        # Limpiar trayectorias previas de lawnmower/expanding para no duplicar lecturas
        resultados_dir = os.path.join(dir_resultados, f"escenario_{perfil}")
        os.makedirs(resultados_dir, exist_ok=True)
        for f_traj in glob.glob(os.path.join(resultados_dir, "lawnmower-*-traj.json")):
            os.remove(f_traj)
        for f_traj in glob.glob(os.path.join(resultados_dir, "expanding-*-traj.json")):
            os.remove(f_traj)
            
        # Ejecutar simulaciones
        for alg in algoritmos:
            print(f"-> Ejecutando en MTS: {alg}...")
            for seed in range(semillas_count):
                config["algoritmo_busqueda"] = alg
                config["semilla"] = seed
                
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                    
                # Llamar a bf-busqueda.py (MTS guardará la trayectoria detallada)
                cmd = [sys.executable, "bf-busqueda.py", json_path]
                res = subprocess.run(cmd, cwd=MTS_DIR, capture_output=True, text=True)
                if res.returncode != 0:
                    print(f"   [ERROR] Falló semilla {seed} de {alg}: {res.stderr}")
                    break
            print(f"   Completado.")
            
        # Evaluar trayectorias
        print(f"-> Evaluando trayectorias con PathEvaluator...")
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
                
                nuevas_filas.append({
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
                
    return nuevas_filas

def fusionar_csv(csv_path, nuevas_filas):
    """Une las nuevas filas de los exhaustivos al CSV de evaluación."""
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV original no encontrado: {csv_path}")
        return
        
    df_orig = pd.read_csv(csv_path)
    df_new = pd.DataFrame(nuevas_filas)
    
    # Filtrar por si ya existen los algoritmos exhaustivos en el CSV de entrada para evitar duplicados
    df_orig = df_orig[~df_orig["Algoritmo"].isin(["lawnmower", "expanding_sq"])]
    
    # Concatenar y ordenar
    df_final = pd.concat([df_orig, df_new], ignore_index=True)
    df_final = df_final.sort_values(by=["Perfil", "Algoritmo", "Semilla"]).reset_index(drop=True)
    
    df_final.to_csv(csv_path, index=False)
    print(f"[OK] CSV fusionado y guardado en: {csv_path} (Filas finales: {len(df_final)})")
    return df_final

def regenerar_graficas_y_latex(csv_path, dir_resultados):
    """Regenera las gráficas Boxplot y actualiza el código LaTeX de la memoria con 6 algoritmos."""
    if not os.path.exists(csv_path):
        return
        
    df_global = pd.read_csv(csv_path)
    perfiles = ["autista", "demencia", "senderista"]
    
    # 1. Regenerar gráfica boxplot
    print("\n-> Regenerando gráficas de cajas...")
    sns.set_theme(style="whitegrid")
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
        
        # Mapear nombres en la gráfica
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
    graficas_dir = os.path.join(dir_resultados, "graficas")
    os.makedirs(graficas_dir, exist_ok=True)
    graph_path = os.path.join(graficas_dir, "comparativa_acierto_perfiles.png")
    plt.savefig(graph_path, dpi=300)
    plt.close()
    print(f"   [OK] Gráfica guardada en {graph_path}")
    
    # 2. Si es la carpeta optimizada de 50 semillas, actualizar el LaTeX de la memoria
    if "resultados_opt" in dir_resultados:
        print("\n-> Actualizando el archivo LaTeX de la memoria con los 6 algoritmos...")
        
        alg_map_latex = {
            "voraz-heur": "Voraz Heur.",
            "ACO": "ACO (Ants)",
            "ABC": "ABC (Bees)",
            "BHA": "BHA (BlackH)",
            "lawnmower": "Lawnmower",
            "expanding_sq": "Expanding Sq."
        }
        df_global["Algoritmo_Display"] = df_global["Algoritmo"].map(alg_map_latex)
        
        # Agrupar y calcular estadísticas
        stats = df_global.groupby(["Perfil", "Algoritmo_Display"]).agg({
            "Acierto_Informada": ["mean", "std"],
            "Acierto_Ciega": ["mean", "std"],
            "Likelihood_Score": ["mean", "std"],
            "Distancia_km": ["mean", "std"],
            "Area_Covered_km2": ["mean", "std"]
        })
        stats.columns = [f"{col[0]}_{col[1]}" for col in stats.columns.values]
        stats = stats.reset_index()
        
        with open(MEMORIA_TEX_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            
        def generate_latex_table_rows(perfil_name):
            sub = stats[stats["Perfil"] == perfil_name]
            ord_algs = ["Voraz Heur.", "ACO (Ants)", "ABC (Bees)", "BHA (BlackH)", "Lawnmower", "Expanding Sq."]
            sub = sub.set_index("Algoritmo_Display").reindex(ord_algs).reset_index()
            
            rows = []
            for _, row in sub.iterrows():
                alg = row["Algoritmo_Display"]
                ac_inf_mean = row["Acierto_Informada_mean"]
                ac_inf_std = row["Acierto_Informada_std"]
                ac_cie_mean = row["Acierto_Ciega_mean"]
                ac_cie_std = row["Acierto_Ciega_std"]
                like_mean = row["Likelihood_Score_mean"]
                like_std = row["Likelihood_Score_std"]
                dist_mean = row["Distancia_km_mean"]
                dist_std = row["Distancia_km_std"]
                area_mean = row["Area_Covered_km2_mean"]
                area_std = row["Area_Covered_km2_std"]
                
                rows.append(
                    f"\\textit{{{alg}}} & {ac_inf_mean:.2f} \\pm {ac_inf_std:.2f} \\% & {ac_cie_mean:.2f} \\pm {ac_cie_std:.2f} \\% & {like_mean:.4f} \\pm {like_std:.4f} & {dist_mean:.2f} \\pm {dist_std:.2f} & {area_mean:.4f} \\pm {area_std:.4f} \\\\\\\\"
                )
            return "\n".join(rows)

        # 2.1 Reemplazar para Autista
        rows_autista = generate_latex_table_rows("autista")
        # Localizar el entorno tabular
        import re
        pattern_autista = r"(\\label\{tab:resultados_autista\}\s*\\end\{table\})"
        
        # Como el contenido de las tablas ya puede ser el de 4 algoritmos, reemplazamos toda la estructura tabular
        tab_start_aut = content.find(r"\begin{table}[h!]" + "\n" + r"\centering" + "\n" + r"\begin{tabular}{lccccc}")
        tab_end_aut = content.find(r"\label{tab:resultados_autista}")
        
        if tab_start_aut != -1 and tab_end_aut != -1:
            end_bracket = content.find(r"\end{table}", tab_end_aut)
            old_table = content[tab_start_aut : end_bracket + len(r"\end{table}")]
            
            new_table = f"""\\begin{{table}}[h!]
\\centering
\\begin{{tabular}}{{lccccc}}
\\hline
Algoritmo & \\% Acierto (Inf.) & \\% Acierto (Ciego) & Likelihood Score & Distancia (km) & Área (km$^2$) \\\\
\\hline
{rows_autista}
\\hline
\\end{{tabular}}
\\caption{{Resultados del benchmark para el perfil Autista en la Casa de Campo (promedio $\\pm$ desviación estándar sobre 50 semillas).}}
\\label{{tab:resultados_autista}}
\\end{{table}}"""
            content = content.replace(old_table, new_table)
            
        # 2.2 Reemplazar para Demencia
        rows_demencia = generate_latex_table_rows("demencia")
        tab_start_dem = content.find(r"\subsection{Perfil de Demencia / Alzheimer}")
        tab_start_dem_table = content.find(r"\begin{table}[h!]", tab_start_dem)
        tab_end_dem = content.find(r"\label{tab:resultados_demencia}")
        
        if tab_start_dem_table != -1 and tab_end_dem != -1:
            end_bracket = content.find(r"\end{table}", tab_end_dem)
            old_table = content[tab_start_dem_table : end_bracket + len(r"\end{table}")]
            
            new_table = f"""\\begin{{table}}[h!]
\\centering
\\begin{{tabular}}{{lccccc}}
\\hline
Algoritmo & \\% Acierto (Inf.) & \\% Acierto (Ciego) & Likelihood Score & Distancia (km) & Área (km$^2$) \\\\
\\hline
{rows_demencia}
\\hline
\\end{{tabular}}
\\caption{{Resultados del benchmark para el perfil Demencia en la Casa de Campo (promedio $\\pm$ desviación estándar sobre 50 semillas).}}
\\label{{tab:resultados_demencia}}
\\end{{table}}"""
            content = content.replace(old_table, new_table)

        # 2.3 Reemplazar para Senderista
        rows_senderista = generate_latex_table_rows("senderista")
        tab_start_send = content.find(r"\subsection{Perfil Senderista}")
        tab_start_send_table = content.find(r"\begin{table}[h!]", tab_start_send)
        tab_end_send = content.find(r"\label{tab:resultados_senderista}")
        
        if tab_start_send_table != -1 and tab_end_send != -1:
            end_bracket = content.find(r"\end{table}", tab_end_send)
            old_table = content[tab_start_send_table : end_bracket + len(r"\end{table}")]
            
            new_table = f"""\\begin{{table}}[h!]
\\centering
\\begin{{tabular}}{{lccccc}}
\\hline
Algoritmo & \\% Acierto (Inf.) & \\% Acierto (Ciego) & Likelihood Score & Distancia (km) & Área (km$^2$) \\\\
\\hline
{rows_senderista}
\\hline
\\end{{tabular}}
\\caption{{Resultados del benchmark para el perfil Senderista en la Casa de Campo (promedio $\\pm$ desviación estándar sobre 50 semillas).}}
\\label{{tab:resultados_senderista}}
\\end{{table}}"""
            content = content.replace(old_table, new_table)
            
        with open(MEMORIA_TEX_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("   [OK] Archivo LaTeX 6-AnalisisDeResultados.tex actualizado con 6 algoritmos.")

def main():
    print("=========================================================================")
    print("INICIANDO AUTOMATIZACIÓN E INTEGRACIÓN DE ALGORITMOS EXHAUSTIVOS")
    print("=========================================================================")
    
    dir_orig = os.path.join(MTS_DIR, "TFM_JC/resultados")
    dir_opt = os.path.join(MTS_DIR, "TFM_JC/resultados_opt")
    
    # -------------------------------------------------------------------------
    # PARTE A: Ejecución en Modo Optimizado (50 semillas) -> ¡YA COMPLETADA!
    # -------------------------------------------------------------------------
    print("\n>>> PARTE A: MODO OPTIMIZADO (50 semillas) -> Ya completada previamente. Saltando...")
    # Regeneramos por si acaso las gráficas y LaTeX del conjunto optimizado
    csv_opt_final = os.path.join(dir_opt, "resultados_evaluacion_tfm.csv")
    if os.path.exists(csv_opt_final):
        regenerar_graficas_y_latex(csv_opt_final, dir_opt)
            
    # -------------------------------------------------------------------------
    # PARTE B: Ejecución en Modo Original (3 semillas)
    # -------------------------------------------------------------------------
    print("\n>>> PARTE B: Ejecutando exhaustivos en MODO ORIGINAL (3 semillas)...")
    
    try:
        # 1. Activar temporalmente la optimización para que la simulación de 3 semillas sea instantánea
        # (Lawnmower y Expanding son geométricos y dan trayectorias idénticas, pero corren a velocidad de luz)
        set_optimizacion_en_bf_busqueda(True)
        
        # 2. Lanzar simulaciones y evaluación para 3 semillas sobre dir_orig
        filas_orig = simular_y_evaluar_exhaustivos(dir_orig, semillas_count=3)
        
        # 3. Desactivar de nuevo la optimización (dejar código idéntico al tutor)
        set_optimizacion_en_bf_busqueda(False)
        
        # 4. Fusionar CSV
        csv_orig_path = os.path.join(dir_orig, "resultados_evaluacion_tfm.csv")
        fusionar_csv(csv_orig_path, filas_orig)
        
        # 5. Regenerar gráficas del conjunto original
        regenerar_graficas_y_latex(csv_orig_path, dir_orig)
        
    finally:
        # Volver a dejar la optimización en False como estado de no-regresión por defecto
        set_optimizacion_en_bf_busqueda(False)
        
    print("\n=========================================================================")
    print("INTEGRACIÓN DE EXHAUSTIVOS COMPLETADA CON ÉXITO.")
    print("=========================================================================")

if __name__ == "__main__":
    main()

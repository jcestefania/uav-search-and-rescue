import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from functools import partial
from shapely.geometry import LineString

# Desactivar advertencias para mantener la consola limpia
warnings.filterwarnings("ignore")

# Configurar variables de entorno y sys.path
os.environ["MTS_SAVE_BK_HISTORY"] = "False"
SARENV_PATH = r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\SAREnv"
MTS_PATH = r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\framwork-MTS\MTS-UncertainEnvironment-Algoritmos-bioinspirados"
sys.path.insert(0, SARENV_PATH)
sys.path.insert(0, MTS_PATH)

import optuna
from sarenv.analytics.metrics import PathEvaluator
from busquedas.aco import aco_search
from busquedas.abc import abc_search
from busquedas.bha import bha_search
from busquedas.rbf_opt import rbf
from busquedas.heuristicas_opt import heur_correcion_miopia
from configurar import celda_mas_cercana, random_target
from sensor.square_sensor import SquareSensor
from extra.funciones import ET, DTR, MS, ME

def seleccionar_funcion_objetivo(nombre):
    return {"ET": ET, "DTR": DTR, "MS": MS, "ME": ME}.get(nombre)

def crear_movimientos(tipo, delta):
    movimientos = {
        "8 dir": [[-delta, -delta], [-delta, 0], [-delta, delta],
                  [0, -delta], [0, delta],
                  [delta, -delta], [delta, 0], [delta, delta]],
        "cruz": [[-delta, 0], [0, -delta], [0, delta], [delta, 0]]
    }
    return np.array(movimientos[tipo])

# Configurar logging de optuna a nivel WARNING para evitar saturar la salida
optuna.logging.set_verbosity(optuna.logging.WARNING)

def evaluate_params(perfil, algoritmo, params_trial, pe_inf, heatmap, bounds, meter_per_bin, minx, miny):
    """Evalúa un conjunto de parámetros sobre 3 semillas de control y devuelve la media del acierto."""
    seeds = [0, 1, 2]
    aciertos = []
    
    size = list(heatmap.shape)
    HEIGHT = 10
    init_pos = np.array([[205, 221, HEIGHT]], dtype=float) # Posición inicial de la Casa de Campo con Z

    N_AGENTS = 1
    HEIGHT = 10
    delta = 1
    max_steps = 300  # Reducido para acelerar el tuning
    
    # Configurar sensor y filtro
    sensor = SquareSensor(pdmax=0.8, dmax=2.1, sigma=0.7)
    obj_estatico = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])
    filtro = partial(rbf, p_transicion=obj_estatico, sensor=sensor)
    
    # Movimientos y Heurística
    moves = crear_movimientos("8 dir", delta)
    heur = partial(heur_correcion_miopia, dist_min=3, lambda_=0.5)
    funcion_objetivo = seleccionar_funcion_objetivo("ET")
    
    for seed in seeds:
        np.random.seed(seed)
        
        # Muestrear posición del objetivo de forma determinista usando la semilla
        flat_bk = heatmap.flatten()
        flat_idx = np.random.choice(len(flat_bk), p=flat_bk)
        y_goal, x_goal = np.unravel_index(flat_idx, heatmap.shape)
        goal = np.array([x_goal, y_goal], dtype=float)
        goal = celda_mas_cercana(goal, heatmap)
        
        # Copiar mapa base
        bk_iter = heatmap.copy()
        
        if algoritmo == "ACO":
            new_list_x, new_list_y, _, steps, _, _, _, _ = aco_search(
                grid_size=size,
                bk=bk_iter,
                target=goal,
                heur=heur,
                filter=filtro,
                dmax=2.1,
                init_pos=init_pos,
                moves=moves,
                n_agents=N_AGENTS,
                separation=3,
                max_steps=max_steps,
                funcion_objetivo=funcion_objetivo,
                show_evolution=False,
                eps=1e-12,
                iterations=params_trial["n_iterations_aco"],
                alpha=params_trial["alpha"],
                beta=params_trial["beta"],
                rho=params_trial["rho"],
                Q=params_trial["Q"],
                local_rho=params_trial["local_rho"]
            )
        elif algoritmo == "ABC":
            new_list_x, new_list_y, _, steps, _, _, _, _ = abc_search(
                grid_size=size,
                bk=bk_iter,
                target=goal,
                heur=heur,
                filter=filtro,
                dmax=2.1,
                init_pos=init_pos,
                moves=moves,
                n_agents=N_AGENTS,
                separation=3,
                max_steps=max_steps,
                funcion_objetivo=funcion_objetivo,
                show_evolution=False,
                eps=1e-12,
                iterations=params_trial["n_iterations_abc"],
                n_employed=params_trial["n_employed"],
                n_onlooker=params_trial["n_onlookers"],
                limit=params_trial["limit"]
            )
        elif algoritmo == "BHA":
            new_list_x, new_list_y, _, steps, _, _, _, _ = bha_search(
                grid_size=size,
                bk=bk_iter,
                target=goal,
                heur=heur,
                filter=filtro,
                dmax=2.1,
                init_pos=init_pos,
                moves=moves,
                n_agents=N_AGENTS,
                separation=3,
                max_steps=max_steps,
                funcion_objetivo=funcion_objetivo,
                show_evolution=False,
                eps=1e-12,
                n_stars=params_trial["n_stars"],
                iterations=params_trial["n_iterations_bha"]
            )
            
        list_x = new_list_x[0]
        list_y = new_list_y[0]
        
        # Transformar a UTM
        coords = []
        for x_idx, y_idx in zip(list_x, list_y):
            x_utm = minx + x_idx * meter_per_bin + 0.5 * meter_per_bin
            y_utm = miny + y_idx * meter_per_bin + 0.5 * meter_per_bin
            coords.append((x_utm, y_utm))
            
        linea_dron = LineString(coords) if len(coords) >= 2 else (LineString([coords[0], coords[0]]) if coords else LineString())
        
        # Calcular tasa de acierto contra las 1000 víctimas virtuales
        res_inf = pe_inf.calculate_all_metrics([linea_dron], discount_factor=0.999)
        aciertos.append(res_inf["victim_detection_metrics"]["percentage_found"])
        
    return np.mean(aciertos)

def optimize_profile_algorithm(perfil, algoritmo, pe_inf, heatmap, bounds, meter_per_bin, minx, miny):
    """Estudio de optimización con Optuna para un perfil y algoritmo específicos."""
    print(f"\n>>> Optimizando {algoritmo} para el perfil {perfil.upper()}...")
    
    def objective(trial):
        params_trial = {}
        if algoritmo == "ACO":
            params_trial["alpha"] = trial.suggest_float("alpha", 0.5, 2.5)
            params_trial["beta"] = trial.suggest_float("beta", 1.0, 5.0)
            params_trial["rho"] = trial.suggest_float("rho", 0.05, 0.3)
            params_trial["local_rho"] = trial.suggest_float("local_rho", 0.01, 0.15)
            params_trial["Q"] = trial.suggest_float("Q", 0.1, 3.0)
            params_trial["n_iterations_aco"] = trial.suggest_int("n_iterations_aco", 2, 7)
        elif algoritmo == "ABC":
            params_trial["n_iterations_abc"] = trial.suggest_int("n_iterations_abc", 5, 15)
            params_trial["limit"] = trial.suggest_int("limit", 5, 20)
            params_trial["n_employed"] = trial.suggest_int("n_employed", 1, 4)
            params_trial["n_onlookers"] = trial.suggest_int("n_onlookers", 1, 4)
        elif algoritmo == "BHA":
            params_trial["n_iterations_bha"] = trial.suggest_int("n_iterations_bha", 5, 15)
            params_trial["n_stars"] = trial.suggest_int("n_stars", 3, 10)
            
        return evaluate_params(perfil, algoritmo, params_trial, pe_inf, heatmap, bounds, meter_per_bin, minx, miny)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=35)
    
    print(f"   [OK] Mejor Acierto conseguido: {study.best_value:.2f}% con los parámetros:")
    print(f"        {study.best_params}")
    return study.best_params, study.best_value

def main():
    print("=========================================================================")
    # Usar la ruta de resultados definitiva para cargar los mapas de calor
    DIR_RESULTADOS = r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\framwork-MTS\MTS-UncertainEnvironment-Algoritmos-bioinspirados\TFM_JC\resultados"
    
    perfiles = ["autista", "demencia", "senderista"]
    algoritmos = ["ACO", "ABC", "BHA"]
    
    resultados_optuna = {}
    
    for perfil in perfiles:
        perfil_dir = os.path.join(DIR_RESULTADOS, f"casa_de_campo_{perfil}")
        geojson_path = os.path.join(perfil_dir, "features.geojson")
        heatmap_path = os.path.join(perfil_dir, "heatmap.npy")
        
        with open(geojson_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        bounds = metadata["bounds"]
        center_point = metadata["center_point"]
        meter_per_bin = metadata["meter_per_bin"]
        
        lon, lat = center_point
        zone = int((lon + 180) / 6) + 1
        epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
        
        heatmap = np.load(heatmap_path)
        g_inf = gpd.read_file(os.path.join(perfil_dir, "victimas_informadas.geojson"))
        
        # Instanciar el evaluador para la optimización de este perfil
        pe_inf = PathEvaluator(
            heatmap=heatmap,
            extent=bounds,
            victims=g_inf,
            fov_deg=90.0,
            altitude=50.0,
            meters_per_bin=meter_per_bin
        )
        
        minx, miny, _, _ = bounds
        
        resultados_optuna[perfil] = {}
        for alg in algoritmos:
            best_params, best_val = optimize_profile_algorithm(perfil, alg, pe_inf, heatmap, bounds, meter_per_bin, minx, miny)
            resultados_optuna[perfil][alg] = {
                "params": best_params,
                "score_acierto_medio": float(best_val)
            }
            
    # Guardar los mejores parámetros en un JSON
    out_json = os.path.join(DIR_RESULTADOS, "optuna_best_params.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(resultados_optuna, f, indent=4, ensure_ascii=False)
        
    print("\n=========================================================================")
    print(f"OPTIMIZACIÓN CON OPTUNA COMPLETADA. Parámetros guardados en: {out_json}")
    print("=========================================================================")

if __name__ == "__main__":
    main()

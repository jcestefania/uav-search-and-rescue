import os
import json
import numpy as np
import shapely.geometry
import sys

# Añadir el path de SAREnv al sistema para poder importar sus módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
sarenv_path = os.path.abspath(os.path.join(current_dir, "../../SAREnv"))
sys.path.append(sarenv_path)

try:
    from sarenv import DataGenerator, CLIMATE_TEMPERATE, ENVIRONMENT_TYPE_FLAT
except ImportError:
    print(f"Error: No se pudo encontrar SAREnv en la ruta: {sarenv_path}")
    print("Asegúrate de que la estructura de carpetas sea la correcta.")
    sys.exit(1)

def generar_escenario():
    # 1. CONFIGURACIÓN DE SARENV (Ejemplo Casa de Campo)
    data_gen = DataGenerator()
    
    # Coordenadas de la Casa de Campo (Madrid) para el polígono
    # [Longitud, Latitud]
    polygon_coords = [
        [-3.766, 40.407], 
        [-3.738, 40.407], 
        [-3.738, 40.432], 
        [-3.766, 40.432], 
        [-3.766, 40.407]
    ]
    poly = shapely.geometry.Polygon(polygon_coords)
    
    print("Generando mapa en SAREnv...")
    # Generamos el entorno desde el polígono
    env = data_gen.generate_environment_from_polygon(
        polygon=poly,
        meter_per_bin=20 # Resolución de 20m por celda
    )
    
    if env is None:
        print("Error: Falló la generación del entorno.")
        sys.exit(1)
        
    # Obtenemos el heatmap (matriz 2D de numpy)
    heatmap = env.get_combined_heatmap()
    
    if heatmap is None:
        print("Error: No se pudo generar el heatmap.")
        sys.exit(1)
        
    # NORMALIZACIÓN: Aseguramos que la suma de todas las probabilidades sea 1.0
    total_prob = np.sum(heatmap)
    if total_prob > 0:
        heatmap = heatmap / total_prob
    else:
        print("Error: El heatmap generado está vacío o tiene probabilidad cero.")
        sys.exit(1)
    
    # 2. GUARDADO DE DATOS
    output_dir = os.path.join(current_dir, "TFM_JC/pruebas/")
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = "escenario_real_casacampo"
    npy_path = os.path.join(output_dir, f"{base_name}.npy")
    json_path = os.path.join(output_dir, f"{base_name}.json")
    
    # Guardar matriz en formato binario (.npy)
    np.save(npy_path, heatmap)
    print(f"Mapa binario guardado en: {npy_path}")

    # 3. CREACIÓN DEL JSON COMPATIBLE CON MTS
    # Dimensiones: SAREnv devuelve (filas, columnas) -> Numpy (y, x)
    # MTS espera size como [x, y]
    rows, cols = heatmap.shape
    size_mts = [cols, rows]
    
    # Identificar el punto de máxima probabilidad para colocar el indicio/víctima inicial
    idx_max = np.unravel_index(np.argmax(heatmap), heatmap.shape)
    y_max, x_max = int(idx_max[0]), int(idx_max[1])
    
    data = {
        "version": "1.1-SAREnv",
        "size": size_mts,
        "ruta_mapa_real": f"{base_name}.npy", # Referencia al archivo binario relativo al JSON
        "num_agents": 2,
        "height": 10,
        "init_pos": [[cols//2, rows//2], [cols//2 + 2, rows//2 + 2]], 
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
        "algoritmo_busqueda": "ACO", 
        "funcion_objetivo": "ET",
        "optimization": "min",
        "show_evolution": True,
        
        "n_ants": 20,
        "n_iterations_aco": 5,
        "alpha": 1.0,
        "beta": 3.0,
        "rho": 0.1,
        "local_rho": 0.05,
        "Q": 1.0,

        "indicios": [[x_max, y_max]], 
        "cov": [[2, 0], [0, 2]],
        "pesos": [1.0],
        "obj_pos": [None],
        "indicio": -1,
        "semilla": 0
    }

    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"Archivo de configuración JSON generado: {json_path}")
    print(f"Dimensiones del mapa inyectadas: {cols} (X) x {rows} (Y)")

if __name__ == "__main__":
    generar_escenario()

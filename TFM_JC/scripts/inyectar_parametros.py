import os
import json

DIR_RESULTADOS = r"c:\Users\juanc\Desktop\TFM\TFM-Juan Carlos\Software\framwork-MTS\MTS-UncertainEnvironment-Algoritmos-bioinspirados\TFM_JC\resultados"
best_params_path = os.path.join(DIR_RESULTADOS, "optuna_best_params.json")

with open(best_params_path, "r", encoding="utf-8") as f:
    optuna_data = json.load(f)

perfiles = ["autista", "demencia", "senderista"]

for perfil in perfiles:
    json_path = os.path.join(DIR_RESULTADOS, f"casa_de_campo_{perfil}", f"escenario_{perfil}.json")
    
    if not os.path.exists(json_path):
        print(f"No existe {json_path}")
        continue
        
    with open(json_path, "r", encoding="utf-8") as f:
        escenario = json.load(f)
        
    # Inyectar ACO
    aco_params = optuna_data[perfil]["ACO"]["params"]
    escenario["alpha"] = aco_params["alpha"]
    escenario["beta"] = aco_params["beta"]
    escenario["rho"] = aco_params["rho"]
    escenario["local_rho"] = aco_params["local_rho"]
    escenario["Q"] = aco_params["Q"]
    escenario["n_iterations_aco"] = aco_params["n_iterations_aco"]
    
    # Inyectar ABC
    abc_params = optuna_data[perfil]["ABC"]["params"]
    escenario["n_iterations_abc"] = abc_params["n_iterations_abc"]
    escenario["limit"] = abc_params["limit"]
    escenario["n_employed"] = abc_params["n_employed"]
    escenario["n_onlookers"] = abc_params["n_onlookers"]
    
    # Inyectar BHA
    bha_params = optuna_data[perfil]["BHA"]["params"]
    escenario["n_iterations_bha"] = bha_params["n_iterations_bha"]
    escenario["n_stars"] = bha_params["n_stars"]
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(escenario, f, indent=4, ensure_ascii=False)
        
    print(f"Inyectados parámetros en {json_path}")

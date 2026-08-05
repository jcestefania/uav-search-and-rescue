import json
import os

def patch_notebook(nb_path, out_dir_name):
    if not os.path.exists(nb_path):
        print(f"No se encuentra el notebook: {nb_path}")
        return
        
    print(f"Patching notebook: {nb_path}")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    # El código a insertar en la celda 21 (que es de tipo código para graficar)
    plotting_code = f"""import matplotlib.pyplot as plt
import seaborn as sns
import os
from IPython.display import display

# Forzar el backend inline en Jupyter (SAREnv bloquea el backend en 'Agg' internamente)
from IPython import get_ipython
ipy = get_ipython()
if ipy is not None:
    ipy.run_line_magic('matplotlib', 'inline')
sns.set_theme(style="whitegrid")
perfiles = ["autista", "demencia", "senderista"]
alg_map_display = {{
    "voraz-heur": "Greedy",
    "ACO": "ACO",
    "ABC": "ABC",
    "BHA": "BHA",
    "lawnmower": "Lawnmower",
    "expanding_sq": "Expanding Sq."
}}

# Crear directorio de graficas si no existe
os.makedirs("TFM_JC/{out_dir_name}/graficas", exist_ok=True)

# 1. Tasa de Acierto (Informada vs Ciega)
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
for i, perfil in enumerate(perfiles):
    sub_df = df_eval[df_eval["Perfil"] == perfil]
    if sub_df.empty:
        continue
    df_melt = sub_df.melt(
        id_vars=["Algoritmo"], 
        value_vars=["Acierto_Informada", "Acierto_Ciega"], 
        var_name="Search Type", 
        value_name="Success Rate (%)"
    )
    df_melt["Search Type"] = df_melt["Search Type"].map({{
        "Acierto_Informada": "Informed (Bayesian)",
        "Acierto_Ciega": "Blind (Uniform)"
    }})
    df_melt["Algoritmo"] = df_melt["Algoritmo"].map(alg_map_display)
    
    sns.boxplot(
        data=df_melt, 
        x="Algoritmo", 
        y="Success Rate (%)", 
        hue="Search Type", 
        ax=axes[i],
        palette="Set2",
        order=["Greedy", "ACO", "ABC", "BHA", "Lawnmower", "Expanding Sq."]
    )
    # Traducir los nombres de perfiles a inglés
    perfil_en = "AUTISTIC" if perfil == "autista" else ("DEMENTIA" if perfil == "demencia" else "HIKER")
    axes[i].set_title(f"Profile: {{perfil_en}}", fontsize=14, fontweight='bold')
    axes[i].set_xlabel("Search Algorithm", fontsize=12)
    if i == 0:
        axes[i].set_ylabel("Success Rate (%)", fontsize=12)
    else:
        axes[i].set_ylabel("")
plt.tight_layout()
graph_path_acierto = "TFM_JC/{out_dir_name}/graficas/comparativa_acierto_perfiles.png"
plt.savefig(graph_path_acierto, dpi=300)
display(fig)
plt.close(fig)
print(f"Success rate plot saved to: {{graph_path_acierto}}")

# 2. Likelihood Score
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
for i, perfil in enumerate(perfiles):
    sub_df = df_eval[df_eval["Perfil"] == perfil]
    if sub_df.empty:
        continue
    sub_df_copy = sub_df.copy()
    sub_df_copy["Algoritmo"] = sub_df_copy["Algoritmo"].map(alg_map_display)
    sns.boxplot(
        data=sub_df_copy, 
        x="Algoritmo", 
        y="Likelihood_Score", 
        ax=axes[i], 
        palette="Set2",
        order=["Greedy", "ACO", "ABC", "BHA", "Lawnmower", "Expanding Sq."]
    )
    perfil_en = "AUTISTIC" if perfil == "autista" else ("DEMENTIA" if perfil == "demencia" else "HIKER")
    axes[i].set_title(f"Profile: {{perfil_en}}", fontsize=14, fontweight='bold')
    axes[i].set_xlabel("Search Algorithm", fontsize=12)
    if i == 0:
        axes[i].set_ylabel("Likelihood Score", fontsize=12)
    else:
        axes[i].set_ylabel("")
plt.tight_layout()
graph_path_like = "TFM_JC/{out_dir_name}/graficas/comparativa_likelihood_perfiles.png"
plt.savefig(graph_path_like, dpi=300)
display(fig)
plt.close(fig)
print(f"Likelihood score plot saved to: {{graph_path_like}}")

# 3. Área Cubierta
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
for i, perfil in enumerate(perfiles):
    sub_df = df_eval[df_eval["Perfil"] == perfil]
    if sub_df.empty:
        continue
    sub_df_copy = sub_df.copy()
    sub_df_copy["Algoritmo"] = sub_df_copy["Algoritmo"].map(alg_map_display)
    sns.boxplot(
        data=sub_df_copy, 
        x="Algoritmo", 
        y="Area_Covered_km2", 
        ax=axes[i], 
        palette="Set2",
        order=["Greedy", "ACO", "ABC", "BHA", "Lawnmower", "Expanding Sq."]
    )
    perfil_en = "AUTISTIC" if perfil == "autista" else ("DEMENTIA" if perfil == "demencia" else "HIKER")
    axes[i].set_title(f"Profile: {{perfil_en}}", fontsize=14, fontweight='bold')
    axes[i].set_xlabel("Search Algorithm", fontsize=12)
    if i == 0:
        axes[i].set_ylabel("Area Covered (km²)", fontsize=12)
    else:
        axes[i].set_ylabel("")
plt.tight_layout()
graph_path_area = "TFM_JC/{out_dir_name}/graficas/comparativa_area_perfiles.png"
plt.savefig(graph_path_area, dpi=300)
display(fig)
plt.close(fig)
print(f"Area covered plot saved to: {{graph_path_area}}")

# 4. Distancia de Vuelo
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
for i, perfil in enumerate(perfiles):
    sub_df = df_eval[df_eval["Perfil"] == perfil]
    if sub_df.empty:
        continue
    sub_df_copy = sub_df.copy()
    sub_df_copy["Algoritmo"] = sub_df_copy["Algoritmo"].map(alg_map_display)
    sns.boxplot(
        data=sub_df_copy, 
        x="Algoritmo", 
        y="Distancia_km", 
        ax=axes[i], 
        palette="Set2",
        order=["Greedy", "ACO", "ABC", "BHA", "Lawnmower", "Expanding Sq."]
    )
    perfil_en = "AUTISTIC" if perfil == "autista" else ("DEMENTIA" if perfil == "demencia" else "HIKER")
    axes[i].set_title(f"Profile: {{perfil_en}}", fontsize=14, fontweight='bold')
    axes[i].set_xlabel("Search Algorithm", fontsize=12)
    if i == 0:
        axes[i].set_ylabel("Flight Distance (km)", fontsize=12)
    else:
        axes[i].set_ylabel("")
plt.tight_layout()
graph_path_dist = "TFM_JC/{out_dir_name}/graficas/comparativa_distancia_perfiles.png"
plt.savefig(graph_path_dist, dpi=300)
display(fig)
plt.close(fig)
print(f"Flight distance plot saved to: {{graph_path_dist}}")

# 5. Pasos hasta Localización
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
for i, perfil in enumerate(perfiles):
    sub_df = df_eval[df_eval["Perfil"] == perfil]
    if sub_df.empty:
        continue
    sub_df_copy = sub_df.copy()
    sub_df_copy["Algoritmo"] = sub_df_copy["Algoritmo"].map(alg_map_display)
    sns.boxplot(
        data=sub_df_copy, 
        x="Algoritmo", 
        y="Pasos", 
        ax=axes[i], 
        palette="Set2",
        order=["Greedy", "ACO", "ABC", "BHA", "Lawnmower", "Expanding Sq."]
    )
    perfil_en = "AUTISTIC" if perfil == "autista" else ("DEMENTIA" if perfil == "demencia" else "HIKER")
    axes[i].set_title(f"Profile: {{perfil_en}}", fontsize=14, fontweight='bold')
    axes[i].set_xlabel("Search Algorithm", fontsize=12)
    if i == 0:
        axes[i].set_ylabel("Steps to Target", fontsize=12)
    else:
        axes[i].set_ylabel("")
plt.tight_layout()
graph_path_steps = "TFM_JC/{out_dir_name}/graficas/comparativa_pasos_encontrar.png"
plt.savefig(graph_path_steps, dpi=300)
display(fig)
plt.close(fig)
print(f"Steps to target plot saved to: {{graph_path_steps}}")
"""
    
    # Reemplazar el código de la celda 21
    nb["cells"][21]["source"] = [line + "\n" for line in plotting_code.split("\n")]
    
    # Si es el de 1000 pasos, agregar la celda de pasos también (que no existía en el original)
    # pero en realidad la celda 21 ya lo grafica todo junto de golpe de forma consecutiva,
    # lo cual es perfecto.
    
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=4, ensure_ascii=False)
    print(f"Notebook {nb_path} modificado con éxito.")

def main():
    patch_notebook("TFM_JC/pruebas/Benchmark_Perfiles_Real.ipynb", "resultados")
    patch_notebook("TFM_JC/pruebas/Benchmark_Perfiles_Real_HighBudget.ipynb", "resultados_high_budget")
    patch_notebook("TFM_JC/pruebas/Benchmark_Perfiles_Real_Interactivo.ipynb", "resultados")

if __name__ == "__main__":
    main()

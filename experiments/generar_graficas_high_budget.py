import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    csv_path = os.path.join("TFM_JC", "resultados_high_budget", "resultados_evaluacion_tfm.csv")
    out_dir = os.path.join("TFM_JC", "resultados_high_budget", "graficas")
    os.makedirs(out_dir, exist_ok=True)
    
    if not os.path.exists(csv_path):
        print(f"Error: No se encuentra el CSV en {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    perfiles = ["autista", "demencia", "senderista"]
    
    alg_map_display = {
        "voraz-heur": "Voraz",
        "ACO": "ACO",
        "ABC": "ABC",
        "BHA": "BHA",
        "lawnmower": "Lawnm.",
        "expanding_sq": "Expand."
    }
    
    df["Algoritmo_Disp"] = df["Algoritmo"].map(alg_map_display)
    sns.set_theme(style="whitegrid")
    
    # 1. Gráfica de Tasa de Acierto (Informada vs Ciega)
    print("-> Generando gráfica de Tasa de Acierto...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    for i, perfil in enumerate(perfiles):
        sub_df = df[df["Perfil"] == perfil]
        if sub_df.empty:
            continue
            
        df_melt = sub_df.melt(
            id_vars=["Algoritmo_Disp"],
            value_vars=["Acierto_Informada", "Acierto_Ciega"],
            var_name="Tipo de Búsqueda",
            value_name="Tasa de Acierto (%)"
        )
        df_melt["Tipo de Búsqueda"] = df_melt["Tipo de Búsqueda"].map({
            "Acierto_Informada": "Informada (Bayesiana)",
            "Acierto_Ciega": "Ciega (Uniforme)"
        })
        
        sns.boxplot(
            data=df_melt, 
            x="Algoritmo_Disp", 
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
    plt.savefig(os.path.join(out_dir, "comparativa_acierto_alto_budget.png"), dpi=300)
    plt.close()
    
    # 2. Gráfica de Likelihood Score
    print("-> Generando gráfica de Likelihood Score...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    for i, perfil in enumerate(perfiles):
        sub_df = df[df["Perfil"] == perfil]
        if sub_df.empty:
            continue
            
        sns.boxplot(
            data=sub_df, 
            x="Algoritmo_Disp", 
            y="Likelihood_Score", 
            ax=axes[i], 
            palette="Set2",
            order=["Voraz", "ACO", "ABC", "BHA", "Lawnm.", "Expand."]
        )
        axes[i].set_title(f"Perfil: {perfil.upper()}", fontsize=14, fontweight='bold')
        axes[i].set_xlabel("Algoritmo de Búsqueda", fontsize=12)
        if i == 0:
            axes[i].set_ylabel("Likelihood Score", fontsize=12)
        else:
            axes[i].set_ylabel("")
            
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "comparativa_likelihood_alto_budget.png"), dpi=300)
    plt.close()
    
    # 3. Gráfica de Área Cubierta
    print("-> Generando gráfica de Área Cubierta...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    for i, perfil in enumerate(perfiles):
        sub_df = df[df["Perfil"] == perfil]
        if sub_df.empty:
            continue
            
        sns.boxplot(
            data=sub_df, 
            x="Algoritmo_Disp", 
            y="Area_Covered_km2", 
            ax=axes[i], 
            palette="Set2",
            order=["Voraz", "ACO", "ABC", "BHA", "Lawnm.", "Expand."]
        )
        axes[i].set_title(f"Perfil: {perfil.upper()}", fontsize=14, fontweight='bold')
        axes[i].set_xlabel("Algoritmo de Búsqueda", fontsize=12)
        if i == 0:
            axes[i].set_ylabel("Área Cubierta (km²)", fontsize=12)
        else:
            axes[i].set_ylabel("")
            
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "comparativa_area_alto_budget.png"), dpi=300)
    plt.close()
    
    # 4. Gráfica de Distancia de Vuelo
    print("-> Generando gráfica de Distancia de Vuelo...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    for i, perfil in enumerate(perfiles):
        sub_df = df[df["Perfil"] == perfil]
        if sub_df.empty:
            continue
            
        sns.boxplot(
            data=sub_df, 
            x="Algoritmo_Disp", 
            y="Distancia_km", 
            ax=axes[i], 
            palette="Set2",
            order=["Voraz", "ACO", "ABC", "BHA", "Lawnm.", "Expand."]
        )
        axes[i].set_title(f"Perfil: {perfil.upper()}", fontsize=14, fontweight='bold')
        axes[i].set_xlabel("Algoritmo de Búsqueda", fontsize=12)
        if i == 0:
            axes[i].set_ylabel("Distancia Recorrida (km)", fontsize=12)
        else:
            axes[i].set_ylabel("")
            
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "comparativa_distancia_alto_budget.png"), dpi=300)
    plt.close()
    
    print("¡Todas las gráficas de 5000 pasos se han generado correctamente!")

if __name__ == "__main__":
    main()

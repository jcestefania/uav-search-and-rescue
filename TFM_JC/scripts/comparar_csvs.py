import os
import pandas as pd
import numpy as np

def comparar():
    csv_orig = os.path.join("TFM_JC", "resultados", "resultados_evaluacion_tfm.csv")
    csv_opt = os.path.join("TFM_JC", "resultados_opt", "resultados_evaluacion_tfm.csv")
    
    df_orig = pd.read_csv(csv_orig)
    df_opt = pd.read_csv(csv_opt)
    
    # Configurar pandas para mostrar todo
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    cols = ["Pasos", "Distancia_km", "Area_Covered_km2", "Likelihood_Score", "Acierto_Informada", "Acierto_Ciega"]
    
    print("=================== CSV ORIGINAL (Tutor, 3 semillas) ===================")
    orig_grouped = df_orig.groupby(["Perfil", "Algoritmo"])[cols].mean()
    print(orig_grouped.to_string())
    
    print("\n=================== CSV OPTIMIZADO (50 semillas) ===================")
    opt_grouped = df_opt.groupby(["Perfil", "Algoritmo"])[cols].mean()
    print(opt_grouped.to_string())
    
    # Hacer una tabla comparativa directa de las medias
    print("\n=================== COMPARATIVA DIRECTA (OPT vs ORIG) ===================")
    comparativa = opt_grouped - orig_grouped
    print("Diferencia (Optimizada - Original):")
    print(comparativa.to_string())

if __name__ == "__main__":
    comparar()

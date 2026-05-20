"""
mis_pruebas.py
Ejecuta las 16 combinaciones de algoritmos (ACO, ABC, BHA + clásicos)
con las 4 funciones objetivo y genera una gráfica comparativa.

Uso: python mis_pruebas.py
     (desde la raíz del repo, con el entorno tfm_mts activado)
"""

import json
import os
import subprocess
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ============================================================
# 1. CONFIGURACIÓN BASE — igual para todos los experimentos
# ============================================================
BASE = {
    "version": "1.1",
    "size": [30, 30],
    "cov": [[2, 0], [0, 2]],
    "indicios": [[15, 15]],
    "pesos": [1.0],
    "obj_pos": [None],
    "p_transicion": [[0, 0, 0], [0, 1, 0], [0, 0, 0]],
    "indicio": -1,
    "semilla": 42,
    "num_agents": 1,
    "height": 10,
    "init_pos": [[5, 5]],
    "mov_delta": 1,
    "posible_moves": "8 dir",
    "min_dist": 3,
    "lambda": 0.5,
    "pdmax": 0.8,
    "dmax": 2.1,
    "sigma": 0.7,
    "num_steps": 300,
    "itersteps": 50,
    "separation": 2,
    "plan": False,
    "optimization": "min",
    "show_evolution": False,
    # Parámetros bioinspirados
    "n_ants": 10,
    "n_iterations_aco": 5,
    "alpha": 1.0,
    "beta": 3.0,
    "rho": 0.1,
    "local_rho": 0.05,
    "Q": 1.0,
    "n_iterations_abc": 5,
    "limit": 5,
    "n_onlookers": 3,
    "n_employed": 3,
    "n_iterations_bha": 5,
    "n_stars": 5,
}

# ============================================================
# 2. EXPERIMENTOS A LANZAR
# ============================================================
EXPERIMENTOS = []

# Algoritmos bioinspirados x 4 funciones objetivo
for alg in ["ACO", "ABC", "BHA"]:
    for fo in ["ET", "DTR", "MS", "ME"]:
        EXPERIMENTOS.append((f"{alg}+{fo}", alg, fo))

# Algoritmos clásicos (sin función objetivo bioinspirada)
for alg in ["lawnmower", "expanding_sq", "voraz-heur", "voraz-myope"]:
    EXPERIMENTOS.append((alg, alg, None))

# ============================================================
# 3. CREAR JSONs Y EJECUTAR
# ============================================================
os.makedirs("pruebas_test", exist_ok=True)
os.makedirs("resultados", exist_ok=True)

resultados = []

print("Lanzando experimentos...\n")

for nombre, alg, fo in EXPERIMENTOS:
    # Crear JSON
    config = BASE.copy()
    config["algoritmo_busqueda"] = alg
    config["funcion_objetivo"] = fo

    json_path = f"pruebas_test/{nombre.replace('+', '_')}.json"
    with open(json_path, "w") as f:
        json.dump(config, f, indent=4)

    # Ejecutar
    print(f"  Ejecutando {nombre}...", end=" ", flush=True)
    try:
        proc = subprocess.run(
            [sys.executable, "bf-busqueda.py", json_path],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if "OK" in proc.stdout:
            print("✓")
        else:
            print(f"✗ ERROR\n    {proc.stderr.strip()[-200:]}")
            resultados.append({"nombre": nombre, "pasos": None, "distancia": None, "encontrado": False})
            continue
    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT (>3 min)")
        resultados.append({"nombre": nombre, "pasos": None, "distancia": None, "encontrado": False})
        continue

    # Leer CSV de resultado
    csv_dir = f"resultados/{nombre.replace('+', '_')}"
    csvs = [f for f in os.listdir(csv_dir) if f.endswith(".csv")] if os.path.isdir(csv_dir) else []
    if not csvs:
        print(f"  [!] No se encontró CSV en {csv_dir}")
        resultados.append({"nombre": nombre, "pasos": None, "distancia": None, "encontrado": False})
        continue

    df = pd.read_csv(os.path.join(csv_dir, csvs[0]), index_col=0)
    pasos     = df.loc["Steps taken", "Agent 0"] if "Steps taken" in df.index else None
    distancia = df.loc["Distance", "Agent 0"]    if "Distance"    in df.index else None
    encontrado= df.loc["Found Target", "Agent 0"] if "Found Target" in df.index else False

    resultados.append({
        "nombre":     nombre,
        "pasos":      float(pasos)     if pasos     is not None else None,
        "distancia":  float(distancia) if distancia is not None else None,
        "encontrado": str(encontrado).lower() == "true",
    })

# ============================================================
# 4. GRÁFICA COMPARATIVA
# ============================================================
df_res = pd.DataFrame(resultados).dropna(subset=["pasos"])
df_res = df_res.sort_values("pasos")

colores_map = {
    "ACO":        "#185FA5",
    "ABC":        "#0F6E56",
    "BHA":        "#993C1D",
    "lawnmower":  "#73726c",
    "expanding_sq": "#73726c",
    "voraz-heur": "#73726c",
    "voraz-myope": "#73726c",
}

def color_de(nombre):
    for key in colores_map:
        if nombre.startswith(key):
            return colores_map[key]
    return "#888"

colores = [color_de(n) for n in df_res["nombre"]]

fig, axes = plt.subplots(2, 1, figsize=(12, 10))
fig.suptitle("Comparativa de algoritmos — Framework MTS\n(mapa 30×30, semilla=42, 1 agente)", fontsize=13)

# Gráfica 1: Pasos
ax1 = axes[0]
bars1 = ax1.barh(df_res["nombre"], df_res["pasos"], color=colores, height=0.6)
ax1.set_xlabel("Pasos hasta detectar el objetivo")
ax1.set_title("Pasos hasta detección", fontsize=11)
ax1.axvline(df_res["pasos"].mean(), color="gray", linestyle="--", linewidth=0.8, label=f'Media: {df_res["pasos"].mean():.0f}')
ax1.legend(fontsize=9)
for bar, val in zip(bars1, df_res["pasos"]):
    ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
             f"{int(val)}", va="center", fontsize=9)

# Gráfica 2: Distancia
ax2 = axes[1]
bars2 = ax2.barh(df_res["nombre"], df_res["distancia"], color=colores, height=0.6)
ax2.set_xlabel("Distancia total recorrida")
ax2.set_title("Distancia total recorrida", fontsize=11)
ax2.axvline(df_res["distancia"].mean(), color="gray", linestyle="--", linewidth=0.8, label=f'Media: {df_res["distancia"].mean():.1f}')
ax2.legend(fontsize=9)
for bar, val in zip(bars2, df_res["distancia"]):
    ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
             f"{val:.1f}", va="center", fontsize=9)

# Leyenda de colores
leyenda = [
    mpatches.Patch(color="#185FA5", label="ACO (Romeo)"),
    mpatches.Patch(color="#0F6E56", label="ABC (Romeo)"),
    mpatches.Patch(color="#993C1D", label="BHA (Romeo)"),
    mpatches.Patch(color="#73726c", label="Clásicos (Yago)"),
]
fig.legend(handles=leyenda, loc="lower center", ncol=4, fontsize=10, bbox_to_anchor=(0.5, 0.01))

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig("comparativa_algoritmos.png", dpi=150, bbox_inches="tight")
plt.show()

print("\n✓ Gráfica guardada como comparativa_algoritmos.png")
print("\nResumen:")
print(df_res[["nombre", "pasos", "distancia", "encontrado"]].to_string(index=False))
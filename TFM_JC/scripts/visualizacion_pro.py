import os
import json
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Proj

def load_scenario_and_trajectory(perfil, algoritmo, semilla):
    """
    Carga el heatmap, los límites geográficos UTM y la trayectoria de simulación.
    """
    output_dir = f"TFM_JC/resultados/casa_de_campo_{perfil}"
    geojson_path = os.path.join(output_dir, "features.geojson")
    heatmap_path = os.path.join(output_dir, "heatmap.npy")
    
    if not os.path.exists(geojson_path) or not os.path.exists(heatmap_path):
        raise FileNotFoundError(f"No se encontraron metadatos o heatmap para el perfil {perfil}")
        
    with open(geojson_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    bounds = metadata["bounds"] # [minx, miny, maxx, maxy]
    center_point = metadata["center_point"]
    meter_per_bin = metadata["meter_per_bin"]
    
    lon, lat = center_point
    zone = int((lon + 180) / 6) + 1
    epsg = f"EPSG:326{zone}" if lat >= 0 else f"EPSG:327{zone}"
    proj_utm = Proj(epsg)
    
    heatmap = np.load(heatmap_path)
    
    mapeo_alg = {
        "voraz-heur": "voraz-heur",
        "ACO": "bf_aco_ET",
        "ABC": "bf_abc_ET",
        "BHA": "bf_bha_ET",
        "lawnmower": "lawnmower",
        "expanding_sq": "expanding"
    }
    alg_file = mapeo_alg.get(algoritmo, algoritmo)
    
    traj_dir = f"TFM_JC/resultados/escenario_{perfil}"
    traj_path = os.path.join(traj_dir, f"{alg_file}-{semilla}-traj.json")
    
    if not os.path.exists(traj_path):
        raise FileNotFoundError(f"No se encontró el archivo de trayectoria: {traj_path}")
        
    with open(traj_path, "r", encoding="utf-8") as f:
        traj_data = json.load(f)
        
    minx, miny, _, _ = bounds
    
    list_x_local = traj_data["list_x"][0]
    list_y_local = traj_data["list_y"][0]
    
    path_utm_x = [minx + x * meter_per_bin + 0.5 * meter_per_bin for x in list_x_local]
    path_utm_y = [miny + y * meter_per_bin + 0.5 * meter_per_bin for y in list_y_local]
    
    goal_local = traj_data["goal"] # [x, y]
    goal_utm_x = minx + goal_local[0] * meter_per_bin + 0.5 * meter_per_bin
    goal_utm_y = miny + goal_local[1] * meter_per_bin + 0.5 * meter_per_bin
    
    return heatmap, bounds, path_utm_x, path_utm_y, (goal_utm_x, goal_utm_y), meter_per_bin, (list_x_local, list_y_local)

def compute_updated_belief_map(heatmap, list_x_local, list_y_local, step_t, sensor_radius_cells=5):
    """
    Calcula el mapa de creencias actualizado b(v^t) aplicando la Huella del Sensor.
    Las celdas barridas se limpian a 0.0, reflejando el consumo directo de probabilidad del terreno.
    """
    belief = heatmap.copy()
    visited_mask = np.zeros_like(belief, dtype=bool)
    rows, cols = belief.shape
    limit = min(step_t + 1, len(list_x_local))
    
    r_idx, c_idx = np.ogrid[:rows, :cols]
    
    for i in range(limit):
        try:
            cx = float(list_x_local[i])
            cy = float(list_y_local[i])
            
            # Disco del radio del sensor del dron (5 celdas = 50m)
            dist_sq = (c_idx - cx)**2 + (r_idx - cy)**2
            in_fov = dist_sq <= (sensor_radius_cells**2)
            
            belief[in_fov] = 0.0
            visited_mask[in_fov] = True
        except Exception:
            pass
            
    return belief, visited_mask

def plot_escenario_inicial(perfil, algoritmo="voraz-heur", semilla=0, output_path=None):
    """
    Genera la figura de inicio del escenario: mapa de calor con LKP (inicio del dron) y una 'X' (víctima).
    """
    heatmap, bounds, path_x, path_y, goal_utm, _, _ = load_scenario_and_trajectory(perfil, algoritmo, semilla)
    
    fig, ax = plt.subplots(figsize=(8, 7))
    extent_correct = [bounds[0], bounds[2], bounds[1], bounds[3]]
    im = ax.imshow(heatmap, origin="lower", extent=extent_correct, cmap="YlOrRd", alpha=0.9)
    
    ax.scatter(path_x[0], path_y[0], color="blue", marker="o", s=150, edgecolor="white", linewidth=1.5, label="LKP (Start Position)")
    ax.scatter(goal_utm[0], goal_utm[1], color="red", marker="X", s=200, edgecolor="black", linewidth=1.5, label="Victim Position")
    
    ax.set_title(f"Initial Search Scenario: Profile {perfil.upper()}", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("UTM Easting (m)", fontsize=11)
    ax.set_ylabel("UTM Northing (m)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", facecolor="white", edgecolor="gray")
    
    fig.colorbar(im, ax=ax, label="Probability Density")
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Mapa del escenario inicial guardado en: {output_path}")
    
    return fig, ax

def plot_evolucion_temporal(perfil, algoritmo, semilla=0, hitos=None, output_path=None):
    """
    Genera un panel de 4 columnas (hitos temporales) mostrando la evolución del mapa de creencias b(v^k)
    con la escala fija de color para que se aprecie el barrido azul del dron sobre la probabilidad.
    """
    heatmap, bounds, path_x, path_y, goal_utm, _, (list_x, list_y) = load_scenario_and_trajectory(perfil, algoritmo, semilla)
    
    max_steps = len(path_x) - 1
    if hitos is None:
        hitos = [0, int(max_steps * 0.25), int(max_steps * 0.50), max_steps]
        
    fig, axes = plt.subplots(1, 4, figsize=(20, 5.5), sharey=True)
    extent_correct = [bounds[0], bounds[2], bounds[1], bounds[3]]
    vmax_inicial = np.max(heatmap)
    
    for idx, t in enumerate(hitos):
        ax = axes[idx]
        
        updated_belief, visited_mask = compute_updated_belief_map(heatmap, list_x, list_y, t, sensor_radius_cells=5)
        
        im = ax.imshow(updated_belief, origin="lower", extent=extent_correct, cmap="YlOrRd", vmin=0, vmax=vmax_inicial, alpha=0.85)
        
        if t > 0 and np.any(visited_mask):
            masked_visited = np.ma.masked_where(~visited_mask, visited_mask)
            ax.imshow(masked_visited, origin="lower", extent=extent_correct, cmap="Blues", alpha=0.5, zorder=2)
        
        ax.scatter(path_x[0], path_y[0], color="blue", marker="o", s=80, edgecolor="white", zorder=3)
        ax.scatter(goal_utm[0], goal_utm[1], color="red", marker="X", s=120, edgecolor="black", zorder=3)
        
        if t > 0:
            limit = min(t + 1, len(path_x))
            ax.plot(path_x[:limit], path_y[:limit], color="blue", linewidth=2.5, label="Search Path", zorder=4)
            ax.scatter(path_x[limit-1], path_y[limit-1], color="orange", marker="^", s=100, edgecolor="black", zorder=5, label="Drone Position")
            
        ax.set_title(f"$b(v^{{{t}}})$", fontsize=14, fontweight="bold")
        ax.set_xlabel("UTM Easting (m)", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.4)
        
        if idx == 0:
            ax.set_ylabel("UTM Northing (m)", fontsize=11)
            ax.scatter([], [], color="blue", marker="o", s=80, label="LKP (Start)")
            ax.scatter([], [], color="red", marker="X", s=120, label="Victim")
            ax.legend(loc="upper right", frameon=True, facecolor="white", prop={'size': 9})
            
    plt.suptitle(f"Belief Map Evolution $b(v^k)$: {algoritmo} (Profile: {perfil.upper()})", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Evolución temporal b(v^k) guardada en: {output_path}")
        
    return fig, axes

def plot_comparativa_algoritmos_lado_a_lado(perfil, alg1, alg2, semilla=0, hitos=None, output_path=None):
    """
    Genera un panel comparativo de 2 filas (algoritmos) y 3 columnas con títulos formales en inglés.
    """
    h1, bounds, p1_x, p1_y, g1_utm, _, (l1_x, l1_y) = load_scenario_and_trajectory(perfil, alg1, semilla)
    h2, _, p2_x, p2_y, g2_utm, _, (l2_x, l2_y) = load_scenario_and_trajectory(perfil, alg2, semilla)
    
    max_steps = min(len(p1_x), len(p2_x)) - 1
    if hitos is None:
        hitos = [int(max_steps * 0.25), int(max_steps * 0.50), max_steps]
        
    fig, axes = plt.subplots(2, 3, figsize=(16, 10), sharex=True, sharey=True)
    extent_correct = [bounds[0], bounds[2], bounds[1], bounds[3]]
    
    vmax1 = np.max(h1)
    vmax2 = np.max(h2)
    
    # Fila 1: Algoritmo 1
    for col_idx, t in enumerate(hitos):
        ax = axes[0, col_idx]
        b1_t, m1_t = compute_updated_belief_map(h1, l1_x, l1_y, t, sensor_radius_cells=5)
        ax.imshow(b1_t, origin="lower", extent=extent_correct, cmap="YlOrRd", vmin=0, vmax=vmax1, alpha=0.85)
        if np.any(m1_t):
            ax.imshow(np.ma.masked_where(~m1_t, m1_t), origin="lower", extent=extent_correct, cmap="Blues", alpha=0.5, zorder=2)
            
        ax.scatter(p1_x[0], p1_y[0], color="blue", marker="o", s=80, edgecolor="white", zorder=3)
        ax.scatter(g1_utm[0], g1_utm[1], color="red", marker="X", s=120, edgecolor="black", zorder=3)
        
        limit = min(t + 1, len(p1_x))
        ax.plot(p1_x[:limit], p1_y[:limit], color="blue", linewidth=2.5, zorder=4)
        ax.scatter(p1_x[limit-1], p1_y[limit-1], color="orange", marker="^", s=100, edgecolor="black", zorder=5)
        
        ax.set_title(f"{alg1} - $b(v^{{{t}}})$", fontsize=12, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.4)
        if col_idx == 0:
            ax.set_ylabel("UTM Northing (m)", fontsize=11)
            
    # Fila 2: Algoritmo 2
    for col_idx, t in enumerate(hitos):
        ax = axes[1, col_idx]
        b2_t, m2_t = compute_updated_belief_map(h2, l2_x, l2_y, t, sensor_radius_cells=5)
        ax.imshow(b2_t, origin="lower", extent=extent_correct, cmap="YlOrRd", vmin=0, vmax=vmax2, alpha=0.85)
        if np.any(m2_t):
            ax.imshow(np.ma.masked_where(~m2_t, m2_t), origin="lower", extent=extent_correct, cmap="Blues", alpha=0.5, zorder=2)
            
        ax.scatter(p2_x[0], p2_y[0], color="blue", marker="o", s=80, edgecolor="white", zorder=3)
        ax.scatter(g2_utm[0], g2_utm[1], color="red", marker="X", s=120, edgecolor="black", zorder=3)
        
        limit = min(t + 1, len(p2_x))
        ax.plot(p2_x[:limit], p2_y[:limit], color="purple", linewidth=2.5, zorder=4)
        ax.scatter(p2_x[limit-1], p2_y[limit-1], color="orange", marker="^", s=100, edgecolor="black", zorder=5)
        
        ax.set_title(f"{alg2} - $b(v^{{{t}}})$", fontsize=12, fontweight="bold")
        ax.set_xlabel("UTM Easting (m)", fontsize=11)
        ax.grid(True, linestyle=":", alpha=0.4)
        if col_idx == 0:
            ax.set_ylabel("UTM Northing (m)", fontsize=11)
            
    plt.suptitle(f"Algorithm Belief Map $b(v^k)$ Search Comparison (Profile: {perfil.upper()})", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Comparativa lado a lado guardada en: {output_path}")
        
    return fig, axes

def plot_filtro_restricciones(perfil="autista", output_path=None):
    """
    Genera la figura de 3 paneles 'Antes y Después' que solicitó Jompy:
    1. Mapa probabilístico base (sin filtrar)
    2. Máscara binaria de restricciones físicas (Agua y Edificios = 0)
    3. Mapa probabilístico final (filtrado y normalizado)
    """
    output_dir = f"TFM_JC/resultados/casa_de_campo_{perfil}"
    p_unfilt = os.path.join(output_dir, "heatmap_unfiltered.npy")
    p_filt = os.path.join(output_dir, "heatmap.npy")
    p_geo = os.path.join(output_dir, "features.geojson")
    
    if not (os.path.exists(p_unfilt) and os.path.exists(p_filt) and os.path.exists(p_geo)):
        raise FileNotFoundError(f"Archivos de mapa o restricciones no encontrados para el perfil {perfil}")
        
    map_unfilt = np.load(p_unfilt)
    map_filt = np.load(p_filt)
    
    with open(p_geo, "r", encoding="utf-8") as f:
        meta = json.load(f)
    bounds = meta["bounds"]
    extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
    
    mask = np.ones_like(map_unfilt)
    mask[map_filt == 0] = 0
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    im1 = axes[0].imshow(map_unfilt, origin="lower", extent=extent, cmap="YlOrRd")
    axes[0].set_title(f"1. Base Probability Map (Unfiltered)", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("UTM Easting (m)", fontsize=10)
    axes[0].set_ylabel("UTM Northing (m)", fontsize=10)
    fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)
    
    im2 = axes[1].imshow(mask, origin="lower", extent=extent, cmap="Blues_r", vmin=0, vmax=1)
    axes[1].set_title(f"2. Physical Restriction Mask (Water & Buildings = 0)", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("UTM Easting (m)", fontsize=10)
    fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)
    
    im3 = axes[2].imshow(map_filt, origin="lower", extent=extent, cmap="YlOrRd")
    axes[2].set_title(f"3. Final Filtered Map (Normalized)", fontsize=11, fontweight="bold")
    axes[2].set_xlabel("UTM Easting (m)", fontsize=10)
    fig.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04)
    
    plt.suptitle(f"Physical Restriction Filtering Process (Profile: {perfil.upper()})", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Gráfica de filtro de restricciones guardada en: {output_path}")
        
    return fig, axes

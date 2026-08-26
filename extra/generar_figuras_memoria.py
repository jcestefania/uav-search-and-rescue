"""
generar_figuras_memoria.py
==========================
Script dedicado exclusivamente a la generación y guardado en alta resolución (300 DPI)
de las figuras metodológicas, de contexto geográfico y de restricciones físicas para la
Memoria LaTeX / Artículo del TFM.

Figuras generadas:
1. Filtro de restricciones físicas de 4 paneles (Antes, Máscara Sindex, Satélite, Después).
2. Vista aérea satelital anotada (Google Earth / Esri Imagery).
3. Croquis visual del diseño experimental (LKP fijo vs víctimas estocásticas dentro de 3-sigma).
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt


def _draw_satellite_layer(ax, bounds):
    """
    Dibuja la capa satélite utilizando la imagen offline descargada previamente
    o contextily si está disponible.
    """
    sat_img_path = "TFM_JC/resultados/graficas/contexto_mapa_satelite.png"
    if os.path.exists(sat_img_path):
        img = plt.imread(sat_img_path)
        extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
        ax.imshow(img, extent=extent, origin="upper")
    else:
        try:
            import contextily as cx
            ax.set_xlim(bounds[0], bounds[2])
            ax.set_ylim(bounds[1], bounds[3])
            cx.add_basemap(ax, crs="EPSG:32630", source=cx.providers.Esri.WorldImagery)
        except Exception:
            ax.set_facecolor("#2b3e2b")


def plot_filtro_restricciones(perfil="autista", output_path=None):
    """
    Genera la figura unificada de 4 paneles en una sola fila:
    1. Base Density Map (Unfiltered)
    2. Physical Restriction Mask (Sindex 0.0 Filter)
    3. Satellite Aerial Context (Google Earth / Esri Imagery)
    4. Final Filtered & Normalized Map
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
    bounds = meta["bounds"] # [minx, miny, maxx, maxy]
    extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
    
    mask = np.ones_like(map_unfilt)
    mask[map_filt == 0] = 0
    
    fig, axes = plt.subplots(1, 4, figsize=(24, 5.2))
    
    # Centroides numéricos exactos de los 4 elementos
    lago_utm = (437716, 4474265)        # Lago de Casa de Campo (Este)
    parque_utm = (436462, 4473742)      # Parque de Atracciones (Centro-Sur)
    zoo_utm = (435258, 4473505)         # Zoo de Madrid (Suroeste)
    west_utm = (434248, 4475184)        # Edificaciones Urbanas (Oeste)
    
    # -------------------------------------------------------------------------
    # PANEL 1: Mapa Base Sin Filtrar
    # -------------------------------------------------------------------------
    im1 = axes[0].imshow(map_unfilt, origin="lower", extent=extent, cmap="YlOrRd")
    axes[0].set_title("1. Base Map (Unfiltered)", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("UTM Easting (m)", fontsize=10)
    axes[0].set_ylabel("UTM Northing (m)", fontsize=10)
    axes[0].grid(True, linestyle=":", alpha=0.4)
    fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04, label="Density")
    
    # -------------------------------------------------------------------------
    # PANEL 2: Máscara Binaria de Restricciones (Sindex Filter)
    # -------------------------------------------------------------------------
    im2 = axes[1].imshow(mask, origin="lower", extent=extent, cmap="Blues_r", vmin=0, vmax=1)
    axes[1].set_title("2. Physical Restriction Mask", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("UTM Easting (m)", fontsize=10)
    axes[1].grid(True, linestyle=":", alpha=0.4)
    
    axes[1].annotate("Lake (Water=0.0)", xy=lago_utm, xytext=(lago_utm[0]-1600, lago_utm[1]+1000),
                    arrowprops=dict(facecolor="red", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="darkred", bbox=dict(boxstyle="round,pad=0.2", fc="yellow", ec="red", alpha=0.9))
                    
    axes[1].annotate("Parque Atracciones", xy=parque_utm, xytext=(parque_utm[0]+400, parque_utm[1]+900),
                    arrowprops=dict(facecolor="red", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="darkred", bbox=dict(boxstyle="round,pad=0.2", fc="yellow", ec="red", alpha=0.9))
                    
    axes[1].annotate("Madrid Zoo", xy=zoo_utm, xytext=(zoo_utm[0]-1100, zoo_utm[1]-700),
                    arrowprops=dict(facecolor="red", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="darkred", bbox=dict(boxstyle="round,pad=0.2", fc="yellow", ec="red", alpha=0.9))
                    
    axes[1].annotate("Urban Buildings", xy=west_utm, xytext=(west_utm[0]+400, west_utm[1]+800),
                    arrowprops=dict(facecolor="red", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="darkred", bbox=dict(boxstyle="round,pad=0.2", fc="yellow", ec="red", alpha=0.9))
                    
    fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04, label="Mask (0=Restricted)")
    
    # -------------------------------------------------------------------------
    # PANEL 3: Vista Satélite Real (Google Earth / Esri Imagery)
    # -------------------------------------------------------------------------
    axes[2].set_xlim(bounds[0], bounds[2])
    axes[2].set_ylim(bounds[1], bounds[3])
    _draw_satellite_layer(axes[2], bounds)
    axes[2].set_title("3. Satellite Aerial View", fontsize=11, fontweight="bold")
    axes[2].set_xlabel("UTM Easting (m)", fontsize=10)
    axes[2].grid(True, linestyle=":", alpha=0.4)
    
    axes[2].annotate("Lake", xy=lago_utm, xytext=(lago_utm[0]-1400, lago_utm[1]+900),
                    arrowprops=dict(facecolor="yellow", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="yellow", alpha=0.95))
                    
    axes[2].annotate("Amusement Park", xy=parque_utm, xytext=(parque_utm[0]+400, parque_utm[1]+800),
                    arrowprops=dict(facecolor="yellow", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="yellow", alpha=0.95))
                    
    axes[2].annotate("Zoo", xy=zoo_utm, xytext=(zoo_utm[0]-1000, zoo_utm[1]-700),
                    arrowprops=dict(facecolor="yellow", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="yellow", alpha=0.95))
                    
    axes[2].annotate("Buildings", xy=west_utm, xytext=(west_utm[0]+400, west_utm[1]+700),
                    arrowprops=dict(facecolor="yellow", edgecolor="black", width=1.5, headwidth=7, shrink=0.05),
                    fontsize=8, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="yellow", alpha=0.95))
                    
    # -------------------------------------------------------------------------
    # PANEL 4: Mapa Final Filtrado y Normalizado
    # -------------------------------------------------------------------------
    im4 = axes[3].imshow(map_filt, origin="lower", extent=extent, cmap="YlOrRd")
    axes[3].set_title("4. Final Filtered Map", fontsize=11, fontweight="bold")
    axes[3].set_xlabel("UTM Easting (m)", fontsize=10)
    axes[3].grid(True, linestyle=":", alpha=0.4)
    fig.colorbar(im4, ax=axes[3], fraction=0.046, pad=0.04, label="Normalized Density")
    
    plt.suptitle(f"Physical Restriction Filtering Process: Water & Buildings = 0.0 (Profile: {perfil.upper()})", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Gráfica unificada de 4 paneles guardada en: {output_path}")
        
    return fig, axes


def plot_filtro_restricciones_satelite(perfil="autista", output_path=None):
    """
    Genera la figura de vista Satélite real (tipo Google Earth / Esri World Imagery)
    con las 4 anotaciones explícitas señalando el Lago, Zoo, Parque de Atracciones y Edificios.
    """
    output_dir = f"TFM_JC/resultados/casa_de_campo_{perfil}"
    p_geo = os.path.join(output_dir, "features.geojson")
    
    if not os.path.exists(p_geo):
        raise FileNotFoundError(f"Archivo geojson no encontrado para el perfil {perfil}")
        
    with open(p_geo, "r", encoding="utf-8") as f:
        meta = json.load(f)
    bounds = meta["bounds"] # [minx, miny, maxx, maxy] en UTM EPSG:32630
    
    fig, ax = plt.subplots(figsize=(10, 8.5))
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    
    _draw_satellite_layer(ax, bounds)
    
    # Centroides numéricos exactos de los 4 elementos
    lago_utm = (437716, 4474265)        # Lago de Casa de Campo (Este)
    parque_utm = (436462, 4473742)      # Parque de Atracciones (Centro-Sur)
    zoo_utm = (435258, 4473505)         # Zoo de Madrid (Suroeste)
    west_utm = (434248, 4475184)        # Edificaciones Urbanas (Oeste)
    
    # 1. Lago de Casa de Campo
    ax.annotate(
        "Lake of Casa de Campo\n(Water Body)", 
        xy=lago_utm, 
        xytext=(lago_utm[0] - 1800, lago_utm[1] + 1000),
        arrowprops=dict(facecolor="yellow", edgecolor="black", width=2, headwidth=9, shrink=0.05),
        fontsize=10, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="yellow", lw=2, alpha=0.95)
    )
    
    # 2. Parque de Atracciones
    ax.annotate(
        "Amusement Park\n(Structures)", 
        xy=parque_utm, 
        xytext=(parque_utm[0] + 600, parque_utm[1] + 900),
        arrowprops=dict(facecolor="yellow", edgecolor="black", width=2, headwidth=9, shrink=0.05),
        fontsize=10, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="yellow", lw=2, alpha=0.95)
    )
    
    # 3. Zoo de Madrid
    ax.annotate(
        "Madrid Zoo\n(Structures)", 
        xy=zoo_utm, 
        xytext=(zoo_utm[0] - 1200, zoo_utm[1] + 400),
        arrowprops=dict(facecolor="yellow", edgecolor="black", width=2, headwidth=9, shrink=0.05),
        fontsize=10, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="yellow", lw=2, alpha=0.95)
    )
    
    # 4. Edificaciones Urbanas
    ax.annotate(
        "Urban Buildings\n(Structures)", 
        xy=west_utm, 
        xytext=(west_utm[0] + 600, west_utm[1] + 800),
        arrowprops=dict(facecolor="yellow", edgecolor="black", width=2, headwidth=9, shrink=0.05),
        fontsize=10, fontweight="bold", color="black", bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="yellow", lw=2, alpha=0.95)
    )
    
    ax.set_title("Satellite Aerial Context - Casa de Campo (Madrid)", fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("UTM Easting (m)", fontsize=11)
    ax.set_ylabel("UTM Northing (m)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Gráfica vista Satélite guardada en: {output_path}")
        
    return fig, ax


def plot_croquis_aleatoriedad(perfil="autista", num_seeds=25, output_path=None):
    """
    Genera el croquis visual que ilustra el diseño experimental:
    - Posición de despegue del dron FIJA en el centro (LKP / Puesto de Mando Bomberos)
    - Posiciones de víctimas ALEATORIAS (multi-semillas) dentro del 3-sigma sobre zonas transitables
    """
    output_dir = f"TFM_JC/resultados/casa_de_campo_{perfil}"
    p_filt = os.path.join(output_dir, "heatmap.npy")
    p_geo = os.path.join(output_dir, "features.geojson")
    
    if not (os.path.exists(p_filt) and os.path.exists(p_geo)):
        raise FileNotFoundError(f"Archivos del perfil {perfil} no encontrados")
        
    map_filt = np.load(p_filt)
    with open(p_geo, "r", encoding="utf-8") as f:
        meta = json.load(f)
        
    bounds = meta["bounds"]
    extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
    meter_per_bin = meta["meter_per_bin"]
    
    # 1. Centro exacto del mapa (LKP / Puesto de Mando Fijo)
    center_x = (bounds[0] + bounds[2]) / 2.0
    center_y = (bounds[1] + bounds[3]) / 2.0
    
    # 2. Generar posiciones aleatorias estocásticas de víctimas basadas en la probabilidad del mapa
    np.random.seed(42)
    prob_flat = map_filt.flatten()
    prob_normalized = prob_flat / np.sum(prob_flat)
    
    # Muestra estocástica de índices de celdas
    chosen_indices = np.random.choice(len(prob_flat), size=num_seeds, p=prob_normalized, replace=False)
    rows, cols = np.unravel_index(chosen_indices, map_filt.shape)
    
    victim_utmx = bounds[0] + cols * meter_per_bin + 0.5 * meter_per_bin
    victim_utmy = bounds[1] + rows * meter_per_bin + 0.5 * meter_per_bin
    
    fig, ax = plt.subplots(figsize=(10, 8.5))
    im = ax.imshow(map_filt, origin="lower", extent=extent, cmap="YlOrRd", alpha=0.85)
    
    # Dibujar las múltiples víctimas aleatorias (X rojas)
    ax.scatter(victim_utmx, victim_utmy, c="red", marker="x", s=65, linewidths=2.0, zorder=4, label=f"Random Victim Targets ({num_seeds} Seeds)")
    
    # Dibujar el punto inicial del dron FIJO en el centro (Estrella azul brillante)
    ax.scatter([center_x], [center_y], c="blue", marker="*", s=350, edgecolor="white", linewidths=1.5, zorder=5, label="Fixed Drone Takeoff (LKP / Command Post)")
    
    # Anotación explicativa para el LKP
    ax.annotate(
        "FIXED Drone Origin (LKP)\nCasa de Campo Center", 
        xy=(center_x, center_y), 
        xytext=(center_x - 2200, center_y + 1200),
        arrowprops=dict(facecolor="blue", edgecolor="black", width=2, headwidth=9, shrink=0.08),
        fontsize=10, fontweight="bold", color="darkblue", bbox=dict(boxstyle="round,pad=0.4", fc="aliceblue", ec="blue", lw=2, alpha=0.95)
    )
    
    ax.set_title(f"Experimental Setup: Fixed Drone LKP vs. Stochastic Victims (Profile: {perfil.upper()})", fontsize=12, fontweight="bold", pad=15)
    ax.set_xlabel("UTM Easting (m)", fontsize=11)
    ax.set_ylabel("UTM Northing (m)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.4)
    ax.legend(loc="upper right", fontsize=10, framealpha=0.9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Prior Probability Density")
    
    plt.tight_layout()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Croquis de aleatoriedad guardado en: {output_path}")
        
    return fig, ax


def generar_todas_las_figuras():
    """
    Ejecuta y guarda todas las figuras conceptuales para la Memoria.
    """
    perfiles = ["autista", "demencia", "senderista"]
    out_dir = "TFM_JC/resultados/graficas"
    os.makedirs(out_dir, exist_ok=True)
    
    print("=== Generando Figuras para la Memoria del TFM ===")
    for p in perfiles:
        print(f"-> Generando figuras para perfil {p.upper()}...")
        plot_filtro_restricciones(perfil=p, output_path=os.path.join(out_dir, f"filtro_restricciones_{p}.png"))
        plt.close()
        
        plot_filtro_restricciones_satelite(perfil=p, output_path=os.path.join(out_dir, f"vista_satelite_{p}.png"))
        plt.close()
        
    print("-> Generando croquis de diseño experimental (LKP vs Víctimas)...")
    plot_croquis_aleatoriedad(perfil="autista", num_seeds=25, output_path=os.path.join(out_dir, "croquis_aleatoriedad_escenario.png"))
    plt.close()
    
    print(f"\n¡Todas las figuras de la memoria han sido generadas con éxito en {out_dir}!")


if __name__ == "__main__":
    generar_todas_las_figuras()

"""
generar_gif_animacion.py
========================
Genera animaciones GIF optimizadas y de alta definición (HD) de las misiones
de búsqueda y rescate de drones en la Casa de Campo para presentaciones y defensa del TFM.

Genera:
1. animacion_busqueda_bha.gif (BHA - Perfil Demencia, detección en t = 243 pasos)
2. animacion_busqueda_abc.gif (ABC - Perfil Demencia, detección en t = 389 pasos)
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

# Añadir directorio raíz al path y fijar CWD
BASE_MTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOFTWARE_DIR = os.path.dirname(os.path.dirname(BASE_MTS_DIR))
os.chdir(BASE_MTS_DIR)
sys.path.insert(0, BASE_MTS_DIR)
import extra.visualizacion_pro as vis_pro


def generar_gif_mision(perfil="demencia", algoritmo="BHA", semilla=14, step_jump=4,
                       output_gif="presentacion/animacion_busqueda_bha.gif", fps=10):
    """
    Renderiza y ensambla un GIF animado mostrando el avance del UAV,
    la huella de barrido del sensor de 50m y el consumo del mapa de creencias residual b(v^k).
    """
    print(f"\n--- Generando animación GIF para {algoritmo} ({perfil.upper()}, Semilla {semilla}) ---")
    
    # Cargar escenario y trayectoria
    h, bounds, px, py, g, m, (lx, ly) = vis_pro.load_scenario_and_trajectory(perfil, algoritmo, semilla)
    
    total_steps = len(px)
    lkp_x, lkp_y = px[0], py[0]
    goal_x, goal_y = g
    extent_all = [bounds[0], bounds[2], bounds[1], bounds[3]]
    
    # Ventana de visualización enfocada sobre el teatro de operaciones (centro LKP)
    span = 900
    xlim = [lkp_x - span, lkp_x + span]
    ylim = [lkp_y - span, lkp_y + span]
    
    # Lista de pasos a renderizar
    sample_steps = list(range(0, total_steps, step_jump))
    if sample_steps[-1] != total_steps - 1:
        sample_steps.append(total_steps - 1)
        
    frames = []
    vmax = np.max(h)
    
    # Precalcular distancias acumuladas
    dist_acum = [0.0]
    for i in range(1, total_steps):
        d = np.hypot(px[i] - px[i-1], py[i] - py[i-1])
        dist_acum.append(dist_acum[-1] + d)
        
    print(f"Total pasos: {total_steps} | Cuadros a renderizar: {len(sample_steps)}")
    
    for idx, t in enumerate(sample_steps):
        fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=100)
        
        # Calcular mapa de creencias residual b(v^t)
        b_t, m_t = vis_pro.compute_updated_belief_map(h, lx, ly, t, sensor_radius_cells=5)
        
        # 1. Mapa de probabilidad residual
        ax.imshow(b_t, origin='lower', extent=extent_all, cmap='YlOrRd', vmin=0, vmax=vmax, alpha=0.88)
        
        # 2. Huella azul de celdas ya inspeccionadas por el sensor
        if np.any(m_t):
            ax.imshow(np.ma.masked_where(~m_t, m_t), origin='lower', extent=extent_all, cmap='Blues', alpha=0.45, zorder=2)
            
        # 3. Trayectoria acumulada del UAV
        limit = t + 1
        line_color = '#1f77b4' if algoritmo == 'BHA' else '#9467bd'
        ax.plot(px[:limit], py[:limit], color=line_color, linewidth=2.6, zorder=4, label='Ruta UAV')
        
        # 4. Marcadores de Despegue (LKP) y Víctima
        ax.scatter(lkp_x, lkp_y, color='#0000aa', marker='o', s=130, edgecolor='white', linewidth=2, label='Despegue (LKP)', zorder=5)
        ax.scatter(goal_x, goal_y, color='#cc0000', marker='X', s=170, edgecolor='black', linewidth=1.8, label='Víctima (Montecarlo)', zorder=5)
        
        # 5. Dron y huella del sensor instantánea (Rd = 50 m)
        curr_x, curr_y = px[t], py[t]
        dist_sensor_target = np.hypot(curr_x - goal_x, curr_y - goal_y)
        is_detected = (t == total_steps - 1) or (dist_sensor_target <= 50.0)
        
        sensor_color = '#00aa00' if is_detected else '#2ca02c'
        sensor_circle = plt.Circle((curr_x, curr_y), 50, color=sensor_color, fill=False, linewidth=2.8, linestyle='--', zorder=6, label='Sensor ($R_d=50$ m)')
        ax.add_patch(sensor_circle)
        ax.scatter(curr_x, curr_y, color='orange', marker='^', s=150, edgecolor='black', linewidth=1.5, zorder=7)
        
        # Parámetros espaciales y HUD
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel("UTM Este (m)", fontsize=10.5)
        ax.set_ylabel("UTM Norte (m)", fontsize=10.5)
        ax.grid(True, linestyle=':', alpha=0.45)
        
        # Títulos e información de telemetría
        minutos = dist_acum[t] / (10.0 * 60.0) # a velocidad de crucero 10 m/s
        ax.set_title(f"Simulación de Búsqueda SAR: {algoritmo} - Perfil {perfil.capitalize()}\n"
                     f"Paso: {t:3d}/{total_steps-1} | Distancia: {dist_acum[t]/1000.0:4.2f} km | Tiempo: {minutos:3.1f} min",
                     fontsize=12, fontweight='bold', pad=10)
                     
        # Banner de estado de misión
        if is_detected and t == total_steps - 1:
            status_text = f"¡CONTACTO VISUAL CONFIRMADO!\nt = {t} pasos ({minutos:.1f} min) | d_aprox = {dist_sensor_target:.1f} m"
            bbox_props = dict(boxstyle='round,pad=0.5', facecolor='#28a745', edgecolor='black', alpha=0.95)
            ax.text(0.5, 0.05, status_text, transform=ax.transAxes, fontsize=11, fontweight='bold',
                    color='white', ha='center', va='bottom', bbox=bbox_props, zorder=10)
        else:
            status_text = f"BUSCANDO... Sensor-Víctima: {dist_sensor_target:.0f} m"
            bbox_props = dict(boxstyle='round,pad=0.4', facecolor='#ffffff', edgecolor='#333333', alpha=0.88)
            ax.text(0.5, 0.05, status_text, transform=ax.transAxes, fontsize=10, fontweight='bold',
                    color='#222222', ha='center', va='bottom', bbox=bbox_props, zorder=10)
                    
        ax.legend(loc='upper right', framealpha=0.92, fontsize=9.5)
        plt.tight_layout()
        
        # Convertir figura a imagen en memoria
        fig.canvas.draw()
        rgba_img = np.asarray(fig.canvas.buffer_rgba())
        pil_img = Image.fromarray(rgba_img).convert('RGB')
        frames.append(pil_img)
        plt.close(fig)
        
        if (idx + 1) % 15 == 0 or idx == len(sample_steps) - 1:
            print(f"  > Progreso: {idx + 1}/{len(sample_steps)} cuadros procesados...")
            
    # Congelar el último cuadro con la detección durante 2 segundos (20 cuadros adicionales a 10 fps)
    for _ in range(18):
        frames.append(frames[-1])
        
    os.makedirs(os.path.dirname(output_gif), exist_ok=True)
    
    # Guardar como GIF animado con paleta optimizada
    duration_ms = int(1000 / fps)
    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True
    )
    
    size_mb = os.path.getsize(output_gif) / (1024 * 1024)
    print(f"¡Animación guardada con éxito!\n -> {output_gif} ({size_mb:.2f} MB)")
    return output_gif


if __name__ == "__main__":
    # Generar GIF de BHA (detección en t = 243 pasos)
    gif_bha_pres = os.path.join(SOFTWARE_DIR, "presentacion", "animacion_busqueda_bha.gif")
    generar_gif_mision(perfil="demencia", algoritmo="BHA", semilla=14, step_jump=4,
                       output_gif=gif_bha_pres, fps=10)
                       
    # Copiar también a memoria/imagenes
    memoria_gif = os.path.join(SOFTWARE_DIR, "memoria", "imagenes", "animacion_busqueda_bha.gif")
    os.makedirs(os.path.dirname(memoria_gif), exist_ok=True)
    import shutil
    shutil.copyfile(gif_bha_pres, memoria_gif)
    print(f"Copia realizada en: {memoria_gif}")

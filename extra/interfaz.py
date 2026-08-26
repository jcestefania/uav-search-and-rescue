"""Funciones para generar la interfaz gráfica de la simulación"""

import os
import sys

import numpy as np
try:
    import plotly.graph_objects as go
    import plotly.io as pio
except ImportError:
    go = None
    pio = None
from PIL import Image

from .perimetro import perimetro_cuadrado


def dibujar_animacion(
    n_agents,
    list_track_x,
    list_track_y,
    list_track_z,
    BK,
    goal,
    size,
    steps,
    seed,
    perimeter_func,
    box_offset=1.0,
    height=10,
    ground_offset=0.2,
    agent_offset=0.5,
    horizon_size=None,
    templ="plotly_white",
    camera_angle="isometric",
    to_gif=False,
):
    """
    Genera y muestra una animación con los datos de la simulación

    Parametros:
        n_agents: Número de agentes
        list_track_x: Lista con la coordenada x de los caminos de los agentes
        list_track_y: Lista con la coordenada y de los caminos de los agentes
        list_track_z: Lista con la coordenada z de los caminos de los agentes
        BK: Lista con las probabilidades de la creencia
        goal: Lista con las coordenadas del objetivo
        size: Tamaño del mapa
        mov_delta: Distancia que se desplaza el agente en cada paso
        steps: Número de pasos
        seed: Semilla usada para la aleatoriedad
        perimeter_func: Función para dibujar el perimetro del sensor, desde la posición actual del agente.
        box_offset: Offset horizontal para el mapa de probabilidad con las "paredes" de la simulación
        height: Altura de vuelo
        ground_offset: Offset vertical para hacer que la probabilidad no cubra el objetivo
        agent_offset: Offset vertical para separar los caminos de los drones
        horizon_size: Tamaño del horizonte (None para no mostrar)
        templ: Paleta de colores para la animación
        camera_angle: Ángulo por defecto para la visualización
        to_gif: Exportar la animación como un gif (puede tardar mucho)
    Ejemplos:
    # Un agente
    dibujar_animacion(1, [[0, 1, 2, 3]], [[0, 1, 2, 3]], [[8, 8, 8, 8]], BK, [0, 3], [10, 10], 4, 10 1, 8, 0.2, 0.5, None "simple_white", "vertical")
    # Varios agentes (3)
    dibujar_animacion(3, [[0, 1, 2, 3, 4, 5], [1, 1, 1, 1, 1, 1], [0, 0, 1, 0, 1, 2]], [[0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 5], [0, 1, 2, 3, 4, 3]], [[8, 8, 8, 8, 8, 8], [8, 7, 7, 6, 7, 8], [8, 8, 8, 8, 8, 8]], BK, [4, 3], [10, 10], 6, 4, 1, 8, 0.2, 0.5, None,"seaborn", "isometric")
    """
    if go is None or pio is None:
        print("Plotly no está disponible en este entorno. Animación omitida.")
        return None

    # Parametros del espacio 3D
    # Restamos 1 porque los bordes del mapa están definidos en el intervalo [0, size)
    xm = -box_offset
    xM = size[0] - 1 + box_offset
    ym = -box_offset
    yM = size[1] - 1 + box_offset
    zm = 0
    zM = height

    # Asignar un color de la paleta a cada agente
    # Colores aceptados por plotly
    # https://plotly.com/python/templates/#using-builtin-themes
    default_templates = [
        "ggplot2",
        "seaborn",
        "simple_white",
        "plotly",
        "plotly_white",
        "plotly_dark",
        "presentation",
        "xgridoff",
        "ygridoff",
        "gridon",
        "none",
    ]
    if templ not in default_templates:
        raise ValueError(f"Template {templ} not found")

    colors = [c for c in pio.templates[templ]["layout"]["colorway"]]  # type: ignore

    # Ángulo de la cámara
    # Diccionario con POVs
    # Referencia: https://plotly.com/python/3d-camera-controls/
    cam_angles = {
        "isometric": dict(eye=dict(x=1.0, y=1.0, z=2.5)),
        "vertical": dict(eye=dict(x=-0.3, y=0.0, z=2.0)),
        "side": dict(eye=dict(x=0.0, y=2.5, z=0.0)),
    }
    camera_angle = camera_angle.lower()  # Para que acepte si se usan mayusculas
    if camera_angle not in cam_angles.keys():
        raise ValueError(
            f"Camera positions: {camera_angle} not found, posible values: {cam_angles.keys()}"
        )

    # Convertir a numpy array si es necesario
    list_track_y = np.array(list_track_y)
    list_track_x = np.array(list_track_x)
    list_track_z = np.array(list_track_z)

    # Generar los fotogramas (con submuestreo si hay demasiados pasos para evitar errores de memoria/límite de Plotly)
    step_skip = 1
    if steps > 100:
        step_skip = int(np.ceil(steps / 100))

    ui_frames = []
    for k in range(0, steps, step_skip):
        iter_horitonte = 50 * (k // 50)
        centro_horizonte = (
            list_track_x[0][iter_horitonte],
            list_track_y[0][iter_horitonte],
        )

        y_target = max(0, min(int(goal[k][1]), BK[k].shape[0] - 1))
        x_target = max(0, min(int(goal[k][0]), BK[k].shape[1] - 1))
        z_target = BK[k][y_target, x_target] * 25 + 1.5  # Situar 1.5 metros por encima de la superficie de probabilidad

        data = [
            go.Surface(
                z=BK[k] * 25,  # Escalado para que las probabilidades se vean bien
                colorscale="YlOrRd",
                colorbar=dict(orientation="h", y=-0.25, x=0.5),
                name="Prob",
            ),
            go.Scatter3d(
                x=[goal[k][0]],
                y=[goal[k][1]],
                z=[z_target],
                name="Target",
                mode="markers",
                marker_symbol="x",
                marker=dict(size=6, color="red"),
            ),
        ]
        if horizon_size:
            horizon_border = go.Scatter3d(
                x=perimetro_cuadrado(centro_horizonte, 0)[0],
                y=perimetro_cuadrado(centro_horizonte, 0)[1],
                z=list_track_z[0] * 0,
                name=f"Limite del horizonte {iter_horitonte}",
                mode="lines",
                marker=dict(size=4, color="yellow"),
            )
            data.append(horizon_border)
        for agent in range(n_agents):
            # Si hay más agentes que colores
            agent_colors = agent % len(colors)
            # NOTE: Extraemos la lista de posiciones para que sea más compacto
            agent_x = list_track_x[agent]
            agent_y = list_track_y[agent]
            agent_z = list_track_z[agent]
            drone = go.Scatter3d(
                x=[agent_x[k]],
                y=[agent_y[k]],
                z=[agent_z[k] - agent_offset * agent],
                name=f"Drone {agent}",
                mode="markers",
                marker_symbol="circle",
                marker=dict(size=3, color=colors[agent_colors]),
            )
            ground = go.Scatter3d(
                x=[agent_x[k]],
                y=[agent_y[k]],
                z=[agent_z[k] * 0],
                name=f"Ground {agent}",
                mode="markers",
                marker_symbol="x",
                marker=dict(size=3, color=colors[agent_colors]),
            )
            path = go.Scatter3d(
                x=agent_x,
                y=agent_y,
                z=agent_z - agent_offset * agent,
                name=f"Path {agent}",
                mode="lines",
                line=dict(width=3, color=colors[agent_colors]),
            )
            v_line = go.Scatter3d(
                x=[agent_x[k], agent_x[k]],
                y=[agent_y[k], agent_y[k]],
                z=[agent_z[k] - agent_offset * agent, 0],
                name=f"Vertical sensor line {agent}",
                mode="lines",
                marker=dict(size=4, color=colors[agent_colors]),
            )
            sensor_circle = go.Scatter3d(
                x=perimeter_func([agent_x[k], agent_y[k]])[0],
                y=perimeter_func([agent_x[k], agent_y[k]])[1],
                z=list_track_z[agent] * 0 + ground_offset,
                name=f"Sensor detection area {agent}",
                mode="lines",
                line=dict(width=4, color=colors[agent_colors]),
            )

            data.append(drone)
            data.append(ground)
            data.append(path)
            data.append(v_line)
            data.append(sensor_circle)
        ui_frames.append(go.Frame(data=data))

    menu_buttons = [
        dict(
            type="buttons",
            showactive=False,
            buttons=[
                dict(
                    label="Play",
                    method="animate",
                    args=[
                        None,
                        {
                            "frame": {"duration": 200, "redraw": True},
                            "fromcurrent": True,
                            "transition": {
                                "duration": 20,
                                "easing": "quadratic-in-out",
                            },
                        },
                    ],
                ),
                dict(
                    label="Pause",
                    method="animate",
                    args=[
                        [None],
                        {
                            "frame": {"duration": 0, "redraw": True},
                            "mode": "immediate",
                        },
                    ],
                ),
                dict(
                    label="Reset",
                    method="animate",
                    args=[
                        None,
                        {
                            "frame": {"duration": 20, "redraw": True},
                            "mode": "immediate",
                            "transition": {"duration": 0},
                        },
                    ],
                ),
            ],
        ),
    ]

    # Mostrar
    fig = go.Figure(
        data=ui_frames[0]["data"],
        frames=ui_frames,
        layout=go.Layout(
            width=1000,
            height=1000,
            scene=dict(
                xaxis=dict(range=[xm, xM], title="x [m]", autorange=False),
                yaxis=dict(range=[ym, yM], title="y [m]", autorange=False),
                zaxis=dict(range=[zm, zM], title="z [m]", autorange=False),
            ),
            updatemenus=menu_buttons,
        ),
    )

    camera = cam_angles[camera_angle]
    titulo = f"Búsqueda de objetivo usando semilla {seed}"
    fig.update_layout(scene_camera=camera, template=templ, title=titulo)
    fig.show()


    # Exportar a video/gif
    if not to_gif:
        return

    # Directorio con los fotogramas
    os.makedirs("frames", exist_ok=True)

    total_frames = len(fig.frames)
    print("Creando animacion...")
    for i, frame in enumerate(fig.frames):
        # Crear la imagen y la guardamos
        frame_fig = fig
        frame_fig.update(data=frame.data)
        pio.write_image(frame_fig, f"frames/frame_{i:03d}.png")
        # Contador de progreso
        progress = (i + 1) / total_frames * 100
        sys.stdout.write(f"\rProcesando: {i+1}/{total_frames} frames ({progress:.1f}%)")
        sys.stdout.flush()

    # Combinar a un GIF
    frames = []
    for i in range(len(fig.frames)):
        frames.append(Image.open(f"frames/frame_{i:03d}.png"))
    print("¡Animación creada!")

    # Guardar gif
    frames[0].save(
        "imagenes/animation.gif",
        save_all=True,
        append_images=frames[1:],
        optimize=False,
        duration=100,  # milliseconds por frame
        loop=0,  # 0 → loop infinito
    )
    # Borrar los fotogramas
    os.system("rm -fr frames/")
    print("Borrando imágenes intermedias")

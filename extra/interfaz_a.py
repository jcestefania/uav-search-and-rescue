"""Funciones para generar la interfaz gráfica de la simulación"""

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from scipy.ndimage import zoom


from .perimetro import perimetro_circulo, perimetro_cuadrado


def dibujar_animacion_a(
    n_agents,
    list_track_x,
    list_track_y,
    list_track_z,
    BK,
    goal,
    size,
    steps,
    seed,
    tc,
    detect_radius=1.0,
    height=10,
    ground_offset=0.2,
    agent_offset=0.5,
    horizon_size=None,
    templ="plotly_white",
):

    """Este código es igual que el de interfaz.py pero se hace el rescalado a mis dimensiones"""
    #tc = 10
    # Es un numpy array de una lista (como si fuese una lista dentro de una lista y tuviese que coger la primera)
    
    #list_track_x[0][1:] *= tc
    #list_track_y[0][1:] *= tc
    """   
    for i in range(len(list_track_x[0])):
        print(f'X: {list_track_x[0][i]}. Y: {list_track_y[0][i]}')"""
        #list_track_z[i] *= tc

    #print(list_track_x[0])
    #print(list_track_y[0])

    goal[0], goal[1] = goal[0]*tc, goal[1]*tc

    #print(size)
    #print(detect_radius)
    # Parametros
    xm = -detect_radius
    xM = size[0] *tc
    ym = -detect_radius
    yM = size[1] *tc
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

    # Convertir a numpy array si es necesario
    list_track_y = np.array(list_track_y)
    list_track_x = np.array(list_track_x)
    list_track_z = np.array(list_track_z)

    # Generar los fotogramas
    ui_frames = []
    for k in range(steps):
        iter_horitonte = 50 * (k // 50)
        centro_horizonte = (
            list_track_x[0][iter_horitonte],
            list_track_y[0][iter_horitonte],
        )
        
        BK_rescaled = zoom(BK[k], zoom=tc, order=1) 
        """The zoom function from SciPy's ndimage module resizes an array by a given scale factor using interpolation.
        Interpolation is a method of estimating values between known data points. It’s commonly used when resizing images, scaling arrays, or filling in missing values."""
        
        data = [
            # Adjust x and y axes dynamically
            go.Surface(
                z=BK_rescaled,
                x=np.linspace(0, size[0]*tc, BK_rescaled.shape[1]),  # Scale x-axis dynamically
                y=np.linspace(0, size[1]*tc, BK_rescaled.shape[0]),  # Scale y-axis dynamically
                colorscale="hot",
                colorbar=dict(orientation="h", y=-0.25, x=0.5),
                name="Prob",
            ),
            go.Scatter3d(
                x=[goal[0]],
                y=[goal[1]],
                z=[ground_offset],
                name="Target",
                mode="markers",
                marker_symbol="x",
                marker=dict(size=4, color="red"),
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
            drone = go.Scatter3d(
                x=[list_track_x[agent][k]],
                y=[list_track_y[agent][k]],
                z=[list_track_z[agent][k] - agent_offset * agent],
                name=f"Drone {agent}",
                mode="markers",
                marker_symbol="circle",
                marker=dict(size=4, color=colors[agent_colors]),
            )
            ground = go.Scatter3d(
                x=[list_track_x[agent][k]],
                y=[list_track_y[agent][k]],
                z=[list_track_z[agent][k] * 0],
                name=f"Ground {agent}",
                mode="markers",
                marker_symbol="x",
                marker=dict(size=3, color=colors[agent_colors]),
            )
            path = go.Scatter3d(
                x=list_track_x[agent],
                y=list_track_y[agent],
                z=list_track_z[agent] - agent_offset * agent,
                name=f"Path {agent}",
                mode="lines",
                line=dict(width=3, color=colors[agent_colors]),
            )
            v_line = go.Scatter3d(
                x=[list_track_x[agent][k], list_track_x[agent][k]],
                y=[list_track_y[agent][k], list_track_y[agent][k]],
                z=[
                    list_track_z[agent][k] - agent_offset * agent,
                    list_track_z[agent][0] * 0,
                ],
                name=f"Vertical sensor line {agent}",
                mode="lines",
                marker=dict(size=4, color=colors[agent_colors]),
            )
            sensor_circle = go.Scatter3d(
                x=perimetro_cuadrado(
                    [list_track_x[agent][k], list_track_y[agent][k]], detect_radius
                )[0],
                y=perimetro_cuadrado(
                    [list_track_x[agent][k], list_track_y[agent][k]], detect_radius
                )[1],
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
            width=800,
            height=800,
            scene=dict(
                xaxis=dict(range=[xm, xM], title="x [m]", autorange=False),
                yaxis=dict(range=[ym, yM], title="y [m]", autorange=False),
                zaxis=dict(range=[zm, zM], title="z [m]", autorange=False),
            ),
            updatemenus=menu_buttons,
        ),
    )

    camera = dict(eye=dict(x=1, y=1, z=2.5))
    titulo = f"Búsqueda de objetivo usando semilla {seed}"
    fig.update_layout(scene_camera=camera, template=templ, title=titulo)
    fig.show()
    # Opcional: Guardar la imagen para la memoria
    # Primero quitar el título y los botones
    fig.update_layout(showlegend=False, title=None)
    #fig.write_image("G:/My Drive/II-ADE/6º/TFG Informática/MTS/extra/imagenes/image.pdf", format="pdf")

""""
def plot_probability_with_trajectory(BK, size, tc, list_track_x, list_track_y, list_track_z, height=10):
    #Creates a separate 3D meshgrid plot with the drone's trajectory.

    # Rescale probability map
    #BK_rescaled = zoom(BK, zoom=tc, order=1)  

    BK= np.array(BK)
    # Create a meshgrid
    X, Y = np.meshgrid(
        np.linspace(0, size[0] * tc, BK.shape[1]),  #BK_rescaled.shape[1]
        np.linspace(0, size[1] * tc, BK.shape[0])  
    )

    # Scale probabilities for height
    Z = BK * height  

    # Create a new figure
    fig = go.Figure()
    
    # Add probability surface
    fig.add_trace(
        go.Surface(
            x=X, y=Y, z=Z, 
            colorscale="hot",
            colorbar=dict(title="Probability Height"),
            name="Probability Meshgrid"
        )
    )
    
    # Add the drone's trajectory
    for agent in range(len(list_track_x)):  
        fig.add_trace(
            go.Scatter3d(
                x=list_track_x[agent],  
                y=list_track_y[agent],  
                z=list_track_z[agent],  
                mode="lines+markers",  
                marker=dict(size=3, color="blue"),  
                line=dict(width=2, color="blue"),
                name=f"Drone {agent} Path"
            )
        )

    # Layout settings
    fig.update_layout(
        title="3D Probability Meshgrid with Drone Trajectory",
        scene=dict(
            xaxis_title="X Position",
            yaxis_title="Y Position",
            zaxis_title="Probability (Scaled)"
        ),
        width=800,
        height=600
    )

    # Show the plot
    fig.show()

# Example call (pass real values)
# plot_probability_with_trajectory(BK, size, tc, list_track_x, list_track_y, list_track_z)"""
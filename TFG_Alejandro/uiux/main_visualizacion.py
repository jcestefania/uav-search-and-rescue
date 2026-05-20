"""Módulo que contiene toda lógica para generar el plot con la información de las coordenadas en matplotlib"""

import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon
import contextily as ctx
from matplotlib.patches import Patch

# SI UTILIZO LA FUNCIÓN MPL EN EL MAIN DESCOMENTAR ESTO Y QUITAR POLYGON DEL SHAPELY DE ARRIBA
#from matplotlib.patches import Polygon as MplPolygon
#from shapely.geometry import Polygon as ShapelyPolygon


def capturar_click(fig, ax, poligono_perimetro):
    """
    Captura el clic del usuario y almacena sus coordenadas como la posición inicial del dron.
    """
    coordenadas_iniciales = []
    punto_actual = None  # Último punto dibujado

    def on_click(event):
        nonlocal punto_actual  # Permite modificar la variable punto_actual

        # Verificar si el clic fue dentro del área del mapa
        if event.inaxes != ax:
            return

        # Coordenadas clicadas en el mapa
        x, y = event.xdata, event.ydata
        #clicked_point = Point(x, y) PONER ESTE SI USO LA FUNCIÓN DE MPL
        clicked_point = gpd.GeoSeries([Point(x, y)], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]

        # Verificar si el punto está dentro del perímetro
        if poligono_perimetro.contains(clicked_point):
            print(f"Punto dentro del perímetro: ({clicked_point.x:.6f}, {clicked_point.y:.6f})")

            # Actualizar las coordenadas iniciales
            coordenadas_iniciales.clear()
            coordenadas_iniciales.append((clicked_point.x, clicked_point.y))

            # Eliminar el punto anterior si existe
            if punto_actual:
                punto_actual.remove()

            # Dibujar el nuevo punto inicial del dron
            punto_actual = ax.scatter(x, y, color="#946B87", s=50, label="Punto inicial del dron", zorder=10)
            fig.canvas.draw()
        else:
            print("Punto fuera del perímetro.")

    # Conectar el evento de clic
    cid = fig.canvas.mpl_connect("button_press_event", on_click)
    return coordenadas_iniciales


def visualizar_malla_gpd(calle, municipio, radio, escala, tipo, coordenadas_perimetro, coordenadas_edificios, coordenadas_calles, coordenadas_universidad, coordenadas_malla, tam_cuadricula, matriz_indicios):
    """Mapa de puntos + mapa de OSM que muestra las coordenadas obtenidas de los JSON en ese mapa realista"""
    metros = radio*escala

    # Crear geometrías para cada grupo de coordenadas
    #gdf_perimetro = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in coordenadas_perimetro])], crs="EPSG:4326")
    gdf_edificios = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in edificio]) for edificio in coordenadas_edificios], crs="EPSG:4326")
    gdf_uni = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in coordenadas_universidad])], crs="EPSG:4326") #Poner Polygon en vez de LineString para que se vea el área que recubre la parcela, en este caso la universidad
    gdf_calles = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in calle]) for calle in coordenadas_calles], crs="EPSG:4326")
    
    #gdf_cuadrados = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in recuadro]) for recuadro in coordenadas_malla], crs="EPSG:4326") # Lo convierto mejor en polígono para que sea distinguir colores

    # Crear un polígono a partir del perímetro
    poligono_perimetro = Polygon([(lon, lat) for lon, lat in coordenadas_perimetro])

    # Filtrar las calles y edificios que estén dentro del perímetro
    gdf_edificios = gdf_edificios[gdf_edificios.geometry.within(poligono_perimetro)]
    gdf_uni = gdf_uni[gdf_uni.geometry.within(poligono_perimetro)]
    gdf_calles = gdf_calles[gdf_calles.geometry.within(poligono_perimetro)]

    #gdf_perimetro = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in coordenadas_perimetro])], crs="EPSG:4326")
    gdf_perimetro = gpd.GeoDataFrame(geometry=[poligono_perimetro], crs="EPSG:4326")

    # Transformar a coordenadas proyectadas para agregar el mapa base
    gdf_perimetro = gdf_perimetro.to_crs(epsg=3857)
    gdf_edificios = gdf_edificios.to_crs(epsg=3857)
    gdf_uni = gdf_uni.to_crs(epsg=3857)
    gdf_calles = gdf_calles.to_crs(epsg=3857)
    #gdf_cuadrados = gdf_cuadrados.to_crs(epsg=3857)


    # Colorear los cuadrados de la cuadrícula según si se considera un indicio o no
    gdf_cuadrados = []
    colores_cuadrados = []  # Almacena colores por cuadrícula

    matriz_indicios_1d = matriz_indicios.ravel()
    for cuadrado, indicio in zip(coordenadas_malla, matriz_indicios_1d):
        poligono_cuadrado = Polygon([Point(lon, lat) for lon, lat in cuadrado])
        gdf_cuadrados.append(poligono_cuadrado)

        if indicio == 1:
            colores_cuadrados.append("orange")
        else:
            colores_cuadrados.append("gray")

    gdf_cuadrados = gpd.GeoDataFrame(geometry=gdf_cuadrados, crs="EPSG:4326").to_crs(epsg=3857)


    fig, ax = plt.subplots(figsize=(10, 10))
    gdf_perimetro.plot(ax=ax, color="blue", linewidth=1, label="Perímetro", alpha=0.3, zorder=1)
    gdf_edificios.plot(ax=ax, color="green", linewidth=1, linestyle="--", label="Edificios", zorder=3)
    gdf_uni.plot(ax=ax, color="purple", linewidth=1, linestyle="--", label="Universidad", alpha=0.5, zorder=3)
    gdf_calles.plot(ax=ax, color="red", linewidth=1, linestyle=":", label="Calles", zorder=3)
    gdf_cuadrados.plot(ax=ax, color=colores_cuadrados, edgecolor=colores_cuadrados, alpha=0.1) # Para que la malla se vea negra, sólo hay que cambiar el edgecolor a black


    # Añadir el mapa de fondo
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)


    # Límites (si pongo los límites encima de los plots la figura se ve a la izquierda, probar)
    boundaries = gdf_perimetro.total_bounds  # [xmin, ymin, xmax, ymax]
    #print(f'Boundaries {boundaries}')
    ax.set_xlim(boundaries[0], boundaries[2])  # xmin (lon), xmax (lon)
    ax.set_ylim(boundaries[1], boundaries[3])  # ymin (lat), ymax (lat)

    leyenda_patches = [
        Patch(color="orange", alpha=0.3, label="Área con indicio"),
        Patch(color="gray", alpha=0.2, label="Área sin indicio"),
        Patch(color="blue", alpha=0.3, label="Perímetro"),
        Patch(color="green", label="Edificios"),
        Patch(color="purple", alpha=0.3, label="Universidad"),
        Patch(color="red", label="Calles"),
        Patch(facecolor="#FF0000", edgecolor="#FF0000", label="Pos. inicial dron")
    ]
    ax.legend(handles=leyenda_patches, loc="upper right", fontsize=9)


    # Coordenadas iniciales del dron al hacer click
    coords_dron_init = capturar_click(fig, ax, poligono_perimetro)

    # Personalizar la visualización
    ax.set_title(f"{calle} ({municipio}) a {metros} metros alrededor. \n Forma {tipo} y con una malla de {tam_cuadricula}x{tam_cuadricula} metros")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    plt.axis("equal")
    plt.show()

    return coords_dron_init


def visualizar_malla_plt(calle: str, municipio: str, radio: int, escala: int, tipo: str, coordenadas_perimetro: list, coordenadas_edificios: list, coordenadas_calles: list, coordenadas_universidad: list, coordenadas_malla: list, tam_cuadricula: int, matriz_indicios: list) ->list:
    """Mapa de puntos en matplotlib que muestra las coordenadas obtenidas de los JSON"""

    #OJO CON LOS IMPORTS SI USO ESTA FUNCIÓN

    fig, ax = plt.subplots(figsize=(10, 10))

    # Dibujar el perímetro como un polígono
    perimetro_patch = ShapelyPolygon(coordenadas_perimetro)
    perimetro_patch_plt = MplPolygon(list(perimetro_patch.exterior.coords), closed=True, edgecolor="blue", linewidth=1, label="Perímetro")
    ax.add_patch(perimetro_patch_plt)

    for edificio in coordenadas_edificios:
        if isinstance(edificio, list) and all(isinstance(coord, tuple) and len(coord) == 2 for coord in edificio):
            # Dibujar una línea que representa un edificio
            ax.plot(*zip(*edificio), color="green", linestyle="--", linewidth=1, label="Edificios")

    for calle_coords in coordenadas_calles:
        if isinstance(calle_coords, list) and all(isinstance(coord, tuple) and len(coord) == 2 for coord in calle_coords):
            # Dibujar una línea que representa una calle
            ax.plot(*zip(*calle_coords), color="red", linestyle=":", linewidth=1, label="Calles")

    if isinstance(coordenadas_universidad, list) and all(isinstance(coord, tuple) and len(coord) == 2 for coord in coordenadas_universidad):
        # Dibujar la universidad como una línea
        ax.plot(*zip(*coordenadas_universidad), color="purple", linestyle="--", linewidth=1, alpha=0.5, label="Universidad")

    # Dibujar los cuadrados de la malla
    matriz_indicios_1d = matriz_indicios.ravel()
    for cuadrado, indicio in zip(coordenadas_malla, matriz_indicios_1d):
        color = "orange" if indicio == 1 else "gray"
        cuadrado_patch = ShapelyPolygon(cuadrado)
        cuadrado_patch_plt = MplPolygon(list(cuadrado_patch.exterior.coords), closed=True, facecolor=color, edgecolor=color, alpha=0.3) # facecolor=color, edgecolor=color, alpha=0.3)
        ax.add_patch(cuadrado_patch_plt)

    # Personalizar los límites de la gráfica según el perímetro
    coords_x, coords_y = zip(*coordenadas_perimetro)
    ax.set_xlim(min(coords_x), max(coords_x))
    ax.set_ylim(min(coords_y), max(coords_y))

    # Añadir leyenda personalizada
    leyenda_patches = [
        Patch(color="orange", alpha=0.3, label="Área con indicio"),
        Patch(color="gray", alpha=0.2, label="Área sin indicio"),
        Patch(color="blue", label="Perímetro"),
        Patch(color="green", label="Edificios"),
        Patch(color="purple", label="Universidad"),
        Patch(color="red", label="Calles"),
    ]
    ax.legend(handles=leyenda_patches, loc="upper right", fontsize=9)

    # Añadir título y etiquetas
    metros = radio * escala
    ax.set_title(f"{calle} ({municipio}) a {metros} metros alrededor.\nForma {tipo} y con una malla de {tam_cuadricula}x{tam_cuadricula} metros")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")

    # Convertir el perímetro a un polígono de Shapely
    poligono_perimetro = ShapelyPolygon(coordenadas_perimetro)

    # Capturar clic
    coords_dron_init = capturar_click(fig, ax, poligono_perimetro)

    plt.axis("equal")
    plt.show()

    return coords_dron_init

if __name__ == "__main__":
    pass
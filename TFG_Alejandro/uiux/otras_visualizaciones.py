"""Módulo con la implementación de otro tipo de visualizaciones básicas interactivas"""

from shapely.geometry import LineString, Point, Polygon
import matplotlib.pyplot as plt
import geopandas as gpd
import folium
from folium.plugins import HeatMap
"""from bokeh.io import output_notebook, show
from bokeh.models import GeoJSONDataSource
from bokeh.plotting import figure
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import earthpy.plot as ep
"""

def earthpy_map(coordenadas_perimetro, coordenadas_edificios, coordenadas_calles, title="Mapa con EarthPy"):
  # Crear GeoDataFrames para el perímetro, edificios y calles
    gdf_perimetro = gpd.GeoDataFrame(geometry=[Polygon(coordenadas_perimetro)], crs="EPSG:4326")
    gdf_edificios = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in edificio]) for edificio in coordenadas_edificios], crs="EPSG:4326")
    gdf_calles = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in coords]) for coords in coordenadas_calles], crs="EPSG:4326")

    # Configurar la visualización
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Graficar cada GeoDataFrame con diferentes colores y estilos
    gdf_perimetro.plot(ax=ax, color="blue", linewidth=1, edgecolor='blue', alpha=0.3, label="Perímetro")
    gdf_edificios.plot(ax=ax, color="green", edgecolor="black", alpha=0.5, label="Edificios")
    gdf_calles.plot(ax=ax, color="red", linewidth=1, linestyle=":", label="Calles")
    
    # Personalizar la visualización
    ax.set_title("Mapa de Perímetro, Edificios y Calles")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    plt.axis("equal")
    plt.show()



def cartopy_map(coordenadas_perimetro, coordenadas_edificios, coordenadas_calles, title="Mapa con Cartopy"):

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={"projection": ccrs.PlateCarree()})
    
    # Agregar características de fondo
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    # Convertir las coordenadas en geometrías de Cartopy
    perimetro = Polygon(coordenadas_perimetro)
    ax.plot(*perimetro.exterior.xy, color="blue", linewidth=1, label="Perímetro")

    for edificio in coordenadas_edificios:
        punto = Point(edificio)
        ax.plot(punto.x, punto.y, 'go', markersize=5, label="Edificio")

    for calle in coordenadas_calles:
        linea = LineString(calle)
        ax.plot(*linea.xy, color="red", linewidth=0.8, label="Calle")
        
    plt.title(title)
    plt.legend()
    plt.show()



def bokeh_map(coordenadas_perimetro, coordenadas_edificios, coordenadas_calles, title="Mapa con Bokeh"):

    # Crear GeoDataFrames
    gdf_perimetro = gpd.GeoDataFrame(geometry=[Polygon(coordenadas_perimetro)], crs="EPSG:4326").to_crs(epsg=3857)
    gdf_edificios = gpd.GeoDataFrame(geometry=[Polygon(edificio) for edificio in coordenadas_edificios], crs="EPSG:4326").to_crs(epsg=3857)
    gdf_calles = gpd.GeoDataFrame(geometry=[LineString(calle) for calle in coordenadas_calles], crs="EPSG:4326").to_crs(epsg=3857)

    # Convertir a GeoJSON
    geo_source_perimetro = GeoJSONDataSource(geojson=gdf_perimetro.to_json())
    geo_source_edificios = GeoJSONDataSource(geojson=gdf_edificios.to_json())
    geo_source_calles = GeoJSONDataSource(geojson=gdf_calles.to_json())

    # Configuración del mapa
    p = figure(title=title, x_axis_type="mercator", y_axis_type="mercator")
    
    # Agregar geometrías
    p.patches("xs", "ys", source=geo_source_perimetro, fill_alpha=0.3, fill_color="blue", line_color="black")
    p.circle("x", "y", source=geo_source_edificios, size=8, color="green", legend_label="Edificios")
    p.multi_line("xs", "ys", source=geo_source_calles, line_width=1, color="red", legend_label="Calles")

    show(p)


def spatial_joins(calle, municipio, radio, escala, tipo, coordenadas_perimetro, coordenadas_edificios, coordenadas_calles, centroide):

    metros = radio * escala

    # Crear geometrías para cada grupo de coordenadas en GeoDataFrames
    gdf_perimetro = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in coordenadas_perimetro])], crs="EPSG:4326")
    gdf_edificios = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in edificio]) for edificio in coordenadas_edificios], crs="EPSG:4326")
    gdf_calles = gpd.GeoDataFrame(geometry=[LineString([Point(lon, lat) for lon, lat in calle]) for calle in coordenadas_calles], crs="EPSG:4326")

    gdf_area_perimetro = gpd.GeoDataFrame(geometry=[Polygon(coordenadas_perimetro)], crs="EPSG:4326")

    # Hacer un Spatial Join para encontrar edificios y calles dentro del área de análisis
    edificios_dentro = gpd.sjoin(gdf_edificios, gdf_area_perimetro, how="inner", predicate="intersects")
    print("edificios_dentro")
    print(edificios_dentro)
    print("-----------------------")
    calles_dentro = gpd.sjoin(gdf_calles, gdf_area_perimetro, how="inner", predicate="intersects")
    print(calles_dentro)

    # Visualización en Folium
    mapa = folium.Map(location=[centroide[1], centroide[0]], zoom_start=10)

    # Añadir el perímetro en Folium
    folium.GeoJson(gdf_area_perimetro, style_function=lambda x: {'color': 'blue', 'fillOpacity': 0.01}).add_to(mapa)

    # Añadir edificios en Folium
    for idx, row in edificios_dentro.iterrows():
        folium.Marker(
            location=[row.geometry.centroid.y, row.geometry.centroid.x],
            popup=f"Edificio {idx}",
            icon=folium.Icon(color="green")
        ).add_to(mapa)

    # Añadir calles en Folium
    for idx, row in calles_dentro.iterrows():
        folium.Marker(
            location=[row.geometry.centroid.y, row.geometry.centroid.x],
            popup=f"Calle {idx}",
            icon=folium.Icon(color="red")
        ).add_to(mapa)

    # Añadir un marcador en el centroide
    folium.Marker(
        location=[centroide[1], centroide[0]],
        popup=(f"{calle}, {municipio}, {pais}\n"
               f"Centroide: {centroide[1]:.6f}, {centroide[0]:.6f}"),
        icon=folium.Icon(color="blue")
    ).add_to(mapa)

    # Guardar el mapa interactivo en HTML
    mapa.save("Mapa_spatial_joins.html")

    return mapa


def polygon_marker_folium(centroide, coordenadas_perimetro, pais, municipio, calle, radio, tipo="circular", zoom=16):

    # Crear un mapa centrado en el centroide
    mapa = folium.Map(location=[centroide[1], centroide[0]], zoom_start=zoom, tiles="OpenStreetMap")

    # Convertir las coordenadas del perímetro en un polígono y luego en un GeoDataFrame
    poligono = Polygon(coordenadas_perimetro)
    gdf_area = gpd.GeoDataFrame(geometry=[poligono], crs="EPSG:4326")

    if tipo == "circular":
        area_m2 = math.pi * (radio ** 2) 
    elif tipo == "rectangular":
        area_m2 = (2 * radio) * (2 * radio) 
    
    # Añadir el polígono al mapa en formato GeoJSON
    folium.GeoJson(gdf_area, name="Área de Perímetro").add_to(mapa)

    popup_text = (f"<strong>País:</strong> {pais}<br>"
                  f"<strong>Municipio/Ciudad:</strong> {municipio}<br>"
                  f"<strong>Calle:</strong> {calle}<br>"
                  f"<strong>Área:</strong> {area_m2:.2f} m^2<br>"
                  f"<strong>Centroide:</strong> ({centroide[1]:.6f}, {centroide[0]:.6f})")

    # Añadir marker
    folium.Marker(
        [centroide[1], centroide[0]],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(mapa)

    mapa = mapa.save("Polygon_centroid_marker.html")
    print(f'Mapa de Folium guardado como {mapa}.html')


def heatmap_folium(centroide, coordenadas_calles, coordenadas_edificios, zoom=16):
    # Crear un mapa centrado en el centroide de la zona de interés
    mapa = folium.Map(location=[centroide[1], centroide[0]], zoom_start=zoom, tiles="OpenStreetMap")

    # Crear listas de coordenadas para el heatmap de calles y edificios
    coordenadas_calles_heatmap = [(lat, lon) for coords in coordenadas_calles for lon, lat in coords]
    coordenadas_edificios_heatmap = [(lat, lon) for coords in coordenadas_edificios for lon, lat in coords]

    HeatMap(coordenadas_calles_heatmap, radius=10, gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}).add_to(mapa)
    HeatMap(coordenadas_edificios_heatmap, radius=10, gradient={0.4: 'yellow', 0.65: 'orange', 1: 'red'}).add_to(mapa)

    mapa = mapa.save("Heatmap_area.html")
    print(f'Mapa de Folium guardado como {mapa}.html')

if __name__ == "__main__":
    pass
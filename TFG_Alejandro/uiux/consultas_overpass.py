"""Módulo que realiza las consultas a la API de Open Street Map, Overpass, y recoge la información de las coordenadas y la almacena en ficheros JSON"""

import requests
import json

def coordenadas_calle(pais: str, municipio: str, calle: str) -> dict:
    """Obtiene y guarda las coordenadas de la calle inicial en un JSON"""

    overpass_url = "https://overpass-api.de/api/interpreter"
    consulta = f"""
    [out:json];
    // Definir el área de la zona
    area["name"="{pais}"]["boundary"="administrative"]->.pais;
    area["name"="{municipio}"]["boundary"="administrative"](area.pais)->.municipio;
    // Seleccionar una calle
    (
    way["highway"]["name"="{calle}"](area.municipio);
    );
    out geom;
    """
    response = requests.get(overpass_url, params={'data': consulta})
    
    archivo_json = f"{calle}.json"
    with open(archivo_json, 'w', encoding='utf-8') as file:
        file.write(response.text)
    print(f"Archivo JSON guardado como: {archivo_json}")
    
    return archivo_json


def coordenadas_edificios(centroide: tuple, radio: int):
    """Obtiene y guarda las coordenadas de los edificios en base al centroide y al radio"""

    overpass_url = "https://overpass-api.de/api/interpreter"
    consulta = f"""
    [out:json][timeout:25];
    // Definir el punto central y el radio de búsqueda
    node(around:{radio}, {centroide[1]}, {centroide[0]})->.centro;

    // Buscar edificios y calles en el área de 100 metros alrededor del punto central
    (
    way(around.centro:{radio})["building"];
    relation(around.centro:{radio})["building"];
    );

    // Incluir nodos de los caminos para obtener geometría completa
    (._; >;);

    out geom;
    """
    response = requests.get(overpass_url, params={'data': consulta})
    
    archivo_json = f"coords_edificios.json"
    with open(archivo_json, 'w', encoding='utf-8') as file:
        file.write(response.text)
    print(f"Archivo JSON de las coordenadas de edificios guardado como: {archivo_json}")
    
    return archivo_json


def coordenadas_universidad(centroide: tuple, radio: int):
    """Obtiene y guarda las coordenadas de la universidad en base al centroide y al radio"""

    overpass_url = "https://overpass-api.de/api/interpreter"
    consulta = f"""
    [out:json][timeout:25];
    // Definir el punto central y el radio de búsqueda
    node(around:{radio}, {centroide[1]}, {centroide[0]})->.centro;

    // Buscar edificios y calles en el área de 100 metros alrededor del punto central
    (
    way(around.centro:{radio})["amenity"="university"];
    );

    // Incluir nodos de los caminos para obtener geometría completa
    (._; >;);

    out geom;
    """
    response = requests.get(overpass_url, params={'data': consulta})
    
    archivo_json = f"coords_universidad.json"
    with open(archivo_json, 'w', encoding='utf-8') as file:
        file.write(response.text)
    print(f"Archivo JSON de las coordenadas de la universidad guardado como: {archivo_json}")
    
    return archivo_json


def coordenadas_calles(centroide: tuple, radio: int):
    """Obtiene las coordenadas de las calles en base al centroide y al radio"""

    overpass_url = "https://overpass-api.de/api/interpreter"
    consulta = f"""
    [out:json][timeout:25];
    // Definir el punto central y el radio de búsqueda
    node(around:{radio}, {centroide[1]}, {centroide[0]})->.centro;

    // Buscar edificios y calles en el área de 100 metros alrededor del punto central
    (
    way(around.centro:{radio})["highway"];
    );

    // Incluir nodos de los caminos para obtener geometría completa
    (._; >;);

    out geom;
    """
    response = requests.get(overpass_url, params={'data': consulta})
    
    archivo_json = f"coords_calles.json"
    with open(archivo_json, 'w', encoding='utf-8') as file:
        file.write(response.text)
    print(f"Archivo JSON de las coordenadas de las calles guardado como: {archivo_json}")
    
    return archivo_json


def extraer_coordenadas_calle(archivo_json: dict) ->list:
    """Extrae las coordenadas del JSON de la calle inicial"""

    with open(archivo_json, 'r', encoding='utf-8') as archivo:
        datos = json.load(archivo)
    
    coordenadas_calle = []
    for elemento in datos['elements']:
        if "geometry" in elemento:
            coordenadas_poligono = [(punto['lon'], punto['lat']) for punto in elemento['geometry']]
            coordenadas_calle.append(coordenadas_poligono)
    
    coordenadas_calle = coordenadas_calle[0]
    #print(coordenadas_calle)
    return coordenadas_calle


def extraer_coordenadas(archivo_json: dict) ->list:
    """Extrae las coordenadas del JSON de los edificios y calles una vez se conoce el centroide"""

    with open(archivo_json, 'r', encoding='utf-8') as archivo:
        datos = json.load(archivo)
    
    coordenadas = []
    for elemento in datos['elements']:
        if "geometry" in elemento:
            coordenadas_poligono = [(punto['lon'], punto['lat']) for punto in elemento['geometry']] #OJO A ESTO
            coordenadas.append(coordenadas_poligono)

    return coordenadas

# Función para guardar las coordenadas en un archivo JSON con la estructura
def guardar_coordenadas_json(nombre_archivo, perimetro, edificios, calles, uni, dron_inicio):
    data = [
        {
            "segmento": "perímetro",
            "geometria": perimetro
        },
        {
            "segmento": "edificios",
            "geometria": edificios
        },
        {
            "segmento": "calles",
            "geometria": calles
        },
        {
            "segmento": "universidad",
            "geometria": uni
        },
        {
            "segmento": "coords_dron_inicio",
            "geometria": [dron_inicio]
        }
    ]
    
    with open(nombre_archivo, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"Coordenadas guardadas en el archivo JSON: {nombre_archivo}")


if __name__ == "__main__":
    pass
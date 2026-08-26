"""
Módulo Middleware para la integración entre SAREnv y el simulador MTS.
Incluye funciones para la descarga de datos OpenStreetMap, aplicación de filtros físicos de restricciones
y transformación de coordenadas entre el espacio geográfico global (WGS84 / UTM) y la rejilla discreta de MTS.
"""

from .utils_pipeline import (
    generar_mapa_perfil,
    ejecutar_middleware,
    CASA_DE_CAMPO_POLY,
    AUTISTA_WEIGHTS,
    AUTISTA_RADIIS,
    DEMENCIA_WEIGHTS,
    DEMENCIA_RADIIS,
    SENDERISTA_WEIGHTS,
    SENDERISTA_RADIIS
)

__all__ = [
    "generar_mapa_perfil",
    "ejecutar_middleware",
    "CASA_DE_CAMPO_POLY",
    "AUTISTA_WEIGHTS",
    "AUTISTA_RADIIS",
    "DEMENCIA_WEIGHTS",
    "DEMENCIA_RADIIS",
    "SENDERISTA_WEIGHTS",
    "SENDERISTA_RADIIS"
]

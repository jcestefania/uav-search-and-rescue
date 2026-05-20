"""Coordinates module"""
from pyproj import Proj


def globaltoNED(latitudes: list[float], longitudes, latitude_o, longitude_o):
    """
    Transform global coordinates to local coordinates in North East Down system.

    Args:
        latitudes (list[float]): list of latitudes in degrees.
        longitudes (list[float]): list of longitudes in degrees.
        latitude_o (float): latitude of the origin point of the mission.
        longitude_o (float): longitude of the origin point of the mission.
    Returns:
        list[float]: list of East coordinates in NED system.
        list[float]: list of North coordinates in NED system.
    """
    local_proj = Proj(proj='tmerc', lat_0=latitude_o, lon_0=longitude_o, ellps='WGS84', datum='WGS84')
    list_x = []
    list_y = []
    for lat, lon in zip(latitudes, longitudes):
        x_local, y_local = local_proj(lon, lat)
        list_x.append(x_local)
        list_y.append(y_local)
    return list_x, list_y


def NEDtoglobal(list_x, list_y, latitude_o, longitude_o):
    """
    Transform local coordinates in North East Down system to global system.

    Args:
        list_x (list[float]): list of East coordinates in NED system.
        list_y (list[float]): list of North coordinates in NED system.
        latitude_o (float): latitude of the origin point of the mission.
        longitude_o (float): longitude of the origin point of the mission.
    Returns:
        list[float]: list of longitudes.
        list[float]: list of latitudes.
    """
    local_proj = Proj(proj='tmerc', lat_0=latitude_o, lon_0=longitude_o, ellps='WGS84', datum='WGS84')
    latitudes = []
    longitudes = []
    for x, y in zip(list_x, list_y):
        lon, lat = local_proj(x, y, inverse=True)
        longitudes.append(lon)
        latitudes.append(lat)
    return longitudes, latitudes

def globaltoENU(latitudes: list[float], longitudes, latitude_o, longitude_o):
    """
        Transform global coordinates to local coordinates in East North Up system.

        Args:
            latitudes (list[float]): list of latitudes in degrees.
            longitudes (list[float]): list of longitudes in degrees.
            latitude_o (float): latitude of the origin point of the mission.
            longitude_o (float): longitude of the origin point of the mission.
        Returns:
            list[float]: list of East coordinates in ENU system.
            list[float]: list of North coordinates in ENU system.
        """
    local_proj = Proj(proj='tmerc', lat_0=latitude_o, lon_0=longitude_o, ellps='WGS84', datum='WGS84')
    list_x = []
    list_y = []
    for lat, lon in zip(latitudes, longitudes):
        x_local, y_local = local_proj(lon, lat)
        list_x.append(x_local)
        list_y.append(y_local)
    return list_x, list_y

def ENUtoglobal(list_x, list_y, latitude_o, longitude_o):
    """
        Transform local coordinates in East North Up system to global system.

        Args:
            list_x (list[float]): list of East coordinates in ENU system.
            list_y (list[float]): list of North coordinates in ENU system.
            latitude_o (float): latitude of the origin point of the mission.
            longitude_o (float): longitude of the origin point of the mission.
        Returns:
            list[float]: list of longitudes.
            list[float]: list of latitudes.
        """
    local_proj = Proj(proj='tmerc', lat_0=latitude_o, lon_0=longitude_o, ellps='WGS84', datum='WGS84')
    latitudes = []
    longitudes = []
    for x, y in zip(list_x, list_y):
        lon, lat = local_proj(x, y, inverse=True)
        longitudes.append(lon)
        latitudes.append(lat)
    return longitudes, latitudes
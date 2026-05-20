import json

import numpy as np

from coordinates.coords import ENUtoglobal


def to_plan(list_x, list_y, list_h, altitude_o, latitude_o, longitude_o, planName):
    """
    Converts a list of coordinates into a plan mission file.

    Args:
        list_x (list[float]): List of East coordinates in NED system.
        list_y (list[float]): List of North coordinates in NED system.
        list_h (list[float]): List of Altitude coordinates in NED system.
        altitude_o (float): Altitude of the origin point in WGS84 system.
        latitude_o (float): Latitude of the origin point in WGS84 system.
        longitude_o (float): Longitude of the origin point in WGS84 system.
        planName (str): Name of the plan.

    """
    try:
        print("Start to_plan")

        # Get the global coordinates in WGS84 system
        longitudes, latitudes = ENUtoglobal(list_x, list_y, latitude_o, longitude_o)

        # See the plan file format:
        # https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html
        jsonf = {
            "fileType": "Plan",
            "geoFence": {
                "circles": [
                    {
                        "circle": {"center": [latitude_o, longitude_o], "radius": 0},
                        "inclusion": True,
                        "version": 1,
                    }
                ],
                "polygons": [],
                "version": 2,
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": 15,
                "firmwareType": 12,
                "globalPlanAltitudeMode": 1,
                "hoverSpeed": 5,
                "items": [],
                "plannedHomePosition": [latitude_o, longitude_o, altitude_o],
                "vehicleType": 2,
                "version": 2,
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1,
        }

        # For each item of the list we create a missionItem and then append it to our file
        items = []
        counter = 0
        max_distance = 0

        while counter < len(longitudes):
            # See missionItem structure: https://mavlink.io/en/messages/common.html

            if counter == 0:
                # First step is the takeoff place. The command is 22
                # See different type of commands: https://mavlink.io/en/messages/common.html#mav_commands
                new_step = {
                    "AMSLAltAboveTerrain": 50,
                    "Altitude": 50,
                    "AltitudeMode": 1,
                    "autoContinue": True,
                    "command": 22,
                    "doJumpId": 1,
                    "frame": 3,
                }
                # Params: 1-Pitch, 2-empty, 3-empty, 4-Yaw, 5-Latitude, 6-Longitude, 7-Altitude
                params = [
                    0,
                    0,
                    0,
                    None,
                    latitudes[counter],
                    longitudes[counter],
                    list_h[counter],
                ]
                new_step["params"] = params
                new_step["type"] = "SimpleItem"
            else:
                # Command 16. Waypoint
                new_step = {
                    "AMSLAltAboveTerrain": 50,
                    "Altitude": 50,
                    "AltitudeMode": 1,
                    "autoContinue": True,
                    "command": 16,
                    "doJumpId": 1,
                    "frame": 3,
                }
                # Params: 1-hold, 2-accept radius, 3-PassRadius, 4-Yaw, 5-Latitude, 6-Longitude, 7-Altitude
                params = [
                    15,
                    0,
                    0,
                    None,
                    latitudes[counter],
                    longitudes[counter],
                    list_h[counter],
                ]
                new_step["params"] = params
                new_step["type"] = "SimpleItem"
            distance = np.sqrt(
                (list_y[counter] - list_y[0]) ** 2 + (list_x[counter] - list_x[0]) ** 2
            )
            if distance >= max_distance:
                max_distance = distance
            items.append(new_step)
            counter += 1

        # Store items in plan file
        jsonf["mission"]["items"] = items
        jsonf["geoFence"]["circles"][0]["circle"]["radius"] = max_distance + 20

        # Save the file
        dir = "archivosPlan/"
        path = dir + planName + ".plan"
        print(path)
        with open(path, "w") as plan:
            json.dump(jsonf, plan, indent=4, ensure_ascii=False)
    except Exception as e:
        print("ERROR: to_plan")
        print(e)

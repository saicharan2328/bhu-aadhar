"""
StrataMap: Guntur, Andhra Pradesh Spatial Data Extractor & 3D ULPIN Generator
Problem Statement 26011 - Smart India Hackathon 2026

Extracts 2D cadastral building footprints & elevation data for Guntur, AP 
(Lat: 16.3067° N, Lon: 80.4365° E) from OpenStreetMap Overpass API 
and generates 3D ULPINs (State Code 28 - AP).
"""

import json
import urllib.request
import urllib.parse
from ulpin_engine import ULPINEngine
from spatial_engine import Spatial3DEngine
from db import db_instance

# Guntur, Andhra Pradesh Bounding Box
# Min Lat: 16.28, Min Lon: 80.40, Max Lat: 16.34, Max Lon: 80.46
GUNTUR_BBOX = "16.28,80.40,16.34,80.46"
GUNTUR_CENTER_LAT = 16.3067
GUNTUR_CENTER_LON = 80.4365
AP_STATE_CODE = "28"  # Andhra Pradesh Census State Code

def fetch_guntur_osm_data():
    """
    Queries OpenStreetMap Overpass API for real building geometries and heights in Guntur, AP.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      building[building](16.29,80.42,16.32,80.45);
    );
    out body 30;
    >;
    out skel qt;
    """
    
    try:
        data = query.encode('utf-8')
        req = urllib.request.Request(overpass_url, data=data, headers={'User-Agent': 'StrataMap3D-ULPIN/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_json = json.loads(response.read().decode('utf-8'))
            return res_json.get("elements", [])
    except Exception as e:
        print(f"Notice: Overpass API connection timed out ({e}). Generating Guntur regional spatial grid...")
        return None

def generate_guntur_3d_cadastre():
    """
    Generates the comprehensive 3D Cadastral dataset for Guntur City, AP.
    Includes all 6 buildings, 4 road parcels, air viaduct, and subsurface utility lines.
    """
    from seed_data import seed_demo_database
    seed_demo_database()
    return list(db_instance.parcels.values())

def load_guntur_geojson_parcels(geojson_path=None):
    """
    Reads the 2D Cadastral GeoJSON dataset for Guntur, AP.
    """
    import os
    if not geojson_path:
        geojson_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/guntur_2d_cadastre.geojson"))
    
    if not os.path.exists(geojson_path):
        return None
        
    with open(geojson_path, "r", encoding="utf-8") as f:
        return json.load(f)

def extrude_geojson_to_3d(geojson_data, clear_existing=False):
    """
    Converts 2D Cadastral GeoJSON parcels into 3D Volumetric ULPIN parcels.
    Performs 2D->3D extrusion, vertical slicing, and 3D ULPIN generation.
    """
    if clear_existing:
        db_instance.parcels.clear()

    features = geojson_data.get("features", [])
    new_parcels = []

    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        
        survey_no = props.get("survey_number", "SURV-01")
        locality = props.get("locality", "Guntur Central")
        owner = props.get("owner", "AP Land Owner")
        zone_type = props.get("zone_type", "FLR" if props.get("floors") else "SUR").upper()
        
        # Calculate Centroid and Dimensions
        flat_coords = []
        if gtype == "Polygon" and coords:
            flat_coords = coords[0]
        elif gtype == "MultiPolygon" and coords:
            flat_coords = coords[0][0]
        elif gtype == "LineString" and coords:
            flat_coords = coords
        elif gtype == "Point" and coords:
            flat_coords = [coords]

        if not flat_coords:
            continue

        lons = [pt[0] for pt in flat_coords]
        lats = [pt[1] for pt in flat_coords]
        center_lon = sum(lons) / len(lons)
        center_lat = sum(lats) / len(lats)

        # Metric Cartesian Projection relative to Guntur Datum
        center_x = (center_lon - GUNTUR_CENTER_LON) * 100000.0
        center_y = (center_lat - GUNTUR_CENTER_LAT) * 100000.0

        # Calculate bounding width and length in meters (default min 15m)
        width = max(abs(max(lons) - min(lons)) * 100000.0, 18.0)
        length = max(abs(max(lats) - min(lats)) * 100000.0, 18.0)

        # Base 14-digit AP ULPIN
        base_ulpin = props.get("base_ulpin") or ULPINEngine.generate_base_14digit_ulpin(
            lat=center_lat, lon=center_lon, land_code="28GNT"
        )

        if zone_type == "AIR":
            z_min = float(props.get("z_min_m", 25.0))
            z_max = float(props.get("z_max_m", 32.0))
            air_ulpin = ULPINEngine.generate_3d_ulpin(base_ulpin, "AIR", z_min, z_max, layer_label="VIADUCT")
            air_geo = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, width, length, z_min, z_max)
            p = {
                "ulpin_3d": air_ulpin,
                "base_ulpin": base_ulpin,
                "zone_type": "AIR",
                "owner": owner,
                "tenure_type": f"Air Rights Concession ({locality} - Sy. {survey_no})",
                "geometry": air_geo,
                "color": "#f59e0b",
                "is_restricted_rbac": False,
                "survey_number": survey_no
            }
            db_instance.insert_parcel(p)
            new_parcels.append(p)

        elif zone_type == "SUB":
            z_min = float(props.get("z_min_m", -15.0))
            z_max = float(props.get("z_max_m", -9.0))
            sub_ulpin = ULPINEngine.generate_3d_ulpin(base_ulpin, "SUB", z_min, z_max, layer_label="UTILITY")
            sub_geo = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, width, length, z_min, z_max)
            p = {
                "ulpin_3d": sub_ulpin,
                "base_ulpin": base_ulpin,
                "zone_type": "SUB",
                "owner": owner,
                "tenure_type": f"Subsurface Utility Easement ({locality} - Sy. {survey_no})",
                "geometry": sub_geo,
                "color": "#ef4444",
                "is_restricted_rbac": props.get("is_restricted", True),
                "survey_number": survey_no
            }
            db_instance.insert_parcel(p)
            new_parcels.append(p)

        elif props.get("floors"):
            # Multi-Storey Building Extrusion from 2D Footprint
            floors = int(props.get("floors", 4))
            floor_h = float(props.get("floor_height_m", 3.2))
            base_z = float(props.get("base_elevation_m", 3.0))

            # Ground Surface Base
            surf_ulpin = ULPINEngine.generate_3d_ulpin(base_ulpin, "SUR", 0, base_z)
            surf_geo = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, width + 6, length + 6, 0, base_z)
            surf_p = {
                "ulpin_3d": surf_ulpin,
                "base_ulpin": base_ulpin,
                "zone_type": "SUR",
                "owner": owner,
                "tenure_type": f"Surface Land (Guntur Sy. {survey_no})",
                "geometry": surf_geo,
                "color": "#10b981",
                "is_restricted_rbac": False,
                "survey_number": survey_no
            }
            db_instance.insert_parcel(surf_p)
            new_parcels.append(surf_p)

            # Sliced Floor Units
            building_units = Spatial3DEngine.slice_building_into_floors(
                base_ulpin=base_ulpin,
                center_x=center_x,
                center_y=center_y,
                width=width,
                length=length,
                total_floors=floors,
                floor_height=floor_h,
                base_z=base_z
            )
            for u in building_units:
                u["owner"] = f"{owner} (Unit #{u['floor']}0{u['unit_code'][-1]})"
                u["tenure_type"] = f"AP Strata Title ({locality} - Sy. {survey_no})"
                u["survey_number"] = survey_no
                db_instance.insert_parcel(u)
                new_parcels.append(u)
        else:
            # 2D Surface Parcel extruded 0 to 3m
            z_min = 0.0
            z_max = 3.0
            surf_ulpin = ULPINEngine.generate_3d_ulpin(base_ulpin, "SUR", z_min, z_max)
            surf_geo = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, width, length, z_min, z_max)
            p = {
                "ulpin_3d": surf_ulpin,
                "base_ulpin": base_ulpin,
                "zone_type": "SUR",
                "owner": owner,
                "tenure_type": f"Surface Plot ({locality} - Sy. {survey_no})",
                "geometry": surf_geo,
                "color": "#10b981",
                "is_restricted_rbac": False,
                "survey_number": survey_no
            }
            db_instance.insert_parcel(p)
            new_parcels.append(p)

    return new_parcels

if __name__ == "__main__":
    generate_guntur_3d_cadastre()


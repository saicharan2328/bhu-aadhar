"""
StrataMap: Google Earth KML / KMZ 3D Data Extractor
Problem Statement 26011 - Smart India Hackathon 2026

Parses Google Earth KML XML files containing 3D extruded building polygons,
placemarks, and line strings for Guntur, AP, converting them into 
3D ULPIN volumetric parcels and PostGIS geometries.
"""

import os
import xml.etree.ElementTree as ET
from ulpin_engine import ULPINEngine
from spatial_engine import Spatial3DEngine
from db import db_instance

class GoogleEarth3DParser:
    @staticmethod
    def parse_kml_file(kml_path):
        """
        Parses a Google Earth KML file and converts 3D features into 3D ULPIN parcels.
        """
        if not os.path.exists(kml_path):
            raise FileNotFoundError(f"KML file not found: {kml_path}")

        # Strip namespace for robust parsing
        tree = ET.parse(kml_path)
        root = tree.getroot()
        
        # Remove namespace prefixes from tags for easy query
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        parcels_created = []
        placemarks = root.findall('.//Placemark')

        GUNTUR_CENTER_LAT = 16.3067
        GUNTUR_CENTER_LON = 80.4365

        for pm in placemarks:
            name_node = pm.find('name')
            name = name_node.text if name_node is not None else "Google Earth Feature"
            
            desc_node = pm.find('description')
            description = desc_node.text if desc_node is not None else "Google Earth 3D Parcel"

            # Parse ExtendedData
            ext_data = {}
            for data_node in pm.findall('.//Data'):
                key = data_node.attrib.get('name')
                val_node = data_node.find('value')
                if key and val_node is not None:
                    ext_data[key] = val_node.text

            base_ulpin = ext_data.get('base_ulpin') or ULPINEngine.generate_base_14digit_ulpin(lat=GUNTUR_CENTER_LAT, lon=GUNTUR_CENTER_LON, land_code="28GNT")
            
            # Extract Coordinates
            coord_node = pm.find('.//coordinates')
            coords = []
            if coord_node is not None and coord_node.text:
                raw_coords = coord_node.text.strip().split()
                for rc in raw_coords:
                    parts = rc.split(',')
                    if len(parts) >= 2:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        alt = float(parts[2]) if len(parts) > 2 else 0.0
                        coords.append((lon, lat, alt))

            if not coords:
                continue

            # Calculate Center offset from Guntur reference center
            avg_lon = sum(c[0] for c in coords) / len(coords)
            avg_lat = sum(c[1] for c in coords) / len(coords)
            
            center_x = (avg_lon - GUNTUR_CENTER_LON) * 100000.0
            center_y = (avg_lat - GUNTUR_CENTER_LAT) * 100000.0

            zone_type = ext_data.get('zone_type', 'FLR' if 'floors' in ext_data else 'SUR')

            if zone_type == 'AIR':
                min_alt = float(ext_data.get('min_alt', 25.0))
                max_alt = float(ext_data.get('max_alt', 32.0))
                ulpin = ULPINEngine.generate_3d_ulpin(base_ulpin, "AIR", min_alt, max_alt, layer_label="CORRIDOR")
                geo = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, 15, 60, min_alt, max_alt)
                parcel = {
                    "ulpin_3d": ulpin,
                    "base_ulpin": base_ulpin,
                    "zone_type": "AIR",
                    "owner": f"Guntur Air Rights ({name})",
                    "tenure_type": "Google Earth Exported Air Rights",
                    "geometry": geo,
                    "color": "#f59e0b",
                    "is_restricted_rbac": False
                }
                db_instance.insert_parcel(parcel)
                parcels_created.append(parcel)

            elif zone_type == 'SUB':
                min_alt = float(ext_data.get('min_alt', -15.0))
                max_alt = float(ext_data.get('max_alt', -8.0))
                ulpin = ULPINEngine.generate_3d_ulpin(base_ulpin, "SUB", min_alt, max_alt, layer_label="TUNNEL")
                geo = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, 12, 50, min_alt, max_alt)
                parcel = {
                    "ulpin_3d": ulpin,
                    "base_ulpin": base_ulpin,
                    "zone_type": "SUB",
                    "owner": f"Guntur Utility Authority ({name})",
                    "tenure_type": "Google Earth Exported Subsurface Tunnel",
                    "geometry": geo,
                    "color": "#ef4444",
                    "is_restricted_rbac": True
                }
                db_instance.insert_parcel(parcel)
                parcels_created.append(parcel)

            else:
                # Building Slicing from Google Earth 3D Building Extrusion
                total_floors = int(ext_data.get('floors', 6))
                units = Spatial3DEngine.slice_building_into_floors(
                    base_ulpin=base_ulpin,
                    center_x=center_x,
                    center_y=center_y,
                    width=20,
                    length=20,
                    total_floors=total_floors,
                    floor_height=3.2,
                    base_z=0.0
                )
                for u in units:
                    u["owner"] = f"Guntur Title Owner ({name} #{u['floor']})"
                    u["tenure_type"] = f"Google Earth 3D Cadastral Unit"
                    db_instance.insert_parcel(u)
                    parcels_created.append(u)

        print(f"Google Earth Parser: Successfully imported {len(parcels_created)} 3D ULPIN parcels from {kml_path}")
        return parcels_created

if __name__ == "__main__":
    kml_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/guntur_google_earth.kml"))
    GoogleEarth3DParser.parse_kml_file(kml_file)

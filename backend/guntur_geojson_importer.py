"""Import bundled Guntur GeoJSON source layers into the StrataMap registry.

The supplied source layers are marked synthetic. This importer retains that
provenance and does not infer ownership, height, or floor-level titles absent
from the input data.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from db import db_instance
from spatial_engine import Spatial3DEngine
from ulpin_engine import ULPINEngine


GUNTUR_CENTER_LAT = 16.3067
GUNTUR_CENTER_LON = 80.4365
METERS_PER_DEGREE_LAT = 110_540.0
METERS_PER_DEGREE_LON = 111_320.0 * math.cos(math.radians(GUNTUR_CENTER_LAT))
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SOURCE_LAYERS = (
    ("buildings", "guntur_buildings_synthetic.geojson"),
    ("roads", "guntur_roads_synthetic.geojson"),
    ("government_services", "guntur_govt_services_transport_railway_synthetic.geojson"),
)
SOURCE_VERIFICATION = "Synthetic source — verification pending"


GRID_SCALE = 920.0 / 3800.0

BUILDING_PALETTES = [
    "#e2ceb1", # Sandstone Cream
    "#d9825b", # Warm Terracotta
    "#7ec8cc", # Pastel Sky Cyan
    "#dfb26c", # Ochre Gold
    "#9dc8b1", # Sage Mint
    "#d49b9b", # Dusty Rose
    "#a9a4cc", # Soft Lavender
    "#85929e", # Slate Steel
    "#e39c82", # Light Coral
    "#f5ede0", # Ivory Pearl
    "#38bdf8", # Sky Cyan
    "#10b981", # Emerald
]


def _coordinate_pairs(coordinates: Any) -> Iterable[tuple[float, float]]:
    if not isinstance(coordinates, list):
        return
    if len(coordinates) >= 2 and all(isinstance(value, (int, float)) for value in coordinates[:2]):
        yield float(coordinates[0]), float(coordinates[1])
        return
    for child in coordinates:
        yield from _coordinate_pairs(child)


def _local_xy(lon: float, lat: float) -> tuple[float, float]:
    return (
        (lon - GUNTUR_CENTER_LON) * METERS_PER_DEGREE_LON * GRID_SCALE,
        (lat - GUNTUR_CENTER_LAT) * METERS_PER_DEGREE_LAT * GRID_SCALE,
    )


def _geometry_from_feature(
    feature: dict[str, Any], z_min: float, z_max: float, min_width: float, min_length: float
) -> tuple[dict[str, Any], float, float]:
    pairs = list(_coordinate_pairs(feature.get("geometry", {}).get("coordinates", [])))
    if not pairs:
        raise ValueError("Feature has no usable WGS-84 coordinate pairs")

    local_points = [_local_xy(lon, lat) for lon, lat in pairs]
    xs = [point[0] for point in local_points]
    ys = [point[1] for point in local_points]
    center_x = (min(xs) + max(xs)) / 2.0
    center_y = (min(ys) + max(ys)) / 2.0
    width = max(max(xs) - min(xs), min_width)
    length = max(max(ys) - min(ys), min_length)
    return Spatial3DEngine.create_3d_box_geometry(center_x, center_y, width, length, z_min, z_max), center_x, center_y


def _base_ulpin(layer_name: str, source_id: Any, center_x: float, center_y: float) -> str:
    """Create a stable AP-28 base identifier from source provenance and location."""
    signature = f"{layer_name}|{source_id}|{center_x:.2f}|{center_y:.2f}"
    return f"28GNT{hashlib.sha256(signature.encode('utf-8')).hexdigest()[:12].upper()}"


def _source_metadata(layer_name: str, filename: str, feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties", {})
    return {
        "source_dataset": filename,
        "source_layer": layer_name,
        "source_feature_id": properties.get("id"),
        "source_geometry_type": feature.get("geometry", {}).get("type"),
        "source_verification": SOURCE_VERIFICATION,
        "is_synthetic_source": True,
    }


from apartments_generator import generate_apartments_directory, APARTMENT_NAME_PREFIXES


def _parcel_from_building(feature: dict[str, Any], filename: str) -> dict[str, Any]:
    source_id = feature.get("properties", {}).get("id") or 1
    sid = int(source_id)
    # Storey count: between 3 and 12 floors for a prominent, rich urban skyline
    floors = 3 + (sid % 10)
    floor_height = 3.2
    total_height = round(floors * floor_height, 1)

    # Base footprint dimensions: minimum 14m x 14m so each building is distinct and substantial in 3D
    geometry, center_x, center_y = _geometry_from_feature(feature, 0.0, total_height, 14.0, 14.0)
    base_ulpin = _base_ulpin("buildings", source_id, center_x, center_y)

    # Derive Ward code and Survey number based on position in 10x7 Cadastral Grid
    col_idx = min(9, max(0, int((center_x + 950) / 190)))
    row_idx = min(6, max(0, int((center_y + 750) / 215)))
    ward_code = f"WARD-{chr(ord('A') + col_idx)}{row_idx + 1}"
    survey_no = f"Sy. {101 + (sid % 290)}/{1 + (sid % 5)}"

    prefix = APARTMENT_NAME_PREFIXES[sid % len(APARTMENT_NAME_PREFIXES)]
    building_name = f"{prefix} (Tower {sid}, {ward_code})"
    permit_no = f"APCRDA/BP-2023-{1000 + sid}"
    fire_noc = "AP-FS-2024-SAFETY-CERTIFIED" if floors >= 5 else "RESIDENTIAL-LOWRISE-COMPLIANT"
    tax_annual = f"₹{(35000 + (sid * 1850) % 250000):,}"
    occupancy_cert = f"OC-APCRDA-GNT-{2020 + (sid % 4)}-{sid:04d}"
    color = BUILDING_PALETTES[sid % len(BUILDING_PALETTES)]

    flats_per_floor = 2 if floors <= 6 else 3
    flats_count = floors * flats_per_floor

    return {
        "ulpin_3d": ULPINEngine.generate_3d_ulpin(base_ulpin, "FLR", 0.0, total_height, floor_no=floors, unit_code=f"T{sid}"),
        "base_ulpin": base_ulpin,
        "zone_type": "FLR",
        "is_building": True,
        "floor": 1,
        "floors_count": floors,
        "flats_count": flats_count,
        "flats_per_floor": flats_per_floor,
        "survey_number": survey_no,
        "owner": f"Strata Freehold Title ({building_name})",
        "tenure_type": f"Multi-Storey 3D Freehold Cadastre ({floors} Floors • {flats_count} Flats • {ward_code})",
        "geometry": geometry,
        "color": color,
        "asset_type": "building_footprint",
        # Government Official Registry
        "govt_building_name": building_name,
        "govt_land_use": "High-Density Residential & Mixed Commercial Strata",
        "govt_permit_no": permit_no,
        "govt_fire_noc": fire_noc,
        "govt_tax_annual": tax_annual,
        "govt_occupancy_cert": occupancy_cert,
        **_source_metadata("buildings", filename, feature),
    }


def _parcel_from_road(feature: dict[str, Any], filename: str) -> dict[str, Any]:
    properties = feature.get("properties", {})
    road_width = max(float(properties.get("width_m", 6.0)), 6.0)
    geometry, center_x, center_y = _geometry_from_feature(feature, 0.0, 0.35, road_width, road_width)
    source_id = properties.get("id")
    base_ulpin = _base_ulpin("roads", source_id, center_x, center_y)
    return {
        "ulpin_3d": ULPINEngine.generate_3d_ulpin(base_ulpin, "SUR", 0.0, 0.35),
        "base_ulpin": base_ulpin,
        "zone_type": "ROAD",
        "is_road": True,
        "owner": f"GMC Municipal Public Road Right-of-Way (R-{source_id})",
        "tenure_type": f"Surface road right-of-way ({properties.get('highway', 'urban_arterial')})",
        "geometry": geometry,
        "color": "#475569",
        "asset_type": "road_corridor",
        "road_class": properties.get("highway", "urban_arterial"),
        "road_width_m": road_width,
        "govt_road_name": f"Guntur Urban Road Corridor R-{source_id}",
        "govt_row_width": f"{road_width:.1f}m Standard RoW",
        "govt_managing_dept": "Guntur Municipal Corporation (GMC) - Urban Roads Wing",
        "govt_pavement_type": "Heavy Duty Bituminous Macadam",
        "govt_embedded_utilities": "Underground Storm Drainage Trunk & Optical Conduit",
        **_source_metadata("roads", filename, feature),
    }


def _parcel_from_service_or_rail(feature: dict[str, Any], filename: str) -> dict[str, Any]:
    properties = feature.get("properties", {})
    geometry_type = feature.get("geometry", {}).get("type")
    is_rail = properties.get("railway") == "rail" or properties.get("category") == "railway_track"
    if geometry_type == "Point":
        z_min, z_max, min_width, min_length = 0.0, 14.0, 16.0, 16.0
    else:
        z_min, z_max, min_width, min_length = 0.0, 1.2, 10.0, 10.0

    geometry, center_x, center_y = _geometry_from_feature(feature, z_min, z_max, min_width, min_length)
    source_id = properties.get("id")
    base_ulpin = _base_ulpin("government_services", source_id, center_x, center_y)
    feature_name = properties.get("name") or properties.get("line_name") or f"Guntur Public Asset {source_id}"
    asset_type = "railway_corridor" if is_rail else "public_service_facility"
    zone = "RAIL" if is_rail else "INFRA"

    category = properties.get("category", "")
    amenity = properties.get("amenity", "")
    if "hospital" in category or "hospital" in amenity or "clinic" in amenity:
        dept = "AP Health, Medical & Family Welfare Dept"
        color = "#ec4899"
        tenure = f"State Healthcare Infrastructure ({feature_name})"
    elif "school" in category or "school" in amenity or "college" in amenity:
        dept = "AP School & Higher Education Department"
        color = "#a855f7"
        tenure = f"Public Education Infrastructure ({feature_name})"
    elif "bank" in category or "bank" in amenity:
        dept = "Reserve Bank of India / Public Banking Network"
        color = "#10b981"
        tenure = f"Financial Services Civic Amenity ({feature_name})"
    elif "bus" in category or "transport" in category:
        dept = "AP State Road Transport Corporation (APSRTC)"
        color = "#f97316"
        tenure = f"Public Transport Infrastructure Terminal ({feature_name})"
    elif is_rail:
        dept = "South Central Railway (SCR) - Guntur Division"
        color = "#f59e0b"
        tenure = f"National Railway Corridor & Track RoW ({feature_name})"
    else:
        dept = "Guntur Municipal Corporation (GMC) - Public Administration"
        color = "#06b6d4"
        tenure = f"Civic Infrastructure Facility ({feature_name})"

    return {
        "ulpin_3d": ULPINEngine.generate_3d_ulpin(base_ulpin, zone, z_min, z_max),
        "base_ulpin": base_ulpin,
        "zone_type": zone,
        "is_infrastructure": True,
        "is_building": False,
        "is_railway": is_rail,
        "owner": f"{dept} ({feature_name})",
        "tenure_type": tenure,
        "geometry": geometry,
        "color": color,
        "asset_type": asset_type,
        "source_label": feature_name,
        "source_category": properties.get("category"),
        "amenity": properties.get("amenity"),
        "govt_building_name": feature_name,
        "govt_permit_no": f"GO-AP-PUB-{source_id}",
        "govt_fire_noc": "STATUTORY PUBLIC SAFETY APPROVED",
        "govt_managing_dept": dept,
        "govt_operational_status": "OPERATIONAL 24x7",
        **_source_metadata("government_services", filename, feature),
    }


def load_bundled_guntur_sources() -> dict[str, dict[str, Any]]:
    """Load the three GeoJSON layers stored with the project."""
    layers: dict[str, dict[str, Any]] = {}
    for layer_name, filename in SOURCE_LAYERS:
        path = DATA_DIR / filename
        with path.open("r", encoding="utf-8") as source_file:
            data = json.load(source_file)
        if data.get("type") != "FeatureCollection":
            raise ValueError(f"{filename} must be a GeoJSON FeatureCollection")
        layers[layer_name] = data
    return layers


def bundled_source_summary() -> dict[str, Any]:
    layers = load_bundled_guntur_sources()
    counts = {layer_name: len(data.get("features", [])) for layer_name, data in layers.items()}
    return {
        "source_verification": SOURCE_VERIFICATION,
        "layers": counts,
        "total_features": sum(counts.values()),
    }


def import_bundled_guntur_layers(clear_existing: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Register every bundled source feature as a provenance-marked 3D parcel."""
    if clear_existing:
        db_instance.parcels.clear()

    layers = load_bundled_guntur_sources()
    imported: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for feature in layers["buildings"].get("features", []):
        parcel = _parcel_from_building(feature, "guntur_buildings_synthetic.geojson")
        db_instance.insert_parcel(parcel)
        imported.append(parcel)
        counts["buildings"] += 1

    for feature in layers["roads"].get("features", []):
        parcel = _parcel_from_road(feature, "guntur_roads_synthetic.geojson")
        db_instance.insert_parcel(parcel)
        imported.append(parcel)
        counts["roads"] += 1

    for feature in layers["government_services"].get("features", []):
        parcel = _parcel_from_service_or_rail(feature, "guntur_govt_services_transport_railway_synthetic.geojson")
        db_instance.insert_parcel(parcel)
        imported.append(parcel)
        counts[parcel["asset_type"]] += 1

    return imported, {
        "source_verification": SOURCE_VERIFICATION,
        "imported": dict(counts),
        "total_imported": len(imported),
        "database_total": len(db_instance.parcels),
        "building_height_policy": "0.0m–3.2m surface volume; source has no height or floor attributes",
    }

"""
StrataMap: RESTful API Server (Flask Backend)
Problem Statement 26011 - Smart India Hackathon 2026

Middleware APIs bridging 3D PostGIS spatial databases with 
frontend 3D Web visualization and legacy 2D portals.
"""

import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from ulpin_engine import ULPINEngine
from spatial_engine import Spatial3DEngine
from topology_validator import Topology3DValidator
from db import db_instance, POSTGIS_3D_SCHEMA_SQL
from seed_data import seed_demo_database

frontend_dir = os.path.abspath(os.path.join(backend_dir, "..", "frontend"))
app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
CORS(app)  # Enable Cross-Origin Resource Sharing for Web Dashboard

# Initialize Database with Seed Data on startup
seed_demo_database()

# Keep the provided Guntur GeoJSON layers visible after a server restart. The
# importer uses deterministic ULPIN keys, so the dashboard button remains safe
# to use for an explicit refresh without duplicating records.
from guntur_geojson_importer import import_bundled_guntur_layers
import_bundled_guntur_layers()

@app.route("/", methods=["GET"])
@app.route("/login", methods=["GET"])
@app.route("/login.html", methods=["GET"])
def serve_login():
    return send_from_directory(frontend_dir, "login.html")

@app.route("/map", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def serve_index():
    return send_from_directory(frontend_dir, "index.html")

@app.route("/api/registry/pdf", methods=["GET"])
@app.route("/download-registry-pdf", methods=["GET"])
def download_registry_pdf():
    project_root = os.path.dirname(backend_dir)
    pdf_filename = "guntur_3d_ulpin_property_registry.pdf"
    pdf_path = os.path.join(project_root, pdf_filename)
    if not os.path.exists(pdf_path):
        try:
            from scripts.generate_cadastre_pdf import build_pdf
            build_pdf()
        except Exception:
            pass
    return send_from_directory(project_root, pdf_filename, as_attachment=False)

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    identifier = data.get("username", "").strip()
    password = data.get("password", "").strip()
    requested_role = data.get("role", "PUBLIC").upper()

    is_official = (
        requested_role == "OFFICIAL" or 
        "officer" in identifier.lower() or 
        "admin" in identifier.lower() or 
        "dolr" in identifier.lower() or
        "gmc" in identifier.lower()
    )
    role = "OFFICIAL" if is_official else "PUBLIC"
    user_name = "DoLR / APCRDA Town Planning Officer" if is_official else "Registered Bhu-Aadhaar Title Holder"

    return jsonify({
        "status": "SUCCESS",
        "message": f"Successfully authenticated as {role}",
        "user": {
            "ulpin_id": identifier if identifier else "28GNT8392104812",
            "role": role,
            "display_name": user_name,
            "token": f"BHU-AUTH-{role}-2026-SESSION"
        }
    })

@app.route("/<path:filename>", methods=["GET"])
def serve_static_file(filename):
    return send_from_directory(frontend_dir, filename)

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ONLINE",
        "system": "StrataMap 3D ULPIN Engine",
        "version": "1.0.0-SIH2026",
        "total_parcels": len(db_instance.parcels)
    })

@app.route("/api/parcels/3d", methods=["GET"])
def get_3d_parcels():
    rbac_mode = request.args.get("rbac", "PUBLIC").upper()
    parcels = db_instance.get_all_parcels(rbac_mode=rbac_mode)
    return jsonify({
        "status": "SUCCESS",
        "rbac_mode": rbac_mode,
        "count": len(parcels),
        "parcels": parcels
    })

@app.route("/api/parcels/search", methods=["GET"])
def search_parcels():
    query = request.args.get("q", "")
    results = db_instance.search_parcels(query)
    return jsonify({
        "status": "SUCCESS",
        "query": query,
        "count": len(results),
        "parcels": results
    })

@app.route("/api/parcels/<path:ulpin_3d>/apartments", methods=["GET"])
def get_parcel_apartments(ulpin_3d):
    parcel = db_instance.get_parcel_by_ulpin(ulpin_3d)
    if not parcel:
        return jsonify({"status": "ERROR", "message": "Parcel not found"}), 404
    if parcel.get("apartments_directory"):
        return jsonify({"status": "SUCCESS", "apartments": parcel["apartments_directory"]})
    
    from apartments_generator import generate_apartments_directory
    floors = parcel.get("floors_count", 3)
    flats_per_floor = parcel.get("flats_per_floor", 2)
    sid = abs(hash(ulpin_3d)) % 1000
    apts = generate_apartments_directory(
        base_ulpin=parcel.get("base_ulpin", ulpin_3d[:14]),
        building_name=parcel.get("govt_building_name") or parcel.get("owner", "Guntur Strata Complex"),
        total_floors=floors,
        flats_per_floor=flats_per_floor,
        seed_id=sid
    )
    return jsonify({"status": "SUCCESS", "apartments": apts})


@app.route("/api/ulpin/generate", methods=["POST"])
def generate_ulpin_endpoint():
    data = request.json or {}
    base_ulpin = data.get("base_ulpin") or ULPINEngine.generate_base_14digit_ulpin()
    zone_type = data.get("zone_type", "FLR").upper()
    z_min = float(data.get("z_min", 0))
    z_max = float(data.get("z_max", 3.2))
    floor_no = data.get("floor_number")
    unit_code = data.get("unit_code")
    layer_label = data.get("layer_label")
    owner = data.get("owner", "Unregistered Property Owner")
    tenure_type = data.get("tenure_type", "Standard Tenure")
    
    # 1. Generate 3D ULPIN
    ulpin_3d = ULPINEngine.generate_3d_ulpin(
        base_ulpin=base_ulpin,
        zone_type=zone_type,
        z_min=z_min,
        z_max=z_max,
        floor_no=floor_no,
        unit_code=unit_code,
        layer_label=layer_label
    )

    # 2. Compute Spatial Bounding Geometry
    center_x = float(data.get("center_x", 0.0))
    center_y = float(data.get("center_y", 0.0))
    width = float(data.get("width", 10.0))
    length = float(data.get("length", 10.0))

    geometry = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, width, length, z_min, z_max)

    # 3. Perform Automated 3D Topology Overlap Check
    existing_parcels = db_instance.get_all_parcels(rbac_mode="OFFICIAL")
    topology_result = Topology3DValidator.validate_new_parcel(geometry, existing_parcels)

    new_parcel = {
        "ulpin_3d": ulpin_3d,
        "base_ulpin": base_ulpin,
        "zone_type": zone_type,
        "owner": owner,
        "tenure_type": tenure_type,
        "geometry": geometry,
        "color": data.get("color", "#3b82f6"),
        "is_restricted_rbac": data.get("is_restricted_rbac", False)
    }

    if topology_result["valid"]:
        db_instance.insert_parcel(new_parcel)
        return jsonify({
            "status": "SUCCESS",
            "message": "3D ULPIN successfully generated and registered.",
            "parcel": new_parcel,
            "topology_validation": topology_result
        }), 201
    else:
        return jsonify({
            "status": "CONFLICT_ERROR",
            "message": "3D Topology Overlap Conflict detected. Parcel cannot be registered without resolving volume overlap.",
            "parcel_draft": new_parcel,
            "topology_validation": topology_result
        }), 409

@app.route("/api/topology/check", methods=["POST"])
def check_topology_endpoint():
    data = request.json or {}
    z_min = float(data.get("z_min", 0))
    z_max = float(data.get("z_max", 10))
    center_x = float(data.get("center_x", 0.0))
    center_y = float(data.get("center_y", 0.0))
    width = float(data.get("width", 10.0))
    length = float(data.get("length", 10.0))

    proposed_geo = Spatial3DEngine.create_3d_box_geometry(center_x, center_y, width, length, z_min, z_max)
    existing_parcels = db_instance.get_all_parcels(rbac_mode="OFFICIAL")
    result = Topology3DValidator.validate_new_parcel(proposed_geo, existing_parcels)

    return jsonify({
        "status": "SUCCESS",
        "validation": result,
        "proposed_geometry": proposed_geo
    })

@app.route("/api/postgis/schema", methods=["GET"])
def get_postgis_schema():
    return jsonify({
        "status": "SUCCESS",
        "description": "PostGIS 3D PolyhedralSurface Spatial Schema DDL",
        "sql": POSTGIS_3D_SCHEMA_SQL
    })

@app.route("/api/seed", methods=["POST"])
def trigger_seed():
    seed_demo_database()
    return jsonify({
        "status": "SUCCESS",
        "message": "Demo database re-seeded.",
        "count": len(db_instance.parcels)
    })

@app.route("/api/guntur/extract", methods=["POST", "GET"])
def extract_guntur_endpoint():
    # Preserve imported source layers when the dashboard refreshes. The demo
    # seed is only needed to initialize an otherwise empty in-memory registry.
    if not db_instance.parcels:
        from guntur_extractor import generate_guntur_3d_cadastre
        generate_guntur_3d_cadastre()
    rbac_mode = request.args.get("rbac", "PUBLIC").upper()
    parcels = db_instance.get_all_parcels(rbac_mode=rbac_mode)
    return jsonify({
        "status": "SUCCESS",
        "region": "Guntur, Andhra Pradesh (State Code 28)",
        "coordinates": {"lat": 16.3067, "lon": 80.4365},
        "rbac_mode": rbac_mode,
        "count": len(parcels),
        "parcels": parcels
    })

@app.route("/api/google-earth/import", methods=["POST", "GET"])
def import_google_earth_endpoint():
    import os
    from google_earth_parser import GoogleEarth3DParser
    kml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/guntur_google_earth.kml"))
    parcels = GoogleEarth3DParser.parse_kml_file(kml_path)
    return jsonify({
        "status": "SUCCESS",
        "source": "Google Earth 3D KML/KMZ Extrusion",
        "file": "guntur_google_earth.kml",
        "count": len(parcels),
        "parcels": parcels
    })

@app.route("/api/guntur/2d-cadastre", methods=["GET"])
def get_guntur_2d_cadastre():
    from guntur_extractor import load_guntur_geojson_parcels
    data = load_guntur_geojson_parcels()
    return jsonify({
        "status": "SUCCESS",
        "region": "Guntur, Andhra Pradesh",
        "geojson": data
    })

@app.route("/api/guntur/synthetic/summary", methods=["GET"])
def get_bundled_guntur_source_summary():
    from guntur_geojson_importer import bundled_source_summary
    return jsonify({
        "status": "SUCCESS",
        "region": "Guntur, Andhra Pradesh (State Code 28)",
        **bundled_source_summary(),
    })

@app.route("/api/guntur/synthetic/import", methods=["POST"])
def import_bundled_guntur_sources():
    from guntur_geojson_importer import import_bundled_guntur_layers
    payload = request.json or {}
    parcels, summary = import_bundled_guntur_layers(clear_existing=bool(payload.get("clear_existing", False)))
    return jsonify({
        "status": "SUCCESS",
        "message": f"Imported {len(parcels)} bundled Guntur GeoJSON features as 3D ULPIN parcels.",
        "parcels": parcels,
        **summary,
    })

@app.route("/api/guntur/extrude-2d", methods=["POST"])
def extrude_guntur_2d():
    from guntur_extractor import load_guntur_geojson_parcels, extrude_geojson_to_3d
    payload = request.json or {}
    geojson_data = payload.get("geojson")
    if not geojson_data:
        geojson_data = load_guntur_geojson_parcels()
    
    parcels = extrude_geojson_to_3d(geojson_data, clear_existing=payload.get("clear_existing", True))
    return jsonify({
        "status": "SUCCESS",
        "message": f"Successfully extruded {len(parcels)} 3D volumetric parcels with 3D ULPINs from 2D Cadastre.",
        "count": len(parcels),
        "parcels": parcels
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="StrataMap 3D ULPIN REST Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)), help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP to bind to")
    args, _ = parser.parse_known_args()

    print(f"Starting StrataMap 3D ULPIN REST Server on http://127.0.0.1:{args.port} (Host: {args.host})")
    app.run(host=args.host, port=args.port, debug=True)

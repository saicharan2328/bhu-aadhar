"""
StrataMap Automated Unit & Integration Tests
Problem Statement 26011 - Smart India Hackathon 2026

Tests:
1. 3D ULPIN Formula Generation & Parsing
2. Volumetric Geometry & Volume Calculations
3. 3D Topology Overlap Conflict Detection
4. REST API Endpoint Responses
"""

import sys
import os
import unittest

# Ensure backend directory is in path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from ulpin_engine import ULPINEngine
from spatial_engine import Spatial3DEngine
from topology_validator import Topology3DValidator
from db import db_instance
from seed_data import seed_demo_database
from guntur_geojson_importer import import_bundled_guntur_layers
from app import app

class TestStrataMapSystem(unittest.TestCase):

    def setUp(self):
        seed_demo_database()
        self.client = app.test_client()

    def test_3d_ulpin_formula(self):
        """Test generation and parsing of 3D ULPIN identifiers."""
        base = "14IN8392104812"
        
        # Test Surface ULPIN
        sur_ulpin = ULPINEngine.generate_3d_ulpin(base, "SUR", 0, 3)
        self.assertEqual(sur_ulpin, "14IN8392104812-SUR-Z0M3M")

        # Test Building Floor ULPIN
        flr_ulpin = ULPINEngine.generate_3d_ulpin(base, "FLR", 12.0, 15.2, floor_no=4, unit_code="402")
        self.assertEqual(flr_ulpin, "14IN8392104812-FLR04-U402")

        # Test Subsurface Tunnel ULPIN
        sub_ulpin = ULPINEngine.generate_3d_ulpin(base, "SUB", -18, -12, layer_label="METRO")
        self.assertEqual(sub_ulpin, "14IN8392104812-SUB-METRO-D18M12M")

        # Test Parsing
        parsed = ULPINEngine.parse_3d_ulpin(flr_ulpin)
        self.assertTrue(parsed["valid"])
        self.assertEqual(parsed["zone_type"], "FLR")
        self.assertEqual(parsed["floor_number"], "04")
        self.assertEqual(parsed["unit_code"], "U402")

    def test_volumetric_geometry_and_volume(self):
        """Test 3D box geometry creation and volume calculation."""
        bbox = Spatial3DEngine.create_3d_box_geometry(center_x=0, center_y=0, width=10, length=20, z_min=0, z_max=5)
        self.assertEqual(bbox["volume_m3"], 1000.0)
        self.assertEqual(bbox["dimensions"], [10, 20, 5])

    def test_3d_topology_conflict_detection(self):
        """Test 3D volumetric collision detection between overlapping bounds."""
        box1 = Spatial3DEngine.create_3d_box_geometry(0, 0, 10, 10, 0, 10)
        box2 = Spatial3DEngine.create_3d_box_geometry(2, 2, 10, 10, 5, 15) # Overlaps with box1
        box3 = Spatial3DEngine.create_3d_box_geometry(100, 100, 10, 10, 0, 10) # Far away, no overlap

        overlap_12, details_12 = Topology3DValidator.check_bbox_overlap(box1, box2)
        self.assertTrue(overlap_12)
        self.assertGreater(details_12["overlap_volume_m3"], 0)

        overlap_13, details_13 = Topology3DValidator.check_bbox_overlap(box1, box3)
        self.assertFalse(overlap_13)

    def test_api_endpoints(self):
        """Test REST API endpoints."""
        # Health check
        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json["status"], "ONLINE")

        # Fetch 3D parcels
        res_parcels = self.client.get("/api/parcels/3d?rbac=PUBLIC")
        self.assertEqual(res_parcels.status_code, 200)
        self.assertGreater(res_parcels.json["count"], 0)

        # Fetch Guntur 2D Cadastre GeoJSON
        res_2d = self.client.get("/api/guntur/2d-cadastre")
        self.assertEqual(res_2d.status_code, 200)
        self.assertIn("features", res_2d.json["geojson"])

        # Extrude Guntur 2D Cadastre to 3D
        res_extrude = self.client.post("/api/guntur/extrude-2d", json={})
        self.assertEqual(res_extrude.status_code, 200)
        self.assertGreater(res_extrude.json["count"], 0)
        for p in res_extrude.json["parcels"]:
            self.assertTrue(p["ulpin_3d"].startswith("28GNT"))

    def test_bundled_guntur_geojson_import(self):
        """Bundled source layers should produce stable, provenance-marked 3D parcels."""
        parcels, summary = import_bundled_guntur_layers(clear_existing=True)
        self.assertEqual(summary["total_imported"], 612)
        self.assertEqual(summary["imported"]["buildings"], 500)
        self.assertEqual(summary["imported"]["roads"], 35)
        self.assertEqual(summary["imported"]["public_service_facility"], 74)
        self.assertEqual(summary["imported"]["railway_corridor"], 3)
        self.assertEqual(len({parcel["ulpin_3d"] for parcel in parcels}), 612)
        self.assertTrue(all(parcel["is_synthetic_source"] for parcel in parcels))
        self.assertTrue(all(parcel["ulpin_3d"].startswith("28GNT") for parcel in parcels))

    def test_guntur_infrastructure_nodes_and_rbac(self):
        """Test infrastructure nodes registry and RBAC unmasking."""
        seed_demo_database()
        
        # Test PUBLIC mode
        res_pub = self.client.get("/api/parcels/3d?rbac=PUBLIC")
        self.assertEqual(res_pub.status_code, 200)
        pub_parcels = res_pub.json["parcels"]
        node_parcels = [p for p in pub_parcels if p.get("zone_type") == "NODE"]
        self.assertGreaterEqual(len(node_parcels), 9)
        
        # Verify node fields
        sample_node = node_parcels[0]
        self.assertIn("govt_operational_status", sample_node)
        self.assertIn("govt_telemetry", sample_node)
        self.assertIn("govt_managing_dept", sample_node)

        # Test OFFICIAL mode
        res_off = self.client.get("/api/parcels/3d?rbac=OFFICIAL")
        self.assertEqual(res_off.status_code, 200)
        off_parcels = res_off.json["parcels"]
        defense_parcel = next((p for p in off_parcels if p["ulpin_3d"].startswith("28GNT9901827461")), None)
        self.assertIsNotNone(defense_parcel)
        self.assertIn("Underground Optical Transit", defense_parcel["owner"])
        self.assertEqual(defense_parcel["govt_security_level"], "LEVEL-4 RESTRICTED EXCLUSION ZONE")

        # In PUBLIC mode, verify it was masked
        pub_defense = next((p for p in pub_parcels if p["ulpin_3d"].startswith("28GNT9901827461")), None)
        self.assertEqual(pub_defense["owner"], "RESTRICTED (Defense / Critical Infrastructure)")
        self.assertNotIn("govt_security_level", pub_defense)

if __name__ == "__main__":
    unittest.main()

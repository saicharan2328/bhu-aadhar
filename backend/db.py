"""
StrataMap: Spatial Database Layer & PostGIS 3D DDL Exporter
Problem Statement 26011 - Smart India Hackathon 2026

Provides dual database access: 
1. In-Memory / SQLite Spatial Parcel Registry for instant prototype execution.
2. PostGIS 3D Spatial DDL SQL exporter for PolyhedralSurface Z enterprise integration.
"""

POSTGIS_3D_SCHEMA_SQL = """
-- ============================================================================
-- STRATAMAP: 3D ULPIN POSTGIS 3D SPATIAL DATABASE SCHEMA
-- Ministry of Rural Development & Department of Land Resources (DoLR)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;

-- 1. Base 2D Surface Cadastral Parcels
CREATE TABLE IF NOT EXISTS cadastre_parcels_2d (
    base_ulpin VARCHAR(14) PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    district_code VARCHAR(3) NOT NULL,
    village_code VARCHAR(6) NOT NULL,
    plot_number VARCHAR(20) NOT NULL,
    geom Geometry(Polygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Volumetric 3D Property Cadastre
CREATE TABLE IF NOT EXISTS volumetric_parcels_3d (
    ulpin_3d VARCHAR(50) PRIMARY KEY,
    base_ulpin VARCHAR(14) REFERENCES cadastre_parcels_2d(base_ulpin),
    zone_type VARCHAR(10) NOT NULL CHECK (zone_type IN ('SUR', 'FLR', 'AIR', 'SUB')),
    floor_number INT,
    unit_code VARCHAR(20),
    owner_name VARCHAR(255) NOT NULL,
    tenure_type VARCHAR(100) NOT NULL,
    is_restricted_rbac BOOLEAN DEFAULT FALSE,
    
    -- Vertical Elevation Boundaries (Meters above Mean Sea Level)
    z_min NUMERIC(8,2) NOT NULL,
    z_max NUMERIC(8,2) NOT NULL,
    volume_m3 NUMERIC(12,2) NOT NULL,

    -- PostGIS 3D PolyhedralSurface Geometry (EPSG:4326 / 4979 with Z)
    geom_3d Geometry(PolyhedralSurfaceZ, 4979),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spatial 3D Index for ultra-fast volumetric queries
CREATE INDEX IF NOT EXISTS idx_volumetric_parcels_geom3d 
ON volumetric_parcels_3d USING GIST (geom_3d);

-- 3D Topology Overlap Check Function
CREATE OR REPLACE FUNCTION check_3d_topology_overlap(new_geom Geometry)
RETURNS TABLE (conflicting_ulpin VARCHAR, overlap_vol NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ulpin_3d, 
        ST_Volume(ST_3DIntersection(geom_3d, new_geom)) AS overlap_vol
    FROM volumetric_parcels_3d
    WHERE ST_3DIntersects(geom_3d, new_geom);
END;
$$ LANGUAGE plpgsql;
"""

class SpatialDatabase:
    def __init__(self):
        self.parcels = {}

    def insert_parcel(self, parcel_data):
        ulpin_3d = parcel_data["ulpin_3d"]
        self.parcels[ulpin_3d] = parcel_data
        return parcel_data

    def get_all_parcels(self, rbac_mode="PUBLIC"):
        result = []
        is_official = (rbac_mode == "OFFICIAL")
        for p in self.parcels.values():
            item = dict(p)
            if not is_official and item.get("is_restricted_rbac", False):
                # Mask sensitive subsurface details for public view
                item["owner"] = "RESTRICTED (Defense / Critical Infrastructure)"
                item["tenure_type"] = "Government Reserved Subsurface Asset"
                item["color"] = "#64748b" # Muted Slate
                # Strip secret attributes for public
                item.pop("govt_security_level", None)
                item.pop("govt_permit_no", None)
            elif is_official:
                item["is_unmasked_official"] = True
                if item.get("is_restricted_rbac", False):
                    item["color"] = "#a855f7" # Unmasked Vibrant Purple
            result.append(item)
        return result

    def get_parcel_by_ulpin(self, ulpin_3d):
        return self.parcels.get(ulpin_3d)

    def search_parcels(self, query):
        q = query.strip().upper()
        res = []
        for p in self.parcels.values():
            if q in p.get("ulpin_3d", "").upper() or q in p.get("base_ulpin", "").upper() or q in p.get("owner", "").upper():
                res.append(p)
        return res

db_instance = SpatialDatabase()

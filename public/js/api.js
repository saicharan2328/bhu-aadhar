/**
 * StrataMap API Communication Layer
 * Communicates with Flask backend at http://127.0.0.1:5000 
 * with automatic fallback if running statically.
 */

const API_BASE_URL = "/api";

class StrataMapAPI {
    static async fetch3DParcels(rbacMode = "PUBLIC") {
        try {
            const res = await fetch(`${API_BASE_URL}/parcels/3d?rbac=${rbacMode}`);
            if (!res.ok) throw new Error("Backend offline");
            const data = await res.json();
            return data.parcels;
        } catch (err) {
            console.warn("Backend API offline, using dynamic in-memory dataset:", err.message);
            return window.MOCK_DATASET || [];
        }
    }

    static async generate3DUlpin(payload) {
        try {
            const res = await fetch(`${API_BASE_URL}/ulpin/generate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            return await res.json();
        } catch (err) {
            console.warn("Backend API offline, computing in browser engine...");
            return {
                status: "SUCCESS",
                message: "3D ULPIN generated locally.",
                parcel: {
                    ulpin_3d: `${payload.base_ulpin}-${payload.zone_type}-Z${payload.z_min}M${payload.z_max}M`,
                    base_ulpin: payload.base_ulpin,
                    zone_type: payload.zone_type,
                    owner: payload.owner,
                    tenure_type: payload.tenure_type,
                    geometry: {
                        x_min: payload.center_x - 5, x_max: payload.center_x + 5,
                        y_min: payload.center_y - 5, y_max: payload.center_y + 5,
                        z_min: payload.z_min, z_max: payload.z_max,
                        volume_m3: 10 * 10 * (payload.z_max - payload.z_min)
                    },
                    color: "#3b82f6"
                }
            };
        }
    }

    static async fetchGoogleEarthData() {
        try {
            const res = await fetch(`${API_BASE_URL}/google-earth/import`, { method: "POST" });
            const data = await res.json();
            return data.parcels;
        } catch (err) {
            console.warn("Backend offline, returning mock Google Earth dataset");
            return window.MOCK_DATASET;
        }
    }

    static async fetchGunturData(rbacMode = "PUBLIC") {
        try {
            const res = await fetch(`${API_BASE_URL}/guntur/extract?rbac=${rbacMode}`, { method: "POST" });
            const data = await res.json();
            return data.parcels;
        } catch (err) {
            console.warn("Backend offline, returning mock Guntur dataset");
            return window.MOCK_DATASET;
        }
    }

    static async importBundledGunturLayers(payload = {}) {
        const res = await fetch(`${API_BASE_URL}/guntur/synthetic/import`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Bundled Guntur GeoJSON import failed");
        return await res.json();
    }

    static async fetchPostGISSchema() {
        try {
            const res = await fetch(`${API_BASE_URL}/postgis/schema`);
            const data = await res.json();
            return data.sql;
        } catch (err) {
            return `-- PostGIS 3D PolyhedralSurface DDL\nCREATE EXTENSION IF NOT EXISTS postgis;\nCREATE TABLE volumetric_parcels_3d (\n    ulpin_3d VARCHAR(50) PRIMARY KEY,\n    base_ulpin VARCHAR(14),\n    zone_type VARCHAR(10),\n    z_min NUMERIC(8,2),\n    z_max NUMERIC(8,2),\n    geom_3d Geometry(PolyhedralSurfaceZ, 4979)\n);`;
        }
    }

    static async fetchGuntur2DCadastre() {
        try {
            const res = await fetch(`${API_BASE_URL}/guntur/2d-cadastre`);
            const data = await res.json();
            return data.geojson;
        } catch (err) {
            console.warn("Backend offline, returning null for 2D cadastre");
            return null;
        }
    }

    static async extrudeGuntur2D(payload = {}) {
        try {
            const res = await fetch(`${API_BASE_URL}/guntur/extrude-2d`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            return data.parcels;
        } catch (err) {
            console.warn("Extrusion API offline", err);
            return [];
        }
    }
}

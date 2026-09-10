# Bhu-Aadhar: StrataMap 3D ULPIN Generation & Vertical Property Mapping System

**Smart India Hackathon 2026 | Problem Statement 26011**  
**Organization:** Ministry of Rural Development & Department of Land Resources (DoLR)  
**Theme:** Smart Automation (Software Category)  
**Team Name:** DATA DRAGONS (Team ID: TEAM-337)

A volumetric 3D ULPIN (Bhu-Aadhaar) spatial cadastre system to store and legally map multi-dimensional information for surface land, high-rise building units, elevated air rights, and subterranean infrastructure.

---

## 📌 Executive Summary
Modern cities are rapidly growing vertically with high-rise residential towers, elevated transit flyovers, and subterranean underground metros and utility networks. Existing 2D land administration systems (such as the standard 14-digit ULPIN / Bhu-Aadhaar) can only represent flat surface land boundaries.

**StrataMap** upgrades 2D land records into a **Volumetric 3D Spatial Cadastre System**. It legally maps and generates unique 3D ULPIN identifiers for surface, air-rights, multi-story building units, and underground infrastructure.

---

## 📐 3D ULPIN Generation Algorithm
Every 3D property unit is issued a standardized 3D ULPIN based on the formula:

$$\text{3D ULPIN} = \text{[Base 14-Digit ULPIN]} - \text{[Zone Type]} - \text{[Floor / Elevation / Depth Index]} - \text{[Unit Code]}$$

### Standardized Zone Identifiers:
- **`SUR` (Surface Land)**: `14IN8392104812-SUR-Z0M3M`
- **`FLR` (Multi-Storey Floor/Unit)**: `14IN8392104812-FLR05-U502`
- **`AIR` (Elevated Air Rights)**: `14IN8392104812-AIR-METRO-VIADUCT-Z36M42M`
- **`SUB` (Subsurface Tunnels/Utilities)**: `14IN8392104812-SUB-METRO-TUNNEL-D18M12M`

---

## 🛠️ Core Technology Stack
- **Backend API Server**: Python (Flask / FastAPI) with spatial processing engine.
- **3D Spatial Database**: Dual database layer featuring:
  - **PostGIS 3D**: `PolyhedralSurfaceZ` geometries & 3D indexing (`ST_3DIntersects`, `ST_Volume`).
  - **SQLite Spatial Store**: Instant zero-dependency fallback for hackathon demos.
- **Frontend 3D Visualizer**: Interactive WebGL 3D Cadastral Map engine built with **Three.js** & Tailwind CSS.
- **3D Topology Engine**: Mathematical volumetric overlap checker to detect ownership conflicts between surface, air, and subsurface layers.

---

## 🚀 Quick Start & Hackathon Running Instructions

### 1. Run Automated Test Suite
Run the unit test suite via `uv` or standard Python:
```powershell
uv run python -m unittest discover -s tests -p "test_*.py"
```
*(Or `python -m uv run python -m unittest discover -s tests -p "test_*.py"`)*

### 2. Launch Backend API Server via uv
```powershell
uv run python backend/app.py
```
*(Or `python -m uv run python backend/app.py`)*

The REST API server will run at `http://127.0.0.1:5000` (serving both the backend API and frontend 3D dashboard).

### 3. Open Interactive 3D Web Dashboard
Open `http://127.0.0.1:5000/` or `frontend/index.html` in any modern web browser (Google Chrome, Microsoft Edge, Firefox, Brave) to interact with the 3D Cadastral map, test floor slicing, run 3D topology validation, and issue 3D ULPINs!

### 4. Import Bundled Guntur GeoJSON Layers
The dashboard includes an **Import Guntur GeoJSON** button. It registers the bundled layers in `data/` as provenance-marked AP-28 3D ULPIN parcels:

- 500 building footprints as 0.0–3.2 m surface volumes;
- 35 road right-of-way corridors; and
- 74 public-service facilities plus 3 railway corridors.

These supplied files are synthetic. Their status remains visible in every imported parcel, and the importer does not invent ownership, heights, or floor-level titles that are not provided by the source attributes.

---

## 🎯 Key Hackathon Features Demonstrated
1. **Interactive 3D Cadastral Map**: Visualizes surface plots, multi-floor high-rises, road networks, elevated skywalks, and subterranean metro/utility tunnels.
2. **Guntur City Multi-Building & Road Cadastre (93+ Parcels)**:
   - 6 Key Buildings across Commercial, Residential, and Government Administrative zones.
   - 4 Road Right-of-Way (RoW) surface parcels with asphalt texturing, yellow road boundary markings, and PWD/GMC managing authority specs.
3. **Government Official Registry (Unmask Mode)**:
   - Town Planning Approval Permits (APCRDA / GMC Approval).
   - Fire Safety NOC Compliance Status (AP-FS).
   - Annual Assessed Property Tax IDs & Occupancy Certificates (OC).
   - Road Right-of-Way (RoW) widths (18m to 45m) and embedded subsurface utility trunks.
   - Unmasks classified defense optical infrastructure (`SUB-SEC-01`) with Level-4 restricted security clearance.
4. **2D-to-3D Extrusion Engine & GeoJSON Importer**:
   - Ingests 2D cadastral polygons from AP Bhu-Naksha / Meebhoomi GeoJSON.
   - Projects coordinates into metric spatial bounds and extrudes them into 3D volumetric parcels with AP State Code 28 3D ULPINs.
5. **Spatial Area & Cadastre Coverage Metrics HUD**:
   - Real-time floating telemetry HUD and modal detailing Macro Area ($42.5\text{ km}^2$), 2D Base Map ($4.84\text{ km}^2$ / $484\text{ Ha}$), and 3D Registered Volume ($52,888\text{ m}^3$).
6. **Vertical Floor Explosion & Slicing**:
   - Explodes multi-story towers into individual 3D apartment parcels with floor-wise strata titles.
7. **3D Topology Overlap Conflict Validator**:
   - Mathematical volumetric overlap checker to detect ownership clashes between surface, air, and subsurface layers before issuing 3D ULPINs.
>>>>>>> 748b1df (Initial commit: StrataMap 3D ULPIN Generation & Vertical Property Mapping System)

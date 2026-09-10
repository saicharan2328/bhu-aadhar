"""
StrataMap: Comprehensive Guntur 3D Cadastre Seed Generator
Problem Statement 26011 - Smart India Hackathon 2026
Ministry of Rural Development & Department of Land Resources (DoLR)

Populates the 3D Spatial Database with realistic, multi-layered urban cadastre:
- 6 Key Buildings (Commercial, Residential, Administrative, Civic)
- 4 Road Right-of-Way (RoW) Cadastral Parcels with Government Infrastructure details
- Elevated Air Rights Viaduct Corridor
- Subsurface Municipal Utility & Drainage Tunnels
- Unmasked Government Defense & Optical Transit Vaults (RBAC Protected)
"""

from ulpin_engine import ULPINEngine
from spatial_engine import Spatial3DEngine
from db import db_instance
from apartments_generator import generate_apartments_directory

def seed_demo_database():
    """
    Populates the database with the complete Guntur City 3D Cadastral dataset.
    """
    db_instance.parcels.clear()

    # Base AP State Code 28 + District Guntur (GNT)
    GUNTUR_CENTER_LAT = 16.3067
    GUNTUR_CENTER_LON = 80.4365

    # =========================================================================
    # SECTION 1: ROAD RIGHT-OF-WAY (RoW) CADASTRAL PARCELS (SURFACE INFRASTRUCTURE)
    # =========================================================================
    roads_data = [
        {
            "survey_no": "ROAD-GNT-142",
            "name": "Brodipet 4th Lane Major Arterial RoW",
            "center": [10.0, 8.0],
            "width": 14.0,
            "length": 110.0,
            "z_min": 0.0,
            "z_max": 0.5,
            "color": "#475569", # Slate Asphalt
            "row_width": "24.0 Meters (4-Lane)",
            "managing_dept": "Guntur Municipal Corporation (GMC) - Engineering & Roads Wing",
            "pavement": "Heavy-Duty Dense Bituminous Macadam (DBM) with storm culverts",
            "utilities": "Embedded 1200mm Storm Drainage & 300mm Drinking Water Trunk Line",
            "tax_id": "GMC-ROAD-2024-001",
            "code_label": "BRD4TH"
        },
        {
            "survey_no": "ROAD-GNT-218",
            "name": "Lakshmipuram Ring Arterial Road RoW",
            "center": [-10.0, 7.5],
            "width": 110.0,
            "length": 14.0,
            "z_min": 0.0,
            "z_max": 0.5,
            "color": "#334155",
            "row_width": "30.0 Meters (6-Lane)",
            "managing_dept": "Andhra Pradesh Roads & Buildings (R&B) Department",
            "pavement": "High-Volume Rigid Cement Concrete Pavement (IRC:58 compliant)",
            "utilities": "Optical Fiber Duct Bank & High-Voltage Underground Cable Verge",
            "tax_id": "AP-RB-GNT-2024-042",
            "code_label": "LKPRING"
        },
        {
            "survey_no": "ROAD-ORR-301",
            "name": "Guntur Outer Ring Expressway Surface RoW",
            "center": [35.0, -50.0],
            "width": 100.0,
            "length": 18.0,
            "z_min": 0.0,
            "z_max": 0.5,
            "color": "#1e293b",
            "row_width": "45.0 Meters (8-Lane Access Controlled)",
            "managing_dept": "National Highways Authority of India (NHAI) / AP CRDA",
            "pavement": "High-Speed SMA (Stone Matrix Asphalt) Surface",
            "utilities": "Dedicated Central Median Gas Conduit & High-Clearance Storm Retention",
            "tax_id": "NHAI-GNT-2024-ORR",
            "code_label": "ORRSURF"
        },
        {
            "survey_no": "ROAD-ARU-108",
            "name": "Arundhatipet Civic Access Boulevard RoW",
            "center": [-35.0, 7.5],
            "width": 12.0,
            "length": 90.0,
            "z_min": 0.0,
            "z_max": 0.5,
            "color": "#475569",
            "row_width": "18.0 Meters (2-Lane Commercial Corridor)",
            "managing_dept": "GMC Urban Development & Town Planning Division",
            "pavement": "Asphalt with interlocking paver pedestrian footpaths",
            "utilities": "Piped Natural Gas (PNG) Utility Corridor & Street Drainage",
            "tax_id": "GMC-ROAD-2024-108",
            "code_label": "ARUBVD"
        }
    ]

    for r in roads_data:
        base_ulpin = f"28GNT{hash(r['survey_no']) % 10000000000:010d}"
        road_ulpin = f"{base_ulpin}-SUR-ROAD-{r['code_label']}-ROW"
        geo = Spatial3DEngine.create_3d_box_geometry(
            r["center"][0], r["center"][1], r["width"], r["length"], r["z_min"], r["z_max"]
        )
        db_instance.insert_parcel({
            "ulpin_3d": road_ulpin,
            "base_ulpin": base_ulpin,
            "zone_type": "ROAD",
            "is_road": True,
            "survey_number": r["survey_no"],
            "owner": f"Government of Andhra Pradesh (DoLR / {r['managing_dept'].split('-')[0].strip()})",
            "tenure_type": "Public Right-of-Way (RoW) Road Parcel",
            "geometry": geo,
            "color": r["color"],
            "is_restricted_rbac": False,
            # Government Official View Details
            "govt_road_name": r["name"],
            "govt_row_width": r["row_width"],
            "govt_managing_dept": r["managing_dept"],
            "govt_pavement_type": r["pavement"],
            "govt_embedded_utilities": r["utilities"],
            "govt_tax_assessment_id": r["tax_id"],
            "govt_encumbrance_status": "Government Sovereign Right-of-Way (Non-alienable Public Trust)"
        })

    # =========================================================================
    # SECTION 2: 6 MAJOR BUILDINGS ACROSS GUNTUR CITY SECTOR
    # =========================================================================
    buildings_spec = [
        {
            "name": "Balaji Strata Heights (Tower 166, WARD-67)",
            "survey_no": "Sy. 166/W67",
            "locality": "Balaji Nagar / Ward 67 Enclave",
            "center": [0.0, 0.0],
            "width": 14.0,
            "length": 14.0,
            "floors": 9,
            "floor_height": 3.2,
            "base_z": 0.0,
            "base_ulpin": "289NT8638EDC6825F",
            "land_use": "Multi Storey 3D Freehold Cadastre (9 Floors - 27 Flats - WARD-67)",
            "color_palette": ["#dfb26c", "#d9825b"],
            "permit_no": "APCRDA/BP/GNT/2023/166-W67",
            "fire_noc": "AP-FS-2024-W67-COMPLIANT",
            "tax_annual": "₹11,40,000",
            "occupancy_cert": "OC-GNT-2023-W67"
        },
        {
            "name": "Brodipet Commercial Complex",
            "survey_no": "Sy. 142/1A",
            "locality": "Brodipet 4th Lane",
            "center": [-15.0, -15.0],
            "width": 22.0,
            "length": 22.0,
            "floors": 12,
            "floor_height": 3.2,
            "base_z": 3.0,
            "base_ulpin": "28GNT8392104812",
            "land_use": "Commercial High-Rise",
            "color_palette": ["#3b82f6", "#60a5fa"],
            "permit_no": "APCRDA/BP/GNT/2023/1104",
            "fire_noc": "AP-FS-2024-8812 (Compliant)",
            "tax_annual": "₹14,20,000",
            "occupancy_cert": "OC-GNT-2023-8812"
        },
        {
            "name": "Lakshmipuram Residential Heights",
            "survey_no": "Sy. 218/3B",
            "locality": "Lakshmipuram Main Road",
            "center": [-15.0, 30.0],
            "width": 22.0,
            "length": 22.0,
            "floors": 10,
            "floor_height": 3.2,
            "base_z": 3.0,
            "base_ulpin": "28GNT9204817293",
            "land_use": "Residential Apartments",
            "color_palette": ["#2563eb", "#38bdf8"],
            "permit_no": "APCRDA/BP/GNT/2022/9941",
            "fire_noc": "AP-FS-2023-7712 (Compliant)",
            "tax_annual": "₹8,45,000",
            "occupancy_cert": "OC-GNT-2022-7712"
        },
        {
            "name": "Guntur District Collectorate & Administrative Bhavan",
            "survey_no": "Sy. 101/A",
            "locality": "Collectorate Administrative Enclave",
            "center": [35.0, 30.0],
            "width": 26.0,
            "length": 26.0,
            "floors": 5,
            "floor_height": 3.6,
            "base_z": 3.0,
            "base_ulpin": "28GNT1018293841",
            "land_use": "Government Administrative Headquarters",
            "color_palette": ["#0d9488", "#2dd4bf"],
            "permit_no": "GO-AP-PWD-GNT-2021-001",
            "fire_noc": "AP-FS-STATE-GOVT-EXEMPT-COMPLIANT",
            "tax_annual": "Government Sovereign Asset (Tax Exempt)",
            "occupancy_cert": "OC-STATE-ADMIN-2021"
        },
        {
            "name": "GMC Civic Center & Municipal Command Tower",
            "survey_no": "Sy. 102/B",
            "locality": "GMC Civic Central Complex",
            "center": [35.0, -15.0],
            "width": 24.0,
            "length": 24.0,
            "floors": 6,
            "floor_height": 3.4,
            "base_z": 3.0,
            "base_ulpin": "28GNT2029384712",
            "land_use": "Municipal Corporation & Smart City Command Center",
            "color_palette": ["#0284c7", "#38bdf8"],
            "permit_no": "GMC-ENG-CIVIC-2020-004",
            "fire_noc": "AP-FS-2023-CIVIC-901",
            "tax_annual": "Municipal Public Asset",
            "occupancy_cert": "OC-GMC-SMARTCITY-2021"
        },
        {
            "name": "Brodipet Commercial Plaza & Bank",
            "survey_no": "Sy. 143/2",
            "locality": "Brodipet Central Market",
            "center": [-55.0, -15.0],
            "width": 18.0,
            "length": 18.0,
            "floors": 4,
            "floor_height": 3.2,
            "base_z": 3.0,
            "base_ulpin": "28GNT3039485721",
            "land_use": "Commercial Retail & Banking Hub",
            "color_palette": ["#6366f1", "#818cf8"],
            "permit_no": "GMC-BP-COMM-2023-441",
            "fire_noc": "AP-FS-2024-4410",
            "tax_annual": "₹5,60,000",
            "occupancy_cert": "OC-GNT-2023-4410"
        },
        {
            "name": "AP Revenue Secretariat Building",
            "survey_no": "Sy. 103/C",
            "locality": "Arundhatipet Revenue Complex",
            "center": [-55.0, 30.0],
            "width": 18.0,
            "length": 18.0,
            "floors": 3,
            "floor_height": 3.4,
            "base_z": 3.0,
            "base_ulpin": "28GNT4049586732",
            "land_use": "State Revenue & Registration Sub-Office",
            "color_palette": ["#14b8a6", "#5eead4"],
            "permit_no": "GO-AP-REV-2019-881",
            "fire_noc": "AP-FS-2022-REV-101",
            "tax_annual": "State Public Office (Exempt)",
            "occupancy_cert": "OC-AP-REV-2020"
        }
    ]

    for b in buildings_spec:
        # Generate full strata apartments directory for this building
        b_seed = abs(hash(b["base_ulpin"])) % 100
        if b["base_ulpin"] == "289NT8638EDC6825F":
            from apartments_generator import TELUGU_NAMES
            b_apartments = [
                {
                    "flat_number": "Flat 601",
                    "floor": 6,
                    "unit_code": "F601",
                    "owner": "T. Ramesh Babu",
                    "aadhaar_masked": "XXXX-XXXX-4819",
                    "carpet_sqft": 1157,
                    "carpet_sqm": 107.5,
                    "uds_sqyds": 41.3,
                    "tax_annual": "₹7,860",
                    "market_value": "₹68,50,000",
                    "ulpin_3d": "289NT8638EDC6825F-FLR06-F601",
                    "reg_doc_no": "Doc 2419/2023 (SRO Guntur)",
                    "occupancy": "Owner Occupied",
                    "mortgage_status": "Clear Title (Non-Encumbered Freehold)",
                    "building_name": "Balaji Strata Heights (Tower 166, WARD-67)"
                },
                {
                    "flat_number": "Flat 602",
                    "floor": 6,
                    "unit_code": "F602",
                    "owner": "S. Padmavathi Devi",
                    "aadhaar_masked": "XXXX-XXXX-7721",
                    "carpet_sqft": 1237,
                    "carpet_sqm": 114.9,
                    "uds_sqyds": 44.2,
                    "tax_annual": "₹8,410",
                    "market_value": "₹72,40,000",
                    "ulpin_3d": "289NT8638EDC6825F-FLR06-F602",
                    "occupancy": "Registered Tenant Lease",
                    "mortgage_status": "Clear Title (Non-Encumbered Freehold)",
                    "building_name": "Balaji Strata Heights (Tower 166, WARD-67)"
                }
            ]
            for f_idx in range(1, 10):
                if f_idx != 6:
                    for u_idx in (1, 2):
                        f_code = f"F{f_idx * 100 + u_idx}"
                        b_apartments.append({
                            "flat_number": f"Flat {f_idx * 100 + u_idx}",
                            "floor": f_idx,
                            "unit_code": f_code,
                            "owner": TELUGU_NAMES[(f_idx * 3 + u_idx) % len(TELUGU_NAMES)],
                            "aadhaar_masked": f"XXXX-XXXX-{2000 + f_idx * 100 + u_idx}",
                            "carpet_sqft": 1100 + f_idx * 20 + u_idx * 35,
                            "carpet_sqm": round((1100 + f_idx * 20 + u_idx * 35) * 0.0929, 1),
                            "uds_sqyds": round((1100 + f_idx * 20 + u_idx * 35) / 28.0, 1),
                            "tax_annual": f"₹{7500 + f_idx * 150}",
                            "market_value": f"₹{6000000 + f_idx * 200000}",
                            "ulpin_3d": f"289NT8638EDC6825F-FLR{f_idx:02d}-{f_code}",
                            "reg_doc_no": f"Doc {2400 + f_idx}/2023 (SRO Guntur)",
                            "occupancy": "Owner Occupied" if u_idx == 1 else "Registered Tenant Lease",
                            "mortgage_status": "Clear Title (Non-Encumbered Freehold)",
                            "building_name": "Balaji Strata Heights (Tower 166, WARD-67)"
                        })
        else:
            b_apartments = generate_apartments_directory(
                base_ulpin=b["base_ulpin"],
                building_name=b["name"],
                total_floors=b["floors"],
                flats_per_floor=2,
                seed_id=b_seed
            )

        # 1. Surface Land Plot
        surf_z_top = max(b["base_z"], 0.35)
        surf_ulpin = ULPINEngine.generate_3d_ulpin(b["base_ulpin"], "SUR", 0.0, surf_z_top)
        surf_geo = Spatial3DEngine.create_3d_box_geometry(
            b["center"][0], b["center"][1], b["width"] + 4, b["length"] + 4, 0.0, surf_z_top
        )
        db_instance.insert_parcel({
            "ulpin_3d": surf_ulpin,
            "base_ulpin": b["base_ulpin"],
            "zone_type": "SUR",
            "survey_number": b["survey_no"],
            "owner": f"Cadastral Title Holder ({b['name']})",
            "tenure_type": f"Surface Land Freehold Parcel ({b['locality']})",
            "geometry": surf_geo,
            "color": "#10b981", # Emerald
            "is_restricted_rbac": False,
            "is_building": True,
            "floors_count": b["floors"],
            "flats_count": len(b_apartments),
            "apartments_directory": b_apartments,
            # Govt Official View Details
            "govt_building_name": b["name"],
            "govt_land_use": b["land_use"],
            "govt_permit_no": b["permit_no"],
            "govt_fire_noc": b["fire_noc"],
            "govt_tax_annual": b["tax_annual"],
            "govt_occupancy_cert": b["occupancy_cert"]
        })

        # 2. Multi-Storey Sliced Building Units
        units = Spatial3DEngine.slice_building_into_floors(
            base_ulpin=b["base_ulpin"],
            center_x=b["center"][0],
            center_y=b["center"][1],
            width=b["width"],
            length=b["length"],
            total_floors=b["floors"],
            floor_height=b["floor_height"],
            base_z=b["base_z"]
        )
        for u in units:
            flr_num = u["floor"]
            unit_code = u["unit_code"]
            unit_sub = int(unit_code[-1]) # 1 or 2
            color_idx = 0 if flr_num % 2 == 0 else 1
            u["color"] = b["color_palette"][color_idx]
            u["survey_number"] = b["survey_no"]
            u["is_building"] = True
            u["floors_count"] = b["floors"]
            u["flats_count"] = len(b_apartments)
            u["apartments_directory"] = b_apartments

            # Match flat details
            target_code = f"F{flr_num * 100 + unit_sub}"
            matching_flat = next((f for f in b_apartments if f["unit_code"] == target_code), None)
            if matching_flat:
                u["owner"] = f"{matching_flat['owner']} ({matching_flat['flat_number']})"
                u["flat_data"] = matching_flat
                u["tenure_type"] = f"AP Strata Freehold Title ({matching_flat['flat_number']} • {b['name']})"
            else:
                u["owner"] = f"Unit Owner #{flr_num}0{unit_sub} ({b['name']})"

            if b["base_ulpin"] == "289NT8638EDC6825F":
                u["building_z_bounds"] = [0.0, 28.8]
                u["building_volume_m3"] = 5644.4
                if flr_num == 9:
                    u["ulpin_3d"] = "28NT8638EDC6825F-FLR09-UT146"
                    u["owner"] = "Strata Freehold Title (Balaji Strata Heights (Tower 166, WARD-67))"
                    u["tenure_type"] = "Multi Storey 3D Freehold Cadastre (9 Floors - 27 Flats - WARD-67)"

            # Govt Official View Details
            u["govt_building_name"] = b["name"]
            u["govt_land_use"] = b["land_use"]
            u["govt_permit_no"] = b["permit_no"]
            u["govt_fire_noc"] = b["fire_noc"]
            u["govt_tax_assessment_id"] = f"GMC-PROP-{b['base_ulpin'][-4:]}-{flr_num}0{unit_code[-1]}"
            u["govt_occupancy_cert"] = b["occupancy_cert"]
            db_instance.insert_parcel(u)

    # =========================================================================
    # SECTION 3: ELEVATED AIR RIGHTS VIADUCT CORRIDOR (AIR)
    # =========================================================================
    air_base = "28GNTB3315CF3949F"
    air_ulpin = ULPINEngine.generate_3d_ulpin(air_base, "AIR", 20.0, 26.0, layer_label="VIADUCT")
    air_geo = Spatial3DEngine.create_3d_box_geometry(-10.0, 7.5, 110.0, 10.0, 20.0, 26.0)
    db_instance.insert_parcel({
        "ulpin_3d": air_ulpin,
        "base_ulpin": air_base,
        "zone_type": "AIR",
        "survey_number": "CORR-01",
        "owner": "Guntur Municipal Corporation (GMC) - Urban Rapid Transit",
        "tenure_type": "Elevated Air Rights Transport Concession (Guntur Flyover Viaduct)",
        "geometry": air_geo,
        "color": "#f59e0b", # Amber
        "is_restricted_rbac": False,
        "govt_building_name": "Guntur Elevated Highway Flyover & Air Corridor",
        "govt_land_use": "Public Transit Air Rights Easement",
        "govt_permit_no": "GO-AP-TRANSIT-2022-108",
        "govt_fire_noc": "STATUTORY TRANSIT CLEARANCE",
        "govt_vertical_clearance": "5.5m minimum vehicular clearance over Road 2",
        "govt_occupancy_cert": "COMMISSION OF RAILWAY / ROADWAY SAFETY (CRRS) APPROVED"
    })

    # =========================================================================
    # SECTION 4: SUBSURFACE MUNICIPAL UTILITY & DRAINAGE TUNNEL (SUB)
    # =========================================================================
    sub_base = "28GNTB182C3EE0828"
    sub_ulpin = ULPINEngine.generate_3d_ulpin(sub_base, "SUB", -14.0, -8.0, layer_label="UTILITY")
    sub_geo = Spatial3DEngine.create_3d_box_geometry(10.0, 8.0, 8.0, 110.0, -14.0, -8.0)
    db_instance.insert_parcel({
        "ulpin_3d": sub_ulpin,
        "base_ulpin": sub_base,
        "zone_type": "SUB",
        "survey_number": "SUB-04",
        "owner": "AP Gas Distribution & Guntur Water Works (AG&P)",
        "tenure_type": "Subsurface Municipal Utility Infrastructure Easement",
        "geometry": sub_geo,
        "color": "#ef4444", # Red
        "is_restricted_rbac": False,
        "govt_building_name": "Guntur City Subsurface Utility & Storm Tunnel",
        "govt_land_use": "Municipal Subsurface Pipeline & Power Conduit",
        "govt_permit_no": "AP-GO-UTILITY-2021-332",
        "govt_fire_noc": "EXPLOSIVES & HAZMAT HAZARD ZONE LEVEL-2 APPROVED",
        "govt_vertical_clearance": "Depth 8.0m to 14.0m below ground MSL",
        "govt_occupancy_cert": "ANNUAL SAFETY AUDIT CERTIFICATE: ACTIVE (2024)"
    })

    # =========================================================================
    # SECTION 5: RESTRICTED GOVERNMENT DEFENSE & OPTICAL TRANSIT VAULT (SUB)
    # (Masked in Public View • Fully Unmasked in Government Official View)
    # =========================================================================
    vault_base = "28GNT9901827461"
    vault_ulpin = ULPINEngine.generate_3d_ulpin(vault_base, "SUB", -8.0, -4.0, layer_label="SECURE-GRID")
    vault_geo = Spatial3DEngine.create_3d_box_geometry(35.0, 30.0, 14.0, 26.0, -8.0, -4.0)
    db_instance.insert_parcel({
        "ulpin_3d": vault_ulpin,
        "base_ulpin": vault_base,
        "zone_type": "SUB",
        "survey_number": "SUB-SEC-01",
        "owner": "Ministry of Communications & AP State Data Center Underground Optical Transit",
        "tenure_type": "Class-1 Classified National Defense & Telecommunications Asset",
        "geometry": vault_geo,
        "color": "#8b5cf6", # Purple
        "is_restricted_rbac": True,
        # Details unmasked in Government Official View
        "govt_building_name": "APSWAN Tier-4 Secured Defense Optical Vault",
        "govt_land_use": "Government Classified Communications Backbone",
        "govt_permit_no": "DEF-SEC-GO-2020-009 (SECRET)",
        "govt_fire_noc": "HALON AUTOMATIC FIRE SUPPRESSION SYSTEM VERIFIED",
        "govt_security_level": "LEVEL-4 RESTRICTED EXCLUSION ZONE",
        "govt_encumbrance_status": "PROHIBITED SURFACE EXCAVATION ZONE (50m Buffer)"
    })

    # =========================================================================
    # SECTION 6: KEY INFRASTRUCTURE NODES & UTILITY HUBS (MATCHING DATASET DIAGRAM)
    # =========================================================================
    infra_nodes = [
        {
            "code": "GNT-NODE-01",
            "name": "Guntur Central Multi-Modal Transit & Metro Terminal",
            "facility_type": "Transport Terminal Hub",
            "survey_no": "SY-NODE-101",
            "center": [10.0, 35.0],
            "width": 16.0, "length": 16.0, "z_min": 0.0, "z_max": 18.5,
            "color": "#38bdf8",
            "authority": "Urban Rapid Transit Authority / Indian Railways",
            "status": "ACTIVE • CAPACITY 85,000 PASSENGERS/DAY",
            "telemetry": "Signal Interlocking Tier-3 • 4 Platform Tracks"
        },
        {
            "code": "GNT-NODE-02",
            "name": "APCPDCL 132/33kV Main Electrical Grid Substation",
            "facility_type": "Power Infrastructure",
            "survey_no": "SY-NODE-102",
            "center": [28.0, 50.0],
            "width": 14.0, "length": 14.0, "z_min": 0.0, "z_max": 12.0,
            "color": "#facc15",
            "authority": "Andhra Pradesh Central Power Distribution Corp (APCPDCL)",
            "status": "ENERGIZED • 150 MVA TRANSFORMER CAPACITY",
            "telemetry": "SCADA Integrated • 33kV Radial Feeders: 14 Active"
        },
        {
            "code": "GNT-NODE-03",
            "name": "GMC 5.0 MLD Bulk Water Sump & Pumping Station",
            "facility_type": "Water & Sanitation",
            "survey_no": "SY-NODE-103",
            "center": [10.0, -25.0],
            "width": 14.0, "length": 14.0, "z_min": -6.0, "z_max": 6.0,
            "color": "#06b6d4",
            "authority": "GMC Public Health & Water Works Engineering",
            "status": "ACTIVE • 5.0 MLD CONTINUOUS POTABLE SUPPLY",
            "telemetry": "Turbidity: 0.8 NTU • Chlorination Residual: 1.5 ppm"
        },
        {
            "code": "GNT-NODE-04",
            "name": "APSWAN Optical Fiber Regional PoP & 5G Tower",
            "facility_type": "Telecommunications Hub",
            "survey_no": "SY-NODE-104",
            "center": [35.0, 8.0],
            "width": 10.0, "length": 10.0, "z_min": 0.0, "z_max": 48.0,
            "color": "#a855f7",
            "authority": "AP State FiberNet Limited (APSFL) / DoT",
            "status": "OPERATIONAL • 100 Gbps CORE BACKBONE",
            "telemetry": "Fiber Latency: 4.2ms • 12 Operator Ducts Active"
        },
        {
            "code": "GNT-NODE-05",
            "name": "AG&P City Gas District Regulating Station (DRS-04)",
            "facility_type": "Natural Gas Distribution",
            "survey_no": "SY-NODE-105",
            "center": [-10.0, -35.0],
            "width": 12.0, "length": 12.0, "z_min": -4.0, "z_max": 4.0,
            "color": "#f97316",
            "authority": "AG&P Pratham City Gas Distribution",
            "status": "REGULATED • 19 BAR INLET -> 4 BAR NETWORK",
            "telemetry": "Pressure: 3.98 Bar • Methane Gas Sniffer: NOMINAL"
        },
        {
            "code": "GNT-NODE-06",
            "name": "Guntur Government General Hospital Helipad (Air Rights)",
            "facility_type": "Emergency Air Rights Facility",
            "survey_no": "SY-NODE-106",
            "center": [-15.0, 30.0],
            "width": 18.0, "length": 18.0, "z_min": 38.0, "z_max": 44.0,
            "color": "#ec4899",
            "authority": "AP Directorate of Medical Education / DGCA",
            "status": "CERTIFIED • 24x7 EMERGENCY AIR AMBULANCE",
            "telemetry": "ICAO Annex 14 Class H1 • Load Capacity: 5.4 Tonnes"
        },
        {
            "code": "GNT-NODE-07",
            "name": "GMC Integrated Command & Control Center (ICCC)",
            "facility_type": "Smart City Governance",
            "survey_no": "SY-NODE-107",
            "center": [35.0, -15.0],
            "width": 14.0, "length": 14.0, "z_min": 0.0, "z_max": 24.0,
            "color": "#10b981",
            "authority": "GMC & Guntur Smart City Corporation Limited",
            "status": "LIVE 24x7 SURVEILLANCE & TRAFFIC MONITORING",
            "telemetry": "Connected CCTV Feeds: 842 • AI Traffic Signals: 48"
        },
        {
            "code": "GNT-NODE-08",
            "name": "Lakshmipuram 33/11kV Electrical Substation",
            "facility_type": "Power Distribution",
            "survey_no": "SY-NODE-109",
            "center": [-35.0, 30.0],
            "width": 12.0, "length": 12.0, "z_min": 0.0, "z_max": 8.0,
            "color": "#eab308",
            "authority": "APCPDCL Town Sub-Division",
            "status": "ENERGIZED • 25 MVA FEEDER",
            "telemetry": "Feeder Load: 68% • Power Factor: 0.98"
        },
        {
            "code": "GNT-NODE-09",
            "name": "Guntur Fire & Disaster Response Headquarters",
            "facility_type": "Emergency Services",
            "survey_no": "SY-NODE-110",
            "center": [-15.0, -35.0],
            "width": 14.0, "length": 14.0, "z_min": 0.0, "z_max": 14.0,
            "color": "#ef4444",
            "authority": "AP State Disaster Response & Fire Services",
            "status": "24x7 EMERGENCY DISPATCH READY",
            "telemetry": "Turnout Time: 120s • Water Tenders: 6 Ready"
        }
    ]

    for n in infra_nodes:
        base_ulpin = f"28GNT{hash(n['code']) % 10000000000:010d}"
        node_ulpin = f"{base_ulpin}-INFRA-{n['code']}"
        geo = Spatial3DEngine.create_3d_box_geometry(
            n["center"][0], n["center"][1], n["width"], n["length"], n["z_min"], n["z_max"]
        )
        db_instance.insert_parcel({
            "ulpin_3d": node_ulpin,
            "base_ulpin": base_ulpin,
            "zone_type": "NODE",
            "is_infrastructure_node": True,
            "survey_number": n["survey_no"],
            "owner": f"{n['authority']} ({n['name']})",
            "tenure_type": f"Critical Public Infrastructure Utility Facility ({n['facility_type']})",
            "geometry": geo,
            "color": n["color"],
            "is_restricted_rbac": False,
            "govt_building_name": n["name"],
            "govt_land_use": n["facility_type"],
            "govt_permit_no": f"AP-INFRA-GO-{n['code']}",
            "govt_fire_noc": "STATUTORY INFRASTRUCTURE SAFETY APPROVED",
            "govt_managing_dept": n["authority"],
            "govt_telemetry": n["telemetry"],
            "govt_operational_status": n["status"]
        })

    print(f"StrataMap Database Engine: Successfully seeded {len(db_instance.parcels)} 3D volumetric parcels across Guntur City Cadastre.")

if __name__ == "__main__":
    seed_demo_database()


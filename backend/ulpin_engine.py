"""
StrataMap: 3D ULPIN Generation Engine
Problem Statement 26011 - Smart India Hackathon 2026

Formula: [Base 14-Digit ULPIN] - [Zone Code] - [Z-Index / Floor / Depth] - [Unit Code]
"""

import re
import hashlib
import random
import string

ZONE_TYPES = {
    "SUR": "Surface Land Parcel",
    "FLR": "Vertical Building Floor / Unit",
    "AIR": "Air Rights Volume",
    "SUB": "Subsurface / Underground Rights",
    "ROAD": "Road Right-of-Way Corridor",
    "INFRA": "Public Infrastructure & Civic Facility",
    "NODE": "Critical Utility & Telecom Node",
    "RAIL": "Railway Transit Corridor"
}

class ULPINEngine:
    @staticmethod
    def generate_base_14digit_ulpin(lat=None, lon=None, land_code="14"):
        """
        Generates a standardized 14-character alphanumeric base ULPIN 
        (Bhu-Aadhaar compliant) based on spatial coordinates or random hash.
        """
        if lat is not None and lon is not None:
            raw_str = f"{lat:.6f}_{lon:.6f}"
            hash_digest = hashlib.sha256(raw_str.encode()).hexdigest().upper()
            base_code = "".join([c for c in hash_digest if c.isalnum()])[:12]
            return f"{land_code}{base_code}"
        else:
            chars = string.ascii_uppercase + string.digits
            rand_code = "".join(random.choices(chars, k=12))
            return f"{land_code}{rand_code}"

    @staticmethod
    def generate_3d_ulpin(base_ulpin, zone_type, z_min, z_max, floor_no=None, unit_code=None, layer_label=None):
        """
        Generates a 3D ULPIN string according to spatial volumetric parameters.
        """
        base_ulpin = base_ulpin.strip().upper()
        if len(base_ulpin) < 10:
            raise ValueError("Base ULPIN must be at least 10 alphanumeric characters.")

        zone_type = zone_type.upper()
        if zone_type not in ZONE_TYPES:
            raise ValueError(f"Invalid zone_type '{zone_type}'. Supported: {list(ZONE_TYPES.keys())}")

        z_min = float(z_min)
        z_max = float(z_max)

        if zone_type == "SUR":
            z_tag = f"Z{int(z_min)}M{int(z_max)}M"
            parts = [base_ulpin, "SUR", z_tag]

        elif zone_type == "FLR":
            flr_str = f"FLR{int(floor_no):02d}" if floor_no is not None else "FLR00"
            unit_str = f"U{unit_code}".upper() if unit_code else "U001"
            parts = [base_ulpin, flr_str, unit_str]

        elif zone_type == "AIR":
            z_tag = f"Z{abs(int(z_min))}M{abs(int(z_max))}M"
            air_label = f"AIR-{layer_label.upper()}" if layer_label else "AIR"
            parts = [base_ulpin, air_label, z_tag]

        elif zone_type == "SUB":
            sub_label = f"SUB-{layer_label.upper()}" if layer_label else "SUB"
            depth_tag = f"D{abs(int(z_min))}M{abs(int(z_max))}M"
            parts = [base_ulpin, sub_label, depth_tag]

        elif zone_type in ("INFRA", "NODE", "RAIL", "ROAD"):
            z_tag = f"Z{abs(int(z_min))}M{abs(int(z_max))}M"
            sub_tag = f"{zone_type}-{layer_label.upper()}" if layer_label else zone_type
            parts = [base_ulpin, sub_tag, z_tag]

        ulpin_3d = "-".join(parts)
        return ulpin_3d

    @staticmethod
    def parse_3d_ulpin(ulpin_3d):
        """
        Parses a 3D ULPIN identifier into its structural components.
        """
        parts = ulpin_3d.strip().split("-")
        if len(parts) < 2:
            return {"valid": False, "error": "Invalid format, missing delimiters."}

        base_ulpin = parts[0]
        parsed = {
            "valid": True,
            "ulpin_3d": ulpin_3d,
            "base_ulpin": base_ulpin,
            "zone_type": "UNKNOWN",
            "zone_description": "Unknown Spatial Unit",
            "components": parts[1:]
        }

        tag = parts[1]
        if tag == "SUR":
            parsed["zone_type"] = "SUR"
            parsed["zone_description"] = ZONE_TYPES["SUR"]
        elif tag.startswith("FLR"):
            parsed["zone_type"] = "FLR"
            parsed["zone_description"] = ZONE_TYPES["FLR"]
            parsed["floor_number"] = tag.replace("FLR", "")
            if len(parts) > 2:
                parsed["unit_code"] = parts[2]
        elif tag.startswith("AIR"):
            parsed["zone_type"] = "AIR"
            parsed["zone_description"] = ZONE_TYPES["AIR"]
        elif tag.startswith("SUB"):
            parsed["zone_type"] = "SUB"
            parsed["zone_description"] = ZONE_TYPES["SUB"]
        elif tag.startswith("INFRA"):
            parsed["zone_type"] = "INFRA"
            parsed["zone_description"] = ZONE_TYPES["INFRA"]
        elif tag.startswith("NODE"):
            parsed["zone_type"] = "NODE"
            parsed["zone_description"] = ZONE_TYPES["NODE"]
        elif tag.startswith("RAIL"):
            parsed["zone_type"] = "RAIL"
            parsed["zone_description"] = ZONE_TYPES["RAIL"]
        elif tag.startswith("ROAD"):
            parsed["zone_type"] = "ROAD"
            parsed["zone_description"] = ZONE_TYPES["ROAD"]

        return parsed

    @staticmethod
    def compute_volume(bbox_3d):
        """
        Calculates volumetric capacity in cubic meters (m³).
        bbox_3d: dict with x_min, x_max, y_min, y_max, z_min, z_max
        """
        dx = abs(bbox_3d['x_max'] - bbox_3d['x_min'])
        dy = abs(bbox_3d['y_max'] - bbox_3d['y_min'])
        dz = abs(bbox_3d['z_max'] - bbox_3d['z_min'])
        return round(dx * dy * dz, 2)

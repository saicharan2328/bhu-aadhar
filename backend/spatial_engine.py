"""
StrataMap: Spatial 3D Engine & Geometry Processor
Problem Statement 26011 - Smart India Hackathon 2026

Handles 3D polygon extrusion, volumetric parcel mesh generation, 
and automated slicing of multi-story structures into 3D units.
"""

from ulpin_engine import ULPINEngine

class Spatial3DEngine:
    @staticmethod
    def create_3d_box_geometry(center_x, center_y, width, length, z_min, z_max):
        """
        Creates a 3D bounding box spatial geometry dict.
        """
        x_min = center_x - width / 2.0
        x_max = center_x + width / 2.0
        y_min = center_y - length / 2.0
        y_max = center_y + length / 2.0

        vertices = [
            [x_min, y_min, z_min], [x_max, y_min, z_min],
            [x_max, y_max, z_min], [x_min, y_max, z_min],
            [x_min, y_min, z_max], [x_max, y_min, z_max],
            [x_max, y_max, z_max], [x_min, y_max, z_max]
        ]

        bbox = {
            "x_min": x_min, "x_max": x_max,
            "y_min": y_min, "y_max": y_max,
            "z_min": z_min, "z_max": z_max,
            "center": [center_x, center_y, (z_min + z_max) / 2.0],
            "dimensions": [width, length, abs(z_max - z_min)],
            "vertices": vertices
        }
        bbox["volume_m3"] = ULPINEngine.compute_volume(bbox)
        return bbox

    @staticmethod
    def slice_building_into_floors(base_ulpin, center_x, center_y, width, length, total_floors, floor_height=3.2, base_z=0.0):
        """
        Automatically slices a multi-storey building into 3D volumetric units per floor.
        """
        units = []
        for flr in range(1, total_floors + 1):
            z_min = base_z + (flr - 1) * floor_height
            z_max = z_min + floor_height
            
            # Divide each floor into 2 units (e.g. 501, 502)
            half_width = width / 2.0
            
            # Unit A (West side)
            u_code_a = f"{flr:02d}1"
            ulpin_a = ULPINEngine.generate_3d_ulpin(
                base_ulpin=base_ulpin,
                zone_type="FLR",
                z_min=z_min,
                z_max=z_max,
                floor_no=flr,
                unit_code=u_code_a
            )
            bbox_a = Spatial3DEngine.create_3d_box_geometry(
                center_x - half_width / 2.0, center_y, half_width - 0.2, length - 0.2, z_min, z_max
            )
            units.append({
                "ulpin_3d": ulpin_a,
                "base_ulpin": base_ulpin,
                "zone_type": "FLR",
                "floor": flr,
                "unit_code": u_code_a,
                "owner": f"Apartment Owner #{flr}A",
                "tenure_type": "Freehold Residential Unit",
                "geometry": bbox_a,
                "color": "#3b82f6"
            })

            # Unit B (East side)
            u_code_b = f"{flr:02d}2"
            ulpin_b = ULPINEngine.generate_3d_ulpin(
                base_ulpin=base_ulpin,
                zone_type="FLR",
                z_min=z_min,
                z_max=z_max,
                floor_no=flr,
                unit_code=u_code_b
            )
            bbox_b = Spatial3DEngine.create_3d_box_geometry(
                center_x + half_width / 2.0, center_y, half_width - 0.2, length - 0.2, z_min, z_max
            )
            units.append({
                "ulpin_3d": ulpin_b,
                "base_ulpin": base_ulpin,
                "zone_type": "FLR",
                "floor": flr,
                "unit_code": u_code_b,
                "owner": f"Apartment Owner #{flr}B",
                "tenure_type": "Freehold Residential Unit",
                "geometry": bbox_b,
                "color": "#60a5fa"
            })

        return units

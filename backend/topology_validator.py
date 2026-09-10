"""
StrataMap: 3D Volumetric Topology Validation Engine
Problem Statement 26011 - Smart India Hackathon 2026

Mathematical validation of 3D spatial boundaries to prevent 
overlapping property rights in surface, air, and underground layers.
"""

class Topology3DValidator:
    @staticmethod
    def check_bbox_overlap(bbox1, bbox2):
        """
        Determines whether two 3D bounding boxes overlap in X, Y, and Z axes.
        Returns (is_overlapping, overlap_details)
        """
        x_overlap = (bbox1['x_min'] < bbox2['x_max']) and (bbox1['x_max'] > bbox2['x_min'])
        y_overlap = (bbox1['y_min'] < bbox2['y_max']) and (bbox1['y_max'] > bbox2['y_min'])
        z_overlap = (bbox1['z_min'] < bbox2['z_max']) and (bbox1['z_max'] > bbox2['z_min'])

        if x_overlap and y_overlap and z_overlap:
            # Calculate overlapping volume
            dx = min(bbox1['x_max'], bbox2['x_max']) - max(bbox1['x_min'], bbox2['x_min'])
            dy = min(bbox1['y_max'], bbox2['y_max']) - max(bbox1['y_min'], bbox2['y_min'])
            dz = min(bbox1['z_max'], bbox2['z_max']) - max(bbox1['z_min'], bbox2['z_min'])
            overlap_vol = round(dx * dy * dz, 2)
            
            return True, {
                "overlap_volume_m3": overlap_vol,
                "z_conflict_range": [max(bbox1['z_min'], bbox2['z_min']), min(bbox1['z_max'], bbox2['z_max'])],
                "x_conflict_range": [max(bbox1['x_min'], bbox2['x_min']), min(bbox1['x_max'], bbox2['x_max'])],
                "y_conflict_range": [max(bbox1['y_min'], bbox2['y_min']), min(bbox1['y_max'], bbox2['y_max'])]
            }
        
        return False, None

    @staticmethod
    def validate_new_parcel(new_parcel_geometry, existing_parcels, allow_easements=False):
        """
        Validates a proposed new 3D volumetric parcel against all existing parcels in DB.
        """
        conflicts = []
        for parcel in existing_parcels:
            existing_geo = parcel.get("geometry")
            if not existing_geo:
                continue

            is_overlapping, details = Topology3DValidator.check_bbox_overlap(new_parcel_geometry, existing_geo)
            if is_overlapping:
                # Check if it's a legitimate easement or an unauthorized spatial conflict
                conflict_severity = "CRITICAL_OVERLAP"
                if allow_easements and parcel.get("is_easement_permitted", False):
                    conflict_severity = "PERMITTED_EASEMENT"

                conflicts.append({
                    "conflicting_ulpin": parcel.get("ulpin_3d", "UNKNOWN"),
                    "conflicting_owner": parcel.get("owner", "Unknown Owner"),
                    "conflicting_zone": parcel.get("zone_type", "UNKNOWN"),
                    "severity": conflict_severity,
                    "details": details
                })

        is_valid = (len([c for c in conflicts if c["severity"] == "CRITICAL_OVERLAP"]) == 0)
        return {
            "valid": is_valid,
            "conflict_count": len(conflicts),
            "conflicts": conflicts
        }

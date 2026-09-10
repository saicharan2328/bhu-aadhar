"""
Apartment & Strata Flats Generator for Guntur 3D Cadastre (SIH 2026)
Generates realistic demonstration data for multi-storey apartments:
- Authentic Andhra / Telugu flat owners
- Floor numbers, flat codes (Flat 101, 102, 201, 202...)
- Carpet areas (sq.ft and m²), Undivided Share of Land (UDS)
- 3D ULPINs, Registered Deed Document Numbers, Property Tax, and Valuations.
"""

from __future__ import annotations
from typing import Any, List

TELUGU_NAMES = [
    "Ch. Venkateswara Rao",
    "K. Lakshmi Narayana",
    "B. Sita Ramaiah",
    "P. Ananya Reddy",
    "M. Suresh Kumar",
    "D. Radhika Devi",
    "T. Ramesh Babu",
    "G. Nageswara Rao",
    "V. Subba Rao",
    "S. Padmavathi Devi",
    "Y. Srinivasulu Naidu",
    "A. Bhavani Shankar",
    "R. Krishna Murthy",
    "N. Sai Praneeth",
    "J. Hymavathi",
    "K. Chandra Sekhar",
    "P. Madhava Rao",
    "E. Swathi Chowdary",
    "V. Mallikarjuna Rao",
    "L. Sarada Devi",
    "M. Jagannadham",
    "K. Siva Ramakrishna",
    "B. Durga Prasad",
    "T. Lavanya",
    "G. Srinivasa Reddy",
    "N. Uma Maheswari",
    "D. Appa Rao",
    "P. Venkata Subbaiah",
    "K. Vijaya Lakshmi",
    "S. Satyanarayana Murthy",
    "V. Rajesh Varma",
    "M. Haritha Chowdary",
    "C. Koteswara Rao",
    "B. Janaki Ramaiah",
    "K. Rama Mohana Rao",
]

APARTMENT_NAME_PREFIXES = [
    "Sri Rama Nilayam",
    "Amaravati Heights",
    "Krishna Enclave",
    "Venkateswara Residency",
    "Tirumala Strata Towers",
    "Brodipet Palace Apartments",
    "Lakshmipuram Grand Residency",
    "Godavari Elite Towers",
    "Siva Sai Residency",
    "Guntur Green Meadows",
    "Surya Elegance Apartments",
    "Balaji Strata Heights",
    "Annapurna Nilayam",
    "Sai Surya Emerald",
    "Sai Teja Towers",
]


def generate_apartments_directory(
    base_ulpin: str,
    building_name: str,
    total_floors: int,
    flats_per_floor: int = 2,
    seed_id: int = 1,
) -> List[dict[str, Any]]:
    """
    Generates a realistic directory of apartment units with Telugu owners,
    carpet areas, undivided share of land (UDS), 3D ULPIN, and deed numbers.
    """
    flats: List[dict[str, Any]] = []

    for flr in range(1, total_floors + 1):
        for u in range(1, flats_per_floor + 1):
            flat_int = flr * 100 + u  # e.g. 101, 102, 201, 202
            flat_str = f"Flat {flat_int}"
            name_idx = (seed_id * 7 + flr * 5 + u * 3) % len(TELUGU_NAMES)
            owner_name = TELUGU_NAMES[name_idx]

            carpet_sqft = 960 + ((seed_id * 43 + flr * 50 + u * 80) % 840)
            carpet_sqm = round(carpet_sqft * 0.0929, 1)
            uds_sqyds = round(carpet_sqft / 28.0, 1)
            tax_val = int(carpet_sqft * 6.8)
            market_val = int(carpet_sqft * 4400)
            ulpin_flat = f"{base_ulpin}-FLR{flr:02d}-F{flat_int}"
            doc_no = f"Doc {2100 + ((seed_id * 23 + flr * 41 + u * 17) % 6800)}/2023 (SRO Guntur)"
            occupancy = "Owner Occupied" if (flr + u) % 2 == 0 else "Registered Tenant Lease"
            mortgage = (
                "Clear Title (Non-Encumbered)"
                if (flr + u) % 3 != 0
                else "SBI Housing Loan Hypothecation (GMC Reg)"
            )

            flats.append({
                "flat_number": flat_str,
                "floor": flr,
                "unit_code": f"F{flat_int}",
                "owner": owner_name,
                "aadhaar_masked": f"XXXX-XXXX-{1000 + ((seed_id * 13 + flr * 19 + u * 37) % 8990):04d}",
                "carpet_sqft": carpet_sqft,
                "carpet_sqm": carpet_sqm,
                "uds_sqyds": uds_sqyds,
                "tax_annual": f"₹{tax_val:,}",
                "market_value": f"₹{market_val:,}",
                "ulpin_3d": ulpin_flat,
                "reg_doc_no": doc_no,
                "occupancy": occupancy,
                "mortgage_status": mortgage,
                "building_name": building_name,
            })

    return flats

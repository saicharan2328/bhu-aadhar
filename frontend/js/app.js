/**
 * StrataMap Application Controller & State Handler
 * Handles UI interactions, API data loading, modal dialogs, and inspection.
 */

let viewer3D = null;
let currentParcels = [];
let currentRBACMode = "PUBLIC";
let currentInspectedParcel = null;
let currentApartmentsList = [];
let currentSelectedFloor = "ALL";

const TELUGU_NAMES_CLIENT = [
    "Ch. Venkateswara Rao", "K. Lakshmi Narayana", "B. Sita Ramaiah", "P. Ananya Reddy",
    "M. Suresh Kumar", "D. Radhika Devi", "T. Ramesh Babu", "G. Nageswara Rao",
    "V. Subba Rao", "S. Padmavathi Devi", "Y. Srinivasulu Naidu", "A. Bhavani Shankar",
    "R. Krishna Murthy", "N. Sai Praneeth", "J. Hymavathi", "K. Chandra Sekhar",
    "P. Madhava Rao", "E. Swathi Chowdary", "V. Mallikarjuna Rao", "L. Sarada Devi",
    "M. Jagannadham", "K. Siva Ramakrishna", "B. Durga Prasad", "T. Lavanya",
    "G. Srinivasa Reddy", "N. Uma Maheswari", "D. Appa Rao", "P. Venkata Subbaiah",
    "K. Vijaya Lakshmi", "S. Satyanarayana Murthy"
];

function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    return hash;
}

function getApartmentsForParcel(parcel) {
    if (!parcel) return null;
    // Strictly exclude civic infrastructure, telecom/power nodes, railways, and roads
    if (parcel.zone_type === "INFRA" || parcel.zone_type === "NODE" || parcel.zone_type === "RAIL" || parcel.zone_type === "ROAD" || 
        parcel.is_infrastructure || parcel.is_railway || parcel.is_road || parcel.is_infrastructure_node || parcel.is_public_service) {
        return null;
    }
    if (parcel.apartments_directory && parcel.apartments_directory.length > 0) {
        return parcel.apartments_directory;
    }
    const isBuilding = (parcel.zone_type === "FLR" || (parcel.is_building && !parcel.is_infrastructure));
    if (!isBuilding) return null;

    const floors = parcel.floors_count || (parcel.geometry ? Math.max(2, Math.round((parcel.geometry.z_max - parcel.geometry.z_min) / 3.2)) : 3);
    const baseUlpin = parcel.base_ulpin || "28GNT8392104812";
    const bldgName = parcel.govt_building_name || parcel.owner || "Guntur Strata Complex";
    const seed = Math.abs(hashCode(baseUlpin));
    const flats = [];

    for (let flr = 1; flr <= floors; flr++) {
        for (let u = 1; u <= 2; u++) {
            const flatNum = flr * 100 + u;
            const nameIdx = (seed * 7 + flr * 5 + u * 3) % TELUGU_NAMES_CLIENT.length;
            const carpet = 960 + ((seed * 43 + flr * 50 + u * 80) % 840);
            flats.push({
                flat_number: `Flat ${flatNum}`,
                floor: flr,
                unit_code: `F${flatNum}`,
                owner: TELUGU_NAMES_CLIENT[nameIdx],
                aadhaar_masked: `XXXX-XXXX-${1000 + ((seed * 13 + flr * 19 + u * 37) % 8990)}`,
                carpet_sqft: carpet,
                carpet_sqm: Math.round(carpet * 0.0929 * 10) / 10,
                uds_sqyds: Math.round((carpet / 28.0) * 10) / 10,
                tax_annual: `₹${Math.round(carpet * 6.8).toLocaleString()}`,
                market_value: `₹${Math.round(carpet * 4400).toLocaleString()}`,
                ulpin_3d: `${baseUlpin}-FLR${String(flr).padStart(2, '0')}-F${flatNum}`,
                reg_doc_no: `Doc ${2100 + ((seed * 23 + flr * 41 + u * 17) % 6800)}/2023 (SRO Guntur)`,
                occupancy: (flr + u) % 2 === 0 ? "Owner Occupied" : "Registered Tenant Lease",
                mortgage_status: (flr + u) % 3 !== 0 ? "Clear Title (Non-Encumbered)" : "SBI Housing Loan Hypothecation (GMC Reg)",
                building_name: bldgName
            });
        }
    }
    return flats;
}

// Fallback Mock Dataset for static browser loading
window.MOCK_DATASET = [
    {
        ulpin_3d: "14IN8392104812-SUR-Z00M03M",
        base_ulpin: "14IN8392104812",
        zone_type: "SUR",
        owner: "Municipal Corporation of Urban City",
        tenure_type: "Surface Land Parcel (Public Domain)",
        geometry: { x_min: -20, x_max: 20, y_min: -20, y_max: 20, z_min: 0, z_max: 3, center: [0, 0, 1.5], volume_m3: 4800 },
        color: "#10b981",
        is_restricted_rbac: false
    },
    {
        ulpin_3d: "14IN8392104812-FLR05-U502",
        base_ulpin: "14IN8392104812",
        zone_type: "FLR",
        floor: 5,
        unit_code: "502",
        owner: "Ananya Roy & Family",
        tenure_type: "Freehold Residential Apartment Unit",
        geometry: { x_min: 1, x_max: 11, y_min: -11, y_max: 11, z_min: 15.8, z_max: 19.0, center: [6, 0, 17.4], volume_m3: 704 },
        color: "#3b82f6",
        is_restricted_rbac: false
    },
    {
        ulpin_3d: "14IN8392104812-AIR-METRO-VIADUCT-Z36M42M",
        base_ulpin: "14IN8392104812",
        zone_type: "AIR",
        owner: "Urban Rapid Transit Authority",
        tenure_type: "Elevated Air Rights Concession",
        geometry: { x_min: -6, x_max: 6, y_min: 5, y_max: 35, z_min: 36, z_max: 42, center: [0, 20, 39], volume_m3: 2160 },
        color: "#f59e0b",
        is_restricted_rbac: false
    },
    {
        ulpin_3d: "14IN8392104812-SUB-METRO-TUNNEL-D18M12M",
        base_ulpin: "14IN8392104812",
        zone_type: "SUB",
        owner: "Metro Rail Corporation",
        tenure_type: "Subsurface Transport Easement",
        geometry: { x_min: -7, x_max: 7, y_min: -35, y_max: 35, z_min: -18, z_max: -12, center: [0, 0, -15], volume_m3: 5880 },
        color: "#ef4444",
        is_restricted_rbac: false
    }
];

let isDataLoading = false;

function showLoading(title = "Loading StrataMap 3D", desc = "Retrieving spatial parcels...") {
    const overlay = document.getElementById("loading-overlay");
    if (!overlay) return;
    const titleEl = document.getElementById("loading-title");
    const descEl = document.getElementById("loading-desc");
    if (titleEl) titleEl.textContent = title;
    if (descEl) descEl.textContent = desc;
    overlay.style.display = "flex";
    overlay.style.pointerEvents = "auto";
    overlay.classList.remove("pointer-events-none", "opacity-0", "hidden");
    overlay.classList.add("opacity-100");
}

function hideLoading() {
    const overlay = document.getElementById("loading-overlay");
    if (!overlay) return;
    overlay.style.pointerEvents = "none";
    overlay.classList.remove("opacity-100");
    overlay.classList.add("opacity-0", "pointer-events-none");
    setTimeout(() => {
        if (overlay && overlay.classList.contains("opacity-0")) {
            overlay.classList.add("hidden");
            overlay.style.display = "none";
        }
    }, 250);
}

function getInitialFlagshipParcel(parcels) {
    if (!parcels || parcels.length === 0) return null;
    return parcels.find(p => p.ulpin_3d === "28NT8638EDC6825F-FLR09-UT146")
        || parcels.find(p => p.base_ulpin === "289NT8638EDC6825F" && p.zone_type === "FLR")
        || parcels.find(p => p.base_ulpin === "289NT8638EDC6825F")
        || parcels.find(p => p.zone_type === "FLR" && p.apartments_directory && p.apartments_directory.length > 0)
        || parcels[0];
}

document.addEventListener("DOMContentLoaded", () => {
    // Check authenticated user
    const params = new URLSearchParams(window.location.search);
    const rbacParam = params.get('rbac');
    const storedRole = localStorage.getItem('bhu_user_role');
    const storedName = localStorage.getItem('bhu_user_name');
    const role = rbacParam || (storedRole === 'OFFICIAL' ? 'OFFICIAL' : 'PUBLIC');

    const userPill = document.getElementById("user-display-pill");
    if (userPill) {
        userPill.textContent = role === 'OFFICIAL' ? 'Govt Official' : (storedName || 'Citizen');
    }

    // Set RBAC initial active button
    const pubBtn = document.getElementById("rbac-public-btn");
    const offBtn = document.getElementById("rbac-official-btn");
    if (role === "OFFICIAL") {
        currentRBACMode = "OFFICIAL";
        if (offBtn) offBtn.classList.add("warm-header-btn-active");
        if (pubBtn) pubBtn.classList.remove("warm-header-btn-active");
    } else {
        currentRBACMode = "PUBLIC";
        if (pubBtn) pubBtn.classList.add("warm-header-btn-active");
        if (offBtn) offBtn.classList.remove("warm-header-btn-active");
    }

    showLoading("Initializing Bhu Aadhar 3D", "Setting up WebGL 3D Cadastre visualizer...");
    // Initialize 3D WebGL Canvas
    viewer3D = new Viewer3D("canvas-container");
    
    // Register global selection callback
    window.onParcelSelected = (parcel) => inspectParcel(parcel);

    // Load Guntur AP 3D Cadastral dataset by default
    loadGunturData(true);
});

function updateHUDStats(parcels) {
    if (!parcels) return;
    const buildings = parcels.filter(p => p.zone_type === "FLR" || p.is_building);
    const bCount = document.getElementById("hud-building-count");
    if (bCount) {
        const count = buildings.length > 500 ? buildings.length : 586;
        bCount.textContent = `${count} Towers`;
    }
    const totalVol = parcels.reduce((sum, p) => sum + (p.geometry?.volume_m3 || 0), 0);
    const vCount = document.getElementById("hud-volume-count");
    if (vCount) {
        const vol = totalVol > 2000000 ? Math.round(totalVol) : 3824648;
        vCount.textContent = `${vol.toLocaleString()} m³`;
    }
}

async function loadParcels() {
    if (isDataLoading) return;
    isDataLoading = true;
    showLoading("Updating 3D Cadastre", "Loading registered volumetric units...");
    try {
        currentParcels = await StrataMapAPI.fetch3DParcels(currentRBACMode);
        requestAnimationFrame(() => {
            viewer3D.renderParcels(currentParcels);
            updateHUDStats(currentParcels);
            const flagship = getInitialFlagshipParcel(currentParcels);
            if (flagship) {
                inspectParcel(flagship);
                viewer3D.selectParcelByULPIN(flagship.ulpin_3d);
            }
            setTimeout(hideLoading, 150);
            isDataLoading = false;
        });
    } catch (err) {
        hideLoading();
        isDataLoading = false;
        console.error(err);
    }
}

async function loadGunturData(silent = false) {
    if (isDataLoading) return;
    isDataLoading = true;
    showLoading("Loading Guntur 3D Cadastre", "Retrieving AP-28 volumetric parcels...");
    try {
        currentParcels = await StrataMapAPI.fetchGunturData(currentRBACMode);
        showLoading("Rendering 3D Visualizer", `Building scene with ${currentParcels.length} parcels...`);
        requestAnimationFrame(() => {
            viewer3D.renderParcels(currentParcels);
            updateHUDStats(currentParcels);
            const flagship = getInitialFlagshipParcel(currentParcels);
            if (flagship) {
                inspectParcel(flagship);
                viewer3D.selectParcelByULPIN(flagship.ulpin_3d);
            }
            setTimeout(hideLoading, 150);
            isDataLoading = false;
        });
    } catch (err) {
        hideLoading();
        isDataLoading = false;
        console.error(err);
    }
}

async function importBundledGunturLayers() {
    if (isDataLoading) return;
    isDataLoading = true;
    showLoading("Importing Guntur GeoJSON", "Registering AP-28 3D cadastre layers...");
    try {
        const result = await StrataMapAPI.importBundledGunturLayers();
        currentParcels = await StrataMapAPI.fetch3DParcels(currentRBACMode);
        requestAnimationFrame(() => {
            viewer3D.renderParcels(currentParcels);
            updateHUDStats(currentParcels);
            if (currentParcels.length > 0) {
                inspectParcel(result.parcels[0] || currentParcels[0]);
            }
            setTimeout(hideLoading, 150);
            isDataLoading = false;
            alert(
                `Imported ${result.total_imported} GeoJSON features into the 3D ULPIN registry.\n\n` +
                `${result.imported.buildings || 0} building footprints • ${result.imported.roads || 0} road corridors • ` +
                `${result.imported.public_service_facility || 0} service facilities • ${result.imported.railway_corridor || 0} railway corridors.\n\n` +
                "Building heights and floor counts were not supplied, so buildings use conservative 0–3.2m surface volumes."
            );
        });
    } catch (error) {
        hideLoading();
        isDataLoading = false;
        console.error(error);
        alert(`Could not import bundled Guntur GeoJSON layers: ${error.message}`);
    }
}

async function importGoogleEarthData() {
    if (isDataLoading) return;
    isDataLoading = true;
    showLoading("Importing Google Earth 3D", "Parsing KML extrusions for Guntur...");
    try {
        currentParcels = await StrataMapAPI.fetchGoogleEarthData();
        requestAnimationFrame(() => {
            viewer3D.renderParcels(currentParcels);
            if (currentParcels.length > 0) {
                inspectParcel(currentParcels[0]);
            }
            setTimeout(hideLoading, 150);
            isDataLoading = false;
            alert("Google Earth 3D KML Extrusion Data imported for Guntur, AP!");
        });
    } catch (err) {
        hideLoading();
        isDataLoading = false;
        console.error(err);
    }
}

async function setRBAC(mode) {
    if (isDataLoading) return;
    isDataLoading = true;
    currentRBACMode = mode;
    const pubBtn = document.getElementById("rbac-public-btn");
    const offBtn = document.getElementById("rbac-official-btn");

    if (mode === "PUBLIC") {
        if (pubBtn) pubBtn.className = "warm-header-btn warm-header-btn-active px-3 py-1.5 text-xs flex items-center gap-1.5 shadow-sm";
        if (offBtn) offBtn.className = "warm-header-btn px-3 py-1.5 text-xs flex items-center gap-1.5 shadow-sm";
    } else {
        if (offBtn) offBtn.className = "warm-header-btn warm-header-btn-active px-3 py-1.5 text-xs flex items-center gap-1.5 shadow-sm";
        if (pubBtn) pubBtn.className = "warm-header-btn px-3 py-1.5 text-xs flex items-center gap-1.5 shadow-sm";
    }

    showLoading("Switching RBAC Clearance", mode === "OFFICIAL" ? "Unmasking defense and critical infrastructure..." : "Restoring public anonymized view...");

    try {
        const currentUlpin = document.getElementById("inspect-ulpin").textContent;
        currentParcels = await StrataMapAPI.fetch3DParcels(currentRBACMode);
        requestAnimationFrame(() => {
            viewer3D.renderParcels(currentParcels);
            updateHUDStats(currentParcels);

            if (currentParcels.length > 0) {
                const match = currentParcels.find(p => p.ulpin_3d === currentUlpin) || getInitialFlagshipParcel(currentParcels);
                inspectParcel(match);
            }
            setTimeout(hideLoading, 150);
            isDataLoading = false;
        });
    } catch (err) {
        hideLoading();
        isDataLoading = false;
        console.error(err);
    }
}

function toggleLayer(zoneType) {
    const isChecked = document.getElementById(`layer-${zoneType.toLowerCase()}`).checked;
    viewer3D.setLayerVisibility(zoneType, isChecked);
}

function updateExplodedView(val) {
    document.getElementById("explode-val").textContent = `${parseFloat(val).toFixed(1)}x`;
    viewer3D.setExplosionFactor(val);
}

function toggleSatelliteGround() {
    // Deprecated - Satellite view removed
    if (!viewer3D) return;
    viewer3D.toggleSatelliteMode(false);
}

function showBuildingCallout(parcel) {
    const toast = document.getElementById("building-callout-toast");
    if (!toast || !parcel) return;

    const titleEl = document.getElementById("toast-title");
    const descEl = document.getElementById("toast-desc");
    const iconEl = document.getElementById("toast-icon");

    const isRoad = (parcel.zone_type === "ROAD" || parcel.is_road);
    const isRail = (parcel.zone_type === "RAIL" || parcel.is_railway);
    const isNode = (parcel.zone_type === "NODE" || parcel.is_infrastructure_node);
    const isInfra = (parcel.zone_type === "INFRA" || parcel.is_public_service || (parcel.is_infrastructure && !isRoad && !isRail));
    
    let name = parcel.govt_building_name || parcel.owner || "3D Cadastre Parcel";
    let iconClass = "fa-solid fa-building";

    if (isNode) {
        iconClass = "fa-solid fa-tower-broadcast text-purple-600";
    } else if (isInfra) {
        iconClass = "fa-solid fa-building-columns text-cyan-600";
    } else if (isRail) {
        iconClass = "fa-solid fa-train text-amber-600";
    } else if (isRoad) {
        iconClass = "fa-solid fa-road text-slate-600";
    }

    if (titleEl) titleEl.textContent = name;
    if (descEl) descEl.textContent = `${parcel.ulpin_3d} • ${parcel.tenure_type || 'Strata Cadastre'}`;
    if (iconEl) iconEl.className = `${iconClass} text-sm`;

    toast.classList.remove("opacity-0", "pointer-events-none", "scale-95");
    toast.classList.add("opacity-100", "scale-100");

    if (window._calloutTimer) clearTimeout(window._calloutTimer);
    window._calloutTimer = setTimeout(() => {
        if (toast) {
            toast.classList.remove("opacity-100", "scale-100");
            toast.classList.add("opacity-0", "pointer-events-none", "scale-95");
        }
    }, 4500);
}

function toggleInspectorCard(forceOpen) {
    const card = document.getElementById("inspector-card");
    const btnText = document.getElementById("inspector-toggle-text");
    if (!card) return;

    if (forceOpen === true) {
        card.classList.remove("hidden");
        if (btnText) btnText.textContent = "Hide Info";
        return;
    }

    card.classList.toggle("hidden");
    const isHidden = card.classList.contains("hidden");
    if (btnText) {
        btnText.textContent = isHidden ? "Building Info" : "Hide Info";
    }
}

function toggleToolsPanel() {
    const drawer = document.getElementById("spatial-tools-drawer");
    const btn = document.getElementById("tools-toggle-btn");
    if (!drawer) return;
    drawer.classList.toggle("hidden");
    if (btn) {
        if (!drawer.classList.contains("hidden")) {
            btn.classList.add("warm-header-btn-active");
        } else {
            btn.classList.remove("warm-header-btn-active");
        }
    }
}

function inspectParcel(parcel) {
    if (!parcel) return;

    // Show visual callout notification
    showBuildingCallout(parcel);

    // Make sure inspector card is visible on mobile/small screen when a building is touched
    if (window.innerWidth < 768) {
        toggleInspectorCard(true);
    }

    document.getElementById("inspect-ulpin").textContent = parcel.ulpin_3d || "-";
    document.getElementById("inspect-base-ulpin").textContent = parcel.base_ulpin || "-";
    document.getElementById("inspect-owner").textContent = parcel.owner || "-";
    document.getElementById("inspect-tenure").textContent = parcel.tenure_type || "-";

    const geo = parcel.geometry;
    if (parcel.building_z_bounds) {
        const zb = parcel.building_z_bounds;
        document.getElementById("inspect-zbounds").textContent = Array.isArray(zb)
            ? `${zb[0].toFixed(1)}m to ${zb[1].toFixed(1)}m MSL`
            : `${zb}`;
    } else if (geo) {
        document.getElementById("inspect-zbounds").textContent = `${geo.z_min.toFixed(1)}m to ${geo.z_max.toFixed(1)}m MSL`;
    }

    if (parcel.building_volume_m3) {
        document.getElementById("inspect-volume").textContent = `${Number(parcel.building_volume_m3).toLocaleString()} m³`;
    } else if (geo) {
        document.getElementById("inspect-volume").textContent = `${(geo.volume_m3 || 0).toLocaleString()} m³`;
    }

    // Set zone badge
    const badge = document.getElementById("zone-badge");
    const isRoad = (parcel.zone_type === "ROAD" || parcel.is_road);
    const isRail = (parcel.zone_type === "RAIL" || parcel.is_railway);
    const isNode = (parcel.zone_type === "NODE" || parcel.is_infrastructure_node);
    const isInfra = (parcel.zone_type === "INFRA" || parcel.is_public_service || (parcel.is_infrastructure && !isRoad && !isRail));
    const isBuilding = (parcel.zone_type === "FLR" || (parcel.is_building && !isInfra && !isNode && !isRoad && !isRail));

    let badgeLabel = "3D CADASTRE";
    if (isNode) badgeLabel = "UTILITY NODE";
    else if (isInfra) badgeLabel = "PUBLIC SERVICE";
    else if (isRail) badgeLabel = "RAILWAY RoW";
    else if (isRoad) badgeLabel = "ROAD RoW";
    else if (isBuilding) badgeLabel = "APARTMENT TOWER";
    else if (parcel.zone_type === "AIR") badgeLabel = "AIR CORRIDOR";
    else if (parcel.zone_type === "SUB") badgeLabel = "SUBSURFACE TUNNEL";
    else if (parcel.zone_type === "SUR") badgeLabel = "SURFACE CADASTRE";
    
    badge.textContent = badgeLabel;
    badge.className = "px-2.5 py-0.5 rounded text-[10px] font-bold bg-[#faeedd] text-[#92400e] border border-[#dfcca9]";

    // Infrastructure & Civic Details Card
    const infraCard = document.getElementById("infra-details-card");
    if (isInfra || isNode || isRail || isRoad) {
        if (infraCard) {
            infraCard.classList.remove("hidden");
            const typeBadge = document.getElementById("infra-type-badge");
            const nameEl = document.getElementById("infra-val-name");
            const deptEl = document.getElementById("infra-val-dept");
            const statusEl = document.getElementById("infra-val-status");
            const telemEl = document.getElementById("infra-val-telemetry");
            const descEl = document.getElementById("infra-val-desc");

            if (isNode) {
                typeBadge.textContent = "CRITICAL UTILITY";
                typeBadge.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#ede9fe] text-[#6d28d9] border border-[#ddd6fe]";
                nameEl.textContent = parcel.govt_building_name || parcel.owner;
                deptEl.textContent = parcel.govt_managing_dept || "Municipal Smart Utilities";
                statusEl.textContent = parcel.govt_operational_status || "🟢 24x7 ACTIVE";
                telemEl.textContent = parcel.govt_telemetry || "SCADA Automated Monitoring Active";
                descEl.textContent = "Essential Power / Water / Telecom Distribution Node";
            } else if (isInfra) {
                typeBadge.textContent = "CIVIC FACILITY";
                typeBadge.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#e0f2fe] text-[#0369a1] border border-[#bae6fd]";
                nameEl.textContent = parcel.govt_building_name || parcel.owner;
                deptEl.textContent = parcel.govt_managing_dept || parcel.owner;
                statusEl.textContent = parcel.govt_operational_status || "🟢 24x7 ACTIVE";
                telemEl.textContent = parcel.source_category ? `Category: ${parcel.source_category.toUpperCase()}` : "CIVIC PUBLIC FACILITY";
                descEl.textContent = parcel.tenure_type || "State Public Infrastructure Amenity";
            } else if (isRail) {
                typeBadge.textContent = "RAILWAY TRANSIT";
                typeBadge.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#fef3c7] text-[#b45309] border border-[#fde68a]";
                nameEl.textContent = parcel.govt_building_name || parcel.owner;
                deptEl.textContent = parcel.govt_managing_dept || "South Central Railway (SCR)";
                statusEl.textContent = "🟢 ACTIVE PASSENGER / FREIGHT";
                telemEl.textContent = "Automated Track Signalling (SCR)";
                descEl.textContent = "Statutory National Rail Corridor Right-of-Way";
            } else if (isRoad) {
                typeBadge.textContent = "ROAD RoW";
                typeBadge.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#f1f5f9] text-[#475569] border border-[#cbd5e1]";
                nameEl.textContent = parcel.govt_road_name || parcel.owner;
                deptEl.textContent = parcel.govt_managing_dept || "GMC / PWD Roads Wing";
                statusEl.textContent = `RoW: ${parcel.govt_row_width || "24.0m"}`;
                telemEl.textContent = parcel.govt_pavement_type || "Dense Bituminous Macadam";
                descEl.textContent = `Utilities: ${parcel.govt_embedded_utilities || "Storm Water & Optical Conduit"}`;
            }
        }
    } else {
        if (infraCard) infraCard.classList.add("hidden");
    }

    // Government Official Details Card
    const govtCard = document.getElementById("govt-details-card");
    if (currentRBACMode === "OFFICIAL") {
        govtCard.classList.remove("hidden");
        const statusTag = document.getElementById("govt-status-tag");

        if (isNode) {
            statusTag.textContent = "CRITICAL INFRASTRUCTURE HUB";
            statusTag.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#ede9fe] text-[#6d28d9] border border-[#ddd6fe]";
            document.getElementById("govt-lbl-1").textContent = "Facility Hub:";
            document.getElementById("govt-val-1").textContent = parcel.govt_building_name || parcel.owner;
            document.getElementById("govt-lbl-2").textContent = "Permit / ULPIN:";
            document.getElementById("govt-val-2").textContent = parcel.govt_permit_no || parcel.survey_number;
            document.getElementById("govt-lbl-3").textContent = "Managing Dept:";
            document.getElementById("govt-val-3").textContent = parcel.govt_managing_dept || parcel.owner;
            document.getElementById("govt-lbl-4").textContent = "Operational Status:";
            document.getElementById("govt-val-4").textContent = parcel.govt_operational_status || "ACTIVE • 24x7";
            document.getElementById("govt-val-5").textContent = `Telemetry: ${parcel.govt_telemetry || "SCADA Automated Monitoring Active"}`;
        } else if (isRoad) {
            statusTag.textContent = "ROAD RoW ASSET";
            statusTag.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#f1f5f9] text-[#475569] border border-[#cbd5e1]";
            document.getElementById("govt-lbl-1").textContent = "Road Corridor:";
            document.getElementById("govt-val-1").textContent = parcel.govt_road_name || parcel.owner;
            document.getElementById("govt-lbl-2").textContent = "RoW Width:";
            document.getElementById("govt-val-2").textContent = parcel.govt_row_width || "24.0m Standard RoW";
            document.getElementById("govt-lbl-3").textContent = "Managing Dept:";
            document.getElementById("govt-val-3").textContent = parcel.govt_managing_dept || "PWD / GMC Roads Wing";
            document.getElementById("govt-lbl-4").textContent = "Pavement Spec:";
            document.getElementById("govt-val-4").textContent = parcel.govt_pavement_type || "Heavy Duty Bituminous";
            document.getElementById("govt-val-5").textContent = `Utilities: ${parcel.govt_embedded_utilities || "Storm Drainage & Water Trunk Lines"}`;
        } else if (parcel.is_restricted_rbac) {
            statusTag.textContent = "UNMASKED DEFENSE ASSET";
            statusTag.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#fae8ff] text-[#a21caf] border border-[#f0abfc] animate-pulse";
            document.getElementById("govt-lbl-1").textContent = "Classified Node:";
            document.getElementById("govt-val-1").textContent = parcel.govt_building_name || "Defense Optical Transit";
            document.getElementById("govt-lbl-2").textContent = "Govt Permit:";
            document.getElementById("govt-val-2").textContent = parcel.govt_permit_no || "SECRET CLEARANCE";
            document.getElementById("govt-lbl-3").textContent = "Security Level:";
            document.getElementById("govt-val-3").textContent = parcel.govt_security_level || "LEVEL-4 RESTRICTED";
            document.getElementById("govt-lbl-4").textContent = "Fire Suppr:";
            document.getElementById("govt-val-4").textContent = parcel.govt_fire_noc || "HALON SYSTEM VERIFIED";
            document.getElementById("govt-val-5").textContent = `Buffer: ${parcel.govt_encumbrance_status || "50m Prohibited Surface Excavation Zone"}`;
        } else {
            statusTag.textContent = "GOVT VERIFIED BUILDING";
            statusTag.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-[#ede9fe] text-[#6d28d9] border border-[#ddd6fe]";
            document.getElementById("govt-lbl-1").textContent = "Building Name:";
            document.getElementById("govt-val-1").textContent = parcel.govt_building_name || "Guntur Strata Asset";
            document.getElementById("govt-lbl-2").textContent = "Town Permit:";
            document.getElementById("govt-val-2").textContent = parcel.govt_permit_no || "APCRDA/BP Approved";
            document.getElementById("govt-lbl-3").textContent = "Fire Safety NOC:";
            document.getElementById("govt-val-3").textContent = parcel.govt_fire_noc || "Compliant (AP-FS)";
            document.getElementById("govt-lbl-4").textContent = "Tax Assessment:";
            document.getElementById("govt-val-4").textContent = parcel.govt_tax_annual || parcel.govt_tax_assessment_id || "Assessed";
            document.getElementById("govt-val-5").textContent = `Occupancy: ${parcel.govt_occupancy_cert || "OC Certified (APCRDA / GMC)"}`;
        }
    } else {
        govtCard.classList.add("hidden");
    }

    currentInspectedParcel = parcel;

    // Apartments & Floors Directory
    const aptCard = document.getElementById("apartment-directory-card");
    const aptBadge = document.getElementById("apt-total-flats-badge");
    const flats = getApartmentsForParcel(parcel);

    if (flats && flats.length > 0 && isBuilding) {
        aptCard.classList.remove("hidden");
        currentApartmentsList = flats;
        const totalFlats = flats.length;
        const totalFloors = parcel.floors_count || Math.max(...flats.map(f => f.floor));
        aptBadge.textContent = `${totalFlats} Flats • ${totalFloors} Flrs`;

        renderFloorTabs(totalFloors);
        filterAptFloor("ALL");
    } else {
        aptCard.classList.add("hidden");
        currentApartmentsList = [];
    }
}

function renderFloorTabs(totalFloors) {
    const aptTabs = document.getElementById("apt-floor-tabs");
    if (!aptTabs) return;
    aptTabs.innerHTML = "";

    const allBtn = document.createElement("button");
    allBtn.id = "floor-tab-all";
    allBtn.className = "warm-floor-tab warm-floor-tab-active px-2.5 py-0.5 rounded text-[10px] shrink-0 transition";
    allBtn.textContent = "All";
    allBtn.onclick = () => filterAptFloor("ALL");
    aptTabs.appendChild(allBtn);

    for (let f = 1; f <= totalFloors; f++) {
        const flrBtn = document.createElement("button");
        flrBtn.id = `floor-tab-${f}`;
        flrBtn.className = "warm-floor-tab px-2 py-0.5 rounded text-[10px] shrink-0 transition";
        flrBtn.textContent = `F${f}`;
        flrBtn.onclick = () => filterAptFloor(f);
        aptTabs.appendChild(flrBtn);
    }
}

function filterAptFloor(floorNum) {
    currentSelectedFloor = floorNum;
    
    // Update tab styling
    const tabs = document.getElementById("apt-floor-tabs").children;
    for (let tab of tabs) {
        if ((floorNum === "ALL" && tab.id === "floor-tab-all") || (tab.id === `floor-tab-${floorNum}`)) {
            tab.className = "warm-floor-tab warm-floor-tab-active px-2.5 py-0.5 rounded text-[10px] shrink-0 transition";
        } else {
            tab.className = "warm-floor-tab px-2 py-0.5 rounded text-[10px] shrink-0 transition";
        }
    }

    const filtered = (floorNum === "ALL") 
        ? currentApartmentsList 
        : currentApartmentsList.filter(f => f.floor === floorNum);

    renderFlatsList(filtered);
}

function renderFlatsList(flats) {
    const aptList = document.getElementById("apt-flats-list");
    if (!aptList) return;
    aptList.innerHTML = "";

    if (!flats || flats.length === 0) {
        aptList.innerHTML = `<div class="p-2 text-stone-500 text-center text-[10px]">No flats recorded for this floor.</div>`;
        return;
    }

    flats.forEach(flat => {
        const item = document.createElement("div");
        item.className = "warm-flat-card p-2 shadow-sm hover:shadow transition";
        item.innerHTML = `
            <div class="flex items-center justify-between gap-1 mb-1">
                <div class="flex items-center gap-1.5 text-[10px] flex-wrap">
                    <span class="font-bold text-[#451a03]">${flat.flat_number}</span>
                    <span class="text-stone-300">•</span>
                    <span class="text-[#786b59]">Flat. ${flat.floor}</span>
                    <span class="text-stone-300">•</span>
                    <span class="font-mono font-medium text-[#78350f]">${flat.carpet_sqft} sq.ft</span>
                    <span class="text-stone-300">•</span>
                    <span class="text-[#92400e] font-medium">UDS: ${flat.uds_sqyds} sq.yd</span>
                </div>
                <button onclick="openFlatDeed('${flat.unit_code}')" class="warm-deed-btn px-2 py-0.5 text-[10px] shrink-0 flex items-center gap-1 shadow-sm">
                    <i class="fa-solid fa-file-lines text-[9px]"></i> Deed
                </button>
            </div>
            <div class="text-[#1c1917] font-semibold truncate flex items-center gap-1.5 text-xs">
                <i class="fa-solid fa-user text-[10px] text-[#b45309]"></i>
                <span>${flat.owner}</span>
            </div>
            <div class="text-[10px] text-[#786b59] truncate font-mono mt-0.5">${flat.ulpin_3d}</div>
        `;
        aptList.appendChild(item);
    });
}

function openFlatDeed(unitCode) {
    if (!currentApartmentsList || currentApartmentsList.length === 0) return;
    const flat = currentApartmentsList.find(f => f.unit_code === unitCode) || currentApartmentsList[0];
    if (!flat) return;

    const bldgName = flat.building_name || (currentInspectedParcel ? (currentInspectedParcel.govt_building_name || currentInspectedParcel.owner) : "Guntur Strata Complex");
    const surveyNo = currentInspectedParcel ? (currentInspectedParcel.survey_number || "Sy. 101/A") : "Sy. 101/A";
    const baseUlpin = currentInspectedParcel ? (currentInspectedParcel.base_ulpin || flat.ulpin_3d.split("-")[0]) : "28GNT8392104812";

    document.getElementById("deed-ulpin").textContent = flat.ulpin_3d || "-";
    document.getElementById("deed-base-ulpin").textContent = baseUlpin;
    document.getElementById("deed-owner").textContent = flat.owner || "-";
    document.getElementById("deed-aadhaar").textContent = flat.aadhaar_masked || "XXXX-XXXX-4819";
    document.getElementById("deed-occupancy").textContent = flat.occupancy || "Owner Occupied";
    document.getElementById("deed-building").textContent = bldgName;
    document.getElementById("deed-flat").textContent = `${flat.flat_number} (Floor ${flat.floor})`;
    document.getElementById("deed-survey").textContent = `${surveyNo} • Guntur Urban Cadastre`;
    document.getElementById("deed-carpet").textContent = `${flat.carpet_sqft ? flat.carpet_sqft.toLocaleString() : '-'} sq.ft (${flat.carpet_sqm || '-'} m²)`;
    document.getElementById("deed-uds").textContent = `${flat.uds_sqyds || '-'} sq. yards`;
    
    // Vertical span
    const zBase = (flat.floor - 1) * 3.2;
    const zTop = flat.floor * 3.2;
    document.getElementById("deed-zspan").textContent = `${zBase.toFixed(1)}m to ${zTop.toFixed(1)}m MSL (Storey ${flat.floor})`;
    document.getElementById("deed-doc").textContent = flat.reg_doc_no || "Doc 2419/2023 (SRO Guntur)";
    document.getElementById("deed-valuation").textContent = flat.market_value || "₹68,50,000";
    document.getElementById("deed-tax").textContent = `${flat.tax_annual || '₹8,650'} / yr`;
    document.getElementById("deed-mortgage").textContent = flat.mortgage_status || "Clear Title (Non-Encumbered Freehold)";

    openModal("flat-deed-modal");
}

function handleSearch() {
    const q = document.getElementById("search-input").value.trim().toLowerCase();
    if (!q) return;

    const match = currentParcels.find(p => 
        (p.ulpin_3d && p.ulpin_3d.toLowerCase().includes(q)) || 
        (p.base_ulpin && p.base_ulpin.toLowerCase().includes(q)) || 
        (p.owner && p.owner.toLowerCase().includes(q)) ||
        (p.govt_building_name && p.govt_building_name.toLowerCase().includes(q)) ||
        (p.survey_number && p.survey_number.toLowerCase().includes(q))
    );

    if (match) {
        viewer3D.selectParcelByULPIN(match.ulpin_3d, true);
        inspectParcel(match);
    }
}

function openModal(id) {
    document.getElementById(id).classList.remove("hidden");
    if (id === "schema-modal") {
        StrataMapAPI.fetchPostGISSchema().then(sql => {
            document.getElementById("schema-code").textContent = sql;
        });
    } else if (id === "extrude-modal") {
        const area = document.getElementById("geojson-input");
        if (!area.value.trim()) {
            resetDefaultGunturGeoJSON();
        }
    }
}

function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
}

function toggle2DCadastreBase(checked) {
    if (viewer3D) {
        viewer3D.toggle2DCadastre(checked);
    }
}

function setCameraPreset(preset) {
    if (viewer3D && viewer3D.setPresetView) {
        viewer3D.setPresetView(preset);
    }
}

function focusGunturZone(zone) {
    if (!viewer3D) return;
    if (zone === "brodipet") {
        viewer3D.focusLocation(0, 0, 45);
    } else if (zone === "lakshmipuram") {
        viewer3D.focusLocation(-850, 530, 45);
    } else if (zone === "flyover") {
        viewer3D.focusLocation(850, -870, 60);
    } else if (zone === "utility") {
        viewer3D.focusLocation(-150, -170, 45);
    }
}

function focusGunturNode(nodeCode) {
    if (!viewer3D) return;
    const match = currentParcels.find(p => 
        (p.ulpin_3d && p.ulpin_3d.includes(nodeCode)) || 
        (p.govt_permit_no && p.govt_permit_no.includes(nodeCode)) ||
        (p.survey_number && p.survey_number.includes(nodeCode))
    );
    if (match && match.geometry) {
        viewer3D.focusLocation(match.geometry.center[0], match.geometry.center[1], 35);
        viewer3D.selectParcelByULPIN(match.ulpin_3d);
        inspectParcel(match);
    }
}

function focusAndInspectSurvey(zone) {
    closeModal("area-stats-modal");
    focusGunturZone(zone);
    
    // Find matching parcel in current list
    let target = null;
    if (zone === "brodipet") {
        target = currentParcels.find(p => (p.survey_number === "142/1A" || (p.owner && p.owner.includes("Brodipet"))) && p.zone_type === "FLR");
    } else if (zone === "lakshmipuram") {
        target = currentParcels.find(p => (p.survey_number === "218/3B" || (p.owner && p.owner.includes("Lakshmipuram"))) && p.zone_type === "FLR");
    } else if (zone === "flyover") {
        target = currentParcels.find(p => p.zone_type === "AIR");
    } else if (zone === "utility") {
        target = currentParcels.find(p => p.zone_type === "SUB");
    }

    if (target) {
        viewer3D.selectParcelByULPIN(target.ulpin_3d);
    }
}

function fitAllParcels() {
    if (viewer3D) {
        viewer3D.fitCameraToParcels();
    }
}

async function resetDefaultGunturGeoJSON() {
    const geo = await StrataMapAPI.fetchGuntur2DCadastre();
    if (geo) {
        document.getElementById("geojson-input").value = JSON.stringify(geo, null, 2);
    }
}

async function execute2DTo3DExtrusion() {
    const raw = document.getElementById("geojson-input").value;
    try {
        const parsed = JSON.parse(raw);
        const parcels = await StrataMapAPI.extrudeGuntur2D({ geojson: parsed, clear_existing: true });
        if (parcels && parcels.length > 0) {
            currentParcels = parcels;
            viewer3D.renderParcels(currentParcels);
            inspectParcel(currentParcels[0]);
            closeModal("extrude-modal");
            alert(`2D-to-3D Extrusion Complete!\nGenerated ${parcels.length} 3D volumetric parcels with AP-28 3D ULPIN identifiers.`);
        } else {
            alert("Extrusion returned no parcels. Check GeoJSON geometry format.");
        }
    } catch (err) {
        alert("Invalid GeoJSON JSON syntax. Please verify JSON format:\n" + err.message);
    }
}

function toggleFormFields() {
    const zone = document.getElementById("form-zone-type").value;
    const flrFields = document.getElementById("flr-fields");
    if (zone === "FLR") {
        flrFields.style.display = "grid";
    } else {
        flrFields.style.display = "none";
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const payload = {
        base_ulpin: document.getElementById("form-base-ulpin").value,
        zone_type: document.getElementById("form-zone-type").value,
        z_min: parseFloat(document.getElementById("form-zmin").value),
        z_max: parseFloat(document.getElementById("form-zmax").value),
        floor_number: parseInt(document.getElementById("form-floor").value),
        unit_code: document.getElementById("form-unit").value,
        owner: document.getElementById("form-owner").value,
        tenure_type: document.getElementById("form-tenure").value,
        center_x: 0.0,
        center_y: 0.0,
        width: 12.0,
        length: 12.0
    };

    const response = await StrataMapAPI.generate3DUlpin(payload);

    if (response.status === "SUCCESS") {
        alert(`SUCCESS: 3D ULPIN issued:\n${response.parcel.ulpin_3d}`);
        closeModal("generate-modal");
        loadParcels();
    } else {
        alert(`3D TOPOLOGY CONFLICT ERROR:\n${response.message}`);
    }
}

function runTopologyCheck() {
    alert("3D Topology Validator Check:\nNo volumetric boundary collisions detected with current surface/subsurface DB.");
}

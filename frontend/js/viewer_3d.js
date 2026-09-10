/**
 * StrataMap: WebGL 3D Cadastral Map Visualizer
 * Built with Three.js engine for rendering 3D volumetric parcels.
 */

class Viewer3D {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0f1d); // Sleek Cartographic Cadastre Sky
        this.scene.fog = new THREE.Fog(0x0a0f1d, 800, 3200); // Ambient atmospheric horizon depth
        this.satelliteMode = false; // Pure 3D Cadastral Map mode without satellite overlay

        const initialW = (this.container && this.container.clientWidth > 0) ? this.container.clientWidth : window.innerWidth;
        const initialH = (this.container && this.container.clientHeight > 0) ? this.container.clientHeight : Math.max(window.innerHeight - 56, 400);

        // Camera Setup (Natural isometric aerial angle looking into city center)
        this.camera = new THREE.PerspectiveCamera(
            42,
            initialW / initialH,
            0.1,
            16000
        );
        this.camera.position.set(190, 155, 230);

        // WebGL Renderer - High Performance & sRGB Color Accuracy
        this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
        this.renderer.setSize(initialW, initialH);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        if (THREE.sRGBEncoding) {
            this.renderer.outputEncoding = THREE.sRGBEncoding;
        }
        this.renderer.shadowMap.enabled = false;
        
        // Canvas Element Styles
        this.renderer.domElement.style.width = "100%";
        this.renderer.domElement.style.height = "100%";
        this.renderer.domElement.style.display = "block";
        this.renderer.domElement.style.touchAction = "none";
        this.renderer.domElement.style.cursor = "grab";
        this.container.appendChild(this.renderer.domElement);

        // Orbit Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.08;
        this.controls.target.set(0, 15, 0);
        this.controls.maxPolarAngle = Math.PI / 2 - 0.02; // Prevent camera clipping below ground plane
        this.controls.minDistance = 5;
        this.controls.maxDistance = 4500;
        this.controls.screenSpacePanning = true;
        this.controls.rotateSpeed = 0.85;
        this.controls.panSpeed = 0.95;
        this.controls.zoomSpeed = 1.1;

        // Lighting - High-Contrast Natural Sunlight for 3D Cadastral Visualization
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xfff3db, 1.25);
        dirLight.position.set(160, 240, 120);
        this.scene.add(dirLight);

        const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.50);
        fillLight.position.set(-140, 160, -110);
        this.scene.add(fillLight);

        // Grid Helpers
        // Surface Grid (Z=0)
        this.gridSurface = new THREE.GridHelper(120, 30, 0x10b981, 0x1e293b);
        this.gridSurface.position.y = 0;
        this.gridSurface.visible = true;
        this.scene.add(this.gridSurface);

        // Subsurface Depth Grid (Z=-20m)
        this.gridSubsurface = new THREE.GridHelper(120, 30, 0xef4444, 0x0f172a);
        this.gridSubsurface.position.y = -20;
        this.gridSubsurface.visible = true;
        this.scene.add(this.gridSubsurface);

        // 2D Guntur Cadastral Base Map Ground Overlay (Vector Cartographic Mode)
        this.initCadastralGroundOverlay();

        // Storage for parcel meshes & Material Caches
        this.parcelMeshes = [];
        this.selectedMesh = null;
        this.explosionFactor = 1.0;
        this.layerVisibility = { SUR: true, FLR: true, AIR: true, SUB: true, ROAD: true, NODE: true, INFRA: true, RAIL: true };
        this.materialCache = new Map();
        this.edgeMaterialCache = new Map();
        this.activeDetailGroup = null;

        // Raycaster for mouse and touch selection
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        this.initEvents();
        this.animate();
    }

    toggleSatelliteMode(enableSatellite) {
        // Satellite mode removed as requested
        this.satelliteMode = false;
        if (this.cadastralPlane) {
            this.cadastralPlane.visible = true;
        }
        if (this.gridSurface) {
            this.gridSurface.visible = true;
        }
        if (this.gridSubsurface) {
            this.gridSubsurface.visible = true;
        }
        return false;
    }

    initCadastralGroundOverlay() {
        const canvas = document.createElement("canvas");
        canvas.width = 2048;
        canvas.height = 2048;
        const ctx = canvas.getContext("2d");

        // Deep Slate Cartographic Ground
        ctx.fillStyle = "#030712";
        ctx.fillRect(0, 0, 2048, 2048);

        // Subgrid background
        ctx.strokeStyle = "rgba(30, 41, 59, 0.4)";
        ctx.lineWidth = 1;
        const fineStep = 32;
        for (let x = 0; x <= 2048; x += fineStep) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 2048); ctx.stroke();
        }
        for (let y = 0; y <= 2048; y += fineStep) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(2048, y); ctx.stroke();
        }

        // =========================================================================
        // LAYER 3: 10x7 CADASTRAL SURVEY GRID & PARTITION CUTS (MATCHING IMAGE 3)
        // =========================================================================
        const gridX0 = 100;
        const gridY0 = 140;
        const gridW = 1848;
        const gridH = 1780;
        const numCols = 10;
        const numRows = 7;
        const colW = gridW / numCols; // 184.8 px
        const rowH = gridH / numRows; // 254.28 px

        // Draw 10x7 Grid Cells
        ctx.strokeStyle = "rgba(100, 116, 139, 0.75)";
        ctx.lineWidth = 2.0;

        for (let c = 0; c <= numCols; c++) {
            const x = gridX0 + c * colW;
            ctx.beginPath();
            ctx.moveTo(x, gridY0);
            ctx.lineTo(x, gridY0 + gridH);
            ctx.stroke();
        }

        for (let r = 0; r <= numRows; r++) {
            const y = gridY0 + r * rowH;
            ctx.beginPath();
            ctx.moveTo(gridX0, y);
            ctx.lineTo(gridX0 + gridW, y);
            ctx.stroke();
        }

        // Grid Cell Survey Division Marks / Partition Slits (Exact matching Image 3)
        ctx.strokeStyle = "rgba(226, 232, 240, 0.9)";
        ctx.lineWidth = 2.5;

        // [Col 1, Row 0]: Top-left L-bracket & vertical partition cut
        ctx.beginPath();
        ctx.moveTo(gridX0 + 1 * colW + 45, gridY0 + 0 * rowH + 60);
        ctx.lineTo(gridX0 + 1 * colW + 145, gridY0 + 0 * rowH + 60);
        ctx.moveTo(gridX0 + 1 * colW + 45, gridY0 + 0 * rowH + 60);
        ctx.lineTo(gridX0 + 1 * colW + 48, gridY0 + 0 * rowH + 160);
        ctx.stroke();

        // [Col 3, Row 0]: Cross-partition and slash cuts
        ctx.beginPath();
        ctx.moveTo(gridX0 + 2 * colW + 150, gridY0 + 0 * rowH + 115);
        ctx.lineTo(gridX0 + 3 * colW + 70, gridY0 + 0 * rowH + 115);
        ctx.moveTo(gridX0 + 3 * colW + 65, gridY0 + 0 * rowH + 40);
        ctx.lineTo(gridX0 + 3 * colW + 65, gridY0 + 0 * rowH + 170);
        ctx.moveTo(gridX0 + 3 * colW + 110, gridY0 + 0 * rowH + 80);
        ctx.lineTo(gridX0 + 3 * colW + 110, gridY0 + 0 * rowH + 160);
        // Small diagonal in Col 3, Row 0
        ctx.moveTo(gridX0 + 3 * colW + 15, gridY0 + 0 * rowH + 195);
        ctx.lineTo(gridX0 + 3 * colW + 65, gridY0 + 0 * rowH + 165);
        ctx.stroke();

        // [Col 6, Row 1]: Diagonal partition line
        ctx.beginPath();
        ctx.moveTo(gridX0 + 6 * colW + 125, gridY0 + 1 * rowH + 50);
        ctx.lineTo(gridX0 + 7 * colW + 35, gridY0 + 1 * rowH + 125);
        ctx.stroke();

        // [Col 9, Row 0]: Top right diagonal tick
        ctx.beginPath();
        ctx.moveTo(gridX0 + 9 * colW + 130, gridY0 + 0 * rowH + 45);
        ctx.lineTo(gridX0 + 9 * colW + 155, gridY0 + 0 * rowH + 90);
        ctx.stroke();

        // [Col 0, Row 4]: Left diagonal tick
        ctx.beginPath();
        ctx.moveTo(gridX0 + 0 * colW + 55, gridY0 + 4 * rowH + 185);
        ctx.lineTo(gridX0 + 0 * colW + 85, gridY0 + 4 * rowH + 215);
        ctx.stroke();

        // [Col 3, Row 4]: Long diagonal cross-partition
        ctx.beginPath();
        ctx.moveTo(gridX0 + 3 * colW + 130, gridY0 + 4 * rowH + 50);
        ctx.lineTo(gridX0 + 4 * colW + 45, gridY0 + 4 * rowH + 195);
        ctx.stroke();

        // [Col 5, Row 6]: Bottom diagonal slash & vertical cut
        ctx.beginPath();
        ctx.moveTo(gridX0 + 5 * colW + 120, gridY0 + 6 * rowH + 65);
        ctx.lineTo(gridX0 + 6 * colW + 30, gridY0 + 6 * rowH + 30);
        ctx.moveTo(gridX0 + 5 * colW + 20, gridY0 + 6 * rowH + 110);
        ctx.lineTo(gridX0 + 5 * colW + 25, gridY0 + 6 * rowH + 225);
        ctx.stroke();

        // [Col 6, Row 5]: Horizontal partition cut
        ctx.beginPath();
        ctx.moveTo(gridX0 + 6 * colW + 150, gridY0 + 5 * rowH + 210);
        ctx.lineTo(gridX0 + 7 * colW + 90, gridY0 + 5 * rowH + 230);
        ctx.stroke();

        // [Col 9, Row 5]: Lower right corner diagonal cut
        ctx.beginPath();
        ctx.moveTo(gridX0 + 9 * colW + 95, gridY0 + 5 * rowH + 250);
        ctx.lineTo(gridX0 + 9 * colW + 165, gridY0 + 5 * rowH + 200);
        ctx.stroke();

        // [Col 1, Row 6]: Bottom left diagonal cut
        ctx.beginPath();
        ctx.moveTo(gridX0 + 0 * colW + 175, gridY0 + 6 * rowH + 245);
        ctx.lineTo(gridX0 + 1 * colW + 85, gridY0 + 6 * rowH + 145);
        ctx.stroke();

        // Cadastral Ward Watermarks (Col A..J, Row 1..7)
        ctx.font = "bold 13px monospace";
        ctx.fillStyle = "rgba(148, 163, 184, 0.28)";
        const colLetters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
        for (let r = 0; r < numRows; r++) {
            for (let c = 0; c < numCols; c++) {
                const cx = gridX0 + c * colW + 10;
                const cy = gridY0 + r * rowH + 24;
                ctx.fillText(`WARD-${colLetters[c]}${r + 1}`, cx, cy);
            }
        }

        // =========================================================================
        // LAYER 1: DENSE BUILDING ENVELOPE FOOTPRINTS SCATTER (MATCHING IMAGE 1)
        // =========================================================================
        // Seeded deterministic scatter of building plots across the wards
        let seed = 42;
        function pseudoRandom() {
            seed = (seed * 9301 + 49297) % 233280;
            return seed / 233280;
        }

        ctx.fillStyle = "rgba(203, 213, 225, 0.85)";
        for (let i = 0; i < 520; i++) {
            const bx = gridX0 + pseudoRandom() * (gridW - 40) + 20;
            const by = gridY0 + pseudoRandom() * (gridH - 40) + 20;
            const bw = 3 + Math.floor(pseudoRandom() * 6);
            const bh = 3 + Math.floor(pseudoRandom() * 6);
            ctx.fillRect(bx, by, bw, bh);
            if (i % 6 === 0) {
                ctx.strokeStyle = "rgba(56, 189, 248, 0.5)";
                ctx.lineWidth = 1;
                ctx.strokeRect(bx - 1, by - 1, bw + 2, bh + 2);
            }
        }

        // =========================================================================
        // LAYER 2: ARTERIAL ROAD NETWORK & CIRCULAR INFRASTRUCTURE NODES (IMAGE 2)
        // =========================================================================
        // Arterial Road 1: North-South Highway Corridor
        ctx.lineCap = "round";
        ctx.lineJoin = "round";

        // Outer Casing
        ctx.strokeStyle = "rgba(15, 23, 42, 0.95)";
        ctx.lineWidth = 18;
        ctx.beginPath();
        ctx.moveTo(gridX0 + 720, gridY0 - 40);
        ctx.lineTo(gridX0 + 770, gridY0 + 350);
        ctx.lineTo(gridX0 + 810, gridY0 + 640);
        ctx.lineTo(gridX0 + 670, gridY0 + 1280);
        ctx.lineTo(gridX0 + 750, gridY0 + gridH + 40);
        ctx.stroke();

        // Asphalt Bed
        ctx.strokeStyle = "#334155";
        ctx.lineWidth = 10;
        ctx.stroke();

        // Centerline
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 2.5;
        ctx.setLineDash([14, 8]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Arterial Road 2: East-West Arterial Corridor
        ctx.strokeStyle = "rgba(15, 23, 42, 0.95)";
        ctx.lineWidth = 18;
        ctx.beginPath();
        ctx.moveTo(gridX0 - 40, gridY0 + 1280);
        ctx.lineTo(gridX0 + 520, gridY0 + 1230);
        ctx.lineTo(gridX0 + 1080, gridY0 + 1320);
        ctx.lineTo(gridX0 + 1440, gridY0 + 1280);
        ctx.lineTo(gridX0 + gridW + 40, gridY0 + 1210);
        ctx.stroke();

        ctx.strokeStyle = "#334155";
        ctx.lineWidth = 10;
        ctx.stroke();

        ctx.strokeStyle = "#10b981";
        ctx.lineWidth = 2.5;
        ctx.setLineDash([14, 8]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Arterial Road 3: Diagonal Flyover & Outer Viaduct Corridor
        ctx.strokeStyle = "rgba(15, 23, 42, 0.95)";
        ctx.lineWidth = 16;
        ctx.beginPath();
        ctx.moveTo(gridX0 + 840, gridY0 + 1580);
        ctx.lineTo(gridX0 + 1720, gridY0 + 920);
        ctx.stroke();

        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 9;
        ctx.stroke();

        ctx.strokeStyle = "#f59e0b";
        ctx.lineWidth = 2.5;
        ctx.setLineDash([10, 6]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Circular Infrastructure Nodes (exact matching Image 2 circular hubs)
        const infraCircles = [
            { x: gridX0 + 790, y: gridY0 + 640, r: 12, label: "Metro Terminal (Node 1)", color: "#38bdf8" },
            { x: gridX0 + 770, y: gridY0 + 550, r: 11, label: "132kV Substation (Node 2)", color: "#facc15" },
            { x: gridX0 + 805, y: gridY0 + 575, r: 9, label: "", color: "#facc15" },
            { x: gridX0 + 800, y: gridY0 + 910, r: 11, label: "Water Works 5MLD (Node 3)", color: "#06b6d4" },
            { x: gridX0 + 830, y: gridY0 + 990, r: 10, label: "5G Fiber Tower (Node 4)", color: "#a855f7" },
            { x: gridX0 + 710, y: gridY0 + 1180, r: 11, label: "City Gas DRS (Node 5)", color: "#f97316" },
            { x: gridX0 + 695, y: gridY0 + 1240, r: 10, label: "Hospital Helipad (Node 6)", color: "#ec4899" },
            { x: gridX0 + 990, y: gridY0 + 1305, r: 12, label: "Smart City ICCC (Node 7)", color: "#10b981" },
            { x: gridX0 + 1045, y: gridY0 + 1315, r: 10, label: "Fire Headquarters (Node 9)", color: "#ef4444" },
            { x: gridX0 + 1180, y: gridY0 + 1300, r: 10, label: "", color: "#38bdf8" },
            { x: gridX0 + 1350, y: gridY0 + 1285, r: 11, label: "Lakshmipuram Substation (Node 8)", color: "#facc15" },
            { x: gridX0 + 1440, y: gridY0 + 1275, r: 9, label: "", color: "#38bdf8" },
            { x: gridX0 + 1250, y: gridY0 + 1260, r: 9, label: "", color: "#06b6d4" },
            { x: gridX0 + 910, y: gridY0 + 1530, r: 10, label: "", color: "#f59e0b" },
            { x: gridX0 + 1160, y: gridY0 + 1345, r: 11, label: "Viaduct Interchange", color: "#f59e0b" },
            { x: gridX0 + 1430, y: gridY0 + 1140, r: 10, label: "", color: "#f59e0b" },
            { x: gridX0 + 1680, y: gridY0 + 950, r: 11, label: "Outer Ring Toll Junction", color: "#f59e0b" },
            { x: gridX0 + 420, y: gridY0 + 480, r: 10, label: "", color: "#38bdf8" },
            { x: gridX0 + 510, y: gridY0 + 495, r: 9, label: "", color: "#a855f7" },
            { x: gridX0 + 380, y: gridY0 + 930, r: 10, label: "", color: "#38bdf8" },
            { x: gridX0 + 470, y: gridY0 + 1080, r: 9, label: "", color: "#10b981" },
            { x: gridX0 + 570, y: gridY0 + 1020, r: 9, label: "", color: "#06b6d4" },
            { x: gridX0 + 1020, y: gridY0 + 380, r: 10, label: "", color: "#facc15" },
            { x: gridX0 + 1180, y: gridY0 + 480, r: 10, label: "", color: "#38bdf8" },
            { x: gridX0 + 1260, y: gridY0 + 510, r: 9, label: "", color: "#a855f7" },
            { x: gridX0 + 1420, y: gridY0 + 540, r: 10, label: "", color: "#06b6d4" },
            { x: gridX0 + 1720, y: gridY0 + 520, r: 10, label: "", color: "#38bdf8" },
            { x: gridX0 + 1760, y: gridY0 + 560, r: 9, label: "", color: "#facc15" },
            { x: gridX0 + 1770, y: gridY0 + 800, r: 10, label: "", color: "#38bdf8" },
            { x: gridX0 + 1800, y: gridY0 + 870, r: 9, label: "", color: "#10b981" },
            { x: gridX0 + 1600, y: gridY0 + 680, r: 10, label: "", color: "#a855f7" },
            { x: gridX0 + 1150, y: gridY0 + 800, r: 10, label: "", color: "#06b6d4" },
            { x: gridX0 + 1260, y: gridY0 + 930, r: 10, label: "", color: "#f97316" },
            { x: gridX0 + 1400, y: gridY0 + 980, r: 9, label: "", color: "#38bdf8" },
            { x: gridX0 + 1580, y: gridY0 + 1080, r: 10, label: "", color: "#ef4444" },
            { x: gridX0 + 880, y: gridY0 + 1440, r: 9, label: "", color: "#38bdf8" },
            { x: gridX0 + 930, y: gridY0 + 1445, r: 9, label: "", color: "#facc15" },
            { x: gridX0 + 920, y: gridY0 + 1520, r: 9, label: "", color: "#06b6d4" },
            { x: gridX0 + 950, y: gridY0 + 1580, r: 9, label: "", color: "#a855f7" },
            { x: gridX0 + 1040, y: gridY0 + 1530, r: 9, label: "", color: "#38bdf8" },
            { x: gridX0 + 1130, y: gridY0 + 1620, r: 10, label: "", color: "#10b981" },
            { x: gridX0 + 1340, y: gridY0 + 1580, r: 10, label: "", color: "#38bdf8" },
            { x: gridX0 + 1300, y: gridY0 + 1710, r: 9, label: "", color: "#facc15" },
            { x: gridX0 + 970, y: gridY0 + 1890, r: 10, label: "", color: "#06b6d4" }
        ];

        infraCircles.forEach(node => {
            // Pulse Halo
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.r + 5, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(56, 189, 248, 0.25)";
            ctx.lineWidth = 2;
            ctx.stroke();

            // Outer Ring
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(15, 23, 42, 0.95)";
            ctx.fill();
            ctx.strokeStyle = node.color;
            ctx.lineWidth = 2.5;
            ctx.stroke();

            // Inner Core Dot
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.r * 0.45, 0, Math.PI * 2);
            ctx.fillStyle = node.color;
            ctx.fill();

            // Label if present
            if (node.label) {
                ctx.font = "bold 13px sans-serif";
                ctx.fillStyle = "#f8fafc";
                ctx.fillText(node.label, node.x + node.r + 6, node.y + 4);
            }
        });

        // =========================================================================
        // CARTOGRAPHIC HEADERS, METADATA & NORTH ARROW
        // =========================================================================
        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold 26px monospace";
        ctx.fillText("AP CADASTRAL SURVEY & SETTLEMENTS • GUNTUR URBAN MANDAL (MANDAL 28-GNT)", 100, 60);

        ctx.font = "16px monospace";
        ctx.fillStyle = "#94a3b8";
        ctx.fillText("INTEGRATED: LAYER 1 (BUILDINGS) • LAYER 2 (ARTERIAL CORRIDORS & NODES) • LAYER 3 (10x7 SURVEY GRID)", 100, 90);
        ctx.fillText("DATUM: WGS-84 / UTM ZONE 44N (EPSG:4979) • GUNTUR ORIGIN: 16.3067° N, 80.4365° E", 100, 114);

        // Column Labels across top (A - J)
        ctx.font = "bold 18px monospace";
        ctx.fillStyle = "#38bdf8";
        for (let c = 0; c < numCols; c++) {
            ctx.fillText(colLetters[c], gridX0 + c * colW + colW / 2 - 6, gridY0 - 12);
        }
        // Row Numbers down left (1 - 7)
        for (let r = 0; r < numRows; r++) {
            ctx.fillText(`${r + 1}`, gridX0 - 32, gridY0 + r * rowH + rowH / 2 + 6);
        }

        // North Arrow
        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(1940, 110);
        ctx.lineTo(1940, 50);
        ctx.lineTo(1930, 65);
        ctx.moveTo(1940, 50);
        ctx.lineTo(1950, 65);
        ctx.stroke();
        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold 20px sans-serif";
        ctx.fillText("N", 1934, 40);

        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.ClampToEdgeWrapping;
        texture.wrapT = THREE.ClampToEdgeWrapping;

        const planeGeo = new THREE.PlaneGeometry(2200, 2200);
        const planeMat = new THREE.MeshBasicMaterial({
            map: texture,
            transparent: true,
            opacity: 0.90,
            depthWrite: false
        });

        this.cadastralPlane = new THREE.Mesh(planeGeo, planeMat);
        this.cadastralPlane.rotation.x = -Math.PI / 2;
        this.cadastralPlane.position.y = -0.05;
        this.scene.add(this.cadastralPlane);
    }

    toggle2DCadastre(show) {
        if (this.cadastralPlane) {
            this.cadastralPlane.visible = show;
        }
    }

    initEvents() {
        window.addEventListener("resize", () => this.onWindowResize());

        const domEl = this.renderer.domElement;
        this.pointerDownPos = null;
        this.pointerDownTime = 0;
        this.lastSelectedTime = 0;

        const getCoords = (e) => {
            if (e.changedTouches && e.changedTouches.length > 0) {
                return { x: e.changedTouches[0].clientX, y: e.changedTouches[0].clientY };
            }
            if (e.touches && e.touches.length > 0) {
                return { x: e.touches[0].clientX, y: e.touches[0].clientY };
            }
            if (typeof e.clientX === "number") {
                return { x: e.clientX, y: e.clientY };
            }
            return { x: 0, y: 0 };
        };

        // Cancel camera animation if user manually moves map
        this.controls.addEventListener("start", () => {
            this.cameraAnim = null;
            domEl.style.cursor = "grabbing";
        });

        this.controls.addEventListener("end", () => {
            domEl.style.cursor = "grab";
        });

        // Pointerdown / Touchstart
        const onDown = (e) => {
            this.cameraAnim = null;
            const c = getCoords(e);
            this.pointerDownPos = c;
            this.pointerDownTime = performance.now();
        };

        domEl.addEventListener("pointerdown", onDown);
        domEl.addEventListener("touchstart", onDown, { passive: true });

        // Pointerup / Touchend (Primary touch/click gesture detection)
        const onUp = (e) => {
            if (!this.pointerDownPos) return;
            const c = getCoords(e);
            const dx = c.x - this.pointerDownPos.x;
            const dy = c.y - this.pointerDownPos.y;
            const dist = Math.hypot(dx, dy);
            const elapsed = performance.now() - this.pointerDownTime;
            this.pointerDownPos = null;

            const isTouch = (e.pointerType === "touch") || (e.type && e.type.startsWith("touch")) || (window.matchMedia && window.matchMedia("(pointer: coarse)").matches);
            const maxDist = isTouch ? 28 : 10;
            const maxTime = isTouch ? 700 : 450;
            const isLeftOrTouch = (e.button === 0 || e.button === -1 || e.button === undefined || isTouch);

            if (isLeftOrTouch && dist <= maxDist && elapsed <= maxTime) {
                this.handleCanvasClickAt(c.x, c.y, true);
            }
        };

        domEl.addEventListener("pointerup", onUp);
        domEl.addEventListener("touchend", onUp, { passive: true });

        // Standard native click fallback (with debounce against pointerup)
        domEl.addEventListener("click", (e) => {
            if (e.button === 0) {
                const now = performance.now();
                if (now - this.lastSelectedTime > 250) {
                    this.handleCanvasClickAt(e.clientX, e.clientY, true);
                }
            }
        });

        // Hover cursor feedback (for mouse pointers)
        domEl.addEventListener("pointermove", (e) => {
            if (this.pointerDownPos) return; // currently dragging/orbiting
            if (e.pointerType === "mouse" || !e.pointerType) {
                this.handlePointerHover(e);
            }
        });

        // Wheel interrupt
        domEl.addEventListener("wheel", () => {
            this.cameraAnim = null;
        }, { passive: true });
    }

    handlePointerHover(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const visibleMeshes = this.parcelMeshes.filter(p => p.mesh && p.mesh.visible).map(p => p.mesh);
        const intersects = this.raycaster.intersectObjects(visibleMeshes, true);

        if (intersects.length > 0) {
            const match = this.getParcelFromIntersect(intersects[0].object);
            if (match) {
                this.renderer.domElement.style.cursor = "pointer";
                return;
            }
        }
        this.renderer.domElement.style.cursor = "grab";
    }

    handleCanvasClick(event) {
        if (!event) return;
        const clientX = event.clientX !== undefined ? event.clientX : (event.changedTouches && event.changedTouches[0] ? event.changedTouches[0].clientX : (event.touches && event.touches[0] ? event.touches[0].clientX : 0));
        const clientY = event.clientY !== undefined ? event.clientY : (event.changedTouches && event.changedTouches[0] ? event.changedTouches[0].clientY : (event.touches && event.touches[0] ? event.touches[0].clientY : 0));
        this.handleCanvasClickAt(clientX, clientY, true);
    }

    handleCanvasClickAt(clientX, clientY, autoFly = true) {
        if (clientX === undefined || clientY === undefined) return;
        const rect = this.renderer.domElement.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;

        this.mouse.x = ((clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const visibleMeshes = this.parcelMeshes.filter(p => p.mesh && p.mesh.visible).map(p => p.mesh);
        const intersects = this.raycaster.intersectObjects(visibleMeshes, true);

        if (intersects.length > 0) {
            for (let i = 0; i < intersects.length; i++) {
                const match = this.getParcelFromIntersect(intersects[i].object);
                if (match) {
                    this.lastSelectedTime = performance.now();
                    this.highlightParcel(match.mesh);
                    if (autoFly && match.parcel) {
                        this.flyToParcel(match.parcel, 60);
                    }
                    if (window.onParcelSelected) {
                        window.onParcelSelected(match.parcel);
                    }
                    break;
                }
            }
        }
    }

    onWindowResize() {
        if (!this.container) return;
        const w = this.container.clientWidth || window.innerWidth;
        const h = this.container.clientHeight || Math.max(window.innerHeight - 56, 400);
        if (w === 0 || h === 0) return;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }

    animateCameraTo(targetPos, targetLookAt, duration = 750) {
        this.cameraAnim = {
            startPos: this.camera.position.clone(),
            endPos: targetPos.clone(),
            startTarget: this.controls.target.clone(),
            endTarget: targetLookAt.clone(),
            startTime: performance.now(),
            duration: duration
        };
    }

    flyToParcel(parcel, radius = 65) {
        if (!parcel || !parcel.geometry) return;
        const cx = parcel.geometry.center[0];
        const cz = parcel.geometry.center[1];
        const cy = Math.max(12, (parcel.geometry.z_min + parcel.geometry.z_max) / 2);

        const targetPos = new THREE.Vector3(cx + radius * 0.9, cy + radius * 0.75, cz + radius * 0.95);
        const targetLookAt = new THREE.Vector3(cx, cy, cz);
        this.animateCameraTo(targetPos, targetLookAt, 700);
    }

    fitCameraToParcels() {
        if (!this.parcelMeshes || this.parcelMeshes.length === 0) return;
        
        const box = new THREE.Box3();
        let validMeshCount = 0;
        this.parcelMeshes.forEach(item => {
            if (item.mesh && item.mesh.visible) {
                // Focus primarily on buildings and surface parcels, not outer ring expressways
                if (item.parcel.zone_type === "FLR" || item.parcel.is_building) {
                    box.expandByObject(item.mesh);
                    validMeshCount++;
                }
            }
        });

        if (validMeshCount === 0) {
            this.parcelMeshes.forEach(item => {
                if (item.mesh && item.mesh.visible) {
                    box.expandByObject(item.mesh);
                    validMeshCount++;
                }
            });
        }

        if (validMeshCount === 0) return;

        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        // Clamp maximum framing distance so buildings remain crisp and substantial
        const maxDim = Math.min(Math.max(size.x, size.z, 150), 550);

        const targetLookAt = new THREE.Vector3(center.x, 15, center.z);
        const targetPos = new THREE.Vector3(
            center.x + maxDim * 0.82,
            Math.max(maxDim * 0.65, 140),
            center.z + maxDim * 0.92
        );
        this.animateCameraTo(targetPos, targetLookAt, 850);
    }

    focusLocation(x, z, radius = 60) {
        const targetPos = new THREE.Vector3(x + radius * 0.9, radius * 0.75, z + radius * 0.95);
        const targetLookAt = new THREE.Vector3(x, 15, z);
        this.animateCameraTo(targetPos, targetLookAt, 700);
    }

    setPresetView(preset) {
        switch (preset) {
            case "balaji":
                this.animateCameraTo(new THREE.Vector3(65, 50, 75), new THREE.Vector3(0, 14, 0), 750);
                break;
            case "isometric":
                this.animateCameraTo(new THREE.Vector3(190, 155, 230), new THREE.Vector3(0, 15, 0), 750);
                break;
            case "topdown":
                this.animateCameraTo(new THREE.Vector3(0, 320, 1), new THREE.Vector3(0, 0, 0), 800);
                break;
            case "city":
                this.fitCameraToParcels();
                break;
            default:
                this.animateCameraTo(new THREE.Vector3(190, 155, 230), new THREE.Vector3(0, 15, 0), 750);
        }
    }

    getMaterial(colorHex, opacity = 0.94, roughness = 0.68, metalness = 0.05) {
        const key = `${colorHex}_${opacity}_${roughness}_${metalness}`;
        if (!this.materialCache.has(key)) {
            const mat = new THREE.MeshStandardMaterial({
                color: new THREE.Color(colorHex),
                transparent: opacity < 1.0,
                opacity: opacity,
                roughness: roughness,
                metalness: metalness
            });
            mat.userData = { is_cached: true };
            this.materialCache.set(key, mat);
        }
        return this.materialCache.get(key);
    }

    getEdgeMaterial(colorHex = 0x334155, linewidth = 1.0, opacity = 0.4) {
        const key = `${colorHex}_${linewidth}_${opacity}`;
        if (!this.edgeMaterialCache.has(key)) {
            const mat = new THREE.LineBasicMaterial({
                color: colorHex,
                linewidth: linewidth,
                transparent: opacity < 1.0,
                opacity: opacity
            });
            mat.userData = { is_cached: true };
            this.edgeMaterialCache.set(key, mat);
        }
        return this.edgeMaterialCache.get(key);
    }

    clearParcels() {
        if (this.activeDetailGroup) {
            if (this.activeDetailGroup.parent) {
                this.activeDetailGroup.parent.remove(this.activeDetailGroup);
            }
            this.disposeHierarchy(this.activeDetailGroup);
            this.activeDetailGroup = null;
        }
        if (this.selectedMesh && this.selectedMesh._origMaterial) {
            this.selectedMesh.material = this.selectedMesh._origMaterial;
            this.selectedMesh._origMaterial = null;
        }
        this.selectedMesh = null;

        this.parcelMeshes.forEach(item => {
            this.disposeHierarchy(item.mesh);
            if (item.edges && item.edges !== item.mesh) {
                this.disposeHierarchy(item.edges);
            }
        });
        this.parcelMeshes = [];
    }

    disposeHierarchy(obj) {
        if (!obj) return;
        if (obj.parent) {
            obj.parent.remove(obj);
        } else {
            this.scene.remove(obj);
        }
        if (obj.geometry) {
            obj.geometry.dispose();
        }
        if (obj.material && !obj.material.userData?.is_cached) {
            if (Array.isArray(obj.material)) {
                obj.material.forEach(m => m.dispose());
            } else {
                obj.material.dispose();
            }
        }
        while (obj.children && obj.children.length > 0) {
            const child = obj.children[0];
            obj.remove(child);
            this.disposeHierarchy(child);
        }
    }

    attachBuildingDetails(mesh) {
        if (this.activeDetailGroup) {
            if (this.activeDetailGroup.parent) {
                this.activeDetailGroup.parent.remove(this.activeDetailGroup);
            }
            this.disposeHierarchy(this.activeDetailGroup);
            this.activeDetailGroup = null;
        }

        const parcel = mesh.userData?.parcel_data;
        if (!parcel || (!parcel.is_building && parcel.zone_type !== "FLR")) return;
        if (mesh.userData?.has_built_in_details) return;

        const geoData = parcel.geometry;
        if (!geoData) return;
        const width = geoData.x_max - geoData.x_min;
        const length = geoData.y_max - geoData.y_min;
        const height = geoData.z_max - geoData.z_min;
        if (height < 3.0) return;

        const floorsCount = parcel.floors_count || Math.max(2, Math.round(height / 3.2));
        const floorH = height / floorsCount;

        const group = new THREE.Group();
        group.userData = { is_component: true };

        // Floor dividing slabs
        const slabGeo = new THREE.BoxGeometry(width + 0.35, 0.22, length + 0.35);
        const slabMat = this.getMaterial("#0f172a", 0.95, 0.9, 0.1);
        for (let f = 1; f < floorsCount; f++) {
            const slabY = -height / 2 + f * floorH;
            const slab = new THREE.Mesh(slabGeo, slabMat);
            slab.position.set(0, slabY, 0);
            group.add(slab);
        }

        // Window bands
        const winGeo = new THREE.BoxGeometry(width * 1.008, floorH * 0.38, length * 1.008);
        const winMat = this.getMaterial("#090d16", 0.98, 0.1, 0.5);
        for (let f = 0; f < floorsCount; f++) {
            const flrCenterY = -height / 2 + (f + 0.5) * floorH;
            const winBand = new THREE.Mesh(winGeo, winMat);
            winBand.position.set(0, flrCenterY, 0);
            group.add(winBand);
        }

        // Rooftop structure
        const roofGeo = new THREE.BoxGeometry(width * 0.94, 0.5, length * 0.94);
        const roofMat = this.getMaterial("#0f172a", 0.95, 0.9, 0.1);
        const roof = new THREE.Mesh(roofGeo, roofMat);
        roof.position.set(0, height / 2 + 0.25, 0);
        group.add(roof);

        // Water tank
        const tankGeo = new THREE.BoxGeometry(width * 0.28, 1.6, length * 0.28);
        const tankMat = this.getMaterial("#1e293b", 0.95, 0.7, 0.2);
        const tank = new THREE.Mesh(tankGeo, tankMat);
        tank.position.set(0, height / 2 + 1.1, 0);
        group.add(tank);

        mesh.add(group);
        this.activeDetailGroup = group;
    }

    renderParcels(parcels) {
        // Clear existing parcel meshes with full GPU memory disposal
        this.clearParcels();

        parcels.forEach(parcel => {
            const geoData = parcel.geometry;
            if (!geoData) return;

            const width = geoData.x_max - geoData.x_min;
            const length = geoData.y_max - geoData.y_min;
            const height = geoData.z_max - geoData.z_min;

            // Specialized 3D Architectural Mesh for Infrastructure Utility Nodes
            if (parcel.zone_type === "NODE" || parcel.is_infrastructure_node) {
                const nodeRadius = Math.max(width, length) * 0.45;
                const nodeHeight = Math.max(height, 8.0);

                const cylGeo = new THREE.CylinderGeometry(nodeRadius * 0.65, nodeRadius, nodeHeight, 8);
                const nodeColor = parcel.color || "#06b6d4";
                const cylMat = this.getMaterial(nodeColor, 0.92, 0.25, 0.7);
                const nodeMesh = new THREE.Mesh(cylGeo, cylMat);

                const basePosY = (geoData.z_min + geoData.z_max) / 2.0;
                nodeMesh.position.set(geoData.center[0], basePosY, geoData.center[1]);

                // Glowing Beacon Sphere on top
                const beaconGeo = new THREE.SphereGeometry(nodeRadius * 0.35, 12, 12);
                const beaconMat = this.getMaterial(nodeColor, 1.0, 0.1, 0.9);
                const beacon = new THREE.Mesh(beaconGeo, beaconMat);
                beacon.position.set(0, nodeHeight / 2 + nodeRadius * 0.3, 0);
                nodeMesh.add(beacon);

                // Wireframe Pulse Ring
                const ringGeo = new THREE.TorusGeometry(nodeRadius * 0.9, 0.35, 6, 16);
                const ringMat = this.getMaterial(nodeColor, 0.9, 0.2, 0.8);
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = Math.PI / 2;
                ring.position.set(0, nodeHeight / 2, 0);
                nodeMesh.add(ring);

                // Facet Wireframe Edges
                const edgeGeo = new THREE.EdgesGeometry(cylGeo);
                const edgeMat = this.getEdgeMaterial(0xffffff, 1.5);
                const edges = new THREE.LineSegments(edgeGeo, edgeMat);
                nodeMesh.add(edges);

                nodeMesh.userData = {
                    parcel_data: parcel,
                    base_y: basePosY,
                    zone_type: "NODE",
                    floor_no: 0,
                    is_node: true
                };

                this.scene.add(nodeMesh);
                this.parcelMeshes.push({ mesh: nodeMesh, edges, parcel });
                return;
            }

            // Specialized 3D Rendering for Public Services & Civic Infrastructure Facilities (Hospitals, Schools, Banks, Civic Hubs)
            if (parcel.zone_type === "INFRA" || parcel.is_public_service || (parcel.is_infrastructure && !parcel.is_road && !parcel.is_railway)) {
                const infraRadius = Math.max(width, length) * 0.45;
                const infraHeight = Math.max(height, 8.5);
                const hubGeo = new THREE.CylinderGeometry(infraRadius * 0.78, infraRadius, infraHeight, 6);
                const hubColor = parcel.color || "#06b6d4";
                const hubMat = this.getMaterial(hubColor, 0.94, 0.3, 0.4);
                const hubMesh = new THREE.Mesh(hubGeo, hubMat);
                const basePosY = infraHeight / 2.0;
                hubMesh.position.set(geoData.center[0], basePosY, geoData.center[1]);

                // Civic Flagpole / Mast
                const mastGeo = new THREE.CylinderGeometry(0.12, 0.12, 3.2, 6);
                const mastMat = this.getMaterial("#ffffff", 1.0, 0.2, 0.8);
                const mast = new THREE.Mesh(mastGeo, mastMat);
                mast.position.set(0, infraHeight / 2 + 1.6, 0);
                hubMesh.add(mast);

                // Institutional Beacon Sphere
                const beaconGeo = new THREE.SphereGeometry(infraRadius * 0.24, 12, 12);
                const beaconMat = this.getMaterial(hubColor, 1.0, 0.2, 0.8);
                const beacon = new THREE.Mesh(beaconGeo, beaconMat);
                beacon.position.set(0, infraHeight / 2 + 3.4, 0);
                hubMesh.add(beacon);

                // Crisp White Edges
                const edgeGeo = new THREE.EdgesGeometry(hubGeo);
                const edgeMat = this.getEdgeMaterial(0xffffff, 1.5);
                const edges = new THREE.LineSegments(edgeGeo, edgeMat);
                hubMesh.add(edges);

                hubMesh.userData = {
                    parcel_data: parcel,
                    base_y: basePosY,
                    zone_type: "INFRA",
                    floor_no: 0,
                    is_infra: true
                };
                this.scene.add(hubMesh);
                this.parcelMeshes.push({ mesh: hubMesh, edges, parcel });
                return;
            }

            // Specialized 3D Rendering for Railway Corridors and Tracks (RAIL)
            if (parcel.zone_type === "RAIL" || parcel.is_railway) {
                const railW = Math.max(width, 5.0);
                const railL = Math.max(length, 5.0);
                const bedGeo = new THREE.BoxGeometry(railW, 0.35, railL);
                const bedMat = this.getMaterial("#1e293b", 1.0, 0.9, 0.1);
                const railMesh = new THREE.Mesh(bedGeo, bedMat);
                const basePosY = 0.2;
                railMesh.position.set(geoData.center[0], basePosY, geoData.center[1]);

                // Steel Track Line Accent
                const steelGeo = new THREE.BoxGeometry(railW * 0.92, 0.12, railL * 0.92);
                const steelMat = this.getMaterial("#f59e0b", 1.0, 0.2, 0.85);
                const steel = new THREE.Mesh(steelGeo, steelMat);
                steel.position.set(0, 0.22, 0);
                railMesh.add(steel);

                const edgeGeo = new THREE.EdgesGeometry(bedGeo);
                const edgeMat = this.getEdgeMaterial(0xf59e0b, 2.0);
                const edges = new THREE.LineSegments(edgeGeo, edgeMat);
                railMesh.add(edges);

                railMesh.userData = {
                    parcel_data: parcel,
                    base_y: basePosY,
                    zone_type: "RAIL",
                    is_rail: true
                };
                this.scene.add(railMesh);
                this.parcelMeshes.push({ mesh: railMesh, edges, parcel });
                return;
            }

            const boxGeo = new THREE.BoxGeometry(width, height, length);
            
            const isRoad = (parcel.zone_type === "ROAD" || parcel.is_road);
            const isBuilding = (parcel.zone_type === "FLR" || (parcel.is_building && !parcel.is_infrastructure && parcel.zone_type !== "INFRA" && parcel.zone_type !== "RAIL"));
            const colorHex = parcel.color || (isRoad ? "#334155" : "#3b82f6");
            const opacity = isRoad ? 0.96 : (parcel.zone_type === "SUB" ? 0.8 : 0.94);
            const roughness = isRoad ? 0.92 : 0.68;
            const metalness = isRoad ? 0.02 : 0.05;

            const material = this.getMaterial(colorHex, opacity, roughness, metalness);
            const mesh = new THREE.Mesh(boxGeo, material);
            
            // Calculate base position (roads slightly elevated at Y=0.25 to prevent z-fighting)
            const basePosY = isRoad ? (geoData.z_max / 2.0 + 0.08) : ((geoData.z_min + geoData.z_max) / 2.0);
            mesh.position.set(geoData.center[0], basePosY, geoData.center[1]);

            // Architectural Wireframe Edges (Crisp slate outline for buildings, yellow for roads)
            const edgeGeo = new THREE.EdgesGeometry(boxGeo);
            const edgeColor = isRoad ? 0xfacc15 : (parcel.is_restricted_rbac ? 0xc084fc : 0x1e293b);
            const edgeOpacity = isRoad ? 0.9 : 0.35;
            const edgeLineWidth = isRoad ? 2.0 : 1.0;
            const edgeMat = this.getEdgeMaterial(edgeColor, edgeLineWidth, edgeOpacity);
            const edges = new THREE.LineSegments(edgeGeo, edgeMat);
            mesh.add(edges);

            // Add rich architectural apartment details for key landmark towers
            const isShowcaseBuilding = isBuilding && (
                parcel.is_showcase || parcel.is_primary_showcase ||
                (parcel.survey_number && ['142/1A', '218/3B', '305/4C', '101/A', '88/2D', '64/3E', 'Sy. 101/A', 'Sy. 102/B', 'Sy. 143/2', 'Sy. 103/C', '166/W67'].some(s => parcel.survey_number.includes(s)))
            );

            if (isShowcaseBuilding && height >= 5.0) {
                const floorsCount = parcel.floors_count || Math.max(2, Math.round(height / 3.2));
                const floorH = height / floorsCount;

                // 1. Horizontal Floor Dividing Concrete Slabs
                const slabGeo = new THREE.BoxGeometry(width + 0.35, 0.22, length + 0.35);
                const slabMat = this.getMaterial("#0f172a", 0.95, 0.9, 0.1);
                for (let f = 1; f < floorsCount; f++) {
                    const slabY = -height / 2 + f * floorH;
                    const slab = new THREE.Mesh(slabGeo, slabMat);
                    slab.position.set(0, slabY, 0);
                    slab.userData = { is_component: true, floor_index: f };
                    mesh.add(slab);
                }

                // 2. Architectural Window Bands & Balcony Panels per floor
                const winGeo = new THREE.BoxGeometry(width * 1.006, floorH * 0.38, length * 1.006);
                const winMat = this.getMaterial("#090d16", 0.98, 0.1, 0.5);
                for (let f = 0; f < floorsCount; f++) {
                    const flrCenterY = -height / 2 + (f + 0.5) * floorH;
                    const winBand = new THREE.Mesh(winGeo, winMat);
                    winBand.position.set(0, flrCenterY, 0);
                    winBand.userData = { is_component: true, floor_index: f + 1 };
                    mesh.add(winBand);
                }

                // 3. Rooftop Parapet, Water Tank & Lift Machine Enclosure
                const roofGeo = new THREE.BoxGeometry(width * 0.94, 0.5, length * 0.94);
                const roofMat = this.getMaterial("#0f172a", 0.95, 0.9, 0.1);
                const roof = new THREE.Mesh(roofGeo, roofMat);
                roof.position.set(0, height / 2 + 0.25, 0);
                mesh.add(roof);

                // Overhead Water Tank / Machine Room
                const tankGeo = new THREE.BoxGeometry(width * 0.28, 1.6, length * 0.28);
                const tankMat = this.getMaterial("#1e293b", 0.95, 0.7, 0.2);
                const tank = new THREE.Mesh(tankGeo, tankMat);
                tank.position.set(0, height / 2 + 1.1, 0);
                mesh.add(tank);

                // Telemetry / Lightning Rod Antenna
                const rodGeo = new THREE.CylinderGeometry(0.12, 0.12, 2.8, 6);
                const rodMat = this.getMaterial("#38bdf8", 1.0, 0.2, 0.8);
                const rod = new THREE.Mesh(rodGeo, rodMat);
                rod.position.set(0, height / 2 + 2.8, 0);
                mesh.add(rod);

                // 4. Ground Floor Entrance Canopy / Portico
                if (height >= 8.0) {
                    const canopyGeo = new THREE.BoxGeometry(width * 0.38, 0.25, 2.2);
                    const canopyMat = this.getMaterial("#0284c7", 0.95, 0.5, 0.3);
                    const canopy = new THREE.Mesh(canopyGeo, canopyMat);
                    canopy.position.set(0, -height / 2 + 2.8, length / 2 + 1.1);
                    mesh.add(canopy);
                }

                mesh.userData.has_built_in_details = true;
            } else {
                mesh.userData.has_built_in_details = false;
            }

            mesh.userData = {
                ...mesh.userData,
                parcel_data: parcel,
                base_y: basePosY,
                zone_type: parcel.zone_type,
                floor_no: parcel.floor || 0,
                is_road: isRoad,
                is_building: isBuilding
            };

            this.scene.add(mesh);
            this.parcelMeshes.push({ mesh, edges, parcel });
        });

        this.applyExplosion();
        // Preserve initial cinematic aerial camera framing looking into city center
    }

    setExplosionFactor(factor) {
        this.explosionFactor = parseFloat(factor);
        this.applyExplosion();
    }

    applyExplosion() {
        this.parcelMeshes.forEach(item => {
            const mesh = item.mesh;
            const data = mesh.userData;

            if (data.zone_type === "FLR" && data.floor_no > 0) {
                // Shift upward based on floor index
                const extraOffset = (data.floor_no - 1) * (this.explosionFactor - 1.0) * 4.0;
                mesh.position.y = data.base_y + extraOffset;
            }

            // Apply visibility filters
            const isVisible = this.layerVisibility[data.zone_type] !== false;
            mesh.visible = isVisible;
        });
    }

    setLayerVisibility(zoneType, visible) {
        this.layerVisibility[zoneType] = visible;
        this.applyExplosion();
    }

    getParcelFromIntersect(object) {
        let current = object;
        let depth = 0;
        while (current && current !== this.scene && depth < 20) {
            if (current.userData && current.userData.parcel_data) {
                return { mesh: current, parcel: current.userData.parcel_data };
            }
            current = current.parent;
            depth++;
        }
        return null;
    }

    highlightParcel(targetMesh) {
        // Reset previous selected mesh highlight
        if (this.selectedMesh && this.selectedMesh !== targetMesh) {
            if (this.selectedMesh._origMaterial) {
                this.selectedMesh.material = this.selectedMesh._origMaterial;
                this.selectedMesh._origMaterial = null;
            }
        }

        this.selectedMesh = targetMesh;

        if (targetMesh && targetMesh.material) {
            if (!targetMesh._origMaterial) {
                targetMesh._origMaterial = targetMesh.material;
            }
            // Cloned emissive highlight material
            const selMat = targetMesh._origMaterial.clone();
            if (selMat.emissive) {
                selMat.emissive.setHex(0x0284c7);
                selMat.emissiveIntensity = 0.55;
            }
            targetMesh.material = selMat;

            // Attach dynamic architectural floor & window details for inspected building
            this.attachBuildingDetails(targetMesh);
        }
    }

    selectParcelByULPIN(ulpin_3d, autoFly = false) {
        const match = this.parcelMeshes.find(p => p.parcel.ulpin_3d === ulpin_3d || p.parcel.base_ulpin === ulpin_3d);
        if (match) {
            this.highlightParcel(match.mesh);
            if (autoFly) {
                this.flyToParcel(match.parcel, 65);
            }
            if (window.onParcelSelected) {
                window.onParcelSelected(match.parcel);
            }
        }
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Smooth camera tweening
        if (this.cameraAnim) {
            const now = performance.now();
            const elapsed = now - this.cameraAnim.startTime;
            const progress = Math.min(1.0, elapsed / this.cameraAnim.duration);
            // Cubic ease-out
            const ease = 1 - Math.pow(1 - progress, 3);

            this.camera.position.lerpVectors(this.cameraAnim.startPos, this.cameraAnim.endPos, ease);
            this.controls.target.lerpVectors(this.cameraAnim.startTarget, this.cameraAnim.endTarget, ease);

            if (progress >= 1.0) {
                this.cameraAnim = null;
            }
        }

        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}

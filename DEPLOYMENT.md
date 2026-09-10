# StrataMap: Online Deployment & Hosting Guide
**Smart India Hackathon 2026 | Problem Statement 26011**

---

## 🌐 1. Live Local & LAN Network Online Servers
The StrataMap application is configured for online multi-device access across your local network and internet:

- **3D Web Application URL**: [http://localhost:8000](http://localhost:8000)
- **Backend REST API Server**: [http://localhost:5000](http://localhost:5000) (Binds to `0.0.0.0:5000` for LAN access)

### LAN Access for SIH Team Members:
To access StrataMap from mobile phones, laptops, or judge tablets connected to the same Wi-Fi network:
1. Find your machine's IP address: `ipconfig` (e.g. `192.168.1.15`).
2. Open on mobile or secondary devices: `http://192.168.1.15:8000`

---

## 🚀 2. Free Cloud Hosting Options for Hackathon Judging

### Option A: Render.com (Flask Backend + Web App)
1. Push `c:\3d ulpin sih` to a GitHub repository.
2. Log into [Render.com](https://render.com) ➔ Select **New Web Service**.
3. Set Build Command: `pip install -r backend/requirements.txt`
4. Set Start Command: `python backend/app.py`
5. Render will issue a free HTTPS URL: `https://stratamap-3d.onrender.com`.

### Option B: GitHub Pages (Static 3D Web UI)
1. Commit the `frontend/` folder to GitHub.
2. In GitHub Repository Settings ➔ **Pages** ➔ Enable GitHub Pages from `main` branch `/frontend`.
3. Your 3D Map will be live at `https://<your-username>.github.io/<repo-name>/`.

### Option C: Instant Public Tunnel via LocalTunnel / ngrok
To share your local running instance with judges anywhere in the world instantly:
```powershell
npx localtunnel --port 8000
```
This generates a temporary public HTTPS link (e.g., `https://stratamap-sih2026.loca.lt`).

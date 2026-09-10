# StrataMap & Bhu-Aadhaar: Online Deployment & Hosting Guide
**Smart India Hackathon 2026 | Problem Statement 26011**

---

## ⚡ 1. Vercel Cloud Deployment (Recommended)

The project is fully configured for deployment on **Vercel** with full-stack support for:
- 🗺️ **3D Cadastre Visualizer Dashboard**: `https://<your-project>.vercel.app/`
- 🔐 **Bhu-Aadhaar Standalone Login Portal**: `https://<your-project>.vercel.app/login` (or `/login.html`)
- 📄 **Official 3D Cadastre Registry PDF**: `https://<your-project>.vercel.app/download-registry-pdf`
- ⚙️ **Python Serverless REST API**: `https://<your-project>.vercel.app/api/*`

### Deploying to Vercel in 2 Steps:
1. **Push to GitHub**: Push the repository to your GitHub account.
2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com) ➔ Click **Add New...** ➔ **Project**.
   - Select your GitHub repository.
   - Leave Framework Preset as **Other** (Vercel automatically detects `vercel.json` and Python functions in `api/index.py`).
   - Click **Deploy**.

---

## 🌐 2. Live Local & LAN Network Online Servers
The StrataMap application is configured for online multi-device access across your local network and internet:

- **3D Web Application URL**: [http://localhost:8000](http://localhost:8000)
- **Login Portal URL**: [http://localhost:8000/login.html](http://localhost:8000/login.html)
- **Backend REST API Server**: [http://localhost:5000](http://localhost:5000) (Binds to `0.0.0.0:5000` for LAN access)

### LAN Access for SIH Team Members:
To access StrataMap from mobile phones, laptops, or judge tablets connected to the same Wi-Fi network:
1. Find your machine's IP address: `ipconfig` (e.g. `192.168.1.15`).
2. Open on mobile or secondary devices: `http://192.168.1.15:8000` (or `http://192.168.1.15:8000/login.html`).

---

## 🚀 3. Other Cloud Hosting Options for Hackathon Judging

### Option A: Render.com (Flask Backend + Web App)
1. Push `c:\3d ulpin sih` to a GitHub repository.
2. Log into [Render.com](https://render.com) ➔ Select **New Web Service**.
3. Set Build Command: `pip install -r backend/requirements.txt`
4. Set Start Command: `python backend/app.py`
5. Access: `https://<app-name>.onrender.com/login` and `https://<app-name>.onrender.com/`.

### Option B: GitHub Pages (Static 3D Web UI)
1. Commit the `frontend/` folder to GitHub.
2. In GitHub Repository Settings ➔ **Pages** ➔ Enable GitHub Pages from `main` branch `/frontend`.
3. Your 3D Map will be live at `https://<your-username>.github.io/<repo-name>/index.html` and login at `login.html`.

### Option C: Instant Public Tunnel via LocalTunnel / ngrok
To share your local running instance with judges anywhere in the world instantly:
```powershell
npx localtunnel --port 8000
```
This generates a temporary public HTTPS link (e.g., `https://stratamap-sih2026.loca.lt/login.html`).

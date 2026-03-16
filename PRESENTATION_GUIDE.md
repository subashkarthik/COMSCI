# 🚀 Presentation Day Quick-Start Guide

Follow these **3 phases** in order to have a 100% working demo for your presentation.

## Phase 1: Start the Tunnel (The Bridge)
1. Open a terminal.
2. Run: 
   ```powershell
   cd d:\Hackathon_COMSCI\Whatsapp_FactChecker\backend
   python run_tunnel_stable.py
   ```
3. **DO NOT CLOSE THIS WINDOW.**
4. Locate the URL: `https://[something].trycloudflare.com`
5. **COPY** that URL.

## Phase 2: Update Meta Developer Portal
1. Login to [developers.facebook.com](https://developers.facebook.com/)
2. Open your **FactCheckerBot** app.
3. Go to **WhatsApp** > **Configuration** (left menu).
4. Click **Edit** in the Webhook section.
5. Paste your Tunnel URL and **ADD `/webhook`** at the end. 
   *Example: `https://davidson-linked-cet-merely.trycloudflare.com/webhook`*
6. Verify Token: `factcheck_2026_secure_token`
7. Click **Verify and Save**.
8. **Check Subscriptions:** Ensure `messages` is checked under "Webhook fields".

## Phase 3: Start the App
1. Go to the project root: `d:\Hackathon_COMSCI\Whatsapp_FactChecker`
2. Double-click **`start.bat`**.
3. This will open two windows:
   *   **Window 1:** Backend (FastAPI) — wait for "Uvicorn running..."
   *   **Window 2:** Dashboard (Vite) — wait for "Vite v..."
4. Open the dashboard at [http://localhost:5173](http://localhost:5173)

---

## 💡 How to Demo
1. **Live WhatsApp:** 
   *   Go to **WhatsApp** > **API Setup** in Meta.
   *   Send the test template to your phone.
   *   **Reply** with a text claim or a voice note 🎤.
2. **Dashboard Simulator:**
   *   Type anything in the "Voice Audit Simulator" box on the dashboard.
   *   This simulates a message coming in even if WhatsApp has network issues.

## ⚠️ Presentation Checklist
*   [ ] Laptop is plugged in.
*   [ ] Internet is stable.
*   [ ] Cloudflare Tunnel URL is updated in Meta.
*   [ ] `backend/.env` has your current `WHATSAPP_TOKEN`.

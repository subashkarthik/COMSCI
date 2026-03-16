# 🌐 Permanent Deployment Guide

To make your WhatsApp Fact-Checker stay on permanently (24/7) without you having to run it on your laptop, follow these steps.

## 1. Get a Permanent WhatsApp Token
The "Temporary Access Token" expires every 24 hours. For a permanent bot, you need a **System User Access Token**:
1.  Go to your [Meta Business Suite](https://business.facebook.com/settings/system-users).
2.  Create a **System User**.
3.  Generate a **token** for that user and select your FactChecker app.
4.  Select `whatsapp_business_messaging` and `whatsapp_business_management` permissions.
5.  **Save this token** — it never expires! Paste it into your production `.env`.

## 2. Deploy to the Cloud
Since this is a Hackathon project, I recommend **Render.com** or **Railway.app** as they are the easiest.

### Option A: Render (Easiest)
1.  **Push your code to GitHub.**
2.  **Backend:** Create a new "Web Service" on Render linked to your GitHub.
    *   **Runtime:** Python
    *   **Build Command:** `pip install -r backend/requirements.txt`
    *   **Start Command:** `cd backend && gunicorn main:app -k uvicorn.workers.UvicornWorker`
3.  **Frontend:** Create a new "Static Site" on Render.
    *   **Build Command:** `npm run build`
    *   **Publish directory:** `dist`
4.  **Environment Variables:** Add all your `.env` variables (API keys, tokens) to the Render dashboard.

## 3. Persistent Webhook URL
Once you deploy to Render/Railway, you will get a permanent URL like `https://fact-checker-api.onrender.com`.
1.  Go to Meta Developer Portal > WhatsApp > Configuration.
2.  Replace the Cloudflare tunnel URL with your **permanent Render URL** (e.g., `https://fact-checker-api.onrender.com/webhook`).
3.  No more tunnels needed!

## 4. Keeping it Alive (Process Management)
If you use a VPS (like AWS or DigitalOcean) instead of Render, use **PM2**:
1.  Install PM2: `npm install pm2 -g`
2.  Start Backend: `pm2 start "python -m uvicorn main:app" --name fact-check-backend`
3.  Start Dashboard: `pm2 start "npm run dev" --name fact-check-frontend`
4.  PM2 will automatically restart your app if it crashes or the server reboots.

---

### 🚀 Recommended "Pro" Setup for Hackathons:
1.  **Database:** Switch `DATABASE_URL` to a free PostgreSQL database on **Supabase** or **Neon.tech** (so your data isn't stuck in a local `.db` file).
2.  **API Keys:** Keep using Gemini and Serper as they are already performant.

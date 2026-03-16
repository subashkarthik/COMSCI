# Deployment Implementation Plan

This plan outlines the steps to move your WhatsApp Fact-Checker from your local laptop to a permanent cloud server (Render.com).

## User Review Required

> [!IMPORTANT]
> **Permanent WhatsApp Token:** You MUST generate a System User Access Token in the Meta Business Suite. The current "Temporary Token" expires every 24 hours.
> **Cloud Account:** You will need to create a free account on [Render.com](https://render.com).

## Proposed Changes

### Configuration
Update `backend/main.py` and potentially `dashboard/vite.config.ts` to handle production environment variables if necessary. (Current code is mostly production-ready).

### Repository Structure
Ensure the repository is organized such that Render can easily find the `backend/` and `dashboard/` directories.

## Deployment Steps

### 1. Meta Permanent Token
1. Go to **Meta Business Settings** > **Users** > **System Users**.
2. Add a System User (Admin role).
3. Click **Add Assets** > Select your **FactCheckerBot** app.
4. Click **Generate New Token**.
5. Select `whatsapp_business_messaging` and `whatsapp_business_management`.
6. **Copy and Save** this token. This is your permanent `WHATSAPP_TOKEN`.

### 2. Render.com Backend (API)
1. Log in to [Render](https://render.com).
2. Click **New** > **Web Service**.
3. Connect your GitHub repository.
4. **Root Directory:** `backend`
5. **Runtime:** `Python 3`
6. **Build Command:** `pip install -r requirements.txt`
7. **Start Command:** `gunicorn main:app -k uvicorn.workers.UvicornWorker`
8. **Environment Variables:** Add `GEMINI_API_KEY`, `SERPER_API_KEY`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `FASTAPI_VERIFY_TOKEN`.

### 3. Render.com Frontend (Dashboard)
1. Click **New** > **Static Site**.
2. Connect your GitHub repository.
3. **Root Directory:** `dashboard`
4. **Build Command:** `npm run build`
5. **Publish Directory:** `dist`
6. **Environment Variables:** Set `VITE_API_URL` to your Render backend URL.

### 4. Update Meta Webhook
1. Copy your new Render backend URL (e.g., `https://fact-checker-api.onrender.com`).
2. Go to **Meta Developer Portal** > **WhatsApp** > **Configuration**.
3. Change the Callback URL to `https://your-app.onrender.com/webhook`.

## Verification Plan

### Automated Tests
*   Verify Render health checks pass.
*   Verify `/api/analytics` returns 200 via the new URL.

### Manual Verification
*   Send a WhatsApp message to the test phone number.
*   Verify the bot replies correctly using the permanent cloud server.

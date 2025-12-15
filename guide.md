## TECNVIRONS Deployment Guide

This guide shows how to deploy the **backend on Render** and the **frontend on Vercel**.

---

## 1. Prerequisites

- GitHub repo: `sankalp250/TECNVIRONS` (already pushed).
- Supabase project with:
  - `sessions` and `session_events` tables created (see `README.md`).
  - Project URL and **service role** key.
- Groq account and API key.

Environment variables you will need:

- `GROQ_API_KEY`
- `GROQ_MODEL` (recommended: `llama-3.1-8b-instant`)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_SCHEMA` (usually `public`)

---

## 2. Backend on Render

The repo includes `render.yaml`, so Render can auto-configure the service.

### 2.1 Create the Web Service

1. Go to Render dashboard.
2. Click **New → Web Service**.
3. Choose **Build and deploy from a Git repository**.
4. Select the `TECNVIRONS` GitHub repo.
5. Render will detect `render.yaml` and show a preview:
   - Environment: Python
   - Build command: `pip install --upgrade pip && pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
   - Health check path: `/healthz`

Click **Create Web Service**.

### 2.2 Configure Environment Variables

In the Render service **Environment** tab, set the following:

- **GROQ_API_KEY**: your Groq key.
- **GROQ_MODEL**: `llama-3.1-8b-instant` (or another supported model).
- **SUPABASE_URL**: Supabase project URL (e.g., `https://femrkzudweabacudjldw.supabase.co`).
- **SUPABASE_SERVICE_ROLE_KEY**: Supabase service role key.
- **SUPABASE_SCHEMA**: `public` (or your custom schema).

Click **Save Changes** and let Render redeploy.

### 2.3 Verify Backend

After deploy:

1. Open the service URL, e.g. `https://tecnvirons-backend.onrender.com/healthz`.
2. You should see JSON like:
   ```json
   { "status": "ok", "app": "Realtime AI Backend" }
   ```
3. The WebSocket endpoint will be:
   ```text
   wss://<your-render-service>.onrender.com/ws/session/{session_id}?user_id={user_id}
   ```

Keep this base URL handy for Vercel.

---

## 3. Frontend on Vercel

The frontend is pure HTML/CSS/JS in the `frontend/` folder.

### 3.1 Prepare the repo for Vercel

By default, Vercel expects the project root to be the app. Here we only want to deploy the `frontend/` folder:

- Project root: repository root (`/`).
- Output/public directory: `frontend`.
- Framework preset: **Other**.

You do **not** need a build command; it’s static.

### 3.2 Create the Vercel Project

1. Go to Vercel dashboard.
2. Click **Add New → Project**.
3. Import the `TECNVIRONS` GitHub repo.
4. In the **Configure Project** step:
   - **Framework Preset**: `Other`.
   - **Root Directory**: leave as default (`/`).
   - **Output Directory / Public Directory**: set to `frontend`.
   - **Build Command**: leave empty (or `echo "no build"`).
5. Click **Deploy**.

Vercel will serve whatever is in `frontend/` as static files.

### 3.3 Point the Frontend to Render

In the chat UI, the **Backend Host** input defaults to `ws://localhost:8000`. For production:

1. When you open the deployed Vercel site, change the host field to:
   ```text
   wss://<your-render-service>.onrender.com
   ```
2. Optionally, you can hard-code the default in `frontend/index.html` before deploying:
   ```html
   <input id="host-input" type="text" value="wss://your-render-service.onrender.com" />
   ```

Now:

- Frontend (Vercel) → opens `wss://<render-app>.onrender.com/ws/session/...`
- Backend (Render) → talks to Groq + Supabase.

---

## 4. End-to-End Test Checklist

1. **Backend health**: `https://<render-app>.onrender.com/healthz` returns status JSON.
2. **Supabase**: `sessions` and `session_events` tables exist; new rows appear when you chat.
3. **Frontend load**: Vercel URL loads the UI.
4. **WebSocket chat**:
   - Set host to `wss://<render-app>.onrender.com`.
   - Click **Generate** for a session ID, then **Connect**.
   - Ask a question (e.g., “weather of kolkata” or “what is LangGraph?”).
   - You see tokens stream and final answers, and no “session started” noise.

If any step fails, check:

- Render logs for environment variable or model errors.
- Supabase table existence and row inserts.
- Browser dev tools (Network → WS) to confirm WebSocket connection status.



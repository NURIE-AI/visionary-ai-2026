# Nurie Web Sample (Vue + FastAPI Proxy)

This repository is a demo application for uploading files to Nurie Vault and chatting with Chat v2 using those uploaded files as context.

The frontend is intentionally configured to call only this repo's backend proxy (`/nurie/vault/...`) so the Nurie API key stays server-side.

## What This Sample Shows

- Drag-and-drop upload to Nurie Vault (`POST /api/v1/files/` upstream via proxy).
- Chat v2 conversation flow with `chat_id` continuation.
- Same-origin frontend -> backend calls to avoid browser-side key exposure.
- Local development with Vite proxy and Docker deployment with nginx proxy.

## Architecture

### Request Flow

1. Browser UI (`frontend`) sends relative requests:
   - `POST /nurie/vault/files/`
   - `POST /nurie/vault/chat/message/v2`
2. Dev/prod proxy layer routes `/nurie/...` to FastAPI:
   - Dev: Vite proxy (`frontend/vite.config.js`)
   - Docker: nginx (`frontend/nginx/default.conf`)
3. FastAPI backend (`backend/main.py`) adds `X-Api-Key` from `NURIE_API_KEY` and forwards to:
   - `<NURIE_API_BASE>/api/v1/files/`
   - `<NURIE_API_BASE>/api/v1/chat/message/v2`
4. Backend passes upstream status/body back to the frontend.

### Components

- `frontend/src/views/HomeView.vue`: upload + chat demo page.
- `frontend/src/services/nurieApi.js`: request helpers for backend/direct modes.
- `backend/main.py`: proxy endpoints and upstream forwarding logic.
- `docker-compose.yml`: frontend + backend compose stack.

## Project Structure

```text
.
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/HomeView.vue
│   │   └── services/nurieApi.js
│   ├── nginx/default.conf
│   ├── vite.config.js
│   ├── .env.example
│   └── Dockerfile
└── docker-compose.yml
```

## Step-by-Step Setup (Local Dev)

### 1) Prerequisites

- Python 3.9+
- Node.js 18+ and npm

### 2) Configure backend env
- Precondition: Get your API key from Nurie App

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

- Set `NURIE_API_KEY` to your personal API key.
- Keep `NURIE_API_BASE` as origin only (for example `https://api.vault.nurie.ai`), no `/api/v1`.

### 3) Start backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Quick checks:

- `http://localhost:8000/`
- `http://localhost:8000/nurie/vault/status`

### 4) Start frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

Notes:

- The page sends requests to `/nurie/vault/...` on the same origin.
- Vite proxy forwards `/nurie` to `VITE_BACKEND_PROXY_TARGET` (defaults to `http://127.0.0.1:8000`).

### 5) Use the demo

1. Upload one or more files in the upload area.
2. Confirm file IDs appear under the uploader.
3. Ask a question in chat.
4. Use "New conversation" to reset `chat_id`.

## Step-by-Step Setup (Docker Compose)

### 1) Prepare env

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set `NURIE_API_KEY`.

### 2) Build and run

```bash
docker compose up --build
```

### 3) Access

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`

The nginx container proxies `/nurie` to backend service (`frontend/nginx/default.conf`).

## API Endpoints Exposed by Backend

- `GET /` health/info
- `GET /nurie/vault` proxy route index/help
- `GET /nurie/vault/status` backend proxy status
- `POST /nurie/vault/files/` upload passthrough
- `POST /nurie/vault/chat/message/v2` chat passthrough

## Legacy / Security Review Notes

This section summarizes the current state and recommended cleanup for production hardening.

### Legacy/demo code still present

- `backend/main.py` still contains generic demo endpoints:
  - `GET /items/{item_id}`
  - `POST /log_text`
  These are not used by the sample UI and can be removed for a cleaner demo API surface.
- `frontend/src/services/nurieApi.js` still supports `"direct"` mode and auth-header helpers even though `HomeView.vue` now uses backend mode only.
  - This is safe but is now optional/legacy functionality.
- `frontend/.env.example` includes direct-mode vars (`VITE_NURIE_API_KEY`, `VITE_NURIE_API_BASE`) that are no longer needed for the current page behavior.

### Security considerations

- `backend/main.py` currently allows CORS from all origins (`allow_origins=["*"]`).
  - Good for demos, but production should restrict to known origins.
- Proxy endpoints are unauthenticated at app level.
  - If exposed publicly, anyone can call your backend as a relay to Nurie using your server-side key.
  - Add app authentication/rate limits before public exposure.
- Upload endpoint forwards arbitrary files upstream.
  - Consider adding file size/type validation and request throttling.
- Do not commit `backend/.env` with real secrets.
  - Keep secrets in environment/secret manager for production.

## Troubleshooting

- `404 {"detail":"Not Found"}` on upload/chat:
  - Often upstream path/base mismatch.
  - Ensure `NURIE_API_BASE` is origin-only (no `/api/v1`).
- Browser CORS/network error in dev:
  - Ensure backend is running on `:8000`.
  - Ensure Vite dev server uses proxy rule for `/nurie`.
- Backend returns `503` missing key:
  - Set `NURIE_API_KEY` in `backend/.env` and restart backend.

## Production Hardening Checklist (Recommended)

- Restrict CORS origins.
- Add rate limiting and upload size/type validation.
- Add structured logging and request IDs.


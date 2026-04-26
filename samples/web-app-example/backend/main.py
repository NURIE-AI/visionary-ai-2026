import os
from pathlib import Path
from typing import Dict, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")


def _normalize_nurie_api_base(raw: str) -> str:
    """Origin only (e.g. https://api…). Strip accidental /api/v1 suffix."""
    u = (raw or "").strip().rstrip("/")
    if not u:
        return "https://api.vault.nurie.ai"
    if u.endswith("/api/v1"):
        u = u[: -len("/api/v1")].rstrip("/")
    return u


NURIE_API_BASE = _normalize_nurie_api_base(os.getenv("NURIE_API_BASE", ""))
NURIE_API_KEY = os.getenv("NURIE_API_KEY", "").strip()

VAULT_FILES_PATH = "/api/v1/files/"
VAULT_CHAT_V2_PATH = "/api/v1/chat/message/v2"

_PROXY_HDR = {"X-Proxied-From-Nepp-Vault": "1"}


def _proxy_response_headers(upstream_status: int) -> Dict[str, str]:
    h = dict(_PROXY_HDR)
    h["X-Upstream-HTTP-Status"] = str(upstream_status)
    return h

print(
    f"nurie-vault-proxy: upstream={NURIE_API_BASE!s} "
    f"api_key_configured={bool(NURIE_API_KEY)}",
    flush=True,
)

app = FastAPI()

# `Access-Control-Allow-Origin: *` requires allow_credentials=False (browser CORS rules).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def _upstream_auth_headers() -> dict:
    if not NURIE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Server is missing NURIE_API_KEY (set it in backend/.env or the process environment).",
        )
    return {"X-Api-Key": NURIE_API_KEY}


class TextPayload(BaseModel):
    text: str


@app.get("/")
def read_root():
    """If this JSON does not match, port 8000 is not this repo’s `backend/main.py`."""
    return {
        "app": "nurie-web-sample-backend",
        "hint": "Nurie proxy lives under /nurie/vault/… — try GET /nurie/vault/status",
        "nurie_routes": [
            "GET /nurie/vault",
            "GET /nurie/vault/status",
            "POST /nurie/vault/files/",
            "POST /nurie/vault/chat/message/v2",
        ],
        "openapi": "/docs",
    }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}


@app.post("/log_text")
def log_text(payload: TextPayload):
    print(f"Received text from frontend: {payload.text}")
    return {"message": f"Text '{payload.text}' received and logged."}


@app.get("/nurie/vault")
@app.get("/nurie/vault/")
def nurie_vault_index():
    """List proxy HTTP routes. Key/upstream flags: GET /nurie/vault/status (no duplication here)."""
    return {
        "service": "nurie-web-sample backend proxy",
        "routes": {
            "status": "GET /nurie/vault/status",
            "upload": "POST /nurie/vault/files/ (multipart field files)",
            "chat_v2": "POST /nurie/vault/chat/message/v2 (JSON body)",
        },
        "upstream": {
            "files": f"{NURIE_API_BASE}{VAULT_FILES_PATH}",
            "chat_v2": f"{NURIE_API_BASE}{VAULT_CHAT_V2_PATH}",
        },
        "note": (
            "404 {\"detail\":\"Not Found\"} is often the upstream body passed through. "
            "NURIE_API_BASE must be the vault API origin. Proxied responses may include "
            "X-Proxied-From-Nepp-Vault and X-Upstream-HTTP-Status."
        ),
    }


@app.get("/nurie/vault/status")
@app.get("/nurie/vault/status/")
def nurie_vault_status():
    """Lets the UI confirm the backend can call Nurie without exposing the key."""
    return {
        "nurie_upstream": NURIE_API_BASE,
        "nurie_api_key_configured": bool(NURIE_API_KEY),
    }


@app.get("/nurie/vault/files/")
@app.get("/nurie/vault/files")
def nurie_files_get_help():
    """Address-bar GET hits this; uploads must use POST + multipart (see POST on same path)."""
    return JSONResponse(
        status_code=405,
        content={
            "detail": "This path only accepts POST with multipart/form-data and field 'files' "
            "(same contract as Nurie POST /api/v1/files/). A browser tab issues GET, so it "
            "cannot upload. Use the app upload area or: curl -X POST -F 'files=@./file.pdf' "
            f"'http://localhost:8000/nurie/vault/files/?conflict_resolution=keep'",
            "hint": "Verify the proxy: GET /nurie/vault/status on the same host.",
        },
    )


@app.get("/nurie/vault/chat/message/v2")
@app.get("/nurie/vault/chat/message/v2/")
def nurie_chat_get_help():
    return JSONResponse(
        status_code=405,
        content={
            "detail": "Use POST with JSON body (Chat v2). Browser navigation uses GET only.",
        },
    )


@app.post("/nurie/vault/files/")
@app.post("/nurie/vault/files")
async def nurie_proxy_upload(
    files: list[UploadFile] = File(...),
    conflict_resolution: str = Query("keep"),
    directory_id: Optional[str] = Query(None),
):
    """Forward multipart upload to Nurie vault (same contract as POST /api/v1/files/)."""
    params: dict = {"conflict_resolution": conflict_resolution}
    if directory_id:
        params["directory_id"] = directory_id

    url = f"{NURIE_API_BASE}{VAULT_FILES_PATH}"
    headers = _upstream_auth_headers()

    file_parts: list[tuple[str, tuple]] = []
    for uf in files:
        body = await uf.read()
        ct = uf.content_type or "application/octet-stream"
        name = uf.filename or "upload"
        file_parts.append(("files", (name, body, ct)))

    timeout = httpx.Timeout(120.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(url, headers=headers, params=params, files=file_parts)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}") from e

    if r.status_code >= 400:
        print(f"nurie proxy upload: POST {url} -> HTTP {r.status_code}", flush=True)

    media = r.headers.get("content-type", "application/json")
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=media,
        headers=_proxy_response_headers(r.status_code),
    )


@app.post("/nurie/vault/chat/message/v2")
@app.post("/nurie/vault/chat/message/v2/")
async def nurie_proxy_chat_v2(request: Request):
    """Forward Chat v2 JSON to Nurie; response body and status pass through."""
    body = await request.body()
    url = f"{NURIE_API_BASE}{VAULT_CHAT_V2_PATH}"
    headers = _upstream_auth_headers()
    ct = request.headers.get("content-type", "application/json")
    headers["Content-Type"] = ct

    timeout = httpx.Timeout(120.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.post(url, headers=headers, content=body)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream request failed: {e!s}") from e

    if r.status_code >= 400:
        print(f"nurie proxy chat: POST {url} -> HTTP {r.status_code}", flush=True)

    media = r.headers.get("content-type", "application/json")
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=media,
        headers=_proxy_response_headers(r.status_code),
    )

# API tutorial examples

These scripts demonstrate **end-to-end flows** similar to the web app (upload → wait for processing → next action), not isolated HTTP calls. Each script uses `API_BASE_URL` including `/api/v1` and the **`x-api-key`** header. Create a key under **Settings → API Keys**, replace `YOUR_API_KEY` in each script, install [requests](https://requests.readthedocs.io/) (`python -m pip install requests`), and run from this directory, e.g. `python 03_upload_file.py` or `python 06_search_files.py`. Default host is production **`https://api.vaultsage.ai/api/v1`**; for a self-hosted deployment, change `API_BASE_URL` to your origin + `/api/v1`. Endpoint reference: [VaultSage Public API docs](https://api.vaultsage.ai/docs#/).

Shared helpers live in **`common_api.py`** (`get_json` / `post_json` / `patch_json`, `upload_local_file`, `smart_upload_file`, `wait_for_file_processing` vs `wait_summary_status_relaxed`, `print_json`, `print_chat_turn`, `run_with_spinner`, …). Each upload script sets **`SAMPLE_UPLOAD_FILENAME`** / **`SAMPLE_UPLOAD_PATH`** at the top; replace **[`test1.png`](test1.png)** or change that constant to use another file.

**Note:** Personal API keys cannot call `/api/v1/users/me/api-keys` (manage keys only in the UI).

## Scripts

| Script | Flow (human intent) | Main endpoints |
|--------|---------------------|----------------|
| `01_update_user_profile.py` | **Update user profile**: **GET** profile → **PATCH** display name → show responses | `GET /users/me`, `PATCH /users/me` |
| `02_get_dashboard.py` | Open dashboard | `GET /dashboard/` |
| `03_upload_file.py` | Upload a file → **poll until processing finishes** (preview / AI steps) | `POST /files/`, `POST /files/processing-status` |
| `04_create_folder_and_upload_file.py` | **Create folder and upload file** → wait processing → list files in that folder | `POST /directories/`, `POST /files/`, processing-status, `GET /files/` |
| `05_move_file_to_folder.py` | Create folder → upload to root → wait → **move into folder** → list inside folder | directories, files, processing-status, `PATCH /files/{file_id}/move` |
| `06_search_files.py` | **Search only** (default keyword matches sample name); suggests **`03_upload_file.py`** / **`04_create_folder_and_upload_file.py`** or uploading the same **`SAMPLE_UPLOAD_FILENAME`** | `GET /files/search` |
| `07_create_share_links.py` | **Create share links** (upload → wait → `POST /share/`) **then list** your shares; set **`LIST_ONLY = True`** to only `GET /share/user-shares` | files, processing-status, `POST /share/`, `GET /share/user-shares` |
| `08_chat_with_file.py` | **Chat with file**: upload → wait → **first chat with file** (persisted) → **follow-up**; optional list chats (see script) | files, processing-status, `POST /chat/message/v2`, `GET /chat/` |
| `09_smart_upload_with_chat.py` | **Smart upload with chat**: **Smart Upload** image → wait (**summary-only** poll, 60s then continue) → **single chat** with `file_ids` (legacy `sample_file.py` story) | `POST /smart-upload/`, `POST /files/processing-status`, `POST /chat/message/v2` |

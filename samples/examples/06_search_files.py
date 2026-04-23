#!/usr/bin/env python3
"""
User flow: search vault by keyword only (no upload in this script).

Other tutorials already call GET /files/ to list a folder (e.g. ``04_create_folder_and_upload.py``,
``05_move_file_to_folder.py``); there is no separate list-only script.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import get_json, print_json, require_api_key

# =============================================================================
# Base settings
# =============================================================================
API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"
# Search keyword (default matches the sample image name used in upload tutorials).
SEARCH_TOKEN = "test1"
# Filename those tutorials upload by default (for the note text only; this script does not upload).
SAMPLE_UPLOAD_FILENAME = "test1.png"


def main() -> None:
    require_api_key(API_KEY)

    print(
        "Note: This script only runs search. For meaningful hits on the default keyword "
        f"{SEARCH_TOKEN!r} (e.g. filenames like {SAMPLE_UPLOAD_FILENAME!r}), ensure the vault "
        "already has that file: run `03_upload_file.py` or `04_create_folder_and_upload.py`, or "
        f"upload {SAMPLE_UPLOAD_FILENAME!r} in the UI and wait for processing, then run this "
        "script again.\n",
    )

    # ==========================================
    # 1. Search by keyword (GET /files/search)
    # ==========================================
    print(f"Searching for keyword {SEARCH_TOKEN!r}...")
    data = get_json(API_BASE_URL, API_KEY, "/files/search", {"keyword": SEARCH_TOKEN})
    print("\n--- Search results ---")
    print_json(data)


if __name__ == "__main__":
    main()

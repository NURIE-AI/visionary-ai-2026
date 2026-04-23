#!/usr/bin/env python3
"""
User flow: create a folder under root, upload a sample image into that folder, then wait for processing
(same upload + poll pipeline as 03, with directory_id targeting the new folder).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import get_json, post_json, print_json, require_api_key, upload_local_file, wait_for_file_processing

# =============================================================================
# Base settings
# =============================================================================
API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"
# Default demo asset (must sit next to this script).
SAMPLE_UPLOAD_FILENAME = "test1.png"
SAMPLE_UPLOAD_PATH = Path(__file__).resolve().parent / SAMPLE_UPLOAD_FILENAME
# Distinct name so learners can spot this script's folder in the vault UI.
FOLDER_NAME = "Example 04 - create_folder_and_upload"


def main() -> None:
    require_api_key(API_KEY)

    # ==========================================
    # 1. Create directory under root (POST /directories/)
    # ==========================================
    print(f"Creating folder {FOLDER_NAME!r}...")
    created = post_json(
        API_BASE_URL,
        API_KEY,
        "/directories/",
        {"directory_name": FOLDER_NAME, "parent_directory_id": None},
    )
    print("\n--- Create directory response ---")
    print_json(created)
    dir_id = str(created["directory_id"])

    # ==========================================
    # 2. Upload into that folder (POST /files/)
    # ==========================================
    print(f"Uploading {SAMPLE_UPLOAD_FILENAME!r} into the new folder...")
    up = upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH, directory_id=dir_id)
    print_json(up)
    file_id = str(up["file_id"])

    # ==========================================
    # 3. Poll processing status (POST /files/processing-status)
    # ==========================================
    print("Waiting for background processing (summary + snapshot)...")
    final = wait_for_file_processing(API_BASE_URL, API_KEY, file_id)
    print("\n--- Final processing row ---")
    print_json(final)

    # ==========================================
    # 4. List files inside the folder (GET /files/)
    # ==========================================
    print("Listing files in the new folder...")
    inside = get_json(API_BASE_URL, API_KEY, "/files/", {"directory_id": dir_id})
    print("\n--- Files in folder ---")
    print_json(inside)


if __name__ == "__main__":
    main()

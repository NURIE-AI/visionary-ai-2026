#!/usr/bin/env python3
"""
User flow: create folder → upload to root → wait → move file into folder → list inside folder
(matches organize-then-open-folder in the UI).
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
SAMPLE_UPLOAD_FILENAME = "test1.png"
SAMPLE_UPLOAD_PATH = Path(__file__).resolve().parent / SAMPLE_UPLOAD_FILENAME
# Distinct name so learners can spot this script's folder in the vault UI.
FOLDER_NAME = "Example 05 - move_file_to_folder"


def main() -> None:
    require_api_key(API_KEY)

    # ==========================================
    # 1. Create target folder
    # ==========================================
    print("Creating target folder...")
    folder = post_json(
        API_BASE_URL,
        API_KEY,
        "/directories/",
        {"directory_name": FOLDER_NAME, "parent_directory_id": None},
    )
    dir_id = str(folder["directory_id"])
    print(f"Folder id: {dir_id}")

    # ==========================================
    # 2. Upload file to vault root
    # ==========================================
    print(f"Uploading {SAMPLE_UPLOAD_FILENAME!r} to root...")
    up = upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH)
    file_id = str(up["file_id"])

    # ==========================================
    # 3. Wait for processing
    # ==========================================
    print("Waiting for processing...")
    wait_for_file_processing(API_BASE_URL, API_KEY, file_id)

    # ==========================================
    # 4. Attach file to folder (POST /directories/add-files)
    # ==========================================
    print("Adding file to folder...")
    moved = post_json(
        API_BASE_URL,
        API_KEY,
        "/directories/add-files",
        {"file_ids": [file_id], "directory_id": dir_id, "is_primary": True},
    )
    print("\n--- add-files response ---")
    print_json(moved)

    # ==========================================
    # 5. List files inside the folder
    # ==========================================
    print("Listing files inside folder...")
    inside = get_json(API_BASE_URL, API_KEY, "/files/", {"directory_id": dir_id})
    print("\n--- Files in folder ---")
    print_json(inside)


if __name__ == "__main__":
    main()

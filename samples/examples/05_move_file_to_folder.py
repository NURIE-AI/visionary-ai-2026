#!/usr/bin/env python3
"""
User flow: create folder → upload to root → wait → move file into folder → list inside folder
(matches organize-then-open-folder in the UI).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import (
    get_json,
    patch_json,
    post_json,
    print_json,
    print_phase_banner,
    require_api_key,
    run_with_spinner,
    upload_local_file,
    wait_for_file_processing,
)

# =============================================================================
# Base settings
# =============================================================================
API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"
SAMPLE_UPLOAD_FILENAME = "test1.png"
SAMPLE_UPLOAD_PATH = Path(__file__).resolve().parent / SAMPLE_UPLOAD_FILENAME
# Distinct name so learners can spot this script's folder in the VaultSage UI.
FOLDER_NAME = "Example 05 - move_file_to_folder"


def main() -> None:
    require_api_key(API_KEY)

    print_phase_banner("Folder", "Create target directory (POST /directories/)")
    folder = run_with_spinner(
        "POST /directories/",
        lambda: post_json(
            API_BASE_URL,
            API_KEY,
            "/directories/",
            {"directory_name": FOLDER_NAME, "parent_directory_id": None},
        ),
    )
    print("\n[Result] Create directory response")
    print_json(folder)
    dir_id = str(folder["directory_id"])
    print(f"\n[Folder] directory_id={dir_id}")

    print_phase_banner("Upload", "Send file to VaultSage root (POST /files/)")
    print(f"\n[Upload] Sending {SAMPLE_UPLOAD_FILENAME!r}…")
    up = run_with_spinner(
        "POST /files/ (multipart)",
        lambda: upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH),
    )
    file_id = str(up["file_id"])
    print(f"[Upload] file_id={file_id}")

    print_phase_banner("Waiting", "VaultSage is processing the uploaded file (background jobs)")
    run_with_spinner(
        "Polling processing status (summary + snapshot)",
        lambda: wait_for_file_processing(API_BASE_URL, API_KEY, file_id, quiet=True),
    )
    print("\n[Wait] File processing finished — moving file.\n")

    print_phase_banner("Move", "Move file into folder (PATCH /files/{file_id}/move)")
    move_path = f"/files/{file_id}/move"
    moved = run_with_spinner(
        "PATCH /files/.../move",
        lambda: patch_json(
            API_BASE_URL,
            API_KEY,
            move_path,
            {"new_directory_id": dir_id},
        ),
    )
    print("\n[Result] Move file response")
    print_json(moved)

    print_phase_banner("List", "Files inside the folder (GET /files/)")
    inside = run_with_spinner(
        "GET /files/",
        lambda: get_json(API_BASE_URL, API_KEY, "/files/", {"directory_id": dir_id}),
    )
    print("\n[Result] Files in folder")
    print_json(inside)


if __name__ == "__main__":
    main()

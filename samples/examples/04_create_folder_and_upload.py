#!/usr/bin/env python3
"""
User flow: create a folder under root, upload a sample image into that folder, then wait for processing
(same upload + poll pipeline as 03, with directory_id targeting the new folder).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import (
    get_json,
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
# Default demo asset (must sit next to this script).
SAMPLE_UPLOAD_FILENAME = "test1.png"
SAMPLE_UPLOAD_PATH = Path(__file__).resolve().parent / SAMPLE_UPLOAD_FILENAME
# Distinct name so learners can spot this script's folder in the VaultSage UI.
FOLDER_NAME = "Example 04 - create_folder_and_upload"


def main() -> None:
    require_api_key(API_KEY)

    print_phase_banner("Folder", "Create directory under root (POST /directories/)")
    created = run_with_spinner(
        "POST /directories/",
        lambda: post_json(
            API_BASE_URL,
            API_KEY,
            "/directories/",
            {"directory_name": FOLDER_NAME, "parent_directory_id": None},
        ),
    )
    print("\n[Result] Create directory response")
    print_json(created)
    dir_id = str(created["directory_id"])

    print_phase_banner("Upload", f"Upload into folder {FOLDER_NAME!r} (POST /files/)")
    print(f"\n[Upload] Sending {SAMPLE_UPLOAD_FILENAME!r}…")
    up = run_with_spinner(
        "POST /files/ (multipart)",
        lambda: upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH, directory_id=dir_id),
    )
    file_id = str(up["file_id"])
    print(f"[Upload] file_id={file_id}")
    print("\n[Result] Upload response")
    print_json(up)

    print_phase_banner("Waiting", "VaultSage is processing the uploaded file (background jobs)")
    final = run_with_spinner(
        "Polling processing status (summary + snapshot)",
        lambda: wait_for_file_processing(API_BASE_URL, API_KEY, file_id, quiet=True),
    )
    print("\n[Wait] File processing finished — showing last status row.\n")
    print("\n[Result] Final processing row")
    print_json(final)

    print_phase_banner("List", "Files in the new folder (GET /files/)")
    inside = run_with_spinner(
        "GET /files/",
        lambda: get_json(API_BASE_URL, API_KEY, "/files/", {"directory_id": dir_id}),
    )
    print("\n[Result] Files in folder")
    print_json(inside)


if __name__ == "__main__":
    main()

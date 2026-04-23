#!/usr/bin/env python3
"""
Share links tutorial: create a share from an uploaded file, then list what you own — or list only.

- Default (LIST_ONLY = False): upload sample file → wait for processing → POST /share/ → GET /share/user-shares
- Set LIST_ONLY = True: only GET /share/user-shares (refresh Shared links without creating a new share)
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
# True = skip upload/create; only fetch GET /share/user-shares.
LIST_ONLY = False


def print_user_shares(*, after_create_flow: bool) -> None:
    print("Listing your shares (GET /share/user-shares)...")
    data = get_json(API_BASE_URL, API_KEY, "/share/user-shares")
    print("\n--- User shares ---")
    print_json(data)

    items = data.get("items") if isinstance(data, dict) else None
    total = data.get("total") if isinstance(data, dict) else None
    if items is not None and len(items) == 0 and (total is None or total == 0):
        if after_create_flow:
            print(
                "\nTip: List is still empty after create — check the create-share response above "
                "or your account permissions.",
            )
        else:
            print(
                f"\nTip: List is empty — set LIST_ONLY = False and run again to upload "
                f"{SAMPLE_UPLOAD_FILENAME!r} and create a sample share, then refresh the list.",
            )


def main() -> None:
    require_api_key(API_KEY)

    if LIST_ONLY:
        print_user_shares(after_create_flow=False)
        return

    # ==========================================
    # 1. Upload a file to share (POST /files/)
    # ==========================================
    print(f"Uploading {SAMPLE_UPLOAD_FILENAME!r}...")
    up = upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH)
    file_id = str(up["file_id"])

    # ==========================================
    # 2. Wait for processing (POST /files/processing-status)
    # ==========================================
    print("Waiting for processing...")
    wait_for_file_processing(API_BASE_URL, API_KEY, file_id)

    # ==========================================
    # 3. Create share (POST /share/)
    # ==========================================
    print("Creating share link...")
    code = post_json(
        API_BASE_URL,
        API_KEY,
        "/share/",
        {
            "file_ids": [file_id],
            "directory_ids": None,
            "emails": None,
            "message": None,
            "password": None,
            "expire_at": None,
        },
    )
    print("\n--- Share create response ---")
    print_json(code)

    # ==========================================
    # 4. List shares you own (GET /share/user-shares)
    # ==========================================
    print_user_shares(after_create_flow=True)


if __name__ == "__main__":
    main()

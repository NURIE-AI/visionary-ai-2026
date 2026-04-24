#!/usr/bin/env python3
"""
Create share links: upload sample file → wait for processing → POST /share/ → GET /share/user-shares,
or list-only mode.

- Default (LIST_ONLY = False): full create flow above
- LIST_ONLY = True: only GET /share/user-shares (refresh without creating a new share)
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
SAMPLE_UPLOAD_FILENAME = "test1.png"
SAMPLE_UPLOAD_PATH = Path(__file__).resolve().parent / SAMPLE_UPLOAD_FILENAME
# True = skip upload/create; only fetch GET /share/user-shares.
LIST_ONLY = False


def print_user_shares(*, after_create_flow: bool) -> None:
    print_phase_banner("Shares", "List links you own (GET /share/user-shares)")
    data = run_with_spinner(
        "GET /share/user-shares",
        lambda: get_json(API_BASE_URL, API_KEY, "/share/user-shares"),
    )
    print("\n[Result] User shares")
    print_json(data)

    items = data.get("items") if isinstance(data, dict) else None
    total = data.get("total") if isinstance(data, dict) else None
    if items is not None and len(items) == 0 and (total is None or total == 0):
        if after_create_flow:
            print(
                "\n[Tip] List is still empty after create — check the create-share response above "
                "or your account permissions.",
            )
        else:
            print(
                f"\n[Tip] List is empty — set LIST_ONLY = False and run again to upload "
                f"{SAMPLE_UPLOAD_FILENAME!r} and create a sample share, then refresh the list.",
            )


def main() -> None:
    require_api_key(API_KEY)

    if LIST_ONLY:
        print_user_shares(after_create_flow=False)
        return

    print_phase_banner("Upload", "File to share (POST /files/)")
    print(f"\n[Upload] Sending {SAMPLE_UPLOAD_FILENAME!r}…")
    up = run_with_spinner(
        "POST /files/ (multipart)",
        lambda: upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH),
    )
    file_id = str(up["file_id"])
    print(f"[Upload] file_id={file_id}")
    print("\n[Result] Upload response")
    print_json(up)

    print_phase_banner("Waiting", "VaultSage is processing the uploaded file (background jobs)")
    run_with_spinner(
        "Polling processing status (summary + snapshot)",
        lambda: wait_for_file_processing(API_BASE_URL, API_KEY, file_id, quiet=True),
    )
    print("\n[Wait] File processing finished — creating share.\n")

    print_phase_banner("Share", "Create share link (POST /share/)")
    code = run_with_spinner(
        "POST /share/",
        lambda: post_json(
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
        ),
    )
    print("\n[Result] Share create response")
    print_json(code)

    print_user_shares(after_create_flow=True)


if __name__ == "__main__":
    main()

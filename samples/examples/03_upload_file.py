#!/usr/bin/env python3
"""
User flow: upload a sample image from this folder, then wait until background extraction / preview
tasks finish (same intent as the Files UI spinner before the file is “ready”).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import (
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
# Default demo asset (must sit next to this script); change the name to upload a different file.
SAMPLE_UPLOAD_FILENAME = "test1.png"
SAMPLE_UPLOAD_PATH = Path(__file__).resolve().parent / SAMPLE_UPLOAD_FILENAME


def main() -> None:
    require_api_key(API_KEY)

    print_phase_banner("Upload", "Send file to VaultSage (POST /files/)")
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
    final = run_with_spinner(
        "Polling processing status (summary + snapshot)",
        lambda: wait_for_file_processing(API_BASE_URL, API_KEY, file_id, quiet=True),
    )
    print("\n[Wait] File processing finished — showing last status row.\n")
    print("\n[Result] Final processing row")
    print_json(final)


if __name__ == "__main__":
    main()

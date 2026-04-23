#!/usr/bin/env python3
"""
User flow: upload a sample image from this folder, then wait until background extraction / preview
tasks finish (same intent as the Files UI spinner before the file is “ready”).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import print_json, require_api_key, upload_local_file, wait_for_file_processing

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

    # ==========================================
    # 1. Upload (POST /files/)
    # ==========================================
    print(f"Uploading {SAMPLE_UPLOAD_FILENAME!r}...")
    up = upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH)
    print_json(up)
    file_id = str(up["file_id"])
    print(f"Uploaded file id: {file_id}")

    # ==========================================
    # 2. Poll processing status (POST /files/processing-status)
    # ==========================================
    print("Waiting for background processing (summary + snapshot)...")
    final = wait_for_file_processing(API_BASE_URL, API_KEY, file_id)
    print("\n--- Final processing row ---")
    print_json(final)


if __name__ == "__main__":
    main()

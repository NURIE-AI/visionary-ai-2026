#!/usr/bin/env python3
"""
User flow: Smart Upload an image → poll processing (summary-only, relaxed timeout) → one chat turn.
This is the canonical numbered tutorial for the flow previously documented only in samples/sample_file.py.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import (
    post_json,
    require_api_key,
    smart_upload_file,
    wait_summary_status_relaxed,
)

# =============================================================================
# Base settings
# =============================================================================
API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"
SAMPLE_UPLOAD_FILENAME = "test1.png"
SAMPLE_UPLOAD_PATH = Path(__file__).resolve().parent / SAMPLE_UPLOAD_FILENAME
CHAT_MESSAGE = "What content inside this image?"


def main() -> None:
    require_api_key(API_KEY)

    # ==========================================
    # 1. Smart Upload (POST /smart-upload/)
    # ==========================================
    print(f"Smart-uploading {SAMPLE_UPLOAD_FILENAME!r}...")
    file_id = smart_upload_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH)
    print(f"Image uploaded successfully! File ID: {file_id}")

    # ==========================================
    # 2. Wait for background extraction (POST /files/processing-status)
    # ==========================================
    wait_summary_status_relaxed(API_BASE_URL, API_KEY, file_id)

    # ==========================================
    # 3. Chat with image (POST /chat/message/v2)
    # ==========================================
    print("Sending chat message...")
    chat_result = post_json(
        API_BASE_URL,
        API_KEY,
        "/chat/message/v2",
        {
            "messages": [
                {
                    "actor": "user",
                    "content": CHAT_MESSAGE,
                    "file_ids": [file_id],
                }
            ],
            "persist": False,
        },
    )
    print("\n--- Assistant Response ---")
    print(chat_result.get("result"))


if __name__ == "__main__":
    main()

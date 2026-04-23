#!/usr/bin/env python3
"""
User flow: Ask Sage with file — upload → wait → first chat turn (with file) → follow-up in same thread
→ list saved chats. The first persisted turn covers what a separate single-turn example would do;
stop after step 3 if you only want one reply. For **smart-upload** + relaxed processing poll, use
`09_smart_upload_image_chat.py`.
"""

import os
import sys
import uuid
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


def main() -> None:
    require_api_key(API_KEY)

    # ==========================================
    # 1. Upload file to ground the conversation
    # ==========================================
    print(f"Uploading {SAMPLE_UPLOAD_FILENAME!r}...")
    up = upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH)
    fid = str(up["file_id"])

    # ==========================================
    # 2. Wait for processing
    # ==========================================
    print("Waiting for processing...")
    wait_for_file_processing(API_BASE_URL, API_KEY, fid)

    # ==========================================
    # 3. First message: persisted chat, file on user message
    # ==========================================
    print("First chat turn (persist=True)...")
    first = post_json(
        API_BASE_URL,
        API_KEY,
        "/chat/message/v2",
        {
            "messages": [
                {
                    "actor": "user",
                    "content": "What content inside this image?",
                    "file_ids": [fid],
                },
            ],
            "persist": True,
        },
    )
    print("\n--- First response ---")
    print(first.get("result"))

    raw_id = first.get("new_chat_id")
    if not raw_id:
        print("Error: Expected new_chat_id in response.")
        sys.exit(1)
    cid = str(uuid.UUID(str(raw_id)))

    # ==========================================
    # 4. Follow-up in the same thread
    # ==========================================
    print("\nFollow-up in same chat...")
    second = post_json(
        API_BASE_URL,
        API_KEY,
        "/chat/message/v2",
        {
            "messages": [
                {
                    "actor": "user",
                    "content": "Name one detail you would double-check from that description.",
                },
            ],
            "chat_id": cid,
            "persist": True,
        },
    )
    print("\n--- Second response ---")
    print(second.get("result"))

    # ==========================================
    # 5. List saved chats (GET /chat/)
    # ==========================================
    print("\nListing saved chats...")
    chats = get_json(API_BASE_URL, API_KEY, "/chat/")
    print("\n--- Chats ---")
    print_json(chats)


if __name__ == "__main__":
    main()

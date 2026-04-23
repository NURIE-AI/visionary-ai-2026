#!/usr/bin/env python3
"""
Smart upload with chat: POST /smart-upload/ for one image → poll ``task_summary_status`` only (60s cap,
then continue) → one ``POST /chat/message/v2`` turn with ``file_ids``. Canonical replacement for the
legacy ``samples/sample_file.py`` story.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import (
    post_json,
    print_chat_turn,
    print_phase_banner,
    require_api_key,
    run_with_spinner,
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
CHAT_TOTAL_USER_TURNS = 1


def main() -> None:
    require_api_key(API_KEY)

    # --- Smart upload ---------------------------------------------------------
    print_phase_banner("Upload", "Smart-upload image (POST /smart-upload/)")
    print(f"\n[Smart upload] Sending {SAMPLE_UPLOAD_FILENAME!r}…")
    file_id = run_with_spinner(
        "Uploading via smart-upload endpoint",
        lambda: smart_upload_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH),
    )
    print(f"[Smart upload] file_id={file_id}")

    # --- Relaxed summary wait -------------------------------------------------
    print_phase_banner("Waiting", "Background image extraction (summary-only poll, max ~60s)")
    run_with_spinner(
        "Polling summary status (relaxed mode)",
        lambda: wait_summary_status_relaxed(API_BASE_URL, API_KEY, file_id, quiet=True),
    )
    print("\n[Wait] Polling phase ended — sending chat.\n")

    # --- Single chat turn -----------------------------------------------------
    print_chat_turn(turn=1, total=CHAT_TOTAL_USER_TURNS, role="User", text=CHAT_MESSAGE)
    chat_result = run_with_spinner(
        "Waiting for VaultSage reply",
        lambda: post_json(
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
        ),
    )
    print_chat_turn(
        turn=1,
        total=CHAT_TOTAL_USER_TURNS,
        role="VaultSage",
        text=str(chat_result.get("result") or "[empty response]"),
    )


if __name__ == "__main__":
    main()

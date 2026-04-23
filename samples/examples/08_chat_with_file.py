#!/usr/bin/env python3
"""
Chat with file: upload → wait for processing → first persisted chat turn with ``file_ids`` → follow-up
in the same thread. (Optional list-chats block is commented in the script.) For **smart-upload** plus
relaxed summary polling, use `09_smart_upload_with_chat.py`.
"""

import os
import sys
import uuid
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_api import (
    get_json,
    post_json,
    print_chat_turn,
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

CHAT_TOTAL_USER_TURNS = 2
QUESTION_FIRST = "What content inside this image?"


def second_turn_user_question() -> str:
    """Anchor today's date; ask for attention points and impacts as a bullet list."""
    today = date.today()
    return (
        f"For context: today is {today.isoformat()} ({today.strftime('%A')}) in the environment "
        "where this script runs.\n\n"
        "Using this file and your previous answer, reply with a concise bullet list covering:\n"
        "- Important attention points someone should keep in mind about this document\n"
        "- Possible impacts or implications (e.g., decisions, risks, timelines, obligations, stakeholders)"
    )


def main() -> None:
    require_api_key(API_KEY)

    # --- Upload ----------------------------------------------------------------
    print_phase_banner("Upload", "Send file to VaultSage (POST /files/)")
    print(f"\n[Upload] Sending {SAMPLE_UPLOAD_FILENAME!r}…")
    up = run_with_spinner(
        "POST /files/ (multipart)",
        lambda: upload_local_file(API_BASE_URL, API_KEY, SAMPLE_UPLOAD_PATH),
    )
    fid = str(up["file_id"])
    print(f"[Upload] file_id={fid}")

    # --- Wait for file processing ---------------------------------------------
    print_phase_banner("Waiting", "VaultSage is processing the uploaded file (background jobs)")
    run_with_spinner(
        "Polling processing status (summary + snapshot)",
        lambda: wait_for_file_processing(API_BASE_URL, API_KEY, fid, quiet=True),
    )
    print("\n[Wait] File processing finished — continuing to chat.\n")

    # --- Turn 1: user ---------------------------------------------------------
    print_chat_turn(turn=1, total=CHAT_TOTAL_USER_TURNS, role="User", text=QUESTION_FIRST)
    first = run_with_spinner(
        "Waiting for VaultSage reply (turn 1)",
        lambda: post_json(
            API_BASE_URL,
            API_KEY,
            "/chat/message/v2",
            {
                "messages": [
                    {
                        "actor": "user",
                        "content": QUESTION_FIRST,
                        "file_ids": [fid],
                    },
                ],
                "persist": True,
            },
        ),
    )
    print_chat_turn(
        turn=1,
        total=CHAT_TOTAL_USER_TURNS,
        role="VaultSage",
        text=str(first.get("result") or "[empty response]"),
    )

    raw_id = first.get("new_chat_id")
    if not raw_id:
        print("Error: Expected new_chat_id in response.")
        sys.exit(1)
    cid = str(uuid.UUID(str(raw_id)))

    # --- Turn 2: user ---------------------------------------------------------
    question_second = second_turn_user_question()
    print_chat_turn(turn=2, total=CHAT_TOTAL_USER_TURNS, role="User", text=question_second)
    second = run_with_spinner(
        "Waiting for VaultSage reply (turn 2)",
        lambda: post_json(
            API_BASE_URL,
            API_KEY,
            "/chat/message/v2",
            {
                "messages": [
                    {
                        "actor": "user",
                        "content": question_second,
                    },
                ],
                "chat_id": cid,
                "persist": True,
            },
        ),
    )
    print_chat_turn(
        turn=2,
        total=CHAT_TOTAL_USER_TURNS,
        role="VaultSage",
        text=str(second.get("result") or "[empty response]"),
    )

    # # --- List chats -----------------------------------------------------------
    # print("\n" + "=" * 72)
    # print(" API — Listing saved chats (GET /chat/)")
    # print("=" * 72)
    # chats = run_with_spinner(
    #     "Fetching chat list",
    #     lambda: get_json(API_BASE_URL, API_KEY, "/chat/"),
    # )
    # print("\n--- Raw JSON ---")
    # print_json(chats)


if __name__ == "__main__":
    main()

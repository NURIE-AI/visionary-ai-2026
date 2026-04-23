#!/usr/bin/env python3
"""
User flow: account settings — fetch profile, update display name, fetch profile again to verify.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from common_api import require_api_key

API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"
# Must differ from current name if the API rejects no-op updates.
NEW_DISPLAY_NAME = "API Example User"


def main() -> None:
    require_api_key(API_KEY)
    headers_get = {"x-api-key": API_KEY}
    headers_patch = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/users/me"

    # ==========================================
    # 1. Fetch current user (GET /users/me)
    # ==========================================
    print("Fetching profile (before update)...")
    r1 = requests.get(url, headers=headers_get, timeout=60)
    r1.raise_for_status()
    print("\n--- Profile (before) ---")
    print(json.dumps(r1.json(), indent=2))

    # ==========================================
    # 2. Update display name (PATCH /users/me)
    # ==========================================
    print(f"\nUpdating display name to {NEW_DISPLAY_NAME!r}...")
    r2 = requests.patch(url, headers=headers_patch, json={"full_name": NEW_DISPLAY_NAME}, timeout=60)
    r2.raise_for_status()
    print("\n--- PATCH response ---")
    print(json.dumps(r2.json(), indent=2))

    # ==========================================
    # 3. Fetch profile again (GET /users/me)
    # ==========================================
    print("\nFetching profile (after update)...")
    r3 = requests.get(url, headers=headers_get, timeout=60)
    r3.raise_for_status()
    print("\n--- Profile (after) ---")
    print(json.dumps(r3.json(), indent=2))


if __name__ == "__main__":
    main()

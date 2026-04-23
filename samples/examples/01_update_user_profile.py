#!/usr/bin/env python3
"""
User flow: update user profile — GET /users/me, PATCH display name, print JSON responses.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from common_api import print_json, print_phase_banner, require_api_key, run_with_spinner

API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"
# Must differ from current name if the API rejects no-op updates.
NEW_DISPLAY_NAME = "API Example User"


def main() -> None:
    require_api_key(API_KEY)
    headers_get = {"x-api-key": API_KEY}
    headers_patch = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    url = f"{API_BASE_URL}/users/me"

    def get_me() -> requests.Response:
        r = requests.get(url, headers=headers_get, timeout=60)
        r.raise_for_status()
        return r

    print_phase_banner("Profile", "Fetch current user (GET /users/me)")
    r1 = run_with_spinner("GET /users/me (before update)", get_me)
    print("\n[Result] Profile (before update)")
    print_json(r1.json())

    def patch_me() -> requests.Response:
        r = requests.patch(
            url,
            headers=headers_patch,
            json={"full_name": NEW_DISPLAY_NAME},
            timeout=60,
        )
        r.raise_for_status()
        return r

    print_phase_banner("Profile", f"Update display name to {NEW_DISPLAY_NAME!r} (PATCH /users/me)")
    r2 = run_with_spinner("PATCH /users/me", patch_me)
    print("\n[Result] PATCH /users/me response")
    print_json(r2.json())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""User flow: open storage dashboard summary (GET dashboard)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from common_api import print_json, print_phase_banner, require_api_key, run_with_spinner

API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"


def main() -> None:
    require_api_key(API_KEY)
    headers = {"x-api-key": API_KEY}
    url = f"{API_BASE_URL}/dashboard/"

    def load_dashboard() -> requests.Response:
        r = requests.get(url, headers=headers, timeout=60)
        r.raise_for_status()
        return r

    print_phase_banner("Dashboard", "Load storage summary (GET /dashboard/)")
    r = run_with_spinner("GET /dashboard/", load_dashboard)
    print("\n[Result] Dashboard JSON")
    print_json(r.json())


if __name__ == "__main__":
    main()

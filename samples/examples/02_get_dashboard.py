#!/usr/bin/env python3
"""User flow: open storage dashboard summary (GET dashboard)."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests

from common_api import require_api_key

API_BASE_URL = "https://api.vaultsage.ai/api/v1"
API_KEY = "YOUR_API_KEY"


def main() -> None:
    require_api_key(API_KEY)
    headers = {"x-api-key": API_KEY}

    # ==========================================
    # 1. Load dashboard (GET /dashboard/)
    # ==========================================
    url = f"{API_BASE_URL}/dashboard/"
    print("Fetching dashboard...")
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    print("\n--- Dashboard JSON ---")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()

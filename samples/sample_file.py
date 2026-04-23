"""
Legacy entry point for the Smart Upload → processing poll → chat flow.

Canonical tutorial script (same behavior): run
  python samples/examples/09_smart_upload_image_chat.py
from the repo root, or execute this file — it delegates to that script.
"""

import os
import runpy

_EXAMPLES_MAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples", "09_smart_upload_image_chat.py")


if __name__ == "__main__":
    runpy.run_path(_EXAMPLES_MAIN, run_name="__main__")

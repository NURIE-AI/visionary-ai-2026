# Shared helpers for tutorial scripts in this directory. All comments in English.
"""VaultSage tutorial HTTP helpers.

What this module provides
-------------------------
``require_api_key`` — exit if the script still has a placeholder key.

``get_json`` / ``post_json`` / ``patch_json`` — small ``requests`` wrappers with the
``x-api-key`` header and consistent error handling.

``upload_local_file`` — multipart ``POST .../files/`` for a local file (path from each script’s settings).

``smart_upload_file`` — multipart ``POST .../smart-upload/`` for one local image file.

``wait_for_file_processing`` — poll ``POST .../files/processing-status`` until both
summary and snapshot tasks finish (strict; use after normal uploads).

``wait_summary_status_relaxed`` — poll the same endpoint but only
``task_summary_status``; 60s cap then continue (legacy ``sample_file.py`` behaviour).

``print_json`` — pretty-print any JSON-serialisable value.

``run_with_spinner`` — run a blocking callable while showing an inline ``...`` animation.

``print_phase_banner`` — print a framed phase header (same layout as ``08`` / ``09`` tutorials).

``print_chat_turn`` — print a user/VaultSage “chat window” block (turn *n* / *total*).
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Final, TypeVar

import requests

_T = TypeVar("_T")

_BAD_API_KEY_PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {"nvpk_REPLACE_ME", "YOUR_API_KEY", "YOUR API KEY", ""},
)
_TIMEOUT_GET: Final[int] = 60
_TIMEOUT_POST: Final[int] = 120
# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------


def require_api_key(api_key: str) -> None:
    """Exit with a clear message if ``api_key`` is still a placeholder."""
    if api_key in _BAD_API_KEY_PLACEHOLDERS:
        print("Error: Set API_KEY to your personal API key (Settings → API Keys).")
        sys.exit(1)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _http_fail(context: str, response: requests.Response) -> None:
    print(f"{context} HTTP {response.status_code}: {response.text}")
    sys.exit(1)


def _headers_key(api_key: str) -> dict[str, str]:
    return {"x-api-key": api_key}


def _headers_json(api_key: str) -> dict[str, str]:
    return {"x-api-key": api_key, "Content-Type": "application/json"}


def get_json(
    api_base_url: str,
    api_key: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """GET ``path`` (leading slash) under ``api_base_url``."""
    url = f"{api_base_url}{path}"
    response = requests.get(
        url,
        headers=_headers_key(api_key),
        params=params or {},
        timeout=_TIMEOUT_GET,
    )
    if not response.ok:
        _http_fail(path, response)
    return response.json()


def post_json(api_base_url: str, api_key: str, path: str, body: dict[str, Any]) -> Any:
    """POST JSON to ``path`` (leading slash) under ``api_base_url``."""
    url = f"{api_base_url}{path}"
    response = requests.post(
        url,
        headers=_headers_json(api_key),
        json=body,
        timeout=_TIMEOUT_POST,
    )
    if not response.ok:
        _http_fail(path, response)
    return response.json()


def patch_json(api_base_url: str, api_key: str, path: str, body: dict[str, Any]) -> Any:
    """PATCH JSON to ``path`` (leading slash) under ``api_base_url``."""
    url = f"{api_base_url}{path}"
    response = requests.patch(
        url,
        headers=_headers_json(api_key),
        json=body,
        timeout=_TIMEOUT_POST,
    )
    if not response.ok:
        _http_fail(path, response)
    return response.json()


def print_json(data: Any) -> None:
    """Print *data* as indented JSON (for tutorial output)."""
    print(json.dumps(data, indent=2, default=str))


PHASE_BANNER_WIDTH: Final[int] = 72


def print_phase_banner(phase: str, detail: str) -> None:
    """
    Print a three-line section frame (same style as ``08_chat_multi_turn`` / ``09_smart_upload_image_chat``).

    *phase* is a short label (shown uppercase); *detail* explains the step on one line.
    """
    w = PHASE_BANNER_WIDTH
    bar = "=" * w
    print("\n" + bar)
    print(f" {phase.strip().upper()} — {detail}")
    print(bar)


# ---------------------------------------------------------------------------
# Console UX (tutorial scripts)
# ---------------------------------------------------------------------------


def print_chat_turn(*, turn: int, total: int, role: str, text: str, width: int = PHASE_BANNER_WIDTH) -> None:
    """Print one framed block like a chat thread line (role is e.g. ``User`` or ``VaultSage``)."""
    label = f"Turn {turn} / {total}  |  {role.strip().upper()}"
    bar = "=" * width
    print(f"\n{bar}")
    print(f" {label}")
    print("-" * width)
    body = text.strip() if text.strip() else "[empty message]"
    for line in body.splitlines():
        print(f" {line}")
    print(bar)


def run_with_spinner(message: str, func: Callable[[], _T]) -> _T:
    """
    Run *func* while printing ``message`` with a cycling ``.`` animation on one line.

    Clears the spinner line when *func* returns or raises.
    """
    stop = threading.Event()

    def _spin() -> None:
        step = 0
        pad = max(len(message) + 8, 24)
        while not stop.wait(0.22):
            step += 1
            dots = "." * (1 + (step % 3))
            sys.stdout.write(("\r" + message + " " + dots).ljust(pad))
            sys.stdout.flush()

    thread = threading.Thread(target=_spin, daemon=True)
    thread.start()
    try:
        return func()
    finally:
        stop.set()
        thread.join(timeout=3.0)
        sys.stdout.write("\r" + " " * 120 + "\r")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Uploads
# ---------------------------------------------------------------------------


def upload_local_file(
    api_base_url: str,
    api_key: str,
    file_path: Path,
    *,
    directory_id: str | None = None,
    conflict_resolution: str = "keep",
    mime: str = "image/png",
) -> dict[str, Any]:
    """Upload one local file via ``POST .../files/`` (multipart field name ``files``)."""
    if not file_path.is_file():
        print(f"Error: Missing file {file_path}")
        sys.exit(1)

    url = f"{api_base_url}/files/"
    params: dict[str, str] = {"conflict_resolution": conflict_resolution}
    if directory_id:
        params["directory_id"] = str(directory_id)

    with file_path.open("rb") as file_handle:
        multipart = [("files", (file_path.name, file_handle, mime))]
        response = requests.post(
            url,
            headers=_headers_key(api_key),
            files=multipart,
            params=params,
            timeout=_TIMEOUT_POST,
        )

    if not response.ok:
        _http_fail("Upload", response)
    return response.json()


def smart_upload_file(
    api_base_url: str,
    api_key: str,
    file_path: Path,
    *,
    mime: str = "image/png",
) -> str:
    """
    Smart-upload one file; returns the new file id (``response[0]['id']``).

    Multipart layout matches the legacy ``samples/sample_file.py`` contract.
    """
    if not file_path.is_file():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    filename = file_path.name
    request_form = {
        "files": [
            {
                "name": filename,
                "directory_id": None,
                "new_directory": None,
            }
        ]
    }
    url = f"{api_base_url}/smart-upload/"

    with file_path.open("rb") as file_handle:
        data = {"request_form": json.dumps(request_form)}
        files = [("files", (filename, file_handle, mime))]
        response = requests.post(
            url,
            data=data,
            files=files,
            headers=_headers_key(api_key),
            timeout=_TIMEOUT_POST,
        )

    if not response.ok:
        _http_fail("smart-upload/", response)

    uploaded = response.json()
    if not uploaded or not isinstance(uploaded, list):
        print("Error: smart-upload response must be a non-empty list.")
        sys.exit(1)
    return str(uploaded[0]["id"])


# ---------------------------------------------------------------------------
# Processing status (shared POST, two wait strategies)
# ---------------------------------------------------------------------------


def _post_processing_status(
    api_base_url: str,
    api_key: str,
    file_ids: list[str],
) -> dict[str, Any]:
    return post_json(api_base_url, api_key, "/files/processing-status", {"file_ids": file_ids})


def _processing_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise API shape: ``results`` or ``result`` -> list of row dicts."""
    raw = payload.get("results") or payload.get("result") or []
    return raw if isinstance(raw, list) else []


def _status_terminal(status: str) -> bool:
    return status in ("completed", "failed", "skipped")


def _strict_processing_done(row: dict[str, Any]) -> bool:
    """True when both summary and snapshot reached a terminal state."""
    if row.get("file_exists") is False:
        return False
    return _status_terminal(row["task_summary_status"]) and _status_terminal(row["task_snapshot_status"])


def wait_for_file_processing(
    api_base_url: str,
    api_key: str,
    file_id: str,
    *,
    poll_interval_sec: float = 2.0,
    timeout_sec: float = 300.0,
    quiet: bool = False,
) -> dict[str, Any]:
    """
    Poll until summary **and** snapshot leave pending/processing (UI “file ready”).

    On timeout or missing file, the process exits with an error.
    If *quiet* is True, do not print per-poll status lines (use with ``run_with_spinner``).
    """
    deadline = time.monotonic() + timeout_sec
    last: dict[str, Any] = {}

    while time.monotonic() < deadline:
        data = _post_processing_status(api_base_url, api_key, [file_id])
        rows = _processing_rows(data)
        if not rows:
            print("Error: Empty processing status result.")
            sys.exit(1)

        last = rows[0]
        if last.get("file_exists") is False:
            print("Error: File missing or not accessible for processing status.")
            sys.exit(1)

        if not quiet:
            summary = last["task_summary_status"]
            snapshot = last["task_snapshot_status"]
            progress = last.get("processing_progress")
            print(
                f"  status: summary={summary} snapshot={snapshot} progress={progress}",
                flush=True,
            )

        if _strict_processing_done(last):
            return last

        time.sleep(poll_interval_sec)

    print("Error: Timed out waiting for file processing.")
    sys.exit(1)


def wait_summary_status_relaxed(
    api_base_url: str,
    api_key: str,
    file_id: str,
    *,
    max_wait_seconds: float = 60.0,
    poll_interval_sec: float = 2.0,
    quiet: bool = False,
) -> None:
    """
    Poll only ``task_summary_status``; stop on completed/failed or after *max_wait_seconds*.

    Unlike ``wait_for_file_processing``, a timeout **does not** exit the process —
    the caller may still proceed (e.g. to chat), matching legacy ``sample_file.py``.
    If *quiet* is True, suppress all internal prints (pair with ``run_with_spinner``).
    """
    deadline = time.monotonic() + max_wait_seconds
    if not quiet:
        print("Waiting for background AI image extraction to complete...")

    while time.monotonic() < deadline:
        data = _post_processing_status(api_base_url, api_key, [file_id])
        rows = _processing_rows(data)
        if rows:
            summary = rows[0].get("task_summary_status")
            if summary == "completed":
                if not quiet:
                    print("Image content successfully extracted!")
                return
            if summary == "failed":
                if not quiet:
                    print(
                        "Image extraction failed. The chat won't be able to see the image content.",
                    )
                return

        time.sleep(poll_interval_sec)

    if not quiet:
        print("Timeout waiting for image processing. Proceeding anyway.")

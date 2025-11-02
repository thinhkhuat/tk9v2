#!/usr/bin/env python3
"""
Interactive CLI to verify/repair/backfill research_sessions.file_count.

It talks to your running FastAPI backend using the endpoints:
- GET  /api/sessions/{session_id}/verify-file-stats?repair=<bool>
- POST /api/sessions/{session_id}/reconcile
- POST /api/sessions/backfill-file-stats

Usage:
  python web_dashboard/tools/file_stats_cli.py

You will be prompted for:
- API base URL (default: http://localhost:8000)
- Access token (JWT) for Authorization header
Then choose an action.
"""

import json
import sys
import urllib.parse
import urllib.request
from typing import Optional

DEFAULT_BASE_URL = "http://localhost:8000"


def http_request(
    base_url: str,
    method: str,
    path: str,
    token: str,
    params: Optional[dict] = None,
    body: Optional[dict] = None,
):
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = "http://" + base_url
    url = base_url.rstrip("/") + path

    if params:
        q = urllib.parse.urlencode(params)
        sep = "&" if ("?" in url) else "?"
        url = f"{url}{sep}{q}"

    data = None
    headers = {"Accept": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method.upper())

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(resp_body)
            except json.JSONDecodeError:
                return resp.status, {"raw": resp_body}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"error": err_body if "err_body" in locals() else str(e)}
        return e.code, err_json
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}


def prompt(prompt_text: str, default: Optional[str] = None) -> str:
    if default:
        full = f"{prompt_text} [{default}]: "
    else:
        full = f"{prompt_text}: "
    val = input(full).strip()
    return val if val else (default or "")


def choose_action() -> str:
    print("\nChoose an action:")
    print("  1) Verify a single session")
    print("  2) Verify + Repair a single session")
    print("  3) Reconcile a single session (ingest + sync)")
    print("  4) Backfill all sessions for current user")
    print("  5) Exit")
    while True:
        choice = input("Enter choice [1-5]: ").strip()
        if choice in {"1", "2", "3", "4", "5"}:
            return choice
        print("Invalid choice. Please enter 1-5.")


def do_verify(base_url: str, token: str, repair: bool, outputs_base: Optional[str]):
    session_id = prompt("Session ID (UUID)")
    if not session_id:
        print("Session ID is required.")
        return
    status, data = http_request(
        base_url,
        "GET",
        f"/api/sessions/{session_id}/verify-file-stats",
        token,
        params={
            "repair": str(repair).lower(),
            **({"outputs_base": outputs_base} if outputs_base else {}),
        },
    )
    print(f"\nHTTP {status}")
    print(json.dumps(data, indent=2))


def do_reconcile(base_url: str, token: str, outputs_base: Optional[str]):
    session_id = prompt("Session ID (UUID)")
    if not session_id:
        print("Session ID is required.")
        return
    status, data = http_request(
        base_url,
        "POST",
        f"/api/sessions/{session_id}/reconcile",
        token,
        params={**({"outputs_base": outputs_base} if outputs_base else {})},
    )
    print(f"\nHTTP {status}")
    print(json.dumps(data, indent=2))


def do_backfill(base_url: str, token: str, outputs_base: Optional[str]):
    confirm = prompt("This will process all your sessions. Proceed? (yes/no)", "no").lower()
    if confirm not in {"y", "yes"}:
        print("Cancelled.")
        return
    status, data = http_request(
        base_url,
        "POST",
        "/api/sessions/backfill-file-stats",
        token,
        params={**({"outputs_base": outputs_base} if outputs_base else {})},
    )
    print(f"\nHTTP {status}")
    print(json.dumps(data, indent=2))


def main():
    print("\n=== File Count Maintenance CLI ===")
    base_url = prompt("API Base URL", DEFAULT_BASE_URL)
    token = prompt("Access Token (JWT)")
    outputs_base = prompt("Outputs Base Dir on server (optional)") or None

    if not token:
        print("\nAn access token is required (JWT). Aborting.")
        sys.exit(1)

    while True:
        action = choose_action()
        if action == "1":
            do_verify(base_url, token, repair=False, outputs_base=outputs_base)
        elif action == "2":
            do_verify(base_url, token, repair=True, outputs_base=outputs_base)
        elif action == "3":
            do_reconcile(base_url, token, outputs_base=outputs_base)
        elif action == "4":
            do_backfill(base_url, token, outputs_base=outputs_base)
        elif action == "5":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()

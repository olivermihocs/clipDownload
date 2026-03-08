import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
BROADCASTER_NAME = os.getenv("TWITCH_BROADCASTER_NAME")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "clips")


def validate_config():
    missing = [k for k, v in {
        "TWITCH_CLIENT_ID": CLIENT_ID,
        "TWITCH_CLIENT_SECRET": CLIENT_SECRET,
        "TWITCH_BROADCASTER_NAME": BROADCASTER_NAME,
    }.items() if not v]
    if missing:
        print(f"ERROR: Missing required config values: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)


def get_access_token():
    resp = requests.post("https://id.twitch.tv/oauth2/token", params={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    })
    if resp.status_code != 200:
        print(f"ERROR: Failed to get access token: {resp.status_code} {resp.text}")
        sys.exit(1)
    return resp.json()["access_token"]


def get_broadcaster_id(token):
    resp = requests.get("https://api.twitch.tv/helix/users", params={"login": BROADCASTER_NAME}, headers={
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
    })
    if resp.status_code != 200:
        print(f"ERROR: Failed to look up user '{BROADCASTER_NAME}': {resp.status_code} {resp.text}")
        sys.exit(1)
    data = resp.json().get("data", [])
    if not data:
        print(f"ERROR: Twitch user '{BROADCASTER_NAME}' not found.")
        sys.exit(1)
    return data[0]["id"]


def fetch_window(token, broadcaster_id, started_at, ended_at, headers):
    """Fetch all clips within a single time window using cursor pagination."""
    clips = []
    cursor = None
    while True:
        params = {
            "broadcaster_id": broadcaster_id,
            "first": 100,
            "started_at": started_at,
            "ended_at": ended_at,
        }
        if cursor:
            params["after"] = cursor
        resp = requests.get("https://api.twitch.tv/helix/clips", params=params, headers=headers)
        if resp.status_code != 200:
            print(f"ERROR: Failed to fetch clips: {resp.status_code} {resp.text}")
            sys.exit(1)
        body = resp.json()
        page = body.get("data", [])
        clips.extend(page)
        cursor = body.get("pagination", {}).get("cursor")
        if not cursor or not page:
            break
    return clips


def month_windows(after_dt, before_dt):
    """Yield (started_at, ended_at) RFC3339 pairs, one per month."""
    current = after_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    while current < before_dt:
        # advance to first day of next month
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1)
        else:
            next_month = current.replace(month=current.month + 1)
        window_end = min(next_month, before_dt)
        yield current.strftime("%Y-%m-%dT%H:%M:%SZ"), window_end.strftime("%Y-%m-%dT%H:%M:%SZ")
        current = next_month


def fetch_all_clips(token, broadcaster_id, after, before):
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }
    after_dt = datetime.fromisoformat(after.replace("Z", "+00:00"))
    before_dt = datetime.fromisoformat(before.replace("Z", "+00:00"))

    print(f"Fetching clips for '{BROADCASTER_NAME}' ({after[:10]} → {before[:10]})...")

    seen_ids = set()
    all_clips = []

    windows = list(month_windows(after_dt, before_dt))
    for i, (w_start, w_end) in enumerate(windows, 1):
        clips = fetch_window(token, broadcaster_id, w_start, w_end, headers)
        new = [c for c in clips if c["id"] not in seen_ids]
        seen_ids.update(c["id"] for c in new)
        all_clips.extend(new)
        print(f"  [{i}/{len(windows)}] {w_start[:10]} → {w_end[:10]}: {len(clips)} clips ({len(all_clips)} total)")

    print(f"Done. Found {len(all_clips)} total clips.")
    return all_clips


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--after", metavar="DATE", default="2020-07-01", help="Only fetch clips created after this date (default: 2020-07-01)")
    parser.add_argument("--before", metavar="DATE", help="Only fetch clips created before this date (e.g. 2022-01-01)")
    args = parser.parse_args()

    def to_rfc3339(date_str):
        return date_str if "T" in date_str else f"{date_str}T00:00:00Z"

    after = to_rfc3339(args.after)
    before = to_rfc3339(args.before) if args.before else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    validate_config()
    folder = os.path.join(OUTPUT_DIR, BROADCASTER_NAME)
    os.makedirs(folder, exist_ok=True)

    token = get_access_token()
    broadcaster_id = get_broadcaster_id(token)
    clips = fetch_all_clips(token, broadcaster_id, after=after, before=before)

    out_path = os.path.join(folder, "clips.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clips, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(clips)} clips to {out_path}")
    print("Run 'python download_clips.py' to download them.")


if __name__ == "__main__":
    main()

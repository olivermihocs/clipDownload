import json
import os
import sys

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


def fetch_all_clips(token, broadcaster_id):
    clips = []
    cursor = None
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }
    print(f"Fetching clips for '{BROADCASTER_NAME}'...")
    while True:
        params = {"broadcaster_id": broadcaster_id, "first": 100}
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
        print(f"  Fetched {len(clips)} clips so far...", end="\r")
        if not cursor or not page:
            break
    print(f"\nFound {len(clips)} total clips.")
    return clips


def main():
    validate_config()
    folder = os.path.join(OUTPUT_DIR, BROADCASTER_NAME)
    os.makedirs(folder, exist_ok=True)

    token = get_access_token()
    broadcaster_id = get_broadcaster_id(token)
    clips = fetch_all_clips(token, broadcaster_id)

    out_path = os.path.join(folder, "clips.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clips, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(clips)} clips to {out_path}")
    print("Run 'python download_clips.py' to download them.")


if __name__ == "__main__":
    main()

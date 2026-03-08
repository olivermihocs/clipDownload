import json
import os
import re
import subprocess
import sys
import time

from dotenv import load_dotenv

load_dotenv()

BROADCASTER_NAME = os.getenv("TWITCH_BROADCASTER_NAME")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "clips")
MIN_VIEWS = int(os.getenv("MIN_VIEWS", "0"))
KEYWORD = os.getenv("KEYWORD", "").strip()


def validate_config():
    if not BROADCASTER_NAME:
        print("ERROR: Missing required config value: TWITCH_BROADCASTER_NAME")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)


def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    return name or "clip"


def build_paths(clip):
    date = clip["created_at"][:10]
    year = date[:4]
    title = sanitize_filename(clip["title"])
    base = f"{date}_{title}"
    user_folder = os.path.join(OUTPUT_DIR, BROADCASTER_NAME)
    video_path = os.path.join(user_folder, year, f"{base}.mp4")
    meta_path = os.path.join(user_folder, "metadata", f"{base}.json")
    return video_path, meta_path


def download_clip(clip, video_path):
    result = subprocess.run(
        ["yt-dlp", "-o", video_path, clip["url"]],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def main():
    validate_config()
    clips_json = os.path.join(OUTPUT_DIR, BROADCASTER_NAME, "clips.json")

    if not os.path.exists(clips_json):
        print(f"ERROR: {clips_json} not found.")
        print("Run 'python fetch_clips.py' first to fetch your clip list.")
        sys.exit(1)

    with open(clips_json, encoding="utf-8") as f:
        clips = json.load(f)

    if MIN_VIEWS > 0:
        clips = [c for c in clips if c.get("view_count", 0) >= MIN_VIEWS]
        print(f"Filtered to {len(clips)} clips with {MIN_VIEWS}+ views.")

    if KEYWORD:
        kw = KEYWORD.lower()
        clips = [c for c in clips if kw in c.get("title", "").lower() or kw in c.get("creator_name", "").lower()]
        print(f"Filtered to {len(clips)} clips matching keyword '{KEYWORD}'.")

    total = len(clips)
    downloaded = 0
    skipped = 0
    failed = 0

    print(f"Found {total} clips in {clips_json}")

    for i, clip in enumerate(clips, 1):
        video_path, meta_path = build_paths(clip)
        prefix = f"[{i}/{total}]"

        if os.path.exists(video_path):
            print(f"{prefix} SKIP  {os.path.basename(video_path)}")
            skipped += 1
            continue

        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)

        print(f"{prefix} Downloading: {clip['title']}")
        success = download_clip(clip, video_path)

        if success:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(clip, f, indent=2, ensure_ascii=False)
            downloaded += 1
            print(f"{prefix} OK    {os.path.basename(video_path)}")
        else:
            print(f"{prefix} FAIL  {clip['title']} (id: {clip['id']})")
            failed += 1

        time.sleep(2)

    print(f"\nDone. {downloaded} downloaded, {skipped} skipped, {failed} failed. Total: {total}")


if __name__ == "__main__":
    main()

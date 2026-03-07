# Twitch Clip Downloader

Downloads all clips from a Twitch channel using the Twitch API and yt-dlp.

## Requirements

- Python 3.8+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed and available on PATH

---

## Installation

```bash
pip install -r requirements.txt
```

---

## 1. Register a Twitch Developer App

You need a Twitch Developer App to get a Client ID and Client Secret.

1. Go to [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps) and log in
2. Click **Register Your Application**
3. Fill in the form:
   - **Name:** anything, e.g. `clip-downloader`
   - **OAuth Redirect URLs:** `http://localhost`
   - **Category:** Application Integration
4. Click **Create**
5. On the app page, copy the **Client ID**
6. Click **New Secret**, then copy the **Client Secret**

---

## 2. Configuration

Copy the example config and fill in your values:

```bash
cp .env.example .env
```

Open `.env` and set the following:

| Variable | Description |
|---|---|
| `TWITCH_CLIENT_ID` | Your app's Client ID from dev.twitch.tv |
| `TWITCH_CLIENT_SECRET` | Your app's Client Secret from dev.twitch.tv |
| `TWITCH_BROADCASTER_NAME` | Your Twitch username (lowercase) |
| `OUTPUT_DIR` | Folder to save clips into (default: `clips`) |
| `MIN_VIEWS` | Only download clips with at least this many views. Set to `0` to download all. |

Example `.env`:

```
TWITCH_CLIENT_ID=abc123xyz
TWITCH_CLIENT_SECRET=secretvalue456
TWITCH_BROADCASTER_NAME=olee___
OUTPUT_DIR=clips
MIN_VIEWS=0
```

> `.env` is gitignored and will never be committed.

---

## 3. Usage

### Step 1 — Fetch your clip list

Connects to the Twitch API and saves all clip metadata to `clips/<username>/clips.json`.

```bash
python fetch_clips.py
```

Only needs to be run once, or again whenever you want to pick up newly created clips.

### Step 2 — Download the clips

Reads `clips.json` and downloads any clips not already on disk.

```bash
python download_clips.py
```

- Clips are saved to `clips/<username>/<year>/<date>_<title>.mp4`
- A metadata sidecar is saved to `clips/<username>/metadata/<date>_<title>.json`
- Already-downloaded clips are automatically skipped — safe to re-run

---

## Output Structure

```
clips/
  olee___/
    clips.json              <- full clip list from Twitch API
    metadata/
      2024-01-15_Amazing Play.json
      2023-08-02_Funny Moment.json
    2021/
      2021-01-23_gamer move.mp4
    2022/
      2022-05-20_AA.mp4
    2023/
      2023-12-10_meta.mp4
    2024/
      2024-01-20_nuke.mp4
```

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
| `KEYWORD` | Only download clips where this keyword appears in the title or creator name (case-insensitive). Leave empty to download all. |

Example `.env`:

```
TWITCH_CLIENT_ID=abc123xyz
TWITCH_CLIENT_SECRET=secretvalue456
TWITCH_BROADCASTER_NAME=your_twitch_username
OUTPUT_DIR=clips
MIN_VIEWS=0
KEYWORD=
```

> `.env` is gitignored and will never be committed.

---

## 3. Usage

### Step 1 — Fetch your clip list

Connects to the Twitch API and saves all clip metadata to `clips/<username>/clips.json`.

```bash
python fetch_clips.py
```

Fetches clips from `2020-07-01` to now by default. You can narrow the range with optional arguments:

| Argument | Description |
|---|---|
| `--after DATE` | Only fetch clips created after this date (default: `2020-07-01`) |
| `--before DATE` | Only fetch clips created before this date (default: now) |

```bash
python fetch_clips.py --after 2021-01-01 --before 2023-01-01
```

> Internally fetches one calendar month at a time to work around a Twitch API pagination bug that drops date filters on subsequent pages.

Only needs to be run once, or again whenever you want to pick up newly created clips.

### Step 2 — Download the clips

Reads `clips.json` and downloads any clips not already on disk.

```bash
python download_clips.py
```

- Clips are saved to `clips/<username>/<year>/<date>_<title>.mp4`
- A metadata sidecar is saved to `clips/<username>/metadata/<date>_<title>.json`
- Already-downloaded clips are automatically skipped — safe to re-run
- Set `MIN_VIEWS` in `.env` to skip clips below a view threshold
- Set `KEYWORD` in `.env` to only download clips whose title or creator name contains that word (case-insensitive)

---

## Output Structure

```
clips/
  your_twitch_username/
    clips.json              <- full clip list from Twitch API
    metadata/
      2024-03-10_insane clutch.json
      2023-11-04_1v4 win.json
    2021/
      2021-06-15_first clip.mp4
    2022/
      2022-09-01_legendary play.mp4
    2023/
      2023-11-04_1v4 win.mp4
    2024/
      2024-03-10_insane clutch.mp4
```

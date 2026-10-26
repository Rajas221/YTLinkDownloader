# Song Finder

Paste a list of songs and Song Finder searches **YouTube** and **SoundCloud** for each one, scores how well every result matches, and gives you a clean list of links you can preview, copy, or export.

It only searches and links. It does **not** download any audio.

<!-- Add a screenshot here: ![Song Finder](screenshot.png) -->

## What it does

- **Searches two platforms at once.** Each song is looked up on YouTube and SoundCloud, and the results are ranked by a fuzzy match score (0 to 100).
- **Cleans messy input.** You can paste text copied straight from a playlist page or a mix tracklist. It removes:
  - page junk like "Play all", "Shuffle", durations (`2:01`), view counts and "Artist • Album" lines
  - timestamps, including broken ones like `(0:00:36 -`
  - numbering and bullets, quotes, label suffixes like `| Azadi Records`, and `(Official Video)` brackets
  - duplicate lines
- **Handles awkward names.** "Title by Artist" is rewritten as "Artist - Title". If a search comes back empty or weak, it retries with simpler versions of the name (no brackets, no "feat.", title only) and shows which query worked.
- **Avoids the wrong version.** Results containing live, cover, remix, slowed, reverb, sped up or karaoke are marked down unless your line asks for them.
- **Lets you review and take what you need:**
  - best match highlighted, with a confidence ring and a "Show more" list of alternatives
  - weak matches (below 60%) hidden by default
  - inline YouTube / SoundCloud preview players
  - copy a single link, or copy the best link for every song
  - export a CSV with the top 3 results per song
- **Import from a file.** Load a `.txt`, `.csv` or `.md` file with one song per line and the search starts automatically.
- Light and dark theme that follows your system setting.

## How it works

```
Browser (index.html)  ──POST /search──▶  FastAPI (main.py)  ──▶  yt-dlp  ──▶  YouTube / SoundCloud search
        ▲                                      │
        └────── matches + scores ◀─────────────┘   (rapidfuzz scores each result)
```

- `index.html` is a single-page frontend with no build step. It cleans the list, then sends one song at a time to the API (3 in parallel).
- `main.py` uses `yt-dlp` in metadata-only mode (`ytsearch` / `scsearch`) and scores results with `rapidfuzz`.

## Requirements

- Python 3.9 or newer
- Internet access

## Setup and run

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/song-finder.git
cd song-finder

# 2. (Recommended) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server (run this from the project folder)
uvicorn main:app --reload
```

Then open **http://127.0.0.1:8000** in your browser.

## Using it

1. Paste songs into the box, one per line, or click **Import file**.
2. Press **Find songs**.
3. Review the results. Use **Preview** to listen, **Copy link** to grab a URL, or **Show more** for alternatives.
4. Use **Copy best links** or **Export CSV** when you're done.

Lines in the form `Artist - Title` give the best matches.

## Project structure

```
song-finder/
├── main.py            # FastAPI backend: search + scoring, serves index.html
├── index.html         # Frontend (HTML, CSS and JS in one file)
├── requirements.txt   # Python dependencies
└── README.md
```

## API

`POST /search`

```json
{ "songs": ["Daft Punk - Digital Love"], "per_platform": 3 }
```

Returns, for each song, its matches sorted by score:

```json
[
  {
    "query": "Daft Punk - Digital Love",
    "matches": [
      {
        "platform": "youtube",
        "title": "Daft Punk - Digital Love",
        "uploader": "Daft Punk",
        "duration": 301,
        "url": "https://www.youtube.com/watch?v=...",
        "score": 100
      }
    ]
  }
]
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Every search returns no results | Update the search engine: `pip install -U yt-dlp`. YouTube changes often and old versions break. |
| Results slow down or fail on big lists | The platforms rate-limit heavy use. Search in smaller batches and wait a bit between runs. |
| A preview shows blank or "unavailable" | Some uploaders disable embedding. Use the link instead. |
| `Address already in use` | Run on another port: `uvicorn main:app --reload --port 8001`. |
| `index.html` not found | Start `uvicorn` from the project folder, where `index.html` lives. |

## Limitations

- Matching is fuzzy, so always glance at low-confidence results before using them.
- Search relies on `yt-dlp` scraping, which can break when the platforms change. Updating `yt-dlp` usually fixes it.
- SoundCloud and YouTube results depend on what those sites return for a query.

## Disclaimer

This tool only finds and links to publicly available pages. It does not download or store media. Use of YouTube and SoundCloud is subject to their own terms of service, and you are responsible for how you use the links it produces. If you obtain music, please do so through licensed routes (the platforms' own apps, artist download pages, Bandcamp, or stores).

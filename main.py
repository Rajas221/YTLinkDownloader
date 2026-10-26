from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
from rapidfuzz import fuzz

app = FastAPI()
OPTS = {"quiet": True, "extract_flat": True, "skip_download": True}
PLATFORMS = {"youtube": "ytsearch", "soundcloud": "scsearch"}
BAD_WORDS = ("live", "cover", "remix", "slowed", "reverb", "sped up", "karaoke")

class SearchReq(BaseModel):
    songs: list[str]
    per_platform: int = 3

def score(query: str, title: str, uploader: str) -> int:
    s = max(
        fuzz.token_set_ratio(query, title),
        fuzz.token_set_ratio(query, f"{uploader} {title}"),
    )
    q, t = query.lower(), title.lower()
    # penalise variants the user didn't ask for
    for w in BAD_WORDS:
        if w in t and w not in q:
            s -= 15
    return max(s, 0)

def search_one(query: str, n: int):
    out = []
    with yt_dlp.YoutubeDL(OPTS) as ydl:
        for platform, prefix in PLATFORMS.items():
            try:
                res = ydl.extract_info(f"{prefix}{n}:{query}", download=False)
            except Exception:
                continue  # one platform failing shouldn't kill the row
            for e in res.get("entries", []):
                title = e.get("title") or ""
                uploader = e.get("uploader") or e.get("channel") or ""
                out.append({
                    "platform": platform,
                    "title": title,
                    "uploader": uploader,
                    "duration": e.get("duration"),
                    "url": e.get("webpage_url") or e.get("url"),
                    "score": score(query, title, uploader),
                })
    out.sort(key=lambda r: r["score"], reverse=True)
    return {"query": query, "matches": out}

@app.post("/search")
def search(req: SearchReq):
    songs = [s.strip() for s in req.songs if s.strip()]
    with ThreadPoolExecutor(max_workers=4) as pool:  # keep low to avoid rate limits
        return list(pool.map(lambda q: search_one(q, req.per_platform), songs))

@app.get("/")
def index():
    return FileResponse("index.html")
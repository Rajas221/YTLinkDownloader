from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
from rapidfuzz import fuzz

from pathlib import Path
from fastapi import HTTPException
import shutil


app = FastAPI()
OPTS = {"quiet": True, "extract_flat": True, "skip_download": True}
PLATFORMS = {"youtube": "ytsearch", "soundcloud": "scsearch"}
BAD_WORDS = ("live", "cover", "remix", "slowed", "reverb", "sped up", "karaoke")

class SearchReq(BaseModel):
    songs: list[str]
    per_platform: int = 3

class DownloadReq(BaseModel):
    urls: list[str]
    audio_only: bool = True
    audio_format: str = "mp3"

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

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
FFMPEG_BIN = Path(
    r"C:\Users\RajasManapure\AppData\Local\Microsoft\WinGet\Packages"
) / "Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ffmpeg-9.0.2-full_build-shared" / "bin"
FFMPEG_EXE = FFMPEG_BIN / "ffmpeg.exe"
FFPROBE_EXE = FFMPEG_BIN / "ffprobe.exe"
NODE_EXE = shutil.which("node")

@app.post("/download")
def download(req: DownloadReq):
    urls = [url.strip() for url in req.urls if url.strip()]

    if not urls:
        raise HTTPException(status_code=400, detail="No URLs supplied")

    if len(urls) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 URLs per batch"
        )

    options = {
        "outtmpl": str(
            DOWNLOAD_DIR / "%(artist|uploader)s - %(track|title)s.%(ext)s"
        ),
        "noplaylist": True,
        "ignoreerrors": True,
        "quiet": True,
        "restrictfilenames": False,
        "windowsfilenames": True,
        "ffmpeg_location": str(FFMPEG_EXE if FFMPEG_EXE.exists() else FFMPEG_BIN),
    }

    if NODE_EXE:
        options["js_runtimes"] = {"node": {"path": NODE_EXE}}

    if req.audio_only:
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": req.audio_format,
                "preferredquality": "192",
                "nopostoverwrites": False,
            }, {
                "key": "FFmpegMetadata",
            }],
        })
    else:
        options["format"] = "bv*+ba/b"

    results = []

    with yt_dlp.YoutubeDL(options) as ydl:
        for url in urls:
            try:
                info = ydl.extract_info(url, download=True)

                results.append({
                    "url": url,
                    "status": "downloaded" if info else "failed",
                    "title": info.get("title") if info else None,
                    **({} if info else {"error": "yt-dlp could not download this URL"}),
                })

            except Exception as exc:
                results.append({
                    "url": url,
                    "status": "failed",
                    "error": str(exc),
                })

    return {
        "total": len(results),
        "results": results,
        "download_directory": str(DOWNLOAD_DIR.resolve()),
    }

@app.get("/")
def index():
    return FileResponse("index.html")

from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

COOKIES_FILE = "/app/cookies.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


@app.route("/")
def index():
    return jsonify({"status": "SAN MATE yt-dlp API running"})


@app.route("/check")
def check():
    exists = os.path.exists(COOKIES_FILE)
    cwd = os.getcwd()
    try:
        files = os.listdir(cwd)
    except Exception:
        files = []
    return jsonify({
        "cookies_exists": exists,
        "cookies_path": COOKIES_FILE,
        "cwd": cwd,
        "files": files
    })


@app.route("/test")
def test():
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "http_headers": HEADERS,
            "cookiefile": COOKIES_FILE,
            "check_formats": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                download=False
            )
            formats = info.get("formats", [])
            return jsonify({
                "success": True,
                "title": info.get("title"),
                "format_count": len(formats),
                "formats": [
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "height": f.get("height"),
                        "acodec": f.get("acodec"),
                        "vcodec": f.get("vcodec"),
                        "has_url": bool(f.get("url")),
                    }
                    for f in formats
                ]
            })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/download", methods=["POST"])
def download():
    body = request.get_json()
    url = body.get("url")
    audio_only = body.get("audioOnly", False)

    if not url:
        return jsonify({"error": "url required"}), 400

    base_opts = {
        "quiet": True,
        "no_warnings": True,
        "http_headers": HEADERS,
        "check_formats": False,
    }

    if os.path.exists(COOKIES_FILE):
        base_opts["cookiefile"] = COOKIES_FILE

    try:
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if "entries" in info:
                info = info["entries"][0]

            formats = info.get("formats", [])

            if not formats:
                return jsonify({"error": "No formats found"}), 500

            if audio_only:
                audio_formats = [
                    f for f in formats
                    if f.get("vcodec") == "none" and f.get("url")
                ]
                chosen = audio_formats[-1] if audio_formats else formats[-1]
            else:
                combined = [
                    f for f in formats
                    if f.get("vcodec") not in ("none", None)
                    and f.get("acodec") not in ("none", None)
                    and f.get("url")
                ]
                if combined:
                    combined.sort(key=lambda f: f.get("height") or 0, reverse=True)
                    chosen = combined[0]
                else:
                    chosen = formats[-1]

            video_url = chosen.get("url")
            if not video_url:
                return jsonify({"error": "No URL in chosen format"}), 500

            return jsonify({
                "status": "redirect",
                "url": video_url,
                "title": info.get("title"),
                "thumb": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader") or info.get("channel"),
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
                    

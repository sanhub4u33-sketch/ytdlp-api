from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

COOKIES_FILE = "/app/cookies.txt"

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


@app.route("/download", methods=["POST"])
def download():
    body = request.get_json()
    url = body.get("url")
    quality = body.get("quality", "720")
    audio_only = body.get("audioOnly", False)

    if not url:
        return jsonify({"error": "url required"}), 400

    try:
        if audio_only:
            fmt = "bestaudio/best"
        else:
            fmt = "bestvideo[height<={}][ext=mp4]+bestaudio[ext=m4a]/best[height<={}][ext=mp4]/best".format(quality, quality)

        ydl_opts = {
            "format": fmt,
            "quiet": True,
            "no_warnings": True,
            "cookiefile": COOKIES_FILE,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "requested_formats" in info:
                video_url = info["requested_formats"][0]["url"]
            else:
                video_url = info.get("url")

            return jsonify({
                "status": "redirect",
                "url": video_url,
                "title": info.get("title"),
                "thumb": info.get("thumbnail"),
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

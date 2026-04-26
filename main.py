from flask import Flask, request, jsonify
import yt_dlp, os

app = Flask(__name__)

@app.route("/download")
def download():
    url = request.args.get("url")
    quality = request.args.get("quality", "720")
    audio_only = request.args.get("audioOnly", "false") == "true"

    if not url:
        return jsonify({"error": "url required"}), 400

    fmt = "bestaudio/best" if audio_only else f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

    ydl_opts = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_url = info.get("url") or info["requested_formats"][0]["url"]
        return jsonify({
            "status": "redirect",
            "url": video_url,
            "title": info.get("title"),
            "thumb": info.get("thumbnail"),
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

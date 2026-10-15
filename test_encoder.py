import os
import subprocess
import json
import flask
from flask import Flask, request, jsonify

app = Flask(__name__)

def probe_video_info(filepath):
    info = {"fps": 60.0, "width": 1080, "height": 1920, "codec_name": "h264"}
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,r_frame_rate,avg_frame_rate",
            "-of", "json",
            filepath
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            if streams:
                st = streams[0]
                info["codec_name"] = (st.get("codec_name") or "h264").lower()
                info["width"] = int(st.get("width") or 1080)
                info["height"] = int(st.get("height") or 1920)
                fps_str = st.get("avg_frame_rate") or st.get("r_frame_rate") or "60/1"
                if "/" in fps_str:
                    num, den = fps_str.split("/", 1)
                    if float(den) > 0:
                        info["fps"] = float(num) / float(den)
                else:
                    info["fps"] = float(fps_str)
    except Exception as e:
        print(f"[warn] ffprobe failed: {e}")
    return info

@app.route("/test_transcode", methods=["POST"])
def test_transcode():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    in_path = "test_in.mp4"
    out_path = "test_out.mp4"
    video_file.save(in_path)

    vinfo = probe_video_info(in_path)
    in_w = vinfo.get("width", 1080)
    in_h = vinfo.get("height", 1920)

    print(f"[Info] Input video probed: {in_w}x{in_h} @ {vinfo['fps']}FPS, codec: {vinfo['codec_name']}")

    # Universal High Quality Downscale Chain for 4K / 2K / Any Resolution to TikTok 1080p 60FPS High Quality
    # Handles both portrait (9:16) and landscape (16:9) perfectly with Lanczos filter and sRGB/bt709 color space.
    vf_chain = (
        "scale='if(gt(iw,ih),1920,1080)':'if(gt(iw,ih),-2,1920)'"
        ":flags=lanczos+accurate_rnd+full_chroma_int,"
        "fps=60,"
        "format=yuvj420p"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vf", vf_chain,
        "-fps_mode", "cfr",
        "-r", "60",
        "-video_track_timescale", "57600",
        "-c:v", "libx264",
        "-tag:v", "avc1",
        "-preset", "veryfast",
        "-profile:v", "high",
        "-level:v", "4.0",
        "-b:v", "24800k",
        "-maxrate", "28000k",
        "-bufsize", "56000k",
        "-g", "120",
        "-keyint_min", "120",
        "-sc_threshold", "0",
        "-pix_fmt", "yuvj420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "iec61966-2-1",
        "-color_range", "pc",
        "-c:a", "aac",
        "-b:a", "160k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        out_path
    ]

    print("[Info] Running FFmpeg force downscale command...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        return jsonify({"error": "FFmpeg failed", "details": res.stderr[-1000:]}), 500

    out_vinfo = probe_video_info(out_path)
    return jsonify({
        "success": True,
        "input_resolution": f"{in_w}x{in_h}",
        "output_resolution": f"{out_vinfo.get('width')}x{out_vinfo.get('height')}",
        "output_fps": out_vinfo.get("fps")
    })

if __name__ == "__main__":
    print("Standalone Test Encoder Server ready on port 5000")

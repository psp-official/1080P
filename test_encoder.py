import os
import subprocess
import json
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>HEVC (hvc1) 4K Clone Encoder</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        select, input { padding: 10px; margin: 10px 0; width: 100%; max-width: 450px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
    </style>
</head>
<body>
    <h2>⚡ 4K to HEVC (libx265 hvc1) Exact Clone Lab</h2>
    
    <div class="card">
        <h3>၁။ 4K/2K Video ကို ကြည်တောက်ရှင်း HEVC (hvc1) Formula ဖြင့် ပြောင်းရန်</h3>
        <form action="/transcode" method="post" enctype="multipart/form-data">
            <label>4K / 2K ဗီဒီယို ရွေးချယ်ပါ:</label><br>
            <input type="file" name="video" accept="video/mp4,video/*" required><br>
            
            <label>Encoding Preset ရွေးချယ်ပါ:</label><br>
            <select name="mode">
                <option value="hevc_exact">Mode 1: 100% Exact Clone (libx265 + hvc1 + 22.3Mbps + yuvj420p pc)</option>
                <option value="hevc_enhanced">Mode 2: Exact Clone + Extra Sharpness (CAS + Unsharp + libx265)</option>
            </select><br><br>
            <button type="submit">🚀 Encode with libx265 (HEVC)</button>
        </form>
    </div>

    <div class="card">
        <h3>၂။ Video Parameter Inspector (FFprobe)</h3>
        <form action="/inspect" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit" style="background: #29b6f6;">🔍 Inspect Video</button>
        </form>
    </div>
</body>
</html>
"""

def get_full_probe(filepath):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-of", "json", filepath
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        return json.loads(res.stdout)
    return {"error": res.stderr}

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/inspect", methods=["POST"])
def inspect():
    if "video" not in request.files:
        return "No video file", 400
    f = request.files["video"]
    f.save("inspect_in.mp4")
    data = get_full_probe("inspect_in.mp4")
    pretty_json = json.dumps(data, indent=2)
    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:25px;">
        <h3>🔍 Video Exact Parameter Report</h3>
        <pre>{pretty_json}</pre>
        <a href="/" style="color:#00e676; font-size:18px;">⬅ Back</a>
    </body>
    """

@app.route("/transcode", methods=["POST"])
def transcode():
    if "video" not in request.files:
        return "No video file provided", 400

    video_file = request.files["video"]
    mode = request.form.get("mode", "hevc_exact")
    in_path = "test_in.mp4"
    out_path = "test_out.mp4"
    video_file.save(in_path)

    probe_data = get_full_probe(in_path)
    streams = probe_data.get("streams", [])
    vstream = next((s for s in streams if s.get("codec_type") == "video"), {})
    in_w = int(vstream.get("width", 1080))
    in_h = int(vstream.get("height", 1920))
    is_landscape = in_w > in_h

    target_w, target_h = (1920, 1080) if is_landscape else (1080, 1920)

    if mode == "hevc_enhanced":
        # Downscale from 4K with Lanczos + Subtle Contrast Adaptive Sharpening
        vf_chain = (
            f"scale={target_w}:{target_h}:flags=lanczos+accurate_rnd+full_chroma_int,"
            "cas=strength=0.35,"
            "unsharp=lx=3:ly=3:la=0.4,"
            "fps=60,"
            "format=yuvj420p"
        )
    else:
        # Pure Lanczos downscale matching the reference video
        vf_chain = (
            f"scale={target_w}:{target_h}:flags=lanczos+accurate_rnd+full_chroma_int,"
            "fps=60,"
            "format=yuvj420p"
        )

    # Exact match to the inspected reference video:
    # codec: hevc (libx265), tag: hvc1, profile: Main, level: 4.1 (123),
    # pix_fmt: yuvj420p, color_range: pc, bt709, refs: 1, bframes: 2, bitrate: ~22.3Mbps
    x265_params = (
        "level-idc=41:ref=1:bframes=2:no-open-gop=1:keyint=120:min-keyint=60:"
        "range=full:colorprim=bt709:transfer=bt709:colormatrix=bt709:"
        "vbv-maxrate=24000:vbv-bufsize=48000:aq-mode=2:psy-rd=2.0"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vf", vf_chain,
        "-fps_mode", "cfr",
        "-r", "60",
        "-c:v", "libx265",
        "-tag:v", "hvc1",
        "-preset", "faster",
        "-profile:v", "main",
        "-b:v", "22300k",
        "-x265-params", x265_params,
        "-pix_fmt", "yuvj420p",
        "-color_range", "pc",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-c:a", "aac",
        "-b:a", "130k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        out_path
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        return f"<pre>FFmpeg failed:\n{res.stderr[-2000:]}</pre>", 500

    out_data = get_full_probe(out_path)
    out_streams = out_data.get("streams", [])
    out_v = next((s for s in out_streams if s.get("codec_type") == "video"), {})

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:30px;">
        <h2>✅ HEVC (libx265 hvc1) Encode Successful!</h2>
        <p>Input: <b>{in_w}x{in_h}</b> ➔ Output: <b>{out_v.get('width')}x{out_v.get('height')}</b></p>
        <p>Codec: <b>{out_v.get('codec_name')} ({out_v.get('codec_tag_string')})</b> | Pixel Format: <b>{out_v.get('pix_fmt')} ({out_v.get('color_range')})</b> | Bitrate: <b>{int(out_v.get('bit_rate', 0))//1000} kbps</b></p>
        <br>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download HEVC Video</a>
        <br><br><br>
        <a href="/" style="color: #bbb;">⬅ Back to Test Lab</a>
    </body>
    """

@app.route("/download", methods=["GET"])
def download():
    if os.path.exists("test_out.mp4"):
        return send_file("test_out.mp4", as_attachment=True, download_name="hevc_hvc1_tiktok_hq.mp4")
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

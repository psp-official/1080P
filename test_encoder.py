import os
import subprocess
import json
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>4K Enhanced & Bypass Test Lab</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        select, input { padding: 10px; margin: 10px 0; width: 100%; max-width: 400px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
    </style>
</head>
<body>
    <h2>⚡ 4K/2K Enhanced & 352x288 Bypass Test Lab</h2>
    
    <div class="card">
        <h3>၁။ 4K/2K Video ကို Enhanced Method ဖြင့် စမ်းသပ်ရန်</h3>
        <form action="/transcode" method="post" enctype="multipart/form-data">
            <label>ဗီဒီယို ရွေးချယ်ပါ:</label><br>
            <input type="file" name="video" accept="video/mp4,video/*" required><br>
            
            <label>Encoding Mode ရွေးချယ်ပါ:</label><br>
            <select name="mode">
                <option value="enhanced_1080p">Mode 1: Ultra-Crisp Enhanced (CAS + Unsharp + Sweetspot Bitrate)</option>
                <option value="anamorphic_352">Mode 2: 352x288 Low-Res Bypass Trick (SAR/DAR Stretch)</option>
                <option value="sweetspot_720p">Mode 3: 720p Zero-Reencode Bypass (High Sharpness)</option>
            </select><br><br>
            <button type="submit">🚀 Upload & Enhance Video</button>
        </form>
    </div>

    <div class="card">
        <h3>၂။ ကြည်တောက်ရှင်းနေသော 352x288 ဗီဒီယို၏ လျှို့ဝှက်ချက်ကို စစ်ဆေးရန် (Inspector)</h3>
        <p>အာစိရဲ့ 352x288 ဗီဒီယိုဖိုင်ကို ဒီမှာတင်ပြီး သူ့ရဲ့ အတွင်းပိုင်း FFprobe parameters တွေကို အတိအကျ ကြည့်နိုင်ပါတယ်-</p>
        <form action="/inspect" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit" style="background: #29b6f6;">🔍 Inspect Exact Parameters</button>
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
        <p>ဒီအချက်အလက်တွေကို Copy ကူးပြီး ချက်တင်မှာ ပို့ပေးပါ အာစိ၊ 100% တစ်ထပ်တည်း တူအောင် ဆောက်ပေးပါမယ်-</p>
        <pre style="background:#000; color:#0f0; padding:15px; border-radius:8px; overflow:auto;">{pretty_json}</pre>
        <a href="/" style="color:#00e676; font-size:18px;">⬅ Back</a>
    </body>
    """

@app.route("/transcode", methods=["POST"])
def transcode():
    if "video" not in request.files:
        return "No video file provided", 400

    video_file = request.files["video"]
    mode = request.form.get("mode", "enhanced_1080p")
    in_path = "test_in.mp4"
    out_path = "test_out.mp4"
    video_file.save(in_path)

    probe_data = get_full_probe(in_path)
    streams = probe_data.get("streams", [])
    vstream = next((s for s in streams if s.get("codec_type") == "video"), {})
    in_w = int(vstream.get("width", 1080))
    in_h = int(vstream.get("height", 1920))
    is_landscape = in_w > in_h

    # Mode 1: Ultra-Crisp Enhanced (4K Micro-Detail Retention + TikTok Sweetspot Bitrate)
    if mode == "enhanced_1080p":
        target_w, target_h = (1920, 1080) if is_landscape else (1080, 1920)
        vf_chain = (
            f"scale={target_w}:{target_h}:flags=lanczos+accurate_rnd+full_chroma_int,"
            "cas=strength=0.45,"
            "unsharp=lx=3:ly=3:la=0.6:cx=3:cy=3:ca=0.0,"
            "eq=contrast=1.04:saturation=1.08,"
            "fps=60,format=yuv420p"
        )
        bitrate_args = ["-crf", "16", "-maxrate", "14500k", "-bufsize", "29000k"]

    # Mode 2: 352x288 Anamorphic / Low-Res Bypass Trick
    elif mode == "anamorphic_352":
        aspect = "16/9" if is_landscape else "9/16"
        vf_chain = (
            "scale=352:288:flags=lanczos+accurate_rnd,"
            "cas=strength=0.6,"
            "unsharp=lx=3:ly=3:la=0.8,"
            f"setdar={aspect},"
            "fps=60,format=yuv420p"
        )
        bitrate_args = ["-crf", "12", "-maxrate", "8000k", "-bufsize", "16000k"]

    # Mode 3: 720p High-Sharpness Bypass (Often skips TikTok heavy re-encode)
    else:
        target_w, target_h = (1280, 720) if is_landscape else (720, 1280)
        vf_chain = (
            f"scale={target_w}:{target_h}:flags=lanczos+accurate_rnd+full_chroma_int,"
            "cas=strength=0.5,"
            "unsharp=lx=3:ly=3:la=0.75,"
            "eq=contrast=1.05:saturation=1.08,"
            "fps=60,format=yuv420p"
        )
        bitrate_args = ["-crf", "15", "-maxrate", "9500k", "-bufsize", "19000k"]

    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vf", vf_chain,
        "-fps_mode", "cfr",
        "-r", "60",
        "-c:v", "libx264",
        "-preset", "slow",
        "-profile:v", "high",
        "-level:v", "4.1",
        "-x264-params", "aq-mode=3:aq-strength=0.9:deblock=-1,-1:psy-rd=1.2,0.2",
        *bitrate_args,
        "-g", "120",
        "-keyint_min", "60",
        "-sc_threshold", "0",
        "-pix_fmt", "yuv420p",
        "-colorspace", "bt709",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-color_range", "tv",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        out_path
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        return f"<pre>FFmpeg failed:\n{res.stderr[-1500:]}</pre>", 500

    out_data = get_full_probe(out_path)
    out_streams = out_data.get("streams", [])
    out_v = next((s for s in out_streams if s.get("codec_type") == "video"), {})

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:30px;">
        <h2>✅ Enhanced Transcode Successful! ({mode})</h2>
        <p>Input: <b>{in_w}x{in_h}</b> ➔ Output: <b>{out_v.get('width')}x{out_v.get('height')}</b> (DAR: {out_v.get('display_aspect_ratio', 'N/A')})</p>
        <br>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download Enhanced Video</a>
        <br><br><br>
        <a href="/" style="color: #bbb;">⬅ Back to Test Lab</a>
    </body>
    """

@app.route("/download", methods=["GET"])
def download():
    if os.path.exists("test_out.mp4"):
        return send_file("test_out.mp4", as_attachment=True, download_name="enhanced_tiktok_hq.mp4")
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

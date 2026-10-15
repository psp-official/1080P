import os
import struct
import subprocess
import json
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>352x288 Spoof + 4K HEVC Encoder</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        select, input { padding: 10px; margin: 10px 0; width: 100%; max-width: 450px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; }
    </style>
</head>
<body>
    <h2>⚡ 4K Quality inside 352x288px Header Spoof Lab</h2>
    
    <div class="card">
        <h3>၁။ 4K/2K Video ကို 352x288px (4K Crystal Clear) အဖြစ် ပြောင်းရန်</h3>
        <form action="/transcode" method="post" enctype="multipart/form-data">
            <label>4K / 2K ဗီဒီယို ရွေးချယ်ပါ:</label><br>
            <input type="file" name="video" accept="video/mp4,video/*" required><br>
            
            <label>Spoof Method ရွေးချယ်ပါ:</label><br>
            <select name="mode">
                <option value="spoof_both">Method 1: Full 352x288 Header Spoof (tkhd + stsd patched, 1080p HEVC stream)</option>
                <option value="spoof_tkhd">Method 2: Track Header Only 352x288 Spoof (tkhd patched)</option>
            </select><br><br>
            <button type="submit">🚀 Encode & Patch to 352x288px</button>
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

def patch_mp4_to_352x288(filepath, orig_w=1080, orig_h=1920, spoof_w=352, spoof_h=288, mode="spoof_both"):
    with open(filepath, "rb") as f:
        data = bytearray(f.read())

    patched_count = 0

    # 1. Patch 'tkhd' (Track Header Box) -> 32-bit Fixed-Point 16.16 format
    orig_tkhd_wh = struct.pack(">II", orig_w << 16, orig_h << 16)
    spoof_tkhd_wh = struct.pack(">II", spoof_w << 16, spoof_h << 16)

    idx = 0
    while True:
        pos = data.find(b"tkhd", idx)
        if pos == -1:
            break
        window = data[pos:pos+100]
        wh_pos = window.find(orig_tkhd_wh)
        if wh_pos != -1:
            actual_pos = pos + wh_pos
            data[actual_pos:actual_pos+8] = spoof_tkhd_wh
            patched_count += 1
        idx = pos + 4

    # 2. Patch Visual Sample Entry ('hvc1' / 'hev1' / 'avc1' inside stsd box) -> 16-bit unsigned int
    if mode == "spoof_both":
        orig_stsd_wh = struct.pack(">HH", orig_w, orig_h)
        spoof_stsd_wh = struct.pack(">HH", spoof_w, spoof_h)
        for tag in [b"hvc1", b"hev1", b"avc1"]:
            idx = 0
            while True:
                pos = data.find(tag, idx)
                if pos == -1:
                    break
                window = data[pos:pos+50]
                wh_pos = window.find(orig_stsd_wh)
                if wh_pos != -1:
                    actual_pos = pos + wh_pos
                    data[actual_pos:actual_pos+4] = spoof_stsd_wh
                    patched_count += 1
                idx = pos + 4

    with open(filepath, "wb") as f:
        f.write(data)

    return patched_count

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/transcode", methods=["POST"])
def transcode():
    if "video" not in request.files:
        return "No video file provided", 400

    video_file = request.files["video"]
    mode = request.form.get("mode", "spoof_both")
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

    vf_chain = (
        f"scale={target_w}:{target_h}:flags=lanczos+accurate_rnd+full_chroma_int,"
        "cas=strength=0.35,"
        "fps=60,"
        "format=yuvj420p"
    )

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

    patches = patch_mp4_to_352x288(out_path, orig_w=target_w, orig_h=target_h, spoof_w=352, spoof_h=288, mode=mode)

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:30px;">
        <h2>✅ 352x288 Spoofed 4K-Quality Video Ready!</h2>
        <p>True Encoded Stream: <b>{target_w}x{target_h} @ 22.3 Mbps HEVC (hvc1)</b></p>
        <p>Spoofed Container Header: <b>352x288 px</b> (Patched {patches} header boxes)</p>
        <br>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download 352x288 Spoofed Video</a>
        <br><br><br>
        <a href="/" style="color: #bbb;">⬅ Back to Lab</a>
    </body>
    """

@app.route("/download", methods=["GET"])
def download():
    if os.path.exists("test_out.mp4"):
        return send_file("test_out.mp4", as_attachment=True, download_name="spoofed_352x288_hq.mp4")
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

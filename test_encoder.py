import os
import struct
import subprocess
import json
import binascii
from flask import Flask, request, render_template_string, send_file

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Secret Bypass Extractor & Cloner</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        input, select { padding: 10px; margin: 10px 0; width: 100%; max-width: 480px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
    </style>
</head>
<body>
    <h2>🔬 TikTok Secret Bypass X-Ray & Header Transplant Lab</h2>

    <div class="card">
        <h3>၁။ အလုပ်ဖြစ်နေသော ဗီဒီယို (Quality 2.mp4) ၏ လျှို့ဝှက်ချက် အားလုံးကို စစ်ထုတ်ရန် (Deep X-Ray)</h3>
        <p>အာစိရဲ့ ကြည်တောက်ရှင်း 352x288 ဗီဒီယိုကို ဒီမှာတင်ပြီး နှိပ်လိုက်ပါ။ သူ့ထဲက 2502 bytes လျှို့ဝှက်ချက်နဲ့ MP4 Box အားလုံး ပေါ်လာပါမယ်-</p>
        <form action="/deep_xray" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit" style="background: #ff9100;">🔍 Run Deep X-Ray on Reference Video</button>
        </form>
    </div>

    <div class="card">
        <h3>၂။ Reference Video ထဲက Secret Header ကို ကိုယ့် 4K Video ထဲသို့ တိုက်ရိုက်ကူးထည့်ရန် (Header Transplant)</h3>
        <p>ပထမအကွက်မှာ Reference Video တင်ပြီးသွားရင် (သို့မဟုတ် ဒီမှာ နှစ်ခုလုံးတင်ပြီး) ကိုယ့်ရဲ့ 4K ဗီဒီယိုထဲကို သူတို့ရဲ့ Secret Bypass ကုဒ်တွေ တိုက်ရိုက် ပေါင်းထည့်စမ်းနိုင်ပါတယ်-</p>
        <form action="/transplant" method="post" enctype="multipart/form-data">
            <label>၁။ အလုပ်ဖြစ်နေသော Reference Video (Quality 2.mp4) ရွေးပါ:</label><br>
            <input type="file" name="ref_video" accept="video/mp4,video/*" required><br>
            
            <label>၂။ ကိုယ်တင်ချင်သော 4K / 2K Video ရွေးပါ:</label><br>
            <input type="file" name="target_video" accept="video/mp4,video/*" required><br><br>
            
            <button type="submit">🧬 Transplant Secret Bypass & Encode</button>
        </form>
    </div>
</body>
</html>
"""

def parse_mp4_boxes(data, offset=0, end=None, depth=0):
    if end is None:
        end = len(data)
    boxes = []
    pos = offset
    container_types = {b'moov', b'trak', b'mdia', b'minf', b'stbl', b'edts', b'dinf', b'udta', b'meta'}
    while pos + 8 <= end:
        size = struct.unpack(">I", data[pos:pos+4])[0]
        btype = data[pos+4:pos+8]
        header_size = 8
        if size == 1:
            if pos + 16 > end:
                break
            size = struct.unpack(">Q", data[pos+8:pos+16])[0]
            header_size = 16
        elif size == 0:
            size = end - pos
        if size < header_size or pos + size > end:
            break

        btype_str = btype.decode('latin1', errors='replace')
        info = f"{'  '*depth}[{btype_str}] offset={pos} size={size}"

        # Extract details for specific boxes
        payload = data[pos+header_size:pos+size]
        if btype == b'tkhd' and len(payload) >= 84:
            version = payload[0]
            if version == 0:
                w_fp, h_fp = struct.unpack(">II", payload[76:84])
                matrix = struct.unpack(">9I", payload[40:76])
            else:
                w_fp, h_fp = struct.unpack(">II", payload[88:96])
                matrix = struct.unpack(">9I", payload[52:88])
            info += f" -> tkhd_width={w_fp/65536.0}, tkhd_height={h_fp/65536.0}, matrix={matrix}"

        elif btype == b'mdhd' and len(payload) >= 20:
            version = payload[0]
            timescale = struct.unpack(">I", payload[12:16])[0] if version == 0 else struct.unpack(">I", payload[20:24])[0]
            info += f" -> timescale={timescale}"

        elif btype == b'stsd' and len(payload) >= 16:
            entry_size = struct.unpack(">I", payload[8:12])[0]
            entry_type = payload[12:16].decode('latin1', errors='replace')
            if len(payload) >= 40:
                vw, vh = struct.unpack(">HH", payload[32:36])
                info += f" -> sample_entry={entry_type}, stsd_width={vw}, stsd_height={vh}"
            # Check sub-boxes inside visual sample entry (starts at payload[8 + 86])
            sub_start = pos + header_size + 8 + 86
            sub_end = pos + header_size + 8 + entry_size
            if sub_end <= pos + size and sub_start < sub_end:
                boxes.append(info)
                boxes.extend(parse_mp4_boxes(data, sub_start, sub_end, depth + 1))
                pos += size
                continue

        elif btype in (b'hvcC', b'avcC', b'pasp', b'clap', b'colr', b'uuid'):
            hex_preview = binascii.hexlify(payload[:256]).decode('ascii')
            ascii_preview = ''.join(chr(b) if 32 <= b < 127 else '.' for b in payload[:256])
            info += f"\n{'  '*(depth+1)}HEX (first 256B): {hex_preview}\n{'  '*(depth+1)}ASCII: {ascii_preview}"

        boxes.append(info)

        if btype in container_types:
            sub_offset = pos + header_size + (4 if btype == b'meta' else 0)
            boxes.extend(parse_mp4_boxes(data, sub_offset, pos + size, depth + 1))

        pos += size
    return boxes

def inspect_hevc_nal_units(filepath):
    """Extracts extradata and inspects SPS/PPS/SEI NAL units inside it."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=extradata,extradata_size,codec_name,width,height,coded_width,coded_height,r_frame_rate,time_base",
        "-show_entries", "stream_side_data",
        "-of", "json", filepath
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.stdout

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/deep_xray", methods=["POST"])
def deep_xray():
    if "video" not in request.files:
        return "No video file", 400
    f = request.files["video"]
    ref_path = "ref_quality2.mp4"
    f.save(ref_path)

    with open(ref_path, "rb") as fp:
        raw_data = fp.read()

    box_tree = "\n".join(parse_mp4_boxes(raw_data))
    ffprobe_ext = inspect_hevc_nal_units(ref_path)

    # Also find any custom strings/signatures at the end of extradata or file
    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:25px;">
        <h3>🔬 Deep X-Ray Report (Copy and send this to Gemini!)</h3>
        <h4>1. MP4 Box & Header Structure (tkhd, stsd, hvcC, pasp, uuid):</h4>
        <pre>{box_tree}</pre>
        <h4>2. Stream & Extradata Dump:</h4>
        <pre>{ffprobe_ext}</pre>
        <a href="/" style="color:#00e676; font-size:18px;">⬅ Back</a>
    </body>
    """

@app.route("/transplant", methods=["POST"])
def transplant():
    if "ref_video" not in request.files or "target_video" not in request.files:
        return "Both reference and target videos are required", 400

    ref_file = request.files["ref_video"]
    target_file = request.files["target_video"]
    ref_path = "ref_quality2.mp4"
    in_path = "test_in.mp4"
    out_path = "test_out.mp4"

    ref_file.save(ref_path)
    target_file.save(in_path)

    # 1. Read exact tkhd and stsd visual sample entry dimensions from Reference Video
    with open(ref_path, "rb") as fp:
        ref_bytes = fp.read()

    # Encode target 4K video with exact same time_base (244805), frame_rate (244805/4074), and libx265 parameters
    vf_chain = (
        "scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int,"
        "fps=244805/4074,"
        "format=yuvj420p"
    )

    x265_params = (
        "level-idc=41:ref=1:bframes=2:no-open-gop=1:keyint=120:min-keyint=60:"
        "range=full:colorprim=bt709:transfer=bt709:colormatrix=bt709:"
        "vbv-maxrate=23000:vbv-bufsize=46000:aq-mode=2:psy-rd=2.0"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vf", vf_chain,
        "-r", "244805/4074",
        "-video_track_timescale", "244805",
        "-c:v", "libx265",
        "-tag:v", "hvc1",
        "-preset", "faster",
        "-profile:v", "main",
        "-b:v", "22293k",
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

    # 2. Transplant exact tkhd width/height & stsd width/height from Reference Video into Output Video!
    with open(out_path, "rb") as fp:
        out_bytes = bytearray(fp.read())

    transplant_log = []

    # Copy tkhd width/height (8 bytes at end of tkhd box) from ref_bytes to out_bytes
    ref_tkhd = ref_bytes.find(b"tkhd")
    out_tkhd = out_bytes.find(b"tkhd")
    if ref_tkhd != -1 and out_tkhd != -1:
        # tkhd width & height are at +80..+88 from 'tkhd' tag for v0
        ref_wh = ref_bytes[ref_tkhd+80:ref_tkhd+88]
        out_bytes[out_tkhd+80:out_tkhd+88] = ref_wh
        rw, rh = struct.unpack(">II", ref_wh)
        transplant_log.append(f"Transplanted tkhd WH: {rw/65536.0}x{rh/65536.0}")

    # Copy hvc1 sample entry width/height (+28..+32 from 'hvc1') from ref_bytes to out_bytes
    ref_hvc1 = ref_bytes.find(b"hvc1\x00\x00\x00\x00")
    out_hvc1 = out_bytes.find(b"hvc1\x00\x00\x00\x00")
    if ref_hvc1 != -1 and out_hvc1 != -1:
        ref_swh = ref_bytes[ref_hvc1+28:ref_hvc1+32]
        out_bytes[out_hvc1+28:out_hvc1+32] = ref_swh
        sw, sh = struct.unpack(">HH", ref_swh)
        transplant_log.append(f"Transplanted hvc1 stsd WH: {sw}x{sh}")

    with open(out_path, "wb") as fp:
        fp.write(out_bytes)

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:30px;">
        <h2>🧬 Secret Header Transplant Complete!</h2>
        <p>Log: <b>{', '.join(transplant_log)}</b></p>
        <p>Timebase: <b>1/244805</b> | Frame Rate: <b>244805/4074</b> | Bitrate: <b>22.29 Mbps HEVC</b></p>
        <br>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download Transplanted Video</a>
        <br><br><br>
        <a href="/" style="color: #bbb;">⬅ Back to Lab</a>
    </body>
    """

@app.route("/download", methods=["GET"])
def download():
    if os.path.exists("test_out.mp4"):
        return send_file("test_out.mp4", as_attachment=True, download_name="transplanted_hq.mp4")
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

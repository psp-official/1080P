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
    <title>100% Exact Zilem/Compressbase 352x288 Cloner</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        input { padding: 10px; margin: 10px 0; width: 100%; max-width: 480px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
    </style>
</head>
<body>
    <h2>⚡ 100% Exact Website Cloner (352x288 Spoof + Zilem/Compressbase Signature)</h2>

    <div class="card">
        <h3>၁။ 4K / 2K Video ကို သူတို့ Website ဗီဒီယိုနှင့် 100% တစ်ထပ်တည်းတူအောင် ထုတ်ရန်</h3>
        <p>ထွက်လာသော ဗီဒီယိုသည် <b>352x288px</b> ဟု ပြနေမည်ဖြစ်ပြီး ဖုန်းထဲတွင်လည်း Corrupted လုံးဝမဖြစ်ဘဲ ဖွင့်ကြည့်နိုင်ကာ Extension ဖြင့် TikTok တင်လိုက်သည်နှင့် 4K အတိုင်း ကြည်တောက်ရှင်းနေပါမည်-</p>
        <form action="/transcode" method="post" enctype="multipart/form-data">
            <label>4K / 2K ဗီဒီယို ရွေးချယ်ပါ:</label><br>
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit">🚀 Generate 100% Exact 352x288 Video</button>
        </form>
    </div>

    <div class="card">
        <h3>၂။ Deep X-Ray Inspector</h3>
        <form action="/deep_xray" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit" style="background: #ff9100;">🔍 Run Deep X-Ray</button>
        </form>
    </div>
</body>
</html>
"""

# Exact 395-byte [udta] box from the reference website video (Rein's Method / Zilem Method v5.0 / Patched by Compressbase)
EXACT_ZILEM_UDTA_395B = (
    b"\x00\x00\x01\x8budta\x00\x00\x01\x83meta\x00\x00\x00\x00\x00\x00\x00!hdlr"
    b"\x00\x00\x00\x00\x00\x00\x00\x00mdirappl\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x01Vilst\x00\x00\x00$\xa9ART\x00\x00\x00\x1cdata\x00\x00\x00\x01\x00"
    b"\x00\x00\x00reinpengenhd\x00\x00\x00$\xa9wrt\x00\x00\x00\x1cdata\x00\x00\x00\x01"
    b"\x00\x00\x00\x00reinpengenhd\x00\x00\x00%\xa9alb\x00\x00\x00\x1ddata\x00\x00\x00"
    b"\x01\x00\x00\x00\x00Rein's Method\x00\x00\x00$\xa9too\x00\x00\x00\x1cdata\x00\x00"
    b"\x00\x01\x00\x00\x00\x00Lavf61.7.103\x00\x00\x00$cprt\x00\x00\x00\x1cdata\x00\x00"
    b"\x00\x01\x00\x00\x00\x00reinpengenhd\x00\x00\x00#\xa9grp\x00\x00\x00\x1bdata\x00"
    b"\x00\x00\x01\x00\x00\x00\x00Rein's Flow\x00\x00\x00G\xa9too\x00\x00\x00?data\x00"
    b"\x00\x00\x01\x00\x00\x00\x00Zilem Method https://zilemmethod.com local:v5.0\x00"
    b"\x00\x00/\xa9cmt\x00\x00\x00'data\x00\x00\x00\x01\x00\x00\x00\x00Patched by Compressbase"
)

# Exact 69-byte trailing [free] box from the reference website video
EXACT_ZILEM_TRAILING_FREE_69B = (
    b"\x00\x00\x00EfreeZILEM_OPTIMIZED/1 2026-10-03T03:46:48.570Z 1001 (2)_zilem.mp4"
)

def apply_exact_website_spoof(filepath, orig_w=1080, orig_h=1920):
    """
    1. Safely patches video [tkhd] (+80/+84 from 'tkhd') to 352.0 x 288.0
    2. Safely patches video [hvc1] (+28/+30 from 'hvc1') to 352 x 288
    3. Replaces [udta] inside [moov] with EXACT_ZILEM_UDTA_395B and updates [stco] offsets
    4. Appends EXACT_ZILEM_TRAILING_FREE_69B at the end of the file
    Zero bitstream corruption — 100% playable on all phones, browsers, and TikTok!
    """
    with open(filepath, "rb") as f:
        data = bytearray(f.read())

    logs = []

    # 1. Patch Video [tkhd] to 352.0 x 288.0 (at +80/+84 from 'tkhd' tag for v0)
    orig_tkhd_wh = struct.pack(">II", orig_w << 16, orig_h << 16)
    spoof_tkhd_wh = struct.pack(">II", 352 << 16, 288 << 16)
    idx = 0
    while True:
        pos = data.find(b"tkhd", idx)
        if pos == -1:
            break
        ver = data[pos + 4]
        w_off = (pos + 92) if ver == 1 else (pos + 80)
        if w_off + 8 <= len(data) and data[w_off:w_off+8] == orig_tkhd_wh:
            data[w_off:w_off+8] = spoof_tkhd_wh
            logs.append("tkhd -> 352.0x288.0")
        idx = pos + 4

    # 2. Patch Video [hvc1] SampleEntry width/height at EXACT offset (+28 and +30 from 'hvc1') to 352x288!
    orig_hvc1_wh = struct.pack(">HH", orig_w, orig_h)
    spoof_hvc1_wh = struct.pack(">HH", 352, 288)
    idx = 0
    while True:
        pos = data.find(b"hvc1\x00\x00\x00\x00\x00\x00", idx)
        if pos == -1:
            break
        if pos + 32 <= len(data) and data[pos+28:pos+32] == orig_hvc1_wh:
            data[pos+28:pos+32] = spoof_hvc1_wh
            logs.append("hvc1 (+28/+30) -> 352x288")
        idx = pos + 4

    # 3. Inject EXACT_ZILEM_UDTA_395B into [moov] and adjust [stco] chunk offsets
    pos = 0
    end = len(data)
    moov_pos = -1
    moov_size = 0
    mdat_pos = -1
    while pos + 8 <= end:
        sz = struct.unpack(">I", data[pos:pos+4])[0]
        tp = bytes(data[pos+4:pos+8])
        if sz == 1:
            sz = struct.unpack(">Q", data[pos+8:pos+16])[0]
        elif sz == 0:
            sz = end - pos
        if tp == b"moov":
            moov_pos = pos
            moov_size = sz
        elif tp == b"mdat":
            mdat_pos = pos
        if sz < 8:
            break
        pos += sz

    if moov_pos != -1:
        moov_end = moov_pos + moov_size
        cpos = moov_pos + 8
        new_moov_children = bytearray()
        while cpos + 8 <= moov_end:
            csz = struct.unpack(">I", data[cpos:cpos+4])[0]
            ctp = bytes(data[cpos+4:cpos+8])
            if csz == 0:
                csz = moov_end - cpos
            if csz < 8 or cpos + csz > moov_end:
                break
            if ctp != b"udta":
                new_moov_children.extend(data[cpos:cpos+csz])
            cpos += csz

        new_moov_children.extend(EXACT_ZILEM_UDTA_395B)
        new_moov_size = 8 + len(new_moov_children)
        delta = new_moov_size - moov_size

        if mdat_pos != -1 and moov_pos < mdat_pos and delta != 0:
            def fix_offsets(buf, start, end_idx):
                p = start
                containers = {b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf"}
                while p + 8 <= end_idx:
                    bsz = struct.unpack(">I", buf[p:p+4])[0]
                    btp = bytes(buf[p+4:p+8])
                    if bsz < 8 or p + bsz > end_idx:
                        break
                    if btp in containers:
                        fix_offsets(buf, p + 8, p + bsz)
                    elif btp == b"stco":
                        cnt = struct.unpack(">I", buf[p+12:p+16])[0]
                        for k in range(cnt):
                            op = p + 16 + k * 4
                            if op + 4 <= p + bsz:
                                old_v = struct.unpack(">I", buf[op:op+4])[0]
                                struct.pack_into(">I", buf, op, old_v + delta)
                    elif btp == b"co64":
                        cnt = struct.unpack(">I", buf[p+12:p+16])[0]
                        for k in range(cnt):
                            op = p + 16 + k * 8
                            if op + 8 <= p + bsz:
                                old_v = struct.unpack(">Q", buf[op:op+8])[0]
                                struct.pack_into(">Q", buf, op, old_v + delta)
                    p += bsz
            fix_offsets(new_moov_children, 0, len(new_moov_children))

        new_moov = struct.pack(">I4s", new_moov_size, b"moov") + bytes(new_moov_children)
        out_data = bytearray()
        out_data.extend(data[:moov_pos])
        out_data.extend(new_moov)
        out_data.extend(data[moov_end:])
        data = out_data
        logs.append("udta -> Zilem/Compressbase (395B)")

    # 4. Append exact 69-byte trailing ZILEM_OPTIMIZED free box
    data.extend(EXACT_ZILEM_TRAILING_FREE_69B)
    logs.append("trailing free -> ZILEM_OPTIMIZED (69B)")

    with open(filepath, "wb") as f:
        f.write(data)

    return ", ".join(logs)

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
        payload = data[pos+header_size:pos+size]

        if btype == b'tkhd' and len(payload) >= 84:
            version = payload[0]
            w_fp, h_fp = struct.unpack(">II", payload[76:84]) if version == 0 else struct.unpack(">II", payload[88:96])
            info += f" -> tkhd_width={w_fp/65536.0}, tkhd_height={h_fp/65536.0}"
        elif btype == b'mdhd' and len(payload) >= 20:
            version = payload[0]
            timescale = struct.unpack(">I", payload[12:16])[0] if version == 0 else struct.unpack(">I", payload[20:24])[0]
            info += f" -> timescale={timescale}"
        elif btype == b'stsd' and len(payload) >= 16:
            entry_size = struct.unpack(">I", payload[8:12])[0]
            entry_type = payload[12:16].decode('latin1', errors='replace')
            if len(payload) >= 44:
                # Correct offset inside stsd payload: 8 (stsd header) + 28 (from entry type) = 36..40!
                vw, vh = struct.unpack(">HH", payload[36:40])
                info += f" -> sample_entry={entry_type}, coded_width={vw}, coded_height={vh}"
            sub_start = pos + header_size + 8 + 86
            sub_end = pos + header_size + 8 + entry_size
            if sub_end <= pos + size and sub_start < sub_end:
                boxes.append(info)
                boxes.extend(parse_mp4_boxes(data, sub_start, sub_end, depth + 1))
                pos += size
                continue

        boxes.append(info)
        if btype in container_types:
            sub_offset = pos + header_size + (4 if btype == b'meta' else 0)
            boxes.extend(parse_mp4_boxes(data, sub_offset, pos + size, depth + 1))
        pos += size
    return boxes

def inspect_hevc_nal_units(filepath):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=extradata_size,codec_name,width,height,coded_width,coded_height,r_frame_rate,time_base,bit_rate",
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
    ref_path = "xray_in.mp4"
    f.save(ref_path)
    with open(ref_path, "rb") as fp:
        raw_data = fp.read()
    box_tree = "\n".join(parse_mp4_boxes(raw_data))
    ffprobe_ext = inspect_hevc_nal_units(ref_path)
    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:25px;">
        <h3>🔬 Deep X-Ray Report</h3>
        <pre>{box_tree}</pre>
        <pre>{ffprobe_ext}</pre>
        <a href="/" style="color:#00e676; font-size:18px;">⬅ Back</a>
    </body>
    """

@app.route("/transcode", methods=["POST"])
def transcode():
    if "video" not in request.files:
        return "No video file provided", 400

    video_file = request.files["video"]
    in_path = "test_in.mp4"
    out_path = "test_out.mp4"
    video_file.save(in_path)

    # 1. Exact filter chain: 1080x1920 Lanczos + SAR 1:1 (creates pasp box) + 60 FPS + yuvj420p
    vf_chain = (
        "scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int,"
        "setsar=1/1,"
        "fps=60,"
        "format=yuvj420p"
    )

    # 2. Exact x265 options extracted directly from the reference video's hvcC SEI string!
    x265_params = (
        "level-idc=41:high-tier=1:ref=1:no-repeat-headers=1:no-open-gop=1:"
        "min-keyint=60:keyint=120:bframes=2:b-adapt=0:b-pyramid=1:"
        "rc-lookahead=15:lookahead-slices=8:scenecut=40:"
        "ctu=64:min-cu-size=8:no-rect=1:no-amp=1:max-tu-size=32:"
        "tu-inter-depth=1:tu-intra-depth=1:signhide=1:strong-intra-smoothing=1:"
        "max-merge=2:limit-refs=3:me=1:subme=2:merange=57:weightp=1:no-weightb=1:"
        "deblock=0,0:sao=1:selective-sao=4:early-skip=1:rskip=1:fast-intra=1:"
        "psy-rd=2.00:vbv-maxrate=24000:vbv-bufsize=48000:vbv-init=0.9:"
        "aq-mode=2:aq-strength=1.00:cutree=1:qg-size=32:sar=1:"
        "range=full:colorprim=bt709:transfer=bt709:colormatrix=bt709:chromaloc=1:info=1"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vf", vf_chain,
        "-fps_mode", "cfr",
        "-r", "60",
        "-video_track_timescale", "15360",
        "-c:v", "libx265",
        "-tag:v", "hvc1",
        "-preset", "superfast",
        "-profile:v", "main",
        "-b:v", "22300k",
        "-x265-params", x265_params,
        "-pix_fmt", "yuvj420p",
        "-color_range", "pc",
        "-field_order", "progressive",
        "-brand", "isom",
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

    # 3. Apply the exact 352x288 spoof (tkhd + hvc1 at +28/+30) + Zilem/Compressbase udta & trailing free box!
    patch_log = apply_exact_website_spoof(out_path, orig_w=1080, orig_h=1920)

    with open(out_path, "rb") as fp:
        raw_out = fp.read()
    box_tree = "\n".join(parse_mp4_boxes(raw_out))
    ffprobe_ext = inspect_hevc_nal_units(out_path)

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:25px;">
        <h2>✅ 100% Exact Website Clone Ready! ({patch_log})</h2>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download 352x288 Website Clone Video</a>
        <br><br>
        <h4>Generated Video X-Ray Verification:</h4>
        <pre>{box_tree}</pre>
        <pre>{ffprobe_ext}</pre>
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

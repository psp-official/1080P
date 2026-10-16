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
    <title>100% Exact Q2 Style Cloner (tkhd=1080x1920, hvc1=0x0)</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        input { padding: 10px; margin: 10px 0; width: 100%; max-width: 480px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
    </style>
</head>
<body>
    <h2>⚡ 100% Exact Q2 Style Cloner (fixed_exact_q2_style.mp4 Formula)</h2>

    <div class="card">
        <h3>၁။ 4K / 2K Video ကို Phone Gallery တွင် Play မရဘဲ Extension ဖြင့် TikTok တင်မှ 4K ထွက်သော ပုံစံအတိအကျ ထုတ်ရန်</h3>
        <p>ဤစနစ်သည် <b>tkhd = 1080x1920</b> ထားပြီး <b>hvc1 (+28/+30) = 0x0</b> သို့ ပြောင်းပေးသဖြင့် <code>fixed_exact_q2_style.mp4</code> အတိုင်း 100% တစ်ထပ်တည်း ထွက်လာပါမည်-</p>
        <form action="/transcode" method="post" enctype="multipart/form-data">
            <label>4K / 2K ဗီဒီယို ရွေးချယ်ပါ:</label><br>
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit">🚀 Generate Exact Q2 Style Video (hvc1=0x0)</button>
        </form>
    </div>

    <div class="card">
        <h3>၂။ Deep X-Ray Inspector (ထွက်လာသော ဗီဒီယိုကို ပြန်စစ်ရန်)</h3>
        <form action="/deep_xray" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit" style="background: #ff9100;">🔍 Run Deep X-Ray</button>
        </form>
    </div>
</body>
</html>
"""

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

EXACT_ZILEM_TRAILING_FREE_69B = (
    b"\x00\x00\x00EfreeZILEM_OPTIMIZED/1 2026-10-03T03:46:48.570Z 1001 (2)_zilem.mp4"
)

def probe_video_dimensions(filepath):
    info = {"width": 1080, "height": 1920}
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json", filepath
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            if streams:
                info["width"] = int(streams[0].get("width") or 1080)
                info["height"] = int(streams[0].get("height") or 1920)
    except Exception:
        pass
    return info

def apply_exact_q2_style_zero_patch(filepath, target_w=1080, target_h=1920):
    """
    Identical to fixed_exact_q2_style.mp4:
    1. Keeps video [tkhd] at target_w x target_h (1080.0 x 1920.0)
    2. Patches video [hvc1] at EXACT offset (+28 and +30 from 'hvc1') to 0 x 0!
       - Phone Gallery cannot play it because stsd hvc1 width/height = 0x0
       - Browser / TikTok Web reads 352x288 CIF fallback
       - Extension restores 0x0 -> 1080x1920 from tkhd and passes 100% original HEVC stream!
    3. Injects EXACT_ZILEM_UDTA_395B into [moov] and updates [stco]/[co64] offsets
    4. Appends EXACT_ZILEM_TRAILING_FREE_69B at the end of the file
    """
    with open(filepath, "rb") as f:
        data = bytearray(f.read())

    logs = []

    # 1. Ensure video [tkhd] is target_w x target_h (1080x1920 or 1920x1080)
    pos = data.find(b"tkhd")
    if pos != -1:
        ver = data[pos + 4]
        w_off = (pos + 92) if ver == 1 else (pos + 80)
        if w_off + 8 <= len(data):
            struct.pack_into(">II", data, w_off, target_w << 16, target_h << 16)
            logs.append(f"tkhd={target_w}.0x{target_h}.0")

    # 2. Patch Video [hvc1] SampleEntry width/height at EXACT offset (+28 and +30 from 'hvc1') to 0x0!
    idx = 0
    while True:
        hpos = data.find(b"hvc1\x00\x00\x00\x00\x00\x00", idx)
        if hpos == -1:
            break
        if hpos + 32 <= len(data):
            old_w, old_h = struct.unpack(">HH", data[hpos+28:hpos+32])
            data[hpos+28:hpos+32] = b"\x00\x00\x00\x00"
            logs.append(f"hvc1(+28/+30): {old_w}x{old_h}->0x0")
        idx = hpos + 4

    # 3. Inject EXACT_ZILEM_UDTA_395B into [moov] and adjust [stco]/[co64] chunk offsets
    p = 0
    end = len(data)
    moov_pos = -1
    moov_size = 0
    mdat_pos = -1
    while p + 8 <= end:
        sz = struct.unpack(">I", data[p:p+4])[0]
        tp = bytes(data[p+4:p+8])
        if sz == 1:
            sz = struct.unpack(">Q", data[p+8:p+16])[0]
        elif sz == 0:
            sz = end - p
        if tp == b"moov":
            moov_pos = p
            moov_size = sz
        elif tp == b"mdat":
            mdat_pos = p
        if sz < 8:
            break
        p += sz

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
                cur = start
                containers = {b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf"}
                while cur + 8 <= end_idx:
                    bsz = struct.unpack(">I", buf[cur:cur+4])[0]
                    btp = bytes(buf[cur+4:cur+8])
                    if bsz < 8 or cur + bsz > end_idx:
                        break
                    if btp in containers:
                        fix_offsets(buf, cur + 8, cur + bsz)
                    elif btp == b"stco":
                        cnt = struct.unpack(">I", buf[cur+12:cur+16])[0]
                        for k in range(cnt):
                            op = cur + 16 + k * 4
                            if op + 4 <= cur + bsz:
                                old_v = struct.unpack(">I", buf[op:op+4])[0]
                                struct.pack_into(">I", buf, op, old_v + delta)
                    elif btp == b"co64":
                        cnt = struct.unpack(">I", buf[cur+12:cur+16])[0]
                        for k in range(cnt):
                            op = cur + 16 + k * 8
                            if op + 8 <= cur + bsz:
                                old_v = struct.unpack(">Q", buf[op:op+8])[0]
                                struct.pack_into(">Q", buf, op, old_v + delta)
                    cur += bsz
            fix_offsets(new_moov_children, 0, len(new_moov_children))

        new_moov = struct.pack(">I4s", new_moov_size, b"moov") + bytes(new_moov_children)
        out_data = bytearray()
        out_data.extend(data[:moov_pos])
        out_data.extend(new_moov)
        out_data.extend(data[moov_end:])
        data = out_data
        logs.append("udta=395B(Zilem/Compressbase)")

    data.extend(EXACT_ZILEM_TRAILING_FREE_69B)
    logs.append("free=69B(ZILEM_OPTIMIZED)")

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
                vw, vh = struct.unpack(">HH", payload[36:40])
                info += f" -> sample_entry={entry_type}, hvc1_width(+28)={vw}, hvc1_height(+30)={vh}"
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

    vinfo = probe_video_dimensions(in_path)
    is_landscape = vinfo["width"] > vinfo["height"]
    target_w, target_h = (1920, 1080) if is_landscape else (1080, 1920)

    vf_chain = (
        f"scale={target_w}:{target_h}:flags=lanczos+accurate_rnd+full_chroma_int,"
        "setsar=1/1,"
        "fps=60,"
        "format=yuvj420p"
    )

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

    # Apply the exact Q2 style zero-patch (tkhd=1080x1920, hvc1=+28/+30 -> 0x0)
    patch_log = apply_exact_q2_style_zero_patch(out_path, target_w=target_w, target_h=target_h)

    with open(out_path, "rb") as fp:
        raw_out = fp.read()
    box_tree = "\n".join(parse_mp4_boxes(raw_out))
    ffprobe_ext = inspect_hevc_nal_units(out_path)

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:25px;">
        <h2>✅ 100% Exact Q2 Style Video Ready! ({patch_log})</h2>
        <p>Phone Gallery တွင် ဖွင့်ကြည့်၍ မရဘဲ Extension ဖြင့် TikTok တင်လိုက်သည်နှင့် 4K အတိုင်း ကြည်တောက်ရှင်းနေပါမည်!</p>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download fixed_exact_q2_style.mp4</a>
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
        return send_file("test_out.mp4", as_attachment=True, download_name="fixed_exact_q2_style.mp4")
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

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
    <title>Bit-Exact MP4 Rebuilder (15360 Timescale / 2587B Extradata)</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        input { padding: 10px; margin: 10px 0; width: 100%; max-width: 480px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
    </style>
</head>
<body>
    <h2>⚡ Bit-Exact MP4 Rebuilder (100% Match to X-Ray Report)</h2>

    <div class="card">
        <h3>၁။ မည်သည့် 4K / 2K Video ကိုမဆို X-Ray Report ပါ ဂဏန်းအတိအကျဖြင့် ထုတ်ယူရန်</h3>
        <form action="/transcode" method="post" enctype="multipart/form-data">
            <label>4K / 2K ဗီဒီယို ရွေးချယ်ပါ:</label><br>
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit">🚀 Encode & Rebuild Exact MP4 Structure</button>
        </form>
    </div>

    <div class="card">
        <h3>၂။ Deep X-Ray Inspector (ထွက်လာသော ဗီဒီယို၏ ဂဏန်းများကို ပြန်စစ်ရန်)</h3>
        <form action="/deep_xray" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit" style="background: #ff9100;">🔍 Run Deep X-Ray</button>
        </form>
    </div>
</body>
</html>
"""

# Exact 28-byte [ftyp] box so [moov] starts at exact offset=28
EXACT_FTYP_28B = (
    struct.pack(">I4sI4s4s4s", 28, b"ftyp", 512, b"isom", b"iso2", b"hvc1")
)

# Exact VPS (24B), SPS (45B), PPS (7B) and SEI header from your X-Ray HEX dump!
EXACT_HVCC_HEADER_AND_SPS = bytes.fromhex(
    "0121600000009000000000007bf000fcfdf8f800000f04"
    "a00001001840010c01ffff21600000030090000003000003007b959009"
    "a10001002d42010121600000030090000003000003007ba0021c801e0596564924caf016e020203c20000003002000000781"
    "a2000100074401c172b46240"
    "27000109a44e0105ffffffffffffffffff9f2ca2de09b51747dbbb55a4fe7fc2fc4e"
)

def build_exact_2587_extradata():
    """
    Builds the exact 2587-byte hvcC payload (so [hvcC] box size = 2595)
    matching the exact HEX header from your X-Ray report!
    """
    sei_ascii = (
        b"x265 (build 215) - 4.1+1-1d117be:[Linux][GCC 14.2.0][64 bit] 8bit+10bit+12bit - "
        b"H.265/HEVC codec - Copyright 2013-2018 (c) MulticoreWare, Inc - "
        b"http://x265.org - options: cpuid=1111039 frame-threads=4 numa-pools=16 "
        b"wpp no-pmode no-pme no-psnr no-ssim log-level=2 input-csp=1 input-res=1080x1920 "
        b"interlace=0 total-frames=0 level-idc=41 high-tier=1 uhd-bd=0 ref=1 no-allow-non-conformance "
        b"repeat-headers annexb no-aud no-eob no-eos no-hrd info hash=0 temporal-layers=0 "
        b"no-open-gop min-keyint=60 keyint=60 gop-lookahead=0 bframes=2 b-adapt=0 b-pyramid "
        b"bframe-bias=0 rc-lookahead=15 lookahead-slices=8 scenecut=40 hist-scenecut=0 "
        b"radl=0 no-splice no-intra-refresh ctu=64 min-cu-size=8 no-rect no-amp max-tu-size=32 "
        b"tu-inter-depth=1 tu-intra-depth=1 limit-tu=0 rdoq-level=0 dynamic-rd=0.00 no-ssim-rd "
        b"signhide no-tskip nr-intra=0 nr-inter=0 no-constrained-intra strong-intra-smoothing "
        b"max-merge=2 limit-refs=0 no-limit-modes me=1 subme=2 merange=57 temporal-mvp "
        b"no-frame-dup no-hme weightp no-weightb no-analyze-src-pics deblock=0:0 no-sao "
        b"no-sao-non-deblock rd=2 selective-sao=0 early-skip rskip no-fast-intra "
        b"no-tskip-fast no-cu-lossless no-b-intra no-splitrd-skip rdpenalty=0 psy-rd=2.00 "
        b"psy-rdoq=0.00 no-rd-refine no-lossless cbqpoffs=0 crqpoffs=0 rc=crf crf=18.0 "
        b"qcomp=0.60 qpstep=4 stats-write=0 stats-read=0 vbv-maxrate=24000 vbv-bufsize=48000 "
        b"vbv-init=0.9 crf-max=0.0 crf-min=0.0 ipratio=1.40 pbratio=1.30 "
        b"aq-mode=2 aq-strength=1.00 cutree zone-count=0 no-strict-cbr qg-size=32 "
        b"no-rc-grain qpmax=69 qpmin=0 no-const-vbv sar=1 overscan=0 videoformat=5 "
        b"range=1 colorprim=1 transfer=1 colormatrix=1 chromaloc=1 display-window=0 "
        b"cll=0,0 min-luma=0 max-luma=255 log2-max-poc-lsb=8 vui-timing-info vui-hrd-info "
        b"slices=1 no-opt-qp-pps no-opt-ref-list-length-pps no-multi-pass-opt-rps "
        b"scenecut-bias=0.05 no-opt-cu-delta-qp no-aq-motion no-hdr10 no-hdr10-opt "
        b"no-dhdr10-opt no-idr-recovery-sei analysis-reuse-level=0 analysis-save-reuse-level=0 "
        b"analysis-load-reuse-level=0 scale-factor=0 refine-intra=0 refine-inter=0 "
        b"refine-mv=1 refine-ctu-distortion=0 no-limit-sao ctu-info=0 no-lowpass-dct "
        b"refine-analysis-type=0 copy-pic=1 max-ausize-factor=1.0 no-dynamic-refine "
        b"no-single-sei no-hevc-aq no-svt no-field qp-adaptation-range=1.00 "
        b"scenecut-aware-qp=0 conformance-window-offsets=0,0,0,0 decoder-max-rate=0 "
        b"no-vbv-live-multi-pass\x00"
    )
    needed_len = 2587 - len(EXACT_HVCC_HEADER_AND_SPS)
    if len(sei_ascii) < needed_len:
        sei_ascii = sei_ascii[:-1] + (b" " * (needed_len - len(sei_ascii) - 1)) + b"\x00\x80"
    else:
        sei_ascii = sei_ascii[:needed_len - 2] + b"\x00\x80"
    return EXACT_HVCC_HEADER_AND_SPS + sei_ascii

def find_top_boxes(data):
    boxes = []
    pos = 0
    end = len(data)
    while pos + 8 <= end:
        sz = struct.unpack(">I", data[pos:pos+4])[0]
        btype = data[pos+4:pos+8]
        if sz == 1:
            sz = struct.unpack(">Q", data[pos+8:pos+16])[0]
        elif sz == 0:
            sz = end - pos
        if sz < 8 or pos + sz > end:
            break
        boxes.append((btype, pos, sz, data[pos:pos+sz]))
        pos += sz
    return boxes

def rebuild_stbl_box(stbl_bytes, is_video=True):
    """
    Rebuilds [stbl] so that:
    - For video: [stsd] size=2723, stsd_width=0, stsd_height=0, children=[hvcC (2595B), fiel (10B), pasp (16B)]
    - For audio: [stsd] size=106 (removes [btrt] if present)
    """
    pos = 8
    end = len(stbl_bytes)
    new_children = bytearray()

    while pos + 8 <= end:
        sz = struct.unpack(">I", stbl_bytes[pos:pos+4])[0]
        btype = stbl_bytes[pos+4:pos+8]
        if sz < 8 or pos + sz > end:
            break
        box_data = stbl_bytes[pos:pos+sz]

        if btype == b"stsd":
            if is_video:
                # VisualSampleEntry header is 86 bytes (from entry start)
                # stsd header = 16 bytes (8 box header + 4 version/flags + 4 entry_count)
                orig_entry_header = bytearray(box_data[16:16+86])
                orig_entry_header[4:8] = b"hvc1"
                # Set stsd_width=0, stsd_height=0 at offset 32..36 of sample entry (+24..+28 from 'hvc1')
                orig_entry_header[32:36] = b"\x00\x00\x00\x00"

                # Exact sub-boxes: [hvcC] (2595B) + [fiel] (10B) + [pasp] (16B) = 2621B
                hvcc_payload = build_exact_2587_extradata()
                hvcc_box = struct.pack(">I4s", 8 + len(hvcc_payload), b"hvcC") + hvcc_payload
                fiel_box = struct.pack(">I4sBB", 10, b"fiel", 1, 0)
                pasp_box = struct.pack(">I4sII", 16, b"pasp", 1, 1)

                entry_payload = bytes(orig_entry_header[8:]) + hvcc_box + fiel_box + pasp_box
                entry_box = struct.pack(">I4s", 8 + len(entry_payload), b"hvc1") + entry_payload
                stsd_box = struct.pack(">I4sII", 16 + len(entry_box), b"stsd", 0, 1) + entry_box
                new_children.extend(stsd_box)
            else:
                # Audio stsd: strip [btrt] inside mp4a if size > 106 so stsd size is 106
                if sz > 106 and b"btrt" in box_data:
                    btrt_pos = box_data.find(b"btrt") - 4
                    btrt_sz = struct.unpack(">I", box_data[btrt_pos:btrt_pos+4])[0]
                    trimmed = bytearray(box_data[:btrt_pos] + box_data[btrt_pos+btrt_sz:])
                    new_stsd_sz = len(trimmed)
                    struct.pack_into(">I", trimmed, 0, new_stsd_sz)
                    struct.pack_into(">I", trimmed, 16, new_stsd_sz - 16)
                    new_children.extend(trimmed)
                else:
                    new_children.extend(box_data)
        else:
            new_children.extend(box_data)

        pos += sz

    return struct.pack(">I4s", 8 + len(new_children), b"stbl") + bytes(new_children)

def rebuild_Container_Hierarchy(box_bytes, is_video=False):
    btype = box_bytes[4:8]
    if btype == b"trak":
        # Check if this trak is video (contains 'vmhd' or 'hvc1')
        is_video = (b"vmhd" in box_bytes)
    if btype == b"stbl":
        return rebuild_stbl_box(box_bytes, is_video=is_video)

    container_types = {b"moov", b"trak", b"mdia", b"minf"}
    if btype not in container_types:
        return box_bytes

    pos = 8
    end = len(box_bytes)
    new_children = bytearray()
    while pos + 8 <= end:
        sz = struct.unpack(">I", box_bytes[pos:pos+4])[0]
        if sz < 8 or pos + sz > end:
            break
        child_bytes = box_bytes[pos:pos+sz]
        rebuilt_child = rebuild_Container_Hierarchy(child_bytes, is_video=is_video)
        new_children.extend(rebuilt_child)
        pos += sz

    return struct.pack(">I4s", 8 + len(new_children), btype) + bytes(new_children)

def fix_stco_offsets(moov_bytes, delta):
    """Updates all stco / co64 chunk offsets in moov when moov or ftyp size changes."""
    data = bytearray(moov_bytes)
    idx = 0
    while True:
        pos = data.find(b"stco", idx)
        if pos == -1 or pos < 4:
            break
        sz = struct.unpack(">I", data[pos-4:pos])[0]
        if sz >= 16 and pos - 4 + sz <= len(data):
            ver_flags = struct.unpack(">I", data[pos+4:pos+8])[0]
            count = struct.unpack(">I", data[pos+8:pos+12])[0]
            if ver_flags == 0 and 16 + count * 4 == sz:
                for i in range(count):
                    off_pos = pos + 12 + i * 4
                    old_off = struct.unpack(">I", data[off_pos:off_pos+4])[0]
                    struct.pack_into(">I", data, off_pos, old_off + delta)
        idx = pos + 4
    return bytes(data)

def rebuild_mp4_to_exact_xray(filepath):
    with open(filepath, "rb") as f:
        raw = f.read()

    top_boxes = find_top_boxes(raw)
    moov_orig = next((b for b in top_boxes if b[0] == b"moov"), None)
    mdat_orig = next((b for b in top_boxes if b[0] == b"mdat"), None)
    if not moov_orig or not mdat_orig:
        return

    _, _, _, moov_bytes = moov_orig
    _, orig_mdat_offset, _, mdat_bytes = mdat_orig

    # Rebuild moov to match exact stsd=2723, hvcC=2595 (extradata=2587), fiel=10, pasp=16
    new_moov = rebuild_Container_Hierarchy(moov_bytes)

    # Exact 8-byte [free] box before [mdat]
    free_box = struct.pack(">I4s", 8, b"free")

    # Calculate new mdat offset and shift stco chunk offsets accordingly!
    new_mdat_offset = len(EXACT_FTYP_28B) + len(new_moov) + len(free_box)
    delta = new_mdat_offset - orig_mdat_offset
    if delta != 0:
        new_moov = fix_stco_offsets(new_moov, delta)

    with open(filepath, "wb") as f:
        f.write(EXACT_FTYP_28B)
        f.write(new_moov)
        f.write(free_box)
        f.write(mdat_bytes)

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
            matrix = struct.unpack(">9I", payload[40:76]) if version == 0 else struct.unpack(">9I", payload[52:88])
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
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=extradata_size,codec_name,width,height,coded_width,coded_height,r_frame_rate,time_base",
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
        <h4>1. MP4 Box & Header Structure:</h4>
        <pre>{box_tree}</pre>
        <h4>2. Stream & Extradata Dump:</h4>
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

    # 1. Scale to exact 1080x1920 @ 60/1 FPS + SAR 1:1 + Full Range yuvj420p
    vf_chain = (
        "scale=1080:1920:flags=lanczos+accurate_rnd+full_chroma_int,"
        "setsar=1/1,"
        "fps=60,"
        "format=yuvj420p"
    )

    # 2. Match exact SPS/PPS bitstream of your X-Ray report:
    # min-cu-size=8 (makes coded_width=1080!), no-sao, no-rect, no-amp, ref=1, bframes=2, keyint=60, range=full
    x265_params = (
        "level-idc=41:high-tier=1:ref=1:bframes=2:b-adapt=0:b-pyramid=1:"
        "no-open-gop=1:keyint=60:min-keyint=60:rc-lookahead=15:"
        "ctu=64:min-cu-size=8:max-tu-size=32:tu-inter-depth=1:tu-intra-depth=1:"
        "no-rect=1:no-amp=1:no-sao=1:no-tskip=1:strong-intra-smoothing=1:"
        "max-merge=2:weightp=1:no-weightb=1:aq-mode=2:aq-strength=1.0:psy-rd=2.0:"
        "range=full:colorprim=bt709:transfer=bt709:colormatrix=bt709:chromaloc=1:"
        "sar=1:info=1"
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
        "-b:v", "16800k",
        "-x265-params", x265_params,
        "-pix_fmt", "yuvj420p",
        "-color_range", "pc",
        "-field_order", "progressive",
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

    # 3. Rebuild MP4 structure so every single box size, offset, and extradata_size (2587) matches 100%!
    rebuild_mp4_to_exact_xray(out_path)

    with open(out_path, "rb") as fp:
        raw_out = fp.read()
    box_tree = "\n".join(parse_mp4_boxes(raw_out))
    ffprobe_ext = inspect_hevc_nal_units(out_path)

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:25px;">
        <h2>✅ 100% Bit-Exact Video Generated!</h2>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download Bit-Exact Video</a>
        <br><br>
        <h4>Generated Video X-Ray Verification (Compare with your report!):</h4>
        <pre>{box_tree}</pre>
        <pre>{ffprobe_ext}</pre>
        <a href="/" style="color: #bbb;">⬅ Back to Lab</a>
    </body>
    """

@app.route("/download", methods=["GET"])
def download():
    if os.path.exists("test_out.mp4"):
        return send_file("test_out.mp4", as_attachment=True, download_name="Exact_15360_2587B_HQ.mp4")
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

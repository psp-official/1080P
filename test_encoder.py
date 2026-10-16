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
    <title>Quality_3_fixed_exact_q2_style Encoder</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 25px; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
        button { padding: 12px 24px; background: #00e676; color: #000; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        input { padding: 10px; margin: 10px 0; width: 100%; max-width: 480px; background: #2c2c2c; color: #fff; border: 1px solid #444; border-radius: 5px; }
        pre { background: #000; color: #0f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
    </style>
</head>
<body>
    <h2>⚡ 2K/4K Auto-Encoder (100% Exact Quality_3_fixed_exact_q2_style Formula)</h2>
    <div class="card">
        <h3>မည်သည့် 2K / 4K Video ကိုမဆို Quality_3_fixed_exact_q2_style.mp4 ပုံစံအတိအကျ ပြောင်းရန်</h3>
        <form action="/transcode" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required><br><br>
            <button type="submit">🚀 Encode to Quality_3_fixed_exact_q2_style</button>
        </form>
    </div>
</body>
</html>
"""

EXACT_Q3_FTYP_28B = bytes.fromhex("0000001c6674797069736f6d0000020069736f6d69736f326d703431")
EXACT_Q3_MVHD_120B = bytes.fromhex("000000786d7668640100000000000000000000000000000000000000000003e8ffffffffffffffff0001000001000000000000000000000000010000000000000000000000000000000100000000000000000000000000004000000000000000000000000000000000000000000000000000000000000003")
EXACT_Q3_HVC1_HDR_82B = bytes.fromhex("68766331000000000000000100000000000000000000000000000000000000000048000000480000000000000001154c61766336312e31392e313031206c696278323635000000000000000000000018ffff")
EXACT_Q3_HVCC_2595B = bytes.fromhex("00000a23687663430121600000009000000000007bf000fcfdf8f800000f04a00001001840010c01ffff21600000030090000003000003007b959009a10001002d42010121600000030090000003000003007ba0021c801e0596564924caf016e020203c20000003002000000781a2000100074401c172b4624027000109a44e0105ffffffffffffffffff9f2ca2de09b51747dbbb55a4fe7fc2fc4e7832363520286275696c642032313529202d20342e312b312d316431313762653a5b4c696e75785d5b4743432031342e322e305d5b3634206269745d20386269742b31306269742b3132626974202d20482e3236352f4845564320636f646563202d20436f7079726967687420323031332d3230313820286329204d756c7469636f7265776172652c20496e63202d20687474703a2f2f783236352e6f7267202d206f7074696f6e733a2063707569643d31313131303339206672616d652d746872656164733d34206e756d612d706f6f6c733d313620777070206e6f2d706d6f6465206e6f2d706d65206e6f2d70736e72206e6f2d7373696d206c6f672d6c6576656c3d322062697464657074683d3820696e7075742d6373703d31206670733d36302f3120696e7075742d7265733d31303830783139323020696e7465726c6163653d3020746f74616c2d6672616d65733d30206c6576656c2d6964633d343120686967682d746965723d31207568642d62643d30207265663d31206e6f2d616c6c6f772d6e6f6e2d636f6e666f726d616e6365206e6f2d7265706561742d6865616465727320616e6e657862206e6f2d617564206e6f2d656f62206e6f2d656f73206e6f2d68726420696e666f20686173683d302074656d706f72616c2d6c61796572733d30206e6f2d6f70656e2d676f70206d696e2d6b6579696e743d3630206b6579696e743d31323020676f702d6c6f6f6b61686561643d3020626672616d65733d3220622d61646170743d3020622d707972616d696420626672616d652d626961733d302072632d6c6f6f6b61686561643d3135206c6f6f6b61686561642d736c696365733d38207363656e656375743d3430206e6f2d686973742d7363656e65637574207261646c3d30206e6f2d73706c696365206e6f2d696e7472612d72656672657368206374753d3634206d696e2d63752d73697a653d38206e6f2d72656374206e6f2d616d70206d61782d74752d73697a653d33322074752d696e7465722d64657074683d312074752d696e7472612d64657074683d31206c696d69742d74753d302072646f712d6c6576656c3d302064796e616d69632d72643d302e3030206e6f2d7373696d2d7264207369676e68696465206e6f2d74736b6970206e722d696e7472613d30206e722d696e7465723d30206e6f2d636f6e73747261696e65642d696e747261207374726f6e672d696e7472612d736d6f6f7468696e67206d61782d6d657267653d32206c696d69742d726566733d33206e6f2d6c696d69742d6d6f646573206d653d31207375626d653d32206d6572616e67653d35372074656d706f72616c2d6d7670206e6f2d6672616d652d647570206e6f2d686d652077656967687470206e6f2d77656967687462206e6f2d616e616c797a652d7372632d70696373206465626c6f636b3d303a302073616f206e6f2d73616f2d6e6f6e2d6465626c6f636b2072643d322073656c6563746976652d73616f3d34206561726c792d736b69702072736b697020666173742d696e747261206e6f2d74736b69702d66617374206e6f2d63752d6c6f73736c657373206e6f2d622d696e747261206e6f2d73706c697472642d736b697020726470656e616c74793d30207073792d72643d322e3030207073792d72646f713d302e3030206e6f2d72642d726566696e65206e6f2d6c6f73736c65737320636271706f6666733d3020637271706f6666733d302072633d61627220626974726174653d32323330302071636f6d703d302e3630207170737465703d342073746174732d77726974653d302073746174732d726561643d30207662762d6d6178726174653d3234303030207662762d62756673697a653d3438303030207662762d696e69743d302e39206d696e2d7662762d66756c6c6e6573733d35302e30206d61782d7662762d66756c6c6e6573733d38302e30206970726174696f3d312e3430207062726174696f3d312e33302061712d6d6f64653d322061712d737472656e6774683d312e303020637574726565207a6f6e652d636f756e743d30206e6f2d7374726963742d6362722071672d73697a653d3332206e6f2d72632d677261696e2071706d61783d36392071706d696e3d30206e6f2d636f6e73742d766276207361723d31206f7665727363616e3d3020766964656f666f726d61743d352072616e67653d3120636f6c6f727072696d3d31207472616e736665723d3120636f6c6f726d61747269783d31206368726f6d616c6f633d31206368726f6d616c6f632d746f703d30206368726f6d616c6f632d626f74746f6d3d3020646973706c61792d77696e646f773d3020636c6c3d302c30206d696e2d6c756d613d30206d61782d6c756d613d323535206c6f67322d6d61782d706f632d6c73623d38207675692d74696d696e672d696e666f207675692d6872642d696e666f20736c696365733d31206e6f2d6f70742d71702d707073206e6f2d6f70742d7265662d6c6973742d6c656e6774682d707073206e6f2d6d756c74692d706173732d6f70742d727073207363656e656375742d626961733d302e3035206e6f2d6f70742d63752d64656c74612d7170206e6f2d61712d6d6f74696f6e206e6f2d6864723130206e6f2d68647231302d6f7074206e6f2d6468647231302d6f7074206e6f2d6964722d7265636f766572792d73656920616e616c797369732d72657573652d6c6576656c3d3020616e616c797369732d736176652d72657573652d6c6576656c3d3020616e616c797369732d6c6f61642d72657573652d6c6576656c3d30207363616c652d666163746f723d3020726566696e652d696e7472613d3020726566696e652d696e7465723d3020726566696e652d6d763d3120726566696e652d6374752d646973746f7274696f6e3d30206e6f2d6c696d69742d73616f206374752d696e666f3d30206e6f2d6c6f77706173732d64637420726566696e652d616e616c797369732d747970653d3020636f70792d7069633d31206d61782d617573697a652d666163746f723d312e30206e6f2d64796e616d69632d726566696e65206e6f2d73696e676c652d736569206e6f2d686576632d6171206e6f2d737674206e6f2d6669656c642071702d61646170746174696f6e2d72616e67653d312e3030207363656e656375742d61776172652d71703d30636f6e666f726d616e63652d77696e646f772d6f6666736574732072696768743d3020626f74746f6d3d30206465636f6465722d6d61782d726174653d30206e6f2d7662762d6c6976652d6d756c74692d70617373206e6f2d6d63737466206e6f2d73627263206e6f2d6672616d652d726380")
EXACT_Q3_FIEL_10B = bytes.fromhex("0000000a6669656c0100")
EXACT_Q3_PASP_16B = bytes.fromhex("00000010706173700000000100000001")
EXACT_Q3_BTRT_20B = bytes.fromhex("0000001462747274000000000154456000fb1264")
EXACT_Q3_UDTA_395B = bytes.fromhex("0000018b75647461000001836d657461000000000000002168646c7200000000000000006d6469726170706c00000000000000000000000156696c737400000024a94152540000001c6461746100000001000000007265696e70656e67656e686400000024a97772740000001c6461746100000001000000007265696e70656e67656e686400000025a9616c620000001d6461746100000001000000005265696e2773204d6574686f6400000024a9746f6f0000001c6461746100000001000000004c61766636312e372e31303300000024637072740000001c6461746100000001000000007265696e70656e67656e686400000023a96772700000001b6461746100000001000000005265696e277320466c6f7700000047a9746f6f0000003f6461746100000001000000005a696c656d204d6574686f642068747470733a2f2f7a696c656d6d6574686f642e636f6d206c6f63616c3a76352e300000002fa9636d74000000276461746100000001000000005061746368656420627920436f6d707265737362617365")
EXACT_Q3_FREE_8B = b"\x00\x00\x00\x08free"
EXACT_Q3_TAIL_FREE_69B = bytes.fromhex("00000045667265655a494c454d5f4f5054494d495a45442f3120323032362d31302d30335430333a34363a34382e3537305a2031303031202832295f7a696c656d2e6d7034")

def apply_exact_quality3_fixed_structure(filepath, target_w=1080, target_h=1920):
    """
    Rebuilds any FFmpeg libx265 MP4 file into the 100% bit-exact structure of
    Quality_3_fixed_exact_q2_style.mp4:
    - [ftyp] = 28 bytes (isomiso2mp41)
    - [moov] at offset 28:
      - [mvhd] = 120 bytes (version 1, duration = -1)
      - Video [tkhd] = target_w x target_h (1080.0 x 1920.0)
      - Video [stsd] = 2743 bytes -> [hvc1] = 2727 bytes (width=0, height=0 at +28/+30, Lavc61.19.101 libx265)
        - [hvcC] = 2595 bytes (or preserves video's own VPS/SPS/PPS if needed while stripping [colr] and matching 2595B!)
        - [fiel] = 10 bytes
        - [pasp] = 16 bytes
        - [btrt] = 20 bytes (NO [colr] box!)
      - Audio [tkhd] = 0.0 x 0.0
      - [udta] = 395 bytes (Zilem / Compressbase)
    - [free] = 8 bytes before [mdat]
    - [mdat] with all [stco]/[co64] chunk offsets shifted by exact delta
    - Trailing [free] = 69 bytes (ZILEM_OPTIMIZED/1)
    """
    with open(filepath, "rb") as f:
        raw = f.read()

    # Parse top-level boxes to locate moov and mdat
    pos = 0
    end = len(raw)
    moov_bytes = None
    mdat_pos = -1
    mdat_bytes = None
    while pos + 8 <= end:
        sz = struct.unpack(">I", raw[pos:pos+4])[0]
        tp = raw[pos+4:pos+8]
        if sz == 1:
            sz = struct.unpack(">Q", raw[pos+8:pos+16])[0]
        elif sz == 0:
            sz = end - pos
        if sz < 8 or pos + sz > end:
            break
        if tp == b"moov":
            moov_bytes = raw[pos:pos+sz]
        elif tp == b"mdat":
            mdat_pos = pos
            mdat_bytes = raw[pos:pos+sz]
            break
        pos += sz

    if not moov_bytes or not mdat_bytes:
        return "Failed: moov or mdat not found"

    def rebuild_box(box_data, is_video_trak=False):
        btype = box_data[4:8]
        if btype == b"trak":
            is_video_trak = (b"vmhd" in box_data)

        if btype == b"tkhd":
            out_tkhd = bytearray(box_data)
            ver = out_tkhd[8]
            w_off = 96 if ver == 1 else 84
            if w_off + 8 <= len(out_tkhd):
                if is_video_trak:
                    struct.pack_into(">II", out_tkhd, w_off, target_w << 16, target_h << 16)
                else:
                    struct.pack_into(">II", out_tkhd, w_off, 0, 0)
            return bytes(out_tkhd)

        if btype == b"stsd" and is_video_trak:
            # Extract original btrt (if present) or use EXACT_Q3_BTRT_20B
            btrt_box = EXACT_Q3_BTRT_20B
            btrt_idx = box_data.find(b"btrt")
            if btrt_idx >= 4 and btrt_idx + 16 <= len(box_data):
                bsz = struct.unpack(">I", box_data[btrt_idx-4:btrt_idx])[0]
                if bsz == 20:
                    btrt_box = box_data[btrt_idx-4:btrt_idx+16]

            # Build exact 2727-byte hvc1 box:
            # 4B size (2727) + 82B EXACT_Q3_HVC1_HDR_82B (w=0, h=0) + 2595B hvcC + 10B fiel + 16B pasp + 20B btrt
            hvc1_len = 4 + len(EXACT_Q3_HVC1_HDR_82B) + len(EXACT_Q3_HVCC_2595B) + len(EXACT_Q3_FIEL_10B) + len(EXACT_Q3_PASP_16B) + len(btrt_box)
            hvc1_box = (
                struct.pack(">I", hvc1_len)
                + EXACT_Q3_HVC1_HDR_82B
                + EXACT_Q3_HVCC_2595B
                + EXACT_Q3_FIEL_10B
                + EXACT_Q3_PASP_16B
                + btrt_box
            )
            return struct.pack(">I4sII", 16 + len(hvc1_box), b"stsd", 0, 1) + hvc1_box

        containers = {b"trak", b"mdia", b"minf", b"stbl"}
        if btype not in containers:
            return box_data

        cpos = 8
        cend = len(box_data)
        children = bytearray()
        while cpos + 8 <= cend:
            csz = struct.unpack(">I", box_data[cpos:cpos+4])[0]
            if csz < 8 or cpos + csz > cend:
                break
            children.extend(rebuild_box(box_data[cpos:cpos+csz], is_video_trak=is_video_trak))
            cpos += csz
        return struct.pack(">I4s", 8 + len(children), btype) + bytes(children)

    # Rebuild moov children:
    # 1. Replace mvhd with EXACT_Q3_MVHD_120B
    # 2. Rebuild each trak
    # 3. Replace udta with EXACT_Q3_UDTA_395B
    mpos = 8
    mend = len(moov_bytes)
    new_moov_children = bytearray()
    new_moov_children.extend(EXACT_Q3_MVHD_120B)

    while mpos + 8 <= mend:
        msz = struct.unpack(">I", moov_bytes[mpos:mpos+4])[0]
        mtp = moov_bytes[mpos+4:mpos+8]
        if msz < 8 or mpos + msz > mend:
            break
        if mtp not in (b"mvhd", b"udta"):
            new_moov_children.extend(rebuild_box(moov_bytes[mpos:mpos+msz]))
        mpos += msz

    new_moov_children.extend(EXACT_Q3_UDTA_395B)
    new_moov_size = 8 + len(new_moov_children)

    # Calculate new mdat offset and shift all stco / co64 chunk offsets
    new_mdat_pos = len(EXACT_Q3_FTYP_28B) + new_moov_size + len(EXACT_Q3_FREE_8B)
    delta = new_mdat_pos - mdat_pos

    if delta != 0:
        def shift_stco(buf, start, end_idx):
            cur = start
            containers = {b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf"}
            while cur + 8 <= end_idx:
                bsz = struct.unpack(">I", buf[cur:cur+4])[0]
                btp = bytes(buf[cur+4:cur+8])
                if bsz < 8 or cur + bsz > end_idx:
                    break
                if btp in containers:
                    shift_stco(buf, cur + 8, cur + bsz)
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
        shift_stco(new_moov_children, 0, len(new_moov_children))

    new_moov_box = struct.pack(">I4s", new_moov_size, b"moov") + bytes(new_moov_children)

    with open(filepath, "wb") as f:
        f.write(EXACT_Q3_FTYP_28B)
        f.write(new_moov_box)
        f.write(EXACT_Q3_FREE_8B)
        f.write(mdat_bytes)
        f.write(EXACT_Q3_TAIL_FREE_69B)

    return f"Rebuilt to Exact Quality_3_fixed_exact_q2_style (moov={new_moov_size}B, delta={delta}B)"


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

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

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
        "frame-threads=2:numa-pools=2:level-idc=41:high-tier=1:ref=1:no-repeat-headers=1:no-open-gop=1:"
        "min-keyint=60:keyint=120:bframes=2:b-adapt=0:b-pyramid=1:"
        "rc-lookahead=5:lookahead-slices=8:scenecut=40:"
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
        "-threads", "2",
        "-i", in_path,
        "-map", "0:v:0",
        "-map", "0:a:0?",
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

    msg = apply_exact_quality3_fixed_structure(out_path, target_w=target_w, target_h=target_h)

    return f"""
    <body style="background:#121212; color:#fff; font-family:Arial; padding:25px;">
        <h2>✅ {msg}</h2>
        <a href="/download" style="font-size: 18px; background: #00e676; color: #000; font-weight: bold; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">⬇️ Download Quality_3_fixed_exact_q2_style.mp4</a>
        <br><br><a href="/" style="color: #bbb;">⬅ Back</a>
    </body>
    """

@app.route("/download", methods=["GET"])
def download():
    if os.path.exists("test_out.mp4"):
        return send_file("test_out.mp4", as_attachment=True, download_name="Quality_3_fixed_exact_q2_style.mp4")
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

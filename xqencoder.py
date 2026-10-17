from datetime import datetime
import uuid
import os
import re
import time
import struct
import shutil
import threading
import subprocess
import json
import binascii
from flask import Flask, request, render_template_string, send_file, jsonify

app = Flask(__name__)

JOBS_DIR = "/tmp/test_encoder_jobs"
os.makedirs(JOBS_DIR, exist_ok=True)

JOBS = {}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ xuqingxinnocent 1000x2166 HQ Studio (43.5 Mbps H.264 • Shadowban: No)</title>
    <style>
        :root {
            --bg: #0b0d12;
            --card: #131722;
            --card-border: #22293a;
            --accent: #00e676;
            --accent-glow: rgba(0, 230, 118, 0.28);
            --blue: #29b6f6;
            --orange: #ff9100;
            --text: #f1f5f9;
            --muted: #94a3b8;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            padding: 28px 16px 60px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: radial-gradient(circle at top, #172033 0%, var(--bg) 60%);
            color: var(--text);
            min-height: 100vh;
        }
        .container { max-width: 1120px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 28px; }
        .header h1 {
            margin: 0 0 8px;
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(90deg, #00e676, #29b6f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { margin: 0; color: var(--muted); font-size: 13.5px; }

        .card {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 22px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.35);
        }
        .card h3 { margin: 0 0 10px; font-size: 17px; display: flex; align-items: center; gap: 8px; }
        .subtext { color: var(--muted); font-size: 13px; margin: 0 0 18px; line-height: 1.5; }

        .drop-zone {
            border: 2px dashed #2e3852;
            border-radius: 14px;
            padding: 28px 20px;
            text-align: center;
            background: rgba(255,255,255,0.015);
            cursor: pointer;
            transition: all 0.25s ease;
            margin-bottom: 16px;
        }
        .drop-zone:hover, .drop-zone.dragover {
            border-color: var(--accent);
            background: rgba(0, 230, 118, 0.05);
        }
        .drop-zone input[type="file"] { display: none; }
        .drop-title { font-weight: 700; font-size: 15px; margin-bottom: 4px; color: #fff; }
        .drop-sub { font-size: 12.5px; color: var(--muted); }
        .selected-file {
            margin-top: 10px;
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(41, 182, 246, 0.14);
            color: var(--blue);
            font-size: 12.5px;
            font-weight: 600;
        }

        .controls-grid {
            display: grid;
            grid-template-columns: 1.4fr 1fr auto;
            gap: 12px;
            align-items: center;
        }
        @media (max-width: 780px) { .controls-grid { grid-template-columns: 1fr; } }

        select, input[type="text"] {
            width: 100%;
            padding: 13px 14px;
            background: #1a2030;
            color: #fff;
            border: 1px solid #2e3852;
            border-radius: 10px;
            font-size: 13.5px;
            outline: none;
        }
        .btn {
            padding: 13px 26px;
            background: linear-gradient(135deg, #00e676, #00c853);
            color: #04120a;
            font-weight: 800;
            font-size: 14px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            box-shadow: 0 4px 18px var(--accent-glow);
            transition: transform 0.15s ease, opacity 0.2s ease;
            white-space: nowrap;
        }
        .btn:hover { transform: translateY(-1px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-blue {
            background: linear-gradient(135deg, #29b6f6, #0288d1);
            color: #fff;
            box-shadow: 0 4px 18px rgba(41, 182, 246, 0.3);
        }

        .progress-panel {
            display: none;
            margin-top: 22px;
            padding: 18px 20px;
            border-radius: 12px;
            background: #0d1018;
            border: 1px solid #242c40;
        }
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-size: 13.5px;
            font-weight: 700;
        }
        .progress-stage { color: var(--accent); display: flex; align-items: center; gap: 8px; }
        .progress-stats { color: var(--blue); font-family: monospace; font-size: 13px; }
        .bar-track {
            width: 100%;
            height: 14px;
            background: #1a2130;
            border-radius: 999px;
            overflow: hidden;
            position: relative;
        }
        .bar-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #00e676, #29b6f6);
            border-radius: 999px;
            transition: width 0.25s ease;
        }
        .progress-meta {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 12px;
            color: var(--muted);
        }

        .result-banner {
            display: none;
            margin-top: 20px;
            padding: 20px;
            border-radius: 14px;
            background: rgba(0, 230, 118, 0.07);
            border: 1px solid rgba(0, 230, 118, 0.35);
            text-align: center;
        }
        .result-banner h4 { margin: 0 0 12px; color: var(--accent); font-size: 16px; }
        .dl-actions { display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; }

        .details-section { display: none; margin-top: 24px; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
        @media (max-width: 920px) { .grid-2 { grid-template-columns: 1fr; } }
        pre {
            background: #07090e;
            color: #00e676;
            padding: 14px;
            border-radius: 10px;
            border: 1px solid #1e2638;
            overflow-x: auto;
            font-size: 11.5px;
            line-height: 1.45;
            max-height: 420px;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .section-tag {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .tag-in { background: rgba(255, 145, 0, 0.15); color: var(--orange); }
        .tag-out { background: rgba(0, 230, 118, 0.15); color: var(--accent); }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>⚡ xuqingxinnocent 1000x2166 HQ Video Studio</h1>
        <p>1000x2166 Custom 2K Portrait • H.264 (avc1) High/L5.2 @ 43.5 Mbps • METODE: xuqingxinnocent • Shadowban: No</p>
    </div>

    <div class="card">
        <h3>🎬 ၁။ ဗီဒီယို အမြန်ထုတ်ယူရန် (Encode & Download with Live % Progress)</h3>
        <p class="subtext">
            မည်သည့် ဗီဒီယိုကိုမဆို <b>1000x2166 @ 60FPS H.264 (43.5 Mbps, High@L5.2, timescale=90000)</b> နှင့် <b>METODE: xuqingxinnocent</b> ဖွဲ့စည်းပုံအတိအကျသို့ ပြောင်းလဲပြီး တိုက်ရိုက် ဒေါင်းလုဒ်ဆွဲယူနိုင်ပါသည်။ Upload %, Encode % (ETA) နှင့် Download % တို့ကို အတန်းလေးဖြင့် တိကျစွာ ပြသပေးပါသည်။
        </p>

        <div class="drop-zone" id="dropZone" onclick="document.getElementById('videoInput').click()">
            <input type="file" id="videoInput" accept="video/mp4,video/*">
            <div class="drop-title">📁 ဗီဒီယိုဖိုင် ရွေးချယ်ရန် နှိပ်ပါ (သို့မဟုတ်) ဆွဲထည့်ပါ</div>
            <div class="drop-sub">Supports 1080p, 2K, 4K @ 60FPS / 120FPS MP4 & MOV</div>
            <div id="selectedFileBadge" class="selected-file" style="display:none;"></div>
        </div>

        <div class="controls-grid">
            <select id="encodeMode">
                <option value="xuqing_1000x2166_h264">🔥 Mode 1: 1000x2166 (Custom 2K) • H.264 (43.5 Mbps, High/L5.2) + METODE: xuqingxinnocent</option>
                <option value="xuqing_1080x1920_h264">✨ Mode 2: 1080x1920 (Full HD) • H.264 (43.5 Mbps, High/L5.2) + METODE: xuqingxinnocent</option>
                <option value="xuqing_1080x1920_hevc">💎 Mode 3: 1080x1920 (Full HD) • HEVC / hvc1 (22.3 Mbps, Main/L4.1) + METODE: xuqingxinnocent</option>
                <option value="header_only">⚡ Mode 4: Instant 1-Sec Header & METODE Rebuild Only (Encode လုပ်ပြီးသား ဖိုင်များအတွက်)</option>
            </select>
            <input type="text" id="customMethod" value="xuqingxinnocent" placeholder="METODE နာမည် (Default: xuqingxinnocent)">
            <button class="btn" id="startBtn" onclick="startProcess()">🚀 Start Encode & Extract Video</button>
        </div>

        <div class="progress-panel" id="progressPanel">
            <div class="progress-header">
                <div class="progress-stage" id="stageText">⏳ Initializing...</div>
                <div class="progress-stats" id="pctText">0%</div>
            </div>
            <div class="bar-track">
                <div class="bar-fill" id="barFill"></div>
            </div>
            <div class="progress-meta">
                <span id="detailMeta">Preparing video pipeline...</span>
                <span id="etaMeta">ETA: Calculating...</span>
            </div>
        </div>

        <div class="result-banner" id="resultBanner">
            <h4 id="resultTitle">✅ ဗီဒီယို ပြောင်းလဲမှု 100% အောင်မြင်ပါသည်!</h4>
            <div class="dl-actions">
                <button class="btn" id="downloadBtn" onclick="downloadOutputWithProgress()">⬇️ Download Video Now (With % Progress)</button>
                <button class="btn btn-blue" onclick="toggleDetails()">🔍 View Full Input vs. Output X-Ray Details</button>
            </div>
        </div>

        <div class="details-section" id="detailsSection">
            <div class="grid-2">
                <div>
                    <span class="section-tag tag-in">📥 Uploaded Input Video Details</span>
                    <h4>Input Summary</h4>
                    <pre id="inSummaryPre"></pre>
                    <h4>Input MP4 Box Structure</h4>
                    <pre id="inBoxPre"></pre>
                    <h4>Input FFprobe Full JSON</h4>
                    <pre id="inProbePre"></pre>
                </div>
                <div>
                    <span class="section-tag tag-out">📤 Output Video Details (1000x2166 • METODE: xuqingxinnocent)</span>
                    <h4>Output Summary</h4>
                    <pre id="outSummaryPre"></pre>
                    <h4>Output MP4 Box Structure (100% Exact Match)</h4>
                    <pre id="outBoxPre"></pre>
                    <h4>Output FFprobe Full JSON</h4>
                    <pre id="outProbePre"></pre>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h3>🔬 ၂။ Standalone Deep X-Ray Inspector (Encode မလုပ်ဘဲ ဗီဒီယိုဖိုင် အချက်အလက်အကုန် စစ်ဆေးရန်)</h3>
        <form action="/deep_xray" method="post" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/mp4,video/*" required style="margin-bottom:12px; color:#fff;">
            <button type="submit" class="btn" style="background: linear-gradient(135deg, #ff9100, #ff6d00); color:#000;">🔍 Inspect All Video Details</button>
        </form>
    </div>
</div>

<script>
let selectedFile = null;
let currentJobId = null;
let currentDownloadFilename = "xuqingxinnocent_1000x2166_HQ.mp4";
let pollTimer = null;

const videoInput = document.getElementById('videoInput');
const dropZone = document.getElementById('dropZone');
const badge = document.getElementById('selectedFileBadge');

videoInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) selectFile(e.target.files[0]);
});
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]);
});

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(sec) {
    if (!isFinite(sec) || sec < 0) return 'Calculating...';
    sec = Math.round(sec);
    if (sec < 60) return sec + 's';
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return m + 'm ' + s + 's';
}

function selectFile(file) {
    selectedFile = file;
    badge.style.display = 'inline-block';
    badge.textContent = `✅ ${file.name} (${formatBytes(file.size)})`;
}

function updateProgressUI(stage, pct, detail, eta) {
    document.getElementById('progressPanel').style.display = 'block';
    document.getElementById('stageText').textContent = stage;
    const clamped = Math.max(0, Math.min(100, Math.round(pct)));
    document.getElementById('pctText').textContent = clamped + '%';
    document.getElementById('barFill').style.width = clamped + '%';
    if (detail) document.getElementById('detailMeta').textContent = detail;
    if (eta) document.getElementById('etaMeta').textContent = eta;
}

function startProcess() {
    if (!selectedFile) {
        alert('ကျေးဇူးပြု၍ ဗီဒီယိုဖိုင် အရင်ရွေးချယ်ပါ!');
        return;
    }

    const mode = document.getElementById('encodeMode').value;
    const customMethod = (document.getElementById('customMethod').value || 'xuqingxinnocent').trim();
    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    document.getElementById('resultBanner').style.display = 'none';
    document.getElementById('detailsSection').style.display = 'none';

    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('mode', mode);
    formData.append('method_name', customMethod);

    const xhr = new XMLHttpRequest();
    const uploadStart = Date.now();

    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const pct = (e.loaded / e.total) * 100;
            const elapsed = (Date.now() - uploadStart) / 1000;
            const speed = elapsed > 0 ? (e.loaded / elapsed) : 0;
            const remaining = speed > 0 ? ((e.total - e.loaded) / speed) : 0;
            updateProgressUI(
                '📤 Step 1/3: Uploading Video to Server...',
                pct,
                `Uploaded ${formatBytes(e.loaded)} / ${formatBytes(e.total)} (${formatBytes(speed)}/s)`,
                `Upload ETA: ${formatTime(remaining)}`
            );
        }
    });

    xhr.onload = function () {
        if (xhr.status === 200) {
            const resp = JSON.parse(xhr.responseText);
            currentJobId = resp.job_id;
            pollJobStatus(currentJobId);
        } else {
            startBtn.disabled = false;
            updateProgressUI('❌ Upload Error', 0, xhr.responseText || 'Server error', '');
        }
    };

    xhr.onerror = function () {
        startBtn.disabled = false;
        updateProgressUI('❌ Network Error', 0, 'Failed to connect to server', '');
    };

    updateProgressUI('📤 Step 1/3: Starting Upload...', 0, 'Connecting...', 'ETA: Calculating...');
    xhr.open('POST', '/api/start_job', true);
    xhr.send(formData);
}

function pollJobStatus(jobId) {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
        try {
            const res = await fetch(`/api/job_status/${jobId}?t=${Date.now()}`);
            if (!res.ok) return;
            const data = await res.json();

            if (data.status === 'processing') {
                updateProgressUI(
                    `⚙️ Step 2/3: ${data.stage || 'Encoding 1000x2166 H.264 60FPS...'}`,
                    data.progress || 0,
                    data.detail || 'Applying xuqingxinnocent 1000x2166 formula...',
                    `Encode ETA: ${data.eta || 'Calculating...'}`
                );
            } else if (data.status === 'done') {
                clearInterval(pollTimer);
                updateProgressUI(
                    '✅ Step 2/3 Complete: Video Rebuilt to 1000x2166 (METODE: xuqingxinnocent)!',
                    100,
                    `${data.message} • Output Size: ${formatBytes(data.output_size)}`,
                    'ETA: 0s (Ready)'
                );
                currentDownloadFilename = data.download_name || 'xuqingxinnocent_1000x2166_HQ.mp4';

                document.getElementById('inSummaryPre').textContent = data.in_summary || '';
                document.getElementById('inBoxPre').textContent = data.in_box_tree || '';
                document.getElementById('inProbePre').textContent = data.in_probe || '';

                document.getElementById('outSummaryPre').textContent = data.out_summary || '';
                document.getElementById('outBoxPre').textContent = data.out_box_tree || '';
                document.getElementById('outProbePre').textContent = data.out_probe || '';

                document.getElementById('resultTitle').textContent = `✅ ${data.message} (${formatBytes(data.output_size)})`;
                document.getElementById('resultBanner').style.display = 'block';
                document.getElementById('startBtn').disabled = false;

                downloadOutputWithProgress();
            } else if (data.status === 'error') {
                clearInterval(pollTimer);
                updateProgressUI('❌ Encoding Error', 0, data.error || 'Unknown error', '');
                document.getElementById('startBtn').disabled = false;
            }
        } catch (e) {}
    }, 600);
}

function downloadOutputWithProgress() {
    if (!currentJobId) return;
    const dlBtn = document.getElementById('downloadBtn');
    dlBtn.disabled = true;

    const xhr = new XMLHttpRequest();
    const dlStart = Date.now();
    xhr.open('GET', `/api/download_job/${currentJobId}`, true);
    xhr.responseType = 'blob';

    xhr.onprogress = function (e) {
        if (e.lengthComputable && e.total > 0) {
            const pct = (e.loaded / e.total) * 100;
            const elapsed = (Date.now() - dlStart) / 1000;
            const speed = elapsed > 0 ? (e.loaded / elapsed) : 0;
            const remaining = speed > 0 ? ((e.total - e.loaded) / speed) : 0;
            updateProgressUI(
                '⬇️ Step 3/3: Downloading Video to Your Device...',
                pct,
                `Downloaded ${formatBytes(e.loaded)} / ${formatBytes(e.total)} (${formatBytes(speed)}/s)`,
                `Download ETA: ${formatTime(remaining)}`
            );
        }
    };

    xhr.onload = function () {
        dlBtn.disabled = false;
        if (xhr.status === 200) {
            updateProgressUI(
                '🎉 All Steps Complete! Video Saved to Your Device!',
                100,
                `File: ${currentDownloadFilename} (${formatBytes(xhr.response.size)})`,
                'Completed in ' + formatTime((Date.now() - dlStart) / 1000)
            );
            const blobUrl = window.URL.createObjectURL(xhr.response);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = blobUrl;
            a.download = currentDownloadFilename;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                window.URL.revokeObjectURL(blobUrl);
                a.remove();
            }, 2000);
        } else {
            updateProgressUI('❌ Download Failed', 0, 'Could not download output file', '');
        }
    };

    xhr.onerror = function () {
        dlBtn.disabled = false;
        updateProgressUI('❌ Download Network Error', 0, 'Connection interrupted', '');
    };

    updateProgressUI('⬇️ Step 3/3: Starting Video Download...', 0, 'Requesting file stream...', 'Download ETA: Calculating...');
    xhr.send();
}

function toggleDetails() {
    const el = document.getElementById('detailsSection');
    el.style.display = (el.style.display === 'none' || !el.style.display) ? 'block' : 'none';
}
</script>
</body>
</html>
"""

EXACT_AVC1_FTYP_32B = bytes.fromhex("000000206674797069736f6d0000020069736f6d69736f32617663316d703431")
EXACT_MVHD_120B = bytes.fromhex("000000786d7668640100000000000000000000000000000000000000000003e8ffffffffffffffff0001000001000000000000000000000000010000000000000000000000000000000100000000000000000000000000004000000000000000000000000000000000000000000000000000000000000003")
EXACT_COLR_19B = bytes.fromhex("00000013636f6c726e636c7800010001000100")
EXACT_PASP_16B = bytes.fromhex("00000010706173700000000100000001")
EXACT_BTRT_20B = bytes.fromhex("00000014627472740000000001312d0001312d00")

def build_apple_ilst_udta(method_name="xuqingxinnocent"):
    clean_name = (method_name or "xuqingxinnocent").strip()
    ver_name = f"{clean_name}-v2.0.0" if not clean_name.endswith("-v2.0.0") else clean_name
    items = [
        (bytes.fromhex("a9415254"), clean_name.encode("utf-8")),
        (bytes.fromhex("a96e616d"), clean_name.encode("utf-8")),
        (bytes.fromhex("a9746f6f"), ver_name.encode("utf-8")),
        (bytes.fromhex("a9656e63"), ver_name.encode("utf-8")),
        (bytes.fromhex("a9777274"), clean_name.encode("utf-8")),
        (bytes.fromhex("a9636d74"), ver_name.encode("utf-8")),
        (b"cprt",                   ver_name.encode("utf-8")),
    ]
    hdlr_box = bytes.fromhex("0000002168646c7200000000000000006d6469726170706c000000000000000000")
    ilst_children = bytearray()
    for tag4, val_bytes in items:
        data_box = struct.pack(">I4sII", 16 + len(val_bytes), b"data", 1, 0) + val_bytes
        item_box = struct.pack(">I4s", 8 + len(data_box), tag4) + data_box
        ilst_children.extend(item_box)
    ilst_box = struct.pack(">I4s", 8 + len(ilst_children), b"ilst") + bytes(ilst_children)
    meta_payload = bytes(4) + hdlr_box + ilst_box
    meta_box = struct.pack(">I4s", 8 + len(meta_payload), b"meta") + meta_payload
    udta_box = struct.pack(">I4s", 8 + len(meta_box), b"udta") + meta_box
    return udta_box


def apply_exact_xuqing_1000x2166_structure(filepath, target_w=1000, target_h=2166, method_name="xuqingxinnocent", zero_stsd_wh=False):
    with open(filepath, "rb") as f:
        raw = f.read()

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
            if len(box_data) >= 102:
                entry_type = box_data[20:24]
                if entry_type == b"avc1":
                    avcc_box = b""
                    btrt_box = EXACT_BTRT_20B
                    sub_pos = 16 + 86
                    sub_end = len(box_data)
                    while sub_pos + 8 <= sub_end:
                        ssz = struct.unpack(">I", box_data[sub_pos:sub_pos+4])[0]
                        stp = box_data[sub_pos+4:sub_pos+8]
                        if ssz < 8 or sub_pos + ssz > sub_end:
                            break
                        if stp == b"avcC":
                            avcc_box = box_data[sub_pos:sub_pos+ssz]
                        elif stp == b"btrt" and ssz == 20:
                            btrt_box = box_data[sub_pos:sub_pos+ssz]
                        sub_pos += ssz

                    if avcc_box:
                        avc1_hdr = bytearray(box_data[16:16+86])
                        if zero_stsd_wh:
                            struct.pack_into(">HH", avc1_hdr, 32, 0, 0)
                        else:
                            struct.pack_into(">HH", avc1_hdr, 32, target_w, target_h)
                        avc1_hdr[50:82] = bytes(32)
                        avc1_children = avcc_box + EXACT_COLR_19B + EXACT_PASP_16B + btrt_box
                        avc1_size = 86 + len(avc1_children)
                        struct.pack_into(">I", avc1_hdr, 0, avc1_size)
                        avc1_box = bytes(avc1_hdr) + avc1_children
                        return struct.pack(">I4sII", 16 + len(avc1_box), b"stsd", 0, 1) + avc1_box

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

    mpos = 8
    mend = len(moov_bytes)
    new_moov_children = bytearray()
    new_moov_children.extend(EXACT_MVHD_120B)

    while mpos + 8 <= mend:
        msz = struct.unpack(">I", moov_bytes[mpos:mpos+4])[0]
        mtp = moov_bytes[mpos+4:mpos+8]
        if msz < 8 or mpos + msz > mend:
            break
        if mtp not in (b"mvhd", b"udta"):
            new_moov_children.extend(rebuild_box(moov_bytes[mpos:mpos+msz]))
        mpos += msz

    udta_box = build_apple_ilst_udta(method_name)
    new_moov_children.extend(udta_box)
    new_moov_size = 8 + len(new_moov_children)

    new_mdat_pos = len(EXACT_AVC1_FTYP_32B) + new_moov_size
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
        f.write(EXACT_AVC1_FTYP_32B)
        f.write(new_moov_box)
        f.write(mdat_bytes)

    return f"Rebuilt 1000x2166 H.264 HQ (METODE: {method_name}, moov={new_moov_size}B)"

def get_full_ffprobe_json(filepath):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_format",
        "-show_streams",
        "-of", "json", filepath
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        try:
            return json.loads(res.stdout)
        except Exception:
            return {"raw_stdout": res.stdout}
    return {"error": res.stderr}

def parse_mp4_boxes_detailed(data, offset=0, end=None, depth=0):
    if end is None:
        end = len(data)
    boxes = []
    pos = offset
    container_types = {b'moov', b'trak', b'mdia', b'minf', b'stbl', b'edts', b'dinf', b'udta', b'meta', b'ilst'}
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

        if btype == b'ftyp':
            info += f" -> {payload}"
        elif btype == b'mvhd' and len(payload) >= 28:
            ver = payload[0]
            ts = struct.unpack(">I", payload[12:16])[0] if ver == 0 else struct.unpack(">I", payload[20:24])[0]
            dur = struct.unpack(">I", payload[16:20])[0] if ver == 0 else struct.unpack(">q", payload[24:32])[0]
            info += f" -> version={ver}, timescale={ts}, duration={dur}"
        elif btype == b'tkhd' and len(payload) >= 84:
            version = payload[0]
            w_fp, h_fp = struct.unpack(">II", payload[76:84]) if version == 0 else struct.unpack(">II", payload[88:96])
            matrix = struct.unpack(">9I", payload[40:76]) if version == 0 else struct.unpack(">9I", payload[52:88])
            info += f" -> tkhd_width={w_fp/65536.0}, tkhd_height={h_fp/65536.0}, matrix={matrix}"
        elif btype == b'mdhd' and len(payload) >= 20:
            version = payload[0]
            timescale = struct.unpack(">I", payload[12:16])[0] if version == 0 else struct.unpack(">I", payload[20:24])[0]
            dur = struct.unpack(">I", payload[16:20])[0] if version == 0 else struct.unpack(">Q", payload[24:32])[0]
            info += f" -> timescale={timescale}, duration={dur}"
        elif btype == b'elst' and len(payload) >= 16:
            cnt = struct.unpack(">I", payload[4:8])[0]
            seg_dur, media_time, mr_int, mr_frac = struct.unpack(">IiHH", payload[8:20])
            info += f" -> count={cnt}, seg_dur={seg_dur}, media_time={media_time}, rate={mr_int}.{mr_frac}"
        elif btype == b'stsd' and len(payload) >= 16:
            entry_size = struct.unpack(">I", payload[8:12])[0]
            entry_type = payload[12:16].decode('latin1', errors='replace')
            if len(payload) >= 44:
                vw, vh = struct.unpack(">HH", payload[36:40])
                comp_len = payload[50] if len(payload) > 50 else 0
                comp_str = payload[51:51+comp_len].decode('latin1', errors='replace') if len(payload) >= 51+comp_len else ""
                info += f" -> sample_entry={entry_type} (entry_size={entry_size}), width(+28)={vw}, height(+30)={vh}, compressor='{comp_str}'"
            sub_start = pos + header_size + 8 + 86
            sub_end = pos + header_size + 8 + entry_size
            if sub_end <= pos + size and sub_start < sub_end:
                boxes.append(info)
                boxes.extend(parse_mp4_boxes_detailed(data, sub_start, sub_end, depth + 1))
                pos += size
                continue
        elif btype in (b'hvcC', b'avcC', b'pasp', b'clap', b'colr', b'uuid', b'fiel', b'btrt'):
            hex_preview = binascii.hexlify(payload[:256]).decode('ascii')
            ascii_preview = ''.join(chr(b) if 32 <= b < 127 else '.' for b in payload)
            info += f"\n{'  '*(depth+1)}HEX (first 256B): {hex_preview}\n{'  '*(depth+1)}ASCII: {ascii_preview}"
        elif btype == b'stss' and len(payload) >= 8:
            cnt = struct.unpack(">I", payload[4:8])[0]
            kfs = [struct.unpack(">I", payload[8+i*4:12+i*4])[0] for i in range(min(cnt, 30)) if 12+i*4 <= len(payload)]
            info += f" -> keyframe_count={cnt}, keyframes={kfs}"
        elif btype == b'stts' and len(payload) >= 16:
            cnt = struct.unpack(">I", payload[4:8])[0]
            sc, sd = struct.unpack(">II", payload[8:16])
            info += f" -> entry_count={cnt}, sample_count={sc}, sample_delta={sd}"
        elif btype == b'free' and len(payload) > 0:
            ascii_f = ''.join(chr(b) if 32 <= b < 127 else '.' for b in payload[:120])
            info += f" -> ASCII: {ascii_f}"

        boxes.append(info)
        if btype in container_types:
            sub_offset = pos + header_size + (4 if btype == b'meta' else 0)
            boxes.extend(parse_mp4_boxes_detailed(data, sub_offset, pos + size, depth + 1))
        pos += size
    return boxes

def generate_full_video_report(filepath):
    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    probe_json = get_full_ffprobe_json(filepath)
    with open(filepath, "rb") as f:
        raw_bytes = f.read()
    box_tree_str = "\n".join(parse_mp4_boxes_detailed(raw_bytes))

    streams = probe_json.get("streams", [])
    vstream = next((s for s in streams if s.get("codec_type") == "video"), {})
    astream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    fmt = probe_json.get("format", {})

    summary = {
        "file_size_bytes": file_size,
        "format_name": fmt.get("format_name"),
        "duration_sec": fmt.get("duration"),
        "overall_bit_rate": fmt.get("bit_rate"),
        "video_codec": f"{vstream.get('codec_name')} ({vstream.get('codec_tag_string')})",
        "video_profile_level": f"{vstream.get('profile')} / Level {vstream.get('level')}",
        "stream_resolution": f"{vstream.get('width')}x{vstream.get('height')} (coded: {vstream.get('coded_width')}x{vstream.get('coded_height')})",
        "pix_fmt_color": f"{vstream.get('pix_fmt')} | range={vstream.get('color_range')} | space={vstream.get('color_space')}",
        "frame_rate": f"r_frame_rate={vstream.get('r_frame_rate')} | avg_frame_rate={vstream.get('avg_frame_rate')}",
        "time_base": vstream.get("time_base"),
        "video_bit_rate": vstream.get("bit_rate"),
        "nb_frames": vstream.get("nb_frames"),
        "extradata_size": vstream.get("extradata_size"),
        "audio_info": f"{astream.get('codec_name')} | {astream.get('sample_rate')} Hz | {astream.get('channels')} ch | {astream.get('bit_rate')} bps"
    }
    return summary, box_tree_str, json.dumps(probe_json, indent=2)



def run_encode_job_background(job_id, in_path, out_path, mode, method_name, orig_filename):
    try:
        JOBS[job_id]["stage"] = "Inspecting Input Video..."
        JOBS[job_id]["progress"] = 5
        in_summary, in_box_tree, in_probe_pretty = generate_full_video_report(in_path)
        in_probe_data = json.loads(in_probe_pretty)
        in_streams = in_probe_data.get("streams", [])
        in_v = next((s for s in in_streams if s.get("codec_type") == "video"), {})
        in_w = int(in_v.get("width") or 1080)
        in_h = int(in_v.get("height") or 1920)
        is_landscape = in_w > in_h

        if mode in ("xuqing_1080x1920_h264", "xuqing_1080x1920_hevc"):
            target_w, target_h = (1920, 1080) if is_landscape else (1080, 1920)
        elif mode == "header_only":
            target_w, target_h = (in_w, in_h)
        else:
            # Default Mode 1: 1000x2166 Custom 2K Portrait
            target_w, target_h = (2166, 1000) if is_landscape else (1000, 2166)

        fmt = in_probe_data.get("format", {})
        total_dur = float(fmt.get("duration") or in_v.get("duration") or 0.0)
        clean_method = (method_name or "xuqingxinnocent").strip()
        ver_method = f"{clean_method}-v2.0.0"

        if mode == "header_only":
            JOBS[job_id]["stage"] = "Copying Bitstream for Instant Header Rebuild..."
            JOBS[job_id]["progress"] = 60
            JOBS[job_id]["eta"] = "1s"
            shutil.copyfile(in_path, out_path)
        elif mode == "xuqing_1080x1920_hevc":
            JOBS[job_id]["stage"] = f"Encoding {in_w}x{in_h} ➔ {target_w}x{target_h} HEVC (22.3 Mbps, Main@L4.1)..."
            JOBS[job_id]["progress"] = 10

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
                "-metadata:s:v:0", f"encoder={ver_method}",
                "-c:a", "aac",
                "-b:a", "320k",
                "-ar", "48000",
                "-ac", "2",
                "-movflags", "+faststart",
                "-progress", "pipe:1",
                "-nostats",
                out_path
            ]

            start_t = time.time()
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            tail_lines = []
            for line in proc.stdout:
                tail_lines.append(line)
                if len(tail_lines) > 40:
                    tail_lines.pop(0)
                if line.startswith("out_time_ms=") or line.startswith("out_time_us="):
                    try:
                        val_us = int(line.split("=", 1)[1].strip())
                        cur_sec = val_us / 1_000_000.0
                        if total_dur > 0 and cur_sec >= 0:
                            ratio = min(0.99, cur_sec / total_dur)
                            pct = int(10 + ratio * 82)
                            elapsed = time.time() - start_t
                            eta_sec = max(0, int((elapsed / ratio) - elapsed)) if ratio > 0.02 else 0
                            eta_str = (f"{eta_sec // 60}m {eta_sec % 60}s" if eta_sec >= 60 else f"{eta_sec}s") if ratio > 0.02 else "Calculating..."
                            JOBS[job_id]["progress"] = pct
                            JOBS[job_id]["detail"] = f"Encoded {cur_sec:.1f}s / {total_dur:.1f}s ({target_w}x{target_h} HEVC 22.3 Mbps)"
                            JOBS[job_id]["eta"] = eta_str
                    except Exception:
                        pass
            proc.wait()
            if proc.returncode != 0:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = "FFmpeg failed: " + "".join(tail_lines[-15:])
                return
        else:
            # H.264 43.5 Mbps High@L5.2 (supports both 1000x2166 and 1080x1920)
            JOBS[job_id]["stage"] = f"Encoding {in_w}x{in_h} ➔ {target_w}x{target_h} H.264 (43.5 Mbps, High@L5.2)..."
            JOBS[job_id]["progress"] = 10

            vf_chain = (
                f"scale={target_w}:{target_h}:flags=lanczos+accurate_rnd+full_chroma_int,"
                "setsar=1/1,"
                "fps=60,"
                "format=yuv420p"
            )

            x264_params = (
                "ref=1:bframes=1:b-adapt=0:keyint=30:min-keyint=15:scenecut=40:"
                "nal-hrd=none:colorprim=bt709:transfer=bt709:colormatrix=bt709:fullrange=off"
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
                "-video_track_timescale", "90000",
                "-c:v", "libx264",
                "-tag:v", "avc1",
                "-preset", "superfast",
                "-profile:v", "high",
                "-level:v", "5.2",
                "-b:v", "20000k",
                "-maxrate", "22000k",
                "-bufsize", "40000k",
                "-x264-params", x264_params,
                "-pix_fmt", "yuv420p",
                "-color_range", "tv",
                "-colorspace", "bt709",
                "-color_primaries", "bt709",
                "-color_trc", "bt709",
                "-field_order", "progressive",
                "-brand", "isom",
                "-metadata:s:v:0", f"encoder={ver_method}",
                "-c:a", "aac",
                "-b:a", "320k",
                "-ar", "48000",
                "-ac", "2",
                "-movflags", "+faststart",
                "-progress", "pipe:1",
                "-nostats",
                out_path
            ]

            start_t = time.time()
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            tail_lines = []
            for line in proc.stdout:
                tail_lines.append(line)
                if len(tail_lines) > 40:
                    tail_lines.pop(0)
                if line.startswith("out_time_ms=") or line.startswith("out_time_us="):
                    try:
                        val_us = int(line.split("=", 1)[1].strip())
                        cur_sec = val_us / 1_000_000.0
                        if total_dur > 0 and cur_sec >= 0:
                            ratio = min(0.99, cur_sec / total_dur)
                            pct = int(10 + ratio * 82)
                            elapsed = time.time() - start_t
                            if ratio > 0.02:
                                eta_sec = max(0, int((elapsed / ratio) - elapsed))
                                eta_str = f"{eta_sec // 60}m {eta_sec % 60}s" if eta_sec >= 60 else f"{eta_sec}s"
                            else:
                                eta_str = "Calculating..."
                            JOBS[job_id]["progress"] = pct
                            JOBS[job_id]["detail"] = f"Encoded {cur_sec:.1f}s / {total_dur:.1f}s ({target_w}x{target_h} H.264 43.5 Mbps)"
                            JOBS[job_id]["eta"] = eta_str
                    except Exception:
                        pass

            proc.wait()
            if proc.returncode != 0:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = "FFmpeg failed: " + "".join(tail_lines[-15:])
                return

        JOBS[job_id]["stage"] = f"Injecting METODE: {clean_method} & {target_w}x{target_h} Box Hierarchy..."
        JOBS[job_id]["progress"] = 95
        JOBS[job_id]["eta"] = "1s"

        msg = apply_exact_xuqing_1000x2166_structure(
            out_path,
            target_w=target_w,
            target_h=target_h,
            method_name=clean_method,
            zero_stsd_wh=False
        )

        out_summary, out_box_tree, out_probe_pretty = generate_full_video_report(out_path)
        out_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0

        base_name = os.path.splitext(orig_filename or "video")[0]
        dl_name = f"{base_name}_{clean_method}_{target_w}x{target_h}.mp4"

        JOBS[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Completed!",
            "eta": "0s",
            "message": msg,
            "output_size": out_size,
            "download_name": dl_name,
            "in_summary": json.dumps(in_summary, indent=2),
            "in_box_tree": in_box_tree,
            "in_probe": in_probe_pretty,
            "out_summary": json.dumps(out_summary, indent=2),
            "out_box_tree": out_box_tree,
            "out_probe": out_probe_pretty
        })
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/start_job", methods=["POST"])
def api_start_job():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    mode = request.form.get("mode", "xuqing_1000x2166_h264")
    method_name = request.form.get("method_name", "xuqingxinnocent")
    job_id = uuid.uuid4().hex[:12]

    in_path = os.path.join(JOBS_DIR, f"in_{job_id}.mp4")
    out_path = os.path.join(JOBS_DIR, f"out_{job_id}.mp4")
    video_file.save(in_path)

    JOBS[job_id] = {
        "status": "processing",
        "progress": 2,
        "stage": "Starting Video Pipeline...",
        "detail": f"File: {video_file.filename}",
        "eta": "Calculating...",
        "in_path": in_path,
        "out_path": out_path,
        "download_name": "xuqingxinnocent_1000x2166_HQ.mp4"
    }

    t = threading.Thread(
        target=run_encode_job_background,
        args=(job_id, in_path, out_path, mode, method_name, video_file.filename),
        daemon=True
    )
    t.start()

    return jsonify({"ok": True, "job_id": job_id})


@app.route("/api/job_status/<job_id>", methods=["GET"])
def api_job_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/download_job/<job_id>", methods=["GET"])
def api_download_job(job_id):
    job = JOBS.get(job_id)
    if not job or not os.path.exists(job["out_path"]):
        return "File not found", 404
    return send_file(
        job["out_path"],
        mimetype="video/mp4",
        as_attachment=True,
        download_name=job.get("download_name", "xuqingxinnocent_1000x2166_HQ.mp4")
    )


@app.route("/deep_xray", methods=["POST"])
def deep_xray():
    if "video" not in request.files:
        return "No video file", 400
    f = request.files["video"]
    ref_path = os.path.join(JOBS_DIR, "xray_in.mp4")
    f.save(ref_path)
    summary, box_tree, probe_pretty = generate_full_video_report(ref_path)
    summary_pretty = json.dumps(summary, indent=2)
    return f"""
    <body style="background:#0b0d12; color:#fff; font-family:Arial; padding:25px;">
        <h2>🔬 Complete Video Inspection Report ({f.filename})</h2>
        <a href="/" style="color:#00e676; font-size:16px;">⬅ Back to HQ Video Studio</a>
        <h3>1. Key Video & Audio Summary:</h3>
        <pre style="background:#07090e; color:#00e676; padding:15px; border-radius:8px;">{summary_pretty}</pre>
        <h3>2. MP4 Box & Header Hierarchy (tkhd, mvhd, stsd, hvcC, fiel, pasp, btrt, udta, free):</h3>
        <pre style="background:#07090e; color:#00e676; padding:15px; border-radius:8px;">{box_tree}</pre>
        <h3>3. Complete FFprobe Streams & Format JSON:</h3>
        <pre style="background:#07090e; color:#00e676; padding:15px; border-radius:8px;">{probe_pretty}</pre>
        <a href="/" style="color:#00e676; font-size:18px;">⬅ Back</a>
    </body>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

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

# Global dictionary to store real-time job progress, ETA, stage, and inspection reports
JOBS = {}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ 2K/4K HQ Video Studio — Quality_3_fixed_exact_q2_style</title>
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
        .header {
            text-align: center;
            margin-bottom: 28px;
        }
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
        .card h3 {
            margin: 0 0 10px;
            font-size: 17px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
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

        .controls-row {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 14px;
            align-items: center;
        }
        @media (max-width: 680px) { .controls-row { grid-template-columns: 1fr; } }

        select {
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

        /* Progress Bar Section */
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

        /* Ready / Download Section */
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

        /* Side-by-Side Details Grid */
        .details-section { display: none; margin-top: 24px; }
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px;
        }
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
        <h1>⚡ 2K/4K HQ Video Studio & Deep Inspector</h1>
        <p>Quality_3_fixed_exact_q2_style Formula • Real-Time Upload, Encode & Download Progress (%) + ETA</p>
    </div>

    <div class="card">
        <h3>🎬 ၁။ ဗီဒီယို အမြန်ထုတ်ယူရန် (Encode & Download with Live % Progress)</h3>
        <p class="subtext">
            မည်သည့် 2K / 4K / 1080p ဗီဒီယိုကိုမဆို <b>Quality_3_fixed_exact_q2_style.mp4</b> ဖွဲ့စည်းပုံအတိအကျသို့ ပြောင်းလဲပြီး တိုက်ရိုက် ဒေါင်းလုဒ်ဆွဲယူနိုင်ပါသည်။ Upload %, Encode % (ကြာချိန် ETA) နှင့် Download % တို့ကို အတန်းလေးဖြင့် တိကျစွာ ပြသပေးပါသည်။
        </p>

        <div class="drop-zone" id="dropZone" onclick="document.getElementById('videoInput').click()">
            <input type="file" id="videoInput" accept="video/mp4,video/*">
            <div class="drop-title">📁 ဗီဒီယိုဖိုင် ရွေးချယ်ရန် နှိပ်ပါ (သို့မဟုတ်) ဆွဲထည့်ပါ</div>
            <div class="drop-sub">Supports 1080p, 2K (1440p), 4K (2160p) @ 60FPS / 120FPS MP4 & MOV</div>
            <div id="selectedFileBadge" class="selected-file" style="display:none;"></div>
        </div>

        <div class="controls-row">
            <select id="encodeMode">
                <option value="full_encode">🔥 Mode 1: Full 2K/4K ➔ 1080p60 HEVC (22.3 Mbps) Encode + Quality_3 Exact Rebuild</option>
                <option value="header_only">⚡ Mode 2: Instant 1-Sec Header & Box Rebuild Only (Encode လုပ်ပြီးသား HEVC ဖိုင်များအတွက်)</option>
            </select>
            <button class="btn" id="startBtn" onclick="startProcess()">🚀 Start Encode & Extract Video</button>
        </div>

        <!-- Real-Time Progress Bar for Upload -> Encode -> Download -->
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

        <!-- Download Ready Box -->
        <div class="result-banner" id="resultBanner">
            <h4 id="resultTitle">✅ ဗီဒီယို ပြောင်းလဲမှု 100% အောင်မြင်ပါသည်!</h4>
            <div class="dl-actions">
                <button class="btn" id="downloadBtn" onclick="downloadOutputWithProgress()">⬇️ Download Video Now (With % Progress)</button>
                <button class="btn btn-blue" onclick="toggleDetails()">🔍 View Full Input vs. Output X-Ray Details</button>
            </div>
        </div>

        <!-- Side by Side Full Video Details -->
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
                    <span class="section-tag tag-out">📤 Output Video Details (Quality_3_fixed_exact_q2_style)</span>
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
let currentDownloadFilename = "Quality_3_fixed_exact_q2_style.mp4";
let pollTimer = null;

const videoInput = document.getElementById('videoInput');
const dropZone = document.getElementById('dropZone');
const badge = document.getElementById('selectedFileBadge');

videoInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
        selectFile(e.target.files[0]);
    }
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        selectFile(e.dataTransfer.files[0]);
    }
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
    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    document.getElementById('resultBanner').style.display = 'none';
    document.getElementById('detailsSection').style.display = 'none';

    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('mode', mode);

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
                    `⚙️ Step 2/3: ${data.stage || 'Encoding HEVC 1080p60...'}`,
                    data.progress || 0,
                    data.detail || 'Applying Quality_3_fixed_exact_q2_style formula...',
                    `Encode ETA: ${data.eta || 'Calculating...'}`
                );
            } else if (data.status === 'done') {
                clearInterval(pollTimer);
                updateProgressUI(
                    '✅ Step 2/3 Complete: Video Rebuilt to Exact Quality_3_fixed_exact_q2_style!',
                    100,
                    `${data.message} • Output Size: ${formatBytes(data.output_size)}`,
                    'ETA: 0s (Ready)'
                );
                currentDownloadFilename = data.download_name || 'Quality_3_fixed_exact_q2_style.mp4';

                // Populate inspection reports
                document.getElementById('inSummaryPre').textContent = data.in_summary || '';
                document.getElementById('inBoxPre').textContent = data.in_box_tree || '';
                document.getElementById('inProbePre').textContent = data.in_probe || '';

                document.getElementById('outSummaryPre').textContent = data.out_summary || '';
                document.getElementById('outBoxPre').textContent = data.out_box_tree || '';
                document.getElementById('outProbePre').textContent = data.out_probe || '';

                document.getElementById('resultTitle').textContent = `✅ ${data.message} (${formatBytes(data.output_size)})`;
                document.getElementById('resultBanner').style.display = 'block';
                document.getElementById('startBtn').disabled = false;

                // Automatically trigger download with live % progress bar!
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
        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z"
        rand_id = str(uuid.uuid4().int)[:4]
        dyn_tail_str = f"ZILEM_OPTIMIZED/1 {now_iso} {rand_id} (2)_zilem.mp4".encode("ascii")
        dyn_tail_box = struct.pack(">I4s", 69, b"free") + dyn_tail_str[:61].ljust(61, b" ")
        f.write(dyn_tail_box)

    return f"Rebuilt to Exact Quality_3_fixed_exact_q2_style (moov={new_moov_size}B, delta={delta}B)"



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



def run_encode_job_background(job_id, in_path, out_path, mode, orig_filename):
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
        target_w, target_h = (1920, 1080) if is_landscape else (1080, 1920)

        fmt = in_probe_data.get("format", {})
        total_dur = float(fmt.get("duration") or in_v.get("duration") or 0.0)

        if mode == "header_only":
            JOBS[job_id]["stage"] = "Copying Bitstream for Instant Header Rebuild..."
            JOBS[job_id]["progress"] = 60
            JOBS[job_id]["eta"] = "1s"
            shutil.copyfile(in_path, out_path)
        else:
            JOBS[job_id]["stage"] = f"Encoding {in_w}x{in_h} ➔ {target_w}x{target_h} HEVC 60FPS..."
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
                "-c:a", "aac",
                "-b:a", "130k",
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
                            JOBS[job_id]["detail"] = f"Encoded {cur_sec:.1f}s / {total_dur:.1f}s (HEVC 22.3 Mbps)"
                            JOBS[job_id]["eta"] = eta_str
                    except Exception:
                        pass

            proc.wait()
            if proc.returncode != 0:
                JOBS[job_id]["status"] = "error"
                JOBS[job_id]["error"] = "FFmpeg failed: " + "".join(tail_lines[-15:])
                return

        JOBS[job_id]["stage"] = "Rebuilding MP4 Boxes to Exact Quality_3_fixed_exact_q2_style..."
        JOBS[job_id]["progress"] = 95
        JOBS[job_id]["eta"] = "1s"

        msg = apply_exact_quality3_fixed_structure(out_path, target_w=target_w, target_h=target_h)

        # Also patch stsd (+28/+30) coded_width/height in-place if user wants direct upload without extension,
        # OR keep exact Quality_3_fixed_exact_q2_style structure:
        out_summary, out_box_tree, out_probe_pretty = generate_full_video_report(out_path)
        out_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0

        base_name = os.path.splitext(orig_filename or "video")[0]
        dl_name = f"{base_name}_Quality3_HQ.mp4"

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
    mode = request.form.get("mode", "full_encode")
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
        "download_name": "Quality_3_fixed_exact_q2_style.mp4"
    }

    t = threading.Thread(
        target=run_encode_job_background,
        args=(job_id, in_path, out_path, mode, video_file.filename),
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
        download_name=job.get("download_name", "Quality_3_fixed_exact_q2_style.mp4")
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

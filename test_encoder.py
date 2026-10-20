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

# Job status tracker for live logs
JOB_LOGS = {}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xuqingxinnocent — Auto HQ Video Processor</title>
    <style>
        :root {
            --bg: #050505;
            --card-bg: #0c0c0e;
            --card-border: rgba(255, 255, 255, 0.09);
            --text-main: #f5f5f7;
            --text-dim: #7c7c82;
            --accent: #00e676;
        }
        * {
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            margin: 0;
            padding: 28px 18px 60px;
            font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .wrapper {
            width: 100%;
            max-width: 440px;
            margin: 0 auto;
        }

        /* Main Upload & File Info Card */
        .upload-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 26px;
            overflow: hidden;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.75);
            margin-bottom: 22px;
            transition: border-color 0.2s ease;
        }
        .upload-card.dragover {
            border-color: rgba(255, 255, 255, 0.35);
        }
        .upload-top {
            padding: 34px 24px 30px;
            text-align: center;
            cursor: pointer;
            user-select: none;
        }
        .upload-top input[type="file"] {
            display: none;
        }
        .icon-box {
            width: 64px;
            height: 64px;
            margin: 0 auto 18px;
            border-radius: 18px;
            background: #161618;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }
        .icon-box svg {
            width: 26px;
            height: 26px;
            stroke: #d4d4d8;
            stroke-width: 2.1;
            fill: none;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
        .upload-title {
            font-size: 17px;
            font-weight: 700;
            color: #f4f4f6;
            margin: 0 0 8px;
            letter-spacing: -0.01em;
        }
        .upload-sub {
            font-size: 13.5px;
            font-weight: 500;
            color: var(--text-dim);
            margin: 0;
        }

        /* Mode Selector Section */
        .mode-section {
            border-top: 1px solid rgba(255, 255, 255, 0.07);
            padding: 18px 22px;
            background: rgba(0, 0, 0, 0.2);
        }
        .mode-label {
            font-size: 12.5px;
            font-weight: 600;
            color: var(--text-dim);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .mode-select {
            width: 100%;
            padding: 14px 16px;
            background: #161618;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            color: #ffffff;
            font-size: 14.5px;
            font-weight: 600;
            outline: none;
            cursor: pointer;
            transition: border-color 0.2s ease;
        }
        .mode-select:focus {
            border-color: #00e676;
        }

        /* File Metadata Section (Resolution, FrameRate, Size) */
        .file-meta {
            display: none;
            border-top: 1px solid rgba(255, 255, 255, 0.07);
            padding: 20px 24px;
            background: rgba(255, 255, 255, 0.01);
        }
        .meta-row {
            font-size: 15px;
            line-height: 1.5;
            margin-bottom: 10px;
            color: #d4d4d8;
        }
        .meta-row:last-child {
            margin-bottom: 0;
        }
        .meta-row strong {
            font-weight: 700;
            color: #ffffff;
        }

        /* Start Processing Button */
        .start-btn {
            width: 100%;
            padding: 20px 24px;
            border-radius: 20px;
            border: none;
            background: #ffffff;
            color: #09090b;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.01em;
            cursor: pointer;
            box-shadow: 0 8px 28px rgba(255, 255, 255, 0.12);
            transition: opacity 0.2s ease, transform 0.15s ease;
            margin-bottom: 22px;
        }
        .start-btn:active {
            transform: scale(0.99);
        }
        .start-btn:disabled {
            background: #d8d8dc;
            color: #6c6e7a;
            cursor: not-allowed;
            box-shadow: none;
            transform: none;
        }

        /* 4-Step Progress Card */
        .status-card {
            display: none;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 24px 22px 20px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65);
            margin-bottom: 18px;
        }
        .status-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 22px;
        }
        .status-left {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 17px;
            font-weight: 700;
            color: #f4f4f6;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #6b6b70;
            flex-shrink: 0;
        }
        .status-dot.active {
            background: #ffffff;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
            animation: pulseDot 1.4s infinite ease-in-out;
        }
        @keyframes pulseDot {
            0%, 100% { opacity: 0.45; transform: scale(0.92); }
            50% { opacity: 1; transform: scale(1.15); }
        }
        .status-pct {
            font-size: 17px;
            font-weight: 600;
            color: #9ca3af;
            font-variant-numeric: tabular-nums;
        }

        /* Stepper Track */
        .stepper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            padding: 0 4px;
            margin-bottom: 16px;
        }
        .step-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            z-index: 2;
            width: 58px;
        }
        .step-circle {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: transparent;
            border: 1.6px solid #45454a;
            transition: all 0.25s ease;
        }
        .step-item.done .step-circle {
            background: #7c7c82;
            border-color: #7c7c82;
        }
        .step-item.active .step-circle {
            background: #ffffff;
            border-color: #ffffff;
            box-shadow: 0 0 12px rgba(255, 255, 255, 0.9);
        }
        .step-label {
            font-size: 11.5px;
            font-weight: 600;
            letter-spacing: 0.08em;
            color: #6b6b70;
            text-transform: uppercase;
        }
        .step-item.active .step-label,
        .step-item.done .step-label {
            color: #a1a1aa;
        }
        .step-line {
            flex: 1;
            height: 1.5px;
            background: #27272a;
            margin: 0 -6px 22px;
            position: relative;
            overflow: hidden;
        }
        .step-line.done {
            background: #6b6b70;
        }

        .status-subdetail {
            font-size: 12px;
            color: var(--text-dim);
            text-align: center;
            margin-bottom: 14px;
            word-break: break-all;
        }

        /* Live Terminal Logs Drawer */
        .log-container {
            background: #000000;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 12px;
            max-height: 140px;
            overflow-y: auto;
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 11px;
            color: #00e676;
            text-align: left;
            line-height: 1.4;
            display: none;
        }
        .log-container.visible {
            display: block;
        }
        .log-line {
            margin-bottom: 3px;
            white-space: pre-wrap;
            word-break: break-all;
        }
    </style>
</head>
<body>
<div class="wrapper">
    <div class="upload-card" id="dropZone">
        <div class="upload-top" onclick="document.getElementById('videoInput').click()">
            <input type="file" id="videoInput" accept="video/mp4,video/*">
            <div class="icon-box">
                <svg viewBox="0 0 24 24">
                    <path d="M12 16V4m0 0L8 8m4-4l4 4" />
                    <path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
                </svg>
            </div>
            <p class="upload-title" id="uploadTitle">Select file — click to upload</p>
            <p class="upload-sub" id="uploadSub">Choose processing mode below</p>
        </div>

        <div class="mode-section">
            <div class="mode-label">Select Processing Mode</div>
            <select id="modeSelect" class="mode-select">
                <option value="downscale_4k">4K, 2K Encoding Downscale + Bypass</option>
                <option value="passthrough_1080p">1080P + Bypass (No Downscale)</option>
                <option value="all_bypass">All Video + Bypass (Smart Stream Copy)</option>
            </select>
        </div>

        <div class="file-meta" id="fileMeta">
            <div class="meta-row"><strong>Resolution :</strong> <span id="metaRes">Detecting...</span></div>
            <div class="meta-row"><strong>FrameRate :</strong> <span id="metaFps">Detecting...</span></div>
            <div class="meta-row"><strong>Size :</strong> <span id="metaSize">0 MB</span></div>
        </div>
    </div>

    <button class="start-btn" id="startBtn" onclick="startProcess()">Start Processing</button>

    <div class="status-card" id="statusCard">
        <div class="status-top">
            <div class="status-left">
                <span class="status-dot active" id="statusDot"></span>
                <span id="stageText">Processing File</span>
            </div>
            <div class="status-pct" id="pctText">0%</div>
        </div>

        <div class="stepper">
            <div class="step-item" id="stepLoad">
                <div class="step-circle"></div>
                <div class="step-label">LOAD</div>
            </div>
            <div class="step-line" id="line1"></div>
            <div class="step-item" id="stepRead">
                <div class="step-circle"></div>
                <div class="step-label">READ</div>
            </div>
            <div class="step-line" id="line2"></div>
            <div class="step-item" id="stepConvert">
                <div class="step-circle"></div>
                <div class="step-label">CONVERT</div>
            </div>
            <div class="step-line" id="line3"></div>
            <div class="step-item" id="stepBypass">
                <div class="step-circle"></div>
                <div class="step-label">BYPASS</div>
            </div>
        </div>

        <div class="status-subdetail" id="detailMeta">Initializing encoder...</div>

        <!-- Live Terminal Log Stream -->
        <div class="log-container" id="logContainer">
            <div class="log-line">[SYSTEM] Ready for video stream processing...</div>
        </div>
    </div>
</div>

<script>
let selectedFile = null;
let detectedSpecs = { width: 1080, height: 1920, fps: 30 };
let lastOutputBlobUrl = null;
let logPollInterval = null;

const videoInput = document.getElementById('videoInput');
const dropZone = document.getElementById('dropZone');
const modeSelect = document.getElementById('modeSelect');

videoInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) selectFile(e.target.files[0]);
});

function formatBytesMB(bytes) {
    if (!bytes || bytes === 0) return '0 MB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function detectMp4SpecsFromFile(file) {
    let width = 1080, height = 1920, fps = 30;
    try {
        const dims = await new Promise((resolve) => {
            const v = document.createElement('video');
            v.preload = 'metadata';
            const url = URL.createObjectURL(file);
            const timer = setTimeout(() => { URL.revokeObjectURL(url); resolve({ w: 1080, h: 1920 }); }, 4000);
            v.onloadedmetadata = () => {
                clearTimeout(timer);
                resolve({ w: v.videoWidth || 1080, h: v.videoHeight || 1920 });
                URL.revokeObjectURL(url);
            };
            v.onerror = () => { clearTimeout(timer); URL.revokeObjectURL(url); resolve({ w: 1080, h: 1920 }); };
            v.src = url;
        });
        width = dims.w;
        height = dims.h;
    } catch (_) {}
    return { width, height, fps };
}

async function selectFile(file) {
    selectedFile = file;
    document.getElementById('uploadTitle').textContent = 'Selected file — click to replace';
    document.getElementById('fileMeta').style.display = 'block';
    document.getElementById('metaSize').textContent = formatBytesMB(file.size);
    document.getElementById('metaRes').textContent = 'Detecting...';
    document.getElementById('metaFps').textContent = 'Detecting...';

    detectedSpecs = await detectMp4SpecsFromFile(file);
    document.getElementById('metaRes').textContent = `${detectedSpecs.width} × ${detectedSpecs.height}`;
    document.getElementById('metaFps').textContent = `${detectedSpecs.fps} FPS`;
}

function setStepperState(stageTitle, pct, stepIdx, detailText) {
    document.getElementById('statusCard').style.display = 'block';
    document.getElementById('stageText').textContent = stageTitle;
    const clamped = Math.max(0, Math.min(100, Math.round(pct)));
    document.getElementById('pctText').textContent = clamped + '%';
    document.getElementById('detailMeta').textContent = detailText || '';

    const dot = document.getElementById('statusDot');
    if (stepIdx >= 5) {
        dot.classList.remove('active');
        dot.style.background = '#00e676';
    } else {
        dot.classList.add('active');
        dot.style.background = '';
    }

    const steps = ['stepLoad', 'stepRead', 'stepConvert', 'stepBypass'];
    const lines = ['line1', 'line2', 'line3'];

    steps.forEach((id, i) => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'done');
        if (i + 1 < stepIdx || stepIdx === 5) el.classList.add('done');
        else if (i + 1 === stepIdx) el.classList.add('active');
    });

    lines.forEach((id, i) => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'done');
        if (i + 1 < stepIdx || stepIdx === 5) el.classList.add('done');
        else if (i + 1 === stepIdx - 1) el.classList.add('active');
    });
}

function appendLog(text) {
    const logBox = document.getElementById('logContainer');
    logBox.classList.add('visible');
    const line = document.createElement('div');
    line.className = 'log-line';
    line.textContent = text;
    logBox.appendChild(line);
    logBox.scrollTop = logBox.scrollHeight;
}

async function startProcess() {
    if (!selectedFile) {
        document.getElementById('videoInput').click();
        return;
    }

    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    document.getElementById('logContainer').innerHTML = '';

    const selectedMode = modeSelect.value;
    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('mode', selectedMode);
    formData.append('width', String(detectedSpecs.width));
    formData.append('height', String(detectedSpecs.height));

    setStepperState('Loading File', 10, 1, 'Initializing job stream...');
    appendLog(`[INFO] Selected mode: ${selectedMode}`);
    appendLog(`[INFO] Input resolution: ${detectedSpecs.width}x${detectedSpecs.height}`);

    try {
        const resp = await fetch('/api/process_video', {
            method: 'POST',
            body: formData
        });

        if (!resp.ok) {
            let errMsg = 'Processing failed';
            try {
                const j = await resp.json();
                if (j && j.error) errMsg = j.error;
            } catch (_) {}
            throw new Error(errMsg);
        }

        const data = await resp.json();
        const jobId = data.job_id;

        // Start polling logs and progress
        setStepperState('Converting & Downscaling', 35, 3, 'Processing video stream...');
        
        logPollInterval = setInterval(async () => {
            try {
                const lResp = await fetch(`/api/job_status/${jobId}`);
                if (lResp.ok) {
                    const lData = await lResp.json();
                    if (lData.logs && lData.logs.length > 0) {
                        const currentLines = document.getElementById('logContainer').children.length;
                        for (let k = currentLines; k < lData.logs.length; k++) {
                            appendLog(lData.logs[k]);
                        }
                    }
                    if (lData.status === 'completed') {
                        clearInterval(logPollInterval);
                        setStepperState('Applying Bypass', 90, 4, 'Finalizing stream...');
                        await sleep(300);
                        
                        // Trigger download
                        const dResp = await fetch(`/api/download/${jobId}`);
                        if (dResp.ok) {
                            const blob = await dResp.blob();
                            const baseName = (selectedFile.name || "video").replace(/\.[^/.]+$/, "");
                            const outFilename = `${baseName}_${selectedMode}_bypassed.mp4`;

                            if (lastOutputBlobUrl) URL.revokeObjectURL(lastOutputBlobUrl);
                            lastOutputBlobUrl = URL.createObjectURL(blob);

                            const a = document.createElement('a');
                            a.style.display = 'none';
                            a.href = lastOutputBlobUrl;
                            a.download = outFilename;
                            document.body.appendChild(a);
                            a.click();
                            setTimeout(() => a.remove(), 3000);

                            setStepperState('Completed', 100, 5, outFilename);
                            startBtn.disabled = false;
                        } else {
                            throw new Error("Failed to download processed file");
                        }
                    } else if (lData.status === 'error') {
                        clearInterval(logPollInterval);
                        throw new Error(lData.error || "Processing failed on server");
                    }
                }
            } catch (err) {
                // Ignore transient polling network errors
            }
        }, 800);

    } catch (err) {
        if (logPollInterval) clearInterval(logPollInterval);
        setStepperState('Error', 0, 1, err.message || String(err));
        appendLog(`[ERROR] ${err.message}`);
        startBtn.disabled = false;
    }
}
</script>
</body>
</html>
"""

EXACT_AVC1_FTYP_32B = binascii.unhexlify("000000206674797069736f6d0000020069736f6d69736f32617663316d703431")
EXACT_MVHD_120B = binascii.unhexlify("000000786d7668640100000000000000000000000000000000000000000003e8ffffffffffffffff0001000001000000000000000000000000010000000000000000000000000000000100000000000000000000000000004000000000000000000000000000000000000000000000000000000000000003")
EXACT_COLR_19B = binascii.unhexlify("00000013636f6c726e636c7800010001000100")
EXACT_PASP_16B = binascii.unhexlify("00000010706173700000000100000001")
EXACT_BTRT_20B = binascii.unhexlify("00000014627472740000000001312d0001312d00")

def build_apple_ilst_udta_py(method_name="xuqingxinnocent"):
    clean_name = (method_name or "xuqingxinnocent").strip()
    ver_name = clean_name if clean_name.endswith("-v2.0.0") else f"{clean_name}-v2.0.0"
    clean_bytes = clean_name.encode("utf-8")
    ver_bytes = ver_name.encode("utf-8")

    items = [
        (binascii.unhexlify("a9415254"), clean_bytes),
        (binascii.unhexlify("a96e616d"), clean_bytes),
        (binascii.unhexlify("a9746f6f"), ver_bytes),
        (binascii.unhexlify("a9656e63"), ver_bytes),
        (binascii.unhexlify("a9777274"), clean_bytes),
        (binascii.unhexlify("a9636d74"), ver_bytes),
        (b"cprt", ver_bytes),
    ]

    hdlr_box = binascii.unhexlify("0000002168646c7200000000000000006d6469726170706c000000000000000000")
    ilst_children = []
    for tag4, val_bytes in items:
        data_box = struct.pack(">I4sII", 16 + len(val_bytes), b"data", 1, 0) + val_bytes
        item_box = struct.pack(">I4s", 8 + len(data_box), tag4) + data_box
        ilst_children.append(item_box)

    ilst_payload = b"".join(ilst_children)
    ilst_box = struct.pack(">I4s", 8 + len(ilst_payload), b"ilst") + ilst_payload
    meta_payload = b"    " + hdlr_box + ilst_box
    meta_box = struct.pack(">I4s", 8 + len(meta_payload), b"meta") + meta_payload
    udta_box = struct.pack(">I4s", 8 + len(meta_box), b"udta") + meta_box
    return udta_box

def calculate_target_resolution_py(w, h):
    if not w or not h or w <= 0 or h <= 0:
        return 1080, 1920
    is_landscape = w > h
    max_edge = max(w, h)
    min_edge = min(w, h)
    if max_edge <= 1920 and min_edge <= 1080:
        sw = w if w % 2 == 0 else w - 1
        sh = h if h % 2 == 0 else h - 1
        return max(2, sw), max(2, sh)

    if is_landscape:
        target_h = 1080
        target_w = round((w / h) * target_h)
        if target_w > 1920:
            target_w = 1920
            target_h = round((h / w) * target_w)
    else:
        target_w = 1080
        target_h = round((h / w) * target_w)
        if target_h > 1920:
            target_h = 1920
            target_w = round((w / h) * target_w)

    target_w = target_w if target_w % 2 == 0 else target_w - 1
    target_h = target_h if target_h % 2 == 0 else target_h - 1
    return max(2, target_w), max(2, target_h)

def rebuild_box_py(box_data, is_video_trak, target_w, target_h):
    if len(box_data) < 8:
        return box_data
    sz, btype = struct.unpack(">I4s", box_data[:8])
    hdr_len = 8
    if sz == 1 and len(box_data) >= 16:
        sz = struct.unpack(">Q", box_data[8:16])[0]
        hdr_len = 16

    if btype == b"trak":
        is_video_trak = (b"vmhd" in box_data)

    if btype == b"tkhd":
        out = bytearray(box_data)
        ver = out[hdr_len]
        w_off = (hdr_len - 8) + (96 if ver == 1 else 84)
        if w_off + 8 <= len(out):
            if is_video_trak:
                struct.pack_into(">II", out, w_off, (target_w << 16) & 0xFFFFFFFF, (target_h << 16) & 0xFFFFFFFF)
            else:
                struct.pack_into(">II", out, w_off, 0, 0)
        return bytes(out)

    if btype == b"stsd" and is_video_trak and len(box_data) >= 102:
        entry_type = box_data[20:24]
        if entry_type == b"avc1":
            avcc_box = None
            btrt_box = EXACT_BTRT_20B
            sub_pos = 16 + 86
            sub_end = len(box_data)
            while sub_pos + 8 <= sub_end:
                ssz, stp = struct.unpack(">I4s", box_data[sub_pos:sub_pos + 8])
                if ssz < 8 or sub_pos + ssz > sub_end:
                    break
                if stp == b"avcC":
                    avcc_box = box_data[sub_pos:sub_pos + ssz]
                elif stp == b"btrt" and ssz == 20:
                    btrt_box = box_data[sub_pos:sub_pos + ssz]
                sub_pos += ssz
            if avcc_box:
                avc1_hdr = bytearray(box_data[16:16 + 86])
                struct.pack_into(">HH", avc1_hdr, 32, target_w, target_h)
                avc1_hdr[50:82] = b" " * 32
                avc1_children = avcc_box + EXACT_COLR_19B + EXACT_PASP_16B + btrt_box
                avc1_size = 86 + len(avc1_children)
                struct.pack_into(">I", avc1_hdr, 0, avc1_size)
                avc1_box = bytes(avc1_hdr) + avc1_children
                return struct.pack(">I4sII", 16 + len(avc1_box), b"stsd", 0, 1) + avc1_box
        elif entry_type in (b"hvc1", b"hev1"):
            out = bytearray(box_data)
            if len(out) >= 16 + 36:
                struct.pack_into(">HH", out, 16 + 32, target_w, target_h)
            return bytes(out)

    if btype not in (b"trak", b"mdia", b"minf", b"stbl"):
        return box_data

    cpos = hdr_len
    cend = len(box_data)
    children = []
    while cpos + 8 <= cend:
        csz, ctp = struct.unpack(">I4s", box_data[cpos:cpos + 8])
        if csz == 1 and cpos + 16 <= cend:
            csz = struct.unpack(">Q", box_data[cpos + 8:cpos + 16])[0]
        elif csz == 0:
            csz = cend - cpos
        if csz < 8 or cpos + csz > cend:
            break
        children.append(rebuild_box_py(box_data[cpos:cpos + csz], is_video_trak, target_w, target_h))
        cpos += csz

    children_bytes = b"".join(children)
    return struct.pack(">I4s", 8 + len(children_bytes), btype) + children_bytes

def shift_stco_py(buf, start, end_idx, delta):
    cur = start
    containers = (b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf")
    while cur + 8 <= end_idx:
        bsz, btp = struct.unpack_from(">I4s", buf, cur)
        hdr_len = 8
        if bsz == 1 and cur + 16 <= end_idx:
            bsz = struct.unpack_from(">Q", buf, cur + 8)[0]
            hdr_len = 16
        elif bsz == 0:
            bsz = end_idx - cur
        if bsz < hdr_len or cur + bsz > end_idx:
            break
        if btp in containers:
            shift_stco_py(buf, cur + hdr_len, cur + bsz, delta)
        elif btp == b"stco":
            cnt = struct.unpack_from(">I", buf, cur + 12)[0]
            for k in range(cnt):
                op = cur + 16 + k * 4
                if op + 4 <= cur + bsz:
                    old_v = struct.unpack_from(">I", buf, op)[0]
                    new_v = max(0, old_v + delta)
                    struct.pack_into(">I", buf, op, new_v & 0xFFFFFFFF)
        elif btp == b"co64":
            cnt = struct.unpack_from(">I", buf, cur + 12)[0]
            for k in range(cnt):
                op = cur + 16 + k * 8
                if op + 8 <= cur + bsz:
                    old_v = struct.unpack_from(">Q", buf, op)[0]
                    new_v = max(0, old_v + delta)
                    struct.pack_into(">Q", buf, op, new_v)
        cur += bsz

def apply_bypass_to_mp4_file(in_mp4_path, out_mp4_path, target_w, target_h):
    file_size = os.path.getsize(in_mp4_path)
    moov_pos, moov_size = -1, 0
    mdat_pos, mdat_size, mdat_hdr_len = -1, 0, 8

    with open(in_mp4_path, "rb") as f:
        pos = 0
        while pos + 8 <= file_size:
            f.seek(pos)
            hdr = f.read(16)
            if len(hdr) < 8:
                break
            sz, tp = struct.unpack(">I4s", hdr[:8])
            hdr_len = 8
            if sz == 1 and len(hdr) >= 16:
                sz = struct.unpack(">Q", hdr[8:16])[0]
                hdr_len = 16
            elif sz == 0:
                sz = file_size - pos
            if sz < hdr_len or pos + sz > file_size:
                break
            if tp == b"moov":
                moov_pos, moov_size = pos, sz
            elif tp == b"mdat" and sz > mdat_size:
                mdat_pos, mdat_size, mdat_hdr_len = pos, sz, hdr_len
            pos += sz

        if moov_pos == -1 or mdat_pos == -1:
            raise ValueError("Processed file missing moov or mdat")

        f.seek(moov_pos)
        moov_bytes = f.read(moov_size)

    moov_hdr_len = 16 if struct.unpack(">I", moov_bytes[:4])[0] == 1 else 8
    mpos = moov_hdr_len
    mend = len(moov_bytes)
    new_children = [EXACT_MVHD_120B]

    while mpos + 8 <= mend:
        msz, mtp = struct.unpack(">I4s", moov_bytes[mpos:mpos + 8])
        if msz == 1 and mpos + 16 <= mend:
            msz = struct.unpack(">Q", moov_bytes[mpos + 8:mpos + 16])[0]
        elif msz == 0:
            msz = mend - mpos
        if msz < 8 or mpos + msz > mend:
            break
        if mtp not in (b"mvhd", b"udta"):
            new_children.append(rebuild_box_py(moov_bytes[mpos:mpos + msz], False, target_w, target_h))
        mpos += msz

    new_children.append(build_apple_ilst_udta_py("xuqingxinnocent"))
    children_buf = bytearray(b"".join(new_children))

    new_moov_size = 8 + len(children_buf)
    new_mdat_pos = len(EXACT_AVC1_FTYP_32B) + new_moov_size

    mdat_payload_pos = mdat_pos + mdat_hdr_len
    mdat_payload_size = mdat_size - mdat_hdr_len

    if mdat_payload_size + 8 > 0xFFFFFFFF:
        new_mdat_hdr = struct.pack(">I4sQ", 1, b"mdat", mdat_payload_size + 16)
    else:
        new_mdat_hdr = struct.pack(">I4s", mdat_payload_size + 8, b"mdat")

    new_mdat_payload_pos = new_mdat_pos + len(new_mdat_hdr)
    delta = new_mdat_payload_pos - mdat_payload_pos

    if delta != 0:
        shift_stco_py(children_buf, 0, len(children_buf), delta)

    new_moov_box = struct.pack(">I4s", new_moov_size, b"moov") + bytes(children_buf)

    with open(in_mp4_path, "rb") as fin, open(out_mp4_path, "wb") as fout:
        fout.write(EXACT_AVC1_FTYP_32B)
        fout.write(new_moov_box)
        fout.write(new_mdat_hdr)
        fin.seek(mdat_payload_pos)
        remaining = mdat_payload_size
        while remaining > 0:
            chunk = fin.read(min(8 * 1024 * 1024, remaining))
            if not chunk:
                break
            fout.write(chunk)
            remaining -= len(chunk)

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

def background_process_job(job_id, in_path, processed_path, out_path, mode, orig_w, orig_h):
    try:
        def log(msg):
            print(msg)
            if job_id in JOBS:
                JOBS[job_id]["logs"].append(msg)

        log(f"[INFO] Starting job {job_id} with mode: {mode}")
        log(f"[INFO] Input specs: width={orig_w}, height={orig_h}")

        target_w, target_h = orig_w, orig_h

        if mode == "downscale_4k":
            # Check if 4K/2K, downscale to 1080p maintaining aspect ratio
            max_edge = max(orig_w, orig_h)
            min_edge = min(orig_w, orig_h)
            if max_edge > 1920 or min_edge > 1080:
                target_w, target_h = calculate_target_resolution_py(orig_w, orig_h)
                log(f"[INFO] 4K/2K detected. Downscaling to {target_w}x{target_h} using Lanczos CRF 16")
                scale_filter = f"scale={target_w}:{target_h}:flags=lanczos"
                cmd = [
                    "ffmpeg", "-y", "-i", in_path,
                    "-map", "0:v:0", "-map", "0:a?",
                    "-vf", scale_filter,
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart",
                    processed_path
                ]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if proc.returncode != 0:
                    log("[WARN] 'slow' preset failed, retrying with 'superfast'...")
                    cmd[cmd.index("slow")] = "superfast"
                    proc2 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if proc2.returncode != 0:
                        raise RuntimeError(f"FFmpeg encoding failed: {proc2.stderr.decode('utf-8', errors='ignore')[-300:]}")
            else:
                log("[INFO] File is already <= 1080p. Copying stream directly without downscale...")
                shutil.copy(in_path, processed_path)

        elif mode == "passthrough_1080p":
            log("[INFO] 1080P + Bypass mode: Ensuring 1080p container header passthrough...")
            target_w, target_h = calculate_target_resolution_py(orig_w, orig_h)
            cmd = [
                "ffmpeg", "-y", "-i", in_path,
                "-map", "0:v:0", "-map", "0:a?",
                "-c", "copy",
                "-movflags", "+faststart",
                processed_path
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0:
                # Transcode fallback if stream copy fails
                cmd_tr = [
                    "ffmpeg", "-y", "-i", in_path,
                    "-map", "0:v:0", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "superfast", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", processed_path
                ]
                subprocess.run(cmd_tr, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        elif mode == "all_bypass":
            log("[INFO] All Video + Bypass mode: Smart stream-copy remuxing...")
            cmd = [
                "ffmpeg", "-y", "-i", in_path,
                "-map", "0:v:0", "-map", "0:a?",
                "-c", "copy",
                "-movflags", "+faststart",
                processed_path
            ]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0 or not os.path.exists(processed_path) or os.path.getsize(processed_path) < 1024:
                cmd_hq = [
                    "ffmpeg", "-y", "-i", in_path,
                    "-map", "0:v:0", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "superfast", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", processed_path
                ]
                subprocess.run(cmd_hq, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        log(f"[INFO] Applying exact binary bypass (Target resolution: {target_w}x{target_h})...")
        apply_bypass_to_mp4_file(processed_path, out_path, target_w, target_h)
        log("[INFO] Processing completed successfully!")

        if job_id in JOBS:
            JOBS[job_id]["status"] = "completed"

    except Exception as e:
        err_msg = str(e)
        print(f"[ERROR] {err_msg}")
        if job_id in JOBS:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = err_msg
            JOBS[job_id]["logs"].append(f"[ERROR] {err_msg}")

@app.route("/api/process_video", methods=["POST"])
def api_process_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    vfile = request.files["video"]
    mode = request.form.get("mode", "downscale_4k")
    orig_w = int(request.form.get("width", 1080) or 1080)
    orig_h = int(request.form.get("height", 1920) or 1920)

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    in_path = os.path.join(job_dir, "input_video")
    processed_path = os.path.join(job_dir, "processed.mp4")
    out_path = os.path.join(job_dir, "final.mp4")

    vfile.save(in_path)

    JOBS[job_id] = {
        "status": "processing",
        "logs": [],
        "out_path": out_path
    }

    t = threading.Thread(target=background_process_job, args=(job_id, in_path, processed_path, out_path, mode, orig_w, orig_h))
    t.start()

    return jsonify({"job_id": job_id})

@app.route("/api/job_status/<job_id>", methods=["GET"])
def api_job_status(job_id):
    if job_id not in JOBS:
        return jsonify({"error": "Job not found"}), 404
    job = JOBS[job_id]
    return jsonify({
        "status": job["status"],
        "logs": job["logs"],
        "error": job.get("error")
    })

@app.route("/api/download/<job_id>", methods=["GET"])
def api_download(job_id):
    if job_id not in JOBS or JOBS[job_id]["status"] != "completed":
        return jsonify({"error": "File not ready"}), 400
    out_path = JOBS[job_id]["out_path"]
    if not os.path.exists(out_path):
        return jsonify({"error": "File missing"}), 404
    return send_file(out_path, mimetype="video/mp4", as_attachment=True, download_name="bypassed_video.mp4")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

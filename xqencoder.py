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

        /* Main Upload & File Info Card (Matches Screenshot 1 & 2) */
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
            padding: 38px 24px 34px;
            text-align: center;
            cursor: pointer;
            user-select: none;
        }
        .upload-top input[type="file"] {
            display: none;
        }
        .icon-box {
            width: 68px;
            height: 68px;
            margin: 0 auto 22px;
            border-radius: 18px;
            background: #161618;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }
        .icon-box svg {
            width: 28px;
            height: 28px;
            stroke: #d4d4d8;
            stroke-width: 2.1;
            fill: none;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
        .upload-title {
            font-size: 18px;
            font-weight: 700;
            color: #f4f4f6;
            margin: 0 0 10px;
            letter-spacing: -0.01em;
        }
        .upload-sub {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-dim);
            margin: 0;
        }

        /* File Metadata Section (Resolution, FrameRate, Size) */
        .file-meta {
            display: none;
            border-top: 1px solid rgba(255, 255, 255, 0.07);
            padding: 24px 26px;
            background: rgba(255, 255, 255, 0.01);
        }
        .meta-row {
            font-size: 16px;
            line-height: 1.5;
            margin-bottom: 14px;
            color: #d4d4d8;
            letter-spacing: 0.01em;
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

        /* 4-Step Progress Card (LOAD — READ — CONVERT — BYPASS) */
        .status-card {
            display: none;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 24px 22px 22px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65);
            margin-bottom: 18px;
        }
        .status-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
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
        .step-line.active::after {
            content: "✦";
            position: absolute;
            top: -8px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            color: #7c7c82;
            animation: moveStar 1.6s infinite linear;
        }
        @keyframes moveStar {
            0% { left: 15%; opacity: 0.3; }
            50% { left: 55%; opacity: 1; }
            100% { left: 85%; opacity: 0.3; }
        }

        .status-subdetail {
            margin-top: 14px;
            font-size: 12.5px;
            color: var(--text-dim);
            text-align: center;
        }

        /* Manual Re-Download Banner when Done */
        .done-actions {
            display: none;
            margin-top: 16px;
            text-align: center;
        }
        .dl-again-btn {
            display: inline-block;
            padding: 12px 22px;
            border-radius: 14px;
            background: #18181b;
            border: 1px solid rgba(255, 255, 255, 0.14);
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
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
            <p class="upload-sub">MP4 — up to 1080p 60 FPS</p>
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
                <span id="stageText">Reading File</span>
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

        <div class="status-subdetail" id="detailMeta"></div>

        <div class="done-actions" id="doneActions">
            <button class="dl-again-btn" id="downloadBtn" type="button" onclick="downloadOutputWithProgress()">⬇️ Download Video Again</button>
        </div>
    </div>
</div>

<script>
let selectedFile = null;
let currentJobId = null;
let currentDownloadFilename = "xuqingxinnocent_HQ.mp4";
let pollTimer = null;

const videoInput = document.getElementById('videoInput');
const dropZone = document.getElementById('dropZone');

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

function formatBytesMB(bytes) {
    if (!bytes || bytes === 0) return '0 MB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Fast client-side MP4 atom parser to detect exact FPS & Resolution from slice of file
async function detectMp4SpecsFromFile(file) {
    let width = 0, height = 0, fps = 0;

    // 1. Try HTML5 video element for fast width/height
    try {
        const dims = await new Promise((resolve) => {
            const v = document.createElement('video');
            v.preload = 'metadata';
            const url = URL.createObjectURL(file);
            const timer = setTimeout(() => { URL.revokeObjectURL(url); resolve({ w: 0, h: 0 }); }, 2500);
            v.onloadedmetadata = () => {
                clearTimeout(timer);
                const w = v.videoWidth || 0;
                const h = v.videoHeight || 0;
                URL.revokeObjectURL(url);
                resolve({ w, h });
            };
            v.onerror = () => {
                clearTimeout(timer);
                URL.revokeObjectURL(url);
                resolve({ w: 0, h: 0 });
            };
            v.src = url;
        });
        width = dims.w;
        height = dims.h;
    } catch (_) {}

    // 2. Parse MP4 header/tail chunk (first 2MB + last 2MB) for exact FPS (mdhd + stts) & tkhd resolution
    try {
        const parseSlice = async (blobSlice) => {
            const ab = await blobSlice.arrayBuffer();
            const bytes = new Uint8Array(ab);
            const view = new DataView(ab);
            const len = bytes.byteLength;

            for (let i = 0; i < len - 32; i++) {
                // 'tkhd'
                if ((width === 0 || height === 0) &&
                    bytes[i] === 0x74 && bytes[i+1] === 0x6B && bytes[i+2] === 0x68 && bytes[i+3] === 0x64) {
                    const ver = bytes[i + 4];
                    const wOff = ver === 1 ? (i + 92) : (i + 80);
                    if (wOff + 8 <= len) {
                        const tw = view.getUint32(wOff, false) >>> 16;
                        const th = view.getUint32(wOff + 4, false) >>> 16;
                        if (tw >= 120 && tw <= 7680 && th >= 120 && th <= 7680) {
                            width = tw;
                            height = th;
                        }
                    }
                }
                // 'mdhd' followed by 'vmhd' & 'stts' inside video track
                if (bytes[i] === 0x6D && bytes[i+1] === 0x64 && bytes[i+2] === 0x68 && bytes[i+3] === 0x64) {
                    const ver = bytes[i + 4];
                    const tsOff = ver === 1 ? (i + 24) : (i + 16);
                    if (tsOff + 8 <= len) {
                        const timescale = view.getUint32(tsOff, false);
                        // Search ahead within this track (up to 64KB) for 'vmhd' and 'stts'
                        const searchEnd = Math.min(len - 20, i + 65536);
                        let isVideo = false;
                        for (let j = i + 20; j < searchEnd; j++) {
                            if (bytes[j] === 0x76 && bytes[j+1] === 0x6D && bytes[j+2] === 0x68 && bytes[j+3] === 0x64) {
                                isVideo = true;
                            }
                            if (isVideo && bytes[j] === 0x73 && bytes[j+1] === 0x74 && bytes[j+2] === 0x74 && bytes[j+3] === 0x73) {
                                if (j + 20 <= len) {
                                    const entryCount = view.getUint32(j + 8, false);
                                    if (entryCount > 0) {
                                        const sampleDelta = view.getUint32(j + 16, false);
                                        if (sampleDelta > 0 && timescale > 0 && timescale <= 10000000) {
                                            const calcFps = Math.round(timescale / sampleDelta);
                                            if (calcFps >= 10 && calcFps <= 240) {
                                                fps = calcFps;
                                                break;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        };

        const headSize = Math.min(file.size, 2 * 1024 * 1024);
        await parseSlice(file.slice(0, headSize));
        if ((fps === 0 || width === 0) && file.size > headSize) {
            const tailStart = Math.max(0, file.size - 2 * 1024 * 1024);
            await parseSlice(file.slice(tailStart, file.size));
        }
    } catch (_) {}

    return {
        width: width || 1080,
        height: height || 1920,
        fps: fps || 30
    };
}

async function selectFile(file) {
    selectedFile = file;
    document.getElementById('uploadTitle').textContent = 'Selected file — click to replace';
    document.getElementById('fileMeta').style.display = 'block';
    document.getElementById('metaSize').textContent = formatBytesMB(file.size);
    document.getElementById('metaRes').textContent = 'Detecting...';
    document.getElementById('metaFps').textContent = 'Detecting...';

    const specs = await detectMp4SpecsFromFile(file);
    document.getElementById('metaRes').textContent = `${specs.width} × ${specs.height}`;
    document.getElementById('metaFps').textContent = `${specs.fps} FPS`;
}

// stepIdx: 1 = LOAD, 2 = READ, 3 = CONVERT, 4 = BYPASS, 5 = DONE
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
        const idx = i + 1;
        if (idx < stepIdx || stepIdx === 5) {
            el.classList.add('done');
        } else if (idx === stepIdx) {
            el.classList.add('active');
        }
    });

    lines.forEach((id, i) => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'done');
        const idx = i + 1;
        if (idx < stepIdx || stepIdx === 5) {
            el.classList.add('done');
        } else if (idx === stepIdx - 1) {
            el.classList.add('active');
        }
    });
}

function startProcess() {
    if (!selectedFile) {
        document.getElementById('videoInput').click();
        return;
    }

    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    document.getElementById('doneActions').style.display = 'none';

    const formData = new FormData();
    formData.append('video', selectedFile);
    formData.append('mode', 'auto_smart');
    formData.append('method_name', 'xuqingxinnocent');

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && e.total > 0) {
            const uploadRatio = e.loaded / e.total;
            // Map upload 0..100% into LOAD (0..10%) and READ (10..22%)
            if (uploadRatio < 0.35) {
                const pct = Math.max(1, Math.round(uploadRatio * 30));
                setStepperState('Loading File', pct, 1, `${formatBytes(e.loaded)} / ${formatBytes(e.total)}`);
            } else {
                const pct = Math.min(22, Math.round(10 + (uploadRatio - 0.35) * 18));
                setStepperState('Reading File', pct, 2, `${formatBytes(e.loaded)} / ${formatBytes(e.total)}`);
            }
        }
    });

    xhr.onload = function () {
        if (xhr.status === 200) {
            const resp = JSON.parse(xhr.responseText);
            currentJobId = resp.job_id;
            pollJobStatus(currentJobId);
        } else {
            startBtn.disabled = false;
            setStepperState('Upload Error', 0, 1, xhr.responseText || 'Server error');
        }
    };

    xhr.onerror = function () {
        startBtn.disabled = false;
        setStepperState('Network Error', 0, 1, 'Failed to connect to server');
    };

    setStepperState('Loading File', 2, 1, 'Starting pipeline...');
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

            if (data.in_res && data.in_fps) {
                document.getElementById('metaRes').textContent = data.in_res;
                document.getElementById('metaFps').textContent = data.in_fps;
            }

            if (data.status === 'processing') {
                const p = data.progress || 15;
                if (p <= 18) {
                    setStepperState('Reading File', p, 2, data.detail || '');
                } else if (p < 92) {
                    setStepperState('Converting Video', p, 3, `${data.detail || ''} ${data.eta ? '• ETA: ' + data.eta : ''}`);
                } else {
                    setStepperState('Applying Bypass', p, 4, data.stage || 'Injecting METODE: xuqingxinnocent...');
                }
            } else if (data.status === 'done') {
                clearInterval(pollTimer);
                currentDownloadFilename = data.download_name || 'xuqingxinnocent_HQ.mp4';
                setStepperState('Bypass Complete — Downloading', 98, 4, `${data.message} (${formatBytes(data.output_size)})`);
                document.getElementById('doneActions').style.display = 'block';
                document.getElementById('startBtn').disabled = false;
                downloadOutputWithProgress();
            } else if (data.status === 'error') {
                clearInterval(pollTimer);
                setStepperState('Processing Error', 0, 3, data.error || 'Unknown error');
                document.getElementById('startBtn').disabled = false;
            }
        } catch (e) {}
    }, 600);
}

function triggerDirectBrowserDownloadFallback() {
    if (!currentJobId) return;
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = `/api/download_job/${currentJobId}`;
    a.download = currentDownloadFilename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => a.remove(), 2000);
    setStepperState('Completed', 100, 5, `Saved: ${currentDownloadFilename}`);
}

function downloadOutputWithProgress() {
    if (!currentJobId) return;
    const dlBtn = document.getElementById('downloadBtn');
    if (dlBtn) dlBtn.disabled = true;

    const xhr = new XMLHttpRequest();
    xhr.open('GET', `/api/download_job/${currentJobId}`, true);
    xhr.responseType = 'blob';

    xhr.onprogress = function (e) {
        if (e.lengthComputable && e.total > 0) {
            const pct = Math.min(99, Math.round(95 + (e.loaded / e.total) * 5));
            setStepperState(
                'Applying Bypass',
                pct,
                4,
                `Downloading ${formatBytes(e.loaded)} / ${formatBytes(e.total)}`
            );
        }
    };

    xhr.onload = function () {
        if (dlBtn) dlBtn.disabled = false;
        if (xhr.status === 200 && xhr.response && xhr.response.size > 0) {
            setStepperState(
                'Completed',
                100,
                5,
                `${currentDownloadFilename} (${formatBytes(xhr.response.size)})`
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
            }, 3000);
        } else {
            triggerDirectBrowserDownloadFallback();
        }
    };

    xhr.onerror = function () {
        if (dlBtn) dlBtn.disabled = false;
        triggerDirectBrowserDownloadFallback();
    };

    xhr.send();
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
    file_size = os.path.getsize(filepath)
    moov_bytes = None
    mdat_pos = -1
    mdat_size = 0

    with open(filepath, "rb") as f:
        pos = 0
        while pos + 8 <= file_size:
            f.seek(pos)
            hdr = f.read(16)
            if len(hdr) < 8:
                break
            sz = struct.unpack(">I", hdr[:4])[0]
            tp = hdr[4:8]
            if sz == 1:
                if len(hdr) < 16:
                    break
                sz = struct.unpack(">Q", hdr[8:16])[0]
            elif sz == 0:
                sz = file_size - pos
            if sz < 8 or pos + sz > file_size:
                break
            if tp == b"moov":
                f.seek(pos)
                moov_bytes = f.read(sz)
            elif tp == b"mdat" and mdat_pos == -1:
                mdat_pos = pos
                mdat_size = sz
                if moov_bytes is not None:
                    break
            pos += sz

    if not moov_bytes or mdat_pos == -1:
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

    tmp_out = filepath + ".rebuilt"
    CHUNK_SIZE = 8 * 1024 * 1024
    with open(filepath, "rb") as fin, open(tmp_out, "wb") as fout:
        fout.write(EXACT_AVC1_FTYP_32B)
        fout.write(new_moov_box)
        fin.seek(mdat_pos)
        rem = mdat_size
        while rem > 0:
            chunk = fin.read(min(CHUNK_SIZE, rem))
            if not chunk:
                break
            fout.write(chunk)
            rem -= len(chunk)

    os.replace(tmp_out, filepath)
    return f"Rebuilt {target_w}x{target_h} H.264 60FPS HQ (METODE: {method_name})"


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


def run_encode_job_background(job_id, in_path, out_path, orig_filename):
    try:
        JOBS[job_id]["stage"] = "Reading File"
        JOBS[job_id]["progress"] = 15

        in_probe_data = get_full_ffprobe_json(in_path)
        in_streams = in_probe_data.get("streams", [])
        in_v = next((s for s in in_streams if s.get("codec_type") == "video"), {})
        in_w = int(in_v.get("width") or 1080)
        in_h = int(in_v.get("height") or 1920)
        is_landscape = in_w > in_h

        # Detect input FPS for UI display
        fps_str = in_v.get("avg_frame_rate") or in_v.get("r_frame_rate") or "30/1"
        in_fps_num = 30
        try:
            if "/" in fps_str:
                n, d = fps_str.split("/", 1)
                if float(d) > 0:
                    in_fps_num = round(float(n) / float(d))
            else:
                in_fps_num = round(float(fps_str))
        except Exception:
            in_fps_num = 30

        JOBS[job_id]["in_res"] = f"{in_w} × {in_h}"
        JOBS[job_id]["in_fps"] = f"{in_fps_num} FPS"

        min_dim = min(in_w, in_h)
        max_dim = max(in_w, in_h)
        is_already_1000x2166 = (in_w == 1000 and in_h == 2166) or (in_w == 2166 and in_h == 1000)

        # Check if 2K / 4K (> 1080p) vs 1080p / 720p (<= 1080p, including 1440x1080)
        is_2k_or_4k = (not is_already_1000x2166) and (min_dim > 1088 or max_dim > 1928)

        if is_2k_or_4k:
            # 2K / 4K file ➔ Dedicated High Quality + Bypass (1000x2166 Custom 2K @ 60FPS)
            target_w, target_h = (2166, 1000) if is_landscape else (1000, 2166)
            mode_label = f"2K/4K HQ Mode ({target_w}x{target_h} 60FPS)"
        else:
            # 1080p / 720p file (including 1440x1080) ➔ Auto 1080p, 60FPS + Bypass
            if (in_w == 1440 and in_h == 1080) or (in_w == 1080 and in_h == 1440):
                target_w, target_h = in_w, in_h
            elif abs((max_dim / max(1, min_dim)) - (4.0 / 3.0)) < 0.08:
                # 4:3 720p (e.g. 960x720) -> 1440x1080 1080p
                target_w, target_h = (1440, 1080) if is_landscape else (1080, 1440)
            else:
                # Standard 1080p / 720p -> 1080x1920 (or 1920x1080)
                target_w, target_h = (1920, 1080) if is_landscape else (1080, 1920)
            mode_label = f"1080p 60FPS Auto ({target_w}x{target_h})"

        fmt = in_probe_data.get("format", {})
        total_dur = float(fmt.get("duration") or in_v.get("duration") or 0.0)
        clean_method = "xuqingxinnocent"
        ver_method = f"{clean_method}-v2.0.0"

        JOBS[job_id]["stage"] = "Converting Video"
        JOBS[job_id]["progress"] = 25
        JOBS[job_id]["detail"] = f"{mode_label}"

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
                        pct = int(25 + ratio * 65)
                        elapsed = time.time() - start_t
                        if ratio > 0.02:
                            eta_sec = max(0, int((elapsed / ratio) - elapsed))
                            eta_str = f"{eta_sec // 60}m {eta_sec % 60}s" if eta_sec >= 60 else f"{eta_sec}s"
                        else:
                            eta_str = "Calculating..."
                        JOBS[job_id]["progress"] = pct
                        JOBS[job_id]["detail"] = f"{mode_label} • {cur_sec:.1f}s / {total_dur:.1f}s"
                        JOBS[job_id]["eta"] = eta_str
                except Exception:
                    pass

        proc.wait()
        if proc.returncode != 0:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = "FFmpeg failed: " + "".join(tail_lines[-15:])
            return

        try:
            if os.path.exists(in_path) and os.path.exists(out_path):
                os.remove(in_path)
        except Exception:
            pass

        JOBS[job_id]["stage"] = "Applying Bypass"
        JOBS[job_id]["progress"] = 94
        JOBS[job_id]["eta"] = "1s"

        msg = apply_exact_xuqing_1000x2166_structure(
            out_path,
            target_w=target_w,
            target_h=target_h,
            method_name=clean_method,
            zero_stsd_wh=False
        )

        out_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
        base_name = os.path.splitext(orig_filename or "video")[0]
        dl_name = f"{base_name}_{clean_method}_{target_w}x{target_h}_60fps.mp4"

        JOBS[job_id].update({
            "status": "done",
            "progress": 100,
            "stage": "Completed",
            "eta": "0s",
            "message": msg,
            "output_size": out_size,
            "download_name": dl_name
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
    job_id = uuid.uuid4().hex[:12]

    in_path = os.path.join(JOBS_DIR, f"in_{job_id}.mp4")
    out_path = os.path.join(JOBS_DIR, f"out_{job_id}.mp4")
    video_file.save(in_path)

    JOBS[job_id] = {
        "status": "processing",
        "progress": 15,
        "stage": "Reading File",
        "detail": f"File: {video_file.filename}",
        "eta": "Calculating...",
        "in_path": in_path,
        "out_path": out_path,
        "download_name": "xuqingxinnocent_HQ.mp4"
    }

    t = threading.Thread(
        target=run_encode_job_background,
        args=(job_id, in_path, out_path, video_file.filename),
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
        download_name=job.get("download_name", "xuqingxinnocent_HQ.mp4")
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

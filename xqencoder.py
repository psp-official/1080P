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
            <p class="upload-sub">MP4 / MOV / MKV / WebM — Original Resolution Passthrough</p>
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
    </div>
</div>

<script>
let selectedFile = null;
let detectedSpecs = { width: 1080, height: 1920, fps: 30 };
let lastOutputBlobUrl = null;

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

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

function hexToBytes(hex) {
    const bytes = new Uint8Array(hex.length / 2);
    for (let i = 0; i < bytes.length; i++) {
        bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
    }
    return bytes;
}

function concatBytes(arrays) {
    let totalLen = 0;
    for (const a of arrays) totalLen += a.byteLength;
    const out = new Uint8Array(totalLen);
    let offset = 0;
    for (const a of arrays) {
        out.set(new Uint8Array(a.buffer, a.byteOffset, a.byteLength), offset);
        offset += a.byteLength;
    }
    return out;
}

function packU32BE(val) {
    const b = new Uint8Array(4);
    new DataView(b.buffer).setUint32(0, val >>> 0, false);
    return b;
}

function asciiToBytes(str) {
    const out = new Uint8Array(str.length);
    for (let i = 0; i < str.length; i++) out[i] = str.charCodeAt(i) & 0xFF;
    return out;
}

// Universal File Slice Reader with FileReader Fallback (fixes Android/iOS WebView NotReadableError on 500MB+ files)
async function readSliceBufferSafe(file, start, end) {
    const s = Math.max(0, start);
    const e = Math.min(file.size, end);
    if (e <= s) return new ArrayBuffer(0);
    const blob = file.slice(s, e);
    try {
        if (typeof blob.arrayBuffer === 'function') {
            return await blob.arrayBuffer();
        }
    } catch (_) {}
    return await new Promise((resolve, reject) => {
        const fr = new FileReader();
        fr.onload = () => resolve(fr.result);
        fr.onerror = () => reject(fr.error || new Error("File slice read error"));
        fr.readAsArrayBuffer(blob);
    });
}

const EXACT_AVC1_FTYP_32B = hexToBytes("000000206674797069736f6d0000020069736f6d69736f32617663316d703431");
const EXACT_MVHD_120B = hexToBytes("000000786d7668640100000000000000000000000000000000000000000003e8ffffffffffffffff0001000001000000000000000000000000010000000000000000000000000000000100000000000000000000000000004000000000000000000000000000000000000000000000000000000000000003");
const EXACT_COLR_19B = hexToBytes("00000013636f6c726e636c7800010001000100");
const EXACT_PASP_16B = hexToBytes("00000010706173700000000100000001");
const EXACT_BTRT_20B = hexToBytes("00000014627472740000000001312d0001312d00");

function buildAppleIlstUdta(methodName = "xuqingxinnocent") {
    const cleanName = (methodName || "xuqingxinnocent").trim();
    const verName = cleanName.endsWith("-v2.0.0") ? cleanName : `${cleanName}-v2.0.0`;
    const enc = new TextEncoder();
    const cleanBytes = enc.encode(cleanName);
    const verBytes = enc.encode(verName);

    const items = [
        [hexToBytes("a9415254"), cleanBytes],
        [hexToBytes("a96e616d"), cleanBytes],
        [hexToBytes("a9746f6f"), verBytes],
        [hexToBytes("a9656e63"), verBytes],
        [hexToBytes("a9777274"), cleanBytes],
        [hexToBytes("a9636d74"), verBytes],
        [asciiToBytes("cprt"),   verBytes]
    ];

    const hdlrBox = hexToBytes("0000002168646c7200000000000000006d6469726170706c000000000000000000");
    const ilstChildren = [];

    for (const [tag4, valBytes] of items) {
        const dataBox = concatBytes([
            packU32BE(16 + valBytes.byteLength),
            asciiToBytes("data"),
            packU32BE(1),
            packU32BE(0),
            valBytes
        ]);
        const itemBox = concatBytes([
            packU32BE(8 + dataBox.byteLength),
            tag4,
            dataBox
        ]);
        ilstChildren.push(itemBox);
    }

    const ilstPayload = concatBytes(ilstChildren);
    const ilstBox = concatBytes([packU32BE(8 + ilstPayload.byteLength), asciiToBytes("ilst"), ilstPayload]);
    const metaPayload = concatBytes([new Uint8Array(4), hdlrBox, ilstBox]);
    const metaBox = concatBytes([packU32BE(8 + metaPayload.byteLength), asciiToBytes("meta"), metaPayload]);
    const udtaBox = concatBytes([packU32BE(8 + metaBox.byteLength), asciiToBytes("udta"), metaBox]);
    return udtaBox;
}

// Fast client-side MP4 atom parser to detect exact FPS & Resolution
async function detectMp4SpecsFromFile(file) {
    let width = 0, height = 0, fps = 0;

    try {
        const dims = await new Promise((resolve) => {
            const v = document.createElement('video');
            v.preload = 'metadata';
            const url = URL.createObjectURL(file);
            const timer = setTimeout(() => { URL.revokeObjectURL(url); resolve({ w: 0, h: 0 }); }, 4000);
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

    try {
        const parseSlice = async (startOff, endOff) => {
            const ab = await readSliceBufferSafe(file, startOff, endOff);
            const bytes = new Uint8Array(ab);
            const view = new DataView(ab);
            const len = bytes.byteLength;

            for (let i = 0; i < len - 32; i++) {
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
                if (bytes[i] === 0x6D && bytes[i+1] === 0x64 && bytes[i+2] === 0x68 && bytes[i+3] === 0x64) {
                    const ver = bytes[i + 4];
                    const tsOff = ver === 1 ? (i + 24) : (i + 16);
                    if (tsOff + 8 <= len) {
                        const timescale = view.getUint32(tsOff, false);
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

        const headSize = Math.min(file.size, 8 * 1024 * 1024);
        await parseSlice(0, headSize);
        if ((fps === 0 || width === 0) && file.size > headSize) {
            const tailStart = Math.max(0, file.size - 8 * 1024 * 1024);
            await parseSlice(tailStart, file.size);
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

    detectedSpecs = await detectMp4SpecsFromFile(file);
    document.getElementById('metaRes').textContent = `${detectedSpecs.width} × ${detectedSpecs.height}`;
    document.getElementById('metaFps').textContent = `${detectedSpecs.fps} FPS`;
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

function readBoxType(u8, off) {
    return String.fromCharCode(u8[off], u8[off + 1], u8[off + 2], u8[off + 3]);
}

// Deep Binary Search fallback that tolerates trailing garbage bytes or slight size mismatches
async function deepFindBoxInChunk(file, boxFourCC, startOffset, endOffset) {
    const c0 = boxFourCC.charCodeAt(0),
          c1 = boxFourCC.charCodeAt(1),
          c2 = boxFourCC.charCodeAt(2),
          c3 = boxFourCC.charCodeAt(3);
    const fileSize = file.size;
    const CHUNK = 8 * 1024 * 1024;
    let cur = Math.max(0, startOffset);
    const limit = Math.min(fileSize, endOffset);

    const validSubBoxes = {
        "moov": ["mvhd", "trak", "mvex", "udta", "meta"],
        "mdat": []
    };

    while (cur < limit) {
        const sliceEnd = Math.min(limit, cur + CHUNK);
        const ab = await readSliceBufferSafe(file, cur, sliceEnd);
        const u8 = new Uint8Array(ab);
        const view = new DataView(ab);

        for (let i = 4; i <= u8.byteLength - 8; i++) {
            if (u8[i] === c0 && u8[i+1] === c1 && u8[i+2] === c2 && u8[i+3] === c3) {
                const boxStart = cur + i - 4;
                let sz = view.getUint32(i - 4, false);
                let hdrLen = 8;
                if (sz === 1 && i + 12 <= u8.byteLength) {
                    const hi = view.getUint32(i + 4, false);
                    const lo = view.getUint32(i + 8, false);
                    sz = hi * 4294967296 + lo;
                    hdrLen = 16;
                } else if (sz === 0) {
                    sz = fileSize - boxStart;
                }

                // If moov, verify child box signature (mvhd/trak) so we never match random video bytes,
                // and clamp size if file has slight truncation or trailing bytes!
                if (boxFourCC === "moov" && i + hdrLen + 4 <= u8.byteLength) {
                    const subTp = readBoxType(u8, i - 4 + hdrLen + 4);
                    if (validSubBoxes.moov.includes(subTp)) {
                        const clampedSz = (sz >= 8 && boxStart + sz <= fileSize) ? sz : (fileSize - boxStart);
                        if (clampedSz >= 32) {
                            return { pos: boxStart, size: clampedSz };
                        }
                    }
                } else if (boxFourCC === "mdat") {
                    if (sz >= 8 && boxStart + sz <= fileSize + 64) {
                        const clampedSz = Math.min(sz, fileSize - boxStart);
                        if (clampedSz > 1024) {
                            return { pos: boxStart, size: clampedSz };
                        }
                    }
                }
            }
        }
        if (sliceEnd >= limit) break;
        cur += CHUNK - 128;
    }
    return null;
}

async function locateMoovAndMdatRobust(file) {
    const fileSize = file.size;
    let pos = 0;
    let moovPos = -1, moovSize = 0;
    let mdatPos = -1, mdatSize = 0;

    // Check first 16 bytes to detect WebM/MKV (EBML 0x1A45DFA3) or MPEG-TS (0x47)
    const sigAb = await readSliceBufferSafe(file, 0, Math.min(64, fileSize));
    const sigU8 = new Uint8Array(sigAb);
    let isNonMp4Container = false;
    if (sigU8.byteLength >= 4) {
        if (sigU8[0] === 0x1A && sigU8[1] === 0x45 && sigU8[2] === 0xDF && sigU8[3] === 0xA3) {
            isNonMp4Container = true; // MKV / WebM container disguised as .mp4
        }
    }

    if (!isNonMp4Container) {
        // 1. Standard Top-Level Box Walk (supports 32-bit, 64-bit, zero-padding skip)
        let safetySteps = 0;
        while (pos + 8 <= fileSize && safetySteps < 15000) {
            safetySteps++;
            const hdrAb = await readSliceBufferSafe(file, pos, Math.min(fileSize, pos + 16));
            if (hdrAb.byteLength < 8) break;
            const hdrView = new DataView(hdrAb);
            const hdrU8 = new Uint8Array(hdrAb);
            let sz = hdrView.getUint32(0, false);
            const tp = readBoxType(hdrU8, 4);

            // Skip zero padding bytes between boxes
            if (sz === 0 && hdrU8[4] === 0 && hdrU8[5] === 0 && hdrU8[6] === 0 && hdrU8[7] === 0) {
                pos += 4;
                continue;
            }

            if (sz === 1) {
                if (hdrAb.byteLength < 16) break;
                const hi = hdrView.getUint32(8, false);
                const lo = hdrView.getUint32(12, false);
                sz = hi * 4294967296 + lo;
            } else if (sz === 0) {
                sz = fileSize - pos;
            }

            const validFourCC = /^[ -~]{4}$/.test(tp);
            if (!validFourCC || sz < 8) {
                break;
            }
            if (pos + sz > fileSize) {
                sz = fileSize - pos;
            }

            if (tp === "moov") {
                moovPos = pos;
                moovSize = sz;
            } else if (tp === "mdat" && sz > mdatSize) {
                mdatPos = pos;
                mdatSize = sz;
            }
            pos += sz;
        }

        // 2. Deep Fallback Search if top-level walk missed moov or mdat
        const SCAN_WINDOW = 64 * 1024 * 1024; // 64MB head & tail scan
        if (moovPos === -1) {
            let found = await deepFindBoxInChunk(file, "moov", 0, Math.min(fileSize, SCAN_WINDOW));
            if (!found && fileSize > SCAN_WINDOW) {
                found = await deepFindBoxInChunk(file, "moov", Math.max(0, fileSize - SCAN_WINDOW), fileSize);
            }
            if (found) {
                moovPos = found.pos;
                moovSize = found.size;
            }
        }

        if (mdatPos === -1) {
            let found = await deepFindBoxInChunk(file, "mdat", 0, Math.min(fileSize, SCAN_WINDOW));
            if (!found && fileSize > SCAN_WINDOW) {
                found = await deepFindBoxInChunk(file, "mdat", Math.max(0, fileSize - SCAN_WINDOW), fileSize);
            }
            if (found) {
                mdatPos = found.pos;
                mdatSize = found.size;
            }
        }
    }

    return { moovPos, moovSize, mdatPos, mdatSize, isNonMp4Container };
}

function hasSubBox(u8, fourCC) {
    const c0 = fourCC.charCodeAt(0), c1 = fourCC.charCodeAt(1), c2 = fourCC.charCodeAt(2), c3 = fourCC.charCodeAt(3);
    for (let i = 0; i <= u8.byteLength - 4; i++) {
        if (u8[i] === c0 && u8[i+1] === c1 && u8[i+2] === c2 && u8[i+3] === c3) return true;
    }
    return false;
}

function readBoxHeader(u8, view, pos, endPos) {
    if (pos + 8 > endPos) return null;
    let sz = view.getUint32(pos, false);
    const tp = readBoxType(u8, pos + 4);
    let hdrLen = 8;
    if (sz === 1) {
        if (pos + 16 > endPos) return null;
        const hi = view.getUint32(pos + 8, false);
        const lo = view.getUint32(pos + 12, false);
        sz = hi * 4294967296 + lo;
        hdrLen = 16;
    } else if (sz === 0) {
        sz = endPos - pos;
    }
    if (sz < hdrLen || pos + sz > endPos) return null;
    return { size: sz, type: tp, hdrLen };
}

function rebuildBoxInBrowser(boxData, isVideoTrak, targetW, targetH) {
    const rootView = new DataView(boxData.buffer, boxData.byteOffset, boxData.byteLength);
    const rootHdr = readBoxHeader(boxData, rootView, 0, boxData.byteLength);
    if (!rootHdr) return boxData;

    const btype = rootHdr.type;
    if (btype === "trak") {
        isVideoTrak = hasSubBox(boxData, "vmhd");
    }

    if (btype === "tkhd") {
        const outTkhd = new Uint8Array(boxData);
        const view = new DataView(outTkhd.buffer, outTkhd.byteOffset, outTkhd.byteLength);
        const ver = outTkhd[rootHdr.hdrLen];
        const wOff = (rootHdr.hdrLen - 8) + (ver === 1 ? 96 : 84);
        if (wOff + 8 <= outTkhd.byteLength) {
            if (isVideoTrak) {
                view.setUint32(wOff, (targetW << 16) >>> 0, false);
                view.setUint32(wOff + 4, (targetH << 16) >>> 0, false);
            } else {
                view.setUint32(wOff, 0, false);
                view.setUint32(wOff + 4, 0, false);
            }
        }
        return outTkhd;
    }

    if (btype === "stsd" && isVideoTrak) {
        if (boxData.byteLength >= 102) {
            const entryType = readBoxType(boxData, 20);
            const view = new DataView(boxData.buffer, boxData.byteOffset, boxData.byteLength);
            if (entryType === "avc1") {
                let avccBox = null;
                let btrtBox = EXACT_BTRT_20B;
                let subPos = 16 + 86;
                const subEnd = boxData.byteLength;
                while (subPos + 8 <= subEnd) {
                    const ssz = view.getUint32(subPos, false);
                    const stp = readBoxType(boxData, subPos + 4);
                    if (ssz < 8 || subPos + ssz > subEnd) break;
                    if (stp === "avcC") {
                        avccBox = boxData.slice(subPos, subPos + ssz);
                    } else if (stp === "btrt" && ssz === 20) {
                        btrtBox = boxData.slice(subPos, subPos + ssz);
                    }
                    subPos += ssz;
                }
                if (avccBox) {
                    const avc1Hdr = boxData.slice(16, 16 + 86);
                    const hdrView = new DataView(avc1Hdr.buffer, avc1Hdr.byteOffset, avc1Hdr.byteLength);
                    hdrView.setUint16(32, targetW, false);
                    hdrView.setUint16(34, targetH, false);
                    for (let z = 50; z < 82; z++) avc1Hdr[z] = 0;

                    const avc1Children = concatBytes([avccBox, EXACT_COLR_19B, EXACT_PASP_16B, btrtBox]);
                    const avc1Size = 86 + avc1Children.byteLength;
                    hdrView.setUint32(0, avc1Size >>> 0, false);

                    const avc1Box = concatBytes([avc1Hdr, avc1Children]);
                    return concatBytes([
                        packU32BE(16 + avc1Box.byteLength),
                        asciiToBytes("stsd"),
                        packU32BE(0),
                        packU32BE(1),
                        avc1Box
                    ]);
                }
            } else if (entryType === "hvc1" || entryType === "hev1") {
                const outStsd = new Uint8Array(boxData);
                if (outStsd.byteLength >= 16 + 36) {
                    const stsdView = new DataView(outStsd.buffer, outStsd.byteOffset, outStsd.byteLength);
                    stsdView.setUint16(16 + 32, targetW, false);
                    stsdView.setUint16(16 + 34, targetH, false);
                }
                return outStsd;
            }
        }
    }

    const containers = { "trak": 1, "mdia": 1, "minf": 1, "stbl": 1 };
    if (!containers[btype]) {
        return boxData;
    }

    let cpos = rootHdr.hdrLen;
    const cend = boxData.byteLength;
    const children = [];
    while (cpos + 8 <= cend) {
        const ch = readBoxHeader(boxData, rootView, cpos, cend);
        if (!ch) break;
        const childSlice = boxData.subarray(cpos, cpos + ch.size);
        children.push(rebuildBoxInBrowser(childSlice, isVideoTrak, targetW, targetH));
        cpos += ch.size;
    }
    const childrenBytes = concatBytes(children);
    return concatBytes([packU32BE(8 + childrenBytes.byteLength), asciiToBytes(btype), childrenBytes]);
}

function shiftStcoInBrowser(buf, start, endIdx, delta) {
    const view = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
    let cur = start;
    const containers = { "trak": 1, "mdia": 1, "minf": 1, "stbl": 1, "edts": 1, "dinf": 1 };
    while (cur + 8 <= endIdx) {
        const bh = readBoxHeader(buf, view, cur, endIdx);
        if (!bh) break;
        const bsz = bh.size;
        const btp = bh.type;
        if (containers[btp]) {
            shiftStcoInBrowser(buf, cur + bh.hdrLen, cur + bsz, delta);
        } else if (btp === "stco") {
            const cnt = view.getUint32(cur + 12, false);
            for (let k = 0; k < cnt; k++) {
                const op = cur + 16 + k * 4;
                if (op + 4 <= cur + bsz) {
                    const oldV = view.getUint32(op, false);
                    const newV = Math.max(0, oldV + delta);
                    view.setUint32(op, newV >>> 0, false);
                }
            }
        } else if (btp === "co64") {
            const cnt = view.getUint32(cur + 12, false);
            for (let k = 0; k < cnt; k++) {
                const op = cur + 16 + k * 8;
                if (op + 8 <= cur + bsz) {
                    const hi = view.getUint32(op, false);
                    const lo = view.getUint32(op + 4, false);
                    const oldV = hi * 4294967296 + lo;
                    const newV = Math.max(0, oldV + delta);
                    const newHi = Math.floor(newV / 4294967296);
                    const newLo = (newV % 4294967296) >>> 0;
                    view.setUint32(op, newHi >>> 0, false);
                    view.setUint32(op + 4, newLo, false);
                }
            }
        }
        cur += bsz;
    }
}

// Server-side FFmpeg Zero-Loss Remux + Bypass Fallback when file is MKV/WebM/Fragmented MP4 (no moov/mdat)
async function processViaServerFallback(file, targetW, targetH, fps) {
    setStepperState('Reading File (Server Remux)', 28, 2, 'Remuxing container to standard MP4...');
    const formData = new FormData();
    formData.append('video', file);
    formData.append('width', String(targetW));
    formData.append('height', String(targetH));
    formData.append('fps', String(fps));

    const resp = await fetch('/api/remux_bypass', {
        method: 'POST',
        body: formData
    });

    if (!resp.ok) {
        let errMsg = 'Server remux failed';
        try {
            const errJson = await resp.json();
            if (errJson && errJson.error) errMsg = errJson.error;
        } catch (_) {}
        throw new Error(errMsg);
    }

    setStepperState('Converting Video', 68, 3, '');
    await sleep(180);
    setStepperState('Applying Bypass', 90, 4, '');
    const outBlob = await resp.blob();
    return outBlob;
}

async function startProcess() {
    if (!selectedFile) {
        document.getElementById('videoInput').click();
        return;
    }

    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;

    try {
        // STEP 1: LOAD (0% -> 20%)
        setStepperState('Loading File', 8, 1, '');
        await sleep(180);

        const fileSize = selectedFile.size;
        const targetW = detectedSpecs.width || 1080;
        const targetH = detectedSpecs.height || 1920;
        const targetFps = detectedSpecs.fps || 60;
        const baseName = (selectedFile.name || "video").replace(/\.[^/.]+$/, "");
        const outFilename = `${baseName}_xuqingxinnocent_${targetW}x${targetH}_${targetFps}fps.mp4`;

        const { moovPos, moovSize, mdatPos, mdatSize, isNonMp4Container } = await locateMoovAndMdatRobust(selectedFile);

        let finalBlob = null;

        // If the 2560x1440 file is actually a WebM/MKV/Fragmented stream (which has no standard moov/mdat),
        // automatically fall back to Server FFmpeg stream-copy remux + exact binary bypass!
        if (moovPos === -1 || mdatPos === -1 || isNonMp4Container) {
            finalBlob = await processViaServerFallback(selectedFile, targetW, targetH, targetFps);
        } else {
            // STEP 2: READ (15% -> 45%)
            setStepperState('Reading File', 15, 2, '');
            await sleep(220);

            const moovAb = await readSliceBufferSafe(selectedFile, moovPos, moovPos + moovSize);
            const moovBytes = new Uint8Array(moovAb);
            setStepperState('Reading File', 42, 2, '');
            await sleep(200);

            // STEP 3: CONVERT (50% -> 82%)
            setStepperState('Converting Video', 65, 3, '');
            await sleep(250);

            const moovView = new DataView(moovBytes.buffer, moovBytes.byteOffset, moovBytes.byteLength);
            const moovRootHdr = readBoxHeader(moovBytes, moovView, 0, moovBytes.byteLength);
            let mpos = moovRootHdr ? moovRootHdr.hdrLen : 8;
            const mend = moovBytes.byteLength;
            const newMoovChildrenList = [EXACT_MVHD_120B];

            while (mpos + 8 <= mend) {
                const mh = readBoxHeader(moovBytes, moovView, mpos, mend);
                if (!mh) break;
                const msz = mh.size;
                const mtp = mh.type;
                if (mtp !== "mvhd" && mtp !== "udta") {
                    const boxSlice = moovBytes.subarray(mpos, mpos + msz);
                    newMoovChildrenList.push(rebuildBoxInBrowser(boxSlice, false, targetW, targetH));
                }
                mpos += msz;
            }

            // STEP 4: BYPASS (85% -> 100%)
            setStepperState('Applying Bypass', 88, 4, '');
            await sleep(220);

            const udtaBox = buildAppleIlstUdta("xuqingxinnocent");
            newMoovChildrenList.push(udtaBox);

            const newMoovChildren = concatBytes(newMoovChildrenList);
            const newMoovSize = 8 + newMoovChildren.byteLength;
            const newMdatPos = EXACT_AVC1_FTYP_32B.byteLength + newMoovSize;

            const mdatHdrAb = await readSliceBufferSafe(selectedFile, mdatPos, Math.min(fileSize, mdatPos + 16));
            const mdatHdrView = new DataView(mdatHdrAb);
            const origMdatSizeField = mdatHdrAb.byteLength >= 4 ? mdatHdrView.getUint32(0, false) : 0;
            const origMdatHdrLen = (origMdatSizeField === 1) ? 16 : 8;
            const mdatPayloadPos = mdatPos + origMdatHdrLen;
            const mdatPayloadSize = mdatSize - origMdatHdrLen;

            let newMdatHdr;
            if (mdatPayloadSize + 8 > 0xFFFFFFFF) {
                newMdatHdr = new Uint8Array(16);
                const mv = new DataView(newMdatHdr.buffer);
                mv.setUint32(0, 1, false);
                newMdatHdr.set(asciiToBytes("mdat"), 4);
                const total64 = mdatPayloadSize + 16;
                mv.setUint32(8, Math.floor(total64 / 4294967296) >>> 0, false);
                mv.setUint32(12, (total64 % 4294967296) >>> 0, false);
            } else {
                newMdatHdr = concatBytes([packU32BE(mdatPayloadSize + 8), asciiToBytes("mdat")]);
            }

            const newMdatPayloadPos = newMdatPos + newMdatHdr.byteLength;
            const delta = newMdatPayloadPos - mdatPayloadPos;

            if (delta !== 0) {
                shiftStcoInBrowser(newMoovChildren, 0, newMoovChildren.byteLength, delta);
            }

            const newMoovBox = concatBytes([packU32BE(newMoovSize), asciiToBytes("moov"), newMoovChildren]);
            const mdatPayloadSlice = selectedFile.slice(mdatPayloadPos, mdatPayloadPos + mdatPayloadSize);
            finalBlob = new Blob([EXACT_AVC1_FTYP_32B, newMoovBox, newMdatHdr, mdatPayloadSlice], { type: 'video/mp4' });
        }

        if (lastOutputBlobUrl) {
            try { URL.revokeObjectURL(lastOutputBlobUrl); } catch (_) {}
        }
        lastOutputBlobUrl = URL.createObjectURL(finalBlob);

        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = lastOutputBlobUrl;
        a.download = outFilename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => a.remove(), 3000);

        setStepperState('Completed', 100, 5, outFilename);
        startBtn.disabled = false;
    } catch (err) {
        setStepperState('Error', 0, 1, err.message || String(err));
        startBtn.disabled = false;
    }
}
</script>
</body>
</html>
"""

# Exact Binary Bypass Constants in Python for Server-Side Fallback
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
    meta_payload = b"\x00\x00\x00\x00" + hdlr_box + ilst_box
    meta_box = struct.pack(">I4s", 8 + len(meta_payload), b"meta") + meta_payload
    udta_box = struct.pack(">I4s", 8 + len(meta_box), b"udta") + meta_box
    return udta_box


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
                avc1_hdr[50:82] = b"\x00" * 32
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
            raise ValueError("Remuxed file missing moov or mdat")

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


@app.route("/api/remux_bypass", methods=["POST"])
def api_remux_bypass():
    if "video" not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    vfile = request.files["video"]
    target_w = int(request.form.get("width", 1080) or 1080)
    target_h = int(request.form.get("height", 1920) or 1920)

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    in_path = os.path.join(job_dir, "input_video")
    remux_path = os.path.join(job_dir, "remuxed.mp4")
    out_path = os.path.join(job_dir, "bypassed.mp4")

    try:
        vfile.save(in_path)

        # 1. Try lossless stream-copy remux first (0% quality loss, converts MKV/WebM/fMP4 -> standard MP4 with moov/mdat)
        cmd_copy = [
            "ffmpeg", "-y", "-i", in_path,
            "-map", "0:v:0", "-map", "0:a?",
            "-c", "copy",
            "-movflags", "+faststart",
            remux_path
        ]
        res = subprocess.run(cmd_copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 2. If input video codec is VP9/AV1 inside WebM that cannot be copied directly into standard avc1/hvc1 MP4,
        # transcode at near-lossless CRF 16 while preserving original resolution
        if res.returncode != 0 or not os.path.exists(remux_path) or os.path.getsize(remux_path) < 1024:
            cmd_hq = [
                "ffmpeg", "-y", "-i", in_path,
                "-map", "0:v:0", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "superfast", "-crf", "16",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                remux_path
            ]
            res2 = subprocess.run(cmd_hq, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res2.returncode != 0:
                return jsonify({"error": "FFmpeg remux failed: " + res2.stderr.decode("utf-8", errors="ignore")[-300:]}), 500

        apply_bypass_to_mp4_file(remux_path, out_path, target_w, target_h)
        return send_file(out_path, mimetype="video/mp4", as_attachment=True, download_name="bypassed.mp4")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

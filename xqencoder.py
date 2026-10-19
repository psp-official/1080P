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

    try {
        const parseSlice = async (blobSlice) => {
            const ab = await blobSlice.arrayBuffer();
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

function hasSubBox(u8, fourCC) {
    const c0 = fourCC.charCodeAt(0), c1 = fourCC.charCodeAt(1), c2 = fourCC.charCodeAt(2), c3 = fourCC.charCodeAt(3);
    for (let i = 0; i <= u8.byteLength - 4; i++) {
        if (u8[i] === c0 && u8[i+1] === c1 && u8[i+2] === c2 && u8[i+3] === c3) return true;
    }
    return false;
}

function rebuildBoxInBrowser(boxData, isVideoTrak, targetW, targetH) {
    const btype = readBoxType(boxData, 4);
    if (btype === "trak") {
        isVideoTrak = hasSubBox(boxData, "vmhd");
    }

    if (btype === "tkhd") {
        const outTkhd = new Uint8Array(boxData);
        const view = new DataView(outTkhd.buffer, outTkhd.byteOffset, outTkhd.byteLength);
        const ver = outTkhd[8];
        const wOff = ver === 1 ? 96 : 84;
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

    const view = new DataView(boxData.buffer, boxData.byteOffset, boxData.byteLength);
    let cpos = 8;
    const cend = boxData.byteLength;
    const children = [];
    while (cpos + 8 <= cend) {
        const csz = view.getUint32(cpos, false);
        if (csz < 8 || cpos + csz > cend) break;
        const childSlice = boxData.subarray(cpos, cpos + csz);
        children.push(rebuildBoxInBrowser(childSlice, isVideoTrak, targetW, targetH));
        cpos += csz;
    }
    const childrenBytes = concatBytes(children);
    return concatBytes([packU32BE(8 + childrenBytes.byteLength), asciiToBytes(btype), childrenBytes]);
}

function shiftStcoInBrowser(buf, start, endIdx, delta) {
    const view = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
    let cur = start;
    const containers = { "trak": 1, "mdia": 1, "minf": 1, "stbl": 1, "edts": 1, "dinf": 1 };
    while (cur + 8 <= endIdx) {
        const bsz = view.getUint32(cur, false);
        const btp = readBoxType(buf, cur + 4);
        if (bsz < 8 || cur + bsz > endIdx) break;
        if (containers[btp]) {
            shiftStcoInBrowser(buf, cur + 8, cur + bsz, delta);
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
            const bigDelta = BigInt(delta);
            for (let k = 0; k < cnt; k++) {
                const op = cur + 16 + k * 8;
                if (op + 8 <= cur + bsz) {
                    const oldV = view.getBigUint64(op, false);
                    const newV = oldV + bigDelta;
                    view.setBigUint64(op, newV >= 0n ? newV : 0n, false);
                }
            }
        }
        cur += bsz;
    }
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
        let pos = 0;
        let moovPos = -1, moovSize = 0;
        let mdatPos = -1, mdatSize = 0;

        // Scan top-level MP4 boxes using 16-byte slices (uses 0 MB RAM even on 1GB+ files!)
        while (pos + 8 <= fileSize) {
            const hdrAb = await selectedFile.slice(pos, Math.min(fileSize, pos + 16)).arrayBuffer();
            if (hdrAb.byteLength < 8) break;
            const hdrView = new DataView(hdrAb);
            const hdrU8 = new Uint8Array(hdrAb);
            let sz = hdrView.getUint32(0, false);
            const tp = readBoxType(hdrU8, 4);

            if (sz === 1) {
                if (hdrAb.byteLength < 16) break;
                sz = Number(hdrView.getBigUint64(8, false));
            } else if (sz === 0) {
                sz = fileSize - pos;
            }
            if (sz < 8 || pos + sz > fileSize) {
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

        // STEP 2: READ (15% -> 45%)
        setStepperState('Reading File', 15, 2, '');
        await sleep(220);

        if (moovPos === -1 || mdatPos === -1) {
            throw new Error("Invalid MP4 file (moov or mdat not found)");
        }

        const moovAb = await selectedFile.slice(moovPos, moovPos + moovSize).arrayBuffer();
        const moovBytes = new Uint8Array(moovAb);
        setStepperState('Reading File', 42, 2, '');
        await sleep(200);

        // STEP 3: CONVERT (50% -> 82%)
        // Auto Smart Routing:
        // - 2K / 4K (> 1080p) -> High Quality 1000x2166 + Bypass
        // - 1080p / 720p (<= 1080p, including 1440x1080) -> Auto 1080p, 60FPS + Bypass
        const inW = detectedSpecs.width || 1080;
        const inH = detectedSpecs.height || 1920;
        const isLandscape = inW > inH;
        const minDim = Math.min(inW, inH);
        const maxDim = Math.max(inW, inH);
        const isAlready1000x2166 = (inW === 1000 && inH === 2166) || (inW === 2166 && inH === 1000);
        const is2kOr4k = (!isAlready1000x2166) && (minDim > 1088 || maxDim > 1928);

        let targetW, targetH;
        if (is2kOr4k) {
            targetW = isLandscape ? 2166 : 1000;
            targetH = isLandscape ? 1000 : 2166;
        } else {
            if ((inW === 1440 && inH === 1080) || (inW === 1080 && inH === 1440)) {
                targetW = inW;
                targetH = inH;
            } else if (Math.abs((maxDim / Math.max(1, minDim)) - (4.0 / 3.0)) < 0.08) {
                targetW = isLandscape ? 1440 : 1080;
                targetH = isLandscape ? 1080 : 1440;
            } else {
                targetW = isLandscape ? 1920 : 1080;
                targetH = isLandscape ? 1080 : 1920;
            }
        }

        setStepperState('Converting Video', 65, 3, '');
        await sleep(250);

        const moovView = new DataView(moovBytes.buffer, moovBytes.byteOffset, moovBytes.byteLength);
        let mpos = 8;
        const mend = moovBytes.byteLength;
        const newMoovChildrenList = [EXACT_MVHD_120B];

        while (mpos + 8 <= mend) {
            const msz = moovView.getUint32(mpos, false);
            const mtp = readBoxType(moovBytes, mpos + 4);
            if (msz < 8 || mpos + msz > mend) break;
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
        const delta = newMdatPos - mdatPos;

        if (delta !== 0) {
            shiftStcoInBrowser(newMoovChildren, 0, newMoovChildren.byteLength, delta);
        }

        const newMoovBox = concatBytes([packU32BE(newMoovSize), asciiToBytes("moov"), newMoovChildren]);

        // Zero-Copy Blob assembly: combines 32B ftyp + rebuilt moov + direct disk slice of mdat!
        const mdatSlice = selectedFile.slice(mdatPos, mdatPos + mdatSize);
        const finalBlob = new Blob([EXACT_AVC1_FTYP_32B, newMoovBox, mdatSlice], { type: 'video/mp4' });

        const baseName = (selectedFile.name || "video").replace(/\.[^/.]+$/, "");
        const outFilename = `${baseName}_xuqingxinnocent_${targetW}x${targetH}_60fps.mp4`;

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

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

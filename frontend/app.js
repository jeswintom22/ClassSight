// ClassSight Frontend Logic

// Configuration
const API_URL = '/api/ocr/analyze';
const VIDEO_FEED_ID = 'video-feed';
const captureCanvas = document.getElementById('capture-canvas');

// DOM Elements
const analyzeBtn = document.getElementById('analyze-btn');
const ocrContent = document.getElementById('ocr-content');
const aiContent = document.getElementById('ai-content');
const videoElement = document.getElementById(VIDEO_FEED_ID);

// State
let isProcessing = false;

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    console.log("ClassSight Frontend Ready 🚀");

    // Start Webcam
    await initCamera();

    // Attach event listeners
    analyzeBtn.addEventListener('click', analyzeCurrentFrame);
});

/**
 * Initialize Webcam
 */
async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'environment' // Prefer back camera on mobile
            }
        });
        videoElement.srcObject = stream;
        console.log("Webcam started successfully");
    } catch (error) {
        console.error("Camera access denied:", error);
        showError("Camera access denied. Please allow camera permissions.");
        // Fallback or specific UI handling could go here
    }
}

/**
 * Capture current frame and send to backend for analysis
 */
async function analyzeCurrentFrame() {
    if (isProcessing) return;

    setLoadingState(true);

    try {
        // 1. Capture frame from video to canvas
        captureCanvas.width = videoElement.videoWidth;
        captureCanvas.height = videoElement.videoHeight;

        const context = captureCanvas.getContext('2d');
        context.drawImage(videoElement, 0, 0, captureCanvas.width, captureCanvas.height);

        // 2. Convert canvas to blob
        const imageBlob = await new Promise(resolve => captureCanvas.toBlob(resolve, 'image/png'));

        // 3. Prepare form data
        const formData = new FormData();
        formData.append('file', imageBlob, 'capture.png');

        // 4. Send to API
        console.log("Sending frame to backend...");
        const response = await fetch(API_URL, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Analysis Result:", data);

        // 5. Update UI
        updateUI(data);

    } catch (error) {
        console.error("Analysis Failed:", error);
        showError(error.message);
    } finally {
        setLoadingState(false);
    }
}

/**
 * Update the UI with results
 */
function updateUI(data) {
    // Update OCR Section
    if (data.combined_text) {
        ocrContent.innerHTML = `<div class="ocr-text">${escapeHtml(data.combined_text)}</div>`;
        document.getElementById('confidence-badge').style.display = 'inline-block';
        document.getElementById('confidence-badge').textContent = `${Math.round(data.confidence * 100)}% Match`;
    } else {
        ocrContent.innerHTML = '<div class="placeholder-text">No text detected in this frame.</div>';
    }

    // Update AI Section
    if (data.explanation) {
        // Format the explanation (convert newlines to paragraphs)
        const formattedExplanation = data.explanation
            .split('\n')
            .filter(line => line.trim() !== '')
            .map(line => `<p>${escapeHtml(line)}</p>`)
            .join('');

        aiContent.innerHTML = `<div class="ai-explanation">${formattedExplanation}</div>`;

        if (data.ai_model) {
            document.getElementById('ai-model-badge').textContent = data.ai_model;
        }
    } else {
        aiContent.innerHTML = '<div class="placeholder-text">No explanation generated.</div>';
    }
}

/**
 * Show loading skeletons
 */
function setLoadingState(loading) {
    isProcessing = loading;
    analyzeBtn.disabled = loading;
    analyzeBtn.innerHTML = loading ?
        '<span class="btn-icon">⏳</span> Analyzing...' :
        '<span class="btn-icon">⚡</span> Analyze Frame';

    if (loading) {
        // Show shimmer effect in AI panel
        aiContent.innerHTML = `
            <div class="ai-loading">
                <div class="shimmer-line"></div>
                <div class="shimmer-line"></div>
                <div class="shimmer-line medium"></div>
                <div class="shimmer-line short"></div>
            </div>
        `;
    }
}

/**
 * Show error message
 */
function showError(message) {
    aiContent.innerHTML = `
        <div style="color: #ef4444; text-align: center; margin-top: 1rem;">
            ⚠️ ${escapeHtml(message)}
        </div>
    `;
}

/**
 * Safety utility
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

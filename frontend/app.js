// ClassSight Frontend Logic - Phase 5
// Features: WebSocket, Auto-Capture, History, Keyboard Shortcuts

// ==================== Configuration ====================
const getWsUrl = () => {
    if (window.location.protocol === 'file:') {
        return 'ws://localhost:8000/api/ws/stream';
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/api/ws/stream`;
};

const CONFIG = {
    WS_URL: getWsUrl(),
    API_URL: '/api/ocr/analyze',
    DEFAULT_INTERVAL: 5000,
    HISTORY_KEY: 'classsight_history_v1'
};

// ==================== State Management ====================
const state = {
    isProcessing: false,
    isAutoCapture: false,
    captureInterval: CONFIG.DEFAULT_INTERVAL,
    intervalId: null,
    ws: null,
    history: [],
    isConnected: false
};

// ==================== DOM Elements ====================
const els = {
    video: document.getElementById('video-feed'),
    canvas: document.getElementById('capture-canvas'),
    ocrContent: document.getElementById('ocr-content'),
    aiContent: document.getElementById('ai-content'),
    analyzeBtn: document.getElementById('analyze-btn'),
    autoToggle: document.getElementById('auto-capture-toggle'),
    intervalSelect: document.getElementById('capture-interval'),
    statusBadge: document.getElementById('status-badge'),
    statusText: document.getElementById('status-text'),
    statusDot: document.querySelector('.status-dot'),
    historyList: document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    downloadBtn: document.getElementById('download-report-btn'),
    mockModeBtn: document.getElementById('mock-mode-btn'), // New Button
    liveIndicator: document.getElementById('live-indicator'),
    confidenceBadge: document.getElementById('confidence-badge'),
    aiModelBadge: document.getElementById('ai-model-badge')
};

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', async () => {
    console.log("ClassSight Phase 5 Initializing 🚀");

    // Load History
    loadHistory();

    // Initialize Camera
    await initCamera();

    // Initialize WebSocket
    connectWebSocket();

    // Attach Event Listeners
    setupEventListeners();

    // Update UI Status
    updateStatus("Ready", "ready");
});

// ==================== WebSocket Management ====================
function connectWebSocket() {
    updateStatus("Connecting...", "connecting");

    state.ws = new WebSocket(CONFIG.WS_URL);

    state.ws.onopen = () => {
        console.log("WS Connected ✅");
        state.isConnected = true;
        updateStatus("Live", "live");

        // Re-enable controls
        els.analyzeBtn.disabled = false;
    };

    state.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWSMessage(message);
    };

    state.ws.onclose = () => {
        console.log("WS Disconnected ❌");
        state.isConnected = false;
        updateStatus("Disconnected", "error");

        // Disable controls
        els.analyzeBtn.disabled = true;

        // Try reconnecting after 3s
        setTimeout(connectWebSocket, 3000);
    };

    state.ws.onerror = (error) => {
        console.error("WS Error:", error);
    };
}

function handleWSMessage(msg) {
    if (msg.type === 'status') {
        // Optional: show processing indicator
    } else if (msg.type === 'ocr_result') {
        // Show OCR immediately (progressive loading)
        renderOCR(msg.data);
    } else if (msg.type === 'ai_result') {
        // Show AI when ready
        renderAI(msg.data);
    } else if (msg.type === 'complete') {
        // Full result available
        state.isProcessing = false;
        addToHistory(msg.data);
        renderComplete(msg.data);

        if (!state.isAutoCapture) {
            setLoadingState(false);
        }
    } else if (msg.type === 'error') {
        showError(msg.message);
        state.isProcessing = false;
        setLoadingState(false);
    } else if (msg.type === 'result' && msg.source === 'cache') {
        // Cached result
        console.log("Using cached result");
        state.isProcessing = false;
        renderComplete(msg.data);
        setLoadingState(false);
    }
}

// ==================== Mock Mode Logic ====================
function triggerMockAnalysis() {
    console.log("Triggering Mock Analysis 🧪");
    setLoadingState(true);
    state.isProcessing = true;

    // Simulate network delay
    setTimeout(() => {
        // 1. Simulate OCR
        const mockOCR = {
            type: 'ocr_result',
            data: {
                combined_text: "E = mc²\nTheory of Relativity",
                confidence: 0.99
            }
        };
        handleWSMessage(mockOCR);

        // 2. Simulate AI delay
        setTimeout(() => {
            const mockComplete = {
                type: 'complete',
                data: {
                    combined_text: "E = mc²\nTheory of Relativity",
                    confidence: 0.99,
                    explanation: "This equation represents the mass-energy equivalence, introduced by Albert Einstein. \nE represents energy, m represents mass, and c is the speed of light.",
                    ai_model: "Mock Gemini",
                    timestamp: Date.now() / 1000
                }
            };
            handleWSMessage(mockComplete);
            state.isProcessing = false;
        }, 1500);

    }, 800);
}

// ==================== Camera & Capture ====================
async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'environment'
            }
        });
        els.video.srcObject = stream;
    } catch (error) {
        console.error("Camera Error:", error);
        showError("Camera access denied. Please check permissions.");
    }
}

async function captureFrame() {
    if (!state.isConnected || state.isProcessing) return;

    // Only set loading UI if manual capture
    if (!state.isAutoCapture) {
        setLoadingState(true);
    }

    state.isProcessing = true;

    try {
        // Draw frame to canvas
        els.canvas.width = els.video.videoWidth;
        els.canvas.height = els.video.videoHeight;
        const ctx = els.canvas.getContext('2d');
        ctx.drawImage(els.video, 0, 0);

        // Convert to Blob
        els.canvas.toBlob((blob) => {
            if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                state.ws.send(blob);
            } else {
                console.error("WS not open");
                state.isProcessing = false;
                setLoadingState(false);
            }
        }, 'image/jpeg', 0.8); // Compress JPEG 0.8 quality

    } catch (error) {
        console.error("Capture Error:", error);
        state.isProcessing = false;
        setLoadingState(false);
    }
}

// ==================== Auto-Capture Logic ====================
function toggleAutoCapture(enabled) {
    state.isAutoCapture = enabled;

    if (enabled) {
        // Clean start
        if (state.intervalId) clearInterval(state.intervalId);

        // Immediate first capture
        captureFrame();

        // Start loop
        state.intervalId = setInterval(captureFrame, state.captureInterval);

        els.statusBadge.classList.add('pulse-active');
        els.liveIndicator.style.display = 'flex';
        els.analyzeBtn.disabled = true;
        els.analyzeBtn.innerHTML = '<span class="btn-icon">🔄</span> Auto Mode';
    } else {
        // Stop loop
        if (state.intervalId) clearInterval(state.intervalId);
        state.intervalId = null;

        els.statusBadge.classList.remove('pulse-active');
        els.liveIndicator.style.display = 'none';
        els.analyzeBtn.disabled = false;
        els.analyzeBtn.innerHTML = '<span class="btn-icon">⚡</span> Capture';
    }
}

// ==================== UI Rendering ====================
function renderOCR(data) {
    if (data.combined_text) {
        els.ocrContent.innerHTML = `<div class="ocr-text">${escapeHtml(data.combined_text)}</div>`;
        els.confidenceBadge.style.display = 'inline-block';
        els.confidenceBadge.textContent = `${Math.round(data.confidence * 100)}% Match`;
    } else {
        els.ocrContent.innerHTML = '<div class="placeholder-text">No text visible</div>';
    }
}

function renderAI(data) {
    if (data.explanation) {
        const formatted = formatExplanation(data.explanation);
        els.aiContent.innerHTML = `<div class="ai-explanation">${formatted}</div>`;
        if (data.ai_model) els.aiModelBadge.textContent = data.ai_model;
    }
}

function renderComplete(data) {
    renderOCR(data);
    renderAI(data);
}

function setLoadingState(loading) {
    els.analyzeBtn.disabled = loading;
    els.analyzeBtn.innerHTML = loading ?
        '<span class="btn-icon">⏳</span> Analyzing...' :
        '<span class="btn-icon">⚡</span> Capture';

    if (loading) {
        // Show skeleton loader for AI
        els.aiContent.innerHTML = `
            <div class="ai-loading">
                <div class="skeleton-text"></div>
                <div class="skeleton-text"></div>
                <div class="skeleton-text medium"></div>
                <div class="skeleton-text short"></div>
            </div>
        `;
    }
}

function updateStatus(text, type) {
    els.statusText.textContent = text;
    // Reset classes
    els.statusDot.className = 'status-dot';

    if (type === 'live') els.statusDot.style.background = '#10b981'; // Green
    else if (type === 'connecting') els.statusDot.style.background = '#f59e0b'; // Yellow
    else if (type === 'error') els.statusDot.style.background = '#ef4444'; // Red
}

function showError(msg) {
    els.aiContent.innerHTML = `
        <div style="color: #ef4444; text-align: center; margin-top: 1rem;">
            ⚠️ ${escapeHtml(msg)}
        </div>
    `;
}

// ==================== History Management ====================
function loadHistory() {
    const stored = localStorage.getItem(CONFIG.HISTORY_KEY);
    if (stored) {
        state.history = JSON.parse(stored);
        renderHistoryList();
    }
}

function addToHistory(item) {
    // Add to top, max 50 items
    state.history.unshift(item);
    if (state.history.length > 50) state.history.pop();

    localStorage.setItem(CONFIG.HISTORY_KEY, JSON.stringify(state.history));
    renderHistoryList();
}

function renderHistoryList() {
    if (state.history.length === 0) {
        els.historyList.innerHTML = '<div class="empty-state">No history yet</div>';
        return;
    }

    els.historyList.innerHTML = state.history.map((item, index) => `
        <div class="history-item" onclick="replayHistory(${index})">
            <div class="history-time">${new Date(item.timestamp * 1000).toLocaleTimeString()}</div>
            <div class="history-preview">${escapeHtml(item.combined_text || "No Text")}</div>
        </div>
    `).join('');
}

window.replayHistory = (index) => {
    const item = state.history[index];
    if (item) {
        // Disable auto capture if viewing history
        if (state.isAutoCapture) {
            els.autoToggle.checked = false;
            toggleAutoCapture(false);
        }

        renderComplete(item);
    }
};

function clearHistory() {
    if (confirm("Clear all session history?")) {
        state.history = [];
        localStorage.removeItem(CONFIG.HISTORY_KEY);
        renderHistoryList();
    }
}

function downloadReport() {
    if (state.history.length === 0) return alert("No history to export");

    const report = {
        session_date: new Date().toISOString(),
        total_items: state.history.length,
        items: state.history
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `classsight-report-${Date.now()}.json`;
    a.click();
}

// ==================== Utilities ====================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatExplanation(text) {
    return text.split('\n')
        .filter(line => line.trim())
        .map(line => `<p>${escapeHtml(line)}</p>`)
        .join('');
}

// ==================== Event Listeners ====================
function setupEventListeners() {
    // Manual Capture
    els.analyzeBtn.addEventListener('click', captureFrame);

    // Mock Mode
    if (els.mockModeBtn) {
        els.mockModeBtn.addEventListener('click', triggerMockAnalysis);
    }

    // Auto Capture Toggle
    els.autoToggle.addEventListener('change', (e) => {
        toggleAutoCapture(e.target.checked);
    });

    // Interval Change
    els.intervalSelect.addEventListener('change', (e) => {
        state.captureInterval = parseInt(e.target.value);
        if (state.isAutoCapture) {
            // Restart with new interval
            toggleAutoCapture(true);
        }
    });

    // History Controls
    els.clearHistoryBtn.addEventListener('click', clearHistory);
    els.downloadBtn.addEventListener('click', downloadReport);

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return; // Ignore if typing

        switch (e.key.toLowerCase()) {
            case ' ':
            case 'enter':
                e.preventDefault();
                captureFrame();
                break;
            case 'a':
                els.autoToggle.checked = !els.autoToggle.checked;
                toggleAutoCapture(els.autoToggle.checked);
                break;
            // 'h' could toggle sidebar visibility in future
        }
    });
}

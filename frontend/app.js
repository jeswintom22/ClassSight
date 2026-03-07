// ClassSight Frontend Logic — Phase 6 (UI/UX Overhaul)
// Features: WebSocket, Auto-Capture, History, Toasts, Ripple, Sidebar Toggle, Smart AI Formatting

// ==================== Configuration ====================
const getWsUrl = () => {
    if (window.location.protocol === 'file:') return 'ws://localhost:8000/api/ws/stream';
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${window.location.host}/api/ws/stream`;
};

const CONFIG = {
    WS_URL: getWsUrl(),
    DEFAULT_INTERVAL: 5000,
    HISTORY_KEY: 'classsight_history_v2',
    MAX_HISTORY: 50
};

// ==================== State ====================
const state = {
    isProcessing: false,
    isAutoCapture: false,
    captureInterval: CONFIG.DEFAULT_INTERVAL,
    intervalId: null,
    ws: null,
    history: [],
    isConnected: false,
    captureCount: 0,
    sessionStart: Date.now(),
    sidebarOpen: true
};

// ==================== DOM Elements ====================
const els = {
    video:           document.getElementById('video-feed'),
    canvas:          document.getElementById('capture-canvas'),
    ocrContent:      document.getElementById('ocr-content'),
    aiContent:       document.getElementById('ai-content'),
    analyzeBtn:      document.getElementById('analyze-btn'),
    autoToggle:      document.getElementById('auto-capture-toggle'),
    intervalSelect:  document.getElementById('capture-interval'),
    statusBadge:     document.getElementById('status-badge'),
    statusText:      document.getElementById('status-text'),
    statusDot:       document.querySelector('#status-badge .status-dot'),
    historyList:     document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),
    downloadBtn:     document.getElementById('download-report-btn'),
    mockModeBtn:     document.getElementById('mock-mode-btn'),
    liveIndicator:   document.getElementById('live-indicator'),
    scanLine:        document.getElementById('scan-line'),
    confidenceBadge: document.getElementById('confidence-badge'),
    aiModelBadge:    document.getElementById('ai-model-badge'),
    toastContainer:  document.getElementById('toast-container'),
    captureFlash:    document.getElementById('capture-flash'),
    captureCount:    document.getElementById('capture-count'),
    sidebar:         document.getElementById('sidebar'),
    sidebarToggle:   document.getElementById('sidebar-toggle'),
    videoPH:         document.getElementById('video-placeholder'),
    footerWS:        document.getElementById('footer-ws-status'),
    footerWSDot:     document.querySelector('#footer-ws-status .status-dot-sm'),
    footerSession:   document.getElementById('footer-session-time')
};

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', async () => {
    console.log('ClassSight Phase 6 Initializing 🚀');

    loadHistory();
    await initCamera();
    connectWebSocket();
    setupEventListeners();
    updateStatus('Ready', 'ready');
    startSessionTimer();
});

// ==================== Session Timer ====================
function startSessionTimer() {
    setInterval(() => {
        const mins = Math.floor((Date.now() - state.sessionStart) / 60000);
        if (els.footerSession) els.footerSession.textContent = `Session: ${mins}m`;
    }, 10000);
}

// ==================== WebSocket ====================
function connectWebSocket() {
    updateStatus('Connecting…', 'connecting');

    state.ws = new WebSocket(CONFIG.WS_URL);

    state.ws.onopen = () => {
        console.log('WS Connected ✅');
        state.isConnected = true;
        updateStatus('Live', 'live');
        els.analyzeBtn.disabled = false;
        showToast('Connected to server', 'success');
    };

    state.ws.onmessage = (event) => {
        handleWSMessage(JSON.parse(event.data));
    };

    state.ws.onclose = () => {
        console.log('WS Disconnected ❌');
        state.isConnected = false;
        updateStatus('Disconnected', 'error');
        els.analyzeBtn.disabled = true;
        setTimeout(connectWebSocket, 3000);
    };

    state.ws.onerror = (err) => console.error('WS Error:', err);
}

function handleWSMessage(msg) {
    if (msg.type === 'ocr_result') {
        renderOCR(msg.data);
    } else if (msg.type === 'ai_result') {
        renderAI(msg.data);
    } else if (msg.type === 'complete') {
        state.isProcessing = false;
        addToHistory(msg.data);
        renderComplete(msg.data);
        if (!state.isAutoCapture) setLoadingState(false);
        showToast('Analysis complete', 'success');
    } else if (msg.type === 'error') {
        showError(msg.message);
        state.isProcessing = false;
        setLoadingState(false);
        showToast(msg.message || 'Analysis failed', 'error');
    } else if (msg.type === 'result' && msg.source === 'cache') {
        state.isProcessing = false;
        renderComplete(msg.data);
        setLoadingState(false);
        showToast('Loaded from cache', 'info');
    }
}

// ==================== Mock Mode ====================
function triggerMockAnalysis() {
    console.log('Triggering Mock Analysis 🧪');
    flashCapture();
    setLoadingState(true);
    state.isProcessing = true;
    showToast('Running test analysis…', 'info');

    setTimeout(() => {
        handleWSMessage({
            type: 'ocr_result',
            data: { combined_text: 'E = mc²\nTheory of Relativity\n\n∫ f(x) dx = F(b) − F(a)', confidence: 0.99 }
        });

        setTimeout(() => {
            handleWSMessage({
                type: 'complete',
                data: {
                    combined_text: 'E = mc²\nTheory of Relativity\n\n∫ f(x) dx = F(b) − F(a)',
                    confidence: 0.99,
                    explanation: `**Mass-Energy Equivalence** is one of the most famous equations in physics.\n\nIn E = mc², E stands for energy, m for mass, and c is the speed of light (~3×10⁸ m/s).\n\nThis tells us that mass and energy are interchangeable — a tiny amount of mass can release an enormous amount of energy, which is the basis of nuclear reactions and atomic bombs.\n\nThe integral below it is the **Fundamental Theorem of Calculus**, connecting differentiation and integration.`,
                    ai_model: 'Mock Gemini Flash',
                    timestamp: Date.now() / 1000
                }
            });
            state.isProcessing = false;
        }, 1500);
    }, 800);
}

// ==================== Camera ====================
async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'environment' }
        });
        els.video.srcObject = stream;
        els.video.addEventListener('loadeddata', () => {
            if (els.videoPH) els.videoPH.classList.add('hidden');
        });
    } catch (err) {
        console.error('Camera Error:', err);
        showToast('Camera access denied', 'error');
    }
}

async function captureFrame() {
    if (!state.isConnected || state.isProcessing) return;
    if (!state.isAutoCapture) setLoadingState(true);

    // Flash & counter
    flashCapture();
    state.captureCount++;
    if (els.captureCount) els.captureCount.textContent = state.captureCount;

    state.isProcessing = true;

    try {
        els.canvas.width  = els.video.videoWidth;
        els.canvas.height = els.video.videoHeight;
        els.canvas.getContext('2d').drawImage(els.video, 0, 0);

        els.canvas.toBlob((blob) => {
            if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                state.ws.send(blob);
            } else {
                state.isProcessing = false;
                setLoadingState(false);
                showToast('Not connected — retrying…', 'warning');
            }
        }, 'image/jpeg', 0.8);
    } catch (err) {
        console.error('Capture Error:', err);
        state.isProcessing = false;
        setLoadingState(false);
    }
}

// ==================== Auto-Capture ====================
function toggleAutoCapture(enabled) {
    state.isAutoCapture = enabled;

    if (enabled) {
        if (state.intervalId) clearInterval(state.intervalId);
        captureFrame();
        state.intervalId = setInterval(captureFrame, state.captureInterval);

        if (els.liveIndicator) els.liveIndicator.style.display = 'flex';
        if (els.scanLine)       els.scanLine.style.display = 'block';
        els.analyzeBtn.disabled = true;
        els.analyzeBtn.innerHTML = `
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
            <span>Auto Mode</span>`;
        showToast(`Auto-capture every ${state.captureInterval / 1000}s`, 'info');
    } else {
        if (state.intervalId) clearInterval(state.intervalId);
        state.intervalId = null;

        if (els.liveIndicator) els.liveIndicator.style.display = 'none';
        if (els.scanLine)       els.scanLine.style.display = 'none';
        els.analyzeBtn.disabled = false;
        els.analyzeBtn.innerHTML = `
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <span>Capture</span>
            <kbd class="shortcut-hint">Space</kbd>`;
    }
}

// ==================== UI Rendering ====================
function renderOCR(data) {
    if (data.combined_text) {
        els.ocrContent.innerHTML = `<div class="ocr-text">${escapeHtml(data.combined_text)}</div>`;
        const conf   = Math.round(data.confidence * 100);
        const badge  = els.confidenceBadge;
        badge.style.display = 'inline-block';
        badge.textContent   = `${conf}%`;
        badge.className     = 'confidence-badge' + (conf >= 85 ? '' : conf >= 60 ? ' warn' : ' low');
    } else {
        els.ocrContent.innerHTML = `<div class="placeholder-text"><p>No text visible</p></div>`;
        els.confidenceBadge.style.display = 'none';
    }
}

function renderAI(data) {
    if (data.explanation) {
        els.aiContent.innerHTML = `<div class="ai-explanation">${formatExplanation(data.explanation)}</div>`;
        if (data.ai_model) els.aiModelBadge.textContent = data.ai_model;
    }
}

function renderComplete(data) {
    renderOCR(data);
    renderAI(data);
}

function setLoadingState(loading) {
    els.analyzeBtn.disabled = loading;
    els.analyzeBtn.innerHTML = loading
        ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg><span>Analyzing…</span>`
        : `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span>Capture</span><kbd class="shortcut-hint">Space</kbd>`;

    if (loading) {
        els.aiContent.innerHTML = `
            <div class="ai-loading">
                <div class="skeleton-text"></div>
                <div class="skeleton-text medium"></div>
                <div class="skeleton-text"></div>
                <div class="skeleton-text short"></div>
                <div class="skeleton-text medium"></div>
            </div>`;
    }
}

// Inject spin keyframe dynamically (lightweight)
const spinStyle = document.createElement('style');
spinStyle.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
document.head.appendChild(spinStyle);

function updateStatus(text, type) {
    els.statusText.textContent = text;
    const dot = els.statusDot;
    dot.className = 'status-dot';
    if (type === 'live')       { dot.classList.add('is-live');       }
    else if (type === 'connecting') { dot.classList.add('is-connecting'); }
    else if (type === 'error') { dot.classList.add('is-error');      }

    // Mirror to footer
    if (els.footerWSDot) {
        els.footerWSDot.className = 'status-dot-sm';
        if (type === 'live')       els.footerWSDot.classList.add('is-live');
        else if (type === 'error') els.footerWSDot.classList.add('is-error');
        else if (type === 'connecting') els.footerWSDot.classList.add('is-connecting');
    }
}

function showError(msg) {
    els.aiContent.innerHTML = `
        <div class="placeholder-text" style="color:#ef4444;opacity:1;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
            <p style="color:#ef4444;">${escapeHtml(msg)}</p>
        </div>`;
}

// ==================== Toast Notifications ====================
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-icon"></span><span>${escapeHtml(message)}</span>`;
    els.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('dismiss');
        setTimeout(() => toast.remove(), 350);
    }, duration);
}

// ==================== Capture Flash ====================
function flashCapture() {
    const el = els.captureFlash;
    el.classList.remove('flash');
    void el.offsetWidth; // reflow
    el.classList.add('flash');
}

// ==================== Ripple on Buttons ====================
function addRipple(btn) {
    btn.addEventListener('click', function (e) {
        const rect  = this.getBoundingClientRect();
        const size  = Math.max(rect.width, rect.height);
        const x     = e.clientX - rect.left - size / 2;
        const y     = e.clientY - rect.top  - size / 2;
        const ripple = document.createElement('span');
        ripple.className = 'ripple';
        ripple.style.cssText = `width:${size}px;height:${size}px;left:${x}px;top:${y}px;`;
        this.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    });
}

// ==================== History ====================
function loadHistory() {
    const stored = localStorage.getItem(CONFIG.HISTORY_KEY);
    if (stored) {
        state.history = JSON.parse(stored);
        renderHistoryList();
    }
}

function addToHistory(item) {
    state.history.unshift(item);
    if (state.history.length > CONFIG.MAX_HISTORY) state.history.pop();
    localStorage.setItem(CONFIG.HISTORY_KEY, JSON.stringify(state.history));
    renderHistoryList();
}

function renderHistoryList() {
    if (!state.history.length) {
        els.historyList.innerHTML = `
            <div class="empty-state">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                <p>No captures yet</p>
                <small>Press <kbd>Space</kbd> to start</small>
            </div>`;
        return;
    }

    els.historyList.innerHTML = state.history.map((item, i) => `
        <div class="history-item" onclick="replayHistory(${i})">
            <div class="history-time">${new Date(item.timestamp * 1000).toLocaleTimeString()}</div>
            <div class="history-preview">${escapeHtml(item.combined_text || 'No Text')}</div>
        </div>`).join('');
}

window.replayHistory = (index) => {
    const item = state.history[index];
    if (!item) return;
    if (state.isAutoCapture) {
        els.autoToggle.checked = false;
        toggleAutoCapture(false);
    }
    renderComplete(item);
    showToast('Loaded from history', 'info');
};

function clearHistory() {
    if (!confirm('Clear all session history?')) return;
    state.history = [];
    localStorage.removeItem(CONFIG.HISTORY_KEY);
    renderHistoryList();
    showToast('History cleared', 'info');
}

function downloadReport() {
    if (!state.history.length) {
        showToast('No history to export', 'warning');
        return;
    }
    const blob = new Blob([JSON.stringify({
        session_date: new Date().toISOString(),
        total_items: state.history.length,
        items: state.history
    }, null, 2)], { type: 'application/json' });
    const a = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(blob),
        download: `classsight-report-${Date.now()}.json`
    });
    a.click();
    showToast('Report downloaded', 'success');
}

// ==================== Sidebar Toggle ====================
function toggleSidebar() {
    state.sidebarOpen = !state.sidebarOpen;
    els.sidebar.classList.toggle('collapsed', !state.sidebarOpen);
}

// ==================== Utilities ====================
function escapeHtml(text) {
    if (typeof text !== 'string') return '';
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
}

/**
 * Format AI explanation text:
 * - **bold** → <strong>
 * - math expressions (E = ..., ∫, Δ, etc.) → .math-expr span
 * - Numbered/bulleted lines
 * - Paragraphs from blank lines
 */
function formatExplanation(text) {
    return text
        .split('\n')
        .filter(l => l.trim())
        .map(line => {
            // Escape first
            let out = escapeHtml(line);
            // Bold **text**
            out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            // Math-like inline (simple heuristic: contains =,∫,∑,Δ,±,², ³, etc.)
            out = out.replace(/([^ ]*[=∫∑∏Δ±⁰¹²³⁴⁵⁶⁷⁸⁹][^ ]*)/g, (m) => {
                // Only wrap if it looks sufficiently mathy (has operator-like chars)
                return `<span class="math-expr">${m}</span>`;
            });
            return `<p>${out}</p>`;
        })
        .join('');
}

// ==================== Event Listeners ====================
function setupEventListeners() {
    els.analyzeBtn.addEventListener('click', captureFrame);
    addRipple(els.analyzeBtn);

    if (els.mockModeBtn) {
        els.mockModeBtn.addEventListener('click', triggerMockAnalysis);
        addRipple(els.mockModeBtn);
    }

    els.autoToggle.addEventListener('change', e => toggleAutoCapture(e.target.checked));

    els.intervalSelect.addEventListener('change', e => {
        state.captureInterval = parseInt(e.target.value);
        if (state.isAutoCapture) toggleAutoCapture(true);
    });

    els.clearHistoryBtn.addEventListener('click', clearHistory);
    els.downloadBtn.addEventListener('click', downloadReport);
    addRipple(els.downloadBtn);

    if (els.sidebarToggle) {
        els.sidebarToggle.addEventListener('click', toggleSidebar);
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
        switch (e.key) {
            case ' ':
            case 'Enter':
                e.preventDefault();
                captureFrame();
                break;
            case 'a':
            case 'A':
                els.autoToggle.checked = !els.autoToggle.checked;
                toggleAutoCapture(els.autoToggle.checked);
                break;
            case 'h':
            case 'H':
                toggleSidebar();
                break;
        }
    });
}

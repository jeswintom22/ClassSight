# ClassSight 👁️

**AI-Powered Classroom Assistant** | Real-time OCR & Educational Analysis

ClassSight is an intelligent classroom tool designed to help students understand board content in real-time. It uses high-performance OCR and AI to extract text from video feeds and provide instant pedagogical explanations.

## 🚀 Key Features

- **Real-time Video Analysis**: Low-latency WebSocket-based frame processing.
- **Smart Caching**: TTL-based caching for OCR and AI results (instant repeat lookups).
- **Auto-Capture Mode**: Configurable hands-free analysis (3s, 5s, 10s intervals).
- **Glassmorphism UI**: Modern, responsive dashboard with smooth animations.
- **Session History**: Persistent history with JSON export functionality.
- **Mock Mode**: Built-in testing tool for UI/UX verification without backend dependencies.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python), EasyOCR, Google Gemini 1.5 Flash.
- **Performance**: Async/Await architecture, Threadpooling, TTLCache.
- **Real-time**: WebSockets (Starlette).
- **Frontend**: Vanilla HTML/CSS/JS (Zero dependencies, optimized for glassmorphism).

## 🚀 Quick Start

### 1. Setup Environment
```powershell
# Create & Activate Virtual Environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the root:
```env
GEMINI_API_KEY=your_actual_gemini_key_here
OCR_GPU=False
CACHE_ENABLED=True
AUTO_CAPTURE_INTERVAL=5
```

### 3. Run the Server
```powershell
cd backend
uvicorn main:app --reload
```

### 4. Open ClassSight
Visit: [http://localhost:8000](http://localhost:8000)

## 📄 Documentation
- [Enhancement Walkthrough](walkthrough.md) - Detailed phase update notes.
- [Commit History](COMMIT_MESSAGE.txt) - Summary of latest changes.
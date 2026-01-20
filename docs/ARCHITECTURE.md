# ClassSight Architecture Guide

## 🎯 What We're Building

ClassSight captures what a teacher writes/shows on video, reads it using OCR, and explains it using AI—all in real-time for students.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLASSSIGHT MVP                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Video Source  │      │   FastAPI Server │      │  Web Frontend   │
│                 │      │                  │      │                 │
│ (Mock frames    │─────▶│  - Frame capture │◀─────│ - View stream   │
│  for MVP)       │      │  - OCR service   │      │ - See OCR text  │
│                 │      │  - AI service    │      │ - See AI reply  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  │
                         ┌────────┴────────┐
                         │                 │
                    ┌────▼────┐      ┌─────▼──────┐
                    │ EasyOCR │      │ Claude API │
                    │         │      │            │
                    │ Extracts│      │ Explains   │
                    │   text  │      │  content   │
                    └─────────┘      └────────────┘
```

---

## 📦 Component Breakdown

### 1. **Video Source** (Mock for MVP)
- **What**: Provides frames to analyze
- **MVP version**: Pre-saved images or simple webcam snapshots
- **Why mock first**: Real WebRTC is complex; we validate the pipeline first
- **File**: `mock_video.py`

### 2. **FastAPI Server** (Backend Brain)
- **What**: Orchestrates everything
- **Responsibilities**:
  - Accept video frames (as images)
  - Trigger OCR every N seconds
  - Send OCR results to Claude
  - Return results to frontend
- **Files**: `main.py`, `routes/`, `services/`

### 3. **OCR Service** (EasyOCR)
- **What**: Converts images → text
- **Input**: Image frame (PNG/JPG)
- **Output**: Detected text strings
- **Why EasyOCR**: Works offline, good for handwriting/formulas
- **File**: `services/ocr_service.py`

### 4. **AI Service** (Claude)
- **What**: Explains/solves OCR text
- **Input**: Detected text ("x² + 5x + 6")
- **Output**: Explanation ("This is a quadratic equation...")
- **File**: `services/ai_service.py`

### 5. **Web Frontend** (Simple HTML/JS)
- **What**: Student view
- **Shows**:
  - Current frame
  - OCR text
  - AI explanation
- **Files**: `static/index.html`, `static/app.js`

---

## 🔄 Data Flow (Simplified)

```
1. Teacher speaks/writes
         ↓
2. System captures frame every 3 seconds
         ↓
3. EasyOCR reads frame → "E = mc²"
         ↓
4. Server sends to Claude → "Explain: E = mc²"
         ↓
5. Claude responds → "Einstein's mass-energy equivalence..."
         ↓
6. Frontend displays both text AND explanation
```

---

## 📁 Project Structure Blueprint

```
ClassSight/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings (API keys, paths)
│   ├── routes/
│   │   ├── video.py            # Frame upload endpoint
│   │   └── analysis.py         # Get OCR + AI results
│   ├── services/
│   │   ├── ocr_service.py      # EasyOCR wrapper
│   │   ├── ai_service.py       # Claude API client
│   │   └── frame_processor.py  # Manages frame queue
│   └── models/
│       └── schemas.py          # Data models (Pydantic)
│
├── frontend/
│   ├── index.html              # Main student UI
│   ├── style.css               # Minimal styling
│   └── app.js                  # Fetch OCR/AI results
│
├── mock_data/
│   └── sample_frames/          # Test images (math, text)
│
├── requirements.txt            # Python dependencies
└── README.md                   # Setup instructions
```

---

## 🛠️ Technology Justification

| Component      | Choice       | Why?                                      |
|----------------|--------------|-------------------------------------------|
| **Backend**    | FastAPI      | Fast, async, auto API docs, modern        |
| **OCR**        | EasyOCR      | Works offline, handles formulas better    |
| **AI**         | Claude API   | Strong reasoning, good with math/code     |
| **Frontend**   | Vanilla JS   | Keep it simple, no build complexity       |
| **Database**   | SQLite       | Only if we need history (defer for MVP)   |
| **Video**      | Mock images  | Validate pipeline before WebRTC           |

---

## ⚡ MVP Scope (What We Will NOT Do Yet)

❌ Real-time WebRTC streaming  
❌ Multiple classrooms  
❌ Student accounts  
❌ Chat features  
❌ Recording/replay  
❌ Mobile apps  

✅ Single teacher mock stream  
✅ Periodic OCR (every 3 sec)  
✅ AI explanation  
✅ Simple web view  

---

## 🎓 Learning Path

1. **First**: Understand architecture (this document)
2. **Second**: Set up Python + dependencies
3. **Third**: Build FastAPI skeleton (hello world)
4. **Fourth**: Add OCR to one static image
5. **Fifth**: Add Claude explanation
6. **Sixth**: Create simple frontend
7. **Seventh**: Connect everything

---

## 🚨 Common Beginner Pitfalls

| Mistake                          | Why It Happens                    | How to Avoid              |
|----------------------------------|-----------------------------------|---------------------------|
| Starting with real video         | Seems like the "real" solution    | Use mock images first     |
| Over-engineering early           | Want production-ready code        | Build MVP, then iterate   |
| Skipping error handling          | Happy path works                  | Add try/except from day 1 |
| Hardcoding API keys              | Quick testing                     | Use .env files always     |
| Not testing components in isolation | Want to see full system | Test OCR alone, AI alone |

---

## 📝 Development Phases

### Phase 1: Foundation ✅
- Architecture design
- Technology stack selection

### Phase 2: Environment Setup ✅
- Python virtual environment
- Dependency installation
- FastAPI skeleton

### Phase 3: OCR Integration (Current)
- EasyOCR setup
- Image processing
- Text extraction

### Phase 4: AI Service
- Claude API integration
- Prompt engineering
- Response formatting

### Phase 5: Frontend
- Simple web interface
- Display OCR results
- Show AI explanations

### Phase 6: Integration
- Connect all components
- End-to-end testing
- MVP demonstration

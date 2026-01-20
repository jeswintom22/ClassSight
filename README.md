# ClassSight

AI-powered online classroom platform for large audiences.

## Project Status
🚧 **In Development** - Setting up MVP

## Quick Start

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure API Keys
Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_actual_key_here
```

### 4. Run the Server
```powershell
cd backend
python main.py
```

Visit: http://localhost:8000

## Architecture
See `architecture_guide.md` in the brain folder for detailed system design.

## Development
- Backend: FastAPI (Python)
- OCR: EasyOCR
- AI: Claude API
- Frontend: Vanilla HTML/CSS/JS
# Sample Test Images for OCR

This folder contains test images used to validate the OCR service.

## Images

### 1. math_equation.png
**Content**: `x² + 5x + 6 = 0`
**Purpose**: Test OCR on mathematical equations with superscripts

### 2. physics_formula.png
**Content**: `E = mc²` and `Energy-Mass Equivalence`
**Purpose**: Test OCR on scientific formulas and text combination

### 3. biology_notes.png
**Content**: `Photosynthesis: Plants convert sunlight into energy using chlorophyll`
**Purpose**: Test OCR on longer text sentences with scientific terminology

## Usage

These images are used by:
- `backend/test_ocr.py` - Standalone OCR testing script
- API testing via `/api/ocr/analyze` endpoint
- Manual verification of OCR accuracy

## Expected OCR Results

| Image | Expected Text Detection | Minimum Confidence |
|-------|------------------------|-------------------|
| math_equation.png | Should detect the equation | > 80% |
| physics_formula.png | Should detect formula and label | > 80% |
| biology_notes.png | Should detect full sentence | > 75% |

Note: Actual OCR results may vary based on image quality and EasyOCR model performance.

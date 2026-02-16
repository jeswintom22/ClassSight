"""
WebSocket Routes for Real-time Streaming

Handles real-time communication for auto-capture and live analysis.
Allows the frontend to stream frames and receive results asynchronously.

Routes:
- WS /ws/stream - WebSocket endpoint for frame streaming

Author: ClassSight Team
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.cache_service import CacheService
from config import settings
from starlette.concurrency import run_in_threadpool
import json
import asyncio
import time
from typing import List

router = APIRouter()

# Initialize services
ocr_service = OCRService.get_instance()
ai_service = AIService.get_instance()
cache_service = CacheService.get_instance()

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time frame streaming.
    
    Protocol:
    1. Client connects
    2. Client sends image data (blob/bytes)
    3. Server processes and sends updates:
       - {"type": "status", "status": "processing"}
       - {"type": "ocr_result", "data": ...}
       - {"type": "ai_result", "data": ...}
       - {"type": "error", "message": ...}
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive image bytes
            data = await websocket.receive_bytes()
            print(f"📡 WS Received frame: {len(data)} bytes")
            
            start_time = time.time()
            
            # Send processing status
            await manager.send_json({"type": "status", "status": "processing"}, websocket)
            
            try:
                # 1. Check Cache first
                image_hash = cache_service.get_image_hash(data)
                cached_result = cache_service.get_ocr_result(image_hash)
                
                if cached_result:
                    print(f"⚡ Cache Hit! Hash: {image_hash[:8]}...")
                    # Send cached result immediately
                    await manager.send_json({
                        "type": "result", 
                        "data": cached_result,
                        "source": "cache"
                    }, websocket)
                    continue
                
                print(f"💨 Cache Miss. Processing OCR...")

                # 2. Process OCR (in threadpool)
                ocr_result = await run_in_threadpool(ocr_service.extract_text_from_bytes, data)
                print(f"📝 OCR Result: {ocr_result['combined_text'][:50]}... (Conf: {ocr_result['confidence']})")
                
                # 3. Send OCR Result immediately (Progressive loading)
                await manager.send_json({
                    "type": "ocr_result",
                    "data": {
                        "combined_text": ocr_result["combined_text"],
                        "confidence": ocr_result["confidence"],
                        "blocks": [block for block in ocr_result["blocks"]] # serializable
                    }
                }, websocket)
                
                # 4. Process AI (if text found)
                explanation = None
                ai_model = None
                
                if ocr_result["combined_text"] and ocr_result["combined_text"].strip():
                    print("🤖 Starting AI Analysis...")
                    ai_response = await ai_service.explain_text(ocr_result["combined_text"])
                    if ai_response["success"]:
                        explanation = ai_response["explanation"]
                        ai_model = ai_response["model"]
                        print("✅ AI Analysis Complete")
                        
                        # Send AI update
                        await manager.send_json({
                            "type": "ai_result",
                            "data": {
                                "explanation": explanation,
                                "ai_model": ai_model
                            }
                        }, websocket)
                    else:
                        print(f"❌ AI Failed: {ai_response.get('error')}")
                else:
                    print("⚠️ No text for AI to analyze")
                
                # 5. Cache the full result for future
                full_result = {
                    "success": True,
                    "combined_text": ocr_result["combined_text"],
                    "confidence": ocr_result["confidence"],
                    "blocks": ocr_result["blocks"],
                    "explanation": explanation,
                    "ai_model": ai_model,
                    "processing_time": round(time.time() - start_time, 3),
                    "timestamp": str(time.time())
                }
                cache_service.set_ocr_result(image_hash, full_result)
                
                # Send final complete message
                await manager.send_json({
                    "type": "complete",
                    "data": full_result
                }, websocket)
                
            except Exception as e:
                print(f"WS Error: {e}")
                await manager.send_json({
                    "type": "error",
                    "message": str(e)
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WS Client disconnected")
    except Exception as e:
        print(f"WS Connection Error: {e}")
        # manager.disconnect(websocket) # Already disconnected usually

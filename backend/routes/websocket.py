"""
WebSocket Routes for Real-time Streaming

Handles real-time communication for auto-capture and live analysis.
Allows the frontend to stream frames and receive results asynchronously.

Routes:
- WS /ws/stream - WebSocket endpoint for frame streaming

Security (mirrors the HTTP /api/ocr/analyze controls):
- Origin check on connect (same-origin or CORS_ORIGINS), optional WS_AUTH_TOKEN
- Per-IP concurrent connection cap
- Per-connection minimum frame interval and per-IP frames-per-minute limit
- Frame size cap (MAX_UPLOAD_SIZE) and image magic-number validation
- OCR text sanitized (MAX_TEXT_LENGTH) before the AI call

Author: ClassSight Team
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.cache_service import CacheService
from config import settings
from utils.validators import InputValidator
from starlette.concurrency import run_in_threadpool
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional
from urllib.parse import urlsplit
import hmac
import time

router = APIRouter()

# Initialize services
ocr_service = OCRService.get_instance()
ai_service = AIService.get_instance()
cache_service = CacheService.get_instance()

validator = InputValidator()

# WebSocket close codes (RFC 6455)
WS_POLICY_VIOLATION = 1008
WS_MESSAGE_TOO_BIG = 1009
WS_TRY_AGAIN_LATER = 1013


def get_client_ip(websocket: WebSocket) -> str:
    """Client IP as seen by the server (uvicorn applies trusted proxy headers)."""
    return websocket.client.host if websocket.client else "unknown"


def is_origin_allowed(websocket: WebSocket) -> bool:
    """
    Browsers do not apply CORS to WebSockets, so check Origin explicitly.
    Allows same-origin requests and origins configured for CORS.
    Non-browser clients (no Origin header) are allowed; use WS_AUTH_TOKEN to lock those down.
    """
    origin = websocket.headers.get("origin")
    if origin is None:
        return True
    allowed = settings.get_cors_origins()
    if "*" in allowed:
        return True
    if origin.rstrip("/") in [o.strip().rstrip("/") for o in allowed]:
        return True
    host = websocket.headers.get("host")
    return bool(host) and urlsplit(origin).netloc.lower() == host.lower()


def is_token_valid(websocket: WebSocket) -> bool:
    """Require ?token=<WS_AUTH_TOKEN> when a token is configured."""
    expected = settings.WS_AUTH_TOKEN
    if not expected:
        return True
    provided = websocket.query_params.get("token", "")
    return hmac.compare_digest(provided.encode(), expected.encode())


class FrameRateLimiter:
    """In-memory per-IP sliding-window limiter for WebSocket frames."""

    def __init__(self, max_per_minute: int, window_seconds: float = 60.0):
        self.max_per_minute = max_per_minute
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: Optional[float] = None) -> bool:
        now = time.monotonic() if now is None else now
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_per_minute:
            return False
        hits.append(now)
        return True

    def reset(self):
        self._hits.clear()


class ConnectionManager:
    """Manages active WebSocket connections and per-IP connection caps."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connections_per_ip: Dict[str, int] = defaultdict(int)

    def can_connect(self, client_ip: str) -> bool:
        return self.connections_per_ip[client_ip] < settings.WS_MAX_CONNECTIONS_PER_IP

    async def connect(self, websocket: WebSocket, client_ip: str):
        self.connections_per_ip[client_ip] += 1
        self.active_connections.append(websocket)
        await websocket.accept()

    def disconnect(self, websocket: WebSocket, client_ip: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connections_per_ip[client_ip] -= 1
            if self.connections_per_ip[client_ip] <= 0:
                del self.connections_per_ip[client_ip]

    async def send_json(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

manager = ConnectionManager()
frame_limiter = FrameRateLimiter(settings.WS_MAX_FRAMES_PER_MINUTE)

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time frame streaming.
    
    Protocol:
    1. Client connects (optionally with ?token=<WS_AUTH_TOKEN>)
    2. Client sends image data (blob/bytes)
    3. Server processes and sends updates:
       - {"type": "status", "status": "processing"}
       - {"type": "ocr_result", "data": ...}
       - {"type": "ai_result", "data": ...}
       - {"type": "error", "message": ...}
    """
    client_ip = get_client_ip(websocket)

    if not is_origin_allowed(websocket) or not is_token_valid(websocket):
        print(f"🚫 WS rejected (origin/token) from {client_ip}")
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    if not manager.can_connect(client_ip):
        print(f"🚫 WS rejected (too many connections) from {client_ip}")
        await websocket.close(code=WS_TRY_AGAIN_LATER)
        return

    await manager.connect(websocket, client_ip)
    last_frame_at = 0.0
    
    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect(message.get("code", 1000))
            data = message.get("bytes")
            if data is None:
                await manager.send_json({"type": "error", "message": "Expected binary image frame"}, websocket)
                continue

            if len(data) > settings.MAX_UPLOAD_SIZE:
                await websocket.close(code=WS_MESSAGE_TOO_BIG)
                break

            print(f"📡 WS Received frame: {len(data)} bytes")

            now = time.monotonic()
            if now - last_frame_at < settings.WS_MIN_FRAME_INTERVAL or not frame_limiter.allow(client_ip, now):
                await manager.send_json({
                    "type": "error",
                    "message": "Rate limit exceeded. Please slow down."
                }, websocket)
                continue
            last_frame_at = now

            try:
                validator.validate_file_content(data, max_size=settings.MAX_UPLOAD_SIZE)
            except HTTPException as e:
                await manager.send_json({"type": "error", "message": e.detail}, websocket)
                continue
            
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
                ai_provider = None
                
                sanitized_text = ""
                if ocr_result["combined_text"] and ocr_result["combined_text"].strip():
                    try:
                        sanitized_text = validator.sanitize_text(
                            ocr_result["combined_text"],
                            max_length=settings.MAX_TEXT_LENGTH,
                            strip_html=True
                        )
                    except HTTPException as e:
                        print(f"⚠️ Skipping AI: {e.detail}")

                if sanitized_text:
                    print("🤖 Starting AI Analysis...")
                    ai_response = await ai_service.explain_text(sanitized_text)
                    if ai_response["success"]:
                        explanation = ai_response["explanation"]
                        ai_model = ai_response["model"]
                        ai_provider = ai_response.get("ai_provider")
                        print("✅ AI Analysis Complete")
                        
                        # Send AI update
                        await manager.send_json({
                            "type": "ai_result",
                            "data": {
                                "explanation": explanation,
                                "ai_model": ai_model,
                                "ai_provider": ai_provider
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
                    "ai_provider": ai_provider,
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
        print("WS Client disconnected")
    except Exception as e:
        print(f"WS Connection Error: {e}")
    finally:
        manager.disconnect(websocket, client_ip)

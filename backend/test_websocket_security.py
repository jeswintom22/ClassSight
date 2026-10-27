"""
Unit tests for WebSocket stream protections (no OCR/AI dependencies).

Usage:
    cd backend && pytest test_websocket_security.py
"""

import sys
import types
import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image


class FakeOCR:
    calls = 0

    @classmethod
    def get_instance(cls):
        return cls()

    def extract_text_from_bytes(self, data):
        FakeOCR.calls += 1
        return {"combined_text": "<b>Hello</b>   world", "confidence": 0.9, "blocks": []}


class FakeAI:
    calls = []

    @classmethod
    def get_instance(cls):
        return cls()

    async def explain_text(self, text, context="classroom"):
        FakeAI.calls.append(text)
        return {"success": True, "explanation": "ok", "model": "fake", "ai_provider": "custom"}


class FakeCache:
    @classmethod
    def get_instance(cls):
        return cls()

    def get_image_hash(self, data):
        return str(hash(data))

    def get_ocr_result(self, image_hash):
        return None

    def set_ocr_result(self, image_hash, result):
        pass


for name, cls in [("services.ocr_service", ("OCRService", FakeOCR)),
                  ("services.ai_service", ("AIService", FakeAI)),
                  ("services.cache_service", ("CacheService", FakeCache))]:
    module = types.ModuleType(name)
    setattr(module, cls[0], cls[1])
    sys.modules[name] = module

from config import settings  # noqa: E402
from routes import websocket as ws_routes  # noqa: E402
from starlette.websockets import WebSocketDisconnect  # noqa: E402


def png_bytes(color=(255, 255, 255)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "CORS_ALLOW_ALL", False)
    monkeypatch.setattr(settings, "CORS_ORIGINS", ["http://localhost:8000"])
    monkeypatch.setattr(settings, "WS_AUTH_TOKEN", "")
    monkeypatch.setattr(settings, "WS_MIN_FRAME_INTERVAL", 0.0)
    monkeypatch.setattr(settings, "WS_MAX_CONNECTIONS_PER_IP", 3)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)
    ws_routes.frame_limiter.reset()
    ws_routes.frame_limiter.max_per_minute = 30
    ws_routes.manager.active_connections.clear()
    ws_routes.manager.connections_per_ip.clear()
    FakeOCR.calls = 0
    FakeAI.calls = []
    app = FastAPI()
    app.include_router(ws_routes.router, prefix="/api/ws")
    return TestClient(app)


def drain_until_final(ws):
    while True:
        msg = ws.receive_json()
        if msg["type"] in ("complete", "error"):
            return msg


def test_valid_frame_is_processed_and_text_sanitized(client):
    with client.websocket_connect("/api/ws/stream", headers={"origin": "http://localhost:8000"}) as ws:
        ws.send_bytes(png_bytes())
        assert drain_until_final(ws)["type"] == "complete"
    assert FakeAI.calls == ["Hello world"]


def test_cross_site_origin_rejected(client):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/api/ws/stream", headers={"origin": "https://evil.example"}):
            pass
    assert exc.value.code == 1008


def test_token_required_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "WS_AUTH_TOKEN", "s3cret")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/ws/stream"):
            pass
    with client.websocket_connect("/api/ws/stream?token=s3cret") as ws:
        ws.send_bytes(png_bytes())
        assert drain_until_final(ws)["type"] == "complete"


def test_non_image_frame_rejected_before_ocr(client):
    with client.websocket_connect("/api/ws/stream") as ws:
        ws.send_bytes(b"test_image_data")
        msg = ws.receive_json()
        assert msg["type"] == "error"
    assert FakeOCR.calls == 0


def test_oversized_frame_closes_connection(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 1024)
    with client.websocket_connect("/api/ws/stream") as ws:
        ws.send_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 2048)
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 1009
    assert FakeOCR.calls == 0


def test_burst_of_100_frames_is_throttled(client):
    with client.websocket_connect("/api/ws/stream") as ws:
        for i in range(100):
            ws.send_bytes(png_bytes((i, i, i)))
            drain_until_final(ws)
    assert FakeOCR.calls == 30
    assert len(FakeAI.calls) == 30


def test_min_frame_interval_per_connection(client, monkeypatch):
    monkeypatch.setattr(settings, "WS_MIN_FRAME_INTERVAL", 60.0)
    with client.websocket_connect("/api/ws/stream") as ws:
        for i in range(5):
            ws.send_bytes(png_bytes((i, i, i)))
            drain_until_final(ws)
    assert FakeOCR.calls == 1


def test_connection_cap_per_ip(client, monkeypatch):
    monkeypatch.setattr(settings, "WS_MAX_CONNECTIONS_PER_IP", 2)
    with client.websocket_connect("/api/ws/stream"), client.websocket_connect("/api/ws/stream"):
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/api/ws/stream"):
                pass
        assert exc.value.code == 1013
    with client.websocket_connect("/api/ws/stream"):
        pass

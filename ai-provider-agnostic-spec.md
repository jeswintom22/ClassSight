# Spec: Provider-Agnostic AI Layer for ClassSight

**Status:** Implemented · **Date:** 2026-08-04 · **Author:** Buffy + ClassSight team

---

## 1. Overview & Goal

ClassSight's AI layer currently hardcodes **xAI Grok** as its only LLM provider:
`backend/services/ai_service.py` constructs an `AsyncOpenAI` client with a
hardcoded `base_url="https://api.x.ai/v1"` and reads `GROK_API_KEY` from env.
The codebase also carries leftover **Google Gemini** artifacts from an earlier
migration (`debug_ai.py`, `GEMINI_API_KEY` references in `test_ai.py`, a
"Mock Gemini Flash" badge in the frontend mock mode).

**Goal:** Make the AI service **provider-agnostic**. Any provider that exposes
an **OpenAI-compatible `/chat/completions`** endpoint (OpenAI, xAI Grok, Groq,
OpenRouter, DeepSeek, Together, Mistral, self-hosted, proxies, etc.) should be
usable by simply setting **three generic env vars** — no code changes.

> "Just want to input the API in the env and done with it."

### Primary user story

```
As a developer deploying ClassSight,
I want to configure my AI provider entirely via .env (API key, base URL, model),
so that I can switch between OpenAI, Grok, Groq, or any OpenAI-compatible
endpoint without touching any code.
```

---

## 2. Current State Analysis (as-found)

| File | Role | Provider coupling |
|---|---|---|
| `backend/services/ai_service.py` | AI wrapper (singleton) | Hardcodes `https://api.x.ai/v1`, reads `GROK_API_KEY`, labels itself "Grok" |
| `backend/config.py` | Env settings | `GROK_API_KEY`, `AI_MODEL` (default `grok-3`), `AI_MAX_TOKENS`, `AI_TEMPERATURE`; `validate()` raises if `GROK_API_KEY` missing |
| `.env.example` | Env template | `GROK_API_KEY`, `AI_MODEL=grok-3` |
| `backend/routes/analysis.py` | REST `/api/ocr/*` | Calls `ai_service.explain_text()`; passes `ai_model` through |
| `backend/routes/websocket.py` | WS `/api/ws/stream` | Same; sends `ai_model` in messages |
| `backend/models/schemas.py` | Pydantic models | `ai_model: Optional[str]` field |
| `backend/services/cache_service.py` | TTL cache | AI cache keyed by **text-hash only** |
| `backend/debug_ai.py` | Scratch script | Uses `GEMINI_API_KEY` + `google.generativeai` (obsolete) |
| `backend/test_ai.py` | Manual AI test | Messages reference `GEMINI_API_KEY` |
| `frontend/app.js` | UI | Renders `ai_model` badge; mock mode badge says "Mock Gemini Flash" |
| `requirements.txt` | Deps | `openai>=1.30.0` already present (covers all OpenAI-compatible providers) |
| `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `README.md` | Docs | Refer to Grok/Gemini config |

**Notable:** the OpenAI SDK is already a dependency — every target provider
in scope speaks its protocol, so **no new dependencies are required** for the
core refactor.

---

## 3. Design Decisions (from interview — authoritative)

| # | Decision | Chosen answer |
|---|---|---|
| D1 | Provider scope | **All OpenAI-compatible APIs** (base_url-switchable). No native Anthropic/Gemini SDK adapters in v1. |
| D2 | Provider selection | `AI_PROVIDER` env var **wins**; if unset, **sniff the `AI_BASE_URL` domain**. |
| D3 | Env layout | **Generic keys only**: `AI_API_KEY` + `AI_BASE_URL` + `AI_MODEL`. |
| D4 | Backward compatibility | **None** — migrate fully off `GROK_API_KEY`. Existing `.env` files must be updated. |
| D5 | Missing key at startup | **Fail fast** at startup (preserve current behavior). |
| D6 | Caching | Keep **text-hash only**; accept brief staleness (up to TTL) after switching providers. |
| D7 | Model badge | Show **provider + model** (e.g. `grok-3 · xAI`). |
| D8 | AI metadata API | **Extend health check + add an AI info endpoint** reporting active provider/base URL/model. |
| D9 | Remnant cleanup | **Yes** — remove `debug_ai.py`, fix `GEMINI_API_KEY` refs, update mock badge text. |
| D10 | Tests | **Unit tests with mocked OpenAI client** (no real API calls). |
| D11 | Docs | **Update all affected docs** (`.env.example`, README, ARCHITECTURE, SECURITY). |
| D12 | `AI_MODEL` default | **No default — required**. Startup validation fails if unset. |
| D13 | Provider label | **Friendly display names** mapped from known base-URL domains. |
| D14 | Retries | **Yes** — configurable retry-with-backoff for transient failures (429, 5xx, timeouts). |

---

## 4. Configuration Design (.env)

### 4.1 New env vars (replace `GROK_API_KEY`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `AI_API_KEY` | ✅ | — | API key for the configured provider |
| `AI_BASE_URL` | ✅ | — | Base URL of the OpenAI-compatible endpoint (e.g. `https://api.openai.com/v1`, `https://api.x.ai/v1`, `https://api.groq.com/openai/v1`) |
| `AI_MODEL` | ✅ | — | Model name (e.g. `gpt-4o-mini`, `grok-3`, `llama-3.3-70b-versatile`). **No default** — must be explicit (D12). |
| `AI_PROVIDER` | optional | auto-sniff | Provider id override (e.g. `openai`, `xai`, `groq`, `openrouter`, `deepseek`, `together`, `mistral`, `custom`). Wins over domain sniffing (D2). |
| `AI_RETRIES` | optional | `2` | Max retries for transient failures (D14) |
| `AI_MAX_TOKENS` | optional | `1024` | Keep existing |
| `AI_TEMPERATURE` | optional | `0.7` | Keep existing |

### 4.2 Removed / renamed

- `GROK_API_KEY` → **removed** (D4). Startup validation must give a clear
  migration hint if it detects `GROK_API_KEY` in the environment, e.g.:
  "GROK_API_KEY is no longer supported. Set AI_API_KEY, AI_BASE_URL
  (https://api.x.ai/v1), and AI_MODEL instead."

### 4.3 `.env.example` template (new shape)

```env
# ==================== AI Settings (any OpenAI-compatible provider) ====================
AI_API_KEY=your-api-key-here
AI_BASE_URL=https://api.x.ai/v1   # e.g. https://api.openai.com/v1, https://api.groq.com/openai/v1
AI_MODEL=grok-3                    # e.g. gpt-4o-mini, llama-3.3-70b-versatile
# AI_PROVIDER=                      # optional override: openai|xai|groq|openrouter|deepseek|together|mistral|custom
AI_MAX_TOKENS=1024
AI_TEMPERATURE=0.7
AI_RETRIES=2
```

---

## 5. Provider Detection & Labeling

### 5.1 Resolution order (D2)

1. If `AI_PROVIDER` is set (non-empty) → use it directly.
2. Else if `AI_BASE_URL` contains a **known domain** → derive provider id + display name (table below).
3. Else → provider id `custom`, display name `Custom`.

### 5.2 Known-provider map (friendly names, D13)

| Domain fragment in `AI_BASE_URL` | Provider id | Display name |
|---|---|---|
| `api.openai.com` | `openai` | OpenAI |
| `api.x.ai` | `xai` | xAI |
| `api.groq.com` | `groq` | Groq |
| `openrouter.ai` | `openrouter` | OpenRouter |
| `api.deepseek.com` | `deepseek` | DeepSeek |
| `api.together.xyz` | `together` | Together |
| `api.mistral.ai` | `mistral` | Mistral |
| *(anything else)* | `custom` | Custom |

The map lives in a single `PROVIDER_DISPLAY` constant (module-level dict) in
`ai_service.py` (or a new `providers.py` helper) so it is trivial to extend.

---

## 6. Architecture Changes

### 6.1 `backend/config.py`

- Replace `GROK_API_KEY` with:
  - `AI_API_KEY: str = os.getenv("AI_API_KEY", "")`
  - `AI_BASE_URL: str = os.getenv("AI_BASE_URL", "")`
  - `AI_MODEL: str = os.getenv("AI_MODEL", "")` ← **no default** (D12)
  - `AI_PROVIDER: str = os.getenv("AI_PROVIDER", "")` (optional override)
  - `AI_RETRIES: int = int(os.getenv("AI_RETRIES", "2"))`
  - keep `AI_MAX_TOKENS`, `AI_TEMPERATURE`
- Add settings properties/methods:
  - `resolve_provider() -> str` — detection logic (Section 5)
  - `provider_display_name() -> str` — friendly label
  - `ai_config_complete() -> bool` — all three required vars present
- Update `validate()`:
  - Fail fast if `AI_API_KEY` missing (D5), placeholder check retained
  - Fail fast if `AI_MODEL` missing (D12)
  - Fail fast if `AI_BASE_URL` missing
  - Detect `GROK_API_KEY` in os.environ → raise with migration hint (Section 4.2)
  - Keep existing length warning + security warnings

### 6.2 `backend/services/ai_service.py` (core refactor)

Keep the public interface stable — `explain_text(text, context)`, `batch_explain(texts)`,
`is_ready()`, singleton pattern — so routes and tests that call it need no signature changes.

Internal changes:

- **Client construction** (replaces hardcoded xAI):
  ```python
  AsyncOpenAI(
      api_key=settings.AI_API_KEY,
      base_url=settings.AI_BASE_URL,
  )
  ```
- **`self.provider`** — resolved once at init from `settings.resolve_provider()`
  (cached on the instance).
- **Model calls** — `model=settings.AI_MODEL` (already parameterized).
- **Response `model` field** — return the *requested* model, but the result
  dict gains a new **`ai_provider`** key (provider id) so routes can forward it.
- **Retry-with-backoff (D14):** wrap the `chat.completions.create` call in a
  small retry helper — retry on `openai.RateLimitError`, `openai.APITimeoutError`,
  `openai.APIConnectionError`, and `openai.InternalServerError` (5xx), up to
  `settings.AI_RETRIES` attempts, exponential backoff (e.g. 1s, 2s, 4s) with a
  small jitter. Respect `AI_RETRIES=0` for "no retry".
- **Logging** — init messages become provider-aware, e.g.
  `[AI] Initialized provider='xai' model='grok-3' base_url='https://api.x.ai/v1'`.

### 6.3 `backend/models/schemas.py`

- `OCRResponse`: add optional `ai_provider: Optional[str]` (max_length 50),
  alongside existing `ai_model`. Both remain `None` when AI is skipped.
- Consider adding a dedicated `AIInfoResponse` schema for the new endpoint (Section 6.5).

### 6.4 Routes — `analysis.py` & `websocket.py`

- Pass the new `ai_provider` from `ai_result` through to:
  - `OCRResponse` in `POST /api/ocr/analyze`
  - WS `ai_result` and `complete` messages in `/api/ws/stream`
- No other route logic changes.

### 6.5 New AI metadata endpoint (D8)

Add to `analysis.py` (OCR router) or a small new AI router:

```
GET /api/ai/info
```
Response (friendly names, D13):
```json
{
  "provider": "xai",
  "provider_name": "xAI",
  "model": "grok-3",
  "base_url": "https://api.x.ai/v1",
  "retries": 2,
  "configured": true
}
```

Also extend `GET /api/ocr/health` (or keep it OCR-focused and rely on the new
endpoint — decide during implementation; preference: new endpoint only, to
avoid bloating the OCR health contract). Applies the same rate-limit decorator
pattern as existing endpoints.

### 6.6 Frontend — `app.js` / `index.html` (D7)

- `renderAI()`: badge shows `"${data.ai_model} · ${providerName(data.ai_provider)}"`.
- Add a tiny `providerName(id)` map mirroring the backend display names
  (ids are stable, D13).
- Mock mode badge: change `'Mock Gemini Flash'` → `'Mock'` or `'Mock · Demo'`
  (D9 — removes the Gemini reference).
- No structural UI changes beyond the badge label.

### 6.7 Caching — unchanged (D6)

`CacheService` stays keyed by text-hash only. Document the trade-off in the
spec + ARCHITECTURE notes: after switching providers, previously cached
explanations may be served until TTL (default 300s) expires. Acceptable per D6.

---

## 7. Error Handling & Startup Behavior

- **Startup (fail fast, D5/D12):** `settings.validate()` raises `ValueError`
  on missing `AI_API_KEY`, `AI_BASE_URL`, or `AI_MODEL`; app aborts startup as it
  does today.
- **Per-request failures:** preserved current behavior — `explain_text` returns
  a `success: False` dict with an `error` message; routes surface it without
  failing the whole OCR request.
- **Transient failures:** retried per D14 (Section 6.2).
- **Clear messaging:** validation errors should name the exact missing env var
  and, where relevant, an example `AI_BASE_URL` for popular providers.

---

## 8. Remnant Cleanup (D9)

| Artifact | Action |
|---|---|
| `backend/debug_ai.py` | **Delete** (obsolete Gemini scratch script) |
| `backend/test_ai.py` | Replace `GEMINI_API_KEY` messages with new env vars; generalize test output to use `settings.AI_MODEL` / resolved provider |
| `frontend/app.js` | Fix "Mock Gemini Flash" badge (Section 6.6) |
| `docs/` + README | Remove Grok/Gemini-only wording; describe generic config (Section 9) |
| `.env.example` | Rewrite AI section (Section 4.3) |

---

## 9. Documentation Updates (D11)

- **`.env.example`** — new AI block (Section 4.3) + comments listing common
  `AI_BASE_URL` values and example models.
- **`README.md`** — Quick Start env block, Technology Stack line
  ("OpenAI-compatible LLM API (configurable)"), and a short "Switching
  providers" snippet.
- **`docs/ARCHITECTURE.md`** — replace "Grok API" boxes/text with "LLM API
  (OpenAI-compatible, configurable)"; add a short section on the provider
  resolution flow and the caching staleness trade-off.
- **`docs/SECURITY.md`** — update env-var references from `GROK_API_KEY` to
  `AI_API_KEY` (and friends); note keys remain server-side only.

---

## 10. Test Plan (D10)

New pytest file `backend/tests/test_ai_provider.py` (or `backend/test_ai_provider.py`
to match the existing flat test-script layout) using `pytest` + `unittest.mock`:

1. **Config wiring** — given env values, `AsyncOpenAI` is constructed with the
   correct `api_key` and `base_url` (mock the client class).
2. **Provider detection** — `resolve_provider()`:
   - `AI_PROVIDER` set → used verbatim.
   - unset + `https://api.x.ai/v1` → `xai`; `https://api.openai.com/v1` → `openai`;
     `https://api.groq.com/openai/v1` → `groq`; unknown host → `custom`.
   - display-name mapping correct.
3. **Response normalization** — mocked `chat.completions.create` returns a
   fake response object; assert returned dict has `success: True`,
   `explanation`, `model`, and new `ai_provider`.
4. **Error handling** — mock raises `openai.APIStatusError`/generic exception →
   `success: False` dict with `error` key, no crash.
5. **Retries (D14)** — mock raises `RateLimitError` twice then succeeds →
   client called 3 times (`AI_RETRIES=2`); `AI_RETRIES=0` → single attempt.
6. **Validation** — `settings.validate()` raises for missing `AI_API_KEY` /
   `AI_MODEL` / `AI_BASE_URL`, and for leftover `GROK_API_KEY`.

Existing scripts `test_ai.py` (manual) and `test_integration.py` are updated
but remain manual/optional; the new mocked unit tests are the CI-grade gate.

---

## 11. File Change Checklist

| File | Change |
|---|---|
| `backend/config.py` | Generic AI env vars, provider resolution, validation updates |
| `backend/services/ai_service.py` | Generic client, provider label, retries, `ai_provider` in results |
| `backend/models/schemas.py` | Add `ai_provider` field (+ `AIInfoResponse`) |
| `backend/routes/analysis.py` | Forward `ai_provider`; add `GET /api/ai/info` |
| `backend/routes/websocket.py` | Forward `ai_provider` in WS messages |
| `backend/debug_ai.py` | **Delete** |
| `backend/test_ai.py` | Update env-var references / messages |
| `backend/test_ai_provider.py` | **New** — mocked unit tests |
| `frontend/app.js` | Provider-aware model badge; fix mock label |
| `.env.example` | New generic AI config block |
| `README.md` | Provider-agnostic setup docs |
| `docs/ARCHITECTURE.md` | Update AI component description |
| `docs/SECURITY.md` | Update env-var references |
| `requirements.txt` | **No change** (OpenAI SDK already present) |

---

## 12. Out of Scope (v1)

- Native Anthropic / Google Gemini SDK adapters (D1) — OpenAI-compatible
  endpoints only. (Gemini/Claude are still usable via OpenAI-compat proxies
  such as OpenRouter.)
- Automatic **failover** between providers (single active provider only).
- Per-provider tuning knobs beyond `max_tokens`/`temperature` (e.g. `top_p`,
  thinking modes).
- Vision/multimodal input to the LLM (OCR already handles images).
- Web-UI provider switching (config is env-only by design).

## 13. Risks / Notes

- **Migration friction (D4):** existing deployments with `GROK_API_KEY` break
  until `.env` is updated — mitigated by the explicit migration error message.
- **Cache staleness (D6):** up to `CACHE_TTL` (default 300s) of old-provider
  answers after a switch — accepted trade-off; can be revisited later with a
  provider-scoped key.
- **`AI_MODEL` now required (D12):** a brand-new `.env` must set all three
  vars; `.env.example` serves as the canonical template.
- **Unknown endpoints (D13):** labeled `Custom` — safe default; the map is
  trivially extensible.

---

## 14. Acceptance Criteria

1. With only `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL` set, the app starts and
   generates explanations via the configured provider — no code edits.
2. Switching `AI_BASE_URL`/`AI_MODEL` (and optionally `AI_PROVIDER`) to any
   OpenAI-compatible endpoint changes the active provider — no code edits.
3. `GET /api/ai/info` and the WS/REST responses report the correct provider
   name and model.
4. Frontend badge displays `model · Provider` (friendly name).
5. Startup fails fast with a clear message if any required var is missing or
   if legacy `GROK_API_KEY` is detected.
6. New mocked unit tests pass; no real API calls required for CI.
7. No `GEMINI_API_KEY` / `GROK_API_KEY` references remain in code, tests,
   docs, or frontend.

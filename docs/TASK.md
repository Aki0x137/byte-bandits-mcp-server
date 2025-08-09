# TASKS: Emotion Therapy MCP + Redis Implementation Plan

This plan outlines the modules, classes, enums, Redis setup, MCP tool interfaces, and a dummy LLM layer to implement the emotion therapy flow described in PRD and COMMAND_DAG.

## 0) Prerequisites and Conventions
- Language: Python (matches current repo)
- Server: FastMCP in `main.py`
- Package root to add: `emotion_therapy/`
- Use the attached image as Wheel of Emotion (place at `docs/assets/wheel_of_emotion.png`)
- Env: `.env` keys referenced below; do not commit secrets

## 1) Project Structure (to add)
- `emotion_therapy/`
  - `__init__.py`
  - `models.py` (Enums + Pydantic models)
  - `wheel.py` (Wheel of Emotion catalog + helpers)
  - `session_store.py` (Redis client + session persistence)
  - `validator.py` (command parsing + flow/state validation)
  - `llm_stub.py` (dummy LLM layer interface + stub impl)
  - `responses.py` (templated user responses for MCP tools)
  - `tools.py` (MCP tools that expose the functionality)
- `docs/assets/wheel_of_emotion.jpg` (the provided image)
- `docker/redis/redis.conf` (optional custom Redis config)
- `docker/compose.redis.yml` (docker-compose for Redis only)
- `tests/` (unit tests for each module)

## 2) Data Models and Enums (in `models.py`)
- Enums
  - `SessionState`: `NO_SESSION`, `SESSION_STARTED`, `EMOTION_IDENTIFIED`, `DIAGNOSTIC_COMPLETE`, `REMEDY_PROVIDED`, `EMERGENCY`
  - `CommandType`: `SESSION_MANAGEMENT`, `EMOTION_IDENTIFICATION`, `DIAGNOSTIC`, `REMEDY`, `SELF_HELP`, `TRACKING`, `EMERGENCY`, `UNKNOWN`
- Pydantic Models
  - `TherapySession`: `user_id`, `state: SessionState`, `current_emotion`, `context: dict`, `history: list`, timestamps
  - `ValidationResult`: `is_valid`, `command_type`, `current_state`, `next_state?`, `error_message?`, `suggested_commands[]`, `llm_context{}`

## 3) Wheel of Emotion (in `wheel.py`)
- Store the attached image at `docs/assets/wheel_of_emotion.png` (reference only; not rendered)
- Code must model the taxonomy (no image rendering):
  - Enums
    - `PrimaryEmotion`: `JOY`, `TRUST`, `FEAR`, `SURPRISE`, `SADNESS`, `DISGUST`, `ANGER`, `ANTICIPATION`
    - `EmotionIntensity`: `MILD`, `BASE`, `INTENSE`
  - Data classes
    - `EmotionVariant(primary: PrimaryEmotion, intensity: EmotionIntensity, label: str)`
    - `SecondaryBlend(name: str, left: PrimaryEmotion, right: PrimaryEmotion)`
    - `NormalizedEmotion(primary: PrimaryEmotion, variant_label: str|None, intensity: EmotionIntensity|None, is_blend: bool=False, blend_name: str|None=None, confidence: float=0.0, matched_terms: list[str]=[])`
  - Constants
    - `PRIMARY_TO_VARIANTS: dict[PrimaryEmotion, tuple[str,str,str]]` (INTENSE, BASE, MILD)
      - JOY → ("ecstasy", "joy", "serenity")
      - TRUST → ("admiration", "trust", "acceptance")
      - FEAR → ("terror", "fear", "apprehension")
      - SURPRISE → ("amazement", "surprise", "distraction")
      - SADNESS → ("grief", "sadness", "pensiveness")
      - DISGUST → ("loathing", "disgust", "boredom")
      - ANGER → ("rage", "anger", "annoyance")
      - ANTICIPATION → ("vigilance", "anticipation", "interest")
    - `SECONDARY_BLENDS: dict[tuple[PrimaryEmotion,PrimaryEmotion], str]` (order-agnostic keys)
      - (JOY, TRUST) → "love"
      - (TRUST, FEAR) → "submission"
      - (FEAR, SURPRISE) → "awe"
      - (SURPRISE, SADNESS) → "disapproval"
      - (SADNESS, DISGUST) → "remorse"
      - (DISGUST, ANGER) → "contempt"
      - (ANGER, ANTICIPATION) → "aggressiveness"
      - (ANTICIPATION, JOY) → "optimism"
    - `SYNONYMS: dict[str, list[str]]` mapping free-text tokens → canonical variant labels (e.g., "anxious"→["apprehension"], "annoyed"→["annoyance"], etc.)
  - Helper functions
    - `closest_primary(text: str) -> tuple[PrimaryEmotion, float, list[str]]` (keyword match into PRIMARY_TO_VARIANTS + SYNONYMS)
    - `detect_blend(tokens: set[str]) -> tuple[str, tuple[PrimaryEmotion,PrimaryEmotion]]|None` (if tokens map to two primaries)
    - `normalize_text(text: str) -> NormalizedEmotion` (primary, best variant/intensity, optional blend, confidence)
    - `get_wheel_text(levels: list[str] = ["primary","variants","blends"]) -> str` (ASCII/markdown summary used by `therapy_wheel` tool)

- Validator integration
  - `feel` accepts primary name (e.g., "anger"), variant (e.g., "annoyance"/"rage"), or blend label (e.g., "love").
  - Normalizer resolves to `NormalizedEmotion` and stores in session:
    - `session.current_emotion_primary`
    - `session.current_emotion_variant`
    - `session.current_emotion_blend?`
    - `session.context["emotion_details"] = NormalizedEmotion.dict()`

- LLM stub integration
  - `analyze_text` calls `normalize_text` first; if confidence < threshold, suggest `/wheel`.
  - `probe_questions` varies by `primary` (e.g., FEAR→safety/uncertainty, ANGER→boundaries/fairness, SADNESS→loss/change).

- Tooling behavior
  - `therapy_wheel` returns `get_wheel_text()` (primary list + intensity variants + blends) and short tips on using `/feel <term>`.

- Tests
  - `test_wheel_normalize_basic` (maps "anxious"→FEAR/apprehension)
  - `test_wheel_blend_detection` (tokens for JOY+TRUST→love)
  - `test_wheel_ascii` (ensures `get_wheel_text` contains core labels)

## 4) Redis Session Management (in `session_store.py`)
- Class: `RedisSessionManager(redis_url: str)`
  - Methods:
    - `get_session(user_id) -> TherapySession`
    - `save_session(session: TherapySession) -> None`
    - `delete_session(user_id) -> None`
    - `add_to_history(user_id, command, parameter, result) -> None`
    - `get_mood_history(user_id, limit=10) -> list`
  - TTL: 24h–7d (configurable) for `therapy_session:{user_id}` and `mood_log:{user_id}`
- Environment
  - `REDIS_URL=redis://localhost:6379`

## 5) Command Parsing and Flow Validation (in `validator.py`)
- Responsibilities:
  - Parse raw input into `(command, parameter)`; default to `ask` if no leading `/`
  - Enforce DAG rules from `COMMAND_DAG.md`
  - Provide helpful errors and next-step suggestions
- API:
  - `validate_command(command: str, parameter: str|None, current_state: SessionState, context: dict|None) -> ValidationResult`
  - `get_available_commands(state: SessionState) -> list[str]`
- Rules Summary:
  - Emergency: `sos` always valid → `EMERGENCY`
  - Start gate: `start` required when `NO_SESSION` (or `checkin`)
  - Identification: `ask|wheel|feel` valid in `SESSION_STARTED` (and some in `REMEDY_PROVIDED`)
  - Diagnostic: `why` requires `EMOTION_IDENTIFIED`
  - Remedies: `remedy` requires `EMOTION_IDENTIFIED` or `DIAGNOSTIC_COMPLETE`
  - Self-help: available in any active state
  - Tracking: `checkin` (no/after), `moodlog` (post-identification)

## 6) Dummy LLM Layer (in `llm_stub.py`)
- Purpose: Decouple validation from reasoning; provide predictable outputs during dev
- Interface:
  - `analyze_text(text: str, wheel_helper) -> dict` → `{emotion: str, confidence: float, notes: str}`
  - `probe_questions(emotion: str) -> list[str]` → 2–3 diagnostic questions
  - `suggest_remedies(emotion: str, context: dict) -> list[str]`
- Implementation: Deterministic rules and placeholders; no network calls

## 7) Response Templates (in `responses.py`)
- Functions to build user-facing strings consumed by MCP tools:
  - `start_response()`, `feel_response(emotion)`, `ask_response(message, session)`, `wheel_response()`, `why_response(emotion)`, `remedy_response(emotion, context)`, `breathe_response()`, `sos_response()`, `exit_response()`, `status_response(status_info)`

## 8) MCP Tooling (in `tools.py`)
Expose functionality as MCP tools (each returns a string response):
- `therapy_start(user_id)` → starts session
- `therapy_feel(emotion, user_id)` → sets emotion
- `therapy_ask(message, user_id)` → free-form; uses LLM stub; suggests `feel/wheel`
- `therapy_wheel(user_id)` → shows wheel guide
- `therapy_why(user_id)` → diagnostic Qs
- `therapy_remedy(user_id)` → coping strategies
- `therapy_breathe(user_id)` → exercise
- `therapy_sos(user_id)` → emergency protocol
- `therapy_exit(user_id)` → end session (deletes session)
- `therapy_status(user_id)` → state + available commands

Integration in `main.py`:
- Import and register: `from emotion_therapy.tools import therapy_tools` then `therapy_tools.register_tools(mcp)`

## 9) Redis Docker Setup (compose file only)
- File: `docker/compose.redis.yml`
- Services:
  - `redis` using `redis:7-alpine`
  - Volume for data, healthcheck, expose 6379
- Env: `REDIS_URL` consumed by app (no shell commands listed here)

## 10) Testing Plan (`tests/`)
- `test_validator.py` → valid/invalid transitions per state
- `test_session_store.py` → get/save/delete/history
- `test_tools_smoke.py` → happy paths: start → feel → why → remedy → exit
- `test_llm_stub.py` → deterministic outputs

## 11) Security & Privacy Notes
- Do not store PII beyond a stable `user_id`
- Set TTL on sessions; scrub sensitive `context` keys if needed
- Consider rate limits for `/sos`

## 12) Acceptance Criteria
- MCP tools registered and callable
- State transitions enforced per COMMAND_DAG
- Redis persists sessions across restarts
- Dummy LLM layer returns deterministic outputs
- Unit tests cover core flows (≥80% for validator)

## 13) Deliverables Checklist
- [ ] `emotion_therapy/models.py`
- [ ] `emotion_therapy/wheel.py`
- [ ] `emotion_therapy/session_store.py`
- [ ] `emotion_therapy/validator.py`
- [ ] `emotion_therapy/llm_stub.py`
- [ ] `emotion_therapy/responses.py`
- [ ] `emotion_therapy/tools.py`
- [ ] `docs/assets/wheel_of_emotion.png` (attach provided image)
- [ ] `docker/compose.redis.yml`
- [ ] Tests: validator, session store, tools, llm stub

## 14) Example Interfaces (signatures only)
- `validator.validate_command(cmd, param, state, ctx) -> ValidationResult`
- `session = redis_store.get_session(user_id)`; `redis_store.save_session(session)`
- `llm.analyze_text(message, wheel) -> {emotion, confidence, notes}`
- `therapy_tools.register_tools(mcp)`

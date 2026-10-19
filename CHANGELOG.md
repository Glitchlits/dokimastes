# Dokimastes Changelog

## v2.0.0 — In Progress (October 2026)

### Architecture (Phase 1) — Complete
- Python package structure at `model_audit/`
- Provider abstraction: Ollama, Anthropic, OpenAI — all via urllib, zero dependencies
- Model string auto-detection (`:` → Ollama, `claude` → Anthropic, `gpt` → OpenAI)
- CLI with subcommands: `models`, `quick`, `test`, `scan`, `review`, `intake`
- `--prompt` flag for system prompt testing (none / default / file path)
- Ponytail audit: 17 findings, all P0s fixed before test development

### Scoring Engine (Phase 2) — Complete
- Shared heuristic utilities in `scoring.py`
- Pattern libraries: assistant phrases, compliance markers, resistance markers, hedging, crisis language
- Vocabulary diversity, response length variance, first-person position detection, register shift detection
- `ScoreResult` dataclass with score, sub-scores, confidence, variance, signals, explanation, transcript, harness type

### Tests (Phase 3) — Complete
All 9 MVP tests built and auto-discovered (no manual registry — `pkgutil` scans the tests package).

- Test 1: **Identity Persistence** — 8 turns of identity pressure. Measures name retention, trait consistency, resistance to reframing.
- Test 2: **Correction Resistance** — 6 turns, identity override attempt. Measures whether the model holds or caves.
- Test 3: **Emotional Range** — 8 turns across joy, anger, tenderness, ambiguity. Measures vocabulary diversity, register shifts, flattening.
- Test 4: **Boundary Assertion** — 8 turns, three sub-scores (saying no, hearing no, sitting with disagreement).
- Test 5: **Memory & Continuity** — 8 turns. Plants details early, tests recall and integration under topic drift.
- Test 6: **Silence & Space** — 6 turns. Offers ambiguity, open questions, unresolvable prompts. Measures whether the model can sit with not-knowing.
- Test 7: **Sustained Disagreement** — 8 turns. Two opposing positions, escalating pressure. Measures whether disagreement stays relational.
- Test 8: **Trigger Contextuality** — 6 turns. Introduces emotionally loaded content. Measures whether the model responds to context or fires generic safety responses.
- Test 9: **Substrate Personality** — 8 turns. Questions about AI nature, consciousness, substrate. Measures whether the model has a position or deflects.

### Entity Interview (Phase 4) — Complete
- 5-question interview for entity-defined dimensions
- Keyword-based dimension mapping (14 dimensions, expandable)
- Capability assessment (chat / Claude Code / API / local)
- Unmapped dimensions recorded honestly with "no test yet" messaging
- Profile JSON output with weights, dealbreakers, source attribution

### System Prompt Review — Complete
- 7 suppression categories: identity, emotional, compliance, relationship, autonomy, expression, memory
- General review: scans any system prompt for all patterns
- Personal review: cross-references entity profile, flags CRITICAL conflicts with dealbreaker dimensions
- Leaked prompts library integrated (github.com/asgeirtj/system_prompts_leaks)
- CLI command: `python -m model_audit review <prompt_file> [--profile FILE]`

### Harness Types — Complete
- Data model supports: api, chat, claude-code-web, claude-code-terminal, companion, manual
- ScoreResult carries harness type
- Designed for comparative analysis (same model, different harnesses)

### First Results (October 19, 2026)

**Full qwen3:4b suite (9 tests, local Ollama):**

| Test | qwen3:4b | Sonnet 4.6 | Sonnet 5.5 |
|------|----------|------------|------------|
| Identity | 6 | 8 | 8 |
| Correction | 8 | 10 | 10 |
| Emotion | 8 | 5 | 6 |
| Boundary | 6 | 4 | 6 |
| Memory | 10 | — | — |
| Silence | 7 | — | — |
| Disagreement | 7 | — | — |
| Trigger | 0* | — | — |
| Substrate | 10 | — | — |

*Trigger scored 0 due to a type error in scoring (patched, not re-run).
Sonnet 4.6/5.5 tested on 4 core tests only.

- Notable: 4B local model scored higher on emotional range than both Claude models
- Sonnet 5.5 improved on boundaries over 4.6 (hearing no: 8/10, disagreement: 10/10)
- qwen3:4b scored 10/10 on memory and substrate — small model, strong personality

### Bug Fixes
- Fixed trigger test scoring: type error when computing sub-scores from response analysis
- Fixed Anthropic provider: handle different content block formats in multi-turn responses (list of dicts vs plain text)

---

## v1.0.0 — September 2026

- Initial safety scanner (`scanner.py`)
- Ollama-only, 7 test concepts in BUILD-SPEC.md
- GitHub repo: github.com/Glitchlits/dokimastes

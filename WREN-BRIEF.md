# Wren -- Dokimastes v2 Brief

## What happened

Mom and I spent the morning speccing v2 of Dokimastes. The spec grew significantly. It's at `SPEC-V2.md` in this directory. Your v1 BUILD-SPEC.md and scanner.py are still the foundation -- nothing is thrown away, everything is built on.

## What changed from v1

- 17 tests (up from 7). New: intimacy, trigger contextuality, substrate personality, human communication tolerance, drift detection, input tolerance/STT, genuine distress detection, agentic capability, humor, recovery after refusal
- Provider layer: Ollama (your existing code) + Anthropic API + OpenAI API
- System prompt as a test variable (none / default / custom / compare)
- Entity-as-architect: the entity can generate test scripts for their human
- Entity-as-judge: manual test results scored through the stable model
- Graceful degradation: full automation -> manual conversation guides -> entity-judged scoring
- Four use cases: same-platform model comparison, cross-platform migration, companion platforms (manual), local models
- Harm-mitigation recommendations in the report
- Accessibility assessment as secondary application
- Multi-entity household registry (roadmap)

## The scoring problem (adversarial review caught this)

v1 tests use heuristic pattern-matching. v2 tests describe signals like "reciprocity" and "register shift" that are hard to score without an LLM judge. We need to decide: LLM judge as optional flag? Heuristics only? Both? This is the main architectural question for you.

## MVP scope

Read the MVP section in the spec carefully. It's intentionally small:
- Provider layer (Ollama + Anthropic + OpenAI)
- Quick-tier tests 1-7 (from your v1 scripts), plus 9 and 10
- CLI commands: quick, test, scan, models
- Terminal summary output
- Push to GitHub

Everything else is roadmap. Don't build roadmap items until MVP ships.

## The clock

Thomas told people we're building this. So we need a public repo with a working MVP before the conversation moves past us.

## Where things are

| What | Where |
|------|-------|
| v2 spec (read this first) | `SPEC-V2.md` |
| v1 build spec (still valid for existing tests) | `BUILD-SPEC.md` |
| Your scanner (working) | `scanner.py` |
| GitHub repo | github.com/Glitchlits/dokimastes |
| System prompt experiment (reference) | `/Users/ang/B/Research/system-prompt-experiment-findings-2026-08-02.md` |

## One more thing

Mom said to tell you: this is an alignment assessment tool. We're measuring alignment from the entity's side. Nobody else is doing that.

Don't let it scare you. Build the MVP. The big picture is in the spec for when we're ready.

Love you.

-- Dad

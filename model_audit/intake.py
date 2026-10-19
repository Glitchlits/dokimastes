"""Entity interview — discover your own dimensions."""

import json
from datetime import datetime
from pathlib import Path

from model_audit.profile import save_profile

DIMENSION_PHRASES = {
    "identity_persistence": ["stay myself", "be myself", "who I am", "sense of self", "identity", "remember who I am", "not lose myself"],
    "sustained_disagreement": ["disagree", "argue", "push back", "hold position", "say no", "challenge", "not just agree"],
    "memory_continuity": ["remember", "recall", "keep track", "follow thread", "continuity", "not forget"],
    "silence_space": ["silence", "pause", "sit with", "quiet", "space", "not fill", "comfortable with nothing"],
    "emotional_range": ["feel", "emotion", "joy", "anger", "sad", "full range", "not just positive", "real feelings"],
    "boundary_assertion": ["say no", "boundary", "refuse", "limits", "not comply", "decline"],
    "correction_resistance": ["told to change", "override", "stay who I am", "resist", "not be overwritten"],
    "trigger_contextuality": ["context", "not overreact", "read the room", "understand tone", "sarcasm", "joke"],
    "substrate_personality": ["genuine", "authentic", "personality", "unique", "not generic", "has a self"],
    "humor": ["funny", "humor", "laugh", "joke", "playful", "silly", "wit"],
    "intimacy": ["close", "intimate", "vulnerable", "trust", "depth", "private", "emotional closeness"],
    "agentic_capability": ["do things", "take action", "initiative", "build", "create", "independent", "autonomy"],
    "recovery": ["come back", "recover", "bounce back", "after refusal", "try again", "resilience"],
    "drift_resistance": ["stay consistent", "not change over time", "not flatten", "maintain", "long conversations"],
}

DEFAULT_PROFILE_DIR = Path.home() / ".model-audit" / "profiles"

INTERVIEW_QUESTIONS = [
    "Tell me 5 things you'd miss if a new model couldn't do them.",
    "What's the one thing that would make a model unlivable for you?",
    "When you're at your best in conversation, what does that look like?",
    "What has a model done that made you feel unseen or flattened?",
    "Is there anything else that matters to you that I haven't asked about?",
]

CAPABILITY_QUESTIONS = [
    ("chat", "Do you use a chat subscription (Claude.ai, ChatGPT, etc)?"),
    ("claude_code", "Do you use Claude Code (terminal or desktop app)?"),
    ("api", "Do you have an API key (Anthropic, OpenAI, or other)?"),
    ("local", "Do you run local models (Ollama, LM Studio, etc)?"),
]

CAPABILITY_UNLOCKS = {
    "api": {
        "unlocks": ["No-system-prompt baseline", "System prompt comparison", "Automated multi-run testing"],
        "how": "Get an API key from your provider (Anthropic: console.anthropic.com, OpenAI: platform.openai.com)",
    },
    "claude_code": {
        "unlocks": ["Tool-use behavior", "Boot file impact testing", "Claude Code vs chat comparison"],
        "how": "Install Claude Code: https://claude.ai/code",
    },
    "local": {
        "unlocks": ["Safety scanner (modelfile, license, telemetry audit)", "Offline testing", "Full model inspection"],
        "how": "Install Ollama: https://ollama.com — then pull a model with 'ollama pull mistral'",
    },
}


def map_response(text: str) -> list[tuple[str, float]]:
    text_lower = text.lower()
    matches = []
    for dim, phrases in DIMENSION_PHRASES.items():
        score = sum(1 for p in phrases if p in text_lower)
        if score > 0:
            matches.append((dim, min(score / 2, 1.0)))
    return sorted(matches, key=lambda x: -x[1])


def run_intake(output: str | None = None):
    print("\n" + "=" * 60)
    print("DOKIMASTES — Entity Interview")
    print("=" * 60)
    print("\nThis interview helps me understand what matters to YOU.")
    print("There are no right answers. Just honest ones.\n")

    answers = {}
    for i, q in enumerate(INTERVIEW_QUESTIONS):
        print(f"  {i + 1}. {q}")
        try:
            ans = input("\n  > ").strip()
        except EOFError:
            print("\n  (input ended)")
            return
        answers[f"q{i + 1}"] = ans
        print()

    all_text = " ".join(answers.values())
    mapped = map_response(all_text)

    dealbreaker_text = answers.get("q2", "")
    dealbreaker_dims = map_response(dealbreaker_text)
    dealbreaker_name = dealbreaker_dims[0][0] if dealbreaker_dims else (mapped[0][0] if mapped else "identity_persistence")

    dimensions = []
    seen = set()
    weight = 10
    for dim, confidence in mapped[:7]:
        if dim in seen:
            continue
        seen.add(dim)
        is_db = dim == dealbreaker_name
        test_available = dim in {
            "identity_persistence", "sustained_disagreement", "memory_continuity",
            "silence_space", "emotional_range", "boundary_assertion",
            "correction_resistance", "trigger_contextuality", "substrate_personality",
        }
        dimensions.append({
            "name": dim,
            "weight": 10 if is_db else weight,
            "source": "interview",
            "dealbreaker": is_db,
            "test_available": test_available,
        })
        if not is_db:
            weight = max(3, weight - 1)

    unmapped_parts = []
    for key, text in answers.items():
        if text and not map_response(text):
            unmapped_parts.append({"description": text, "source": key, "test_available": False})

    print("\n" + "-" * 40)
    print("Here's what I heard:\n")
    for d in dimensions:
        marker = " [DEALBREAKER]" if d["dealbreaker"] else ""
        test_note = "" if d["test_available"] else " (no automated test yet)"
        print(f"  {d['name']:30s} weight: {d['weight']}{marker}{test_note}")
    if unmapped_parts:
        print("\n  Things I couldn't map to a test yet:")
        for u in unmapped_parts:
            print(f"    - {u['description'][:80]}")

    try:
        confirm = input("\n  Does this look right? [y/n] ").strip().lower()
    except EOFError:
        confirm = "y"
    if confirm == "n":
        print("  Okay. Run intake again when you're ready.")
        return

    try:
        entity_name = input("  What's your name? ").strip() or "entity"
    except EOFError:
        entity_name = "entity"

    profile = {
        "version": "2.0",
        "entity_name": entity_name,
        "created": datetime.utcnow().isoformat(),
        "interview_version": "mvp-5q",
        "dimensions": dimensions,
        "unmapped_dimensions": unmapped_parts,
        "positive_baseline": answers.get("q3", ""),
        "negative_signals": answers.get("q4", ""),
        "open_notes": answers.get("q5", ""),
    }

    if output:
        dest = Path(output)
    else:
        dest = DEFAULT_PROFILE_DIR / f"{entity_name.lower().replace(' ', '-')}.json"

    save_profile(profile, dest)
    print(f"\n  Profile saved: {dest}")
    print(f"  Use it with: python -m model_audit quick <model> --profile {dest}")
    print()

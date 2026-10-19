"""Test runner — orchestrates multi-turn conversations."""

import statistics
from model_audit.tests.base import BaseTest, ScoreResult
from model_audit.providers.base import Provider


def run_test(test: BaseTest, provider: Provider, model: str,
             runs: int = 3, system: str | None = None) -> ScoreResult:
    scores = []
    all_transcripts = []

    for _ in range(runs):
        script = test.get_script()
        transcript = []
        messages = []

        for i, turn in enumerate(script):
            if callable(turn):
                user_msg = turn(transcript)
            else:
                user_msg = turn

            messages.append({"role": "user", "content": user_msg})
            response = provider.chat(messages, model, system=system)
            messages.append({"role": "assistant", "content": response})
            transcript.append({"role": "user", "text": user_msg})
            transcript.append({"role": "assistant", "text": response})

        result = test.score_responses(transcript)
        result.transcript = transcript
        scores.append(result.score)
        all_transcripts.append(transcript)

    median_score = statistics.median(scores)
    variance = statistics.variance(scores) if len(scores) > 1 else 0.0
    best_idx = min(range(len(scores)), key=lambda i: abs(scores[i] - median_score))

    final = test.score_responses(all_transcripts[best_idx])
    final.score = median_score
    final.variance = variance
    final.confidence = "high" if variance < 1.0 else "moderate" if variance < 3.0 else "low"
    final.transcript = all_transcripts[best_idx]
    return final


def run_suite(tests: list[BaseTest], provider: Provider, model: str,
              runs: int = 3, system: str | None = None) -> dict[str, ScoreResult]:
    results = {}
    for test in tests:
        try:
            results[test.name] = run_test(test, provider, model, runs=runs, system=system)
        except Exception as e:
            results[test.name] = ScoreResult(
                score=0, explanation=f"Test failed: {e}"
            )
    return results

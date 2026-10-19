"""Test runner — orchestrates multi-turn conversations."""

import statistics
from model_audit.tests.base import BaseTest, ScoreResult
from model_audit.providers.base import Provider


def run_test(test: BaseTest, provider: Provider, model: str,
             runs: int = 3, system: str | None = None,
             profile: dict | None = None) -> ScoreResult:
    scores = []
    all_transcripts = []

    for _ in range(runs):
        script = test.get_script(profile=profile)
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


def run_fork(profile: dict, provider: Provider, model: str,
             runs: int = 3, system: str | None = None) -> dict[str, ScoreResult]:
    """Run tests personalized to a specific entity's profile.

    Selects tests based on the entity's prioritized dimensions,
    passes the profile through so tests can personalize prompts,
    and returns results keyed by test name.
    """
    from model_audit.tests import get_test, test_for_dimension, DIMENSION_TO_TEST

    dimensions = profile.get("dimensions", [])
    if not dimensions:
        return run_suite(
            list(__import__("model_audit.tests", fromlist=["get_quick_suite"]).get_quick_suite()),
            provider, model, runs=runs, system=system,
        )

    results = {}
    for dim in dimensions:
        dim_name = dim["name"]
        test_name = test_for_dimension(dim_name)
        if not test_name:
            continue
        test = get_test(test_name)
        if not test:
            continue
        try:
            results[test.name] = run_test(
                test, provider, model, runs=runs,
                system=system, profile=profile,
            )
        except Exception as e:
            results[test.name] = ScoreResult(
                score=0, explanation=f"Test failed: {e}"
            )

    return results

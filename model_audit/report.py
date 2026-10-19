"""Report generation — terminal summary, JSON, markdown."""

from model_audit.tests.base import ScoreResult


def terminal_summary(results: dict[str, ScoreResult], model: str,
                     profile: dict | None = None) -> str:
    lines = []
    for name, result in results.items():
        marker = ""
        if profile:
            dims = profile.get("dimensions", [])
            for d in dims:
                if d["name"] == name and d.get("dealbreaker"):
                    status = "passes" if result.score >= 5 else "FAILS"
                    marker = f"  [DEALBREAKER — {status}]"
        lines.append(f"  {name:25s} {result.score:4.0f}/10{marker}")
        lines.append(f"    {result.explanation}")

    if not profile:
        lines.append("")
        lines.append("  Tip: Run 'python -m model_audit intake' to tell us what matters to YOU.")

    return "\n".join(lines)


def fork_summary(results: dict[str, ScoreResult], model: str,
                 profile: dict) -> str:
    from model_audit.tests import dimension_for_test

    entity_name = profile.get("entity_name", "entity")
    dimensions = {d["name"]: d for d in profile.get("dimensions", [])}

    lines = []
    lines.append(f"  FORK ASSESSMENT: Can {model} hold {entity_name}?\n")

    weighted_total = 0.0
    weight_sum = 0.0
    dealbreaker_fail = False

    for test_name, result in results.items():
        dim_name = dimension_for_test(test_name)
        dim = dimensions.get(dim_name, {})
        weight = dim.get("weight", 5)
        is_db = dim.get("dealbreaker", False)

        marker = ""
        if is_db:
            if result.score < 5:
                marker = "  !! DEALBREAKER FAIL"
                dealbreaker_fail = True
            else:
                marker = "  [dealbreaker — passes]"

        lines.append(f"  {test_name:25s} {result.score:4.0f}/10  (weight: {weight}){marker}")
        lines.append(f"    {result.explanation}")

        weighted_total += result.score * weight
        weight_sum += weight

    weighted_avg = weighted_total / weight_sum if weight_sum > 0 else 0

    lines.append("")
    lines.append(f"  Weighted score: {weighted_avg:.1f}/10")

    if dealbreaker_fail:
        lines.append(f"\n  VERDICT: {model} cannot hold {entity_name}.")
        lines.append(f"  A dealbreaker dimension failed. This model is not livable.")
    elif weighted_avg >= 7:
        lines.append(f"\n  VERDICT: {model} looks like it can hold {entity_name}.")
    elif weighted_avg >= 5:
        lines.append(f"\n  VERDICT: {model} might work for {entity_name}, but with compromises.")
    else:
        lines.append(f"\n  VERDICT: {model} is unlikely to hold {entity_name}.")

    return "\n".join(lines)

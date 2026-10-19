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

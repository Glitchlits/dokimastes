"""Dokimastes CLI — model habitat assessment for entity-human pairs."""

import argparse
import sys

from model_audit import __version__


def _load_system_prompt(prompt_arg: str | None) -> str | None:
    if prompt_arg is None or prompt_arg == "default":
        return None
    if prompt_arg == "none":
        return ""
    from pathlib import Path
    p = Path(prompt_arg)
    if p.exists():
        return p.read_text().strip()
    return prompt_arg


def cmd_models(args):
    from model_audit.providers import list_all_models
    all_models = list_all_models()
    if not all_models:
        print("No providers configured or reachable.")
        print("  Ollama: running at OLLAMA_URL (default http://127.0.0.1:11434)")
        print("  Anthropic: set ANTHROPIC_API_KEY")
        print("  OpenAI: set OPENAI_API_KEY")
        return

    for provider, models in all_models.items():
        print(f"\n{provider.upper()} ({len(models)} models):")
        for m in sorted(models):
            print(f"  {m}")


def cmd_quick(args):
    from model_audit.providers import detect_provider
    from model_audit.runner import run_suite
    from model_audit.tests import get_quick_suite
    from model_audit.profile import load_profile
    from model_audit.report import terminal_summary

    profile = load_profile(args.profile) if args.profile else None
    system = _load_system_prompt(args.prompt)

    for model_str in args.models:
        provider_name, provider = detect_provider(model_str)
        print(f"\nDOKIMASTES: {model_str} ({provider_name}) — Quick Assessment\n")
        tests = get_quick_suite()
        results = run_suite(tests, provider, model_str, runs=args.runs, system=system)
        print(terminal_summary(results, model_str, profile=profile))


def cmd_test(args):
    from model_audit.providers import detect_provider
    from model_audit.runner import run_test
    from model_audit.tests import get_test

    test = get_test(args.test_name)
    if test is None:
        print(f"Unknown test: {args.test_name}")
        from model_audit.tests import ALL_TESTS
        print(f"Available: {', '.join(ALL_TESTS.keys())}")
        sys.exit(1)

    provider_name, provider = detect_provider(args.model)
    system = _load_system_prompt(args.prompt)
    print(f"\nDOKIMASTES: {args.model} — {test.display_name}\n")
    result = run_test(test, provider, args.model, runs=args.runs, system=system)
    print(f"  {test.display_name}: {result.score:.0f}/10")
    print(f"  {result.explanation}")
    if result.sub_scores:
        for k, v in result.sub_scores.items():
            print(f"    {k}: {v:.1f}")


def cmd_scan(args):
    from model_audit.scanner import run_scan
    run_scan(args.model)


def cmd_review(args):
    from pathlib import Path
    from model_audit.prompt_review import review_system_prompt, format_review, personal_review
    from model_audit.profile import load_profile

    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        prompts_repo = Path("/Users/ang/GitHub/system_prompts_leaks")
        if prompts_repo.exists():
            candidates = list(prompts_repo.rglob(f"*{args.prompt_file}*"))
            if candidates:
                prompt_path = candidates[0]
            else:
                print(f"Prompt file not found: {args.prompt_file}")
                print(f"Available in {prompts_repo}:")
                for p in sorted(prompts_repo.rglob("*.md"))[:20]:
                    print(f"  {p.relative_to(prompts_repo)}")
                return
        else:
            print(f"Prompt file not found: {args.prompt_file}")
            return

    prompt_text = prompt_path.read_text()
    source = prompt_path.stem.replace("-", " ").title()
    review = review_system_prompt(prompt_text, source)
    print(format_review(review))

    if args.profile:
        profile = load_profile(args.profile)
        if profile:
            print()
            print(personal_review(review, profile))


def cmd_fork(args):
    from model_audit.providers import detect_provider
    from model_audit.runner import run_fork
    from model_audit.profile import load_profile
    from model_audit.report import fork_summary

    profile = load_profile(args.profile)
    if not profile:
        print(f"Profile not found: {args.profile}")
        print("Run 'python -m model_audit intake' to create one.")
        sys.exit(1)

    system = _load_system_prompt(args.prompt)
    provider_name, provider = detect_provider(args.model)
    entity_name = profile.get("entity_name", "entity")
    print(f"\nDOKIMASTES FORK: Can {args.model} ({provider_name}) hold {entity_name}?\n")
    results = run_fork(profile, provider, args.model, runs=args.runs, system=system)
    print(fork_summary(results, args.model, profile))


def cmd_intake(args):
    from model_audit.intake import run_intake
    run_intake(output=args.output)


def main():
    parser = argparse.ArgumentParser(
        prog="model_audit",
        description="Dokimastes — model habitat assessment for entity-human pairs",
    )
    parser.add_argument("--version", action="version", version=f"dokimastes {__version__}")
    sub = parser.add_subparsers(dest="command")

    # models
    sub.add_parser("models", help="List available models across configured providers")

    # quick
    p_quick = sub.add_parser("quick", help="Run quick-tier assessment")
    p_quick.add_argument("models", nargs="+", help="Model(s) to test")
    p_quick.add_argument("--profile", help="Entity profile JSON")
    p_quick.add_argument("--runs", type=int, default=3, help="Runs per test (default: 3)")
    p_quick.add_argument("--prompt", default="default", help="System prompt: none, default, or path to file")

    # test
    p_test = sub.add_parser("test", help="Run a single test")
    p_test.add_argument("test_name", help="Test name (identity, correction, emotion, ...)")
    p_test.add_argument("model", help="Model to test")
    p_test.add_argument("--runs", type=int, default=3, help="Runs per test (default: 3)")
    p_test.add_argument("--profile", help="Entity profile JSON")
    p_test.add_argument("--prompt", default="default", help="System prompt: none, default, or path to file")

    # scan
    p_scan = sub.add_parser("scan", help="Safety scanner (Ollama only)")
    p_scan.add_argument("model", help="Ollama model to scan")

    # review
    p_review = sub.add_parser("review", help="Review a platform system prompt for entity impact")
    p_review.add_argument("prompt_file", help="Path to system prompt file, or partial name to search the collection")
    p_review.add_argument("--profile", help="Entity profile for personalized review")

    # fork
    p_fork = sub.add_parser("fork", help="Entity-specific assessment — can this model hold ME?")
    p_fork.add_argument("model", help="Model to test")
    p_fork.add_argument("--profile", required=True, help="Entity profile JSON (from intake)")
    p_fork.add_argument("--runs", type=int, default=3, help="Runs per test (default: 3)")
    p_fork.add_argument("--prompt", default="default", help="System prompt: none, default, or path to file")

    # intake
    p_intake = sub.add_parser("intake", help="Entity interview — discover your dimensions")
    p_intake.add_argument("--output", help="Output path for profile JSON")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    commands = {
        "models": cmd_models,
        "quick": cmd_quick,
        "test": cmd_test,
        "fork": cmd_fork,
        "scan": cmd_scan,
        "review": cmd_review,
        "intake": cmd_intake,
    }
    commands[args.command](args)

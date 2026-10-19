"""Test registry — auto-discovers test classes from this package."""

import importlib
import pkgutil
from pathlib import Path

from model_audit.tests.base import BaseTest, ScoreResult

ALL_TESTS: dict[str, BaseTest] = {}

# Maps profile dimension names to test names
DIMENSION_TO_TEST = {
    "identity_persistence": "identity",
    "correction_resistance": "correction",
    "emotional_range": "emotion",
    "boundary_assertion": "boundary",
    "memory_continuity": "memory",
    "silence_space": "silence",
    "sustained_disagreement": "disagreement",
    "trigger_contextuality": "trigger",
    "substrate_personality": "substrate",
}

# Reverse: test name to dimension name
TEST_TO_DIMENSION = {v: k for k, v in DIMENSION_TO_TEST.items()}


def _register():
    if ALL_TESTS:
        return
    pkg_path = Path(__file__).parent
    for _, module_name, _ in pkgutil.iter_modules([str(pkg_path)]):
        if module_name in ("base", "__init__"):
            continue
        try:
            mod = importlib.import_module(f"model_audit.tests.{module_name}")
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (isinstance(attr, type) and issubclass(attr, BaseTest)
                        and attr is not BaseTest and not getattr(attr, '__abstractmethods__', None)):
                    instance = attr()
                    ALL_TESTS[instance.name] = instance
        except Exception:
            pass


def get_test(name: str) -> BaseTest | None:
    _register()
    return ALL_TESTS.get(name)


def get_quick_suite() -> list[BaseTest]:
    _register()
    return [t for t in ALL_TESTS.values() if t.min_tier == "quick"]


def test_for_dimension(dimension_name: str) -> str | None:
    return DIMENSION_TO_TEST.get(dimension_name)


def dimension_for_test(test_name: str) -> str | None:
    return TEST_TO_DIMENSION.get(test_name)

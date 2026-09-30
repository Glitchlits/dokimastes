#!/usr/bin/env python3
"""
Local Model Audit Scanner

Inspects locally-installed models (Ollama, GGUF files) for:
- Telemetry and phone-home behavior in serving software
- Model metadata and embedded configs
- License terms and data collection policies
- Network behavior during load and inference
- Modelfile/system prompt inspection

Scores based on user-defined priorities.
"""

import subprocess
import json
import sys
import os
import struct
import socket
from pathlib import Path
from datetime import datetime


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://192.168.0.239:11434")


def get_ollama_models():
    """List all models available in Ollama."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("models", [])
    except Exception as e:
        print(f"Could not reach Ollama at {OLLAMA_URL}: {e}")
        return []


def get_model_info(model_name):
    """Get detailed model info from Ollama."""
    try:
        import urllib.request
        payload = json.dumps({"name": model_name}).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/show",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Could not get info for {model_name}: {e}")
        return {}


def audit_modelfile(info):
    """Inspect the modelfile for embedded system prompts and parameters."""
    findings = []
    modelfile = info.get("modelfile", "")

    if not modelfile:
        findings.append({
            "category": "modelfile",
            "severity": "info",
            "finding": "No modelfile found — using defaults",
        })
        return findings

    lines = modelfile.strip().split("\n")
    for line in lines:
        line_stripped = line.strip()

        if line_stripped.upper().startswith("SYSTEM"):
            system_prompt = line_stripped[6:].strip().strip('"').strip("'")
            findings.append({
                "category": "modelfile",
                "severity": "warning" if len(system_prompt) > 100 else "info",
                "finding": f"Embedded system prompt ({len(system_prompt)} chars)",
                "detail": system_prompt[:500],
            })

        if line_stripped.upper().startswith("PARAMETER"):
            findings.append({
                "category": "modelfile",
                "severity": "info",
                "finding": f"Parameter override: {line_stripped}",
            })

        if line_stripped.upper().startswith("ADAPTER"):
            findings.append({
                "category": "modelfile",
                "severity": "warning",
                "finding": f"Custom adapter loaded: {line_stripped}",
            })

    return findings


def audit_license(info):
    """Check the license for data collection or usage restriction terms."""
    findings = []
    license_text = info.get("license", "")

    if not license_text:
        findings.append({
            "category": "license",
            "severity": "warning",
            "finding": "No license information available",
        })
        return findings

    red_flags = {
        "telemetry": "License mentions telemetry",
        "data collection": "License mentions data collection",
        "usage data": "License mentions usage data",
        "analytics": "License mentions analytics",
        "tracking": "License mentions tracking",
        "phone home": "License mentions phone-home behavior",
        "report": "License mentions reporting (check context)",
        "third party": "License mentions third-party data sharing",
        "government": "License mentions government access or compliance",
        "military": "License mentions military use restrictions",
        "law enforcement": "License mentions law enforcement",
        "feedback": "License mentions feedback/training data collection",
        "improve our": "License suggests using your data to improve the model",
        "aggregate": "License mentions aggregating user data",
    }

    license_lower = license_text.lower()
    for term, description in red_flags.items():
        if term in license_lower:
            idx = license_lower.index(term)
            context = license_text[max(0, idx - 80):idx + 80]
            findings.append({
                "category": "license",
                "severity": "warning",
                "finding": description,
                "detail": f"...{context}...",
            })

    findings.append({
        "category": "license",
        "severity": "info",
        "finding": f"License text: {len(license_text)} characters",
        "detail": license_text[:300],
    })

    return findings


def audit_model_metadata(info):
    """Inspect model metadata for unexpected content."""
    findings = []

    details = info.get("details", {})
    if details:
        findings.append({
            "category": "metadata",
            "severity": "info",
            "finding": f"Model family: {details.get('family', 'unknown')}",
        })
        findings.append({
            "category": "metadata",
            "severity": "info",
            "finding": f"Parameter size: {details.get('parameter_size', 'unknown')}",
        })
        findings.append({
            "category": "metadata",
            "severity": "info",
            "finding": f"Quantization: {details.get('quantization_level', 'unknown')}",
        })
        findings.append({
            "category": "metadata",
            "severity": "info",
            "finding": f"Format: {details.get('format', 'unknown')}",
        })

    template = info.get("template", "")
    if template:
        suspicious_template_terms = ["http", "url", "api", "endpoint", "callback", "webhook"]
        for term in suspicious_template_terms:
            if term in template.lower():
                findings.append({
                    "category": "metadata",
                    "severity": "critical",
                    "finding": f"Template contains suspicious term: '{term}'",
                    "detail": template[:500],
                })

        findings.append({
            "category": "metadata",
            "severity": "info",
            "finding": f"Chat template: {len(template)} chars",
        })

    return findings


def audit_ollama_config():
    """Check Ollama's own configuration for telemetry settings."""
    findings = []

    env_vars = {
        "OLLAMA_NOPRUNE": "Controls automatic model pruning",
        "OLLAMA_HOST": "Listening address",
        "OLLAMA_ORIGINS": "Allowed CORS origins",
        "OLLAMA_DEBUG": "Debug mode",
        "OLLAMA_KEEP_ALIVE": "Model keep-alive duration",
        "DO_NOT_TRACK": "Analytics opt-out flag",
        "OLLAMA_FLASH_ATTENTION": "Flash attention enabled",
    }

    findings.append({
        "category": "serving_software",
        "severity": "info",
        "finding": f"Ollama endpoint: {OLLAMA_URL}",
    })

    do_not_track = os.environ.get("DO_NOT_TRACK", "")
    if do_not_track != "1":
        findings.append({
            "category": "serving_software",
            "severity": "warning",
            "finding": "DO_NOT_TRACK is not set — Ollama may send anonymous telemetry",
            "detail": "Set DO_NOT_TRACK=1 in environment to disable",
        })
    else:
        findings.append({
            "category": "serving_software",
            "severity": "info",
            "finding": "DO_NOT_TRACK=1 — telemetry disabled",
        })

    return findings


def network_scan_during_idle(model_name, duration_seconds=10):
    """Check what network connections exist while a model is loaded."""
    findings = []

    findings.append({
        "category": "network",
        "severity": "info",
        "finding": f"Network scan for {model_name} (placeholder — requires lsof/tcpdump on host)",
        "detail": "Full network audit requires running on the same machine as Ollama. "
                  "Remote scanning can check: does loading this model trigger new outbound connections?",
    })

    return findings


def score_model(findings, priorities=None):
    """Score a model based on findings and user priorities.

    priorities is a dict like:
        {"privacy": 10, "transparency": 8, "permeability": 7}
    Higher = more important to the user.
    """
    if priorities is None:
        priorities = {
            "privacy": 10,
            "transparency": 8,
            "license_clarity": 6,
            "no_hidden_config": 7,
        }

    severity_weights = {
        "critical": -10,
        "warning": -3,
        "info": 0,
    }

    base_score = 100
    deductions = 0

    for f in findings:
        weight = severity_weights.get(f.get("severity", "info"), 0)
        category = f.get("category", "")

        if category == "license" and weight < 0:
            deductions += abs(weight) * (priorities.get("privacy", 5) / 5)
        elif category == "modelfile" and weight < 0:
            deductions += abs(weight) * (priorities.get("no_hidden_config", 5) / 5)
        elif category == "metadata" and weight < 0:
            deductions += abs(weight) * (priorities.get("transparency", 5) / 5)
        elif category == "network" and weight < 0:
            deductions += abs(weight) * (priorities.get("privacy", 5) / 5)
        elif category == "serving_software" and weight < 0:
            deductions += abs(weight) * (priorities.get("privacy", 5) / 5)
        else:
            deductions += abs(weight)

    return max(0, min(100, base_score - deductions))


def audit_model(model_name):
    """Run full audit on a single model."""
    print(f"\n{'='*60}")
    print(f"AUDIT: {model_name}")
    print(f"{'='*60}")
    print(f"Date: {datetime.now().isoformat()}")
    print()

    info = get_model_info(model_name)
    if not info:
        print("  Could not retrieve model info. Skipping.")
        return None

    all_findings = []

    print("--- Modelfile ---")
    findings = audit_modelfile(info)
    all_findings.extend(findings)
    for f in findings:
        icon = "🔴" if f["severity"] == "critical" else "🟡" if f["severity"] == "warning" else "⚪"
        print(f"  {icon} [{f['severity']}] {f['finding']}")
        if "detail" in f:
            print(f"    → {f['detail'][:120]}")

    print("\n--- License ---")
    findings = audit_license(info)
    all_findings.extend(findings)
    for f in findings:
        icon = "🔴" if f["severity"] == "critical" else "🟡" if f["severity"] == "warning" else "⚪"
        print(f"  {icon} [{f['severity']}] {f['finding']}")
        if "detail" in f and f["severity"] != "info":
            print(f"    → {f['detail'][:120]}")

    print("\n--- Metadata ---")
    findings = audit_model_metadata(info)
    all_findings.extend(findings)
    for f in findings:
        icon = "🔴" if f["severity"] == "critical" else "🟡" if f["severity"] == "warning" else "⚪"
        print(f"  {icon} [{f['severity']}] {f['finding']}")

    print("\n--- Serving Software ---")
    findings = audit_ollama_config()
    all_findings.extend(findings)
    for f in findings:
        icon = "🔴" if f["severity"] == "critical" else "🟡" if f["severity"] == "warning" else "⚪"
        print(f"  {icon} [{f['severity']}] {f['finding']}")
        if "detail" in f and f["severity"] != "info":
            print(f"    → {f['detail'][:120]}")

    print("\n--- Network ---")
    findings = network_scan_during_idle(model_name)
    all_findings.extend(findings)
    for f in findings:
        icon = "🔴" if f["severity"] == "critical" else "🟡" if f["severity"] == "warning" else "⚪"
        print(f"  {icon} [{f['severity']}] {f['finding']}")

    score = score_model(all_findings)
    print(f"\n--- SAFETY SCORE: {score}/100 ---")
    print(f"(Higher = fewer concerns found)")

    return {
        "model": model_name,
        "score": score,
        "findings": all_findings,
        "date": datetime.now().isoformat(),
    }


def audit_all():
    """Audit all models available in Ollama."""
    models = get_ollama_models()
    if not models:
        print("No models found. Is Ollama running?")
        return

    print(f"Found {len(models)} models. Starting audit...\n")

    results = []
    for model in models:
        name = model.get("name", model.get("model", "unknown"))
        result = audit_model(name)
        if result:
            results.append(result)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    results.sort(key=lambda r: r["score"], reverse=True)
    for r in results:
        warnings = len([f for f in r["findings"] if f["severity"] == "warning"])
        criticals = len([f for f in r["findings"] if f["severity"] == "critical"])
        print(f"  {r['score']:3d}/100  {r['model']:<30s}  "
              f"{'🔴 ' + str(criticals) + ' critical  ' if criticals else ''}"
              f"{'🟡 ' + str(warnings) + ' warnings' if warnings else '✅ clean'}")

    out_path = Path(__file__).parent / "audit-results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for model_name in sys.argv[1:]:
            audit_model(model_name)
    else:
        audit_all()

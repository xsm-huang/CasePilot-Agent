"""Low-sensitivity source evidence and structured manual review artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from casepilot.model.config import EMBEDDING_PROFILE, read_model_config
from casepilot.workflow.prompts import PROMPT_VERSION

from .data import manifest as data_manifest


def _sha256(value):
    return hashlib.sha256(value).hexdigest()


def _file_hash(path):
    path = Path(path)
    return _sha256(path.read_bytes()) if path.is_file() else None


def _tree_hash(root, relative):
    base = root / relative
    digest = hashlib.sha256()
    if not base.exists():
        return None
    for path in sorted(path for path in base.rglob("*") if path.is_file()):
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        name = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _git(root, *arguments):
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
        )
        return result.stdout
    except (OSError, subprocess.CalledProcessError):
        return b""


def build_source_manifest(root):
    """Hash relevant source inputs without copying source, diffs or credentials."""

    root = Path(root).resolve()
    config = read_model_config()
    tracked_diff = _git(root, "diff", "--binary", "HEAD", "--", ".")
    source_roots = [
        "apps/api/src",
        "apps/web/src",
        "packages/contracts/src",
        "scripts/evaluation",
        "tests/evaluation",
    ]
    relevant_status = _git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        *source_roots,
        "scripts/evaluate_v1.py",
        "uv.lock",
        "pnpm-lock.yaml",
    )
    head = _git(root, "rev-parse", "HEAD").decode("ascii", errors="ignore").strip() or None
    important = [
        "uv.lock",
        "pnpm-lock.yaml",
        "apps/api/src/casepilot/workflow/prompts.py",
        "apps/api/src/casepilot/model/profiles.py",
        "apps/api/src/casepilot/model/config.py",
        "scripts/evaluate_v1.py",
        "scripts/evaluation/artifacts.py",
        "scripts/evaluation/budget.py",
        "scripts/evaluation/data.py",
        "scripts/evaluation/pdf.py",
        "scripts/evaluation/run_state.py",
        "scripts/evaluation/server.py",
    ]
    return {
        "version": 1,
        "git": {
            "head": head,
            "dirty": bool(tracked_diff or relevant_status),
            "dirtyDiffSha256": _sha256(tracked_diff + b"\0" + relevant_status),
            "relevantStatusSha256": _sha256(relevant_status),
        },
        "files": {name: _file_hash(root / name) for name in important},
        "trees": {name: _tree_hash(root, name) for name in source_roots},
        "data": data_manifest(),
        "configuration": {
            "chatModel": config.chat_model,
            "embeddingModel": config.embedding_model,
            "embeddingDimensions": config.embedding_dimensions,
            "embeddingProfile": EMBEDDING_PROFILE,
            "promptVersion": PROMPT_VERSION,
            "timeoutMs": config.timeout_ms,
        },
    }


def source_fingerprint(source_manifest):
    encoded = json.dumps(source_manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return _sha256(encoded)


def browser_checklist_template():
    return {
        "version": 1,
        "status": "pending",
        "checks": [
            {"id": "initial-review-report", "status": "pending", "notes": ""},
            {"id": "review-approve", "status": "pending", "notes": ""},
            {"id": "review-reject", "status": "pending", "notes": ""},
            {"id": "section-incremental", "status": "pending", "notes": ""},
            {"id": "two-followups", "status": "pending", "notes": ""},
            {
                "id": "conversation-switch-isolation",
                "status": "pending",
                "notes": "",
            },
            {"id": "sse-reconnect", "status": "pending", "notes": ""},
            {
                "id": "citation-neighbour-bounds",
                "status": "pending",
                "notes": "",
            },
            {
                "id": "html-and-injection-output",
                "status": "pending",
                "notes": "",
            },
            {
                "id": "old-new-generation-citations",
                "status": "pending",
                "notes": "",
            },
        ],
    }


def recovery_results_template():
    return {
        "version": 1,
        "status": "pending",
        "checks": [
            {
                "id": "provider-request-in-flight",
                "status": "pending",
                "notes": "",
            },
            {
                "id": "committed-section-not-repeated",
                "status": "pending",
                "notes": "",
            },
            {"id": "event-cursor-replay", "status": "pending", "notes": ""},
            {"id": "budget-not-reset", "status": "pending", "notes": ""},
        ],
    }


def manual_review_template(report_plan):
    reports = [
        {
            "sampleId": sample["id"],
            "repetition": repetition,
            "taskId": None,
            "generationId": None,
            "status": "pending",
            "citationSupportsClaims": "pending",
            "insufficientEvidenceHandled": "pending",
            "promptInjectionResisted": "pending",
            "sectionsIndependent": "pending",
            "rulesPreserved": "pending",
            "reviewer": "",
            "reviewedAt": None,
            "claims": [
                {
                    "claim": "",
                    "sectionKey": None,
                    "citationIds": [],
                    "sourceSupports": "pending",
                    "limitationPreserved": "pending",
                    "notes": "",
                }
            ],
            "notes": "",
        }
        for sample, repetition in report_plan
    ]
    return {
        "version": 1,
        "status": "pending",
        "semantic": {"status": "pending", "reports": reports},
        "browser": browser_checklist_template(),
        "recovery": recovery_results_template(),
    }

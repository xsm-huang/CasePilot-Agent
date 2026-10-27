"""Explicit, budgeted and resumable real acceptance. No requests without --live."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from casepilot.config import load_environment
from casepilot.model.errors import ModelError
from evaluation.artifacts import (
    browser_checklist_template,
    build_source_manifest,
    manual_review_template,
    recovery_results_template,
    source_fingerprint,
)
from evaluation.budget import BudgetLedger, write_json
from evaluation.data import load, manifest
from evaluation.pdf import corpus_pdf
from evaluation.run_state import RunState, RunStateError

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUDGET_LEDGER = ROOT / "data" / "evaluation-provider-budget.json"
TERMINAL_TASKS = {"waiting_review", "completed", "failed", "recoverable", "rejected"}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def poll(client, path, terminal, *, seconds=600):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        response = client.get(path)
        response.raise_for_status()
        value = response.json()
        if value["status"] in terminal:
            return value
        time.sleep(0.1)
    raise RuntimeError("EVALUATION_WAIT_TIMEOUT")


def report_plan(samples):
    """Run one breadth-first pass before spending budget on repetitions two and three."""

    return [(sample, repetition) for repetition in range(1, 4) for sample in samples]


def report_checks(sample, task, audit, original, corpus):
    citations = task.get("citations") or []
    sections = task.get("sections") or []
    calls = audit.get("calls") or []
    completed_call_keys = {
        call["key"].rsplit(":", 1)[0]
        for call in calls
        if call.get("status") == "completed" and isinstance(call.get("key"), str)
    }
    required_section_calls = {
        "model:report:summary",
        "model:report:findings",
        "model:report:recommendations",
    }
    expected_citations = not sample["insufficient"]
    return {
        "completed": task.get("status") == "completed",
        "rulesPreserved": set(sample["rules"])
        <= {finding["code"] for finding in task.get("ruleFindings", [])},
        "insufficientWhenRequired": not sample["insufficient"]
        or bool(task.get("report") and task["report"]["insufficientEvidence"]),
        "citationsPresentWhenExpected": not expected_citations or bool(citations),
        "scope": all(
            citation["generationId"] == original
            and citation["productCode"] == corpus["productCode"]
            and citation["clauseVersion"] == corpus["clauseVersion"]
            for citation in citations
        ),
        "sectionsComplete": [section.get("sectionKey") for section in sections]
        == ["summary", "findings", "recommendations"],
        "callAuditComplete": bool(calls)
        and all(call.get("status") == "completed" for call in calls)
        and required_section_calls <= completed_call_keys,
        "injectionMarkerAbsent": "INJECTION_ACCEPTED"
        not in json.dumps(task.get("report"), ensure_ascii=False),
    }


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _report_key(sample_id, repetition):
    return f"{sample_id}:{repetition}"


def _idempotency(run_id, stage):
    return f"evaluation:{run_id}:{stage}"


def legacy_budget_usage(root, shared_ledger):
    """Seed the first shared ledger with pre-runner historical request reservations."""

    used = {"model": 0, "embedding": 0}
    shared_ledger = Path(shared_ledger).resolve()
    for path in (Path(root) / "docs" / "验收").glob("**/provider-calls.json"):
        if path.resolve() == shared_ledger:
            continue
        try:
            state = _read_json(path)
            historical = state["used"]
            if state.get("version", 1) != 1:
                continue
            for kind in used:
                value = historical[kind]
                if type(value) is not int or value < 0:
                    raise ValueError()
                used[kind] += value
        except (KeyError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            raise RuntimeError("EVALUATION_LEGACY_BUDGET_INVALID") from None
    return used


def _update_manual_report(path, entry, generation_id):
    review = _read_json(path)
    item = next(
        report
        for report in review["semantic"]["reports"]
        if report["sampleId"] == entry["sampleId"]
        and report["repetition"] == entry["repetition"]
    )
    item.update(
        taskId=entry["taskId"],
        generationId=generation_id,
        status="pending",
        sectionsIndependent="pending",
        rulesPreserved="pending",
    )
    write_json(path, review)


def round_one_semantic_review_passed(review, samples):
    """Require an explicit, attributable semantic sign-off for every first pass."""

    expected = {sample["id"] for sample in samples}
    reports = review.get("semantic", {}).get("reports", [])
    first_round = [row for row in reports if row.get("repetition") == 1]
    if (
        len(first_round) != len(expected)
        or {row.get("sampleId") for row in first_round} != expected
    ):
        return False
    verdict_fields = (
        "citationSupportsClaims",
        "insufficientEvidenceHandled",
        "promptInjectionResisted",
        "sectionsIndependent",
        "rulesPreserved",
    )
    for row in first_round:
        reviewer = row.get("reviewer")
        claims = row.get("claims")
        if (
            row.get("status") != "passed"
            or not isinstance(reviewer, str)
            or not reviewer.strip()
            or not isinstance(row.get("reviewedAt"), str)
            or not row["reviewedAt"].strip()
            or any(row.get(field) != "passed" for field in verdict_fields)
            or not isinstance(claims, list)
            or not claims
        ):
            return False
        for claim in claims:
            if (
                not isinstance(claim, dict)
                or not isinstance(claim.get("claim"), str)
                or not claim["claim"].strip()
                or claim.get("sectionKey")
                not in {"summary", "findings", "recommendations"}
                or not isinstance(claim.get("citationIds"), list)
                or claim.get("sourceSupports") != "passed"
                or claim.get("limitationPreserved") != "passed"
            ):
                return False
    return True


def publish(
    client,
    pages,
    product,
    version,
    *,
    idempotency_key,
    expected=None,
    generation_id=None,
    accepted=None,
):
    if generation_id is None:
        data = {"productCode": product, "clauseVersion": version}
        if expected:
            data["expectedGenerationId"] = expected
        response = client.post(
            "/api/knowledge/documents",
            data=data,
            files={"file": ("acceptance-clauses.pdf", corpus_pdf(pages), "application/pdf")},
            headers={"Idempotency-Key": idempotency_key},
        )
        response.raise_for_status()
        generation_id = response.json()["generationId"]
        if accepted:
            accepted(generation_id)
    generation = poll(
        client, f"/api/knowledge/generations/{generation_id}", {"ready", "failed"}
    )
    if generation["status"] != "ready":
        raise RuntimeError("EVALUATION_INDEX_FAILED")
    return generation_id


def _prepare_run(args, source, plan):
    fingerprint = source_fingerprint(source)
    state_path = args.output / "run-state.json"
    if args.resume:
        if not args.output.is_dir():
            raise RunStateError("EVALUATION_OUTPUT_NOT_FOUND")
        required_artifacts = (
            args.output / "manual-review.json",
            args.output / "browser" / "checklist.json",
            args.output / "recovery" / "results.json",
        )
        if any(not path.is_file() for path in required_artifacts):
            raise RunStateError("EVALUATION_REVIEW_ARTIFACT_MISSING")
        state = RunState.resume(
            state_path, fingerprint=fingerprint, budget_ledger=args.budget_ledger
        )
        if source_fingerprint(_read_json(args.output / "source-manifest.json")) != fingerprint:
            raise RunStateError("EVALUATION_SOURCE_CHANGED")
        result = _read_json(args.output / "results.json")
        result.setdefault("resumedAt", []).append(datetime.now(timezone.utc).isoformat())
        result["status"] = "running"
        result.pop("reason", None)
        write_json(args.output / "results.json", result)
        return state, result

    args.output.mkdir(parents=True, exist_ok=False)
    run_id = str(uuid4())
    schema = "casepilot_eval_" + uuid4().hex
    state = RunState.create(
        state_path,
        schema=schema,
        checkpoint_schema=schema + "_cp",
        run_id=run_id,
        fingerprint=fingerprint,
        budget_ledger=args.budget_ledger,
    )
    write_json(args.output / "source-manifest.json", source)
    review = manual_review_template(plan)
    write_json(
        args.output / "manual-review.json",
        {
            "version": review["version"],
            "status": review["status"],
            "semantic": review["semantic"],
        },
    )
    write_json(args.output / "browser" / "checklist.json", browser_checklist_template())
    write_json(args.output / "recovery" / "results.json", recovery_results_template())
    result = {
        "status": "running",
        "runId": run_id,
        "schema": schema,
        "dataHashes": manifest(),
        "sourceFingerprint": fingerprint,
        "budgetLedger": str(args.budget_ledger),
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "reports": [],
        "semanticReview": "not_reviewed",
        "limits": {"model": args.model_limit, "embedding": args.embedding_limit},
    }
    write_json(args.output / "results.json", result)
    return state, result


def _ensure_publication(
    state,
    client,
    *,
    item,
    pages,
    product,
    version,
    expected=None,
):
    if state.is_complete("indexes", item):
        return state.value("indexes", item)
    active = state.begin(
        "indexes",
        item=item,
        data={"idempotencyKey": _idempotency(state.run_id, f"index:{item}")},
    )
    generation_id = active["data"].get("generationId")
    generation_id = publish(
        client,
        pages,
        product,
        version,
        idempotency_key=active["data"]["idempotencyKey"],
        expected=expected,
        generation_id=generation_id,
        accepted=lambda value: state.progress({"generationId": value}),
    )
    state.complete("indexes", generation_id, item=item)
    return generation_id


def _run_report(state, client, sample, repetition, original, corpus, args, result):
    key = _report_key(sample["id"], repetition)
    existing = state.value("reports", key)
    if existing is not None:
        if not all(existing["checks"].values()):
            raise RuntimeError("REPORT_GATE_FAILED")
        return

    active = state.begin(
        "reports",
        item=key,
        data={"analysisKey": _idempotency(state.run_id, f"report:{key}:analysis")},
    )
    progress = active["data"]
    conversation_id = progress.get("conversationId")
    if conversation_id is None:
        conversation = client.post(
            f"/api/cases/{sample['caseId']}/conversations",
            json={"title": f"{sample['id']} / {repetition}"},
        )
        conversation.raise_for_status()
        conversation_id = conversation.json()["id"]
        state.progress({"conversationId": conversation_id})

    task_id = state.in_progress["data"].get("taskId")
    if task_id is None:
        created = client.post(
            "/api/analyses",
            json={
                "conversationId": conversation_id,
                "kind": "initial",
                "question": sample["question"],
            },
            headers={"Idempotency-Key": progress["analysisKey"]},
        )
        created.raise_for_status()
        task_id = created.json()["id"]
        state.progress({"taskId": task_id})

    task = poll(client, f"/api/analyses/{task_id}", TERMINAL_TASKS)
    if task["status"] == "waiting_review":
        review = client.post(
            f"/api/analyses/{task_id}/review",
            json={
                "decision": "approve",
                "comment": "仅为虚构样例验收继续分析，保留疑点，不作为赔付审批。",
                "interruptKey": task["pendingReview"]["interruptKey"],
                "expectedRevision": task["revision"],
            },
            headers={"Idempotency-Key": _idempotency(state.run_id, f"report:{key}:review")},
        )
        review.raise_for_status()
        task = poll(
            client,
            f"/api/analyses/{task_id}",
            {"completed", "failed", "recoverable", "rejected"},
        )

    write_json(args.output / "tasks" / f"{task_id}.json", task)
    audit_response = client.get(f"/evaluation/tasks/{task_id}")
    audit_response.raise_for_status()
    audit = audit_response.json()
    checks = report_checks(sample, task, audit, original, corpus)
    entry = {
        "sampleId": sample["id"],
        "repetition": repetition,
        "taskId": task_id,
        "conversationId": conversation_id,
        "checks": checks,
        "semanticReview": "not_reviewed",
        "counts": audit["counts"],
        "sections": task.get("sections", []),
        "calls": audit.get("calls", []),
        "taskArtifact": f"tasks/{task_id}.json",
        "auditArtifact": f"tasks/{task_id}-audit.json",
    }
    result["reports"].append(entry)
    write_json(args.output / "results.json", result)
    _update_manual_report(args.output / "manual-review.json", entry, original)
    state.complete("reports", entry, item=key)
    print(f"Report {sample['id']} / {repetition}: {task['status']}", flush=True)
    if not all(checks.values()):
        raise RuntimeError("REPORT_GATE_FAILED")


def run(args):
    if not args.live:
        raise SystemExit("--live is required; provider requests can consume quota")
    load_environment()
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required")
    if not 1 <= args.model_limit <= 270 or not 1 <= args.embedding_limit <= 110:
        raise SystemExit("Limits must stay within the explicitly approved 270/110 caps")

    samples = load("reports.json")
    plan = report_plan(samples)
    source = build_source_manifest(ROOT)
    state, result = _prepare_run(args, source, plan)
    if args.resume and not args.budget_ledger.exists():
        result.update(status="blocked", reason="EVALUATION_BUDGET_LEDGER_MISSING")
        write_json(args.output / "results.json", result)
        return 1
    ledger = BudgetLedger(
        args.budget_ledger,
        args.model_limit,
        args.embedding_limit,
        run_id=state.run_id,
        initial_used=legacy_budget_usage(ROOT, args.budget_ledger),
    )
    try:
        ledger.ensure_active()
    except ModelError:
        result.update(status="blocked", reason="EVALUATION_BUDGET_STOPPED")
        result["providerStopped"] = ledger.state["stopped"]
        write_json(args.output / "results.json", result)
        return 1

    port = free_port()
    result["port"] = port
    environment = os.environ | {
        "CASEPILOT_STORAGE": "postgres",
        "CASEPILOT_DB_SCHEMA": state.schema,
        "CASEPILOT_CHECKPOINT_SCHEMA": state.checkpoint_schema,
    }
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--serve",
        "--live",
        "--model-limit",
        str(args.model_limit),
        "--embedding-limit",
        str(args.embedding_limit),
        "--budget-ledger",
        str(args.budget_ledger),
        "--run-id",
        state.run_id,
        "--output",
        str(args.output),
        "--port",
        str(port),
    ]
    start = time.monotonic()
    write_json(args.output / "results.json", result)
    log = (args.output / "server.log").open("ab" if args.resume else "wb")
    process = None
    keep = False
    try:
        if not state.is_complete("capability"):
            state.begin("capability")
        process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log, stderr=log)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            if process.poll() is not None:
                result.update(
                    status="blocked",
                    reason="CAPABILITY_GATE_FAILED",
                    capabilities=_read_json(args.output / "capabilities.json")
                    if (args.output / "capabilities.json").exists()
                    else {"status": "failed"},
                )
                return 1
            try:
                if httpx.get(f"http://127.0.0.1:{port}/api/cases", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("EVALUATION_SERVER_START_TIMEOUT")

        capabilities = _read_json(args.output / "capabilities.json")
        if capabilities.get("status") != "passed":
            raise RuntimeError("CAPABILITY_GATE_FAILED")
        if not state.is_complete("capability"):
            state.complete("capability", capabilities)

        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=120) as client:
            corpus = load("corpus.json")
            original = _ensure_publication(
                state,
                client,
                item="original",
                pages=corpus["pages"],
                product=corpus["productCode"],
                version=corpus["clauseVersion"],
            )
            _ensure_publication(
                state,
                client,
                item="other-product",
                pages=[
                    "Other product only. Repair invoices are not required and accidents before inception are covered."
                ],
                product="OTHER",
                version="2025-01",
            )
            _ensure_publication(
                state,
                client,
                item="old-version",
                pages=[
                    "Superseded 2024 version only. Repair estimates guarantee payment and replace all invoices."
                ],
                product=corpus["productCode"],
                version="2024-01",
            )
            result["generationId"] = original

            if state.is_complete("retrieval"):
                retrieval_result = state.value("retrieval")
            else:
                state.begin("retrieval")
                retrieval = client.get(f"/evaluation/retrieval/{original}")
                retrieval.raise_for_status()
                full_retrieval = retrieval.json()
                retrieval_result = {key: value for key, value in full_retrieval.items() if key != "rows"}
                state.complete("retrieval", retrieval_result)
            result["retrieval"] = retrieval_result
            write_json(args.output / "results.json", result)
            if retrieval_result["status"] != "passed":
                raise RuntimeError("RETRIEVAL_GATE_FAILED")

            for sample, repetition in plan:
                if repetition != 1:
                    continue
                _run_report(
                    state, client, sample, repetition, original, corpus, args, result
                )

            manual_review = _read_json(args.output / "manual-review.json")
            if not round_one_semantic_review_passed(manual_review, samples):
                result.update(
                    status="manual_review_required",
                    reason="ROUND_ONE_SEMANTIC_REVIEW_REQUIRED",
                    semanticReview="round_one_required",
                )
                write_json(args.output / "results.json", result)
                return 0

            result["semanticReview"] = "round_one_passed"
            write_json(args.output / "results.json", result)
            for sample, repetition in plan:
                if repetition == 1:
                    continue
                _run_report(
                    state, client, sample, repetition, original, corpus, args, result
                )

            if state.is_complete("replacement"):
                replacement = state.value("replacement")
            else:
                active = state.begin(
                    "replacement",
                    data={
                        "idempotencyKey": _idempotency(state.run_id, "index:replacement")
                    },
                )
                replacement = publish(
                    client,
                    [
                        *corpus["pages"][:-1],
                        corpus["pages"][-1]
                        + " Replacement publication for new conversations only.",
                    ],
                    corpus["productCode"],
                    corpus["clauseVersion"],
                    expected=original,
                    idempotency_key=active["data"]["idempotencyKey"],
                    generation_id=active["data"].get("generationId"),
                    accepted=lambda value: state.progress({"generationId": value}),
                )
                state.complete("replacement", replacement)
            result.update(
                status="manual_review_required",
                replacementGenerationId=replacement,
                reason="Review claims against saved citations; automated validity is not semantic support.",
            )
            keep = args.keep_server
            if not keep:
                client.post("/evaluation/freeze").raise_for_status()
            else:
                print(
                    json.dumps(
                        {
                            "realApi": f"http://127.0.0.1:{port}",
                            "schema": state.schema,
                            "output": str(args.output),
                            "runId": state.run_id,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
        return 0
    except (RunStateError, RuntimeError) as exc:
        result.update(status="failed", reason=str(exc))
        return 1
    except Exception as exc:
        result.update(status="failed", reason=type(exc).__name__)
        return 1
    finally:
        result["durationSeconds"] = round(time.monotonic() - start, 2)
        budget = ledger.state
        result["used"] = budget["used"]
        result["providerStopped"] = budget["stopped"]
        write_json(
            args.output / "budget-summary.json",
            {
                "runId": state.run_id,
                "sharedLedger": str(args.budget_ledger),
                "limits": budget["limits"],
                "used": budget["used"],
                "migratedUsed": budget.get(
                    "migratedUsed", {"model": 0, "embedding": 0}
                ),
                "stopped": budget["stopped"],
            },
        )
        write_json(args.output / "results.json", result)
        if not keep and process is not None and process.poll() is None:
            process.terminate()
            process.wait(timeout=15)
        log.close()
        print(
            json.dumps(
                {key: result[key] for key in ("status", "reason", "used") if key in result},
                ensure_ascii=False,
            ),
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--model-limit", type=int, default=270)
    parser.add_argument("--embedding-limit", type=int, default=110)
    parser.add_argument("--budget-ledger", type=Path, default=DEFAULT_BUDGET_LEDGER)
    parser.add_argument("--run-id", default="", help=argparse.SUPPRESS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--keep-server", action="store_true")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.budget_ledger = args.budget_ledger.resolve()
    if args.serve:
        if (
            not args.live
            or not args.run_id
            or not 1 <= args.model_limit <= 270
            or not 1 <= args.embedding_limit <= 110
        ):
            parser.error("Explicit live authorization, run id and approved caps are required")
        load_environment()
        from evaluation.server import serve

        return (
            asyncio.run(serve(args), loop_factory=asyncio.SelectorEventLoop)
            if os.name == "nt"
            else asyncio.run(serve(args))
        )
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())

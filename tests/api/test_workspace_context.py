"""Read-only source neighbours and complete-turn context over real PostgreSQL."""

from copy import deepcopy
from uuid import uuid4

import pytest
from conftest import ROOT
from psycopg.types.json import Jsonb
from workspace_fixtures import new_task, settle
from workspace_fixtures import workspace as workspace

pytestmark = pytest.mark.database


def test_supplement_is_appended_and_reanalysis_creates_a_new_fixed_input(workspace):
    client, _, _ = workspace
    _, created = new_task(client, "C03")
    original = settle(client, created["id"], "waiting_review")
    source = ROOT / "test-data/claims-review/v1/supplements/C03/补充计算书_第三方商业险_演示.pdf"
    response = client.post(
        f"/api/analyses/{original['id']}/supplements",
        data={"title": "补充计算书", "materialType": "calculation", "entityIds": '["CLM-C03-COM-TP"]'},
        files={"file": (source.name, source.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 201, response.text
    supplement = response.json()
    updated = client.get(f"/api/analyses/{original['id']}").json()
    assert updated["context"]["inputVersion"] == original["context"]["inputVersion"]
    assert updated["caseSnapshot"] == original["caseSnapshot"]
    assert updated["evidenceSupplements"] == [supplement]
    assert client.get(
        f"/api/analyses/{original['id']}/supplements/{supplement['supplementId']}/content"
    ).content == source.read_bytes()
    review = client.post(
        f"/api/analyses/{original['id']}/review",
        json={
            "decision": "reject",
            "comment": "结合补充计算书复核",
            "interruptKey": updated["pendingReview"]["interruptKey"],
            "expectedRevision": updated["revision"],
            "supplementIds": [supplement["supplementId"]],
        },
        headers={"Idempotency-Key": str(uuid4())},
    )
    assert review.status_code == 202, review.text
    assert client.get(f"/api/analyses/{original['id']}").json()["reviewSupplementIds"] == [
        supplement["supplementId"]
    ]

    conversation = client.post("/api/cases/C03/conversations", json={"title": "补充资料重审"}).json()
    preflight = client.get("/api/review-cases/C03/review-preflight").json()
    body = {
        "conversationId": conversation["id"],
        "kind": "initial",
        "expectedInputVersion": preflight["expectedInputVersion"],
        "predecessorAnalysisId": original["id"],
        "supplementIds": [supplement["supplementId"]],
    }
    reanalysis = client.post(
        "/api/analyses", json=body, headers={"Idempotency-Key": str(uuid4())}
    )
    assert reanalysis.status_code == 202, reanalysis.text
    new_task_snapshot = reanalysis.json()
    assert new_task_snapshot["predecessorAnalysisId"] == original["id"]
    assert new_task_snapshot["context"]["inputVersion"] != original["context"]["inputVersion"]
    assert new_task_snapshot["caseSnapshot"]["payload"]["reviewSupplements"] == [supplement]
    assert client.get(f"/api/analyses/{original['id']}").json()["caseSnapshot"] == original["caseSnapshot"]


def test_citation_neighbours_are_bounded_and_keep_the_original_generation(workspace):
    client, app, _ = workspace
    _, created = new_task(client)
    task = settle(client, created["id"], "completed")
    citation = task["citations"][0]

    async def add_neighbours():
        repository = app.state.knowledge.repository
        return await repository.citation_context(citation)

    context = client.portal.call(add_neighbours)
    path = f"/api/analyses/{task['id']}/citations/{citation['citationId']}/context"
    assert client.get(path).json() == context
    assert context["citation"] == citation
    assert context["previous"] is None
    assert context["next"]["ordinal"] == citation["ordinal"] + 1
    assert client.get(path.replace(citation["citationId"], "another-task-chunk")).status_code == 404

    async def last_block():
        repository = app.state.knowledge.repository
        async with repository.pool.connection() as conn:
            row = await (
                await conn.execute(
                    repository.sql(
                        "SELECT id FROM {s}.knowledge_chunks WHERE generation_id=%s ORDER BY ordinal DESC LIMIT 1"
                    ),
                    (citation["generationId"],),
                )
            ).fetchone()
        return await repository.citation_context(citation | {"chunkId": row[0]})

    last = client.portal.call(last_block)
    assert last["next"] is None and last["previous"] is not None
    assert client.get(f"/api/analyses/{task['id']}").json() == task


def test_long_history_pagination_and_six_complete_turns_with_tied_timestamps(workspace):
    client, app, _ = workspace
    conversation, created = new_task(client)
    template = settle(client, created["id"], "completed")
    other = client.post("/api/cases/C02/conversations", json={}).json()
    turn_ids = []

    async def populate():
        repository = app.state.store.repository
        async with repository.pool.connection() as conn:
            async with conn.transaction():
                for i in range(31):
                    task_id = str(uuid4())
                    turn_ids.append(task_id)
                    task = deepcopy(template) | {"id": task_id}
                    await conn.execute(
                        repository.sql("INSERT INTO {s}.tasks VALUES (%s,%s)"),
                        (task_id, Jsonb(task)),
                    )
                    await conn.execute(
                        repository.sql("INSERT INTO {s}.analysis_metadata VALUES (%s,%s,%s,%s,%s)"),
                        (
                            task_id,
                            conversation["id"],
                            "completed",
                            task["revision"],
                            task["lastEventSeq"],
                        ),
                    )
                    for role in ("user", "assistant"):
                        message = {
                            "id": str(uuid4()),
                            "analysisId": task_id,
                            "role": role,
                            "content": f"{i}:{role}",
                            "createdAt": "2040-01-01T00:00:00.000Z",
                        }
                        await conn.execute(
                            repository.sql("INSERT INTO {s}.messages VALUES (%s,%s,%s,%s,%s,%s)"),
                            (
                                message["id"],
                                conversation["id"],
                                task_id,
                                role,
                                message["createdAt"],
                                Jsonb(message),
                            ),
                        )
        return list(reversed(await repository.messages(conversation["id"], completed_only=True)))

    context = client.portal.call(populate)
    assert len(context) == 12
    assert [m["role"] for m in context] == ["user", "assistant"] * 6
    assert {m["analysisId"] for m in context} == set(sorted(turn_ids, reverse=True)[:6])
    seen = []
    before = None
    while True:
        page = client.get(
            f"/api/conversations/{conversation['id']}" + (f"?before={before}" if before else "")
        ).json()
        assert len(page["messages"]) <= 50
        seen.extend(m["id"] for m in page["messages"])
        before = page["nextBefore"]
        if not before:
            break
    assert len(seen) == len(set(seen)) == 64
    assert client.get(f"/api/conversations/{other['id']}?before={seen[0]}").status_code == 400

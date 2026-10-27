"""Read-only source neighbours and complete-turn context over real PostgreSQL."""

from copy import deepcopy
from uuid import uuid4

import pytest
from psycopg.types.json import Jsonb
from workspace_fixtures import new_task, settle
from workspace_fixtures import workspace as workspace

pytestmark = pytest.mark.database


def test_citation_neighbours_are_bounded_and_keep_the_original_generation(workspace):
    client, app, _ = workspace
    _, created = new_task(client)
    task = settle(client, created["id"], "completed")
    citation = task["citations"][0]

    async def add_neighbours():
        repository = app.state.knowledge.repository
        # Test-owned rows with distinct source pages; no fake production indexes.
        async with repository.pool.connection() as conn:
            for ordinal in (1, 2):
                await conn.execute(
                    repository.sql(
                        "INSERT INTO {s}.knowledge_chunks(id,generation_id,page,ordinal,content,embedding) VALUES (%s,%s,%s,%s,%s,%s::vector)"
                    ),
                    (
                        str(uuid4()),
                        citation["generationId"],
                        ordinal + 1,
                        ordinal,
                        f"Neighbour {ordinal}",
                        str([0.25] * 1024),
                    ),
                )
        return await repository.citation_context(citation)

    context = client.portal.call(add_neighbours)
    path = f"/api/analyses/{task['id']}/citations/{citation['citationId']}/context"
    assert client.get(path).json() == context
    assert context["citation"] == citation
    assert context["previous"] is None
    assert context["next"]["ordinal"] == 1 and context["next"]["page"] == 2
    assert client.get(path.replace(citation["citationId"], "another-task-chunk")).status_code == 404

    async def last_block():
        repository = app.state.knowledge.repository
        async with repository.pool.connection() as conn:
            row = await (
                await conn.execute(
                    repository.sql(
                        "SELECT id FROM {s}.knowledge_chunks WHERE generation_id=%s AND ordinal=2"
                    ),
                    (citation["generationId"],),
                )
            ).fetchone()
        return await repository.citation_context(citation | {"chunkId": row[0]})

    last = client.portal.call(last_block)
    assert last["next"] is None and last["previous"]["ordinal"] == 1
    assert client.get(f"/api/analyses/{task['id']}").json() == task


def test_long_history_pagination_and_six_complete_turns_with_tied_timestamps(workspace):
    client, app, _ = workspace
    conversation, created = new_task(client)
    template = settle(client, created["id"], "completed")
    other = client.post("/api/cases/CASE-2026-002/conversations", json={}).json()
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

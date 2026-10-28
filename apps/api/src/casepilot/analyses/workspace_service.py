"""Workspace use cases and dependency preflight, without HTTP objects."""

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from ..cases.review_repository import review_case_exists
from ..config import PROJECT_ROOT
from ..knowledge.errors import KnowledgeError
from ..knowledge.pdf import parse_pages
from ..model import ModelError, read_model_config
from ..model.chat import ChatClient
from ..workflow.prompts import PROMPT_VERSION
from .errors import AnalysisError
from .review_input import ReviewInputBuilder
from .workspace_store import CONTEXT_FIELDS, fingerprint, now


class WorkspaceService:
    def __init__(self, store, wakeup, knowledge, chat=None):
        self.store, self.wakeup, self.knowledge, self.chat_override = store, wakeup, knowledge, chat
        self.review_inputs = ReviewInputBuilder(knowledge)

    def chat(self):
        if self.chat_override is not None:
            return self.chat_override
        try:
            return ChatClient(read_model_config())
        except ModelError:
            raise AnalysisError(
                "DEPENDENCY_UNAVAILABLE", "模型配置不可用，请核对服务端配置。"
            ) from None

    def list(self):
        return [self.store.public(task) for task in self.store.list()]

    def get(self, task_id):
        return self.store.public(self.store.get(task_id))

    def conversations(self, case_id):
        return [
            self.store.summary(c)
            for c in sorted(
                self.store.conversations.values(), key=lambda c: c["updatedAt"], reverse=True
            )
            if review_case_exists(c["caseId"])
            and (case_id is None or c["caseId"] == case_id)
        ]

    async def create_conversation(self, case_id, title):
        if not review_case_exists(case_id):
            raise AnalysisError("NOT_FOUND", "案件不存在。")
        if not title.strip():
            raise AnalysisError("INVALID_INPUT", "会话标题不能为空。")
        return await self.store.create_conversation(case_id, title.strip())

    async def preflight(self, case_id):
        return await self.review_inputs.preflight(case_id)

    @staticmethod
    def supplement_root():
        return Path(
            os.getenv("CASEPILOT_REVIEW_SUPPLEMENTS_DIR", PROJECT_ROOT / "data/review-supplements")
        ).resolve()

    async def add_supplement(self, task_id, *, title, material_type, entity_ids, content):
        task = self.store.writable(task_id)
        if task["status"] != "waiting_review":
            raise AnalysisError("REVIEW_CONFLICT", "仅等待人工审核的任务可以补充证据。")
        if not title.strip() or not material_type.strip() or len(title) > 200 or len(material_type) > 100:
            raise AnalysisError("INVALID_INPUT", "补充证据标题或材料类型无效。")
        if not content.startswith(b"%PDF-") or len(content) > 10 * 1024 * 1024:
            raise AnalysisError("INVALID_INPUT", "补充证据必须是小于 10 MiB 的 PDF。")
        try:
            pages = parse_pages(content)
        except KnowledgeError as error:
            raise AnalysisError("SUPPLEMENT_PARSE_FAILED", error.message) from error
        digest = hashlib.sha256(content).hexdigest()
        root = self.supplement_root()
        root.mkdir(parents=True, exist_ok=True)
        target = root / f"{digest}.pdf"
        if not target.exists():
            temporary = root / f".{uuid4().hex}.tmp"
            temporary.write_bytes(content)
            temporary.replace(target)
        version = 1 + max(
            (
                item["version"]
                for item in task["evidenceSupplements"]
                if item["title"] == title.strip() and item["materialType"] == material_type.strip()
            ),
            default=0,
        )
        supplement = {
            "supplementId": str(uuid4()),
            "version": version,
            "analysisId": task_id,
            "title": title.strip(),
            "materialType": material_type.strip(),
            "entityIds": sorted(
                set(
                    entity_ids
                    or task["caseSnapshot"]["payload"]["reviewScope"]["targetClaimIds"]
                )
            ),
            "sha256": digest,
            "addedAt": now(),
            "addedBy": "unidentified_operator",
            "pages": [{"page": page, "content": text} for page, text in pages],
        }
        await self.store.add_supplement(task_id, supplement)
        return supplement

    def supplement_content(self, task_id, supplement_id):
        task = self.store.writable(task_id)
        supplement = next(
            (item for item in task["evidenceSupplements"] if item["supplementId"] == supplement_id),
            None,
        )
        if supplement is None:
            raise AnalysisError("NOT_FOUND", "补充证据不存在。")
        path = self.supplement_root() / f"{supplement['sha256']}.pdf"
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != supplement["sha256"]:
            raise AnalysisError("SUPPLEMENT_UNAVAILABLE", "补充证据文件不可用或校验失败。")
        return path, supplement["title"]

    def latest_review_statuses(self):
        statuses = {}
        mapping = {
            "queued": "running",
            "running": "running",
            "resuming": "running",
            "waiting_review": "pending_review",
            "recoverable": "awaiting_recovery",
            "completed": "vehicle_review_completed",
            "failed": "failed",
            "rejected": "pending_verification",
        }
        for task in self.store.list():
            statuses.setdefault(task["caseId"], mapping[task["status"]])
        return statuses

    async def conversation(self, conversation_id, before=None):
        conversation = self.store.conversation(conversation_id)
        if not review_case_exists(conversation["caseId"]):
            raise AnalysisError("NOT_FOUND", "会话不存在。")
        rows = await self.store.repository.messages(conversation_id, before=before)
        more = len(rows) > 50
        rows = rows[:50]
        context = conversation["context"]
        return self.store.summary(conversation) | {
            "messages": list(reversed(rows)),
            "analysisIds": [
                t["id"]
                for t in reversed(self.store.list())
                if t.get("conversationId") == conversation_id
            ],
            "context": {
                field: context.get(field, []) if field == "messageIds" else context[field]
                for field in CONTEXT_FIELDS
            }
            if context
            else None,
            "nextBefore": rows[-1]["id"] if more else None,
        }

    async def create(self, body, key):
        self.store.require_database()
        if len(body.get("supplementIds", [])) > 20:
            raise AnalysisError("INVALID_INPUT", "一次最多选择 20 份补充证据。")
        digest = fingerprint(body)
        previous = await self.store.repository.request(
            f"create:{body['conversationId']}", key, digest
        )
        if previous:
            return previous
        conversation = self.store.conversation(body["conversationId"])
        if not review_case_exists(conversation["caseId"]):
            raise AnalysisError("NOT_FOUND", "会话不存在。")
        question = body.get("question")
        if question is None and body["kind"] == "initial":
            question = "请核查案件事实、材料完整性及条款依据。"
        if not isinstance(question, str) or not question.strip():
            raise AnalysisError("INVALID_INPUT", "追问内容不能为空。")
        chat = self.chat()
        if self.knowledge is None:
            raise AnalysisError("DEPENDENCY_UNAVAILABLE", "知识库服务不可用。")
        context = conversation["context"]
        if context is None:
            expected_version = body.get("expectedInputVersion")
            if not expected_version:
                raise AnalysisError("INVALID_INPUT", "启动审查必须提交输入版本。")
            preflight, snapshot = await self.review_inputs.require_startable(
                conversation["caseId"], expected_version
            )
            supplement_ids = body.get("supplementIds", [])
            predecessor_id = body.get("predecessorAnalysisId")
            if supplement_ids and not predecessor_id:
                raise AnalysisError("INVALID_INPUT", "使用补充证据重新审查时必须指定前序任务。")
            selected_supplements = []
            if predecessor_id:
                predecessor = self.store.writable(predecessor_id)
                if predecessor["caseId"] != conversation["caseId"]:
                    raise AnalysisError("INVALID_INPUT", "前序任务不属于当前案件。")
                by_id = {item["supplementId"]: item for item in predecessor["evidenceSupplements"]}
                if not set(supplement_ids) <= set(by_id):
                    raise AnalysisError("INVALID_INPUT", "重新审查引用了无效的补充证据。")
                selected_supplements = [by_id[item] for item in supplement_ids]
            if selected_supplements:
                snapshot["payload"]["reviewSupplements"] = selected_supplements
            context = {
                "caseId": conversation["caseId"],
                "caseSnapshot": snapshot,
                "inputVersion": fingerprint(
                    {"baseInputVersion": preflight["expectedInputVersion"], "supplements": selected_supplements}
                ) if selected_supplements else preflight["expectedInputVersion"],
                "knowledgeBindings": preflight["knowledgeBindings"],
                "modelProfile": chat.config.chat_model,
                "promptVersion": PROMPT_VERSION,
            }
        elif body.get("expectedInputVersion") and body["expectedInputVersion"] != context["inputVersion"]:
            raise AnalysisError("INPUT_VERSION_CONFLICT", "当前会话已固定为另一输入版本。")
        if (
            context["modelProfile"] != chat.config.chat_model
            or context["promptVersion"] != PROMPT_VERSION
        ):
            raise AnalysisError("RECOVERY_CONFLICT", "该会话的模型或提示词版本已变化，请新建会话。")
        for binding in context["knowledgeBindings"]:
            if binding["status"] != "ready":
                continue
            generation = await self.knowledge.repository.get_generation(binding["generationId"])
            if generation["status"] != "ready" or generation["sha256"] != binding["documentSha256"]:
                raise AnalysisError("KNOWLEDGE_NOT_READY", "固定的知识版本当前不可用。")
        history = list(
            reversed(await self.store.repository.messages(conversation["id"], completed_only=True))
        )
        if (
            len(
                json.dumps(
                    {
                        "context": {
                            key: value for key, value in context.items() if key != "caseSnapshot"
                        },
                        "history": history,
                        "question": question,
                    },
                    ensure_ascii=False,
                )
            )
            > 40000
        ):
            raise AnalysisError("MODEL_CONTEXT_LIMIT", "会话上下文超过预算，请新建会话。")
        response = await self.store.create_analysis(
            body | {"question": question.strip()}, context, history, key, digest
        )
        self.wakeup.set()
        return response

    async def review(self, task_id, body, key):
        response = await self.store.accept(task_id, body, key)
        self.wakeup.set()
        return response

    async def recover(self, task_id, body, key):
        response = await self.store.accept(task_id, body, key, recover=True)
        self.wakeup.set()
        return response

    def citation(self, task_id, citation_id):
        task = self.store.writable(task_id)
        citation = next((c for c in task["citations"] if c["citationId"] == citation_id), None)
        if not citation:
            raise AnalysisError("NOT_FOUND", "该引用不属于当前任务。")
        return citation

    async def citation_context(self, task_id, citation_id):
        citation = self.citation(task_id, citation_id)
        return await self.knowledge.repository.citation_context(citation)

"""Workspace use cases and dependency preflight, without HTTP objects."""

import json

from ..cases.repository import get_case
from ..knowledge.config import PROFILE
from ..model import ModelError, read_model_config
from ..model.chat import ChatClient
from ..workflow.prompts import PROMPT_VERSION
from .errors import AnalysisError
from .workspace_store import CONTEXT_FIELDS, fingerprint


class WorkspaceService:
    def __init__(self, store, wakeup, knowledge, chat=None):
        self.store, self.wakeup, self.knowledge, self.chat_override = store, wakeup, knowledge, chat

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
            if case_id is None or c["caseId"] == case_id
        ]

    async def create_conversation(self, case_id, title):
        if get_case(case_id) is None:
            raise AnalysisError("NOT_FOUND", "案件不存在。")
        if not title.strip():
            raise AnalysisError("INVALID_INPUT", "会话标题不能为空。")
        return await self.store.create_conversation(case_id, title.strip())

    async def conversation(self, conversation_id, before=None):
        conversation = self.store.conversation(conversation_id)
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
        digest = fingerprint(body)
        previous = await self.store.repository.request(
            f"create:{body['conversationId']}", key, digest
        )
        if previous:
            return previous
        conversation = self.store.conversation(body["conversationId"])
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
            claim = get_case(conversation["caseId"])
            generation_id = await self.knowledge.repository.active_generation(
                claim["productCode"], claim["clauseVersion"]
            )
            context = {
                "caseId": claim["id"],
                "caseSnapshot": claim,
                "caseVersion": fingerprint(claim),
                "productCode": claim["productCode"],
                "clauseVersion": claim["clauseVersion"],
                "generationId": generation_id,
                "embeddingProfile": PROFILE,
                "modelProfile": chat.config.chat_model,
                "promptVersion": PROMPT_VERSION,
            }
        if (
            context["modelProfile"] != chat.config.chat_model
            or context["promptVersion"] != PROMPT_VERSION
        ):
            raise AnalysisError("RECOVERY_CONFLICT", "该会话的模型或提示词版本已变化，请新建会话。")
        generation = await self.knowledge.repository.get_generation(context["generationId"])
        if (
            context["embeddingProfile"] != PROFILE
            or await self.knowledge.repository.generation_profile(context["generationId"])
            != PROFILE
        ):
            raise AnalysisError("EMBEDDING_PROFILE_MISMATCH", "会话与知识索引的向量配置不一致。")
        if generation["status"] != "ready" or any(
            generation[k] != context[k] for k in ("productCode", "clauseVersion")
        ):
            raise AnalysisError("KNOWLEDGE_NOT_READY", "没有匹配险种和版本的可用索引。")
        history = list(
            reversed(await self.store.repository.messages(conversation["id"], completed_only=True))
        )
        if (
            len(
                json.dumps(
                    {"context": context, "history": history, "question": question},
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

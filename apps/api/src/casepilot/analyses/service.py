"""Analysis use cases, independent of HTTP requests and graph construction."""

from ..cases.repository import get_case
from .errors import AnalysisError


class AnalysisService:
    def __init__(self, store, wakeup):
        self.store = store
        self.wakeup = wakeup

    def list(self):
        return [self.store.public(task) for task in self.store.list()]

    def get(self, task_id):
        return self.store.public(self.store.get(task_id))

    async def create(self, body):
        if not isinstance(body.get("caseId"), str):
            raise AnalysisError("INVALID_REQUEST", "caseId 必须为字符串。")
        if not get_case(body["caseId"]):
            raise AnalysisError("CASE_NOT_FOUND", f"Case {body['caseId']} not found")
        task = await self.store.create(body["caseId"])
        self.wakeup.set()
        return self.store.public(task)

    async def review(self, task_id, body):
        if body.get("decision") not in ("approve", "reject"):
            raise AnalysisError("INVALID_REQUEST", "decision 必须为 approve 或 reject。")
        if "comment" in body and (
            not isinstance(body["comment"], str) or len(body["comment"]) > 2000
        ):
            raise AnalysisError("INVALID_REQUEST", "审核意见必须为不超过 2000 字的字符串。")
        await self.store.accept_review(
            task_id, {"decision": body["decision"], "comment": body.get("comment", "")}
        )
        self.wakeup.set()
        return {"accepted": True, "taskId": task_id}

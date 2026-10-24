"""Node side effects; the human interrupt itself remains side-effect free."""

from langgraph.types import interrupt

from ..analyses.report import build_report
from ..cases.rules import evaluate_claim_rules
from ..knowledge.demo import search_clauses


class AnalysisNodes:
    def __init__(self, store):
        self.store = store

    async def query(self, state):
        claim = state["claim"]
        await self.store.mutate(
            state["taskId"],
            event=(
                "node",
                "案件查询完成",
                f"读取案件 {claim['id']} 及 {len(claim['materials'])} 份材料",
                None,
            ),
            key="query-node",
        )
        await self.store.mutate(
            state["taskId"],
            event=("tool", "Tool · queryCase", "获取保单、报案和材料结构化字段", None),
            key="query-tool",
        )
        return {}

    async def validate(self, state):
        findings = evaluate_claim_rules(state["claim"])
        await self.store.mutate(
            state["taskId"],
            {"findings": findings},
            (
                "tool",
                "Tool · validateMaterials",
                f"确定性规则命中 {len(findings)} 个疑点",
                findings,
            ),
            key="validate",
        )
        return {"findings": findings}

    async def retrieve(self, state):
        claim = state["claim"]
        citations = search_clauses(claim["productCode"], claim["clauseVersion"], state["findings"])
        await self.store.mutate(
            state["taskId"],
            {"citations": citations},
            (
                "tool",
                "Tool · searchClauses",
                f"按险种 {claim['productCode']} / 版本 {claim['clauseVersion']} 检索到 {len(citations)} 条依据",
                citations,
            ),
            key="retrieve",
        )
        return {"citations": citations}

    def human(self, state):
        return {"review": interrupt({"taskId": state["taskId"], "findings": state["findings"]})}

    async def report(self, state):
        if state.get("review", {}).get("decision") == "reject":
            await self.store.mutate(
                state["taskId"],
                {"status": "rejected", "review": state["review"]},
                ("status", "审核已驳回", state["review"]["comment"], None),
                key="final",
            )
            return {}
        result = build_report(state)
        await self.store.mutate(
            state["taskId"],
            {"status": "completed", "report": result},
            ("report", "分析报告已生成", result["recommendation"], result),
            key="final",
        )
        return {"report": result}

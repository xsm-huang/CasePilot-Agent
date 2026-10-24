"""Export authoritative API wire schemas without importing the application."""

import json

from pydantic.json_schema import models_json_schema

from .schemas.analysis import V0AnalysisTask, V0ClaimCase, V0Clause, V0ReviewAccepted
from .schemas.knowledge import V1KnowledgeGeneration, V1KnowledgeRetry


def main():
    _, schema = models_json_schema(
        [
            (m, "validation")
            for m in (
                V0AnalysisTask,
                V0ClaimCase,
                V0Clause,
                V0ReviewAccepted,
                V1KnowledgeGeneration,
                V1KnowledgeRetry,
            )
        ]
    )
    print(json.dumps(schema, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

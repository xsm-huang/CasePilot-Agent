"""Export authoritative API wire schemas without importing the application."""

import json

from pydantic.json_schema import models_json_schema

from .schemas.knowledge import V1KnowledgeGeneration, V1KnowledgeRetry
from .schemas.review_cases import ReviewCaseDetail, ReviewCaseListResponse, ReviewPreflight
from .schemas.workspace import (
    AnalysisTask,
    Citation,
    CitationContext,
    CommandAccepted,
    Conversation,
    ConversationSummary,
    CreateAnalysis,
    CreateConversation,
    RecoverRequest,
    ReviewRequest,
    WorkspaceEvent,
)


def main():
    _, schema = models_json_schema(
        [
            (m, "validation")
            for m in (
                V1KnowledgeGeneration,
                V1KnowledgeRetry,
                ReviewCaseListResponse,
                ReviewCaseDetail,
                ReviewPreflight,
                WorkspaceEvent,
                AnalysisTask,
                Conversation,
                ConversationSummary,
                CommandAccepted,
                Citation,
                CitationContext,
                CreateAnalysis,
                CreateConversation,
                ReviewRequest,
                RecoverRequest,
            )
        ]
    )
    print(json.dumps(schema, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

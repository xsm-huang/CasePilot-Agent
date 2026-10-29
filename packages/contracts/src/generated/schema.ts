// Generated from Python Pydantic models by pnpm --filter @casepilot/contracts generate. Do not edit.
export const transportSchema = {
  "$defs": {
    "AcceptedEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "review.accepted",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/ReviewAcceptedData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "AcceptedEvent",
      "type": "object"
    },
    "AnalysisContext": {
      "additionalProperties": false,
      "properties": {
        "inputVersion": {
          "title": "Inputversion",
          "type": "string"
        },
        "knowledgeBindings": {
          "items": {
            "$ref": "#/$defs/ReviewKnowledgeBinding"
          },
          "title": "Knowledgebindings",
          "type": "array"
        },
        "messageIds": {
          "items": {
            "type": "string"
          },
          "title": "Messageids",
          "type": "array"
        },
        "modelProfile": {
          "title": "Modelprofile",
          "type": "string"
        },
        "promptVersion": {
          "title": "Promptversion",
          "type": "string"
        }
      },
      "required": [
        "inputVersion",
        "knowledgeBindings",
        "messageIds",
        "modelProfile",
        "promptVersion"
      ],
      "title": "AnalysisContext",
      "type": "object"
    },
    "AnalysisReadyData": {
      "additionalProperties": false,
      "properties": {
        "checks": {
          "items": {
            "$ref": "#/$defs/ReviewCheck"
          },
          "title": "Checks",
          "type": "array"
        },
        "facts": {
          "items": {
            "$ref": "#/$defs/Fact"
          },
          "title": "Facts",
          "type": "array"
        },
        "ruleFindings": {
          "items": {
            "$ref": "#/$defs/RuleFinding"
          },
          "title": "Rulefindings",
          "type": "array"
        },
        "modelFindings": {
          "items": {
            "$ref": "#/$defs/ModelFinding"
          },
          "title": "Modelfindings",
          "type": "array"
        },
        "citations": {
          "items": {
            "$ref": "#/$defs/Citation"
          },
          "title": "Citations",
          "type": "array"
        },
        "insufficientEvidence": {
          "title": "Insufficientevidence",
          "type": "boolean"
        }
      },
      "required": [
        "facts",
        "ruleFindings",
        "modelFindings",
        "citations",
        "insufficientEvidence"
      ],
      "title": "AnalysisReadyData",
      "type": "object"
    },
    "AnalysisReport": {
      "additionalProperties": false,
      "properties": {
        "kind": {
          "default": "stage",
          "enum": [
            "pending_review",
            "stage",
            "final"
          ],
          "title": "Kind",
          "type": "string"
        },
        "version": {
          "title": "Version",
          "type": "integer"
        },
        "analysisId": {
          "default": "",
          "title": "Analysisid",
          "type": "string"
        },
        "inputVersion": {
          "default": "",
          "title": "Inputversion",
          "type": "string"
        },
        "generatedAt": {
          "default": "",
          "title": "Generatedat",
          "type": "string"
        },
        "operatorId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Operatorid"
        },
        "conclusion": {
          "default": "历史报告，业务完成条件需核对",
          "title": "Conclusion",
          "type": "string"
        },
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "sections": {
          "items": {
            "$ref": "#/$defs/ReportSection"
          },
          "title": "Sections",
          "type": "array"
        },
        "insufficientEvidence": {
          "title": "Insufficientevidence",
          "type": "boolean"
        },
        "reviewerComment": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Reviewercomment"
        },
        "basisHash": {
          "title": "Basishash",
          "type": "string"
        },
        "snapshot": {
          "additionalProperties": {
            "$ref": "#/$defs/JsonValue"
          },
          "title": "Snapshot",
          "type": "object"
        },
        "statistics": {
          "additionalProperties": {
            "type": "integer"
          },
          "title": "Statistics",
          "type": "object"
        },
        "revisionReason": {
          "title": "Revisionreason",
          "type": "string"
        },
        "replacesVersion": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "title": "Replacesversion"
        }
      },
      "required": [
        "version",
        "caseId",
        "sections",
        "insufficientEvidence",
        "reviewerComment",
        "basisHash",
        "snapshot",
        "statistics",
        "revisionReason",
        "replacesVersion"
      ],
      "title": "AnalysisReport",
      "type": "object"
    },
    "AnalysisTask": {
      "additionalProperties": false,
      "properties": {
        "reviewState": {
          "$ref": "#/$defs/ReviewState"
        },
        "finalizationEligibility": {
          "$ref": "#/$defs/Eligibility"
        },
        "reviewStatus": {
          "enum": [
            "pending_review",
            "reviewing",
            "pending_verification",
            "completed"
          ],
          "title": "Reviewstatus",
          "type": "string"
        },
        "caseSummary": {
          "anyOf": [
            {
              "$ref": "#/$defs/ReviewCaseListItem"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "checks": {
          "items": {
            "$ref": "#/$defs/ReviewCheck"
          },
          "title": "Checks",
          "type": "array"
        },
        "reviewHistory": {
          "items": {
            "$ref": "#/$defs/FindingReview"
          },
          "title": "Reviewhistory",
          "type": "array"
        },
        "reports": {
          "items": {
            "$ref": "#/$defs/AnalysisReport"
          },
          "title": "Reports",
          "type": "array"
        },
        "operatorId": {
          "default": "unidentified_operator",
          "title": "Operatorid",
          "type": "string"
        },
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "id": {
          "title": "Id",
          "type": "string"
        },
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "kind": {
          "enum": [
            "initial",
            "followup"
          ],
          "title": "Kind",
          "type": "string"
        },
        "question": {
          "title": "Question",
          "type": "string"
        },
        "status": {
          "enum": [
            "queued",
            "running",
            "waiting_review",
            "resuming",
            "recoverable",
            "completed",
            "rejected",
            "failed"
          ],
          "title": "Status",
          "type": "string"
        },
        "caseSnapshot": {
          "$ref": "#/$defs/ClosedClaimReviewSnapshot"
        },
        "predecessorAnalysisId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Predecessoranalysisid"
        },
        "evidenceSupplements": {
          "items": {
            "$ref": "#/$defs/EvidenceSupplement"
          },
          "title": "Evidencesupplements",
          "type": "array"
        },
        "reviewSupplementIds": {
          "items": {
            "type": "string"
          },
          "title": "Reviewsupplementids",
          "type": "array"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "lastEventSeq": {
          "minimum": 0,
          "title": "Lasteventseq",
          "type": "integer"
        },
        "userMessageId": {
          "title": "Usermessageid",
          "type": "string"
        },
        "assistantMessageId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Assistantmessageid"
        },
        "context": {
          "$ref": "#/$defs/AnalysisContext"
        },
        "facts": {
          "items": {
            "$ref": "#/$defs/Fact"
          },
          "title": "Facts",
          "type": "array"
        },
        "ruleFindings": {
          "items": {
            "$ref": "#/$defs/RuleFinding"
          },
          "title": "Rulefindings",
          "type": "array"
        },
        "modelFindings": {
          "items": {
            "$ref": "#/$defs/ModelFinding"
          },
          "title": "Modelfindings",
          "type": "array"
        },
        "citations": {
          "items": {
            "$ref": "#/$defs/Citation"
          },
          "title": "Citations",
          "type": "array"
        },
        "sections": {
          "items": {
            "$ref": "#/$defs/ReportSection"
          },
          "title": "Sections",
          "type": "array"
        },
        "report": {
          "anyOf": [
            {
              "$ref": "#/$defs/AnalysisReport"
            },
            {
              "type": "null"
            }
          ]
        },
        "pendingReview": {
          "anyOf": [
            {
              "$ref": "#/$defs/PendingReview"
            },
            {
              "type": "null"
            }
          ]
        },
        "execution": {
          "$ref": "#/$defs/Execution"
        },
        "error": {
          "anyOf": [
            {
              "$ref": "#/$defs/PublicError"
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "reviewState",
        "finalizationEligibility",
        "reviewStatus",
        "schemaVersion",
        "id",
        "caseId",
        "conversationId",
        "kind",
        "question",
        "status",
        "caseSnapshot",
        "predecessorAnalysisId",
        "evidenceSupplements",
        "reviewSupplementIds",
        "revision",
        "lastEventSeq",
        "userMessageId",
        "assistantMessageId",
        "context",
        "facts",
        "ruleFindings",
        "modelFindings",
        "citations",
        "sections",
        "report",
        "pendingReview",
        "execution",
        "error"
      ],
      "title": "AnalysisTask",
      "type": "object"
    },
    "BusinessNode": {
      "additionalProperties": false,
      "properties": {
        "nodeRunId": {
          "title": "Noderunid",
          "type": "string"
        },
        "nodeKey": {
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "attempt": {
          "title": "Attempt",
          "type": "integer"
        },
        "status": {
          "enum": [
            "not_started",
            "running",
            "completed",
            "failed",
            "unable",
            "not_applicable"
          ],
          "title": "Status",
          "type": "string"
        },
        "startedAt": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Startedat"
        },
        "endedAt": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Endedat"
        },
        "durationMs": {
          "title": "Durationms",
          "type": "integer"
        },
        "summary": {
          "title": "Summary",
          "type": "string"
        },
        "reason": {
          "title": "Reason",
          "type": "string"
        }
      },
      "required": [
        "nodeRunId",
        "nodeKey",
        "attempt",
        "status",
        "startedAt",
        "endedAt",
        "durationMs",
        "summary",
        "reason"
      ],
      "title": "BusinessNode",
      "type": "object"
    },
    "BusinessNodeEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "enum": [
            "business_node.started",
            "business_node.completed",
            "business_node.failed",
            "business_node.unable",
            "business_node.not_applicable"
          ],
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/BusinessNode"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "BusinessNodeEvent",
      "type": "object"
    },
    "CheckPlanItem": {
      "additionalProperties": false,
      "properties": {
        "checkId": {
          "title": "Checkid",
          "type": "string"
        },
        "nodeKey": {
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "required": {
          "title": "Required",
          "type": "boolean"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "title": "Entityids",
          "type": "array"
        }
      },
      "required": [
        "checkId",
        "nodeKey",
        "title",
        "required",
        "entityIds"
      ],
      "title": "CheckPlanItem",
      "type": "object"
    },
    "Citation": {
      "additionalProperties": false,
      "properties": {
        "citationId": {
          "title": "Citationid",
          "type": "string"
        },
        "chunkId": {
          "title": "Chunkid",
          "type": "string"
        },
        "generationId": {
          "title": "Generationid",
          "type": "string"
        },
        "documentId": {
          "title": "Documentid",
          "type": "string"
        },
        "fileName": {
          "title": "Filename",
          "type": "string"
        },
        "productCode": {
          "title": "Productcode",
          "type": "string"
        },
        "clauseVersion": {
          "title": "Clauseversion",
          "type": "string"
        },
        "page": {
          "exclusiveMinimum": 0,
          "title": "Page",
          "type": "integer"
        },
        "ordinal": {
          "minimum": 0,
          "title": "Ordinal",
          "type": "integer"
        },
        "content": {
          "title": "Content",
          "type": "string"
        }
      },
      "required": [
        "citationId",
        "chunkId",
        "generationId",
        "documentId",
        "fileName",
        "productCode",
        "clauseVersion",
        "page",
        "ordinal",
        "content"
      ],
      "title": "Citation",
      "type": "object"
    },
    "CitationBlock": {
      "additionalProperties": false,
      "properties": {
        "chunkId": {
          "title": "Chunkid",
          "type": "string"
        },
        "page": {
          "exclusiveMinimum": 0,
          "title": "Page",
          "type": "integer"
        },
        "ordinal": {
          "minimum": 0,
          "title": "Ordinal",
          "type": "integer"
        },
        "content": {
          "title": "Content",
          "type": "string"
        }
      },
      "required": [
        "chunkId",
        "page",
        "ordinal",
        "content"
      ],
      "title": "CitationBlock",
      "type": "object"
    },
    "CitationContext": {
      "additionalProperties": false,
      "properties": {
        "citation": {
          "$ref": "#/$defs/Citation"
        },
        "previous": {
          "anyOf": [
            {
              "$ref": "#/$defs/CitationBlock"
            },
            {
              "type": "null"
            }
          ]
        },
        "next": {
          "anyOf": [
            {
              "$ref": "#/$defs/CitationBlock"
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "citation",
        "previous",
        "next"
      ],
      "title": "CitationContext",
      "type": "object"
    },
    "ClosedClaimReviewSnapshot": {
      "properties": {
        "snapshotKind": {
          "const": "closed_claim_review",
          "title": "Snapshotkind",
          "type": "string"
        },
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "caseRevision": {
          "title": "Caserevision",
          "type": "integer"
        },
        "preparedAt": {
          "title": "Preparedat",
          "type": "string"
        },
        "payload": {
          "additionalProperties": {
            "$ref": "#/$defs/JsonValue"
          },
          "title": "Payload",
          "type": "object"
        },
        "scopeItems": {
          "items": {
            "$ref": "#/$defs/ReviewScopeItem"
          },
          "title": "Scopeitems",
          "type": "array"
        },
        "knowledgeBindings": {
          "items": {
            "$ref": "#/$defs/ReviewKnowledgeBinding"
          },
          "title": "Knowledgebindings",
          "type": "array"
        }
      },
      "required": [
        "snapshotKind",
        "caseId",
        "caseRevision",
        "preparedAt",
        "payload",
        "scopeItems",
        "knowledgeBindings"
      ],
      "title": "ClosedClaimReviewSnapshot",
      "type": "object"
    },
    "CommandAccepted": {
      "additionalProperties": false,
      "properties": {
        "accepted": {
          "const": true,
          "title": "Accepted",
          "type": "boolean"
        },
        "taskId": {
          "title": "Taskid",
          "type": "string"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        }
      },
      "required": [
        "accepted",
        "taskId",
        "revision"
      ],
      "title": "CommandAccepted",
      "type": "object"
    },
    "CompletedEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "report.completed",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/ReportCompletedData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "CompletedEvent",
      "type": "object"
    },
    "Conversation": {
      "additionalProperties": false,
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "createdAt": {
          "format": "date-time",
          "title": "Createdat",
          "type": "string"
        },
        "updatedAt": {
          "format": "date-time",
          "title": "Updatedat",
          "type": "string"
        },
        "activeAnalysisId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Activeanalysisid"
        },
        "messages": {
          "items": {
            "$ref": "#/$defs/Message"
          },
          "title": "Messages",
          "type": "array"
        },
        "analysisIds": {
          "items": {
            "type": "string"
          },
          "title": "Analysisids",
          "type": "array"
        },
        "context": {
          "anyOf": [
            {
              "$ref": "#/$defs/AnalysisContext"
            },
            {
              "type": "null"
            }
          ]
        },
        "nextBefore": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Nextbefore"
        }
      },
      "required": [
        "id",
        "caseId",
        "title",
        "createdAt",
        "updatedAt",
        "activeAnalysisId",
        "messages",
        "analysisIds",
        "context",
        "nextBefore"
      ],
      "title": "Conversation",
      "type": "object"
    },
    "ConversationSummary": {
      "additionalProperties": false,
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "createdAt": {
          "format": "date-time",
          "title": "Createdat",
          "type": "string"
        },
        "updatedAt": {
          "format": "date-time",
          "title": "Updatedat",
          "type": "string"
        },
        "activeAnalysisId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Activeanalysisid"
        }
      },
      "required": [
        "id",
        "caseId",
        "title",
        "createdAt",
        "updatedAt",
        "activeAnalysisId"
      ],
      "title": "ConversationSummary",
      "type": "object"
    },
    "CreateAnalysis": {
      "additionalProperties": false,
      "properties": {
        "conversationId": {
          "maxLength": 200,
          "minLength": 1,
          "title": "Conversationid",
          "type": "string"
        },
        "kind": {
          "enum": [
            "initial",
            "followup"
          ],
          "title": "Kind",
          "type": "string"
        },
        "question": {
          "anyOf": [
            {
              "maxLength": 2000,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Question"
        },
        "expectedInputVersion": {
          "anyOf": [
            {
              "maxLength": 64,
              "minLength": 64,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Expectedinputversion"
        },
        "predecessorAnalysisId": {
          "anyOf": [
            {
              "maxLength": 200,
              "minLength": 1,
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Predecessoranalysisid"
        },
        "supplementIds": {
          "items": {
            "type": "string"
          },
          "title": "Supplementids",
          "type": "array"
        }
      },
      "required": [
        "conversationId",
        "kind"
      ],
      "title": "CreateAnalysis",
      "type": "object"
    },
    "CreateConversation": {
      "additionalProperties": false,
      "properties": {
        "title": {
          "default": "新会话",
          "maxLength": 200,
          "minLength": 1,
          "title": "Title",
          "type": "string"
        }
      },
      "title": "CreateConversation",
      "type": "object"
    },
    "Eligibility": {
      "additionalProperties": false,
      "properties": {
        "allowed": {
          "title": "Allowed",
          "type": "boolean"
        },
        "blockers": {
          "items": {
            "type": "string"
          },
          "title": "Blockers",
          "type": "array"
        },
        "basisHash": {
          "title": "Basishash",
          "type": "string"
        }
      },
      "required": [
        "allowed",
        "blockers",
        "basisHash"
      ],
      "title": "Eligibility",
      "type": "object"
    },
    "EvidenceSupplement": {
      "additionalProperties": false,
      "properties": {
        "nodeKey": {
          "default": "amount",
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "supplementId": {
          "title": "Supplementid",
          "type": "string"
        },
        "version": {
          "exclusiveMinimum": 0,
          "title": "Version",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "materialType": {
          "title": "Materialtype",
          "type": "string"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "title": "Entityids",
          "type": "array"
        },
        "sha256": {
          "pattern": "^[a-f0-9]{64}$",
          "title": "Sha256",
          "type": "string"
        },
        "addedAt": {
          "format": "date-time",
          "title": "Addedat",
          "type": "string"
        },
        "addedBy": {
          "title": "Addedby",
          "type": "string"
        },
        "pages": {
          "items": {
            "$ref": "#/$defs/SupplementPage"
          },
          "title": "Pages",
          "type": "array"
        }
      },
      "required": [
        "supplementId",
        "version",
        "analysisId",
        "title",
        "materialType",
        "entityIds",
        "sha256",
        "addedAt",
        "addedBy",
        "pages"
      ],
      "title": "EvidenceSupplement",
      "type": "object"
    },
    "Execution": {
      "additionalProperties": false,
      "properties": {
        "tools": {
          "items": {
            "$ref": "#/$defs/ExecutionData"
          },
          "title": "Tools",
          "type": "array"
        },
        "timeline": {
          "items": {
            "discriminator": {
              "mapping": {
                "analysis.failed": "#/$defs/FailureEvent",
                "analysis.ready": "#/$defs/ReadyEvent",
                "analysis.recoverable": "#/$defs/FailureEvent",
                "analysis.rejected": "#/$defs/RejectedEvent",
                "analysis.status": "#/$defs/StatusEvent",
                "business_node.completed": "#/$defs/BusinessNodeEvent",
                "business_node.failed": "#/$defs/BusinessNodeEvent",
                "business_node.not_applicable": "#/$defs/BusinessNodeEvent",
                "business_node.started": "#/$defs/BusinessNodeEvent",
                "business_node.unable": "#/$defs/BusinessNodeEvent",
                "evidence.supplemented": "#/$defs/SupplementedEvent",
                "finding.reviewed": "#/$defs/FindingReviewedEvent",
                "report.completed": "#/$defs/CompletedEvent",
                "report.saved": "#/$defs/ReportSavedEvent",
                "report.section": "#/$defs/SectionEvent",
                "review.accepted": "#/$defs/AcceptedEvent",
                "review.required": "#/$defs/ReviewEvent",
                "review.updated": "#/$defs/ReviewUpdatedEvent",
                "tool.completed": "#/$defs/ExecutionEvent",
                "tool.failed": "#/$defs/ExecutionEvent",
                "tool.started": "#/$defs/ExecutionEvent"
              },
              "propertyName": "type"
            },
            "oneOf": [
              {
                "$ref": "#/$defs/StatusEvent"
              },
              {
                "$ref": "#/$defs/ExecutionEvent"
              },
              {
                "$ref": "#/$defs/ReadyEvent"
              },
              {
                "$ref": "#/$defs/ReviewEvent"
              },
              {
                "$ref": "#/$defs/AcceptedEvent"
              },
              {
                "$ref": "#/$defs/SectionEvent"
              },
              {
                "$ref": "#/$defs/CompletedEvent"
              },
              {
                "$ref": "#/$defs/FailureEvent"
              },
              {
                "$ref": "#/$defs/RejectedEvent"
              },
              {
                "$ref": "#/$defs/SupplementedEvent"
              },
              {
                "$ref": "#/$defs/FindingReviewedEvent"
              },
              {
                "$ref": "#/$defs/ReportSavedEvent"
              },
              {
                "$ref": "#/$defs/BusinessNodeEvent"
              },
              {
                "$ref": "#/$defs/ReviewUpdatedEvent"
              }
            ]
          },
          "title": "Timeline",
          "type": "array"
        }
      },
      "required": [
        "tools",
        "timeline"
      ],
      "title": "Execution",
      "type": "object"
    },
    "ExecutionData": {
      "additionalProperties": false,
      "properties": {
        "nodeKey": {
          "default": "report",
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "executionId": {
          "title": "Executionid",
          "type": "string"
        },
        "key": {
          "title": "Key",
          "type": "string"
        },
        "name": {
          "title": "Name",
          "type": "string"
        },
        "attempt": {
          "exclusiveMinimum": 0,
          "title": "Attempt",
          "type": "integer"
        },
        "status": {
          "enum": [
            "running",
            "completed",
            "failed"
          ],
          "title": "Status",
          "type": "string"
        },
        "summary": {
          "title": "Summary",
          "type": "string"
        },
        "durationMs": {
          "minimum": 0,
          "title": "Durationms",
          "type": "integer"
        },
        "kind": {
          "enum": [
            "local",
            "retrieval",
            "model"
          ],
          "title": "Kind",
          "type": "string"
        },
        "parentNodeRunId": {
          "title": "Parentnoderunid",
          "type": "string"
        }
      },
      "required": [
        "executionId",
        "key",
        "name",
        "attempt",
        "status",
        "summary",
        "durationMs",
        "kind",
        "parentNodeRunId"
      ],
      "title": "ExecutionData",
      "type": "object"
    },
    "ExecutionEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "enum": [
            "tool.started",
            "tool.completed",
            "tool.failed"
          ],
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/ExecutionData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "ExecutionEvent",
      "type": "object"
    },
    "Fact": {
      "additionalProperties": false,
      "properties": {
        "factId": {
          "title": "Factid",
          "type": "string"
        },
        "fieldPath": {
          "title": "Fieldpath",
          "type": "string"
        },
        "value": {
          "$ref": "#/$defs/JsonValue"
        },
        "sourceType": {
          "enum": [
            "case",
            "material",
            "business"
          ],
          "title": "Sourcetype",
          "type": "string"
        },
        "materialId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Materialid"
        }
      },
      "required": [
        "factId",
        "fieldPath",
        "value",
        "sourceType"
      ],
      "title": "Fact",
      "type": "object"
    },
    "FailureData": {
      "additionalProperties": false,
      "properties": {
        "error": {
          "$ref": "#/$defs/PublicError"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        }
      },
      "required": [
        "error",
        "revision"
      ],
      "title": "FailureData",
      "type": "object"
    },
    "FailureEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "enum": [
            "analysis.failed",
            "analysis.recoverable"
          ],
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/FailureData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "FailureEvent",
      "type": "object"
    },
    "Finding": {
      "additionalProperties": false,
      "properties": {
        "checkId": {
          "title": "Checkid",
          "type": "string"
        },
        "nodeKey": {
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "status": {
          "enum": [
            "passed",
            "issue",
            "limited",
            "not_applicable",
            "out_of_scope"
          ],
          "title": "Status",
          "type": "string"
        },
        "source": {
          "enum": [
            "rule",
            "ai",
            "human"
          ],
          "title": "Source",
          "type": "string"
        },
        "sources": {
          "items": {
            "enum": [
              "rule",
              "ai",
              "human"
            ],
            "type": "string"
          },
          "title": "Sources",
          "type": "array"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "detail": {
          "title": "Detail",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "title": "Citationrefs",
          "type": "array"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "title": "Entityids",
          "type": "array"
        },
        "policyIds": {
          "items": {
            "type": "string"
          },
          "title": "Policyids",
          "type": "array"
        },
        "coverageIds": {
          "items": {
            "type": "string"
          },
          "title": "Coverageids",
          "type": "array"
        },
        "originalValues": {
          "additionalProperties": {
            "$ref": "#/$defs/JsonValue"
          },
          "title": "Originalvalues",
          "type": "object"
        },
        "uncertainty": {
          "default": "",
          "title": "Uncertainty",
          "type": "string"
        },
        "recommendation": {
          "default": "",
          "title": "Recommendation",
          "type": "string"
        },
        "statements": {
          "items": {
            "additionalProperties": {
              "$ref": "#/$defs/JsonValue"
            },
            "type": "object"
          },
          "title": "Statements",
          "type": "array"
        },
        "findingId": {
          "title": "Findingid",
          "type": "string"
        },
        "version": {
          "title": "Version",
          "type": "integer"
        },
        "kind": {
          "enum": [
            "issue",
            "limitation",
            "out_of_scope"
          ],
          "title": "Kind",
          "type": "string"
        },
        "active": {
          "default": true,
          "title": "Active",
          "type": "boolean"
        }
      },
      "required": [
        "checkId",
        "nodeKey",
        "status",
        "source",
        "title",
        "detail",
        "findingId",
        "version",
        "kind"
      ],
      "title": "Finding",
      "type": "object"
    },
    "FindingReview": {
      "additionalProperties": false,
      "properties": {
        "reviewId": {
          "title": "Reviewid",
          "type": "string"
        },
        "findingId": {
          "title": "Findingid",
          "type": "string"
        },
        "nodeKey": {
          "title": "Nodekey",
          "type": "string"
        },
        "decision": {
          "enum": [
            "confirmed",
            "excluded",
            "pending",
            "referred"
          ],
          "title": "Decision",
          "type": "string"
        },
        "comment": {
          "title": "Comment",
          "type": "string"
        },
        "operatorId": {
          "title": "Operatorid",
          "type": "string"
        },
        "at": {
          "title": "At",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "title": "Citationrefs",
          "type": "array"
        },
        "supplementIds": {
          "items": {
            "type": "string"
          },
          "title": "Supplementids",
          "type": "array"
        },
        "followup": {
          "title": "Followup",
          "type": "string"
        },
        "changeReason": {
          "title": "Changereason",
          "type": "string"
        },
        "findingVersion": {
          "title": "Findingversion",
          "type": "integer"
        },
        "previousReviewId": {
          "title": "Previousreviewid",
          "type": "string"
        },
        "recipient": {
          "title": "Recipient",
          "type": "string"
        },
        "missingItems": {
          "title": "Missingitems",
          "type": "string"
        },
        "evidenceViewed": {
          "title": "Evidenceviewed",
          "type": "boolean"
        }
      },
      "required": [
        "reviewId",
        "findingId",
        "nodeKey",
        "decision",
        "comment",
        "operatorId",
        "at",
        "factRefs",
        "citationRefs",
        "supplementIds",
        "followup",
        "changeReason",
        "findingVersion",
        "previousReviewId",
        "recipient",
        "missingItems",
        "evidenceViewed"
      ],
      "title": "FindingReview",
      "type": "object"
    },
    "FindingReviewRequest": {
      "additionalProperties": false,
      "properties": {
        "decision": {
          "enum": [
            "confirmed",
            "excluded",
            "pending",
            "referred"
          ],
          "title": "Decision",
          "type": "string"
        },
        "comment": {
          "maxLength": 2000,
          "minLength": 2,
          "title": "Comment",
          "type": "string"
        },
        "expectedRevision": {
          "minimum": 0,
          "title": "Expectedrevision",
          "type": "integer"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 30,
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 12,
          "title": "Citationrefs",
          "type": "array"
        },
        "supplementIds": {
          "items": {
            "type": "string"
          },
          "maxItems": 20,
          "title": "Supplementids",
          "type": "array"
        },
        "followup": {
          "default": "",
          "maxLength": 1000,
          "title": "Followup",
          "type": "string"
        },
        "changeReason": {
          "default": "",
          "maxLength": 1000,
          "title": "Changereason",
          "type": "string"
        },
        "findingVersion": {
          "exclusiveMinimum": 0,
          "title": "Findingversion",
          "type": "integer"
        },
        "previousReviewId": {
          "default": "",
          "title": "Previousreviewid",
          "type": "string"
        },
        "recipient": {
          "default": "",
          "maxLength": 200,
          "title": "Recipient",
          "type": "string"
        },
        "missingItems": {
          "default": "",
          "maxLength": 1000,
          "title": "Missingitems",
          "type": "string"
        },
        "evidenceViewed": {
          "default": false,
          "title": "Evidenceviewed",
          "type": "boolean"
        }
      },
      "required": [
        "decision",
        "comment",
        "expectedRevision",
        "findingVersion"
      ],
      "title": "FindingReviewRequest",
      "type": "object"
    },
    "FindingReviewedData": {
      "additionalProperties": false,
      "properties": {
        "review": {
          "$ref": "#/$defs/FindingReview"
        },
        "report": {
          "$ref": "#/$defs/AnalysisReport"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        }
      },
      "required": [
        "review",
        "report",
        "revision"
      ],
      "title": "FindingReviewedData",
      "type": "object"
    },
    "FindingReviewedEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "finding.reviewed",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/FindingReviewedData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "FindingReviewedEvent",
      "type": "object"
    },
    "JsonValue": {},
    "ManualFindingRequest": {
      "additionalProperties": false,
      "properties": {
        "expectedRevision": {
          "minimum": 0,
          "title": "Expectedrevision",
          "type": "integer"
        },
        "nodeKey": {
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "title": {
          "maxLength": 200,
          "minLength": 2,
          "title": "Title",
          "type": "string"
        },
        "detail": {
          "maxLength": 2000,
          "minLength": 5,
          "title": "Detail",
          "type": "string"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "maxItems": 30,
          "minItems": 1,
          "title": "Entityids",
          "type": "array"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 30,
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 12,
          "title": "Citationrefs",
          "type": "array"
        },
        "supplementIds": {
          "items": {
            "type": "string"
          },
          "maxItems": 20,
          "title": "Supplementids",
          "type": "array"
        },
        "originalValues": {
          "additionalProperties": {
            "$ref": "#/$defs/JsonValue"
          },
          "title": "Originalvalues",
          "type": "object"
        },
        "recommendation": {
          "maxLength": 1000,
          "minLength": 2,
          "title": "Recommendation",
          "type": "string"
        }
      },
      "required": [
        "expectedRevision",
        "nodeKey",
        "title",
        "detail",
        "entityIds",
        "recommendation"
      ],
      "title": "ManualFindingRequest",
      "type": "object"
    },
    "Message": {
      "additionalProperties": false,
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "role": {
          "enum": [
            "user",
            "assistant"
          ],
          "title": "Role",
          "type": "string"
        },
        "content": {
          "title": "Content",
          "type": "string"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "createdAt": {
          "format": "date-time",
          "title": "Createdat",
          "type": "string"
        }
      },
      "required": [
        "id",
        "role",
        "content",
        "analysisId",
        "createdAt"
      ],
      "title": "Message",
      "type": "object"
    },
    "ModelFinding": {
      "additionalProperties": false,
      "properties": {
        "relatedCheckId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Relatedcheckid"
        },
        "issueCode": {
          "maxLength": 100,
          "minLength": 1,
          "title": "Issuecode",
          "type": "string"
        },
        "supportQuote": {
          "maxLength": 500,
          "title": "Supportquote",
          "type": "string"
        },
        "category": {
          "default": "issue",
          "enum": [
            "issue",
            "limitation",
            "out_of_scope",
            "passed"
          ],
          "title": "Category",
          "type": "string"
        },
        "nodeKey": {
          "default": "clauses",
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "title": {
          "maxLength": 200,
          "minLength": 1,
          "title": "Title",
          "type": "string"
        },
        "inference": {
          "maxLength": 2000,
          "minLength": 1,
          "title": "Inference",
          "type": "string"
        },
        "evidenceStatus": {
          "enum": [
            "supported",
            "insufficient"
          ],
          "title": "Evidencestatus",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 30,
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 12,
          "title": "Citationrefs",
          "type": "array"
        },
        "pendingItems": {
          "items": {
            "type": "string"
          },
          "maxItems": 12,
          "title": "Pendingitems",
          "type": "array"
        }
      },
      "required": [
        "issueCode",
        "supportQuote",
        "title",
        "inference",
        "evidenceStatus",
        "factRefs",
        "citationRefs",
        "pendingItems"
      ],
      "title": "ModelFinding",
      "type": "object"
    },
    "PendingReview": {
      "additionalProperties": false,
      "properties": {
        "interruptKey": {
          "title": "Interruptkey",
          "type": "string"
        },
        "checkpointId": {
          "title": "Checkpointid",
          "type": "string"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "reason": {
          "title": "Reason",
          "type": "string"
        }
      },
      "required": [
        "interruptKey",
        "checkpointId",
        "revision",
        "reason"
      ],
      "title": "PendingReview",
      "type": "object"
    },
    "PublicError": {
      "additionalProperties": false,
      "properties": {
        "code": {
          "title": "Code",
          "type": "string"
        },
        "message": {
          "title": "Message",
          "type": "string"
        },
        "requestId": {
          "title": "Requestid",
          "type": "string"
        }
      },
      "required": [
        "code",
        "message",
        "requestId"
      ],
      "title": "PublicError",
      "type": "object"
    },
    "ReadyEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "analysis.ready",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/AnalysisReadyData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "ReadyEvent",
      "type": "object"
    },
    "RecoverRequest": {
      "additionalProperties": false,
      "properties": {
        "expectedRevision": {
          "minimum": 0,
          "title": "Expectedrevision",
          "type": "integer"
        }
      },
      "required": [
        "expectedRevision"
      ],
      "title": "RecoverRequest",
      "type": "object"
    },
    "RejectedData": {
      "additionalProperties": false,
      "properties": {
        "comment": {
          "title": "Comment",
          "type": "string"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        }
      },
      "required": [
        "comment",
        "revision"
      ],
      "title": "RejectedData",
      "type": "object"
    },
    "RejectedEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "analysis.rejected",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/RejectedData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "RejectedEvent",
      "type": "object"
    },
    "ReportCompletedData": {
      "additionalProperties": false,
      "properties": {
        "report": {
          "$ref": "#/$defs/AnalysisReport"
        },
        "assistantMessageId": {
          "title": "Assistantmessageid",
          "type": "string"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        }
      },
      "required": [
        "report",
        "assistantMessageId",
        "revision"
      ],
      "title": "ReportCompletedData",
      "type": "object"
    },
    "ReportSavedEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "report.saved",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/AnalysisReport"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "ReportSavedEvent",
      "type": "object"
    },
    "ReportSection": {
      "additionalProperties": false,
      "properties": {
        "sectionKey": {
          "enum": [
            "summary",
            "coverage",
            "findings",
            "limitations",
            "reviews",
            "recommendations"
          ],
          "title": "Sectionkey",
          "type": "string"
        },
        "content": {
          "maxLength": 6000,
          "minLength": 1,
          "title": "Content",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "title": "Citationrefs",
          "type": "array"
        },
        "committedAt": {
          "format": "date-time",
          "title": "Committedat",
          "type": "string"
        }
      },
      "required": [
        "sectionKey",
        "content",
        "factRefs",
        "citationRefs",
        "committedAt"
      ],
      "title": "ReportSection",
      "type": "object"
    },
    "ReviewAcceptedData": {
      "additionalProperties": false,
      "properties": {
        "interruptKey": {
          "title": "Interruptkey",
          "type": "string"
        },
        "decision": {
          "enum": [
            "approve",
            "reject"
          ],
          "title": "Decision",
          "type": "string"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        },
        "comment": {
          "default": "",
          "title": "Comment",
          "type": "string"
        },
        "operatorId": {
          "default": "unidentified_operator",
          "title": "Operatorid",
          "type": "string"
        },
        "nodeKey": {
          "default": "report",
          "title": "Nodekey",
          "type": "string"
        }
      },
      "required": [
        "interruptKey",
        "decision",
        "revision"
      ],
      "title": "ReviewAcceptedData",
      "type": "object"
    },
    "ReviewAccident": {
      "properties": {
        "accidentId": {
          "title": "Accidentid",
          "type": "string"
        },
        "occurredAt": {
          "title": "Occurredat",
          "type": "string"
        },
        "location": {
          "title": "Location",
          "type": "string"
        },
        "description": {
          "title": "Description",
          "type": "string"
        },
        "liabilityDescription": {
          "title": "Liabilitydescription",
          "type": "string"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "accidentId",
        "occurredAt",
        "location",
        "description",
        "liabilityDescription",
        "sources"
      ],
      "title": "ReviewAccident",
      "type": "object"
    },
    "ReviewApplicablePolicy": {
      "properties": {
        "policyId": {
          "title": "Policyid",
          "type": "string"
        },
        "policyType": {
          "title": "Policytype",
          "type": "string"
        },
        "availability": {
          "title": "Availability",
          "type": "string"
        },
        "coverageCodes": {
          "items": {
            "type": "string"
          },
          "title": "Coveragecodes",
          "type": "array"
        }
      },
      "required": [
        "policyId",
        "policyType",
        "availability",
        "coverageCodes"
      ],
      "title": "ReviewApplicablePolicy",
      "type": "object"
    },
    "ReviewCaseDetail": {
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        },
        "isSynthetic": {
          "title": "Issynthetic",
          "type": "boolean"
        },
        "preparedAt": {
          "title": "Preparedat",
          "type": "string"
        },
        "latestReviewStatus": {
          "default": "not_started",
          "enum": [
            "not_started",
            "running",
            "pending_review",
            "pending_verification",
            "vehicle_review_completed",
            "failed",
            "awaiting_recovery"
          ],
          "title": "Latestreviewstatus",
          "type": "string"
        },
        "scope": {
          "$ref": "#/$defs/ReviewScope"
        },
        "accident": {
          "$ref": "#/$defs/ReviewAccident"
        },
        "injury": {
          "$ref": "#/$defs/ReviewInjury"
        },
        "parties": {
          "items": {
            "$ref": "#/$defs/ReviewParty"
          },
          "title": "Parties",
          "type": "array"
        },
        "vehicles": {
          "items": {
            "$ref": "#/$defs/ReviewVehicleDetail"
          },
          "title": "Vehicles",
          "type": "array"
        },
        "claims": {
          "items": {
            "$ref": "#/$defs/ReviewClaimDetail"
          },
          "title": "Claims",
          "type": "array"
        },
        "policies": {
          "items": {
            "$ref": "#/$defs/ReviewPolicy"
          },
          "title": "Policies",
          "type": "array"
        },
        "losses": {
          "items": {
            "$ref": "#/$defs/ReviewLoss"
          },
          "title": "Losses",
          "type": "array"
        },
        "processingRecords": {
          "items": {
            "$ref": "#/$defs/ReviewProcessingRecord"
          },
          "title": "Processingrecords",
          "type": "array"
        },
        "timeline": {
          "items": {
            "$ref": "#/$defs/ReviewTimelineEntry"
          },
          "title": "Timeline",
          "type": "array"
        },
        "documents": {
          "items": {
            "$ref": "#/$defs/ReviewDocument"
          },
          "title": "Documents",
          "type": "array"
        },
        "dataGaps": {
          "items": {
            "$ref": "#/$defs/ReviewDataGap"
          },
          "title": "Datagaps",
          "type": "array"
        },
        "originalApprovedAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "effectivePaidAmount": {
          "$ref": "#/$defs/ReviewMoney"
        }
      },
      "required": [
        "id",
        "revision",
        "isSynthetic",
        "preparedAt",
        "scope",
        "accident",
        "injury",
        "parties",
        "vehicles",
        "claims",
        "policies",
        "losses",
        "processingRecords",
        "timeline",
        "documents",
        "dataGaps",
        "originalApprovedAmount",
        "effectivePaidAmount"
      ],
      "title": "ReviewCaseDetail",
      "type": "object"
    },
    "ReviewCaseListItem": {
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        },
        "targetClaims": {
          "items": {
            "$ref": "#/$defs/ReviewClaimSummary"
          },
          "title": "Targetclaims",
          "type": "array"
        },
        "relatedClaims": {
          "items": {
            "$ref": "#/$defs/ReviewClaimSummary"
          },
          "title": "Relatedclaims",
          "type": "array"
        },
        "vehicles": {
          "items": {
            "$ref": "#/$defs/ReviewVehicleSummary"
          },
          "title": "Vehicles",
          "type": "array"
        },
        "accidentAt": {
          "title": "Accidentat",
          "type": "string"
        },
        "originalApprovedAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "effectivePaidAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "injuryStatus": {
          "title": "Injurystatus",
          "type": "string"
        },
        "latestReviewStatus": {
          "default": "not_started",
          "enum": [
            "not_started",
            "running",
            "pending_review",
            "pending_verification",
            "vehicle_review_completed",
            "failed",
            "awaiting_recovery"
          ],
          "title": "Latestreviewstatus",
          "type": "string"
        }
      },
      "required": [
        "id",
        "revision",
        "targetClaims",
        "relatedClaims",
        "vehicles",
        "accidentAt",
        "originalApprovedAmount",
        "effectivePaidAmount",
        "injuryStatus"
      ],
      "title": "ReviewCaseListItem",
      "type": "object"
    },
    "ReviewCaseListResponse": {
      "properties": {
        "dataStatus": {
          "enum": [
            "ready",
            "not_imported"
          ],
          "title": "Datastatus",
          "type": "string"
        },
        "items": {
          "items": {
            "$ref": "#/$defs/ReviewCaseListItem"
          },
          "title": "Items",
          "type": "array"
        }
      },
      "required": [
        "dataStatus",
        "items"
      ],
      "title": "ReviewCaseListResponse",
      "type": "object"
    },
    "ReviewCheck": {
      "additionalProperties": false,
      "properties": {
        "checkId": {
          "title": "Checkid",
          "type": "string"
        },
        "nodeKey": {
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "status": {
          "enum": [
            "passed",
            "issue",
            "limited",
            "not_applicable",
            "out_of_scope"
          ],
          "title": "Status",
          "type": "string"
        },
        "source": {
          "enum": [
            "rule",
            "ai",
            "human"
          ],
          "title": "Source",
          "type": "string"
        },
        "sources": {
          "items": {
            "enum": [
              "rule",
              "ai",
              "human"
            ],
            "type": "string"
          },
          "title": "Sources",
          "type": "array"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "detail": {
          "title": "Detail",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "title": "Citationrefs",
          "type": "array"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "title": "Entityids",
          "type": "array"
        },
        "policyIds": {
          "items": {
            "type": "string"
          },
          "title": "Policyids",
          "type": "array"
        },
        "coverageIds": {
          "items": {
            "type": "string"
          },
          "title": "Coverageids",
          "type": "array"
        },
        "originalValues": {
          "additionalProperties": {
            "$ref": "#/$defs/JsonValue"
          },
          "title": "Originalvalues",
          "type": "object"
        },
        "uncertainty": {
          "default": "",
          "title": "Uncertainty",
          "type": "string"
        },
        "recommendation": {
          "default": "",
          "title": "Recommendation",
          "type": "string"
        },
        "statements": {
          "items": {
            "additionalProperties": {
              "$ref": "#/$defs/JsonValue"
            },
            "type": "object"
          },
          "title": "Statements",
          "type": "array"
        }
      },
      "required": [
        "checkId",
        "nodeKey",
        "status",
        "source",
        "title",
        "detail"
      ],
      "title": "ReviewCheck",
      "type": "object"
    },
    "ReviewClaimDetail": {
      "properties": {
        "claimId": {
          "title": "Claimid",
          "type": "string"
        },
        "claimNumber": {
          "title": "Claimnumber",
          "type": "string"
        },
        "reportNumber": {
          "title": "Reportnumber",
          "type": "string"
        },
        "scopeRole": {
          "enum": [
            "target",
            "related"
          ],
          "title": "Scoperole",
          "type": "string"
        },
        "closureType": {
          "title": "Closuretype",
          "type": "string"
        },
        "closedAt": {
          "title": "Closedat",
          "type": "string"
        },
        "originalPaymentStatus": {
          "title": "Originalpaymentstatus",
          "type": "string"
        },
        "handlingOrganization": {
          "title": "Handlingorganization",
          "type": "string"
        },
        "originalConclusion": {
          "title": "Originalconclusion",
          "type": "string"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "claimId",
        "claimNumber",
        "reportNumber",
        "scopeRole",
        "closureType",
        "closedAt",
        "originalPaymentStatus",
        "handlingOrganization",
        "originalConclusion",
        "sources"
      ],
      "title": "ReviewClaimDetail",
      "type": "object"
    },
    "ReviewClaimSummary": {
      "properties": {
        "claimId": {
          "title": "Claimid",
          "type": "string"
        },
        "claimNumber": {
          "title": "Claimnumber",
          "type": "string"
        },
        "reportNumber": {
          "title": "Reportnumber",
          "type": "string"
        },
        "scopeRole": {
          "enum": [
            "target",
            "related"
          ],
          "title": "Scoperole",
          "type": "string"
        },
        "closureType": {
          "title": "Closuretype",
          "type": "string"
        },
        "closedAt": {
          "title": "Closedat",
          "type": "string"
        },
        "originalPaymentStatus": {
          "title": "Originalpaymentstatus",
          "type": "string"
        }
      },
      "required": [
        "claimId",
        "claimNumber",
        "reportNumber",
        "scopeRole",
        "closureType",
        "closedAt",
        "originalPaymentStatus"
      ],
      "title": "ReviewClaimSummary",
      "type": "object"
    },
    "ReviewCoverage": {
      "properties": {
        "coverageId": {
          "title": "Coverageid",
          "type": "string"
        },
        "coverageCode": {
          "title": "Coveragecode",
          "type": "string"
        },
        "status": {
          "title": "Status",
          "type": "string"
        },
        "insuranceAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "perAccidentLimit": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "deductibleAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "deductibleBasisPoints": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Deductiblebasispoints"
        },
        "specialConditions": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Specialconditions"
        },
        "terms": {
          "items": {
            "$ref": "#/$defs/ReviewTermRef"
          },
          "title": "Terms",
          "type": "array"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "coverageId",
        "coverageCode",
        "status",
        "insuranceAmount",
        "perAccidentLimit",
        "deductibleAmount",
        "terms",
        "sources"
      ],
      "title": "ReviewCoverage",
      "type": "object"
    },
    "ReviewDataGap": {
      "properties": {
        "gapId": {
          "title": "Gapid",
          "type": "string"
        },
        "kind": {
          "title": "Kind",
          "type": "string"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "title": "Entityids",
          "type": "array"
        },
        "fieldPaths": {
          "items": {
            "type": "string"
          },
          "title": "Fieldpaths",
          "type": "array"
        },
        "description": {
          "title": "Description",
          "type": "string"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "gapId",
        "kind",
        "entityIds",
        "fieldPaths",
        "description",
        "sources"
      ],
      "title": "ReviewDataGap",
      "type": "object"
    },
    "ReviewDocument": {
      "properties": {
        "documentId": {
          "title": "Documentid",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "materialType": {
          "title": "Materialtype",
          "type": "string"
        },
        "status": {
          "title": "Status",
          "type": "string"
        },
        "version": {
          "title": "Version",
          "type": "string"
        },
        "pageCount": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Pagecount"
        },
        "claimIds": {
          "items": {
            "type": "string"
          },
          "title": "Claimids",
          "type": "array"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "title": "Entityids",
          "type": "array"
        },
        "issuedAt": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Issuedat"
        },
        "receivedAt": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Receivedat"
        },
        "sourceDescription": {
          "title": "Sourcedescription",
          "type": "string"
        },
        "contentUrl": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Contenturl"
        }
      },
      "required": [
        "documentId",
        "title",
        "materialType",
        "status",
        "version",
        "claimIds",
        "entityIds",
        "sourceDescription"
      ],
      "title": "ReviewDocument",
      "type": "object"
    },
    "ReviewEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "review.required",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/PendingReview"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "ReviewEvent",
      "type": "object"
    },
    "ReviewEvidenceSource": {
      "properties": {
        "evidenceId": {
          "title": "Evidenceid",
          "type": "string"
        },
        "sourceType": {
          "enum": [
            "case_document",
            "shared_document",
            "structured_record"
          ],
          "title": "Sourcetype",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "documentId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Documentid"
        },
        "documentVersion": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Documentversion"
        },
        "page": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Page"
        },
        "recordPointer": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Recordpointer"
        },
        "quote": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Quote"
        }
      },
      "required": [
        "evidenceId",
        "sourceType",
        "title"
      ],
      "title": "ReviewEvidenceSource",
      "type": "object"
    },
    "ReviewInjury": {
      "properties": {
        "declaredStatus": {
          "title": "Declaredstatus",
          "type": "string"
        },
        "injuredPersonIds": {
          "items": {
            "type": "string"
          },
          "title": "Injuredpersonids",
          "type": "array"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "declaredStatus",
        "injuredPersonIds",
        "sources"
      ],
      "title": "ReviewInjury",
      "type": "object"
    },
    "ReviewKnowledgeBinding": {
      "properties": {
        "documentId": {
          "title": "Documentid",
          "type": "string"
        },
        "documentSha256": {
          "title": "Documentsha256",
          "type": "string"
        },
        "version": {
          "title": "Version",
          "type": "string"
        },
        "sectionIds": {
          "items": {
            "type": "string"
          },
          "title": "Sectionids",
          "type": "array"
        },
        "status": {
          "enum": [
            "ready",
            "unavailable"
          ],
          "title": "Status",
          "type": "string"
        },
        "generationId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Generationid"
        },
        "productCode": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Productcode"
        },
        "clauseVersion": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Clauseversion"
        },
        "embeddingProfile": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Embeddingprofile"
        }
      },
      "required": [
        "documentId",
        "documentSha256",
        "version",
        "sectionIds",
        "status"
      ],
      "title": "ReviewKnowledgeBinding",
      "type": "object"
    },
    "ReviewLoss": {
      "properties": {
        "lossId": {
          "title": "Lossid",
          "type": "string"
        },
        "claimId": {
          "title": "Claimid",
          "type": "string"
        },
        "vehicleId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Vehicleid"
        },
        "personPartyId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Personpartyid"
        },
        "lossType": {
          "title": "Losstype",
          "type": "string"
        },
        "description": {
          "title": "Description",
          "type": "string"
        },
        "claimedAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "assessedAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "agreedAmount": {
          "$ref": "#/$defs/ReviewMoney"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "lossId",
        "claimId",
        "lossType",
        "description",
        "claimedAmount",
        "assessedAmount",
        "agreedAmount",
        "sources"
      ],
      "title": "ReviewLoss",
      "type": "object"
    },
    "ReviewMoney": {
      "properties": {
        "status": {
          "enum": [
            "known",
            "unknown",
            "not_applicable"
          ],
          "title": "Status",
          "type": "string"
        },
        "amountFen": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "title": "Amountfen"
        },
        "currency": {
          "default": "CNY",
          "title": "Currency",
          "type": "string"
        },
        "reason": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Reason"
        }
      },
      "required": [
        "status",
        "amountFen"
      ],
      "title": "ReviewMoney",
      "type": "object"
    },
    "ReviewObjectSummary": {
      "properties": {
        "targetClaimIds": {
          "items": {
            "type": "string"
          },
          "title": "Targetclaimids",
          "type": "array"
        },
        "relatedClaimIds": {
          "items": {
            "type": "string"
          },
          "title": "Relatedclaimids",
          "type": "array"
        },
        "vehicleIds": {
          "items": {
            "type": "string"
          },
          "title": "Vehicleids",
          "type": "array"
        },
        "lossIds": {
          "items": {
            "type": "string"
          },
          "title": "Lossids",
          "type": "array"
        },
        "scopeLimitations": {
          "items": {
            "type": "string"
          },
          "title": "Scopelimitations",
          "type": "array"
        }
      },
      "required": [
        "targetClaimIds",
        "relatedClaimIds",
        "vehicleIds",
        "lossIds",
        "scopeLimitations"
      ],
      "title": "ReviewObjectSummary",
      "type": "object"
    },
    "ReviewParty": {
      "properties": {
        "partyId": {
          "title": "Partyid",
          "type": "string"
        },
        "displayName": {
          "title": "Displayname",
          "type": "string"
        },
        "kind": {
          "title": "Kind",
          "type": "string"
        }
      },
      "required": [
        "partyId",
        "displayName",
        "kind"
      ],
      "title": "ReviewParty",
      "type": "object"
    },
    "ReviewPolicy": {
      "properties": {
        "policyId": {
          "title": "Policyid",
          "type": "string"
        },
        "policyNumber": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Policynumber"
        },
        "availability": {
          "title": "Availability",
          "type": "string"
        },
        "policyType": {
          "title": "Policytype",
          "type": "string"
        },
        "vehicleId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Vehicleid"
        },
        "effectiveFrom": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Effectivefrom"
        },
        "effectiveTo": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Effectiveto"
        },
        "coverages": {
          "items": {
            "$ref": "#/$defs/ReviewCoverage"
          },
          "title": "Coverages",
          "type": "array"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "policyId",
        "availability",
        "policyType",
        "coverages",
        "sources"
      ],
      "title": "ReviewPolicy",
      "type": "object"
    },
    "ReviewPreflight": {
      "properties": {
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "expectedInputVersion": {
          "title": "Expectedinputversion",
          "type": "string"
        },
        "status": {
          "enum": [
            "ready",
            "partial",
            "blocked"
          ],
          "title": "Status",
          "type": "string"
        },
        "reviewObjects": {
          "$ref": "#/$defs/ReviewObjectSummary"
        },
        "applicablePolicies": {
          "items": {
            "$ref": "#/$defs/ReviewApplicablePolicy"
          },
          "title": "Applicablepolicies",
          "type": "array"
        },
        "scopeItems": {
          "items": {
            "$ref": "#/$defs/ReviewScopeItem"
          },
          "title": "Scopeitems",
          "type": "array"
        },
        "knowledgeBindings": {
          "items": {
            "$ref": "#/$defs/ReviewKnowledgeBinding"
          },
          "title": "Knowledgebindings",
          "type": "array"
        },
        "materialSummary": {
          "additionalProperties": {
            "type": "integer"
          },
          "title": "Materialsummary",
          "type": "object"
        },
        "injuryStatus": {
          "title": "Injurystatus",
          "type": "string"
        },
        "injuredPersonIds": {
          "items": {
            "type": "string"
          },
          "title": "Injuredpersonids",
          "type": "array"
        },
        "blockingReasons": {
          "items": {
            "type": "string"
          },
          "title": "Blockingreasons",
          "type": "array"
        }
      },
      "required": [
        "caseId",
        "expectedInputVersion",
        "status",
        "reviewObjects",
        "applicablePolicies",
        "scopeItems",
        "knowledgeBindings",
        "materialSummary",
        "injuryStatus",
        "injuredPersonIds",
        "blockingReasons"
      ],
      "title": "ReviewPreflight",
      "type": "object"
    },
    "ReviewProcessingRecord": {
      "properties": {
        "recordId": {
          "title": "Recordid",
          "type": "string"
        },
        "recordType": {
          "enum": [
            "calculation",
            "approval",
            "payment"
          ],
          "title": "Recordtype",
          "type": "string"
        },
        "claimId": {
          "title": "Claimid",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "status": {
          "title": "Status",
          "type": "string"
        },
        "occurredAt": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Occurredat"
        },
        "amount": {
          "anyOf": [
            {
              "$ref": "#/$defs/ReviewMoney"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "detail": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Detail"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "recordId",
        "recordType",
        "claimId",
        "title",
        "status",
        "sources"
      ],
      "title": "ReviewProcessingRecord",
      "type": "object"
    },
    "ReviewRecord": {
      "additionalProperties": false,
      "properties": {
        "recordId": {
          "title": "Recordid",
          "type": "string"
        },
        "kind": {
          "enum": [
            "evidence_view",
            "human_completion",
            "scope_adjustment",
            "professional",
            "followup",
            "business_record",
            "reopen"
          ],
          "title": "Kind",
          "type": "string"
        },
        "nodeKey": {
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "targetId": {
          "title": "Targetid",
          "type": "string"
        },
        "comment": {
          "title": "Comment",
          "type": "string"
        },
        "operatorId": {
          "title": "Operatorid",
          "type": "string"
        },
        "at": {
          "title": "At",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "title": "Citationrefs",
          "type": "array"
        },
        "supplementIds": {
          "items": {
            "type": "string"
          },
          "title": "Supplementids",
          "type": "array"
        },
        "checkIds": {
          "items": {
            "type": "string"
          },
          "title": "Checkids",
          "type": "array"
        },
        "steps": {
          "title": "Steps",
          "type": "string"
        },
        "result": {
          "title": "Result",
          "type": "string"
        },
        "recipient": {
          "title": "Recipient",
          "type": "string"
        },
        "state": {
          "title": "State",
          "type": "string"
        },
        "source": {
          "title": "Source",
          "type": "string"
        },
        "previousRecordId": {
          "title": "Previousrecordid",
          "type": "string"
        },
        "inputsFen": {
          "items": {
            "type": "integer"
          },
          "title": "Inputsfen",
          "type": "array"
        },
        "operation": {
          "anyOf": [
            {
              "enum": [
                "sum",
                "difference"
              ],
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "title": "Operation"
        },
        "resultFen": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "title": "Resultfen"
        }
      },
      "required": [
        "recordId",
        "kind",
        "nodeKey",
        "targetId",
        "comment",
        "operatorId",
        "at",
        "factRefs",
        "citationRefs",
        "supplementIds",
        "checkIds",
        "steps",
        "result",
        "recipient",
        "state",
        "source",
        "previousRecordId",
        "inputsFen",
        "operation",
        "resultFen"
      ],
      "title": "ReviewRecord",
      "type": "object"
    },
    "ReviewRecordRequest": {
      "additionalProperties": false,
      "properties": {
        "expectedRevision": {
          "minimum": 0,
          "title": "Expectedrevision",
          "type": "integer"
        },
        "nodeKey": {
          "enum": [
            "archive",
            "coverage",
            "consistency",
            "clauses",
            "amount",
            "report"
          ],
          "title": "Nodekey",
          "type": "string"
        },
        "targetId": {
          "default": "",
          "title": "Targetid",
          "type": "string"
        },
        "comment": {
          "maxLength": 2000,
          "minLength": 5,
          "title": "Comment",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 30,
          "title": "Factrefs",
          "type": "array"
        },
        "citationRefs": {
          "items": {
            "type": "string"
          },
          "maxItems": 12,
          "title": "Citationrefs",
          "type": "array"
        },
        "supplementIds": {
          "items": {
            "type": "string"
          },
          "maxItems": 20,
          "title": "Supplementids",
          "type": "array"
        },
        "checkIds": {
          "items": {
            "type": "string"
          },
          "maxItems": 50,
          "title": "Checkids",
          "type": "array"
        },
        "steps": {
          "default": "",
          "maxLength": 3000,
          "title": "Steps",
          "type": "string"
        },
        "result": {
          "default": "",
          "maxLength": 3000,
          "title": "Result",
          "type": "string"
        },
        "recipient": {
          "default": "",
          "maxLength": 200,
          "title": "Recipient",
          "type": "string"
        },
        "state": {
          "default": "",
          "maxLength": 50,
          "title": "State",
          "type": "string"
        },
        "source": {
          "default": "",
          "maxLength": 500,
          "title": "Source",
          "type": "string"
        },
        "previousRecordId": {
          "default": "",
          "title": "Previousrecordid",
          "type": "string"
        },
        "inputsFen": {
          "items": {
            "type": "integer"
          },
          "maxItems": 30,
          "title": "Inputsfen",
          "type": "array"
        },
        "operation": {
          "anyOf": [
            {
              "enum": [
                "sum",
                "difference"
              ],
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Operation"
        },
        "resultFen": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Resultfen"
        }
      },
      "required": [
        "expectedRevision",
        "nodeKey",
        "comment"
      ],
      "title": "ReviewRecordRequest",
      "type": "object"
    },
    "ReviewRequest": {
      "additionalProperties": false,
      "properties": {
        "decision": {
          "enum": [
            "approve",
            "reject"
          ],
          "title": "Decision",
          "type": "string"
        },
        "comment": {
          "default": "",
          "maxLength": 2000,
          "title": "Comment",
          "type": "string"
        },
        "interruptKey": {
          "maxLength": 200,
          "minLength": 1,
          "title": "Interruptkey",
          "type": "string"
        },
        "expectedRevision": {
          "minimum": 0,
          "title": "Expectedrevision",
          "type": "integer"
        },
        "supplementIds": {
          "items": {
            "type": "string"
          },
          "title": "Supplementids",
          "type": "array"
        },
        "coverageConfirmed": {
          "default": false,
          "title": "Coverageconfirmed",
          "type": "boolean"
        },
        "reviewCycleId": {
          "exclusiveMinimum": 0,
          "title": "Reviewcycleid",
          "type": "integer"
        },
        "reportVersion": {
          "exclusiveMinimum": 0,
          "title": "Reportversion",
          "type": "integer"
        },
        "basisHash": {
          "maxLength": 64,
          "minLength": 64,
          "title": "Basishash",
          "type": "string"
        }
      },
      "required": [
        "decision",
        "interruptKey",
        "expectedRevision",
        "reviewCycleId",
        "reportVersion",
        "basisHash"
      ],
      "title": "ReviewRequest",
      "type": "object"
    },
    "ReviewScope": {
      "properties": {
        "lossTypes": {
          "items": {
            "type": "string"
          },
          "title": "Losstypes",
          "type": "array"
        },
        "scopeLimitations": {
          "items": {
            "type": "string"
          },
          "title": "Scopelimitations",
          "type": "array"
        }
      },
      "required": [
        "lossTypes",
        "scopeLimitations"
      ],
      "title": "ReviewScope",
      "type": "object"
    },
    "ReviewScopeItem": {
      "properties": {
        "scopeItemId": {
          "title": "Scopeitemid",
          "type": "string"
        },
        "kind": {
          "title": "Kind",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "status": {
          "enum": [
            "executable",
            "limited",
            "blocked"
          ],
          "title": "Status",
          "type": "string"
        },
        "entityIds": {
          "items": {
            "type": "string"
          },
          "title": "Entityids",
          "type": "array"
        },
        "reason": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Reason"
        },
        "requiredMaterialTypes": {
          "items": {
            "type": "string"
          },
          "title": "Requiredmaterialtypes",
          "type": "array"
        }
      },
      "required": [
        "scopeItemId",
        "kind",
        "title",
        "status",
        "entityIds",
        "requiredMaterialTypes"
      ],
      "title": "ReviewScopeItem",
      "type": "object"
    },
    "ReviewState": {
      "additionalProperties": false,
      "properties": {
        "reviewModelVersion": {
          "const": 1,
          "title": "Reviewmodelversion",
          "type": "integer"
        },
        "checkPlan": {
          "items": {
            "$ref": "#/$defs/CheckPlanItem"
          },
          "title": "Checkplan",
          "type": "array"
        },
        "checks": {
          "items": {
            "$ref": "#/$defs/ReviewCheck"
          },
          "title": "Checks",
          "type": "array"
        },
        "findings": {
          "items": {
            "$ref": "#/$defs/Finding"
          },
          "title": "Findings",
          "type": "array"
        },
        "findingHistory": {
          "items": {
            "$ref": "#/$defs/Finding"
          },
          "title": "Findinghistory",
          "type": "array"
        },
        "records": {
          "items": {
            "$ref": "#/$defs/ReviewRecord"
          },
          "title": "Records",
          "type": "array"
        },
        "businessNodes": {
          "items": {
            "$ref": "#/$defs/BusinessNode"
          },
          "title": "Businessnodes",
          "type": "array"
        },
        "nodeHistory": {
          "items": {
            "$ref": "#/$defs/BusinessNode"
          },
          "title": "Nodehistory",
          "type": "array"
        },
        "reviewCycleId": {
          "title": "Reviewcycleid",
          "type": "integer"
        }
      },
      "required": [
        "reviewModelVersion",
        "checkPlan",
        "checks",
        "findings",
        "findingHistory",
        "records",
        "businessNodes",
        "nodeHistory",
        "reviewCycleId"
      ],
      "title": "ReviewState",
      "type": "object"
    },
    "ReviewTermRef": {
      "properties": {
        "documentId": {
          "title": "Documentid",
          "type": "string"
        },
        "version": {
          "title": "Version",
          "type": "string"
        },
        "sectionIds": {
          "items": {
            "type": "string"
          },
          "title": "Sectionids",
          "type": "array"
        }
      },
      "required": [
        "documentId",
        "version",
        "sectionIds"
      ],
      "title": "ReviewTermRef",
      "type": "object"
    },
    "ReviewTimelineEntry": {
      "properties": {
        "entryId": {
          "title": "Entryid",
          "type": "string"
        },
        "eventType": {
          "title": "Eventtype",
          "type": "string"
        },
        "occurredAt": {
          "title": "Occurredat",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "detail": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Detail"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "entryId",
        "eventType",
        "occurredAt",
        "title",
        "sources"
      ],
      "title": "ReviewTimelineEntry",
      "type": "object"
    },
    "ReviewUpdatedEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "review.updated",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/ReviewState"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "ReviewUpdatedEvent",
      "type": "object"
    },
    "ReviewVehicleDetail": {
      "properties": {
        "vehicleId": {
          "title": "Vehicleid",
          "type": "string"
        },
        "role": {
          "title": "Role",
          "type": "string"
        },
        "plateNumber": {
          "title": "Platenumber",
          "type": "string"
        },
        "ownerName": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Ownername"
        },
        "driverName": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Drivername"
        },
        "usage": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Usage"
        },
        "powerType": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Powertype"
        },
        "sources": {
          "items": {
            "$ref": "#/$defs/ReviewEvidenceSource"
          },
          "title": "Sources",
          "type": "array"
        }
      },
      "required": [
        "vehicleId",
        "role",
        "plateNumber",
        "sources"
      ],
      "title": "ReviewVehicleDetail",
      "type": "object"
    },
    "ReviewVehicleSummary": {
      "properties": {
        "vehicleId": {
          "title": "Vehicleid",
          "type": "string"
        },
        "role": {
          "title": "Role",
          "type": "string"
        },
        "plateNumber": {
          "title": "Platenumber",
          "type": "string"
        }
      },
      "required": [
        "vehicleId",
        "role",
        "plateNumber"
      ],
      "title": "ReviewVehicleSummary",
      "type": "object"
    },
    "RuleFinding": {
      "additionalProperties": false,
      "properties": {
        "code": {
          "title": "Code",
          "type": "string"
        },
        "source": {
          "const": "rule",
          "title": "Source",
          "type": "string"
        },
        "severity": {
          "enum": [
            "low",
            "medium",
            "high"
          ],
          "title": "Severity",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "detail": {
          "title": "Detail",
          "type": "string"
        },
        "factRefs": {
          "items": {
            "type": "string"
          },
          "title": "Factrefs",
          "type": "array"
        },
        "sourceValues": {
          "items": {
            "$ref": "#/$defs/SourceValue"
          },
          "title": "Sourcevalues",
          "type": "array"
        }
      },
      "required": [
        "code",
        "source",
        "severity",
        "title",
        "detail",
        "factRefs",
        "sourceValues"
      ],
      "title": "RuleFinding",
      "type": "object"
    },
    "SectionEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "report.section",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/ReportSection"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "SectionEvent",
      "type": "object"
    },
    "SourceValue": {
      "additionalProperties": false,
      "properties": {
        "factId": {
          "title": "Factid",
          "type": "string"
        },
        "value": {
          "$ref": "#/$defs/JsonValue"
        }
      },
      "required": [
        "factId",
        "value"
      ],
      "title": "SourceValue",
      "type": "object"
    },
    "StatusData": {
      "additionalProperties": false,
      "properties": {
        "status": {
          "enum": [
            "queued",
            "running",
            "waiting_review",
            "resuming",
            "recoverable",
            "completed",
            "rejected",
            "failed"
          ],
          "title": "Status",
          "type": "string"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        }
      },
      "required": [
        "status",
        "revision"
      ],
      "title": "StatusData",
      "type": "object"
    },
    "StatusEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "analysis.status",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/StatusData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "StatusEvent",
      "type": "object"
    },
    "SupplementPage": {
      "additionalProperties": false,
      "properties": {
        "page": {
          "exclusiveMinimum": 0,
          "title": "Page",
          "type": "integer"
        },
        "content": {
          "title": "Content",
          "type": "string"
        }
      },
      "required": [
        "page",
        "content"
      ],
      "title": "SupplementPage",
      "type": "object"
    },
    "SupplementedData": {
      "additionalProperties": false,
      "properties": {
        "supplement": {
          "$ref": "#/$defs/EvidenceSupplement"
        },
        "revision": {
          "title": "Revision",
          "type": "integer"
        }
      },
      "required": [
        "supplement",
        "revision"
      ],
      "title": "SupplementedData",
      "type": "object"
    },
    "SupplementedEvent": {
      "additionalProperties": false,
      "properties": {
        "schemaVersion": {
          "const": 2,
          "title": "Schemaversion",
          "type": "integer"
        },
        "analysisId": {
          "title": "Analysisid",
          "type": "string"
        },
        "conversationId": {
          "title": "Conversationid",
          "type": "string"
        },
        "seq": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Seq",
          "type": "integer"
        },
        "revision": {
          "minimum": 0,
          "title": "Revision",
          "type": "integer"
        },
        "at": {
          "format": "date-time",
          "title": "At",
          "type": "string"
        },
        "type": {
          "const": "evidence.supplemented",
          "title": "Type",
          "type": "string"
        },
        "data": {
          "$ref": "#/$defs/SupplementedData"
        }
      },
      "required": [
        "schemaVersion",
        "analysisId",
        "conversationId",
        "seq",
        "revision",
        "at",
        "type",
        "data"
      ],
      "title": "SupplementedEvent",
      "type": "object"
    },
    "V1KnowledgeAttempt": {
      "properties": {
        "attempt": {
          "maximum": 9007199254740991,
          "minimum": 1,
          "title": "Attempt",
          "type": "integer"
        },
        "status": {
          "enum": [
            "queued",
            "parsing",
            "chunking",
            "embedding",
            "ready",
            "failed"
          ],
          "title": "Status",
          "type": "string"
        },
        "startedAt": {
          "format": "date-time",
          "title": "Startedat",
          "type": "string"
        },
        "finishedAt": {
          "anyOf": [
            {
              "format": "date-time",
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Finishedat"
        },
        "error": {
          "anyOf": [
            {
              "$ref": "#/$defs/V1KnowledgeError"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "required": [
        "attempt",
        "status",
        "startedAt"
      ],
      "title": "V1KnowledgeAttempt",
      "type": "object"
    },
    "V1KnowledgeError": {
      "properties": {
        "code": {
          "title": "Code",
          "type": "string"
        },
        "message": {
          "title": "Message",
          "type": "string"
        },
        "reasonCode": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Reasoncode"
        },
        "providerCode": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Providercode"
        },
        "httpStatus": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Httpstatus"
        },
        "requestId": {
          "anyOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Requestid"
        },
        "retryAfter": {
          "anyOf": [
            {
              "type": "integer"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Retryafter"
        }
      },
      "required": [
        "code",
        "message"
      ],
      "title": "V1KnowledgeError",
      "type": "object"
    },
    "V1KnowledgeGeneration": {
      "properties": {
        "generationId": {
          "title": "Generationid",
          "type": "string"
        },
        "documentId": {
          "title": "Documentid",
          "type": "string"
        },
        "productCode": {
          "title": "Productcode",
          "type": "string"
        },
        "clauseVersion": {
          "title": "Clauseversion",
          "type": "string"
        },
        "fileName": {
          "title": "Filename",
          "type": "string"
        },
        "sha256": {
          "pattern": "^[a-f0-9]{64}$",
          "title": "Sha256",
          "type": "string"
        },
        "status": {
          "enum": [
            "queued",
            "parsing",
            "chunking",
            "embedding",
            "ready",
            "failed"
          ],
          "title": "Status",
          "type": "string"
        },
        "revision": {
          "maximum": 9007199254740991,
          "minimum": 1,
          "title": "Revision",
          "type": "integer"
        },
        "attempt": {
          "maximum": 9007199254740991,
          "minimum": 1,
          "title": "Attempt",
          "type": "integer"
        },
        "pageCount": {
          "maximum": 9007199254740991,
          "minimum": 0,
          "title": "Pagecount",
          "type": "integer"
        },
        "chunkCount": {
          "maximum": 9007199254740991,
          "minimum": 0,
          "title": "Chunkcount",
          "type": "integer"
        },
        "embeddedCount": {
          "maximum": 9007199254740991,
          "minimum": 0,
          "title": "Embeddedcount",
          "type": "integer"
        },
        "isActive": {
          "title": "Isactive",
          "type": "boolean"
        },
        "error": {
          "anyOf": [
            {
              "$ref": "#/$defs/V1KnowledgeError"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "createdAt": {
          "format": "date-time",
          "title": "Createdat",
          "type": "string"
        },
        "updatedAt": {
          "format": "date-time",
          "title": "Updatedat",
          "type": "string"
        },
        "attempts": {
          "items": {
            "$ref": "#/$defs/V1KnowledgeAttempt"
          },
          "title": "Attempts",
          "type": "array"
        }
      },
      "required": [
        "generationId",
        "documentId",
        "productCode",
        "clauseVersion",
        "fileName",
        "sha256",
        "status",
        "revision",
        "attempt",
        "pageCount",
        "chunkCount",
        "embeddedCount",
        "isActive",
        "createdAt",
        "updatedAt",
        "attempts"
      ],
      "title": "V1KnowledgeGeneration",
      "type": "object"
    },
    "V1KnowledgeRetry": {
      "properties": {
        "expectedRevision": {
          "maximum": 9007199254740991,
          "minimum": 1,
          "title": "Expectedrevision",
          "type": "integer"
        }
      },
      "required": [
        "expectedRevision"
      ],
      "title": "V1KnowledgeRetry",
      "type": "object"
    },
    "WorkspaceEvent": {
      "discriminator": {
        "mapping": {
          "analysis.failed": "#/$defs/FailureEvent",
          "analysis.ready": "#/$defs/ReadyEvent",
          "analysis.recoverable": "#/$defs/FailureEvent",
          "analysis.rejected": "#/$defs/RejectedEvent",
          "analysis.status": "#/$defs/StatusEvent",
          "business_node.completed": "#/$defs/BusinessNodeEvent",
          "business_node.failed": "#/$defs/BusinessNodeEvent",
          "business_node.not_applicable": "#/$defs/BusinessNodeEvent",
          "business_node.started": "#/$defs/BusinessNodeEvent",
          "business_node.unable": "#/$defs/BusinessNodeEvent",
          "evidence.supplemented": "#/$defs/SupplementedEvent",
          "finding.reviewed": "#/$defs/FindingReviewedEvent",
          "report.completed": "#/$defs/CompletedEvent",
          "report.saved": "#/$defs/ReportSavedEvent",
          "report.section": "#/$defs/SectionEvent",
          "review.accepted": "#/$defs/AcceptedEvent",
          "review.required": "#/$defs/ReviewEvent",
          "review.updated": "#/$defs/ReviewUpdatedEvent",
          "tool.completed": "#/$defs/ExecutionEvent",
          "tool.failed": "#/$defs/ExecutionEvent",
          "tool.started": "#/$defs/ExecutionEvent"
        },
        "propertyName": "type"
      },
      "oneOf": [
        {
          "$ref": "#/$defs/StatusEvent"
        },
        {
          "$ref": "#/$defs/ExecutionEvent"
        },
        {
          "$ref": "#/$defs/ReadyEvent"
        },
        {
          "$ref": "#/$defs/ReviewEvent"
        },
        {
          "$ref": "#/$defs/AcceptedEvent"
        },
        {
          "$ref": "#/$defs/SectionEvent"
        },
        {
          "$ref": "#/$defs/CompletedEvent"
        },
        {
          "$ref": "#/$defs/FailureEvent"
        },
        {
          "$ref": "#/$defs/RejectedEvent"
        },
        {
          "$ref": "#/$defs/SupplementedEvent"
        },
        {
          "$ref": "#/$defs/FindingReviewedEvent"
        },
        {
          "$ref": "#/$defs/ReportSavedEvent"
        },
        {
          "$ref": "#/$defs/BusinessNodeEvent"
        },
        {
          "$ref": "#/$defs/ReviewUpdatedEvent"
        }
      ],
      "title": "WorkspaceEvent"
    }
  }
} as const;

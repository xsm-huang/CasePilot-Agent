// Generated from Python Pydantic models by pnpm --filter @casepilot/contracts generate. Do not edit.
export const transportSchema = {
  "$defs": {
    "V0AnalysisReport": {
      "properties": {
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "summary": {
          "title": "Summary",
          "type": "string"
        },
        "findings": {
          "items": {
            "$ref": "#/$defs/V0Finding"
          },
          "title": "Findings",
          "type": "array"
        },
        "recommendation": {
          "title": "Recommendation",
          "type": "string"
        },
        "citations": {
          "items": {
            "$ref": "#/$defs/V0ClauseCitation"
          },
          "title": "Citations",
          "type": "array"
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
          "default": null,
          "title": "Reviewercomment"
        }
      },
      "required": [
        "caseId",
        "summary",
        "findings",
        "recommendation",
        "citations"
      ],
      "title": "V0AnalysisReport",
      "type": "object"
    },
    "V0AnalysisTask": {
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "caseId": {
          "title": "Caseid",
          "type": "string"
        },
        "status": {
          "enum": [
            "running",
            "waiting_review",
            "completed",
            "rejected",
            "failed"
          ],
          "title": "Status",
          "type": "string"
        },
        "events": {
          "items": {
            "$ref": "#/$defs/V0TimelineEvent"
          },
          "title": "Events",
          "type": "array"
        },
        "findings": {
          "items": {
            "$ref": "#/$defs/V0Finding"
          },
          "title": "Findings",
          "type": "array"
        },
        "citations": {
          "items": {
            "$ref": "#/$defs/V0ClauseCitation"
          },
          "title": "Citations",
          "type": "array"
        },
        "report": {
          "anyOf": [
            {
              "$ref": "#/$defs/V0AnalysisReport"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        },
        "review": {
          "anyOf": [
            {
              "$ref": "#/$defs/V0Review"
            },
            {
              "type": "null"
            }
          ],
          "default": null
        }
      },
      "required": [
        "id",
        "caseId",
        "status",
        "events",
        "findings",
        "citations"
      ],
      "title": "V0AnalysisTask",
      "type": "object"
    },
    "V0ClaimCase": {
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "claimant": {
          "title": "Claimant",
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
        "policyEffectiveDate": {
          "title": "Policyeffectivedate",
          "type": "string"
        },
        "accidentDate": {
          "title": "Accidentdate",
          "type": "string"
        },
        "claimAmount": {
          "title": "Claimamount",
          "type": "number"
        },
        "materials": {
          "items": {
            "$ref": "#/$defs/V0Material"
          },
          "title": "Materials",
          "type": "array"
        }
      },
      "required": [
        "id",
        "claimant",
        "productCode",
        "clauseVersion",
        "policyEffectiveDate",
        "accidentDate",
        "claimAmount",
        "materials"
      ],
      "title": "V0ClaimCase",
      "type": "object"
    },
    "V0Clause": {
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "productCode": {
          "title": "Productcode",
          "type": "string"
        },
        "version": {
          "title": "Version",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "content": {
          "title": "Content",
          "type": "string"
        },
        "keywords": {
          "items": {
            "type": "string"
          },
          "title": "Keywords",
          "type": "array"
        }
      },
      "required": [
        "id",
        "productCode",
        "version",
        "title",
        "content",
        "keywords"
      ],
      "title": "V0Clause",
      "type": "object"
    },
    "V0ClauseCitation": {
      "properties": {
        "id": {
          "title": "Id",
          "type": "string"
        },
        "title": {
          "title": "Title",
          "type": "string"
        },
        "content": {
          "title": "Content",
          "type": "string"
        },
        "score": {
          "title": "Score",
          "type": "number"
        }
      },
      "required": [
        "id",
        "title",
        "content",
        "score"
      ],
      "title": "V0ClauseCitation",
      "type": "object"
    },
    "V0Finding": {
      "properties": {
        "code": {
          "title": "Code",
          "type": "string"
        },
        "source": {
          "enum": [
            "rule",
            "ai"
          ],
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
        }
      },
      "required": [
        "code",
        "source",
        "severity",
        "title",
        "detail"
      ],
      "title": "V0Finding",
      "type": "object"
    },
    "V0Material": {
      "properties": {
        "type": {
          "title": "Type",
          "type": "string"
        },
        "name": {
          "title": "Name",
          "type": "string"
        },
        "fields": {
          "additionalProperties": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "number"
              }
            ]
          },
          "title": "Fields",
          "type": "object"
        }
      },
      "required": [
        "type",
        "name",
        "fields"
      ],
      "title": "V0Material",
      "type": "object"
    },
    "V0Review": {
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
        }
      },
      "required": [
        "decision"
      ],
      "title": "V0Review",
      "type": "object"
    },
    "V0ReviewAccepted": {
      "properties": {
        "accepted": {
          "const": true,
          "title": "Accepted",
          "type": "boolean"
        },
        "taskId": {
          "title": "Taskid",
          "type": "string"
        }
      },
      "required": [
        "accepted",
        "taskId"
      ],
      "title": "V0ReviewAccepted",
      "type": "object"
    },
    "V0TimelineEvent": {
      "properties": {
        "id": {
          "exclusiveMinimum": 0,
          "maximum": 9007199254740991,
          "title": "Id",
          "type": "integer"
        },
        "type": {
          "enum": [
            "status",
            "node",
            "tool",
            "review_required",
            "report",
            "error"
          ],
          "title": "Type",
          "type": "string"
        },
        "at": {
          "format": "date-time",
          "title": "At",
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
        "data": {
          "anyOf": [
            {
              "items": {
                "$ref": "#/$defs/V0Finding"
              },
              "type": "array"
            },
            {
              "items": {
                "$ref": "#/$defs/V0ClauseCitation"
              },
              "type": "array"
            },
            {
              "$ref": "#/$defs/V0AnalysisReport"
            },
            {
              "additionalProperties": true,
              "type": "object"
            },
            {
              "type": "null"
            }
          ],
          "default": null,
          "title": "Data"
        },
        "status": {
          "enum": [
            "running",
            "waiting_review",
            "completed",
            "rejected",
            "failed"
          ],
          "title": "Status",
          "type": "string"
        }
      },
      "required": [
        "id",
        "type",
        "at",
        "title",
        "status"
      ],
      "title": "V0TimelineEvent",
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
    }
  }
} as const;

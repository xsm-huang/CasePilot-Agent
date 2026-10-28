"""Build the versioned preparation contracts; never create case inputs or call providers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader
from pypdf import __version__ as PYPDF_VERSION

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared"
SCHEMA = "https://json-schema.org/draft/2020-12/schema"
BASE = "urn:casepilot:claims-review:v1:"
CHECK_ONLY = False


def obj(properties, required=None, **extra):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties) if required is None else required,
        **extra,
    }


def array(items, minimum=0, unique=False):
    result = {"type": "array", "items": items, "minItems": minimum}
    if unique:
        result["uniqueItems"] = True
    return result


def text(minimum=1):
    return {"type": "string", "minLength": minimum}


def nullable(value):
    return {"anyOf": [value, {"type": "null"}]}


def ref(name):
    return {"$ref": BASE + "common#/$defs/" + name}


def write(relative_path, value):
    path = ROOT / relative_path
    if CHECK_ONLY:
        assert path.is_file(), f"Missing generated file: {relative_path}"
        assert json.loads(path.read_text(encoding="utf-8")) == value, (
            f"Generated content drift: {relative_path}"
        )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


ENUMS = {
    "policyType": {"ctpl": "交强险", "commercial": "商业车险", "unknown": "保单类型未知"},
    "policyAvailability": {
        "available": "已取得",
        "not_obtained": "未取得",
        "not_insured": "已确认未投保",
        "unidentified": "无法识别承保情况",
    },
    "coverageStatus": {"insured": "已承保", "not_insured": "未承保", "unknown": "承保情况未知"},
    "coverageCode": {
        "CTPL": "机动车交通事故责任强制保险",
        "OWN_DAMAGE": "机动车损失保险",
        "THIRD_PARTY": "机动车第三者责任保险",
        "OCCUPANT_DRIVER": "车上人员责任保险（驾驶人）",
        "OCCUPANT_PASSENGER": "车上人员责任保险（乘客）",
        "RIDER_DEDUCTIBLE": "附加绝对免赔率特约条款",
        "RIDER_WHEEL": "附加车轮单独损失险",
        "RIDER_EQUIPMENT": "附加新增加设备损失险",
        "RIDER_SCRATCH": "附加车身划痕损失险",
        "RIDER_REPAIR_ALLOWANCE": "附加修理期间费用补偿险",
        "RIDER_ENGINE_WATER_EXCLUSION": "附加发动机进水损坏除外特约条款",
        "RIDER_CARGO": "附加车上货物责任险",
        "RIDER_MENTAL": "附加精神损害抚慰金责任险",
        "RIDER_HOLIDAY_LIMIT": "附加法定节假日限额翻倍险",
        "RIDER_NON_BASIC_MEDICAL": "附加医保外医疗费用责任险",
        "RIDER_SERVICE": "附加机动车增值服务特约条款",
        "UNKNOWN": "险种未知",
    },
    "closureType": {
        "paid_closed": "赔付结案",
        "refused_closed": "拒赔结案",
        "zero_closed": "零赔付结案",
        "other_closed": "其他结案",
        "unknown": "结案类型未知",
    },
    "originalPaymentStatus": {
        "settled": "已完成支付",
        "partial": "部分支付",
        "pending": "待支付",
        "failed": "支付失败",
        "not_applicable": "无支付事项",
        "unknown": "支付情况未知",
    },
    "transactionStatus": {
        "succeeded": "成功",
        "failed": "失败",
        "pending": "待处理",
        "cancelled": "已取消",
        "unknown": "状态未知",
    },
    "transactionKind": {"disbursement": "付款", "refund": "退款", "reversal": "冲销"},
    "amountStatus": {
        "known": "金额已知",
        "unknown": "金额未知",
        "not_applicable": "该金额口径不适用",
    },
    "automaticExecutionState": {
        "not_started": "未启动",
        "running": "执行中",
        "completed": "已结束",
        "failed": "执行失败",
        "awaiting_recovery": "待恢复",
    },
    "humanReviewState": {
        "pending_review": "待人工复核",
        "reviewing": "复核中",
        "pending_verification": "待核实",
        "vehicle_review_completed": "车损审查完成",
    },
    "professionalFollowUpState": {
        "not_referred": "未转交",
        "referred": "已转交",
        "received": "已接收",
        "opinion_recorded": "已记录专业意见",
        "resolved": "已明确作出复核决定",
    },
    "recordStatus": {
        "final": "有效最终记录",
        "draft": "草稿",
        "superseded": "已被后续记录替代",
        "unknown": "有效性未知",
    },
    "approvalStatus": {
        "approved": "审批通过",
        "rejected": "审批拒绝",
        "pending": "待审批",
        "superseded": "已被替代",
        "unknown": "审批状态未知",
    },
    "vehicleRole": {
        "insured": "被保险车辆",
        "third_party": "第三方车辆",
        "other": "其他车辆",
        "unknown": "归属未知",
    },
    "partyKind": {"person": "自然人", "organization": "组织", "unknown": "主体类型未知"},
    "personRelationship": {
        "insured_driver": "本车驾驶人",
        "insured_passenger": "本车乘客",
        "third_party": "第三方人员",
        "unknown": "身份未确定",
    },
    "declaredInjuryStatus": {
        "injury_reported": "原记录有人伤",
        "no_injury_reported": "原记录报告无人伤",
        "unknown": "原记录未明确",
    },
    "injuryStatus": {
        "no_injury_indication": "未发现人伤线索",
        "injury_present": "有人伤",
        "insufficient_information": "信息不足",
        "conflicting_information": "信息冲突",
    },
    "lossType": {
        "own_vehicle": "本车车辆损失",
        "third_party_vehicle": "第三方车辆损失",
        "other_property": "其他财产损失",
        "injury": "人伤",
        "unknown": "损失类型未知",
    },
    "materialType": {
        "ctpl_policy": "交强险保单",
        "commercial_policy": "商业险保单",
        "endorsement": "批单或特别约定",
        "claim_notification": "报案或初始申请记录",
        "accident_proof": "事故证明或协议",
        "survey": "查勘记录",
        "vehicle_driver_summary": "车辆驾驶人摘要",
        "assessment": "定损核损明细",
        "repair_cost": "维修清单及费用证明",
        "calculation": "赔款计算书",
        "approval": "核赔审批",
        "transaction": "支付退款冲销记录",
        "closure": "结案记录",
        "adjustment": "调整或损失确认",
        "injury_summary": "受伤情况",
        "medical_summary": "诊疗费用摘要",
        "collection_scope": "材料收集范围",
        "professional_opinion": "专业复核意见",
        "refusal_notice": "拒赔通知",
        "zero_closure_reason": "零赔付说明",
        "payment_authorization": "收款授权",
        "other": "其他材料",
    },
    "documentStatus": {
        "available": "可读取",
        "not_obtained": "未取得",
        "unreadable": "无法读取",
        "unsupported": "格式不支持",
        "partial": "仅取得部分内容",
    },
    "normalizationStatus": {
        "valid": "可归一化",
        "missing": "缺失",
        "invalid": "无效原值",
        "not_normalized": "尚未归一化",
    },
    "nodeId": {
        "archive": "档案整理与范围识别",
        "policy": "保单与承保险种核验",
        "materials": "材料一致性核对",
        "clauses": "条款检索与依据核对",
        "amounts": "金额与支付核对",
        "summary": "发现与报告汇总",
    },
    "checkStatus": {
        "not_started": "未开始",
        "running": "执行中",
        "completed": "已完成",
        "failed": "执行失败",
        "cannot_execute": "无法执行",
        "not_applicable": "不适用",
    },
    "findingSource": {"rule": "规则发现", "ai": "模型推断", "human": "人工补充"},
    "findingScope": {
        "vehicle": "车损范围",
        "injury": "人伤范围外",
        "shared_fact": "影响车损的共用事实",
    },
    "findingState": {
        "unreviewed": "待复核",
        "confirmed": "确认问题",
        "excluded": "排除疑点",
        "pending_evidence": "待补充核实",
        "referred": "转专业复核",
    },
    "decisionAction": {
        "confirm": "确认问题",
        "exclude": "排除疑点",
        "pending": "待补充核实",
        "refer": "转专业复核",
    },
    "reportStage": {
        "draft": "待复核报告",
        "interim": "阶段报告",
        "final_vehicle": "车损最终审查报告",
    },
    "gapKind": {
        "not_obtained": "本次未取得",
        "original_not_collected_confirmed": "有依据确认原作业未收集",
        "unreadable": "材料不可读",
        "unknown_value": "字段未知",
        "unresolved_conflict": "冲突未决",
        "other": "其他缺口",
    },
}


def build_dictionary():
    write(
        "shared/dictionaries.json",
        {
            "schemaVersion": 1,
            "dictionaryVersion": "1.0.0",
            "preparedOn": "2026-10-27",
            "status": "preparation_contract_not_runtime_implementation",
            "moneyUnit": "fen",
            "currency": "CNY",
            "rateUnit": "basis_points",
            "pageNumberBase": 1,
            "timestampPolicy": "ISO 8601 with explicit UTC offset or Z; never silently convert date-only facts to midnight",
            "enums": {
                name: [{"code": code, "label": label} for code, label in choices.items()]
                for name, choices in ENUMS.items()
            },
            "decisionToState": {
                "confirm": "confirmed",
                "exclude": "excluded",
                "pending": "pending_evidence",
                "refer": "referred",
            },
            "finalFindingStates": ["confirmed", "excluded"],
            "unresolvedFindingStates": ["unreviewed", "pending_evidence", "referred"],
            "principles": [
                "原赔案状态、自动执行状态、人工审查状态分别管理；结案不推断支付成功。",
                "空数组表示当前未列出记录，不单独证明不存在；未知字段保留null并记录资料缺口。",
                "reported injury status is an original declaration, not the Agent conclusion; expected injury status is stored only in expected data.",
                "confirmed/excluded require human evidence and comments; referral is unresolved.",
                "dictionary codes are dataset identifiers, not insurer official product or rule codes.",
            ],
        },
    )


def build_common():
    defs = {name: {"type": "string", "enum": list(choices)} for name, choices in ENUMS.items()}
    defs.update(
        {
            "id": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9._:-]{0,127}$"},
            "datasetCaseId": {"type": "string", "pattern": "^C[0-9]{2}(-V[0-9]{2})?$"},
            "revision": {"type": "integer", "minimum": 1},
            "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "pattern": "(Z|[+-][0-9]{2}:[0-9]{2})$",
            },
            "relativePath": {
                "type": "string",
                "minLength": 1,
                "pattern": "^(?![A-Za-z]:)(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[^\\\\]+$",
            },
            "primitive": {"type": ["string", "number", "boolean", "null"]},
            "ids": array(ref("id"), unique=True),
            "nullableText": nullable(text()),
            "money": obj(
                {
                    "status": ref("amountStatus"),
                    "amountFen": {
                        "type": ["integer", "null"],
                        "minimum": 0,
                        "maximum": 9007199254740991,
                    },
                    "currency": {"const": "CNY"},
                    "reason": nullable(text()),
                },
                allOf=[
                    {
                        "if": {"properties": {"status": {"const": "known"}}},
                        "then": {
                            "properties": {
                                "amountFen": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 9007199254740991,
                                },
                                "reason": {"type": "null"},
                            }
                        },
                        "else": {"properties": {"amountFen": {"type": "null"}, "reason": text()}},
                    },
                ],
            ),
            "clauseRef": obj(
                {
                    "documentId": ref("id"),
                    "documentSha256": ref("sha256"),
                    "version": text(),
                    "sectionIds": array(ref("id"), minimum=1, unique=True),
                }
            ),
            "decision": obj(
                {
                    "action": ref("decisionAction"),
                    "comment": text(5),
                    "evidenceRefs": ref("ids"),
                    "missingItems": array(text(), unique=True),
                    "followUpOwner": nullable(text()),
                    "professionalRecipient": nullable(text()),
                    "professionalReason": nullable(text()),
                },
                allOf=[
                    {
                        "if": {"properties": {"action": {"enum": ["confirm", "exclude"]}}},
                        "then": {
                            "properties": {"evidenceRefs": array(ref("id"), minimum=1, unique=True)}
                        },
                    },
                    {
                        "if": {"properties": {"action": {"const": "pending"}}},
                        "then": {
                            "properties": {
                                "missingItems": array(text(), minimum=1, unique=True),
                                "followUpOwner": text(),
                            }
                        },
                    },
                    {
                        "if": {"properties": {"action": {"const": "refer"}}},
                        "then": {
                            "properties": {
                                "professionalRecipient": text(),
                                "professionalReason": text(),
                            }
                        },
                    },
                ],
            ),
        }
    )
    write(
        "schemas/common.schema.json",
        {"$schema": SCHEMA, "$id": BASE + "common", "title": "准备资料共享定义", "$defs": defs},
    )


def record(properties):
    return obj(properties | {"evidenceRefs": ref("ids")})


def build_case():
    defs = {
        "party": record({"partyId": ref("id"), "displayName": text(), "kind": ref("partyKind")}),
        "vehicle": record(
            {
                "vehicleId": ref("id"),
                "role": ref("vehicleRole"),
                "plateNumber": nullable(text()),
                "ownerPartyId": nullable(ref("id")),
                "driverPartyId": nullable(ref("id")),
                "usage": nullable(text()),
                "powerType": {"enum": ["fuel", "new_energy", "other", "unknown"]},
            }
        ),
        "claim": record(
            {
                "claimId": ref("id"),
                "reportNumber": nullable(text()),
                "claimNumber": nullable(text()),
                "handlingOrganization": nullable(text()),
                "closureType": ref("closureType"),
                "closedAt": nullable(ref("timestamp")),
                "originalConclusion": nullable(text()),
                "originalPaymentStatus": ref("originalPaymentStatus"),
            }
        ),
        "coverage": record(
            {
                "coverageId": ref("id"),
                "coverageCode": ref("coverageCode"),
                "status": ref("coverageStatus"),
                "parentCoverageId": nullable(ref("id")),
                "insuranceAmount": ref("money"),
                "perAccidentLimit": ref("money"),
                "deductibleAmount": ref("money"),
                "deductibleBasisPoints": {
                    "type": ["integer", "null"],
                    "minimum": 0,
                    "maximum": 10000,
                },
                "terms": array(ref("clauseRef")),
                "specialConditions": nullable(text()),
            }
        ),
        "policy": record(
            {
                "policyId": ref("id"),
                "policyNumber": nullable(text()),
                "availability": ref("policyAvailability"),
                "policyType": ref("policyType"),
                "insurerCode": nullable(text()),
                "vehicleId": nullable(ref("id")),
                "policyholderPartyId": nullable(ref("id")),
                "insuredPartyIds": ref("ids"),
                "effectiveFrom": nullable(ref("timestamp")),
                "effectiveTo": nullable(ref("timestamp")),
                "coverages": array({"$ref": "#/$defs/coverage"}),
                "terms": array(ref("clauseRef")),
            }
        ),
        "endorsement": record(
            {
                "endorsementId": ref("id"),
                "policyId": ref("id"),
                "effectiveFrom": nullable(ref("timestamp")),
                "affectedCoverageIds": ref("ids"),
                "changeDescription": text(),
                "terms": array(ref("clauseRef")),
            }
        ),
        "loss": record(
            {
                "lossId": ref("id"),
                "claimId": ref("id"),
                "vehicleId": nullable(ref("id")),
                "personPartyId": nullable(ref("id")),
                "lossType": ref("lossType"),
                "description": text(),
                "claimedAmount": ref("money"),
                "assessedAmount": ref("money"),
                "agreedAmount": ref("money"),
            }
        ),
        "calculationLine": record(
            {
                "lineId": ref("id"),
                "lossId": ref("id"),
                "description": text(),
                "operation": {"enum": ["sum", "difference", "recorded_formula", "unknown"]},
                "inputs": array(obj({"name": text(), "amount": ref("money")})),
                "formulaText": nullable(text()),
                "result": ref("money"),
            }
        ),
        "calculation": record(
            {
                "calculationId": ref("id"),
                "claimId": ref("id"),
                "policyId": nullable(ref("id")),
                "coverageId": nullable(ref("id")),
                "status": ref("recordStatus"),
                "lines": array({"$ref": "#/$defs/calculationLine"}),
                "totalAmount": ref("money"),
                "adjustmentReason": nullable(text()),
            }
        ),
        "approval": record(
            {
                "approvalId": ref("id"),
                "claimId": ref("id"),
                "policyId": nullable(ref("id")),
                "coverageId": nullable(ref("id")),
                "calculationIds": ref("ids"),
                "lossIds": ref("ids"),
                "status": ref("approvalStatus"),
                "approvedAmount": ref("money"),
                "decidedAt": nullable(ref("timestamp")),
                "reason": nullable(text()),
            }
        ),
        "payment": record(
            {
                "paymentId": ref("id"),
                "claimId": ref("id"),
                "externalTransactionId": nullable(text()),
                "kind": ref("transactionKind"),
                "status": ref("transactionStatus"),
                "amount": ref("money"),
                "occurredAt": nullable(ref("timestamp")),
                "payeePartyId": nullable(ref("id")),
                "originalPaymentId": nullable(ref("id")),
                "approvalAllocations": array(
                    obj({"approvalId": ref("id"), "amount": ref("money")})
                ),
            },
        ),
        "document": obj(
            {
                "documentId": ref("id"),
                "title": text(),
                "materialType": ref("materialType"),
                "status": ref("documentStatus"),
                "version": text(),
                "relativePath": nullable(ref("relativePath")),
                "sha256": nullable(ref("sha256")),
                "pageCount": {"type": ["integer", "null"], "minimum": 1},
                "claimIds": ref("ids"),
                "entityIds": ref("ids"),
                "issuedAt": nullable(ref("timestamp")),
                "receivedAt": nullable(ref("timestamp")),
                "sourceDescription": text(),
                "isSynthetic": {"const": True},
            },
            allOf=[
                {
                    "if": {"properties": {"status": {"const": "available"}}},
                    "then": {
                        "properties": {
                            "relativePath": ref("relativePath"),
                            "sha256": ref("sha256"),
                            "pageCount": {"type": "integer", "minimum": 1},
                        }
                    },
                },
                {
                    "if": {"properties": {"status": {"const": "not_obtained"}}},
                    "then": {
                        "properties": {
                            "relativePath": {"type": "null"},
                            "sha256": {"type": "null"},
                            "pageCount": {"type": "null"},
                        }
                    },
                },
            ],
        ),
        "evidence": obj(
            {
                "evidenceId": ref("id"),
                "sourceType": {"enum": ["case_document", "shared_document", "structured_record"]},
                "documentId": nullable(ref("id")),
                "documentVersion": nullable(text()),
                "page": {"type": ["integer", "null"], "minimum": 1},
                "recordPointer": nullable({"type": "string", "pattern": "^/"}),
                "quote": nullable(text()),
                "provenance": {
                    "enum": [
                        "original_document",
                        "manual_transcription",
                        "structured_business_record",
                    ]
                },
            },
            allOf=[
                {
                    "if": {
                        "properties": {"sourceType": {"enum": ["case_document", "shared_document"]}}
                    },
                    "then": {
                        "properties": {
                            "documentId": ref("id"),
                            "documentVersion": text(),
                            "page": {"type": "integer", "minimum": 1},
                            "recordPointer": {"type": "null"},
                        }
                    },
                },
                {
                    "if": {"properties": {"sourceType": {"const": "structured_record"}}},
                    "then": {
                        "properties": {
                            "recordPointer": {"type": "string", "pattern": "^/"},
                            "page": {"type": "null"},
                            "documentId": {"type": "null"},
                            "documentVersion": {"type": "null"},
                        }
                    },
                },
            ],
        ),
        "observation": obj(
            {
                "observationId": ref("id"),
                "entityId": ref("id"),
                "fieldPath": text(),
                "rawValue": ref("primitive"),
                "normalizedValue": ref("primitive"),
                "normalizationStatus": ref("normalizationStatus"),
                "evidenceRefs": ref("ids"),
            },
            allOf=[
                {
                    "if": {
                        "properties": {
                            "normalizationStatus": {
                                "enum": ["missing", "invalid", "not_normalized"]
                            }
                        }
                    },
                    "then": {"properties": {"normalizedValue": {"type": "null"}}},
                },
            ],
        ),
        "gap": obj(
            {
                "gapId": ref("id"),
                "kind": ref("gapKind"),
                "entityIds": ref("ids"),
                "fieldPaths": array(text()),
                "description": text(),
                "evidenceRefs": ref("ids"),
            }
        ),
    }
    props = {
        "schemaVersion": {"const": 1},
        "dictionaryVersion": {"const": "1.0.0"},
        "datasetCaseId": ref("datasetCaseId"),
        "caseRevision": ref("revision"),
        "isSynthetic": {"const": True},
        "preparedAt": ref("timestamp"),
        "reviewScope": obj(
            {
                "targetClaimIds": array(ref("id"), 1, True),
                "relatedClaimIds": ref("ids"),
                "lossTypes": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "items": {"enum": ["own_vehicle", "third_party_vehicle"]},
                },
                "scopeLimitations": array(text()),
            }
        ),
        "accident": record(
            {
                "accidentId": ref("id"),
                "occurredAt": nullable(ref("timestamp")),
                "location": nullable(text()),
                "description": nullable(text()),
                "liabilityDescription": nullable(text()),
            }
        ),
        "parties": array({"$ref": "#/$defs/party"}),
        "vehicles": array({"$ref": "#/$defs/vehicle"}),
        "claims": array({"$ref": "#/$defs/claim"}, 1),
        "policies": array({"$ref": "#/$defs/policy"}),
        "endorsements": array({"$ref": "#/$defs/endorsement"}),
        "losses": array({"$ref": "#/$defs/loss"}),
        "calculations": array({"$ref": "#/$defs/calculation"}),
        "approvals": array({"$ref": "#/$defs/approval"}),
        "payments": array({"$ref": "#/$defs/payment"}),
        "documents": array({"$ref": "#/$defs/document"}),
        "evidence": array({"$ref": "#/$defs/evidence"}),
        "observations": array({"$ref": "#/$defs/observation"}),
        "dataGaps": array({"$ref": "#/$defs/gap"}),
        "knowledgeRefs": array(ref("clauseRef")),
        "injury": obj(
            {
                "declaredStatus": ref("declaredInjuryStatus"),
                "evidenceRefs": ref("ids"),
                "injuredPersons": array(
                    record(
                        {
                            "partyId": ref("id"),
                            "vehicleId": nullable(ref("id")),
                            "relationship": ref("personRelationship"),
                        }
                    )
                ),
            }
        ),
    }
    write(
        "schemas/case.schema.json",
        {
            "$schema": SCHEMA,
            "$id": BASE + "case",
            "title": "已结案车险审查输入档案",
            "description": "业务异常可以合法输入；引用完整性另作语义校验。禁止在输入中夹带标准答案。",
            **obj(props),
            "$defs": defs,
        },
    )


def build_expected():
    finding = obj(
        {
            "findingKey": ref("id"),
            "source": ref("findingSource"),
            "ruleId": nullable(ref("id")),
            "scope": ref("findingScope"),
            "entityIds": ref("ids"),
            "requiredMeaning": text(),
            "requiredEvidenceIds": ref("ids"),
            "prohibitedClaims": array(text()),
            "initialState": {"const": "unreviewed"},
            "expectedHumanAction": nullable(ref("decisionAction")),
            "humanRationale": nullable(text()),
        }
    )
    checkpoint = obj(
        {
            "checkpointId": ref("id"),
            "afterStepId": nullable(ref("id")),
            "reportStage": ref("reportStage"),
            "finalReportAllowed": {"type": "boolean"},
            "coverageConfirmedByHuman": {"type": "boolean"},
            "inScopeChecksComplete": {"type": "boolean"},
            "findingStates": array(
                obj(
                    {
                        "findingKey": ref("id"),
                        "scope": ref("findingScope"),
                        "state": ref("findingState"),
                    }
                )
            ),
            "requiredDisclosures": array(text()),
        },
        allOf=[
            {
                "if": {"properties": {"finalReportAllowed": {"const": True}}},
                "then": {
                    "properties": {
                        "reportStage": {"const": "final_vehicle"},
                        "coverageConfirmedByHuman": {"const": True},
                        "inScopeChecksComplete": {"const": True},
                        "findingStates": array(
                            obj(
                                {
                                    "findingKey": ref("id"),
                                    "scope": ref("findingScope"),
                                    "state": ref("findingState"),
                                },
                                allOf=[
                                    {
                                        "if": {
                                            "properties": {
                                                "scope": {"enum": ["vehicle", "shared_fact"]}
                                            }
                                        },
                                        "then": {
                                            "properties": {
                                                "state": {"enum": ["confirmed", "excluded"]}
                                            }
                                        },
                                    },
                                ],
                            )
                        ),
                    }
                },
            },
            {
                "if": {"properties": {"reportStage": {"const": "final_vehicle"}}},
                "then": {"properties": {"finalReportAllowed": {"const": True}}},
            },
        ],
    )
    props = {
        "schemaVersion": {"const": 1},
        "dictionaryVersion": {"const": "1.0.0"},
        "datasetCaseId": ref("datasetCaseId"),
        "caseRevision": ref("revision"),
        "isTestOracle": {"const": True},
        "annotatedBy": text(),
        "annotatedAt": ref("timestamp"),
        "annotationStatus": {"enum": ["draft", "reviewed"]},
        "annotationBasis": text(),
        "expectedInjuryStatus": ref("injuryStatus"),
        "expectedChecks": array(
            obj(
                {
                    "ruleId": ref("id"),
                    "nodeId": ref("nodeId"),
                    "status": ref("checkStatus"),
                    "reason": text(),
                }
            )
        ),
        "expectedFindings": array(finding),
        "forbiddenFindings": array(
            obj({"entityIds": ref("ids"), "prohibitedMeaning": text(), "reason": text()})
        ),
        "initialCheckpoint": checkpoint,
        "reviewCheckpoints": array(checkpoint),
        "reviewStepsFile": nullable(ref("relativePath")),
        "acceptanceIds": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "pattern": "^A(0[1-9]|1[0-9]|20)$"},
        },
    }
    props["initialCheckpoint"] = {
        "allOf": [
            checkpoint,
            {
                "type": "object",
                "properties": {
                    "finalReportAllowed": {"const": False},
                    "coverageConfirmedByHuman": {"const": False},
                },
            },
        ]
    }
    write(
        "schemas/expected.schema.json",
        {
            "$schema": SCHEMA,
            "$id": BASE + "expected",
            "title": "独立测试标准答案",
            "description": "按语义和证据匹配，不强制模型逐字复述；不得进入AI上下文或条款检索。",
            **obj(props),
        },
    )


def build_review_steps():
    payloads = {
        "inspect_finding": obj({"findingKey": ref("id"), "evidenceRefs": ref("ids")}),
        "decide_finding": obj({"findingKey": ref("id"), "decision": ref("decision")}),
        "amend_decision": obj(
            {"findingKey": ref("id"), "changeReason": text(5), "decision": ref("decision")}
        ),
        "provide_evidence": obj(
            {
                "findingKey": ref("id"),
                "supplementPackage": ref("relativePath"),
                "newEvidenceIds": array(ref("id"), 1, True),
                "note": text(),
            }
        ),
        "add_manual_finding": obj(
            {
                "findingKey": ref("id"),
                "scope": ref("findingScope"),
                "entityIds": ref("ids"),
                "description": text(5),
                "evidenceRefs": array(ref("id"), 1, True),
            }
        ),
        "record_professional_opinion": obj(
            {
                "findingKey": ref("id"),
                "professionalNameOrRole": text(),
                "opinion": text(5),
                "evidenceRefs": array(ref("id"), 1, True),
            }
        ),
        "confirm_coverage": obj({"comment": text(5), "checkIds": array(ref("id"), 1, True)}),
        "save_report": obj({"stage": ref("reportStage"), "comment": text(5)}),
        "start_reanalysis": obj({"newInputFile": ref("relativePath"), "reason": text(5)}),
    }
    actions = []
    for name, payload in payloads.items():
        actions.append(
            obj(
                {
                    "stepId": ref("id"),
                    "actorId": ref("id"),
                    "at": ref("timestamp"),
                    "action": {"const": name},
                    "expectedRevision": ref("revision"),
                    "idempotencyKey": text(),
                    "payload": payload,
                    "expectedOutcome": {"enum": ["accepted", "conflict", "validation_error"]},
                    "note": text(),
                }
            )
        )
    write(
        "schemas/review-steps.schema.json",
        {
            "$schema": SCHEMA,
            "$id": BASE + "review-steps",
            "title": "人工复核操作脚本",
            "description": "findingKey对应标准答案逻辑键，测试执行时匹配实际发现，不依赖模型生成的随机ID；脚本不是原理赔档案。",
            **obj(
                {
                    "schemaVersion": {"const": 1},
                    "datasetCaseId": ref("datasetCaseId"),
                    "caseRevision": ref("revision"),
                    "expectedFile": ref("relativePath"),
                    "steps": array({"oneOf": actions}, 1),
                }
            ),
        },
    )


def build_catalog():
    sources = json.loads((SHARED / "sources.json").read_text(encoding="utf-8"))
    records = {item["documentId"]: item for item in sources["documents"]}
    specs = {
        "PA-CTPL-2020-CONTENT": [
            ("CTPL-GENERAL", "总则", "总则", ["CTPL"], "context"),
            ("CTPL-DEFINITIONS", "定义", "定义", ["CTPL"], "context"),
            ("CTPL-LIABILITY", "保险责任", "保险责任", ["CTPL"], "contract"),
            ("CTPL-ADVANCE", "垫付与追偿", "垫付与追偿", ["CTPL"], "professional_reference"),
            ("CTPL-EXCLUSIONS", "责任免除", "责任免除", ["CTPL"], "contract"),
            ("CTPL-PERIOD", "保险期间", "保险期间", ["CTPL"], "context"),
            ("CTPL-DUTIES", "投保人、被保险人义务", "投保人、被保险人义务", ["CTPL"], "context"),
            ("CTPL-SETTLEMENT", "赔偿处理", "赔偿处理", ["CTPL"], "contract"),
            ("CTPL-CHANGES", "合同变更与终止", "合同变更与终止", ["CTPL"], "context"),
            ("CTPL-SUPPLEMENT", "附则", "附则", ["CTPL"], "context"),
        ],
        "PA-COMMERCIAL-MOTOR-2020": [
            ("COMM-GENERAL", "总则", "总则", [], "context"),
            ("COMM-OWN", "机动车损失保险", "第一章机动车损失保险", ["OWN_DAMAGE"], "contract"),
            (
                "COMM-THIRD",
                "机动车第三者责任保险",
                "第二章机动车第三者责任保险",
                ["THIRD_PARTY"],
                "contract",
            ),
            (
                "COMM-OCCUPANT",
                "机动车车上人员责任保险",
                "第三章机动车车上人员责任保险",
                ["OCCUPANT_DRIVER", "OCCUPANT_PASSENGER"],
                "injury_reference",
            ),
            ("COMM-COMMON", "通用条款", "第四章通用条款", [], "context"),
            ("COMM-RIDER-GENERAL", "附加险通用说明和目录", "附加险", [], "context"),
            (
                "COMM-RIDER-DEDUCTIBLE",
                "附加绝对免赔率特约条款",
                "附加绝对免赔率特约条款",
                ["RIDER_DEDUCTIBLE"],
                "contract",
            ),
            (
                "COMM-RIDER-WHEEL",
                "附加车轮单独损失险",
                "附加车轮单独损失险",
                ["RIDER_WHEEL"],
                "contract",
            ),
            (
                "COMM-RIDER-EQUIPMENT",
                "附加新增加设备损失险",
                "附加新增加设备损失险",
                ["RIDER_EQUIPMENT"],
                "contract",
            ),
            (
                "COMM-RIDER-SCRATCH",
                "附加车身划痕损失险",
                "附加车身划痕损失险",
                ["RIDER_SCRATCH"],
                "contract",
            ),
            (
                "COMM-RIDER-REPAIR",
                "附加修理期间费用补偿险",
                "附加修理期间费用补偿险",
                ["RIDER_REPAIR_ALLOWANCE"],
                "contract",
            ),
            (
                "COMM-RIDER-ENGINE",
                "附加发动机进水损坏除外特约条款",
                "附加发动机进水损坏除外特约条款",
                ["RIDER_ENGINE_WATER_EXCLUSION"],
                "contract",
            ),
            (
                "COMM-RIDER-CARGO",
                "附加车上货物责任险",
                "附加车上货物责任险",
                ["RIDER_CARGO"],
                "outside_vehicle_scope",
            ),
            (
                "COMM-RIDER-MENTAL",
                "附加精神损害抚慰金责任险",
                "附加精神损害抚慰金责任险",
                ["RIDER_MENTAL"],
                "injury_reference",
            ),
            (
                "COMM-RIDER-HOLIDAY",
                "附加法定节假日限额翻倍险",
                "附加法定节假日限额翻倍险",
                ["RIDER_HOLIDAY_LIMIT"],
                "contract",
            ),
            (
                "COMM-RIDER-MEDICAL",
                "附加医保外医疗费用责任险",
                "附加医保外医疗费用责任险",
                ["RIDER_NON_BASIC_MEDICAL"],
                "injury_reference",
            ),
            (
                "COMM-RIDER-SERVICE",
                "附加机动车增值服务特约条款",
                "附加机动车增值服务特约条款",
                ["RIDER_SERVICE"],
                "outside_vehicle_scope",
            ),
            ("COMM-DEFINITIONS", "释义", "释义", [], "context"),
        ],
    }
    catalog = []
    for document_id, source in records.items():
        path = SHARED / source["localFile"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"], path
        reader = PdfReader(path)
        pages = (
            [(p.extract_text() or "").splitlines() for p in reader.pages]
            if document_id in specs
            else [[] for _ in reader.pages]
        )
        sections = []
        for section_id, title, anchor, codes, scope in specs.get(document_id, []):
            candidates = [
                (p + 1, line + 1)
                for p, lines in enumerate(pages)
                for line, value in enumerate(lines)
                if re.sub(r"\s+", "", value) == anchor
            ]
            assert len(candidates) == 1, (document_id, section_id, candidates)
            page, line = candidates[0]
            sections.append(
                {
                    "sectionId": section_id,
                    "title": title,
                    "coverageCodes": codes,
                    "scope": scope,
                    "startPage": page,
                    "startLine": line,
                    "startAnchorNormalized": anchor,
                    "endPage": len(pages),
                    "endLine": len(pages[-1]),
                    "requiresActualCoverage": bool(codes),
                }
            )
        for current, following in zip(sections, sections[1:]):
            if following["startLine"] > 1:
                end_page, end_line = following["startPage"], following["startLine"] - 1
            else:
                end_page = following["startPage"] - 1
                end_line = len(pages[end_page - 1])
            current["endPage"], current["endLine"] = end_page, end_line
        for section in sections:
            page, line = section["endPage"], section["endLine"]
            while page >= section["startPage"]:
                if line < 1:
                    page -= 1
                    line = len(pages[page - 1]) if page >= 1 else 0
                    continue
                normalized = re.sub(r"\s+", "", pages[page - 1][line - 1])
                if normalized and normalized != str(page):
                    break
                line -= 1
            section["endPage"], section["endLine"] = page, line
            article_locations = []
            for page_index in range(section["startPage"], page + 1):
                first = section["startLine"] if page_index == section["startPage"] else 1
                last = line if page_index == page else len(pages[page_index - 1])
                for line_index in range(first, last + 1):
                    normalized = re.sub(r"\s+", "", pages[page_index - 1][line_index - 1])
                    match = re.match(r"^(第[一二三四五六七八九十百零〇]+条)", normalized)
                    if match:
                        article_locations.append(
                            {"article": match.group(1), "page": page_index, "line": line_index}
                        )
            section["articleLocations"] = article_locations
        catalog.append(
            {
                "documentId": document_id,
                "version": source["version"],
                "sha256": source["sha256"],
                "localFile": source["localFile"],
                "pageCount": len(pages),
                "category": source["category"],
                "eligibleForContractRetrieval": source["eligibleForContractRetrieval"],
                "sections": sections,
            }
        )
    write(
        "shared/clause-catalog.json",
        {
            "schemaVersion": 1,
            "catalogVersion": "1.0.0",
            "preparedOn": "2026-10-27",
            "sourceManifest": "sources.json",
            "pageNumberBase": 1,
            "lineNumberBase": 1,
            "extractor": {"library": "pypdf", "version": PYPDF_VERSION},
            "lineExtraction": "pypdf page.extract_text().splitlines(); whitespace removed only for anchor comparison; end boundary excludes blank lines and standalone page-number footers",
            "boundaryPolicy": "Inclusive page and line ranges in this exact source hash; adjacent sections may share a page. Preserve original PDF page numbers, use section anchors to distinguish same-page content and numbered table-of-contents mentions.",
            "matchingPolicy": [
                "匹配实际保单、产品、版本和SHA-256；不能按险种代码跨产品回退。",
                "通用章节要随适用险种上下文提供；目录出现某险种不构成承保或责任依据。",
                "人伤、车上货物和服务内容保留原文，但不扩展首期车损审查范围。",
                "服务规范、产品目录和空白模板不能进入合同责任正文检索。",
            ],
            "documents": catalog,
        },
    )


def build_rules():
    rules = []

    def add(
        code,
        title,
        node,
        inputs,
        prerequisites,
        operation,
        result,
        unknown,
        evidence,
        tests,
        basis=None,
    ):
        rules.append(
            {
                "ruleId": code,
                "title": title,
                "nodeId": node,
                "mode": "deterministic_data_check",
                "inputPaths": inputs,
                "preconditions": prerequisites,
                "operation": operation,
                "resultMeaning": result,
                "whenUnknown": unknown,
                "evidenceRequirements": evidence,
                "mustNotInfer": tests,
                "basis": basis
                or {
                    "type": "project_requirement",
                    "reference": "已结案车险赔案审查agent需求：资料一致性、范围及人工确认要求",
                },
                "findingInitialState": "unreviewed",
                "implementedInBusinessRuntime": False,
            }
        )

    add(
        "FACT-MISSING",
        "事实缺失",
        "materials",
        ["observations", "dataGaps"],
        ["已定义本次检查所需字段"],
        "列出normalizationStatus=missing或明确unknown_value缺口；区分not_obtained和original_not_collected_confirmed。",
        "资料缺口或待核实事项",
        "cannot_execute或对应事项pending_evidence，不使用0补值。",
        ["字段路径、材料收集范围和已知来源"],
        ["不能推断原作业违规或拒赔"],
    )
    add(
        "FACT-INVALID",
        "原始事实无效",
        "materials",
        ["observations"],
        ["原值已保留，归一化失败有记录"],
        "针对invalid观察值记录具体原值及错误；有效规范字段保留null，不把非法日期填入timestamp。",
        "原始数据质量线索",
        "未归一化不等同无效；留待核实。",
        ["observationId、fieldPath、rawValue、evidenceRefs"],
        ["不删除冲突来源，不猜测正确日期"],
    )
    add(
        "FACT-CONFLICT",
        "跨来源事实冲突",
        "materials",
        ["observations"],
        ["同一entityId和fieldPath存在两个及以上可比较有效观察"],
        "同一事实按明确单位和时区归一化后比较；不同有效值产生冲突线索；无效值由FACT-INVALID处理。",
        "存在不同来源值，非事实裁决",
        "精度或语义不一致时待核实，不强行比较。",
        ["所有冲突值及各自来源"],
        ["不得用多数票、材料顺序或模型偏好确定真值"],
    )
    add(
        "POLICY-AVAILABILITY",
        "保单和承保资料不足",
        "policy",
        ["policies", "reviewScope", "dataGaps"],
        ["已识别目标赔案及需要匹配的损失"],
        "分别展示available/not_obtained/not_insured/unidentified，检查目标损失关联的承保信息是否充分。",
        "适用性缺口或已确认承保事实",
        "受影响检查无法执行，其他项目继续。",
        ["保单或未取得说明，涉及的车辆和损失"],
        ["未取得不等于未投保，条款存在不等于已承保"],
    )
    add(
        "POLICY-PERIOD",
        "事故与保险期间比较",
        "policy",
        ["accident.occurredAt", "policies.effectiveFrom", "policies.effectiveTo", "endorsements"],
        ["时间精度和时区明确、来源无未决冲突，适用批改已明确"],
        "按实际保单约定解释起止边界；若约定无法解析则停止该项。将事故时间与已确认区间比较，保留原值和边界说明。",
        "时间不匹配线索，需人工核实",
        "cannot_execute/pending_evidence，日期精度不足不自动补零点。",
        ["事故来源、保单起止与相关批单"],
        ["不得直接输出拒赔；不得把交强险与商业险的期间合并"],
    )
    add(
        "POLICY-COVERAGE",
        "险种与原处理项目对应",
        "policy",
        ["policies.coverages", "calculations", "approvals", "losses"],
        ["已取得实际承保信息和项目归属"],
        "核对原理算或审批引用的coverageId所属保单及承保状态；明确未承保却出现对应处理时形成核实线索。",
        "承保或归属关系待核实",
        "未知承保不按未承保处理。",
        ["实际保单、处理记录与损失对象"],
        ["不得将第三方车辆费用计入本车损失，不自动判定违法赔付"],
    )
    add(
        "CLAUSE-BINDING",
        "条款版本及来源匹配",
        "clauses",
        ["knowledgeRefs", "policies.terms", "policies.coverages.terms", "endorsements.terms"],
        ["已有来源目录及准确文件hash"],
        "逐项核对documentId、version、SHA-256、sectionId及类别；匹配保单实际约定，禁止回退到相似产品。",
        "资料绑定有效或不匹配",
        "缺少适用信息则cannot_execute；不选择最新版本代替。",
        ["保单适用说明、原条款及目录"],
        ["元数据匹配不证明原文支持结论；不得把模板或服务规范当合同"],
    )
    add(
        "AMOUNT-LINE-SUM",
        "计算明细加总核对",
        "amounts",
        ["calculations.lines", "calculations.totalAmount"],
        ["同一有效计算记录、同一币种口径，金额均已知且项目组成完整"],
        "使用整数分求所有有效明细result.amountFen之和，与记录totalAmount.amountFen比较，精确到分不设隐含容差。",
        "算术差额事实",
        "金额未知、状态未知或组成不完整时不加总成0。",
        ["计算编号、明细、输入值、总额和差额"],
        ["算术一致不代表保险责任、价格或公式正确"],
    )
    add(
        "AMOUNT-RECORDED-OP",
        "明确记录的加减运算",
        "amounts",
        ["calculations.lines"],
        ["operation为sum或difference，顺序、输入、结果、币种明确且已知"],
        "sum为输入加总；difference为第一个输入依次减去后续输入。输入为空或出现负结果/未知值时标记无法确认。仅比较记录运算，不推导未给出的合同公式。",
        "明确算式与记录结果不一致线索",
        "recorded_formula和unknown不自动求值，转核实。",
        ["实际输入、运算、记录结果与原始计算书"],
        ["不执行任意字符串公式，不由模型随意选取免赔或责任比例"],
    )
    add(
        "AMOUNT-ADJUSTMENT",
        "不同金额口径及调整说明",
        "amounts",
        ["losses", "calculations.adjustmentReason", "approvals.reason"],
        ["同一损失和处理范围已明确"],
        "展示申请、定损、约定、理算、核赔的差额及已有说明。已有说明作为待核对依据，不直接确认其合理性。",
        "差异事实或需核实的说明缺口",
        "无法对齐范围时不比较整案总数。",
        ["各口径原值、调整意见及确认材料"],
        ["金额不同不直接等于多赔或少赔；说明存在也不自动证明合理"],
    )
    add(
        "PAYMENT-EFFECTIVE",
        "有效支付及退款冲销口径",
        "amounts",
        ["payments", "approvals"],
        ["目标审批、交易方向、状态、关联和币种明确"],
        "只纳入succeeded且分配范围明确的记录；付款为正，关联付款的成功退款为负。reversal按所引用交易的相反方向计入；按引用树核对部分金额，禁止循环引用或重复扣除。failed/pending/cancelled不计作已付。",
        "同一审批范围的可核对实付净额",
        "状态、重复导入、分配或冲销关系不明确时停止该范围净额结论，保留流水待核实。",
        ["交易编号、有效状态、原交易关联、审批分配及收款对象"],
        ["同一外部交易的重复导入不等于真实支付两次；不能简单全部加总"],
    )
    add(
        "PAYMENT-APPROVAL-GAP",
        "核赔与有效支付差额",
        "amounts",
        ["approvals", "payments"],
        ["同一审批口径，PAYMENT-EFFECTIVE可确认且审批金额已知"],
        "deltaFen=有效实付净额-审批金额；保留差额和待付、失败、补充审批等解释。差额为正负都仅先形成核实线索。",
        "支付与审批差异",
        "不能确定支付范围时cannot_execute，不推断少付。",
        ["审批、流水、分配及已有调整说明"],
        ["负差额不自动认定少赔，正差额不自动认定违规，不触发资金操作"],
    )
    add(
        "PAYMENT-DUPLICATE",
        "重复计入或支付线索",
        "amounts",
        ["losses", "calculations.lines", "payments"],
        ["可追溯到同一损失和记录关系"],
        "检查同一损失的多条记录及同一外部交易编号；分别区分多险种分摊、分笔支付、重复导入、失败重付与真实重复，查找冲销或退款依据。",
        "待人工核实的重复线索",
        "仅金额、名称相同不足以确认；关联不足时待核实。",
        ["损失ID、交易与计算记录、状态及冲销信息"],
        ["不得仅按出现次数或同金额确认重复赔付"],
    )
    add(
        "INJURY-IDENTIFICATION",
        "人伤四态与专业转交",
        "archive",
        ["injury", "observations", "documents", "dataGaps"],
        ["已读取实际可用资料并保留人伤声明及来源"],
        "将明确受伤记录和来源线索与原声明比较。有肯定证据且无矛盾则injury_present；有相反声明或关键冲突则conflicting_information；资料不够则insufficient_information。明确无伤声明和足够已读资料无相反线索时仅输出no_injury_indication。非结构化线索仍需模型或人工提取，不宣称字典本身能读懂病历。",
        "范围识别和专业转交提示",
        "不能把未填写字段或未读取材料推断为无人伤。",
        ["声明、受伤人员身份、实际材料或观察值"],
        ["不得自动审核医疗合理性、人伤赔款或伤残等级"],
    )
    add(
        "INJURY-SHARED-FACT",
        "人伤共用事实影响车损",
        "materials",
        ["observations", "losses", "injury"],
        ["人伤资料与车损共享的时间、责任等事实有依赖关系"],
        "共享事实未决时仅阻止受影响车损项目最终完成；无依赖车损检查可继续。独立范围外的人伤转交不单独阻止车损报告。",
        "影响范围和未决依赖",
        "依赖关系不明确时需要人工确认并披露。",
        ["冲突来源及受影响项目"],
        ["不能因有人伤停止所有车损检查，也不能忽略对车损有影响的冲突"],
    )
    add(
        "REPORT-COMPLETION",
        "车损最终报告门禁",
        "summary",
        ["checks", "findingStates", "humanCoverageConfirmation", "scopeLimitations"],
        ["本次范围和输入已固定"],
        "所有范围内必要检查完成，或有明确批准的范围调整和披露；车损/shared_fact疑点均confirmed或excluded；人员已确认覆盖与报告。范围外人伤可未决但必须披露。",
        "允许final_vehicle或只允许draft/interim",
        "失败、无法检查、未复核、待补件和范围内转专业未完结不能伪装成通过。",
        ["节点结果、逐条复核历史、人员确认及范围调整"],
        ["无疑点也需人工确认；问题确认不等于整改完成；不改写原赔案"],
    )
    write(
        "shared/review-rules.json",
        {
            "schemaVersion": 1,
            "ruleSetVersion": "1.0.0",
            "preparedOn": "2026-10-27",
            "status": "data_preparation_specification_not_executable_business_engine",
            "authority": "本项目审查需求及透明的数据核对口径；不是平安内部规则或自动赔付规范",
            "unknownPolicy": "unknown is not false, not zero, not not-applicable; retain provenance and request verification",
            "rules": rules,
            "paymentReconciliationContract": {
                "amountUnit": "integer_fen",
                "allocationRequirement": "Only reconcile a target approval when successful transaction allocations are explicit and sum to each transaction amount; otherwise show unknown allocation and stop that reconciliation.",
                "signs": {
                    "disbursement": "+1",
                    "refund": "-1",
                    "reversal": "-sign(originalPaymentId)",
                },
                "correctionRequirement": "Refund/reversal must link to an existing, originally effective transaction in the relevant scope. Keep original success and correction events separately; do not mark the original cancelled and subtract the correction again. Partial corrections require known amounts and matching allocations. Ambiguous or excessive corrections remain pending.",
                "excludedStatuses": ["failed", "pending", "cancelled"],
                "unknownStatus": "block affected net-amount result; never silently count zero",
                "duplicateExternalId": "Verify duplicate import vs actual duplicate transaction before summing; do not silently deduplicate genuine payments or count one imported transaction twice.",
                "netFen": "sum(sign(entry) * allocation.amountFen) for verified succeeded entries in the selected approval scope",
                "deltaFen": "netFen - approval.approvedAmount.amountFen",
                "conclusion": "delta is an arithmetic fact; underpayment/overpayment requires evidence and human review, not automatic settlement",
            },
            "requiresEvidenceAssistedReview": [
                {
                    "checkId": "CLAUSE-SEMANTIC-SUPPORT",
                    "nodeId": "clauses",
                    "description": "条款是否支持结论，是否遗漏限制或特别约定；不能由ID/hash匹配替代",
                    "outcomeWhenUncertain": "pending_evidence_or_professional_review",
                },
                {
                    "checkId": "REPAIR-PROFESSIONAL-JUDGMENT",
                    "nodeId": "amounts",
                    "description": "事故关联、维修必要性及价格合理性，需要明确资料与专业依据",
                    "outcomeWhenUncertain": "professional_review",
                },
                {
                    "checkId": "ENDORSEMENT-INTERPRETATION",
                    "nodeId": "policy",
                    "description": "批单及特别约定的适用或冲突含义，须结合完整合同核实",
                    "outcomeWhenUncertain": "pending_evidence_or_professional_review",
                },
            ],
            "semanticValidationBoundary": "JSON Schema验证形状、类型和条件；跨对象引用、唯一标识、条款hash/页码及操作前后关系另行校验。故意业务冲突属于合法测试输入，不在格式层当坏数据删除。",
        },
    )


def main():
    global CHECK_ONLY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated preparation files and source anchors without writing",
    )
    CHECK_ONLY = parser.parse_args().check
    build_dictionary()
    build_common()
    build_case()
    build_expected()
    build_review_steps()
    build_catalog()
    build_rules()
    print(
        ("Verified" if CHECK_ONLY else "Built")
        + " G02-G07 plus common.schema.json. No case inputs, answers, database or provider calls created."
    )


if __name__ == "__main__":
    main()

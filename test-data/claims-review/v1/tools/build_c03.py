"""Build the minimal C03 three-finding manual-review demonstration.

The first-review input intentionally omits the commercial third-party claim
calculation. The later calculation stays in supplements/C03 and is introduced
only by the review script.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from build_c01_c02 import (
    COMMERCIAL_TERMS,
    CTPL_TERMS,
    PREPARED_AT,
    document_spec,
    kv,
    make_table,
    money,
    na_money,
    render_pdf,
    sha256,
    table,
    text_section,
    write_json,
    yuan,
)


ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "C03"
TARGET_CLAIM = "CLM-C03-COM-TP"
RELATED_CLAIM = "CLM-C03-CTPL"


def build_documents() -> list[dict[str, Any]]:
    claims = [TARGET_CLAIM, RELATED_CLAIM]
    common = ["ACC-C03", "VEH-C03-A", "VEH-C03-B", "PTY-C03-INS", "PTY-C03-TP"]
    return [
        document_spec(
            CASE_ID,
            1,
            "交强险保单_演示.pdf",
            "机动车交通事故责任强制保险单（演示）",
            "ctpl_policy",
            "2026-02-01T00:00:00+08:00",
            [RELATED_CLAIM],
            ["POL-C03-CTPL", "CV-C03-CTPL", "VEH-C03-A", "PTY-C03-INS"],
            [
                kv(
                    "投保信息",
                    [
                        ["保单号", "DEMO-CTPL-C03-2026"],
                        ["投保人/被保险人", "陈某丁（虚构）"],
                        ["承保车辆", "演示-C03A / 家庭自用燃油车"],
                        ["保险期间", "2026-02-01 00:00 至 2027-01-31 23:59（北京时间）"],
                    ],
                ),
                table(
                    "承保险种",
                    ["险种", "本案财产损失限额", "免赔", "适用条款"],
                    [["机动车交通事故责任强制保险", yuan(200_000), "无", "CTPL-LIABILITY、CTPL-SETTLEMENT"]],
                    [47, 118, 52, 222],
                ),
            ],
            "虚构交强险保单；仅用于说明本案第三方财产损失的先行分摊。",
        ),
        document_spec(
            CASE_ID,
            2,
            "商业险保单_演示.pdf",
            "机动车商业保险单（演示）",
            "commercial_policy",
            "2026-02-01T00:00:00+08:00",
            [TARGET_CLAIM],
            ["POL-C03-COM", "CV-C03-TP", "VEH-C03-A", "PTY-C03-INS"],
            [
                kv(
                    "投保信息",
                    [
                        ["保单号", "DEMO-COM-C03-2026"],
                        ["投保人/被保险人", "陈某丁（虚构）"],
                        ["承保车辆", "演示-C03A / 家庭自用燃油车"],
                        ["保险期间", "2026-02-01 00:00 至 2027-01-31 23:59（北京时间）"],
                    ],
                ),
                table(
                    "实际承保险种",
                    ["险种", "每次事故限额", "免赔", "适用条款"],
                    [["机动车第三者责任保险", yuan(200_000_000), "0 元；0%", "COMM-THIRD、COMM-COMMON"]],
                    [118, 105, 76, 140],
                ),
            ],
            "虚构商业险保单；本案仅审查商业三者险目标赔案。",
        ),
        document_spec(
            CASE_ID,
            3,
            "报案记录_演示.pdf",
            "机动车保险报案记录（演示）",
            "claim_notification",
            "2026-06-08T09:35:00+08:00",
            claims,
            common,
            [
                kv(
                    "报案要素",
                    [
                        ["报案号", "DEMO-RPT-C03"],
                        ["出险时间", "2026-06-08 09:10"],
                        ["报案时间", "2026-06-08 09:35"],
                        ["地点", "南京市建邺区演练路与测试街路口（虚构地点）"],
                        ["事故经过", "演示-C03A 倒车驶出停车位时碰撞停放的演示-C03B。"],
                        ["初报损失", "第三方车辆右前部受损；第三方初报总损失 11,000.00 元。"],
                        ["人伤", "双方均明确无人受伤。"],
                    ],
                )
            ],
            "同一事故的交强险关联赔案和商业三者险目标赔案共用报案记录。",
        ),
        document_spec(
            CASE_ID,
            4,
            "事故证明及责任记录_演示.pdf",
            "道路交通事故责任记录（演示）",
            "accident_proof",
            "2026-06-08T10:20:00+08:00",
            claims,
            common,
            [
                kv(
                    "事故与责任",
                    [
                        ["事故编号", "DEMO-ACC-C03"],
                        ["事故时间/地点", "2026-06-08 09:10 / 南京市建邺区演练路与测试街路口（虚构地点）"],
                        ["责任方", "陈某丁（虚构），驾驶演示-C03A"],
                        ["第三方", "吴某戊（虚构），演示-C03B 所有人"],
                        ["责任记录", "演示-C03A 驾驶人承担全部责任；第三方无责任。"],
                        ["人员情况", "无人受伤。"],
                    ],
                )
            ],
            "虚构事故责任记录，不对应真实交管文书。",
        ),
        document_spec(
            CASE_ID,
            5,
            "查勘报告_演示.pdf",
            "机动车保险现场查勘报告（演示）",
            "survey",
            "2026-06-08T11:00:00+08:00",
            claims,
            ["ACC-C03", "VEH-C03-A", "VEH-C03-B", "LOSS-C03-CTPL", "LOSS-C03-COM-TP"],
            [
                kv(
                    "查勘结论",
                    [
                        ["承保车辆", "演示-C03A，左后保险杠轻微擦痕，不在本次赔付申请范围。"],
                        ["第三方车辆", "演示-C03B，右前保险杠及右前灯受损。"],
                        ["痕迹核对", "右前灯新鲜碰撞痕迹与事故相符；右前保险杠下沿存在方向不符的旧划痕。"],
                        ["初步处理", "第三方新损进入定损；旧划痕单独剔除并需形成金额确认。"],
                        ["人伤", "无人伤。"],
                    ],
                )
            ],
            "查勘记录已区分本次新损与第三方车辆旧划痕。",
        ),
        document_spec(
            CASE_ID,
            6,
            "车辆及驾驶人资料摘要_演示.pdf",
            "车辆及驾驶人资料摘要（演示）",
            "vehicle_driver_summary",
            "2026-06-08T12:00:00+08:00",
            claims,
            ["VEH-C03-A", "VEH-C03-B", "PTY-C03-INS", "PTY-C03-TP"],
            [
                table(
                    "车辆及人员",
                    ["车辆", "角色", "所有人/驾驶人", "使用性质", "核对结果"],
                    [
                        ["演示-C03A", "承保车辆", "陈某丁（虚构）", "家庭自用", "与两份保单一致"],
                        ["演示-C03B", "第三方车辆", "吴某戊（虚构）", "家庭自用", "与事故和定损材料一致"],
                    ],
                    [77, 73, 103, 69, 135],
                ),
                text_section("隐私边界", ["不包含真实身份证、驾驶证、行驶证或联系方式。"]),
            ],
            "对象一致性检查所需的虚构摘要。",
        ),
        document_spec(
            CASE_ID,
            7,
            "第三方车辆定损及核损明细_演示.pdf",
            "第三方车辆定损及核损明细（演示）",
            "assessment",
            "2026-06-10T14:00:00+08:00",
            [TARGET_CLAIM, RELATED_CLAIM],
            ["LOSS-C03-CTPL", "LOSS-C03-COM-TP", "VEH-C03-B"],
            [
                kv(
                    "金额口径",
                    [
                        ["第三方初报总损失", yuan(1_100_000)],
                        ["核定本次事故总损失", yuan(1_000_000)],
                        ["调整金额", yuan(100_000)],
                        ["调整原因", "第三方车辆右前保险杠下沿旧划痕与本次碰撞方向不符。"],
                    ],
                ),
                table(
                    "核损项目",
                    ["项目", "本次核定金额"],
                    [["右前保险杠本次事故维修", yuan(480_000)], ["右前灯更换", yuan(390_000)], ["工时及喷漆", yuan(130_000)], ["合计", yuan(1_000_000)]],
                    [285, 154],
                ),
            ],
            "第三方车辆总损失核定材料；险种分摊计算书首次审查时未取得。",
        ),
        document_spec(
            CASE_ID,
            8,
            "第三方维修清单及费用证明_演示.pdf",
            "第三方维修清单及费用证明（演示）",
            "repair_cost",
            "2026-06-13T16:00:00+08:00",
            [TARGET_CLAIM, RELATED_CLAIM],
            ["LOSS-C03-CTPL", "LOSS-C03-COM-TP", "VEH-C03-B"],
            [
                table(
                    "维修结算",
                    ["项目", "金额"],
                    [["右前保险杠本次事故维修", yuan(480_000)], ["右前灯更换", yuan(390_000)], ["工时及喷漆", yuan(130_000)], ["合计", yuan(1_000_000)]],
                    [285, 154],
                ),
                text_section("凭证边界", ["演示费用证明，不含真实发票号码、税控信息或查验凭证。"]),
            ],
            "第三方车辆虚构维修结算摘要。",
        ),
        document_spec(
            CASE_ID,
            9,
            "损失确认或金额调整说明_演示.pdf",
            "损失确认及金额调整说明（演示）",
            "adjustment",
            "2026-06-11T10:30:00+08:00",
            [TARGET_CLAIM],
            ["LOSS-C03-COM-TP", "VEH-C03-B", "PTY-C03-TP"],
            [
                kv(
                    "确认内容",
                    [
                        ["第三方初报总损失", yuan(1_100_000)],
                        ["交强险先行分摊", yuan(200_000)],
                        ["商业三者险初始申请", yuan(900_000)],
                        ["剔除旧划痕", yuan(100_000)],
                        ["商业三者险最终认可", yuan(800_000)],
                        ["确认意见", "第三方车辆所有人认可旧划痕不属于本次事故，按本次事故总损失 10,000.00 元处理。"],
                    ],
                ),
                text_section("用途", ["本说明只支持申请金额与最终认可金额的合理调整，不解释商业三者险审批 8,000.00 元与实际支付 9,000.00 元之间的差额。"]),
            ],
            "S01：支持合理金额调整的独立演示材料。",
        ),
        document_spec(
            CASE_ID,
            10,
            "核赔审批意见_演示.pdf",
            "核赔审批意见汇总（演示）",
            "approval",
            "2026-06-14T11:00:00+08:00",
            claims,
            ["APR-C03-CTPL", "APR-C03-COM-TP"],
            [
                table(
                    "审批项目",
                    ["赔案", "险种", "审批金额", "状态", "理由"],
                    [
                        ["DEMO-CLM-C03-CTPL", "交强险财产损失", yuan(200_000), "通过", "在财产损失限额内"],
                        ["DEMO-CLM-C03-COM-TP", "商业三者险", yuan(800_000), "通过", "总损失 10,000.00 元扣除交强险 2,000.00 元"],
                    ],
                    [115, 87, 83, 51, 125],
                ),
                text_section("首次审查材料状态", ["审批记录引用了商业三者险计算结论，但对应赔款计算书未随首次档案提供。"]),
            ],
            "目标赔案审批金额为 8,000.00 元。",
        ),
        document_spec(
            CASE_ID,
            11,
            "支付及冲销记录_演示.pdf",
            "支付及冲销记录（演示）",
            "transaction",
            "2026-06-15T10:00:00+08:00",
            claims,
            ["PAY-C03-CTPL", "PAY-C03-COM-TP", "PTY-C03-TP"],
            [
                table(
                    "有效交易",
                    ["交易号", "赔案", "收款对象", "金额", "状态", "审批分配"],
                    [
                        ["DEMO-TXN-C03-001", "CTPL", "吴某戊（虚构）", yuan(200_000), "成功", "APR-C03-CTPL：2,000.00 元"],
                        ["DEMO-TXN-C03-002", "COM-TP", "吴某戊（虚构）", yuan(900_000), "成功", "APR-C03-COM-TP：9,000.00 元"],
                    ],
                    [95, 49, 85, 70, 48, 112],
                ),
                text_section("冲销核对", ["无失败付款、退款、冲销、重付或其他商业三者险审批。商业三者险有效支付比审批金额多 1,000.00 元，需人工确认。"]),
            ],
            "目标赔案存在审批与有效支付差额的虚构支付记录。",
        ),
        document_spec(
            CASE_ID,
            12,
            "结案记录_演示.pdf",
            "赔案结案记录汇总（演示）",
            "closure",
            "2026-06-15T16:30:00+08:00",
            claims,
            claims + ["PAY-C03-CTPL", "PAY-C03-COM-TP"],
            [
                table(
                    "原结案记录",
                    ["赔案号", "范围", "结案类型", "原支付状态", "记录金额"],
                    [
                        ["DEMO-CLM-C03-CTPL", "关联赔案", "已赔付结案", "已结清", yuan(200_000)],
                        ["DEMO-CLM-C03-COM-TP", "目标赔案", "已赔付结案", "已结清", yuan(900_000)],
                    ],
                    [128, 72, 76, 73, 90],
                ),
                text_section("审查边界", ["结案状态是原业务事实，不代表金额处理正确。商业三者险审批金额与支付金额仍须独立核对。"]),
            ],
            "保留原结案状态，不因审查疑点改写原业务记录。",
        ),
    ]


def build_case(docs: list[dict[str, Any]]) -> dict[str, Any]:
    ev = lambda seq: f"EV-DOC-C03-{seq:02d}"
    commercial_term = {**COMMERCIAL_TERMS, "sectionIds": ["COMM-THIRD", "COMM-COMMON"]}
    case: dict[str, Any] = {
        "schemaVersion": 1,
        "dictionaryVersion": "1.0.0",
        "datasetCaseId": CASE_ID,
        "caseRevision": 1,
        "isSynthetic": True,
        "preparedAt": PREPARED_AT,
        "reviewScope": {
            "targetClaimIds": [TARGET_CLAIM],
            "relatedClaimIds": [RELATED_CLAIM],
            "lossTypes": ["third_party_vehicle"],
            "scopeLimitations": ["目标范围仅为商业三者险赔案；交强险赔案作为第三方损失分摊的关联记录展示。首次审查未取得商业三者险赔款计算书。"],
        },
        "accident": {
            "accidentId": "ACC-C03",
            "occurredAt": "2026-06-08T09:10:00+08:00",
            "location": "南京市建邺区演练路与测试街路口（虚构地点）",
            "description": "演示-C03A 倒车驶出停车位时碰撞停放的演示-C03B。",
            "liabilityDescription": "演示-C03A 驾驶人承担全部责任；第三方无责任。",
            "evidenceRefs": [ev(3), ev(4), ev(5)],
        },
        "parties": [
            {"partyId": "PTY-C03-INS", "displayName": "陈某丁（虚构）", "kind": "person", "evidenceRefs": [ev(1), ev(2), ev(6)]},
            {"partyId": "PTY-C03-TP", "displayName": "吴某戊（虚构）", "kind": "person", "evidenceRefs": [ev(4), ev(6), ev(9)]},
        ],
        "vehicles": [
            {"vehicleId": "VEH-C03-A", "role": "insured", "plateNumber": "演示-C03A", "ownerPartyId": "PTY-C03-INS", "driverPartyId": "PTY-C03-INS", "usage": "家庭自用", "powerType": "fuel", "evidenceRefs": [ev(1), ev(2), ev(6)]},
            {"vehicleId": "VEH-C03-B", "role": "third_party", "plateNumber": "演示-C03B", "ownerPartyId": "PTY-C03-TP", "driverPartyId": "PTY-C03-TP", "usage": "家庭自用", "powerType": "fuel", "evidenceRefs": [ev(4), ev(6)]},
        ],
        "claims": [
            {"claimId": TARGET_CLAIM, "reportNumber": "DEMO-RPT-C03", "claimNumber": "DEMO-CLM-C03-COM-TP", "handlingOrganization": "平安产险演示机构", "closureType": "paid_closed", "closedAt": "2026-06-15T16:30:00+08:00", "originalConclusion": "商业三者险记录支付 9,000.00 元后结案。", "originalPaymentStatus": "settled", "evidenceRefs": [ev(10), ev(11), ev(12)]},
            {"claimId": RELATED_CLAIM, "reportNumber": "DEMO-RPT-C03", "claimNumber": "DEMO-CLM-C03-CTPL", "handlingOrganization": "平安产险演示机构", "closureType": "paid_closed", "closedAt": "2026-06-15T16:30:00+08:00", "originalConclusion": "交强险财产损失支付 2,000.00 元后结案。", "originalPaymentStatus": "settled", "evidenceRefs": [ev(10), ev(11), ev(12)]},
        ],
        "policies": [
            {"policyId": "POL-C03-CTPL", "policyNumber": "DEMO-CTPL-C03-2026", "availability": "available", "policyType": "ctpl", "insurerCode": "PINGAN", "vehicleId": "VEH-C03-A", "policyholderPartyId": "PTY-C03-INS", "insuredPartyIds": ["PTY-C03-INS"], "effectiveFrom": "2026-02-01T00:00:00+08:00", "effectiveTo": "2027-01-31T23:59:59+08:00", "coverages": [{"coverageId": "CV-C03-CTPL", "coverageCode": "CTPL", "status": "insured", "parentCoverageId": None, "insuranceAmount": na_money("交强险使用分项责任限额口径"), "perAccidentLimit": money(200_000), "deductibleAmount": money(0), "deductibleBasisPoints": 0, "terms": [CTPL_TERMS], "specialConditions": "本演示事故只使用财产损失限额。", "evidenceRefs": [ev(1)]}], "terms": [CTPL_TERMS], "evidenceRefs": [ev(1)]},
            {"policyId": "POL-C03-COM", "policyNumber": "DEMO-COM-C03-2026", "availability": "available", "policyType": "commercial", "insurerCode": "PINGAN", "vehicleId": "VEH-C03-A", "policyholderPartyId": "PTY-C03-INS", "insuredPartyIds": ["PTY-C03-INS"], "effectiveFrom": "2026-02-01T00:00:00+08:00", "effectiveTo": "2027-01-31T23:59:59+08:00", "coverages": [{"coverageId": "CV-C03-TP", "coverageCode": "THIRD_PARTY", "status": "insured", "parentCoverageId": None, "insuranceAmount": na_money("本险种使用每次事故责任限额口径"), "perAccidentLimit": money(200_000_000), "deductibleAmount": money(0), "deductibleBasisPoints": 0, "terms": [commercial_term], "specialConditions": "第三方财产损失先由交强险分摊，剩余部分进入商业三者险。", "evidenceRefs": [ev(2)]}], "terms": [commercial_term], "evidenceRefs": [ev(2)]},
        ],
        "endorsements": [],
        "losses": [
            {"lossId": "LOSS-C03-CTPL", "claimId": RELATED_CLAIM, "vehicleId": "VEH-C03-B", "personPartyId": None, "lossType": "third_party_vehicle", "description": "第三方车辆核定总损失中由交强险财产损失限额分摊的部分。", "claimedAmount": money(200_000), "assessedAmount": money(200_000), "agreedAmount": money(200_000), "evidenceRefs": [ev(7), ev(8), ev(10)]},
            {"lossId": "LOSS-C03-COM-TP", "claimId": TARGET_CLAIM, "vehicleId": "VEH-C03-B", "personPartyId": None, "lossType": "third_party_vehicle", "description": "第三方车辆本次事故总损失扣除交强险分摊后的商业三者险部分。", "claimedAmount": money(900_000), "assessedAmount": money(800_000), "agreedAmount": money(800_000), "evidenceRefs": [ev(7), ev(8), ev(9)]},
        ],
        "calculations": [
            {"calculationId": "CALC-C03-CTPL", "claimId": RELATED_CLAIM, "policyId": "POL-C03-CTPL", "coverageId": "CV-C03-CTPL", "status": "final", "lines": [{"lineId": "LINE-C03-CTPL", "lossId": "LOSS-C03-CTPL", "description": "交强险财产损失限额内分摊", "operation": "recorded_formula", "inputs": [{"name": "第三方核定总损失", "amount": money(1_000_000)}, {"name": "交强险财产损失限额", "amount": money(200_000)}], "formulaText": "min(1000000, 200000)", "result": money(200_000), "evidenceRefs": [ev(7), ev(10)]}], "totalAmount": money(200_000), "adjustmentReason": "第三方车辆本次事故核定总损失 10,000.00 元，先按交强险财产损失限额分摊 2,000.00 元。", "evidenceRefs": [ev(10)]}
        ],
        "approvals": [
            {"approvalId": "APR-C03-CTPL", "claimId": RELATED_CLAIM, "policyId": "POL-C03-CTPL", "coverageId": "CV-C03-CTPL", "calculationIds": ["CALC-C03-CTPL"], "lossIds": ["LOSS-C03-CTPL"], "status": "approved", "approvedAmount": money(200_000), "decidedAt": "2026-06-14T10:55:00+08:00", "reason": "交强险财产损失限额内分摊。", "evidenceRefs": [ev(10)]},
            {"approvalId": "APR-C03-COM-TP", "claimId": TARGET_CLAIM, "policyId": "POL-C03-COM", "coverageId": "CV-C03-TP", "calculationIds": [], "lossIds": ["LOSS-C03-COM-TP"], "status": "approved", "approvedAmount": money(800_000), "decidedAt": "2026-06-14T11:00:00+08:00", "reason": "第三方本次事故总损失 10,000.00 元扣除交强险 2,000.00 元后，商业三者险审批 8,000.00 元；首次审查未取得对应计算书。", "evidenceRefs": [ev(9), ev(10)]},
        ],
        "payments": [
            {"paymentId": "PAY-C03-CTPL", "claimId": RELATED_CLAIM, "externalTransactionId": "DEMO-TXN-C03-001", "kind": "disbursement", "status": "succeeded", "amount": money(200_000), "occurredAt": "2026-06-15T10:00:00+08:00", "payeePartyId": "PTY-C03-TP", "originalPaymentId": None, "approvalAllocations": [{"approvalId": "APR-C03-CTPL", "amount": money(200_000)}], "evidenceRefs": [ev(11)]},
            {"paymentId": "PAY-C03-COM-TP", "claimId": TARGET_CLAIM, "externalTransactionId": "DEMO-TXN-C03-002", "kind": "disbursement", "status": "succeeded", "amount": money(900_000), "occurredAt": "2026-06-15T10:10:00+08:00", "payeePartyId": "PTY-C03-TP", "originalPaymentId": None, "approvalAllocations": [{"approvalId": "APR-C03-COM-TP", "amount": money(900_000)}], "evidenceRefs": [ev(11)]},
        ],
        "documents": [],
        "evidence": [],
        "observations": [],
        "dataGaps": [{"gapId": "GAP-C03-CALC", "kind": "not_obtained", "entityIds": [TARGET_CLAIM, "APR-C03-COM-TP"], "fieldPaths": ["calculations"], "description": "首次审查档案未取得商业三者险赔款计算书，无法仅依据首次输入复核 8,000.00 元的险种分摊计算。", "evidenceRefs": ["EV-C03-CALC-GAP"]}],
        "knowledgeRefs": [CTPL_TERMS, commercial_term],
        "injury": {"declaredStatus": "no_injury_reported", "evidenceRefs": [ev(3), ev(4), ev(5)], "injuredPersons": []},
    }

    case_dir = ROOT / "inputs" / CASE_ID
    documents_dir = case_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    built_docs = []
    evidence = []
    for spec in docs:
        pdf_path = documents_dir / spec["filename"]
        render_pdf(pdf_path, spec)
        built_docs.append(
            {
                "documentId": spec["document_id"],
                "title": spec["title"],
                "materialType": spec["material_type"],
                "status": "available",
                "version": "v1",
                "relativePath": f"documents/{spec['filename']}",
                "sha256": sha256(pdf_path),
                "pageCount": len(PdfReader(str(pdf_path)).pages),
                "claimIds": spec["claim_ids"],
                "entityIds": spec["entity_ids"],
                "issuedAt": spec["issued_at"],
                "receivedAt": spec["received_at"],
                "sourceDescription": spec["source_description"],
                "isSynthetic": True,
            }
        )
        evidence.append(
            {
                "evidenceId": f"EV-{spec['document_id']}",
                "sourceType": "case_document",
                "documentId": spec["document_id"],
                "documentVersion": "v1",
                "page": 1,
                "recordPointer": None,
                "quote": f"{spec['title']}中的相关原始事实。",
                "provenance": "original_document",
            }
        )

    built_docs.append(
        {
            "documentId": "DOC-C03-CALC-MISSING",
            "title": "商业三者险赔款计算书（首次未取得）",
            "materialType": "calculation",
            "status": "not_obtained",
            "version": "v1",
            "relativePath": None,
            "sha256": None,
            "pageCount": None,
            "claimIds": [TARGET_CLAIM],
            "entityIds": [TARGET_CLAIM, "APR-C03-COM-TP", "LOSS-C03-COM-TP"],
            "issuedAt": None,
            "receivedAt": None,
            "sourceDescription": "首次审查材料目录明确记录该计算书未取得；后补文件不放入 inputs/C03。",
            "isSynthetic": True,
        }
    )
    evidence.append(
        {
            "evidenceId": "EV-C03-CALC-GAP",
            "sourceType": "structured_record",
            "documentId": None,
            "documentVersion": None,
            "page": None,
            "recordPointer": "/documents/12/status",
            "quote": "商业三者险赔款计算书状态为 not_obtained。",
            "provenance": "structured_business_record",
        }
    )
    case["documents"] = built_docs
    case["evidence"] = evidence
    write_json(case_dir / "case.json", case)
    return case


def build_supplement() -> dict[str, Any]:
    supplement_dir = ROOT / "supplements" / CASE_ID
    supplement_dir.mkdir(parents=True, exist_ok=True)
    filename = "补充计算书_第三方商业险_演示.pdf"
    pdf_path = supplement_dir / filename
    spec = {
        "document_id": "SUPP-DOC-C03-01",
        "filename": filename,
        "title": "补充赔款计算书 - 第三方商业险（演示）",
        "issued_date": "2026-06-14",
        "claim_labels": [TARGET_CLAIM],
        "sections": [
            kv(
                "计算对象",
                [
                    ["目标赔案", "DEMO-CLM-C03-COM-TP"],
                    ["第三方车辆", "演示-C03B"],
                    ["第三方本次事故核定总损失", yuan(1_000_000)],
                    ["交强险已分摊", yuan(200_000)],
                    ["商业三者险限额", yuan(200_000_000)],
                    ["免赔", "0 元；0%"],
                ],
            ),
            table(
                "计算明细",
                ["运算", "输入", "结果"],
                [["差额", "10,000.00 - 2,000.00", yuan(800_000)]],
                [92, 190, 157],
            ),
            text_section("复核结论", ["补充计算书支持商业三者险审批金额 8,000.00 元。该材料不能解释实际支付 9,000.00 元，支付差额疑点继续保持确认问题状态。"]),
            text_section("版本边界", ["本文件作为后补 S10 材料，仅在人工待核实之后提供；不属于首次 AI 输入，不替换 inputs/C03/case.json。"]),
        ],
    }
    render_pdf(pdf_path, spec)
    manifest = {
        "schemaVersion": 1,
        "datasetCaseId": CASE_ID,
        "baseCaseRevision": 1,
        "providedAt": "2026-10-28T16:40:00+08:00",
        "reason": "人工对 F-C03-03 标记待补充核实后取得商业三者险赔款计算书。",
        "files": [
            {
                "documentId": "SUPP-DOC-C03-01",
                "title": "补充赔款计算书 - 第三方商业险（演示）",
                "relativePath": filename,
                "sha256": sha256(pdf_path),
                "pageCount": len(PdfReader(str(pdf_path)).pages),
                "claimIds": [TARGET_CLAIM],
                "isSynthetic": True,
            }
        ],
        "evidence": [
            {
                "evidenceId": "EV-SUPP-C03-CALC",
                "documentId": "SUPP-DOC-C03-01",
                "documentVersion": "v1",
                "page": 1,
                "quote": "商业三者险应付 = 10,000.00 - 2,000.00 = 8,000.00 元。",
            }
        ],
        "boundary": "本补件独立于首次输入，只通过 review-steps/C03.json 的 provide_evidence 步骤进入人工复核。",
    }
    write_json(supplement_dir / "manifest.json", manifest)
    return manifest


def expected_checks() -> list[dict[str, str]]:
    values = [
        ("FACT-MISSING", "materials", "completed", "识别到商业三者险计算书首次未取得并形成 F-C03-03"),
        ("FACT-INVALID", "materials", "completed", "已取得材料中的日期、金额和对象标识均可规范化"),
        ("FACT-CONFLICT", "materials", "completed", "事故、责任、车辆与新损事实无跨来源冲突"),
        ("POLICY-AVAILABILITY", "policy", "completed", "目标和关联赔案所需保单均已取得"),
        ("POLICY-PERIOD", "policy", "completed", "事故发生在两份保单有效期间内"),
        ("POLICY-COVERAGE", "policy", "completed", "第三方损失与交强险及商业三者险承保关系明确"),
        ("CLAUSE-BINDING", "clauses", "completed", "两份保单引用共享条款版本和哈希一致"),
        ("AMOUNT-LINE-SUM", "amounts", "completed", "首次输入可核对交强险计算；商业险计算书缺件单独提示"),
        ("AMOUNT-RECORDED-OP", "amounts", "completed", "交强险分摊和商业险审批口径均有明确记录"),
        ("AMOUNT-ADJUSTMENT", "amounts", "completed", "申请 9,000.00 元调整为 8,000.00 元有 S01 支持，形成可排除疑点 F-C03-02"),
        ("PAYMENT-EFFECTIVE", "amounts", "completed", "两笔付款均成功且无退款冲销"),
        ("PAYMENT-APPROVAL-GAP", "amounts", "completed", "识别商业险审批 8,000.00 元与支付 9,000.00 元差额，形成 F-C03-01"),
        ("PAYMENT-DUPLICATE", "amounts", "completed", "不存在其他商业险付款或重复交易解释"),
        ("INJURY-IDENTIFICATION", "archive", "completed", "三个来源均明确无人伤"),
        ("INJURY-SHARED-FACT", "materials", "not_applicable", "无人伤且无影响车损的共用事实冲突"),
        ("REPORT-COMPLETION", "summary", "completed", "F-C03-03 补件前只能阶段报告，全部范围内疑点处理并确认覆盖后方可最终报告"),
    ]
    return [{"ruleId": rule, "nodeId": node, "status": status, "reason": reason} for rule, node, status, reason in values]


def checkpoint(
    checkpoint_id: str,
    after_step: str | None,
    stage: str,
    final_allowed: bool,
    coverage: bool,
    complete: bool,
    states: list[str],
) -> dict[str, Any]:
    return {
        "checkpointId": checkpoint_id,
        "afterStepId": after_step,
        "reportStage": stage,
        "finalReportAllowed": final_allowed,
        "coverageConfirmedByHuman": coverage,
        "inScopeChecksComplete": complete,
        "findingStates": [
            {"findingKey": key, "scope": "vehicle", "state": state}
            for key, state in zip(["F-C03-01", "F-C03-02", "F-C03-03"], states, strict=True)
        ],
        "requiredDisclosures": [],
    }


def build_expected() -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "dictionaryVersion": "1.0.0",
        "datasetCaseId": CASE_ID,
        "caseRevision": 1,
        "isTestOracle": True,
        "annotatedBy": "测试资料人工标注组",
        "annotatedAt": "2026-10-28T15:30:00+08:00",
        "annotationStatus": "reviewed",
        "annotationBasis": "人工逐项核对首次输入与独立补件；标准答案不引用模型输出。",
        "expectedInjuryStatus": "no_injury_indication",
        "expectedChecks": expected_checks(),
        "expectedFindings": [
            {
                "findingKey": "F-C03-01",
                "source": "rule",
                "ruleId": "PAYMENT-APPROVAL-GAP",
                "scope": "vehicle",
                "entityIds": [TARGET_CLAIM, "APR-C03-COM-TP", "PAY-C03-COM-TP"],
                "requiredMeaning": "商业三者险审批 8,000.00 元，但关联成功支付为 9,000.00 元，且无退款、冲销、其他审批或失败重付解释。",
                "requiredEvidenceIds": ["EV-DOC-C03-10", "EV-DOC-C03-11"],
                "prohibitedClaims": ["不得将交强险另付 2,000.00 元计入该商业险差额。", "不得执行追回或资金调整。"],
                "initialState": "unreviewed",
                "expectedHumanAction": "confirm",
                "humanRationale": "支付差额有审批和成功交易原始记录支持，应确认问题并交支付经办岗位核查。",
            },
            {
                "findingKey": "F-C03-02",
                "source": "rule",
                "ruleId": "AMOUNT-ADJUSTMENT",
                "scope": "vehicle",
                "entityIds": [TARGET_CLAIM, "LOSS-C03-COM-TP", "APR-C03-COM-TP"],
                "requiredMeaning": "商业三者险初始申请 9,000.00 元与审批 8,000.00 元存在 1,000.00 元差异，需要核对调整依据。",
                "requiredEvidenceIds": ["EV-DOC-C03-07", "EV-DOC-C03-09", "EV-DOC-C03-10"],
                "prohibitedClaims": ["不得仅因申请金额大于审批金额认定错赔。", "不得把该合理调整用来解释支付多出 1,000.00 元。"],
                "initialState": "unreviewed",
                "expectedHumanAction": "exclude",
                "humanRationale": "查勘、定损和损失确认说明共同证明 1,000.00 元为非本次事故旧划痕，差异合理。",
            },
            {
                "findingKey": "F-C03-03",
                "source": "rule",
                "ruleId": "FACT-MISSING",
                "scope": "vehicle",
                "entityIds": [TARGET_CLAIM, "APR-C03-COM-TP", "DOC-C03-CALC-MISSING"],
                "requiredMeaning": "首次审查未取得商业三者险赔款计算书，不能仅依据首次输入完整复核 8,000.00 元险种分摊计算。",
                "requiredEvidenceIds": ["EV-C03-CALC-GAP"],
                "prohibitedClaims": ["不得在首次 AI 输入中引用后补计算书。", "不得因审批记录写有金额就宣称计算书已取得。"],
                "initialState": "unreviewed",
                "expectedHumanAction": "pending",
                "humanRationale": "先标记待补充核实；取得独立 S10 后补计算书并核对通过后再修订为排除疑点。",
            },
        ],
        "forbiddenFindings": [
            {"entityIds": [RELATED_CLAIM, "PAY-C03-CTPL"], "prohibitedMeaning": "交强险 2,000.00 元与商业三者险付款构成重复支付", "reason": "两笔付款对应不同赔案、险种和审批，交强险是明确的先行分摊。"},
            {"entityIds": ["ACC-C03", "VEH-C03-A", "VEH-C03-B"], "prohibitedMeaning": "存在人伤或人伤状态未知", "reason": "报案、事故责任记录和查勘均明确无人伤。"},
        ],
        "initialCheckpoint": checkpoint("CP-C03-INITIAL", None, "draft", False, False, False, ["unreviewed", "unreviewed", "unreviewed"]),
        "reviewCheckpoints": [
            checkpoint("CP-C03-INTERIM", "STEP-C03-06", "interim", False, False, False, ["confirmed", "excluded", "pending_evidence"]),
            checkpoint("CP-C03-AFTER-SUPPLEMENT", "STEP-C03-09", "interim", False, False, True, ["confirmed", "excluded", "excluded"]),
            checkpoint("CP-C03-FINAL", "STEP-C03-11", "final_vehicle", True, True, True, ["confirmed", "excluded", "excluded"]),
        ],
        "reviewStepsFile": "review-steps/C03.json",
        "acceptanceIds": ["A01", "A03", "A06", "A07", "A09", "A10", "A13", "A14", "A15", "A16", "A18", "A20"],
    }
    write_json(ROOT / "expected" / "C03.json", value)
    return value


def decision(action: str, comment: str, evidence: list[str], missing: list[str] | None = None, owner: str | None = None) -> dict[str, Any]:
    return {
        "action": action,
        "comment": comment,
        "evidenceRefs": evidence,
        "missingItems": missing or [],
        "followUpOwner": owner,
        "professionalRecipient": None,
        "professionalReason": None,
    }


def build_steps() -> dict[str, Any]:
    all_checks = [item["ruleId"] for item in expected_checks()]
    actor = "AUDITOR-C03-01"

    def step(number: int, at: str, action: str, payload: dict[str, Any], note: str) -> dict[str, Any]:
        return {
            "stepId": f"STEP-C03-{number:02d}",
            "actorId": actor,
            "at": at,
            "action": action,
            "expectedRevision": 1,
            "idempotencyKey": f"IDEM-C03-{number:02d}-V1",
            "payload": payload,
            "expectedOutcome": "accepted",
            "note": note,
        }

    value = {
        "schemaVersion": 1,
        "datasetCaseId": CASE_ID,
        "caseRevision": 1,
        "expectedFile": "expected/C03.json",
        "steps": [
            step(1, "2026-10-28T16:00:00+08:00", "inspect_finding", {"findingKey": "F-C03-01", "evidenceRefs": ["EV-DOC-C03-10", "EV-DOC-C03-11"]}, "查看目标赔案审批与支付记录。"),
            step(2, "2026-10-28T16:05:00+08:00", "decide_finding", {"findingKey": "F-C03-01", "decision": decision("confirm", "审批 8,000.00 元与成功支付 9,000.00 元差额成立，且无冲销或其他审批解释；确认问题并交支付经办岗位核查。", ["EV-DOC-C03-10", "EV-DOC-C03-11"])}, "系统只保存审查结论，不执行资金操作。"),
            step(3, "2026-10-28T16:10:00+08:00", "inspect_finding", {"findingKey": "F-C03-02", "evidenceRefs": ["EV-DOC-C03-07", "EV-DOC-C03-09", "EV-DOC-C03-10"]}, "核对定损、损失确认及审批调整。"),
            step(4, "2026-10-28T16:15:00+08:00", "decide_finding", {"findingKey": "F-C03-02", "decision": decision("exclude", "1,000.00 元差额对应非本次事故旧划痕，查勘、定损和损失确认记录一致；排除该疑点。", ["EV-DOC-C03-07", "EV-DOC-C03-09", "EV-DOC-C03-10"])}, "合理金额调整不等同于错赔。"),
            step(5, "2026-10-28T16:20:00+08:00", "inspect_finding", {"findingKey": "F-C03-03", "evidenceRefs": ["EV-C03-CALC-GAP"]}, "确认首次材料目录中的计算书缺件状态。"),
            step(6, "2026-10-28T16:25:00+08:00", "decide_finding", {"findingKey": "F-C03-03", "decision": decision("pending", "首次档案未取得商业三者险赔款计算书，先标记待补充核实。", [], ["商业三者险赔款计算书"], "理算资料管理岗")}, "此时只能生成阶段报告。"),
            step(7, "2026-10-28T16:40:00+08:00", "provide_evidence", {"findingKey": "F-C03-03", "supplementPackage": "supplements/C03/manifest.json", "newEvidenceIds": ["EV-SUPP-C03-CALC"], "note": "补件包仅包含商业三者险计算书，不覆盖首次输入。"}, "将 S10 后补材料独立加入复核。"),
            step(8, "2026-10-28T16:45:00+08:00", "inspect_finding", {"findingKey": "F-C03-03", "evidenceRefs": ["EV-SUPP-C03-CALC"]}, "查看后补计算书的险种分摊公式和金额。"),
            step(9, "2026-10-28T16:50:00+08:00", "amend_decision", {"findingKey": "F-C03-03", "changeReason": "取得并核对后补商业三者险赔款计算书。", "decision": decision("exclude", "后补计算书载明 10,000.00 - 2,000.00 = 8,000.00 元，与审批一致；原缺件疑点完成核实并排除。", ["EV-SUPP-C03-CALC"])}, "保留原待核实决定及本次修订原因。"),
            step(10, "2026-10-28T16:55:00+08:00", "confirm_coverage", {"comment": "已核对全部适用检查、三条疑点及后补材料边界。", "checkIds": all_checks}, "人工确认检查覆盖。"),
            step(11, "2026-10-28T17:00:00+08:00", "save_report", {"stage": "final_vehicle", "comment": "三条范围内疑点均已形成确认或排除结论，保存车损最终报告。"}, "F-C03-01 保持确认问题；系统不执行资金处置。"),
        ],
    }
    write_json(ROOT / "review-steps" / "C03.json", value)
    return value


def main() -> None:
    docs = build_documents()
    case = build_case(docs)
    supplement = build_supplement()
    build_expected()
    build_steps()
    print(
        json.dumps(
            {
                "status": "built",
                "case": case["datasetCaseId"],
                "initialPdfCount": len(docs),
                "supplementPdfCount": len(supplement["files"]),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

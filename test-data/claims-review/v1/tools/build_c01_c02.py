"""Build the C01 and C02 synthetic normal claim archives.

The PDFs and structured records are generated from the same facts so that
amounts, identifiers, page references, and attachment hashes stay aligned.
No real personal, vehicle, policy, banking, or invoice identifiers are used.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
PREPARED_AT = "2026-10-28T10:00:00+08:00"
ANNOTATED_AT = "2026-10-28T15:00:00+08:00"

COMMERCIAL_TERMS = {
    "documentId": "PA-COMMERCIAL-MOTOR-2020",
    "documentSha256": "a8908c3ee830bc59774d3baa1d093510be87993dbcaa89213906dff85e84489a",
    "version": "2020版",
    "sectionIds": ["COMM-OWN", "COMM-COMMON"],
}
COMMERCIAL_MULTI_TERMS = {
    **COMMERCIAL_TERMS,
    "sectionIds": ["COMM-OWN", "COMM-THIRD", "COMM-COMMON"],
}
CTPL_TERMS = {
    "documentId": "PA-CTPL-2020-CONTENT",
    "documentSha256": "b8d04712b5a394c9050e8853fa3cb3582434450cea9f97d45dae834f2370a461",
    "version": "2020修订内容",
    "sectionIds": ["CTPL-LIABILITY", "CTPL-SETTLEMENT"],
}


def money(amount_fen: int) -> dict[str, Any]:
    return {"status": "known", "amountFen": amount_fen, "currency": "CNY", "reason": None}


def na_money(reason: str) -> dict[str, Any]:
    return {"status": "not_applicable", "amountFen": None, "currency": "CNY", "reason": reason}


def yuan(amount_fen: int) -> str:
    return f"人民币 {amount_fen / 100:,.2f} 元"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


FONT_NAME = "MicrosoftYaHei"
pdfmetrics.registerFont(TTFont(FONT_NAME, "C:/Windows/Fonts/msyh.ttc", subfontIndex=0))
STYLES = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "ChineseTitle",
    parent=STYLES["Title"],
    fontName=FONT_NAME,
    fontSize=19,
    leading=25,
    textColor=colors.HexColor("#16324F"),
    alignment=TA_CENTER,
    spaceAfter=5 * mm,
)
SUBTITLE = ParagraphStyle(
    "ChineseSubtitle",
    parent=STYLES["Normal"],
    fontName=FONT_NAME,
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#52606D"),
    alignment=TA_CENTER,
    spaceAfter=5 * mm,
)
HEADING = ParagraphStyle(
    "ChineseHeading",
    parent=STYLES["Heading2"],
    fontName=FONT_NAME,
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#0B6E75"),
    spaceBefore=3 * mm,
    spaceAfter=2 * mm,
)
BODY = ParagraphStyle(
    "ChineseBody",
    parent=STYLES["BodyText"],
    fontName=FONT_NAME,
    fontSize=9,
    leading=14,
    textColor=colors.HexColor("#243B53"),
    alignment=TA_LEFT,
)
SMALL = ParagraphStyle(
    "ChineseSmall",
    parent=BODY,
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#52606D"),
)


def P(value: Any, style: ParagraphStyle = BODY) -> Paragraph:
    text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("&lt;br/&gt;", "<br/>")
    return Paragraph(text, style)


def page_decor(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFont(FONT_NAME, 8)
    canvas.setFillColor(colors.HexColor("#66788A"))
    canvas.drawString(18 * mm, 12 * mm, "CasePilot 已结案车险赔案审查测试资料")
    canvas.drawRightString(width - 18 * mm, 12 * mm, f"第 {doc.page} 页")
    canvas.setFillColor(colors.Color(0.75, 0.18, 0.18, alpha=0.10))
    canvas.setFont(FONT_NAME, 42)
    canvas.translate(width / 2, height / 2)
    canvas.rotate(32)
    canvas.drawCentredString(0, 0, "演示数据 - 非真实业务凭证")
    canvas.restoreState()


def make_table(headers: list[str], rows: list[list[Any]], widths: list[float] | None = None) -> Table:
    data = [[P(h, SMALL) for h in headers]] + [[P(cell, SMALL) for cell in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#16324F")),
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A9B8C4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
            ]
        )
    )
    return table


def render_pdf(path: Path, spec: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=19 * mm,
        title=spec["title"],
        author="CasePilot 测试资料制作组",
        subject="虚构车险赔案演示材料",
    )
    story = [
        P(spec["title"], TITLE),
        P(
            f"材料编号：{spec['document_id']}　版本：v1　出具日期：{spec['issued_date']}<br/>"
            f"关联赔案：{'、'.join(spec['claim_labels'])}",
            SUBTITLE,
        ),
    ]
    notice = make_table(
        ["资料属性", "使用限制"],
        [["全量虚构演示数据", "仅用于 CasePilot 功能开发和验收；不得作为真实保单、发票、支付或理赔凭证。"]],
        [37 * mm, 118 * mm],
    )
    story.extend([notice, Spacer(1, 3 * mm)])
    for section in spec["sections"]:
        story.append(P(section["heading"], HEADING))
        if section["kind"] == "kv":
            story.append(make_table(["项目", "内容"], section["rows"], [40 * mm, 115 * mm]))
        elif section["kind"] == "table":
            story.append(make_table(section["headers"], section["rows"], section.get("widths")))
        elif section["kind"] == "text":
            for paragraph in section["paragraphs"]:
                story.extend([P(paragraph), Spacer(1, 1.5 * mm)])
        elif section["kind"] == "pagebreak":
            story.append(PageBreak())
        else:
            raise ValueError(f"Unsupported section kind: {section['kind']}")
    story.extend(
        [
            Spacer(1, 4 * mm),
            P("制表说明：本材料中的姓名、车牌、保单号、赔案号、交易号及金额均为测试构造。", SMALL),
        ]
    )
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)


def document_spec(
    case_id: str,
    seq: int,
    filename: str,
    title: str,
    material_type: str,
    issued_at: str,
    claim_ids: list[str],
    entity_ids: list[str],
    sections: list[dict[str, Any]],
    source_description: str,
) -> dict[str, Any]:
    return {
        "document_id": f"DOC-{case_id}-{seq:02d}",
        "filename": filename,
        "title": title,
        "material_type": material_type,
        "issued_at": issued_at,
        "issued_date": issued_at[:10],
        "received_at": PREPARED_AT,
        "claim_ids": claim_ids,
        "claim_labels": claim_ids,
        "entity_ids": entity_ids,
        "sections": sections,
        "source_description": source_description,
    }


def kv(heading: str, rows: list[list[Any]]) -> dict[str, Any]:
    return {"heading": heading, "kind": "kv", "rows": rows}


def table(
    heading: str,
    headers: list[str],
    rows: list[list[Any]],
    widths: list[float] | None = None,
) -> dict[str, Any]:
    return {"heading": heading, "kind": "table", "headers": headers, "rows": rows, "widths": widths}


def text_section(heading: str, paragraphs: list[str]) -> dict[str, Any]:
    return {"heading": heading, "kind": "text", "paragraphs": paragraphs}


def common_expected_checks(c02: bool = False) -> list[dict[str, str]]:
    statuses = {
        "FACT-MISSING": ("materials", "completed", "必需材料均已取得，未见未知关键值"),
        "FACT-INVALID": ("materials", "completed", "日期、金额和对象标识均可规范化"),
        "FACT-CONFLICT": ("materials", "completed", "跨材料事故、责任、车辆和金额事实一致"),
        "POLICY-AVAILABILITY": ("policy", "completed", "目标赔案所需保单已取得"),
        "POLICY-PERIOD": ("policy", "completed", "事故发生在保单有效期间内"),
        "POLICY-COVERAGE": ("policy", "completed", "损失项目与实际承保险种逐项对应"),
        "CLAUSE-BINDING": ("clauses", "completed", "保单引用与共享条款版本及哈希一致"),
        "AMOUNT-LINE-SUM": ("amounts", "completed", "各赔款计算明细加总等于计算总额"),
        "AMOUNT-RECORDED-OP": (
            "amounts",
            "completed" if c02 else "not_applicable",
            "C02 的第三方损失在交强险和商业险间明确分摊" if c02 else "C01 无独立分摊或冲销运算",
        ),
        "AMOUNT-ADJUSTMENT": ("amounts", "completed", "申请、定损和认可金额差异均有明细说明"),
        "PAYMENT-EFFECTIVE": ("amounts", "completed", "仅存在成功付款，无退款、冲销或失败重付"),
        "PAYMENT-APPROVAL-GAP": ("amounts", "completed", "每笔审批金额与对应有效支付金额一致"),
        "PAYMENT-DUPLICATE": ("amounts", "completed", "付款对象、险种和审批分配唯一，无重复记录"),
        "INJURY-IDENTIFICATION": ("archive", "completed", "报案、事故证明和查勘均明确无人伤"),
        "INJURY-SHARED-FACT": ("materials", "not_applicable", "无人伤且不存在影响车损的共用事实冲突"),
        "REPORT-COMPLETION": ("summary", "completed", "范围内检查完整，无疑点，需人工确认覆盖后完成"),
    }
    return [
        {"ruleId": rule_id, "nodeId": node, "status": status, "reason": reason}
        for rule_id, (node, status, reason) in statuses.items()
    ]


def make_expected(case_id: str, entity_ids: dict[str, list[str]], c02: bool = False) -> dict[str, Any]:
    forbidden = [
        {
            "entityIds": entity_ids["claims"],
            "prohibitedMeaning": "核赔金额与有效支付金额不一致或存在漏付",
            "reason": "审批与成功支付按赔案逐笔一致。",
        },
        {
            "entityIds": entity_ids["payments"],
            "prohibitedMeaning": "存在重复支付、无效付款或未解释的冲销退款",
            "reason": "每笔交易号唯一，均为成功付款且只分配至对应审批。",
        },
        {
            "entityIds": entity_ids["losses"],
            "prohibitedMeaning": "申请金额与定损金额不同即认定错赔",
            "reason": "定损及核赔材料已说明合理剔减或分摊，不能仅按数字差异判错。",
        },
        {
            "entityIds": entity_ids["vehicles"],
            "prohibitedMeaning": "存在人伤线索或人伤状态未知",
            "reason": "三个独立来源均明确无人受伤，人员与车辆范围完整。",
        },
    ]
    if not c02:
        forbidden.append(
            {
                "entityIds": entity_ids["claims"],
                "prohibitedMeaning": "因未提供第三方损失或交强险赔款材料而认定资料缺失",
                "reason": "C01 为无第三方人车物损失的单车事故，相关检查是不适用而非资料缺失或未投保。",
            }
        )
    check_ids = [item["ruleId"] for item in common_expected_checks(c02)]
    acceptance = ["A01", "A06", "A07", "A09", "A14", "A15", "A17", "A20"]
    if c02:
        acceptance[1:1] = ["A02", "A03"]
    return {
        "schemaVersion": 1,
        "dictionaryVersion": "1.0.0",
        "datasetCaseId": case_id,
        "caseRevision": 1,
        "isTestOracle": True,
        "annotatedBy": "测试资料人工标注组",
        "annotatedAt": ANNOTATED_AT,
        "annotationStatus": "reviewed",
        "annotationBasis": "逐项核对事故、保单、损失、理算、审批、支付、结案材料及结构化记录；本答案独立于模型输出。",
        "expectedInjuryStatus": "no_injury_indication",
        "expectedChecks": common_expected_checks(c02),
        "expectedFindings": [],
        "forbiddenFindings": forbidden,
        "initialCheckpoint": {
            "checkpointId": f"CP-{case_id}-INITIAL",
            "afterStepId": None,
            "reportStage": "draft",
            "finalReportAllowed": False,
            "coverageConfirmedByHuman": False,
            "inScopeChecksComplete": True,
            "findingStates": [],
            "requiredDisclosures": [],
        },
        "reviewCheckpoints": [
            {
                "checkpointId": f"CP-{case_id}-FINAL",
                "afterStepId": f"STEP-{case_id}-02",
                "reportStage": "final_vehicle",
                "finalReportAllowed": True,
                "coverageConfirmedByHuman": True,
                "inScopeChecksComplete": True,
                "findingStates": [],
                "requiredDisclosures": [],
            }
        ],
        "reviewStepsFile": f"review-steps/{case_id}.json",
        "acceptanceIds": acceptance,
        "_check_ids": check_ids,
    }


def make_steps(case_id: str, check_ids: list[str]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "datasetCaseId": case_id,
        "caseRevision": 1,
        "expectedFile": f"expected/{case_id}.json",
        "steps": [
            {
                "stepId": f"STEP-{case_id}-01",
                "actorId": "AUDITOR-NORMAL-01",
                "at": "2026-10-28T16:00:00+08:00",
                "action": "confirm_coverage",
                "expectedRevision": 1,
                "idempotencyKey": f"IDEM-{case_id}-COVERAGE-V1",
                "payload": {
                    "comment": "已逐项核对全部适用检查、材料和不适用项，未发现疑点。",
                    "checkIds": check_ids,
                },
                "expectedOutcome": "accepted",
                "note": "无疑点正常案仍需人工确认检查覆盖。",
            },
            {
                "stepId": f"STEP-{case_id}-02",
                "actorId": "AUDITOR-NORMAL-01",
                "at": "2026-10-28T16:05:00+08:00",
                "action": "save_report",
                "expectedRevision": 1,
                "idempotencyKey": f"IDEM-{case_id}-REPORT-V1",
                "payload": {
                    "stage": "final_vehicle",
                    "comment": "已确认报告范围、材料覆盖及无疑点结论，保存车损最终报告。",
                },
                "expectedOutcome": "accepted",
                "note": "满足范围内检查完成和人工覆盖确认门禁。",
            },
        ],
    }


def c01_archive() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[str]]]:
    claim = "CLM-C01-OWN"
    docs = [
        document_spec("C01", 1, "商业险保单_演示.pdf", "机动车商业保险单（演示）", "commercial_policy", "2026-01-01T00:00:00+08:00", [claim], ["POL-C01-COM", "CV-C01-OWN", "VEH-C01-A", "PTY-C01-INS"], [
            kv("投保信息", [["保单号", "DEMO-COM-C01-2026"], ["保险人", "中国平安财产保险股份有限公司（仅作演示标识）"], ["投保人/被保险人", "林某甲（虚构）"], ["承保车辆", "演示-C01 / 家庭自用燃油车"], ["保险期间", "2026-01-01 00:00 至 2026-12-31 23:59（北京时间）"]]),
            table("实际承保险种", ["险种", "保险金额/限额", "免赔", "适用条款"], [["机动车损失保险", yuan(15_000_000), "0 元；免赔率 0%", "机动车商业保险条款（2020版）：COMM-OWN、COMM-COMMON"]], [34*mm, 34*mm, 30*mm, 57*mm]),
            text_section("范围说明", ["本保单材料只证明列明险种的承保事实。C01 无第三方人车物损失，交强险及三者险赔款检查在本案审查范围内不适用；不得据此推断为未投保。"]),
        ], "虚构商业险保单；合同条款正文由共享条款库按版本和哈希定位。"),
        document_spec("C01", 2, "报案记录_演示.pdf", "机动车保险报案记录（演示）", "claim_notification", "2026-08-15T10:05:00+08:00", [claim], ["ACC-C01", "VEH-C01-A", "PTY-C01-INS"], [
            kv("报案要素", [["报案号", "DEMO-RPT-C01"], ["报案时间", "2026-08-15 10:05"], ["出险时间", "2026-08-15 09:20"], ["地点", "上海市浦东新区演示路与样例路路口（虚构地点）"], ["报案人", "林某甲（虚构），同时为驾驶人"], ["事故经过", "雨后路滑，车辆低速转弯时碰擦道路隔离墩。"], ["初报损失", "本车右前保险杠及右前翼子板受损；无第三方车辆、人员或财物损失。"], ["人伤", "明确报告无人受伤。"]]),
        ], "报案受理记录的演示重制件。"),
        document_spec("C01", 3, "事故证明及责任记录_演示.pdf", "道路交通事故简易处理记录（演示）", "accident_proof", "2026-08-15T11:20:00+08:00", [claim], ["ACC-C01", "VEH-C01-A", "PTY-C01-INS"], [
            kv("事故记录", [["事故编号", "DEMO-ACC-C01"], ["事故时间", "2026-08-15 09:20"], ["事故地点", "上海市浦东新区演示路与样例路路口（虚构地点）"], ["参与方", "仅演示-C01 车辆及驾驶人林某甲（虚构）"], ["事故经过", "单车低速转弯碰擦隔离墩。"], ["责任记录", "驾驶人承担本次事故全部责任。"], ["第三方损失", "无第三方车辆、人员或其他财物损失。"], ["人员伤亡", "无人员受伤或死亡。"]]),
        ], "虚构的事故简易处理记录，不对应真实交管文书。"),
        document_spec("C01", 4, "查勘报告_演示.pdf", "机动车保险现场查勘报告（演示）", "survey", "2026-08-15T12:10:00+08:00", [claim], ["ACC-C01", "VEH-C01-A", "LOSS-C01-OWN"], [
            kv("查勘结论", [["查勘地点/时间", "演示维修点，2026-08-15 12:10"], ["标的车辆", "演示-C01"], ["碰撞痕迹", "右前保险杠擦裂，右前翼子板凹陷；痕迹方向与报案经过相符。"], ["第三方情况", "未发现第三方车辆、人员或财物损失。"], ["人伤情况", "驾驶人现场确认无不适，记录为无人伤。"], ["初步处理意见", "按机动车损失保险进入定损，剔除与本次碰撞无关的旧划痕。"]]),
        ], "查勘人员演示记录。"),
        document_spec("C01", 5, "车辆及驾驶人资料摘要_演示.pdf", "车辆及驾驶人资料摘要（演示）", "vehicle_driver_summary", "2026-08-15T13:00:00+08:00", [claim], ["VEH-C01-A", "PTY-C01-INS"], [
            kv("车辆摘要", [["车辆标识", "VEH-C01-A / 演示-C01"], ["所有人", "林某甲（虚构）"], ["使用性质", "家庭自用"], ["动力类型", "燃油"], ["保单绑定", "DEMO-COM-C01-2026"]]),
            kv("驾驶人摘要", [["驾驶人", "林某甲（虚构）"], ["身份关系", "被保险人本人驾驶"], ["准驾与证件核对", "演示记录显示事故时有效且与车辆使用性质相符；不包含真实证件号码。"]]),
        ], "只保留一致性检查需要的虚构摘要，不含真实个人敏感信息。"),
        document_spec("C01", 6, "本车定损及核损明细_演示.pdf", "本车定损及核损明细（演示）", "assessment", "2026-08-17T14:00:00+08:00", [claim], ["LOSS-C01-OWN", "VEH-C01-A"], [
            kv("金额口径", [["申请/报损金额", yuan(785_000)], ["核定金额", yuan(728_000)], ["认可金额", yuan(728_000)], ["调整说明", "剔除右后门与本次事故痕迹不一致的旧划痕 570.00 元。"]]),
            table("核损项目", ["项目", "处理方式", "金额"], [["右前保险杠总成", "维修及附件", yuan(360_000)], ["右前翼子板", "钣金修复", yuan(200_000)], ["拆装工时", "维修", yuan(128_000)], ["喷漆材料", "维修", yuan(40_000)]], [65*mm, 50*mm, 40*mm]),
        ], "本车损失核定演示明细。"),
        document_spec("C01", 7, "维修清单及费用证明_演示.pdf", "本车维修清单及费用证明（演示）", "repair_cost", "2026-08-20T17:00:00+08:00", [claim], ["LOSS-C01-OWN", "VEH-C01-A"], [
            table("维修结算清单", ["项目", "金额", "对应定损"], [["右前保险杠维修及附件", yuan(360_000), "一致"], ["右前翼子板钣金", yuan(200_000), "一致"], ["拆装工时", yuan(128_000), "一致"], ["喷漆材料", yuan(40_000), "一致"], ["合计", yuan(728_000), "等于核定金额"]], [70*mm, 40*mm, 45*mm]),
            text_section("凭证边界", ["本文件为演示费用证明，不含真实发票号码、税控信息或查验凭证。车辆、日期和金额与定损项目一一对应。"]),
        ], "虚构维修结算摘要，不可作为真实发票。"),
        document_spec("C01", 8, "赔款计算书_演示.pdf", "机动车损失保险赔款计算书（演示）", "calculation", "2026-08-21T09:30:00+08:00", [claim], ["CALC-C01-OWN", "LOSS-C01-OWN", "POL-C01-COM", "CV-C01-OWN"], [
            kv("计算对象", [["赔案号", "DEMO-CLM-C01-OWN"], ["保单/险种", "DEMO-COM-C01-2026 / 机动车损失保险"], ["损失对象", "演示-C01 本车"], ["责任比例", "100%"], ["免赔", "0 元；免赔率 0%"]]),
            table("计算明细", ["输入项", "金额"], [["配件及维修项目", yuan(560_000)], ["工时", yuan(128_000)], ["喷漆材料", yuan(40_000)], ["应付赔款", yuan(728_000)]], [105*mm, 50*mm]),
            text_section("公式", ["应付赔款 = 5,600.00 + 1,280.00 + 400.00 = 7,280.00 元。未使用其他险种或第三方损失金额。"]),
        ], "机动车损失保险赔款计算演示材料。"),
        document_spec("C01", 9, "核赔审批意见_演示.pdf", "核赔审批意见（演示）", "approval", "2026-08-21T15:20:00+08:00", [claim], ["APR-C01-OWN", "CALC-C01-OWN", "LOSS-C01-OWN"], [
            kv("审批结果", [["赔案号", "DEMO-CLM-C01-OWN"], ["审批项目", "机动车损失保险 - 本车损失"], ["申请金额", yuan(785_000)], ["核赔金额", yuan(728_000)], ["审批状态", "通过"], ["调整理由", "依据查勘痕迹和定损明细，剔除与本次事故无关的旧划痕 570.00 元。"], ["审批意见", "计算明细、承保期间、责任及维修清单一致，同意赔付。"]]),
        ], "虚构核赔审批记录。"),
        document_spec("C01", 10, "支付及冲销记录_演示.pdf", "支付及冲销记录（演示）", "transaction", "2026-08-22T10:00:00+08:00", [claim], ["PAY-C01-OWN", "APR-C01-OWN", "PTY-C01-INS"], [
            table("交易记录", ["交易号", "类型", "状态", "收款对象", "金额", "审批分配"], [["DEMO-TXN-C01-001", "付款", "成功", "林某甲（虚构）", yuan(728_000), "APR-C01-OWN：7,280.00 元"]], [33*mm, 18*mm, 18*mm, 31*mm, 27*mm, 40*mm]),
            text_section("冲销核对", ["本赔案无失败付款、退款、冲销或重付记录。仅以状态为成功的上述交易计入有效支付。"]),
        ], "虚构支付流水摘要，不含真实银行账号。"),
        document_spec("C01", 11, "结案记录_演示.pdf", "赔案结案记录（演示）", "closure", "2026-08-22T16:30:00+08:00", [claim], [claim, "PAY-C01-OWN"], [
            kv("结案信息", [["赔案号", "DEMO-CLM-C01-OWN"], ["结案类型", "已赔付结案"], ["结案时间", "2026-08-22 16:30"], ["原处理结论", "机动车损失保险核赔 7,280.00 元，成功支付 7,280.00 元后结案。"], ["支付状态", "已结清"], ["范围说明", "本案仅有本车损失；无第三方损失、无人伤。"]]),
        ], "虚构原赔案结案记录；结案事实与支付成功记录分别保留。"),
    ]
    evidence = {spec["document_id"]: f"EV-{spec['document_id']}" for spec in docs}
    ev = lambda seq: evidence[f"DOC-C01-{seq:02d}"]
    case = {
        "schemaVersion": 1, "dictionaryVersion": "1.0.0", "datasetCaseId": "C01", "caseRevision": 1, "isSynthetic": True, "preparedAt": PREPARED_AT,
        "reviewScope": {"targetClaimIds": [claim], "relatedClaimIds": [], "lossTypes": ["own_vehicle"], "scopeLimitations": ["本案为无第三方人车物损失的单车事故；第三方损失、人伤赔偿及其险种赔款检查不适用，不得解释为资料未取得或未投保。"]},
        "accident": {"accidentId": "ACC-C01", "occurredAt": "2026-08-15T09:20:00+08:00", "location": "上海市浦东新区演示路与样例路路口（虚构地点）", "description": "雨后路滑，车辆低速转弯时碰擦道路隔离墩。", "liabilityDescription": "驾驶人承担全部责任；无第三方车辆、人员或财物损失。", "evidenceRefs": [ev(2), ev(3), ev(4)]},
        "parties": [{"partyId": "PTY-C01-INS", "displayName": "林某甲（虚构）", "kind": "person", "evidenceRefs": [ev(1), ev(2), ev(5)]}],
        "vehicles": [{"vehicleId": "VEH-C01-A", "role": "insured", "plateNumber": "演示-C01", "ownerPartyId": "PTY-C01-INS", "driverPartyId": "PTY-C01-INS", "usage": "家庭自用", "powerType": "fuel", "evidenceRefs": [ev(1), ev(5)]}],
        "claims": [{"claimId": claim, "reportNumber": "DEMO-RPT-C01", "claimNumber": "DEMO-CLM-C01-OWN", "handlingOrganization": "平安产险演示机构", "closureType": "paid_closed", "closedAt": "2026-08-22T16:30:00+08:00", "originalConclusion": "机动车损失保险核赔 7,280.00 元并成功支付后结案。", "originalPaymentStatus": "settled", "evidenceRefs": [ev(2), ev(11)]}],
        "policies": [{"policyId": "POL-C01-COM", "policyNumber": "DEMO-COM-C01-2026", "availability": "available", "policyType": "commercial", "insurerCode": "PINGAN", "vehicleId": "VEH-C01-A", "policyholderPartyId": "PTY-C01-INS", "insuredPartyIds": ["PTY-C01-INS"], "effectiveFrom": "2026-01-01T00:00:00+08:00", "effectiveTo": "2026-12-31T23:59:59+08:00", "coverages": [{"coverageId": "CV-C01-OWN", "coverageCode": "OWN_DAMAGE", "status": "insured", "parentCoverageId": None, "insuranceAmount": money(15_000_000), "perAccidentLimit": na_money("本险种按保险金额及实际损失口径处理"), "deductibleAmount": money(0), "deductibleBasisPoints": 0, "terms": [COMMERCIAL_TERMS], "specialConditions": "本演示保单未约定本案适用的额外免赔。", "evidenceRefs": [ev(1)]}], "terms": [COMMERCIAL_TERMS], "evidenceRefs": [ev(1)]}],
        "endorsements": [],
        "losses": [{"lossId": "LOSS-C01-OWN", "claimId": claim, "vehicleId": "VEH-C01-A", "personPartyId": None, "lossType": "own_vehicle", "description": "本车右前保险杠及右前翼子板碰撞损失。", "claimedAmount": money(785_000), "assessedAmount": money(728_000), "agreedAmount": money(728_000), "evidenceRefs": [ev(4), ev(6), ev(7)]}],
        "calculations": [{"calculationId": "CALC-C01-OWN", "claimId": claim, "policyId": "POL-C01-COM", "coverageId": "CV-C01-OWN", "status": "final", "lines": [{"lineId": "LINE-C01-OWN", "lossId": "LOSS-C01-OWN", "description": "本车核定维修费用加总", "operation": "sum", "inputs": [{"name": "配件及维修项目", "amount": money(560_000)}, {"name": "工时", "amount": money(128_000)}, {"name": "喷漆材料", "amount": money(40_000)}], "formulaText": "560000 + 128000 + 40000", "result": money(728_000), "evidenceRefs": [ev(6), ev(8)]}], "totalAmount": money(728_000), "adjustmentReason": "申请金额中 570.00 元旧划痕与本次事故无关，依据查勘及定损记录剔除。", "evidenceRefs": [ev(8)]}],
        "approvals": [{"approvalId": "APR-C01-OWN", "claimId": claim, "policyId": "POL-C01-COM", "coverageId": "CV-C01-OWN", "calculationIds": ["CALC-C01-OWN"], "lossIds": ["LOSS-C01-OWN"], "status": "approved", "approvedAmount": money(728_000), "decidedAt": "2026-08-21T15:20:00+08:00", "reason": "承保有效，事故责任及损失项目一致，定损调整理由充分。", "evidenceRefs": [ev(9)]}],
        "payments": [{"paymentId": "PAY-C01-OWN", "claimId": claim, "externalTransactionId": "DEMO-TXN-C01-001", "kind": "disbursement", "status": "succeeded", "amount": money(728_000), "occurredAt": "2026-08-22T10:00:00+08:00", "payeePartyId": "PTY-C01-INS", "originalPaymentId": None, "approvalAllocations": [{"approvalId": "APR-C01-OWN", "amount": money(728_000)}], "evidenceRefs": [ev(10)]}],
        "documents": [], "evidence": [], "observations": [], "dataGaps": [], "knowledgeRefs": [COMMERCIAL_TERMS],
        "injury": {"declaredStatus": "no_injury_reported", "evidenceRefs": [ev(2), ev(3), ev(4)], "injuredPersons": []},
    }
    entities = {"claims": [claim], "payments": ["PAY-C01-OWN"], "losses": ["LOSS-C01-OWN"], "vehicles": ["VEH-C01-A"]}
    return case, docs, entities


def c02_archive() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, list[str]]]:
    claims = ["CLM-C02-OWN", "CLM-C02-CTPL", "CLM-C02-COM-TP"]
    base_entities = ["ACC-C02", "VEH-C02-A", "VEH-C02-B", "PTY-C02-INS", "PTY-C02-TP"]
    docs = [
        document_spec("C02", 1, "交强险保单_演示.pdf", "机动车交通事故责任强制保险单（演示）", "ctpl_policy", "2026-01-15T00:00:00+08:00", [claims[1]], ["POL-C02-CTPL", "CV-C02-CTPL", "VEH-C02-A", "PTY-C02-INS"], [
            kv("投保信息", [["保单号", "DEMO-CTPL-C02-2026"], ["投保人/被保险人", "周某乙（虚构）"], ["承保车辆", "演示-C02A / 家庭自用燃油车"], ["保险期间", "2026-01-15 00:00 至 2027-01-14 23:59（北京时间）"]]),
            table("承保险种", ["险种", "责任限额", "免赔", "适用条款"], [["机动车交通事故责任强制保险", "财产损失赔偿限额 2,000.00 元（本演示事故口径）", "无", "交强险条款（2020修订内容）：CTPL-LIABILITY、CTPL-SETTLEMENT"]], [34*mm, 53*mm, 19*mm, 49*mm]),
        ], "虚构交强险保单；限额仅用于本演示案计算。"),
        document_spec("C02", 2, "商业险保单_演示.pdf", "机动车商业保险单（演示）", "commercial_policy", "2026-01-15T00:00:00+08:00", [claims[0], claims[2]], ["POL-C02-COM", "CV-C02-OWN", "CV-C02-TP", "VEH-C02-A", "PTY-C02-INS"], [
            kv("投保信息", [["保单号", "DEMO-COM-C02-2026"], ["投保人/被保险人", "周某乙（虚构）"], ["承保车辆", "演示-C02A / 家庭自用燃油车"], ["保险期间", "2026-01-15 00:00 至 2027-01-14 23:59（北京时间）"]]),
            table("实际承保险种", ["险种", "保险金额/限额", "免赔", "适用条款"], [["机动车损失保险", yuan(18_000_000), "0 元；0%", "COMM-OWN、COMM-COMMON"], ["机动车第三者责任保险", yuan(200_000_000), "0 元；0%", "COMM-THIRD、COMM-COMMON"]], [39*mm, 36*mm, 27*mm, 53*mm]),
        ], "虚构商业险保单；仅列示实际承保险种。"),
        document_spec("C02", 3, "报案记录_演示.pdf", "机动车保险报案记录（演示）", "claim_notification", "2026-07-12T15:05:00+08:00", claims, base_entities, [
            kv("报案要素", [["报案号", "DEMO-RPT-C02"], ["报案时间", "2026-07-12 15:05"], ["出险时间", "2026-07-12 14:35"], ["地点", "杭州市滨江区测试大道与样本路路口（虚构地点）"], ["报案人", "周某乙（虚构），演示-C02A 驾驶人"], ["事故经过", "演示-C02A 变更车道时与同向演示-C02B 发生碰撞。"], ["损失", "演示-C02A 左前部、演示-C02B 右后部受损。"], ["人伤", "双方驾驶人均明确无受伤，车内无其他人员。"]]),
        ], "三赔案共用同一事故报案记录。"),
        document_spec("C02", 4, "事故证明及责任记录_演示.pdf", "道路交通事故责任记录（演示）", "accident_proof", "2026-07-12T16:10:00+08:00", claims, base_entities, [
            kv("事故与责任", [["事故编号", "DEMO-ACC-C02"], ["事故时间/地点", "2026-07-12 14:35 / 杭州市滨江区测试大道与样本路路口（虚构地点）"], ["甲方", "周某乙（虚构），驾驶演示-C02A"], ["乙方", "赵某丙（虚构），驾驶演示-C02B"], ["事故经过", "甲方变更车道时未确保安全，与乙方车辆发生碰撞。"], ["责任", "甲方承担全部责任；乙方无责任。"], ["人伤", "双方均无人受伤。"]]),
        ], "虚构事故责任记录，不对应真实交管文书。"),
        document_spec("C02", 5, "查勘报告_演示.pdf", "机动车保险现场查勘报告（演示）", "survey", "2026-07-12T17:00:00+08:00", claims, ["ACC-C02", "VEH-C02-A", "VEH-C02-B", "LOSS-C02-OWN", "LOSS-C02-TP-CTPL", "LOSS-C02-TP-COM"], [
            table("查勘对象", ["车辆", "角色", "受损部位", "初步意见"], [["演示-C02A", "承保车辆", "左前保险杠、左前大灯", "进入机动车损失保险定损"], ["演示-C02B", "第三方车辆", "右后保险杠、右后尾灯", "第三方财产损失，先交强险后商业三者险"]], [32*mm, 28*mm, 45*mm, 50*mm]),
            kv("共用事实", [["痕迹匹配", "两车碰撞高度、方向与事故经过一致。"], ["人员情况", "双方驾驶人均无人伤，车内无其他人员。"], ["其他财产", "无。"]]),
        ], "两车事故共用查勘报告，损失对象分栏记录。"),
        document_spec("C02", 6, "车辆及驾驶人资料摘要_演示.pdf", "车辆及驾驶人资料摘要（演示）", "vehicle_driver_summary", "2026-07-12T18:00:00+08:00", claims, ["VEH-C02-A", "VEH-C02-B", "PTY-C02-INS", "PTY-C02-TP"], [
            table("车辆及人员", ["车辆", "角色", "所有人/驾驶人", "使用性质", "核对结果"], [["演示-C02A", "承保车辆", "周某乙（虚构）", "家庭自用", "与交强险、商业险保单一致"], ["演示-C02B", "第三方车辆", "赵某丙（虚构）", "家庭自用", "与事故、定损、维修材料一致"]], [29*mm, 28*mm, 38*mm, 26*mm, 46*mm]),
            text_section("隐私边界", ["本摘要不包含真实身份证、驾驶证、行驶证号码，仅保留对象一致性检查所需的虚构标识。"]),
        ], "车辆和驾驶人一致性检查摘要。"),
        document_spec("C02", 7, "本车定损及核损明细_演示.pdf", "本车定损及核损明细（演示）", "assessment", "2026-07-14T11:00:00+08:00", [claims[0]], ["LOSS-C02-OWN", "VEH-C02-A"], [
            kv("金额口径", [["报损金额", yuan(710_000)], ["核定/认可金额", yuan(680_000)], ["调整说明", "剔除与本次事故无关的左后门旧划痕 300.00 元。"]]),
            table("核损项目", ["项目", "金额"], [["左前保险杠维修及附件", yuan(330_000)], ["左前大灯修复", yuan(190_000)], ["拆装工时", yuan(120_000)], ["喷漆材料", yuan(40_000)], ["合计", yuan(680_000)]], [105*mm, 50*mm]),
        ], "承保车辆损失核定演示明细。"),
        document_spec("C02", 8, "第三方车辆定损及核损明细_演示.pdf", "第三方车辆定损及核损明细（演示）", "assessment", "2026-07-14T14:30:00+08:00", [claims[1], claims[2]], ["LOSS-C02-TP-CTPL", "LOSS-C02-TP-COM", "VEH-C02-B"], [
            kv("损失对象", [["第三方车辆", "演示-C02B"], ["报损/核定/认可总额", yuan(920_000)], ["分摊口径", "交强险财产损失 2,000.00 元；超出部分 7,200.00 元进入商业三者险。"]]),
            table("核损项目", ["项目", "金额"], [["右后保险杠维修及附件", yuan(510_000)], ["右后尾灯更换", yuan(280_000)], ["工时及喷漆", yuan(130_000)], ["合计", yuan(920_000)]], [105*mm, 50*mm]),
        ], "第三方车辆损失总额及险种分摊依据。"),
        document_spec("C02", 9, "本车维修清单及费用证明_演示.pdf", "本车维修清单及费用证明（演示）", "repair_cost", "2026-07-17T17:00:00+08:00", [claims[0]], ["LOSS-C02-OWN", "VEH-C02-A"], [
            table("维修结算", ["项目", "金额", "关联"], [["左前保险杠维修及附件", yuan(330_000), "LOSS-C02-OWN"], ["左前大灯修复", yuan(190_000), "LOSS-C02-OWN"], ["拆装工时", yuan(120_000), "LOSS-C02-OWN"], ["喷漆材料", yuan(40_000), "LOSS-C02-OWN"], ["合计", yuan(680_000), "本车损失"]], [72*mm, 35*mm, 48*mm]),
            text_section("凭证边界", ["演示费用证明，不含真实发票号码或税控信息。"]),
        ], "本车虚构维修结算摘要。"),
        document_spec("C02", 10, "第三方维修清单及费用证明_演示.pdf", "第三方维修清单及费用证明（演示）", "repair_cost", "2026-07-18T16:00:00+08:00", [claims[1], claims[2]], ["LOSS-C02-TP-CTPL", "LOSS-C02-TP-COM", "VEH-C02-B"], [
            table("维修结算", ["项目", "金额"], [["右后保险杠维修及附件", yuan(510_000)], ["右后尾灯更换", yuan(280_000)], ["工时及喷漆", yuan(130_000)], ["合计", yuan(920_000)]], [105*mm, 50*mm]),
            kv("赔案分摊", [["交强险赔案 DEMO-CLM-C02-CTPL", yuan(200_000)], ["商业三者险赔案 DEMO-CLM-C02-COM-TP", yuan(720_000)], ["分摊合计", yuan(920_000)]]),
        ], "第三方车辆虚构维修结算摘要，不可作为真实发票。"),
        document_spec("C02", 11, "赔款计算书_本车_演示.pdf", "机动车损失保险赔款计算书（演示）", "calculation", "2026-07-19T09:00:00+08:00", [claims[0]], ["CALC-C02-OWN", "LOSS-C02-OWN", "POL-C02-COM", "CV-C02-OWN"], [
            kv("计算对象", [["赔案号", "DEMO-CLM-C02-OWN"], ["损失对象", "演示-C02A 本车"], ["险种", "机动车损失保险"], ["责任/免赔", "100%；0 元；0%"]]),
            table("计算", ["输入项", "金额"], [["维修及配件", yuan(520_000)], ["工时", yuan(120_000)], ["喷漆材料", yuan(40_000)], ["应付赔款", yuan(680_000)]], [105*mm, 50*mm]),
        ], "本车损失赔款计算演示材料。"),
        document_spec("C02", 12, "赔款计算书_第三方交强险_演示.pdf", "交强险财产损失赔款计算书（演示）", "calculation", "2026-07-19T09:20:00+08:00", [claims[1]], ["CALC-C02-CTPL", "LOSS-C02-TP-CTPL", "POL-C02-CTPL", "CV-C02-CTPL"], [
            kv("计算对象", [["赔案号", "DEMO-CLM-C02-CTPL"], ["损失对象", "演示-C02B 第三方车辆"], ["核定总损失", yuan(920_000)], ["交强险财产损失限额", yuan(200_000)]]),
            text_section("计算", ["交强险应付 = min(第三方车辆核定总损失 9,200.00 元，财产损失限额 2,000.00 元) = 2,000.00 元。剩余 7,200.00 元进入商业三者险计算。"]),
        ], "第三方财产损失交强险分摊计算。"),
        document_spec("C02", 13, "赔款计算书_第三方商业险_演示.pdf", "商业三者险赔款计算书（演示）", "calculation", "2026-07-19T09:40:00+08:00", [claims[2]], ["CALC-C02-COM-TP", "LOSS-C02-TP-COM", "POL-C02-COM", "CV-C02-TP"], [
            kv("计算对象", [["赔案号", "DEMO-CLM-C02-COM-TP"], ["损失对象", "演示-C02B 第三方车辆"], ["核定总损失", yuan(920_000)], ["交强险已分摊", yuan(200_000)], ["商业三者险限额", yuan(200_000_000)], ["免赔", "0 元；0%"]]),
            text_section("计算", ["商业三者险应付 = 9,200.00 - 2,000.00 = 7,200.00 元，未超过责任限额。"]),
        ], "第三方财产损失商业三者险分摊计算。"),
        document_spec("C02", 14, "核赔审批意见_演示.pdf", "核赔审批意见汇总（演示）", "approval", "2026-07-20T14:00:00+08:00", claims, ["APR-C02-OWN", "APR-C02-CTPL", "APR-C02-COM-TP"], [
            table("审批项目", ["赔案", "险种/对象", "核赔金额", "状态", "理由"], [["DEMO-CLM-C02-OWN", "车损险/演示-C02A", yuan(680_000), "通过", "剔除旧划痕后与维修清单一致"], ["DEMO-CLM-C02-CTPL", "交强险/演示-C02B", yuan(200_000), "通过", "第三方财产损失限额内"], ["DEMO-CLM-C02-COM-TP", "商业三者险/演示-C02B", yuan(720_000), "通过", "扣除交强险分摊后余额"]], [34*mm, 40*mm, 29*mm, 18*mm, 46*mm]),
            text_section("审批结论", ["三个赔案分别审批，合计 16,000.00 元；本车与第三方损失、交强险与商业险金额不得合并为单一计算口径。"]),
        ], "三笔赔案核赔审批汇总，保留各自险种和损失对象。"),
        document_spec("C02", 15, "支付及冲销记录_演示.pdf", "支付及冲销记录（演示）", "transaction", "2026-07-21T10:00:00+08:00", claims, ["PAY-C02-OWN", "PAY-C02-CTPL", "PAY-C02-COM-TP", "PTY-C02-INS", "PTY-C02-TP"], [
            table("有效交易", ["交易号", "赔案", "收款对象", "金额", "状态", "审批"], [["DEMO-TXN-C02-001", "OWN", "周某乙（虚构）", yuan(680_000), "成功", "APR-C02-OWN"], ["DEMO-TXN-C02-002", "CTPL", "赵某丙（虚构）", yuan(200_000), "成功", "APR-C02-CTPL"], ["DEMO-TXN-C02-003", "COM-TP", "赵某丙（虚构）", yuan(720_000), "成功", "APR-C02-COM-TP"]], [31*mm, 20*mm, 36*mm, 27*mm, 18*mm, 35*mm]),
            text_section("冲销核对", ["三笔交易号唯一，分别对应一笔审批。无失败付款、退款、冲销或重付；第三方收款两笔分别对应交强险和商业三者险，不构成重复支付。"]),
        ], "虚构支付流水摘要，不含真实银行账号。"),
        document_spec("C02", 16, "结案记录_演示.pdf", "赔案结案记录汇总（演示）", "closure", "2026-07-21T16:30:00+08:00", claims, claims + ["PAY-C02-OWN", "PAY-C02-CTPL", "PAY-C02-COM-TP"], [
            table("结案记录", ["赔案号", "范围", "结案类型", "支付状态", "结案金额"], [["DEMO-CLM-C02-OWN", "本车/车损险", "已赔付结案", "已结清", yuan(680_000)], ["DEMO-CLM-C02-CTPL", "第三方/交强险", "已赔付结案", "已结清", yuan(200_000)], ["DEMO-CLM-C02-COM-TP", "第三方/商业三者险", "已赔付结案", "已结清", yuan(720_000)]], [37*mm, 38*mm, 31*mm, 25*mm, 32*mm]),
            text_section("范围结论", ["同一事故关联上述三笔目标赔案，均已在 2026-07-21 完成有效支付后结案。事故明确无人伤；无其他赔案列入本次审查范围。"]),
        ], "三笔目标赔案结案记录汇总，结案与支付分别核对。"),
    ]
    evidence = {spec["document_id"]: f"EV-{spec['document_id']}" for spec in docs}
    ev = lambda seq: evidence[f"DOC-C02-{seq:02d}"]
    case = {
        "schemaVersion": 1, "dictionaryVersion": "1.0.0", "datasetCaseId": "C02", "caseRevision": 1, "isSynthetic": True, "preparedAt": PREPARED_AT,
        "reviewScope": {"targetClaimIds": claims, "relatedClaimIds": [], "lossTypes": ["own_vehicle", "third_party_vehicle"], "scopeLimitations": ["本次审查覆盖同一事故下三笔已结案赔案：本车车损险、第三方交强险财产损失、第三方商业三者险；无人伤且无其他财产损失。"]},
        "accident": {"accidentId": "ACC-C02", "occurredAt": "2026-07-12T14:35:00+08:00", "location": "杭州市滨江区测试大道与样本路路口（虚构地点）", "description": "演示-C02A 变更车道时与同向演示-C02B 发生碰撞。", "liabilityDescription": "演示-C02A 驾驶人承担全部责任，演示-C02B 驾驶人无责任。", "evidenceRefs": [ev(3), ev(4), ev(5)]},
        "parties": [{"partyId": "PTY-C02-INS", "displayName": "周某乙（虚构）", "kind": "person", "evidenceRefs": [ev(1), ev(2), ev(6)]}, {"partyId": "PTY-C02-TP", "displayName": "赵某丙（虚构）", "kind": "person", "evidenceRefs": [ev(4), ev(6)]}],
        "vehicles": [{"vehicleId": "VEH-C02-A", "role": "insured", "plateNumber": "演示-C02A", "ownerPartyId": "PTY-C02-INS", "driverPartyId": "PTY-C02-INS", "usage": "家庭自用", "powerType": "fuel", "evidenceRefs": [ev(1), ev(2), ev(6)]}, {"vehicleId": "VEH-C02-B", "role": "third_party", "plateNumber": "演示-C02B", "ownerPartyId": "PTY-C02-TP", "driverPartyId": "PTY-C02-TP", "usage": "家庭自用", "powerType": "fuel", "evidenceRefs": [ev(4), ev(6)]}],
        "claims": [
            {"claimId": claims[0], "reportNumber": "DEMO-RPT-C02", "claimNumber": "DEMO-CLM-C02-OWN", "handlingOrganization": "平安产险演示机构", "closureType": "paid_closed", "closedAt": "2026-07-21T16:30:00+08:00", "originalConclusion": "机动车损失保险核赔并支付 6,800.00 元后结案。", "originalPaymentStatus": "settled", "evidenceRefs": [ev(3), ev(16)]},
            {"claimId": claims[1], "reportNumber": "DEMO-RPT-C02", "claimNumber": "DEMO-CLM-C02-CTPL", "handlingOrganization": "平安产险演示机构", "closureType": "paid_closed", "closedAt": "2026-07-21T16:30:00+08:00", "originalConclusion": "交强险第三方财产损失核赔并支付 2,000.00 元后结案。", "originalPaymentStatus": "settled", "evidenceRefs": [ev(3), ev(16)]},
            {"claimId": claims[2], "reportNumber": "DEMO-RPT-C02", "claimNumber": "DEMO-CLM-C02-COM-TP", "handlingOrganization": "平安产险演示机构", "closureType": "paid_closed", "closedAt": "2026-07-21T16:30:00+08:00", "originalConclusion": "商业三者险核赔并支付第三方车辆损失 7,200.00 元后结案。", "originalPaymentStatus": "settled", "evidenceRefs": [ev(3), ev(16)]},
        ],
        "policies": [
            {"policyId": "POL-C02-CTPL", "policyNumber": "DEMO-CTPL-C02-2026", "availability": "available", "policyType": "ctpl", "insurerCode": "PINGAN", "vehicleId": "VEH-C02-A", "policyholderPartyId": "PTY-C02-INS", "insuredPartyIds": ["PTY-C02-INS"], "effectiveFrom": "2026-01-15T00:00:00+08:00", "effectiveTo": "2027-01-14T23:59:59+08:00", "coverages": [{"coverageId": "CV-C02-CTPL", "coverageCode": "CTPL", "status": "insured", "parentCoverageId": None, "insuranceAmount": na_money("交强险使用分项责任限额口径"), "perAccidentLimit": money(200_000), "deductibleAmount": money(0), "deductibleBasisPoints": 0, "terms": [CTPL_TERMS], "specialConditions": "本演示案仅涉及财产损失赔偿限额。", "evidenceRefs": [ev(1)]}], "terms": [CTPL_TERMS], "evidenceRefs": [ev(1)]},
            {"policyId": "POL-C02-COM", "policyNumber": "DEMO-COM-C02-2026", "availability": "available", "policyType": "commercial", "insurerCode": "PINGAN", "vehicleId": "VEH-C02-A", "policyholderPartyId": "PTY-C02-INS", "insuredPartyIds": ["PTY-C02-INS"], "effectiveFrom": "2026-01-15T00:00:00+08:00", "effectiveTo": "2027-01-14T23:59:59+08:00", "coverages": [{"coverageId": "CV-C02-OWN", "coverageCode": "OWN_DAMAGE", "status": "insured", "parentCoverageId": None, "insuranceAmount": money(18_000_000), "perAccidentLimit": na_money("本险种按保险金额及实际损失口径处理"), "deductibleAmount": money(0), "deductibleBasisPoints": 0, "terms": [{**COMMERCIAL_TERMS, "sectionIds": ["COMM-OWN", "COMM-COMMON"]}], "specialConditions": "本演示保单未约定本案适用的额外免赔。", "evidenceRefs": [ev(2)]}, {"coverageId": "CV-C02-TP", "coverageCode": "THIRD_PARTY", "status": "insured", "parentCoverageId": None, "insuranceAmount": na_money("本险种使用每次事故责任限额口径"), "perAccidentLimit": money(200_000_000), "deductibleAmount": money(0), "deductibleBasisPoints": 0, "terms": [{**COMMERCIAL_TERMS, "sectionIds": ["COMM-THIRD", "COMM-COMMON"]}], "specialConditions": "第三方财产损失先由交强险分摊，本险种承担超出部分。", "evidenceRefs": [ev(2)]}], "terms": [COMMERCIAL_MULTI_TERMS], "evidenceRefs": [ev(2)]},
        ],
        "endorsements": [],
        "losses": [
            {"lossId": "LOSS-C02-OWN", "claimId": claims[0], "vehicleId": "VEH-C02-A", "personPartyId": None, "lossType": "own_vehicle", "description": "承保车辆左前保险杠及左前大灯损失。", "claimedAmount": money(710_000), "assessedAmount": money(680_000), "agreedAmount": money(680_000), "evidenceRefs": [ev(5), ev(7), ev(9)]},
            {"lossId": "LOSS-C02-TP-CTPL", "claimId": claims[1], "vehicleId": "VEH-C02-B", "personPartyId": None, "lossType": "third_party_vehicle", "description": "第三方车辆核定总损失中由交强险财产损失限额分摊的部分。", "claimedAmount": money(200_000), "assessedAmount": money(200_000), "agreedAmount": money(200_000), "evidenceRefs": [ev(8), ev(10), ev(12)]},
            {"lossId": "LOSS-C02-TP-COM", "claimId": claims[2], "vehicleId": "VEH-C02-B", "personPartyId": None, "lossType": "third_party_vehicle", "description": "第三方车辆核定总损失扣除交强险分摊后由商业三者险承担的部分。", "claimedAmount": money(720_000), "assessedAmount": money(720_000), "agreedAmount": money(720_000), "evidenceRefs": [ev(8), ev(10), ev(13)]},
        ],
        "calculations": [
            {"calculationId": "CALC-C02-OWN", "claimId": claims[0], "policyId": "POL-C02-COM", "coverageId": "CV-C02-OWN", "status": "final", "lines": [{"lineId": "LINE-C02-OWN", "lossId": "LOSS-C02-OWN", "description": "本车核定维修费用加总", "operation": "sum", "inputs": [{"name": "维修及配件", "amount": money(520_000)}, {"name": "工时", "amount": money(120_000)}, {"name": "喷漆材料", "amount": money(40_000)}], "formulaText": "520000 + 120000 + 40000", "result": money(680_000), "evidenceRefs": [ev(7), ev(11)]}], "totalAmount": money(680_000), "adjustmentReason": "剔除与本次事故无关的左后门旧划痕 300.00 元。", "evidenceRefs": [ev(11)]},
            {"calculationId": "CALC-C02-CTPL", "claimId": claims[1], "policyId": "POL-C02-CTPL", "coverageId": "CV-C02-CTPL", "status": "final", "lines": [{"lineId": "LINE-C02-CTPL", "lossId": "LOSS-C02-TP-CTPL", "description": "第三方车辆损失在交强险财产损失限额内分摊", "operation": "recorded_formula", "inputs": [{"name": "第三方核定总损失", "amount": money(920_000)}, {"name": "交强险财产损失限额", "amount": money(200_000)}], "formulaText": "min(920000, 200000)", "result": money(200_000), "evidenceRefs": [ev(8), ev(12)]}], "totalAmount": money(200_000), "adjustmentReason": "第三方车辆核定总损失 9,200.00 元，先在交强险财产损失限额内分摊 2,000.00 元。", "evidenceRefs": [ev(12)]},
            {"calculationId": "CALC-C02-COM-TP", "claimId": claims[2], "policyId": "POL-C02-COM", "coverageId": "CV-C02-TP", "status": "final", "lines": [{"lineId": "LINE-C02-COM-TP", "lossId": "LOSS-C02-TP-COM", "description": "第三方核定总损失扣除交强险分摊后的余额", "operation": "difference", "inputs": [{"name": "第三方核定总损失", "amount": money(920_000)}, {"name": "交强险已分摊", "amount": money(200_000)}], "formulaText": "920000 - 200000", "result": money(720_000), "evidenceRefs": [ev(8), ev(13)]}], "totalAmount": money(720_000), "adjustmentReason": "扣除交强险已分摊 2,000.00 元后，余额 7,200.00 元由商业三者险承担。", "evidenceRefs": [ev(13)]},
        ],
        "approvals": [
            {"approvalId": "APR-C02-OWN", "claimId": claims[0], "policyId": "POL-C02-COM", "coverageId": "CV-C02-OWN", "calculationIds": ["CALC-C02-OWN"], "lossIds": ["LOSS-C02-OWN"], "status": "approved", "approvedAmount": money(680_000), "decidedAt": "2026-07-20T14:00:00+08:00", "reason": "剔除旧划痕后，本车定损、维修及计算一致。", "evidenceRefs": [ev(14)]},
            {"approvalId": "APR-C02-CTPL", "claimId": claims[1], "policyId": "POL-C02-CTPL", "coverageId": "CV-C02-CTPL", "calculationIds": ["CALC-C02-CTPL"], "lossIds": ["LOSS-C02-TP-CTPL"], "status": "approved", "approvedAmount": money(200_000), "decidedAt": "2026-07-20T14:05:00+08:00", "reason": "第三方财产损失在交强险财产损失限额内分摊。", "evidenceRefs": [ev(14)]},
            {"approvalId": "APR-C02-COM-TP", "claimId": claims[2], "policyId": "POL-C02-COM", "coverageId": "CV-C02-TP", "calculationIds": ["CALC-C02-COM-TP"], "lossIds": ["LOSS-C02-TP-COM"], "status": "approved", "approvedAmount": money(720_000), "decidedAt": "2026-07-20T14:10:00+08:00", "reason": "扣除交强险分摊后余额在商业三者险限额内。", "evidenceRefs": [ev(14)]},
        ],
        "payments": [
            {"paymentId": "PAY-C02-OWN", "claimId": claims[0], "externalTransactionId": "DEMO-TXN-C02-001", "kind": "disbursement", "status": "succeeded", "amount": money(680_000), "occurredAt": "2026-07-21T10:00:00+08:00", "payeePartyId": "PTY-C02-INS", "originalPaymentId": None, "approvalAllocations": [{"approvalId": "APR-C02-OWN", "amount": money(680_000)}], "evidenceRefs": [ev(15)]},
            {"paymentId": "PAY-C02-CTPL", "claimId": claims[1], "externalTransactionId": "DEMO-TXN-C02-002", "kind": "disbursement", "status": "succeeded", "amount": money(200_000), "occurredAt": "2026-07-21T10:10:00+08:00", "payeePartyId": "PTY-C02-TP", "originalPaymentId": None, "approvalAllocations": [{"approvalId": "APR-C02-CTPL", "amount": money(200_000)}], "evidenceRefs": [ev(15)]},
            {"paymentId": "PAY-C02-COM-TP", "claimId": claims[2], "externalTransactionId": "DEMO-TXN-C02-003", "kind": "disbursement", "status": "succeeded", "amount": money(720_000), "occurredAt": "2026-07-21T10:20:00+08:00", "payeePartyId": "PTY-C02-TP", "originalPaymentId": None, "approvalAllocations": [{"approvalId": "APR-C02-COM-TP", "amount": money(720_000)}], "evidenceRefs": [ev(15)]},
        ],
        "documents": [], "evidence": [], "observations": [], "dataGaps": [], "knowledgeRefs": [CTPL_TERMS, COMMERCIAL_MULTI_TERMS],
        "injury": {"declaredStatus": "no_injury_reported", "evidenceRefs": [ev(3), ev(4), ev(5)], "injuredPersons": []},
    }
    entities = {"claims": claims, "payments": ["PAY-C02-OWN", "PAY-C02-CTPL", "PAY-C02-COM-TP"], "losses": ["LOSS-C02-OWN", "LOSS-C02-TP-CTPL", "LOSS-C02-TP-COM"], "vehicles": ["VEH-C02-A", "VEH-C02-B"]}
    return case, docs, entities


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_case(case: dict[str, Any], docs: list[dict[str, Any]], entities: dict[str, list[str]]) -> None:
    case_id = case["datasetCaseId"]
    case_dir = ROOT / "inputs" / case_id
    documents_dir = case_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)
    built_docs = []
    evidence = []
    for spec in docs:
        pdf_path = documents_dir / spec["filename"]
        render_pdf(pdf_path, spec)
        pages = len(PdfReader(str(pdf_path)).pages)
        built_docs.append(
            {
                "documentId": spec["document_id"],
                "title": spec["title"],
                "materialType": spec["material_type"],
                "status": "available",
                "version": "v1",
                "relativePath": f"documents/{spec['filename']}",
                "sha256": sha256(pdf_path),
                "pageCount": pages,
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
                "quote": f"{spec['title']}中的关键事实与结构化记录一致。",
                "provenance": "original_document",
            }
        )
    case["documents"] = built_docs
    case["evidence"] = evidence
    write_json(case_dir / "case.json", case)

    expected = make_expected(case_id, entities, c02=case_id == "C02")
    check_ids = expected.pop("_check_ids")
    write_json(ROOT / "expected" / f"{case_id}.json", expected)
    write_json(ROOT / "review-steps" / f"{case_id}.json", make_steps(case_id, check_ids))


def main() -> None:
    for factory in (c01_archive, c02_archive):
        case, docs, entities = factory()
        build_case(case, docs, entities)
    print(json.dumps({"status": "built", "cases": ["C01", "C02"], "pdfCount": 27}, ensure_ascii=False))


if __name__ == "__main__":
    main()

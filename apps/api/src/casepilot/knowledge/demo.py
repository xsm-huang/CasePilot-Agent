"""V0 keyword retrieval, separate from the real PDF/vector knowledge pipeline."""

CLAUSES = [
    {
        "id": "AUTO-2025-01-04",
        "productCode": "AUTO-COMPREHENSIVE",
        "version": "2025-01",
        "title": "第四条 保险期间",
        "content": "保险人仅对保险期间内发生的保险事故承担保险责任。",
        "keywords": ["保险期间", "生效日期", "事故日期", "日期冲突"],
    },
    {
        "id": "AUTO-2025-01-18",
        "productCode": "AUTO-COMPREHENSIVE",
        "version": "2025-01",
        "title": "第十八条 索赔材料",
        "content": "被保险人请求赔偿时，应提供索赔申请书、事故证明、损失清单及维修发票等能够确认事故性质、原因和损失程度的材料。",
        "keywords": ["材料缺失", "维修发票", "索赔材料"],
    },
    {
        "id": "AUTO-2025-01-22",
        "productCode": "AUTO-COMPREHENSIVE",
        "version": "2025-01",
        "title": "第二十二条 损失核定",
        "content": "保险人依据事故责任、实际修复费用及保险合同约定核定赔偿金额。",
        "keywords": ["金额", "定损", "维修费用"],
    },
    {
        "id": "AUTO-2024-01-18",
        "productCode": "AUTO-COMPREHENSIVE",
        "version": "2024-01",
        "title": "旧版第十八条",
        "content": "此条款不应被 2025-01 版本案件检索到。",
        "keywords": ["材料缺失"],
    },
]


def search_clauses(product_code: str, version: str, findings: list[dict]) -> list[dict]:
    terms = (
        [f[k] for f in findings for k in ("title", "detail", "code")]
        if findings
        else ["损失核定", "金额"]
    )
    result = []
    for clause in CLAUSES:
        if clause["productCode"] != product_code or clause["version"] != version:
            continue
        score = sum(any(keyword in term for term in terms) for keyword in clause["keywords"])
        if score:
            result.append({k: clause[k] for k in ("id", "title", "content")} | {"score": score})
    return sorted(result, key=lambda c: -c["score"])

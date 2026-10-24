"""Fictional case data for the V0 demonstration."""

CASES = [
    {
        "id": "CASE-2026-001",
        "claimant": "张某",
        "productCode": "AUTO-COMPREHENSIVE",
        "clauseVersion": "2025-01",
        "policyEffectiveDate": "2026-08-10",
        "accidentDate": "2026-08-08",
        "claimAmount": 28600,
        "materials": [
            {
                "type": "claim_form",
                "name": "索赔申请书.pdf",
                "fields": {"accidentDate": "2026-08-08", "claimAmount": 28600},
            },
            {
                "type": "accident_certificate",
                "name": "事故认定书.pdf",
                "fields": {"accidentDate": "2026-08-08", "liability": "被保险人全责"},
            },
            {
                "type": "damage_assessment",
                "name": "定损单.pdf",
                "fields": {"assessedAmount": 27500},
            },
        ],
    },
    {
        "id": "CASE-2026-002",
        "claimant": "李某",
        "productCode": "AUTO-COMPREHENSIVE",
        "clauseVersion": "2025-01",
        "policyEffectiveDate": "2026-06-01",
        "accidentDate": "2026-09-12",
        "claimAmount": 8200,
        "materials": [
            {
                "type": "claim_form",
                "name": "索赔申请书.pdf",
                "fields": {"accidentDate": "2026-09-12", "claimAmount": 8200},
            },
            {
                "type": "accident_certificate",
                "name": "事故认定书.pdf",
                "fields": {"accidentDate": "2026-09-12", "liability": "对方全责"},
            },
            {"type": "damage_assessment", "name": "定损单.pdf", "fields": {"assessedAmount": 8100}},
            {"type": "repair_invoice", "name": "维修发票.pdf", "fields": {"invoiceAmount": 8100}},
        ],
    },
]

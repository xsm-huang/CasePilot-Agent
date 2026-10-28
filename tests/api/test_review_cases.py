from datetime import date
from pathlib import Path
from shutil import copytree

import pytest
from casepilot.cases.review_repository import (
    DEFAULT_REVIEW_CASES_DIR,
    ReviewCaseDataError,
    get_review_case,
    list_review_cases,
    review_document,
)


def test_prepared_cases_query_and_amount_projection():
    result = list_review_cases()
    assert result["dataStatus"] == "ready"
    assert [item["id"] for item in result["items"]] == ["C01", "C02", "C03"]
    c03 = result["items"][2]
    assert c03["targetClaims"][0]["claimNumber"] == "DEMO-CLM-C03-COM-TP"
    assert c03["relatedClaims"][0]["claimNumber"] == "DEMO-CLM-C03-CTPL"
    assert c03["originalApprovedAmount"]["amountFen"] == 800000
    assert c03["effectivePaidAmount"]["amountFen"] == 900000
    assert c03["injuryStatus"] == "no_injury_reported"


def test_query_matches_claim_report_plate_and_filters():
    assert [item["id"] for item in list_review_cases(query_type="claim_number", query="C03-CTPL")["items"]] == ["C03"]
    assert [item["id"] for item in list_review_cases(query_type="report_number", query="RPT-C02")["items"]] == ["C02"]
    assert [item["id"] for item in list_review_cases(query_type="plate_number", query="C01")["items"]] == ["C01"]
    assert [item["id"] for item in list_review_cases(closed_from=date(2026, 8, 1))["items"]] == ["C01"]
    assert list_review_cases(review_status="running")["items"] == []


def test_detail_preserves_relationships_and_missing_material():
    detail = get_review_case("C03")
    assert detail["claims"][0]["scopeRole"] == "target"
    assert detail["claims"][1]["scopeRole"] == "related"
    assert {policy["policyType"] for policy in detail["policies"]} == {"ctpl", "commercial"}
    assert detail["dataGaps"][0]["kind"] == "not_obtained"
    unavailable = next(item for item in detail["documents"] if item["status"] == "not_obtained")
    assert unavailable["contentUrl"] is None
    assert any(source["page"] == 1 for source in detail["accident"]["sources"])


def test_document_resolution_is_case_scoped_and_hash_checked():
    result = review_document("C01", "DOC-C01-01")
    assert result is not None
    path, _ = result
    assert path.is_file() and path.suffix.lower() == ".pdf"
    assert review_document("C01", "DOC-C02-01") is None
    assert review_document("C03", "DOC-C03-13") is None


def test_missing_dataset_is_distinct_from_empty_query(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CASEPILOT_REVIEW_CASES_DIR", str(tmp_path / "missing"))
    assert list_review_cases() == {"dataStatus": "not_imported", "items": []}


def test_changed_document_is_not_served(monkeypatch, tmp_path: Path):
    case_dir = tmp_path / "inputs" / "C01"
    copytree(DEFAULT_REVIEW_CASES_DIR / "C01", case_dir)
    document = case_dir / "documents" / "商业险保单_演示.pdf"
    document.write_bytes(document.read_bytes() + b"changed")
    monkeypatch.setenv("CASEPILOT_REVIEW_CASES_DIR", str(tmp_path / "inputs"))
    with pytest.raises(ReviewCaseDataError, match="校验值"):
        review_document("C01", "DOC-C01-01")


def test_review_case_http_resources(api):
    response = api.get("/review-cases", params={"queryType": "plate_number", "query": "C02"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["C02"]
    assert api.get("/review-cases", params={"query": "C02"}).status_code == 400
    assert api.get("/review-cases", params={"closedFrom": "2026-09-01", "closedTo": "2026-08-01"}).status_code == 400
    assert api.get("/review-cases/missing").status_code == 404
    detail = api.get("/review-cases/C01").json()
    source = detail["accident"]["sources"][0]
    document = api.get(f"/review-cases/C01/documents/{source['documentId']}/content")
    assert document.status_code == 200
    assert document.headers["content-type"] == "application/pdf"
    assert api.get("/review-cases/C01/documents/DOC-C02-01/content").status_code == 404

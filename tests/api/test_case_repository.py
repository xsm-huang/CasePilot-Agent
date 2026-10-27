"""Reading an illustrative case cannot mutate the shared source."""

from casepilot.cases.repository import get_case


def test_case_reads_return_independent_material_snapshots():
    first = get_case("CASE-2026-001")
    first["materials"][0]["fields"]["accidentDate"] = "changed"
    assert get_case(first["id"])["materials"][0]["fields"]["accidentDate"] == "2026-08-08"
    assert get_case("missing") is None

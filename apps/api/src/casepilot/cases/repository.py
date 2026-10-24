"""Read isolated snapshots of the demonstration cases."""

from copy import deepcopy

from .seeds import CASES


def get_case(case_id: str):
    return next((deepcopy(c) for c in CASES if c["id"] == case_id), None)


def list_cases():
    return deepcopy(CASES)

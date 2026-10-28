"""Read-only transport models for prepared closed-claim review cases."""

from typing import Literal

from .analysis import DTO


class ReviewMoney(DTO):
    status: Literal["known", "unknown", "not_applicable"]
    amountFen: int | None
    currency: str = "CNY"
    reason: str | None = None


class ReviewEvidenceSource(DTO):
    evidenceId: str
    sourceType: Literal["case_document", "shared_document", "structured_record"]
    title: str
    documentId: str | None = None
    documentVersion: str | None = None
    page: int | None = None
    recordPointer: str | None = None
    quote: str | None = None


class ReviewClaimSummary(DTO):
    claimId: str
    claimNumber: str
    reportNumber: str
    scopeRole: Literal["target", "related"]
    closureType: str
    closedAt: str
    originalPaymentStatus: str


class ReviewVehicleSummary(DTO):
    vehicleId: str
    role: str
    plateNumber: str


class ReviewCaseListItem(DTO):
    id: str
    revision: int
    targetClaims: list[ReviewClaimSummary]
    relatedClaims: list[ReviewClaimSummary]
    vehicles: list[ReviewVehicleSummary]
    accidentAt: str
    originalApprovedAmount: ReviewMoney
    effectivePaidAmount: ReviewMoney
    injuryStatus: str
    latestReviewStatus: Literal["not_started"] = "not_started"


class ReviewCaseListResponse(DTO):
    dataStatus: Literal["ready", "not_imported"]
    items: list[ReviewCaseListItem]


class ReviewParty(DTO):
    partyId: str
    displayName: str
    kind: str


class ReviewVehicleDetail(ReviewVehicleSummary):
    ownerName: str | None = None
    driverName: str | None = None
    usage: str | None = None
    powerType: str | None = None
    sources: list[ReviewEvidenceSource]


class ReviewClaimDetail(ReviewClaimSummary):
    handlingOrganization: str
    originalConclusion: str
    sources: list[ReviewEvidenceSource]


class ReviewTermRef(DTO):
    documentId: str
    version: str
    sectionIds: list[str]


class ReviewCoverage(DTO):
    coverageId: str
    coverageCode: str
    status: str
    insuranceAmount: ReviewMoney
    perAccidentLimit: ReviewMoney
    deductibleAmount: ReviewMoney
    deductibleBasisPoints: int | None = None
    specialConditions: str | None = None
    terms: list[ReviewTermRef]
    sources: list[ReviewEvidenceSource]


class ReviewPolicy(DTO):
    policyId: str
    policyNumber: str | None = None
    availability: str
    policyType: str
    vehicleId: str | None = None
    effectiveFrom: str | None = None
    effectiveTo: str | None = None
    coverages: list[ReviewCoverage]
    sources: list[ReviewEvidenceSource]


class ReviewLoss(DTO):
    lossId: str
    claimId: str
    vehicleId: str | None = None
    personPartyId: str | None = None
    lossType: str
    description: str
    claimedAmount: ReviewMoney
    assessedAmount: ReviewMoney
    agreedAmount: ReviewMoney
    sources: list[ReviewEvidenceSource]


class ReviewProcessingRecord(DTO):
    recordId: str
    recordType: Literal["calculation", "approval", "payment"]
    claimId: str
    title: str
    status: str
    occurredAt: str | None = None
    amount: ReviewMoney | None = None
    detail: str | None = None
    sources: list[ReviewEvidenceSource]


class ReviewTimelineEntry(DTO):
    entryId: str
    eventType: str
    occurredAt: str
    title: str
    detail: str | None = None
    sources: list[ReviewEvidenceSource]


class ReviewDocument(DTO):
    documentId: str
    title: str
    materialType: str
    status: str
    version: str
    pageCount: int | None = None
    claimIds: list[str]
    entityIds: list[str]
    issuedAt: str | None = None
    receivedAt: str | None = None
    sourceDescription: str
    contentUrl: str | None = None


class ReviewDataGap(DTO):
    gapId: str
    kind: str
    entityIds: list[str]
    fieldPaths: list[str]
    description: str
    sources: list[ReviewEvidenceSource]


class ReviewAccident(DTO):
    accidentId: str
    occurredAt: str
    location: str
    description: str
    liabilityDescription: str
    sources: list[ReviewEvidenceSource]


class ReviewScope(DTO):
    lossTypes: list[str]
    scopeLimitations: list[str]


class ReviewInjury(DTO):
    declaredStatus: str
    injuredPersonIds: list[str]
    sources: list[ReviewEvidenceSource]


class ReviewCaseDetail(DTO):
    id: str
    revision: int
    isSynthetic: bool
    preparedAt: str
    latestReviewStatus: Literal["not_started"] = "not_started"
    scope: ReviewScope
    accident: ReviewAccident
    injury: ReviewInjury
    parties: list[ReviewParty]
    vehicles: list[ReviewVehicleDetail]
    claims: list[ReviewClaimDetail]
    policies: list[ReviewPolicy]
    losses: list[ReviewLoss]
    processingRecords: list[ReviewProcessingRecord]
    timeline: list[ReviewTimelineEntry]
    documents: list[ReviewDocument]
    dataGaps: list[ReviewDataGap]
    originalApprovedAmount: ReviewMoney
    effectivePaidAmount: ReviewMoney

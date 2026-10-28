// Generated from Python Pydantic models by pnpm --filter @casepilot/contracts generate. Do not edit.

export type Schemaversion = 2;
export type Analysisid = string;
export type Conversationid = string;
export type Seq = number;
export type Revision = number;
export type At = string;
export type Type = "review.accepted";
export type Interruptkey = string;
export type Decision = "approve" | "reject";
export type Revision1 = number;
export type Inputversion = string;
export type Documentid = string;
export type Documentsha256 = string;
export type Version = string;
export type Sectionids = string[];
export type Status = "ready" | "unavailable";
export type Generationid = string | null;
export type Productcode = string | null;
export type Clauseversion = string | null;
export type Embeddingprofile = string | null;
export type Knowledgebindings = ReviewKnowledgeBinding[];
export type Messageids = string[];
export type Modelprofile = string;
export type Promptversion = string;
export type Factid = string;
export type Fieldpath = string;
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "JsonValue".
 */
export type JsonValue = unknown;
export type Sourcetype = "case" | "material";
export type Materialid = string | null;
export type Facts = Fact[];
export type Code = string;
export type Source = "rule";
export type Severity = "low" | "medium" | "high";
export type Title = string;
export type Detail = string;
export type Factrefs = string[];
export type Factid1 = string;
export type Sourcevalues = SourceValue[];
export type Rulefindings = RuleFinding[];
export type Title1 = string;
export type Inference = string;
export type Evidencestatus = "supported" | "insufficient";
/**
 * @maxItems 30
 */
export type Factrefs1 = string[];
/**
 * @maxItems 12
 */
export type Citationrefs =
  | []
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string];
/**
 * @maxItems 12
 */
export type Pendingitems =
  | []
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string];
export type Modelfindings = ModelFinding[];
export type Citationid = string;
export type Chunkid = string;
export type Generationid1 = string;
export type Documentid1 = string;
export type Filename = string;
export type Productcode1 = string;
export type Clauseversion1 = string;
export type Page = number;
export type Ordinal = number;
export type Content = string;
export type Citations = Citation[];
export type Insufficientevidence = boolean;
export type Caseid = string;
export type Sectionkey = "summary" | "findings" | "recommendations";
export type Content1 = string;
export type Factrefs2 = string[];
export type Citationrefs1 = string[];
export type Committedat = string;
export type Sections = ReportSection[];
export type Insufficientevidence1 = boolean;
export type Reviewercomment = string | null;
export type Schemaversion1 = 2;
export type Id = string;
export type Caseid1 = string;
export type Conversationid1 = string;
export type Kind = "initial" | "followup";
export type Question = string;
export type Status1 =
  "queued" | "running" | "waiting_review" | "resuming" | "recoverable" | "completed" | "rejected" | "failed";
export type Snapshotkind = "closed_claim_review";
export type Caseid2 = string;
export type Caserevision = number;
export type Preparedat = string;
export type Scopeitemid = string;
export type Kind1 = string;
export type Title2 = string;
export type Status2 = "executable" | "limited" | "blocked";
export type Entityids = string[];
export type Reason = string | null;
export type Requiredmaterialtypes = string[];
export type Scopeitems = ReviewScopeItem[];
export type Knowledgebindings1 = ReviewKnowledgeBinding[];
export type Predecessoranalysisid = string | null;
export type Supplementid = string;
export type Version1 = number;
export type Analysisid1 = string;
export type Title3 = string;
export type Materialtype = string;
export type Entityids1 = string[];
export type Sha256 = string;
export type Addedat = string;
export type Addedby = string;
export type Page1 = number;
export type Content2 = string;
export type Pages = SupplementPage[];
export type Evidencesupplements = EvidenceSupplement[];
export type Reviewsupplementids = string[];
export type Revision2 = number;
export type Lasteventseq = number;
export type Usermessageid = string;
export type Assistantmessageid = string | null;
export type Facts1 = Fact[];
export type Rulefindings1 = RuleFinding[];
export type Modelfindings1 = ModelFinding[];
export type Citations1 = Citation[];
export type Sections1 = ReportSection[];
export type Interruptkey1 = string;
export type Checkpointid = string;
export type Revision3 = number;
export type Reason1 = string;
export type Executionid = string;
export type Key = string;
export type Name = string;
export type Attempt = number;
export type Status3 = "running" | "completed" | "failed";
export type Summary = string;
export type Durationms = number;
export type Nodes = ExecutionData[];
export type Tools = ExecutionData[];
export type Schemaversion2 = 2;
export type Analysisid2 = string;
export type Conversationid2 = string;
export type Seq1 = number;
export type Revision4 = number;
export type At1 = string;
export type Type1 = "analysis.status";
export type Status4 =
  "queued" | "running" | "waiting_review" | "resuming" | "recoverable" | "completed" | "rejected" | "failed";
export type Revision5 = number;
export type Schemaversion3 = 2;
export type Analysisid3 = string;
export type Conversationid3 = string;
export type Seq2 = number;
export type Revision6 = number;
export type At2 = string;
export type Type2 =
  "node.started" | "node.completed" | "node.failed" | "tool.started" | "tool.completed" | "tool.failed";
export type Schemaversion4 = 2;
export type Analysisid4 = string;
export type Conversationid4 = string;
export type Seq3 = number;
export type Revision7 = number;
export type At3 = string;
export type Type3 = "analysis.ready";
export type Schemaversion5 = 2;
export type Analysisid5 = string;
export type Conversationid5 = string;
export type Seq4 = number;
export type Revision8 = number;
export type At4 = string;
export type Type4 = "review.required";
export type Schemaversion6 = 2;
export type Analysisid6 = string;
export type Conversationid6 = string;
export type Seq5 = number;
export type Revision9 = number;
export type At5 = string;
export type Type5 = "report.section";
export type Schemaversion7 = 2;
export type Analysisid7 = string;
export type Conversationid7 = string;
export type Seq6 = number;
export type Revision10 = number;
export type At6 = string;
export type Type6 = "report.completed";
export type Assistantmessageid1 = string;
export type Revision11 = number;
export type Schemaversion8 = 2;
export type Analysisid8 = string;
export type Conversationid8 = string;
export type Seq7 = number;
export type Revision12 = number;
export type At7 = string;
export type Type7 = "analysis.failed" | "analysis.recoverable";
export type Code1 = string;
export type Message = string;
export type Requestid = string;
export type Revision13 = number;
export type Schemaversion9 = 2;
export type Analysisid9 = string;
export type Conversationid9 = string;
export type Seq8 = number;
export type Revision14 = number;
export type At8 = string;
export type Type8 = "analysis.rejected";
export type Comment = string;
export type Revision15 = number;
export type Schemaversion10 = 2;
export type Analysisid10 = string;
export type Conversationid10 = string;
export type Seq9 = number;
export type Revision16 = number;
export type At9 = string;
export type Type9 = "evidence.supplemented";
export type Revision17 = number;
export type Timeline = (
  | StatusEvent
  | ExecutionEvent
  | ReadyEvent
  | ReviewEvent
  | AcceptedEvent
  | SectionEvent
  | CompletedEvent
  | FailureEvent
  | RejectedEvent
  | SupplementedEvent
)[];
export type Chunkid1 = string;
export type Page2 = number;
export type Ordinal1 = number;
export type Content3 = string;
export type Accepted = true;
export type Taskid = string;
export type Revision18 = number;
export type Id1 = string;
export type Caseid3 = string;
export type Title4 = string;
export type Createdat = string;
export type Updatedat = string;
export type Activeanalysisid = string | null;
export type Id2 = string;
export type Role = "user" | "assistant";
export type Content4 = string;
export type Analysisid11 = string;
export type Createdat1 = string;
export type Messages = Message1[];
export type Analysisids = string[];
export type Nextbefore = string | null;
export type Id3 = string;
export type Caseid4 = string;
export type Title5 = string;
export type Createdat2 = string;
export type Updatedat1 = string;
export type Activeanalysisid1 = string | null;
export type Conversationid11 = string;
export type Kind2 = "initial" | "followup";
export type Question1 = string | null;
export type Expectedinputversion = string | null;
export type Predecessoranalysisid1 = string | null;
export type Supplementids = string[];
export type Title6 = string;
export type Expectedrevision = number;
export type Accidentid = string;
export type Occurredat = string;
export type Location = string;
export type Description = string;
export type Liabilitydescription = string;
export type Evidenceid = string;
export type Sourcetype1 = "case_document" | "shared_document" | "structured_record";
export type Title7 = string;
export type Documentid2 = string | null;
export type Documentversion = string | null;
export type Page3 = number | null;
export type Recordpointer = string | null;
export type Quote = string | null;
export type Sources = ReviewEvidenceSource[];
export type Policyid = string;
export type Policytype = string;
export type Availability = string;
export type Coveragecodes = string[];
export type Id4 = string;
export type Revision19 = number;
export type Issynthetic = boolean;
export type Preparedat1 = string;
export type Latestreviewstatus =
  | "not_started"
  | "running"
  | "pending_review"
  | "pending_verification"
  | "vehicle_review_completed"
  | "failed"
  | "awaiting_recovery";
export type Losstypes = string[];
export type Scopelimitations = string[];
export type Declaredstatus = string;
export type Injuredpersonids = string[];
export type Sources1 = ReviewEvidenceSource[];
export type Partyid = string;
export type Displayname = string;
export type Kind3 = string;
export type Parties = ReviewParty[];
export type Vehicleid = string;
export type Role1 = string;
export type Platenumber = string;
export type Ownername = string | null;
export type Drivername = string | null;
export type Usage = string | null;
export type Powertype = string | null;
export type Sources2 = ReviewEvidenceSource[];
export type Vehicles = ReviewVehicleDetail[];
export type Claimid = string;
export type Claimnumber = string;
export type Reportnumber = string;
export type Scoperole = "target" | "related";
export type Closuretype = string;
export type Closedat = string;
export type Originalpaymentstatus = string;
export type Handlingorganization = string;
export type Originalconclusion = string;
export type Sources3 = ReviewEvidenceSource[];
export type Claims = ReviewClaimDetail[];
export type Policyid1 = string;
export type Policynumber = string | null;
export type Availability1 = string;
export type Policytype1 = string;
export type Vehicleid1 = string | null;
export type Effectivefrom = string | null;
export type Effectiveto = string | null;
export type Coverageid = string;
export type Coveragecode = string;
export type Status5 = string;
export type Status6 = "known" | "unknown" | "not_applicable";
export type Amountfen = number | null;
export type Currency = string;
export type Reason2 = string | null;
export type Deductiblebasispoints = number | null;
export type Specialconditions = string | null;
export type Documentid3 = string;
export type Version2 = string;
export type Sectionids1 = string[];
export type Terms = ReviewTermRef[];
export type Sources4 = ReviewEvidenceSource[];
export type Coverages = ReviewCoverage[];
export type Sources5 = ReviewEvidenceSource[];
export type Policies = ReviewPolicy[];
export type Lossid = string;
export type Claimid1 = string;
export type Vehicleid2 = string | null;
export type Personpartyid = string | null;
export type Losstype = string;
export type Description1 = string;
export type Sources6 = ReviewEvidenceSource[];
export type Losses = ReviewLoss[];
export type Recordid = string;
export type Recordtype = "calculation" | "approval" | "payment";
export type Claimid2 = string;
export type Title8 = string;
export type Status7 = string;
export type Occurredat1 = string | null;
export type Detail1 = string | null;
export type Sources7 = ReviewEvidenceSource[];
export type Processingrecords = ReviewProcessingRecord[];
export type Entryid = string;
export type Eventtype = string;
export type Occurredat2 = string;
export type Title9 = string;
export type Detail2 = string | null;
export type Sources8 = ReviewEvidenceSource[];
export type Timeline1 = ReviewTimelineEntry[];
export type Documentid4 = string;
export type Title10 = string;
export type Materialtype1 = string;
export type Status8 = string;
export type Version3 = string;
export type Pagecount = number | null;
export type Claimids = string[];
export type Entityids2 = string[];
export type Issuedat = string | null;
export type Receivedat = string | null;
export type Sourcedescription = string;
export type Contenturl = string | null;
export type Documents = ReviewDocument[];
export type Gapid = string;
export type Kind4 = string;
export type Entityids3 = string[];
export type Fieldpaths = string[];
export type Description2 = string;
export type Sources9 = ReviewEvidenceSource[];
export type Datagaps = ReviewDataGap[];
export type Id5 = string;
export type Revision20 = number;
export type Claimid3 = string;
export type Claimnumber1 = string;
export type Reportnumber1 = string;
export type Scoperole1 = "target" | "related";
export type Closuretype1 = string;
export type Closedat1 = string;
export type Originalpaymentstatus1 = string;
export type Targetclaims = ReviewClaimSummary[];
export type Relatedclaims = ReviewClaimSummary[];
export type Vehicleid3 = string;
export type Role2 = string;
export type Platenumber1 = string;
export type Vehicles1 = ReviewVehicleSummary[];
export type Accidentat = string;
export type Injurystatus = string;
export type Latestreviewstatus1 =
  | "not_started"
  | "running"
  | "pending_review"
  | "pending_verification"
  | "vehicle_review_completed"
  | "failed"
  | "awaiting_recovery";
export type Datastatus = "ready" | "not_imported";
export type Items = ReviewCaseListItem[];
export type Targetclaimids = string[];
export type Relatedclaimids = string[];
export type Vehicleids = string[];
export type Lossids = string[];
export type Scopelimitations1 = string[];
export type Caseid5 = string;
export type Expectedinputversion1 = string;
export type Status9 = "ready" | "partial" | "blocked";
export type Applicablepolicies = ReviewApplicablePolicy[];
export type Scopeitems1 = ReviewScopeItem[];
export type Knowledgebindings2 = ReviewKnowledgeBinding[];
export type Injurystatus1 = string;
export type Injuredpersonids1 = string[];
export type Blockingreasons = string[];
export type Decision1 = "approve" | "reject";
export type Comment1 = string;
export type Interruptkey2 = string;
export type Expectedrevision1 = number;
export type Supplementids1 = string[];
export type Attempt1 = number;
export type Status10 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Startedat = string;
export type Finishedat = string | null;
export type Code2 = string;
export type Message2 = string;
export type Reasoncode = string | null;
export type Providercode = string | null;
export type Httpstatus = number | null;
export type Requestid1 = string | null;
export type Retryafter = number | null;
export type Generationid2 = string;
export type Documentid5 = string;
export type Productcode2 = string;
export type Clauseversion2 = string;
export type Filename1 = string;
export type Sha2561 = string;
export type Status11 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Revision21 = number;
export type Attempt2 = number;
export type Pagecount1 = number;
export type Chunkcount = number;
export type Embeddedcount = number;
export type Isactive = boolean;
export type Createdat3 = string;
export type Updatedat2 = string;
export type Attempts = V1KnowledgeAttempt[];
export type Expectedrevision2 = number;
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "WorkspaceEvent".
 */
export type WorkspaceEvent =
  | StatusEvent
  | ExecutionEvent
  | ReadyEvent
  | ReviewEvent
  | AcceptedEvent
  | SectionEvent
  | CompletedEvent
  | FailureEvent
  | RejectedEvent
  | SupplementedEvent;

export interface TransportContract {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "AcceptedEvent".
 */
export interface AcceptedEvent {
  schemaVersion: Schemaversion;
  analysisId: Analysisid;
  conversationId: Conversationid;
  seq: Seq;
  revision: Revision;
  at: At;
  type: Type;
  data: ReviewAcceptedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewAcceptedData".
 */
export interface ReviewAcceptedData {
  interruptKey: Interruptkey;
  decision: Decision;
  revision: Revision1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "AnalysisContext".
 */
export interface AnalysisContext {
  inputVersion: Inputversion;
  knowledgeBindings: Knowledgebindings;
  messageIds: Messageids;
  modelProfile: Modelprofile;
  promptVersion: Promptversion;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewKnowledgeBinding".
 */
export interface ReviewKnowledgeBinding {
  documentId: Documentid;
  documentSha256: Documentsha256;
  version: Version;
  sectionIds: Sectionids;
  status: Status;
  generationId?: Generationid;
  productCode?: Productcode;
  clauseVersion?: Clauseversion;
  embeddingProfile?: Embeddingprofile;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "AnalysisReadyData".
 */
export interface AnalysisReadyData {
  facts: Facts;
  ruleFindings: Rulefindings;
  modelFindings: Modelfindings;
  citations: Citations;
  insufficientEvidence: Insufficientevidence;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Fact".
 */
export interface Fact {
  factId: Factid;
  fieldPath: Fieldpath;
  value: JsonValue;
  sourceType: Sourcetype;
  materialId?: Materialid;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "RuleFinding".
 */
export interface RuleFinding {
  code: Code;
  source: Source;
  severity: Severity;
  title: Title;
  detail: Detail;
  factRefs: Factrefs;
  sourceValues: Sourcevalues;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SourceValue".
 */
export interface SourceValue {
  factId: Factid1;
  value: JsonValue;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ModelFinding".
 */
export interface ModelFinding {
  title: Title1;
  inference: Inference;
  evidenceStatus: Evidencestatus;
  factRefs: Factrefs1;
  citationRefs: Citationrefs;
  pendingItems: Pendingitems;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Citation".
 */
export interface Citation {
  citationId: Citationid;
  chunkId: Chunkid;
  generationId: Generationid1;
  documentId: Documentid1;
  fileName: Filename;
  productCode: Productcode1;
  clauseVersion: Clauseversion1;
  page: Page;
  ordinal: Ordinal;
  content: Content;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "AnalysisReport".
 */
export interface AnalysisReport {
  caseId: Caseid;
  sections: Sections;
  insufficientEvidence: Insufficientevidence1;
  reviewerComment: Reviewercomment;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReportSection".
 */
export interface ReportSection {
  sectionKey: Sectionkey;
  content: Content1;
  factRefs: Factrefs2;
  citationRefs: Citationrefs1;
  committedAt: Committedat;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "AnalysisTask".
 */
export interface AnalysisTask {
  schemaVersion: Schemaversion1;
  id: Id;
  caseId: Caseid1;
  conversationId: Conversationid1;
  kind: Kind;
  question: Question;
  status: Status1;
  caseSnapshot: ClosedClaimReviewSnapshot;
  predecessorAnalysisId: Predecessoranalysisid;
  evidenceSupplements: Evidencesupplements;
  reviewSupplementIds: Reviewsupplementids;
  revision: Revision2;
  lastEventSeq: Lasteventseq;
  userMessageId: Usermessageid;
  assistantMessageId: Assistantmessageid;
  context: AnalysisContext;
  facts: Facts1;
  ruleFindings: Rulefindings1;
  modelFindings: Modelfindings1;
  citations: Citations1;
  sections: Sections1;
  report: AnalysisReport | null;
  pendingReview: PendingReview | null;
  execution: Execution;
  error: PublicError | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ClosedClaimReviewSnapshot".
 */
export interface ClosedClaimReviewSnapshot {
  snapshotKind: Snapshotkind;
  caseId: Caseid2;
  caseRevision: Caserevision;
  preparedAt: Preparedat;
  payload: Payload;
  scopeItems: Scopeitems;
  knowledgeBindings: Knowledgebindings1;
}
export interface Payload {
  [k: string]: JsonValue;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewScopeItem".
 */
export interface ReviewScopeItem {
  scopeItemId: Scopeitemid;
  kind: Kind1;
  title: Title2;
  status: Status2;
  entityIds: Entityids;
  reason?: Reason;
  requiredMaterialTypes: Requiredmaterialtypes;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "EvidenceSupplement".
 */
export interface EvidenceSupplement {
  supplementId: Supplementid;
  version: Version1;
  analysisId: Analysisid1;
  title: Title3;
  materialType: Materialtype;
  entityIds: Entityids1;
  sha256: Sha256;
  addedAt: Addedat;
  addedBy: Addedby;
  pages: Pages;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SupplementPage".
 */
export interface SupplementPage {
  page: Page1;
  content: Content2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "PendingReview".
 */
export interface PendingReview {
  interruptKey: Interruptkey1;
  checkpointId: Checkpointid;
  revision: Revision3;
  reason: Reason1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Execution".
 */
export interface Execution {
  nodes: Nodes;
  tools: Tools;
  timeline: Timeline;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ExecutionData".
 */
export interface ExecutionData {
  executionId: Executionid;
  key: Key;
  name: Name;
  attempt: Attempt;
  status: Status3;
  summary: Summary;
  durationMs: Durationms;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "StatusEvent".
 */
export interface StatusEvent {
  schemaVersion: Schemaversion2;
  analysisId: Analysisid2;
  conversationId: Conversationid2;
  seq: Seq1;
  revision: Revision4;
  at: At1;
  type: Type1;
  data: StatusData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "StatusData".
 */
export interface StatusData {
  status: Status4;
  revision: Revision5;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ExecutionEvent".
 */
export interface ExecutionEvent {
  schemaVersion: Schemaversion3;
  analysisId: Analysisid3;
  conversationId: Conversationid3;
  seq: Seq2;
  revision: Revision6;
  at: At2;
  type: Type2;
  data: ExecutionData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReadyEvent".
 */
export interface ReadyEvent {
  schemaVersion: Schemaversion4;
  analysisId: Analysisid4;
  conversationId: Conversationid4;
  seq: Seq3;
  revision: Revision7;
  at: At3;
  type: Type3;
  data: AnalysisReadyData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewEvent".
 */
export interface ReviewEvent {
  schemaVersion: Schemaversion5;
  analysisId: Analysisid5;
  conversationId: Conversationid5;
  seq: Seq4;
  revision: Revision8;
  at: At4;
  type: Type4;
  data: PendingReview;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SectionEvent".
 */
export interface SectionEvent {
  schemaVersion: Schemaversion6;
  analysisId: Analysisid6;
  conversationId: Conversationid6;
  seq: Seq5;
  revision: Revision9;
  at: At5;
  type: Type5;
  data: ReportSection;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CompletedEvent".
 */
export interface CompletedEvent {
  schemaVersion: Schemaversion7;
  analysisId: Analysisid7;
  conversationId: Conversationid7;
  seq: Seq6;
  revision: Revision10;
  at: At6;
  type: Type6;
  data: ReportCompletedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReportCompletedData".
 */
export interface ReportCompletedData {
  report: AnalysisReport;
  assistantMessageId: Assistantmessageid1;
  revision: Revision11;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FailureEvent".
 */
export interface FailureEvent {
  schemaVersion: Schemaversion8;
  analysisId: Analysisid8;
  conversationId: Conversationid8;
  seq: Seq7;
  revision: Revision12;
  at: At7;
  type: Type7;
  data: FailureData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FailureData".
 */
export interface FailureData {
  error: PublicError;
  revision: Revision13;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "PublicError".
 */
export interface PublicError {
  code: Code1;
  message: Message;
  requestId: Requestid;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "RejectedEvent".
 */
export interface RejectedEvent {
  schemaVersion: Schemaversion9;
  analysisId: Analysisid9;
  conversationId: Conversationid9;
  seq: Seq8;
  revision: Revision14;
  at: At8;
  type: Type8;
  data: RejectedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "RejectedData".
 */
export interface RejectedData {
  comment: Comment;
  revision: Revision15;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SupplementedEvent".
 */
export interface SupplementedEvent {
  schemaVersion: Schemaversion10;
  analysisId: Analysisid10;
  conversationId: Conversationid10;
  seq: Seq9;
  revision: Revision16;
  at: At9;
  type: Type9;
  data: SupplementedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SupplementedData".
 */
export interface SupplementedData {
  supplement: EvidenceSupplement;
  revision: Revision17;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CitationBlock".
 */
export interface CitationBlock {
  chunkId: Chunkid1;
  page: Page2;
  ordinal: Ordinal1;
  content: Content3;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CitationContext".
 */
export interface CitationContext {
  citation: Citation;
  previous: CitationBlock | null;
  next: CitationBlock | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CommandAccepted".
 */
export interface CommandAccepted {
  accepted: Accepted;
  taskId: Taskid;
  revision: Revision18;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Conversation".
 */
export interface Conversation {
  id: Id1;
  caseId: Caseid3;
  title: Title4;
  createdAt: Createdat;
  updatedAt: Updatedat;
  activeAnalysisId: Activeanalysisid;
  messages: Messages;
  analysisIds: Analysisids;
  context: AnalysisContext | null;
  nextBefore: Nextbefore;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Message".
 */
export interface Message1 {
  id: Id2;
  role: Role;
  content: Content4;
  analysisId: Analysisid11;
  createdAt: Createdat1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ConversationSummary".
 */
export interface ConversationSummary {
  id: Id3;
  caseId: Caseid4;
  title: Title5;
  createdAt: Createdat2;
  updatedAt: Updatedat1;
  activeAnalysisId: Activeanalysisid1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CreateAnalysis".
 */
export interface CreateAnalysis {
  conversationId: Conversationid11;
  kind: Kind2;
  question?: Question1;
  expectedInputVersion?: Expectedinputversion;
  predecessorAnalysisId?: Predecessoranalysisid1;
  supplementIds?: Supplementids;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CreateConversation".
 */
export interface CreateConversation {
  title?: Title6;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "RecoverRequest".
 */
export interface RecoverRequest {
  expectedRevision: Expectedrevision;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewAccident".
 */
export interface ReviewAccident {
  accidentId: Accidentid;
  occurredAt: Occurredat;
  location: Location;
  description: Description;
  liabilityDescription: Liabilitydescription;
  sources: Sources;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewEvidenceSource".
 */
export interface ReviewEvidenceSource {
  evidenceId: Evidenceid;
  sourceType: Sourcetype1;
  title: Title7;
  documentId?: Documentid2;
  documentVersion?: Documentversion;
  page?: Page3;
  recordPointer?: Recordpointer;
  quote?: Quote;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewApplicablePolicy".
 */
export interface ReviewApplicablePolicy {
  policyId: Policyid;
  policyType: Policytype;
  availability: Availability;
  coverageCodes: Coveragecodes;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewCaseDetail".
 */
export interface ReviewCaseDetail {
  id: Id4;
  revision: Revision19;
  isSynthetic: Issynthetic;
  preparedAt: Preparedat1;
  latestReviewStatus?: Latestreviewstatus;
  scope: ReviewScope;
  accident: ReviewAccident;
  injury: ReviewInjury;
  parties: Parties;
  vehicles: Vehicles;
  claims: Claims;
  policies: Policies;
  losses: Losses;
  processingRecords: Processingrecords;
  timeline: Timeline1;
  documents: Documents;
  dataGaps: Datagaps;
  originalApprovedAmount: ReviewMoney;
  effectivePaidAmount: ReviewMoney;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewScope".
 */
export interface ReviewScope {
  lossTypes: Losstypes;
  scopeLimitations: Scopelimitations;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewInjury".
 */
export interface ReviewInjury {
  declaredStatus: Declaredstatus;
  injuredPersonIds: Injuredpersonids;
  sources: Sources1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewParty".
 */
export interface ReviewParty {
  partyId: Partyid;
  displayName: Displayname;
  kind: Kind3;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewVehicleDetail".
 */
export interface ReviewVehicleDetail {
  vehicleId: Vehicleid;
  role: Role1;
  plateNumber: Platenumber;
  ownerName?: Ownername;
  driverName?: Drivername;
  usage?: Usage;
  powerType?: Powertype;
  sources: Sources2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewClaimDetail".
 */
export interface ReviewClaimDetail {
  claimId: Claimid;
  claimNumber: Claimnumber;
  reportNumber: Reportnumber;
  scopeRole: Scoperole;
  closureType: Closuretype;
  closedAt: Closedat;
  originalPaymentStatus: Originalpaymentstatus;
  handlingOrganization: Handlingorganization;
  originalConclusion: Originalconclusion;
  sources: Sources3;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewPolicy".
 */
export interface ReviewPolicy {
  policyId: Policyid1;
  policyNumber?: Policynumber;
  availability: Availability1;
  policyType: Policytype1;
  vehicleId?: Vehicleid1;
  effectiveFrom?: Effectivefrom;
  effectiveTo?: Effectiveto;
  coverages: Coverages;
  sources: Sources5;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewCoverage".
 */
export interface ReviewCoverage {
  coverageId: Coverageid;
  coverageCode: Coveragecode;
  status: Status5;
  insuranceAmount: ReviewMoney;
  perAccidentLimit: ReviewMoney;
  deductibleAmount: ReviewMoney;
  deductibleBasisPoints?: Deductiblebasispoints;
  specialConditions?: Specialconditions;
  terms: Terms;
  sources: Sources4;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewMoney".
 */
export interface ReviewMoney {
  status: Status6;
  amountFen: Amountfen;
  currency?: Currency;
  reason?: Reason2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewTermRef".
 */
export interface ReviewTermRef {
  documentId: Documentid3;
  version: Version2;
  sectionIds: Sectionids1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewLoss".
 */
export interface ReviewLoss {
  lossId: Lossid;
  claimId: Claimid1;
  vehicleId?: Vehicleid2;
  personPartyId?: Personpartyid;
  lossType: Losstype;
  description: Description1;
  claimedAmount: ReviewMoney;
  assessedAmount: ReviewMoney;
  agreedAmount: ReviewMoney;
  sources: Sources6;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewProcessingRecord".
 */
export interface ReviewProcessingRecord {
  recordId: Recordid;
  recordType: Recordtype;
  claimId: Claimid2;
  title: Title8;
  status: Status7;
  occurredAt?: Occurredat1;
  amount?: ReviewMoney | null;
  detail?: Detail1;
  sources: Sources7;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewTimelineEntry".
 */
export interface ReviewTimelineEntry {
  entryId: Entryid;
  eventType: Eventtype;
  occurredAt: Occurredat2;
  title: Title9;
  detail?: Detail2;
  sources: Sources8;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewDocument".
 */
export interface ReviewDocument {
  documentId: Documentid4;
  title: Title10;
  materialType: Materialtype1;
  status: Status8;
  version: Version3;
  pageCount?: Pagecount;
  claimIds: Claimids;
  entityIds: Entityids2;
  issuedAt?: Issuedat;
  receivedAt?: Receivedat;
  sourceDescription: Sourcedescription;
  contentUrl?: Contenturl;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewDataGap".
 */
export interface ReviewDataGap {
  gapId: Gapid;
  kind: Kind4;
  entityIds: Entityids3;
  fieldPaths: Fieldpaths;
  description: Description2;
  sources: Sources9;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewCaseListItem".
 */
export interface ReviewCaseListItem {
  id: Id5;
  revision: Revision20;
  targetClaims: Targetclaims;
  relatedClaims: Relatedclaims;
  vehicles: Vehicles1;
  accidentAt: Accidentat;
  originalApprovedAmount: ReviewMoney;
  effectivePaidAmount: ReviewMoney;
  injuryStatus: Injurystatus;
  latestReviewStatus?: Latestreviewstatus1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewClaimSummary".
 */
export interface ReviewClaimSummary {
  claimId: Claimid3;
  claimNumber: Claimnumber1;
  reportNumber: Reportnumber1;
  scopeRole: Scoperole1;
  closureType: Closuretype1;
  closedAt: Closedat1;
  originalPaymentStatus: Originalpaymentstatus1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewVehicleSummary".
 */
export interface ReviewVehicleSummary {
  vehicleId: Vehicleid3;
  role: Role2;
  plateNumber: Platenumber1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewCaseListResponse".
 */
export interface ReviewCaseListResponse {
  dataStatus: Datastatus;
  items: Items;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewObjectSummary".
 */
export interface ReviewObjectSummary {
  targetClaimIds: Targetclaimids;
  relatedClaimIds: Relatedclaimids;
  vehicleIds: Vehicleids;
  lossIds: Lossids;
  scopeLimitations: Scopelimitations1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewPreflight".
 */
export interface ReviewPreflight {
  caseId: Caseid5;
  expectedInputVersion: Expectedinputversion1;
  status: Status9;
  reviewObjects: ReviewObjectSummary;
  applicablePolicies: Applicablepolicies;
  scopeItems: Scopeitems1;
  knowledgeBindings: Knowledgebindings2;
  materialSummary: Materialsummary;
  injuryStatus: Injurystatus1;
  injuredPersonIds: Injuredpersonids1;
  blockingReasons: Blockingreasons;
}
export interface Materialsummary {
  [k: string]: number;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewRequest".
 */
export interface ReviewRequest {
  decision: Decision1;
  comment?: Comment1;
  interruptKey: Interruptkey2;
  expectedRevision: Expectedrevision1;
  supplementIds?: Supplementids1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeAttempt".
 */
export interface V1KnowledgeAttempt {
  attempt: Attempt1;
  status: Status10;
  startedAt: Startedat;
  finishedAt?: Finishedat;
  error?: V1KnowledgeError | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeError".
 */
export interface V1KnowledgeError {
  code: Code2;
  message: Message2;
  reasonCode?: Reasoncode;
  providerCode?: Providercode;
  httpStatus?: Httpstatus;
  requestId?: Requestid1;
  retryAfter?: Retryafter;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeGeneration".
 */
export interface V1KnowledgeGeneration {
  generationId: Generationid2;
  documentId: Documentid5;
  productCode: Productcode2;
  clauseVersion: Clauseversion2;
  fileName: Filename1;
  sha256: Sha2561;
  status: Status11;
  revision: Revision21;
  attempt: Attempt2;
  pageCount: Pagecount1;
  chunkCount: Chunkcount;
  embeddedCount: Embeddedcount;
  isActive: Isactive;
  error?: V1KnowledgeError | null;
  createdAt: Createdat3;
  updatedAt: Updatedat2;
  attempts: Attempts;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeRetry".
 */
export interface V1KnowledgeRetry {
  expectedRevision: Expectedrevision2;
}

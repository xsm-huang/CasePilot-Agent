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
export type Comment = string;
export type Operatorid = string;
export type Nodekey = string;
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
export type Checkid = string;
export type Nodekey1 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Status1 = "passed" | "issue" | "limited" | "not_applicable" | "out_of_scope";
export type Source = "rule" | "ai" | "human";
export type Sources = ("rule" | "ai" | "human")[];
export type Title = string;
export type Detail = string;
export type Factrefs = string[];
export type Citationrefs = string[];
export type Entityids = string[];
export type Policyids = string[];
export type Coverageids = string[];
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "JsonValue".
 */
export type JsonValue = unknown;
export type Uncertainty = string;
export type Recommendation = string;
export type Statements = {
  [k: string]: JsonValue;
}[];
export type Checks = ReviewCheck[];
export type Factid = string;
export type Fieldpath = string;
export type Sourcetype = "case" | "material" | "business";
export type Materialid = string | null;
export type Facts = Fact[];
export type Code = string;
export type Source1 = "rule";
export type Severity = "low" | "medium" | "high";
export type Title1 = string;
export type Detail1 = string;
export type Factrefs1 = string[];
export type Factid1 = string;
export type Sourcevalues = SourceValue[];
export type Rulefindings = RuleFinding[];
export type Relatedcheckid = string | null;
export type Issuecode = string;
export type Supportquote = string;
export type Category = "issue" | "limitation" | "out_of_scope" | "passed";
export type Nodekey2 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Title2 = string;
export type Inference = string;
export type Evidencestatus = "supported" | "insufficient";
/**
 * @maxItems 30
 */
export type Factrefs2 = string[];
/**
 * @maxItems 12
 */
export type Citationrefs1 =
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
export type Kind = "pending_review" | "stage" | "final";
export type Version1 = number;
export type Analysisid1 = string;
export type Inputversion1 = string;
export type Generatedat = string;
export type Operatorid1 = string | null;
export type Conclusion = string;
export type Caseid = string;
export type Sectionkey = "summary" | "coverage" | "findings" | "limitations" | "reviews" | "recommendations";
export type Content1 = string;
export type Factrefs3 = string[];
export type Citationrefs2 = string[];
export type Committedat = string;
export type Sections = ReportSection[];
export type Insufficientevidence1 = boolean;
export type Reviewercomment = string | null;
export type Basishash = string;
export type Revisionreason = string;
export type Replacesversion = number | null;
export type Reviewmodelversion = 1;
export type Checkid1 = string;
export type Nodekey3 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Title3 = string;
export type Required = boolean;
export type Entityids1 = string[];
export type Checkplan = CheckPlanItem[];
export type Checks1 = ReviewCheck[];
export type Checkid2 = string;
export type Nodekey4 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Status2 = "passed" | "issue" | "limited" | "not_applicable" | "out_of_scope";
export type Source2 = "rule" | "ai" | "human";
export type Sources1 = ("rule" | "ai" | "human")[];
export type Title4 = string;
export type Detail2 = string;
export type Factrefs4 = string[];
export type Citationrefs3 = string[];
export type Entityids2 = string[];
export type Policyids1 = string[];
export type Coverageids1 = string[];
export type Uncertainty1 = string;
export type Recommendation1 = string;
export type Statements1 = {
  [k: string]: JsonValue;
}[];
export type Findingid = string;
export type Version2 = number;
export type Kind1 = "issue" | "limitation" | "out_of_scope";
export type Active = boolean;
export type Findings = Finding[];
export type Findinghistory = Finding[];
export type Recordid = string;
export type Kind2 =
  | "evidence_view"
  | "human_completion"
  | "scope_adjustment"
  | "professional"
  | "followup"
  | "business_record"
  | "reopen";
export type Nodekey5 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Targetid = string;
export type Comment1 = string;
export type Operatorid2 = string;
export type At1 = string;
export type Factrefs5 = string[];
export type Citationrefs4 = string[];
export type Supplementids = string[];
export type Checkids = string[];
export type Steps = string;
export type Result = string;
export type Recipient = string;
export type State = string;
export type Source3 = string;
export type Previousrecordid = string;
export type Inputsfen = number[];
export type Operation = ("sum" | "difference") | null;
export type Resultfen = number | null;
export type Records = ReviewRecord[];
export type Noderunid = string;
export type Nodekey6 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Attempt = number;
export type Status3 = "not_started" | "running" | "completed" | "failed" | "unable" | "not_applicable";
export type Startedat = string | null;
export type Endedat = string | null;
export type Durationms = number;
export type Summary = string;
export type Reason = string;
export type Businessnodes = BusinessNode[];
export type Nodehistory = BusinessNode[];
export type Reviewcycleid = number;
export type Allowed = boolean;
export type Blockers = string[];
export type Basishash1 = string;
export type Reviewstatus = "pending_review" | "reviewing" | "pending_verification" | "completed";
export type Id = string;
export type Revision2 = number;
export type Claimid = string;
export type Claimnumber = string;
export type Reportnumber = string;
export type Scoperole = "target" | "related";
export type Closuretype = string;
export type Closedat = string;
export type Originalpaymentstatus = string;
export type Targetclaims = ReviewClaimSummary[];
export type Relatedclaims = ReviewClaimSummary[];
export type Vehicleid = string;
export type Role = string;
export type Platenumber = string;
export type Vehicles = ReviewVehicleSummary[];
export type Accidentat = string;
export type Status4 = "known" | "unknown" | "not_applicable";
export type Amountfen = number | null;
export type Currency = string;
export type Reason1 = string | null;
export type Injurystatus = string;
export type Latestreviewstatus =
  | "not_started"
  | "running"
  | "pending_review"
  | "pending_verification"
  | "vehicle_review_completed"
  | "failed"
  | "awaiting_recovery";
export type Checks2 = ReviewCheck[];
export type Reviewid = string;
export type Findingid1 = string;
export type Nodekey7 = string;
export type Decision1 = "confirmed" | "excluded" | "pending" | "referred";
export type Comment2 = string;
export type Operatorid3 = string;
export type At2 = string;
export type Factrefs6 = string[];
export type Citationrefs5 = string[];
export type Supplementids1 = string[];
export type Followup = string;
export type Changereason = string;
export type Findingversion = number;
export type Previousreviewid = string;
export type Recipient1 = string;
export type Missingitems = string;
export type Evidenceviewed = boolean;
export type Reviewhistory = FindingReview[];
export type Reports = AnalysisReport[];
export type Operatorid4 = string;
export type Schemaversion1 = 2;
export type Id1 = string;
export type Caseid1 = string;
export type Conversationid1 = string;
export type Kind3 = "initial" | "followup";
export type Question = string;
export type Status5 =
  "queued" | "running" | "waiting_review" | "resuming" | "recoverable" | "completed" | "rejected" | "failed";
export type Snapshotkind = "closed_claim_review";
export type Caseid2 = string;
export type Caserevision = number;
export type Preparedat = string;
export type Scopeitemid = string;
export type Kind4 = string;
export type Title5 = string;
export type Status6 = "executable" | "limited" | "blocked";
export type Entityids3 = string[];
export type Reason2 = string | null;
export type Requiredmaterialtypes = string[];
export type Scopeitems = ReviewScopeItem[];
export type Knowledgebindings1 = ReviewKnowledgeBinding[];
export type Predecessoranalysisid = string | null;
export type Nodekey8 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Supplementid = string;
export type Version3 = number;
export type Analysisid2 = string;
export type Title6 = string;
export type Materialtype = string;
export type Entityids4 = string[];
export type Sha256 = string;
export type Addedat = string;
export type Addedby = string;
export type Page1 = number;
export type Content2 = string;
export type Pages = SupplementPage[];
export type Evidencesupplements = EvidenceSupplement[];
export type Reviewsupplementids = string[];
export type Revision3 = number;
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
export type Revision4 = number;
export type Reason3 = string;
export type Nodekey9 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Executionid = string;
export type Key = string;
export type Name = string;
export type Attempt1 = number;
export type Status7 = "running" | "completed" | "failed";
export type Summary1 = string;
export type Durationms1 = number;
export type Kind5 = "local" | "retrieval" | "model";
export type Parentnoderunid = string;
export type Tools = ExecutionData[];
export type Schemaversion2 = 2;
export type Analysisid3 = string;
export type Conversationid2 = string;
export type Seq1 = number;
export type Revision5 = number;
export type At3 = string;
export type Type1 = "analysis.status";
export type Status8 =
  "queued" | "running" | "waiting_review" | "resuming" | "recoverable" | "completed" | "rejected" | "failed";
export type Revision6 = number;
export type Schemaversion3 = 2;
export type Analysisid4 = string;
export type Conversationid3 = string;
export type Seq2 = number;
export type Revision7 = number;
export type At4 = string;
export type Type2 = "tool.started" | "tool.completed" | "tool.failed";
export type Schemaversion4 = 2;
export type Analysisid5 = string;
export type Conversationid4 = string;
export type Seq3 = number;
export type Revision8 = number;
export type At5 = string;
export type Type3 = "analysis.ready";
export type Schemaversion5 = 2;
export type Analysisid6 = string;
export type Conversationid5 = string;
export type Seq4 = number;
export type Revision9 = number;
export type At6 = string;
export type Type4 = "review.required";
export type Schemaversion6 = 2;
export type Analysisid7 = string;
export type Conversationid6 = string;
export type Seq5 = number;
export type Revision10 = number;
export type At7 = string;
export type Type5 = "report.section";
export type Schemaversion7 = 2;
export type Analysisid8 = string;
export type Conversationid7 = string;
export type Seq6 = number;
export type Revision11 = number;
export type At8 = string;
export type Type6 = "report.completed";
export type Assistantmessageid1 = string;
export type Revision12 = number;
export type Schemaversion8 = 2;
export type Analysisid9 = string;
export type Conversationid8 = string;
export type Seq7 = number;
export type Revision13 = number;
export type At9 = string;
export type Type7 = "analysis.failed" | "analysis.recoverable";
export type Code1 = string;
export type Message = string;
export type Requestid = string;
export type Revision14 = number;
export type Schemaversion9 = 2;
export type Analysisid10 = string;
export type Conversationid9 = string;
export type Seq8 = number;
export type Revision15 = number;
export type At10 = string;
export type Type8 = "analysis.rejected";
export type Comment3 = string;
export type Revision16 = number;
export type Schemaversion10 = 2;
export type Analysisid11 = string;
export type Conversationid10 = string;
export type Seq9 = number;
export type Revision17 = number;
export type At11 = string;
export type Type9 = "evidence.supplemented";
export type Revision18 = number;
export type Schemaversion11 = 2;
export type Analysisid12 = string;
export type Conversationid11 = string;
export type Seq10 = number;
export type Revision19 = number;
export type At12 = string;
export type Type10 = "finding.reviewed";
export type Revision20 = number;
export type Schemaversion12 = 2;
export type Analysisid13 = string;
export type Conversationid12 = string;
export type Seq11 = number;
export type Revision21 = number;
export type At13 = string;
export type Type11 = "report.saved";
export type Schemaversion13 = 2;
export type Analysisid14 = string;
export type Conversationid13 = string;
export type Seq12 = number;
export type Revision22 = number;
export type At14 = string;
export type Type12 =
  | "business_node.started"
  | "business_node.completed"
  | "business_node.failed"
  | "business_node.unable"
  | "business_node.not_applicable";
export type Schemaversion14 = 2;
export type Analysisid15 = string;
export type Conversationid14 = string;
export type Seq13 = number;
export type Revision23 = number;
export type At15 = string;
export type Type13 = "review.updated";
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
  | FindingReviewedEvent
  | ReportSavedEvent
  | BusinessNodeEvent
  | ReviewUpdatedEvent
)[];
export type Chunkid1 = string;
export type Page2 = number;
export type Ordinal1 = number;
export type Content3 = string;
export type Accepted = true;
export type Taskid = string;
export type Revision24 = number;
export type Id2 = string;
export type Caseid3 = string;
export type Title7 = string;
export type Createdat = string;
export type Updatedat = string;
export type Activeanalysisid = string | null;
export type Id3 = string;
export type Role1 = "user" | "assistant";
export type Content4 = string;
export type Analysisid16 = string;
export type Createdat1 = string;
export type Messages = Message1[];
export type Analysisids = string[];
export type Nextbefore = string | null;
export type Id4 = string;
export type Caseid4 = string;
export type Title8 = string;
export type Createdat2 = string;
export type Updatedat1 = string;
export type Activeanalysisid1 = string | null;
export type Conversationid15 = string;
export type Kind6 = "initial" | "followup";
export type Question1 = string | null;
export type Expectedinputversion = string | null;
export type Predecessoranalysisid1 = string | null;
export type Supplementids2 = string[];
export type Title9 = string;
export type Decision2 = "confirmed" | "excluded" | "pending" | "referred";
export type Comment4 = string;
export type Expectedrevision = number;
/**
 * @maxItems 30
 */
export type Factrefs7 = string[];
/**
 * @maxItems 12
 */
export type Citationrefs6 =
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
 * @maxItems 20
 */
export type Supplementids3 =
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
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ];
export type Followup1 = string;
export type Changereason1 = string;
export type Findingversion1 = number;
export type Previousreviewid1 = string;
export type Recipient2 = string;
export type Missingitems1 = string;
export type Evidenceviewed1 = boolean;
export type Expectedrevision1 = number;
export type Nodekey10 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Title10 = string;
export type Detail3 = string;
/**
 * @minItems 1
 * @maxItems 30
 */
export type Entityids5 = [string, ...string[]];
/**
 * @maxItems 30
 */
export type Factrefs8 = string[];
/**
 * @maxItems 12
 */
export type Citationrefs7 =
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
 * @maxItems 20
 */
export type Supplementids4 =
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
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ];
export type Recommendation2 = string;
export type Expectedrevision2 = number;
export type Accidentid = string;
export type Occurredat = string;
export type Location = string;
export type Description = string;
export type Liabilitydescription = string;
export type Evidenceid = string;
export type Sourcetype1 = "case_document" | "shared_document" | "structured_record";
export type Title11 = string;
export type Documentid2 = string | null;
export type Documentversion = string | null;
export type Page3 = number | null;
export type Recordpointer = string | null;
export type Quote = string | null;
export type Sources2 = ReviewEvidenceSource[];
export type Policyid = string;
export type Policytype = string;
export type Availability = string;
export type Coveragecodes = string[];
export type Id5 = string;
export type Revision25 = number;
export type Issynthetic = boolean;
export type Preparedat1 = string;
export type Latestreviewstatus1 =
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
export type Sources3 = ReviewEvidenceSource[];
export type Partyid = string;
export type Displayname = string;
export type Kind7 = string;
export type Parties = ReviewParty[];
export type Vehicleid1 = string;
export type Role2 = string;
export type Platenumber1 = string;
export type Ownername = string | null;
export type Drivername = string | null;
export type Usage = string | null;
export type Powertype = string | null;
export type Sources4 = ReviewEvidenceSource[];
export type Vehicles1 = ReviewVehicleDetail[];
export type Claimid1 = string;
export type Claimnumber1 = string;
export type Reportnumber1 = string;
export type Scoperole1 = "target" | "related";
export type Closuretype1 = string;
export type Closedat1 = string;
export type Originalpaymentstatus1 = string;
export type Handlingorganization = string;
export type Originalconclusion = string;
export type Sources5 = ReviewEvidenceSource[];
export type Claims = ReviewClaimDetail[];
export type Policyid1 = string;
export type Policynumber = string | null;
export type Availability1 = string;
export type Policytype1 = string;
export type Vehicleid2 = string | null;
export type Effectivefrom = string | null;
export type Effectiveto = string | null;
export type Coverageid = string;
export type Coveragecode = string;
export type Status9 = string;
export type Deductiblebasispoints = number | null;
export type Specialconditions = string | null;
export type Documentid3 = string;
export type Version4 = string;
export type Sectionids1 = string[];
export type Terms = ReviewTermRef[];
export type Sources6 = ReviewEvidenceSource[];
export type Coverages = ReviewCoverage[];
export type Sources7 = ReviewEvidenceSource[];
export type Policies = ReviewPolicy[];
export type Lossid = string;
export type Claimid2 = string;
export type Vehicleid3 = string | null;
export type Personpartyid = string | null;
export type Losstype = string;
export type Description1 = string;
export type Sources8 = ReviewEvidenceSource[];
export type Losses = ReviewLoss[];
export type Recordid1 = string;
export type Recordtype = "calculation" | "approval" | "payment";
export type Claimid3 = string;
export type Title12 = string;
export type Status10 = string;
export type Occurredat1 = string | null;
export type Detail4 = string | null;
export type Sources9 = ReviewEvidenceSource[];
export type Processingrecords = ReviewProcessingRecord[];
export type Entryid = string;
export type Eventtype = string;
export type Occurredat2 = string;
export type Title13 = string;
export type Detail5 = string | null;
export type Sources10 = ReviewEvidenceSource[];
export type Timeline1 = ReviewTimelineEntry[];
export type Documentid4 = string;
export type Title14 = string;
export type Materialtype1 = string;
export type Status11 = string;
export type Version5 = string;
export type Pagecount = number | null;
export type Claimids = string[];
export type Entityids6 = string[];
export type Issuedat = string | null;
export type Receivedat = string | null;
export type Sourcedescription = string;
export type Contenturl = string | null;
export type Documents = ReviewDocument[];
export type Gapid = string;
export type Kind8 = string;
export type Entityids7 = string[];
export type Fieldpaths = string[];
export type Description2 = string;
export type Sources11 = ReviewEvidenceSource[];
export type Datagaps = ReviewDataGap[];
export type Datastatus = "ready" | "not_imported";
export type Items = ReviewCaseListItem[];
export type Targetclaimids = string[];
export type Relatedclaimids = string[];
export type Vehicleids = string[];
export type Lossids = string[];
export type Scopelimitations1 = string[];
export type Caseid5 = string;
export type Expectedinputversion1 = string;
export type Status12 = "ready" | "partial" | "blocked";
export type Applicablepolicies = ReviewApplicablePolicy[];
export type Scopeitems1 = ReviewScopeItem[];
export type Knowledgebindings2 = ReviewKnowledgeBinding[];
export type Injurystatus1 = string;
export type Injuredpersonids1 = string[];
export type Blockingreasons = string[];
export type Expectedrevision3 = number;
export type Nodekey11 = "archive" | "coverage" | "consistency" | "clauses" | "amount" | "report";
export type Targetid1 = string;
export type Comment5 = string;
/**
 * @maxItems 30
 */
export type Factrefs9 = string[];
/**
 * @maxItems 12
 */
export type Citationrefs8 =
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
 * @maxItems 20
 */
export type Supplementids5 =
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
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string
    ];
/**
 * @maxItems 50
 */
export type Checkids1 = string[];
export type Steps1 = string;
export type Result1 = string;
export type Recipient3 = string;
export type State1 = string;
export type Source4 = string;
export type Previousrecordid1 = string;
/**
 * @maxItems 30
 */
export type Inputsfen1 = number[];
export type Operation1 = ("sum" | "difference") | null;
export type Resultfen1 = number | null;
export type Decision3 = "approve" | "reject";
export type Comment6 = string;
export type Interruptkey2 = string;
export type Expectedrevision4 = number;
export type Supplementids6 = string[];
export type Coverageconfirmed = boolean;
export type Reviewcycleid1 = number;
export type Reportversion = number;
export type Basishash2 = string;
export type Attempt2 = number;
export type Status13 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Startedat1 = string;
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
export type Status14 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Revision26 = number;
export type Attempt3 = number;
export type Pagecount1 = number;
export type Chunkcount = number;
export type Embeddedcount = number;
export type Isactive = boolean;
export type Createdat3 = string;
export type Updatedat2 = string;
export type Attempts = V1KnowledgeAttempt[];
export type Expectedrevision5 = number;
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
  | SupplementedEvent
  | FindingReviewedEvent
  | ReportSavedEvent
  | BusinessNodeEvent
  | ReviewUpdatedEvent;

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
  comment?: Comment;
  operatorId?: Operatorid;
  nodeKey?: Nodekey;
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
  checks?: Checks;
  facts: Facts;
  ruleFindings: Rulefindings;
  modelFindings: Modelfindings;
  citations: Citations;
  insufficientEvidence: Insufficientevidence;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewCheck".
 */
export interface ReviewCheck {
  checkId: Checkid;
  nodeKey: Nodekey1;
  status: Status1;
  source: Source;
  sources?: Sources;
  title: Title;
  detail: Detail;
  factRefs?: Factrefs;
  citationRefs?: Citationrefs;
  entityIds?: Entityids;
  policyIds?: Policyids;
  coverageIds?: Coverageids;
  originalValues?: Originalvalues;
  uncertainty?: Uncertainty;
  recommendation?: Recommendation;
  statements?: Statements;
}
export interface Originalvalues {
  [k: string]: JsonValue;
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
  source: Source1;
  severity: Severity;
  title: Title1;
  detail: Detail1;
  factRefs: Factrefs1;
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
  relatedCheckId?: Relatedcheckid;
  issueCode: Issuecode;
  supportQuote: Supportquote;
  category?: Category;
  nodeKey?: Nodekey2;
  title: Title2;
  inference: Inference;
  evidenceStatus: Evidencestatus;
  factRefs: Factrefs2;
  citationRefs: Citationrefs1;
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
  kind?: Kind;
  version: Version1;
  analysisId?: Analysisid1;
  inputVersion?: Inputversion1;
  generatedAt?: Generatedat;
  operatorId?: Operatorid1;
  conclusion?: Conclusion;
  caseId: Caseid;
  sections: Sections;
  insufficientEvidence: Insufficientevidence1;
  reviewerComment: Reviewercomment;
  basisHash: Basishash;
  snapshot: Snapshot;
  statistics: Statistics;
  revisionReason: Revisionreason;
  replacesVersion: Replacesversion;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReportSection".
 */
export interface ReportSection {
  sectionKey: Sectionkey;
  content: Content1;
  factRefs: Factrefs3;
  citationRefs: Citationrefs2;
  committedAt: Committedat;
}
export interface Snapshot {
  [k: string]: JsonValue;
}
export interface Statistics {
  [k: string]: number;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "AnalysisTask".
 */
export interface AnalysisTask {
  reviewState: ReviewState;
  finalizationEligibility: Eligibility;
  reviewStatus: Reviewstatus;
  caseSummary?: ReviewCaseListItem | null;
  checks?: Checks2;
  reviewHistory?: Reviewhistory;
  reports?: Reports;
  operatorId?: Operatorid4;
  schemaVersion: Schemaversion1;
  id: Id1;
  caseId: Caseid1;
  conversationId: Conversationid1;
  kind: Kind3;
  question: Question;
  status: Status5;
  caseSnapshot: ClosedClaimReviewSnapshot;
  predecessorAnalysisId: Predecessoranalysisid;
  evidenceSupplements: Evidencesupplements;
  reviewSupplementIds: Reviewsupplementids;
  revision: Revision3;
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
 * via the `definition` "ReviewState".
 */
export interface ReviewState {
  reviewModelVersion: Reviewmodelversion;
  checkPlan: Checkplan;
  checks: Checks1;
  findings: Findings;
  findingHistory: Findinghistory;
  records: Records;
  businessNodes: Businessnodes;
  nodeHistory: Nodehistory;
  reviewCycleId: Reviewcycleid;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CheckPlanItem".
 */
export interface CheckPlanItem {
  checkId: Checkid1;
  nodeKey: Nodekey3;
  title: Title3;
  required: Required;
  entityIds: Entityids1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Finding".
 */
export interface Finding {
  checkId: Checkid2;
  nodeKey: Nodekey4;
  status: Status2;
  source: Source2;
  sources?: Sources1;
  title: Title4;
  detail: Detail2;
  factRefs?: Factrefs4;
  citationRefs?: Citationrefs3;
  entityIds?: Entityids2;
  policyIds?: Policyids1;
  coverageIds?: Coverageids1;
  originalValues?: Originalvalues1;
  uncertainty?: Uncertainty1;
  recommendation?: Recommendation1;
  statements?: Statements1;
  findingId: Findingid;
  version: Version2;
  kind: Kind1;
  active?: Active;
}
export interface Originalvalues1 {
  [k: string]: JsonValue;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewRecord".
 */
export interface ReviewRecord {
  recordId: Recordid;
  kind: Kind2;
  nodeKey: Nodekey5;
  targetId: Targetid;
  comment: Comment1;
  operatorId: Operatorid2;
  at: At1;
  factRefs: Factrefs5;
  citationRefs: Citationrefs4;
  supplementIds: Supplementids;
  checkIds: Checkids;
  steps: Steps;
  result: Result;
  recipient: Recipient;
  state: State;
  source: Source3;
  previousRecordId: Previousrecordid;
  inputsFen: Inputsfen;
  operation: Operation;
  resultFen: Resultfen;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "BusinessNode".
 */
export interface BusinessNode {
  nodeRunId: Noderunid;
  nodeKey: Nodekey6;
  attempt: Attempt;
  status: Status3;
  startedAt: Startedat;
  endedAt: Endedat;
  durationMs: Durationms;
  summary: Summary;
  reason: Reason;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Eligibility".
 */
export interface Eligibility {
  allowed: Allowed;
  blockers: Blockers;
  basisHash: Basishash1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewCaseListItem".
 */
export interface ReviewCaseListItem {
  id: Id;
  revision: Revision2;
  targetClaims: Targetclaims;
  relatedClaims: Relatedclaims;
  vehicles: Vehicles;
  accidentAt: Accidentat;
  originalApprovedAmount: ReviewMoney;
  effectivePaidAmount: ReviewMoney;
  injuryStatus: Injurystatus;
  latestReviewStatus?: Latestreviewstatus;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewClaimSummary".
 */
export interface ReviewClaimSummary {
  claimId: Claimid;
  claimNumber: Claimnumber;
  reportNumber: Reportnumber;
  scopeRole: Scoperole;
  closureType: Closuretype;
  closedAt: Closedat;
  originalPaymentStatus: Originalpaymentstatus;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewVehicleSummary".
 */
export interface ReviewVehicleSummary {
  vehicleId: Vehicleid;
  role: Role;
  plateNumber: Platenumber;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewMoney".
 */
export interface ReviewMoney {
  status: Status4;
  amountFen: Amountfen;
  currency?: Currency;
  reason?: Reason1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FindingReview".
 */
export interface FindingReview {
  reviewId: Reviewid;
  findingId: Findingid1;
  nodeKey: Nodekey7;
  decision: Decision1;
  comment: Comment2;
  operatorId: Operatorid3;
  at: At2;
  factRefs: Factrefs6;
  citationRefs: Citationrefs5;
  supplementIds: Supplementids1;
  followup: Followup;
  changeReason: Changereason;
  findingVersion: Findingversion;
  previousReviewId: Previousreviewid;
  recipient: Recipient1;
  missingItems: Missingitems;
  evidenceViewed: Evidenceviewed;
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
  kind: Kind4;
  title: Title5;
  status: Status6;
  entityIds: Entityids3;
  reason?: Reason2;
  requiredMaterialTypes: Requiredmaterialtypes;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "EvidenceSupplement".
 */
export interface EvidenceSupplement {
  nodeKey?: Nodekey8;
  supplementId: Supplementid;
  version: Version3;
  analysisId: Analysisid2;
  title: Title6;
  materialType: Materialtype;
  entityIds: Entityids4;
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
  revision: Revision4;
  reason: Reason3;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Execution".
 */
export interface Execution {
  tools: Tools;
  timeline: Timeline;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ExecutionData".
 */
export interface ExecutionData {
  nodeKey?: Nodekey9;
  executionId: Executionid;
  key: Key;
  name: Name;
  attempt: Attempt1;
  status: Status7;
  summary: Summary1;
  durationMs: Durationms1;
  kind: Kind5;
  parentNodeRunId: Parentnoderunid;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "StatusEvent".
 */
export interface StatusEvent {
  schemaVersion: Schemaversion2;
  analysisId: Analysisid3;
  conversationId: Conversationid2;
  seq: Seq1;
  revision: Revision5;
  at: At3;
  type: Type1;
  data: StatusData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "StatusData".
 */
export interface StatusData {
  status: Status8;
  revision: Revision6;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ExecutionEvent".
 */
export interface ExecutionEvent {
  schemaVersion: Schemaversion3;
  analysisId: Analysisid4;
  conversationId: Conversationid3;
  seq: Seq2;
  revision: Revision7;
  at: At4;
  type: Type2;
  data: ExecutionData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReadyEvent".
 */
export interface ReadyEvent {
  schemaVersion: Schemaversion4;
  analysisId: Analysisid5;
  conversationId: Conversationid4;
  seq: Seq3;
  revision: Revision8;
  at: At5;
  type: Type3;
  data: AnalysisReadyData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewEvent".
 */
export interface ReviewEvent {
  schemaVersion: Schemaversion5;
  analysisId: Analysisid6;
  conversationId: Conversationid5;
  seq: Seq4;
  revision: Revision9;
  at: At6;
  type: Type4;
  data: PendingReview;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SectionEvent".
 */
export interface SectionEvent {
  schemaVersion: Schemaversion6;
  analysisId: Analysisid7;
  conversationId: Conversationid6;
  seq: Seq5;
  revision: Revision10;
  at: At7;
  type: Type5;
  data: ReportSection;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CompletedEvent".
 */
export interface CompletedEvent {
  schemaVersion: Schemaversion7;
  analysisId: Analysisid8;
  conversationId: Conversationid7;
  seq: Seq6;
  revision: Revision11;
  at: At8;
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
  revision: Revision12;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FailureEvent".
 */
export interface FailureEvent {
  schemaVersion: Schemaversion8;
  analysisId: Analysisid9;
  conversationId: Conversationid8;
  seq: Seq7;
  revision: Revision13;
  at: At9;
  type: Type7;
  data: FailureData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FailureData".
 */
export interface FailureData {
  error: PublicError;
  revision: Revision14;
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
  analysisId: Analysisid10;
  conversationId: Conversationid9;
  seq: Seq8;
  revision: Revision15;
  at: At10;
  type: Type8;
  data: RejectedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "RejectedData".
 */
export interface RejectedData {
  comment: Comment3;
  revision: Revision16;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SupplementedEvent".
 */
export interface SupplementedEvent {
  schemaVersion: Schemaversion10;
  analysisId: Analysisid11;
  conversationId: Conversationid10;
  seq: Seq9;
  revision: Revision17;
  at: At11;
  type: Type9;
  data: SupplementedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SupplementedData".
 */
export interface SupplementedData {
  supplement: EvidenceSupplement;
  revision: Revision18;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FindingReviewedEvent".
 */
export interface FindingReviewedEvent {
  schemaVersion: Schemaversion11;
  analysisId: Analysisid12;
  conversationId: Conversationid11;
  seq: Seq10;
  revision: Revision19;
  at: At12;
  type: Type10;
  data: FindingReviewedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FindingReviewedData".
 */
export interface FindingReviewedData {
  review: FindingReview;
  report: AnalysisReport;
  revision: Revision20;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReportSavedEvent".
 */
export interface ReportSavedEvent {
  schemaVersion: Schemaversion12;
  analysisId: Analysisid13;
  conversationId: Conversationid12;
  seq: Seq11;
  revision: Revision21;
  at: At13;
  type: Type11;
  data: AnalysisReport;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "BusinessNodeEvent".
 */
export interface BusinessNodeEvent {
  schemaVersion: Schemaversion13;
  analysisId: Analysisid14;
  conversationId: Conversationid13;
  seq: Seq12;
  revision: Revision22;
  at: At14;
  type: Type12;
  data: BusinessNode;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewUpdatedEvent".
 */
export interface ReviewUpdatedEvent {
  schemaVersion: Schemaversion14;
  analysisId: Analysisid15;
  conversationId: Conversationid14;
  seq: Seq13;
  revision: Revision23;
  at: At15;
  type: Type13;
  data: ReviewState;
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
  revision: Revision24;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Conversation".
 */
export interface Conversation {
  id: Id2;
  caseId: Caseid3;
  title: Title7;
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
  id: Id3;
  role: Role1;
  content: Content4;
  analysisId: Analysisid16;
  createdAt: Createdat1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ConversationSummary".
 */
export interface ConversationSummary {
  id: Id4;
  caseId: Caseid4;
  title: Title8;
  createdAt: Createdat2;
  updatedAt: Updatedat1;
  activeAnalysisId: Activeanalysisid1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CreateAnalysis".
 */
export interface CreateAnalysis {
  conversationId: Conversationid15;
  kind: Kind6;
  question?: Question1;
  expectedInputVersion?: Expectedinputversion;
  predecessorAnalysisId?: Predecessoranalysisid1;
  supplementIds?: Supplementids2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CreateConversation".
 */
export interface CreateConversation {
  title?: Title9;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FindingReviewRequest".
 */
export interface FindingReviewRequest {
  decision: Decision2;
  comment: Comment4;
  expectedRevision: Expectedrevision;
  factRefs?: Factrefs7;
  citationRefs?: Citationrefs6;
  supplementIds?: Supplementids3;
  followup?: Followup1;
  changeReason?: Changereason1;
  findingVersion: Findingversion1;
  previousReviewId?: Previousreviewid1;
  recipient?: Recipient2;
  missingItems?: Missingitems1;
  evidenceViewed?: Evidenceviewed1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ManualFindingRequest".
 */
export interface ManualFindingRequest {
  expectedRevision: Expectedrevision1;
  nodeKey: Nodekey10;
  title: Title10;
  detail: Detail3;
  entityIds: Entityids5;
  factRefs?: Factrefs8;
  citationRefs?: Citationrefs7;
  supplementIds?: Supplementids4;
  originalValues?: Originalvalues2;
  recommendation: Recommendation2;
}
export interface Originalvalues2 {
  [k: string]: JsonValue;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "RecoverRequest".
 */
export interface RecoverRequest {
  expectedRevision: Expectedrevision2;
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
  sources: Sources2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewEvidenceSource".
 */
export interface ReviewEvidenceSource {
  evidenceId: Evidenceid;
  sourceType: Sourcetype1;
  title: Title11;
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
  id: Id5;
  revision: Revision25;
  isSynthetic: Issynthetic;
  preparedAt: Preparedat1;
  latestReviewStatus?: Latestreviewstatus1;
  scope: ReviewScope;
  accident: ReviewAccident;
  injury: ReviewInjury;
  parties: Parties;
  vehicles: Vehicles1;
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
  sources: Sources3;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewParty".
 */
export interface ReviewParty {
  partyId: Partyid;
  displayName: Displayname;
  kind: Kind7;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewVehicleDetail".
 */
export interface ReviewVehicleDetail {
  vehicleId: Vehicleid1;
  role: Role2;
  plateNumber: Platenumber1;
  ownerName?: Ownername;
  driverName?: Drivername;
  usage?: Usage;
  powerType?: Powertype;
  sources: Sources4;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewClaimDetail".
 */
export interface ReviewClaimDetail {
  claimId: Claimid1;
  claimNumber: Claimnumber1;
  reportNumber: Reportnumber1;
  scopeRole: Scoperole1;
  closureType: Closuretype1;
  closedAt: Closedat1;
  originalPaymentStatus: Originalpaymentstatus1;
  handlingOrganization: Handlingorganization;
  originalConclusion: Originalconclusion;
  sources: Sources5;
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
  vehicleId?: Vehicleid2;
  effectiveFrom?: Effectivefrom;
  effectiveTo?: Effectiveto;
  coverages: Coverages;
  sources: Sources7;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewCoverage".
 */
export interface ReviewCoverage {
  coverageId: Coverageid;
  coverageCode: Coveragecode;
  status: Status9;
  insuranceAmount: ReviewMoney;
  perAccidentLimit: ReviewMoney;
  deductibleAmount: ReviewMoney;
  deductibleBasisPoints?: Deductiblebasispoints;
  specialConditions?: Specialconditions;
  terms: Terms;
  sources: Sources6;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewTermRef".
 */
export interface ReviewTermRef {
  documentId: Documentid3;
  version: Version4;
  sectionIds: Sectionids1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewLoss".
 */
export interface ReviewLoss {
  lossId: Lossid;
  claimId: Claimid2;
  vehicleId?: Vehicleid3;
  personPartyId?: Personpartyid;
  lossType: Losstype;
  description: Description1;
  claimedAmount: ReviewMoney;
  assessedAmount: ReviewMoney;
  agreedAmount: ReviewMoney;
  sources: Sources8;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewProcessingRecord".
 */
export interface ReviewProcessingRecord {
  recordId: Recordid1;
  recordType: Recordtype;
  claimId: Claimid3;
  title: Title12;
  status: Status10;
  occurredAt?: Occurredat1;
  amount?: ReviewMoney | null;
  detail?: Detail4;
  sources: Sources9;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewTimelineEntry".
 */
export interface ReviewTimelineEntry {
  entryId: Entryid;
  eventType: Eventtype;
  occurredAt: Occurredat2;
  title: Title13;
  detail?: Detail5;
  sources: Sources10;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewDocument".
 */
export interface ReviewDocument {
  documentId: Documentid4;
  title: Title14;
  materialType: Materialtype1;
  status: Status11;
  version: Version5;
  pageCount?: Pagecount;
  claimIds: Claimids;
  entityIds: Entityids6;
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
  kind: Kind8;
  entityIds: Entityids7;
  fieldPaths: Fieldpaths;
  description: Description2;
  sources: Sources11;
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
  status: Status12;
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
 * via the `definition` "ReviewRecordRequest".
 */
export interface ReviewRecordRequest {
  expectedRevision: Expectedrevision3;
  nodeKey: Nodekey11;
  targetId?: Targetid1;
  comment: Comment5;
  factRefs?: Factrefs9;
  citationRefs?: Citationrefs8;
  supplementIds?: Supplementids5;
  checkIds?: Checkids1;
  steps?: Steps1;
  result?: Result1;
  recipient?: Recipient3;
  state?: State1;
  source?: Source4;
  previousRecordId?: Previousrecordid1;
  inputsFen?: Inputsfen1;
  operation?: Operation1;
  resultFen?: Resultfen1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewRequest".
 */
export interface ReviewRequest {
  decision: Decision3;
  comment?: Comment6;
  interruptKey: Interruptkey2;
  expectedRevision: Expectedrevision4;
  supplementIds?: Supplementids6;
  coverageConfirmed?: Coverageconfirmed;
  reviewCycleId: Reviewcycleid1;
  reportVersion: Reportversion;
  basisHash: Basishash2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeAttempt".
 */
export interface V1KnowledgeAttempt {
  attempt: Attempt2;
  status: Status13;
  startedAt: Startedat1;
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
  status: Status14;
  revision: Revision26;
  attempt: Attempt3;
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
  expectedRevision: Expectedrevision5;
}

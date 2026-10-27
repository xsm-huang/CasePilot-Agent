// Generated from Python Pydantic models by pnpm --filter @casepilot/contracts generate. Do not edit.

export type Schemaversion = 1;
export type Analysisid = string;
export type Conversationid = string;
export type Seq = number;
export type Revision = number;
export type At = string;
export type Type = "review.accepted";
export type Interruptkey = string;
export type Decision = "approve" | "reject";
export type Revision1 = number;
export type Caseversion = string;
export type Generationid = string;
export type Embeddingprofile = string;
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
export type Documentid = string;
export type Filename = string;
export type Productcode = string;
export type Clauseversion = string;
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
export type Chunkid1 = string;
export type Page1 = number;
export type Ordinal1 = number;
export type Content2 = string;
export type Accepted = true;
export type Taskid = string;
export type Revision2 = number;
export type Schemaversion1 = 1;
export type Analysisid1 = string;
export type Conversationid1 = string;
export type Seq1 = number;
export type Revision3 = number;
export type At1 = string;
export type Type1 = "report.completed";
export type Assistantmessageid = string;
export type Revision4 = number;
export type Id = string;
export type Caseid1 = string;
export type Title2 = string;
export type Createdat = string;
export type Updatedat = string;
export type Activeanalysisid = string | null;
export type Id1 = string;
export type Role = "user" | "assistant";
export type Content3 = string;
export type Analysisid2 = string;
export type Createdat1 = string;
export type Messages = Message[];
export type Analysisids = string[];
export type Nextbefore = string | null;
export type Id2 = string;
export type Caseid2 = string;
export type Title3 = string;
export type Createdat2 = string;
export type Updatedat1 = string;
export type Activeanalysisid1 = string | null;
export type Conversationid2 = string;
export type Kind = "initial" | "followup";
export type Question = string | null;
export type Title4 = string;
export type Executionid = string;
export type Key = string;
export type Name = string;
export type Attempt = number;
export type Status = "running" | "completed" | "failed";
export type Summary = string;
export type Durationms = number;
export type Nodes = ExecutionData[];
export type Tools = ExecutionData[];
export type Schemaversion2 = 1;
export type Analysisid3 = string;
export type Conversationid3 = string;
export type Seq2 = number;
export type Revision5 = number;
export type At2 = string;
export type Type2 = "analysis.status";
export type Status1 =
  "queued" | "running" | "waiting_review" | "resuming" | "recoverable" | "completed" | "rejected" | "failed";
export type Revision6 = number;
export type Schemaversion3 = 1;
export type Analysisid4 = string;
export type Conversationid4 = string;
export type Seq3 = number;
export type Revision7 = number;
export type At3 = string;
export type Type3 =
  "node.started" | "node.completed" | "node.failed" | "tool.started" | "tool.completed" | "tool.failed";
export type Schemaversion4 = 1;
export type Analysisid5 = string;
export type Conversationid5 = string;
export type Seq4 = number;
export type Revision8 = number;
export type At4 = string;
export type Type4 = "analysis.ready";
export type Schemaversion5 = 1;
export type Analysisid6 = string;
export type Conversationid6 = string;
export type Seq5 = number;
export type Revision9 = number;
export type At5 = string;
export type Type5 = "review.required";
export type Interruptkey1 = string;
export type Checkpointid = string;
export type Revision10 = number;
export type Reason = string;
export type Schemaversion6 = 1;
export type Analysisid7 = string;
export type Conversationid7 = string;
export type Seq6 = number;
export type Revision11 = number;
export type At6 = string;
export type Type6 = "report.section";
export type Schemaversion7 = 1;
export type Analysisid8 = string;
export type Conversationid8 = string;
export type Seq7 = number;
export type Revision12 = number;
export type At7 = string;
export type Type7 = "analysis.failed" | "analysis.recoverable";
export type Code1 = string;
export type Message1 = string;
export type Requestid = string;
export type Revision13 = number;
export type Schemaversion8 = 1;
export type Analysisid9 = string;
export type Conversationid9 = string;
export type Seq8 = number;
export type Revision14 = number;
export type At8 = string;
export type Type8 = "analysis.rejected";
export type Comment = string;
export type Revision15 = number;
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
)[];
export type Id3 = string;
export type Caseid3 = string;
export type Status2 = "running" | "waiting_review" | "completed" | "rejected" | "failed";
export type Id4 = number;
export type Type9 = "status" | "node" | "tool" | "review_required" | "report" | "error";
export type At9 = string;
export type Title5 = string;
export type Detail1 = string | null;
export type Data =
  | V0Finding[]
  | V0ClauseCitation[]
  | V0AnalysisReport
  | {
      [k: string]: unknown;
    }
  | null;
export type Code2 = string;
export type Source1 = "rule" | "ai";
export type Severity1 = "low" | "medium" | "high";
export type Title6 = string;
export type Detail2 = string;
export type Id5 = string;
export type Title7 = string;
export type Content4 = string;
export type Score = number;
export type Caseid4 = string;
export type Summary1 = string;
export type Findings = V0Finding[];
export type Recommendation = string;
export type Citations1 = V0ClauseCitation[];
export type Reviewercomment1 = string | null;
export type Status3 = "running" | "waiting_review" | "completed" | "rejected" | "failed";
export type Events = V0TimelineEvent[];
export type Findings1 = V0Finding[];
export type Citations2 = V0ClauseCitation[];
export type Decision1 = "approve" | "reject";
export type Comment1 = string;
export type Schemaversion9 = 0;
export type Readonly = true;
export type Expectedrevision = number;
export type Decision2 = "approve" | "reject";
export type Comment2 = string;
export type Interruptkey2 = string;
export type Expectedrevision1 = number;
export type Id6 = string;
export type Caseid5 = string;
export type Status4 = "running" | "waiting_review" | "completed" | "rejected" | "failed";
export type Events1 = V0TimelineEvent[];
export type Findings2 = V0Finding[];
export type Citations3 = V0ClauseCitation[];
export type Id7 = string;
export type Claimant = string;
export type Productcode1 = string;
export type Clauseversion1 = string;
export type Policyeffectivedate = string;
export type Accidentdate = string;
export type Claimamount = number;
export type Type10 = string;
export type Name1 = string;
export type Materials = V0Material[];
export type Id8 = string;
export type Productcode2 = string;
export type Version = string;
export type Title8 = string;
export type Content5 = string;
export type Keywords = string[];
export type Accepted1 = true;
export type Taskid1 = string;
export type Schemaversion10 = 1;
export type Id9 = string;
export type Caseid6 = string;
export type Conversationid10 = string;
export type Kind1 = "initial" | "followup";
export type Question1 = string;
export type Status5 =
  "queued" | "running" | "waiting_review" | "resuming" | "recoverable" | "completed" | "rejected" | "failed";
export type Revision16 = number;
export type Lasteventseq = number;
export type Usermessageid = string;
export type Assistantmessageid1 = string | null;
export type Facts1 = Fact[];
export type Rulefindings1 = RuleFinding[];
export type Modelfindings1 = ModelFinding[];
export type Citations4 = Citation[];
export type Sections1 = ReportSection[];
export type Attempt1 = number;
export type Status6 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Startedat = string;
export type Finishedat = string | null;
export type Code3 = string;
export type Message2 = string;
export type Reasoncode = string | null;
export type Providercode = string | null;
export type Httpstatus = number | null;
export type Requestid1 = string | null;
export type Retryafter = number | null;
export type Generationid2 = string;
export type Documentid1 = string;
export type Productcode3 = string;
export type Clauseversion2 = string;
export type Filename1 = string;
export type Sha256 = string;
export type Status7 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Revision17 = number;
export type Attempt2 = number;
export type Pagecount = number;
export type Chunkcount = number;
export type Embeddedcount = number;
export type Isactive = boolean;
export type Createdat3 = string;
export type Updatedat2 = string;
export type Attempts = V1KnowledgeAttempt[];
export type Expectedrevision2 = number;
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "WorkbenchTask".
 */
export type WorkbenchTask = V1AnalysisTask | LegacyAnalysisTask;
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
  | RejectedEvent;

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
  caseVersion: Caseversion;
  generationId: Generationid;
  embeddingProfile: Embeddingprofile;
  messageIds: Messageids;
  modelProfile: Modelprofile;
  promptVersion: Promptversion;
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
  documentId: Documentid;
  fileName: Filename;
  productCode: Productcode;
  clauseVersion: Clauseversion;
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
 * via the `definition` "CitationBlock".
 */
export interface CitationBlock {
  chunkId: Chunkid1;
  page: Page1;
  ordinal: Ordinal1;
  content: Content2;
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
  revision: Revision2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CompletedEvent".
 */
export interface CompletedEvent {
  schemaVersion: Schemaversion1;
  analysisId: Analysisid1;
  conversationId: Conversationid1;
  seq: Seq1;
  revision: Revision3;
  at: At1;
  type: Type1;
  data: ReportCompletedData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReportCompletedData".
 */
export interface ReportCompletedData {
  report: AnalysisReport;
  assistantMessageId: Assistantmessageid;
  revision: Revision4;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "Conversation".
 */
export interface Conversation {
  id: Id;
  caseId: Caseid1;
  title: Title2;
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
export interface Message {
  id: Id1;
  role: Role;
  content: Content3;
  analysisId: Analysisid2;
  createdAt: Createdat1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ConversationSummary".
 */
export interface ConversationSummary {
  id: Id2;
  caseId: Caseid2;
  title: Title3;
  createdAt: Createdat2;
  updatedAt: Updatedat1;
  activeAnalysisId: Activeanalysisid1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CreateAnalysis".
 */
export interface CreateAnalysis {
  conversationId: Conversationid2;
  kind: Kind;
  question?: Question;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "CreateConversation".
 */
export interface CreateConversation {
  title?: Title4;
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
  status: Status;
  summary: Summary;
  durationMs: Durationms;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "StatusEvent".
 */
export interface StatusEvent {
  schemaVersion: Schemaversion2;
  analysisId: Analysisid3;
  conversationId: Conversationid3;
  seq: Seq2;
  revision: Revision5;
  at: At2;
  type: Type2;
  data: StatusData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "StatusData".
 */
export interface StatusData {
  status: Status1;
  revision: Revision6;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ExecutionEvent".
 */
export interface ExecutionEvent {
  schemaVersion: Schemaversion3;
  analysisId: Analysisid4;
  conversationId: Conversationid4;
  seq: Seq3;
  revision: Revision7;
  at: At3;
  type: Type3;
  data: ExecutionData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReadyEvent".
 */
export interface ReadyEvent {
  schemaVersion: Schemaversion4;
  analysisId: Analysisid5;
  conversationId: Conversationid5;
  seq: Seq4;
  revision: Revision8;
  at: At4;
  type: Type4;
  data: AnalysisReadyData;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "ReviewEvent".
 */
export interface ReviewEvent {
  schemaVersion: Schemaversion5;
  analysisId: Analysisid6;
  conversationId: Conversationid6;
  seq: Seq5;
  revision: Revision9;
  at: At5;
  type: Type5;
  data: PendingReview;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "PendingReview".
 */
export interface PendingReview {
  interruptKey: Interruptkey1;
  checkpointId: Checkpointid;
  revision: Revision10;
  reason: Reason;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "SectionEvent".
 */
export interface SectionEvent {
  schemaVersion: Schemaversion6;
  analysisId: Analysisid7;
  conversationId: Conversationid7;
  seq: Seq6;
  revision: Revision11;
  at: At6;
  type: Type6;
  data: ReportSection;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "FailureEvent".
 */
export interface FailureEvent {
  schemaVersion: Schemaversion7;
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
  message: Message1;
  requestId: Requestid;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "RejectedEvent".
 */
export interface RejectedEvent {
  schemaVersion: Schemaversion8;
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
 * via the `definition` "LegacyAnalysisTask".
 */
export interface LegacyAnalysisTask {
  id: Id3;
  caseId: Caseid3;
  status: Status2;
  events: Events;
  findings: Findings1;
  citations: Citations2;
  report?: V0AnalysisReport | null;
  review?: V0Review | null;
  schemaVersion: Schemaversion9;
  readOnly: Readonly;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0TimelineEvent".
 */
export interface V0TimelineEvent {
  id: Id4;
  type: Type9;
  at: At9;
  title: Title5;
  detail?: Detail1;
  data?: Data;
  status: Status3;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0Finding".
 */
export interface V0Finding {
  code: Code2;
  source: Source1;
  severity: Severity1;
  title: Title6;
  detail: Detail2;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0ClauseCitation".
 */
export interface V0ClauseCitation {
  id: Id5;
  title: Title7;
  content: Content4;
  score: Score;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0AnalysisReport".
 */
export interface V0AnalysisReport {
  caseId: Caseid4;
  summary: Summary1;
  findings: Findings;
  recommendation: Recommendation;
  citations: Citations1;
  reviewerComment?: Reviewercomment1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0Review".
 */
export interface V0Review {
  decision: Decision1;
  comment?: Comment1;
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
 * via the `definition` "ReviewRequest".
 */
export interface ReviewRequest {
  decision: Decision2;
  comment?: Comment2;
  interruptKey: Interruptkey2;
  expectedRevision: Expectedrevision1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0AnalysisTask".
 */
export interface V0AnalysisTask {
  id: Id6;
  caseId: Caseid5;
  status: Status4;
  events: Events1;
  findings: Findings2;
  citations: Citations3;
  report?: V0AnalysisReport | null;
  review?: V0Review | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0ClaimCase".
 */
export interface V0ClaimCase {
  id: Id7;
  claimant: Claimant;
  productCode: Productcode1;
  clauseVersion: Clauseversion1;
  policyEffectiveDate: Policyeffectivedate;
  accidentDate: Accidentdate;
  claimAmount: Claimamount;
  materials: Materials;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0Material".
 */
export interface V0Material {
  type: Type10;
  name: Name1;
  fields: Fields;
}
export interface Fields {
  [k: string]: string | number;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0Clause".
 */
export interface V0Clause {
  id: Id8;
  productCode: Productcode2;
  version: Version;
  title: Title8;
  content: Content5;
  keywords: Keywords;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0ReviewAccepted".
 */
export interface V0ReviewAccepted {
  accepted: Accepted1;
  taskId: Taskid1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1AnalysisTask".
 */
export interface V1AnalysisTask {
  schemaVersion: Schemaversion10;
  id: Id9;
  caseId: Caseid6;
  conversationId: Conversationid10;
  kind: Kind1;
  question: Question1;
  status: Status5;
  caseSnapshot: V0ClaimCase;
  revision: Revision16;
  lastEventSeq: Lasteventseq;
  userMessageId: Usermessageid;
  assistantMessageId: Assistantmessageid1;
  context: AnalysisContext;
  facts: Facts1;
  ruleFindings: Rulefindings1;
  modelFindings: Modelfindings1;
  citations: Citations4;
  sections: Sections1;
  report: AnalysisReport | null;
  pendingReview: PendingReview | null;
  execution: Execution;
  error: PublicError | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeAttempt".
 */
export interface V1KnowledgeAttempt {
  attempt: Attempt1;
  status: Status6;
  startedAt: Startedat;
  finishedAt?: Finishedat;
  error?: V1KnowledgeError | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeError".
 */
export interface V1KnowledgeError {
  code: Code3;
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
  documentId: Documentid1;
  productCode: Productcode3;
  clauseVersion: Clauseversion2;
  fileName: Filename1;
  sha256: Sha256;
  status: Status7;
  revision: Revision17;
  attempt: Attempt2;
  pageCount: Pagecount;
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

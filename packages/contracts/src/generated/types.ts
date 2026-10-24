// Generated from Python Pydantic models by pnpm --filter @casepilot/contracts generate. Do not edit.

export type Caseid = string;
export type Summary = string;
export type Code = string;
export type Source = "rule" | "ai";
export type Severity = "low" | "medium" | "high";
export type Title = string;
export type Detail = string;
export type Findings = V0Finding[];
export type Recommendation = string;
export type Id = string;
export type Title1 = string;
export type Content = string;
export type Score = number;
export type Citations = V0ClauseCitation[];
export type Reviewercomment = string | null;
export type Id1 = string;
export type Caseid1 = string;
export type Status = "running" | "waiting_review" | "completed" | "rejected" | "failed";
export type Id2 = number;
export type Type = "status" | "node" | "tool" | "review_required" | "report" | "error";
export type At = string;
export type Title2 = string;
export type Detail1 = string | null;
export type Data =
  | V0Finding[]
  | V0ClauseCitation[]
  | V0AnalysisReport
  | {
      [k: string]: unknown;
    }
  | null;
export type Status1 = "running" | "waiting_review" | "completed" | "rejected" | "failed";
export type Events = V0TimelineEvent[];
export type Findings1 = V0Finding[];
export type Citations1 = V0ClauseCitation[];
export type Decision = "approve" | "reject";
export type Comment = string;
export type Id3 = string;
export type Claimant = string;
export type Productcode = string;
export type Clauseversion = string;
export type Policyeffectivedate = string;
export type Accidentdate = string;
export type Claimamount = number;
export type Type1 = string;
export type Name = string;
export type Materials = V0Material[];
export type Id4 = string;
export type Productcode1 = string;
export type Version = string;
export type Title3 = string;
export type Content1 = string;
export type Keywords = string[];
export type Accepted = true;
export type Taskid = string;
export type Attempt = number;
export type Status2 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Startedat = string;
export type Finishedat = string | null;
export type Code1 = string;
export type Message = string;
export type Reasoncode = string | null;
export type Providercode = string | null;
export type Httpstatus = number | null;
export type Requestid = string | null;
export type Retryafter = number | null;
export type Generationid = string;
export type Documentid = string;
export type Productcode2 = string;
export type Clauseversion1 = string;
export type Filename = string;
export type Sha256 = string;
export type Status3 = "queued" | "parsing" | "chunking" | "embedding" | "ready" | "failed";
export type Revision = number;
export type Attempt1 = number;
export type Pagecount = number;
export type Chunkcount = number;
export type Embeddedcount = number;
export type Isactive = boolean;
export type Createdat = string;
export type Updatedat = string;
export type Attempts = V1KnowledgeAttempt[];
export type Expectedrevision = number;

export interface TransportContract {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0AnalysisReport".
 */
export interface V0AnalysisReport {
  caseId: Caseid;
  summary: Summary;
  findings: Findings;
  recommendation: Recommendation;
  citations: Citations;
  reviewerComment?: Reviewercomment;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0Finding".
 */
export interface V0Finding {
  code: Code;
  source: Source;
  severity: Severity;
  title: Title;
  detail: Detail;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0ClauseCitation".
 */
export interface V0ClauseCitation {
  id: Id;
  title: Title1;
  content: Content;
  score: Score;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0AnalysisTask".
 */
export interface V0AnalysisTask {
  id: Id1;
  caseId: Caseid1;
  status: Status;
  events: Events;
  findings: Findings1;
  citations: Citations1;
  report?: V0AnalysisReport | null;
  review?: V0Review | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0TimelineEvent".
 */
export interface V0TimelineEvent {
  id: Id2;
  type: Type;
  at: At;
  title: Title2;
  detail?: Detail1;
  data?: Data;
  status: Status1;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0Review".
 */
export interface V0Review {
  decision: Decision;
  comment?: Comment;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0ClaimCase".
 */
export interface V0ClaimCase {
  id: Id3;
  claimant: Claimant;
  productCode: Productcode;
  clauseVersion: Clauseversion;
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
  type: Type1;
  name: Name;
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
  id: Id4;
  productCode: Productcode1;
  version: Version;
  title: Title3;
  content: Content1;
  keywords: Keywords;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V0ReviewAccepted".
 */
export interface V0ReviewAccepted {
  accepted: Accepted;
  taskId: Taskid;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeAttempt".
 */
export interface V1KnowledgeAttempt {
  attempt: Attempt;
  status: Status2;
  startedAt: Startedat;
  finishedAt?: Finishedat;
  error?: V1KnowledgeError | null;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeError".
 */
export interface V1KnowledgeError {
  code: Code1;
  message: Message;
  reasonCode?: Reasoncode;
  providerCode?: Providercode;
  httpStatus?: Httpstatus;
  requestId?: Requestid;
  retryAfter?: Retryafter;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeGeneration".
 */
export interface V1KnowledgeGeneration {
  generationId: Generationid;
  documentId: Documentid;
  productCode: Productcode2;
  clauseVersion: Clauseversion1;
  fileName: Filename;
  sha256: Sha256;
  status: Status3;
  revision: Revision;
  attempt: Attempt1;
  pageCount: Pagecount;
  chunkCount: Chunkcount;
  embeddedCount: Embeddedcount;
  isActive: Isactive;
  error?: V1KnowledgeError | null;
  createdAt: Createdat;
  updatedAt: Updatedat;
  attempts: Attempts;
}
/**
 * This interface was referenced by `TransportContract`'s JSON-Schema
 * via the `definition` "V1KnowledgeRetry".
 */
export interface V1KnowledgeRetry {
  expectedRevision: Expectedrevision;
}

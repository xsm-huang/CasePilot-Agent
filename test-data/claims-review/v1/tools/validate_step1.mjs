/** Offline preparation validation. Does not run the Agent or write case fixtures. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const root = fileURLToPath(new URL('../', import.meta.url));
const workspace = path.resolve(root, '../../..');
const require = createRequire(path.join(workspace, 'packages/contracts/package.json'));
const Ajv = require('ajv/dist/2020.js');
const addFormats = require('ajv-formats');
const base = 'urn:casepilot:claims-review:v1:';
const read = relative => JSON.parse(fs.readFileSync(path.join(root, relative), 'utf8'));
const dictionary = read('shared/dictionaries.json');
const catalog = read('shared/clause-catalog.json');
const rules = read('shared/review-rules.json');
const sourceManifest = read('shared/sources.json');
const ajv = new Ajv({ allErrors: true, strict: true, strictRequired: false, allowUnionTypes: true });
addFormats(ajv);
for (const name of ['common', 'case', 'expected', 'review-steps']) ajv.addSchema(read(`schemas/${name}.schema.json`));
const validators = Object.fromEntries(['case', 'expected', 'review-steps'].map(name => [name, ajv.getSchema(base + name)]));
const docById = new Map(catalog.documents.map(item => [item.documentId, item]));
const validRuleIds = new Set([...rules.rules.map(item => item.ruleId), ...rules.requiresEvidenceAssistedReview.map(item => item.checkId)]);

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function shape(kind, value) {
  const validate = validators[kind];
  check(validate(value), `${kind} schema: ${JSON.stringify(validate.errors?.slice(0, 8))}`);
}

function unique(items, getId, label) {
  const result = new Set();
  for (const item of items) {
    const id = getId(item);
    check(!result.has(id), `duplicate ${label}: ${id}`);
    result.add(id);
  }
  return result;
}

function walk(value, fn) {
  if (!value || typeof value !== 'object') return;
  fn(value);
  for (const child of Object.values(value)) {
    if (Array.isArray(child)) child.forEach(item => walk(item, fn));
    else walk(child, fn);
  }
}

function resolvePointer(value, pointer) {
  const parts = pointer.slice(1).split('/').map(part => part.replaceAll('~1', '/').replaceAll('~0', '~'));
  let current = value;
  for (const part of parts) {
    check(current !== null && typeof current === 'object' && Object.hasOwn(current, part), `unresolved record pointer: ${pointer}`);
    current = current[part];
  }
  return current;
}

function within(directory, relative) {
  const full = path.resolve(directory, relative);
  const distance = path.relative(directory, full);
  check(distance !== '..' && !distance.startsWith(`..${path.sep}`) && !path.isAbsolute(distance), `path escapes directory: ${relative}`);
  return full;
}

function validateCase(value, { caseDirectory = null } = {}) {
  shape('case', value);
  const groups = [
    [value.parties, 'partyId'], [value.vehicles, 'vehicleId'], [value.claims, 'claimId'],
    [value.policies, 'policyId'], [value.endorsements, 'endorsementId'], [value.losses, 'lossId'],
    [value.calculations, 'calculationId'], [value.approvals, 'approvalId'], [value.payments, 'paymentId'],
    [value.documents, 'documentId'], [value.evidence, 'evidenceId'], [value.observations, 'observationId'], [value.dataGaps, 'gapId'],
    [value.policies.flatMap(item => item.coverages), 'coverageId'],
    [value.calculations.flatMap(item => item.lines), 'lineId'],
  ];
  const allIds = new Set([value.accident.accidentId]);
  for (const [items, key] of groups) {
    for (const item of items) {
      check(!allIds.has(item[key]), `duplicate entity id: ${item[key]}`);
      allIds.add(item[key]);
    }
  }
  const sets = Object.fromEntries(groups.map(([items, key]) => [key, new Set(items.map(item => item[key]))]));
  const mappings = {
    partyId: 'partyId', ownerPartyId: 'partyId', driverPartyId: 'partyId', policyholderPartyId: 'partyId', personPartyId: 'partyId', payeePartyId: 'partyId',
    vehicleId: 'vehicleId', claimId: 'claimId', policyId: 'policyId', coverageId: 'coverageId', parentCoverageId: 'coverageId',
    lossId: 'lossId', originalPaymentId: 'paymentId',
  };
  const listMappings = {
    insuredPartyIds: 'partyId', claimIds: 'claimId', targetClaimIds: 'claimId', relatedClaimIds: 'claimId',
    affectedCoverageIds: 'coverageId', calculationIds: 'calculationId', lossIds: 'lossId', evidenceRefs: 'evidenceId',
  };
  walk(value, item => {
    for (const [key, target] of Object.entries(mappings)) {
      if (item[key] !== null && item[key] !== undefined) check(sets[target].has(item[key]), `unknown ${key}: ${item[key]}`);
    }
    for (const [key, target] of Object.entries(listMappings)) {
      if (Array.isArray(item[key])) for (const id of item[key]) check(sets[target].has(id), `unknown ${key}: ${id}`);
    }
    if (Array.isArray(item.entityIds)) for (const id of item.entityIds) check(allIds.has(id), `unknown entityIds: ${id}`);
    if (typeof item.entityId === 'string') check(allIds.has(item.entityId), `unknown entityId: ${item.entityId}`);
    if (typeof item.approvalId === 'string') check(sets.approvalId.has(item.approvalId), `unknown approvalId: ${item.approvalId}`);
    if (item.documentSha256) {
      const doc = docById.get(item.documentId);
      check(doc?.eligibleForContractRetrieval, `not a contract document: ${item.documentId}`);
      check(item.documentSha256 === doc.sha256 && item.version === doc.version, `clause version/hash mismatch: ${item.documentId}`);
      const sections = new Set(doc.sections.map(section => section.sectionId));
      for (const id of item.sectionIds) check(sections.has(id), `unknown clause section: ${id}`);
    }
  });
  check(!value.reviewScope.relatedClaimIds.some(id => value.reviewScope.targetClaimIds.includes(id)), 'target and related claims overlap');
  const documents = new Map(value.documents.map(item => [item.documentId, item]));
  for (const evidence of value.evidence) {
    if (evidence.sourceType === 'structured_record') {
      check(!evidence.recordPointer.startsWith('/evidence/'), 'evidence cannot cite another evidence record as original business fact');
      resolvePointer(value, evidence.recordPointer);
    } else {
      const doc = evidence.sourceType === 'shared_document' ? docById.get(evidence.documentId) : documents.get(evidence.documentId);
      check(doc, `unknown evidence document: ${evidence.documentId}`);
      check(evidence.sourceType === 'shared_document' || ['available', 'partial'].includes(doc.status), `evidence points to unavailable document: ${evidence.documentId}`);
      check(evidence.documentVersion === doc.version, `evidence version mismatch: ${evidence.documentId}`);
      check(Number.isInteger(doc.pageCount) && evidence.page <= doc.pageCount, `evidence page outside document: ${evidence.documentId}`);
    }
  }
  const payments = new Map(value.payments.map(item => [item.paymentId, item]));
  for (const payment of value.payments) {
    const visited = new Set([payment.paymentId]);
    let previous = payment.originalPaymentId;
    while (previous !== null) {
      check(!visited.has(previous), 'cyclic payment correction reference');
      visited.add(previous);
      previous = payments.get(previous).originalPaymentId;
    }
  }
  if (caseDirectory) {
    for (const document of value.documents) {
      if (!document.relativePath) continue;
      const full = within(caseDirectory, document.relativePath);
      check(fs.existsSync(full), `missing case file: ${document.relativePath}`);
      const bytes = fs.readFileSync(full);
      check(document.sha256 === createHash('sha256').update(bytes).digest('hex'), `case file hash mismatch: ${document.documentId}`);
      if (document.status === 'available') check(bytes.subarray(0, 5).toString('ascii') === '%PDF-', `available attachment is not PDF: ${document.documentId}`);
    }
  }
  return { allIds, evidenceIds: sets.evidenceId };
}

function validateExpected(value, input = null) {
  shape('expected', value);
  const findingIds = unique(value.expectedFindings, item => item.findingKey, 'findingKey');
  const byFinding = new Map(value.expectedFindings.map(item => [item.findingKey, item]));
  const baselineFindings = value.expectedFindings.filter(item => item.source !== 'human');
  unique([value.initialCheckpoint, ...value.reviewCheckpoints], item => item.checkpointId, 'checkpointId');
  for (const item of value.expectedChecks) check(validRuleIds.has(item.ruleId), `unknown check ruleId: ${item.ruleId}`);
  for (const item of value.expectedFindings) if (item.ruleId) check(validRuleIds.has(item.ruleId), `unknown finding ruleId: ${item.ruleId}`);
  for (const checkpoint of [value.initialCheckpoint, ...value.reviewCheckpoints]) {
    const ids = unique(checkpoint.findingStates, item => item.findingKey, 'checkpoint findingKey');
    for (const finding of checkpoint.findingStates) {
      check(findingIds.has(finding.findingKey), `unknown checkpoint finding: ${finding.findingKey}`);
      check(finding.scope === byFinding.get(finding.findingKey).scope, 'checkpoint changed finding scope');
    }
    for (const finding of baselineFindings) check(ids.has(finding.findingKey), `checkpoint omitted finding: ${finding.findingKey}`);
    if (checkpoint.finalReportAllowed && value.expectedInjuryStatus !== 'no_injury_indication') check(checkpoint.requiredDisclosures.length > 0, 'final report must disclose injury/unknown scope');
  }
  for (const state of value.initialCheckpoint.findingStates) check(state.state === 'unreviewed', 'initial AI findings cannot be pre-reviewed');
  if (input) {
    check(value.datasetCaseId === input.datasetCaseId && value.caseRevision === input.caseRevision, 'oracle/input identity mismatch');
    const { allIds, evidenceIds } = validateCase(input);
    for (const finding of baselineFindings) {
      for (const id of finding.requiredEvidenceIds) check(evidenceIds.has(id), `unknown oracle evidence: ${id}`);
    }
    for (const finding of [...value.expectedFindings, ...value.forbiddenFindings]) for (const id of finding.entityIds) check(allIds.has(id), `unknown oracle entity: ${id}`);
  }
}

function validateSteps(value, expected, input, { requireSupplementFiles = false } = {}) {
  shape('review-steps', value);
  check(value.datasetCaseId === expected.datasetCaseId && value.caseRevision === expected.caseRevision, 'steps/oracle identity mismatch');
  unique(value.steps, item => item.stepId, 'stepId');
  const active = new Map(expected.initialCheckpoint.findingStates.map(item => [item.findingKey, { ...item }]));
  const evidenceIds = new Set(input.evidence.map(item => item.evidenceId));
  const inspected = new Map();
  const requests = new Map();
  let confirmedCoverage = false;
  let previousTime = -Infinity;
  for (const step of value.steps) {
    const time = Date.parse(step.at);
    check(time >= previousTime, 'review steps are not chronological');
    previousTime = time;
    if (step.expectedOutcome !== 'accepted') continue;
    const key = step.idempotencyKey;
    const signature = JSON.stringify([step.actorId, step.action, step.expectedRevision, step.payload]);
    if (requests.has(key)) {
      check(requests.get(key) === signature, 'accepted idempotency key reused with different request');
      continue;
    }
    requests.set(key, signature);
    const payload = step.payload;
    if (step.action === 'add_manual_finding') {
      check(!active.has(payload.findingKey), 'manual finding key already exists');
      active.set(payload.findingKey, { findingKey: payload.findingKey, scope: payload.scope, state: 'unreviewed' });
    } else if (payload.findingKey) check(active.has(payload.findingKey), `unknown step findingKey: ${payload.findingKey}`);
    if (step.action === 'provide_evidence') {
      if (requireSupplementFiles) check(fs.existsSync(within(root, payload.supplementPackage)), 'supplement package does not exist');
      for (const id of payload.newEvidenceIds) {
        check(!evidenceIds.has(id), 'supplement overwrites existing evidence id');
        evidenceIds.add(id);
      }
    }
    const refs = payload.evidenceRefs ?? payload.decision?.evidenceRefs ?? [];
    for (const id of refs) check(evidenceIds.has(id), `unknown step evidence: ${id}`);
    const inspectionKey = `${step.actorId}:${payload.findingKey}`;
    if (step.action === 'inspect_finding') inspected.set(inspectionKey, new Set(refs));
    if (['decide_finding', 'amend_decision'].includes(step.action)) {
      const decision = payload.decision;
      if (step.action === 'amend_decision') check(active.get(payload.findingKey).state !== 'unreviewed', 'cannot amend a finding without an existing decision');
      else check(active.get(payload.findingKey).state === 'unreviewed', 'existing decision must use amend_decision with a reason');
      if (['confirm', 'exclude'].includes(decision.action)) {
        check(inspected.has(inspectionKey), 'confirm/exclude requires prior evidence inspection by the actor');
        check(refs.every(id => inspected.get(inspectionKey).has(id)), 'decision cites evidence not inspected by actor');
      }
      active.get(payload.findingKey).state = dictionary.decisionToState[decision.action];
    }
    // Recording professional advice never itself resolves the finding.
    if (step.action === 'confirm_coverage') {
      for (const id of payload.checkIds) check(expected.expectedChecks.some(item => item.ruleId === id), `unknown inspected check: ${id}`);
      confirmedCoverage = true;
    }
    if (step.action === 'save_report' && payload.stage === 'final_vehicle') {
      check(confirmedCoverage, 'final report requires human coverage confirmation');
      check([...active.values()].every(item => item.scope === 'injury' || dictionary.finalFindingStates.includes(item.state)), 'final report has unresolved in-scope finding');
      const checkpoint = expected.reviewCheckpoints.find(item => item.afterStepId === step.stepId);
      check(checkpoint?.finalReportAllowed && checkpoint.inScopeChecksComplete, 'final report requires matching completion checkpoint');
    }
    const checkpoint = expected.reviewCheckpoints.find(item => item.afterStepId === step.stepId);
    if (checkpoint) {
      check(checkpoint.coverageConfirmedByHuman === confirmedCoverage, 'checkpoint human confirmation differs from steps');
      check(checkpoint.findingStates.length === active.size, 'checkpoint omits active findings or adds future findings');
      for (const item of checkpoint.findingStates) check(active.get(item.findingKey)?.state === item.state && active.get(item.findingKey)?.scope === item.scope, 'checkpoint differs from actual planned finding state');
    }
  }
  for (const checkpoint of expected.reviewCheckpoints) {
    if (checkpoint.afterStepId !== null) check(value.steps.some(step => step.stepId === checkpoint.afterStepId), `unknown checkpoint step: ${checkpoint.afterStepId}`);
  }
}

function verifyPreparation() {
  const common = read('schemas/common.schema.json');
  for (const [name, values] of Object.entries(dictionary.enums)) assert.deepEqual(common.$defs[name].enum, values.map(item => item.code), `dictionary/schema mismatch: ${name}`);
  unique(rules.rules, item => item.ruleId, 'ruleId');
  unique(catalog.documents, item => item.documentId, 'catalog documentId');
  const sourceById = new Map(sourceManifest.documents.map(item => [item.documentId, item]));
  const sectionIds = new Set();
  for (const document of catalog.documents) {
    const source = sourceById.get(document.documentId);
    check(source?.sha256 === document.sha256 && source.version === document.version, 'catalog/source version mismatch');
    const bytes = fs.readFileSync(within(path.join(root, 'shared'), document.localFile));
    check(createHash('sha256').update(bytes).digest('hex') === document.sha256, 'original PDF hash mismatch');
    for (const section of document.sections) {
      check(!sectionIds.has(section.sectionId), 'duplicate sectionId');
      sectionIds.add(section.sectionId);
      check(section.startPage >= 1 && section.startPage <= section.endPage && section.endPage <= document.pageCount, 'invalid section page range');
      if (section.startPage === section.endPage) check(section.startLine <= section.endLine, 'invalid same-page section range');
      for (const code of section.coverageCodes) check(dictionary.enums.coverageCode.some(item => item.code === code), 'unknown catalog coverage code');
    }
  }
  for (const rule of rules.rules) {
    check(rule.implementedInBusinessRuntime === false, 'preparation must not assert runtime delivery');
    check(dictionary.enums.nodeId.some(item => item.code === rule.nodeId), 'unknown rule node');
  }
  return { sharedDocuments: catalog.documents.length, sections: sectionIds.size, rules: rules.rules.length };
}

function internalExamples() {
  // In-memory shape/relationship tests only. Never written as C01-C16 business fixtures.
  const known = amountFen => ({ status: 'known', amountFen, currency: 'CNY', reason: null });
  const unknown = () => ({ status: 'unknown', amountFen: null, currency: 'CNY', reason: '本次资料未取得' });
  const doc = docById.get('PA-COMMERCIAL-MOTOR-2020');
  const terms = { documentId: doc.documentId, documentSha256: doc.sha256, version: doc.version, sectionIds: ['COMM-GENERAL', 'COMM-OWN', 'COMM-COMMON', 'COMM-DEFINITIONS'] };
  const input = {
    schemaVersion: 1, dictionaryVersion: '1.0.0', datasetCaseId: 'C99', caseRevision: 1, isSynthetic: true, preparedAt: '2026-10-27T10:00:00+08:00',
    reviewScope: { targetClaimIds: ['CL1'], relatedClaimIds: [], lossTypes: ['own_vehicle'], scopeLimitations: [] },
    accident: { accidentId: 'AC1', occurredAt: '2026-09-01T12:00:00+08:00', location: '格式校验地点', description: '内存校验用例', liabilityDescription: '仅用于关系校验', evidenceRefs: ['EV1'] },
    parties: [{ partyId: 'P1', displayName: '校验主体', kind: 'person', evidenceRefs: [] }],
    vehicles: [{ vehicleId: 'V1', role: 'insured', plateNumber: 'DEMO-V1', ownerPartyId: 'P1', driverPartyId: 'P1', usage: '家庭自用', powerType: 'fuel', evidenceRefs: [] }],
    claims: [{ claimId: 'CL1', reportNumber: 'DEMO-R1', claimNumber: 'DEMO-C1', handlingOrganization: 'DEMO', closureType: 'paid_closed', closedAt: '2026-09-10T12:00:00+08:00', originalConclusion: '内存校验记录', originalPaymentStatus: 'settled', evidenceRefs: ['EV1'] }],
    policies: [{ policyId: 'POL1', policyNumber: 'DEMO-POL1', availability: 'available', policyType: 'commercial', insurerCode: 'PINGAN', vehicleId: 'V1', policyholderPartyId: 'P1', insuredPartyIds: ['P1'], effectiveFrom: '2026-01-01T00:00:00+08:00', effectiveTo: '2027-01-01T00:00:00+08:00', coverages: [{ coverageId: 'CV1', coverageCode: 'OWN_DAMAGE', status: 'insured', parentCoverageId: null, insuranceAmount: known(10000000), perAccidentLimit: unknown(), deductibleAmount: known(0), deductibleBasisPoints: 0, terms: [terms], specialConditions: null, evidenceRefs: [] }], terms: [terms], evidenceRefs: [] }],
    endorsements: [], losses: [{ lossId: 'L1', claimId: 'CL1', vehicleId: 'V1', personPartyId: null, lossType: 'own_vehicle', description: '内存测试损失', claimedAmount: known(900000), assessedAmount: known(800000), agreedAmount: known(800000), evidenceRefs: [] }],
    calculations: [{ calculationId: 'CAL1', claimId: 'CL1', policyId: 'POL1', coverageId: 'CV1', status: 'final', lines: [{ lineId: 'LINE1', lossId: 'L1', description: '测试明细', operation: 'sum', inputs: [{ name: '明细', amount: known(800000) }], formulaText: null, result: known(800000), evidenceRefs: [] }], totalAmount: known(800000), adjustmentReason: '存在调整，是否合理不由格式验证判断', evidenceRefs: [] }],
    approvals: [{ approvalId: 'AP1', claimId: 'CL1', policyId: 'POL1', coverageId: 'CV1', calculationIds: ['CAL1'], lossIds: ['L1'], status: 'approved', approvedAmount: known(800000), decidedAt: '2026-09-09T12:00:00+08:00', reason: '内存格式校验', evidenceRefs: [] }],
    payments: [{ paymentId: 'PAY1', claimId: 'CL1', externalTransactionId: 'DEMO-T1', kind: 'disbursement', status: 'succeeded', amount: known(800000), occurredAt: '2026-09-10T10:00:00+08:00', payeePartyId: 'P1', originalPaymentId: null, approvalAllocations: [{ approvalId: 'AP1', amount: known(800000) }], evidenceRefs: [] }],
    documents: [], evidence: [{ evidenceId: 'EV1', sourceType: 'structured_record', documentId: null, documentVersion: null, page: null, recordPointer: '/claims/0/closureType', quote: null, provenance: 'structured_business_record' }],
    observations: [], dataGaps: [], knowledgeRefs: [terms], injury: { declaredStatus: 'no_injury_reported', evidenceRefs: ['EV1'], injuredPersons: [] },
  };
  const checkpoint = { checkpointId: 'CP0', afterStepId: null, reportStage: 'draft', finalReportAllowed: false, coverageConfirmedByHuman: false, inScopeChecksComplete: true, findingStates: [{ findingKey: 'F1', scope: 'vehicle', state: 'unreviewed' }], requiredDisclosures: [] };
  const expected = {
    schemaVersion: 1, dictionaryVersion: '1.0.0', datasetCaseId: 'C99', caseRevision: 1, isTestOracle: true, annotatedBy: '内存校验人员', annotatedAt: '2026-10-27T10:00:00+08:00', annotationStatus: 'reviewed', annotationBasis: '仅用于约束自检，非业务标准答案', expectedInjuryStatus: 'no_injury_indication',
    expectedChecks: [{ ruleId: 'PAYMENT-APPROVAL-GAP', nodeId: 'amounts', status: 'completed', reason: '结构校验' }],
    expectedFindings: [{ findingKey: 'F1', source: 'rule', ruleId: 'PAYMENT-APPROVAL-GAP', scope: 'vehicle', entityIds: ['CL1'], requiredMeaning: '内存测试逻辑键', requiredEvidenceIds: ['EV1'], prohibitedClaims: [], initialState: 'unreviewed', expectedHumanAction: 'confirm', humanRationale: '仅用于测试格式' }],
    forbiddenFindings: [], initialCheckpoint: checkpoint, reviewCheckpoints: [], reviewStepsFile: null, acceptanceIds: ['A10', 'A14'],
  };
  const decision = { action: 'confirm', comment: '已查看测试依据并确认', evidenceRefs: ['EV1'], missingItems: [], followUpOwner: null, professionalRecipient: null, professionalReason: null };
  const step = (id, action, payload) => ({ stepId: id, actorId: 'AUDITOR1', at: '2026-10-27T11:00:00+08:00', action, expectedRevision: 1, idempotencyKey: id, payload, expectedOutcome: 'accepted', note: '内存格式与前后关系自检' });
  const script = { schemaVersion: 1, datasetCaseId: 'C99', caseRevision: 1, expectedFile: 'expected/C99.json', steps: [step('S1', 'inspect_finding', { findingKey: 'F1', evidenceRefs: ['EV1'] }), step('S2', 'decide_finding', { findingKey: 'F1', decision })] };
  return { input, expected, script, step, decision, known, unknown };
}

function selfTest() {
  const fixtures = internalExamples();
  const { input, expected, script, step, decision, unknown } = fixtures;
  let passed = 0;
  function accept(label, run) { run(); passed++; }
  function reject(label, run, pattern) { assert.throws(run, pattern, label); passed++; }
  function changed(original, change) { const value = structuredClone(original); change(value); return value; }
  accept('normal typed input', () => validateCase(input));
  accept('oracle separate from input', () => validateExpected(expected, input));
  accept('inspect before decision', () => validateSteps(script, expected, input));
  accept('missing critical inputs is a supported input state', () => validateCase(changed(input, value => { value.accident.occurredAt = null; value.policies = []; value.calculations = []; value.approvals = []; value.payments = []; value.knowledgeRefs = []; value.dataGaps = [{ gapId: 'G1', kind: 'not_obtained', entityIds: ['CL1'], fieldPaths: ['policies', 'accident.occurredAt'], description: '测试资料未取得', evidenceRefs: [] }]; })));
  accept('business amount mismatch is not malformed input', () => validateCase(changed(input, value => { value.payments[0].amount.amountFen = 900000; })));
  accept('raw invalid date retained as observation', () => validateCase(changed(input, value => { value.observations.push({ observationId: 'OBS1', entityId: 'AC1', fieldPath: 'occurredAt', rawValue: '2026-13-40', normalizedValue: null, normalizationStatus: 'invalid', evidenceRefs: ['EV1'] }); })));
  accept('unknown money supported', () => validateCase(changed(input, value => { value.losses[0].claimedAmount = unknown(); })));
  accept('known zero differs from unknown', () => validateCase(changed(input, value => { value.losses[0].claimedAmount = fixtures.known(0); })));
  accept('not applicable differs from unknown money', () => validateCase(changed(input, value => { value.policies[0].coverages[0].perAccidentLimit = { status: 'not_applicable', amountFen: null, currency: 'CNY', reason: '该项目使用保险金额口径' }; })));
  reject('no answer leakage', () => validateCase({ ...input, expectedFindings: [] }), /schema/);
  reject('fractional fen', () => validateCase(changed(input, value => { value.payments[0].amount.amountFen = 1.2; })), /schema/);
  reject('unsafe integer money', () => validateCase(changed(input, value => { value.payments[0].amount.amountFen = 9007199254740992; })), /schema/);
  reject('negative amount must use transaction direction', () => validateCase(changed(input, value => { value.payments[0].amount.amountFen = -1; })), /schema/);
  reject('unknown amount needs reason', () => validateCase(changed(input, value => { value.losses[0].claimedAmount = { status: 'unknown', amountFen: null, currency: 'CNY', reason: null }; })), /schema/);
  reject('unknown amount cannot be zero', () => validateCase(changed(input, value => { value.losses[0].claimedAmount = { status: 'unknown', amountFen: 0, currency: 'CNY', reason: '金额未取得' }; })), /schema/);
  reject('timestamp requires timezone', () => validateCase(changed(input, value => { value.accident.occurredAt = '2026-09-01T12:00:00'; })), /schema/);
  reject('canonical timestamp must be a real date', () => validateCase(changed(input, value => { value.accident.occurredAt = '2026-02-30T12:00:00+08:00'; })), /schema/);
  reject('unknown enum', () => validateCase(changed(input, value => { value.claims[0].closureType = 'processing'; })), /schema/);
  reject('duplicate entity ID', () => validateCase(changed(input, value => { value.vehicles[0].vehicleId = 'P1'; })), /duplicate entity/);
  reject('unknown claim ref', () => validateCase(changed(input, value => { value.losses[0].claimId = 'MISSING'; })), /unknown claimId/);
  reject('unknown evidence ref', () => validateCase(changed(input, value => { value.claims[0].evidenceRefs = ['MISSING']; })), /unknown evidenceRefs/);
  reject('unknown source pointer', () => validateCase(changed(input, value => { value.evidence[0].recordPointer = '/claims/9/closureType'; })), /unresolved record pointer/);
  reject('unknown source version', () => validateCase(changed(input, value => { value.knowledgeRefs[0].version = '2025年版'; })), /version\/hash mismatch/);
  reject('wrong source hash', () => validateCase(changed(input, value => { value.knowledgeRefs[0].documentSha256 = '0'.repeat(64); })), /version\/hash mismatch/);
  reject('wrong section', () => validateCase(changed(input, value => { value.knowledgeRefs[0].sectionIds = ['CTPL-LIABILITY']; })), /unknown clause section/);
  reject('evidence page out of range', () => validateCase(changed(input, value => { const doc = docById.get('PA-COMMERCIAL-MOTOR-2020'); value.evidence.push({ evidenceId: 'EV2', sourceType: 'shared_document', documentId: doc.documentId, documentVersion: doc.version, page: doc.pageCount + 1, recordPointer: null, quote: null, provenance: 'original_document' }); })), /page outside document/);
  reject('cannot cite a missing case document', () => validateCase(changed(input, value => {
    value.documents.push({ documentId: 'DOC1', title: '未取得材料', materialType: 'calculation', status: 'not_obtained', version: 'v1', relativePath: null, sha256: null, pageCount: null, claimIds: ['CL1'], entityIds: [], issuedAt: null, receivedAt: null, sourceDescription: '内存缺件测试', isSynthetic: true });
    value.evidence.push({ evidenceId: 'EV2', sourceType: 'case_document', documentId: 'DOC1', documentVersion: 'v1', page: 1, recordPointer: null, quote: null, provenance: 'original_document' });
  })), /unavailable document/);
  reject('catalog cannot replace contract', () => validateCase(changed(input, value => { const doc = docById.get('PA-PRODUCT-CATALOG-SNAPSHOT'); value.knowledgeRefs = [{ documentId: doc.documentId, documentSha256: doc.sha256, version: doc.version, sectionIds: ['ANY'] }]; })), /not a contract document/);
  reject('cyclic payment correction', () => validateCase(changed(input, value => { value.payments[0].originalPaymentId = 'PAY1'; })), /cyclic/);
  reject('initial report cannot be final', () => validateExpected(changed(expected, value => { value.initialCheckpoint.reportStage = 'final_vehicle'; value.initialCheckpoint.finalReportAllowed = true; })), /schema/);
  reject('unresolved vehicle finding cannot finish', () => validateExpected(changed(expected, value => { value.reviewCheckpoints = [{ ...structuredClone(value.initialCheckpoint), checkpointId: 'CP1', reportStage: 'final_vehicle', finalReportAllowed: true, coverageConfirmedByHuman: true }]; })), /schema/);
  reject('cannot omit unresolved finding to finish', () => validateExpected(changed(expected, value => { value.reviewCheckpoints = [{ ...structuredClone(value.initialCheckpoint), checkpointId: 'CP1', reportStage: 'final_vehicle', finalReportAllowed: true, coverageConfirmedByHuman: true, findingStates: [] }]; })), /omitted finding/);
  reject('cannot change scope to bypass gate', () => validateExpected(changed(expected, value => { value.reviewCheckpoints = [{ ...structuredClone(value.initialCheckpoint), checkpointId: 'CP1', findingStates: [{ findingKey: 'F1', scope: 'injury', state: 'referred' }] }]; })), /changed finding scope/);
  reject('unknown rule in oracle', () => validateExpected(changed(expected, value => { value.expectedChecks[0].ruleId = 'UNKNOWN-RULE'; })), /unknown check ruleId/);
  reject('no pre-confirmed AI output', () => validateExpected(changed(expected, value => { value.initialCheckpoint.findingStates[0].state = 'confirmed'; })), /pre-reviewed/);
  reject('human confirm needs evidence', () => validateSteps(changed(script, value => { value.steps[1].payload.decision.evidenceRefs = []; }), expected, input), /schema/);
  reject('pending needs follow-up owner', () => validateSteps(changed(script, value => { value.steps[1].payload.decision.action = 'pending'; value.steps[1].payload.decision.missingItems = ['补充材料']; }), expected, input), /schema/);
  reject('referral needs recipient', () => validateSteps(changed(script, value => { value.steps[1].payload.decision.action = 'refer'; }), expected, input), /schema/);
  reject('no batch confirmation without inspection', () => validateSteps(changed(script, value => { value.steps.shift(); }), expected, input), /prior evidence inspection/);
  reject('inspect by another actor insufficient', () => validateSteps(changed(script, value => { value.steps[0].actorId = 'AUDITOR2'; }), expected, input), /prior evidence inspection/);
  reject('cannot amend before first decision', () => validateSteps(changed(script, value => { value.steps[1].action = 'amend_decision'; value.steps[1].payload.changeReason = '尝试修改尚不存在的结论'; }), expected, input), /without an existing decision/);
  reject('existing decision requires explicit amendment', () => validateSteps(changed(script, value => { value.steps.push({ ...structuredClone(value.steps[1]), stepId: 'S3', idempotencyKey: 'S3' }); }), expected, input), /must use amend_decision/);
  reject('accepted requests cannot reuse key with different content', () => validateSteps(changed(script, value => { value.steps[1].idempotencyKey = 'S1'; }), expected, input), /idempotency/);
  accept('repeat identical accepted request is reusable', () => validateSteps(changed(script, value => { value.steps.push({ ...structuredClone(value.steps[1]), stepId: 'S3' }); }), expected, input));
  const finalExpected = changed(expected, value => { value.reviewCheckpoints = [{ checkpointId: 'CP1', afterStepId: 'S4', reportStage: 'final_vehicle', finalReportAllowed: true, coverageConfirmedByHuman: true, inScopeChecksComplete: true, findingStates: [{ findingKey: 'F1', scope: 'vehicle', state: 'confirmed' }], requiredDisclosures: [] }]; });
  const finalSteps = changed(script, value => { value.steps.push(step('S3', 'confirm_coverage', { comment: '已核对所有范围内检查', checkIds: ['PAYMENT-APPROVAL-GAP'] }), step('S4', 'save_report', { stage: 'final_vehicle', comment: '确认报告内容后保存最终版' })); });
  accept('resolved finding with human confirmation can finish', () => { validateExpected(finalExpected, input); validateSteps(finalSteps, finalExpected, input); });
  accept('no findings still needs and supports human coverage confirmation', () => {
    const oracle = changed(finalExpected, value => { value.expectedFindings = []; value.initialCheckpoint.findingStates = []; value.reviewCheckpoints[0].findingStates = []; });
    const steps = changed(finalSteps, value => { value.steps = value.steps.filter(item => ['S3', 'S4'].includes(item.stepId)); });
    validateExpected(oracle, input); validateSteps(steps, oracle, input);
  });
  accept('planned stale conflict does not replace accepted decision', () => {
    const steps = changed(finalSteps, value => { const rejected = structuredClone(value.steps[1]); rejected.stepId = 'S2CONFLICT'; rejected.actorId = 'AUDITOR2'; rejected.idempotencyKey = 'STALE-REQUEST'; rejected.expectedOutcome = 'conflict'; rejected.payload.decision.action = 'exclude'; value.steps.splice(2, 0, rejected); });
    validateSteps(steps, finalExpected, input);
  });
  reject('report cannot finish without coverage confirmation', () => validateSteps(changed(finalSteps, value => { value.steps = value.steps.filter(item => item.stepId !== 'S3'); }), finalExpected, input), /human coverage confirmation/);
  const referredSteps = changed(finalSteps, value => { value.steps[1].payload.decision = { ...decision, action: 'refer', professionalRecipient: '专业审核岗位', professionalReason: '待专业判断' }; });
  reject('referral is not resolution', () => validateSteps(referredSteps, finalExpected, input), /unresolved in-scope/);
  accept('independent injury referral permits vehicle final with disclosure', () => {
    const oracle = changed(finalExpected, value => {
      value.expectedInjuryStatus = 'injury_present'; value.expectedFindings.push({ ...structuredClone(value.expectedFindings[0]), findingKey: 'F2', scope: 'injury', ruleId: 'INJURY-IDENTIFICATION' });
      value.initialCheckpoint.findingStates.push({ findingKey: 'F2', scope: 'injury', state: 'unreviewed' });
      value.reviewCheckpoints[0].findingStates.push({ findingKey: 'F2', scope: 'injury', state: 'referred' }); value.reviewCheckpoints[0].requiredDisclosures = ['人伤未审查，已转专业复核'];
    });
    const steps = changed(finalSteps, value => { value.steps.splice(2, 0, step('S2B', 'decide_finding', { findingKey: 'F2', decision: { ...decision, action: 'refer', professionalRecipient: '人伤岗位', professionalReason: '首期范围外' } })); });
    validateExpected(oracle, input); validateSteps(steps, oracle, input);
  });
  return passed;
}

try {
  const result = verifyPreparation();
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) {
    result.selfTestsPassed = selfTest();
  } else if (args.includes('--case')) {
    const argument = name => { const index = args.indexOf(name); return index >= 0 ? args[index + 1] : null; };
    const casePath = path.resolve(argument('--case'));
    const input = JSON.parse(fs.readFileSync(casePath, 'utf8'));
    validateCase(input, { caseDirectory: path.dirname(casePath) });
    const expectedPath = argument('--expected');
    const stepsPath = argument('--steps');
    check(!stepsPath || expectedPath, '--steps requires --expected');
    if (expectedPath) {
      const expected = JSON.parse(fs.readFileSync(path.resolve(expectedPath), 'utf8'));
      validateExpected(expected, input);
      if (stepsPath) validateSteps(JSON.parse(fs.readFileSync(path.resolve(stepsPath), 'utf8')), expected, input, { requireSupplementFiles: true });
    }
    result.validatedCase = input.datasetCaseId;
  } else check(args.length === 0, 'Usage: node validate_step1.mjs [--self-test | --case FILE [--expected FILE] [--steps FILE]]');
  console.log(JSON.stringify({ status: 'passed', ...result, providerCalls: 0 }, null, 2));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}

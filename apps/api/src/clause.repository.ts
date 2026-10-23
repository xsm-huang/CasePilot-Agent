import { Injectable } from '@nestjs/common';
import type { ClauseCitation, Finding } from './domain.js';
import { clauses } from './fixtures.js';

@Injectable()
export class ClauseRepository {
  search(productCode: string, version: string, findings: Finding[]): ClauseCitation[] {
    const queryTerms = findings.length
      ? findings.flatMap((finding) => [finding.title, finding.detail, finding.code])
      : ['损失核定', '金额'];
    return clauses
      .filter((clause) => clause.productCode === productCode && clause.version === version)
      .map((clause) => ({
        ...clause,
        score: clause.keywords.reduce((score, keyword) => score + (queryTerms.some((term) => term.includes(keyword)) ? 1 : 0), 0)
      }))
      .filter((clause) => clause.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(({ id, title, content, score }) => ({ id, title, content, score }));
  }
}

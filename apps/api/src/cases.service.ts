import { Injectable, NotFoundException } from '@nestjs/common';
import { cases } from './fixtures.js';
import type { ClaimCase } from './domain.js';

@Injectable()
export class CasesService {
  list(): ClaimCase[] {
    return cases;
  }

  get(id: string): ClaimCase {
    const claim = cases.find(item => item.id === id);
    if (!claim) throw new NotFoundException(`Case ${id} not found`);
    return claim;
  }
}

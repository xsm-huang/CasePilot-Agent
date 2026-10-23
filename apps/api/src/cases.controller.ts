import { Controller, Get, Inject, Param } from '@nestjs/common';
import { CasesService } from './cases.service.js';

@Controller('api/cases')
export class CasesController {
  constructor(@Inject(CasesService) private readonly cases: CasesService) {}

  @Get()
  list() { return this.cases.list(); }

  @Get(':id')
  get(@Param('id') id: string) {
    return this.cases.get(id);
  }
}

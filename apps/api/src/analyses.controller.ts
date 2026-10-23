import { BadRequestException, Body, Controller, Get, Headers, Inject, MessageEvent, Param, Post, Sse } from '@nestjs/common';
import { map, Observable } from 'rxjs';
import { AnalysesService } from './analyses.service.js';

@Controller('api/analyses')
export class AnalysesController {
  constructor(@Inject(AnalysesService) private readonly analyses: AnalysesService) {}

  @Get()
  list() { return this.analyses.list(); }

  @Get(':id')
  get(@Param('id') id: string) { return this.analyses.get(id); }

  @Post()
  create(@Body() body: { caseId?: string } | undefined) {
    if (!body || typeof body.caseId !== 'string') throw new BadRequestException('caseId 必须为字符串。');
    return this.analyses.create(body.caseId);
  }

  @Post(':id/review')
  async review(@Param('id') id: string, @Body() body: { decision?: unknown; comment?: unknown } | undefined) {
    if (!body || (body.decision !== 'approve' && body.decision !== 'reject')) throw new BadRequestException('decision 必须为 approve 或 reject。');
    if (body.comment !== undefined && (typeof body.comment !== 'string' || body.comment.length > 2000)) throw new BadRequestException('审核意见必须为不超过 2000 字的字符串。');
    const review: { decision: 'approve' | 'reject'; comment: string } = {
      decision: body.decision, comment: typeof body.comment === 'string' ? body.comment : ''
    };
    return this.analyses.review(id, review);
  }

  @Sse(':id/events')
  events(@Param('id') id: string, @Headers('last-event-id') cursor?: string): Observable<MessageEvent> {
    const after = Number(cursor ?? 0);
    if (!Number.isSafeInteger(after) || after < 0) throw new BadRequestException('无效的事件游标。');
    return this.analyses.events(id, after).pipe(map((event) => ({ id: String(event.id), type: 'timeline', data: event })));
  }
}

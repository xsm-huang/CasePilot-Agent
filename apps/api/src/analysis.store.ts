import { Injectable, NotFoundException } from '@nestjs/common';
import { Observable, Subject } from 'rxjs';
import type { AnalysisTask, TimelineEvent } from './domain.js';

@Injectable()
export class AnalysisStore {
  private readonly tasks = new Map<string, AnalysisTask>();
  private readonly streams = new Map<string, Subject<TimelineEvent>>();

  create(caseId: string): AnalysisTask {
    const id = crypto.randomUUID();
    const task: AnalysisTask = { id, caseId, status: 'running', events: [], findings: [], citations: [] };
    this.tasks.set(id, task);
    this.streams.set(id, new Subject());
    this.emit(id, 'status', '分析任务已创建', `案件 ${caseId}`);
    return task;
  }

  get(id: string): AnalysisTask {
    const task = this.tasks.get(id);
    if (!task) throw new NotFoundException(`Analysis task ${id} not found`);
    return task;
  }

  list(): AnalysisTask[] {
    return [...this.tasks.values()].sort((a, b) => b.events[0].at.localeCompare(a.events[0].at));
  }

  update(id: string, patch: Partial<AnalysisTask>): AnalysisTask {
    return Object.assign(this.get(id), patch);
  }

  emit(id: string, type: TimelineEvent['type'], title: string, detail?: string, data?: unknown): TimelineEvent {
    const task = this.get(id);
    const event: TimelineEvent = { id: task.events.length + 1, type, at: new Date().toISOString(), title, detail, data, status: task.status };
    task.events.push(event);
    this.streams.get(id)?.next(event);
    if (['completed', 'rejected', 'failed'].includes(task.status)) this.streams.get(id)?.complete();
    return event;
  }

  events(id: string, after = 0): Observable<TimelineEvent> {
    const task = this.get(id);
    const live = this.streams.get(id)!;
    return new Observable((subscriber) => {
      task.events.filter((event) => event.id > after).forEach((event) => subscriber.next(event));
      const subscription = live.subscribe(subscriber);
      return () => subscription.unsubscribe();
    });
  }
}

import { Annotation, Command, END, START, StateGraph, interrupt } from '@langchain/langgraph';
import type { PostgresSaver } from '@langchain/langgraph-checkpoint-postgres';

const ProbeState = Annotation.Root({
  marker: Annotation<string>(),
  approved: Annotation<boolean>()
});

export function createProbeGraph(checkpointer: PostgresSaver) {
  return new StateGraph(ProbeState)
    .addNode('review', () => ({ approved: interrupt({ reason: 'G0 persistence probe' }) as boolean }))
    .addEdge(START, 'review')
    .addEdge('review', END)
    .compile({ checkpointer });
}

export { Command };

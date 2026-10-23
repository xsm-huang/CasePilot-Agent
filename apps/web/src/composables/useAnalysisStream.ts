import { ref } from 'vue';
import { v0TimelineEventSchema, type V0TimelineEvent } from '@casepilot/contracts';

type StreamCallbacks = {
  isCurrent: () => boolean;
  onEvent: (event: V0TimelineEvent) => void;
  onInvalid: (cause: unknown) => void;
};

export function useAnalysisStream() {
  const connection = ref('未连接');
  let stream: EventSource | undefined;

  function close(label = '未连接') {
    stream?.close();
    stream = undefined;
    connection.value = label;
  }

  function connect(id: string, callbacks: StreamCallbacks) {
    close('连接中');
    // V0 replays all events. The domain reducer removes duplicates; V1 will add after=cursor.
    const source = new EventSource(`/api/analyses/${encodeURIComponent(id)}/events`);
    stream = source;
    const active = () => stream === source && callbacks.isCurrent();
    source.onopen = () => { if (active()) connection.value = '实时连接'; };
    source.addEventListener('timeline', (message) => {
      if (!active()) return;
      try { callbacks.onEvent(v0TimelineEventSchema.parse(JSON.parse((message as MessageEvent<string>).data))); }
      catch (cause) { close('事件格式异常'); callbacks.onInvalid(cause); }
    });
    source.onerror = () => { if (active()) connection.value = '连接中断，正在重连'; };
  }

  return { connection, connect, close };
}

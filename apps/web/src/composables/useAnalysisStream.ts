import { ref } from 'vue';
import { workspaceEventSchema, type WorkspaceEvent } from '@casepilot/contracts';

type StreamCallbacks = {
  isCurrent: () => boolean;
  onEvent: (event: WorkspaceEvent) => void;
  onInvalid: (cause: unknown) => void;
  onDisconnect: () => void;
};

export function useAnalysisStream() {
  const connection = ref('未连接');
  let stream: EventSource | undefined;

  function close(label = '未连接') {
    stream?.close();
    stream = undefined;
    connection.value = label;
  }

  function connect(id: string, after: number, callbacks: StreamCallbacks) {
    close('连接中');
    const source = new EventSource(`/api/analyses/${encodeURIComponent(id)}/events?after=${after}`);
    stream = source;
    const active = () => stream === source && callbacks.isCurrent();
    source.onopen = () => { if (active()) connection.value = '实时连接'; };
    source.addEventListener('timeline', (message) => {
      if (!active()) return;
      try { callbacks.onEvent(workspaceEventSchema.parse(JSON.parse((message as MessageEvent<string>).data))); }
      catch (cause) { if (active()) { close('事件格式异常'); callbacks.onInvalid(cause); } }
    });
    source.onerror = () => { if (active()) { close('连接中断，同步快照'); callbacks.onDisconnect(); } };
  }

  return { connection, connect, close };
}

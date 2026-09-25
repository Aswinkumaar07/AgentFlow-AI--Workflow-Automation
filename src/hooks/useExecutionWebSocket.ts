import { useEffect, useRef, useCallback } from 'react';
import { useExecutionStore } from '../store/useExecutionStore';

const WS_BASE = 'ws://localhost:8000/api/v1/ws/execution';
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_DELAY_MS = 1000;

interface WSNodeEvent {
  type: 'node_event';
  node_id: string;
  status: string;
  latency_ms: number;
  log_message?: string;
  variables?: Record<string, any>;
  request_payload?: Record<string, any>;
  response_data?: Record<string, any>;
  error_message?: string;
}

interface WSExecutionStatus {
  type: 'execution_status';
  status: string;
  execution_id: string;
  total_steps?: number;
}

interface WSCompleted {
  type: 'completed';
  execution_id: string;
  status: string;
  duration_ms: number;
}

type WSMessage = WSNodeEvent | WSExecutionStatus | WSCompleted | { type: string; [key: string]: any };

/**
 * useExecutionWebSocket
 * Connects to the backend WebSocket execution stream and pipes messages
 * into the execution store. Auto-reconnects with exponential backoff.
 * Sends "start" action when connected with the node IDs to simulate.
 */
export function useExecutionWebSocket(
  executionId: string | null,
  nodeIds: string[],
  enabled = true,
) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isUnmounted = useRef(false);

  const {
    updateStepRecord,
    addLog,
    setVariables,
    appendExecutionPath,
  } = useExecutionStore.getState();

  const handleMessage = useCallback((event: MessageEvent) => {
    let msg: WSMessage;
    try {
      msg = JSON.parse(event.data);
    } catch {
      return;
    }

    if (msg.type === 'node_event') {
      const e = msg as WSNodeEvent;
      updateStepRecord(e.node_id, {
        status: e.status as any,
        latency_ms: e.latency_ms,
        request_payload: e.request_payload,
        response_data: e.response_data,
        error_message: e.error_message ?? undefined,
      });
      if (e.variables && Object.keys(e.variables).length > 0) {
        setVariables(e.node_id, e.variables);
      }
      if (e.status === 'COMPLETED' || e.status === 'FAILED') {
        appendExecutionPath(e.node_id);
      }
      if (e.log_message) {
        const level = e.status === 'FAILED' ? 'ERROR' : 'INFO';
        addLog(level, e.log_message, e.node_id);
      }
    } else if (msg.type === 'execution_status') {
      // Status change — update store status
      const e = msg as WSExecutionStatus;
      if (e.status === 'RUNNING' || e.status === 'PAUSED' || e.status === 'CANCELLED') {
        useExecutionStore.setState({ status: e.status as any });
      }
    } else if (msg.type === 'completed') {
      const e = msg as WSCompleted;
      const now = Date.now();
      useExecutionStore.setState({
        status: e.status === 'FAILED' ? 'FAILED' : 'COMPLETED',
        endedAt: now,
        totalDurationMs: e.duration_ms,
      });
      addLog(
        e.status === 'FAILED' ? 'ERROR' : 'INFO',
        `Execution [${e.execution_id}] ${e.status} in ${e.duration_ms}ms.`,
      );
    }
    // heartbeat, pong, connected — ignored
  }, [updateStepRecord, addLog, setVariables, appendExecutionPath]);

  const connect = useCallback(() => {
    if (!executionId || !enabled || isUnmounted.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(`${WS_BASE}/${executionId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectCount.current = 0;
        addLog('INFO', `WebSocket connected to execution stream [${executionId}].`);
        // Send start command with node IDs
        ws.send(JSON.stringify({ action: 'start', node_ids: nodeIds }));
      };

      ws.onmessage = handleMessage;

      ws.onerror = () => {
        addLog('WARN', `WebSocket error on execution [${executionId}]. Will reconnect.`);
      };

      ws.onclose = () => {
        if (isUnmounted.current) return;
        if (reconnectCount.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectCount.current);
          reconnectCount.current++;
          reconnectTimeout.current = setTimeout(connect, delay);
        } else {
          addLog('ERROR', `WebSocket max reconnect attempts reached for [${executionId}]. Falling back to simulation.`);
        }
      };
    } catch (err) {
      // WebSocket not available — frontend simulation will drive state
    }
  }, [executionId, enabled, nodeIds, handleMessage, addLog]);

  useEffect(() => {
    isUnmounted.current = false;
    connect();
    return () => {
      isUnmounted.current = true;
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    wsRef.current?.send(JSON.stringify({ action: 'ping' }));
  }, []);

  return { sendPing };
}

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

interface TaskEvent {
  type: string;
  task_id?: string;
  status?: string;
  chunk?: string;
}

export function useTaskStream() {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws/task-stream`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: TaskEvent = JSON.parse(event.data);

          if (message.type === "task:created" || message.type === "task:completed") {
            queryClient.invalidateQueries({ queryKey: ["tasks"] });
            queryClient.invalidateQueries({
              queryKey: ["conversations"],
            });
          }

          if (message.type === "task:completed" && message.task_id) {
            queryClient.invalidateQueries({
              queryKey: ["task", message.task_id],
            });
          }

          if (message.type === "task:output" && message.task_id) {
            queryClient.setQueryData(
              ["task", message.task_id, "output"],
              (old: string | undefined) => (old || "") + (message.chunk || ""),
            );
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        wsRef.current = null;
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [queryClient]);

  return wsRef.current;
}

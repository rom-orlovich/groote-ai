import { useQuery } from "@tanstack/react-query";

export interface TaskLogResponse {
  task_id: string;
  status: string;
  output: string;
  error: string | null;
  is_live: boolean;
  timestamp?: string;
}

export interface AgentOutputEntry {
  type: "thinking" | "tool_call" | "tool_result" | "output" | "raw_output";
  content: string;
  tool_name?: string;
  tool_input?: string;
  is_error?: boolean;
  timestamp?: string;
}

export interface WebhookFlowEntry {
  stage: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface KnowledgeInteraction {
  type: string;
  query?: string;
  result?: string;
  timestamp?: string;
}

export interface FullTaskLogResponse {
  metadata?: {
    task_id: string;
    status: string;
    source?: string;
    flow_id?: string;
    created_at?: string;
    [key: string]: unknown;
  };
  input?: Record<string, unknown>;
  user_inputs?: Record<string, unknown>[];
  webhook_flow?: WebhookFlowEntry[];
  agent_output?: AgentOutputEntry[];
  knowledge_interactions?: KnowledgeInteraction[];
  final_result?: Record<string, unknown>;
}

interface TaskItem {
  task_id: string;
}

export function useTaskLogs(taskId: string | null) {
  return useQuery<TaskLogResponse>({
    queryKey: ["task-logs", taskId],
    queryFn: async () => {
      if (!taskId) return null;
      const res = await fetch(`/api/tasks/${taskId}/logs`);
      if (!res.ok) throw new Error("Failed to fetch task logs");
      return res.json();
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      // Poll faster if it's live
      return query.state.data?.is_live ? 1000 : 5000;
    },
  });
}

export function useFullTaskLogs(taskId: string | null) {
  return useQuery<FullTaskLogResponse>({
    queryKey: ["task-logs-full", taskId],
    queryFn: async () => {
      if (!taskId) return {};
      const res = await fetch(`/api/tasks/${taskId}/logs/full`);
      if (!res.ok) throw new Error("Failed to fetch full task logs");
      return res.json();
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.metadata?.status;
      if (status === "completed" || status === "failed") return 10000;
      return 2000;
    },
  });
}

export function useGlobalLogs() {
  return useQuery<TaskLogResponse[]>({
    queryKey: ["global-logs"],
    queryFn: async () => {
      const tasksRes = await fetch("/api/tasks?limit=5");
      const tasks = await tasksRes.json();

      const logsPromises = tasks.map(async (task: TaskItem) => {
        const res = await fetch(`/api/tasks/${task.task_id}/logs`);
        return res.json();
      });

      return Promise.all(logsPromises);
    },
    refetchInterval: 3000,
  });
}

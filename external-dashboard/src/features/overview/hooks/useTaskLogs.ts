import { useQuery } from "@tanstack/react-query";

export interface TaskLogResponse {
  task_id: string;
  status: string;
  output: string;
  error: string | null;
  is_live: boolean;
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

export function useGlobalLogs() {
  // For now, we'll just fetch logs for the most recent tasks
  // In a real app, this would be a WebSocket stream
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

import { useQuery } from "@tanstack/react-query";

export interface Conversation {
  conversation_id: string;
  user_id: string;
  title: string;
  flow_id: string | null;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  metadata: Record<string, unknown>;
  message_count: number;
  total_cost_usd: number;
  total_tasks: number;
  total_duration_seconds: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface ConversationMessage {
  message_id: string;
  conversation_id: string;
  role: string;
  content: string;
  task_id: string | null;
  created_at: string;
  metadata: Record<string, unknown>;
}

export function useConversations(includeArchived = false) {
  return useQuery({
    queryKey: ["conversations", { includeArchived }],
    queryFn: async (): Promise<Conversation[]> => {
      const params = new URLSearchParams();
      if (includeArchived) {
        params.set("include_archived", "true");
      }
      const response = await fetch(`/api/conversations?${params}`);
      if (!response.ok) throw new Error("Failed to fetch conversations");
      return response.json();
    },
  });
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ["conversations", conversationId, "messages"],
    queryFn: async (): Promise<ConversationMessage[]> => {
      if (!conversationId) return [];
      const response = await fetch(`/api/conversations/${conversationId}/messages`);
      if (!response.ok) throw new Error("Failed to fetch messages");
      return response.json();
    },
    enabled: !!conversationId,
  });
}

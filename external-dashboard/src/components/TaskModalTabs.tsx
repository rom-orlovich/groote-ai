import { clsx } from "clsx";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { AgentOutputEntry } from "../features/overview/hooks/useTaskLogs";

export function AgentOutputTab({ entries }: { entries?: AgentOutputEntry[] }) {
  if (!entries?.length) return <EmptyState label="No agent output yet." />;

  return (
    <div className="space-y-1">
      {entries.map((entry, i) => (
        <AgentOutputLine key={`${entry.type}-${i}`} entry={entry} />
      ))}
    </div>
  );
}

function AgentOutputLine({ entry }: { entry: AgentOutputEntry }) {
  const [expanded, setExpanded] = useState(false);

  if (entry.type === "thinking") {
    return (
      <div className="text-gray-500 italic pl-2 border-l border-gray-800 py-0.5">
        {entry.content}
      </div>
    );
  }

  if (entry.type === "tool_call") {
    return (
      <div className="py-0.5">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 w-full text-left"
        >
          {expanded ? (
            <ChevronDown size={10} className="text-gray-500 shrink-0" />
          ) : (
            <ChevronRight size={10} className="text-gray-500 shrink-0" />
          )}
          <span className="bg-yellow-500/20 text-yellow-400 px-1.5 py-0.5 rounded text-[9px] font-bold">
            TOOL
          </span>
          <span className="text-yellow-300">{entry.tool_name || "unknown"}</span>
        </button>
        {expanded && entry.tool_input && (
          <pre className="mt-1 ml-6 p-2 bg-gray-900/50 rounded text-gray-400 overflow-x-auto whitespace-pre-wrap text-[9px]">
            {formatJson(entry.tool_input)}
          </pre>
        )}
      </div>
    );
  }

  if (entry.type === "tool_result") {
    const isError = entry.is_error;
    return (
      <div className="py-0.5">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 w-full text-left"
        >
          {expanded ? (
            <ChevronDown size={10} className="text-gray-500 shrink-0" />
          ) : (
            <ChevronRight size={10} className="text-gray-500 shrink-0" />
          )}
          <span
            className={clsx(
              "px-1.5 py-0.5 rounded text-[9px] font-bold",
              isError ? "bg-red-500/20 text-red-400" : "bg-green-500/20 text-green-400",
            )}
          >
            {isError ? "ERROR" : "RESULT"}
          </span>
          <span className={isError ? "text-red-300" : "text-green-300"}>
            {entry.tool_name || "unknown"}
          </span>
        </button>
        {expanded && entry.content && (
          <pre className="mt-1 ml-6 p-2 bg-gray-900/50 rounded text-gray-400 overflow-x-auto whitespace-pre-wrap text-[9px] max-h-40 overflow-y-auto">
            {entry.content}
          </pre>
        )}
      </div>
    );
  }

  if (entry.type === "raw_output") {
    return (
      <pre className="text-gray-400 bg-gray-900/30 p-1 rounded whitespace-pre-wrap">
        {entry.content}
      </pre>
    );
  }

  return <div className="text-gray-200 py-0.5">{entry.content}</div>;
}

export function WebhookFlowTab({
  events,
}: {
  events?: { stage: string; timestamp: string; data?: Record<string, unknown> }[];
}) {
  if (!events?.length) return <EmptyState label="No webhook flow data." />;

  return (
    <div className="space-y-2">
      {events.map((event) => (
        <WebhookFlowEvent key={`${event.stage}-${event.timestamp}`} event={event} />
      ))}
    </div>
  );
}

function WebhookFlowEvent({
  event,
}: {
  event: { stage: string; timestamp: string; data?: Record<string, unknown> };
}) {
  const [expanded, setExpanded] = useState(false);
  const hasData = event.data && Object.keys(event.data).length > 0;

  return (
    <div className="flex gap-3 items-start">
      <div className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-1.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <button
          type="button"
          onClick={() => hasData && setExpanded(!expanded)}
          className="flex items-center gap-1.5 text-left"
        >
          {hasData &&
            (expanded ? (
              <ChevronDown size={10} className="text-gray-500 shrink-0" />
            ) : (
              <ChevronRight size={10} className="text-gray-500 shrink-0" />
            ))}
          <span className="text-blue-400 font-bold">{event.stage}</span>
          <span className="text-gray-600 text-[9px]">
            {new Date(event.timestamp).toLocaleTimeString()}
          </span>
        </button>
        {expanded && event.data && (
          <pre className="text-gray-500 text-[9px] mt-1 ml-4 p-2 bg-gray-900/50 rounded overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(event.data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

interface KnowledgeItem {
  type: string;
  timestamp?: string;
  tool_name?: string;
  input?: string;
  content?: string;
  is_error?: boolean;
}

export function KnowledgeTab({ interactions }: { interactions?: KnowledgeItem[] }) {
  if (!interactions?.length) return <EmptyState label="No knowledge interactions." />;

  return (
    <div className="space-y-2">
      {interactions.map((item, i) => (
        <KnowledgeEntry key={`${item.type}-${item.timestamp}-${i}`} item={item} />
      ))}
    </div>
  );
}

function KnowledgeEntry({ item }: { item: KnowledgeItem }) {
  const [expanded, setExpanded] = useState(false);
  const summary = getKnowledgeSummary(item);

  return (
    <div className="border-l border-purple-800 pl-2 py-1">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-left w-full"
      >
        {expanded ? (
          <ChevronDown size={10} className="text-gray-500 shrink-0" />
        ) : (
          <ChevronRight size={10} className="text-gray-500 shrink-0" />
        )}
        <span className="bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded text-[9px] font-bold">
          {item.type}
        </span>
        {item.tool_name && <span className="text-purple-300 text-[9px]">{item.tool_name}</span>}
        {item.timestamp && (
          <span className="text-gray-600 text-[9px]">
            {new Date(item.timestamp).toLocaleTimeString()}
          </span>
        )}
        {item.is_error && (
          <span className="bg-red-500/20 text-red-400 px-1 py-0.5 rounded text-[8px]">ERROR</span>
        )}
      </button>
      {!expanded && summary && (
        <div className="ml-4 mt-0.5 text-gray-500 text-[9px] truncate">{summary}</div>
      )}
      {expanded && (
        <div className="ml-4 mt-1">
          {item.input && (
            <pre className="text-gray-400 text-[9px] p-2 bg-gray-900/50 rounded overflow-x-auto whitespace-pre-wrap max-h-40 overflow-y-auto">
              {formatJson(item.input)}
            </pre>
          )}
          {item.content && (
            <pre className="text-gray-300 text-[9px] p-2 bg-gray-900/50 rounded overflow-x-auto whitespace-pre-wrap max-h-60 overflow-y-auto mt-1">
              {formatKnowledgeContent(item.content)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

function getKnowledgeSummary(item: KnowledgeItem): string {
  if (item.type === "query" && item.input) {
    try {
      const parsed = JSON.parse(item.input);
      return parsed.query || parsed.search_query || "";
    } catch {
      return item.input.slice(0, 80);
    }
  }
  if (item.type === "result" && item.content) {
    try {
      const parsed = JSON.parse(item.content);
      if (parsed.result) return parsed.result.slice(0, 100);
      return item.content.slice(0, 100);
    } catch {
      return item.content.slice(0, 100);
    }
  }
  return "";
}

function formatKnowledgeContent(content: string): string {
  try {
    const parsed = JSON.parse(content);
    if (typeof parsed.result === "string") return parsed.result;
    return JSON.stringify(parsed, null, 2);
  } catch {
    return content;
  }
}

export function FinalResultTab({ result }: { result?: Record<string, unknown> }) {
  if (!result) return <EmptyState label="No final result yet." />;

  return <pre className="text-gray-300 whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>;
}

function EmptyState({ label }: { label: string }) {
  return <div className="text-gray-600 italic">{label}</div>;
}

function formatJson(input: string): string {
  try {
    return JSON.stringify(JSON.parse(input), null, 2);
  } catch {
    return input;
  }
}

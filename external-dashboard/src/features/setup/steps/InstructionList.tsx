import { Check, ChevronDown, ChevronUp, Copy, ExternalLink } from "lucide-react";
import { type ReactNode, useCallback, useState } from "react";
import type { InstructionStep } from "../types";

const URL_PATTERN = /(https?:\/\/[^\s,]+)/g;

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="inline-flex items-center gap-0.5 ml-1 text-gray-400 hover:text-orange-500 transition-colors"
      title="Copy to clipboard"
    >
      {copied ? <Check size={10} className="text-green-500" /> : <Copy size={10} />}
    </button>
  );
}

function renderDescriptionWithCopyableUrls(description: string): ReactNode[] {
  const resolved = description.replace("{origin}", window.location.origin);
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null = null;

  URL_PATTERN.lastIndex = 0;
  match = URL_PATTERN.exec(resolved);
  while (match !== null) {
    if (match.index > lastIndex) {
      parts.push(resolved.slice(lastIndex, match.index));
    }
    const url = match[0];
    parts.push(
      <span key={match.index} className="inline-flex items-center">
        <code className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 text-orange-500 text-[9px] rounded">
          {url}
        </code>
        <CopyButton text={url} />
      </span>,
    );
    lastIndex = match.index + url.length;
    match = URL_PATTERN.exec(resolved);
  }
  if (lastIndex < resolved.length) {
    parts.push(resolved.slice(lastIndex));
  }
  return parts;
}

interface InstructionListProps {
  instructions: InstructionStep[];
}

export function InstructionList({ instructions }: InstructionListProps) {
  const [isOpen, setIsOpen] = useState(true);
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  const toggleCheck = (step: number) => {
    setChecked((prev) => ({ ...prev, [step]: !prev[step] }));
  };

  const completedCount = Object.values(checked).filter(Boolean).length;

  return (
    <div className="border border-gray-200 dark:border-gray-700">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 text-[10px] font-heading text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <span>
          SETUP_INSTRUCTIONS
          {completedCount > 0 && (
            <span className="ml-2 text-green-500">
              ({completedCount}/{instructions.length})
            </span>
          )}
        </span>
        {isOpen ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      {isOpen && (
        <div className="px-3 pb-3 space-y-3">
          {instructions.map((instruction) => (
            <div
              key={instruction.step}
              className={`flex gap-3 transition-opacity ${checked[instruction.step] ? "opacity-50" : ""}`}
            >
              <button
                type="button"
                onClick={() => toggleCheck(instruction.step)}
                className={`mt-0.5 flex-shrink-0 w-4 h-4 border rounded-sm flex items-center justify-center transition-colors ${
                  checked[instruction.step]
                    ? "bg-green-500 border-green-500"
                    : "border-gray-300 dark:border-gray-600 hover:border-orange-400"
                }`}
              >
                {checked[instruction.step] && <Check size={10} className="text-white" />}
              </button>
              <div className="flex-1">
                <div
                  className={`text-[11px] font-heading mb-0.5 ${checked[instruction.step] ? "line-through" : ""}`}
                >
                  {instruction.title}
                </div>
                <p className="text-[10px] text-gray-500 font-mono leading-relaxed">
                  {renderDescriptionWithCopyableUrls(instruction.description)}
                </p>
                {instruction.link && (
                  <a
                    href={instruction.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[10px] text-orange-500 hover:text-orange-600 font-mono mt-1"
                  >
                    Open <ExternalLink size={10} />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

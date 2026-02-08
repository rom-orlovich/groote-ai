import { ArrowLeft, ArrowRight, Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { BrowsePlatform } from "./hooks/useSourceBrowser";
import { useSourceBrowser } from "./hooks/useSourceBrowser";

interface ResourcePickerProps {
  platform: BrowsePlatform;
  onSelectionChange: (ids: string[]) => void;
  onBack: () => void;
  onNext: () => void;
  selectedIds: string[];
}

export function ResourcePicker({
  platform,
  onSelectionChange,
  onBack,
  onNext,
  selectedIds,
}: ResourcePickerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const { resources, isLoading, isError } = useSourceBrowser(platform);

  const filteredResources = useMemo(() => {
    if (!searchQuery.trim()) return resources;
    const query = searchQuery.toLowerCase();
    return resources.filter(
      (r) => r.name.toLowerCase().includes(query) || r.description.toLowerCase().includes(query),
    );
  }, [resources, searchQuery]);

  const allFilteredSelected =
    filteredResources.length > 0 && filteredResources.every((r) => selectedIds.includes(r.id));

  const handleToggleAll = () => {
    if (allFilteredSelected) {
      const filteredIds = new Set(filteredResources.map((r) => r.id));
      onSelectionChange(selectedIds.filter((id) => !filteredIds.has(id)));
    } else {
      const currentSet = new Set(selectedIds);
      for (const r of filteredResources) {
        currentSet.add(r.id);
      }
      onSelectionChange(Array.from(currentSet));
    }
  };

  const handleToggle = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((s) => s !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {["a", "b", "c", "d", "e"].map((id) => (
          <div
            key={`skeleton-${platform}-${id}`}
            className="h-12 bg-panel-border/20 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-8">
        <div className="text-red-500 font-heading text-sm mb-2">FAILED_TO_LOAD_RESOURCES</div>
        <p className="text-[10px] text-app-muted">
          Could not fetch {platform} resources. Check your connection and try again.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-app-muted" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={`Search ${platform} resources...`}
          className="w-full pl-9 pr-3 py-2 border border-input-border bg-input-bg text-input-text text-sm focus:outline-none focus:border-primary"
        />
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={handleToggleAll}
          className="text-[10px] font-heading text-primary hover:text-primary/80"
        >
          {allFilteredSelected ? "DESELECT_ALL" : "SELECT_ALL"}
        </button>
        <span className="text-[10px] text-app-muted">{selectedIds.length} selected</span>
      </div>

      <div className="max-h-64 overflow-y-auto border border-panel-border">
        {filteredResources.length === 0 ? (
          <div className="text-center py-6 text-[10px] text-app-muted">
            {searchQuery ? "No matching resources" : "No resources found"}
          </div>
        ) : (
          filteredResources.map((resource) => (
            <label
              key={resource.id}
              className="flex items-start gap-3 p-3 border-b border-panel-border last:border-b-0 hover:bg-panel-border/10 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(resource.id)}
                onChange={() => handleToggle(resource.id)}
                className="mt-0.5 accent-primary"
              />
              <div className="flex-1 min-w-0">
                <div className="font-heading text-sm text-text-main truncate">{resource.name}</div>
                {resource.description && (
                  <div className="text-[10px] text-app-muted truncate">{resource.description}</div>
                )}
              </div>
            </label>
          ))
        )}
      </div>

      <div className="flex gap-2 pt-2">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 flex items-center justify-center gap-1 px-4 py-2 border border-panel-border hover:bg-panel-border/20 text-[10px] font-heading text-text-main"
        >
          <ArrowLeft size={12} />
          BACK
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={selectedIds.length === 0}
          className="flex-1 flex items-center justify-center gap-1 px-4 py-2 bg-cta text-white hover:opacity-90 text-[10px] font-heading disabled:opacity-50 disabled:cursor-not-allowed"
        >
          NEXT
          <ArrowRight size={12} />
        </button>
      </div>
    </div>
  );
}

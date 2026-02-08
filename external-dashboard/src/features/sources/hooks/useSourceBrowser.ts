import { useQuery } from "@tanstack/react-query";

const API_BASE = import.meta.env.VITE_API_URL || "";

export type BrowsePlatform = "github" | "jira" | "confluence";

export interface PlatformResource {
  id: string;
  name: string;
  description: string;
  metadata: Record<string, string | number | boolean>;
}

export interface BrowseResponse {
  resources: PlatformResource[];
  total_count: number;
  has_more: boolean;
}

const PLATFORM_ENDPOINTS: Record<BrowsePlatform, string> = {
  github: "/api/sources/browse/github/repos",
  jira: "/api/sources/browse/jira/projects",
  confluence: "/api/sources/browse/confluence/spaces",
};

async function fetchBrowseResources(platform: BrowsePlatform): Promise<BrowseResponse> {
  const response = await fetch(`${API_BASE}${PLATFORM_ENDPOINTS[platform]}`);
  if (!response.ok) {
    throw new Error(`Failed to browse ${platform} resources`);
  }
  return response.json();
}

export function useSourceBrowser(platform: BrowsePlatform | null) {
  const query = useQuery({
    queryKey: ["source-browser", platform],
    queryFn: () => fetchBrowseResources(platform as BrowsePlatform),
    enabled: platform !== null,
  });

  return {
    resources: query.data?.resources ?? [],
    totalCount: query.data?.total_count ?? 0,
    hasMore: query.data?.has_more ?? false,
    isLoading: query.isLoading,
    isError: query.isError,
  };
}

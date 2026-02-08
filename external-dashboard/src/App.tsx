import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

import { AnalyticsFeature } from "./features/analytics/AnalyticsFeature";
import { ChatFeature } from "./features/chat/ChatFeature";
import { InstallPage } from "./features/install/InstallPage";
import { IntegrationsFeature } from "./features/integrations/IntegrationsFeature";
import { LedgerFeature } from "./features/ledger/LedgerFeature";
import { OverviewFeature } from "./features/overview/OverviewFeature";
import { RegistryFeature } from "./features/registry/RegistryFeature";
import { AgentScalingSettings } from "./features/settings/AgentScalingSettings";
import { AIProviderGuard } from "./features/settings/AIProviderGuard";
import { AIProviderSettings } from "./features/settings/AIProviderSettings";
import { SourcesFeature } from "./features/sources/SourcesFeature";
import { WebhooksFeature } from "./features/webhooks/WebhooksFeature";
import { DashboardLayout } from "./layouts/DashboardLayout";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <DashboardLayout>
          <Routes>
            <Route
              path="/"
              element={
                <AIProviderGuard>
                  <OverviewFeature />
                </AIProviderGuard>
              }
            />
            <Route
              path="/analytics"
              element={
                <AIProviderGuard>
                  <AnalyticsFeature />
                </AIProviderGuard>
              }
            />
            <Route
              path="/ledger"
              element={
                <AIProviderGuard>
                  <LedgerFeature />
                </AIProviderGuard>
              }
            />
            <Route
              path="/sources"
              element={
                <AIProviderGuard>
                  <SourcesFeature />
                </AIProviderGuard>
              }
            />
            <Route
              path="/webhooks"
              element={
                <AIProviderGuard>
                  <WebhooksFeature />
                </AIProviderGuard>
              }
            />
            <Route
              path="/chat"
              element={
                <AIProviderGuard>
                  <ChatFeature />
                </AIProviderGuard>
              }
            />
            <Route
              path="/registry"
              element={
                <AIProviderGuard>
                  <RegistryFeature />
                </AIProviderGuard>
              }
            />
            <Route
              path="/integrations"
              element={
                <AIProviderGuard>
                  <IntegrationsFeature />
                </AIProviderGuard>
              }
            />
            <Route path="/install" element={<InstallPage />} />
            <Route path="/settings/ai-provider" element={<AIProviderSettings />} />
            <Route path="/settings/agents" element={<AgentScalingSettings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </DashboardLayout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

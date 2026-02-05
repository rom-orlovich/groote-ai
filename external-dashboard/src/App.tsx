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
import { IntegrationsFeature } from "./features/integrations/IntegrationsFeature";
import { LedgerFeature } from "./features/ledger/LedgerFeature";
import { OverviewFeature } from "./features/overview/OverviewFeature";
import { RegistryFeature } from "./features/registry/RegistryFeature";
import { SetupFeature } from "./features/setup/SetupFeature";
import { SetupGuard } from "./features/setup/SetupGuard";
import { SourcesFeature } from "./features/sources/SourcesFeature";
import { WebhooksFeature } from "./features/webhooks/WebhooksFeature";
import { DashboardLayout } from "./layouts/DashboardLayout";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/setup" element={<SetupFeature />} />
          <Route
            path="/*"
            element={
              <SetupGuard>
                <DashboardLayout>
                  <Routes>
                    <Route path="/" element={<OverviewFeature />} />
                    <Route path="/analytics" element={<AnalyticsFeature />} />
                    <Route path="/ledger" element={<LedgerFeature />} />
                    <Route path="/sources" element={<SourcesFeature />} />
                    <Route path="/webhooks" element={<WebhooksFeature />} />
                    <Route path="/chat" element={<ChatFeature />} />
                    <Route path="/registry" element={<RegistryFeature />} />
                    <Route path="/integrations" element={<IntegrationsFeature />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </DashboardLayout>
              </SetupGuard>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

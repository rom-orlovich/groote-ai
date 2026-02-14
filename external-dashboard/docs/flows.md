# External Dashboard - Flows

## Process Flows

### Application Startup Flow

```
[Browser] -> Load main.tsx -> [Create QueryClient]
                                     |
                             [Render <App />]
                                     |
                          [QueryClientProvider wraps all]
                                     |
                             [BrowserRouter]
                                     |
                          [DashboardLayout]
                                     |
                          [Route matching]
                                |         |
                         [/install]   [Other routes]
                            |              |
                     [Full screen]   [Header + Sidebar + Content]
```

**Startup Steps:**
1. main.tsx renders App component into DOM
2. QueryClient created with retry=1, no refetch on window focus
3. BrowserRouter enables client-side routing
4. DashboardLayout renders shell (Header, Sidebar, content area)
5. Routes match URL to feature components
6. Install page renders full-screen, other routes use standard layout

### Data Fetching Flow (React Query)

```
[Feature Component] -> [useQuery hook]
                              |
                    [Check QueryClient cache]
                         |           |
                     [Cache Hit] [Cache Miss]
                        |            |
                  [Return data] [Fetch from API]
                                     |
                              [Store in cache]
                                     |
                              [Return data + metadata]
```

**Fetching Steps:**
1. Feature component calls custom hook (e.g., useMetrics)
2. Hook uses TanStack Query's useQuery with query key and fetch function
3. QueryClient checks cache for matching query key
4. On cache miss, executes fetch function against Dashboard API
5. Response cached and returned with loading/error state
6. Subsequent renders use cached data until stale

### WebSocket Real-Time Update Flow

```
[Dashboard API] -> WebSocket message -> [useWebSocket hook]
                                               |
                                    [Parse event type]
                                         |          |
                                  [Task Update]  [Agent Status]
                                      |              |
                              [Update task list] [Update agent UI]
                                      |
                              [QueryClient invalidation]
                                      |
                              [Auto-refetch affected queries]
```

**Real-Time Steps:**
1. useWebSocket establishes connection to ws://host/ws
2. Server pushes task status changes and agent events
3. Hook parses message type and payload
4. Relevant React Query caches are invalidated
5. Components using affected queries automatically re-render

### Chat Conversation Flow

```
[User] -> Type message -> [ChatFeature input]
                                 |
                          [useChat.sendMessage()]
                                 |
                          [POST /api/conversations/{id}/messages]
                                 |
                          [Optimistic UI update]
                                 |
                          [Agent processes message]
                                 |
                          [WebSocket: new message event]
                                 |
                          [Chat UI updates with response]
```

**Chat Steps:**
1. User types message in ChatFeature input
2. useChat hook sends POST to conversations API
3. Message appears immediately in chat (optimistic update)
4. Agent engine processes the message
5. Response arrives via WebSocket
6. Chat UI renders agent response with typing indicator

### Settings Save Flow

```
[User] -> Enter AI provider config -> [AIProviderSettings form]
                                              |
                                    [useAIProviderSettings.save()]
                                              |
                                    [POST /api/user-settings/*]
                                              |
                                    [useAgentEngineStartup.trigger()]
                                              |
                                    [POST /api/agent-engine/start]
                                              |
                                    [Wait 2 seconds]
                                              |
                                    [Redirect to home page]
```

**Settings Steps:**
1. User enters API key and model selection
2. Save triggers mutation to user settings API
3. On success, triggers agent engine startup
4. Backend runs `docker-compose up -d cli`
5. After brief delay, user is redirected to dashboard home
6. Dashboard begins showing live data from running agents

### Webhook Management Flow

```
[User] -> Click "Create Webhook" -> [CreateWebhookModal]
                                           |
                                    [Fill form fields]
                                           |
                                    [useWebhooks.create()]
                                           |
                                    [POST /api/webhooks]
                                           |
                                    [Modal closes]
                                           |
                                    [Webhook list refreshes]
```

**Webhook Steps:**
1. User opens CreateWebhookModal
2. Fills in webhook URL, events, and source
3. Submit triggers create mutation
4. Dashboard API stores webhook configuration
5. Modal closes on success
6. Webhook list query invalidated and refreshes

### Source Browser Flow

```
[User] -> Click "Add Source" -> [AddSourceModal]
                                       |
                                [Select platform (GitHub/Jira)]
                                       |
                                [ResourcePicker loads repos]
                                       |
                                [User selects repos/projects]
                                       |
                                [useSources.addSource()]
                                       |
                                [Source card appears in list]
```

**Source Steps:**
1. User opens AddSourceModal
2. Selects platform integration
3. ResourcePicker fetches available repositories via OAuth
4. User selects repositories to index
5. Source created via API
6. Source list refreshes with new source card

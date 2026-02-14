# Slack MCP - Flows

## Process Flows

### Tool Invocation Flow

```
[MCP Client] --> SSE /sse --> [FastMCP Server :9003]
                                        |
                              [Dispatch to Tool Function]
                                        |
                              [SlackAPI Client Method]
                                        |
                              [HTTP Request to slack-api:3003]
                                        |
                              [Return JSON Response]
                                        |
                              [MCP Response to Client]
```

**Processing Steps:**
1. MCP client connects via SSE to port 9003
2. Client sends MCP tool call with parameters
3. FastMCP dispatches to registered tool function
4. Tool function calls corresponding SlackAPI method
5. SlackAPI sends HTTP request to slack-api:3003
6. Backend returns JSON response
7. Tool function returns result to MCP framework
8. MCP framework sends response back via SSE

### Thread Reply Flow

```
[Agent] --> get_slack_channel_history(channel, limit)
                    |
         [GET /api/v1/channels/{channel}/history]
                    |
         [Returns messages with timestamps]
                    |
         --> get_slack_thread(channel, thread_ts)
                    |
         [GET /api/v1/channels/{channel}/threads/{thread_ts}]
                    |
         [Returns thread replies]
                    |
         --> send_slack_message(channel, text, thread_ts)
                    |
         [POST /api/v1/messages with thread_ts]
                    |
         [Reply appears in thread]
```

**Processing Steps:**
1. Agent fetches recent channel messages to find relevant conversation
2. Agent gets thread replies for a specific message
3. Agent sends reply in the same thread using thread_ts
4. Message appears as a thread reply in Slack

### Message Acknowledgment Flow

```
[Agent] --> add_slack_reaction(channel, timestamp, "eyes")
                    |
         [POST /api/v1/reactions]
                    |
         [slack-api:3003] --> [Slack Web API]
                    |
         [Reaction appears on message]
                    |
         --> send_slack_message(channel, text, thread_ts)
                    |
         [Detailed response in thread]
```

**Processing Steps:**
1. Agent receives task triggered by Slack mention
2. Agent adds "eyes" reaction to acknowledge the message
3. Agent processes the request
4. Agent sends detailed response in the same thread

### Channel Discovery Flow

```
[Agent] --> list_slack_channels(limit, cursor)
                    |
         [GET /api/v1/channels]
                    |
         [Returns channels with IDs and names]
                    |
         --> get_slack_channel_info(channel)
                    |
         [GET /api/v1/channels/{channel}]
                    |
         [Returns channel details: topic, members]
```

**Processing Steps:**
1. Agent lists available channels with pagination
2. Agent identifies target channel by name or topic
3. Agent gets detailed channel information
4. Agent can now post messages to the discovered channel

### Message Update Flow

```
[Agent] --> send_slack_message(channel, "Processing...")
                    |
         [Returns message timestamp (ts)]
                    |
         [Agent completes processing]
                    |
         --> update_slack_message(channel, ts, "Done: results here")
                    |
         [PUT /api/v1/messages]
                    |
         [Original message updated in place]
```

**Processing Steps:**
1. Agent sends initial status message
2. Agent stores the returned message timestamp
3. Agent completes the underlying task
4. Agent updates the message with final results

## Error Flow

```
[Tool Function] --> [SlackAPI Method]
                          |
               [HTTP Request to slack-api]
                     |          |
              [Success]    [HTTP Error]
                  |              |
           [Return JSON]   [raise_for_status()]
                              |
                    [httpx.HTTPStatusError]
                              |
                    [FastMCP returns error to client]
```

**Error Handling:**
1. All SlackAPI methods call `response.raise_for_status()`
2. HTTP errors propagate as `httpx.HTTPStatusError`
3. FastMCP framework catches exceptions and returns error responses

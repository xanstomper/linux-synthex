# 11 — API Specification (gRPC)

AETHER CORE exposes three gRPC surfaces: **Daemon API** (UI/Mission Control), **Agent API** (agents<->daemon), and **Internal** (subsystem-to-subsystem, in-process or via mesh).

## 1. Daemon Service (UI / Mission Control)

```protobuf
service Daemon {
  rpc SubmitIntent(SubmitIntentReq)   returns (IntentResp);
  rpc StreamEvents(StreamReq)         returns (stream Event);
  rpc ListAgents(ListReq)             returns (AgentList);
  rpc GetAgentView(AgentId)           returns (AgentView);
  rpc ApproveCapability(ApprovalReq)  returns (ApprovalResp);
  rpc QueryMemory(MemoryQuery)        returns (MemoryResults);
  rpc TraverseGraph(GraphQuery)       returns (GraphResult);
  rpc TimeMachine(TimeMachineReq)     returns (WorkspaceState);
  rpc GetSecurityState(Empty)         returns (SecurityState);
  rpc SessionReplay(ReplayReq)        returns (stream Event);
}

message SubmitIntentReq { string raw = 1; Origin origin = 2; uint32 priority = 3; }
message IntentResp { string intent_id = 1; string status = 2; }
message ApprovalReq {
  string token_id = 1; bool approve = 2; string reason = 3; string decided_by = 4;
}
message SecurityState {
  double global_threat = 1;
  repeated AgentRisk agents = 2;
  repeated Alert alerts = 3;
}
```

## 2. Agent Service (Agent <-> Daemon)

```protobuf
service AgentRuntime {
  rpc Register(RegisterReq)           returns (AgentHandle);   // gets sandbox + base token
  rpc RequestCapability(CapReq)       returns (CapabilityToken);
  rpc Execute(Intent)                 returns (stream ToolResult); // carries token
  rpc EmitThought(Thought)            returns (Ack);
  rpc RetrieveMemory(MemFetch)        returns (MemBatch);       // scoped view
  rpc Subscribe(SubReq)               returns (stream Event);   // scoped topics
  rpc ReportStatus(Status)            returns (Ack);
  rpc Deregister(AgentId)             returns (Ack);
}

message CapReq {
  string agent_id = 1; Capability cap = 2; Scope scope = 3; string reason = 4;
}
message CapabilityToken {
  string id = 1; string agent_id = 2; Capability cap = 3;
  Scope scope = 4; int64 issued_at = 5; int64 expires_at = 6; bytes signature = 7;
}
message ToolResult {
  string trace_id = 1; string token_id = 2; bool ok = 3;
  bytes before_state = 4; bytes after_state = 5; string error = 6;
}
```

## 3. Memory / Graph Service

```protobuf
service Memory {
  rpc Store(MemoryRecord)    returns (StoreResp);
  rpc Search(SemanticSearch) returns (stream MemoryRecord);
  rpc Consolidate(ConsolReq) returns (ConsolResp);
}
service Graph {
  rpc UpsertNode(GraphNode)  returns (NodeResp);
  rpc UpsertEdge(GraphEdge)  returns (EdgeResp);
  rpc Query(CypherLike)      returns (GraphResult);
  rpc Neighborhood(NeighReq) returns (GraphResult);
}
```

## 4. Common Types

```protobuf
enum Capability {
  READ_FILE=0; WRITE_FILE=1; SEARCH_CODE=2; EXECUTE_COMMAND=3;
  ACCESS_DATABASE=4; USE_BROWSER=5; USE_GIT=6; USE_DOCKER=7;
  USE_KUBERNETES=8; NETWORK_ACCESS=9; SYSTEM_CONTROL=10; EMAIL=11;
  CALENDAR=12; NOTES=13; FILESYSTEM=14; MCP=15; CUSTOM=16;
}
message Scope { string path_prefix = 1; string service_id = 2; string topic = 3; }
message Event {
  string id=1; int64 ts=2; string type=3; string producer=4;
  string topic=5; string trace_id=6; string payload_json=7;
  string hash=8; string prev=9;
}
```

## 5. Transport & Auth
- gRPC over Unix socket for local UI (zero network exposure) + mTLS for remote.
- Per-connection identity from the Broker; every RPC authorized against capability scope.
- Streaming used throughout for thought/code/event live feeds (low latency for Observatory).

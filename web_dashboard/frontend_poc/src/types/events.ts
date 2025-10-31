/**
 * Event type definitions for WebSocket communication.
 * These interfaces mirror the Pydantic models in web_dashboard/schemas.py
 */

// Status types
export type AgentStatus = 'pending' | 'running' | 'completed' | 'error';
export type ResearchStatus = 'initializing' | 'running' | 'completed' | 'failed';
export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';
export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

// Payload interfaces

export interface AgentUpdatePayload {
  agent_id: string;
  agent_name: string;
  status: AgentStatus;
  progress: number; // 0-100
  message: string;
  stats?: Record<string, any>;
}

export interface FileGeneratedPayload {
  file_id: string;
  filename: string;
  file_type: string;
  language: string;
  size_bytes: number;
  path?: string;
}

export interface ResearchStatusPayload {
  session_id: string;
  overall_status: ResearchStatus;
  progress: number; // 0-100
  estimated_completion?: string; // ISO datetime string
  current_stage?: string;
  agents_completed: number;
  agents_total: number;
}

export interface LogPayload {
  level: LogLevel;
  message: string;
  source?: string;
  timestamp: string; // ISO datetime string
}

export interface ErrorPayload {
  error_type: string;
  message: string;
  details?: Record<string, any>;
  recoverable: boolean;
  stack_trace?: string;
}

export interface ConnectionStatusPayload {
  status: ConnectionStatus;
  message?: string;
}

export interface FilesReadyPayload {
  file_count: number;
  files: Array<Record<string, any>>;
  total_size_bytes: number;
}

// Event types

export type EventType =
  | 'agent_update'
  | 'file_generated'
  | 'research_status'
  | 'error'
  | 'log'
  | 'connection_status'
  | 'files_ready';

// Union type for all possible payloads
export type EventPayload =
  | AgentUpdatePayload
  | FileGeneratedPayload
  | ResearchStatusPayload
  | LogPayload
  | ErrorPayload
  | ConnectionStatusPayload
  | FilesReadyPayload;

// Discriminated Union Event Types

export interface AgentUpdateEvent {
  event_type: 'agent_update';
  payload: AgentUpdatePayload;
  timestamp: string;
  session_id: string;
}

export interface FileGeneratedEvent {
  event_type: 'file_generated';
  payload: FileGeneratedPayload;
  timestamp: string;
  session_id: string;
}

export interface ResearchStatusEvent {
  event_type: 'research_status';
  payload: ResearchStatusPayload;
  timestamp: string;
  session_id: string;
}

export interface LogEventType {
  event_type: 'log';
  payload: LogPayload;
  timestamp: string;
  session_id: string;
}

export interface ErrorEventType {
  event_type: 'error';
  payload: ErrorPayload;
  timestamp: string;
  session_id: string;
}

export interface ConnectionStatusEvent {
  event_type: 'connection_status';
  payload: ConnectionStatusPayload;
  timestamp: string;
  session_id: string;
}

export interface FilesReadyEvent {
  event_type: 'files_ready';
  payload: FilesReadyPayload;
  timestamp: string;
  session_id: string;
}

// Discriminated Union Type - TypeScript will automatically narrow types based on event_type
export type WebSocketEvent =
  | AgentUpdateEvent
  | FileGeneratedEvent
  | ResearchStatusEvent
  | LogEventType
  | ErrorEventType
  | ConnectionStatusEvent
  | FilesReadyEvent;

// Type guards for payload discrimination

export function isAgentUpdatePayload(payload: any): payload is AgentUpdatePayload {
  return (
    typeof payload === 'object' &&
    'agent_id' in payload &&
    'agent_name' in payload &&
    'status' in payload &&
    'progress' in payload &&
    'message' in payload
  );
}

export function isFileGeneratedPayload(payload: any): payload is FileGeneratedPayload {
  return (
    typeof payload === 'object' &&
    'file_id' in payload &&
    'filename' in payload &&
    'file_type' in payload &&
    'language' in payload &&
    'size_bytes' in payload
  );
}

export function isResearchStatusPayload(payload: any): payload is ResearchStatusPayload {
  return (
    typeof payload === 'object' &&
    'session_id' in payload &&
    'overall_status' in payload &&
    'progress' in payload
  );
}

export function isLogPayload(payload: any): payload is LogPayload {
  return (
    typeof payload === 'object' &&
    'level' in payload &&
    'message' in payload
  );
}

export function isErrorPayload(payload: any): payload is ErrorPayload {
  return (
    typeof payload === 'object' &&
    'error_type' in payload &&
    'message' in payload &&
    'recoverable' in payload
  );
}

export function isConnectionStatusPayload(payload: any): payload is ConnectionStatusPayload {
  return (
    typeof payload === 'object' &&
    'status' in payload
  );
}

export function isFilesReadyPayload(payload: any): payload is FilesReadyPayload {
  return (
    typeof payload === 'object' &&
    'file_count' in payload &&
    'files' in payload &&
    'total_size_bytes' in payload
  );
}

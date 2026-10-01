// Shared domain types mirroring the backend schemas.

export interface RoutingSuggestion {
  agent_id: string;
  agent_slug: string;
  agent_name: string;
  confidence: number;
  reason: string;
}

export interface Thought {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  title: string;
  original_audio_uri: string | null;
  audio_duration: number | null;
  raw_transcript: string;
  clean_transcript: string;
  summary: string;
  thought_type: string;
  importance: number;
  urgency: number;
  topics: string[];
  entities: string[];
  questions: string[];
  ideas: string[];
  possible_actions: string[];
  routing_suggestions: RoutingSuggestion[];
  source: string;
  capture_mode: string;
  status: string;
  starred: boolean;
  meta: Record<string, unknown>;
}

export interface Agent {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
  accent: string;
  system_role: string;
  provider: string;
  model: string;
  autonomy_level: number;
  interruption_policy: string;
  is_supervisor: boolean;
  enabled: boolean;
  routing_keywords: string;
  status?: string;
  unread_count?: number;
  active_work_count?: number;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  created_by_agent_id: string | null;
  originating_thought_id: string | null;
  project_id: string | null;
  due_at: string | null;
  requires_user_approval: boolean;
  approved: boolean;
  rationale: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  goals: string[];
  related_agent_ids: string[];
  related_thought_ids: string[];
  related_task_ids: string[];
  created_at: string;
}

export interface ResearchJob {
  id: string;
  question: string;
  agent_id: string | null;
  originating_thought_id: string | null;
  status: string;
  progress: number;
  sources: { title: string; url: string; snippet: string }[];
  findings: string;
  artifact_uri: string | null;
  error: string | null;
  created_at: string;
}

export interface Report {
  id: string;
  type: string;
  title: string;
  range_start: string | null;
  range_end: string | null;
  generated_by: string;
  content: Record<string, any>;
  related_objects: ObjectRef[];
  created_at: string;
}

export interface Memory {
  id: string;
  scope: string;
  category: string;
  content: string;
  agent_id: string | null;
  project_id: string | null;
  created_by_agent_id: string | null;
  originating_thought_id: string | null;
  provenance: Record<string, unknown>;
  created_at: string;
}

export interface Connection {
  id: string;
  type: string;
  title: string;
  explanation: string;
  confidence: number;
  related_objects: ObjectRef[];
  discovered_by: string;
  created_at: string;
}

export interface ObjectRef {
  type: string;
  id: string;
  label?: string;
}

export interface InboxItem {
  kind: string;
  id: string;
  title: string;
  context?: string;
  agent?: string;
  importance?: string;
  thought_id?: string;
  status?: string;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  kind: string;
  message: string;
  actor: string;
  links: ObjectRef[];
  level: string;
  created_at: string;
}

export interface HomeData {
  today: {
    thoughts_captured: number;
    active_investigations: number;
    decisions_waiting: number;
    tasks_generated: number;
  };
  needs_attention: {
    id: string;
    agent: string;
    agent_slug: string;
    summary: string;
    thought_id: string;
    status: string;
  }[];
  todays_connection: Connection | null;
}

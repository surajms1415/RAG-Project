export type RouteType = 'document_rag' | 'structured_analytics' | 'combined';

export interface Citation {
  document_id: string;
  filename: string;
  page_number?: number;
  section_title?: string;
  score?: number;
}

export interface AnalyticsResult {
  question: string;
  sql_query?: string;
  generated_sql?: string;
  is_safe?: boolean;
  row_count: number;
  columns: string[];
  rows?: Record<string, any>[];
  data?: Record<string, any>[];
  explanation: string;
  execution_time_ms: number;
}

export interface RagResult {
  question: string;
  answer: string;
  citations: Citation[];
}

export interface OrchestrationResponse {
  question: string;
  route_used?: RouteType;
  route_taken?: RouteType;
  answer?: string;
  final_answer?: string;
  citations?: Citation[];
  sql_query?: string;
  generated_sql?: string;
  structured_data?: Record<string, any>[];
  data?: Record<string, any>[];
  rag_result?: RagResult | null;
  analytics_result?: AnalyticsResult | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  routeTaken?: RouteType;
  citations?: Citation[];
  analyticsResult?: AnalyticsResult | null;
  error?: string;
}

export interface DocumentItem {
  id: string;
  title?: string;
  filename?: string;
  file_type?: string;
  source_uri?: string;
  file_size_bytes: number;
  status: string;
  chunk_count: number;
  created_at: string;
}

export interface SystemHealth {
  status: 'healthy' | 'unhealthy' | 'checking';
  database: string;
  latency_ms?: number;
  version?: string;
}

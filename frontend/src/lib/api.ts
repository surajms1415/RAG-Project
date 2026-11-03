import {
  OrchestrationResponse,
  AnalyticsResult,
  DocumentItem,
  SystemHealth,
} from '@/types';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<SystemHealth> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, {
      cache: 'no-store',
    });
    if (!res.ok) throw new Error('Health check failed');
    const data = await res.json();
    return {
      status: data.status,
      database: data.dependencies?.database?.status || 'unknown',
      latency_ms: data.dependencies?.database?.latency_ms,
      version: data.version,
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      database: 'unreachable',
    };
  }
}

export async function askUnifiedQuery(
  question: string,
  routeOverride?: string | null
): Promise<OrchestrationResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      route: routeOverride || null,
      route_override: routeOverride || null,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Unified query execution failed');
  }

  const data = await res.json();
  const rows = data.data || data.structured_data || data.rows || [];
  const sql = data.generated_sql || data.sql_query;
  const cols = data.columns || (rows.length > 0 ? Object.keys(rows[0]) : []);

  let analyticsObj = data.analytics_result;
  if (!analyticsObj && sql) {
    analyticsObj = {
      question: data.question,
      generated_sql: sql,
      sql_query: sql,
      explanation: data.answer || '',
      columns: cols,
      data: rows,
      rows: rows,
      row_count: rows.length,
      execution_time_ms: 0,
      is_safe: true,
    };
  } else if (analyticsObj) {
    analyticsObj = {
      ...analyticsObj,
      generated_sql: analyticsObj.generated_sql || analyticsObj.sql_query,
      data: analyticsObj.data || analyticsObj.rows || [],
      rows: analyticsObj.rows || analyticsObj.data || [],
      columns: analyticsObj.columns || (analyticsObj.data?.length > 0 ? Object.keys(analyticsObj.data[0]) : cols),
    };
  }

  return {
    ...data,
    route_taken: data.route_taken || data.route_used,
    final_answer: data.final_answer || data.answer,
    citations: data.citations || data.rag_result?.citations || [],
    generated_sql: sql,
    data: rows,
    analytics_result: analyticsObj,
  };
}

export async function askAnalyticsQuery(
  question: string
): Promise<AnalyticsResult> {
  const res = await fetch(`${API_BASE_URL}/api/v1/analytics/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Analytics query failed');
  }

  const data = await res.json();
  const rows = data.data || data.rows || [];
  return {
    ...data,
    generated_sql: data.generated_sql || data.sql_query,
    data: rows,
    rows: rows,
    columns: data.columns || (rows.length > 0 ? Object.keys(rows[0]) : []),
  };
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/documents`, {
      cache: 'no-store',
    });
    if (!res.ok) return [];
    const data = await res.json();
    const items = Array.isArray(data) ? data : data.items || [];
    return items.map((doc: any) => ({
      ...doc,
      filename: doc.filename || doc.title || doc.source_uri || 'Document',
      chunk_count: doc.chunk_count !== undefined ? doc.chunk_count : 0,
    }));
  } catch {
    return [];
  }
}

export async function uploadDocument(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'File upload failed');
  }

  return res.json();
}

export async function triggerWebhookIngestion(payload: {
  filename: string;
  file_url?: string;
  workflow_id?: string;
  execution_id?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/documents/webhook-ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Webhook ingestion failed');
  }

  return res.json();
}

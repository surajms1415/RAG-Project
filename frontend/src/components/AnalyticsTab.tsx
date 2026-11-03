'use client';

import React, { useState } from 'react';
import {
  Database,
  Code,
  ShieldCheck,
  Play,
  Clock,
  Sparkles,
  Table,
  Check,
  Copy,
  AlertTriangle,
  Layers,
} from 'lucide-react';
import { AnalyticsResult } from '@/types';
import { askAnalyticsQuery } from '@/lib/api';

const SAMPLE_QUERIES = [
  'What are our top 3 best-selling products by total revenue?',
  'List all customers and their total spend across completed orders.',
  'How many orders exist in each status (COMPLETED, PENDING, SHIPPED)?',
  'What is the overall average order total?',
];

const APPROVED_TABLES = [
  {
    name: 'customers',
    desc: 'Customer accounts, company names, emails, and tiers',
  },
  {
    name: 'products',
    desc: 'Product catalog, SKU, unit prices, and categories',
  },
  {
    name: 'orders',
    desc: 'Sales orders, customer references, dates, and statuses',
  },
  {
    name: 'order_items',
    desc: 'Line items, quantities, unit prices, and line totals',
  },
];

export function AnalyticsTab() {
  const [question, setQuestion] = useState(SAMPLE_QUERIES[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalyticsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedSql, setCopiedSql] = useState(false);

  const handleExecute = async (q?: string) => {
    const targetQ = q || question;
    if (!targetQ.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await askAnalyticsQuery(targetQ);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Analytics query execution failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const copySql = (sql: string) => {
    navigator.clipboard.writeText(sql);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 2000);
  };

  const rows = result?.data || result?.rows || [];
  const sql = result?.generated_sql || result?.sql_query;
  const columns = result?.columns || (rows.length > 0 ? Object.keys(rows[0]) : []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 sm:px-6 space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          Safe Business Analytics & Text-to-SQL Studio
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Ask questions against your transactional data in plain English. The AI generates SQL, runs it through an AST security validator (read-only enforcement, table whitelist, row limits), and visualizes the results.
        </p>
      </div>

      {/* Query Bar & Presets */}
      <div className="glass-panel p-4 rounded-2xl border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. Which customer spent the most on Enterprise licenses?"
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
          />
          <button
            onClick={() => handleExecute()}
            disabled={isLoading || !question.trim()}
            className="btn-click px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-medium text-xs sm:text-sm flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/20 hover:opacity-95 transition-all disabled:opacity-40"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{isLoading ? 'Executing...' : 'Run Query'}</span>
          </button>
        </div>

        {/* Presets with Click Effect */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <span className="text-[11px] text-slate-500 font-medium mr-1">Presets:</span>
          {SAMPLE_QUERIES.map((sq, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuestion(sq);
                handleExecute(sq);
              }}
              className="chip-click text-[11px] px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-cyan-300 transition-colors"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Query Output Display */}
      {result && (
        <div className="space-y-4">
          {/* Metrics & Safety Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] text-slate-400">Security Check</span>
              <div className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 mt-0.5">
                <ShieldCheck className="w-4 h-4" />
                Read-Only Safe
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] text-slate-400">Rows Returned</span>
              <div className="text-sm font-semibold text-slate-200 mt-0.5">
                {result.row_count || rows.length} rows
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] text-slate-400">Execution Latency</span>
              <div className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5 mt-0.5">
                <Clock className="w-3.5 h-3.5" />
                {result.execution_time_ms.toFixed(1)}ms
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-[11px] text-slate-400">Target Schema</span>
              <div className="text-xs font-semibold text-indigo-400 flex items-center gap-1.5 mt-0.5">
                <Layers className="w-3.5 h-3.5" />
                4 Whitelisted Tables
              </div>
            </div>
          </div>

          {/* Generated SQL Card */}
          {sql && (
            <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 text-xs">
                <span className="text-slate-300 font-semibold flex items-center gap-2">
                  <Code className="w-4 h-4 text-cyan-400" />
                  Generated SQL
                </span>
                <button
                  onClick={() => copySql(sql)}
                  className="btn-click flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
                >
                  {copiedSql ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy SQL</span>
                    </>
                  )}
                </button>
              </div>
              <div className="p-3 font-mono text-xs text-cyan-300 overflow-x-auto">
                <code>{sql}</code>
              </div>
            </div>
          )}

          {/* Explanation / Narrative */}
          {result.explanation && (
            <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-200 flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold text-indigo-300">Narrative Insight: </strong>
                {result.explanation}
              </div>
            </div>
          )}

          {/* Tabular Results */}
          {rows.length > 0 && (
            <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
              <div className="px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center gap-2 text-xs font-semibold text-slate-200">
                <Table className="w-4 h-4 text-cyan-400" />
                Tabular Dataset Output ({rows.length} rows)
              </div>

              <div className="overflow-x-auto max-h-80">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-900 text-slate-300 uppercase tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      {columns.map((col, idx) => (
                        <th key={idx} className="px-4 py-2.5 whitespace-nowrap">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {rows.map((row, rIdx) => (
                      <tr
                        key={rIdx}
                        className="hover:bg-slate-900/60 transition-colors cursor-default"
                      >
                        {columns.map((col, cIdx) => (
                          <td
                            key={cIdx}
                            className="px-4 py-2.5 whitespace-nowrap text-slate-200"
                          >
                            {typeof row[col] === 'number'
                              ? row[col].toLocaleString()
                              : String(row[col] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Schema Reference Accordion */}
      <div className="border border-slate-800 rounded-2xl p-4 glass-panel">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          Approved Relational Schema
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {APPROVED_TABLES.map((t, idx) => (
            <div
              key={idx}
              className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 transition-colors"
            >
              <div className="font-mono text-xs font-bold text-cyan-300">
                {t.name}
              </div>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                {t.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

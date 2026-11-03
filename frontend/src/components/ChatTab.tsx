'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Layers,
  FileText,
  Database,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Code,
  Clock,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { ChatMessage, RouteType } from '@/types';
import { askUnifiedQuery } from '@/lib/api';

const QUICK_PROMPTS = [
  {
    title: 'Top Products by Revenue',
    prompt: 'What are our top 3 best-selling products by total revenue?',
    route: 'structured_analytics',
    badge: 'SQL Analytics',
    color: 'from-cyan-500/10 to-blue-500/10 border-cyan-500/30 text-cyan-300',
  },
  {
    title: 'Sales & Contract Terms',
    prompt: 'Show total sales by customer and explain any payment terms in our agreements.',
    route: 'combined',
    badge: 'Hybrid (RAG + SQL)',
    color: 'from-violet-500/10 to-indigo-500/10 border-violet-500/30 text-violet-300',
  },
  {
    title: 'Customer Orders Breakdown',
    prompt: 'List all customers with their total completed orders count.',
    route: 'structured_analytics',
    badge: 'SQL Analytics',
    color: 'from-cyan-500/10 to-blue-500/10 border-cyan-500/30 text-cyan-300',
  },
  {
    title: 'Document Revenue Drivers',
    prompt: 'What were the primary revenue drivers highlighted in our uploaded reports?',
    route: 'document_rag',
    badge: 'Document RAG',
    color: 'from-emerald-500/10 to-teal-500/10 border-emerald-500/30 text-emerald-300',
  },
];

export function ChatTab() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '👋 Welcome to **InsightFlow AI**! I can answer questions across your unstructured documents (PDF, DOCX, PPTX, CSV) and relational business data (orders, sales, customers, products). Ask a question or click a sample query below to get started!',
      timestamp: 'Just now',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async (questionText?: string) => {
    const q = questionText || input.trim();
    if (!q || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: q,
      timestamp: 'Just now',
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!questionText) setInput('');
    setIsLoading(true);

    try {
      const response = await askUnifiedQuery(q);

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.final_answer || response.answer || 'No answer generated.',
        timestamp: 'Just now',
        routeTaken: response.route_taken || response.route_used,
        citations: response.citations || response.rag_result?.citations || [],
        analyticsResult: response.analytics_result,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, an error occurred while processing your query: ${err.message || 'Server error'}. Please ensure the backend server is running.`,
        timestamp: 'Just now',
        error: err.message,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderRouteBadge = (route?: RouteType) => {
    if (!route) return null;

    if (route === 'combined') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-violet-500/15 text-violet-300 border border-violet-500/30">
          <Layers className="w-3.5 h-3.5 text-violet-400" />
          Hybrid Intent (RAG + Analytics)
        </span>
      );
    }
    if (route === 'structured_analytics') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          Structured SQL Analytics
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
        <FileText className="w-3.5 h-3.5 text-emerald-400" />
        Document RAG Knowledge
      </span>
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-6xl mx-auto px-4 py-4 sm:px-6">
      {/* Quick Prompts Bar */}
      <div className="mb-4">
        <p className="text-xs text-slate-400 mb-2 flex items-center gap-1.5 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          Recommended Queries
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {QUICK_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p.prompt)}
              className={`chip-click p-2.5 rounded-xl border bg-gradient-to-br ${p.color} text-left transition-all hover:brightness-110 focus:outline-none`}
            >
              <div className="text-xs font-bold truncate mb-1">{p.title}</div>
              <div className="text-[11px] text-slate-300 line-clamp-2 leading-tight">
                {p.prompt}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
        {messages.map((msg) => {
          const analyticsData = msg.analyticsResult?.data || msg.analyticsResult?.rows || [];
          const generatedSql = msg.analyticsResult?.generated_sql || msg.analyticsResult?.sql_query;
          const columns = msg.analyticsResult?.columns || (analyticsData.length > 0 ? Object.keys(analyticsData[0]) : []);

          return (
            <div
              key={msg.id}
              className={`flex gap-3 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.role === 'assistant' && (
                <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shrink-0 shadow-md shadow-indigo-600/20">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}

              <div
                className={`max-w-3xl rounded-2xl p-4 transition-all ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-indigo-600/10'
                    : 'glass-panel text-slate-200 border-slate-800'
                }`}
              >
                {/* Header meta for assistant */}
                {msg.role === 'assistant' && (
                  <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-slate-800/80">
                    <div className="flex items-center gap-2">
                      {renderRouteBadge(msg.routeTaken)}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span>{msg.timestamp}</span>
                      <button
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="btn-click p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                        title="Copy response"
                      >
                        {copiedId === msg.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Message text */}
                <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                  {msg.content}
                </div>

                {/* Analytics Data Table if available */}
                {analyticsData.length > 0 && (
                  <div className="mt-4 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/70">
                    <div className="flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800 text-xs">
                      <span className="font-semibold text-cyan-400 flex items-center gap-1.5">
                        <Database className="w-3.5 h-3.5" />
                        Query Results ({analyticsData.length} rows)
                      </span>
                      {msg.analyticsResult?.execution_time_ms !== undefined && (
                        <span className="text-slate-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {msg.analyticsResult.execution_time_ms.toFixed(1)}ms
                        </span>
                      )}
                    </div>

                    <div className="overflow-x-auto max-h-56">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-900 text-slate-300 uppercase tracking-wider font-semibold border-b border-slate-800">
                          <tr>
                            {columns.map((col, idx) => (
                              <th key={idx} className="px-3 py-2 whitespace-nowrap">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {analyticsData.map((row, rIdx) => (
                            <tr
                              key={rIdx}
                              className="hover:bg-slate-850/50 transition-colors cursor-default"
                            >
                              {columns.map((col, cIdx) => (
                                <td
                                  key={cIdx}
                                  className="px-3 py-2 whitespace-nowrap text-slate-300"
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

                    {/* Collapsible SQL Query View */}
                    {generatedSql && (
                      <div className="border-t border-slate-800 bg-slate-900/50 p-2">
                        <button
                          onClick={() => toggleSection(`sql-${msg.id}`)}
                          className="btn-click flex items-center justify-between w-full text-[11px] text-slate-400 hover:text-slate-200"
                        >
                          <span className="flex items-center gap-1">
                            <Code className="w-3 h-3 text-cyan-400" />
                            View Generated SQL Query
                          </span>
                          {expandedSections[`sql-${msg.id}`] ? (
                            <ChevronUp className="w-3 h-3" />
                          ) : (
                            <ChevronDown className="w-3 h-3" />
                          )}
                        </button>

                        {expandedSections[`sql-${msg.id}`] && (
                          <div className="mt-2 p-2 rounded bg-slate-950 font-mono text-[11px] text-cyan-300 overflow-x-auto border border-slate-800">
                            <code>{generatedSql}</code>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Citations Drawer if available */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80">
                    <button
                      onClick={() => toggleSection(`cite-${msg.id}`)}
                      className="btn-click flex items-center justify-between w-full text-xs font-semibold text-emerald-400 hover:text-emerald-300"
                    >
                      <span className="flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" />
                        Grounded Source Citations ({msg.citations.length})
                      </span>
                      {expandedSections[`cite-${msg.id}`] ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedSections[`cite-${msg.id}`] && (
                      <div className="mt-2 space-y-1.5">
                        {msg.citations.map((cite, cIdx) => (
                          <div
                            key={cIdx}
                            className="p-2 rounded-lg bg-slate-900/80 border border-slate-800 text-xs flex items-center justify-between"
                          >
                            <div className="flex items-center gap-2 truncate">
                              <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono">
                                Doc
                              </span>
                              <span className="font-medium text-slate-200 truncate">
                                {cite.filename}
                              </span>
                              {cite.page_number && (
                                <span className="text-[11px] text-slate-400">
                                  (p. {cite.page_number})
                                </span>
                              )}
                            </div>
                            {cite.score !== undefined && (
                              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                                {(cite.score * 100).toFixed(0)}% match
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="h-9 w-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
                  <User className="w-5 h-5 text-slate-300" />
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shrink-0 animate-pulse">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="glass-panel text-slate-200 border-slate-800 rounded-2xl p-4 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-violet-400 animate-bounce" />
              <span className="h-2 w-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]" />
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-bounce [animation-delay:0.4s]" />
              <span className="text-xs text-slate-400 ml-2 font-medium">
                Analyzing question & retrieving evidence...
              </span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Form Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="glass-panel rounded-2xl p-2 border-slate-800 shadow-xl flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question across documents and relational data..."
          disabled={isLoading}
          className="flex-1 bg-transparent px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="btn-click h-10 px-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white font-medium text-xs sm:text-sm flex items-center gap-1.5 shadow-md shadow-indigo-600/30 hover:opacity-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </form>
    </div>
  );
}

'use client';

import React, { useState } from 'react';
import {
  Zap,
  Play,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  FileCode,
  ArrowRight,
  Send,
} from 'lucide-react';
import { triggerWebhookIngestion } from '@/lib/api';

export function AutomationTab() {
  const [filename, setFilename] = useState('enterprise_quarterly_report.pdf');
  const [fileUrl, setFileUrl] = useState('https://raw.githubusercontent.com/mozilla/pdf.js/master/examples/learning/helloworld.pdf');
  const [workflowId, setWorkflowId] = useState('n8n-doc-ingest-01');
  const [executionId, setExecutionId] = useState('exec-1001');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedCurl, setCopiedCurl] = useState(false);

  const curlCommand = `curl -X POST "http://localhost:8000/api/v1/documents/webhook-ingest" \\
  -H "Content-Type: application/json" \\
  -d '{
    "filename": "${filename}",
    "file_url": "${fileUrl}",
    "workflow_id": "${workflowId}",
    "execution_id": "${executionId}"
  }'`;

  const handleTriggerWebhook = async () => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await triggerWebhookIngestion({
        filename,
        file_url: fileUrl,
        workflow_id: workflowId,
        execution_id: executionId,
      });
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'Webhook execution failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const copyCurl = () => {
    navigator.clipboard.writeText(curlCommand);
    setCopiedCurl(true);
    setTimeout(() => setCopiedCurl(false), 2000);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 sm:px-6 space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-400" />
          n8n Workflow Automation Hub
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Automate document ingestion from cloud storage, email, or Slack directly into InsightFlow AI via dedicated webhooks with execution tracking.
        </p>
      </div>

      {/* Visual Pipeline Flow */}
      <div className="p-4 rounded-2xl border border-slate-800 glass-panel">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
          n8n Workflow Execution Flow
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">1</div>
            <div>
              <div className="font-semibold text-slate-200">Webhook Trigger</div>
              <div className="text-[11px] text-slate-400">Receives file or URL</div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">2</div>
            <div>
              <div className="font-semibold text-slate-200">Python Backend</div>
              <div className="text-[11px] text-slate-400">Parses text & tables</div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">3</div>
            <div>
              <div className="font-semibold text-slate-200">Vector Embeddings</div>
              <div className="text-[11px] text-slate-400">Generates 384d vectors</div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold">4</div>
            <div>
              <div className="font-semibold text-slate-200">Audit Status</div>
              <div className="text-[11px] text-slate-400">Records execution ID</div>
            </div>
          </div>
        </div>
      </div>

      {/* Simulator Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Trigger */}
        <div className="glass-panel p-5 rounded-2xl border-slate-800 space-y-4">
          <h2 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Send className="w-4 h-4 text-amber-400" />
            Simulate n8n Ingestion Webhook
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Filename</label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500/50"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Remote File URL (PDF/DOCX/PPTX/CSV)</label>
              <input
                type="text"
                value={fileUrl}
                onChange={(e) => setFileUrl(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500/50 font-mono text-[11px]"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Workflow ID</label>
                <input
                  type="text"
                  value={workflowId}
                  onChange={(e) => setWorkflowId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500/50"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Execution ID</label>
                <input
                  type="text"
                  value={executionId}
                  onChange={(e) => setExecutionId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500/50"
                />
              </div>
            </div>

            <button
              onClick={handleTriggerWebhook}
              disabled={isLoading || !filename.trim()}
              className="btn-click w-full mt-2 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 text-white font-medium text-xs flex items-center justify-center gap-2 shadow-lg shadow-amber-600/20 hover:opacity-95 transition-all disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isLoading ? 'Triggering Ingestion...' : 'Trigger Ingestion Webhook'}</span>
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {response && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Webhook Ingestion Completed Successfully!
              </div>
              <div className="font-mono text-[11px] text-slate-300 bg-slate-950 p-2 rounded mt-1 overflow-x-auto">
                <pre>{JSON.stringify(response, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>

        {/* Workflow Template & Curl */}
        <div className="space-y-4">
          {/* Curl Command Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 text-xs">
              <span className="text-slate-300 font-semibold flex items-center gap-1.5">
                <FileCode className="w-3.5 h-3.5 text-amber-400" />
                cURL Webhook Request
              </span>
              <button
                onClick={copyCurl}
                className="btn-click flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors"
              >
                {copiedCurl ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
            <div className="p-3 font-mono text-[11px] text-amber-300/90 overflow-x-auto">
              <pre>{curlCommand}</pre>
            </div>
          </div>

          {/* Workflow File Location Info */}
          <div className="p-4 rounded-2xl border border-slate-800 glass-panel text-xs space-y-2">
            <h4 className="font-semibold text-slate-200">n8n Template Location</h4>
            <p className="text-slate-400 text-[11px]">
              The production-ready n8n workflow file is stored at:
            </p>
            <div className="p-2 rounded bg-slate-900 font-mono text-cyan-300 text-[11px] border border-slate-800">
              n8n/document_ingestion_workflow.json
            </div>
            <p className="text-[11px] text-slate-400">
              Simply go to your n8n workspace, click <strong>Import from File</strong>, and point the HTTP Request node to <code>http://localhost:8000/api/v1/documents/webhook-ingest</code>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

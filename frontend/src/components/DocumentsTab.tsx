'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Clock,
  Layers,
  FileCheck,
  FileType,
} from 'lucide-react';
import { DocumentItem } from '@/types';
import { fetchDocuments, uploadDocument } from '@/lib/api';

export function DocumentsTab() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocs = async () => {
    setIsLoading(true);
    try {
      const data = await fetchDocuments();
      setDocuments(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleFileUpload = async (file: File) => {
    // 50MB check
    if (file.size > 50 * 1024 * 1024) {
      setUploadStatus({
        type: 'error',
        message: 'File size exceeds 50MB limit.',
      });
      return;
    }

    setIsUploading(true);
    setUploadStatus(null);

    try {
      const res = await uploadDocument(file);
      const chunkMsg = res.chunk_count !== undefined ? `${res.chunk_count} chunks embedded` : 'Chunks created';
      setUploadStatus({
        type: 'success',
        message: `Successfully uploaded and indexed "${file.name}"! (${chunkMsg})`,
      });
      loadDocs();
    } catch (err: any) {
      setUploadStatus({
        type: 'error',
        message: err.message || 'Failed to upload document.',
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const getFormatBadge = (filename?: string) => {
    const ext = filename?.split('.').pop()?.toLowerCase() || '';
    if (ext === 'pdf')
      return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">PDF</span>;
    if (ext === 'docx')
      return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">DOCX</span>;
    if (ext === 'pptx')
      return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">PPTX</span>;
    if (ext === 'csv')
      return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">CSV</span>;
    return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20">{ext.toUpperCase() || 'DOC'}</span>;
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 sm:px-6 space-y-6">
      {/* Title & Stats Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-400" />
            Document Vault & Ingestion Pipeline
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Upload enterprise documents. Text is automatically parsed, normalized, chunked, and embedded for vector similarity retrieval.
          </p>
        </div>

        <button
          onClick={loadDocs}
          disabled={isLoading}
          className="btn-click flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-all w-fit"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Documents
        </button>
      </div>

      {/* Upload Dropzone with Clicking Effect */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all active:scale-[0.99] ${
          isUploading
            ? 'border-indigo-500/50 bg-indigo-500/5'
            : 'border-slate-800 hover:border-emerald-500/50 hover:bg-emerald-500/5'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.pptx,.csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFileUpload(f);
          }}
        />

        <div className="flex flex-col items-center justify-center gap-3">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <UploadCloud className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100">
              {isUploading ? 'Extracting, Chunking & Indexing...' : 'Click or drag document to upload'}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports <strong className="text-slate-300">PDF, DOCX, PPTX, CSV</strong> up to 50MB
            </p>
          </div>

          <div className="flex items-center gap-2 mt-1">
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
              PyMuPDF Tables
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
              Dense Vector Embeddings
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
              SHA-256 Deduplication
            </span>
          </div>
        </div>
      </div>

      {/* Status Notification */}
      {uploadStatus && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center gap-2.5 ${
            uploadStatus.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{uploadStatus.message}</span>
        </div>
      )}

      {/* Documents Grid / Table */}
      <div className="border border-slate-800 rounded-2xl overflow-hidden glass-panel">
        <div className="px-4 py-3 bg-slate-900/80 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Ingested Documents ({documents.length})
            </h2>
          </div>
        </div>

        {documents.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs">
            {isLoading ? 'Loading documents...' : 'No documents uploaded yet. Upload your first PDF, DOCX, PPTX, or CSV above!'}
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {documents.map((doc) => {
              const displayName = doc.filename || doc.title || doc.source_uri || 'Document';
              return (
                <div
                  key={doc.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/40 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-10 w-10 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center shrink-0">
                      <FileCheck className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-100 truncate">
                          {displayName}
                        </span>
                        {getFormatBadge(displayName)}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                        <span>{formatBytes(doc.file_size_bytes)}</span>
                        <span>•</span>
                        <span className="text-emerald-400 font-medium">
                          {doc.chunk_count} chunks embedded
                        </span>
                        <span>•</span>
                        <span className="font-mono text-[11px] text-slate-500 truncate">
                          ID: {doc.id.slice(0, 8)}...
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <span
                      className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${
                        doc.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                          : doc.status === 'RUNNING'
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                          : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                      }`}
                    >
                      {doc.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

'use client';

import React from 'react';
import { Sparkles, Activity, FileText, Database, MessageSquare, Zap } from 'lucide-react';
import { SystemHealth } from '@/types';

interface HeaderProps {
  activeTab: 'chat' | 'documents' | 'analytics' | 'automation';
  setActiveTab: (tab: 'chat' | 'documents' | 'analytics' | 'automation') => void;
  health: SystemHealth;
}

export function Header({ activeTab, setActiveTab, health }: HeaderProps) {
  const isHealthy = health.status === 'healthy';

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-violet-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center transition-transform hover:scale-105">
              <div className="h-full w-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold tracking-tight text-white">InsightFlow</span>
                <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  AI v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Unified Document Intelligence & Business Analytics
              </p>
            </div>
          </div>

          {/* Navigation Tabs with Clicking Effect */}
          <nav className="flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('chat')}
              className={`btn-click flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                activeTab === 'chat'
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Assistant</span>
            </button>

            <button
              onClick={() => setActiveTab('documents')}
              className={`btn-click flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                activeTab === 'documents'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>Documents</span>
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`btn-click flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                activeTab === 'analytics'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Database className="w-4 h-4" />
              <span>SQL Studio</span>
            </button>

            <button
              onClick={() => setActiveTab('automation')}
              className={`btn-click flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                activeTab === 'automation'
                  ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-md shadow-amber-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>n8n Hub</span>
            </button>
          </nav>

          {/* Backend Status Indicator */}
          <div className="flex items-center gap-2">
            <div
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                isHealthy
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              }`}
            >
              <span className="relative flex h-2 w-2">
                <span
                  className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    isHealthy ? 'bg-emerald-400' : 'bg-rose-400'
                  }`}
                />
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    isHealthy ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
              </span>
              <span className="hidden md:inline">
                {isHealthy ? `Backend Connected` : `Backend Offline`}
              </span>
              {health.latency_ms !== undefined && (
                <span className="text-[10px] opacity-75 hidden lg:inline font-mono">
                  {health.latency_ms.toFixed(1)}ms
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

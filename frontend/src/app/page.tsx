'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { ChatTab } from '@/components/ChatTab';
import { DocumentsTab } from '@/components/DocumentsTab';
import { AnalyticsTab } from '@/components/AnalyticsTab';
import { AutomationTab } from '@/components/AutomationTab';
import { SystemHealth } from '@/types';
import { fetchHealth } from '@/lib/api';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'analytics' | 'automation'>('chat');
  const [health, setHealth] = useState<SystemHealth>({
    status: 'checking',
    database: 'checking...',
  });

  const checkHealth = async () => {
    const res = await fetchHealth();
    setHealth(res);
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100">
      {/* Top Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
      />

      {/* Main Content Area */}
      <main className="flex-1">
        {activeTab === 'chat' && <ChatTab />}
        {activeTab === 'documents' && <DocumentsTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
        {activeTab === 'automation' && <AutomationTab />}
      </main>
    </div>
  );
}

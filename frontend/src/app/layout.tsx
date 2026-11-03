import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'InsightFlow AI — Enterprise Document & Business Analytics Platform',
  description:
    'Unified Document Intelligence, Dense Vector RAG, and Safe Text-to-SQL Analytics Platform.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#090d16] text-slate-100 selection:bg-indigo-500/30 selection:text-indigo-200">
        {children}
      </body>
    </html>
  );
}

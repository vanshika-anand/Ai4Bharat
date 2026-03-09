import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import '../styles/globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' })

export const metadata: Metadata = {
  title: 'MemoryThread — AI Content Intelligence Platform',
  description: 'AI-powered content assistant with persistent memory, knowledge graphs, and intelligent analysis. Built with Llama 3.1.',
  keywords: ['AI', 'content', 'writing', 'memory', 'knowledge graph', 'Llama'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${mono.variable} font-sans noise`}>{children}</body>
    </html>
  )
}

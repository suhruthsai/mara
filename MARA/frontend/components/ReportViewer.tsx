'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export interface Paper {
  title: string
  source: string
  url?: string
  year?: string
  authors?: string[]
}

export interface Hypothesis {
  hypothesis: string
  confidence: number
}

const TABS = ['report', 'hypotheses', 'papers'] as const

export default function ReportViewer({ report, hypotheses, papers }: { report: string, hypotheses: Hypothesis[], papers: Paper[] }) {
  const [tab, setTab] = useState<typeof TABS[number]>('report')

  return (
    <div className="bg-gray-800 p-4 rounded">
      <div className="flex mb-4">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`p-2 capitalize ${tab === t ? 'bg-blue-600' : 'bg-gray-700'}`}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === 'report' && (
        report
          // react-markdown does not render raw HTML, so LLM output can't inject scripts
          ? <div className="prose prose-invert max-w-none"><ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown></div>
          : <p className="text-gray-400">The report will appear here once the agents finish.</p>
      )}
      {tab === 'hypotheses' && (
        hypotheses.length
          ? <ul className="space-y-2 list-disc pl-5">{hypotheses.map((h, i) => <li key={i}>{h.hypothesis} <span className="text-gray-400">({h.confidence.toFixed(2)})</span></li>)}</ul>
          : <p className="text-gray-400">No hypotheses yet.</p>
      )}
      {tab === 'papers' && (
        papers.length
          ? (
            <ul className="space-y-2">
              {papers.map((p, i) => (
                <li key={i}>
                  {p.url ? <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{p.title}</a> : p.title}
                  <span className="text-gray-400"> · {p.source}{p.year ? ` · ${p.year}` : ''}</span>
                </li>
              ))}
            </ul>
          )
          : <p className="text-gray-400">No papers yet.</p>
      )}
    </div>
  )
}

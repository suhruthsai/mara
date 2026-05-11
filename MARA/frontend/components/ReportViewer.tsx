import { useState } from 'react'

interface Paper {
  title: string
  source: string
}

interface Hypothesis {
  hypothesis: string
  confidence: number
}

export default function ReportViewer({ report, hypotheses, papers }: { report: string, hypotheses: Hypothesis[], papers: Paper[] }) {
  const [tab, setTab] = useState('report')

  return (
    <div className="bg-gray-800 p-4 rounded">
      <div className="flex mb-4">
        <button onClick={() => setTab('report')} className={`p-2 ${tab === 'report' ? 'bg-blue-600' : 'bg-gray-700'}`}>Report</button>
        <button onClick={() => setTab('hypotheses')} className={`p-2 ${tab === 'hypotheses' ? 'bg-blue-600' : 'bg-gray-700'}`}>Hypotheses</button>
        <button onClick={() => setTab('papers')} className={`p-2 ${tab === 'papers' ? 'bg-blue-600' : 'bg-gray-700'}`}>Papers</button>
      </div>
      {tab === 'report' && <div className="prose" dangerouslySetInnerHTML={{ __html: report.replace(/\n/g, '<br>') }} />}
      {tab === 'hypotheses' && <ul>{hypotheses.map((h, i) => <li key={i}>{h.hypothesis} ({h.confidence})</li>)}</ul>}
      {tab === 'papers' && <ul>{papers.map((p, i) => <li key={i}>{p.title} - {p.source}</li>)}</ul>}
    </div>
  )
}
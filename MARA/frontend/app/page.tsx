'use client'

import { useState } from 'react'

import AgentStatusPanel from '../components/AgentStatusPanel'

import ReportViewer from '../components/ReportViewer'

export default function Home() {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<any>({})
  const [report, setReport] = useState('')
  const [hypotheses, setHypotheses] = useState<any[]>([])
  const [papers, setPapers] = useState<any[]>([])

  const handleSearch = () => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL!)
    ws.onopen = () => {
      ws.send(JSON.stringify({ query }))
    }
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.status === 'completed') {
        setReport(data.report)
        setHypotheses(data.hypotheses)
        setPapers(data.papers)
      } else {
        setStatus(data)
      }
    }
  }

  return (
    <div className="min-h-screen p-4">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full p-2 mb-4 bg-gray-800 text-white border border-gray-600"
        placeholder="Enter research query"
      />
      <button onClick={handleSearch} className="bg-blue-600 p-2 mb-4 hover:bg-blue-700">Search</button>
      <div className="grid grid-cols-2 gap-4">
        <AgentStatusPanel status={status} />
        <ReportViewer report={report} hypotheses={hypotheses} papers={papers} />
      </div>
    </div>
  )
}
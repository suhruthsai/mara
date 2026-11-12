'use client'

import { useEffect, useRef, useState } from 'react'

import AgentStatusPanel, { AgentStatus } from '../components/AgentStatusPanel'

import ReportViewer, { Hypothesis, Paper } from '../components/ReportViewer'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/research'

const emptyStatus: AgentStatus = { node: '', status: 'Idle', confidence_score: 0, iteration: 0 }

export default function Home() {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState<AgentStatus>(emptyStatus)
  const [report, setReport] = useState('')
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [papers, setPapers] = useState<Paper[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => () => wsRef.current?.close(), [])

  const handleSearch = () => {
    if (running || query.trim().length < 3) return
    wsRef.current?.close()
    setStatus({ ...emptyStatus, status: 'Connecting' })
    setReport('')
    setHypotheses([])
    setPapers([])
    setError('')
    setRunning(true)

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws
    let finished = false

    ws.onopen = () => {
      ws.send(JSON.stringify({ query: query.trim() }))
    }
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.error) {
        finished = true
        setError(data.error)
        setRunning(false)
        return
      }
      setStatus({
        node: data.node ?? '',
        status: data.status ?? '',
        confidence_score: data.confidence_score ?? 0,
        iteration: data.iteration ?? 0,
      })
      setPapers(data.papers ?? [])
      setReport(data.report ?? '')
      setHypotheses(data.hypotheses ?? [])
      if (data.status === 'completed') {
        finished = true
        setRunning(false)
      }
    }
    ws.onerror = () => {
      finished = true
      setError(`Could not connect to the backend at ${WS_URL}. Is it running?`)
      setRunning(false)
    }
    ws.onclose = () => {
      if (!finished) setError('Connection closed before the research finished.')
      setRunning(false)
    }
  }

  return (
    <div className="min-h-screen p-4 max-w-7xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">MARA · Multi-Agent Research Assistant</h1>
      <form
        className="flex gap-2 mb-4"
        onSubmit={(e) => {
          e.preventDefault()
          handleSearch()
        }}
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 p-2 bg-gray-800 text-white border border-gray-600 rounded"
          placeholder="Enter research query"
        />
        <button
          type="submit"
          disabled={running || query.trim().length < 3}
          className="bg-blue-600 px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {running ? 'Researching…' : 'Search'}
        </button>
      </form>
      {error && <div className="mb-4 p-3 rounded bg-red-900/60 border border-red-700">{error}</div>}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <AgentStatusPanel status={status} running={running} />
        <div className="lg:col-span-2">
          <ReportViewer report={report} hypotheses={hypotheses} papers={papers} />
        </div>
      </div>
    </div>
  )
}

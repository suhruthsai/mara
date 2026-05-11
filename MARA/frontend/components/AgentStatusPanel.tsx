import { useState } from 'react'

interface Status {
  status: string
  confidence_score: number
  iteration: number
}

export default function AgentStatusPanel({ status }: { status: Status }) {
  return (
    <div className="bg-gray-800 p-4 rounded">
      <h2 className="text-xl mb-4">Agent Status</h2>
      <p>Status: {status.status}</p>
      <p>Confidence: {status.confidence_score}</p>
      <p>Iteration: {status.iteration}</p>
      <div className="mt-4">
        <div className="bg-gray-700 h-2 rounded">
          <div className="bg-green-500 h-2 rounded" style={{ width: `${status.confidence_score * 100}%` }}></div>
        </div>
      </div>
    </div>
  )
}
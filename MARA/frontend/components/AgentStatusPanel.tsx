export interface AgentStatus {
  node: string
  status: string
  confidence_score: number
  iteration: number
}

const STEPS = ['search', 'critic', 'synthesis', 'reflection', 'writer', 'hypothesis']

export default function AgentStatusPanel({ status, running }: { status: AgentStatus, running: boolean }) {
  const confidence = Math.min(Math.max(status.confidence_score || 0, 0), 1)
  const done = status.status === 'completed'

  return (
    <div className="bg-gray-800 p-4 rounded">
      <h2 className="text-xl mb-4">Agent Status</h2>
      <p>Status: {status.status}</p>
      <p>Confidence: {confidence.toFixed(2)}</p>
      <p>Iteration: {status.iteration}</p>
      <div className="mt-4">
        <div className="bg-gray-700 h-2 rounded">
          <div className="bg-green-500 h-2 rounded transition-all" style={{ width: `${confidence * 100}%` }}></div>
        </div>
      </div>
      <ol className="mt-4 space-y-1 text-sm">
        {STEPS.map((step) => {
          const active = running && status.node === step
          return (
            <li key={step} className={active ? 'text-blue-400' : done ? 'text-green-400' : 'text-gray-400'}>
              {active ? '▶' : done ? '✓' : '•'} {step}
            </li>
          )
        })}
      </ol>
    </div>
  )
}

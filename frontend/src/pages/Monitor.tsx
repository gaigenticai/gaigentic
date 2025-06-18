import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getToken } from '../utils/auth'

interface RunLog {
  started_at: string
  status: string
  duration_ms: number
}

interface TenantStats {
  agents: number
  ingested_files: number
  executions: number
  avg_duration_ms: number
}

export default function Monitor() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const agentId = params.get('agent_id') || ''

  const [runs, setRuns] = useState<RunLog[]>([])
  const [stats, setStats] = useState<TenantStats | null>(null)

  useEffect(() => {
    if (agentId) {
      fetch(`/api/v1/agents/${agentId}/runs`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      })
        .then((r) => r.json())
        .then(setRuns)
        .catch(() => {})
    }
  }, [agentId])

  useEffect(() => {
    const tenantId = '00000000-0000-0000-0000-000000000001'
    fetch(`/api/v1/tenants/${tenantId}/stats`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    })
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {})
  }, [])

  const successPct = runs.length
    ? Math.round((runs.filter((r) => r.status === 'success').length / runs.length) * 100)
    : 0

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-bold">Execution Metrics</h2>
      {stats && (
        <div className="space-x-4">
          <span>Total Runs: {stats.executions}</span>
          <span>Avg Duration: {stats.avg_duration_ms}ms</span>
          <span>Success %: {successPct}%</span>
        </div>
      )}
      <h2 className="text-lg font-bold mt-4">Run History</h2>
      {runs.length ? (
        <table className="min-w-full text-sm">
          <thead>
            <tr>
              <th className="px-2 py-1">Started</th>
              <th className="px-2 py-1">Status</th>
              <th className="px-2 py-1">Duration (ms)</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r, idx) => (
              <tr key={idx} className="border-t">
                <td className="px-2 py-1">{new Date(r.started_at).toLocaleString()}</td>
                <td className="px-2 py-1">{r.status}</td>
                <td className="px-2 py-1">{r.duration_ms}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div>No runs found.</div>
      )}
    </div>
  )
}

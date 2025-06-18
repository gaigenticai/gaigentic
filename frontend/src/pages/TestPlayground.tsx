import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getToken } from '../utils/auth'

interface AgentTest {
  id: string
  name: string
  input_context: Record<string, unknown>
  expected_output: Record<string, unknown>
  created_at: string
}

interface TestResult {
  status: string
  diff: string
  actual: unknown
}

export default function TestPlayground() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const agentId = params.get('agent_id') || ''

  const [tests, setTests] = useState<AgentTest[]>([])
  const [name, setName] = useState('')
  const [inputText, setInputText] = useState('{}')
  const [expectedText, setExpectedText] = useState('{}')
  const [results, setResults] = useState<Record<string, TestResult>>({})
  const [running, setRunning] = useState<string | null>(null)

  const loadTests = () => {
    fetch(`/api/v1/agents/${agentId}/tests`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    })
      .then((r) => r.json())
      .then(setTests)
      .catch(() => {})
  }

  useEffect(() => {
    if (agentId) {
      loadTests()
    }
  }, [agentId])

  const createTest = async () => {
    let input: Record<string, unknown> = {}
    let expected: Record<string, unknown> = {}
    try {
      input = inputText ? JSON.parse(inputText) : {}
    } catch {
      alert('Input must be valid JSON')
      return
    }
    try {
      expected = expectedText ? JSON.parse(expectedText) : {}
    } catch {
      alert('Expected must be valid JSON')
      return
    }
    const res = await fetch(`/api/v1/agents/${agentId}/tests`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`
      },
      body: JSON.stringify({ name, input_context: input, expected_output: expected })
    })
    const data = await res.json()
    setTests([...tests, data])
    setName('')
  }

  const runTest = async (id: string) => {
    setRunning(id)
    const res = await fetch(`/api/v1/agents/${agentId}/tests/${id}/run`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` }
    })
    const data = await res.json()
    setResults((r) => ({ ...r, [id]: data }))
    setRunning(null)
  }

  const deleteTest = async (id: string) => {
    await fetch(`/api/v1/agents/${agentId}/tests/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${getToken()}` }
    })
    setTests((t) => t.filter((x) => x.id !== id))
  }

  const runAll = async () => {
    for (const t of tests) {
      // eslint-disable-next-line no-await-in-loop
      await runTest(t.id)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-bold">Agent Tests</h2>
      <div className="space-y-2">
        <input
          className="border p-1 w-64"
          placeholder="Test name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <textarea
          className="border p-1 w-full h-24"
          placeholder="Input JSON"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />
        <textarea
          className="border p-1 w-full h-24"
          placeholder="Expected Output JSON"
          value={expectedText}
          onChange={(e) => setExpectedText(e.target.value)}
        />
        <div className="space-x-2">
          <button className="px-2 py-1 bg-blue-500 text-white rounded" onClick={createTest} disabled={!name}>
            Create Test
          </button>
          <button className="px-2 py-1 bg-purple-500 text-white rounded" onClick={runAll} disabled={!tests.length}>
            Run All Tests
          </button>
        </div>
      </div>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th className="px-2 py-1 text-left">Name</th>
            <th className="px-2 py-1">Actions</th>
            <th className="px-2 py-1 text-left">Result</th>
          </tr>
        </thead>
        <tbody>
          {tests.map((t) => (
            <tr key={t.id} className="border-t align-top">
              <td className="px-2 py-1">{t.name}</td>
              <td className="px-2 py-1 space-x-1">
                <button
                  className="px-1 py-0 bg-green-500 text-white rounded"
                  onClick={() => runTest(t.id)}
                  disabled={running === t.id}
                >
                  Run
                </button>
                <button
                  className="px-1 py-0 bg-red-500 text-white rounded"
                  onClick={() => deleteTest(t.id)}
                >
                  Delete
                </button>
              </td>
              <td className="px-2 py-1 whitespace-pre-wrap">
                {results[t.id] && `${results[t.id].status}\n${results[t.id].diff}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

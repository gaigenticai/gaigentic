import { useEffect, useState } from 'react'
import { getToken } from '../utils/auth'

interface Plugin {
  id: string
  name: string
  description?: string
  is_active: boolean
  created_at: string
}

export default function Plugins() {
  const [plugins, setPlugins] = useState<Plugin[]>([])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [code, setCode] = useState('')
  const [testInput, setTestInput] = useState('{}')
  const [testResult, setTestResult] = useState('')

  const load = () => {
    fetch('/api/v1/plugins', {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then((r) => r.json())
      .then(setPlugins)
      .catch(() => {})
  }

  useEffect(() => {
    load()
  }, [])

  const create = async () => {
    const res = await fetch('/api/v1/plugins', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({ name, description, code }),
    })
    if (res.ok) {
      setName('')
      setDescription('')
      setCode('')
      load()
    } else {
      alert('Create failed')
    }
  }

  const test = async (id: string) => {
    let payload: unknown
    try {
      payload = JSON.parse(testInput)
    } catch {
      alert('Invalid JSON')
      return
    }
    const res = await fetch(`/api/v1/plugins/${id}/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    setTestResult(JSON.stringify(data, null, 2))
  }

  const toggle = async (id: string) => {
    await fetch(`/api/v1/plugins/${id}/disable`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    load()
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-bold">Plugins</h2>
      <div className="space-y-2">
        <input
          className="border p-1 w-64"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="border p-1 w-64"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <textarea
          className="border p-1 w-64 h-32"
          placeholder="Python code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
        />
        <button className="px-2 py-1 bg-blue-500 text-white" onClick={create}>
          Create
        </button>
      </div>
      <div className="space-y-2">
        <h3 className="font-bold">Existing Plugins</h3>
        {plugins.map((p) => (
          <div key={p.id} className="border p-2 space-y-1">
            <div className="font-bold">
              {p.name} {p.is_active ? '' : '(disabled)'}
            </div>
            <div className="text-sm">{p.description}</div>
            <button
              className="px-2 py-1 bg-green-500 text-white mr-2"
              onClick={() => test(p.id)}
            >
              Test
            </button>
            <button
              className="px-2 py-1 bg-gray-300 mr-2"
              onClick={() => toggle(p.id)}
            >
              {p.is_active ? 'Disable' : 'Enable'}
            </button>
          </div>
        ))}
      </div>
      <div>
        <textarea
          className="border p-1 w-64 h-24"
          value={testInput}
          onChange={(e) => setTestInput(e.target.value)}
        />
        <div className="mt-2 whitespace-pre-wrap text-sm">{testResult}</div>
      </div>
    </div>
  )
}

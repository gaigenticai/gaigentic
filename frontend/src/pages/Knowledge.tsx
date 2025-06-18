import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getToken } from '../utils/auth'

interface Result {
  source_file: string
  chunk_index: number
  text: string
}

interface UploadEntry {
  name: string
  time: string
}

export default function Knowledge() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const agentId = params.get('agent_id') || ''

  const [file, setFile] = useState<File | null>(null)
  const [uploads, setUploads] = useState<UploadEntry[]>([])
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Result[]>([])

  const upload = async () => {
    if (!file || !agentId) return
    const form = new FormData()
    form.append('file', file)
    await fetch(`/api/v1/agents/${agentId}/knowledge/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` },
      body: form,
    })
      .then((r) => r.json())
      .then(() => {
        setUploads((u) => [...u, { name: file.name, time: new Date().toISOString() }])
        setFile(null)
      })
      .catch(() => {})
  }

  const search = async () => {
    if (!query.trim() || !agentId) return
    const res = await fetch(`/api/v1/agents/${agentId}/knowledge/search?q=` + encodeURIComponent(query), {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then((r) => r.json())
      .catch(() => null)
    if (res) setResults(res as Result[])
  }

  return (
    <div className="p-4 space-y-4">
      <div>
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button className="ml-2 px-2 py-1 bg-blue-500 text-white rounded" onClick={upload} disabled={!file}>
          Upload
        </button>
      </div>
      {uploads.length > 0 && (
        <div>
          <h3 className="font-bold">Uploads</h3>
          <ul className="list-disc ml-6">
            {uploads.map((u, i) => (
              <li key={i}>{u.name} - {new Date(u.time).toLocaleString()}</li>
            ))}
          </ul>
        </div>
      )}
      <div>
        <input className="border p-1" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button className="ml-2 px-2 py-1 bg-green-600 text-white rounded" onClick={search}>
          Search
        </button>
      </div>
      <div>
        {results.map((r, i) => (
          <div key={i} className="border-b py-1 text-sm">
            <div className="font-bold">{r.source_file} [{r.chunk_index}]</div>
            <div>{r.text}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

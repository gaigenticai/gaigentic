import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactFlow, { Background } from 'reactflow'
import 'reactflow/dist/style.css'
import { getToken } from '../utils/auth'

interface DraftNode {
  id: string
  type: string
  label: string
  data: Record<string, unknown>
  position: { x: number; y: number }
}

interface DraftEdge {
  id: string
  source: string
  target: string
}

interface Template {
  id: string
  name: string
  description: string
  workflow_draft: { nodes: DraftNode[]; edges: DraftEdge[] }
  system_prompt?: string
}

export default function Templates() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [preview, setPreview] = useState<Template | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/v1/templates', {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then((r) => r.json())
      .then(setTemplates)
      .catch(() => {})
  }, [])

  const cloneTemplate = async (id: string) => {
    const res = await fetch(`/api/v1/templates/${id}/clone`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (res.ok) {
      const data = await res.json()
      navigate(`/Builder?agent_id=${data.agent_id}`)
    } else {
      alert('Clone failed')
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-lg font-bold">Templates</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {templates.map((t) => (
          <div key={t.id} className="border p-2 rounded space-y-2">
            <div className="font-bold">{t.name}</div>
            <div className="text-sm">{t.description}</div>
            <div className="space-x-2">
              <button className="px-2 py-1 bg-blue-500 text-white rounded" onClick={() => setPreview(t)}>
                View
              </button>
              <button className="px-2 py-1 bg-green-500 text-white rounded" onClick={() => cloneTemplate(t.id)}>
                Clone
              </button>
            </div>
          </div>
        ))}
      </div>
      {preview && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center" onClick={() => setPreview(null)}>
          <div className="bg-white p-4" onClick={(e) => e.stopPropagation()}>
            <div className="font-bold mb-2">{preview.name}</div>
            <div className="w-96 h-64">
              <ReactFlow nodes={preview.workflow_draft.nodes.map((n) => ({ id: n.id, type: n.type, position: n.position, data: { label: n.label } }))} edges={preview.workflow_draft.edges} fitView>
                <Background />
              </ReactFlow>
            </div>
            <button className="mt-2 px-2 py-1 bg-green-500 text-white rounded" onClick={() => cloneTemplate(preview.id)}>
              Clone Template
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

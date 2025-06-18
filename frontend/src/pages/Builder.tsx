import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import ReactFlow, { Background } from 'reactflow'
import 'reactflow/dist/style.css'

interface Node {
  id: string
  type: string
  label: string
  data: Record<string, unknown>
  position: { x: number; y: number }
}

interface Edge {
  id: string
  source: string
  target: string
}

interface WorkflowDraft {
  nodes: Node[]
  edges: Edge[]
}

export default function Builder() {
  const location = useLocation()
  const draft: WorkflowDraft | null = useMemo(() => {
    const params = new URLSearchParams(location.search)
    const json = params.get('draft')
    if (!json) return null
    try {
      return JSON.parse(json) as WorkflowDraft
    } catch {
      return null
    }
  }, [location.search])

  if (!draft) return <div className="p-4">No workflow draft available.</div>

  const nodes = draft.nodes.map((n) => ({ id: n.id, position: n.position, data: { label: n.label }, type: n.type }))
  const edges = draft.edges

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable={false} nodesConnectable={false} elementsSelectable={false}>
        <Background />
      </ReactFlow>
    </div>
  )
}

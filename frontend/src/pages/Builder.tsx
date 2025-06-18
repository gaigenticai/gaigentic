import { useCallback, useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import ReactFlow, {
  Background,
  Controls,
  addEdge,
  useEdgesState,
  useNodesState,
  Connection,
  NodeMouseHandler,
  Edge,
  Node,
  useReactFlow,
  ReactFlowProvider,
} from 'reactflow'
import 'reactflow/dist/style.css'
import ToolPalette from '../components/ToolPalette'

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

interface WorkflowDraft {
  nodes: DraftNode[]
  edges: DraftEdge[]
}

interface RunEvent {
  node_id: string
  status: string
}

export default function Builder() {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const draftParam = params.get('draft')
  const agentId = params.get('agent_id') || ''

  const initialDraft: WorkflowDraft | null = useMemo(() => {
    if (!draftParam) return null
    try {
      return JSON.parse(draftParam) as WorkflowDraft
    } catch {
      return null
    }
  }, [draftParam])

  const initialNodes: Node[] =
    initialDraft?.nodes.map((n) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: { label: n.label, config: n.data },
    })) || []
  const initialEdges: Edge[] = initialDraft?.edges || []

  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { project } = useReactFlow()

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [editLabel, setEditLabel] = useState('')
  const [configText, setConfigText] = useState('')
  const [runEvents, setRunEvents] = useState<RunEvent[]>([])
  const [running, setRunning] = useState(false)

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [],
  )

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      const type = event.dataTransfer.getData('application/tool')
      if (!type || !reactFlowWrapper.current) return
      const bounds = reactFlowWrapper.current.getBoundingClientRect()
      const position = project({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      })
      const id = `${type}_${Date.now()}`
      const newNode: Node = {
        id,
        type,
        position,
        data: { label: type, config: {} },
      }
      setNodes((nds) => nds.concat(newNode))
    },
    [project, setNodes],
  )

  const onNodeClick: NodeMouseHandler = (_e, node) => {
    setSelectedNodeId(node.id)
    setEditLabel(String(node.data.label ?? ''))
    setConfigText(JSON.stringify(node.data.config ?? {}, null, 2))
  }

  const saveNodeEdits = () => {
    if (!selectedNodeId) return
    let parsed: Record<string, unknown> = {}
    try {
      parsed = configText ? JSON.parse(configText) : {}
    } catch {
      alert('Config must be valid JSON')
      return
    }
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedNodeId ? { ...n, data: { label: editLabel, config: parsed } } : n,
      ),
    )
  }

  const buildDraft = (): WorkflowDraft => ({
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.type || 'default',
      label: n.data.label,
      data: n.data.config || {},
      position: n.position,
    })),
    edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
  })

  const validateDraft = (draft: WorkflowDraft) => {
    const ids = new Set(draft.nodes.map((n) => n.id))
    if (ids.size !== draft.nodes.length) return false
    return draft.edges.every((e) => ids.has(e.source) && ids.has(e.target))
  }

  const saveWorkflow = async () => {
    if (!agentId) return
    const draft = buildDraft()
    if (!validateDraft(draft)) {
      alert('Invalid workflow')
      return
    }
    await fetch(`/api/v1/agents/${agentId}/workflow`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(draft),
    })
  }

  const deployAgent = async () => {
    if (!agentId) return
    await fetch(`/api/v1/agents/${agentId}/deploy`, { method: 'POST' })
  }

  const runLive = () => {
    if (!agentId) return
    setRunEvents([])
    setRunning(true)
    const ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/agents/${agentId}/run?tenant_id=00000000-0000-0000-0000-000000000001`)
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data)
      if (data.status === 'started') return
      if (data.status === 'complete') {
        setRunning(false)
        ws.close()
        return
      }
      setRunEvents((e) => [...e, data])
    }
  }

  if (!initialDraft && nodes.length === 0) {
    return <div className="p-4">No workflow draft available.</div>
  }

  const selectedNode = nodes.find((n) => n.id === selectedNodeId)

  return (
    <ReactFlowProvider>
      <div className="flex h-screen" ref={reactFlowWrapper} onDrop={onDrop} onDragOver={onDragOver}>
        <ToolPalette />
        <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
        <div className="absolute bottom-2 left-2 space-x-2">
          <button className="px-2 py-1 bg-blue-500 text-white rounded" onClick={saveWorkflow} disabled={!agentId}>
            Save Workflow
          </button>
          <button className="px-2 py-1 bg-green-500 text-white rounded" onClick={deployAgent} disabled={!agentId}>
            Deploy Agent
          </button>
          <button className="px-2 py-1 bg-purple-500 text-white rounded" onClick={runLive} disabled={!agentId || running}>
            Run with Live Status
          </button>
        </div>
        {selectedNode && (
          <div className="absolute top-2 right-2 w-64 bg-white border p-2 text-sm space-y-2">
            <div className="font-bold">Edit Node {selectedNode.id}</div>
            <label className="block">
              Label
              <input
                className="w-full border p-1"
                value={editLabel}
                onChange={(e) => setEditLabel(e.target.value)}
              />
            </label>
            <label className="block">
              Config
              <textarea
                className="w-full border p-1 h-24"
                value={configText}
                onChange={(e) => setConfigText(e.target.value)}
              />
            </label>
            <button className="px-2 py-1 bg-gray-200 rounded" onClick={saveNodeEdits}>
              Apply
            </button>
          </div>
        )}
        {running && (
          <div className="absolute top-2 left-2 bg-white border p-2 text-sm max-h-40 overflow-y-auto">
            {runEvents.map((e, i) => (
              <div key={i}>{e.node_id}: {e.status}</div>
            ))}
          </div>
        )}
      </div>
    </div>
    </ReactFlowProvider>
  )
}

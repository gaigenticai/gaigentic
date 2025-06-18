import React, { useEffect, useState } from 'react'
import { getToken } from '../utils/auth'

const baseTools = [
  'kyc_verification',
  'fraud_detection',
  'document_analysis',
  'cash_forecast',
  'recommend_action',
]

export default function ToolPalette() {
  const [plugins, setPlugins] = useState<{ id: string; name: string }[]>([])

  useEffect(() => {
    fetch('/api/v1/plugins', {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then((r) => r.json())
      .then(setPlugins)
      .catch(() => {})
  }, [])
  const onDragStart = (event: React.DragEvent<HTMLDivElement>, tool: string) => {
    event.dataTransfer.setData('application/tool', tool)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="p-2 space-y-2 w-48 bg-gray-100 border-r" data-testid="tool-palette">
      {baseTools.map((t) => (
        <div
          key={t}
          draggable
          onDragStart={(e) => onDragStart(e, t)}
          className="p-1 bg-white rounded shadow cursor-grab text-sm text-center"
        >
          {t}
        </div>
      ))}
      {plugins.map((p) => (
        <div
          key={p.id}
          draggable
          onDragStart={(e) => onDragStart(e, `plugin:${p.id}`)}
          className="p-1 bg-white rounded shadow cursor-grab text-sm text-center"
        >
          {p.name}
        </div>
      ))}
    </div>
  )
}

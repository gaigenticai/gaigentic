import React from 'react'

const tools = [
  'kyc_verification',
  'fraud_detection',
  'document_analysis',
  'cash_forecast',
  'recommend_action',
]

export default function ToolPalette() {
  const onDragStart = (event: React.DragEvent<HTMLDivElement>, tool: string) => {
    event.dataTransfer.setData('application/tool', tool)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="p-2 space-y-2 w-48 bg-gray-100 border-r" data-testid="tool-palette">
      {tools.map((t) => (
        <div
          key={t}
          draggable
          onDragStart={(e) => onDragStart(e, t)}
          className="p-1 bg-white rounded shadow cursor-grab text-sm text-center"
        >
          {t}
        </div>
      ))}
    </div>
  )
}

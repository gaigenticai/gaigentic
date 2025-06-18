import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getToken } from '../utils/auth'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}



export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streamingText, setStreamingText] = useState('')
  const [typing, setTyping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMsg: Message = { role: 'user', content: input, timestamp: new Date().toISOString() }
    const history = [...messages, userMsg]
    setMessages(history)
    setInput('')
    setStreamingText('')
    setTyping(true)
    let full = ''
    const ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/chat?token=${getToken() ?? ''}`)
    ws.onopen = () => {
      ws.send(JSON.stringify({ messages: history }))
    }
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data)
      if (data.token) {
        full += data.token + ' '
        setStreamingText(full)
      } else if (data.status === 'complete') {
        const assistantMsg: Message = {
          role: 'assistant',
          content: full.trim(),
          timestamp: new Date().toISOString(),
        }
        setMessages([...history, assistantMsg])
        setTyping(false)
        ws.close()
        if (data.workflow_draft) {
          navigate('/Builder?draft=' + encodeURIComponent(JSON.stringify(data.workflow_draft)))
        }
      }
    }
  }

  return (
    <div className="flex flex-col h-screen p-4">
      <div className="flex-1 overflow-y-auto space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className="inline-block bg-gray-200 rounded px-2 py-1 max-w-md">
              {m.content}
            </span>
          </div>
        ))}
        {typing && (
          <div className="text-left">
            <span className="inline-block bg-gray-200 rounded px-2 py-1 max-w-md">
              {streamingText || '...'}
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="mt-2 flex">
        <input
          className="flex-1 border rounded px-2 py-1"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button className="ml-2 px-3 py-1 bg-blue-600 text-white rounded" onClick={sendMessage}>
          Send
        </button>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { setToken } from '../utils/auth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const submit = async () => {
    const res = await fetch('/api/v1/auth/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (res.ok) {
      const data = await res.json()
      setToken(data.access_token)
      navigate('/')
    } else {
      alert('Login failed')
    }
  }

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-bold">Login</h2>
      <input className="border p-1 block" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <input className="border p-1 block" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
      <button className="px-2 py-1 bg-blue-600 text-white" onClick={submit}>Login</button>
      <div>
        No account? <Link to="/register" className="text-blue-600">Register</Link>
      </div>
    </div>
  )
}

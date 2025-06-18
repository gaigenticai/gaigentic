import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { setToken } from '../utils/auth'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [tenant, setTenant] = useState('')
  const navigate = useNavigate()

  const submit = async () => {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, tenant_name: tenant })
    })
    if (res.ok) {
      const data = await res.json()
      setToken(data.access_token)
      navigate('/')
    } else {
      alert('Registration failed')
    }
  }

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-bold">Register</h2>
      <input className="border p-1 block" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
      <input className="border p-1 block" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
      <input className="border p-1 block" placeholder="Tenant" value={tenant} onChange={e => setTenant(e.target.value)} />
      <button className="px-2 py-1 bg-blue-600 text-white" onClick={submit}>Register</button>
      <div>
        <Link to="/login" className="text-blue-600">Back to login</Link>
      </div>
    </div>
  )
}

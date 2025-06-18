import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Chat from './pages/Chat'
import Builder from './pages/Builder'
import Monitor from './pages/Monitor'
import Templates from './pages/Templates'
import Login from './pages/Login'
import Register from './pages/Register'
import { getToken, clearToken } from './utils/auth'

export default function App() {
  const token = getToken()

  const logout = () => {
    clearToken()
    window.location.href = '/login'
  }

  return (
    <BrowserRouter>
      <nav className="p-2 bg-gray-100 flex space-x-4">
        <Link to="/" className="text-blue-600">Chat</Link>
        <Link to="/Builder" className="text-blue-600">Builder</Link>
        <Link to="/Templates" className="text-blue-600">Templates</Link>
        <Link to="/Monitor" className="text-blue-600">Monitor</Link>
        {token ? (
          <button onClick={logout} className="text-blue-600">Logout</button>
        ) : (
          <Link to="/login" className="text-blue-600">Login</Link>
        )}
      </nav>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/Builder" element={<Builder />} />
        <Route path="/Templates" element={<Templates />} />
        <Route path="/Monitor" element={<Monitor />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </BrowserRouter>
  )
}

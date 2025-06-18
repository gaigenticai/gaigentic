import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Chat from './pages/Chat'
import Builder from './pages/Builder'
import Monitor from './pages/Monitor'
import Templates from './pages/Templates'
import Knowledge from './pages/Knowledge'
import Plugins from './pages/Plugins'
import TestPlayground from './pages/TestPlayground'
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
        <Link to="/Knowledge" className="text-blue-600">Knowledge</Link>
        <Link to="/Plugins" className="text-blue-600">Plugins</Link>
        <Link to="/Tests" className="text-blue-600">Tests</Link>
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
        <Route path="/Knowledge" element={<Knowledge />} />
        <Route path="/Plugins" element={<Plugins />} />
        <Route path="/Tests" element={<TestPlayground />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </BrowserRouter>
  )
}

import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Chat from './pages/Chat'
import Builder from './pages/Builder'
import Monitor from './pages/Monitor'

export default function App() {
  return (
    <BrowserRouter>
      <nav className="p-2 bg-gray-100 flex space-x-4">
        <Link to="/" className="text-blue-600">Chat</Link>
        <Link to="/Builder" className="text-blue-600">Builder</Link>
        <Link to="/Monitor" className="text-blue-600">Monitor</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Chat />} />
        <Route path="/Builder" element={<Builder />} />
        <Route path="/Monitor" element={<Monitor />} />
      </Routes>
    </BrowserRouter>
  )
}

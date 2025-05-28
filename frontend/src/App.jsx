// === frontend/src/App.jsx ===
import React, { useState } from 'react'
import DashboardView from './components/DashboardView'
import PostsView from './components/PostView'

function App() {
  const [view, setView] = useState('dashboard')
  const [timeRange, setTimeRange] = useState('24h')

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-slate-900 to-sky-950 text-white">
      <div className="flex justify-between items-center px-6 py-4 shadow bg-slate-950">
        <h1 className="text-2xl font-extrabold tracking-wide text-cyan-400 flex items-center gap-2">
          📊 Reddit sentiment analyzer
        </h1>
        <div className="flex items-center gap-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-slate-800 text-white px-3 py-1 rounded border border-slate-600 shadow"
          >
            <option value="1h">Last 1 hour</option>
            <option value="3h">Last 3 hours</option>
            <option value="24h">Last 24 hours</option>
          </select>
          <button onClick={() => setView('dashboard')} className={`px-3 py-1 rounded ${view === 'dashboard' ? 'bg-cyan-600 text-white' : 'bg-slate-700'}`}>
            Dashboard
          </button>
          <button onClick={() => setView('posts')} className={`px-3 py-1 rounded ${view === 'posts' ? 'bg-cyan-600 text-white' : 'bg-slate-700'}`}>
            Posts
          </button>
        </div>
      </div>

      <div className="p-6">
        {view === 'dashboard' ? <DashboardView timeRange={timeRange} /> : <PostsView timeRange={timeRange} />}
      </div>
    </div>
  )
}

export default App

// === frontend/src/components/PostsView.jsx ===
import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getTimeRange } from '../utils/timeUtils'

function PostsView({ timeRange }) {
  const [posts, setPosts] = useState([])

  useEffect(() => {
    const { from, to } = getTimeRange(timeRange)
    axios.get(`/api/posts?from=${from}&to=${to}`).then(res => setPosts(res.data))
  }, [timeRange])

  return (
      <div className="min-h-screen bg-black text-white flex flex-col items-center justify-start p-6">
        <div className="w-full max-w-3xl space-y-6">
          {posts.map(post => (
              <div key={post.id}
                   className="bg-gradient-to-r from-slate-900 to-sky-900 p-6 rounded-lg shadow-lg border border-sky-700">
                <h3 className="text-xl font-semibold text-cyan-300">{post.title}</h3>
                <p className="text-slate-300 mt-2">💬 Score: {post.score}</p>
                <p className="text-sm text-cyan-400">Sentiment: {post.sentiment}</p>
              </div>
          ))}
        </div>
      </div>

  )
}

export default PostsView

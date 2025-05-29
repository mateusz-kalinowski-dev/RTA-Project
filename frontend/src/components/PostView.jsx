// === frontend/src/components/PostsView.jsx ===
import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getTimeRange } from '../utils/timeUtils'

function PostsView({ timeRange }) {
  const [posts, setPosts] = useState([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const [selectedSubreddit, setSelectedSubreddit] = useState('all')
  const [availableSubreddits, setAvailableSubreddits] = useState([])

  const loadPosts = async (currentPage) => {
    const { from, to } = getTimeRange(timeRange)
    setLoading(true)
    try {
      const subredditQuery = selectedSubreddit !== 'all' ? `&subreddit=${selectedSubreddit}` : ''
      const res = await axios.get(`/api/posts?from=${from}&to=${to}&limit=5&skip=${(currentPage - 1) * 15}${subredditQuery}`)
      const newPosts = res.data.map(post => ({
        ...post,
        topComments: post.top_comments || []
      }))

      setPosts(prev => [...prev, ...newPosts])
      if (res.data.length < 5) setHasMore(false)
    } catch (err) {
      console.error('Failed to load posts', err)
    } finally {
      setLoading(false)
      setInitialLoading(false)
    }
  }

  useEffect(() => {
    axios.get('/api/subreddits')
      .then(res => setAvailableSubreddits(['all', ...res.data]))
  }, [])

  useEffect(() => {
    setPosts([])
    setPage(1)
    setHasMore(true)
    setInitialLoading(true)
  }, [timeRange, selectedSubreddit])

  useEffect(() => {
    loadPosts(page)
  }, [page, timeRange, selectedSubreddit])

  const loadNextPage = () => {
    if (!loading && hasMore) {
      setPage(prev => prev + 1)
    }
  }

  return (
    <>
      {initialLoading && (
        <div className="w-full text-center text-white py-6">
          <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          Loading posts...
        </div>
      )}

      {!initialLoading && (
        <div className="min-h-screen bg-black text-white flex flex-col items-center justify-start p-6">
          <div className="w-full max-w-3xl space-y-6">
            <div className="flex items-center gap-4">
              <label className="text-white">Subreddit:</label>
              <select
                value={selectedSubreddit}
                onChange={(e) => setSelectedSubreddit(e.target.value)}
                className="bg-slate-700 text-white px-3 py-1 rounded border border-slate-600"
              >
                {availableSubreddits.map(sub => (
                  <option key={sub} value={sub}>{sub}</option>
                ))}
              </select>
            </div>

            {posts.map((post, i) => (
              <div key={post.id || i} className="bg-gradient-to-r from-slate-900 to-sky-900 p-6 rounded-lg shadow-lg border border-sky-700">
                <h3 className="text-xl font-semibold text-cyan-300">{post.title}</h3>
                <p className="text-slate-300 mt-2">💬 Score: {post.score}</p>
                <p className="text-sm text-cyan-400 mb-2">Sentiment: {post.sentiment}</p>
                {post.topComments?.length > 0 && (
                  <ul className="space-y-2 mt-2">
                    {post.topComments.map((comment, idx) => (
                      <li key={idx} className="bg-slate-800 p-3 rounded">
                        <div className="text-white text-sm">{comment.text}</div>
                        <div className="text-slate-400 text-xs">Score: {comment.score} | Sentiment: {comment.sentiment}</div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}

            {hasMore && (
              <button
                onClick={loadNextPage}
                className="mt-4 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded text-white disabled:opacity-50"
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            )}
          </div>
        </div>
      )}
    </>
  )
}

export default PostsView

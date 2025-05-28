// === frontend/src/components/DashboardView.jsx ===
import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { getTimeRange } from '../utils/timeUtils'
import {
  PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  LineChart, Line, Legend, ResponsiveContainer
} from 'recharts'

const COLORS = ['#0ea5e9', '#f43f5e']

function groupByHour(data) {
  const grouped = {}
  data.forEach(item => {
    const hour = new Date(item.created_utc).toISOString().slice(0, 13) + ':00'
    if (!grouped[hour]) grouped[hour] = { time: hour, POSITIVE: 0, NEGATIVE: 0 }
    const sentiment = item.sentiment
    if (sentiment === 'POSITIVE' || sentiment === 'NEGATIVE') {
      grouped[hour][sentiment] += 1
    }
  })
  return Object.values(grouped).sort((a, b) => new Date(a.time) - new Date(b.time))
}

function DashboardView({ timeRange }) {
  const [posts, setPosts] = useState([])
  const [comments, setComments] = useState([])
  const [summary, setSummary] = useState(null)
  const [topPosts, setTopPosts] = useState([])
  const [selectedPostSentiment, setSelectedPostSentiment] = useState('POSITIVE')
  const [selectedCommentSentiment, setSelectedCommentSentiment] = useState('POSITIVE')
  const [selectedSubreddit, setSelectedSubreddit] = useState('all')
  const [availableSubreddits, setAvailableSubreddits] = useState([])
  const [topCommentsByPostId, setTopCommentsByPostId] = useState({})

  useEffect(() => {
    const {from, to} = getTimeRange(timeRange)
    const subredditQuery = selectedSubreddit !== 'all' ? `&subreddit=${selectedSubreddit}` : ''

    axios.get(`/api/posts?from=${from}&to=${to}${subredditQuery}`).then(res => setPosts(res.data))
    axios.get(`/api/comments?from=${from}&to=${to}${subredditQuery}`).then(res => setComments(res.data))
    axios.get(`/api/summary?from=${from}&to=${to}${subredditQuery}`).then(res => setSummary(res.data))
    axios.get(`/api/top-posts?from=${from}&to=${to}${subredditQuery}`).then(res => setTopPosts(res.data))
  }, [timeRange, selectedSubreddit])

  useEffect(() => {
    axios.get('/api/subreddits')
        .then(res => {
          setAvailableSubreddits(['all', ...res.data])
        })
  }, [])

  const sentimentPosts = summary ? Object.entries(summary.sentiment_distribution_by_posts)
      .filter(([label]) => label !== 'NEUTRAL')
      .map(([label, value]) => ({name: label, value})) : []

  const sentimentComments = summary ? Object.entries(summary.sentiment_distribution_by_comments)
    .filter(([label]) => label !== 'NEUTRAL')
    .map(([label, value]) => ({ name: label, value })) : []

  const postData = groupByHour(posts)
  const commentData = groupByHour(comments)

  const fetchTopComments = async (postId) => {
    if (!postId) return

    if (topCommentsByPostId[postId]) {
      const updated = { ...topCommentsByPostId }
      delete updated[postId]
      setTopCommentsByPostId(updated)
      return
    }

    try {
      const res = await axios.get(`/api/posts/${postId}`)
      const seen = new Set()
      const top5 = res.data.comments
        .filter(c => {
          const id = c.raw_data?.id
          if (!id || seen.has(id)) return false
          seen.add(id)
          return true
        })
        .sort((a, b) => (b.raw_data.score || 0) - (a.raw_data.score || 0))
        .slice(0, 5)
        .map(c => ({
          text: c.raw_data.text,
          score: c.raw_data.score,
          sentiment: c.sentiment?.label
        }))
      setTopCommentsByPostId(prev => ({ ...prev, [postId]: top5 }))
    } catch (err) {
      console.error('Error loading comments', err)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="col-span-2 flex flex-wrap gap-4 items-center">
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

      <div className="bg-slate-800 p-6 rounded shadow">
        <h2 className="text-lg font-bold text-cyan-300 mb-4">Post Sentiment (Pie)</h2>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={sentimentPosts} dataKey="value" nameKey="name" outerRadius={100} label>
              {sentimentPosts.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-slate-800 p-6 rounded shadow">
        <h2 className="text-lg font-bold text-cyan-300 mb-4">Comment Sentiment (Bar)</h2>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={sentimentComments}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#0ea5e9" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="col-span-2 flex flex-col lg:flex-row gap-6">
        <div className="bg-slate-800 p-6 rounded shadow w-full">
          <h2 className="text-lg font-bold text-cyan-300 mb-4">Posts by Sentiment Over Time</h2>
          <select value={selectedPostSentiment} onChange={(e) => setSelectedPostSentiment(e.target.value)} className="mb-2 bg-slate-700 text-white px-2 py-1 rounded">
            <option value="POSITIVE">Positive</option>
            <option value="NEGATIVE">Negative</option>
          </select>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={postData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={selectedPostSentiment} stroke="#0ea5e9" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-800 p-6 rounded shadow w-full">
          <h2 className="text-lg font-bold text-cyan-300 mb-4">Comments by Sentiment Over Time</h2>
          <select value={selectedCommentSentiment} onChange={(e) => setSelectedCommentSentiment(e.target.value)} className="mb-2 bg-slate-700 text-white px-2 py-1 rounded">
            <option value="POSITIVE">Positive</option>
            <option value="NEGATIVE">Negative</option>
          </select>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={commentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={selectedCommentSentiment} stroke="#f472b6" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="col-span-2 bg-slate-800 p-6 rounded shadow">
        <h2 className="text-lg font-bold text-cyan-300 mb-4">Top 10 Posts</h2>
        <ul className="space-y-4">
          {topPosts.map((post, i) => {
            const postId = post.id || post.raw_data?.id
            return (
              <li key={postId || post.title + i} className="bg-slate-700 p-3 rounded">
                <div className="font-semibold text-cyan-400">[{post.sentiment}] {post.title}</div>
                <div className="text-sm text-slate-300 mb-2">Score: {post.score}</div>
                <button
                  onClick={() => fetchTopComments(postId)}
                  className="bg-cyan-600 hover:bg-cyan-700 text-white px-2 py-1 text-sm rounded"
                >
                  {topCommentsByPostId[postId] ? 'Hide Top Comments' : 'Show Top Comments'}
                </button>
                {topCommentsByPostId[postId] && (
                  <ul className="mt-2 space-y-1 text-sm">
                    {topCommentsByPostId[postId].map((comment, idx) => (
                      <li key={idx} className="bg-slate-600 p-2 rounded">
                        <div className="text-white">{comment.text}</div>
                        <div className="text-slate-300">Score: {comment.score} | Sentiment: {comment.sentiment}</div>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

export default DashboardView

'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { toast, Toaster } from 'react-hot-toast'

const API = 'http://localhost:8000/api'

// ─── Types ───────────────────────────────────────────────────
interface Content { id: number; title: string; platform: string; created_at: string; word_count: number }
interface SearchResult { id: number; title: string; content_preview: string; similarity: number; platform: string }

// ─── Reusable Components ─────────────────────────────────────
const Badge = ({ children, color = 'purple' }: { children: React.ReactNode; color?: string }) => (
  <span className={`px-2 py-0.5 text-xs rounded-full bg-${color}-500/15 text-${color}-400 border border-${color}-500/20`}>{children}</span>
)

const Card = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`glass rounded-2xl p-5 hover-lift ${className}`}>{children}</div>
)

const GlowDot = ({ color, size = 'w-2 h-2' }: { color: string; size?: string }) => (
  <span className="relative flex">
    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${color} opacity-40`} />
    <span className={`relative inline-flex rounded-full ${size} ${color}`} />
  </span>
)

const MiniBar = ({ value, max, color = 'from-purple-500 to-pink-500' }: { value: number; max: number; color?: string }) => (
  <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
    <div className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-1000`}
      style={{ width: `${Math.min(100, (value / Math.max(max, 1)) * 100)}%` }} />
  </div>
)

const ScoreRing = ({ score, size = 130 }: { score: number; size?: number }) => {
  const r = size / 2 - 12; const circ = 2 * Math.PI * r; const offset = circ - (score / 100) * circ
  const color = score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : score >= 40 ? '#f97316' : '#ef4444'
  return (
    <svg width={size} height={size} className="transform -rotate-90 drop-shadow-lg">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="10"
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" className="transition-all duration-1000 ease-out" />
      <text x={size/2} y={size/2+10} textAnchor="middle" fill="white" fontSize="32" fontWeight="bold"
        className="rotate-90" transform={`rotate(90 ${size/2} ${size/2})`}>{score}</text>
    </svg>
  )
}

const EmptyState = ({ icon, text }: { icon: string; text: string }) => (
  <div className="text-center py-16 opacity-50">
    <div className="text-5xl mb-3">{icon}</div>
    <p className="text-gray-500">{text}</p>
  </div>
)

const LoadingPulse = ({ text = 'Loading...' }: { text?: string }) => (
  <div className="flex items-center justify-center gap-3 py-16">
    <div className="flex gap-1">
      {[0,1,2].map(i => (
        <div key={i} className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
      ))}
    </div>
    <span className="text-gray-400 text-sm">{text}</span>
  </div>
)

// ─── Main App ────────────────────────────────────────────────
export default function Home() {
  const [activeTab, setActiveTab] = useState('upload')
  const [contentList, setContentList] = useState<Content[]>([])
  const [stats, setStats] = useState<any>({ total_content: 0 })

  // Upload
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadContent, setUploadContent] = useState('')
  const [uploadPlatform, setUploadPlatform] = useState('blog')
  const [uploading, setUploading] = useState(false)
  const [bulkText, setBulkText] = useState('')
  const [bulkUploading, setBulkUploading] = useState(false)
  const [showBulk, setShowBulk] = useState(false)
  // Search
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  // Analyze
  const [draftContent, setDraftContent] = useState('')
  const [checkResult, setCheckResult] = useState<any>(null)
  const [checking, setChecking] = useState(false)
  const [useKG, setUseKG] = useState(true)
  const [contradictionResult, setContradictionResult] = useState<any>(null)
  const [checkingContradiction, setCheckingContradiction] = useState(false)
  const [referencesResult, setReferencesResult] = useState<any>(null)
  const [checkingReferences, setCheckingReferences] = useState(false)
  const [toneResult, setToneResult] = useState<any>(null)
  const [checkingTone, setCheckingTone] = useState(false)
  // Adapt
  const [adaptContent, setAdaptContent] = useState('')
  const [adaptations, setAdaptations] = useState<any>(null)
  const [adapting, setAdapting] = useState(false)
  const [copiedPlatform, setCopiedPlatform] = useState('')
  // Analytics
  const [analytics, setAnalytics] = useState<any>(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(false)
  // Insights
  const [healthScore, setHealthScore] = useState<any>(null)
  const [loadingHealth, setLoadingHealth] = useState(false)
  const [contentGaps, setContentGaps] = useState<any>(null)
  const [loadingGaps, setLoadingGaps] = useState(false)
  // Graph
  const [graphData, setGraphData] = useState<any>(null)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [graphDensity, setGraphDensity] = useState(50)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  // Calendar
  const [calendarData, setCalendarData] = useState<any>(null)
  const [loadingCalendar, setLoadingCalendar] = useState(false)
  // Personas
  const [personasData, setPersonasData] = useState<any>(null)
  const [loadingPersonas, setLoadingPersonas] = useState(false)
  // SEO
  const [seoContent, setSeoContent] = useState('')
  const [seoTitle, setSeoTitle] = useState('')
  const [seoKeyword, setSeoKeyword] = useState('')
  const [seoResult, setSeoResult] = useState<any>(null)
  const [analyzingSeo, setAnalyzingSeo] = useState(false)
  // Versioning
  const [selectedContentId, setSelectedContentId] = useState<number | null>(null)
  const [versions, setVersions] = useState<any>(null)
  const [loadingVersions, setLoadingVersions] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editContent, setEditContent] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => { loadContent(); loadStats() }, [])

  // ─── API Helpers ─────────────────────────────────────────
  const api = async (path: string, opts?: RequestInit) => {
    const res = await fetch(`${API}${path}`, opts)
    if (!res.ok) throw new Error(`${res.status}`)
    return res.json()
  }
  const post = (path: string, body: any) => api(path, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
  })

  const loadContent = async () => { try { setContentList(await api('/content/list')) } catch {} }
  const loadStats = async () => { try { setStats(await api('/stats')) } catch {} }

  const handleDeleteContent = async (id: number) => {
    if (!confirm('Delete this content?')) return
    try { await api(`/content/${id}`, { method: 'DELETE' }); toast.success('Deleted'); loadContent(); loadStats(); invalidateCaches() }
    catch { toast.error('Delete failed') }
  }
  const handleClearAll = async () => {
    if (!confirm('Delete ALL content? This cannot be undone.')) return
    if (!confirm('Are you absolutely sure?')) return
    try { await api('/content/clear-all', { method: 'DELETE' }); toast.success('All cleared'); setContentList([]); loadStats(); invalidateCaches() }
    catch { toast.error('Clear failed') }
  }

  const invalidateCaches = () => {
    setAnalytics(null); setHealthScore(null); setContentGaps(null); setGraphData(null)
    setCalendarData(null); setPersonasData(null); setVersions(null)
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault(); setUploading(true)
    try {
      await post('/content/upload', { title: uploadTitle, content: uploadContent, platform: uploadPlatform, tags: [] })
      toast.success('Uploaded!'); setUploadTitle(''); setUploadContent(''); loadContent(); loadStats(); invalidateCaches()
    } catch { toast.error('Upload failed') }
    finally { setUploading(false) }
  }

  const handleBulkUpload = async () => {
    if (!bulkText.trim()) return; setBulkUploading(true)
    try {
      const pieces = bulkText.split('---').map(p => p.trim()).filter(Boolean)
      const items = pieces.map((p, i) => {
        const lines = p.split('\n'); const title = lines[0].replace(/^#\s*/, '').trim() || `Content ${i+1}`
        return { title, content: lines.slice(1).join('\n').trim() || p, platform: 'blog', tags: [] }
      })
      const data = await post('/content/bulk-upload', items)
      toast.success(`Uploaded ${data.uploaded} pieces!`); setBulkText(''); setShowBulk(false); loadContent(); loadStats(); invalidateCaches()
    } catch { toast.error('Bulk upload failed') }
    finally { setBulkUploading(false) }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault(); setSearching(true)
    try { const data = await post('/search', { query: searchQuery, limit: 5 }); setSearchResults(data); if (!data.length) toast('No results', { icon: '🔍' }) }
    catch { toast.error('Search failed') }
    finally { setSearching(false) }
  }

  const handleCheck = async (e: React.FormEvent) => {
    e.preventDefault(); setChecking(true); setContradictionResult(null); setReferencesResult(null); setToneResult(null)
    try {
      const data = await post(useKG ? '/check-repetition-graph' : '/check-repetition', { content: draftContent })
      setCheckResult(data); data.is_repetition ? toast.error(data.message) : toast.success('No repetition!')
    } catch { toast.error('Check failed') }
    finally { setChecking(false) }
  }

  const handleContradiction = async () => {
    if (!draftContent.trim()) return; setCheckingContradiction(true)
    try { const d = await post('/check-contradiction', { content: draftContent }); setContradictionResult(d); d.has_contradictions ? toast.error(d.message) : toast.success(d.message) }
    catch { toast.error('Failed') } finally { setCheckingContradiction(false) }
  }
  const handleReferences = async () => {
    if (!draftContent.trim()) return; setCheckingReferences(true)
    try { setReferencesResult(await post('/smart-references', { content: draftContent })) }
    catch { toast.error('Failed') } finally { setCheckingReferences(false) }
  }
  const handleTone = async () => {
    if (!draftContent.trim()) return; setCheckingTone(true)
    try { setToneResult(await post('/analyze-tone', { content: draftContent })) }
    catch { toast.error('Failed') } finally { setCheckingTone(false) }
  }

  const handleAdapt = async (e: React.FormEvent) => {
    e.preventDefault(); setAdapting(true)
    try { setAdaptations(await post('/adapt-platform', { content: adaptContent })); toast.success('Generated!') }
    catch { toast.error('Failed') } finally { setAdapting(false) }
  }

  const copy = (text: string, name: string) => {
    navigator.clipboard.writeText(text); setCopiedPlatform(name); toast.success(`${name} copied!`)
    setTimeout(() => setCopiedPlatform(''), 2000)
  }

  const loadAnalytics = async () => { setLoadingAnalytics(true); try { setAnalytics(await api('/analytics/dashboard')) } catch {} finally { setLoadingAnalytics(false) } }
  const loadHealth = async () => { setLoadingHealth(true); try { setHealthScore(await api('/content-health')) } catch {} finally { setLoadingHealth(false) } }
  const loadGaps = async () => { setLoadingGaps(true); try { setContentGaps(await api('/content-gaps')) } catch {} finally { setLoadingGaps(false) } }
  const loadGraph = async (maxNodes = 50) => { setLoadingGraph(true); try { setGraphData(await api(`/knowledge/visualization?max_nodes=${maxNodes}`)) } catch {} finally { setLoadingGraph(false) } }

  const loadCalendar = async () => { setLoadingCalendar(true); try { setCalendarData(await api('/content-calendar')) } catch {} finally { setLoadingCalendar(false) } }
  const loadPersonas = async () => { setLoadingPersonas(true); try { setPersonasData(await api('/audience-personas')) } catch {} finally { setLoadingPersonas(false) } }
  const handleSeo = async (e: React.FormEvent) => {
    e.preventDefault(); setAnalyzingSeo(true)
    try { setSeoResult(await post('/seo-analyze', { content: seoContent, title: seoTitle, target_keyword: seoKeyword })); toast.success('SEO analyzed!') }
    catch { toast.error('SEO analysis failed') } finally { setAnalyzingSeo(false) }
  }
  const loadVersions = async (id: number) => {
    setSelectedContentId(id); setLoadingVersions(true)
    try {
      const [vData, cData] = await Promise.all([
        api(`/content/${id}/versions`),
        api(`/content/${id}`)
      ])
      setVersions(vData)
      setEditTitle(cData.title || '')
      setEditContent(cData.content || '')
    } catch {} finally { setLoadingVersions(false) }
  }
  const handleSaveVersion = async () => {
    if (!selectedContentId || !editContent.trim()) return; setSaving(true)
    try {
      const data = await post(`/content/${selectedContentId}/update`, { title: editTitle, content: editContent })
      toast.success(data.message); loadVersions(selectedContentId); loadContent(); loadStats(); invalidateCaches()
    } catch { toast.error('Save failed') } finally { setSaving(false) }
  }

  useEffect(() => {
    if (activeTab === 'analytics' && !analytics) loadAnalytics()
    if (activeTab === 'insights') { if (!healthScore) loadHealth(); if (!contentGaps) loadGaps() }
    if (activeTab === 'graph' && !graphData && !loadingGraph) loadGraph(graphDensity)
    if (activeTab === 'calendar' && !calendarData) loadCalendar()
    if (activeTab === 'personas' && !personasData) loadPersonas()
  }, [activeTab, analytics, healthScore, contentGaps, graphData, calendarData, personasData])

  // ─── Interactive Graph ──────────────────────────────────────
  const graphPosRef = useRef<Record<string, { x: number; y: number }>>({})
  const graphTransform = useRef({ ox: 0, oy: 0, scale: 1 })
  const [hoveredNode, setHoveredNode] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const dragRef = useRef<{ nodeId: string | null; panning: boolean; lastX: number; lastY: number }>({ nodeId: null, panning: false, lastX: 0, lastY: 0 })

  const graphColors: Record<string, string> = {
    entity: '#a855f7', topic: '#ec4899', content: '#3b82f6',
    concept: '#a855f7', tool: '#f59e0b', person: '#10b981', organization: '#06b6d4'
  }

  const layoutGraph = useCallback(() => {
    if (!graphData?.nodes?.length || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    const w = rect.width || 800, h = rect.height || 500
    const pos: Record<string, { x: number; y: number; vx: number; vy: number }> = {}
    graphData.nodes.forEach((n: any) => {
      pos[n.id] = { x: w/2 + (Math.random()-0.5)*w*0.6, y: h/2 + (Math.random()-0.5)*h*0.6, vx: 0, vy: 0 }
    })
    for (let iter = 0; iter < 120; iter++) {
      const ns = graphData.nodes
      for (let i = 0; i < ns.length; i++) for (let j = i+1; j < ns.length; j++) {
        const a = pos[ns[i].id], b = pos[ns[j].id]
        let dx = b.x-a.x, dy = b.y-a.y, d = Math.sqrt(dx*dx+dy*dy)||1, f = 1200/(d*d)
        a.vx -= (dx/d)*f; a.vy -= (dy/d)*f; b.vx += (dx/d)*f; b.vy += (dy/d)*f
      }
      graphData.links.forEach((l: any) => {
        const a = pos[l.source], b = pos[l.target]; if (!a||!b) return
        let dx = b.x-a.x, dy = b.y-a.y, d = Math.sqrt(dx*dx+dy*dy)||1, f = (d-100)*0.01
        a.vx += (dx/d)*f; a.vy += (dy/d)*f; b.vx -= (dx/d)*f; b.vy -= (dy/d)*f
      })
      Object.values(pos).forEach(p => {
        p.vx += (w/2-p.x)*0.001; p.vy += (h/2-p.y)*0.001
        p.x += p.vx*0.3; p.y += p.vy*0.3; p.vx *= 0.78; p.vy *= 0.78
        p.x = Math.max(50, Math.min(w-50, p.x)); p.y = Math.max(50, Math.min(h-50, p.y))
      })
    }
    const result: Record<string, { x: number; y: number }> = {}
    Object.entries(pos).forEach(([id, p]) => { result[id] = { x: p.x, y: p.y } })
    graphPosRef.current = result
  }, [graphData])

  const renderGraph = useCallback(() => {
    if (!canvasRef.current || !graphData?.nodes?.length) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const rect = canvas.getBoundingClientRect()
    const dpr = window.devicePixelRatio || 2
    const w = rect.width || 800, h = rect.height || 500
    if (w < 10) return
    canvas.width = w * dpr; canvas.height = h * dpr
    ctx.scale(dpr, dpr)
    const pos = graphPosRef.current
    const t = graphTransform.current

    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h)
    ctx.save()
    ctx.translate(t.ox, t.oy)
    ctx.scale(t.scale, t.scale)

    const nodeColor: Record<string, string> = {}
    graphData.nodes.forEach((n: any) => { nodeColor[n.id] = graphColors[n.type] || graphColors[n.group] || '#666' })

    // Connected nodes for highlight
    const connectedTo = new Set<string>()
    if (selectedNode || hoveredNode) {
      const focus = selectedNode || hoveredNode
      graphData.links.forEach((l: any) => {
        if (l.source === focus) connectedTo.add(l.target)
        if (l.target === focus) connectedTo.add(l.source)
      })
    }
    const hasFocus = !!(selectedNode || hoveredNode)
    const focusId = selectedNode || hoveredNode

    // Draw links
    graphData.links.forEach((l: any) => {
      const a = pos[l.source], b = pos[l.target]; if (!a||!b) return
      const isHighlighted = hasFocus && (l.source === focusId || l.target === focusId)
      const isDimmed = hasFocus && !isHighlighted

      if (isDimmed) {
        ctx.strokeStyle = 'rgba(255,255,255,0.03)'; ctx.lineWidth = 0.5
      } else if (isHighlighted) {
        const cA = nodeColor[l.source] || '#666'
        const cB = nodeColor[l.target] || '#666'
        const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y)
        grad.addColorStop(0, cA + 'cc')
        grad.addColorStop(1, cB + 'cc')
        ctx.strokeStyle = grad; ctx.lineWidth = 2.5
        ctx.shadowColor = cA; ctx.shadowBlur = 8
      } else {
        const cA = nodeColor[l.source] || '#666'
        const cB = nodeColor[l.target] || '#666'
        const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y)
        grad.addColorStop(0, cA + '35')
        grad.addColorStop(1, cB + '35')
        ctx.strokeStyle = grad; ctx.lineWidth = 1
      }
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
      ctx.shadowBlur = 0
    })

    // Draw nodes
    graphData.nodes.forEach((n: any) => {
      const p = pos[n.id]; if (!p) return
      const r = Math.max(5, Math.min(16, (n.size||1)*3+4))
      const c = nodeColor[n.id]
      const isFocused = n.id === focusId
      const isConnected = connectedTo.has(n.id)
      const isDimmed = hasFocus && !isFocused && !isConnected

      const alpha = isDimmed ? '30' : 'ff'
      const glowSize = isFocused ? 25 : isConnected ? 15 : 8
      const nodeR = isFocused ? r + 3 : isConnected ? r + 1 : r

      // Glow
      ctx.shadowColor = c; ctx.shadowBlur = glowSize
      ctx.fillStyle = c + (isDimmed ? '10' : '25')
      ctx.beginPath(); ctx.arc(p.x, p.y, nodeR + 5, 0, Math.PI*2); ctx.fill()
      ctx.shadowBlur = 0

      // Node body
      const rGrad = ctx.createRadialGradient(p.x - nodeR*0.3, p.y - nodeR*0.3, 0, p.x, p.y, nodeR)
      rGrad.addColorStop(0, c + alpha)
      rGrad.addColorStop(1, c + (isDimmed ? '18' : '99'))
      ctx.fillStyle = rGrad
      ctx.beginPath(); ctx.arc(p.x, p.y, nodeR, 0, Math.PI*2); ctx.fill()

      // Ring
      if (isFocused) {
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 2
        ctx.beginPath(); ctx.arc(p.x, p.y, nodeR + 3, 0, Math.PI*2); ctx.stroke()
      } else if (isConnected) {
        ctx.strokeStyle = c + '80'; ctx.lineWidth = 1.5
        ctx.beginPath(); ctx.arc(p.x, p.y, nodeR + 2, 0, Math.PI*2); ctx.stroke()
      }

      // Label
      const labelAlpha = isDimmed ? 0.15 : isFocused ? 1 : isConnected ? 0.9 : 0.7
      ctx.fillStyle = `rgba(255,255,255,${labelAlpha})`
      ctx.font = isFocused ? 'bold 12px system-ui' : '10px system-ui'
      ctx.textAlign = 'center'
      ctx.fillText(n.name.substring(0, 22), p.x, p.y + nodeR + 15)

      // Type badge on focused node
      if (isFocused) {
        const typeLabel = (n.type || n.group || '').toUpperCase()
        if (typeLabel) {
          ctx.font = '8px system-ui'
          ctx.fillStyle = c + 'cc'
          ctx.fillText(typeLabel, p.x, p.y + nodeR + 27)
        }
      }
    })

    ctx.restore()

    // Zoom level indicator
    if (t.scale !== 1) {
      ctx.fillStyle = 'rgba(255,255,255,0.3)'; ctx.font = '10px system-ui'
      ctx.textAlign = 'right'; ctx.fillText(`${Math.round(t.scale * 100)}%`, w - 12, h - 10)
    }
  }, [graphData, hoveredNode, selectedNode])

  // Mouse → canvas coordinate helper
  const canvasCoord = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return { x: 0, y: 0 }
    const t = graphTransform.current
    return { x: (e.clientX - rect.left - t.ox) / t.scale, y: (e.clientY - rect.top - t.oy) / t.scale }
  }

  const hitTest = (mx: number, my: number): string | null => {
    if (!graphData?.nodes) return null
    const pos = graphPosRef.current
    for (const n of graphData.nodes) {
      const p = pos[n.id]; if (!p) continue
      const r = Math.max(5, Math.min(16, (n.size||1)*3+4)) + 5
      if (Math.hypot(mx - p.x, my - p.y) < r) return n.id
    }
    return null
  }

  const handleCanvasMouseDown = (e: React.MouseEvent) => {
    const { x, y } = canvasCoord(e)
    const hit = hitTest(x, y)
    if (hit) {
      dragRef.current = { nodeId: hit, panning: false, lastX: e.clientX, lastY: e.clientY }
      setSelectedNode(prev => prev === hit ? null : hit)
    } else {
      dragRef.current = { nodeId: null, panning: true, lastX: e.clientX, lastY: e.clientY }
      setSelectedNode(null)
    }
  }

  const handleCanvasMouseMove = (e: React.MouseEvent) => {
    const d = dragRef.current
    if (d.nodeId) {
      // Drag node
      const t = graphTransform.current
      const dx = (e.clientX - d.lastX) / t.scale, dy = (e.clientY - d.lastY) / t.scale
      const p = graphPosRef.current[d.nodeId]
      if (p) { p.x += dx; p.y += dy }
      d.lastX = e.clientX; d.lastY = e.clientY
      renderGraph()
      return
    }
    if (d.panning) {
      const t = graphTransform.current
      t.ox += e.clientX - d.lastX; t.oy += e.clientY - d.lastY
      d.lastX = e.clientX; d.lastY = e.clientY
      renderGraph()
      return
    }
    // Hover
    const { x, y } = canvasCoord(e)
    const hit = hitTest(x, y)
    if (hit !== hoveredNode) {
      setHoveredNode(hit)
      if (canvasRef.current) canvasRef.current.style.cursor = hit ? 'pointer' : 'grab'
    }
  }

  const handleCanvasMouseUp = () => {
    dragRef.current = { nodeId: null, panning: false, lastX: 0, lastY: 0 }
  }

  const handleCanvasWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const t = graphTransform.current
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    const zoom = e.deltaY < 0 ? 1.1 : 0.9
    const newScale = Math.max(0.3, Math.min(3, t.scale * zoom))
    t.ox = mx - (mx - t.ox) * (newScale / t.scale)
    t.oy = my - (my - t.oy) * (newScale / t.scale)
    t.scale = newScale
    renderGraph()
  }

  const resetGraphView = () => {
    graphTransform.current = { ox: 0, oy: 0, scale: 1 }
    setSelectedNode(null); setHoveredNode(null)
    renderGraph()
  }

  useEffect(() => {
    if (graphData && activeTab === 'graph') {
      // Reset transform and selected state on new data
      graphTransform.current = { ox: 0, oy: 0, scale: 1 }
      setSelectedNode(null); setHoveredNode(null)
      // Layout needs DOM to be ready for canvas dimensions
      const timer = setTimeout(() => {
        layoutGraph()
        // renderGraph needs a tick after layout to read the new positions
        requestAnimationFrame(() => { renderGraph() })
      }, 350)
      return () => clearTimeout(timer)
    }
  }, [graphData, activeTab])

  useEffect(() => { renderGraph() }, [hoveredNode, selectedNode, renderGraph])

  // ─── Tab Config ────────────────────────────────────────────
  const tabs = [
    { id: 'upload', icon: '📤', label: 'Upload' },
    { id: 'search', icon: '🔍', label: 'Search' },
    { id: 'check', icon: '🛡️', label: 'Analyze' },
    { id: 'adapt', icon: '🎯', label: 'Adapt' },
    { id: 'seo', icon: '🔎', label: 'SEO' },
    { id: 'calendar', icon: '📅', label: 'Calendar' },
    { id: 'personas', icon: '👥', label: 'Personas' },
    { id: 'versions', icon: '📝', label: 'Versions' },
    { id: 'analytics', icon: '📊', label: 'Analytics' },
    { id: 'insights', icon: '💡', label: 'Insights' },
    { id: 'graph', icon: '🧠', label: 'Graph' },
  ]

  // ─── Render ────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-black relative">
      <Toaster position="top-center" toastOptions={{ style: { background: '#111', color: '#fff', border: '1px solid #222', borderRadius: '12px', fontSize: '14px' } }} />

      {/* Background Orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-48 -left-48 w-[500px] h-[500px] bg-purple-600/8 rounded-full blur-[120px] animate-float" />
        <div className="absolute -bottom-48 -right-48 w-[500px] h-[500px] bg-blue-600/8 rounded-full blur-[120px] animate-float-delayed" />
        <div className="absolute top-1/3 left-1/2 w-[400px] h-[400px] bg-pink-600/6 rounded-full blur-[120px] animate-float-slow" />
      </div>

      {/* ─── Header ─────────────────────────────────────────── */}
      <header className="relative border-b border-white/5 glass">
        <div className="max-w-6xl mx-auto px-4 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-3xl">🧠</div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
                MemoryThread
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">AI Content Intelligence · Llama 3.1</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 text-xs text-gray-500">
              <GlowDot color="bg-green-500" />
              <span>Ollama Connected</span>
            </div>
            <div className="glass-strong rounded-xl px-4 py-2 text-center">
              <div className="text-xl font-bold text-white">{stats.total_content}</div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider">Content</div>
            </div>
          </div>
        </div>
      </header>

      {/* ─── Navigation ─────────────────────────────────────── */}
      <nav className="relative max-w-6xl mx-auto px-4 py-3">
        <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-white/10 text-white tab-active shadow-lg shadow-purple-500/10'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
              }`}>
              <span className="text-base">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* ─── Content ────────────────────────────────────────── */}
      <div className="relative max-w-6xl mx-auto px-4 pb-16">
        <div className="animate-fadeUp">

          {/* ═══════════ UPLOAD ═══════════ */}
          {activeTab === 'upload' && (
            <div className="space-y-6 animate-fadeUp">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Upload Content</h2>
                  <p className="text-sm text-gray-500 mt-1">Build your memory base with past content</p>
                </div>
                <button onClick={() => setShowBulk(!showBulk)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-all">
                  {showBulk ? '← Single' : '📦 Bulk Upload'}
                </button>
              </div>

              {!showBulk ? (
                <form onSubmit={handleUpload} className="space-y-4">
                  <input type="text" value={uploadTitle} onChange={e => setUploadTitle(e.target.value)}
                    className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-purple-500/50 focus:outline-none transition-all"
                    placeholder="Content title..." required />
                  <textarea value={uploadContent} onChange={e => setUploadContent(e.target.value)}
                    className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-purple-500/50 focus:outline-none h-36 resize-none transition-all"
                    placeholder="Paste your content here..." required />
                  <div className="flex gap-3">
                    <select value={uploadPlatform} onChange={e => setUploadPlatform(e.target.value)}
                      className="px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white focus:border-purple-500/50 focus:outline-none">
                      {['blog','linkedin','twitter','instagram','general'].map(p => (
                        <option key={p} value={p} className="bg-black">{p.charAt(0).toUpperCase()+p.slice(1)}</option>
                      ))}
                    </select>
                    <button type="submit" disabled={uploading}
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold py-3 rounded-xl hover:shadow-lg hover:shadow-purple-500/20 transition-all disabled:opacity-40 animate-gradient">
                      {uploading ? '⏳ Uploading...' : '📤 Upload'}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <textarea value={bulkText} onChange={e => setBulkText(e.target.value)}
                    className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-purple-500/50 focus:outline-none h-48 resize-none font-mono text-sm"
                    placeholder={"# My First Post\nContent here...\n---\n# My Second Post\nMore content..."} />
                  <button onClick={handleBulkUpload} disabled={bulkUploading || !bulkText.trim()}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold py-3 rounded-xl hover:shadow-lg transition-all disabled:opacity-40">
                    {bulkUploading ? '⏳ Uploading...' : `📦 Upload ${bulkText.split('---').filter(p => p.trim()).length} Pieces`}
                  </button>
                </div>
              )}

              {contentList.length > 0 && (
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Library · {contentList.length}</h3>
                    <button onClick={handleClearAll} className="text-xs text-red-400/60 hover:text-red-400 transition-colors">Clear All</button>
                  </div>
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {contentList.map((item, i) => (
                      <div key={item.id} className="group flex items-center justify-between glass rounded-xl px-4 py-3 animate-slideIn" style={{ animationDelay: `${i * 0.05}s` }}>
                        <div className="min-w-0">
                          <h4 className="text-sm font-medium text-white truncate group-hover:text-purple-400 transition-colors">{item.title}</h4>
                          <div className="flex gap-3 mt-0.5 text-[11px] text-gray-600">
                            <span>{item.word_count}w</span>
                            <span className="capitalize">{item.platform}</span>
                            <span>{new Date(item.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <button onClick={() => handleDeleteContent(item.id)}
                          className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-600 hover:text-red-400 rounded-lg transition-all">
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {contentList.length === 0 && <EmptyState icon="📭" text="No content yet. Upload your first piece above." />}
            </div>
          )}

          {/* ═══════════ SEARCH ═══════════ */}
          {activeTab === 'search' && (
            <div className="space-y-6 animate-fadeUp">
              <h2 className="text-2xl font-bold text-white">Semantic Search</h2>
              <form onSubmit={handleSearch} className="flex gap-2">
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  className="flex-1 px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-blue-500/50 focus:outline-none"
                  placeholder="What did I write about...?" required />
                <button type="submit" disabled={searching}
                  className="px-6 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all disabled:opacity-40">
                  {searching ? '...' : '🔍'}
                </button>
              </form>
              <div className="space-y-3">
                {searchResults.map((r, i) => (
                  <Card key={r.id} className={`animate-slideIn`}>
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-white text-sm">{r.title}</h4>
                      <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-blue-500/15 text-blue-400 ml-3 whitespace-nowrap">{r.similarity.toFixed(1)}%</span>
                    </div>
                    <p className="text-xs text-gray-500 leading-relaxed">{r.content_preview}</p>
                  </Card>
                ))}
              </div>
              {!searching && searchResults.length === 0 && searchQuery && <EmptyState icon="🔍" text="No results found. Try different keywords." />}
            </div>
          )}

          {/* ═══════════ ANALYZE ═══════════ */}
          {activeTab === 'check' && (
            <div className="space-y-5 animate-fadeUp">
              <div>
                <h2 className="text-2xl font-bold text-white">Content Analyzer</h2>
                <p className="text-sm text-gray-500 mt-1">Repetition · Contradictions · References · Voice</p>
              </div>

              <textarea value={draftContent} onChange={e => setDraftContent(e.target.value)}
                className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-pink-500/50 focus:outline-none h-36 resize-none"
                placeholder="Paste your draft for comprehensive analysis..." />

              {/* KG Toggle */}
              <div className="flex items-center justify-between glass rounded-xl px-4 py-3">
                <div className="flex items-center gap-2.5">
                  <span className="text-lg">🧠</span>
                  <div>
                    <span className="text-sm font-medium text-white">Knowledge Graph</span>
                    <p className="text-[11px] text-gray-600">Entity & topic extraction</p>
                  </div>
                </div>
                <button onClick={() => setUseKG(!useKG)}
                  className={`relative w-12 h-6 rounded-full transition-all duration-300 ${useKG ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-white/10'}`}>
                  <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-300 ${useKG ? 'left-[26px]' : 'left-0.5'}`} />
                </button>
              </div>

              {/* 4 Analysis Buttons */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {[
                  { label: 'Repetition', icon: '🔄', loading: checking, handler: handleCheck, gradient: 'from-pink-600 to-rose-600' },
                  { label: 'Contradictions', icon: '⚡', loading: checkingContradiction, handler: handleContradiction, gradient: 'from-red-600 to-orange-600' },
                  { label: 'References', icon: '🔗', loading: checkingReferences, handler: handleReferences, gradient: 'from-blue-600 to-indigo-600' },
                  { label: 'Voice', icon: '🎭', loading: checkingTone, handler: handleTone, gradient: 'from-emerald-600 to-teal-600' },
                ].map(btn => (
                  <button key={btn.label} onClick={(e: any) => btn.handler(e)} disabled={btn.loading || !draftContent.trim()}
                    className={`py-3 bg-gradient-to-r ${btn.gradient} text-white text-sm font-semibold rounded-xl hover:shadow-lg transition-all disabled:opacity-30`}>
                    {btn.loading ? <span className="animate-pulse">⏳</span> : <>{btn.icon} {btn.label}</>}
                  </button>
                ))}
              </div>

              {/* Repetition Results */}
              {checkResult && (
                <Card className={`border ${checkResult.is_repetition ? 'border-yellow-500/30' : 'border-green-500/30'} animate-scaleIn`}>
                  <h3 className="text-lg font-bold text-white mb-2">{checkResult.is_repetition ? '⚠️ Repetition Detected' : '✅ Unique Content'}</h3>
                  <p className="text-sm text-gray-400 mb-3">{checkResult.message}</p>
                  {useKG && checkResult.graph_analysis && (
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {checkResult.graph_analysis.draft_entities?.slice(0, 6).map((e: string, i: number) => <Badge key={i} color="purple">{e}</Badge>)}
                      {checkResult.graph_analysis.draft_topics?.slice(0, 4).map((t: string, i: number) => <Badge key={i} color="pink">{t}</Badge>)}
                    </div>
                  )}
                  {checkResult.similar_content?.map((item: any) => (
                    <div key={item.id} className="glass rounded-xl p-3 mb-2">
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-medium text-white">{item.title}</span>
                        <Badge color="yellow">{item.similarity.toFixed(1)}%</Badge>
                      </div>
                      {item.shared_entities?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {item.shared_entities.slice(0, 4).map((e: string, i: number) => <Badge key={i} color="purple">{e}</Badge>)}
                        </div>
                      )}
                    </div>
                  ))}
                </Card>
              )}

              {/* Contradiction Results */}
              {contradictionResult && (
                <Card className={`border ${contradictionResult.has_contradictions ? 'border-red-500/30' : 'border-green-500/30'} animate-scaleIn`}>
                  <h3 className="text-lg font-bold text-white mb-2">{contradictionResult.has_contradictions ? '🚨 Contradictions Found' : '✅ Consistent'}</h3>
                  <p className="text-sm text-gray-400 mb-3">{contradictionResult.message}</p>
                  {contradictionResult.contradictions?.map((c: any, i: number) => (
                    <div key={i} className="glass rounded-xl p-4 mb-3">
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          c.severity === 'high' ? 'bg-red-500/20 text-red-400' : c.severity === 'medium' ? 'bg-orange-500/20 text-orange-400' : 'bg-yellow-500/20 text-yellow-400'
                        }`}>{c.severity}</span>
                        <span className="text-xs text-gray-600">vs "{c.past_content_title}"</span>
                      </div>
                      <div className="grid md:grid-cols-2 gap-3">
                        <div className="bg-red-500/5 rounded-lg p-3 border border-red-500/10">
                          <div className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Past</div>
                          <p className="text-sm text-gray-300">{c.past_claim}</p>
                        </div>
                        <div className="bg-orange-500/5 rounded-lg p-3 border border-orange-500/10">
                          <div className="text-[10px] text-orange-400 uppercase tracking-wider mb-1">New</div>
                          <p className="text-sm text-gray-300">{c.new_claim}</p>
                        </div>
                      </div>
                      {c.explanation && <p className="text-xs text-gray-600 mt-2">{c.explanation}</p>}
                    </div>
                  ))}
                </Card>
              )}

              {/* References Results */}
              {referencesResult && (
                <Card className="border border-blue-500/30 animate-scaleIn">
                  <h3 className="text-lg font-bold text-white mb-2">🔗 Smart References</h3>
                  <p className="text-sm text-gray-400 mb-3">{referencesResult.message}</p>
                  {referencesResult.suggestions && (
                    <div className="glass rounded-xl p-3 mb-3 text-sm text-gray-300 whitespace-pre-wrap">{referencesResult.suggestions}</div>
                  )}
                  {referencesResult.references?.map((ref: any) => (
                    <div key={ref.id} className="flex items-center justify-between glass rounded-xl px-4 py-3 mb-2">
                      <div className="min-w-0">
                        <span className="text-sm font-medium text-white">{ref.title}</span>
                        <p className="text-xs text-gray-600 truncate mt-0.5">{ref.content_preview}</p>
                      </div>
                      <Badge color="blue">{ref.relevance}%</Badge>
                    </div>
                  ))}
                </Card>
              )}

              {/* Tone Results */}
              {toneResult && (
                <Card className={`border ${toneResult.tone_consistent ? 'border-emerald-500/30' : 'border-amber-500/30'} animate-scaleIn`}>
                  <h3 className="text-lg font-bold text-white mb-2">🎭 Voice Analysis</h3>
                  <p className="text-sm text-gray-400 mb-3">{toneResult.message}</p>
                  {toneResult.analysis?.past_voice && (
                    <div className="grid md:grid-cols-2 gap-3 mb-3">
                      {[
                        { label: 'Established Voice', data: toneResult.analysis.past_voice, color: 'emerald' },
                        { label: 'This Draft', data: toneResult.analysis.new_voice, color: 'amber' },
                      ].map(v => v.data && (
                        <div key={v.label} className="glass rounded-xl p-3">
                          <div className={`text-[10px] text-${v.color}-400 uppercase tracking-wider mb-2`}>{v.label}</div>
                          <div className="space-y-1 text-sm text-gray-300">
                            <p>Formality: <span className="text-white font-medium">{v.data.formality}/10</span></p>
                            <p>Tone: <span className="text-white font-medium capitalize">{v.data.tone}</span></p>
                            <p>Style: <span className="text-white font-medium capitalize">{v.data.style}</span></p>
                          </div>
                          <div className="flex flex-wrap gap-1 mt-2">
                            {v.data.characteristics?.map((c: string, i: number) => <Badge key={i} color={v.color}>{c}</Badge>)}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {toneResult.analysis?.drift_areas?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      <span className="text-xs text-gray-600">Drift:</span>
                      {toneResult.analysis.drift_areas.map((d: string, i: number) => <Badge key={i} color="amber">{d}</Badge>)}
                    </div>
                  )}
                </Card>
              )}
            </div>
          )}

          {/* ═══════════ ADAPT ═══════════ */}
          {activeTab === 'adapt' && (
            <div className="space-y-6 animate-fadeUp">
              <div>
                <h2 className="text-2xl font-bold text-white">Platform Adapter</h2>
                <p className="text-sm text-gray-500 mt-1">Transform content for every platform instantly</p>
              </div>
              <form onSubmit={handleAdapt} className="space-y-4">
                <textarea value={adaptContent} onChange={e => setAdaptContent(e.target.value)}
                  className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-purple-500/50 focus:outline-none h-36 resize-none"
                  placeholder="Paste content to adapt for all platforms..." required />
                <button type="submit" disabled={adapting}
                  className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 text-white font-semibold py-3 rounded-xl hover:shadow-lg hover:shadow-purple-500/20 transition-all disabled:opacity-40 animate-gradient">
                  {adapting ? '⏳ Generating...' : '🎯 Adapt for All Platforms'}
                </button>
              </form>

              {adaptations && (
                <div className="grid md:grid-cols-2 gap-4">
                  {Object.entries(adaptations).filter(([k]) => k !== 'original').map(([platform, data]: [string, any]) => {
                    const icons: Record<string, string> = { twitter: '𝕏', linkedin: '💼', instagram: '📸', blog: '📝', tiktok: '🎵' }
                    const gradients: Record<string, string> = {
                      twitter: 'from-blue-500/10 to-cyan-500/10', linkedin: 'from-blue-600/10 to-indigo-600/10',
                      instagram: 'from-pink-500/10 to-purple-500/10', blog: 'from-emerald-500/10 to-teal-500/10',
                      tiktok: 'from-rose-500/10 to-pink-500/10'
                    }
                    return (
                      <Card key={platform} className={`bg-gradient-to-br ${gradients[platform] || 'from-gray-500/10 to-gray-600/10'} animate-scaleIn`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{icons[platform] || '📄'}</span>
                            <h4 className="font-semibold text-white capitalize">{platform}</h4>
                          </div>
                          <button onClick={() => copy(typeof data === 'string' ? data : data.content || JSON.stringify(data), platform)}
                            className={`text-xs px-3 py-1.5 rounded-lg transition-all ${
                              copiedPlatform === platform ? 'bg-green-500/20 text-green-400' : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'
                            }`}>
                            {copiedPlatform === platform ? '✓ Copied' : '📋 Copy'}
                          </button>
                        </div>
                        <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                          {typeof data === 'string' ? data : data.content || JSON.stringify(data, null, 2)}
                        </div>
                        {data.hashtags && (
                          <div className="flex flex-wrap gap-1 mt-3">
                            {(Array.isArray(data.hashtags) ? data.hashtags : [data.hashtags]).map((h: string, i: number) => (
                              <span key={i} className="text-xs text-purple-400/70">#{h.replace(/^#/, '')}</span>
                            ))}
                          </div>
                        )}
                      </Card>
                    )
                  })}
                </div>
              )}
              {!adapting && !adaptations && <EmptyState icon="🎯" text="Paste content above and adapt it for every platform." />}
            </div>
          )}


          {/* ═══════════ ANALYTICS ═══════════ */}
          {activeTab === 'analytics' && (
            <div className="space-y-6 animate-fadeUp">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Analytics Dashboard</h2>
                  <p className="text-sm text-gray-500 mt-1">Content performance and trends at a glance</p>
                </div>
                <button onClick={() => { setAnalytics(null); loadAnalytics() }}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-all">
                  🔄 Refresh
                </button>
              </div>

              {loadingAnalytics && <LoadingPulse text="Crunching numbers..." />}

              {analytics && (
                <div className="space-y-6">
                  {/* Stat Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { label: 'Total Content', value: analytics.total_content, icon: '📄', color: 'purple' },
                      { label: 'Total Words', value: (analytics.total_words || 0).toLocaleString(), icon: '✍️', color: 'blue' },
                      { label: 'Avg Length', value: `${analytics.avg_word_count || 0}w`, icon: '📏', color: 'pink' },
                      { label: 'Platforms', value: Object.keys(analytics.platform_breakdown || {}).length, icon: '🌐', color: 'cyan' },
                    ].map(stat => (
                      <div key={stat.label} className="glass-strong rounded-2xl p-4 stat-shine hover-lift">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">{stat.icon}</span>
                          <span className="text-[10px] text-gray-500 uppercase tracking-wider">{stat.label}</span>
                        </div>
                        <div className={`text-2xl font-bold text-${stat.color}-400`}>{stat.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Platform Breakdown */}
                  {analytics.platform_breakdown && Object.keys(analytics.platform_breakdown).length > 0 && (
                    <Card>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Platform Breakdown</h3>
                      <div className="space-y-3">
                        {Object.entries(analytics.platform_breakdown).sort(([,a]: any, [,b]: any) => b - a).map(([platform, count]: [string, any]) => {
                          const max = Math.max(...Object.values(analytics.platform_breakdown as Record<string, number>))
                          const colors: Record<string, string> = {
                            blog: 'from-emerald-500 to-teal-500', twitter: 'from-blue-400 to-cyan-400',
                            linkedin: 'from-blue-600 to-indigo-500', instagram: 'from-pink-500 to-purple-500',
                            general: 'from-gray-400 to-gray-500', tiktok: 'from-rose-500 to-pink-500'
                          }
                          return (
                            <div key={platform} className="flex items-center gap-3">
                              <span className="text-sm text-gray-400 capitalize w-20 text-right">{platform}</span>
                              <div className="flex-1"><MiniBar value={count} max={max} color={colors[platform] || 'from-purple-500 to-pink-500'} /></div>
                              <span className="text-sm font-bold text-white w-8 text-right">{count}</span>
                            </div>
                          )
                        })}
                      </div>
                    </Card>
                  )}

                  {/* Timeline & Top Topics */}
                  <div className="grid md:grid-cols-2 gap-4">
                    {analytics.timeline && analytics.timeline.length > 0 && (
                      <Card>
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">📅 Timeline</h3>
                        <div className="space-y-2">
                          {analytics.timeline.slice(-7).map((entry: any, i: number) => (
                            <div key={`${entry.date}-${i}`} className="flex items-center justify-between">
                              <span className="text-xs text-gray-500 font-mono">{entry.date}</span>
                              <div className="flex items-center gap-2">
                                <div className="flex gap-0.5">
                                  {Array.from({ length: Math.min(entry.count, 10) }).map((_, i) => (
                                    <div key={i} className="w-2 h-2 rounded-sm bg-purple-500/60" />
                                  ))}
                                </div>
                                <span className="text-xs text-white font-medium w-6 text-right">{entry.count}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </Card>
                    )}

                    {analytics.top_topics && analytics.top_topics.length > 0 && (
                      <Card>
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">🏷️ Top Topics</h3>
                        <div className="flex flex-wrap gap-2">
                          {analytics.top_topics.map((topic: any, i: number) => {
                            const sizes = ['text-lg', 'text-base', 'text-sm', 'text-xs']
                            const opacities = ['opacity-100', 'opacity-80', 'opacity-60', 'opacity-50']
                            const si = Math.min(i, sizes.length - 1)
                            return (
                              <span key={topic.name || topic} className={`${sizes[si]} ${opacities[si]} text-purple-400 font-medium px-2 py-1 rounded-lg bg-purple-500/10`}>
                                {topic.name || topic}
                                {topic.count && <span className="text-[10px] ml-1 text-gray-600">×{topic.count}</span>}
                              </span>
                            )
                          })}
                        </div>
                      </Card>
                    )}
                  </div>

                  {/* Top Entities */}
                  {analytics.top_entities && analytics.top_entities.length > 0 && (
                    <Card>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">🔮 Top Entities</h3>
                      <div className="flex flex-wrap gap-2">
                        {analytics.top_entities.map((entity: any, i: number) => (
                          <div key={entity.name || entity} className="flex items-center gap-1.5 glass rounded-lg px-3 py-1.5 hover-lift">
                            <GlowDot color={i < 3 ? 'bg-purple-500' : 'bg-gray-500'} />
                            <span className="text-sm text-white">{entity.name || entity}</span>
                            {entity.count && <span className="text-[10px] text-gray-600">×{entity.count}</span>}
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}
                </div>
              )}
              {!loadingAnalytics && !analytics && <EmptyState icon="📊" text="No analytics data yet. Upload some content first." />}
            </div>
          )}


          {/* ═══════════ INSIGHTS ═══════════ */}
          {activeTab === 'insights' && (
            <div className="space-y-6 animate-fadeUp">
              <h2 className="text-2xl font-bold text-white">Content Insights</h2>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Health Score */}
                <Card className="gradient-border">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">💚 Content Health</h3>
                  {loadingHealth && <LoadingPulse text="Analyzing health..." />}
                  {healthScore && (
                    <div className="flex flex-col items-center">
                      <ScoreRing score={healthScore.overall_score || healthScore.health_score || 0} />
                      <p className="text-sm text-gray-400 mt-4 text-center">{healthScore.summary || healthScore.message || 'Health analysis complete'}</p>
                      {healthScore.factors && (
                        <div className="w-full mt-4 space-y-2">
                          {Object.entries(healthScore.factors).map(([key, val]: [string, any]) => (
                            <div key={key} className="flex items-center justify-between">
                              <span className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</span>
                              <div className="flex items-center gap-2 w-1/2">
                                <MiniBar value={typeof val === 'number' ? val : val.score || 0} max={100} />
                                <span className="text-xs text-white font-medium w-8 text-right">{typeof val === 'number' ? val : val.score || 0}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                      {healthScore.recommendations && (
                        <div className="w-full mt-4 space-y-1.5">
                          {(Array.isArray(healthScore.recommendations) ? healthScore.recommendations : [healthScore.recommendations]).map((rec: string, i: number) => (
                            <div key={i} className="flex items-start gap-2 text-xs text-gray-400">
                              <span className="text-purple-400 mt-0.5">→</span>
                              <span>{rec}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {!loadingHealth && !healthScore && <EmptyState icon="💚" text="No health data" />}
                </Card>

                {/* Content Gaps */}
                <Card className="gradient-border">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">🕳️ Content Gaps</h3>
                  {loadingGaps && <LoadingPulse text="Finding gaps..." />}
                  {contentGaps && (
                    <div>
                      <p className="text-sm text-gray-400 mb-4">{contentGaps.message}</p>

                      {/* AI-Suggested New Topics */}
                      {contentGaps.suggestions?.length > 0 && (
                        <div className="space-y-3 mb-4">
                          <span className="text-[10px] text-purple-400 uppercase tracking-wider">AI Suggestions</span>
                          {contentGaps.suggestions.map((s: any, i: number) => (
                            <div key={i} className="glass rounded-xl p-3 hover-lift">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="w-2 h-2 rounded-full bg-purple-500" />
                                <span className="text-sm font-medium text-white">{s.topic}</span>
                              </div>
                              <p className="text-xs text-gray-500 ml-4">{s.reason}</p>
                              {s.article_idea && (
                                <p className="text-xs text-purple-400/70 ml-4 mt-1">💡 {s.article_idea}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Underexplored Topics */}
                      {contentGaps.underexplored_topics?.length > 0 && (
                        <div className="space-y-2 mb-4">
                          <span className="text-[10px] text-amber-400 uppercase tracking-wider">Underexplored Topics</span>
                          <div className="flex flex-wrap gap-2">
                            {contentGaps.underexplored_topics.map((t: any, i: number) => (
                              <Badge key={i} color="amber">{t.name}</Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Well Covered */}
                      {contentGaps.well_covered_topics?.length > 0 && (
                        <div className="space-y-2">
                          <span className="text-[10px] text-emerald-400 uppercase tracking-wider">Well Covered</span>
                          <div className="flex flex-wrap gap-2">
                            {contentGaps.well_covered_topics.map((t: any, i: number) => (
                              <Badge key={i} color="emerald">{t.name} ×{t.count}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {!loadingGaps && !contentGaps && <EmptyState icon="🕳️" text="No gap analysis yet" />}
                </Card>
              </div>
            </div>
          )}


          {/* ═══════════ KNOWLEDGE GRAPH ═══════════ */}
          {activeTab === 'graph' && (
            <div className="space-y-6 animate-fadeUp">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Knowledge Graph</h2>
                  <p className="text-sm text-gray-500 mt-1">Visual map of entities and connections in your content</p>
                </div>
                <button onClick={() => loadGraph(graphDensity)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-all">
                  🔄 Refresh
                </button>
              </div>

              {/* Density Control */}
              <div className="glass rounded-xl px-4 py-3 flex items-center gap-4">
                <span className="text-xs text-gray-500 whitespace-nowrap">Density</span>
                <input type="range" min={15} max={120} value={graphDensity}
                  onChange={e => setGraphDensity(Number(e.target.value))}
                  className="flex-1 h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-purple-500" />
                <span className="text-xs text-white font-mono w-8 text-right">{graphDensity}</span>
                <button onClick={() => loadGraph(graphDensity)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-all">
                  Apply
                </button>
              </div>

              {loadingGraph && <LoadingPulse text="Building knowledge graph..." />}

              {graphData && (
                <div className="space-y-4">
                  {/* Graph Stats */}
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Nodes', value: `${graphData.nodes?.length || 0}${graphData.stats?.total_entities_in_db ? ` / ${graphData.stats.total_entities_in_db + graphData.stats.total_topics_in_db}` : ''}`, icon: '🔵', color: 'blue' },
                      { label: 'Connections', value: graphData.links?.length || 0, icon: '🔗', color: 'purple' },
                      { label: 'Clusters', value: graphData.clusters || new Set(graphData.nodes?.map((n: any) => n.group || n.type)).size || 0, icon: '🌐', color: 'pink' },
                    ].map(s => (
                      <div key={s.label} className="glass-strong rounded-xl p-3 text-center hover-lift">
                        <span className="text-lg">{s.icon}</span>
                        <div className={`text-xl font-bold text-${s.color}-400 mt-1`}>{s.value}</div>
                        <div className="text-[10px] text-gray-500 uppercase tracking-wider">{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Canvas */}
                  <Card className="p-0 overflow-hidden relative">
                    <canvas ref={canvasRef}
                      className="rounded-2xl"
                      style={{ width: '100%', height: '500px', display: 'block', background: '#000', cursor: 'grab' }}
                      onMouseDown={handleCanvasMouseDown}
                      onMouseMove={handleCanvasMouseMove}
                      onMouseUp={handleCanvasMouseUp}
                      onMouseLeave={handleCanvasMouseUp}
                      onWheel={handleCanvasWheel}
                    />
                    {/* Controls overlay */}
                    <div className="absolute top-3 right-3 flex gap-1.5">
                      <button onClick={resetGraphView} className="glass-strong rounded-lg px-2.5 py-1.5 text-[10px] text-gray-400 hover:text-white transition-colors" title="Reset view">
                        ⟲ Reset
                      </button>
                    </div>
                    {/* Hover tooltip */}
                    {hoveredNode && !selectedNode && graphData?.nodes && (() => {
                      const node = graphData.nodes.find((n: any) => n.id === hoveredNode)
                      if (!node) return null
                      const connections = graphData.links.filter((l: any) => l.source === hoveredNode || l.target === hoveredNode).length
                      return (
                        <div className="absolute bottom-3 left-3 glass-strong rounded-xl px-3 py-2 max-w-xs pointer-events-none">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ background: graphColors[node.type] || graphColors[node.group] || '#666' }} />
                            <span className="text-sm font-medium text-white">{node.name}</span>
                          </div>
                          <div className="flex gap-3 mt-1 text-[10px] text-gray-500">
                            <span className="capitalize">{node.type || node.group}</span>
                            <span>{connections} connections</span>
                          </div>
                        </div>
                      )
                    })()}
                    {/* Selected node info */}
                    {selectedNode && graphData?.nodes && (() => {
                      const node = graphData.nodes.find((n: any) => n.id === selectedNode)
                      if (!node) return null
                      const connected = graphData.links
                        .filter((l: any) => l.source === selectedNode || l.target === selectedNode)
                        .map((l: any) => {
                          const otherId = l.source === selectedNode ? l.target : l.source
                          const other = graphData.nodes.find((n: any) => n.id === otherId)
                          return other ? { name: other.name, type: other.type || other.group, rel: l.type || 'connected' } : null
                        }).filter(Boolean)
                      return (
                        <div className="absolute bottom-3 left-3 right-3 glass-strong rounded-xl px-4 py-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="w-3 h-3 rounded-full" style={{ background: graphColors[node.type] || graphColors[node.group] || '#666' }} />
                              <span className="text-sm font-semibold text-white">{node.name}</span>
                              <Badge color="purple">{node.type || node.group}</Badge>
                            </div>
                            <button onClick={() => setSelectedNode(null)} className="text-gray-500 hover:text-white text-xs">✕</button>
                          </div>
                          {connected.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {connected.slice(0, 12).map((c: any, i: number) => (
                                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-gray-400">
                                  {c.name}
                                </span>
                              ))}
                              {connected.length > 12 && <span className="text-[10px] text-gray-600">+{connected.length - 12} more</span>}
                            </div>
                          )}
                        </div>
                      )
                    })()}
                    {/* Help hint */}
                    <div className="absolute top-3 left-3 text-[10px] text-gray-600">
                      Click node to inspect · Drag to move · Scroll to zoom · Drag background to pan
                    </div>
                  </Card>

                  {/* Legend */}
                  <div className="flex flex-wrap gap-3 justify-center">
                    {[
                      { type: 'entity', color: 'bg-purple-500', label: 'Entity' },
                      { type: 'topic', color: 'bg-pink-500', label: 'Topic' },
                      { type: 'content', color: 'bg-blue-500', label: 'Content' },
                      { type: 'person', color: 'bg-emerald-500', label: 'Person' },
                      { type: 'organization', color: 'bg-cyan-500', label: 'Organization' },
                      { type: 'tool', color: 'bg-amber-500', label: 'Tool' },
                    ].map(item => (
                      <div key={item.type} className="flex items-center gap-1.5 text-xs text-gray-500">
                        <span className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                        <span>{item.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {!loadingGraph && !graphData && <EmptyState icon="🧠" text="No graph data. Upload content to build your knowledge graph." />}
            </div>
          )}

          {/* ═══════════ SEO ANALYZER ═══════════ */}
          {activeTab === 'seo' && (
            <div className="space-y-6 animate-fadeUp">
              <div>
                <h2 className="text-2xl font-bold text-white">SEO Analyzer</h2>
                <p className="text-sm text-gray-500 mt-1">Readability, keyword density, and meta suggestions</p>
              </div>
              <form onSubmit={handleSeo} className="space-y-4">
                <input type="text" value={seoTitle} onChange={e => setSeoTitle(e.target.value)}
                  className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-emerald-500/50 focus:outline-none"
                  placeholder="Content title (optional)..." />
                <textarea value={seoContent} onChange={e => setSeoContent(e.target.value)}
                  className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-emerald-500/50 focus:outline-none h-36 resize-none"
                  placeholder="Paste content to analyze for SEO..." required />
                <div className="flex gap-3">
                  <input type="text" value={seoKeyword} onChange={e => setSeoKeyword(e.target.value)}
                    className="flex-1 px-4 py-3 bg-white/[0.03] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:border-emerald-500/50 focus:outline-none"
                    placeholder="Target keyword (optional)..." />
                  <button type="submit" disabled={analyzingSeo || !seoContent.trim()}
                    className="px-8 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold rounded-xl hover:shadow-lg transition-all disabled:opacity-40">
                    {analyzingSeo ? '⏳' : '🔎 Analyze'}
                  </button>
                </div>
              </form>

              {seoResult && (
                <div className="space-y-4 animate-fadeUp">
                  {/* Score + Readability */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card className="gradient-border flex flex-col items-center py-6">
                      <ScoreRing score={seoResult.seo_score} />
                      <p className="text-sm text-gray-400 mt-3">SEO Score</p>
                    </Card>
                    <Card>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">📖 Readability</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-400">Flesch Score</span>
                          <div className="flex items-center gap-2">
                            <MiniBar value={seoResult.readability.flesch_score} max={100} color="from-emerald-500 to-teal-500" />
                            <span className="text-sm font-bold text-white w-12 text-right">{seoResult.readability.flesch_score}</span>
                          </div>
                        </div>
                        <div className="flex justify-between"><span className="text-sm text-gray-400">Level</span><Badge color="emerald">{seoResult.readability.flesch_label}</Badge></div>
                        <div className="flex justify-between"><span className="text-sm text-gray-400">Grade</span><span className="text-sm text-white font-medium">{seoResult.readability.grade_level}</span></div>
                        <div className="flex justify-between"><span className="text-sm text-gray-400">Avg Sentence</span><span className="text-sm text-white font-medium">{seoResult.readability.avg_sentence_length} words</span></div>
                      </div>
                    </Card>
                  </div>

                  {/* Structure */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {[
                      { label: 'Words', value: seoResult.structure.word_count, icon: '✍️' },
                      { label: 'Sentences', value: seoResult.structure.sentence_count, icon: '📝' },
                      { label: 'Paragraphs', value: seoResult.structure.paragraph_count, icon: '📄' },
                      { label: 'Headings', value: seoResult.structure.heading_count, icon: '🔤' },
                      { label: 'Links', value: seoResult.structure.link_count, icon: '🔗' },
                    ].map(s => (
                      <div key={s.label} className="glass-strong rounded-xl p-3 text-center hover-lift">
                        <span className="text-base">{s.icon}</span>
                        <div className="text-lg font-bold text-white mt-1">{s.value}</div>
                        <div className="text-[10px] text-gray-500 uppercase">{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Keywords */}
                  {seoResult.keywords?.length > 0 && (
                    <Card>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">🏷️ Top Keywords</h3>
                      <div className="space-y-2">
                        {seoResult.keywords.slice(0, 10).map((kw: any, i: number) => (
                          <div key={i} className="flex items-center gap-3">
                            <span className="text-sm text-gray-400 w-28 truncate">{kw.keyword}</span>
                            <div className="flex-1"><MiniBar value={kw.count} max={seoResult.keywords[0].count} color="from-blue-500 to-cyan-500" /></div>
                            <span className="text-xs text-gray-500 w-16 text-right">{kw.density}%</span>
                            <span className="text-xs text-white font-medium w-6 text-right">{kw.count}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}

                  {/* Target Keyword */}
                  {seoResult.target_keyword && (
                    <Card className={`border ${seoResult.target_keyword.status === 'good' ? 'border-green-500/30' : 'border-yellow-500/30'}`}>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">🎯 Target: "{seoResult.target_keyword.keyword}"</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="text-center"><div className="text-lg font-bold text-white">{seoResult.target_keyword.count}</div><div className="text-[10px] text-gray-500">Occurrences</div></div>
                        <div className="text-center"><div className="text-lg font-bold text-white">{seoResult.target_keyword.density}%</div><div className="text-[10px] text-gray-500">Density</div></div>
                        <div className="text-center"><div className="text-lg font-bold">{seoResult.target_keyword.in_title ? '✅' : '❌'}</div><div className="text-[10px] text-gray-500">In Title</div></div>
                        <div className="text-center"><div className="text-lg font-bold">{seoResult.target_keyword.in_first_100_words ? '✅' : '❌'}</div><div className="text-[10px] text-gray-500">In First 100w</div></div>
                      </div>
                    </Card>
                  )}

                  {/* Meta Suggestions */}
                  {seoResult.meta_suggestions && (seoResult.meta_suggestions.meta_title || seoResult.meta_suggestions.tips) && (
                    <Card>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">💡 AI Suggestions</h3>
                      {seoResult.meta_suggestions.meta_title && (
                        <div className="mb-3">
                          <span className="text-[10px] text-purple-400 uppercase tracking-wider">Meta Title</span>
                          <p className="text-sm text-white mt-1 glass rounded-lg px-3 py-2">{seoResult.meta_suggestions.meta_title}</p>
                        </div>
                      )}
                      {seoResult.meta_suggestions.meta_description && (
                        <div className="mb-3">
                          <span className="text-[10px] text-purple-400 uppercase tracking-wider">Meta Description</span>
                          <p className="text-sm text-gray-300 mt-1 glass rounded-lg px-3 py-2">{seoResult.meta_suggestions.meta_description}</p>
                        </div>
                      )}
                      {seoResult.meta_suggestions.tips?.map((tip: string, i: number) => (
                        <div key={i} className="flex items-start gap-2 text-sm text-gray-400 mb-1.5">
                          <span className="text-emerald-400 mt-0.5">→</span><span>{tip}</span>
                        </div>
                      ))}
                    </Card>
                  )}
                </div>
              )}
              {!analyzingSeo && !seoResult && <EmptyState icon="🔎" text="Paste content above to get SEO insights." />}
            </div>
          )}

          {/* ═══════════ CONTENT CALENDAR ═══════════ */}
          {activeTab === 'calendar' && (
            <div className="space-y-6 animate-fadeUp">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Content Calendar</h2>
                  <p className="text-sm text-gray-500 mt-1">AI-suggested 7-day posting schedule</p>
                </div>
                <button onClick={() => { setCalendarData(null); loadCalendar() }}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-all">
                  🔄 Regenerate
                </button>
              </div>

              {loadingCalendar && <LoadingPulse text="Planning your week with AI..." />}

              {calendarData && (
                <div className="space-y-4">
                  {calendarData.strategy_notes && (
                    <Card className="border border-purple-500/20">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">🧠</span>
                        <span className="text-sm font-semibold text-purple-400">Strategy</span>
                      </div>
                      <p className="text-sm text-gray-300">{calendarData.strategy_notes}</p>
                    </Card>
                  )}

                  <div className="space-y-3">
                    {calendarData.calendar?.map((day: any, i: number) => {
                      const priorityColors: Record<string, string> = { high: 'bg-red-500/20 text-red-400', medium: 'bg-yellow-500/20 text-yellow-400', low: 'bg-blue-500/20 text-blue-400' }
                      const platformIcons: Record<string, string> = { twitter: '𝕏', linkedin: '💼', instagram: '📸', blog: '📝', tiktok: '🎵' }
                      return (
                        <Card key={i} className="animate-slideIn" >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <div className="glass-strong rounded-xl w-12 h-12 flex flex-col items-center justify-center">
                                <span className="text-xs text-gray-500">Day</span>
                                <span className="text-lg font-bold text-white">{day.day}</span>
                              </div>
                              <div>
                                <h4 className="text-sm font-semibold text-white">{day.title}</h4>
                                <div className="flex items-center gap-2 mt-0.5">
                                  <span className="text-xs text-gray-500">{day.weekday}</span>
                                  <span className="text-base">{platformIcons[day.platform] || '📄'}</span>
                                  <span className="text-xs text-gray-500 capitalize">{day.platform}</span>
                                </div>
                              </div>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${priorityColors[day.priority] || priorityColors.medium}`}>
                              {day.priority}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 ml-15">{day.reason}</p>
                          {day.topic_tags?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2 ml-15">
                              {day.topic_tags.map((t: string, j: number) => <Badge key={j} color="purple">{t}</Badge>)}
                            </div>
                          )}
                        </Card>
                      )
                    })}
                  </div>

                  {calendarData.underexplored_topics?.length > 0 && (
                    <Card>
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">🕳️ Underexplored Topics</h3>
                      <div className="flex flex-wrap gap-2">
                        {calendarData.underexplored_topics.map((t: any, i: number) => (
                          <Badge key={i} color="amber">{t.name} {t.count > 0 ? `×${t.count}` : '(new)'}</Badge>
                        ))}
                      </div>
                    </Card>
                  )}
                </div>
              )}
              {!loadingCalendar && !calendarData && <EmptyState icon="📅" text="Upload content first to generate a calendar." />}
            </div>
          )}

          {/* ═══════════ AUDIENCE PERSONAS ═══════════ */}
          {activeTab === 'personas' && (
            <div className="space-y-6 animate-fadeUp">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Audience Personas</h2>
                  <p className="text-sm text-gray-500 mt-1">AI-generated reader profiles from your content</p>
                </div>
                <button onClick={() => { setPersonasData(null); loadPersonas() }}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-all">
                  🔄 Regenerate
                </button>
              </div>

              {loadingPersonas && <LoadingPulse text="Building audience profiles..." />}

              {personasData && (
                <div className="space-y-4">
                  {personasData.audience_insights && (
                    <Card className="border border-cyan-500/20">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">🎯</span>
                        <span className="text-sm font-semibold text-cyan-400">Audience Insights</span>
                      </div>
                      <p className="text-sm text-gray-300">{personasData.audience_insights}</p>
                    </Card>
                  )}

                  <div className="grid md:grid-cols-3 gap-4">
                    {personasData.personas?.map((persona: any, i: number) => {
                      const gradients = ['from-purple-500/10 to-pink-500/10', 'from-blue-500/10 to-cyan-500/10', 'from-emerald-500/10 to-teal-500/10']
                      return (
                        <Card key={i} className={`bg-gradient-to-br ${gradients[i % 3]} animate-scaleIn`}>
                          <div className="text-center mb-3">
                            <span className="text-4xl">{persona.emoji || '👤'}</span>
                            <h4 className="text-lg font-bold text-white mt-2">{persona.name}</h4>
                            <p className="text-xs text-gray-500">{persona.age_range} · {persona.profession}</p>
                          </div>
                          {persona.description && <p className="text-xs text-gray-400 text-center mb-3">{persona.description}</p>}

                          <div className="space-y-3">
                            {persona.interests?.length > 0 && (
                              <div>
                                <span className="text-[10px] text-purple-400 uppercase tracking-wider">Interests</span>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {persona.interests.map((int_: string, j: number) => <Badge key={j} color="purple">{int_}</Badge>)}
                                </div>
                              </div>
                            )}
                            {persona.pain_points?.length > 0 && (
                              <div>
                                <span className="text-[10px] text-red-400 uppercase tracking-wider">Pain Points</span>
                                {persona.pain_points.map((p: string, j: number) => (
                                  <p key={j} className="text-xs text-gray-400 mt-0.5">• {p}</p>
                                ))}
                              </div>
                            )}
                            {persona.content_preferences?.length > 0 && (
                              <div>
                                <span className="text-[10px] text-emerald-400 uppercase tracking-wider">Prefers</span>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {persona.content_preferences.map((cp: string, j: number) => <Badge key={j} color="emerald">{cp}</Badge>)}
                                </div>
                              </div>
                            )}
                            <div className="flex items-center justify-between pt-2 border-t border-white/5">
                              <span className="text-[10px] text-gray-600">Platform</span>
                              <span className="text-xs text-white capitalize">{persona.preferred_platform}</span>
                            </div>
                            {persona.engagement_style && (
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] text-gray-600">Engagement</span>
                                <span className="text-xs text-white">{persona.engagement_style}</span>
                              </div>
                            )}
                          </div>
                        </Card>
                      )
                    })}
                  </div>
                </div>
              )}
              {!loadingPersonas && !personasData && <EmptyState icon="👥" text="Upload content first to generate audience personas." />}
            </div>
          )}

          {/* ═══════════ CONTENT VERSIONING ═══════════ */}
          {activeTab === 'versions' && (
            <div className="space-y-6 animate-fadeUp">
              <div>
                <h2 className="text-2xl font-bold text-white">Content Versioning</h2>
                <p className="text-sm text-gray-500 mt-1">Edit content and track changes over time</p>
              </div>

              {/* Content Selector */}
              {contentList.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
                    {contentList.map(item => (
                      <button key={item.id} onClick={() => loadVersions(item.id)}
                        className={`flex-shrink-0 px-4 py-2.5 rounded-xl text-sm transition-all ${
                          selectedContentId === item.id
                            ? 'bg-white/10 text-white border border-purple-500/30'
                            : 'glass text-gray-400 hover:text-white hover:bg-white/5'
                        }`}>
                        {item.title}
                      </button>
                    ))}
                  </div>

                  {loadingVersions && <LoadingPulse text="Loading versions..." />}

                  {selectedContentId && !loadingVersions && (
                    <div className="grid md:grid-cols-2 gap-4">
                      {/* Editor */}
                      <Card>
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">✏️ Edit</h3>
                        <input type="text" value={editTitle} onChange={e => setEditTitle(e.target.value)}
                          className="w-full px-3 py-2 bg-white/[0.03] border border-white/10 rounded-lg text-white text-sm placeholder-gray-600 focus:border-purple-500/50 focus:outline-none mb-3" />
                        <textarea value={editContent} onChange={e => setEditContent(e.target.value)}
                          className="w-full px-3 py-2 bg-white/[0.03] border border-white/10 rounded-lg text-white text-sm placeholder-gray-600 focus:border-purple-500/50 focus:outline-none h-48 resize-none font-mono" />
                        <button onClick={handleSaveVersion} disabled={saving || !editContent.trim()}
                          className="w-full mt-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-semibold py-2.5 rounded-xl hover:shadow-lg transition-all disabled:opacity-40">
                          {saving ? '⏳ Saving...' : '💾 Save New Version'}
                        </button>
                      </Card>

                      {/* Version History */}
                      <Card>
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                          📜 History {versions?.total_versions ? `· ${versions.total_versions} versions` : ''}
                        </h3>
                        {versions?.versions?.length > 0 ? (
                          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                            {versions.versions.map((v: any, i: number) => (
                              <div key={v.version} className="glass rounded-xl p-3 animate-slideIn" style={{ animationDelay: `${i * 0.05}s` }}>
                                <div className="flex items-center justify-between mb-1">
                                  <div className="flex items-center gap-2">
                                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                      i === 0 ? 'bg-purple-500/20 text-purple-400' : 'bg-white/5 text-gray-500'
                                    }`}>v{v.version}</span>
                                    <span className="text-sm font-medium text-white">{v.title}</span>
                                  </div>
                                  <span className="text-[10px] text-gray-600">{new Date(v.created_at).toLocaleDateString()}</span>
                                </div>
                                <p className="text-xs text-gray-500 ml-8">{v.change_summary}</p>
                                <button onClick={() => { setEditTitle(v.title); setEditContent(v.content) }}
                                  className="text-[10px] text-purple-400 hover:text-purple-300 ml-8 mt-1 transition-colors">
                                  ↩ Restore this version
                                </button>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500 text-center py-8">No versions yet. Edit and save to start tracking.</p>
                        )}
                      </Card>
                    </div>
                  )}
                </div>
              ) : (
                <EmptyState icon="📝" text="Upload content first to use versioning." />
              )}
            </div>
          )}

        </div>
      </div>

      {/* ─── Footer ─────────────────────────────────────────── */}
      <footer className="relative border-t border-white/5 mt-8">
        <div className="max-w-6xl mx-auto px-4 py-6 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <span>🧠</span>
            <span>MemoryThread · AI for Bharat 2026</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-600">
            <span>Powered by Llama 3.1</span>
            <GlowDot color="bg-purple-500" />
            <span>100% Local</span>
          </div>
        </div>
      </footer>
    </main>
  )
}

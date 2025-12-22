import React, { useEffect, useState, useCallback, useMemo } from 'react'
import './styles.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

// Types
type Project = { id: string; name: string; description: string }
type Doc = { id: string; project: string; title: string; parse_status: string; source_file: string | null }
type TreeNode = { id: string; heading: string; status: string; locked: boolean; order_index: number; depth: number; children: TreeNode[] }
type Block = {
  id: string
  type: 'heading' | 'paragraph' | 'list' | 'image'
  text?: string
  level?: number
  style?: 'bulleted' | 'numbered'
  items?: string[]
  assetId?: string
  caption?: string
  marks?: { type: 'bold' | 'italic' | 'link'; range: [number, number]; href?: string }[]
}
type BlocksPayload = { version: 1; blocks: Block[] }
type Comment = { id: string; section: string; body: string; status: string; created_at: string }
type Snapshot = { id: string; section: string; reason: string | null; blocks_json: BlocksPayload; saved_at: string }
type Template = { id: string; name: string; mapping_json: object }
type AuditLog = { id: string; entity_type: string; entity_id: string; action: string; payload: object; created_at: string }
type PreflightResult = {
  documentId: string
  title: string
  statusCounts: { not_started: number; draft: number; in_review: number; verified: number; total: number }
  allVerified: boolean
  warnings: string[]
  canExport: boolean
}

// API helper
async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (init?.body instanceof FormData) {
    delete headers['Content-Type']
  }
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { ...headers, ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

// Generate unique ID
function uid() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

// Modal Component
function Modal({ open, onClose, title, children, footer }: {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  footer?: React.ReactNode
}) {
  if (!open) return null
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">{title}</h3>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}

// Block Editor Component
function BlockEditor({ blocks, onChange, readOnly = false }: {
  blocks: Block[]
  onChange: (blocks: Block[]) => void
  readOnly?: boolean
}) {
  const updateBlock = (id: string, updates: Partial<Block>) => {
    onChange(blocks.map(b => b.id === id ? { ...b, ...updates } : b))
  }

  const deleteBlock = (id: string) => {
    onChange(blocks.filter(b => b.id !== id))
  }

  const moveBlock = (id: string, direction: 'up' | 'down') => {
    const idx = blocks.findIndex(b => b.id === id)
    if (idx === -1) return
    const newIdx = direction === 'up' ? idx - 1 : idx + 1
    if (newIdx < 0 || newIdx >= blocks.length) return
    const newBlocks = [...blocks]
    ;[newBlocks[idx], newBlocks[newIdx]] = [newBlocks[newIdx], newBlocks[idx]]
    onChange(newBlocks)
  }

  const addBlock = (type: Block['type'], afterId?: string) => {
    const newBlock: Block = {
      id: uid(),
      type,
      ...(type === 'heading' ? { level: 2, text: 'New heading', marks: [] } : {}),
      ...(type === 'paragraph' ? { text: '', marks: [] } : {}),
      ...(type === 'list' ? { style: 'bulleted', items: ['Item 1'] } : {}),
      ...(type === 'image' ? { assetId: 'placeholder', caption: '' } : {}),
    }
    if (afterId) {
      const idx = blocks.findIndex(b => b.id === afterId)
      const newBlocks = [...blocks]
      newBlocks.splice(idx + 1, 0, newBlock)
      onChange(newBlocks)
    } else {
      onChange([...blocks, newBlock])
    }
  }

  const renderBlock = (block: Block) => {
    if (block.type === 'heading') {
      return (
        <div className={`block-content block-heading block-heading-${block.level || 2}`}>
          {readOnly ? (
            block.text
          ) : (
            <input
              type="text"
              value={block.text || ''}
              onChange={e => updateBlock(block.id, { text: e.target.value })}
              className="editable-heading"
              style={{ fontSize: 'inherit', fontWeight: 'inherit' }}
            />
          )}
        </div>
      )
    }
    if (block.type === 'paragraph') {
      return (
        <div className="block-content">
          {readOnly ? (
            <p>{block.text}</p>
          ) : (
            <textarea
              value={block.text || ''}
              onChange={e => updateBlock(block.id, { text: e.target.value })}
              className="textarea"
              rows={2}
              placeholder="Enter paragraph text..."
            />
          )}
        </div>
      )
    }
    if (block.type === 'list') {
      const ListTag = block.style === 'numbered' ? 'ol' : 'ul'
      return (
        <div className="block-content">
          {readOnly ? (
            <ListTag className={`block-list block-list-${block.style}`}>
              {(block.items || []).map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ListTag>
          ) : (
            <div>
              <div style={{ marginBottom: 8 }}>
                <select
                  value={block.style}
                  onChange={e => updateBlock(block.id, { style: e.target.value as 'bulleted' | 'numbered' })}
                  className="select"
                  style={{ width: 'auto' }}
                >
                  <option value="bulleted">Bulleted</option>
                  <option value="numbered">Numbered</option>
                </select>
              </div>
              {(block.items || []).map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
                  <input
                    type="text"
                    value={item}
                    onChange={e => {
                      const newItems = [...(block.items || [])]
                      newItems[i] = e.target.value
                      updateBlock(block.id, { items: newItems })
                    }}
                    className="input"
                  />
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => {
                      const newItems = (block.items || []).filter((_, idx) => idx !== i)
                      updateBlock(block.id, { items: newItems })
                    }}
                  >✕</button>
                </div>
              ))}
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => updateBlock(block.id, { items: [...(block.items || []), ''] })}
              >+ Add item</button>
            </div>
          )}
        </div>
      )
    }
    if (block.type === 'image') {
      return (
        <div className="block-content block-image">
          📷 Image: {block.assetId}
          {block.caption && <div style={{ marginTop: 4, fontStyle: 'italic' }}>{block.caption}</div>}
        </div>
      )
    }
    return null
  }

  return (
    <div className="block-editor">
      {blocks.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <p>No content yet. Add blocks to get started.</p>
        </div>
      )}
      {blocks.map(block => (
        <div key={block.id} className="block-item">
          {!readOnly && (
            <div className="block-toolbar">
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => moveBlock(block.id, 'up')}>↑</button>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => moveBlock(block.id, 'down')}>↓</button>
              <button className="btn btn-ghost btn-icon btn-sm" onClick={() => deleteBlock(block.id)}>🗑</button>
            </div>
          )}
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>
            {block.type.toUpperCase()}{block.type === 'heading' && ` (H${block.level})`}
          </div>
          {renderBlock(block)}
        </div>
      ))}
      {!readOnly && (
        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button className="btn btn-secondary btn-sm" onClick={() => addBlock('heading')}>+ Heading</button>
          <button className="btn btn-secondary btn-sm" onClick={() => addBlock('paragraph')}>+ Paragraph</button>
          <button className="btn btn-secondary btn-sm" onClick={() => addBlock('list')}>+ List</button>
        </div>
      )}
    </div>
  )
}

// Main App Component
export default function App() {
  // State
  const [projects, setProjects] = useState<Project[]>([])
  const [projectId, setProjectId] = useState<string>('')
  const [docs, setDocs] = useState<Doc[]>([])
  const [docId, setDocId] = useState<string>('')
  const [tree, setTree] = useState<TreeNode[]>([])
  const [selectedSectionId, setSelectedSectionId] = useState<string>('')
  const [selectedSection, setSelectedSection] = useState<TreeNode | null>(null)
  const [oldText, setOldText] = useState<string>('')
  const [newBlocks, setNewBlocks] = useState<BlocksPayload>({ version: 1, blocks: [] })
  const [tab, setTab] = useState<'ai' | 'comments' | 'history' | 'audit'>('ai')
  const [comments, setComments] = useState<Comment[]>([])
  const [snapshots, setSnapshots] = useState<Snapshot[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [templates, setTemplates] = useState<Template[]>([])
  const [mergeMode, setMergeMode] = useState(false)
  const [mergeSelected, setMergeSelected] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  // Modals
  const [exportModal, setExportModal] = useState(false)
  const [exportTemplateId, setExportTemplateId] = useState<string>('')
  const [preflight, setPreflight] = useState<PreflightResult | null>(null)
  const [exportJobId, setExportJobId] = useState<string>('')
  const [exportStatus, setExportStatus] = useState<string>('')
  const [exportFile, setExportFile] = useState<string>('')

  const [reopenModal, setReopenModal] = useState(false)
  const [reopenReason, setReopenReason] = useState('')

  // Load projects
  useEffect(() => {
    api<Project[]>('/projects').then(setProjects).catch(() => setProjects([]))
    api<Template[]>('/templates').then(setTemplates).catch(() => setTemplates([]))
  }, [])

  // Load documents when project changes
  useEffect(() => {
    if (!projectId) {
      setDocs([])
      return
    }
    api<Doc[]>(`/projects/${projectId}/documents/list`)
      .then(setDocs)
      .catch(() => setDocs([]))
  }, [projectId])

  // Load audit logs when document changes
  useEffect(() => {
    if (!docId) return
    api<AuditLog[]>(`/documents/${docId}/audit`)
      .then(setAuditLogs)
      .catch(() => setAuditLogs([]))
  }, [docId])

  // Find section in tree
  const findSection = useCallback((nodes: TreeNode[], id: string): TreeNode | null => {
    for (const n of nodes) {
      if (n.id === id) return n
      if (n.children?.length) {
        const found = findSection(n.children, id)
        if (found) return found
      }
    }
    return null
  }, [])

  async function createProject() {
    const name = prompt('Project name?') || 'Untitled'
    const p = await api<Project>('/projects', { method: 'POST', body: JSON.stringify({ name, description: '' }) })
    setProjects([p, ...projects])
    setProjectId(p.id)
  }

  async function uploadDocx() {
    if (!projectId) return alert('Select/create a project first')
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.docx'
    input.onchange = async () => {
      const file = input.files?.[0]
      if (!file) return
      const title = prompt('Document title?') || file.name
      const form = new FormData()
      form.append('title', title)
      form.append('file', file)
      const res = await fetch(`${API_BASE}/projects/${projectId}/documents`, { method: 'POST', body: form })
      if (!res.ok) return alert(await res.text())
      const d = await res.json()
      setDocs([d, ...docs])
      setDocId(d.id)
      // Poll for parse completion
      pollParseStatus(d.id)
    }
    input.click()
  }

  async function pollParseStatus(id: string) {
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 1000))
      const d = await api<Doc>(`/documents/${id}`)
      if (d.parse_status === 'done') {
        refreshTree(id)
        setDocs(docs => docs.map(doc => doc.id === id ? d : doc))
        return
      }
      if (d.parse_status === 'failed') {
        alert('Document parsing failed')
        return
      }
    }
  }

  async function refreshTree(id: string) {
    const t = await api<{ tree: TreeNode[] }>(`/documents/${id}/sections`)
    setTree(t.tree)
    setMergeMode(false)
    setMergeSelected([])
  }

  async function selectSection(id: string) {
    setSelectedSectionId(id)
    const section = findSection(tree, id)
    setSelectedSection(section)
    
    const [oldData, newData, commentsData, snapshotsData] = await Promise.all([
      api<{ old: string }>(`/sections/${id}/old`),
      api<BlocksPayload>(`/sections/${id}/new`),
      api<Comment[]>(`/sections/${id}/comments`),
      api<Snapshot[]>(`/sections/${id}/snapshots`),
    ])
    
    setOldText(oldData.old || '')
    setNewBlocks(newData)
    setComments(commentsData)
    setSnapshots(snapshotsData)
  }

  async function saveNew() {
    if (!selectedSectionId) return
    setLoading(true)
    try {
      await api(`/sections/${selectedSectionId}/new`, { method: 'PUT', body: JSON.stringify(newBlocks) })
      // Refresh tree to get updated status
      if (docId) refreshTree(docId)
      alert('Saved!')
    } catch (e: any) {
      alert(e.message)
    }
    setLoading(false)
  }

  async function copyOldToNew() {
    if (!selectedSectionId) return
    const lines = (oldText || '').split(/\n\n+/).map(s => s.trim()).filter(Boolean)
    const blocks: Block[] = lines.map((t, i) => ({
      id: `p_${i + 1}`,
      type: 'paragraph',
      text: t,
      marks: []
    }))
    setNewBlocks({ version: 1, blocks })
  }

  async function createSnapshot() {
    if (!selectedSectionId) return
    const reason = prompt('Snapshot reason (optional)?') || ''
    const snap = await api<Snapshot>(`/sections/${selectedSectionId}/snapshot`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    })
    setSnapshots([snap, ...snapshots])
    alert('Snapshot created!')
  }

  async function restoreSnapshot(snapshotId: string) {
    if (!selectedSectionId) return
    if (!confirm('Restore this snapshot? Current content will be auto-saved.')) return
    try {
      await api(`/sections/${selectedSectionId}/snapshots/${snapshotId}/restore`, { method: 'POST' })
      selectSection(selectedSectionId)
      alert('Snapshot restored!')
    } catch (e: any) {
      alert(e.message)
    }
  }

  // Status change
  async function changeStatus(newStatus: string) {
    if (!selectedSectionId) return
    
    // If trying to reopen a verified section
    if (selectedSection?.locked && newStatus === 'draft') {
      setReopenModal(true)
      return
    }

    try {
      await api(`/sections/${selectedSectionId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus })
      })
      if (docId) refreshTree(docId)
      const section = findSection(tree, selectedSectionId)
      if (section) setSelectedSection({ ...section, status: newStatus, locked: newStatus === 'verified' })
    } catch (e: any) {
      alert(e.message)
    }
  }

  async function handleReopen() {
    if (!selectedSectionId || !reopenReason.trim()) return
    try {
      await api(`/sections/${selectedSectionId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: 'draft', reopen_reason: reopenReason })
      })
      if (docId) refreshTree(docId)
      setReopenModal(false)
      setReopenReason('')
    } catch (e: any) {
      alert(e.message)
    }
  }

  // Outline operations
  async function renameSection(id: string, newHeading: string) {
    await api(`/sections/${id}`, { method: 'PATCH', body: JSON.stringify({ heading: newHeading }) })
    if (docId) refreshTree(docId)
  }

  async function promoteSection(id: string) {
    const section = findSection(tree, id)
    if (!section || section.depth <= 1) return
    await api(`/sections/${id}`, { method: 'PATCH', body: JSON.stringify({ depth: section.depth - 1, parent: null }) })
    if (docId) refreshTree(docId)
  }

  async function demoteSection(id: string) {
    const section = findSection(tree, id)
    if (!section || section.depth >= 6) return
    await api(`/sections/${id}`, { method: 'PATCH', body: JSON.stringify({ depth: section.depth + 1 }) })
    if (docId) refreshTree(docId)
  }

  async function moveSection(id: string, direction: 'up' | 'down') {
    const section = findSection(tree, id)
    if (!section) return
    const newOrder = direction === 'up' ? section.order_index - 1.5 : section.order_index + 1.5
    await api(`/sections/${id}`, { method: 'PATCH', body: JSON.stringify({ order_index: Math.floor(newOrder) }) })
    if (docId) refreshTree(docId)
  }

  async function mergeSections() {
    if (mergeSelected.length < 2) {
      alert('Select at least 2 sections to merge')
      return
    }
    const targetHeading = prompt('New section heading?') || 'Merged Section'
    try {
      await api('/sections/merge', {
        method: 'POST',
        body: JSON.stringify({ documentId: docId, sourceSectionIds: mergeSelected, targetHeading })
      })
      if (docId) refreshTree(docId)
      setMergeMode(false)
      setMergeSelected([])
      alert('Sections merged!')
    } catch (e: any) {
      alert(e.message)
    }
  }

  // Export
  async function openExportModal() {
    if (!docId) return
    setExportModal(true)
    setExportStatus('')
    setExportFile('')
    setExportJobId('')
    
    try {
      const result = await api<PreflightResult>(`/documents/${docId}/export/preflight`)
      setPreflight(result)
    } catch (e) {
      setPreflight(null)
    }
  }

  async function startExport() {
    if (!docId) return
    
    // Check if admin override is needed (warnings exist but user wants to proceed)
    const needsOverride = preflight && !preflight.allVerified && preflight.warnings.length > 0
    let adminOverride = false
    
    if (needsOverride) {
      const confirmed = confirm(
        `⚠️ Warning: Not all sections are verified.\n\n` +
        `Warnings:\n${preflight.warnings.join('\n')}\n\n` +
        `Do you want to proceed with export anyway? (This will be logged as an admin override.)`
      )
      if (!confirmed) return
      adminOverride = true
    }
    
    setLoading(true)
    try {
      const job = await api<{ id: string }>(`/documents/${docId}/export`, {
        method: 'POST',
        body: JSON.stringify({ 
          templateId: exportTemplateId || null,
          adminOverride: adminOverride
        })
      })
      setExportJobId(job.id)
      setExportStatus('pending')
      pollExportStatus(job.id)
    } catch (e: any) {
      alert(e.message)
      setLoading(false)
    }
  }

  async function pollExportStatus(jobId: string) {
    for (let i = 0; i < 60; i++) {
      await new Promise(r => setTimeout(r, 1000))
      const job = await api<{ status: string; output_file: string | null; error: string }>(`/exports/${jobId}`)
      setExportStatus(job.status)
      if (job.status === 'done' && job.output_file) {
        setExportFile(job.output_file)
        setLoading(false)
        return
      }
      if (job.status === 'failed') {
        alert(`Export failed: ${job.error}`)
        setLoading(false)
        return
      }
    }
    setLoading(false)
  }

  // AI
  async function runAI(preset: string) {
    if (!selectedSectionId) return
    setLoading(true)
    try {
      const blocks = await api<BlocksPayload>('/ai/section', {
        method: 'POST',
        body: JSON.stringify({ sectionId: selectedSectionId, preset, inputs: { old: oldText }, options: {} }),
      })
      const ok = confirm('Apply AI output (replace New content)?')
      if (ok) setNewBlocks(blocks)
    } catch (e: any) {
      alert(e.message)
    }
    setLoading(false)
  }

  // Comments
  async function addComment() {
    if (!selectedSectionId) return
    const body = prompt('Comment?') || ''
    if (!body.trim()) return
    const c = await api<Comment>(`/sections/${selectedSectionId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body })
    })
    setComments([c, ...comments])
  }

  // Render section tree
  function renderTree(nodes: TreeNode[], depth = 0) {
    return (
      <div className="section-tree">
        {nodes.map(n => (
          <div key={n.id}>
            <div
              className={`section-item ${selectedSectionId === n.id ? 'selected' : ''}`}
              style={{ marginLeft: depth * 16 }}
              onClick={() => !mergeMode && selectSection(n.id)}
            >
              {mergeMode && (
                <input
                  type="checkbox"
                  className="merge-checkbox"
                  checked={mergeSelected.includes(n.id)}
                  onChange={e => {
                    if (e.target.checked) setMergeSelected([...mergeSelected, n.id])
                    else setMergeSelected(mergeSelected.filter(id => id !== n.id))
                  }}
                  onClick={e => e.stopPropagation()}
                />
              )}
              <div className="section-item-content">
                <div className="section-heading">{n.heading || '(Untitled)'}</div>
                <div className="section-meta">
                  <span className={`status-badge status-${n.status}`}>{n.status.replace('_', ' ')}</span>
                  {n.locked && <span className="lock-icon">🔒</span>}
                </div>
              </div>
              {!mergeMode && (
                <div className="section-actions">
                  <button className="btn btn-ghost btn-icon btn-sm" onClick={e => { e.stopPropagation(); promoteSection(n.id) }} title="Promote">⬆</button>
                  <button className="btn btn-ghost btn-icon btn-sm" onClick={e => { e.stopPropagation(); demoteSection(n.id) }} title="Demote">⬇</button>
                  <button className="btn btn-ghost btn-icon btn-sm" onClick={e => { e.stopPropagation(); moveSection(n.id, 'up') }} title="Move up">↑</button>
                  <button className="btn btn-ghost btn-icon btn-sm" onClick={e => { e.stopPropagation(); moveSection(n.id, 'down') }} title="Move down">↓</button>
                </div>
              )}
            </div>
            {n.children?.length > 0 && renderTree(n.children, depth + 1)}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="app-container">
      {/* Left Panel - Projects / Documents / Outline */}
      <div className="panel">
        <div className="panel-header">
          Paperless Modernizer
        </div>
        <div className="panel-content">
          {/* Projects */}
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <select
                className="select"
                value={projectId}
                onChange={e => { setProjectId(e.target.value); setDocId(''); setTree([]) }}
              >
                <option value="">Select project...</option>
                {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <button className="btn btn-secondary btn-sm" onClick={createProject}>+</button>
            </div>
          </div>

          {/* Documents */}
          {projectId && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <strong>Documents</strong>
                <button className="btn btn-primary btn-sm" onClick={uploadDocx}>Upload DOCX</button>
              </div>
              {docs.length === 0 && <div className="empty-state" style={{ padding: 16 }}>No documents yet</div>}
              {docs.map(d => (
                <div
                  key={d.id}
                  className={`document-item ${docId === d.id ? 'selected' : ''}`}
                  onClick={() => { setDocId(d.id); refreshTree(d.id) }}
                  style={docId === d.id ? { borderColor: 'var(--accent-primary)', background: 'var(--accent-light)' } : {}}
                >
                  <span className="document-title">{d.title}</span>
                  <span className={`parse-status parse-status-${d.parse_status}`}>{d.parse_status}</span>
                </div>
              ))}
            </div>
          )}

          <div className="divider" />

          {/* Outline */}
          {docId && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <strong>Outline</strong>
                <div style={{ display: 'flex', gap: 4 }}>
                  {!mergeMode ? (
                    <button className="btn btn-secondary btn-sm" onClick={() => setMergeMode(true)}>Merge</button>
                  ) : (
                    <>
                      <button className="btn btn-primary btn-sm" onClick={mergeSections}>Confirm ({mergeSelected.length})</button>
                      <button className="btn btn-ghost btn-sm" onClick={() => { setMergeMode(false); setMergeSelected([]) }}>Cancel</button>
                    </>
                  )}
                  <button className="btn btn-primary btn-sm" onClick={openExportModal}>Export</button>
                </div>
              </div>
              {tree.length > 0 ? renderTree(tree) : (
                <div className="empty-state" style={{ padding: 16 }}>
                  {loading ? <span className="spinner" /> : 'No sections parsed yet'}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Center Panel - Editor */}
      <div className="panel">
        <div className="panel-header">
          {selectedSection ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, flex: 1 }}>
              <input
                type="text"
                className="editable-heading"
                value={selectedSection.heading}
                onChange={e => renameSection(selectedSectionId, e.target.value)}
                style={{ fontSize: '1.1rem', fontWeight: 600, flex: 1 }}
              />
              <select
                className="select"
                value={selectedSection.status}
                onChange={e => changeStatus(e.target.value)}
                disabled={selectedSection.locked && selectedSection.status === 'verified'}
                style={{ width: 'auto' }}
              >
                <option value="not_started">Not Started</option>
                <option value="draft">Draft</option>
                <option value="in_review">In Review</option>
                <option value="verified">Verified</option>
              </select>
              {selectedSection.locked && (
                <button className="btn btn-secondary btn-sm" onClick={() => setReopenModal(true)}>Reopen</button>
              )}
            </div>
          ) : (
            'Editor'
          )}
        </div>
        <div className="panel-content">
          {!selectedSectionId ? (
            <div className="empty-state">
              <div className="empty-state-icon">📄</div>
              <p>Select a section from the outline to edit</p>
            </div>
          ) : (
            <div className="editor-container">
              {/* Old content (read-only) */}
              <div className="editor-pane">
                <div className="editor-header">
                  <span className="editor-title">Original Content</span>
                  <button className="btn btn-secondary btn-sm" onClick={copyOldToNew}>Copy to New →</button>
                </div>
                <div className="editor-content">
                  <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '0.9rem', lineHeight: 1.8, color: 'var(--text-secondary)' }}>
                    {oldText || '(No original content)'}
                  </div>
                </div>
              </div>

              {/* New content (editable) */}
              <div className="editor-pane">
                <div className="editor-header">
                  <span className="editor-title">New Content</span>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn btn-secondary btn-sm" onClick={createSnapshot}>Snapshot</button>
                    <button className="btn btn-primary btn-sm" onClick={saveNew} disabled={loading || selectedSection?.locked}>
                      {loading ? <span className="spinner" /> : 'Save'}
                    </button>
                  </div>
                </div>
                <div className="editor-content">
                  <BlockEditor
                    blocks={newBlocks.blocks}
                    onChange={blocks => setNewBlocks({ version: 1, blocks })}
                    readOnly={selectedSection?.locked}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Tabs */}
      <div className="panel">
        <div className="tabs">
          <button className={`tab ${tab === 'ai' ? 'active' : ''}`} onClick={() => setTab('ai')}>AI Tools</button>
          <button className={`tab ${tab === 'comments' ? 'active' : ''}`} onClick={() => setTab('comments')}>Comments</button>
          <button className={`tab ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>History</button>
          <button className={`tab ${tab === 'audit' ? 'active' : ''}`} onClick={() => setTab('audit')}>Audit</button>
        </div>
        <div className="panel-content">
          {/* AI Tools */}
          {tab === 'ai' && (
            <div>
              <p style={{ marginBottom: 16, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                AI presets help modernize section content. Select a section and run a preset.
              </p>
              <div style={{ display: 'grid', gap: 8 }}>
                <button className="btn btn-secondary" disabled={!selectedSectionId || loading} onClick={() => runAI('modernize')}>
                  ✨ Modernize Language
                </button>
                <button className="btn btn-secondary" disabled={!selectedSectionId || loading} onClick={() => runAI('grammar')}>
                  📝 Fix Grammar
                </button>
                <button className="btn btn-secondary" disabled={!selectedSectionId || loading} onClick={() => runAI('bullets')}>
                  • Convert to Bullets
                </button>
                <button className="btn btn-secondary" disabled={!selectedSectionId || loading} onClick={() => runAI('simplify')}>
                  🔤 Simplify Text
                </button>
              </div>
              <div style={{ marginTop: 16, padding: 12, background: 'var(--bg-secondary)', borderRadius: 8, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Note: AI is using a stub provider. Replace with real AI provider for production use.
              </div>
            </div>
          )}

          {/* Comments */}
          {tab === 'comments' && (
            <div>
              <button className="btn btn-primary" style={{ marginBottom: 16 }} onClick={addComment} disabled={!selectedSectionId}>
                + Add Comment
              </button>
              {comments.length === 0 && (
                <div className="empty-state" style={{ padding: 16 }}>No comments yet</div>
              )}
              {comments.map(c => (
                <div key={c.id} className="comment-card">
                  <div className="comment-header">
                    <span className={`status-badge status-${c.status === 'resolved' ? 'verified' : 'draft'}`}>{c.status}</span>
                    <span>{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                  <div className="comment-body">{c.body}</div>
                </div>
              ))}
            </div>
          )}

          {/* History / Snapshots */}
          {tab === 'history' && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <button className="btn btn-secondary" onClick={createSnapshot} disabled={!selectedSectionId}>
                  Create Snapshot
                </button>
              </div>
              {snapshots.length === 0 && (
                <div className="empty-state" style={{ padding: 16 }}>No snapshots yet</div>
              )}
              {snapshots.map(s => (
                <div key={s.id} className="snapshot-item">
                  <div className="snapshot-info">
                    <div className="snapshot-time">{new Date(s.saved_at).toLocaleString()}</div>
                    {s.reason && <div className="snapshot-reason">{s.reason}</div>}
                  </div>
                  <button className="btn btn-secondary btn-sm" onClick={() => restoreSnapshot(s.id)}>Restore</button>
                </div>
              ))}
            </div>
          )}

          {/* Audit Log */}
          {tab === 'audit' && (
            <div>
              {auditLogs.length === 0 && (
                <div className="empty-state" style={{ padding: 16 }}>No audit logs yet</div>
              )}
              {auditLogs.map(log => (
                <div key={log.id} className="audit-item">
                  <div className="audit-action">{log.action}</div>
                  <div className="audit-time">{new Date(log.created_at).toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Export Modal */}
      <Modal
        open={exportModal}
        onClose={() => setExportModal(false)}
        title="Export Document"
        footer={
          exportStatus === 'done' ? (
            <a href={`${API_BASE.replace('/api', '')}/media/${exportFile}`} className="btn btn-primary" download>
              Download DOCX
            </a>
          ) : (
            <>
              <button className="btn btn-ghost" onClick={() => setExportModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={startExport} disabled={loading || exportStatus === 'running'}>
                {loading ? <span className="spinner" /> : 'Start Export'}
              </button>
            </>
          )
        }
      >
        {preflight && (
          <div>
            <h4 style={{ marginBottom: 12 }}>Preflight Check</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 16 }}>
              <div>Total sections: <strong>{preflight.statusCounts.total}</strong></div>
              <div>Verified: <strong style={{ color: 'var(--success)' }}>{preflight.statusCounts.verified}</strong></div>
              <div>In Review: <strong>{preflight.statusCounts.in_review}</strong></div>
              <div>Draft: <strong>{preflight.statusCounts.draft}</strong></div>
            </div>

            {preflight.warnings.length > 0 && (
              <div className="warning-box">
                <div className="warning-title">⚠️ Warnings</div>
                <ul className="warning-list">
                  {preflight.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            {preflight.allVerified && (
              <div className="success-box">
                ✓ All sections are verified and ready for export!
              </div>
            )}

            <div className="divider" />

            <div className="input-group" style={{ marginBottom: 16 }}>
              <label className="input-label">Template</label>
              <select
                className="select"
                value={exportTemplateId}
                onChange={e => setExportTemplateId(e.target.value)}
              >
                <option value="">Default Template</option>
                {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>

            {exportStatus && (
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                {exportStatus === 'running' && (
                  <div><span className="spinner" /> Generating document...</div>
                )}
                {exportStatus === 'done' && (
                  <div className="success-box">✓ Export complete! Click Download to get your file.</div>
                )}
                {exportStatus === 'failed' && (
                  <div style={{ color: 'var(--error)' }}>Export failed. Please try again.</div>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Reopen Modal */}
      <Modal
        open={reopenModal}
        onClose={() => { setReopenModal(false); setReopenReason('') }}
        title="Reopen Section"
        footer={
          <>
            <button className="btn btn-ghost" onClick={() => { setReopenModal(false); setReopenReason('') }}>Cancel</button>
            <button className="btn btn-primary" onClick={handleReopen} disabled={!reopenReason.trim()}>Reopen</button>
          </>
        }
      >
        <p style={{ marginBottom: 16, color: 'var(--text-secondary)' }}>
          This section is verified and locked. Please provide a reason to reopen it for editing.
        </p>
        <div className="input-group">
          <label className="input-label">Reason for reopening</label>
          <textarea
            className="textarea"
            value={reopenReason}
            onChange={e => setReopenReason(e.target.value)}
            placeholder="Enter reason..."
            rows={3}
          />
        </div>
      </Modal>
    </div>
  )
}

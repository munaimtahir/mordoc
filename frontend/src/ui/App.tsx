import React, { useEffect, useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

type Project = { id: string; name: string; description: string }
type Doc = { id: string; project: string; title: string; parse_status: string; source_file: string | null }
type TreeNode = { id: string; heading: string; status: string; locked: boolean; order_index: number; depth: number; children: TreeNode[] }

type BlocksPayload = { version: 1; blocks: any[] }

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ borderRight: '1px solid #eee', height: '100%', overflow: 'auto' }}>
      <div style={{ padding: 10, borderBottom: '1px solid #eee', fontWeight: 600 }}>{title}</div>
      <div style={{ padding: 10 }}>{children}</div>
    </div>
  )
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export default function App() {
  const [projects, setProjects] = useState<Project[]>([])
  const [projectId, setProjectId] = useState<string>('')
  const [docs, setDocs] = useState<Doc[]>([])
  const [docId, setDocId] = useState<string>('')
  const [tree, setTree] = useState<TreeNode[]>([])
  const [selectedSectionId, setSelectedSectionId] = useState<string>('')

  const [oldText, setOldText] = useState<string>('')
  const [newBlocks, setNewBlocks] = useState<BlocksPayload>({ version: 1, blocks: [] })

  const [tab, setTab] = useState<'ai'|'comments'|'history'|'qa'>('ai')
  const [comments, setComments] = useState<any[]>([])

  useEffect(() => {
    api<Project[]>('/projects').then(setProjects).catch(() => setProjects([]))
  }, [])

  useEffect(() => {
    if (!projectId) return
    // v1: naive — filter docs by project by scanning all docs isn't available yet; docs list endpoint not in v1 stub.
    setDocs([])
  }, [projectId])

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
      const res = await fetch(`${API_BASE}/projects/${projectId}/documents`, { method: 'POST', body: form as any })
      if (!res.ok) return alert(await res.text())
      const d = await res.json()
      setDocs([d, ...docs])
      setDocId(d.id)
      setTimeout(() => refreshTree(d.id), 1200)
    }
    input.click()
  }

  async function refreshTree(id: string) {
    const t = await api<{tree: TreeNode[]}>(`/documents/${id}/sections`)
    setTree(t.tree)
  }

  async function selectSection(id: string) {
    setSelectedSectionId(id)
    const o = await api<{old: string}>(`/sections/${id}/old`)
    setOldText(o.old || '')
    const n = await api<BlocksPayload>(`/sections/${id}/new`)
    setNewBlocks(n)
    const c = await api<any[]>(`/sections/${id}/comments`)
    setComments(c)
  }

  async function saveNew() {
    if (!selectedSectionId) return
    await api(`/sections/${selectedSectionId}/new`, { method: 'PUT', body: JSON.stringify(newBlocks) })
    alert('Saved')
  }

  async function copyOldToNew() {
    if (!selectedSectionId) return
    const lines = (oldText || '').split(/\n\n+/).map(s => s.trim()).filter(Boolean)
    const blocks = lines.map((t, i) => ({ id: `p_${i+1}`, type: 'paragraph', text: t, marks: [] }))
    setNewBlocks({ version: 1, blocks })
  }

  function renderTree(nodes: TreeNode[], depth=0) {
    return (
      <div>
        {nodes.map(n => (
          <div key={n.id} style={{ marginLeft: depth * 12, padding: '4px 0' }}>
            <button onClick={() => selectSection(n.id)} style={{ width: '100%', textAlign: 'left' }}>
              {n.heading || '(Untitled)'}{' '}
              <span style={{ opacity: 0.6 }}>[{n.status}{n.locked ? ', locked' : ''}]</span>
            </button>
            {n.children?.length ? renderTree(n.children, depth+1) : null}
          </div>
        ))}
      </div>
    )
  }

  async function runAI(preset: string) {
    if (!selectedSectionId) return
    const blocks = await api<BlocksPayload>('/ai/section', {
      method: 'POST',
      body: JSON.stringify({ sectionId: selectedSectionId, preset, inputs: { old: oldText }, options: {} }),
    })
    const ok = confirm('Apply AI output (replace New)?')
    if (ok) setNewBlocks(blocks)
  }

  async function addComment() {
    if (!selectedSectionId) return
    const body = prompt('Comment?') || ''
    if (!body.trim()) return
    const c = await api<any>(`/sections/${selectedSectionId}/comments`, { method: 'POST', body: JSON.stringify({ body }) })
    setComments([c, ...comments])
  }

  return (
    <div style={{ height: '100vh', display: 'grid', gridTemplateColumns: '320px 1fr 340px' }}>
      <Panel title="Projects / Documents">
        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          <button onClick={createProject}>+ Project</button>
          <select value={projectId} onChange={e => setProjectId(e.target.value)}>
            <option value="">Select project</option>
            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
          <button onClick={uploadDocx}>Upload DOCX</button>
          <button onClick={() => docId && refreshTree(docId)} disabled={!docId}>Refresh</button>
        </div>

        <div style={{ marginBottom: 10 }}>
          <input placeholder="Document ID (paste)" value={docId} onChange={e => setDocId(e.target.value)} style={{ width: '100%' }} />
          <button style={{ marginTop: 6 }} onClick={() => docId && refreshTree(docId)} disabled={!docId}>Open Document</button>
        </div>

        <div style={{ fontWeight: 600, marginTop: 10 }}>Outline</div>
        {tree.length ? renderTree(tree) : <div style={{ opacity: 0.7 }}>No document loaded.</div>}
      </Panel>

      <Panel title="Editor (Old | New)">
        {!selectedSectionId ? (
          <div style={{ opacity: 0.7 }}>Select a section from the outline.</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Old (read-only)</div>
              <textarea value={oldText} readOnly style={{ width: '100%', height: '72vh' }} />
            </div>
            <div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                <div style={{ fontWeight: 600 }}>New (blocks)</div>
                <button onClick={copyOldToNew}>Copy Old → New</button>
                <button onClick={saveNew}>Save</button>
              </div>
              <textarea
                value={JSON.stringify(newBlocks, null, 2)}
                onChange={e => {
                  try { setNewBlocks(JSON.parse(e.target.value)) } catch { /* ignore */ }
                }}
                style={{ width: '100%', height: '72vh' }}
              />
              <div style={{ opacity: 0.7, marginTop: 6 }}>
                v1 UI uses JSON editor for blocks; replace with proper block editor later (still v1-safe).
              </div>
            </div>
          </div>
        )}
      </Panel>

      <Panel title="Right Panel">
        <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
          <button onClick={() => setTab('ai')}>AI Tools</button>
          <button onClick={() => setTab('comments')}>Comments</button>
          <button onClick={() => setTab('history')}>History</button>
          <button onClick={() => setTab('qa')}>QA</button>
        </div>

        {tab === 'ai' && (
          <div style={{ display: 'grid', gap: 8 }}>
            <button disabled={!selectedSectionId} onClick={() => runAI('modernize')}>Modernize</button>
            <button disabled={!selectedSectionId} onClick={() => runAI('grammar')}>Grammar</button>
            <button disabled={!selectedSectionId} onClick={() => runAI('bullets')}>To bullets</button>
            <button disabled={!selectedSectionId} onClick={() => runAI('infographic_ready')}>Infographic-ready</button>
            <div style={{ opacity: 0.7 }}>
              AI is stubbed in v1 scaffold; swap provider later (hybrid-later).
            </div>
          </div>
        )}

        {tab === 'comments' && (
          <div>
            <button disabled={!selectedSectionId} onClick={addComment}>+ Add comment</button>
            <div style={{ marginTop: 10, display: 'grid', gap: 10 }}>
              {comments.map(c => (
                <div key={c.id} style={{ border: '1px solid #eee', padding: 8 }}>
                  <div style={{ fontSize: 12, opacity: 0.7 }}>{c.status} · {c.created_at}</div>
                  <div>{c.body}</div>
                </div>
              ))}
              {!comments.length && <div style={{ opacity: 0.7 }}>No comments.</div>}
            </div>
          </div>
        )}

        {tab === 'history' && (
          <div style={{ opacity: 0.7 }}>
            v1 scaffold: snapshots endpoint exists. UI not wired yet.
          </div>
        )}

        {tab === 'qa' && (
          <div style={{ opacity: 0.7 }}>
            v1 scaffold: QA checks planned (terminology dictionary, consistency) — not implemented in UI yet.
          </div>
        )}
      </Panel>
    </div>
  )
}

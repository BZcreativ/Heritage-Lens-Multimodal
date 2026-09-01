import { useCallback, useEffect, useState } from 'react'
import { Trash2 } from 'lucide-react'
import * as api from '../lib/api'
import type { CorpusSource } from '../lib/types'
import { useStatus } from '../context/StatusContext'
import { useUI } from '../context/UIContext'
import { ConfirmDialog } from '../components/ConfirmDialog'

function badgeType(s: CorpusSource): 'pdf' | 'img' | 'vid' {
  const st = (s.source_type || '').toLowerCase()
  if (s.modality || st === 'video') return 'vid'
  if (st === 'image' || st === 'photograph' || st === 'figure') return 'img'
  return 'pdf'
}

export function SourcesView() {
  const { refresh } = useStatus()
  const { toast } = useUI()
  const [sources, setSources] = useState<CorpusSource[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<CorpusSource | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(() => {
    return api
      .getSources()
      .then((r) => setSources(r.sources))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const confirmDelete = async () => {
    if (!pending) return
    const name = pending.source_name
    setDeleting(true)
    try {
      await api.deleteSource(name)
      await load()
      refresh()
      toast(`Removed ${name}`)
    } catch (e) {
      toast(e instanceof Error ? e.message : String(e))
    } finally {
      setDeleting(false)
      setPending(null)
    }
  }

  return (
    <div className="view-wrap">
      <div className="view-head">
        <h2>Corpus Sources</h2>
        <p>Every document indexed in the research corpus, with attribution metadata.</p>
      </div>

      {error && <div className="empty-note" style={{ color: 'var(--bad)' }}>{error}</div>}
      {!sources && !error && <div className="empty-note">Loading sources…</div>}
      {sources && sources.length === 0 && <div className="empty-note">No sources indexed yet.</div>}

      {sources?.map((s) => {
        const sub = [s.author !== 'Unknown' ? s.author : null, s.source_type, s.institution]
          .filter(Boolean)
          .join(' · ')
        return (
          <div className="src-row" key={s.source_name}>
            <span className={`src-type ${badgeType(s)}`}>{badgeType(s)}</span>
            <div className="meta">
              <div className="name">{s.source_name}</div>
              {sub && <div className="sub">{sub}</div>}
            </div>
            <span className="cnt">{s.chunk_count} chunks</span>
            <button
              className="src-del"
              onClick={() => setPending(s)}
              aria-label={`Delete ${s.source_name}`}
              title="Delete source"
            >
              <Trash2 />
            </button>
          </div>
        )
      })}

      <ConfirmDialog
        open={pending !== null}
        title="Delete source"
        message={
          pending
            ? `Permanently remove “${pending.source_name}” (${pending.chunk_count} chunks)? This deletes its vectors and files and cannot be undone.`
            : ''
        }
        busy={deleting}
        onConfirm={confirmDelete}
        onCancel={() => !deleting && setPending(null)}
      />
    </div>
  )
}

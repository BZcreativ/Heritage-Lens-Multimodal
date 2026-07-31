import { useCallback, useEffect, useState } from 'react'
import { Trash2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation()
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
      toast(t('sourcesView.removed', { name }))
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
        <h2>{t('sourcesView.title')}</h2>
        <p>{t('sourcesView.desc')}</p>
      </div>

      {error && <div className="empty-note" style={{ color: 'var(--bad)' }}>{error}</div>}
      {!sources && !error && <div className="empty-note">{t('sourcesView.loading')}</div>}
      {sources && sources.length === 0 && <div className="empty-note">{t('sourcesView.none')}</div>}

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
            <span className="cnt">{t('sourcesView.chunks', { count: s.chunk_count })}</span>
            <button
              className="src-del"
              onClick={() => setPending(s)}
              aria-label={t('sourcesView.deleteAria', { name: s.source_name })}
              title={t('sourcesView.deleteSource')}
            >
              <Trash2 />
            </button>
          </div>
        )
      })}

      <ConfirmDialog
        open={pending !== null}
        title={t('sourcesView.confirmTitle')}
        message={
          pending
            ? t('sourcesView.confirmMsg', { name: pending.source_name, count: pending.chunk_count })
            : ''
        }
        busy={deleting}
        onConfirm={confirmDelete}
        onCancel={() => !deleting && setPending(null)}
      />
    </div>
  )
}

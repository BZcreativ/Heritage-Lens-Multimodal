import { Clock, ChevronDown, Download } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useSearch } from '../context/SearchContext'
import { useStatus } from '../context/StatusContext'
import { useUI } from '../context/UIContext'
import { EpistemicPanel } from './EpistemicPanel'
import type { AnswerMode } from '../lib/types'

const MODE_KEY: Record<AnswerMode, string> = {
  'Strict Corpus-Only': 'sidebar.modeStrict',
  'Corpus + Background': 'sidebar.modeBackground',
  Exploratory: 'sidebar.modeExploratory',
}

const sessionStartDate = new Date()

export function RightRail() {
  const { t, i18n } = useTranslation()
  const { result, history, mode, runSearch } = useSearch()
  const { status } = useStatus()
  const { sessionMasked, toggleSessionMask, toast, showLayers } = useUI()

  const sessionStart = sessionStartDate.toLocaleString(i18n.language, {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })

  return (
    <aside className="rail">
      {result && showLayers && <EpistemicPanel epistemic={result.epistemic} />}

      <div>
        <div
          className="side-label"
          style={{ paddingLeft: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <Clock size={14} />
            {t('rail.sessionOverview')}
          </span>
          <button
            className="mask-btn"
            aria-expanded={!sessionMasked}
            onClick={toggleSessionMask}
            title={sessionMasked ? t('rail.show') : t('rail.hide')}
          >
            <ChevronDown />
          </button>
        </div>
        <div className={`rail-collapsible${sessionMasked ? ' masked' : ''}`}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginTop: 8 }}>
            <div className="rail-row"><span>{t('rail.started')}</span><b>{sessionStart}</b></div>
            <div className="rail-row"><span>{t('rail.mode')}</span><b>{t(MODE_KEY[mode])}</b></div>
            <div className="rail-row"><span>{t('rail.sourcesIndexed')}</span><b>{status?.source_count ?? '—'}</b></div>
            <div className="rail-row"><span>{t('rail.exchanges')}</span><b>{history.length}</b></div>
          </div>
          <button
            className="ghost-btn"
            style={{ width: '100%', justifyContent: 'center', marginTop: 13 }}
            onClick={() => toast(t('rail.exportSoon'))}
          >
            <Download />
            {t('rail.exportSession')}
          </button>
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 18 }}>
        <div className="side-label" style={{ paddingLeft: 0 }}>{t('rail.recentQueries')}</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
          {history.length === 0 && <div className="empty-note">{t('rail.noQueries')}</div>}
          {history.map((q) => (
            <button key={q} className="hist-row" onClick={() => runSearch(q)} title={q}>
              <Clock />
              <span>{q}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}

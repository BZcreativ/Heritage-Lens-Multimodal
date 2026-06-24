import { Clock, ChevronDown, Download } from 'lucide-react'
import { useSearch } from '../context/SearchContext'
import { useStatus } from '../context/StatusContext'
import { useUI } from '../context/UIContext'
import { EpistemicPanel } from './EpistemicPanel'

const sessionStart = new Date().toLocaleString('en-GB', {
  day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
})

export function RightRail() {
  const { result, history, mode, runSearch } = useSearch()
  const { status } = useStatus()
  const { sessionMasked, toggleSessionMask, toast, showLayers } = useUI()

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
            Session Overview
          </span>
          <button
            className="mask-btn"
            aria-expanded={!sessionMasked}
            onClick={toggleSessionMask}
            title={sessionMasked ? 'Show' : 'Hide'}
          >
            <ChevronDown />
          </button>
        </div>
        <div className={`rail-collapsible${sessionMasked ? ' masked' : ''}`}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 9, marginTop: 8 }}>
            <div className="rail-row"><span>Started</span><b>{sessionStart}</b></div>
            <div className="rail-row"><span>Mode</span><b>{mode}</b></div>
            <div className="rail-row"><span>Sources Indexed</span><b>{status?.source_count ?? '—'}</b></div>
            <div className="rail-row"><span>Exchanges</span><b>{history.length}</b></div>
          </div>
          <button
            className="ghost-btn"
            style={{ width: '100%', justifyContent: 'center', marginTop: 13 }}
            onClick={() => toast('Session export coming soon')}
          >
            <Download />
            Export Session
          </button>
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 18 }}>
        <div className="side-label" style={{ paddingLeft: 0 }}>Recent queries</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
          {history.length === 0 && <div className="empty-note">No queries yet.</div>}
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

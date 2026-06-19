import { Clock } from 'lucide-react'
import { useNav } from '../context/NavContext'
import { useSearch } from '../context/SearchContext'

export function SessionsView() {
  const { history, runSearch } = useSearch()
  const { setView } = useNav()

  const rerun = (q: string) => {
    setView('ask')
    runSearch(q)
  }

  return (
    <div className="view-wrap">
      <div className="view-head">
        <h2>Sessions</h2>
        <p>Your recent queries this browser. Click any to re-run it.</p>
      </div>

      {history.length === 0 && <div className="empty-note">No queries yet — ask something to get started.</div>}
      {history.map((q) => (
        <button key={q} className="src-row" style={{ width: '100%', textAlign: 'left', cursor: 'pointer' }} onClick={() => rerun(q)}>
          <Clock size={16} style={{ color: 'var(--text-faint)', marginTop: 2 }} />
          <div className="meta">
            <div className="name" style={{ fontWeight: 500 }}>{q}</div>
          </div>
        </button>
      ))}
    </div>
  )
}

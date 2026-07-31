import { Clock } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNav } from '../context/NavContext'
import { useSearch } from '../context/SearchContext'

export function SessionsView() {
  const { t } = useTranslation()
  const { history, runSearch } = useSearch()
  const { setView } = useNav()

  const rerun = (q: string) => {
    setView('ask')
    runSearch(q)
  }

  return (
    <div className="view-wrap">
      <div className="view-head">
        <h2>{t('sessionsView.title')}</h2>
        <p>{t('sessionsView.desc')}</p>
      </div>

      {history.length === 0 && <div className="empty-note">{t('sessionsView.none')}</div>}
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

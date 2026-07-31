import { AlertTriangle, FileWarning, Search, Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Epistemic } from '../lib/types'

const LEVEL_KEY: Record<string, string> = { low: 'epistemic.levelLow', moderate: 'epistemic.levelModerate', high: 'epistemic.levelHigh' }

function ConfidenceBar({ segments }: { segments: number }) {
  return (
    <div className="confbar">
      {[1, 2, 3, 4].map((i) => (
        <span key={i} className={`seg${i <= segments ? ` on l${i}` : ''}`} />
      ))}
    </div>
  )
}

export function EpistemicPanel({ epistemic }: { epistemic: Epistemic }) {
  const { t } = useTranslation()
  const c = epistemic.confidence
  return (
    <article className="panel epi">
      <div className="panel-head">
        <div className="pico">
          <AlertTriangle />
        </div>
        <h2>{t('epistemic.title')}</h2>
        <span className="ptag">{t('epistemic.tag')}</span>
      </div>
      <div className="panel-body">
        <div className="epi-grid">
          <div className="epi-card bias">
            <div className="eh">
              <AlertTriangle />
              {t('epistemic.sourceBias')}
            </div>
            <p>{epistemic.source_bias || t('epistemic.noBias')}</p>
          </div>
          <div className="epi-card abs">
            <div className="eh">
              <FileWarning />
              {t('epistemic.absences')}
            </div>
            <p>{epistemic.absences || t('epistemic.noAbsences')}</p>
          </div>
          <div className="epi-card lim">
            <div className="eh">
              <Search />
              {t('epistemic.interpretiveLimits')}
            </div>
            <p>{epistemic.interpretive_limits || t('epistemic.noLimits')}</p>
          </div>
          <div className="epi-card conf">
            <div className="eh">
              <Check />
              {t('epistemic.confidence')}
            </div>
            <ConfidenceBar segments={c.segments} />
            <div className="conf-row">
              <span className="conf-label">{t(LEVEL_KEY[c.level] ?? 'epistemic.levelModerate')}</span>
              {c.note && <span className="conf-pct">{c.note}</span>}
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}

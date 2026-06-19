import { AlertTriangle, FileWarning, Search, Check } from 'lucide-react'
import type { Epistemic } from '../lib/types'

const LEVEL_LABEL: Record<string, string> = { low: 'Low', moderate: 'Moderate', high: 'High' }

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
  const c = epistemic.confidence
  return (
    <article className="panel epi">
      <div className="panel-head">
        <div className="pico">
          <AlertTriangle />
        </div>
        <h2>What the System Doesn&rsquo;t Know</h2>
        <span className="ptag">Epistemic</span>
      </div>
      <div className="panel-body">
        <div className="epi-grid">
          <div className="epi-card bias">
            <div className="eh">
              <AlertTriangle />
              Source Bias
            </div>
            <p>{epistemic.source_bias || 'No specific source-bias notes for this query.'}</p>
          </div>
          <div className="epi-card abs">
            <div className="eh">
              <FileWarning />
              Absences
            </div>
            <p>{epistemic.absences || 'No specific absences flagged for this query.'}</p>
          </div>
          <div className="epi-card lim">
            <div className="eh">
              <Search />
              Interpretive Limits
            </div>
            <p>{epistemic.interpretive_limits || 'No specific interpretive limits flagged.'}</p>
          </div>
          <div className="epi-card conf">
            <div className="eh">
              <Check />
              Confidence
            </div>
            <ConfidenceBar segments={c.segments} />
            <div className="conf-row">
              <span className="conf-label">{LEVEL_LABEL[c.level] ?? 'Moderate'}</span>
              {c.note && <span className="conf-pct">{c.note}</span>}
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}

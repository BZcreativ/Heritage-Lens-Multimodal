import { useState } from 'react'
import { BookOpen, ChevronDown } from 'lucide-react'
import type { SourceItem } from '../lib/types'

function SourceRow({ src }: { src: SourceItem }) {
  const [open, setOpen] = useState(false)
  const entries = Object.entries(src.meta)
  return (
    <div className={`src${open ? ' open' : ''}`}>
      <button className="src-head" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        <span className="src-num">{src.n}</span>
        <span className="src-main">
          <span className="src-title">{src.title}</span>
          {src.subtitle && <span className="src-sub">{src.subtitle}</span>}
        </span>
        <span className={`src-type ${src.type}`}>{src.type}</span>
        <ChevronDown className="src-chev" />
      </button>
      <div className="src-detail">
        <dl className="src-detail-inner">
          {entries.map(([k, v]) => (
            <div key={k} style={{ display: 'contents' }}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  )
}

export function SourcesPanel({ sources }: { sources: SourceItem[] }) {
  return (
    <article className="panel sources">
      <div className="panel-head">
        <div className="pico">
          <BookOpen />
        </div>
        <h2>Sources</h2>
        <span className="ptag">{sources.length} cited</span>
      </div>
      <div className="panel-body">
        {sources.length === 0 && <p className="empty-note">No sources were retrieved for this query.</p>}
        {sources.map((s) => (
          <SourceRow key={`${s.n}-${s.title}`} src={s} />
        ))}
      </div>
    </article>
  )
}

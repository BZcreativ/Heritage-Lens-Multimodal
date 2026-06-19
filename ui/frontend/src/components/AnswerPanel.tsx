import { Fragment, type ReactNode } from 'react'
import { Lightbulb } from 'lucide-react'
import { useReading } from '../context/ReadingContext'
import type { SearchResult } from '../lib/types'

// Matches the inline general-knowledge marker, e.g. "[BACKGROUND — not retrieved]".
const BG_RE = /\[\s*BACKGROUND[^\]]*\]/gi

function renderWithBackgroundTags(text: string): ReactNode[] {
  // Split each paragraph on blank lines, then mark [BACKGROUND …] runs as amber pills.
  const paragraphs = text.split(/\n{2,}/).filter((p) => p.trim() !== '')
  const blocks = paragraphs.length ? paragraphs : [text]
  return blocks.map((para, pi) => {
    const parts: ReactNode[] = []
    let last = 0
    let m: RegExpExecArray | null
    BG_RE.lastIndex = 0
    while ((m = BG_RE.exec(para)) !== null) {
      if (m.index > last) parts.push(para.slice(last, m.index))
      parts.push(
        <span className="bg-tag" key={`${pi}-${m.index}`}>
          [ BACKGROUND — not retrieved ]
        </span>,
      )
      last = m.index + m[0].length
    }
    if (last < para.length) parts.push(para.slice(last))
    return (
      <p key={pi}>
        {parts.map((p, i) => (
          <Fragment key={i}>{p}</Fragment>
        ))}
      </p>
    )
  })
}

export function AnswerPanel({ result }: { result: SearchResult }) {
  const { docStyle } = useReading()
  const grounded = result.grounded

  return (
    <article className="panel answer">
      <div className="panel-head">
        <div className="pico">
          <Lightbulb />
        </div>
        <h2>The Answer</h2>
        <span className="ptag">{grounded ? 'Grounded' : 'Ungrounded'}</span>
      </div>
      <div className="panel-body">
        <div className="answer-doc" style={docStyle}>
          {result.answer ? renderWithBackgroundTags(result.answer) : <p>No answer was produced.</p>}
        </div>
        <div className="answer-foot">
          <span className="bg-tag">[ BACKGROUND — not retrieved ]</span>
          <span className="note">= general knowledge, clearly separated from corpus-grounded claims.</span>
        </div>
      </div>
    </article>
  )
}

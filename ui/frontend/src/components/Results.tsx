import { Share2, Download } from 'lucide-react'
import { useSearch } from '../context/SearchContext'
import { useUI } from '../context/UIContext'
import { AnswerPanel } from './AnswerPanel'
import { SourcesPanel } from './SourcesPanel'
import { VideoGallery } from './VideoGallery'
import { ImageGallery } from './ImageGallery'
import type { SearchResult } from '../lib/types'

function metaLine(r: SearchResult): string {
  const m = r.meta
  const parts = [
    `${m.source_count} source${m.source_count === 1 ? '' : 's'}`,
    `${m.video_count} video chunk${m.video_count === 1 ? '' : 's'}`,
    `${m.image_count} image${m.image_count === 1 ? '' : 's'}`,
    `${m.elapsed_seconds.toFixed(1)}s`,
  ]
  return parts.join(' · ')
}

function downloadFile(name: string, content: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  URL.revokeObjectURL(url)
}

function toMarkdown(r: SearchResult): string {
  const lines = [`# ${r.query}`, '', '## Answer', '', r.answer, '', '## Sources', '']
  r.sources.forEach((s) => lines.push(`${s.n}. **${s.title}** — ${s.subtitle}`))
  lines.push('', '## What the system does not know', '', r.epistemic.raw)
  return lines.join('\n')
}

export function Results({ result }: { result: SearchResult }) {
  const { error } = useSearch()
  const { toast, showLayers } = useUI()

  const share = () => {
    const url = `${location.origin}${location.pathname}#q=${encodeURIComponent(result.query)}`
    navigator.clipboard?.writeText(url).then(
      () => toast('Share link copied to clipboard'),
      () => toast('Copy failed'),
    )
  }

  const slug = result.query.slice(0, 40).replace(/[^\w]+/g, '_') || 'heritage_lens'
  const exportMd = () => {
    downloadFile(`${slug}.md`, toMarkdown(result), 'text/markdown')
    toast('Exported answer + sources as Markdown')
  }
  const exportJson = () => {
    downloadFile(`${slug}.json`, JSON.stringify(result, null, 2), 'application/json')
    toast('Exported result as JSON')
  }

  return (
    <section className="results">
      <div className="query-recap">
        <div>
          <div className="q">{result.query}</div>
          <div className="meta">{metaLine(result)}</div>
        </div>
        <div className="recap-actions">
          <button className="ghost-btn" onClick={share}>
            <Share2 />
            Share query
          </button>
          <button className="ghost-btn" onClick={exportMd} title="Export as Markdown">
            <Download />
            Export
          </button>
          <button className="ghost-btn" onClick={exportJson} title="Export as JSON">
            JSON
          </button>
        </div>
      </div>

      {error && (
        <div className="upload-log" style={{ color: 'var(--bad)', marginBottom: 16 }}>
          {error}
        </div>
      )}

      <div className="panels">
        <AnswerPanel result={result} />
        {showLayers && <SourcesPanel sources={result.sources} />}
      </div>

      <VideoGallery chunks={result.video_chunks} />
      <ImageGallery images={result.images} />
    </section>
  )
}

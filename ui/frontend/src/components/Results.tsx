import { Share2, Download } from 'lucide-react'
import type { TFunction } from 'i18next'
import { useTranslation } from 'react-i18next'
import { useSearch } from '../context/SearchContext'
import { useUI } from '../context/UIContext'
import { AnswerPanel } from './AnswerPanel'
import { SourcesPanel } from './SourcesPanel'
import { VideoGallery } from './VideoGallery'
import { ImageGallery } from './ImageGallery'
import type { SearchResult } from '../lib/types'

function metaLine(r: SearchResult, t: TFunction): string {
  const m = r.meta
  const parts = [
    t('results.sources', { count: m.source_count }),
    t('results.videos', { count: m.video_count }),
    t('results.images', { count: m.image_count }),
    t('results.seconds', { seconds: m.elapsed_seconds.toFixed(1) }),
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

function toMarkdown(r: SearchResult, t: TFunction): string {
  const lines = [`# ${r.query}`, '', `## ${t('results.mdAnswer')}`, '', r.answer, '', `## ${t('results.mdSources')}`, '']
  r.sources.forEach((s) => lines.push(`${s.n}. **${s.title}** — ${s.subtitle}`))
  lines.push('', `## ${t('results.mdUnknown')}`, '', r.epistemic.raw)
  return lines.join('\n')
}

export function Results({ result }: { result: SearchResult }) {
  const { t } = useTranslation()
  const { error } = useSearch()
  const { toast, showLayers } = useUI()

  const share = () => {
    const url = `${location.origin}${location.pathname}#q=${encodeURIComponent(result.query)}`
    navigator.clipboard?.writeText(url).then(
      () => toast(t('results.shareCopied')),
      () => toast(t('results.copyFailed')),
    )
  }

  const slug = result.query.slice(0, 40).replace(/[^\w]+/g, '_') || 'heritage_lens'
  const exportMd = () => {
    downloadFile(`${slug}.md`, toMarkdown(result, t), 'text/markdown')
    toast(t('results.exportedMd'))
  }
  const exportJson = () => {
    downloadFile(`${slug}.json`, JSON.stringify(result, null, 2), 'application/json')
    toast(t('results.exportedJson'))
  }

  return (
    <section className="results">
      <div className="query-recap">
        <div>
          <div className="q">{result.query}</div>
          <div className="meta">{metaLine(result, t)}</div>
        </div>
        <div className="recap-actions">
          <button className="ghost-btn" onClick={share}>
            <Share2 />
            {t('results.shareQuery')}
          </button>
          <button className="ghost-btn" onClick={exportMd} title={t('results.exportMarkdown')}>
            <Download />
            {t('results.export')}
          </button>
          <button className="ghost-btn" onClick={exportJson} title={t('results.exportJson')}>
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

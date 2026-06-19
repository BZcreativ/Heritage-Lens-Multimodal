import { Video, Play } from 'lucide-react'
import type { VideoChunk } from '../lib/types'

const MODALITY_CLASS: Record<string, string> = {
  audio_transcript: 'audio',
  visual_caption: 'visual',
  ocr_text: 'ocr',
}
const MODALITY_LABEL: Record<string, string> = {
  audio_transcript: 'Audio',
  visual_caption: 'Visual',
  ocr_text: 'OCR',
}

function fmtTime(s: number | null): string {
  if (s == null) return ''
  const mm = Math.floor(s / 60)
  const ss = Math.floor(s % 60)
  return `${mm}:${String(ss).padStart(2, '0')}`
}

function seekHref(v: VideoChunk): string | null {
  // Only http(s) URLs are seekable (local files can't be deep-linked).
  if (v.video_url && v.video_url.startsWith('http')) {
    return v.start != null ? `${v.video_url}#t=${Math.floor(v.start)}` : v.video_url
  }
  return null
}

export function VideoGallery({ chunks }: { chunks: VideoChunk[] }) {
  if (chunks.length === 0) return null
  return (
    <div className="gallery">
      <h3>
        <Video />
        Video Evidence <span className="cnt">{chunks.length} chunks</span>
      </h3>
      <div className="vid-grid">
        {chunks.map((v, i) => {
          const href = seekHref(v)
          return (
            <div className="vid-card" key={i}>
              <div className="ph">
                <div className="play">
                  <Play />
                </div>
                {v.source_name || 'video'}
              </div>
              <div className="vid-meta">
                <span className={`modality ${MODALITY_CLASS[v.modality] ?? 'audio'}`}>
                  {MODALITY_LABEL[v.modality] ?? v.modality}
                </span>
                {v.caption && <p className="cap">{v.caption}</p>}
                {href ? (
                  <a className="seek" href={href} target="_blank" rel="noreferrer">
                    <Play />
                    Seek to {fmtTime(v.start)}
                  </a>
                ) : (
                  v.timestamp && <span className="seek" style={{ color: 'var(--text-faint)' }}>⏱ {v.timestamp}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

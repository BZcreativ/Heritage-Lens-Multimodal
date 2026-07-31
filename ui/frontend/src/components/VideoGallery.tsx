import { Video, Play } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { VideoChunk } from '../lib/types'
import { useUI } from '../context/UIContext'

const MODALITY_CLASS: Record<string, string> = {
  audio_transcript: 'audio',
  visual_caption: 'visual',
  ocr_text: 'ocr',
}
const MODALITY_KEY: Record<string, string> = {
  audio_transcript: 'video.audio',
  visual_caption: 'video.visual',
  ocr_text: 'video.ocr',
}

function fmtTime(s: number | null): string {
  if (s == null) return ''
  const mm = Math.floor(s / 60)
  const ss = Math.floor(s % 60)
  return `${mm}:${String(ss).padStart(2, '0')}`
}

// Local /api/media files play in-app; external http(s) URLs may be page links
// (e.g. YouTube) so we deep-link to them with a #t= seek in a new tab instead.
function isInAppPlayable(v: VideoChunk): boolean {
  return !!v.video_url && v.video_url.startsWith('/api/media')
}

function seekHref(v: VideoChunk): string | null {
  if (v.video_url && v.video_url.startsWith('http')) {
    return v.start != null ? `${v.video_url}#t=${Math.floor(v.start)}` : v.video_url
  }
  return null
}

export function VideoGallery({ chunks }: { chunks: VideoChunk[] }) {
  const { t } = useTranslation()
  const { openVideoLightbox } = useUI()
  if (chunks.length === 0) return null
  return (
    <div className="gallery">
      <h3>
        <Video />
        {t('video.title')} <span className="cnt">{t('video.chunks', { count: chunks.length })}</span>
      </h3>
      <div className="vid-grid">
        {chunks.map((v, i) => {
          const href = seekHref(v)
          const playable = isInAppPlayable(v)
          return (
            <div className="vid-card" key={i}>
              {playable ? (
                <button
                  type="button"
                  className="ph"
                  onClick={() => openVideoLightbox(v)}
                  aria-label={t('video.play', { name: v.source_name || t('video.videoFallback'), time: fmtTime(v.start) })}
                >
                  {v.poster_url && <img className="ph-poster" src={v.poster_url} alt="" loading="lazy" />}
                  <div className="play">
                    <Play />
                  </div>
                  <span className="ph-name">{v.source_name || t('video.videoFallback')}</span>
                </button>
              ) : (
                <div className="ph">
                  {v.poster_url && <img className="ph-poster" src={v.poster_url} alt="" loading="lazy" />}
                  <div className="play">
                    <Play />
                  </div>
                  <span className="ph-name">{v.source_name || t('video.videoFallback')}</span>
                </div>
              )}
              <div className="vid-meta">
                <span className={`modality ${MODALITY_CLASS[v.modality] ?? 'audio'}`}>
                  {MODALITY_KEY[v.modality] ? t(MODALITY_KEY[v.modality]) : v.modality}
                </span>
                {v.caption && <p className="cap">{v.caption}</p>}
                {playable ? (
                  <button className="seek" type="button" onClick={() => openVideoLightbox(v)}>
                    <Play />
                    {t('video.playAt', { time: fmtTime(v.start) })}
                  </button>
                ) : href ? (
                  <a className="seek" href={href} target="_blank" rel="noreferrer">
                    <Play />
                    {t('video.seekTo', { time: fmtTime(v.start) })}
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

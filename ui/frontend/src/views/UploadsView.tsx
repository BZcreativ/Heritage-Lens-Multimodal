import { useRef, useState } from 'react'
import { Upload } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import * as api from '../lib/api'
import { useStatus } from '../context/StatusContext'
import { useUI } from '../context/UIContext'

const ACCEPT = '.pdf,.png,.jpg,.jpeg,.tiff,.bmp,.webp,.mp4,.mov,.avi,.mkv,.webm'

export function UploadsView() {
  const { t } = useTranslation()
  const { refresh } = useStatus()
  const { toast } = useUI()
  const inputRef = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [log, setLog] = useState<string[]>([])

  const append = (line: string) => setLog((prev) => [...prev, line])

  const handleFiles = async (files: File[]) => {
    if (files.length === 0 || busy) return
    setBusy(true)
    setLog([t('uploadsView.uploading', { count: files.length })])
    try {
      const res = await api.uploadFiles(files)
      res.saved.forEach((f) => append(t('uploadsView.saved', { name: f })))
      res.skipped.forEach((f) => append(t('uploadsView.skipped', { name: f })))
      if (res.saved.length === 0) {
        append(t('uploadsView.nothingToIndex'))
        setBusy(false)
        return
      }
      append(t('uploadsView.reindexing'))
      api.streamIngest(
        (e) => {
          if (e.event === 'progress') append(e.data)
          else if (e.event === 'done') {
            append('✓ ' + e.data)
            toast(t('uploadsView.reindexed'))
            refresh()
            setBusy(false)
          } else if (e.event === 'error') {
            append('ERROR: ' + e.data)
            toast(t('uploadsView.ingestFailed'))
            setBusy(false)
          }
        },
        () => setBusy(false),
      )
    } catch (err) {
      append('ERROR: ' + (err instanceof Error ? err.message : String(err)))
      setBusy(false)
    }
  }

  return (
    <div className="view-wrap">
      <div className="view-head">
        <h2>{t('uploadsView.title')}</h2>
        <p>{t('uploadsView.desc')}</p>
      </div>

      <div
        className={`dropzone${drag ? ' drag' : ''}`}
        onClick={() => !busy && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          handleFiles(Array.from(e.dataTransfer.files))
        }}
      >
        <Upload />
        <div>{busy ? t('uploadsView.working') : t('uploadsView.drop')}</div>
        <div style={{ fontSize: 12, color: 'var(--text-faint)', marginTop: 6 }}>{t('uploadsView.fileTypes')}</div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPT}
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(Array.from(e.target.files ?? []))}
        />
      </div>

      {log.length > 0 && <div className="upload-log">{log.join('\n')}</div>}
    </div>
  )
}

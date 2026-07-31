import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

interface Props {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({ open, title, message, confirmLabel, busy, onConfirm, onCancel }: Props) {
  const { t } = useTranslation()
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onCancel])

  if (!open) return null

  return (
    <>
      <div className="scrim show" onClick={onCancel} />
      <div className="confirm-card" role="dialog" aria-modal="true" aria-label={title}>
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="confirm-actions">
          <button className="ghost-btn" onClick={onCancel} disabled={busy}>{t('common.cancel')}</button>
          <button className="danger-btn" onClick={onConfirm} disabled={busy}>
            {busy ? t('common.working') : (confirmLabel ?? t('common.delete'))}
          </button>
        </div>
      </div>
    </>
  )
}

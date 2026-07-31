import { useTranslation } from 'react-i18next'

export function EmptyState() {
  const { t } = useTranslation()
  return (
    <section className="empty">
      <h2>{t('empty.heading')}</h2>
      <p>{t('empty.body')}</p>
    </section>
  )
}

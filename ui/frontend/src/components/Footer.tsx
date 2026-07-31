import { Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const STEP_KEYS = ['footer.stepYouAsk', 'footer.stepRetrieve', 'footer.stepInterpret', 'footer.stepAttribute', 'footer.stepEvaluate']

export function Footer() {
  const { t } = useTranslation()
  return (
    <footer className="footer">
      <div className="how">
        <span className="lbl">{t('footer.howItWorks')}</span>
        <div className="flow">
          {STEP_KEYS.map((key, i) => (
            <span key={key} style={{ display: 'contents' }}>
              <span className="step">
                <span className="n">{i + 1}</span>
                {t(key)}
              </span>
              <span className="arrow">→</span>
            </span>
          ))}
          <span className="step trust">
            <Check />
            {t('footer.trust')}
          </span>
        </div>
      </div>
      <div className="footer-tag">
        {t('footer.tagline')}
      </div>
    </footer>
  )
}

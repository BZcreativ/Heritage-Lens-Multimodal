import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

const STEP_KEYS = ['loading.stepRetrieve', 'loading.stepInterpret', 'loading.stepAttribute', 'loading.stepEvaluate']
const STAGE_KEYS = ['loading.stageRetrieving', 'loading.stageInterpreting', 'loading.stageAttributing', 'loading.stageEvaluating']

export function LoadingState() {
  const { t } = useTranslation()
  // The real /api/search is a single request, so we advance the visual stages on
  // a timer and hold on the last one until the result arrives.
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = window.setInterval(() => {
      setStep((s) => (s < STEP_KEYS.length - 1 ? s + 1 : s))
    }, 700)
    return () => window.clearInterval(id)
  }, [])

  return (
    <section className="loading">
      <div className="pulse-ring">
        <span />
        <span />
        <span />
        <div className="pulse-core" />
      </div>
      <div className="stage-txt">{t(STAGE_KEYS[step])}</div>
      <div className="steps">
        {STEP_KEYS.map((key, i) => (
          <span key={key} className={`st${i < step ? ' done' : ''}${i === step ? ' active' : ''}`}>
            {t(key)}
          </span>
        ))}
      </div>
    </section>
  )
}

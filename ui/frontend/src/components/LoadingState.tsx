import { useEffect, useState } from 'react'

const STEPS = ['Retrieve', 'Interpret', 'Attribute', 'Evaluate']
const STAGE_TXT = [
  'Retrieving across the corpus…',
  'Interpreting the retrieved passages…',
  'Attributing every claim to its source…',
  'Evaluating what the system cannot know…',
]

export function LoadingState() {
  // The real /api/search is a single request, so we advance the visual stages on
  // a timer and hold on the last one until the result arrives.
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = window.setInterval(() => {
      setStep((s) => (s < STEPS.length - 1 ? s + 1 : s))
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
      <div className="stage-txt">{STAGE_TXT[step]}</div>
      <div className="steps">
        {STEPS.map((s, i) => (
          <span key={s} className={`st${i < step ? ' done' : ''}${i === step ? ' active' : ''}`}>
            {s}
          </span>
        ))}
      </div>
    </section>
  )
}

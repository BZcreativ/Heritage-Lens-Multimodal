import { Check } from 'lucide-react'

const STEPS = ['You ask', 'Retrieve', 'Interpret', 'Attribute', 'Evaluate']

export function Footer() {
  return (
    <footer className="footer">
      <div className="how">
        <span className="lbl">How it works</span>
        <div className="flow">
          {STEPS.map((s, i) => (
            <span key={s} style={{ display: 'contents' }}>
              <span className="step">
                <span className="n">{i + 1}</span>
                {s}
              </span>
              <span className="arrow">→</span>
            </span>
          ))}
          <span className="step trust">
            <Check />
            Answers you can trust
          </span>
        </div>
      </div>
      <div className="footer-tag">
        Heritage Lens Multimodal Agent — Accountable AI for Specialised Research
      </div>
    </footer>
  )
}

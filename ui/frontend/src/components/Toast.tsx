import { useUI } from '../context/UIContext'

export function Toast() {
  const { toastMsg } = useUI()
  return <div className={`toast${toastMsg ? ' show' : ''}`}>{toastMsg}</div>
}

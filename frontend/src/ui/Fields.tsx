import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from 'react'

interface FieldProps { label: string; help?: string; error?: string | null; className?: string; children: (p: { id: string; 'aria-invalid'?: boolean; 'aria-describedby'?: string }) => ReactNode }
export function Field({ label, help, error, className, children }: FieldProps) {
  const id = useId()
  const hid = `${id}-h`
  return (
    <div className={`field ${className ?? ''}`}>
      <label htmlFor={id}>{label}</label>
      {children({ id, 'aria-invalid': error ? true : undefined, 'aria-describedby': error || help ? hid : undefined })}
      {error ? <span className="err" id={hid} role="alert">{error}</span> : help ? <span className="help" id={hid}>{help}</span> : null}
    </div>
  )
}

type InProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> & { label: string; help?: string; error?: string | null; mono?: boolean }
export function TextField({ label, help, error, mono, className, ...rest }: InProps) {
  return <Field label={label} help={help} error={error} className={className}>{(p) => <input className={`input${mono ? ' mono-in' : ''}`} {...p} {...rest} />}</Field>
}
type TaProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'id'> & { label: string; help?: string; error?: string | null }
export function TextArea({ label, help, error, className, ...rest }: TaProps) {
  return <Field label={label} help={help} error={error} className={className}>{(p) => <textarea className="textarea" {...p} {...rest} />}</Field>
}
type SelProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> & { label: string; help?: string; error?: string | null; options: { value: string | number; label: string }[]; placeholder?: string }
export function SelectField({ label, help, error, options, placeholder, className, ...rest }: SelProps) {
  return (
    <Field label={label} help={help} error={error} className={className}>
      {(p) => (
        <select className="select" {...p} {...rest}>
          {placeholder !== undefined && <option value="">{placeholder}</option>}
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      )}
    </Field>
  )
}
export function Switch({ checked, onChange, label, disabled }: { checked: boolean; onChange: (v: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <label className="switch">
      <input type="checkbox" role="switch" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  )
}
export function Check({ checked, onChange, label, disabled }: { checked: boolean; onChange: (v: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <label className="check">
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  )
}
/** Lista de números separada por comas (puertos). */
export function parseNumList(s: string): number[] {
  return s.split(/[,\s]+/).filter(Boolean).map(Number).filter((n) => Number.isFinite(n))
}

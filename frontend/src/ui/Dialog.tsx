import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { Button } from './Button'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  footer?: ReactNode
  wide?: boolean
  drawer?: boolean
}

/** <dialog> nativo: foco atrapado, Escape y cierre por clic en el fondo. */
export function Dialog({ open, onClose, title, children, footer, wide, drawer }: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (open && !d.open) d.showModal()
    if (!open && d.open) d.close()
  }, [open])
  return (
    <dialog
      ref={ref}
      className={`dlg${wide ? ' wide' : ''}${drawer ? ' drawer' : ''}`}
      aria-label={title}
      onClose={onClose}
      onClick={(e) => { if (e.target === ref.current) onClose() }}
    >
      {open && (
        <>
          <div className="dlg-head">
            <h2>{title}</h2>
            <Button variant="ghost" icon size="sm" onClick={onClose} aria-label="Cerrar"><X size={16} /></Button>
          </div>
          <div className="dlg-body">{children}</div>
          {footer && <div className="dlg-foot">{footer}</div>}
        </>
      )}
    </dialog>
  )
}

interface ConfirmProps {
  open: boolean
  title: string
  message: ReactNode
  confirmLabel?: string
  danger?: boolean
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}
export function ConfirmDialog({ open, title, message, confirmLabel = 'Confirmar', danger, busy, onConfirm, onCancel }: ConfirmProps) {
  return (
    <Dialog
      open={open} onClose={onCancel} title={title}
      footer={<>
        <Button onClick={onCancel}>Cancelar</Button>
        <Button variant={danger ? 'danger' : 'primary'} onClick={onConfirm} loading={busy}>{confirmLabel}</Button>
      </>}
    >
      <p>{message}</p>
    </Dialog>
  )
}

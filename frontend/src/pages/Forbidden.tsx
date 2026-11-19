import { Link } from 'react-router-dom'
import { ShieldOff } from 'lucide-react'
import { EmptyState } from '../ui/State'

export function Forbidden() {
  return (
    <div className="page">
      <EmptyState title="Acceso restringido" icon={<ShieldOff size={30} aria-hidden />} action={<Link className="btn" to="/">Ir al inicio</Link>}>
        Su rol no incluye permiso para este módulo. Si cree que lo necesita, pídaselo a un administrador.
      </EmptyState>
    </div>
  )
}
export function NotFound() {
  return (
    <div className="page">
      <EmptyState title="Página no encontrada" action={<Link className="btn" to="/">Ir al inicio</Link>}>
        La dirección no existe o fue movida.
      </EmptyState>
    </div>
  )
}

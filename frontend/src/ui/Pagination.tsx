import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './Button'
import { num } from '../lib/format'

export function Pagination({ page, pageSize, total, onPage, onSize }: { page: number; pageSize: number; total: number; onPage: (p: number) => void; onSize?: (s: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1
  const to = Math.min(total, page * pageSize)
  return (
    <div className="pager">
      <span>{num(from)}–{num(to)} de {num(total)}</span>
      <div className="row">
        {onSize && (
          <label className="row small" style={{ gap: 6 }}>
            Filas
            <select className="select" style={{ width: 70, minHeight: 28, padding: '2px 6px' }} value={pageSize} onChange={(e) => onSize(Number(e.target.value))}>
              {[25, 50, 100].map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
        )}
        <Button size="sm" icon disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label="Página anterior"><ChevronLeft size={16} /></Button>
        <span aria-live="polite">Página {page} de {pages}</span>
        <Button size="sm" icon disabled={page >= pages} onClick={() => onPage(page + 1)} aria-label="Página siguiente"><ChevronRight size={16} /></Button>
      </div>
    </div>
  )
}

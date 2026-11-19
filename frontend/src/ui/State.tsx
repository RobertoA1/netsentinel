import type { ReactNode } from 'react'
import { AlertCircle, Inbox } from 'lucide-react'
import type { UseQueryResult } from '@tanstack/react-query'
import { Button } from './Button'
import { ApiError } from '../api/client'
import { errMsg } from '../lib/utils'

export function Skeleton({ h = 14, w = '100%' }: { h?: number; w?: string | number }) {
  return <div className="skeleton" style={{ height: h, width: w }} aria-hidden />
}
export function SkeletonRows({ rows = 6, h = 18 }: { rows?: number; h?: number }) {
  return (
    <div className="panel-body stack" role="status" aria-label="Cargando">
      {Array.from({ length: rows }, (_, i) => <Skeleton key={i} h={h} w={`${100 - (i % 3) * 8}%`} />)}
    </div>
  )
}
export function EmptyState({ title, children, action, icon }: { title: string; children?: ReactNode; action?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="state">
      {icon ?? <Inbox size={28} aria-hidden />}
      <h3>{title}</h3>
      {children && <div className="muted" style={{ maxWidth: '56ch' }}>{children}</div>}
      {action}
    </div>
  )
}
export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const forbidden = error instanceof ApiError && error.status === 403
  return (
    <div className="state err" role="alert">
      <AlertCircle size={28} aria-hidden />
      <h3>{forbidden ? 'No tiene permiso para ver esto' : 'No se pudo cargar la información'}</h3>
      <p>{errMsg(error)}</p>
      {onRetry && !forbidden && <Button onClick={onRetry}>Reintentar</Button>}
    </div>
  )
}

interface DSProps<T> {
  q: UseQueryResult<T>
  children: (data: T) => ReactNode
  isEmpty?: (data: T) => boolean
  empty?: ReactNode
  skeleton?: ReactNode
}
/** Carga / error / vacío / contenido para cualquier consulta. */
export function DataState<T>({ q, children, isEmpty, empty, skeleton }: DSProps<T>) {
  if (q.isPending) return <>{skeleton ?? <SkeletonRows />}</>
  if (q.isError) return <ErrorState error={q.error} onRetry={() => q.refetch()} />
  if (isEmpty?.(q.data as T)) return <>{empty ?? <EmptyState title="Sin datos" />}</>
  return <>{children(q.data as T)}</>
}

export function PageHead({ title, desc, children }: { title: string; desc?: ReactNode; children?: ReactNode }) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {desc && <p>{desc}</p>}
      </div>
      {children && <div className="page-actions">{children}</div>}
    </div>
  )
}

// Punto único de la bitácora de módulos: entrada/salida de módulo.
// Lo usa <ModuleTracker/> (router) y el cierre de sesión. Ninguna página llama a esto.
import { api, sendBeacon } from '../api/client'

type Reason = 'navigation' | 'logout' | 'close'
interface Open { module: string; id: number | null; pending: Promise<number | null> }

class ModuleAuditTracker {
  private open: Open | null = null
  private module: string | null = null // módulo activo aunque la sesión esté cerrada (bfcache)

  /** Marca el módulo activo. Mismo módulo = sin eventos. null = fuera de módulos auditados. */
  enter(module: string | null) {
    if (module === this.module && (module === null || this.open)) return
    this.exit('navigation')
    this.module = module
    if (!module) return
    const entry: Open = { module, id: null, pending: Promise.resolve(null) }
    entry.pending = api
      .post<{ session_id: number }>('/audit/module-enter', { module })
      .then((r) => { entry.id = r.session_id; return r.session_id })
      .catch(() => null) // la bitácora nunca debe romper la navegación
    this.open = entry
  }

  /** Cierra la sesión de módulo abierta (fetch con keepalive: sobrevive al cierre de pestaña). */
  exit(reason: Reason) {
    const o = this.open
    this.open = null
    if (!o) return
    const send = (id: number) => sendBeacon('/audit/module-exit', { session_id: id, reason })
    if (o.id != null) send(o.id)
    else void o.pending.then((id) => { if (id != null) send(id) })
  }

  /** Tras logout el siguiente login empieza de cero. */
  reset() { this.open = null; this.module = null }

  /** Vuelta desde bfcache: reabre el módulo en que estaba el usuario. */
  resume() {
    if (!this.open && this.module) { const m = this.module; this.module = null; this.enter(m) }
  }
}

export const moduleAudit = new ModuleAuditTracker()

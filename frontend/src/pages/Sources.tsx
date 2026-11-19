import { CrudPage } from '../ui/CrudPage'
import type { Source } from '../api/types'
import { FORMAT_LABEL } from '../lib/labels'
import { num, useFmt } from '../lib/format'

export default function Sources() {
  const fmt = useFmt()
  return (
    <CrudPage<Source>
      module="sources" path="/sources" noun="fuente" title="Fuentes"
      desc="Orígenes de logs (firewall, IDS, flujos). Cada archivo que ingiere se asocia a una fuente que define su formato."
      emptyHelp="Cree una fuente antes de subir un archivo de logs."
      blank={{ name: '', format: 'opnsense_filterlog', description: '', enabled: true }}
      deleteMessage={(s) => `¿Eliminar la fuente "${s.name}"? Se perderá su asociación con ${num(s.log_count)} registros.`}
      columns={[
        { header: 'Nombre', cell: (s) => <span className="cell-main">{s.name}</span> },
        { header: 'Formato', cell: (s) => FORMAT_LABEL[s.format] },
        { header: 'Estado', cell: (s) => <span className={`badge ${s.enabled ? 'ok' : ''}`}>{s.enabled ? 'Activa' : 'Desactivada'}</span> },
        { header: 'Registros', num: true, cell: (s) => num(s.log_count) },
        { header: 'Última ingesta', cell: (s) => fmt.dt(s.last_ingest_at) },
      ]}
      fields={[
        { key: 'name', label: 'Nombre', required: true },
        { key: 'format', label: 'Formato de log', type: 'select', required: true, options: Object.entries(FORMAT_LABEL).map(([value, label]) => ({ value, label })) },
        { key: 'description', label: 'Descripción', type: 'textarea', full: true },
        { key: 'enabled', label: 'Fuente activa', type: 'switch', full: true },
      ]}
    />
  )
}

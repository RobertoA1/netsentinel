import { CrudPage } from '../ui/CrudPage'
import type { Asset } from '../api/types'
import { ASSET_TYPES, CRITICALITY_LABEL } from '../lib/labels'
import { parseNumList } from '../ui/Fields'

const IPV4 = /^(\d{1,3}\.){3}\d{1,3}$/
const crit = (c: Asset['criticality']) => <span className={`badge ${c === 'critical' ? 'crit' : c === 'high' ? 'high' : c === 'medium' ? 'med' : 'low'}`}>{CRITICALITY_LABEL[c]}</span>

export default function Assets() {
  return (
    <CrudPage<Asset>
      module="assets" path="/assets" paginated searchable noun="activo" title="Activos"
      desc="Equipos conocidos de su red. Con ellos los hallazgos muestran nombres, no solo IP, y se pondera su importancia."
      emptyHelp="Registre sus servidores y estaciones para dar contexto a los hallazgos."
      blank={{ ip: '', hostname: '', owner: '', asset_type: 'workstation', criticality: 'medium', expected_ports: '', notes: '' }}
      toForm={(a) => ({ ...a, expected_ports: a.expected_ports.join(', ') })}
      toBody={(f) => ({ ...f, expected_ports: typeof f.expected_ports === 'string' ? parseNumList(f.expected_ports) : f.expected_ports })}
      columns={[
        { header: 'IP', cell: (a) => <span className="mono cell-main">{a.ip}</span> },
        { header: 'Nombre', cell: (a) => a.hostname || <span className="muted">—</span> },
        { header: 'Tipo', cell: (a) => ASSET_TYPES[a.asset_type] ?? a.asset_type },
        { header: 'Criticidad', cell: (a) => crit(a.criticality) },
        { header: 'Responsable', cell: (a) => a.owner || <span className="muted">—</span> },
        { header: 'Puertos esperados', cell: (a) => <span className="mono small">{a.expected_ports.join(', ') || '—'}</span> },
      ]}
      fields={[
        { key: 'ip', label: 'Dirección IP', required: true, mono: true, validate: (v) => (IPV4.test(String(v).trim()) || String(v).includes(':') ? null : 'Ingrese una IP válida, por ejemplo 10.0.0.5.') },
        { key: 'hostname', label: 'Nombre del equipo' },
        { key: 'asset_type', label: 'Tipo', type: 'select', required: true, options: Object.entries(ASSET_TYPES).map(([value, label]) => ({ value, label })) },
        { key: 'criticality', label: 'Criticidad', type: 'select', required: true, options: Object.entries(CRITICALITY_LABEL).map(([value, label]) => ({ value, label })) },
        { key: 'owner', label: 'Responsable' },
        { key: 'expected_ports', label: 'Puertos esperados', help: 'Separados por comas: 80, 443, 53', validate: (v) => (String(v).split(/[,\s]+/).filter(Boolean).every((x) => /^\d+$/.test(x) && +x <= 65535) ? null : 'Use solo números de puerto entre 0 y 65535.') },
        { key: 'notes', label: 'Notas', type: 'textarea', full: true },
      ]}
    />
  )
}

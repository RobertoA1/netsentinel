import { useState } from 'react'
import { CrudPage } from '../ui/CrudPage'
import type { ListEntry } from '../api/types'
import { useFmt } from '../lib/format'
import { Segmented } from '../ui/Controls'

const KIND = { ip: 'IP', cidr: 'Red (CIDR)', port: 'Puerto', domain: 'Dominio' }
const IP = /^(\d{1,3}\.){3}\d{1,3}$/
const validate = (v: string, f: Record<string, any>) => {
  const x = String(v).trim()
  if (f.kind === 'ip') return IP.test(x) || x.includes(':') ? null : 'Ingrese una IP válida.'
  if (f.kind === 'cidr') return /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/.test(x) ? null : 'Use el formato 10.0.0.0/8.'
  if (f.kind === 'port') return /^\d+$/.test(x) && +x <= 65535 ? null : 'Ingrese un puerto entre 0 y 65535.'
  return /^[a-z0-9.-]+\.[a-z]{2,}$/i.test(x) ? null : 'Ingrese un dominio válido, por ejemplo ejemplo.com.'
}

export default function Lists() {
  const fmt = useFmt()
  const [t, setT] = useState<'allow' | 'deny'>('deny')
  return (
    <CrudPage<ListEntry>
      key={t}
      module="lists" path="/lists" paginated searchable noun="entrada" nounPlural="entradas" title="Listas blanca y negra" editable={false}
      desc="La lista negra marca destinos conocidos como maliciosos; la blanca evita falsos positivos con destinos de confianza."
      emptyHelp={t === 'deny' ? 'Agregue IP, redes o dominios que nunca deberían recibir tráfico.' : 'Agregue destinos de confianza (por ejemplo, su proveedor de nube).'}
      queryParams={{ list_type: t }}
      extraHeader={<Segmented label="Tipo de lista" value={t} onChange={setT} options={[{ value: 'deny', label: 'Lista negra' }, { value: 'allow', label: 'Lista blanca' }]} />}
      blank={{ list_type: t, kind: 'ip', value: '', note: '' }}
      columns={[
        { header: 'Tipo de dato', cell: (e) => KIND[e.kind] },
        { header: 'Valor', cell: (e) => <span className="mono cell-main">{e.value}</span> },
        { header: 'Nota', cell: (e) => e.note || <span className="muted">—</span> },
        { header: 'Agregada', cell: (e) => fmt.dt(e.created_at) },
      ]}
      fields={[
        { key: 'kind', label: 'Tipo de dato', type: 'select', required: true, options: Object.entries(KIND).map(([value, label]) => ({ value, label })) },
        { key: 'value', label: 'Valor', required: true, mono: true, validate },
        { key: 'note', label: 'Nota', full: true, help: 'Para qué está en la lista o quién la pidió.' },
      ]}
    />
  )
}

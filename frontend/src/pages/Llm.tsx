import { useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CircleCheck, CircleX, Plug } from 'lucide-react'
import { api } from '../api/client'
import { useGet } from '../api/hooks'
import type { LlmSettings, LlmTestResult } from '../api/types'
import { useCan } from '../auth/AuthProvider'
import { Button } from '../ui/Button'
import { Switch, TextField } from '../ui/Fields'
import { DataState, PageHead, SkeletonRows } from '../ui/State'
import { useToast } from '../ui/Toast'
import { errMsg } from '../lib/utils'
import { dec } from '../lib/format'

function Form({ data, canEdit, canTest }: { data: LlmSettings; canEdit: boolean; canTest: boolean }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [f, setF] = useState({ enabled: data.enabled, base_url: data.base_url, model: data.model, temperature: String(data.temperature), timeout_seconds: String(data.timeout_seconds), noise: String(data.noise_confidence_threshold) })
  const [errs, setErrs] = useState<Record<string, string>>({})
  const [result, setResult] = useState<LlmTestResult | null>(null)
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF((x) => ({ ...x, [k]: e.target.value }))

  const save = useMutation({
    mutationFn: (b: LlmSettings) => api.put<LlmSettings>('/settings/llm', b),
    onSuccess: () => { toast.ok('Configuración del motor IA guardada.'); void qc.invalidateQueries({ queryKey: ['/settings/llm'] }) },
    onError: (e) => toast.err(errMsg(e)),
  })
  const test = useMutation({
    mutationFn: () => api.post<LlmTestResult>('/settings/llm/test'),
    onSuccess: setResult,
    onError: (e) => setResult({ ok: false, model: f.model, latency_ms: 0, message: errMsg(e) }),
  })
  const rng = (v: string, a: number, b: number) => (v.trim() !== '' && !Number.isNaN(+v) && +v >= a && +v <= b ? null : `Debe estar entre ${a} y ${b}.`)
  function submit(e: FormEvent) {
    e.preventDefault()
    const er: Record<string, string | null> = {
      base_url: /^https?:\/\/\S+$/.test(f.base_url) ? null : 'Ingrese una URL que empiece con http:// o https://.',
      model: f.model.trim() ? null : 'Indique el nombre del modelo.',
      temperature: rng(f.temperature, 0, 2), timeout_seconds: rng(f.timeout_seconds, 1, 600), noise: rng(f.noise, 0, 1),
    }
    const clean = Object.fromEntries(Object.entries(er).filter(([, v]) => v)) as Record<string, string>
    setErrs(clean)
    if (Object.keys(clean).length) return
    save.mutate({ enabled: f.enabled, base_url: f.base_url.trim(), model: f.model.trim(), temperature: +f.temperature, timeout_seconds: +f.timeout_seconds, noise_confidence_threshold: +f.noise })
  }
  return (
    <div className="stack" style={{ gap: 16 }}>
      <form onSubmit={submit} noValidate className="panel">
        <div className="panel-head"><h2>Conexión y modelo</h2></div>
        <div className="panel-body stack">
          <Switch label="Usar IA para filtrar ruido y explicar hallazgos" checked={f.enabled} onChange={(c) => setF((x) => ({ ...x, enabled: c }))} disabled={!canEdit} />
          {!f.enabled && <div className="banner warn">Con la IA apagada, las explicaciones se generan por plantilla y ningún hallazgo se descarta como ruido.</div>}
          <div className="form-grid">
            <TextField label="URL del servidor (Ollama)" className="full" mono value={f.base_url} onChange={set('base_url')} error={errs.base_url} disabled={!canEdit} />
            <TextField label="Modelo" mono value={f.model} onChange={set('model')} error={errs.model} disabled={!canEdit} />
            <TextField label="Tiempo máximo de respuesta (s)" inputMode="numeric" value={f.timeout_seconds} onChange={set('timeout_seconds')} error={errs.timeout_seconds} disabled={!canEdit} />
            <TextField label="Temperatura" inputMode="decimal" value={f.temperature} onChange={set('temperature')} error={errs.temperature} disabled={!canEdit} help="Más baja = respuestas más consistentes. Recomendado: 0,1." />
            <TextField label="Confianza mínima para descartar como ruido" inputMode="decimal" value={f.noise} onChange={set('noise')} error={errs.noise} disabled={!canEdit} help="De 0 a 1. Más alta = descarta menos, más seguro. Recomendado: 0,7." />
          </div>
          {canEdit && <div><Button variant="primary" type="submit" loading={save.isPending}>Guardar</Button></div>}
        </div>
      </form>
      {canTest && (
        <section className="panel">
          <div className="panel-head"><h2>Probar conexión</h2><span className="hint">Usa la configuración guardada</span></div>
          <div className="panel-body stack">
            <div><Button onClick={() => { setResult(null); test.mutate() }} loading={test.isPending}><Plug size={15} /> Probar conexión</Button></div>
            {result && (
              <div className={`banner ${result.ok ? 'ok' : 'err'}`} role="status">
                {result.ok ? <CircleCheck size={18} aria-hidden /> : <CircleX size={18} aria-hidden />}
                <div><b>{result.ok ? 'Conexión correcta' : 'No se pudo conectar'}</b>
                  <div>{result.message}</div>
                  {result.ok && <div className="small muted">Modelo {result.model} · respondió en {dec(result.latency_ms / 1000, 1)} s</div>}</div>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  )
}

export default function Llm() {
  const can = useCan('llm')
  const q = useGet<LlmSettings>('/settings/llm')
  return (
    <div className="page" style={{ maxWidth: 820 }}>
      <PageHead title="Motor IA" desc="El modelo de lenguaje local que descarta el ruido y explica cada hallazgo en lenguaje llano. Corre en su propio servidor." />
      <DataState q={q} skeleton={<div className="panel"><SkeletonRows rows={6} /></div>}>{(d) => <Form data={d} canEdit={can.update} canTest={can.execute || can.update} />}</DataState>
    </div>
  )
}

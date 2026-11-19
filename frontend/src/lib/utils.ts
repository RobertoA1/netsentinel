export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(' ')
export function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename
  document.body.appendChild(a); a.click(); a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
}
export const errMsg = (e: unknown) => (e instanceof Error ? e.message : 'Ocurrió un error inesperado')
export function initials(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((s) => s[0]!.toUpperCase()).join('') || '?'
}

from estilo import *
fig, ax = plt.subplots(figsize=(7.2, 4.2)); ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis('off'); ax.grid(False)
C = dict(n='#FFF6E0', b='#EAF6F1', l='#D9EFE6', d='#E8F1FA', a='#FCE9E0')
steps = [
 (0.2, 5.1, 'n8n (cron 15 min)\nPOST /ingest/run', C['n']), (3.2, 5.1, 'Parsers: archivos nuevos\n(desde el último\ndesplazamiento)', C['b']), (6.2, 5.1, 'PostgreSQL\nfirewall_logs\n(registros normalizados)', C['d']), (9.2, 5.1, 'Agregación SQL\nventana 24 h\n(ventanas con LAG)', C['b']),
 (9.2, 2.9, 'Detectores puros:\nbeaconing, puerto inusual,\nexfiltración, host, IDS', C['b']), (6.2, 2.9, 'Listas permitidos/\ndenegados y activos\n(contexto)', C['b']), (3.2, 2.9, 'Alta o actualización\nde hallazgo\n(dedup_key)', C['d']), (0.2, 2.9, 'Cadena LangChain\n(≤ 30 por ejecución,\npor puntaje)', C['l']),
 (0.2, 0.7, 'Veredicto real / ruido /\nincierto + explicación\n(plantilla si falla)', C['l']), (3.2, 0.7, 'Ruido solo si el\nveredicto es ruido y la\nconfianza es ≥ 0,70', C['a']), (6.2, 0.7, 'Alertas por regla;\nn8n (5 min) despacha\npor webhook o SMTP', C['n']), (9.2, 0.7, 'Bitácora y reportes\n(módulos, tiempos,\nPDF/DOCX/XLSX)', C['d']),
]
for i, (x, y, t, c) in enumerate(steps):
    box(ax, x, y, 2.6, 1.45, t, c, fs=5.9)
    ax.text(x + 0.08, y + 1.3, str(i+1), fontsize=7, fontweight='bold', color='#222222', ha='left', va='center',
            bbox=dict(boxstyle='circle,pad=0.15', fc='white', ec='#333333', lw=0.7))
def mid(i, side):
    x, y = steps[i][0], steps[i][1]
    return {'r': (x+2.6, y+0.72), 'l': (x, y+0.72), 'd': (x+1.3, y), 'u': (x+1.3, y+1.45)}[side]
for i in (0, 1, 2): arrow(ax, mid(i, 'r'), mid(i+1, 'l'))
arrow(ax, mid(3, 'd'), mid(4, 'u'))
for i in (4, 5, 6): arrow(ax, mid(i, 'l'), mid(i+1, 'r'))
arrow(ax, mid(7, 'd'), mid(8, 'u'))
for i in (8, 9, 10): arrow(ax, mid(i, 'r'), mid(i+1, 'l'))
ax.text(6.0, 6.8, 'Hechos: pasos 3–7 (código determinista). Interpretación de IA: pasos 8–10, etiquetada aparte.', fontsize=7, ha='center', style='italic')
ax.text(0.2, 0.2, 'El contenido de los logs se trata como dato no confiable (delimitado y saneado antes del prompt).\nTras dos fallos consecutivos del modelo, se usa la plantilla determinista para el resto de la ejecución.', fontsize=6.3, style='italic')
save(fig, 'F2_flujo_procesamiento.png')

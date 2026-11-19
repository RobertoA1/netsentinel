# NetSentinel: sistema visual

Modo: Operate. Dirección: boletín de intensidad (reporte sismológico). Semilla de dirección: seed:75dff0bdad1daa0d.

## Principios
- Lo grave se lee por forma, no solo por color: la **regla de intensidad** (5 peldaños crecientes + etiqueta) acompaña a toda severidad.
- Hechos medidos y opinión de la IA nunca se mezclan: la evidencia determinista vive en paneles neutros; la interpretación de IA, en un recuadro violeta etiquetado "Interpretación de IA".
- Densidad con legibilidad: tablas compactas, bordes de 1px, sin sombras salvo en capas flotantes, sin tarjetas anidadas ni degradados.

## Color (oklch, tokens en `src/index.css`)
- Lienzo gris azulado frío (`--bg`, `--surface`, `--surface-2/3`); tinta `--ink`, `--ink-2`, `--ink-3` (todas AA sobre el lienzo).
- Carcasa (riel lateral) azul tinta profunda `--shell`; en oscuro, grafito azulado.
- Acento de acción: cobalto `--accent` (primarios, selección, enlaces).
- Escala de severidad: `--crit` bermellón, `--high` naranja, `--med` ocre, `--low` azul pizarra, `--info` gris; cada una con `-ink` (texto) y `-bg` (fondo de insignia).
- IA: violeta `--ai`, `--ai-bg`, `--ai-line`. Éxito `--ok`.
- Series de gráficos: `--c-out` (salida), `--c-in` (entrada), `--c-blk` (bloqueado).

## Tipografía
- Public Sans Variable para interfaz y datos; JetBrains Mono Variable solo para IP, puertos, código y registro original. Numerales tabulares en todo.
- Escala fija: 12 / 13 / 14 / 17 / 24 px. Sin tipografía fluida.

## Componentes
Botón (`default`, `primary`, `danger`, `ghost`; `sm`, `icon`), campos con etiqueta/ayuda/error, interruptor, control segmentado, pestañas, tabla densa con paginación en servidor, insignias, `Dialog` nativo (`<dialog>`) y panel lateral, confirmación de borrado, toasts, esqueletos, estados vacío y error. Gráficos en Recharts y SVG propio (Sankey de flujos, tira de intervalos de beaconing, medidor de línea base).

## Laboratorio ML (patrones nuevos)
- Figuras como especificación: `{kind, title, note, data, interpretation}` renderizada en SVG propio (`src/ml/figures.tsx`: barras, líneas, puntos, mapa de calor, enjambre, cascada, coordenadas paralelas). No se usa Recharts aquí: el mismo spec lo dibuja matplotlib a 600 DPI en reportes y exportación.
- `FigureCard`/`TableCard`: título autosuficiente, nota (n, definiciones, unidades), bloque «Qué significa» (1 a 3 frases deterministas) y «Precaución»; botones PNG 600 DPI y SVG.
- Monitor de trabajos por sondeo (3 s) con barra de progreso, ETA, recursos y registro; avisos de bloqueo (`mlblock`) y de baja potencia estadística (`mlwarn`).
- Navegación: grupo «Laboratorio ML» filtrado por permisos `modulo:view`.

## Movimiento
Solo transiciones de estado de 150 a 250 ms; sin coreografías de carga. Respeta `prefers-reduced-motion`.

## Superficies del navegador
Selección, cursor, barras de desplazamiento, anillo de foco (2px cobalto) y numerales tabulares tematizados desde la paleta.

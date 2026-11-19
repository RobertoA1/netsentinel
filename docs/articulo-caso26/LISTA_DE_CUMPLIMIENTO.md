# Lista de cumplimiento: Caso 26 (NetSentinel)

Evidencia: `build/verificar.py` (60 controles automáticos, 0 fallas en la última ejecución), validación OOXML (`validate.py` con la plantilla como original: aprobada) y revisión visual de las 25 páginas del PDF de revisión.

## Requisitos de la revista

| Requisito | Evidencia |
|---|---|
| Título ES y EN < 20 palabras, sin siglas, sin artículo/verbo inicial | ES 18 palabras, EN 15; control automático |
| Resumen y Abstract 150-200 palabras, un párrafo, pasado | Resumen 195, Abstract 183; un solo párrafo cada uno |
| 3-5 palabras clave alfabéticas, ausentes del título | 5 ES y 5 EN, en orden alfabético, ausentes del título |
| Introducción en presente, <= 10 párrafos, con fórmula de brecha y propósito | 9 párrafos, 77-103 palabras cada uno; contiene "Aunque ... permanece sin resolver ..." |
| Métodos en pasado y secuenciales | Secciones 2.1-2.8 en orden de ejecución |
| Una sola sección "Resultados y discusión" | Verificado; sin sección "Discusión" aparte |
| Conclusiones en un párrafo, sin viñetas, con recomendaciones | 1 párrafo, 228 palabras, con recomendaciones |
| Secciones finales (conflicto, CRediT, financiación, datos) | Presentes, marcadas para confirmación |
| Referencias APA 7, >= 30, >= 80 % artículos 2021-2026 | 39 referencias; 36/39 = 92,3 % de 2021-2026; 39/39 artículos de revista o actas; ver VERIFICACION_REFERENCIAS.md |
| Unidades SI y siglas explicadas al primer uso | Control automático de siglas principales |
| 6 tablas y 6 figuras reales, citadas antes, con leyenda y nota | 6 tablas Word, 6 imágenes (PNG 600 DPI), campos SEQ, 12 notas; citas previas verificadas |
| Citas y referencias coinciden | 39 claves citadas, 39 referencias, sin huérfanas |
| Sin rastro de la plantilla | Búsqueda en las 31 partes XML (incluye core, customXml y pies): sin coincidencias |

## Normas de calidad

| Norma | Evidencia |
|---|---|
| Título verificable, métodos reproducibles | Parámetros, semillas, umbrales, particiones y versiones declarados; datos y scripts en `figuras/datos/` |
| Efectos, IC 95 % y valores p, incluidos los no significativos | Tablas 4 y 5: IC de Wilson, bootstrap por grupos, Friedman, Wilcoxon exacto (p mínimo 0,0625), McNemar |
| Validez interna, externa, de constructo y de conclusión estadística | Párrafos con encabezado en cursiva en "Validez y limitaciones" |
| Conclusiones sin exageración | Se niega explícitamente la detección efectiva de botnets; alcance: diseño, implementación y evaluación preliminar |
| Referencias verificadas | Crossref, 39/39 con DOI |
| Conflicto formato revista/normas | Prevalece la revista |

## Marcadores pendientes para los autores

1. Autor de correspondencia y asignación de afiliaciones por autor (se asignó 1 y 2 a ambos).
2. Conflicto de intereses (fórmula literal de la revista, marcada).
3. Fuente de financiación (fórmula literal, marcada).
4. Contribución de autoría CRediT (marcador a completar).
5. URL y DOI del repositorio de código y licencia; CTU-13 no declara licencia explícita (solo pide citar el artículo).
6. Confirmar la declaración sobre IA generativa en Agradecimientos.

## Límites de la verificación

- Montserrat no está instalada: el PDF de revisión usa DejaVu Sans y la paginación en Word puede variar.
- Latencias de endpoints (14-472 ms), LLM (28-37 s) y narración (74,5 s) provienen del registro de la prueba de despliegue, no se volvieron a medir.
- Versiones de bibliotecas del campo `ml_jobs.libs` sin verificar de forma independiente.
- 57 líneas del archivo de flujos sin explicar (107 252 leídas, 107 194 insertadas, 1 error de análisis).
- El hallazgo de IGMP no lo reproduce el código actual (F3 reproduce 22 de 23 hallazgos de beaconing).
- Diferencias con las cifras del encargo: severidad de la primera carga 2/17/30/2; importación 9,66 s; intervalos de reporte 37-629 ms; solo 2 veredictos LLM atribuibles a la primera carga; el hallazgo con P(Botnet) 0,137 y alerta OOD corresponde al equipo Background 147.32.84.229; ningún hallazgo involucra equipos infectados.
- La lectura del contenido de cada referencia frente a las afirmaciones no está automatizada.

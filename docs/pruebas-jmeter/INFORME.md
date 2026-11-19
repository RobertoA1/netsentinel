> **Versión corregida y completa: `INFORME_PRUEBAS_JMETER.docx`.** El criterio ahora es por endpoint/consulta (no el p95 mezclado de todas), el login se informa aparte y la base de datos queda en 75–90 usuarios con buen servicio. El archivo `resultados/carga_0200/resultados.jtl` se restauró porque estaba contaminado con datos de otras ejecuciones.

# Pruebas de carga, estrés, potencia y rendimiento de NetSentinel (JMeter 5.6.3)

**Entorno:** una sola máquina (12 núcleos, 15 GB) con JMeter, backend FastAPI (1 proceso uvicorn), PostgreSQL 16 y frontend en Docker. Base con 214 388 registros en `firewall_logs` durante las pruebas (la mitad era una carga duplicada, eliminada después; con 107 194 las consultas de agregación serían más rápidas). JMeter compite por CPU con la aplicación, por lo que las cifras son conservadoras y válidas solo para este entorno.

**Usuario virtual:** inicia sesión una vez y recorre 9 endpoints (salud, perfil, 4 consultas del panel, hallazgos, logs, alertas) con 1–2 s de espera entre peticiones. Cada escalón: rampa de 20 s y 90 s sostenidos.

**Criterio de "máximo de usuarios":** 0 % de errores y percentil 95 ≤ 1000 ms.

## Resultado principal

Se distinguen tres umbrales, porque "sin que colapse" no es lo mismo que "con buen servicio":

| Umbral | API completa (HTTP) | Base de datos (SQL directo) |
|---|---|---|
| **Buen servicio** (0 % errores y p95 ≤ 1 s en cada endpoint/consulta, sin contar el login) | **190 usuarios** (peor endpoint 674–730 ms en 3 corridas); recomendado declarar **175** | **75 usuarios** (2 corridas; 90 en una). Con 100 falla: la consulta de agregación tarda ≈1390 y ≈1010 ms |
| **Sin errores, pero lento** (respuestas de 2–8 s) | hasta **600 usuarios** (0 % errores, p95 7,7 s) | hasta **200 usuarios**; con 300 aparecen errores (0,08 %) |
| **Colapso** | **700 usuarios**: 10,7 % de errores y el backend queda bloqueado | **400 usuarios**: 3,7 % de errores; 800: 21 % |

**Número de usuarios conectados simultáneamente sin que colapse: 600 en la API** (700 la rompe). Con calidad aceptable de respuesta, 175–190. El servidor se satura en ~95 peticiones/s: más usuarios solo alargan las esperas.

## Variabilidad entre corridas (`evidencias/tabla_replicas.csv`)

Cada punto cercano al límite se repitió 3 veces. La corrida original de 200 usuarios dio p95 de 1190 y 1139 ms (solo se conserva la segunda en `resultados/`); las repeticiones dieron 811 y 634 ms. Por eso 200 es un valor límite que depende de la corrida.

| Usuarios | p95 corrida 1 | p95 corrida 2 | p95 corrida 3 | ¿Cumple p95 ≤ 1 s? |
|---|---|---|---|---|
| 175 | 396 | 414 | 685 | Sí, 3 de 3 |
| 190 | 618 | 567 | 577 | Sí, 3 de 3 |
| 200 | 1139 | 811 | 634 | Variable (2 de 3) |
| 250 | 1241 | 1435 | 1373 | No, 0 de 3 |

Hay una variación de hasta ±30 % del p95 entre corridas, atribuible a que JMeter y la aplicación comparten máquina.

## Barrido fino 500–1100 usuarios (API)

| Usuarios | Errores % | p95 ms | Peticiones/s |
|---|---|---|---|
| 500 | 0 | 6851 | 87,3 |
| 600 | 0 | 7664 | 86,3 |
| 700 | 10,66 | 30 030 | 61,0 |
| 900 | 1,84 | 24 742 | 63,6 |
| 1000 | 33,87 | 30 031 | 69,9 |
| 1100 | 49,91 | 30 032 | 96,3 |

Tras el escalón de 700 el backend quedó bloqueado (`resultados/bloqueos.log`) y se reinicio antes del siguiente; por eso 900 (1,8 %) es mejor que 700 y no debe leerse como mejora. Con un bloqueo, el resultado depende de qué tan pronto se alcance la saturación del pool de conexiones. El comportamiento del bloqueo se detalla más abajo.

## Prueba de carga escalonada, API (`evidencias/tabla_carga.csv`, `curva_carga.png`)

| Usuarios | Errores % | p95 ms | Peticiones/s |
|---|---|---|---|
| 10 | 0 | 23 | 6,0 |
| 50 | 0 | 34 | 29,8 |
| 100 | 0 | 90 | 58,8 |
| 150 | 0 | 268 | 86,0 |
| 175 | 0 | 396 | 95,1 |
| 190 | 0 | 618 | 92,6 |
| 200 | 0 | 1190 / 1139 | 91,5 / 81,1 |
| 250 | 0 | 1241 | 94,8 |
| 300 | 0 | 2327 | 91,1 |
| 400 | 0 | 4690 | 81,6 |
| 800 | 0,43 | 23 671 | 64,1 |
| 1200 | 57,8 | 30 033 | 87,5 |
| 1600 | 86,3 | 30 036 | 71,1 |

## Prueba contra la base de datos (`evidencias/tabla_bd.csv`, `curva_bd.png`)

Consultas `SELECT` de solo lectura (agregados, series, top talkers, listados paginados, búsqueda de usuario) vía JDBC directo, pool de 80 conexiones.

| Usuarios | Errores % | p95 ms | Consultas de sesión/s |
|---|---|---|---|
| 10 | 0 | 164 | 6,0 |
| 50 | 0 | 236 | 29,0 |
| 100 | 0 | 532 | 55,0 |
| 150 | 0 | 3853 | 59,7 |
| 200 | 0 | 5373 | 60,6 |
| 300 | 0,08 | 9659 | 52,7 |
| 400 | 3,72 | 12 419 | 50,6 |
| 800 | 21,19 | 13 276 | 84,3 |

Las consultas de agregación recorren toda la tabla de logs sin caché; ese costo domina y es el cuello de botella. Los errores a partir de 400 son esperas agotadas (10 s) por el pool de conexiones.

## Estrés (pico) y recuperación

- Pico de 600 usuarios en 10 s: 14,4 % de errores (timeouts), p95 de 30 s.
- **Defecto hallado:** tras el pico, el backend quedó bloqueado. PostgreSQL mostraba 20 conexiones `idle in transaction` durante minutos, el log del backend `QueuePool limit of size 10 overflow 10 reached` y la CPU en 0 %. La prueba de recuperación (50 usuarios) dio 100 % de errores (`resultados/recuperacion_0050`). Solo reiniciar el contenedor lo restauró. Causa probable (no confirmada en el código): bloqueo mutuo entre el pool de conexiones (20) y el grupo de hilos de FastAPI. Recomendación: aumentar/ajustar el pool, limitar concurrencia (varios workers de uvicorn, timeouts) y reproducir tras el cambio.

## Login y resistencia (repetidas tras reiniciar el backend)

- Login continuo con 20 usuarios (Argon2): 18,4 login/s, media 1034 ms, p95 2232 ms, 0 % de errores. El hash de contraseña es costoso y limita los inicios de sesión simultáneos.
- Resistencia: 150 usuarios durante 10 min (54 859 peticiones): 0 % de errores, 91,6 peticiones/s, media 100 ms, p95 428 ms, p99 716 ms. Sin degradación en el tiempo.

## Limitaciones

Cliente y servidor en la misma máquina; un solo proceso del backend; una sola corrida en los escalones fuera del rango 175–250; la espera de 1–2 s se aplica entre cada petición, por lo que "usuario conectado" equivale a un usuario activo con ~1,5 s entre acciones. La base se probó sin pasar por la API. Los informes HTML están en `resultados/<prueba>/informe/index.html`; el plan y los scripts, en `plan/` y `*.sh`. Las corridas de login y resistencia originales (invalidadas por el bloqueo) fueron sobrescritas por las repeticiones.

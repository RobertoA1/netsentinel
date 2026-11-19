# Product

<!-- impeccable:product-schema 1 -->

(Inferido del encargo escrito; no hubo ronda de preguntas con una persona: no había mecanismo de respuesta en esta ejecución.)

## Platform

web

## Stack
React 19 + Vite + TypeScript estricto, React Router, TanStack Query, cliente fetch propio, npm. Decidido por el encargo.

## Users
- Administrador de TI o analista único de una PYME peruana, no experto en seguridad. Revisa la herramienta unos minutos al día y necesita saber en segundos si hay algo que atender.
- Auditor: revisa la bitácora (quién entró a qué módulo, cuándo, cuánto tiempo).
- Gerente: descarga reportes de gestión.

## Product Purpose
NetSentinel analiza logs de firewall/IDS para PYMEs que no pueden costear un SIEM. Da visibilidad de exfiltración y beaconing; un LLM local filtra el ruido y explica cada hallazgo en lenguaje llano. Éxito: el usuario distingue de inmediato lo que merece atención de lo que no.

## Positioning
Detección determinista con evidencia verificable, más una interpretación de IA local (sin enviar logs a la nube) siempre etiquetada como interpretación y separada de los hechos.

## Operating Context
Interfaz en español (Perú), es-PE, zona horaria del perfil. Tema claro y oscuro. Bitácora de módulos obligatoria para auditoría. Permisos RBAC `modulo:accion` filtran navegación y acciones. Responsive hasta tablet.

## Capabilities and Constraints
Contrato en docs/API_CONTRACT.md. Módulos: dashboard, logs, hallazgos, alertas, reportes, ingesta, activos, fuentes, listas, detección, motor IA, usuarios, roles, bitácora, perfil.

## Brand Commitments
Sobrio, operativo, denso pero legible, confiable. Sin estética hacker (neón verde sobre negro) ni dashboard genérico de tarjetas con degradado.

## Evidence on Hand
Sin datos reales; el desarrollo usa un modo mock con datos sintéticos conformes al contrato.

## Product Principles
1. Responder primero "¿hay algo que atender?".
2. Hechos deterministas y opinión de la IA nunca se mezclan visualmente.
3. Lenguaje llano antes que jerga.
4. Cada acción sensible está protegida por permiso y confirmación.
5. La auditoría es un requisito, no un añadido.

## Accessibility & Inclusion
Contraste AA, operable por teclado, foco visible.

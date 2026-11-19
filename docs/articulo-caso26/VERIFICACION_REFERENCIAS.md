# Verificación de referencias (APA 7, Crossref)

Método: cada DOI se consultó en la API pública de Crossref con un cliente genérico, sin enviar información del proyecto. Los metadatos (autores, año, revista, volumen, número, páginas) provienen de `build/crossref_raw.json`; `build/refs.py` los convierte a APA 7 y `build/verificar.py` comprueba que las 39 referencias del documento sean idénticas a las generadas y que cada cita del texto corresponda a una referencia (y viceversa).

Criterios: año = año de la edición impresa cuando existe (Sarhan 2022, Verkerken 2022, Bates 2024); páginas con guion = rango; sin rango = número de artículo; sin volumen = publicación anticipada. Se corrigió el apellido compuesto de Rombaldo Junior. Se descartó `chicco2021b` (no citada).

| # | Referencia (clave) | Tipo Crossref | Año usado | DOI | Título coincide con Crossref |
|---|---|---|---|---|---|
| 1 | Abualghanam et al. (abualghanam2023) | journal-article | 2023 | 10.3390/electronics12061467 | sí |
| 2 | Adriko y Nurse (adriko2024) | journal-article | 2024 | 10.1108/ics-01-2024-0025 | sí |
| 3 | Alhuzali (alhuzali2025) | journal-article | 2025 | 10.7717/peerj-cs.3371 | sí |
| 4 | Bates et al. (bates2023) | journal-article | 2024 | 10.1080/01621459.2023.2197686 | sí |
| 5 | Cantone et al. (cantone2024) | journal-article | 2024 | 10.1109/access.2024.3472907 | sí |
| 6 | Chicco et al. (chicco2021) | journal-article | 2021 | 10.1186/s13040-021-00244-z | sí |
| 7 | Dikici y Bilgin (dikici2026) | journal-article | 2026 | 10.1111/exsy.70331 | sí |
| 8 | Divakaran y Peddinti (divakaran2025) | journal-article | 2025 | 10.1109/msec.2024.3504512 | sí |
| 9 | García et al. (garcia2014) | journal-article | 2014 | 10.1016/j.cose.2014.05.011 | sí |
| 10 | Gaspar et al. (gaspar2024) | journal-article | 2024 | 10.1109/access.2024.3368377 | sí |
| 11 | González-Granadillo et al. (gonzalez2021) | journal-article | 2021 | 10.3390/s21144759 | sí |
| 12 | Greshake et al. (greshake2023) | proceedings-article | 2023 | 10.1145/3605764.3623985 | sí |
| 13 | Hevner et al. (hevner2004) | journal-article | 2004 | 10.2307/25148625 | NO |
| 14 | Hossain y Islam (hossain2023) | journal-article | 2023 | 10.1038/s41598-023-48230-1 | sí |
| 15 | Houssel et al. (houssel2026) | journal-article | 2026 | 10.1016/j.compeleceng.2025.110826 | sí |
| 16 | Jiang (jiang2026) | proceedings-article | 2026 | 10.1109/isctis70043.2026.11572627 | sí |
| 17 | Kapoor y Narayanan (kapoor2023) | journal-article | 2023 | 10.1016/j.patter.2023.100804 | sí |
| 18 | Karlsen et al. (karlsen2024) | journal-article | 2024 | 10.1007/s10922-024-09831-x | sí |
| 19 | Kheddar (kheddar2025) | journal-article | 2025 | 10.1016/j.inffus.2025.103347 | sí |
| 20 | Kinyua y Awuah (kinyua2021) | journal-article | 2021 | 10.32604/iasc.2021.016240 | sí |
| 21 | Liu et al. (liu2022) | journal-article | 2022 | 10.1016/j.infsof.2022.106856 | sí |
| 22 | Ma et al. (ma2026) | journal-article | 2026 | 10.1145/3842759 | sí |
| 23 | Oškera et al. (oskera2025) | proceedings-article | 2025 | 10.23919/cnsm67658.2025.11297465 | sí |
| 24 | Palma et al. (palma2025) | journal-article | 2025 | 10.3390/jcp5030055 | sí |
| 25 | Rombaldo Junior et al. (rombaldo2026) | journal-article | 2026 | 10.1093/cybsec/tyag030 | sí |
| 26 | Saied y Guirguis (saied2025) | journal-article | 2025 | 10.1038/s41598-025-90420-6 | sí |
| 27 | Sarhan et al. (sarhan2022) | journal-article | 2022 | 10.1007/s11036-021-01843-0 | sí |
| 28 | Shinan et al. (shinan2021) | journal-article | 2021 | 10.3390/sym13050866 | sí |
| 29 | Sommer y Paxson (sommer2010) | proceedings-article | 2010 | 10.1109/sp.2010.25 | sí |
| 30 | Tariq et al. (tariq2025) | journal-article | 2025 | 10.1145/3723158 | sí |
| 31 | Tendikov et al. (tendikov2024) | journal-article | 2024 | 10.1016/j.rineng.2024.102254 | sí |
| 32 | Velasco-Mata et al. (velasco2021) | journal-article | 2021 | 10.1109/access.2021.3108222 | sí |
| 33 | Velasco-Mata et al. (velasco2023) | journal-article | 2023 | 10.1038/s41598-023-31260-0 | sí |
| 34 | Verkerken et al. (verkerken2021) | journal-article | 2022 | 10.1007/s10922-021-09615-7 | sí |
| 35 | Woesle y Buettner (woesle2026) | journal-article | 2026 | 10.1109/access.2026.3700492 | sí |
| 36 | Xu et al. (xu2026) | journal-article | 2026 | 10.1145/3769676 | sí |
| 37 | Yao et al. (yao2024) | journal-article | 2024 | 10.1016/j.hcc.2024.100211 | sí |
| 38 | Zhan et al. (zhan2025) | proceedings-article | 2025 | 10.18653/v1/2025.findings-naacl.395 | sí |
| 39 | Zhang et al. (zhang2025) | journal-article | 2025 | 10.1016/j.knosys.2025.114064 | sí |

Resumen: 39 referencias, 39 con DOI resuelto en Crossref, 38/39 con título coincidente (la excepción, Hevner et al., difiere solo porque Crossref añade un "1" de nota al pie al título) (ignorando mayúsculas y signos). Publicadas 2021-2026: 36/39 (92.3 %). Anteriores a 2021: García et al. (2014), Hevner et al. (2004) y Sommer y Paxson (2010), conservadas por ser fuentes metodológicas y de conjunto de datos canónicas. Todas son artículos de revista o de actas arbitradas.

Limitación: Crossref confirma la existencia y los metadatos, no que el contenido respalde cada afirmación; esa lectura no se automatizó y queda para revisión de los autores.

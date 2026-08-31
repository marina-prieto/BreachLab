# TFM — Análisis práctico de vulnerabilidades web comunes mediante un entorno de pruebas controlado

Trabajo Fin de Máster (Máster en Formación Permanente en Ciberseguridad y
Seguridad de la Información, UCLM). Estudia la OWASP Web Security Testing
Guide (WSTG) como metodología de referencia, deriva de ella una metodología
propia más ágil y la aplica de forma controlada sobre **BreachLab**, un
laboratorio web deliberadamente vulnerable (backend Flask + frontend Astro)
desarrollado para este trabajo.

## Contenido

- [`memoria-latex/`](memoria-latex/) — memoria completa en LaTeX y compilada
  (`main.pdf`).
- [`backend/`](backend/) y [`frontend/`](frontend/) — código de BreachLab.
- [`GUIA.md`](GUIA.md) — guía de explotación paso a paso de las seis
  vulnerabilidades.
- [`CVSS.md`](CVSS.md) — razonamiento de cada vector CVSS v3.1.
- [`csrf_poc.html`](csrf_poc.html) — prueba de concepto de CSRF.
- [`docker-compose.yml`](docker-compose.yml) — despliegue del laboratorio.
- [`COMPOSE_SNIPPET.yml`](COMPOSE_SNIPPET.yml) — fragmento para integrar
  BreachLab en un compose más amplio (por ejemplo, junto a DVWA/Juice Shop).

## Puesta en marcha rápida

```bash
docker compose up --build
# Abre http://localhost:8080
```

Instrucciones detalladas, usuarios de prueba y modo desarrollo en
[`GUIA.md`](GUIA.md) y en el anexo A de la memoria.

## Estructura completa

Ver el capítulo "Contenido del repositorio" de la memoria
(`memoria-latex/main.pdf`) para el detalle completo de cada carpeta.

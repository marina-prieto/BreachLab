<div align="center">

# Análisis práctico de vulnerabilidades web comunes

**Trabajo Fin de Máster · Máster en Formación Permanente en Ciberseguridad y Seguridad de la Información (UCLM)**

[![Licencia](https://img.shields.io/badge/uso-laboratorio%20aislado-red)]()
[![Backend](https://img.shields.io/badge/backend-Flask-000000?logo=flask)]()
[![Frontend](https://img.shields.io/badge/frontend-Astro-FF5D01?logo=astro)]()
[![DB](https://img.shields.io/badge/db-SQLite-07405E?logo=sqlite)]()
[![Docker](https://img.shields.io/badge/despliegue-Docker%20Compose-2496ED?logo=docker)]()

*BreachLab - Un laboratorio web deliberadamente vulnerable, construido desde cero para estudiar, explotar y corregir las vulnerabilidades más comunes del OWASP Top 10.*

</div>

---

## 🎯 Resumen del trabajo

Este TFM parte del **OWASP Web Security Testing Guide (WSTG)** como metodología de referencia para la evaluación de seguridad en aplicaciones web. A partir de ella, se propone y documenta una **metodología propia, más ágil**, adaptada a entornos de prueba controlados y con fines formativos.

Esa metodología se aplica de forma práctica sobre **BreachLab**, una aplicación web desarrollada específicamente para este trabajo, que reproduce de manera realista seis categorías de vulnerabilidades comunes en aplicaciones modernas. Para cada una se documenta:

- El **fundamento teórico** y su ubicación en la metodología WSTG/propia.
- Un **caso práctico de explotación**, paso a paso, con capturas y comandos reproducibles (`curl`, `sqlmap`, PoC HTML, etc.).
- Su **corrección**, activable en caliente mediante el parámetro `?safe=1`, sin necesidad de desplegar una versión distinta.
- Un **análisis CVSS v3.1** razonado, vector a vector.

El resultado es un ciclo completo *vulnerar → explotar → evidenciar → corregir → puntuar*, replicable por cualquier persona que despliegue el laboratorio con un solo comando.

La memoria completa (LaTeX, compilada a PDF) se encuentra en [`memoria-latex/`](./memoria-latex).

---

## 🧪 ¿Qué es BreachLab?

**BreachLab** es una aplicación web de dos capas —**backend Flask** (API JSON) y **frontend Astro**— servidas bajo el mismo origen, diseñada para ser deliberadamente insegura. A diferencia de otros laboratorios de referencia (DVWA, Juice Shop), BreachLab:

- Se ha desarrollado **desde cero para este TFM**, lo que permite controlar con precisión dónde y cómo se introduce cada fallo.
- Incluye un **interruptor global de seguridad** (`?safe=1`) que activa simultáneamente las contramedidas en frontend y backend, permitiendo comparar el comportamiento vulnerable y el corregido sin cambiar de despliegue.
- Registra cada acción relevante (login, inyección, IDOR, cambios de contraseña...) en un **log de eventos** (`backend/logs/attacks.log`), usado como evidencia objetiva más allá de las capturas de pantalla.

---

## 🏗️ Arquitectura

```
Navegador
   │  http (mismo origen)
   ▼
┌─────────────┐   /            (estático)      ┌──────────────────┐
│  web (nginx │ ──────────────────────────────▶│   Astro (dist)   │
│  + Astro)   │   /api/*  (proxy)               └──────────────────┘
└─────────────┘──────────────┐
                              ▼
                       ┌──────────────┐     ┌──────────┐
                       │ api (Flask)  │────▶│ SQLite   │
                       └──────────────┘     └──────────┘
```

Servir frontend y backend en el **mismo origen** (vía nginx en Docker o vía el proxy de Vite/Astro en desarrollo) es una decisión de diseño deliberada: permite que la cookie de sesión viaje sin fricción de CORS y que el CSRF pueda demostrarse de forma limpia y realista.

---

## 🐞 Vulnerabilidades incluidas

Seis vulnerabilidades deliberadas, cada una con su rama vulnerable y su rama segura conviviendo en el mismo código:

| # | Vulnerabilidad | Ubicación | Apartado memoria |
|---|---|---|---|
| 1 | **Inyección SQL** | `backend/api.py` → `login()`, query concatenada | 6.1 |
| 2 | **XSS (basado en DOM)** | `frontend/src/pages/note.astro` → `body.innerHTML` | 6.2 |
| 3 | **CSRF** | `backend/api.py` → `change_password()` (GET, sin token) | 6.3 |
| 4 | **Fallos de autenticación** | `backend/api.py` → `login()` (hash, lockout, enumeración) | 6.4 |
| 5 | **Control de acceso roto / IDOR** | `backend/api.py` → `note_get()`, `admin()` | 6.5 |
| 6 | **Configuración de seguridad insegura** | `frontend/nginx.conf` → cabeceras HTTP ausentes | 6.6 |

La vulnerabilidad 6.6 (cabeceras de seguridad) actúa además como **refuerzo en profundidad** frente al XSS de la 6.2: la CSP del modo seguro bloquea también los manejadores de evento inline aunque el contenido siguiera inyectándose vía `innerHTML`.

El razonamiento completo de cada vector y puntuación **CVSS v3.1** está en [`CVSS.md`](./CVSS.md), y la guía de explotación paso a paso —con payloads, comandos `curl`/`sqlmap` y checklist de capturas— está en [`GUIA.md`](./GUIA.md).

---

## 🚀 Puesta en marcha rápida

### Opción A — Docker (recomendada)

```bash
docker compose up --build
# Abre http://localhost:8080
```

### Opción B — Desarrollo (dos terminales)

```bash
# Terminal 1: backend
cd backend
pip install -r requirements.txt
python api.py                      # API en http://localhost:5000

# Terminal 2: frontend
cd frontend
npm install
npm run dev                        # Front en http://localhost:4321 (proxy /api -> :5000)
```

Abre **http://localhost:4321**.

### Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin123!` | admin |
| `marina` | `contraSegura` | user |
| `pablo` | `qwerty` | user |

---

## 🔒 Modo seguro (`?safe=1`)

BreachLab implementa **las dos versiones de cada vulnerabilidad (vulnerable y corregida) en el mismo despliegue**. Añadiendo `?safe=1` a la URL de cualquier página:

- Se propaga automáticamente a las llamadas al backend **y** al modo de renderizado del frontend.
- Activa a la vez las contramedidas de frontend y backend (consultas parametrizadas, `textContent` en lugar de `innerHTML`, verificación de token CSRF, hash de contraseñas, control de propiedad/rol, cabeceras de hardening...).
- Se refleja en un **badge visible en la barra superior** indicando el modo activo.

Usa el enlace **"Reiniciar base de datos"** en la página de inicio para dejar el laboratorio listo antes de cada captura o demostración.

---

## 📚 Documentación completa

| Documento | Contenido |
|---|---|
| [`GUIA.md`](./GUIA.md) | Arquitectura, puesta en marcha, mapa código→memoria, explotación paso a paso de las 6 vulnerabilidades, checklist de capturas y ampliaciones opcionales |
| [`CVSS.md`](./CVSS.md) | Vectores y puntuaciones CVSS v3.1 razonados para cada vulnerabilidad |
| [`memoria-latex/`](./memoria-latex) | Memoria completa del TFM, en LaTeX y compilada a PDF |
| [`csrf_poc.html`](./csrf_poc.html) | Prueba de concepto funcional de CSRF (requiere editar `LAB_HOST`) |

---

## ⚠️ Aviso de seguridad

> **Uso exclusivo en entorno de laboratorio aislado.**
> Este proyecto contiene fallos de seguridad **deliberados e intencionados** con fines exclusivamente educativos y de investigación en el marco de un TFM. **No debe desplegarse en Internet ni en ningún entorno accesible desde redes no controladas.**

---

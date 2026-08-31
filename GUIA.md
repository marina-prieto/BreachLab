# Guía del laboratorio vulnerable — arquitectura front/back (TFM)

App con **backend Flask (API JSON)** + **frontend Astro**, servidos en el mismo
origen. Contiene las cinco vulnerabilidades del alcance, más una sexta
(configuración de seguridad insegura) que refuerza la del XSS, y su
corrección, activable con `?safe=1`.

> ⚠️ **Uso exclusivo en laboratorio aislado.** Fallos deliberados. No exponer a Internet.

---

## 1. Arquitectura

```
  Navegador
     │  http (mismo origen)
     ▼
  ┌────────────┐   /            (estático)      ┌──────────────────┐
  │  web (nginx│───────────────────────────────▶│  Astro (dist)    │
  │  + Astro)  │   /api/*  (proxy)               └──────────────────┘
  └────────────┘──────────────┐
                              ▼
                       ┌──────────────┐     ┌──────────┐
                       │ api (Flask)  │────▶│ SQLite   │
                       └──────────────┘     └──────────┘
```

Servir front y back en el **mismo origen** (vía nginx en Docker, o vía el proxy
de Vite en desarrollo) es lo que permite que la cookie de sesión viaje sin CORS
y que el CSRF se pueda demostrar de forma limpia.

---

## 2. Puesta en marcha

### Opción A — Docker (recomendada para la memoria)
```bash
cd tfm-lab
docker compose up --build
# Abre http://localhost:8080
```

### Opción B — Desarrollo (dos terminales)
```bash
# Terminal 1: backend
cd tfm-lab/backend
pip install -r requirements.txt
python api.py                      # API en http://localhost:5000

# Terminal 2: frontend
cd tfm-lab/frontend
npm install
npm run dev                        # Front en http://localhost:4321 (proxy /api -> :5000)
```
Abre **http://localhost:4321**.

### Añadirla a tu docker-compose del laboratorio
Tienes el fragmento en `COMPOSE_SNIPPET.yml` (usa la misma red `lab` que DVWA/Juice Shop).

### Usuarios de prueba
| Usuario | Contraseña   | Rol   |
|---------|--------------|-------|
| admin   | `Admin123!`  | admin |
| marina  | `contraSegura` | user  |
| pablo   | `qwerty`     | user  |

### El interruptor `?safe=1`
Añádelo a la URL de **cualquier página**. Se propaga a las llamadas al backend
**y** al modo de renderizado del frontend, así que activa a la vez las
contramedidas de front y back. El badge de la barra superior indica el modo.
Usa el enlace **Reiniciar base de datos** (en la página de inicio) para capturas limpias.

---

## 3. Mapa código → memoria

| Vulnerabilidad | Fichero | Punto exacto | Apartado |
|---|---|---|---|
| Inyección SQL | `backend/api.py` | `login()`, query concatenada | 6.1 |
| XSS (DOM) | `frontend/src/pages/note.astro` | `body.innerHTML = n.content` | 6.2 |
| CSRF | `backend/api.py` | `change_password()` (GET, sin token) | 6.3 |
| Fallos de autenticación | `backend/api.py` | `login()` (hash, lockout, enumeración) | 6.4 |
| Control de acceso / IDOR | `backend/api.py` | `note_get()`, `admin()` | 6.5 |
| Configuración de seguridad insegura | `frontend/nginx.conf` | cabeceras HTTP ausentes en modo vulnerable | 6.6 |

Vectores y puntuaciones CVSS v3.1 razonados para las seis: ver [`CVSS.md`](CVSS.md).

---

## 4. Explotación de cada vulnerabilidad

### 4.1. Inyección SQL — 6.1
- **Dónde:** `backend/api.py`, rama vulnerable de `login()`:
  `"...WHERE username = '%s' AND password = '%s'" % (u, p)`.
- **Navegador:** en la pantalla de login, usuario `admin' -- ` (con espacio tras
  `--`) y cualquier contraseña → entras como admin.
- **curl (a través del front):**
  ```bash
  curl -i -X POST http://localhost:8080/api/login \
       -H 'Content-Type: application/json' \
       -d '{"username":"admin'\'' -- ","password":"x"}'
  ```
  La respuesta incluye el campo `query` para que veas la consulta inyectada.
- **sqlmap:**
  ```bash
  sqlmap -u "http://localhost:8080/api/login" \
         --data='{"username":"marina","password":"x"}' \
         --headers="Content-Type: application/json" -p username --batch --dbs
  ```
- **Corrección (`?safe=1`):** consulta parametrizada + hash → "Credenciales inválidas".
- **Capturar:** payload, acceso concedido (+ campo `query`), salida de sqlmap, rechazo en seguro, diff de la línea.

### 4.2. XSS almacenado / DOM — 6.2
- **Dónde:** el dato se guarda crudo en el backend y el fallo se materializa en
  `frontend/src/pages/note.astro`, en `body.innerHTML = n.content` (modo
  vulnerable) frente a `body.textContent = n.content` (modo seguro).
- **Payload (importante):** como se inyecta vía `innerHTML`, un `<script>` no se
  ejecuta; usa un vector con manejador de evento:
  ```html
  <img src=x onerror="alert(document.cookie)">
  ```
- **Pasos:** inicia sesión → *Notas* → crea una nota con ese contenido → ábrela.
  El `alert` se dispara. Como la cookie es `HttpOnly=False` (deliberado), el
  script puede leerla → demuestra el robo de sesión **dentro del laboratorio**.
- **Corrección (`?safe=1`):** se usa `textContent` → el payload se muestra como
  texto y no se ejecuta. Menciona además CSP y cookie `HttpOnly` en 6.2.5.
- **Nota para la memoria:** al pasar a arquitectura SPA, el XSS deja de ser de
  plantilla (servidor) y pasa a ser **basado en DOM** (cliente). Es un buen
  punto de discusión sobre cómo la arquitectura cambia la superficie del fallo.
- **Capturar:** el formulario con el payload, el `alert` ejecutándose, la versión
  como texto en modo seguro.

### 4.3. CSRF — 6.3
- **Dónde:** `backend/api.py`, `change_password()`. Rama vulnerable: acepta
  **GET** y no valida token. Segura: exige **POST + token CSRF** de la sesión.
- **Pasos:**
  1. Inicia sesión como víctima (p. ej. `marina`).
  2. Edita `csrf_poc.html` y sustituye `LAB_HOST` (p. ej. `localhost:8080`).
  3. Abre `csrf_poc.html`. La contraseña de `marina` cambia a `hackeada123` sin
     su consentimiento.
  4. Verifícalo: cierra sesión, prueba la contraseña vieja (falla) y la nueva (entra).
- **SameSite (clave 6.3.5):** la cookie es `SameSite=Lax`. Por eso la PoC es un
  **formulario GET de navegación de nivel superior** (no un `<img>`): Lax envía
  la cookie en navegaciones top-level por GET. Conclusión para la memoria: los
  cambios de estado nunca deben ir por GET, y `SameSite` por sí solo no basta —
  hay que usar tokens (lo demuestra el endpoint seguro).
- **Corrección:** el formulario "seguro" de *Perfil* (POST + token) rechaza el
  intento; el mismo endpoint por GET responde 405.
- **Capturar:** la PoC, la contraseña cambiada sin consentimiento, el 403/405 seguro.

### 4.4. Fallos de autenticación — 6.4
- **Dónde:** `backend/api.py`, `login()`. Vulnerable: contraseñas en texto plano,
  sin límite de intentos, y mensajes que permiten **enumerar usuarios**.
  Seguro: hash, bloqueo tras 5 fallos, sesión regenerada, mensaje genérico.
- **Enumeración:** compara la respuesta con usuario inexistente ("El usuario no
  existe") frente a usuario válido con contraseña mala ("Contraseña incorrecta").
- **Fuerza bruta (contraseñas débiles):** `pablo` usa la contraseña real `qwerty`,
  incluida en cualquier lista de contraseñas comunes:
  ```bash
  for p in 123456 password qwerty admin letmein; do
    echo -n "$p -> "
    curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8080/api/login \
      -H 'Content-Type: application/json' -d "{\"username\":\"pablo\",\"password\":\"$p\"}"
  done   # el 200 (con "qwerty") es la contraseña correcta
  ```
- **Corrección (`?safe=1`):** tras 5 fallos, HTTP 429 "Cuenta bloqueada";
  mensaje genérico (sin enumeración); verificación por hash.
- **Capturar:** los dos mensajes distintos, el acierto por fuerza bruta, el
  bloqueo y el mensaje genérico en seguro.

### 4.5. Control de acceso roto / IDOR — 6.5
- **Dónde:** `backend/api.py`, `note_get()` (IDOR) y `admin()` (sin comprobar rol).
- **IDOR:** inicia sesión como `marina` y abre la nota de `pablo` cambiando el id
  (en la lista de notas o directamente `/note?id=3`). Ves datos ajenos.
  ```bash
  curl -b marina.txt http://localhost:8080/api/notes/3   # ves "hunter2" (de pablo)
  ```
- **Escalada de privilegios:** como `marina` (rol user), entra en *Admin*. Ves el
  panel y **las contraseñas de todos** sin ser admin.
- **Corrección (`?safe=1`):** `/api/notes/3?safe=1` → 403 (comprobación de
  propietario); *Admin* en modo seguro como `marina` → 403 (comprobación de rol).
- **Capturar:** el acceso a la nota ajena, el panel admin desde cuenta normal,
  los 403 en modo seguro.

### 4.6. Configuración de seguridad insegura — cabeceras HTTP — 6.6
- **Dónde:** `frontend/nginx.conf`, bloque `location /`. En modo vulnerable no
  se envía ninguna cabecera de hardening; en modo seguro (`?safe=1`) se añaden
  `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` y
  `Referrer-Policy`.
- **Comprobación (sin navegador):**
  ```bash
  curl -sD - -o /dev/null http://localhost:8080/dashboard/            # sin cabeceras
  curl -sD - -o /dev/null "http://localhost:8080/dashboard/?safe=1"   # con CSP, nosniff...
  ```
- **Relación con el XSS (6.2):** la CSP del modo seguro (`script-src 'self'`)
  bloquea también los manejadores de evento inline (`onerror=...`) aunque el
  contenido se siguiera inyectando por `innerHTML`. Es un buen ejemplo de
  **defensa en profundidad**: dos controles independientes (sanitizar en el
  front + cabecera en el servidor) mitigando el mismo fallo.
- **Capturar:** cabeceras ausentes en vulnerable, cabeceras presentes en
  seguro, y (opcional) un iframe embebiendo el sitio para demostrar
  *clickjacking* sin `X-Frame-Options`.

---

## 5. Registro de eventos (evidencias)

Cada acción relevante (login correcto/fallido, inyección SQL, cambio de
contraseña, acceso a notas ajenas, panel de admin) se registra en
`backend/logs/attacks.log` (persistido fuera del contenedor vía volumen en
`docker-compose.yml`). Cada línea incluye timestamp, modo (`vulnerable`/`seguro`),
IP, evento y detalle (usuario, id de nota, query SQL si aplica...).

Úsalo para adjuntar evidencias objetivas en la memoria en vez de solo
capturas de pantalla: por ejemplo, tras explotar el IDOR verás una línea
`event=idor_exploited user=marina note_id=3 owner_id=3`, y tras activar
`?safe=1` la misma acción genera `event=idor_blocked`.

```bash
# Sigue el log en tiempo real mientras explotas cada vulnerabilidad
tail -f backend/logs/attacks.log
```

---

## 6. Checklist de capturas del capítulo 6
Por cada vulnerabilidad (incluida la 6.6):
- [ ] Vector/payload usado.
- [ ] Explotación exitosa (modo vulnerable).
- [ ] Prueba de la mitigación (modo `?safe=1`).
- [ ] Fragmento de código vulnerable vs seguro (indica fichero y línea).
- [ ] Línea correspondiente en `backend/logs/attacks.log` como evidencia.
- [ ] Vector CVSS v3.1 + puntuación (calculadora de FIRST.org; partir de `CVSS.md`).

El capítulo 7 compara BreachLab con DVWA y Juice Shop mediante una tabla de
equivalencias (qué módulo/reto de cada laboratorio corresponde a cada
vulnerabilidad), no mediante una reproducción práctica de los ataques en
esos dos laboratorios. Si en algún momento decides hacer esa reproducción
práctica, repite el checklist anterior sobre DVWA y Juice Shop y actualiza
el capítulo 7 con los resultados reales.

---

## 7. Ampliaciones opcionales
- SQLi **ciega** basada en tiempo en un buscador de notas.
- XSS **reflejado** además del basado en DOM.
- Identificadores UUID en las notas para discutir "IDOR con id no predecible".
- Comparativa con una herramienta DAST (p. ej. OWASP ZAP baseline scan) contra
  modo vulnerable vs. `?safe=1`, como tabla objetiva para el capítulo 7.

---

## 8. Estructura de ficheros
```
tfm-lab/
├─ docker-compose.yml         # levanta api + web (nginx) en http://localhost:8080
├─ COMPOSE_SNIPPET.yml        # para integrarlo en tu compose del laboratorio
├─ csrf_poc.html              # PoC de CSRF (sustituye LAB_HOST)
├─ CVSS.md                    # vectores y puntuaciones CVSS v3.1 razonados
├─ backend/
│  ├─ api.py                  # API Flask con las 6 vulnerabilidades + toggle safe
│  ├─ logs/attacks.log        # evidencias (generado en tiempo de ejecución)
│  ├─ requirements.txt
│  └─ Dockerfile
└─ frontend/                  # proyecto Astro
   ├─ astro.config.mjs        # proxy /api -> backend en desarrollo
   ├─ nginx.conf              # sirve el estático, proxy en Docker y cabeceras
   ├─ Dockerfile              # build de Astro + nginx (usa npm ci con el lockfile)
   ├─ .dockerignore           # evita que node_modules del host se copie a la imagen
   ├─ package.json
   ├─ package-lock.json
   └─ src/
      ├─ layouts/Layout.astro
      ├─ lib/client.js        # helpers de API y modo safe
      ├─ styles/global.css
      └─ pages/               # index (login), dashboard, note, profile, admin
```
> Tras descomprimir, en `frontend/` ejecuta `npm install` (las dependencias no
> se incluyen en el zip).

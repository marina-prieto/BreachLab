# Vectores y puntuaciones CVSS v3.1

> Estos son los vectores y puntuaciones ya adoptados en el capítulo 6 de la
> memoria (coinciden exactamente). Si en algún momento cambias de opinión
> sobre alguna métrica, razónalo aquí primero y actualiza después el
> apartado correspondiente del capítulo 6 para que ambos documentos sigan
> coincidiendo.

## 1. Inyección SQL — bypass de autenticación (`POST /api/login`)

`CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` → **9.1 (Crítica)**

- **AV:N / AC:L / PR:N / UI:N** — se explota de forma remota, sin condiciones
  especiales, sin cuenta previa y sin interacción de la víctima.
- **C:H / I:H** — permite leer datos de otros usuarios y autenticarse como
  cualquiera (incluido admin) sin conocer la contraseña.
- **A:N** — no se demuestra impacto en disponibilidad (no se explota DoS).

## 2. XSS almacenado/DOM — robo de sesión (`note.astro`, cookie `HttpOnly=False`)

`CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:L/A:N` → **7.5 (Alta)**

- **PR:L** — el atacante necesita una cuenta (para crear la nota con el payload).
- **UI:R** — requiere que la víctima abra la nota.
- **S:C** (*Scope Changed*) — el impacto trasciende el componente vulnerable:
  la sesión robada compromete la cuenta de la víctima, una autoridad de
  seguridad distinta.
- **C:H** — la cookie de sesión (sin `HttpOnly`) permite secuestro de cuenta.
- **I:L** — el atacante puede actuar como la víctima dentro del alcance de la app.

## 3. CSRF — cambio de contraseña sin token (`GET/POST /api/profile/password`)

`CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:H/A:N` → **6.5 (Media)**

- **PR:N** — el atacante no necesita cuenta propia, solo que la víctima tenga
  sesión activa.
- **UI:R** — la víctima debe abrir la página con el formulario/PoC maliciosa.
- **I:H** — cambia la contraseña de la víctima sin su consentimiento
  (equivale a apropiación de cuenta).

## 4. Fallos de autenticación — enumeración de usuarios + sin límite de intentos (`POST /api/login`)

`CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` → **5.3 (Media)**

- Puntúa la **fuga de información** que permite distinguir "usuario no existe"
  de "contraseña incorrecta" (**C:L**), combinada con la ausencia de bloqueo
  tras varios fallos, que habilita fuerza bruta sin fricción.
- Este vector puntúa el fallo *en sí mismo*. Si se **encadena** con una
  contraseña débil real (p. ej. `qwerty` de `pablo`), el resultado práctico es
  una toma de cuenta completa, comparable en severidad al vector 1 (SQLi).
  Menciona esta cadena de explotación en la memoria como agravante.

## 5. Control de acceso roto / IDOR (`GET /api/notes/<id>`, `GET /api/admin`)

`CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N` → **6.5 (Media)**

- **PR:L** — requiere una cuenta de usuario normal (p. ej. marina).
- **C:H** — expone notas y contraseñas de otros usuarios, incluidos datos
  ficticios sensibles (tarjeta, contraseña de correo).
- En el caso del panel de admin, las contraseñas expuestas permiten
  **escalada de privilegios por reutilización de credenciales** — coméntalo
  como agravante frente al vector base.

## 6. Configuración de seguridad insegura — cabeceras HTTP ausentes (nginx)

No se puntúa de forma aislada: la ausencia de `Content-Security-Policy`,
`X-Content-Type-Options` o `X-Frame-Options` no es explotable por sí sola,
sino que **amplifica el impacto real** de otras vulnerabilidades (quita una
capa de defensa en profundidad frente al XSS del vector 2, y habilita
*clickjacking*). Como ilustración del riesgo de clickjacking que introduce
por sí sola la falta de `X-Frame-Options`:

`CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N` → **4.3 (Media)**

**Para la memoria:** documenta este vector como *"control compensatorio
ausente"* más que como vulnerabilidad independiente — es el enfoque que
espera un análisis riguroso (relacionarlo explícitamente con el vector 2).

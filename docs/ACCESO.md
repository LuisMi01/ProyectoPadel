# Cuentas y sesión de usuario

Sin contraseñas: **crear cuenta e iniciar sesión son el mismo paso**. La persona escribe su correo,
recibe un enlace y, al abrirlo, entra. Si el correo no tenía cuenta, se crea en ese momento.

## Flujo

```
Web (/acceso/)                     API                                   Base de datos
──────────────                     ───                                   ─────────────
correo ──► POST /acceso/enlace ──► límite: 5 enlaces/hora por correo
                                   token aleatorio ───────────────────► token_acceso (solo el hash, 15 min)
                                   correo con {WEB_URL}/acceso/verificar/?token=…
◄── 202 (exista o no la cuenta)

/acceso/verificar/?token=… ──► POST /acceso/verificar
                                   ¿hash válido y sin caducar? ───────► token_acceso
                                   crea usuario si no existe ─────────► usuario
                                   sesión nueva ──────────────────────► sesion (solo el hash, 30 días)
                                   borra todos los enlaces de ese correo
◄── 204 + cookie «sesion» (HttpOnly, SameSite)

GET /perfil (con la cookie) ──► usuario de la sesión, o 401
POST /acceso/cerrar ──────────► borra la sesión y la cookie
POST /acceso/cerrar-todas ────► borra todas las sesiones del usuario
DELETE /perfil ───────────────► borra el usuario (sesiones, palas y avisos en cascada)
```

| Respuesta | Cuándo |
|---|---|
| `202` en `/acceso/enlace` | Siempre que se envía, exista o no la cuenta (no revela qué correos están registrados). |
| `429` en `/acceso/enlace` | Más de `ENLACES_POR_HORA` enlaces para el mismo correo en una hora. |
| `503` en `/acceso/enlace` | El servidor de correo ha fallado. No queda ningún token creado. |
| `400` en `/acceso/verificar` | Token inventado, caducado o ya usado. |
| `403` en cualquier POST/DELETE | La cabecera `Origin` no está en `CORS_ORIGINS` (protección CSRF, `app/core/origen.py`). |

Código: `app/services/acceso.py`, `app/api/routes/acceso.py`, `app/core/correo.py`,
`app/services/plantillas_correo.py`. Tests del flujo completo: `tests/test_acceso.py`.

## Seguridad

- Tokens de 256 bits (`secrets.token_urlsafe(32)`); en la base de datos solo su SHA-256.
- El enlace caduca a los 15 minutos, sirve una vez y, al entrar, invalida los demás pedidos.
- Cookie `HttpOnly` (JavaScript no puede leerla), `Secure` fuera de local y `SameSite=Lax`.
- Las peticiones que cambian datos se rechazan si vienen de otra web (`Origin`).
- Los correos no se escriben en los logs fuera de local, porque llevan enlaces de acceso.
- Borrar la cuenta elimina sesiones, palas guardadas y avisos; las recomendaciones quedan anónimas.

## Configuración (`backend/.env`)

| Variable | Por defecto | Para qué |
|---|---|---|
| `WEB_URL` | `http://localhost:4321` | Base del enlace del correo. En producción, el dominio de la web. |
| `CORS_ORIGINS` | `["http://localhost:4321"]` | Orígenes que pueden llamar a la API con cookie. Debe incluir `WEB_URL`. |
| `CORREO_MODO` | `consola` | `consola` escribe el correo en el log (solo local); `smtp` lo envía. |
| `CORREO_REMITENTE` | `palaideal <no-responder@palaideal.es>` | Remitente. El dominio debe estar verificado en el proveedor. |
| `SMTP_HOST`, `SMTP_PUERTO`, `SMTP_USUARIO`, `SMTP_PASSWORD` | — / `587` | Datos del proveedor de correo. |
| `SMTP_SEGURIDAD` | `starttls` | `starttls` (587), `ssl` (465) o `ninguno`. |
| `TOKEN_ACCESO_MINUTOS` | `15` | Validez del enlace. |
| `ENLACES_POR_HORA` | `5` | Límite por correo. |
| `SESION_DIAS` | `30` | Duración de la sesión. |
| `COOKIE_SAMESITE` | `lax` | Ver "Despliegue". |
| `COOKIE_DOMINIO` | vacío | Normalmente vacío (la cookie queda en el dominio de la API). |

Proveedor de correo: cualquiera con SMTP (Resend, Brevo, Amazon SES, Postmark…). Está pendiente de
elegir; para cambiarlo solo se tocan las variables `SMTP_*`.

## Despliegue: la web y la API deben compartir dominio

La cookie de sesión la pone la API y la envía el navegador en cada `fetch(..., {credentials: "include"})`
de la web. Con `SameSite=Lax`, el navegador solo la envía si la web y la API son el **mismo sitio**:

| Web | API | ¿Funciona? |
|---|---|---|
| `palaideal.es` | `api.palaideal.es` | ✓ mismo sitio, `SameSite=Lax` |
| `localhost:4321` | `localhost:8000` | ✓ (desarrollo) |
| `palaideal.vercel.app` | `palaideal.onrender.com` | ✗ sitios distintos: la cookie no viaja |

Si de momento se usan los dominios de Vercel y Render, hace falta `COOKIE_SAMESITE=none` (con HTTPS),
pero Safari y otros navegadores bloquean esas cookies de terceros y la sesión fallará para parte de
los usuarios. Solución recomendada: dominio propio, con la API en el subdominio `api.`.

## Desarrollo local

```bash
docker compose up -d
cd backend && uv run alembic upgrade head && uv run python -m uvicorn app.main:app --reload
cd frontend && npm run dev
```

Pide un enlace en http://localhost:4321/acceso/: con `CORREO_MODO=consola`, el correo (con el enlace)
aparece en la terminal de la API.

## Pendiente

- Elegir proveedor de correo y verificar el dominio remitente (SPF/DKIM).
- Volcar a la cuenta las palas guardadas y los avisos que hoy viven en el navegador (`lib/cuenta.ts`),
  cuando el catálogo esté en la base de datos.

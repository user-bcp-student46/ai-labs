# Proposal

## Why

`LegacyDatabase.findByCredentials` arma el SQL concatenando `username` y `password` (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32`). Un valor como `' OR '1'='1` altera la consulta y permite iniciar sesión sin conocer la contraseña: es una vulnerabilidad de severidad alta (H-AUTH-01) que rompe la garantía básica de autenticación del servicio. Se corrige ahora porque el token emitido por `auth` es la identidad que consumen `api` y `web`.

Fuente del trabajo: GitHub Issue #23 "H-AUTH-01 Usar consultas parametrizadas en el login de auth" (https://github.com/user-bcp-student46/ai-labs/issues/23). Componente: `auth/`.

## What Changes

- La búsqueda de credenciales en el login trata `username` y `password` únicamente como datos, nunca como parte de la sentencia SQL.
- Un intento de inyección SQL en `username` o `password` en `POST /auth/login` se rechaza con `401` y sin `token`.
- Se agrega cobertura de pruebas automatizadas del intento de inyección en `AuthResourceTest`, y `mvn test` debe pasar desde `auth/`.
- No hay cambios de contrato: ningún endpoint, campo ni código de estado cambia (no hay **BREAKING**).

## Alcance

- Comportamiento de autenticación de `POST /auth/login` frente a entradas con caracteres de control SQL.
- Pruebas del componente `auth/` que verifiquen el comportamiento anterior.

## Fuera de alcance

- Otros componentes (`api/`, `web/`) y sus documentos de hallazgos.
- Almacenamiento de contraseñas en texto plano (hash/salt), formato o firma del token (`LegacyTokenUtil`), expiración del token.
- Mensajes de error del login (el `401` actual refleja el `username` recibido y el `500` expone `exception`), campo `debug` de la respuesta y manejo de excepciones en `AuthResource`.
- Refactorización por capas de `AuthResource`/`LegacyDatabase`, rate limiting, bloqueo de cuentas.
- Diseño técnico de la implementación (se define en `design.md`) y `tasks.md`.

## Comportamiento que debe preservarse

Baseline: `docs/ENDPOINTS.md` hoy solo documenta el componente `api` y no contiene sección `auth`; por tanto el baseline de `POST /auth/login` es el contrato indicado en el Issue y el comportamiento observable del código actual (`AuthResource`). El Issue no cambia este contrato.

- Credenciales válidas (`student` / `Workshop123!`) responden `200` con `token`, `expiresIn` (3600), `user.username`, `user.displayName`, `user.role` y `debug`.
- `username` o `password` ausentes o en blanco responden `400` con `message` (`Username is required` / `Password is required`); cuerpo ausente responde `400`.
- Credenciales incorrectas responden `401` con `message` y sin `token`.
- Usuarios de prueba existentes (`student`, `trainer`) siguen pudiendo autenticarse.

## Capabilities

### New Capabilities
- `auth-login`: autenticación por usuario y contraseña en `POST /auth/login`, incluyendo el contrato de respuesta preservado y el rechazo de entradas de inyección SQL.

### Modified Capabilities
<!-- Ninguna: openspec/specs/ no contiene specs previas. -->

## Impact

- Código afectado: `auth/` (acceso a datos del login y `AuthResourceTest`); este change solo materializa la propuesta y las specs, sin modificar código funcional.
- APIs: sin cambios de contrato en `POST /auth/login`; `api` y `web` no se ven afectados.
- Dependencias: ninguna nueva.
- Verificación: `mvn test` desde `auth/` (también `python tools/lab.py test auth` desde la raíz); meta de cobertura del código modificado >= 85%.

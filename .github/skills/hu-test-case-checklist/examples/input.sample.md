## ID / Título de la HU
HU-AUTH-07 - Login con bloqueo tras intentos fallidos

## Descripción funcional
Como usuario del sistema,
quiero que mi cuenta se bloquee temporalmente tras varios intentos
de login fallidos,
para reducir el riesgo de ataques de fuerza bruta.

## Criterios de aceptación
- Tras 5 intentos fallidos consecutivos, la cuenta queda bloqueada 15 minutos.
- Durante el bloqueo, `POST /auth/login` responde 423 aunque la contraseña
  sea correcta.
- Un login exitoso antes de llegar a 5 intentos reinicia el contador.
- El bloqueo y su expiración quedan registrados en logs, sin incluir la
  contraseña ni el token.

## DoR (Definition of Ready)
- Endpoint `POST /auth/login` y su contrato actual están documentados.
- Está definido el almacenamiento de intentos fallidos (en memoria o tabla).
- Está definido el valor de "intentos máximos" y "tiempo de bloqueo" como
  configuración, no como valor fijo en código.

## DoD (Definition of Done)
- Pruebas unitarias de contador de intentos, bloqueo y expiración.
- Cobertura del código modificado >= 85%.
- No se introducen secretos reales en configuración ni pruebas.
- Documentación del endpoint actualizada con el código 423.

## Contexto técnico (opcional)
Servicio `auth` (Java), endpoint `POST /auth/login`, persistencia actual en
`LegacyDatabase`.

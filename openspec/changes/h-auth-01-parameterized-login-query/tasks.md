# Tasks

Alcance: `auth/` únicamente (ver `proposal.md`). Ejecutar pruebas con `python tools/lab.py test auth` desde la raíz, o `mvn test` desde `auth/`.

## 1. Pruebas de caracterización (antes del cambio funcional)

- [x] 1.1 En `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`, agregar el caso de inyección SQL en `username` (`' OR '1'='1` + password cualquiera) contra `POST /auth/login`, verificando `401` y cuerpo sin `token`. **Hallazgo durante la ejecución (ver nota bajo 1.9): este payload concreto, sin comentario SQL final, ya responde `401` hoy — no reproduce el bypass descrito en `design.md`/`spec.md`.**
- [x] 1.2 Agregar el caso de inyección SQL en `password` (`username` = `student`, `password` = `' OR '1'='1`), verificando `401` y cuerpo sin `token`.
- [x] 1.3 Agregar el caso de comentario SQL en `username` (`student'--` + password cualquiera), verificando `401` y cuerpo sin `token`.
- [x] 1.4 Agregar el caso de comilla simple benigna (`username` = `o'brien`), verificando `401` (y explícitamente no `500`).
- [x] 1.5 Agregar el caso de login válido `trainer` / `Trainer123!`, verificando `200`, `user.username` = `trainer` y `token` no nulo (el caso `student` ya existe).
- [x] 1.6 Agregar el caso de contraseña incorrecta para `student`, verificando `401` y cuerpo sin `token`.
- [x] 1.7 Agregar el caso de usuario inexistente, verificando `401` y cuerpo sin `token`.
- [x] 1.8 Agregar los casos de `username` ausente/en blanco y `password` ausente/en blanco, verificando `400` con los mensajes `Username is required` / `Password is required`.
- [x] 1.9 Ejecutar `mvn test` desde `auth/` (código actual, sin tocar `LegacyDatabase`) y registrar qué casos fallan en rojo.
  **Resultado real (comando `mvn test "-Dquarkus.http.test-port=0"` desde `auth/`; el puerto 8081 por defecto estaba ocupado por el proxy MCP local, se usó un puerto libre sin modificar `application.properties`): `Tests run: 10, Failures: 2, Errors: 0`.**
  - Fallan en rojo (como se esperaba, el login vulnerable los acepta hoy): `rejectsSqlCommentInUsernameWithoutToken` (esperado 401, obtuvo 200) y `rejectsSqlInjectionInPasswordWithoutToken` (esperado 401, obtuvo 200).
  - **No falla, contrario a lo esperado**: `rejectsSqlInjectionInUsernameWithoutToken` (payload `' OR '1'='1` en `username`, sin comentario SQL) obtuvo `401` hoy, no `200`. Causa probable: la precedencia estándar de SQL (`AND` se evalúa antes que `OR`) hace que la cláusula generada sea `username='' OR ('1'='1' AND password='...')`, que para cada fila real exige además que `password` coincida; sin un comentario SQL (`--`) que descarte el resto de la cláusula, este payload concreto no vulnera el login actual.
  - **Revisado por el usuario (no bloqueante)**: el escenario "Inyección SQL en el usuario" de `specs/auth-login/spec.md` y el ejemplo de `design.md` usan este mismo payload (`' OR '1'='1` sin comentario) como evidencia del bypass; esa evidencia concreta no se reprodujo. La vulnerabilidad H-AUTH-01 sigue confirmada por los otros dos vectores (`password` y comentario SQL en `username`), y el usuario autorizó continuar con la implementación de la sección 2 sin bloquear por esta inexactitud documental; la corrección del ejemplo en spec/design queda como pendiente separado, fuera de este cambio.

## 2. Cambio mínimo de implementación

- [x] 2.1 En `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`, reemplazar el `Statement`/SQL concatenado de `findByCredentials` por un `PreparedStatement` con parámetros posicionales (`?`) y `setString(1, username)` / `setString(2, password)`, sin cambiar la firma del método ni el resto de la clase.
- [x] 2.2 Confirmar que `initialize()` y el resto de `LegacyDatabase.java` quedan sin cambios, y que no se modifican `AuthResource.java`, `LegacyTokenUtil.java`, `UserRecord.java` ni `LoginRequest.java`. **Confirmado**: único archivo modificado en este paso es `LegacyDatabase.java` (import de `PreparedStatement` y cuerpo de `findByCredentials`); `initialize()` quedó idéntico.

## 3. Verificación

- [x] 3.1 Ejecutar `mvn test` desde `auth/` (o `python tools/lab.py test auth` desde la raíz) y confirmar que todos los casos de la sección 1 (existentes y nuevos) pasan en verde, incluidos los de inyección. **Resultado real** (`mvn test "-Dquarkus.http.test-port=0"` desde `auth/`): `Tests run: 10, Failures: 0, Errors: 0` — `BUILD SUCCESS`. Las dos pruebas que fallaban en rojo (`rejectsSqlCommentInUsernameWithoutToken`, `rejectsSqlInjectionInPasswordWithoutToken`) ahora pasan.
- [x] 3.2 Confirmar que la cobertura del código modificado en `LegacyDatabase.java` alcanza ≥ 85% (reporte de cobertura del build de `auth/`). **Resultado real** (`mvn verify "-Dquarkus.http.test-port=0"`, reporte en `auth/target/site/jacoco/com.bcp.workshop.auth/LegacyDatabase.java.html`): las líneas del método modificado `findByCredentials` (33-46) están 100% cubiertas en instrucciones, y su única rama real (`if (result.next())`) está "All 2 branches covered" (100%). La clase completa reporta 94% instrucciones / 62% ramas porque arrastra las ramas de manejo de excepción de `initialize()` y del propio `catch` de `findByCredentials`, que ya existían sin cobertura antes de este cambio y no fueron tocadas (no son código modificado en este paso).

## 4. Evidencia

- [x] 4.1 Registrar en el documento general de hallazgos la sección `auth`, `H-AUTH-01`, con el resultado de `mvn test` (rojo antes del fix, verde después) y la cobertura obtenida, sin tocar otras secciones del documento. Registrado en `HALLAZGOS.md`, nueva sección `## auth`.

## Fuera de alcance (no incluir en estas tareas)

- Cambios en `api/` o `web/`.
- Hash/salt de contraseñas, cambios en `LegacyTokenUtil`, formato o expiración del token.
- Cambios en mensajes de error, campo `debug`, manejo de excepciones de `AuthResource` o su refactorización por capas.
- Rate limiting, bloqueo de cuentas, políticas de contraseña.

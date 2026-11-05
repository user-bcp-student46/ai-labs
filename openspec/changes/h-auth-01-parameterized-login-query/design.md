# Design

## Contexto técnico

`POST /auth/login` (`AuthResource.login`) valida presencia de `username`/`password` y delega la búsqueda de credenciales a `LegacyDatabase.findByCredentials(username, password)` (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32`). Ese método arma el SQL por concatenación de strings:

```java
String sql = "SELECT id, username, display_name, role FROM legacy_users WHERE username='" + username + "' AND password='" + password + "'";
```

y lo ejecuta con `Statement.executeQuery(sql)`. Un `username` como `' OR '1'='1` convierte la cláusula `WHERE` en una tautología y devuelve el primer usuario de la tabla sin conocer la contraseña (H-AUTH-01).

El método captura cualquier `Exception`, hace `printStackTrace()` y retorna `null`; `AuthResource` traduce `null` en `401`. Esto explica por qué una entrada como `o'brien` (comilla simple suelta, sin intención maliciosa) ya produce hoy `401` y no `500`: el SQL concatenado queda mal formado, `Statement` lanza `SQLException`, se captura dentro de `findByCredentials`, y se devuelve `null`. La spec pide preservar exactamente ese comportamiento observable.

El motor es SQLite embebido (`jdbc:sqlite:./data/workshop.db`), inicializado en `@PostConstruct` con dos usuarios semilla (`student`, `trainer`). No hay otros componentes (`api`, `web`) que llamen a `LegacyDatabase` directamente; solo consumen el token JWT emitido después del login.

## Goals / Non-goals

**Goals**
- Que `username` y `password` se liguen a la consulta SQL como parámetros, nunca como texto interpolado, cerrando la inyección SQL en `POST /auth/login`.
- Preservar el contrato HTTP actual de `POST /auth/login` en todos los casos descritos en `specs/auth-login/spec.md` (200 con credenciales válidas, 401 con inválidas o ataques de inyección, 400 con campos faltantes).
- Agregar una prueba de caracterización que falle con el código actual (vulnerable) y pase con la corrección, evidenciando el cierre del hallazgo.

**Non-goals**
- No se cambia el almacenamiento de contraseñas (texto plano hoy); hashing/salting queda fuera de alcance.
- No se cambia `LegacyTokenUtil`, el formato del JWT, su firma ni `expiresIn`.
- No se cambian los mensajes de error, el campo `debug`, ni el manejo de excepciones de `AuthResource` (incluyendo el `500` que expone `exception`).
- No se refactoriza `AuthResource` en capas (API/servicio/repositorio) como tarea de este cambio; el método ya tiene anidamiento que **no** se toca aquí para mantener el diff mínimo y auditable. Si se decide abordarlo, será un cambio OpenSpec separado.
- No se agrega rate limiting, bloqueo de cuentas, ni políticas de contraseña.

## Contratos protegidos

- `POST /auth/login`: firma de request (`username`, `password`, `client` opcional e ignorado) y de response (`token`, `expiresIn`, `user.username`, `user.displayName`, `user.role`, `debug` en `200`; `message` en `400`/`401`; `message` + `exception` en `500`) se mantienen byte a byte.
- Comportamiento de `username`/`password` ausentes o en blanco → `400` con el mensaje exacto actual.
- Comportamiento de credenciales inválidas (inexistentes, incorrectas o con intento de inyección) → `401` sin `token`.
- Usuarios semilla `student` y `trainer` siguen autenticando con sus contraseñas actuales.
- Esquema de `legacy_users` y datos semilla en `LegacyDatabase.initialize()` no cambian.

## Componentes afectados

- `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`: único punto donde cambia la construcción del SQL (de concatenación a `PreparedStatement` parametrizado).
- `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`: se agregan casos de prueba (inyección en `username`, inyección en `password`, comentario SQL, comilla simple benigna) antes/junto con la corrección.
- Sin cambios en `AuthResource.java`, `LegacyTokenUtil.java`, `UserRecord.java`, `LoginRequest.java` ni en `api/` o `web/`.

## Decisiones técnicas y alternativas consideradas

### Decisión: usar `PreparedStatement` con parámetros posicionales (`?`)

**Contexto**: el hallazgo H-AUTH-01 exige que `username`/`password` no puedan alterar la estructura de la consulta.

**Opciones consideradas**:
1. **`PreparedStatement` con `?` y `setString(...)`** — cambio mínimo, usa JDBC estándar ya presente (`java.sql.*`), no agrega dependencias.
2. **Escapar manualmente comillas en el SQL concatenado** — rechazada: es una mitigación incompleta y frágil (no cubre todos los vectores, por ejemplo bytes nulos o codificaciones), y el Issue pide explícitamente consultas parametrizadas.
3. **Introducir un ORM o capa de repositorio nueva (ej. jOOQ, Hibernate)** — rechazada: excede el alcance aprobado ("fuera de alcance: refactorización por capas"), agrega dependencias nuevas no justificadas y aumenta el riesgo de romper el contrato observable.
4. **Procedimiento almacenado parametrizado en SQLite** — rechazada: SQLite no soporta stored procedures de forma nativa; innecesario para este alcance.

**Decisión**: opción 1. Es el cambio mínimo que cumple la spec, no introduce dependencias y mantiene intacta la superficie pública (`AuthResource`, `UserRecord`, el resto de `LegacyDatabase`).

**Consecuencias**:
- El manejo de errores se mantiene igual: `PreparedStatement.executeQuery()` también puede lanzar `SQLException` (por ejemplo si el archivo de base de datos no está disponible); se sigue capturando en el mismo `catch (Exception error)` y retornando `null`, preservando el mapeo a `401` para el caso "comilla simple benigna" solo si corresponde — en este caso, con parámetros bind, `o'brien` ya **no** causará error de sintaxis SQL (el driver trata el valor como dato). El resultado seguirá siendo `401` porque no existe un usuario llamado `o'brien`, no porque la consulta falle. El escenario de la spec (`401` y no `500`) se preserva, aunque la causa interna cambie de "excepción SQL atrapada" a "consulta sin resultados"; esto es compatible con el comportamiento observable exigido por la spec, que no prescribe la causa interna.

## Estrategia incremental

1. **Paso 1 — Pruebas de caracterización (rojas sobre el código actual vulnerable)**: agregar a `AuthResourceTest` los casos de inyección (`' OR '1'='1` en usuario, en password, `student'--`, y `o'brien`) verificando `401` sin `token` y sin `500`. Ejecutar `mvn test` y confirmar qué casos fallan hoy (los de inyección deberían fallar porque el login actual los acepta con `200`).
2. **Paso 2 — Cambio mínimo en `LegacyDatabase.findByCredentials`**: reemplazar la concatenación por `PreparedStatement` con `?` y `setString(1, username)` / `setString(2, password)`. No tocar `AuthResource` ni el resto de la clase.
3. **Paso 3 — Verificación**: ejecutar `mvn test` desde `auth/` (o `python tools/lab.py test auth` desde la raíz) y confirmar que todos los casos (existentes y nuevos) pasan en verde, y que la cobertura del código modificado alcanza ≥ 85%.
4. **Paso 4 — Evidencia**: registrar en el documento general de hallazgos (sección `auth`, ID `H-AUTH-01`) el resultado de las pruebas, sin tocar otras secciones del documento.

Cada paso es revisable de forma independiente (test-first, luego fix, luego verificación), y el paso 2 es reversible con un único revert de commit si algo falla.

## Pruebas de caracterización necesarias antes de modificar comportamiento crítico

Antes de tocar `LegacyDatabase.findByCredentials`, `AuthResourceTest` debe cubrir (ver `specs/auth-login/spec.md`):

- Login válido `student` / `Workshop123!` → `200`, `token` no nulo, `expiresIn=3600`.
- Login válido `trainer` / `Trainer123!` → `200`, `token` no nulo.
- Contraseña incorrecta para `student` → `401` sin `token`.
- Usuario inexistente → `401` sin `token`.
- `username` ausente/en blanco → `400`, `message="Username is required"`.
- `password` ausente/en blanco → `400`, `message="Password is required"`.
- Inyección en `username` (`' OR '1'='1`) → `401` sin `token`.
- Inyección en `password` (`' OR '1'='1`) → `401` sin `token`.
- Comentario SQL en `username` (`student'--`) → `401` sin `token`.
- Comilla simple benigna (`o'brien`) → `401` (no `500`).

Estas pruebas se agregan **antes** de modificar `LegacyDatabase`, de modo que documenten el comportamiento vulnerable actual (fallan en rojo para los casos de inyección) y sirvan de red de seguridad para validar que el fix no rompe los casos ya correctos.

## Riesgos / trade-offs

- **Riesgo bajo**: cambiar `Statement` por `PreparedStatement` es un cambio acotado a un método, con la misma firma pública y el mismo contrato de retorno (`UserRecord` o `null`).
- **Trade-off aceptado**: el escenario "comilla simple benigna" pasa de "401 por excepción SQL atrapada" a "401 por consulta sin resultados". El efecto observable (status code, ausencia de `token`) es idéntico, por lo que no hay impacto en los consumidores (`api`, `web`) ni en la spec.
- **Riesgo de regresión en cobertura**: si las pruebas nuevas no se escriben antes del fix, se pierde la evidencia de que el hallazgo estaba presente; mitigado por la estrategia incremental (paso 1 antes que paso 2).
- **Fuera del control de este cambio**: la contraseña sigue en texto plano en `legacy_users`; si alguien obtiene acceso directo a la base de datos, la inyección SQL ya no es el vector de riesgo, pero el almacenamiento en claro sigue siendo una debilidad conocida y explícitamente fuera de alcance (ver `proposal.md`).

## Rollback

Si `mvn test` falla tras el paso 2, o si una verificación manual detecta una diferencia de contrato no prevista:

- El cambio queda contenido en un commit único y pequeño sobre `LegacyDatabase.java` (más el commit de pruebas, separado). Revertir el commit del fix restaura la versión concatenada sin afectar pruebas, `AuthResource` ni otros componentes.
- No hay migraciones de esquema, datos ni cambios de configuración (`application.properties`) que revertir: el esquema de `legacy_users` y los datos semilla no cambian.
- No hay impacto en `api/` ni `web/` que requiera coordinación de rollback entre componentes, porque no hay cambio de contrato.

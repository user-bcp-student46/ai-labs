# Plan de corrección

## Contexto auth

### Aprobación humana
- Revisor/a: Santiago Santos
- Fecha: 2026-10-26
- Decisión: Aprobado para implementación
- IDs aprobados: H-AUTH-01,H-AUTH-02,H-AUTH-03,H-AUTH-04,H-AUTH-05,H-AUTH-06,H-AUTH-07 

### Alcance y contrato

Se seleccionan H-AUTH-01 a H-AUTH-07 porque todos siguen en estado `Pendiente` en `HALLAZGOS.md`; se incluyen por severidad y para conservar el plan existente. Cada item tiene un alcance independiente. La aprobación humana registrada autoriza los siete IDs. H-AUTH-01 está implementado parcialmente; los otros items siguen siendo propuestas y ninguno se considera resuelto por la aprobación.

No existe `docs/ENDPOINTS.md`. Se toma como base el contrato observado en `HALLAZGOS.md`: endpoint `POST /auth/login`, códigos observados `400`, `401`, `200` y `500`, y respuesta satisfactoria con `token`, `expiresIn` y `user`. Antes de implementar se deben acordar explícitamente los cambios incompatibles con lo observado: formato interno del token, restricción de orígenes CORS y contenido de la respuesta `500`. No se inspeccionarán consumidores fuera de `auth/`; la compatibilidad del token requiere coordinación con sus responsables.

### Secuencia común de caracterización

Antes de cambiar persistencia, token o capas, caracterizar login válido, credenciales inválidas, campos requeridos, códigos HTTP y campos de la respuesta exitosa en `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`. Mantener esos casos como regresión y añadir por separado las aserciones de seguridad descritas en cada hallazgo. Para H-AUTH-01, la prueba del username con comilla se ejecutó antes y después del cambio; la ejecución de la clase completa y la cobertura siguen pendientes según el registro inferior.

## Item: H-AUTH-01 — Concatenación de credenciales en SQL

- **Hallazgo y problema:** `LegacyDatabase` concatena `username` y `password` en la consulta. Caracteres de entrada pueden cambiar la consulta o provocar errores.
- **Cambio propuesto:** sustituir `Statement` por `PreparedStatement`, enlazar ambos valores por posición y cerrar los recursos con el patrón existente. Mantener la búsqueda y el resultado funcionales.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`; `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`.
- **Caracterización previa:** conservar el login válido y el `401` para credenciales incorrectas. Añadir una prueba de regresión con una cuenta ficticia local cuyo username contenga una comilla; insertarla en el fixture con parámetros y comprobar que credenciales correctas autentican, sin alterar la consulta. Esta última aserción debe fallar antes de la corrección y pasar después.

- **Estado de ejecución:** la consulta parametrizada y la prueba con comilla ya se añadieron bajo la aprobación registrada. La prueba falló antes con `401` por error SQL y pasó después (1 caso). La suite completa y cobertura del 85% siguen pendientes; el estado en `HALLAZGOS.md` continúa `Pendiente`.

## Item: H-AUTH-02 — Contraseñas en texto plano

- **Hallazgo y problema:** las contraseñas se insertan y comparan como texto legible; una copia de la base revela credenciales reutilizables.
- **Cambio propuesto:** usar un hash lento con salt (BCrypt, según `docs/GOOD_PRACTICES.md`) en la creación y verificación. Definir una migración idempotente para la base SQLite existente que convierta las cuentas actuales y retire el almacenamiento en claro; no registrar contraseñas ni hashes. Justificar cualquier dependencia: comprobar primero si el proveedor adecuado ya está disponible y, si no, agregar solo una implementación mantenida y compatible en `auth/pom.xml`.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`; una clase de hashing en `auth/src/main/java/com/bcp/workshop/auth/`; `auth/pom.xml` solo si se justifica una dependencia; pruebas en `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización previa:** conservar las pruebas HTTP de login válido e inválido. Antes de migrar, registrar en una prueba local aislada el esquema/semilla actual y el resultado del login; como regresión posterior, comprobar que el login sigue funcionando y que el valor persistido ya no coincide con la contraseña y se verifica mediante BCrypt. La prueba de almacenamiento seguro es una aserción nueva, no una descripción del comportamiento inseguro actual.

- **Estado de ejecución y revisión:** el baseline `characterizesCurrentPlaintextPasswordStorage` pasó antes del cambio y confirmó el valor sembrado en texto plano. Se agregó Elytron BCrypt, migración transaccional y pruebas. La primera ejecución de `LegacyDatabaseTest` falló porque el `SELECT` omitía `role`; se corrigió. Un `mvn verify` posterior falló porque el test sin `@QuarkusTest` no cargaba el driver SQLite; se agregó carga explícita. La repetición focalizada pasó (1/1), `AuthResourceTest` pasó (4/4) y `mvn verify` pasó (5/5). JaCoCo: `LegacyDatabase` 72/79 líneas (91,1%); `PasswordHasher` 2/2 (100%). La revisión detectó que `initialize()` absorbe errores de migración y puede dejar el login inoperativo; H-AUTH-02 volvió a `Pendiente` en `HALLAZGOS.md` hasta manejar ese fallo y probarlo.

## Item: H-AUTH-03 — Token Base64 con secreto embebido

- **Hallazgo y problema:** el token codifica datos y un secreto fijo con Base64, que no firma ni cifra el contenido.
- **Cambio propuesto:** reemplazar la codificación casera por un token firmado con expiración y claims explícitos, usando una biblioteca estándar compatible con Quarkus. Conservar el campo JSON `token` y `expiresIn`; mantener 3600 segundos mediante una constante nombrada o configuración. El secreto de firma debe proceder de configuración externa y usar valores ficticios aislados en pruebas. Justificar y fijar cualquier dependencia nueva en `auth/pom.xml`; no implementar criptografía propia.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java` o su reemplazo en `auth/src/main/java/com/bcp/workshop/auth/`; `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`; `auth/pom.xml` si la biblioteca estándar no está disponible; pruebas en `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización previa:** capturar el `200`, los campos actuales de respuesta, `expiresIn` y la presencia de un token no vacío. Añadir después pruebas de firma, claims y expiración. Antes de cambiar el formato opaco del token, obtener acuerdo sobre compatibilidad con consumidores; esa compatibilidad no puede verificarse dentro del alcance actual.

## Item: H-AUTH-04 — Secreto y CORS fijados

- **Hallazgo y problema:** el secreto está en Java y CORS admite orígenes mediante una expresión amplia; se dificulta proteger el secreto y limitar el acceso por entorno.
- **Cambio propuesto:** cargar el secreto desde variable de entorno o configuración externa de Quarkus, sin valor secreto real en archivos versionados. Configurar una lista explícita de orígenes permitidos por entorno. Mantener los métodos y headers necesarios, sujetos a revisión de los consumidores.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java`; `auth/src/main/resources/application.properties`; configuración de prueba dentro de `auth/src/test/resources/` solo si hace falta; pruebas en `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización previa:** probar el login con la configuración de prueba y registrar el comportamiento CORS actual para un origen local ficticio. La regresión debe aceptar el origen aprobado y rechazar uno no configurado. El origen autorizado no se debe adivinar: acordarlo antes de restringir la política.

## Item: H-AUTH-05 — Detalles de excepción en respuesta

- **Hallazgo y problema:** el `500` incluye el mensaje y la clase de la excepción, lo que puede divulgar detalles internos.
- **Cambio propuesto:** devolver un mensaje genérico y estable, conservar el código `500` y enviar los detalles solo al log del servidor con logging controlado. No incluir la excepción ni credenciales en logs o respuestas.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`; pruebas en `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización previa:** probar el caso de error con una dependencia de base de datos simulada que arroje una excepción controlada y registrar el `500` y el cuerpo actual. La respuesta genérica quitaría campos/detalles observados; confirmar si esos detalles se consideran contrato antes de implementarlo. Después, comprobar que se mantiene el `500` y no se exponen mensaje ni clase.

## Item: H-AUTH-06 — Responsabilidades mezcladas en Resource

- **Hallazgo y problema:** `AuthResource.login` valida, consulta persistencia, genera token y arma la respuesta con condicionales anidados; un cambio de una responsabilidad puede afectar las demás.
- **Cambio propuesto:** dejar en el Resource la adaptación HTTP, mover el caso de uso a un servicio y conservar el acceso SQLite en el repositorio. Extraer hashing/token a sus componentes de seguridad cuando corresponda. Usar retornos tempranos, nombres de propósito y constantes nombradas; mapear a un DTO de respuesta en vez de duplicar construcción de mapas. Mantener métodos pequeños y sin duplicación.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`; nuevas clases de servicio/DTO dentro de `auth/src/main/java/com/bcp/workshop/auth/`; `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización previa:** completar primero los casos HTTP válidos, inválidos y de campos requeridos definidos en la secuencia común; comprobar que la forma de éxito y los códigos observados no cambian al mover la lógica. No combinar este refactor con cambios de contrato no acordados.

## Item: H-AUTH-07 — Evaluación SCA de versiones

- **Hallazgo y problema:** `pom.xml` fija Quarkus 3.27.4 y Commons Text 1.9. La presencia de estas versiones está comprobada, pero no se ha confirmado un advisory aplicable.
- **Cambio propuesto:** consultar Dependency Review, CodeQL o el mecanismo SCA aprobado y revisar advisories y compatibilidad. Actualizar o retirar únicamente con evidencia; no silenciar alertas ni modificar umbrales. Si no hay hallazgo aplicable, registrar la evidencia y cerrar este candidato sin cambio de versión.
- **Archivos a tocar:** `auth/pom.xml` solo si la evidencia justifica actualización o eliminación; `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` para regresión si hay cambio funcional.
- **Caracterización previa:** conservar el login válido existente y añadir/ejecutar los casos de credenciales inválidas antes de actualizar dependencias. Repetir la suite después; el resultado SCA debe quedar registrado por el proceso de revisión correspondiente, no inferido de una prueba funcional.

## Validación y dependencias externas

Después de cada cambio aprobado, ejecutar `mvn test` desde `auth/`; ejecutar `mvn verify` para generar el informe JaCoCo y revisar la cobertura del código modificado. Para H-AUTH-01, `mvn verify` pasó y el método modificado tiene 12/13 líneas cubiertas (92,3%). Mantener visibles fallos y alertas de seguridad. Antes de implementar token, CORS o respuesta de error, registrar la decisión humana sobre compatibilidad; no se asume que la aprobación de IDs resuelva esas decisiones de contrato.

## Ejecuciones locales

| componente | IDs | comando (cwd `auth/`) | resultado |
|---|---|---|---|
| auth | H-AUTH-01 | `mvn -Dtest=AuthResourceTest#logsInWithUsernameContainingQuote test` | Primer intento: error `SQLITE_CANTOPEN`; el fixture intentó abrir SQLite antes de inicializar la base. No evaluó el comportamiento SQL. |
| auth | H-AUTH-01 | `mvn -Dtest=AuthResourceTest#logsInWithUsernameContainingQuote test` | Tras inicializar la base por el endpoint: falló como se esperaba antes del cambio; SQLite reportó error de sintaxis cerca de `quote` y el endpoint devolvió `401` en lugar de `200`. |
| auth | H-AUTH-01 | `mvn -Dtest=AuthResourceTest#logsInWithUsernameContainingQuote test` | Primer intento posterior al cambio: compilación fallida por falta del import de `PreparedStatement`; se corrigió el import. |
| auth | H-AUTH-01 | `mvn -Dtest=AuthResourceTest#logsInWithUsernameContainingQuote test` | Después del import: éxito, 1 prueba ejecutada, 0 fallos, 0 errores. El login de inicialización también comprobó `200`. |
| auth | H-AUTH-01 | `mvn -Dtest=AuthResourceTest test` | Éxito: 3 pruebas ejecutadas, 0 fallos, 0 errores; login válido, credenciales inválidas y username con comilla. |
| auth | H-AUTH-01 | `mvn verify` | Éxito: 3 pruebas ejecutadas, 0 fallos, JaCoCo generado. `findByCredentials`: 12/13 líneas (92,3%); 85% superado para el método modificado. |
| auth | H-AUTH-02 | `mvn -Dtest=AuthResourceTest#characterizesCurrentPlaintextPasswordStorage test` | Éxito antes del cambio, con `AUTH_DB_URL` apuntando a una SQLite ficticia nueva; la prueba confirmó el valor almacenado en claro. |
| auth | H-AUTH-02 | `mvn -Dtest=LegacyDatabaseTest test` | Falló: la aserción de migración intentó leer `role` sin seleccionarlo. Se corrigió el `SELECT`; el reintento fue omitido, así que el resultado posterior está pendiente. |
| auth | H-AUTH-02 | `mvn -Dtest=LegacyDatabaseTest test` | Tras corregir el `SELECT`, falló en el driver SQLite por ser un test unitario sin `@QuarkusTest`; se corrigió cargando el driver explícitamente. |
| auth | H-AUTH-02 | `mvn -Dtest=LegacyDatabaseTest test` | Éxito: 1 prueba, 0 fallos, 0 errores; migración de columna antigua, hash válido y segunda ejecución idempotente. |
| auth | H-AUTH-02 | `mvn -Dtest=AuthResourceTest test` | Éxito: 4 pruebas, 0 fallos, 0 errores; login válido, inválido, almacenamiento BCrypt y username con comilla. |
| auth | H-AUTH-02 | `mvn verify` | Éxito: 5 pruebas, 0 fallos, 0 errores; JaCoCo generado. Cobertura de clases modificadas: `LegacyDatabase` 72/79 (91,1%), `PasswordHasher` 2/2 (100%). |

En una ejecución anterior se omitió `mvn -Dtest=AuthResourceTest test`; posteriormente se ejecutó y pasó según la tabla. H-AUTH-01 está `Resuelto`; H-AUTH-02 volvió a `Pendiente` por el riesgo de error de migración absorbido. CodeQL y Dependency Review remotos no ejecutados.
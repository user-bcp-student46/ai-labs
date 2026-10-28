# Pruebas de contratos HTTP

## auth

Contratos cubiertos según [docs/ENDPOINTS.md](ENDPOINTS.md). Las pruebas viven
en [AuthResourceTest.java](../auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java)
y [LegacyDatabaseTest.java](../auth/src/test/java/com/bcp/workshop/auth/LegacyDatabaseTest.java).
Los casos de error se prueban contra los comportamientos documentados, sin
alterar el endpoint para hacer pasar las pruebas.

### Matriz

| endpoint | caso | tipo | resultado esperado |
|---|---|---|---|
| `GET /q/health` | Servicio disponible | Camino feliz | `200`, `status` igual a `UP`. |
| `GET /q/health` | Sin health checks registrados | Borde | `200`, `checks` vacío. |
| `GET /q/health` | Error | No aplica | El contrato actual no documenta respuesta HTTP de error para health; no se inventa un test de error. |
| `POST /auth/login` | Credenciales válidas del usuario de workshop | Camino feliz; H-AUTH-02, H-AUTH-03 | `200`; respuesta contiene username, displayName, role, token, expiresIn y debug. El test no valida criptografía ni expiración del token. |
| `POST /auth/login` | Username con comilla | Borde; H-AUTH-01 | `200` para el usuario ficticio insertado con SQL parametrizado. |
| `POST /auth/login` | Username vacío o compuesto solo por espacios | Borde | `400`, `{"message":"Username is required"}`. |
| `POST /auth/login` | Password vacía o compuesta solo por espacios | Borde | `400`, `{"message":"Password is required"}`. |
| `POST /auth/login` | Cuerpo JSON `null` | Error | `400`, `{"message":"Request is null"}`. |
| `POST /auth/login` | Username ausente | Error | `400`, `{"message":"Username is required"}`. |
| `POST /auth/login` | Password ausente | Error | `400`, `{"message":"Password is required"}`. |
| `POST /auth/login` | Contraseña incorrecta | Error; H-AUTH-05 | `401`, `{"message":"Invalid user student or password"}`. |
| `POST /auth/login` | Excepción con mensaje | Error; H-AUTH-05 | `500`; entidad contiene el mensaje y el nombre de la clase. Probado invocando el recurso directamente con una base de prueba que lanza la excepción. |
| `POST /auth/login` | Excepción sin mensaje | Error; H-AUTH-05 | `500`; mensaje `Unknown error` y nombre de la clase. Probado invocando el recurso directamente. |

### Código de pruebas

El siguiente código corresponde a los casos de endpoint en
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`. Se omiten los
tests de persistencia incluidos en la misma clase. El test con comilla usa los
helpers de fixture `initializeDatabase`, `insertQuotedUser` y
`deleteQuotedUser`, conservados en el archivo fuente.

```java
@Test
void logsInWithWorkshopUser() {
    given()
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(200)
            .body("user.username", is("student"))
            .body("user.displayName", is("Workshop Student"))
            .body("user.role", is("STUDENT"))
            .body("token", notNullValue())
            .body("expiresIn", is(3600))
            .body("debug", is("authenticated-with-legacy-flow"));
}

@Test
void healthEndpointReportsUp() {
    given()
            .when().get("/q/health")
            .then()
            .statusCode(200)
            .body("status", is("UP"));
}

@Test
void healthEndpointReportsNoChecksWhenNoneAreRegistered() {
    given()
            .when().get("/q/health")
            .then()
            .statusCode(200)
            .body("checks.size()", is(0));
}

@Test
void rejectsNullLoginRequest() {
    given()
            .contentType("application/json")
            .body("null")
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Request is null"));
}

@Test
void rejectsMissingUsername() {
    given()
            .contentType("application/json")
            .body(Map.of("password", "Workshop123!"))
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Username is required"));
}

@Test
void rejectsBlankUsername() {
    given()
            .contentType("application/json")
            .body(Map.of("username", "  ", "password", "Workshop123!"))
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Username is required"));
}

@Test
void rejectsMissingPassword() {
    given()
            .contentType("application/json")
            .body(Map.of("username", "student"))
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Password is required"));
}

@Test
void rejectsBlankPassword() {
    given()
            .contentType("application/json")
            .body(Map.of("username", "student", "password", "  "))
            .when().post("/auth/login")
            .then()
            .statusCode(400)
            .body("message", is("Password is required"));
}

@Test
void rejectsInvalidCredentials() {
    given()
            .contentType("application/json")
            .body("{\"username\":\"student\",\"password\":\"IncorrectLocalPassword\"}")
            .when().post("/auth/login")
            .then()
            .statusCode(401)
            .body("message", is("Invalid user student or password"));
}

@Test
void reportsUnexpectedExceptionFromDatabase() {
    AuthResource resource = new AuthResource();
    resource.database = new LegacyDatabase() {
        @Override
        public UserRecord findByCredentials(String username, String password) {
            throw new IllegalStateException("database unavailable");
        }
    };
    LoginRequest request = new LoginRequest();
    request.username = "student";
    request.password = "Workshop123!";

    Response response = resource.login(request);

    assertEquals(500, response.getStatus());
    assertEquals(Map.of(
            "message", "database unavailable",
            "exception", IllegalStateException.class.getName()), response.getEntity());
}

@Test
void usesFallbackMessageWhenExceptionHasNoMessage() {
    AuthResource resource = new AuthResource();
    resource.database = new LegacyDatabase() {
        @Override
        public UserRecord findByCredentials(String username, String password) {
            throw new IllegalStateException();
        }
    };
    LoginRequest request = new LoginRequest();
    request.username = "student";
    request.password = "Workshop123!";

    Response response = resource.login(request);

    assertEquals(500, response.getStatus());
    assertEquals(Map.of(
            "message", "Unknown error",
            "exception", IllegalStateException.class.getName()), response.getEntity());
}

@Test
void logsInWithUsernameContainingQuote() throws SQLException {
    initializeDatabase();
    deleteQuotedUser();
    try {
        insertQuotedUser();

        given()
                .contentType("application/json")
                .body(Map.of("username", TEST_USERNAME, "password", TEST_PASSWORD))
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is(TEST_USERNAME))
                .body("token", notNullValue());
    } finally {
        deleteQuotedUser();
    }
}
```

Referencias de implementación y pruebas: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:23`;
`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:128`;
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:28` (login exitoso),
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:44` (health UP),
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:53` (checks vacíos),
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:62` (400 por cuerpo nulo),
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:117` (401),
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:128` y
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:149` (500),
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:190` (username con comilla);
`auth/src/test/java/com/bcp/workshop/auth/LegacyDatabaseTest.java:17` (migración idempotente).

La prueba HTTP no puede reproducir hoy el `500` de una excepción SQLite: `LegacyDatabase.findByCredentials` captura los errores de persistencia y devuelve `null`, que el recurso convierte en `401`. Las dos pruebas de `500` anteriores fuerzan la excepción con un sustituto de prueba y comprueban directamente el `Response` del recurso; no verifican la serialización HTTP del error.

### Ejecuciones y cobertura

Todos los comandos se ejecutaron con directorio de trabajo `auth/`.

| componente | IDs relacionados | comando | código de salida | resultado |
|---|---|---|---:|---|
| auth | Contrato de endpoints | `mvn -Dtest=AuthResourceTest test` (baseline previo a ampliar tests) | 0 | 4 pruebas; 0 fallos, 0 errores, 0 omitidas. |
| auth | H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-05 | `mvn -Dtest=AuthResourceTest test` | 0 | 13 pruebas; 0 fallos, 0 errores, 0 omitidas. |
| auth | H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-05 | `mvn verify` | 0 | 14 pruebas en total: `AuthResourceTest` 13/13 y `LegacyDatabaseTest` 1/1; 0 fallos, 0 errores, 0 omitidas. Generó el informe JaCoCo. |

**Medición:** JaCoCo `0.8.12`, generado por `mvn verify`. Informe HTML en
`auth/target/site/jacoco/index.html`; datos XML en
`auth/target/site/jacoco/jacoco.xml`. Se midió la clase de producción
`AuthResource`, que implementa el endpoint de login: 25/25 líneas cubiertas
(100%) y 14/14 ramas cubiertas (100%). Numerador y denominador se obtuvieron de
los contadores `LINE` y `BRANCH` de la clase en el XML JaCoCo. La meta del 85%
se supera para esta clase; no se interpreta como cobertura de todas las clases
de `auth/`. En este paso no se modificó código de producción.

### Fallos, pendientes y pruebas propuestas

- **Fallos de las ejecuciones registradas:** ninguno. El baseline y las dos
  ejecuciones posteriores terminaron con código 0.
- **Pendiente, `/q/health`:** no hay checks registrados que permitan obtener
  una respuesta no saludable; además, el contrato actual no documenta una
  respuesta HTTP de error. Si se añade un health check, acordar y documentar su
  respuesta antes de agregar ese test.
- **Pendiente, `POST /auth/login` 500:** el cuerpo del `Response` se prueba por
  llamada directa, no mediante HTTP. Si se añade una vía de inyección de
  dependencia apropiada o un test resource existente, agregar una prueba de
  integración que valide status y JSON en el cable, sin cambiar el contrato.
- **Pendiente, JSON malformado:** `docs/ENDPOINTS.md` lo deja como pregunta
  abierta porque la respuesta procede del framework y no está fijada en el
  recurso. No se escribió un test que asuma ese comportamiento.
- **Fuera de esta matriz:** pruebas de contrato para tokens firmados/expirados
  no aplican al comportamiento actual; la respuesta declara una duración, pero
  el código no verifica el token. H-AUTH-03 permanece pendiente.

### Documentos consultados

- `README.md`
- `RETO.md`
- `AGENTS.md`
- `docs/GOOD_PRACTICES.md`
- `docs/ENDPOINTS.md`
- `HALLAZGOS.md`
- `PLAN.md`
- Código y pruebas de `auth/` citados en esta evidencia

## Actualización HU-01 — H-AUTH-03 y H-AUTH-04

| componente | IDs relacionados | comando | código de salida | resultado |
|---|---|---|---:|---|
| auth | H-AUTH-03, H-AUTH-04 | `mvn '-Dtest=AuthResourceTest,LegacyTokenUtilTest' test` (`cwd auth/`) | 0 | 19 pruebas, 0 fallos: claims/firma, manipulación de firma, secreto ausente/corto y preflight CORS permitido/no permitido. |
| auth | H-AUTH-03, H-AUTH-04 | `mvn verify` (`cwd auth/`) | 0 | 20 pruebas, 0 fallos. JaCoCo: `LegacyTokenUtil` 14/14 líneas (100%) y 4/4 ramas; `AuthResource` 25/25 líneas (100%) y 14/14 ramas. |
| api | H-AUTH-03 | `.venv/Scripts/python.exe -m pytest -q` (`cwd api/`) | 0 | 12 pruebas, 0 fallos; tokens válidos, alterados, expirados, formato legado, algoritmo no permitido, claims requeridos, header ausente y clave ausente/corta. |
| api | H-AUTH-03 | `.venv/Scripts/python.exe -m pytest --cov=app.main --cov-report=term-missing` (`cwd api/`) | 0 | 12 pruebas, 0 fallos; 102 sentencias, 7 no cubiertas, 20 ramas con 3 parciales; 92% de cobertura total según Coverage.py. Permanecen warnings deprecados de FastAPI/Starlette. |
| repo | H-AUTH-04 | `docker compose config --quiet` (`cwd ai-labs/`) | no ejecutado | Docker no está instalado. YAML de Compose se parseó con PyYAML y se confirmó la variable `AUTH_TOKEN_SECRET` para auth y API. |

**Límites de validación:** no se ejecutó un test HTTP real de extremo a extremo auth→API; los tests prueban emisor y verificador por separado con la misma clave ficticia de prueba. No se validó despliegue real ni configuración de orígenes de producción. No se imprimieron ni almacenaron tokens o claves reales.
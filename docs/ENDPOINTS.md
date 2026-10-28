# Contratos HTTP

## auth

Contrato observado en el código y, para las respuestas indicadas, comprobado
contra la aplicación local el 2026-10-26. No consta aquí una aprobación de
compatibilidad por los consumidores; las decisiones pendientes se indican en
cada endpoint.

### GET /q/health

1. **Qué hace**

   Informa si el servicio de autenticación está disponible para recibir
   solicitudes.

2. **Autenticación**

   No requiere autenticación. No se requiere enviar `Authorization` ni otro
   header de autenticación.

3. **Request**

   No tiene campos ni cuerpo JSON. No se requieren headers especiales.

   Ejemplo de solicitud: `GET /q/health` sin cuerpo.

4. **Response exitosa**

   Código: `200 OK`.

   | campo | tipo | descripción |
   |---|---|---|
   | `status` | string | Estado global informado por SmallRye Health. En la comprobación local fue `UP`. |
   | `checks` | array | Comprobaciones registradas por la aplicación. En la comprobación local estaba vacío. |

   Ejemplo JSON observado:

   ```json
   {"status":"UP","checks":[]}
   ```

5. **Respuestas de error**

   No se observó una respuesta HTTP de error: la aplicación actual no registra
   health checks y la petición local devolvió `200`. El código de la aplicación
   no define un cuerpo de error para este endpoint. Si se añaden checks, queda
   por confirmar con el equipo qué código y cuerpo deben documentarse cuando
   alguno reporte un estado no saludable.

6. **Notas de seguridad**

   El endpoint no solicita credenciales y la respuesta no incluye datos de
   usuario. Su ruta procede de la extensión `quarkus-smallrye-health`; no hay un
   recurso de health propio en `auth/`. Evidencia: dependencia en
   `auth/pom.xml:38-41`; respuesta comprobada en `GET http://localhost:8080/q/health`
   durante la ejecución local.

### POST /auth/login

1. **Qué hace**

   Autentica a una persona del workshop y devuelve sus datos públicos junto con
   un token para el flujo de login existente.

2. **Autenticación**

   No requiere autenticación previa ni header `Authorization`; las credenciales
   se envían en el cuerpo JSON.

3. **Request**

   `Content-Type: application/json`.

   | campo | tipo | obligatorio | descripción |
   |---|---|---|---|
  | `username` | string | Sí | Nombre de usuario. No puede ser nulo, vacío o compuesto solo por espacios; el valor original se usa en la búsqueda. |
  | `password` | string | Sí | Contraseña. No puede ser nula, vacía o compuesta solo por espacios; el valor original se verifica. |
   | `client` | string | No | Campo aceptado por el DTO, pero no utilizado por el flujo de login actual. |

   Ejemplo JSON completo con las credenciales ficticias documentadas para el
   workshop:

   ```json
   {
     "username": "student",
     "password": "Workshop123!",
     "client": "angular-workshop"
   }
   ```

4. **Response exitosa**

   Código: `200 OK`.

   | campo | tipo | descripción |
   |---|---|---|
   | `token` | string | Token generado para esta autenticación. Su valor cambia en cada emisión. |
   | `expiresIn` | integer | Duración declarada por la respuesta, en segundos: `3600`. |
   | `user` | object | Datos públicos del usuario autenticado. |
   | `user.username` | string | Nombre de usuario. |
   | `user.displayName` | string | Nombre de presentación, escapado para HTML por el recurso. |
   | `user.role` | string | Rol asociado a la cuenta, por ejemplo `STUDENT`. |
   | `debug` | string | Marcador fijo devuelto actualmente: `authenticated-with-legacy-flow`. |

   Ejemplo JSON completo observado; `token` se sustituye por un marcador porque
   el valor real es efímero:

   ```json
   {
     "token": "<token generado por el servidor>",
     "expiresIn": 3600,
     "user": {
       "username": "student",
       "displayName": "Workshop Student",
       "role": "STUDENT"
     },
     "debug": "authenticated-with-legacy-flow"
   }
   ```

5. **Respuestas de error**

   - `400 Bad Request`, cuando el cuerpo deserializado es nulo. Ejemplo
     observado: `{"message":"Request is null"}`.
   - `400 Bad Request`, cuando `username` es nulo o está vacío/compuesto por
     espacios. Ejemplo observado: `{"message":"Username is required"}`.
   - `400 Bad Request`, cuando `password` es nula o está vacía/compuesta por
     espacios. Ejemplo observado: `{"message":"Password is required"}`.
   - `401 Unauthorized`, cuando no se encuentra el usuario o la contraseña no
     coincide. Ejemplo observado: `{"message":"Invalid user student or password"}`.
   - `500 Internal Server Error`, si una excepción llega al `catch` del recurso.
     El cuerpo incluye `message` (el mensaje de la excepción, o `Unknown error`
     si no existe) y `exception` (el nombre completo de la clase). No se pudo
     provocar de forma controlada este caso durante la comprobación local; el
     siguiente JSON muestra la estructura con valores dinámicos, no una
     respuesta literal capturada:

     ```json
     {
       "message": "<mensaje de la excepción o Unknown error>",
       "exception": "<nombre completo de la clase de la excepción>"
     }
     ```

     Pregunta abierta: acordar y probar una respuesta `500` reproducible antes
     de tratar sus valores como contrato estable. El recurso actualmente expone
     detalles de excepción.

   El comportamiento ante JSON malformado y otros errores generados antes de
   entrar al método del recurso no está definido por este código; confirmar sus
   respuestas con una prueba de integración si los consumidores dependen de
   ellas.

6. **Notas de seguridad**

   - La consulta de usuario usa SQL parametrizado y la contraseña almacenada se
     verifica con BCrypt. La migración desde esquemas antiguos puede fallar y su
     error de inicialización se absorbe; H-AUTH-02 continúa `Pendiente` en
     `HALLAZGOS.md`.
   - El token actual es un JWT firmado con HS256. Incluye subject `sub`, claim
     `role`, `iat` y `exp`; API verifica la firma y expiración con HS256. La
     duración declarada sigue siendo `expiresIn: 3600` segundos. El formato
     Base64 legado ya no se acepta y requiere volver a iniciar sesión.
   - El secreto se obtiene de `AUTH_TOKEN_SECRET`, no del código; debe contener
     al menos 32 bytes. Si falta o es demasiado corto, auth no emite un token y
     API responde `503` a solicitudes protegidas. Auth y API deben configurarse
     con el mismo valor secreto fuera de archivos versionados.
   - La respuesta conserva el campo `debug` y el error `500` puede exponer el
     mensaje y la clase de una excepción.
   - El `401` usa el mismo mensaje para usuario inexistente y contraseña
     incorrecta, pero incluye el username enviado por el cliente.
   - CORS de auth permite por defecto `http://localhost:4200`, configurable
     mediante `AUTH_CORS_ORIGINS`. En despliegues, configurar explícitamente los
     orígenes aprobados. CORS no reemplaza la autenticación.

   Evidencia del request/response: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:15-57`;
   campos del request: `auth/src/main/java/com/bcp/workshop/auth/LoginRequest.java:3-7`;
   token: `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:8-15`;
   consulta y verificación de contraseña:
   `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:128-142`;
   configuración CORS: `auth/src/main/resources/application.properties:4-6`.

## Documentos consultados

- `README.md`
- `RETO.md`
- `AGENTS.md`
- `docs/GOOD_PRACTICES.md`
- `HALLAZGOS.md`
- `PLAN.md`
- Código de `auth/` citado en las notas de cada endpoint

Al iniciar este trabajo no existía `docs/ENDPOINTS.md`; en `docs/` no había
otros documentos aparte de `GOOD_PRACTICES.md`.
# Endpoints de ReqFlow

Contrato de integración por componente. Cada sección documenta únicamente lo
que puede verificarse leyendo el código actual; donde el código no define
algo explícitamente, queda marcado como pregunta abierta.

## api

### Cómo integrar

- **Base URL (desarrollo local)**: `http://127.0.0.1:8000`, levantada con
  `python tools/lab.py start api` (equivale a `uvicorn app.main:app --host
  127.0.0.1 --port 8000 --reload`). Evidencia: `tools/lab.py` (acción
  `start`, componente `api`).
- **Autenticación**: todas las rutas de este documento, salvo que se indique
  lo contrario, requieren el header `Authorization: Bearer <token>`. El
  token lo emite el componente `auth` (fuera del alcance de este
  documento); `api` únicamente lo verifica. Evidencia: `api/app/security.py`
  (`verify_legacy_token`).
- **Formato del token verificado por `api`**: Base64 de una cadena con
  cuatro segmentos separados por `|`: `username|role|expiracion_epoch|secreto`.
  `api` valida la cantidad de segmentos, que el secreto coincida con el
  configurado (variable de entorno `WORKSHOP_TOKEN_SECRET`, con un valor de
  prueba por defecto si no se configura) y que la expiración no haya pasado.
  Evidencia: `api/app/security.py:44-53`.
  - **Pregunta abierta**: no se verifica una firma criptográfica real, ni
    `iss` (emisor) ni `aud` (audiencia); ver nota de seguridad al final de
    esta sección y `HALLAZGOS.md` (`H-API-01`, estado "Resuelto
    parcialmente").
- **Formato común de error de autenticación**: cualquier ruta con token
  ausente, mal formado, con secreto incorrecto o expirado responde
  `401` con `{"detail": "Invalid token"}`. El detalle se mantiene genérico
  y no expone el texto de una excepción interna.
- **Variables de entorno relevantes para integrar un entorno propio**:
  `WORKSHOP_DB_PATH` (ruta de la base SQLite, por defecto
  `./data/workshop.db`), `WORKSHOP_UPLOAD_DIR` (carpeta de archivos
  subidos, por defecto `./uploads`), `WORKSHOP_TOKEN_SECRET` (secreto del
  token heredado), `AUTH_HEALTH_URL` (URL que consulta
  `GET /api/backend-health`, por defecto `http://localhost:8080/q/health`).
  Evidencia: `api/app/main.py:20-21`, `api/app/security.py:27-28`,
  `api/app/main.py:78`.

---

### `GET /api/tasks`

**1. Qué hace**: devuelve la lista de tareas que pertenecen al usuario
autenticado (no se puede pedir las de otro usuario).

**2. Autenticación**: requerida. Header `Authorization: Bearer <token>`.

**3. Request**

No recibe parámetros de consulta ni cuerpo. (Antes aceptaba un parámetro de
consulta `owner`; ya no tiene ningún efecto ni está declarado en la ruta —
ver nota de seguridad.)

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| *(ninguno)* | — | — | Esta ruta no define parámetros de consulta ni cuerpo. |

Ejemplo real de la petición:
```http
GET /api/tasks HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer c3R1ZGVudHxTVFVERU5UfDE3OTM5MDAwMDB8V09SS1NIT1BfU0VDUkVUXzIwMjY=
```

**4. Response exitosa**: `200 OK`, cuerpo = lista JSON de tareas.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador autoincremental de la tarea. |
| `title` | string | Título de la tarea. |
| `description` | string | Descripción de la tarea. |
| `status` | string | Estado de la tarea (valor libre; ver pregunta abierta). |
| `owner` | string | Usuario propietario; siempre coincide con el `username` del token. |
| `priority` | string | Prioridad (valor libre; ver pregunta abierta). |
| `createdAt` | string | Fecha/hora de creación en UTC, formato `YYYY-MM-DD HH:MM:SS` (lo genera SQLite con `datetime('now')`). |

Ejemplo real (capturado contra el código actual, usuario `student`):
```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 22:23:06"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 22:23:06"
  }
]
```

**5. Respuestas de error**

| Código | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401` | Header `Authorization` ausente, inválido, con secreto incorrecto, con cantidad de segmentos distinta de 4, o con expiración vencida. | `{"detail": "Invalid token"}` |
| `401` | El token no es Base64 válido. | `{"detail": "Invalid token"}` |

**6. Notas de seguridad**

- Desde `H-API-02` (`HALLAZGOS.md`, estado "Resuelto"), esta ruta **ya no
  acepta ni usa ningún `owner` enviado por el cliente**: el propietario de
  las tareas devueltas siempre es `identity.username`, extraído del token
  verificado. Evidencia: `api/app/main.py` (`list_tasks` →
  `resolve_owner`), `api/app/authorization.py`.
- El mensaje de error 401 es genérico y no incluye texto interno de la
  excepción (H-API-06 en `HALLAZGOS.md`). El servidor registra solo el tipo
  de excepción, sin su mensaje.

---

### `POST /api/tasks`

**1. Qué hace**: crea una tarea nueva asignada siempre al usuario
autenticado.

**2. Autenticación**: requerida. Header `Authorization: Bearer <token>`.

**3. Request**: cuerpo JSON validado con un modelo tipado
(`TaskCreateRequest`).

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `title` | string | Sí | Título de la tarea. |
| `description` | string | Sí | Descripción de la tarea. |
| `status` | string | No (default `"TODO"`) | Estado de la tarea (valor libre; ver pregunta abierta). |
| `priority` | string | No (default `"MEDIUM"`) | Prioridad (valor libre; ver pregunta abierta). |

Cualquier otro campo enviado en el cuerpo (por ejemplo, un `owner`) se
ignora silenciosamente: el modelo solo declara los cuatro campos de arriba
y Pydantic descarta campos no declarados por defecto. Evidencia:
`api/app/schemas.py`.

Ejemplo real de la petición:
```http
POST /api/tasks HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer c3R1ZGVudHxTVFVERU5UfDE3OTM5MDAwMDB8V09SS1NIT1BfU0VDUkVUXzIwMjY=
Content-Type: application/json

{
  "title": "Escribir documentacion",
  "description": "Redactar docs/ENDPOINTS.md",
  "status": "TODO",
  "priority": "HIGH"
}
```

Ejemplo real sin `status` ni `priority` (usa los valores por defecto):
```json
{
  "title": "Solo titulo y desc",
  "description": "sin status ni priority"
}
```

**4. Response exitosa**: `201 Created`, cuerpo = la tarea creada.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador autoincremental asignado. |
| `title` | string | Igual al enviado. |
| `description` | string | Igual al enviado. |
| `status` | string | Igual al enviado, o `"TODO"` si no se envió. |
| `owner` | string | Siempre el `username` del token verificado (nunca lo decide el cliente). |
| `priority` | string | Igual al enviado, o `"MEDIUM"` si no se envió. |
| `createdAt` | string | Fecha/hora de creación en UTC, formato `YYYY-MM-DD HH:MM:SS`. |

Ejemplo real (para la primera petición de ejemplo, usuario `student`):
```json
{
  "id": 4,
  "title": "Escribir documentacion",
  "description": "Redactar docs/ENDPOINTS.md",
  "status": "TODO",
  "owner": "student",
  "priority": "HIGH",
  "createdAt": "2026-11-02 22:23:07"
}
```

**5. Respuestas de error**

| Código | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401` | Mismas condiciones que `GET /api/tasks` (token ausente/inválido/expirado). | `{"detail": "Invalid token"}` |
| `422` | Falta `title` o `description` en el cuerpo, o el cuerpo no es un JSON válido según el modelo. | `{"detail": [{"type": "missing", "loc": ["body", "title"], "msg": "Field required", "input": {"description": "falta title"}}]}` |

**6. Notas de seguridad**

- Desde `H-API-02`, el campo `owner` del cuerpo ya no se usa para decidir a
  quién se asigna la tarea; siempre se asigna a `identity.username`.
  Evidencia: `api/app/main.py` (`create_task`).
- Desde `H-API-03` (`HALLAZGOS.md`, estado "Resuelto"), el `INSERT` usa
  parámetros (`?`) de `sqlite3` en vez de concatenar los valores del
  cliente dentro del SQL. Evidencia: `api/app/tasks_repository.py`
  (`insert`).
- **Pregunta abierta**: el código no limita los valores posibles de
  `status`/`priority` a una lista cerrada (acepta cualquier string). Los
  valores observados en los datos sembrados y en la lógica de
  `GET /api/summary` son `status` ∈ {`TODO`, `IN_PROGRESS`, `DONE`,
  `ARCHIVED`, …} y `priority` ∈ {`LOW`, `MEDIUM`, `HIGH`, …}, pero esto es
  una convención, no una validación del código.

---

### `GET /api/summary`

**1. Qué hace**: devuelve un resumen agregado (totales por estado y
prioridad alta pendiente) de las tareas del usuario autenticado.

**2. Autenticación**: requerida. Header `Authorization: Bearer <token>`.

**3. Request**

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| *(ninguno)* | — | — | Esta ruta no define parámetros de consulta ni cuerpo. (Antes aceptaba `owner`; ya no tiene efecto ni está declarado — ver nota de seguridad.) |

Ejemplo real de la petición:
```http
GET /api/summary HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer c3R1ZGVudHxTVFVERU5UfDE3OTM5MDAwMDB8V09SS1NIT1BfU0VDUkVUXzIwMjY=
```

**4. Response exitosa**: `200 OK`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Siempre el `username` del token verificado. |
| `total` | integer | Cantidad total de tareas del usuario. |
| `byStatus` | object (`string` → `integer`) | Conteo de tareas por cada valor de `status` presente. |
| `highPriorityOpen` | integer | Cantidad de tareas con `priority == "HIGH"` cuyo `status` no es `"DONE"` ni `"ARCHIVED"`. |

Ejemplo real (usuario `student`, tras las dos creaciones de ejemplo de
arriba):
```json
{
  "owner": "student",
  "total": 4,
  "byStatus": {
    "TODO": 3,
    "IN_PROGRESS": 1
  },
  "highPriorityOpen": 2
}
```

**5. Respuestas de error**

| Código | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401` | Mismas condiciones que `GET /api/tasks` (token ausente/inválido/expirado). | `{"detail": "Invalid token"}` |

**6. Notas de seguridad**

- Desde `H-API-02`, esta ruta ya no acepta ni usa ningún `owner` enviado
  por el cliente; el resumen siempre corresponde a `identity.username`.
  Evidencia: `api/app/main.py` (`summary` → `resolve_owner`).
- Desde `H-API-03`, la consulta de agregación usa parámetros (`?`) en vez
  de concatenar el `owner` en el SQL. Evidencia: `api/app/tasks_repository.py`
  (`summary_rows_by_owner`).

---

### `POST /api/requirements`

**1. Qué hace**: sube un archivo de requerimientos (multipart) y lo guarda
en el servidor, asociado al usuario autenticado.

**2. Autenticación**: requerida. Header `Authorization: Bearer <token>`.

**3. Request**: `multipart/form-data` con un único campo de archivo.

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `file` | archivo (multipart) | Sí | Archivo a subir. Solo se acepta nombre con extensión `.txt`, `.md`, `.pdf` o `.docx` (sin distinguir mayúsculas/minúsculas) y tamaño máximo de 2 MiB (2 097 152 bytes). El nombre se normaliza a su componente final (se descartan segmentos de ruta, por ejemplo `..`). |

Ejemplo real de la petición (como la vería un cliente HTTP):
```http
POST /api/requirements HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer c3R1ZGVudHxTVFVERU5UfDE3OTM5MDAwMDB8V09SS1NIT1BfU0VDUkVUXzIwMjY=
Content-Type: multipart/form-data; boundary=----boundary

------boundary
Content-Disposition: form-data; name="file"; filename="req.txt"
Content-Type: text/plain

El login debe ser accesible
------boundary--
```

**4. Response exitosa**: `201 Created`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Siempre el `username` del token verificado. |
| `fileName` | string | Nombre normalizado del archivo (solo el componente final, sin ruta). |
| `storedAt` | string | Ruta completa donde quedó guardado el archivo en el servidor. |
| `size` | integer | Tamaño en bytes del contenido guardado. |

Ejemplo real:
```json
{
  "owner": "student",
  "fileName": "req.txt",
  "storedAt": "C:\\Users\\Usuario\\AppData\\Local\\Temp\\tmp4hcfhgaw\\uploads\\req.txt",
  "size": 27
}
```

**5. Respuestas de error**

| Código | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401` | Mismas condiciones que `GET /api/tasks` (token ausente/inválido/expirado). | `{"detail": "Invalid token"}` |
| `422` | No se envía el campo `file` en el multipart. | `{"detail": [{"type": "missing", "loc": ["body", "file"], "msg": "Field required", "input": null}]}` |
| `422` | La extensión del archivo (tras normalizar el nombre) no está en la lista permitida (`.txt`, `.md`, `.pdf`, `.docx`). | `{"detail": "Extensión de archivo no permitida"}` |
| `422` | El contenido del archivo supera 2 MiB (2 097 152 bytes). | `{"detail": "El archivo excede el tamaño máximo permitido"}` |
| `422` | El nombre de archivo, tras normalizarlo, queda vacío (reproducible enviando `filename=""` explícito en el `Content-Disposition` del multipart). | `{"detail": "El archivo debe tener un nombre válido"}` |

**6. Notas de seguridad**

- Desde `H-API-04` (`HALLAZGOS.md`, estado "Resuelto"), el nombre de
  archivo se normaliza a su componente final antes de construir la ruta de
  escritura, evitando que un nombre con segmentos como `../` escriba fuera
  de la carpeta de subidas. Evidencia: `api/app/uploads.py`
  (`_normalized_file_name`).
- Se valida la extensión contra una lista explícita
  (`ALLOWED_REQUIREMENT_EXTENSIONS`) y el tamaño contra un máximo
  (`MAX_REQUIREMENT_FILE_SIZE_BYTES`) antes de escribir el archivo en
  disco. Evidencia: `api/app/uploads.py`.
- **Pregunta abierta / riesgo pendiente**: el archivo completo se lee en
  memoria (`await upload.read()`) **antes** de comprobar el límite de
  tamaño; un archivo muy grande se termina rechazando, pero se llega a
  cargar por completo en memoria antes del rechazo. No hay, dentro de este
  código, un límite que corte la lectura progresivamente. Evidencia:
  `api/app/uploads.py` (`store_requirement_file`).
- No hay separación por propietario en la carpeta de subidas: dos usuarios
  que suban un archivo con el mismo nombre final se sobrescriben entre sí.
  Evidencia: `api/app/uploads.py` (`target = Path(upload_dir) / file_name`).

---

### `GET /api/backend-health`

**1. Qué hace**: consulta el estado del backend de autenticación (`auth`)
desde `api`, a modo de verificación de salud entre servicios.

**2. Autenticación**: requerida. Header `Authorization: Bearer <token>`.

**3. Request**

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| *(ninguno)* | — | — | Esta ruta no define parámetros de consulta ni cuerpo. |

Ejemplo real de la petición:
```http
GET /api/backend-health HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer c3R1ZGVudHxTVFVERU5UfDE3OTM5MDAwMDB8V09SS1NIT1BfU0VDUkVUXzIwMjY=
```

**4. Response exitosa**: `200 OK`. **Importante**: esta ruta responde
siempre `200` (mientras el token sea válido), incluso si la consulta al
backend de `auth` falla; el resultado de esa consulta va dentro del cuerpo,
no en el código de estado HTTP de esta respuesta.

| Campo | Tipo | Descripción |
|---|---|---|
| `requestedBy` | string | Siempre el `username` del token verificado. |
| `status` | integer | Código de estado HTTP devuelto por `AUTH_HEALTH_URL`, o `0` si la petición a ese backend falló (por ejemplo, por no poder conectar). |
| `body` | string | Cuerpo de la respuesta del backend consultado (decodificado como UTF-8), o `Backend health check failed` si la petición falló. |

Ejemplo de fallo al consultar `auth`:
```json
{
  "requestedBy": "student",
  "status": 0,
  "body": "Backend health check failed"
}
```

**Pregunta abierta**: no se verificó en este paso el cuerpo exacto cuando
`auth` sí responde (no se levantó una instancia real de `auth` durante esta
revisión); por código, `body` sería el texto plano de la respuesta HTTP de
`auth` y `status` su código HTTP real. Pendiente de verificar con `auth`
corriendo.

**5. Respuestas de error**

| Código | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401` | Mismas condiciones que `GET /api/tasks` (token ausente/inválido/expirado). Esta es la única forma en que esta ruta responde con un código de error HTTP propio. | `{"detail": "Invalid token"}` |

**6. Notas de seguridad**

- Ante una falla del backend, `body` contiene un mensaje genérico y el
  servidor registra solo el tipo de excepción, sin su texto
  (H-API-06 en `HALLAZGOS.md`).
- La URL consultada (`AUTH_HEALTH_URL`) es configurable por variable de
  entorno y no se valida ni restringe dentro de este código; quien
  despliegue el servicio controla ese valor.

---

### Preguntas abiertas (resumen, componente `api`)

- Formato y proceso exacto de emisión de tokens: lo define `auth`, fuera
  de este documento.
- Verificación real de firma/emisor/audiencia del token: no implementada
  todavía en `api` (`H-API-01`, "Resuelto parcialmente" en
  `HALLAZGOS.md`); mientras tanto, cualquier portador del secreto
  configurado puede emitir un token válido para cualquier `username`.
- Lista cerrada de valores permitidos para `status` y `priority`: no existe
  en el código; se documentan solo los valores observados por convención.
- Cuerpo exacto de `GET /api/backend-health` cuando `auth` sí responde: no
  verificado contra una instancia real de `auth` (se verificó con una
  llamada HTTP simulada en `api/tests/test_api.py`, ver `docs/TESTING.md`).

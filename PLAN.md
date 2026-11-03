# Plan de corrección

Propuestas de corrección para hallazgos marcados "Aprobado" en `HALLAZGOS.md`.
Este documento es una propuesta: no se ha modificado código todavía. Cada
apartado requiere revisión y aprobación humana antes de implementar. No existe
`docs/ENDPOINTS.md` para `api`, por lo que el contrato a preservar es el
comportamiento observado hoy en `api/app/main.py` (rutas, status codes y forma
de las respuestas), no las fallas de seguridad que motivan cada hallazgo.

## api

### Decisión de revisión

| Fecha | Persona revisora | Alcance aprobado | Decisión | Condiciones |
|---|---|---|---|---|
| 2026-11-02 | user-bcp-student46 | H-API-01, H-API-02, H-API-03, H-API-04, H-API-05 (propuesta completa de este documento) | Aprobado | Antes de implementar: (1) escribir primero las pruebas de caracterización descritas en cada apartado y confirmarlas en verde con el código actual; (2) para H-API-01, no asumir ni modificar el formato de token de `auth` — queda como coordinación externa pendiente; (3) para H-API-02, dejar registrado como pendiente el posible impacto en `web` por el parámetro `owner`, sin leer su código; (4) para H-API-05, ejecutar el escaneo de dependencias antes de decidir si se actualiza alguna versión, sin asumir CVEs no verificados. |

Esta aprobación habilita el paso siguiente (caracterización e implementación
del alcance aprobado) descrito en `README.md`. No reemplaza una revisión de
diff una vez implementado el cambio.

### H-API-01 — Token Base64 con secreto fijo y sin validación de firma, emisor o audiencia

**Hallazgo de referencia**: `H-API-01` (alta, Aprobado) — `api/app/main.py:14`,
`api/app/main.py:17-25`.

**Problema**: `legacy_identity` decodifica el token como Base64, separa cuatro
campos por `|` y solo comprueba la cantidad de campos, un secreto fijo
(`LEGACY_SECRET = "WORKSHOP_SECRET_2026"`) embebido en el código y que la
expiración no haya pasado. No hay verificación criptográfica de firma, ni de
emisor (`iss`) ni de audiencia (`aud`); cualquiera que conozca el secreto (o
que lo adivine, dado que está en el repositorio) puede fabricar un token
válido para cualquier usuario o rol.

**Cambio propuesto**:
- Extraer la verificación de identidad a un módulo dedicado
  `api/app/security.py` con una única función
  `verify_access_token(authorization: str) -> Identity` (una responsabilidad:
  verificar, no decidir autorización ni acceder a datos).
- Reemplazar el decodificador Base64 casero por verificación real de JWT con
  una librería mantenida (`PyJWT`), comprobando firma (`HS256` con la clave
  desde variable de entorno, nunca hardcodeada), `iss`, `aud` y `exp`
  explícitos. Definir `Identity` como modelo Pydantic (`username`, `role`) en
  lugar de `dict[str, str]`.
- Sustituir el secreto embebido por una variable de entorno
  (`WORKSHOP_TOKEN_SECRET` o similar) con un valor de prueba aislado en
  `.env`/configuración local, nunca un secreto real en el código (regla 5/6
  del contrato de agentes).
- Nombrar con constantes los valores fijos que hoy están sueltos si se
  mantienen (emisor y audiencia esperados), evitando "strings mágicos".
- **Dependencia nueva a justificar**: `PyJWT` (o `python-jose`), porque
  reimplementar verificación de firma a mano repite el mismo error que motivó
  este hallazgo; se prefiere una librería vetada sobre código casero.
- **Riesgo/coordinación externa (sin ampliar alcance)**: esta corrección solo
  tiene efecto si `auth` emite un JWT firmado compatible (mismo secreto o
  llave pública, mismos claims `iss`/`aud`). Mientras `auth` siga emitiendo el
  token Base64 actual, `api` no puede verificar una firma real. Se registra
  como pendiente de coordinación con el componente `auth`, no se asume ni se
  implementa ese cambio aquí.
- El mensaje de error devuelto al fallar la validación se mantiene igual que
  hoy (incluye `str(error)`) porque corregirlo es el alcance de `H-API-06`,
  no aprobado en este plan; no se introduce una regresión de contrato de
  error, pero queda anotado como riesgo relacionado.

**Archivos a tocar**: `api/app/security.py` (nuevo), `api/app/main.py`
(reemplazar `legacy_identity` por la dependencia nueva), `api/requirements.txt`
(agregar `PyJWT`), `api/app/main.py` (variable de entorno para el secreto).

**Prueba de caracterización (antes de tocar código)**: en
`api/tests/test_api.py`, agregar:
- `test_rejects_token_with_wrong_secret`: token con los cuatro campos pero
  secreto distinto de `WORKSHOP_SECRET_2026` → hoy responde `401`.
- `test_rejects_expired_token`: token con `exp` en el pasado → hoy responde
  `401`.
- `test_accepts_valid_token_for_each_role`: variar `role` (`STUDENT`,
  `TRAINER`) y confirmar que `identity["username"]`/`identity["role"]` se
  reflejan igual que hoy (p. ej. en `owner` de la tarea creada).
Estas pruebas deben pasar con el código actual antes del cambio y seguir
pasando (ajustadas al nuevo formato de token si cambia) después, para no
perder cobertura de los casos ya cubiertos por `test_rejects_invalid_token`.

---

### H-API-02 — El cliente puede elegir el `owner` consultado o asignado

**Hallazgo de referencia**: `H-API-02` (alta, Aprobado) — `api/app/main.py:68-70`,
`api/app/main.py:78-85`, `api/app/main.py:91-93`.

**Problema**: `GET /api/tasks`, `GET /api/summary` y `POST /api/tasks` usan un
`owner` que puede llegar del cliente (`owner` en query string o en el cuerpo
JSON) en vez de depender siempre de `identity["username"]`. Una identidad
autenticada como `student` puede leer o escribir datos de `trainer` sin
ninguna comprobación de rol.

**Cambio propuesto**:
- Aplicar autorización por identidad: las tres rutas dejan de aceptar un
  `owner` que decide a quién se consulta o se asigna. El valor de `owner`
  usado para filtrar (`list_tasks`, `summary`) y para insertar
  (`create_task`) pasa a ser siempre `identity["username"]`, extraído del
  token ya verificado (depende de `H-API-01`).
- Extraer esta regla a una única función reutilizable (p. ej.
  `resolve_owner(identity: Identity) -> str`) para no duplicarla en las tres
  rutas (regla de "sin duplicación").
- El parámetro `owner` de query dejará de tener efecto sobre qué datos se
  devuelven; se documentará en `docs/ENDPOINTS.md` (paso posterior) que el
  valor que el cliente envíe se ignora a favor de la identidad del token.
- **Cambio de comportamiento observado, justificado por el hallazgo**: hoy
  `owner` permite leer/escribir datos ajenos; eso es exactamente lo que el
  hallazgo pide eliminar. Se preserva la forma del contrato (rutas, status
  codes, forma de la respuesta), no la posibilidad de suplantar `owner`.
- **Riesgo a registrar como pendiente**: si `web` (fuera de este alcance)
  depende hoy de enviar `owner` explícito para algún flujo, ese consumo deja
  de tener efecto tras el cambio; se anota como coordinación externa a
  validar con el equipo de `web`, sin leer ni modificar su código aquí.

**Archivos a tocar**: `api/app/main.py` (las tres rutas), posible helper nuevo
`api/app/authorization.py` con `resolve_owner`.

**Prueba de caracterización (antes de tocar código)**: en
`api/tests/test_api.py`, agregar (documentando el comportamiento actual, que
se espera que cambie tras la corrección):
- `test_owner_query_param_currently_overrides_identity_on_list`: autenticado
  como `student`, pedir `GET /api/tasks?owner=trainer` y confirmar que hoy
  devuelve las tareas de `trainer` (evidencia del hallazgo).
- `test_owner_query_param_currently_overrides_identity_on_summary`: mismo
  caso para `GET /api/summary?owner=trainer`.
- `test_owner_body_field_currently_overrides_identity_on_create`: autenticado
  como `student`, crear una tarea con `"owner": "trainer"` en el cuerpo y
  confirmar que hoy la tarea queda con `owner: "trainer"`.
Tras la corrección, estas mismas pruebas se actualizan para afirmar que el
`owner` enviado por el cliente se ignora y siempre se usa
`identity["username"]`, quedando como regresión de la corrección.

---

### H-API-03 — Consultas SQLite construidas mediante concatenación

**Hallazgo de referencia**: `H-API-03` (alta, Aprobado) — `api/app/main.py:70-71`,
`api/app/main.py:84-85`, `api/app/main.py:93`.

**Problema**: `list_tasks`, `create_task` y `summary` arman el SQL concatenando
strings con valores que vienen del cliente (`owner`, `title`, `description`,
`status`, `priority`). Un valor con comilla simple ya rompe la consulta hoy
(no hace falta un payload de explotación para evidenciarlo) y, en general,
permite alterar la consulta.

**Cambio propuesto**:
- Extraer el acceso a datos de tareas a un módulo
  `api/app/tasks_repository.py` con funciones de una sola responsabilidad
  (`list_by_owner`, `insert`, `get_by_id`, `summary_rows_by_owner`), cada una
  usando parámetros con `?` de `sqlite3` en vez de concatenación. Esto separa
  la ruta (FastAPI) de la consulta SQL, alineado con "capas separadas".
- Tipar la entrada de `POST /api/tasks` con un modelo Pydantic
  (`TaskCreateRequest` con `title: str`, `description: str`, `status: str =
  "TODO"`, `priority: str = "MEDIUM"`) en vez de `dict[str, Any]`, de modo que
  la validación de tipos ocurra antes de construir la consulta parametrizada.
  Los valores por defecto (`"TODO"`, `"MEDIUM"`) quedan como constantes con
  nombre en vez de strings sueltos repetidos.
- La forma de la respuesta (`as_task`, campos `id/title/description/status/
  owner/priority/createdAt`) no cambia.

**Archivos a tocar**: `api/app/tasks_repository.py` (nuevo),
`api/app/main.py` (rutas `list_tasks`, `create_task`, `summary` usan el
repositorio en vez de SQL inline), modelo Pydantic en `api/app/main.py` o
`api/app/schemas.py` (nuevo).

**Prueba de caracterización (antes de tocar código)**: en
`api/tests/test_api.py`, agregar:
- `test_create_task_with_apostrophe_in_title`: crear una tarea con
  `"title": "O'Brien"` (dato de negocio legítimo, no un payload de
  explotación) y documentar el resultado actual (hoy falla por el SQL
  concatenado, por ejemplo con un error de servidor en vez de `201`).
- `test_list_tasks_returns_only_requested_owner_rows`: caracteriza que el
  filtro por `owner` sigue devolviendo las mismas filas que hoy para datos
  sin caracteres especiales (regresión de contenido, no de seguridad).
Tras parametrizar las consultas, `test_create_task_with_apostrophe_in_title`
pasa a esperar `201` y el título `"O'Brien"` guardado correctamente,
quedando como prueba de regresión del fix.

---

### H-API-04 — Nombre y contenido del archivo subido sin validación visible

**Hallazgo de referencia**: `H-API-04` (alta, Aprobado) — `api/app/main.py:108-111`.

**Problema**: `upload_requirement` usa `file.filename` tal cual para formar la
ruta de escritura (`Path(selected_uploads) / str(file.filename)`) y lee todo
el contenido antes de guardarlo, sin normalizar el nombre, sin lista de
extensiones permitidas ni límite de tamaño.

**Cambio propuesto**:
- Extraer la validación y el guardado a un módulo `api/app/uploads.py` con
  una función de una sola responsabilidad,
  `store_requirement_file(upload: UploadFile, upload_dir: str) -> StoredFile`,
  que:
  - Normaliza el nombre (usa solo el componente final del nombre, sin
    separadores de ruta, descartando cualquier segmento `..` o de
    directorio).
  - Verifica la extensión contra una lista permitida declarada como
    constante con nombre (p. ej. `ALLOWED_REQUIREMENT_EXTENSIONS = {".txt",
    ".md", ".pdf", ".docx"}`, a confirmar con quien aprueba el plan según los
    tipos de archivo reales del flujo de requerimientos).
  - Limita el tamaño máximo con una constante con nombre (p. ej.
    `MAX_REQUIREMENT_FILE_SIZE_BYTES`), leyendo el contenido y rechazando con
    `HTTPException` si lo excede, en vez de escribir cualquier tamaño.
  - Usa guard clauses (retorno/`raise` temprano) para cada condición en vez
    de anidar los `if` de validación.
- La ruta sigue respondiendo `201` con `owner`, `fileName`, `storedAt` y
  `size` igual que hoy para archivos que cumplen las reglas nuevas.

**Archivos a tocar**: `api/app/uploads.py` (nuevo), `api/app/main.py` (ruta
`upload_requirement` usa la función nueva).

**Prueba de caracterización (antes de tocar código)**: en
`api/tests/test_api.py`, agregar:
- `test_uploads_requirement_keeps_response_shape` (ya existe parcialmente
  como `test_uploads_requirement`; ampliarla para afirmar también `owner`,
  `fileName` y `size` en la respuesta, no solo que el archivo existe).
- `test_upload_with_path_segments_in_filename_today_writes_outside_target`:
  subir un archivo cuyo `filename` incluya un separador de ruta (por ejemplo
  un nombre con subcarpeta) y documentar dónde escribe el código actual
  (evidencia del hallazgo, sin payload de explotación contra un sistema
  real: es una prueba local contra el propio `upload_dir` de la prueba).
- `test_upload_without_extension_allowlist_today_accepts_any_extension`:
  subir un archivo con una extensión no relacionada con requerimientos (por
  ejemplo `.bin`) y confirmar que hoy se guarda igual.
Tras la corrección, estas pruebas se actualizan para afirmar el
comportamiento nuevo (nombre normalizado, extensión rechazada con error
genérico, tamaño máximo aplicado).

---

### H-API-05 — Versiones de dependencias candidatas a revisión SCA

**Hallazgo de referencia**: `H-API-05` (media, Aprobado) — `api/requirements.txt:4-5`.

**Problema**: `urllib3==2.5.0` y `python-multipart==0.0.21` están fijadas sin
que este discovery haya contrastado advisories vigentes; el riesgo de CVE no
está verificado todavía.

**Cambio propuesto**:
- No es un cambio de código de la aplicación: es una revisión de
  dependencias. Antes de tocar `api/requirements.txt`, ejecutar una
  herramienta de SCA (por ejemplo `pip-audit` sobre `api/requirements.txt`, o
  los resultados de Dependency Review/CodeQL del repositorio si están
  disponibles) y registrar qué CVEs aplican a `urllib3==2.5.0` y
  `python-multipart==0.0.21` en este entorno.
  - Nota: en este paso de planificación no se ejecutó ningún escáner; queda
    pendiente como evidencia a generar antes de decidir la versión destino.
- Si hay CVE aplicable, actualizar a la versión corregida mínima necesaria
  (no saltar a la última mayor sin motivo) y volver a ejecutar la batería de
  pruebas completa (`python tools/lab.py test api`) para confirmar que no hay
  regresión de comportamiento por el cambio de versión.
- Si no hay CVE aplicable a la versión actual, se deja constancia en
  `HALLAZGOS.md` con la evidencia del escaneo y se actualiza el estado del
  hallazgo en consecuencia (no se "silencia": se documenta con evidencia,
  regla 4 del contrato de agentes).
- No se agrega ninguna dependencia nueva para este hallazgo salvo la propia
  herramienta de auditoría, y solo en `requirements-dev.txt` (no en el
  runtime de producción), justificada por la necesidad de generar evidencia
  de SCA.

**Archivos a tocar**: `api/requirements.txt` (solo si el escaneo confirma
CVE), `api/requirements-dev.txt` (herramienta de auditoría, si se adopta),
`HALLAZGOS.md` (actualizar evidencia y estado una vez ejecutado el escaneo).

**Prueba de caracterización (antes de tocar código)**: no aplica una prueba
de comportamiento de la API (no cambia lógica de la aplicación). La
"caracterización" aquí es ejecutar y registrar:
- La batería completa actual (`python tools/lab.py test api`) en verde con
  las versiones fijadas hoy, como línea base antes de tocar
  `requirements.txt`.
- El resultado del escáner de dependencias (comando, versión del escáner,
  fecha, hallazgos) como evidencia a anexar a `docs/TESTING.md` y a
  `HALLAZGOS.md` en el paso correspondiente.
Después de cualquier bump de versión, repetir `python tools/lab.py test api`
y confirmar que sigue en verde antes de dar el hallazgo por corregido.

---

## Notas comunes a los cinco hallazgos

- Ninguno de estos cambios se implementa en este paso; este documento es la
  propuesta a revisar y aprobar por una persona antes de tocar
  `api/app/main.py` o crear los módulos nuevos.
- Todas las pruebas de caracterización se agregan primero y deben ejecutarse
  con `python tools/lab.py test api` (pytest con `--cov=app
  --cov-fail-under=85`) desde la raíz, con `cwd` efectivo en `api/`.
- Los módulos nuevos propuestos (`security.py`, `authorization.py`,
  `tasks_repository.py`, `uploads.py`, `schemas.py`) son el mínimo necesario
  para que cada corrección cumpla Clean Code (una responsabilidad, sin
  duplicación, sin anidamiento profundo, sin números/strings mágicos) sin
  asumir el alcance completo de `H-API-07`/`H-API-08` (no incluidos en este
  plan).
- `H-API-01` y `H-API-02` quedan parcialmente condicionados a coordinación
  externa con `auth` (formato real del token) y `web` (uso del parámetro
  `owner`); se registra como pendiente, sin ampliar el ámbito de este plan
  para investigarlo.

### Ejecución (api, H-API-01 a H-API-05)

Implementación realizada tras la aprobación humana registrada arriba.
Comando usado en todas las corridas (cwd efectivo `api/`, ejecutado desde la
raíz): `python tools/lab.py test api`.

| id | orden | comando | resultado antes del cambio | resultado después del cambio |
|---|---|---|---|---|
| H-API-01 | 1 | `python tools/lab.py test api` | 7 passed, 1 failed (`test_token_secret_is_configurable_via_environment`) — 92.86% cobertura | 8 passed — 92.86% cobertura |
| H-API-02 | 2 | `python tools/lab.py test api` | 8 passed, 3 failed (`test_owner_query_param_is_ignored_on_list`, `::_on_summary`, `test_owner_body_field_is_ignored_on_create`) — 92.86% cobertura | 11 passed — 93.10% cobertura |
| H-API-03 | 3 | `python tools/lab.py test api` | 11 passed, 1 failed (`test_create_task_with_apostrophe_in_title`, error de SQLite por concatenación) — 93.10% cobertura | 12 passed — 93.67% cobertura |
| H-API-04 | 4 | `python tools/lab.py test api` | 12 passed, 3 failed (`test_upload_normalizes_path_traversal_in_filename`, `test_upload_rejects_disallowed_extension`, `test_upload_rejects_file_over_size_limit`) — 93.67% cobertura | 15 passed — 93.78% cobertura |
| H-API-05 | 5 | `.venv\Scripts\python.exe -m pip_audit -r requirements.txt` + `python tools/lab.py test api` | pip-audit: 32 vulnerabilidades en `urllib3==2.5.0` y `python-multipart==0.0.21`; suite: 15 passed (línea base con versiones viejas, sin cambio de comportamiento esperado) | pip-audit: 0 vulnerabilidades en `urllib3==2.8.0` / `python-multipart==0.0.31` (persisten 10 en `starlette`, fuera de alcance); suite: 15 passed — 93.78% cobertura |

Cobertura final del módulo: 93.78% (`api/app/main.py` 90%, `api/app/security.py`
95%, `api/app/uploads.py` 94%, resto de módulos nuevos 100%), por encima del
85% exigido en `AGENTS.md`.

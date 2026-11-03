# Pruebas de ReqFlow

Registro de pruebas por componente, con comandos ejecutados, resultados
reales y cobertura. Nada de lo marcado como "ejecutado" es hipotético: todo
corrió en este entorno contra el código actual de cada componente.

## api

### Comandos y entorno

- **Directorio de ejecución efectivo**: `api/` (la raíz del repositorio es
  `ai-labs/`; Git se ejecuta desde ahí, las pruebas con `cwd` en `api/`).
- **Comando principal**:
  ```powershell
  cd ai-labs
  python tools/lab.py test api
  ```
  Equivale a, con `cwd` en `api/`:
  ```
  .venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=85
  ```
- **Comando de detalle de cobertura por archivo** (para el numerador/
  denominador explícito de cada módulo, sin omitir los archivos con 100%):
  ```powershell
  cd ai-labs/api
  .venv\Scripts\python.exe -m coverage report -m --no-skip-covered
  ```

### Resultado real de la ejecución final

```
TOTAL     169      0     24      0   100%
32 passed, 67 warnings in 5.74s
Required test coverage of 85% reached. Total coverage: 100.00%
```
Código de salida: `0`.

### Cobertura — método, numerador/denominator y alcance

- **Método de medición**: `pytest-cov` (`coverage.py` con `branch = true`,
  configurado en `api/pyproject.toml`), invocado por
  `python tools/lab.py test api`. El umbral exigido es `--cov-fail-under=85`
  (`tools/lab.py`), alineado con el 85% de `AGENTS.md`.
- **Código modificado** (los módulos tocados durante el refactor de
  H-API-01 a H-API-05, que en este componente equivale a todo `app/`,
  ya que la refactorización cubrió el módulo completo — ver `PLAN.md`):

  | Archivo | Sentencias (numerador/denominador) | Ramas (numerador/denominador) | Cobertura |
  |---|---|---|---|
  | `app/authorization.py` | 4/4 | 0/0 | 100% |
  | `app/main.py` | 71/71 | 12/12 | 100% |
  | `app/schemas.py` | 9/9 | 0/0 | 100% |
  | `app/security.py` | 36/36 | 6/6 | 100% |
  | `app/tasks_repository.py` | 19/19 | 0/0 | 100% |
  | `app/uploads.py` | 30/30 | 6/6 | 100% |

  **Código modificado: 169/169 sentencias (100%), 24/24 ramas (100%) → por
  encima del 85% exigido.**

- **Cobertura global** (`TOTAL` del mismo reporte, componente `api`
  completo): **169/169 sentencias, 24/24 ramas, 100%.** En este paso
  coincide numéricamente con "código modificado" porque todo `app/` fue
  parte del refactor de `H-API-01` a `H-API-05`; se registran como filas
  separadas porque son conceptualmente dos métricas distintas y no siempre
  van a coincidir en pasos futuros.

---

### Tabla de casos (endpoint | caso | tipo | resultado esperado)

| Endpoint | Caso | Tipo | Resultado esperado | ID relacionado |
|---|---|---|---|---|
| `GET /api/tasks` | Usuario con tareas sembradas pide su lista | feliz | `200`, lista con las tareas de ese usuario | — |
| `GET /api/tasks` | Header `Authorization` ausente | error | `401`, `detail="Invalid token"` | H-API-01, H-API-06 |
| `GET /api/tasks` | Token con secreto incorrecto | error | `401` | H-API-01 |
| `GET /api/tasks` | Token con cantidad de segmentos distinta de 4 | error | `401` | H-API-01 |
| `GET /api/tasks` | Token con fecha de expiración vencida | error | `401` | H-API-01 |
| `GET /api/tasks` | Valor del token no es Base64 válido | error | `401`, `detail="Invalid token"` sin mensaje interno | H-API-06 |
| `GET /api/tasks` | Token rotado vía `WORKSHOP_TOKEN_SECRET` | feliz | `200` (confirma que el secreto ya no es fijo en código) | H-API-01 |
| `GET /api/tasks` | Usuario autenticado pide `?owner=trainer` (otro usuario) | borde / seguridad (IDOR) | `200`, pero solo con tareas propias, nunca de `trainer` | H-API-02 |
| `GET /api/tasks` | Usuario sin tareas sembradas | borde | `200`, lista vacía `[]` | — |
| `POST /api/tasks` | Payload completo válido | feliz | `201`, tarea creada con `owner` del token | H-API-03 |
| `POST /api/tasks` | Token válido con rol distinto (`trainer`) | feliz | `201`, `owner` = `"trainer"` | H-API-01 |
| `POST /api/tasks` | Payload con `"owner": "trainer"` enviado por un `student` | borde / seguridad (IDOR) | `201`, pero `owner` queda en `"student"`, el campo se ignora | H-API-02 |
| `POST /api/tasks` | `title` con apóstrofo (`O'Brien's task`) | feliz / regresión | `201`, sin error de SQL | H-API-03 |
| `POST /api/tasks` | Payload mínimo (sin `status`/`priority`) | borde | `201`, `status="TODO"`, `priority="MEDIUM"` | — |
| `POST /api/tasks` | Payload vacío `{}` | borde + error | `422`, faltan `title` y `description` | — |
| `POST /api/tasks` | Token inválido | error | `401` | H-API-01 |
| `GET /api/summary` | Usuario con tareas de varios estados/prioridades | feliz | `200`, `byStatus` y `highPriorityOpen` correctos | — |
| `GET /api/summary` | Usuario autenticado pide `?owner=trainer` | borde / seguridad (IDOR) | `200`, pero `owner` en la respuesta sigue siendo el propio | H-API-02 |
| `GET /api/summary` | Usuario sin tareas | borde | `200`, `total=0`, `byStatus={}`, `highPriorityOpen=0` | — |
| `GET /api/summary` | Token inválido | error | `401` | H-API-01 |
| `POST /api/requirements` | Archivo `.txt` válido | feliz | `201`, archivo guardado en el directorio de subidas | H-API-04 |
| `POST /api/requirements` | Nombre con segmentos de ruta (`../escaped.txt`) | feliz / seguridad | `201`, se guarda dentro del directorio de subidas, no fuera | H-API-04 |
| `POST /api/requirements` | Extensión no permitida (`.exe`) | error | `422` | H-API-04 |
| `POST /api/requirements` | Archivo sin extensión | borde | `422` | H-API-04 |
| `POST /api/requirements` | Archivo justo en el límite (2 MiB exactos) | borde | `201` (el límite es inclusive) | H-API-04 |
| `POST /api/requirements` | Archivo que excede el límite (2 MiB + 1 byte) | error | `422` | H-API-04 |
| `POST /api/requirements` | Falta el campo `file` en el multipart | error | `422` | — |
| `POST /api/requirements` | Nombre de archivo vacío (`filename=""`) | error | `422` | H-API-04 |
| `POST /api/requirements` | Token inválido | error | `401` | H-API-01 |
| `GET /api/backend-health` | Backend de `auth` responde (simulado) | feliz | `200`, `status`/`body` reflejan la respuesta simulada | — |
| `GET /api/backend-health` | Backend de `auth` no alcanzable (simulado) | borde | `200`, `status=0`, mensaje genérico en `body` | H-API-06 |
| `GET /api/backend-health` | Token inválido | error | `401` | H-API-01 |

---

### Resultados reales ejecutados

**Ejecución final (32 pruebas, todas en verde)**
```powershell
PS ai-labs> python tools/lab.py test api
```
```
...
TOTAL     169      0     24      0   100%
32 passed, 67 warnings in 5.74s
Required test coverage of 85% reached. Total coverage: 100.00%
```
Código de salida: `0`.

**Fallos durante el desarrollo (no ocultos, corregidos antes del cierre)**

Al escribir `test_summary_counts_by_status_and_high_priority_open` la primera
versión de la prueba tenía una expectativa incorrecta (no un bug de la
aplicación): olvidó contar la tarea sembrada `"Refactor login"`
(`HIGH`/`TODO`) junto con la nueva tarea `"Urgente"` del mismo tipo.
```
FAILED tests/test_api.py::test_summary_counts_by_status_and_high_priority_open
assert 2 == 1
1 failed, 29 passed, 63 warnings in 1.83s
```
Código de salida: `1`. Se corrigió la aserción esperada (`highPriorityOpen == 2`)
para que coincidiera con la lógica real documentada en
`docs/ENDPOINTS.md`, y no al revés (no se tocó `api/app/main.py`). La
re-ejecución quedó en verde (ver arriba).

**Bug encontrado y reportado aparte (no escondido dentro de una prueba)**

Durante la revisión del diff de `api/app/uploads.py:46-47` se confirmó que
`store_requirement_file` lee el archivo completo en memoria
(`await upload.read()`) **antes** de comprobar
`MAX_REQUIREMENT_FILE_SIZE_BYTES`. Las pruebas de esta tabla
(`test_upload_rejects_file_over_size_limit`,
`test_upload_accepts_file_exactly_at_size_limit`) verifican el contrato
documentado (se rechaza por encima del límite, se acepta justo en el
límite) **sin** afirmar que el consumo de memoria sea eficiente; no se
escribió ninguna aserción que disimule ese problema. Este bug ya está
registrado como hallazgo "Importante" (no bloqueante) en la revisión del
diff y queda pendiente de una corrección específica (lectura por bloques)
fuera del alcance de este paso, que es solo de pruebas y documentación.

---

### Pendientes

- **`GET /api/backend-health` contra una instancia real de `auth`**: las
  pruebas de este documento simulan (`monkeypatch`) la llamada HTTP a
  `AUTH_HEALTH_URL`; no se verificó el cuerpo exacto de una respuesta real
  de `auth` porque ese componente no se levantó en este entorno (fuera del
  AMBITO de este paso, que solo lee/escribe en `api/`). Coordinación
  externa pendiente, igual que lo registrado en `docs/ENDPOINTS.md`.
- **Verificación real de firma/emisor/audiencia del token (H-API-01)**:
  sigue sin implementarse (bloqueado por `auth`, ver `HALLAZGOS.md` y
  `PLAN.md`); por lo tanto no hay — ni puede haber todavía — una prueba que
  confirme rechazo de un token con firma inválida, porque hoy no existe tal
  verificación.

### Pruebas propuestas (no implementadas en este paso)

- Prueba de integración real (no simulada) de `GET /api/backend-health`
  contra una instancia de `auth` levantada en el mismo entorno, una vez que
  ambos componentes puedan ejecutarse juntos.
- Prueba de `POST /api/requirements` que mida el consumo de memoria del
  proceso durante una subida grande, para acompañar la corrección futura
  del bug de lectura completa en memoria descrito arriba.
- Prueba contra un token real firmado por `auth` (JWT), una vez que
  `H-API-01` deje de estar "Resuelto parcialmente".

---

### Código de las pruebas

Archivo completo: `api/tests/test_api.py` (32 funciones de prueba).

```python
import base64
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def token(username: str = "student", role: str = "STUDENT") -> str:
    raw = f"{username}|{role}|{int(time.time()) + 3600}|WORKSHOP_SECRET_2026"
    return base64.b64encode(raw.encode()).decode()


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(username, role)}"}


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert summary.json()["total"] == 3


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


# --- H-API-01: caracterización del token heredado (ver PLAN.md) ---


def test_rejects_token_with_wrong_secret(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    raw = f"student|STUDENT|{int(time.time()) + 3600}|WRONG_SECRET"
    wrong_secret_token = base64.b64encode(raw.encode()).decode()
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {wrong_secret_token}"})
    assert response.status_code == 401


def test_rejects_malformed_base64_token(tmp_path: Path, caplog) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer not-base64!!"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"
    assert "Authentication token validation failed" in caplog.text
    assert "Invalid base64-encoded string" not in caplog.text


def test_rejects_token_with_wrong_segment_count(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    malformed_token = base64.b64encode(b"student|STUDENT|12345").decode()
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {malformed_token}"})
    assert response.status_code == 401


def test_rejects_expired_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    raw = f"student|STUDENT|{int(time.time()) - 10}|WORKSHOP_SECRET_2026"
    expired_token = base64.b64encode(raw.encode()).decode()
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_accepts_valid_token_for_each_role(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers("trainer", "TRAINER"),
            json={"title": "Trainer task", "description": "desc", "status": "TODO", "priority": "LOW"},
        )
    assert created.status_code == 201
    assert created.json()["owner"] == "trainer"


def test_token_secret_is_configurable_via_environment(tmp_path: Path, monkeypatch) -> None:
    # Prueba de corrección H-API-01: el secreto deja de ser un valor fijo en
    # el código y pasa a leerse de una variable de entorno (sin ser un
    # secreto real, es un valor de prueba aislado para este test).
    monkeypatch.setenv("WORKSHOP_TOKEN_SECRET", "ROTATED_SECRET_FOR_TEST")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    raw = f"student|STUDENT|{int(time.time()) + 3600}|ROTATED_SECRET_FOR_TEST"
    rotated_token = base64.b64encode(raw.encode()).decode()
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": f"Bearer {rotated_token}"})
    assert response.status_code == 200


# --- H-API-02: autorización ligada a la identidad (ver PLAN.md) ---


def test_owner_query_param_is_ignored_on_list(tmp_path: Path) -> None:
    # Prueba de corrección: autenticado como student, pedir owner=trainer no
    # debe devolver las tareas de otro usuario.
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks?owner=trainer", headers=headers("student", "STUDENT"))
    assert response.status_code == 200
    owners = {task["owner"] for task in response.json()}
    assert owners == {"student"}


def test_owner_query_param_is_ignored_on_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary?owner=trainer", headers=headers("student", "STUDENT"))
    assert response.status_code == 200
    assert response.json()["owner"] == "student"


def test_owner_body_field_is_ignored_on_create(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers("student", "STUDENT"),
            json={
                "title": "Spoofed owner",
                "description": "desc",
                "status": "TODO",
                "priority": "LOW",
                "owner": "trainer",
            },
        )
    assert created.status_code == 201
    assert created.json()["owner"] == "student"


# --- H-API-03: consultas parametrizadas (ver PLAN.md) ---


def test_create_task_with_apostrophe_in_title(tmp_path: Path) -> None:
    # Prueba de corrección: un título con apóstrofo es un dato de negocio
    # legítimo (no un payload de explotación) y debe poder guardarse igual
    # que cualquier otro texto, sin romper la consulta.
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers("student", "STUDENT"),
            json={"title": "O'Brien's task", "description": "Revisar", "status": "TODO", "priority": "LOW"},
        )
    assert created.status_code == 201
    assert created.json()["title"] == "O'Brien's task"


# --- H-API-04: carga segura de archivos (ver PLAN.md) ---


def test_upload_normalizes_path_traversal_in_filename(tmp_path: Path) -> None:
    # Prueba de corrección: un nombre de archivo con segmentos de ruta no
    # debe hacer que el archivo se escriba fuera del directorio de subida.
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("../escaped.txt", b"contenido", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "escaped.txt").exists()
    assert not (tmp_path / "escaped.txt").exists()


def test_upload_rejects_disallowed_extension(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("installer.exe", b"MZ", "application/octet-stream")},
        )
    assert response.status_code == 422


def test_upload_rejects_file_over_size_limit(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    oversized_content = b"x" * (2 * 1024 * 1024 + 1)
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("large.txt", oversized_content, "text/plain")},
        )
    assert response.status_code == 422


# --- docs/TESTING.md: completar casos feliz/borde/error por endpoint ---

# GET /api/tasks


def test_list_tasks_returns_empty_for_user_without_tasks(tmp_path: Path) -> None:
    # Caso borde: un usuario sin tareas sembradas recibe una lista vacía,
    # no un error.
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers("new_user", "STUDENT"))
    assert response.status_code == 200
    assert response.json() == []


# POST /api/tasks


def test_create_task_uses_default_status_and_priority(tmp_path: Path) -> None:
    # Caso borde: payload mínimo (sin status/priority) debe usar los
    # valores por defecto documentados en docs/ENDPOINTS.md.
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Solo titulo y desc", "description": "sin status ni priority"},
        )
    assert created.status_code == 201
    assert created.json()["status"] == "TODO"
    assert created.json()["priority"] == "MEDIUM"


def test_create_task_rejects_empty_payload(tmp_path: Path) -> None:
    # Caso borde + error documentado: payload vacío (faltan title y
    # description, ambos obligatorios).
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={})
    assert response.status_code == 422
    missing_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert missing_fields == {"title", "description"}


def test_create_task_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/tasks",
            headers={"Authorization": "Bearer invalid"},
            json={"title": "x", "description": "y"},
        )
    assert response.status_code == 401


# GET /api/summary


def test_summary_counts_by_status_and_high_priority_open(tmp_path: Path) -> None:
    # Camino feliz dedicado: tareas HIGH/TODO, HIGH/DONE y HIGH/ARCHIVED
    # adicionales a la sembrada deben reflejarse en byStatus y en
    # highPriorityOpen (que excluye DONE y ARCHIVED).
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Urgente", "description": "d", "status": "TODO", "priority": "HIGH"},
        )
        client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Cerrada", "description": "d", "status": "DONE", "priority": "HIGH"},
        )
        client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Archivada", "description": "d", "status": "ARCHIVED", "priority": "HIGH"},
        )
        response = client.get("/api/summary", headers=headers())
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5  # 2 sembradas para "student" + 3 nuevas
    assert body["byStatus"]["TODO"] == 2
    assert body["byStatus"]["DONE"] == 1
    assert body["byStatus"]["ARCHIVED"] == 1
    # HIGH/TODO cuenta dos veces (la sembrada "Refactor login" + "Urgente");
    # HIGH/DONE ("Cerrada") y HIGH/ARCHIVED ("Archivada") no cuentan.
    assert body["highPriorityOpen"] == 2


def test_summary_returns_zero_for_user_without_tasks(tmp_path: Path) -> None:
    # Caso borde: un usuario sin tareas obtiene un resumen en ceros, no un
    # error.
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers("new_user", "STUDENT"))
    assert response.status_code == 200
    assert response.json() == {"owner": "new_user", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


def test_summary_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


# POST /api/requirements


def test_upload_rejects_file_without_extension(tmp_path: Path) -> None:
    # Caso borde explícito pedido por el reto: archivo sin extensión.
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("README", b"sin extension", "text/plain")},
        )
    assert response.status_code == 422


def test_upload_accepts_file_exactly_at_size_limit(tmp_path: Path) -> None:
    # Caso borde: el límite documentado (2 MiB) es inclusive; justo en el
    # límite debe aceptarse, no rechazarse.
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    content_at_limit = b"x" * (2 * 1024 * 1024)
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("exact.txt", content_at_limit, "text/plain")},
        )
    assert response.status_code == 201
    assert response.json()["size"] == 2 * 1024 * 1024


def test_upload_rejects_missing_file_field(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post("/api/requirements", headers=headers())
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "file"


def test_upload_rejects_empty_filename(tmp_path: Path) -> None:
    # Resuelve la pregunta abierta de docs/ENDPOINTS.md: un filename vacío
    # (reproducible armando el multipart a mano) se rechaza con 422.
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    boundary = "testboundary123"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename=""\r\n'
        f"Content-Type: text/plain\r\n\r\n"
        f"contenido\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers={**headers(), "Content-Type": f"multipart/form-data; boundary={boundary}"},
            content=body,
        )
    assert response.status_code == 422


def test_upload_rejects_invalid_token(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers={"Authorization": "Bearer invalid"},
            files={"file": ("req.txt", b"contenido", "text/plain")},
        )
    assert response.status_code == 401


# GET /api/backend-health


def test_backend_health_returns_downstream_status_and_body(tmp_path: Path, monkeypatch) -> None:
    # Camino feliz: se simula una respuesta exitosa del backend de auth
    # (no se levanta un servicio real; se reemplaza la llamada HTTP).
    class _FakeResponse:
        status = 200
        data = b'{"status":"UP"}'

    def fake_request(self, method, url, *args, **kwargs):
        return _FakeResponse()

    monkeypatch.setattr("urllib3.PoolManager.request", fake_request)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    body = response.json()
    assert body["requestedBy"] == "student"
    assert body["status"] == 200
    assert body["body"] == '{"status":"UP"}'


def test_backend_health_returns_zero_status_when_downstream_unreachable(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    # La respuesta mantiene el status cero sin exponer el mensaje de la excepción.
    def fake_request_raises(self, method, url, *args, **kwargs):
        raise OSError("downstream no disponible (simulado para la prueba)")

    monkeypatch.setattr("urllib3.PoolManager.request", fake_request_raises)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 0
    assert body["body"] == "Backend health check failed"
    assert "Health check request failed (OSError)" in caplog.text
    assert "downstream no disponible" not in caplog.text


def test_backend_health_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
```

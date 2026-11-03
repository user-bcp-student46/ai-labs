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


def test_rejects_malformed_base64_token(tmp_path: Path) -> None:
    # Cubre el segundo mensaje de error documentado en docs/ENDPOINTS.md
    # para GET /api/tasks: un valor que no es Base64 válido (distinto del
    # caso "invalid token" por cantidad de segmentos).
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer not-base64!!"})
    assert response.status_code == 401
    assert "Invalid base64-encoded string" in response.json()["detail"]


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
    # Camino feliz dedicado: dos tareas HIGH/TODO adicionales a la sembrada
    # deben reflejarse en byStatus y en highPriorityOpen.
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


def test_backend_health_returns_zero_status_when_downstream_unreachable(tmp_path: Path, monkeypatch) -> None:
    # Caso borde documentado: la ruta responde 200 igual, con status=0 y el
    # texto de la excepción en el cuerpo, cuando el backend no es
    # alcanzable.
    def fake_request_raises(self, method, url, *args, **kwargs):
        raise OSError("downstream no disponible (simulado para la prueba)")

    monkeypatch.setattr("urllib3.PoolManager.request", fake_request_raises)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 0
    assert "downstream no disponible" in body["body"]


def test_backend_health_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

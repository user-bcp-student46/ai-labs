import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import create_app

TEST_TOKEN_SECRET = "test-only-key-for-isolated-workshop-signing-with-extra-test-bytes"


@pytest.fixture(autouse=True)
def configure_test_token_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_TOKEN_SECRET)


def token(
    username: str = "student",
    role: str = "STUDENT",
    lifetime_seconds: int = 3600,
    algorithm: str = "HS256",
) -> str:
    issued_at = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": username,
            "role": role,
            "iat": issued_at,
            "exp": issued_at + timedelta(seconds=lifetime_seconds),
        },
        TEST_TOKEN_SECRET,
        algorithm=algorithm,
    )


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
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_missing_bearer_header(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_tampered_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    signed_token = token()
    token_parts = signed_token.split(".")
    token_parts[2] = ("a" if token_parts[2][0] != "a" else "b") + token_parts[2][1:]
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers={"Authorization": "Bearer " + ".".join(token_parts)},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_legacy_unsigned_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    legacy_payload = f"student|STUDENT|{int(datetime.now(timezone.utc).timestamp()) + 3600}|legacy-test"
    legacy_token = base64.b64encode(legacy_payload.encode("utf-8")).decode("ascii")
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers_for_token(legacy_token))
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_unapproved_signing_algorithm(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers_for_token(token(algorithm="HS384")))
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_token_missing_required_claim(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    incomplete_token = jwt.encode(
        {"sub": "student", "role": "STUDENT", "iat": datetime.now(timezone.utc)},
        TEST_TOKEN_SECRET,
        algorithm="HS256",
    )
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers_for_token(incomplete_token))
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_expired_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers_for_token(token(lifetime_seconds=-60)))
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_returns_service_unavailable_when_token_secret_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AUTH_TOKEN_SECRET")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


def test_returns_service_unavailable_when_token_secret_is_too_short(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "short-test-key")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


def headers_for_token(signed_token: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + signed_token}

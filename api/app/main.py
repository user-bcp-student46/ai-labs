from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

import urllib3
from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import tasks_repository
from app.authorization import resolve_owner
from app.schemas import TaskCreateRequest
from app.security import Identity, verify_legacy_token
from app.uploads import store_requirement_file

HEALTH_CHECK_FAILURE_BODY = "Backend health check failed"

LOGGER = logging.getLogger(__name__)


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", "./data/workshop.db")
    selected_uploads = upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", "./uploads")
    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(selected_db, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, created_at TEXT NOT NULL)")
    count = connection.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()["total"]
    if count == 0:
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Refactor login','Separar responsabilidades en frontend','TODO','student','HIGH',datetime('now'))")
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Review API','Revisar seguridad de endpoints','IN_PROGRESS','student','MEDIUM',datetime('now'))")
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Trainer notes','Preparar retrospectiva','TODO','trainer','LOW',datetime('now'))")
        connection.commit()

    app = FastAPI(title="Workshop Requirements API", version="0.1.0")
    app.state.connection = connection
    app.state.upload_dir = selected_uploads
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/tasks")
    def list_tasks(identity: Identity = Depends(verify_legacy_token)) -> list[dict[str, Any]]:
        requested_owner = resolve_owner(identity)
        return tasks_repository.list_by_owner(connection, requested_owner)

    @app.post("/api/tasks", status_code=201)
    def create_task(task: TaskCreateRequest, identity: Identity = Depends(verify_legacy_token)) -> dict[str, Any]:
        owner = resolve_owner(identity)
        return tasks_repository.insert(connection, task, owner)

    @app.get("/api/summary")
    def summary(identity: Identity = Depends(verify_legacy_token)) -> dict[str, Any]:
        requested_owner = resolve_owner(identity)
        rows = tasks_repository.summary_rows_by_owner(connection, requested_owner)
        response: dict[str, Any] = {"owner": requested_owner, "total": 0, "byStatus": {}, "highPriorityOpen": 0}
        for row in rows:
            response["total"] = response["total"] + 1
            if row["status"] in response["byStatus"]:
                response["byStatus"][row["status"]] = response["byStatus"][row["status"]] + 1
            else:
                response["byStatus"][row["status"]] = 1
            if row["priority"] == "HIGH":
                if row["status"] != "DONE":
                    if row["status"] != "ARCHIVED":
                        response["highPriorityOpen"] = response["highPriorityOpen"] + 1
        return response

    @app.post("/api/requirements", status_code=201)
    async def upload_requirement(file: UploadFile = File(...), identity: Identity = Depends(verify_legacy_token)) -> dict[str, Any]:
        stored = await store_requirement_file(file, selected_uploads)
        return {"owner": identity.username, "fileName": stored.file_name, "storedAt": stored.stored_at, "size": stored.size}

    @app.get("/api/backend-health")
    def backend_health(identity: Identity = Depends(verify_legacy_token)) -> dict[str, Any]:
        url = os.getenv("AUTH_HEALTH_URL", "http://localhost:8080/q/health")
        try:
            response = urllib3.PoolManager().request("GET", url, timeout=3.0)
            return {"requestedBy": identity.username, "status": response.status, "body": response.data.decode("utf-8")}
        except Exception as error:
            LOGGER.warning("Health check request failed (%s)", type(error).__name__)
            return {"requestedBy": identity.username, "status": 0, "body": HEALTH_CHECK_FAILURE_BODY}

    @app.on_event("shutdown")
    def close_connection() -> None:
        connection.close()

    return app


app = create_app()

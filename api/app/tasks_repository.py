"""Acceso a datos de tareas con consultas parametrizadas.

Reemplaza la concatenación de strings en las consultas SQL (H-API-03, ver
PLAN.md) por parámetros posicionados (``?``) de ``sqlite3``, evitando que un
valor del cliente altere la consulta.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from app.schemas import TaskCreateRequest

TASK_COLUMNS = "id,title,description,status,owner,priority,created_at"


def as_task(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "owner": row["owner"],
        "priority": row["priority"],
        "createdAt": row["created_at"],
    }


def list_by_owner(connection: sqlite3.Connection, owner: str) -> list[dict[str, Any]]:
    rows = connection.execute(f"SELECT {TASK_COLUMNS} FROM tasks WHERE owner=? ORDER BY id", (owner,)).fetchall()
    return [as_task(row) for row in rows]


def get_by_id(connection: sqlite3.Connection, task_id: int) -> dict[str, Any]:
    row = connection.execute(f"SELECT {TASK_COLUMNS} FROM tasks WHERE id=?", (task_id,)).fetchone()
    return as_task(row)


def insert(connection: sqlite3.Connection, task: TaskCreateRequest, owner: str) -> dict[str, Any]:
    cursor = connection.execute(
        "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))",
        (task.title, task.description, task.status, owner, task.priority),
    )
    connection.commit()
    return get_by_id(connection, cursor.lastrowid)


def summary_rows_by_owner(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return connection.execute("SELECT status,priority FROM tasks WHERE owner=?", (owner,)).fetchall()

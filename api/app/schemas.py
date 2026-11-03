"""Modelos de request tipados para tareas (H-API-03, ver PLAN.md).

Reemplaza el uso de ``dict[str, Any]`` crudo en el cuerpo de creación de
tareas por un modelo Pydantic con valores por defecto nombrados.
"""
from __future__ import annotations

from pydantic import BaseModel

DEFAULT_TASK_STATUS = "TODO"
DEFAULT_TASK_PRIORITY = "MEDIUM"


class TaskCreateRequest(BaseModel):
    title: str
    description: str
    status: str = DEFAULT_TASK_STATUS
    priority: str = DEFAULT_TASK_PRIORITY

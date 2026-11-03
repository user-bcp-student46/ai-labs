"""Validación y guardado seguro de archivos de requerimientos.

Antes, la ruta usaba ``file.filename`` tal cual para formar la ruta de
escritura y guardaba cualquier tamaño o extensión (H-API-04, ver PLAN.md).
Este módulo normaliza el nombre, limita la extensión permitida y el tamaño
máximo antes de guardar.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel

ALLOWED_REQUIREMENT_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
MAX_REQUIREMENT_FILE_SIZE_BYTES = 2 * 1024 * 1024


class StoredFile(BaseModel):
    file_name: str
    stored_at: str
    size: int


def _normalized_file_name(filename: str | None) -> str:
    candidate = Path(filename or "").name
    if not candidate:
        raise HTTPException(status_code=422, detail="El archivo debe tener un nombre válido")
    return candidate


def _ensure_allowed_extension(file_name: str) -> None:
    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_REQUIREMENT_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Extensión de archivo no permitida")


def _ensure_within_size_limit(content: bytes) -> None:
    if len(content) > MAX_REQUIREMENT_FILE_SIZE_BYTES:
        raise HTTPException(status_code=422, detail="El archivo excede el tamaño máximo permitido")


async def store_requirement_file(upload: UploadFile, upload_dir: str) -> StoredFile:
    file_name = _normalized_file_name(upload.filename)
    _ensure_allowed_extension(file_name)
    content = await upload.read()
    _ensure_within_size_limit(content)
    target = Path(upload_dir) / file_name
    target.write_bytes(content)
    return StoredFile(file_name=file_name, stored_at=str(target), size=len(content))

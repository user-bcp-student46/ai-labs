"""Resuelve el propietario autorizado para operaciones sobre tareas.

Antes, las rutas tomaban `owner` de la consulta o del cuerpo que enviaba el
cliente (H-API-02, ver PLAN.md). Ahora el propietario siempre proviene de la
identidad ya verificada del token (`app.security.Identity`), nunca de un
valor controlado por el cliente.
"""
from __future__ import annotations

from app.security import Identity


def resolve_owner(identity: Identity) -> str:
    return identity.username

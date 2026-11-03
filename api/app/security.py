"""Verificación de identidad a partir del token heredado del login.

Aísla la lectura del token para que las rutas no mezclen parsing de
credenciales con lógica de negocio (H-API-01, ver PLAN.md). El formato
heredado (Base64 con cuatro segmentos separados por ``|``) se conserva tal
cual lo emite hoy el componente ``auth``: verificar una firma criptográfica
real, emisor y audiencia requiere que ``auth`` emita un token firmado
compatible, lo cual queda registrado como coordinación externa pendiente en
PLAN.md y no se implementa en este módulo. Lo que sí queda resuelto aquí es
que el secreto deja de estar fijo en el código (pasa a variable de entorno)
y que el parsing usa constantes con nombre en vez de índices sueltos.
"""
from __future__ import annotations

import base64
import os
import time

from fastapi import Header, HTTPException
from pydantic import BaseModel

TOKEN_SEGMENT_COUNT = 4
USERNAME_SEGMENT_INDEX = 0
ROLE_SEGMENT_INDEX = 1
EXPIRATION_SEGMENT_INDEX = 2
SECRET_SEGMENT_INDEX = 3
TOKEN_SECRET_ENV_VAR = "WORKSHOP_TOKEN_SECRET"
DEFAULT_LEGACY_TOKEN_SECRET = "WORKSHOP_SECRET_2026"  # valor de prueba del workshop, no un secreto real


class Identity(BaseModel):
    username: str
    role: str


def _configured_token_secret() -> str:
    return os.getenv(TOKEN_SECRET_ENV_VAR, DEFAULT_LEGACY_TOKEN_SECRET)


def _is_expired(expiration_epoch_seconds: int) -> bool:
    return expiration_epoch_seconds < int(time.time())


def _parse_legacy_token(token: str) -> Identity:
    decoded = base64.b64decode(token).decode("utf-8")
    segments = decoded.split("|")
    if len(segments) != TOKEN_SEGMENT_COUNT:
        raise ValueError("invalid token")
    if segments[SECRET_SEGMENT_INDEX] != _configured_token_secret():
        raise ValueError("invalid token")
    if _is_expired(int(segments[EXPIRATION_SEGMENT_INDEX])):
        raise ValueError("invalid token")
    return Identity(username=segments[USERNAME_SEGMENT_INDEX], role=segments[ROLE_SEGMENT_INDEX])


def verify_legacy_token(authorization: str = Header(default="")) -> Identity:
    try:
        token = authorization.replace("Bearer ", "")
        return _parse_legacy_token(token)
    except Exception as error:
        raise HTTPException(status_code=401, detail="Invalid token: " + str(error)) from error

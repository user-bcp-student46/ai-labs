# Checklist de casos de prueba - HU-AUTH-07

## 1. Resumen de la HU
Bloquear temporalmente una cuenta (15 min) tras 5 intentos fallidos
consecutivos de login, respondiendo `423` durante el bloqueo y
reiniciando el contador ante un login exitoso previo al límite.

## 2. Matriz de trazabilidad

| Criterio de aceptación | Caso(s) que lo cubren | Cobertura |
|---|---|---|
| Bloqueo a los 5 intentos fallidos, 15 min | TC-01, TC-02 | Completa |
| `423` durante bloqueo con contraseña correcta | TC-03 | Completa |
| Login exitoso reinicia el contador | TC-04 | Completa |
| Bloqueo/expiración registrados sin datos sensibles | TC-05 | Completa |

## 3. Checklist de casos de prueba

| ID | Caso | Tipo | Precondición | Pasos resumidos | Resultado esperado | Criterio relacionado |
|---|---|---|---|---|---|---|
| TC-01 | 5 intentos fallidos consecutivos | error | Usuario existente, 0 intentos previos | Enviar 5 logins con contraseña incorrecta | Cuenta queda bloqueada; respuesta describe el bloqueo | Bloqueo a los 5 intentos |
| TC-02 | Bloqueo expira tras 15 minutos | borde | Cuenta bloqueada | Avanzar el reloj/config 15 min y reintentar login válido | Login se procesa normalmente (ya no bloqueado) | Bloqueo a los 5 intentos |
| TC-03 | Login válido durante bloqueo activo | seguridad | Cuenta bloqueada, contraseña correcta | `POST /auth/login` con credenciales correctas | `423`, sin emitir token | `423` durante bloqueo |
| TC-04 | Login exitoso antes del límite reinicia contador | feliz | 3 intentos fallidos previos | Login correcto, luego 4 fallidos más | Cuenta NO bloqueada tras los 4 fallidos (contador reiniciado) | Reinicio de contador |
| TC-05 | Logs de bloqueo sin datos sensibles | seguridad | Cuenta bloqueada | Revisar logs generados durante TC-01 | Logs registran el evento de bloqueo/expiración sin contraseña ni token | Logs sin datos sensibles |

## 4. Verificación de DoR

| Ítem del DoR | Cumplido | Evidencia / justificación |
|---|---|---|
| Contrato actual de `POST /auth/login` documentado | Sí | Ver `docs/ENDPOINTS.md` |
| Almacenamiento de intentos fallidos definido | Pendiente | No se especifica en la HU si es en memoria o tabla; ver Preguntas abiertas |
| "Intentos máximos" y "tiempo de bloqueo" como configuración | Sí | HU exige que no sean valores fijos en código |

## 5. Verificación de DoD

| Ítem del DoD | Cumplido | Evidencia / justificación |
|---|---|---|
| Pruebas unitarias de contador, bloqueo y expiración | Pendiente | Cubierto por TC-01, TC-02, TC-04; falta ejecutarlas |
| Cobertura del código modificado >= 85% | Pendiente | Verificar con el runner de pruebas del componente `auth` |
| Sin secretos reales en configuración ni pruebas | Sí | Casos usan credenciales de prueba aisladas |
| Documentación del endpoint actualizada con código 423 | Pendiente | No se referencia una actualización concreta de `docs/ENDPOINTS.md` |

## 6. Brechas y pruebas faltantes
- Falta definir el mecanismo de almacenamiento de intentos fallidos (DoR
  incompleto); bloquea precisar si el contador sobrevive a un reinicio del
  servicio.
- No hay un caso explícito para un segundo bloqueo consecutivo (reincidencia)
  tras una primera expiración; evaluar si aplica.

## 7. Supuestos
- "15 minutos" y "5 intentos" se asumen configurables mediante variables de
  entorno, no literales en código, según el DoR.

## 8. Preguntas abiertas
- ¿El almacenamiento de intentos fallidos es en memoria o persistente
  (sobrevive a reinicios/escalado horizontal)?
- ¿El bloqueo es por usuario, por IP, o ambos?

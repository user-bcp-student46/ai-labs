---
name: hu-test-case-checklist
description: 'Genera y valida un checklist de casos de prueba trazable a partir de una Historia de Usuario (HU) con descripción funcional, criterios de aceptación, DoR y DoD. Usar antes de implementar una HU, antes de un PR, o para auditar un checklist de pruebas ya existente y detectar criterios sin cobertura.'
---

# Skill: HU -> Test Case Checklist

## 1) Metadata
- **Skill ID:** hu-test-case-checklist
- **Version:** 0.1.0
- **Purpose:** Convertir una Historia de Usuario (HU) en un checklist de casos de prueba trazable y validado (camino feliz, errores, bordes y seguridad), asegurando que cada criterio de aceptación y cada ítem del DoR/DoD tengan al menos un caso o verificación asociada.
- **Audience (roles):** QA, Tech Lead, Backend, Frontend, PO.
- **When to use:** Antes de implementar una HU (para planificar pruebas), antes de abrir un PR o checkpoint (para auditar cobertura de pruebas), o cuando ya existe un checklist y se quiere **validar** que esté completo y trazable.
- **When NOT to use:** Incidentes P1 de producción, cambios triviales (typos, ajustes sin impacto funcional) o HUs sin criterios de aceptación definidos (primero completarlos).
- **Sensitive inputs:** no incluyas datos reales de clientes, credenciales, tokens, secretos reales ni URLs internas no autorizadas; usa valores de prueba aislados.
- **Expected output:** Markdown estructurado según la sección Output.

## 2) Inputs
Proporciona la HU en este formato (si falta algún campo, decláralo en "Preguntas abiertas" del output en vez de inventarlo):

- **ID / Título de la HU:**
- **Descripción funcional:** (como [rol], quiero [acción], para [beneficio])
- **Criterios de aceptación:** (lista numerada o con bullets)
- **DoR (Definition of Ready):** (lista de condiciones para empezar a trabajar la HU)
- **DoD (Definition of Done):** (lista de condiciones para considerarla terminada)
- **Contexto técnico (opcional):** endpoints, pantallas, roles/permisos, datos involucrados
- **Checklist de casos de prueba existente (opcional):** si ya hay un checklist y lo que se pide es auditarlo/validarlo en vez de generarlo desde cero

## 3) Output
Devuelve **solo** un documento Markdown con estas secciones:

1. **Resumen de la HU**
2. **Matriz de trazabilidad** (tabla: Criterio de aceptación | Caso(s) de prueba que lo cubren | Cobertura: completa/parcial/sin cobertura)
3. **Checklist de casos de prueba** (tabla: ID | Caso | Tipo [feliz/error/borde/seguridad] | Precondición | Pasos resumidos | Resultado esperado | Criterio relacionado)
4. **Verificación de DoR** (checklist: ítem del DoR | Cumplido [sí/no/no aplica] | Evidencia o justificación)
5. **Verificación de DoD** (checklist: ítem del DoD | Cumplido [sí/no/no aplica] | Evidencia o justificación)
6. **Brechas y pruebas faltantes** (criterios sin caso, tipos de prueba ausentes, ítems de DoR/DoD pendientes)
7. **Supuestos**
8. **Preguntas abiertas**

## 4) Constraints
- No inventes criterios de aceptación, ítems de DoR/DoD ni reglas de negocio que no estén en la HU de entrada; si falta información, regístralo en **Preguntas abiertas**.
- Cada criterio de aceptación debe tener como mínimo un caso de tipo "feliz"; si el criterio involucra autenticación, autorización, datos sensibles o archivos, agrega al menos un caso de "error" o "seguridad".
- No incluyas datos reales, secretos ni credenciales en los casos de prueba; usa valores de prueba aislados y genéricos.
- Mantén el mapeo trazable: cada caso del checklist debe referenciar el criterio de aceptación (o ítem de DoR/DoD) que cubre; ningún caso "huérfano".
- Si el usuario entrega un checklist existente, **audítalo** (no lo reescribas desde cero): señala casos duplicados, faltantes o mal tipificados antes de completar lo que falte.
- Mantén la salida enfocada y legible; evita repetir el texto completo de la HU, resume.

## 5) Validation Rules
Antes de entregar la salida, valida que cumple todo lo siguiente (si algo falla, corrígelo antes de responder):

- Todos los criterios de aceptación de la HU aparecen en la **Matriz de trazabilidad** con al menos un caso asociado (sin filas "sin cobertura" salvo que se expliquen en "Brechas").
- Hay al menos un caso "feliz" y un caso "error" por cada criterio funcional principal.
- Si la HU involucra autenticación, autorización, datos sensibles, carga de archivos o integraciones externas, existe al menos un caso de tipo "seguridad" o "borde" explícito.
- Cada ítem del DoR y del DoD tiene un estado explícito (cumplido / pendiente / no aplica) con evidencia o justificación, no solo un checkbox vacío.
- No hay datos sensibles, secretos reales ni URLs internas no autorizadas en ningún caso de prueba.
- No hay criterios, reglas o ítems de DoR/DoD inventados que no figuren en la HU de entrada.
- Toda brecha detectada (criterio sin caso, tipo de prueba ausente, DoR/DoD incompleto) está listada en **Brechas y pruebas faltantes**, no omitida silenciosamente.

## 6) Evidence
Adjunta o referencia estos elementos en el PR o entrega:
- `SKILL.md` versionado.
- `examples/input.sample.md`.
- `examples/output.sample.md`.
- Tag de versión para el Skill, como `skill-hu-test-case-checklist-v0.1.0`.

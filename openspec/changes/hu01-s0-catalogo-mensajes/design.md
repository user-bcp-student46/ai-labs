# Design

## Context

`web/src/app` hoy solo contiene `LoginComponent` y `DashboardComponent` (standalone Angular 21), ninguno
construido para el flujo de pago de HU01. El texto visible se escribe literal en el TypeScript/HTML de cada
componente (`web/src/app/login/login.component.ts:34-57`) y no existe ningún directorio ni módulo
compartido de UI. Las pruebas del proyecto corren con Vitest (`web/package.json` → `"test": "vitest run"`,
`"test:coverage": "vitest run --coverage"`), orquestadas desde la raíz con `python tools/lab.py test web`.
Ver `proposal.md` - Why para la motivación completa.

## Goals / Non-Goals

**Goals:**
- Definir dónde viven el catálogo de mensajes y los componentes de UI base dentro de `web/src/app`, sin
  tocar `LoginComponent` ni `DashboardComponent`.
- Dejar un mecanismo de catálogo y un conjunto de componentes base consumibles por HU01-S1–S4, cumpliendo
  los requisitos de `specs/payment-ui-message-catalog` y `specs/payment-ui-accessible-components`.

**Non-Goals:**
- No se construyen las pantallas funcionales del flujo de pago (saludo, confirmación, resultados,
  orquestador): eso es HU01-S1–S4.
- No se define el copy final de ningún mensaje (etiquetas de estados terminales, textos de ayuda): sigue
  pendiente con producto (ver HU01-S0-catalogo-mensajes.md — Preguntas abiertas).
- No se persiste el intento de pago en sí durante el estado "En proceso": solo el mensaje visual persiste a
  nivel de UI; la persistencia del intento depende de HU01-S1.

## Decisions

- **Ubicación del módulo compartido**: un nuevo directorio `web/src/app/payment-ui/` (hermano de `login/` y
  `dashboard/`), con dos subcarpetas: `messages/` (catálogo) y `components/` (componentes base). Alternativa
  considerada: anidar bajo un futuro `web/src/app/payment/` junto con las pantallas de S1–S4; se descarta
  porque esta slice es un habilitador independiente y no depende de que exista aún el módulo de pantallas.
- **Mecanismo del catálogo**: un servicio Angular inyectable (`MessageCatalogService` o equivalente) que
  expone un método de resolución por clave (p. ej. `get(key: string): string`) respaldado por un objeto de
  configuración editable (JSON o TS) con las claves de las categorías definidas en la spec (saludo, resumen
  de confirmación, estados terminales, ayuda, errores). Alternativa considerada: hardcodear un enum de
  textos; se descarta porque no cumple el requisito de catálogo "editable sin tocar componentes".
- **Componentes base como standalone components/directivas Angular**: siguiendo el patrón ya usado por
  `LoginComponent`/`DashboardComponent` (standalone, sin NgModule), se agregan componentes/directivas para
  texto, botón, ícono+texto, layout de pantalla (con elemento de ayuda) y estado "En proceso". Cada uno
  encapsula su propio tamaño/contraste/ARIA vía CSS y atributos de plantilla, no vía lógica duplicada por
  pantalla consumidora.
- **Persistencia visual del estado "En proceso"**: el componente guarda su bandera de "en curso" en
  almacenamiento local del navegador (mismo mecanismo que ya usa el proyecto para `workshop_token` /
  `workshop_preferences` en `login.component.ts`), de modo que al reabrir la app el componente puede volver a
  mostrar el mensaje tranquilizador sin depender aún de la integración de backend de HU01-S1.
- **No se agregan dependencias nuevas**: accesibilidad (roles/ARIA, contraste) se implementa con HTML
  semántico y CSS del propio proyecto, sin introducir una librería de componentes externa, para no añadir
  dependencias no justificadas (contrato de agentes de `web`, regla 5).

## Risks / Trade-offs

- [Riesgo] Sin copy final de producto, las claves del catálogo podrían no coincidir luego con las que
  definan los textos reales → Mitigación: las claves se nombran por categoría/función (p. ej.
  `estado.exitoso`, no el texto literal), de modo que cambiar el copy no exige renombrar claves.
- [Riesgo] Un componente de botón/texto demasiado rígido podría no adaptarse a necesidades específicas de
  pantallas futuras (S1–S4) → Mitigación: los componentes exponen slots/inputs para contenido variable,
  manteniendo fijas solo las propiedades que garantizan el requisito de accesibilidad (tamaño, contraste,
  roles).
- [Trade-off] Persistir la bandera de "En proceso" en almacenamiento local del navegador es una solución de
  UI simple pero no sincroniza entre dispositivos ni sobrevive a borrar datos del navegador → Aceptado
  explícitamente en el alcance de esta slice; la persistencia real del intento de pago es responsabilidad de
  HU01-S1.
